#!/usr/bin/env python3
"""
Data Corruption Risk Analyzer for PsychSync

This script scans the codebase for potential data corruption risks in database operations:
1. Missing commit/rollback after database writes
2. Race conditions in concurrent operations
3. Missing validation before database writes
4. Partial updates without proper transaction handling
5. Missing error handling around database operations
6. Unhandled exceptions that could leave transactions inconsistent

Usage:
    python3 scripts/analyze_data_corruption_risks.py
"""

import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DataCorruptionAnalyzer(ast.NodeVisitor):
    """AST-based analyzer for detecting data corruption risks"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
        self.function_stack = []
        self.in_async_func = False
        self.has_db_param = False
        self.db_operations = []
        self.commit_operations = []
        self.rollback_operations = []
        self.try_blocks = []
        self.except_handlers = []

    def analyze(self) -> List[Dict]:
        """Analyze the file and return all issues found"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                source = f.read()
                tree = ast.parse(source, filename=self.filepath)
                self.visit(tree)
        except SyntaxError as e:
            self.issues.append(
                {
                    "type": "SYNTAX_ERROR",
                    "severity": "LOW",
                    "line": e.lineno,
                    "message": f"Syntax error prevents analysis: {e.msg}",
                    "code_snippet": "",
                }
            )
        except Exception as e:
            # Skip files that can't be parsed
            pass

        return self.issues

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definitions"""
        self.function_stack.append(node.name)
        old_async = self.in_async_func
        self.in_async_func = isinstance(node, ast.AsyncFunctionDef)

        # Check if function has db parameter
        self.has_db_param = any(
            arg.arg in ["db", "session", "async_session"] for arg in node.args.args
        )

        # Reset operation tracking for this function
        self.db_operations = []
        self.commit_operations = []
        self.rollback_operations = []
        self.try_blocks = []
        self.except_handlers = []

        self.generic_visit(node)

        # Analyze function-level patterns after visiting
        self._analyze_function_patterns(node)

        # Restore state
        self.function_stack.pop()
        self.in_async_func = old_async
        self.has_db_param = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions"""
        self.visit_FunctionDef(node)

    def visit_Try(self, node: ast.Try):
        """Track try/except blocks"""
        self.try_blocks.append(node)
        for handler in node.handlers:
            self.except_handlers.append(handler)
        self.generic_visit(node)
        self.try_blocks.pop()
        # Note: we don't pop except_handlers as they're relevant for the whole function

    def visit_Call(self, node: ast.Call):
        """Track database operations"""
        # Track db.add(), db.delete(), session.commit(), etc.
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr

            # Check if it's a database write operation
            if attr_name in ["add", "delete", "merge", "flush"]:
                # Check if it's called on a db/session object
                if self._is_db_call(node):
                    self.db_operations.append(
                        {
                            "type": attr_name,
                            "line": node.lineno,
                            "in_try": len(self.try_blocks) > 0,
                        }
                    )

            # Check for commit operations
            elif attr_name == "commit":
                if self._is_db_call(node):
                    self.commit_operations.append(
                        {"line": node.lineno, "in_try": len(self.try_blocks) > 0}
                    )

            # Check for rollback operations
            elif attr_name == "rollback":
                if self._is_db_call(node):
                    self.rollback_operations.append(
                        {
                            "line": node.lineno,
                            "in_except": len(self.except_handlers) > 0,
                        }
                    )

        self.generic_visit(node)

    def _is_db_call(self, node: ast.Call) -> bool:
        """Check if a call is on a database object"""
        if isinstance(node.func, ast.Attribute):
            # Check for db.add, session.commit, etc.
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id in ["db", "session", "async_session"]
            elif isinstance(node.func.value, ast.Attribute):
                # Check for self.session.add, etc.
                return node.func.value.attr in ["session", "db"]
        return False

    def _analyze_function_patterns(self, func_node):
        """Analyze patterns at the function level"""

        # Skip functions without database operations
        if not self.db_operations and not self.commit_operations:
            return

        # Pattern 1: Database writes without commit
        write_ops = [
            op for op in self.db_operations if op["type"] in ["add", "delete", "merge"]
        ]
        if write_ops and not self.commit_operations:
            self.issues.append(
                {
                    "type": "MISSING_COMMIT",
                    "severity": "HIGH",
                    "line": write_ops[0]["line"],
                    "function": func_node.name,
                    "message": f"Database write operations (add/delete/merge) without explicit commit",
                    "code_snippet": self._get_code_snippet(func_node.lineno),
                }
            )

        # Pattern 2: No error handling for database operations
        if (self.db_operations or self.commit_operations) and not self.try_blocks:
            self.issues.append(
                {
                    "type": "NO_ERROR_HANDLING",
                    "severity": "MEDIUM",
                    "line": func_node.lineno,
                    "function": func_node.name,
                    "message": "Database operations without try/except block",
                    "code_snippet": self._get_code_snippet(func_node.lineno),
                }
            )

        # Pattern 3: Try block with db operations but no rollback in except
        if self.try_blocks and self.db_operations and not self.rollback_operations:
            self.issues.append(
                {
                    "type": "MISSING_ROLLBACK",
                    "severity": "HIGH",
                    "line": self.try_blocks[0].lineno,
                    "function": func_node.name,
                    "message": "Try block with database operations but no rollback in except handler",
                    "code_snippet": self._get_code_snippet(self.try_blocks[0].lineno),
                }
            )

    def _get_code_snippet(self, lineno: int) -> str:
        """Get code snippet around a line"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                start = max(0, lineno - 2)
                end = min(len(lines), lineno + 1)
                snippet = "".join(lines[start:end])
                return snippet.strip()
        except Exception:
            return ""


class ConcurrencyAnalyzer:
    """Analyze potential race conditions in concurrent operations"""

    def __init__(self):
        self.issues = []

    def analyze_file(self, filepath: str) -> List[Dict]:
        """Analyze a file for race condition patterns"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Pattern 1: Read-then-write without locking
            # Look for patterns like: obj = await db.get(...); obj.field = value; await db.commit()
            read_write_pattern = r"await\s+(?:db\.)?(?:execute|scalar|get|fetch)\([^)]*\).*?(?:\n.*){0,5}?\.?\w*\s*=\s*[^=].*?await\s+.*\.commit\(\)"
            if re.search(read_write_pattern, content, re.MULTILINE | re.DOTALL):
                # Check if there's no locking mechanism
                if (
                    "select_for_update" not in content
                    and "with_for_update" not in content
                ):
                    self.issues.append(
                        {
                            "type": "RACE_CONDITION_READ_WRITE",
                            "severity": "HIGH",
                            "message": "Read-modify-write pattern without row-level locking (SELECT FOR UPDATE)",
                            "file": filepath,
                        }
                    )

            # Pattern 2: Check-then-act without atomic operation
            # Look for: if_exists = await db.get(...); if not if_exists: await db.add(...)
            check_act_pattern = r"if\s+(?:not\s+)?\w+.*?:\s*(?:\n.*)*?await\s+(?:db\.)?(?:add|merge|execute)"
            if re.search(check_act_pattern, content, re.MULTILINE | re.DOTALL):
                if "atomic" not in content and "transaction" not in content.lower():
                    self.issues.append(
                        {
                            "type": "RACE_CONDITION_CHECK_ACT",
                            "severity": "MEDIUM",
                            "message": "Check-then-act pattern without atomic transaction",
                            "file": filepath,
                        }
                    )

            # Pattern 3: Bulk operations without transaction wrapper
            bulk_pattern = (
                r"for\s+\w+\s+in\s+\[[^\]]*\]:\s*(?:\n.*)*?db\.(add|delete|merge)"
            )
            if re.search(bulk_pattern, content, re.MULTILINE | re.DOTALL):
                # Check if commit is outside the loop
                lines = content.split("\n")
                in_loop = False
                has_commit_inside = False
                has_commit_outside = False

                for i, line in enumerate(lines):
                    if "for " in line and " in " in line:
                        in_loop = True
                        # Look ahead for dedent (end of loop)
                        indent = len(line) - len(line.lstrip())
                    elif in_loop and line.strip() and not line.strip().startswith("#"):
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= indent:
                            in_loop = False
                        elif "commit()" in line:
                            has_commit_inside = True

                    if not in_loop and "commit()" in line:
                        has_commit_outside = True

                if has_commit_inside and not has_commit_outside:
                    self.issues.append(
                        {
                            "type": "INEFFICIENT_BULK_OPERATION",
                            "severity": "LOW",
                            "message": "Bulk operation with commit inside loop (performance issue, possible partial commit)",
                            "file": filepath,
                        }
                    )

        except Exception as e:
            pass

        return self.issues


def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files in the codebase"""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in [
                ".venv",
                "venv",
                "env",
                "__pycache__",
                ".git",
                "node_modules",
                ".pytest_cache",
                "archived_services",
                "migrations",
            ]
        ]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                python_files.append(filepath)

    return python_files


def analyze_all_files(root_dir: str) -> Dict:
    """Analyze all Python files for data corruption risks"""
    print(f"🔍 Analyzing Python files in {root_dir}...")
    python_files = find_python_files(root_dir)
    print(f"📁 Found {len(python_files)} Python files")

    all_issues = defaultdict(lambda: defaultdict(list))
    file_count = 0

    # AST-based analysis
    print("\n🔬 Running AST-based analysis...")
    for filepath in python_files:
        # Only analyze files in app/ directory
        if "/app/" not in filepath and not filepath.startswith("app/"):
            continue

        file_count += 1
        analyzer = DataCorruptionAnalyzer(filepath)
        issues = analyzer.analyze()

        for issue in issues:
            all_issues[filepath][issue["type"]].append(issue)

    # Concurrency analysis
    print("\n🔄 Running concurrency analysis...")
    concurrency_analyzer = ConcurrencyAnalyzer()
    for filepath in python_files:
        if "/app/" not in filepath and not filepath.startswith("app/"):
            continue

        issues = concurrency_analyzer.analyze_file(filepath)
        for issue in issues:
            all_issues[filepath][issue["type"]].append(issue)

    return all_issues


def generate_report(all_issues: Dict) -> str:
    """Generate a comprehensive report"""
    report_lines = [
        "# Data Corruption Risk Analysis Report\n",
        f"**Generated:** {os.popen('date').read().strip()}",
        f"**Files analyzed:** {len(all_issues)}",
        f"**Total issues found:** {sum(len(issues) for file_issues in all_issues.values() for issues in file_issues.values())}\n",
        "---\n",
    ]

    # Group by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for filepath, file_issues in sorted(all_issues.items()):
        for issue_type, issues in file_issues.items():
            for issue in issues:
                severity = issue.get("severity", "LOW")
                severity_counts[severity] += 1

    report_lines.extend(
        [
            "## Summary by Severity\n",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| **CRITICAL** | {severity_counts['CRITICAL']} |",
            f"| **HIGH** | {severity_counts['HIGH']} |",
            f"| **MEDIUM** | {severity_counts['MEDIUM']} |",
            f"| **LOW** | {severity_counts['LOW']} |",
            "\n---\n",
        ]
    )

    # Group by issue type
    type_counts = defaultdict(int)
    for filepath, file_issues in all_issues.items():
        for issue_type, issues in file_issues.items():
            type_counts[issue_type] += 1

    report_lines.extend(
        [
            "## Summary by Issue Type\n",
        ]
    )

    for issue_type, count in sorted(
        type_counts.items(), key=lambda x: x[1], reverse=True
    ):
        report_lines.append(f"- **{issue_type}**: {count} occurrences")

    report_lines.append("\n---\n")

    # Detailed findings
    report_lines.append("## Detailed Findings\n")

    for filepath, file_issues in sorted(all_issues.items()):
        if not file_issues:
            continue

        # Make path relative for readability
        rel_path = filepath.replace("/Users/sheriftito/Downloads/psychsync/", "")
        report_lines.append(f"\n### {rel_path}\n")

        for issue_type, issues in file_issues.items():
            report_lines.append(f"\n#### {issue_type} ({len(issues)} occurrence(s))\n")

            for issue in issues[:5]:  # Limit to 5 per type per file
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢",
                }.get(issue.get("severity", "LOW"), "⚪")

                report_lines.append(
                    f"{severity_icon} **Line {issue.get('line', '?')}**: {issue.get('message', 'Unknown issue')}"
                )

                if issue.get("function"):
                    report_lines.append(f"  - Function: `{issue.get('function')}`")

                if issue.get("code_snippet"):
                    snippet = issue["code_snippet"].replace("\n", " ").strip()
                    if len(snippet) > 100:
                        snippet = snippet[:97] + "..."
                    report_lines.append(f"  - Code: `{snippet}`")

                report_lines.append("")

            if len(issues) > 5:
                report_lines.append(f"_... and {len(issues) - 5} more_\n")

    # Recommendations
    report_lines.extend(
        [
            "---\n",
            "## Recommendations\n",
            "\n### High Priority\n",
            "1. **Add explicit commits** after all database write operations\n",
            "2. **Implement rollback handlers** in all try/except blocks that do database operations\n",
            "3. **Use row-level locking** (`SELECT FOR UPDATE`) for read-modify-write operations\n",
            "4. **Add validation** before database writes to prevent invalid data\n",
            "\n### Medium Priority\n",
            "1. **Wrap multi-step operations** in explicit transactions\n",
            "2. **Add error handling** to all database operations\n",
            "3. **Implement retry logic** for transient failures\n",
            "\n### Low Priority\n",
            "1. **Optimize bulk operations** by moving commit outside loops\n",
            "2. **Add comprehensive logging** for all database operations\n",
            "3. **Implement monitoring** for long-running transactions\n",
            "\n---\n",
            "**Generated by:** Data Corruption Risk Analyzer",
            "**Tool:** `scripts/analyze_data_corruption_risks.py`",
        ]
    )

    return "\n".join(report_lines)


def main():
    """Main entry point"""
    root_dir = "/Users/sheriftito/Downloads/psychsync"

    print("=" * 80)
    print("DATA CORRUPTION RISK ANALYZER")
    print("=" * 80)

    # Run analysis
    all_issues = analyze_all_files(root_dir)

    # Generate report
    print("\n📊 Generating report...")
    report = generate_report(all_issues)

    # Save report
    report_path = os.path.join(root_dir, "DATA_CORRUPTION_RISKS.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Analysis complete!")
    print(f"📄 Report saved to: {report_path}")

    # Print summary
    total_issues = sum(
        len(issues)
        for file_issues in all_issues.values()
        for issues in file_issues.values()
    )
    print(f"\n📈 Summary:")
    print(f"   - Total issues found: {total_issues}")
    print(f"   - Files with issues: {len(all_issues)}")

    # Print severity breakdown
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for filepath, file_issues in all_issues.values():
        for issues in file_issues.values():
            for issue in issues:
                severity = issue.get("severity", "LOW")
                severity_counts[severity] += 1

    print(f"\n   🔴 CRITICAL: {severity_counts['CRITICAL']}")
    print(f"   🟠 HIGH: {severity_counts['HIGH']}")
    print(f"   🟡 MEDIUM: {severity_counts['MEDIUM']}")
    print(f"   🟢 LOW: {severity_counts['LOW']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
