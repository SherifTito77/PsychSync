#!/usr/bin/env python3
"""
Quick Data Corruption Risk Scanner for PsychSync

Fast grep-based scanner for detecting common data corruption patterns:
1. db.add() without commit()
2. db.delete() without rollback handling
3. Missing error handling in database operations
4. Race conditions in read-modify-write patterns

Usage:
    python3 scripts/quick_data_corruption_scan.py
"""

import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path


def run_grep(pattern, path, include_pattern="*.py"):
    """Run grep and return results"""
    try:
        cmd = ["grep", "-r", "-n", "--include=" + include_pattern, pattern, path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []


def analyze_database_operations():
    """Analyze database operations for corruption risks"""
    root = "/Users/sheriftito/Downloads/psychsync"
    app_dir = os.path.join(root, "app")

    print("=" * 80)
    print("QUICK DATA CORRUPTION RISK SCANNER")
    print("=" * 80)

    issues = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}

    # Pattern 1: Look for db.add() or db.delete() operations
    print("\n🔍 Scanning for database write operations...")
    add_delete_lines = run_grep(
        r"(db\.add\(|db\.delete\(|session\.add\(|session\.delete\()", app_dir
    )

    # Pattern 2: Look for commit operations
    print("🔍 Scanning for commit operations...")
    commit_lines = run_grep(r"\.(commit|flush)\(\)", app_dir)

    # Pattern 3: Look for rollback operations
    print("🔍 Scanning for rollback operations...")
    rollback_lines = run_grep(r"\.rollback\(\)", app_dir)

    # Pattern 4: Look for try/except blocks
    print("🔍 Scanning for error handling...")
    try_blocks = run_grep(r"^\s*try:", app_dir)
    except_blocks = run_grep(r"^\s*except", app_dir)

    # Pattern 5: Look for SELECT FOR UPDATE (row-level locking)
    print("🔍 Scanning for row-level locking...")
    for_update = run_grep(r"(select_for_update|with_for_update|FOR UPDATE)", app_dir)

    # Pattern 6: Look for race-prone patterns (get, modify, commit)
    print("🔍 Scanning for read-modify-write patterns...")
    read_modify = run_grep(r"execute\(|scalar\(|get\(", app_dir)

    # Analyze findings
    print("\n📊 Analyzing results...")

    # Map files to their operations
    file_operations = defaultdict(
        lambda: {
            "add_delete": [],
            "commit": [],
            "rollback": [],
            "try_except": False,
            "for_update": False,
        }
    )

    # Process add/delete operations
    for line in add_delete_lines:
        if not line:
            continue
        parts = line.split(":", 1)
        if len(parts) == 2:
            filepath = parts[0]
            file_operations[filepath]["add_delete"].append(parts[1].strip())

    # Process commits
    for line in commit_lines:
        if not line:
            continue
        parts = line.split(":", 1)
        if len(parts) == 2:
            filepath = parts[0]
            file_operations[filepath]["commit"].append(parts[1].strip())

    # Process rollbacks
    for line in rollback_lines:
        if not line:
            continue
        parts = line.split(":", 1)
        if len(parts) == 2:
            filepath = parts[0]
            file_operations[filepath]["rollback"].append(parts[1].strip())

    # Check for try/except
    for line in try_blocks:
        if not line:
            continue
        filepath = line.split(":", 1)[0]
        file_operations[filepath]["try_except"] = True

    # Check for FOR UPDATE
    for line in for_update:
        if not line:
            continue
        filepath = line.split(":", 1)[0]
        file_operations[filepath]["for_update"] = True

    # Identify issues
    for filepath, ops in file_operations.items():
        # Skip if no add/delete operations
        if not ops["add_delete"]:
            continue

        # Issue 1: Add/delete without commit
        if ops["add_delete"] and not ops["commit"]:
            issues["HIGH"].append(
                {
                    "file": filepath,
                    "issue": "Database write operations without explicit commit()",
                    "details": f"Found {len(ops['add_delete'])} add/delete operations but no commit()",
                }
            )

        # Issue 2: Add/delete without try/except
        if ops["add_delete"] and not ops["try_except"]:
            issues["MEDIUM"].append(
                {
                    "file": filepath,
                    "issue": "Database operations without error handling",
                    "details": f"Found {len(ops['add_delete'])} operations outside try/except block",
                }
            )

        # Issue 3: Add/delete without rollback
        if ops["add_delete"] and ops["try_except"] and not ops["rollback"]:
            issues["HIGH"].append(
                {
                    "file": filepath,
                    "issue": "Database operations in try block but no rollback() in except",
                    "details": "If exception occurs, transaction may not be rolled back",
                }
            )

    # Check for missing row-level locking in update operations
    update_files = run_grep(r"\.update\(|UPDATE\s+.*SET", app_dir)
    update_file_set = set()
    for line in update_files:
        if line:
            filepath = line.split(":", 1)[0]
            if (
                filepath not in file_operations
                or not file_operations[filepath]["for_update"]
            ):
                update_file_set.add(filepath)

    for filepath in update_file_set:
        issues["MEDIUM"].append(
            {
                "file": filepath,
                "issue": "UPDATE operation without row-level locking",
                "details": "Consider using SELECT FOR UPDATE to prevent race conditions",
            }
        )

    # Generate report
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    print(f"\n📈 Summary:")
    print(f"   🔴 CRITICAL: {len(issues['CRITICAL'])}")
    print(f"   🟠 HIGH: {len(issues['HIGH'])}")
    print(f"   🟡 MEDIUM: {len(issues['MEDIUM'])}")
    print(f"   🟢 LOW: {len(issues['LOW'])}")

    # Generate markdown report
    report_lines = [
        "# Data Corruption Risk Analysis Report\n",
        f"**Generated:** {os.popen('date').read().strip()}",
        f"**Total Issues:** {sum(len(v) for v in issues.values())}\n",
        "---\n",
        "## Summary by Severity\n",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| **CRITICAL** | {len(issues['CRITICAL'])} |",
        f"| **HIGH** | {len(issues['HIGH'])} |",
        f"| **MEDIUM** | {len(issues['MEDIUM'])} |",
        f"| **LOW** | {len(issues['LOW'])} |",
        "\n---\n",
    ]

    # Add detailed findings
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if not issues[severity]:
            continue

        severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[
            severity
        ]

        report_lines.append(
            f"\n## {severity_icon} {severity} Priority Issues ({len(issues[severity])})\n"
        )

        for idx, issue in enumerate(
            issues[severity][:20], 1
        ):  # Limit to 20 per severity
            rel_path = issue["file"].replace(
                "/Users/sheriftito/Downloads/psychsync/", ""
            )
            report_lines.append(f"\n### {idx}. {rel_path}")
            report_lines.append(f"**Issue:** {issue['issue']}")
            report_lines.append(f"**Details:** {issue['details']}")

        if len(issues[severity]) > 20:
            report_lines.append(f"\n_... and {len(issues[severity]) - 20} more_")

    # Add recommendations
    report_lines.extend(
        [
            "\n---\n",
            "## Recommendations\n",
            "\n### Immediate Actions (HIGH Priority)\n",
            "1. **Add explicit commits** after all database write operations\n",
            "2. **Implement rollback handlers** in all except blocks\n",
            "3. **Add try/except blocks** around all database operations\n",
            "\n### Best Practices (MEDIUM Priority)\n",
            "1. **Use row-level locking** (`SELECT FOR UPDATE`) for update operations\n",
            "2. **Implement proper transaction boundaries** for multi-step operations\n",
            "3. **Add validation** before database writes\n",
            "4. **Use database constraints** (UNIQUE, FOREIGN KEY, CHECK)\n",
            "\n### Prevention (LOW Priority)\n",
            "1. **Add automated tests** for concurrent operations\n",
            "2. **Implement monitoring** for long-running transactions\n",
            "3. **Add comprehensive logging** for all database operations\n",
            "\n---\n",
            "**Generated by:** Quick Data Corruption Risk Scanner",
            "**Tool:** `scripts/quick_data_corruption_scan.py`\n",
        ]
    )

    # Save report
    report_path = os.path.join(root, "DATA_CORRUPTION_RISKS.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n📄 Report saved to: DATA_CORRUPTION_RISKS.md")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_database_operations()
