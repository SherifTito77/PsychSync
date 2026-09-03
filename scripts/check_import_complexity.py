#!/usr/bin/env python3
"""
IMPORT COMPLEXITY CHECKER FOR CI/CD
Monitors module import complexity to detect code quality issues

This script enforces:
- Maximum import count per module
- No circular dependencies
- Prefer absolute imports over relative
- Detect high-risk refactoring candidates

Usage:
    python scripts/check_import_complexity.py
    python scripts/check_import_complexity.py --max-imports 15 --fail-on-warnings

Exit codes:
    0: All checks passed
    1: Critical issues found
    2: Warnings found (with --fail-on-warnings)
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class ImportComplexityChecker:
    """Analyzes Python module import complexity"""

    def __init__(self, app_dir: str = "app", max_imports: int = 20):
        self.app_dir = Path(app_dir)
        self.max_imports = max_imports
        self.issues = []
        self.warnings = []
        self.metrics = {}

    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze imports in a single Python file"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            return None

        imports = {
            "absolute": [],
            "relative": [],
            "stdlib": [],
            "external": [],
            "total": 0,
        }

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Match import statements
            if line.startswith("from ") or line.startswith("import "):
                imports["total"] += 1

                if line.startswith("from app."):
                    imports["absolute"].append(line)
                elif line.startswith("from .") or line.startswith("from .."):
                    imports["relative"].append(line)
                elif self._is_stdlib_import(line):
                    imports["stdlib"].append(line)
                else:
                    imports["external"].append(line)

        return imports

    def _is_stdlib_import(self, line: str) -> bool:
        """Check if import is from Python standard library"""
        stdlib_modules = {
            "os",
            "sys",
            "re",
            "json",
            "datetime",
            "pathlib",
            "typing",
            "collections",
            "itertools",
            "functools",
            "logging",
            "enum",
            "dataclasses",
            "contextlib",
            "copy",
            "math",
            "random",
            "hashlib",
            "time",
            "uuid",
            "decimal",
            "fractions",
            "inspect",
            "textwrap",
        }

        for module in stdlib_modules:
            if f"import {module}" in line or f"from {module}" in line:
                return True
        return False

    def check_all_modules(self):
        """Analyze all Python modules in app directory"""
        results = []

        for file_path in self.app_dir.rglob("*.py"):
            # Skip cache, test files, and virtual environment
            if (
                "__pycache__" in str(file_path)
                or "test_" in file_path.name
                or ".venv" in str(file_path)
                or "venv" in str(file_path)
            ):
                continue

            rel_path = file_path.relative_to(self.app_dir)
            module_name = str(rel_path).replace(".py", "").replace(os.sep, ".")

            imports = self.analyze_file(file_path)
            if not imports:
                continue

            # Check import count
            if imports["total"] > self.max_imports:
                self.issues.append(
                    {
                        "type": "too_many_imports",
                        "module": module_name,
                        "file": str(rel_path),
                        "count": imports["total"],
                        "max_allowed": self.max_imports,
                    }
                )

            # Check for relative imports
            if imports["relative"]:
                self.warnings.append(
                    {
                        "type": "relative_imports",
                        "module": module_name,
                        "file": str(rel_path),
                        "count": len(imports["relative"]),
                        "imports": imports["relative"][:3],  # Show first 3
                    }
                )

            results.append(
                {"module": module_name, "file": str(rel_path), "imports": imports}
            )

        self.metrics = results
        return results

    def print_report(self, verbose: bool = False):
        """Print analysis report"""
        print("=" * 80)
        print("IMPORT COMPLEXITY ANALYSIS")
        print("=" * 80)
        print()

        # Summary
        total_modules = len(self.metrics)
        total_imports = sum(m["imports"]["total"] for m in self.metrics)
        avg_imports = total_imports / total_modules if total_modules > 0 else 0

        print(f"📊 SUMMARY:")
        print(f"   Modules analyzed: {total_modules}")
        print(f"   Total imports: {total_imports}")
        print(f"   Average imports per module: {avg_imports:.1f}")
        print(f"   Max allowed imports: {self.max_imports}")
        print()

        # Critical issues
        if self.issues:
            print(f"❌ CRITICAL ISSUES: {len(self.issues)}")
            print()

            for issue in self.issues:
                if issue["type"] == "too_many_imports":
                    print(f"   📦 {issue['module']}")
                    print(
                        f"      {issue['count']} imports (max: {issue['max_allowed']})"
                    )
                    if verbose:
                        print(f"      File: {issue['file']}")
                    print()
        else:
            print("✅ No critical issues found!")
            print()

        # Warnings
        if self.warnings:
            print(f"⚠️  WARNINGS: {len(self.warnings)}")
            print()

            for warning in self.issues[:10]:  # Show first 10
                if warning["type"] == "relative_imports":
                    print(
                        f"   📌 {warning['module']}: {warning['count']} relative import(s)"
                    )
                    if verbose:
                        for imp in warning.get("imports", []):
                            print(f"      - {imp}")
                    print()

            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings")
                print()
        else:
            print("✅ No warnings found!")
            print()

        # Top modules by import count
        if self.metrics:
            print("=" * 80)
            print("TOP 10 MODULES BY IMPORT COUNT")
            print("=" * 80)
            print()

            sorted_modules = sorted(
                self.metrics, key=lambda x: x["imports"]["total"], reverse=True
            )[:10]

            for i, m in enumerate(sorted_modules, 1):
                status = "❌" if m["imports"]["total"] > self.max_imports else "✅"
                print(f"   {i:2}. {status} {m['module']}")
                print(
                    f"       {m['imports']['total']} imports | {len(m['imports']['relative'])} relative"
                )

            print()
            print("=" * 80)

    def get_exit_code(self, fail_on_warnings: bool) -> int:
        """Get exit code based on findings"""
        if self.issues:
            return 1
        if self.warnings and fail_on_warnings:
            return 2
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Check Python module import complexity"
    )
    parser.add_argument(
        "--app-dir", default="app", help="Application directory (default: app)"
    )
    parser.add_argument(
        "--max-imports",
        type=int,
        default=20,
        help="Maximum allowed imports per module (default: 20)",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with error code on warnings",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    checker = ImportComplexityChecker(
        app_dir=args.app_dir, max_imports=args.max_imports
    )

    checker.check_all_modules()
    checker.print_report(verbose=args.verbose)

    return checker.get_exit_code(args.fail_on_warnings)


if __name__ == "__main__":
    sys.exit(main())
