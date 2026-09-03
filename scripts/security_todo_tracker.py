#!/usr/bin/env python3
"""
Security TODO Tracker

This script finds, categorizes, and tracks security-related TODO/FIXME/HACK comments
throughout the codebase to ensure critical security tasks are completed.

Usage:
    # Find all security TODOs
    python scripts/security_todo_tracker.py --find

    # Generate prioritized report
    python scripts/security_todo_tracker.py --report > security_todos.md

    # Update status of TODOs
    python scripts/security_todo_tracker.py --update-id TODO-001 --status "In Progress"

    # Export to CSV for tracking in project management tools
    python scripts/security_todo_tracker.py --export > security_todos.csv
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SecurityTODO:
    """Represents a security-related TODO item."""

    id: str
    file: str
    line: int
    type: str  # TODO, FIXME, HACK, XXX, NOTE
    category: str  # auth, validation, encryption, etc.
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    code_snippet: str
    status: str = "Open"  # Open, In Progress, Completed, Deferred
    assigned_to: str = ""
    created_date: str = ""
    updated_date: str = ""

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.updated_date:
            self.updated_date = datetime.now().isoformat()


class SecurityTODOTracker:
    """Tracks and manages security-related TODOs."""

    def __init__(self, root_path: str, tracker_file: str = ".security_todos.json"):
        self.root_path = Path(root_path)
        self.tracker_file = Path(tracker_file)
        self.todos: List[SecurityTODO] = []
        self.categories = {
            "auth": "Authentication/Authorization",
            "validation": "Input Validation",
            "encryption": "Encryption/Cryptography",
            "injection": "Injection Attacks (SQL, XSS, etc.)",
            "config": "Configuration Security",
            "logging": "Security Logging/Auditing",
            "session": "Session Management",
            "cors": "CORS/Origin Security",
            "rate_limit": "Rate Limiting",
            "ssl": "SSL/TLS",
            "data_exposure": "Data Exposure",
            "other": "Other Security",
        }

        # Load existing tracker if available
        self.load_tracker()

    def find_all_files(self) -> List[Path]:
        """Find all source code files."""
        files = []

        # Python files
        files.extend(self.root_path.rglob("**/*.py"))

        # TypeScript files
        files.extend(self.root_path.rglob("**/*.ts"))
        files.extend(self.root_path.rglob("**/*.tsx"))

        # JavaScript files
        files.extend(self.root_path.rglob("**/*.js"))
        files.extend(self.root_path.rglob("**/*.jsx"))

        ignored_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".pytest_cache",
            "dist",
            "build",
            ".next",
            "coverage",
            ".cache",
        }

        return [
            f
            for f in files
            if not any(ignored_dir in f.parts for ignored_dir in ignored_dirs)
            and f.is_file()
        ]

    def detect_category(self, text: str) -> str:
        """Detect security category from TODO text."""
        text_lower = text.lower()

        keywords = {
            "auth": [
                "auth",
                "login",
                "password",
                "credential",
                "token",
                "jwt",
                "session",
            ],
            "validation": ["validat", "sanitiz", "escape", "xss", "injection"],
            "encryption": ["encrypt", "decrypt", "hash", "cipher", "crypto", "secret"],
            "injection": ["sql", "injection", "xss", "csrf", "command"],
            "config": ["config", "setting", "env", "environment", "hardcoded"],
            "logging": ["log", "audit", "monitor", "alert"],
            "cors": ["cors", "origin"],
            "rate_limit": ["rate", "limit", "throttle"],
            "ssl": ["ssl", "tls", "certificate", "https"],
            "data_exposure": ["expose", "leak", "sensitive", "pii"],
        }

        for category, words in keywords.items():
            if any(word in text_lower for word in words):
                return category

        return "other"

    def detect_severity(self, text: str, category: str) -> str:
        """Detect severity from TODO text."""
        text_upper = text.upper()

        # Explicit severity markers
        if (
            "CRITICAL" in text_upper
            or "URGENT" in text_upper
            or "SECURITY" in text_upper
        ):
            return "CRITICAL"

        if "HIGH" in text_upper or "IMPORTANT" in text_upper:
            return "HIGH"

        # Category-based severity
        high_severity_categories = {"auth", "encryption", "injection", "sql"}
        if category in high_severity_categories:
            return "HIGH"

        if "FIXME" in text_upper or "XXX" in text_upper or "HACK" in text_upper:
            return "MEDIUM"

        if "TODO" in text_upper or "NOTE" in text_upper:
            return "MEDIUM"

        return "LOW"

    def parse_todo_comment(
        self, line: str, file_path: Path, line_num: int
    ) -> Optional[SecurityTODO]:
        """Parse a TODO comment line into a SecurityTODO object."""
        # Pattern: TODO(security), FIXME(auth), HACK, etc.
        todo_pattern = r"(TODO|FIXME|HACK|XXX|NOTE)\s*(?:\([^)]+\))?\s*:?\s*(.+)"
        match = re.match(todo_pattern, line.strip())

        if not match:
            return None

        todo_type = match.group(1)
        description = match.group(2).strip()

        # Check if it's security-related
        security_keywords = [
            "security",
            "secure",
            "auth",
            "validat",
            "encrypt",
            "inject",
            "xss",
            "csrf",
            "sql",
            "cors",
            "rate",
            "limit",
            "sanitiz",
            "escape",
            "hash",
            "token",
            "session",
            "credential",
            "password",
            "permission",
            "authorization",
            "audit",
            "log",
        ]

        if not any(keyword in description.lower() for keyword in security_keywords):
            # Also check for context from previous lines
            return None

        category = self.detect_category(description)
        severity = self.detect_severity(description, category)

        # Generate ID
        todo_id = f"TODO-{file_path.stem}-{line_num}"

        return SecurityTODO(
            id=todo_id,
            file=str(file_path.relative_to(self.root_path)),
            line=line_num,
            type=todo_type,
            category=category,
            severity=severity,
            description=description,
            code_snippet=line.strip()[:100],
        )

    def scan_file(self, file_path: Path) -> List[SecurityTODO]:
        """Scan a file for security TODOs."""
        todos = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                # Look for comment markers
                if any(
                    marker in line
                    for marker in [
                        "# TODO",
                        "# FIXME",
                        "# HACK",
                        "# XXX",
                        "# NOTE",
                        "// TODO",
                        "// FIXME",
                        "// HACK",
                        "// XXX",
                        "// NOTE",
                        "<!-- TODO",
                        "<!-- FIXME",
                    ]
                ):
                    todo = self.parse_todo_comment(line, file_path, i)
                    if todo:
                        todos.append(todo)

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")

        return todos

    def scan_all(self) -> None:
        """Scan all files for security TODOs."""
        print("🔍 Scanning for security-related TODOs...\n")

        files = self.find_all_files()
        print(f"Found {len(files)} files to scan\n")

        for file_path in files:
            todos = self.scan_file(file_path)
            self.todos.extend(todos)

        # Remove duplicates (same ID)
        seen_ids = set()
        unique_todos = []
        for todo in self.todos:
            if todo.id not in seen_ids:
                seen_ids.add(todo.id)
                unique_todos.append(todo)

        self.todos = unique_todos

        print(f"✅ Found {len(self.todos)} security-related TODOs\n")

    def load_tracker(self) -> None:
        """Load existing tracker data."""
        if not self.tracker_file.exists():
            return

        try:
            with open(self.tracker_file, "r") as f:
                data = json.load(f)

            # Load saved TODOs
            for todo_data in data.get("todos", []):
                todo = SecurityTODO(**todo_data)
                self.todos.append(todo)

        except Exception as e:
            print(f"⚠️  Error loading tracker: {e}")

    def save_tracker(self) -> None:
        """Save tracker data to file."""
        data = {
            "last_updated": datetime.now().isoformat(),
            "total_count": len(self.todos),
            "todos": [asdict(todo) for todo in self.todos],
        }

        with open(self.tracker_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_status(self, todo_id: str, status: str, assigned_to: str = "") -> bool:
        """Update status of a TODO item."""
        for todo in self.todos:
            if todo.id == todo_id:
                todo.status = status
                todo.updated_date = datetime.now().isoformat()
                if assigned_to:
                    todo.assigned_to = assigned_to
                self.save_tracker()
                return True

        return False

    def print_findings(self) -> None:
        """Print findings grouped by severity and category."""
        if not self.todos:
            print("✅ No security TODOs found!")
            return

        # Group by severity
        by_severity = defaultdict(list)
        for todo in self.todos:
            by_severity[todo.severity].append(todo)

        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        for severity in severity_order:
            todos = by_severity.get(severity, [])
            if not todos:
                continue

            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
            print(f"\n{emoji[severity]} {severity} SEVERITY ({len(todos)} items)")
            print("=" * 80)

            for todo in todos[:5]:  # Show first 5
                print(f"\n  {todo.id}")
                print(f"  📍 {todo.file}:{todo.line}")
                print(f"  📋 {todo.description}")
                print(
                    f"  🏷️  Category: {self.categories.get(todo.category, todo.category)}"
                )
                print(f"  ⚙️  Status: {todo.status}")

            if len(todos) > 5:
                print(f"\n  ... and {len(todos) - 5} more")

    def generate_report(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Security TODO Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"Total TODOs: {len(self.todos)}",
            "\n## Summary by Severity\n",
        ]

        # Count by severity
        severity_counts = defaultdict(int)
        for todo in self.todos:
            severity_counts[todo.severity] += 1

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                lines.append(f"- **{severity}:** {count} items")

        # Count by category
        lines.append("\n## Summary by Category\n")
        category_counts = defaultdict(int)
        for todo in self.todos:
            category_counts[todo.category] += 1

        for category, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                lines.append(
                    f"- **{self.categories.get(category, category)}:** {count} items"
                )

        # Detailed list
        lines.append("\n## Detailed TODOs\n")

        # Group by severity
        by_severity = defaultdict(list)
        for todo in self.todos:
            by_severity[todo.severity].append(todo)

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            todos = by_severity.get(severity, [])
            if not todos:
                continue

            lines.append(f"### {severity} ({len(todos)} items)\n")

            for todo in todos:
                lines.extend(
                    [
                        f"#### {todo.id}",
                        f"- **File:** {todo.file}:{todo.line}",
                        f"- **Category:** {self.categories.get(todo.category, todo.category)}",
                        f"- **Status:** {todo.status}",
                        f"- **Description:** {todo.description}",
                        f"- **Code:** `{todo.code_snippet}`",
                        "",
                    ]
                )

        # Recommendations
        lines.extend(
            [
                "## Recommendations\n",
                "1. **Address all CRITICAL and HIGH severity TODOs before production deployment**",
                "2. **Create dedicated tasks for each TODO in your project management tool**",
                "3. **Assign TODOs to specific developers with clear deadlines**",
                "4. **Add tests to prevent regressions of security issues**",
                "5. **Document security patterns in team documentation**",
                "",
                "## Tracking",
                "",
                "Track these TODOs in your project management system:",
                "- Export to CSV: `python scripts/security_todo_tracker.py --export`",
                "- Update status: `python scripts/security_todo_tracker.py --update-id TODO-xxx --status 'In Progress'`",
                "",
            ]
        )

        return "\n".join(lines)

    def export_csv(self) -> str:
        """Export TODOs to CSV format."""
        lines = [
            "ID,File,Line,Type,Category,Severity,Description,Status,AssignedTo,CreatedDate",
        ]

        for todo in self.todos:
            line = f'"{todo.id}","{todo.file}",{todo.line},{todo.type},{todo.category},{todo.severity},"{todo.description}",{todo.status},"{todo.assigned_to}",{todo.created_date}'
            lines.append(line)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Track and manage security-related TODOs"
    )
    parser.add_argument(
        "--path", default=".", help="Path to scan (default: current directory)"
    )
    parser.add_argument(
        "--find", action="store_true", help="Find and display all security TODOs"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed markdown report"
    )
    parser.add_argument("--export", action="store_true", help="Export to CSV format")
    parser.add_argument("--update-id", help="Update status of specific TODO by ID")
    parser.add_argument(
        "--status", help="New status (Open, In Progress, Completed, Deferred)"
    )
    parser.add_argument("--assigned-to", help="Assign TODO to someone")

    args = parser.parse_args()

    tracker = SecurityTODOTracker(args.path)

    # If updating, don't rescan
    if args.update_id:
        if not args.status:
            print("❌ Error: --status required when using --update-id")
            return 1

        success = tracker.update_status(
            args.update_id, args.status, args.assigned_to or ""
        )
        if success:
            print(f"✅ Updated {args.update_id} to status: {args.status}")
        else:
            print(f"❌ TODO {args.update_id} not found")
            return 1
        return 0

    # Default action is to scan
    tracker.scan_all()
    tracker.save_tracker()

    if args.find:
        tracker.print_findings()

    if args.report:
        report = tracker.generate_report()
        print(report)

    if args.export:
        csv = tracker.export_csv()
        print(csv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
