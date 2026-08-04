#!/usr/bin/env python3
"""
Fix exception chains by adding 'from err' to raise statements in except blocks.

This script addresses B904 ruff errors:
"Within an `except` clause, raise exceptions with `raise ... from err`
or `raise ... from None` to distinguish them from errors in exception handling"

Usage:
    python scripts/fix_exception_chains.py [--file <path>] [--dry-run]

Examples:
    # Fix a single file
    python scripts/fix_exception_chains.py --file app/api/v1/endpoints/auth.py

    # Fix all Python files (interactive)
    python scripts/fix_exception_chains.py

    # Dry run to see what would be changed
    python scripts/fix_exception_chains.py --dry-run
"""

import argparse
import ast
import re
from pathlib import Path


def find_raise_without_from(content: str) -> list[dict]:
    """
    Find raise statements in except blocks that don't have 'from' clause.

    Returns:
        List of dicts with line number, exception name, and raise statement
    """
    issues = []

    # Pattern to match: except X as e: ... raise Y(...) without 'from'
    # This is a simplified regex-based approach for demonstration

    lines = content.split("\n")
    in_except_block = False
    exception_var = None
    indent_level = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        # Check if we're entering an except block
        if re.match(r"except\s+\w+\s+as\s+(\w+):", stripped):
            in_except_block = True
            exception_var = re.match(r"except\s+\w+\s+as\s+(\w+):", stripped).group(1)
            indent_level = current_indent
            continue

        # Check if we're leaving the except block (dedent)
        if in_except_block and stripped and current_indent <= indent_level:
            in_except_block = False
            exception_var = None

        # If we're in an except block, look for raise statements
        if in_except_block and re.match(r"raise\s+\w+Exception\(", stripped):
            # Check if this raise already has 'from'
            if " from " not in line and " from" not in line:
                issues.append(
                    {
                        "line": i,
                        "exception_var": exception_var,
                        "raise_line": line.strip(),
                        "indent": len(line) - len(stripped),
                    }
                )

    return issues


def fix_raise_statement(line: str, exception_var: str) -> str:
    """
    Add 'from exception_var' to a raise statement.

    Args:
        line: The original raise statement
        exception_var: The exception variable name from except clause

    Returns:
        Fixed line with 'from exception_var' added
    """
    # Find the closing parenthesis of the raise statement
    # and insert 'from exception_var' before it
    match = re.match(r"(raise\s+\w+Exception\([^)]*\))", line)
    if match:
        raise_part = match.group(1)
        return f"{raise_part} from {exception_var}"
    return line


def fix_file(file_path: Path, dry_run: bool = False) -> int:
    """
    Fix exception chains in a single file.

    Args:
        file_path: Path to the file to fix
        dry_run: If True, don't actually modify the file

    Returns:
        Number of fixes applied
    """
    content = file_path.read_text()
    issues = find_raise_without_from(content)

    if not issues:
        return 0

    if dry_run:
        print(f"\n{file_path}:")
        for issue in issues:
            print(f"  Line {issue['line']}: {issue['raise_line']}")
            print(f"    → Would add 'from {issue['exception_var']}'")
        return len(issues)

    # Apply fixes (reverse order to maintain line numbers)
    lines = content.split("\n")
    fixes_applied = 0

    for issue in reversed(issues):
        line_idx = issue["line"] - 1
        original_line = lines[line_idx]
        fixed_line = fix_raise_statement(original_line, issue["exception_var"])

        if fixed_line != original_line:
            lines[line_idx] = fixed_line
            fixes_applied += 1
            print(f"  Fixed line {issue['line']}: {original_line[:60]}...")

    # Write back
    file_path.write_text("\n".join(lines))
    return fixes_applied


def main():
    parser = argparse.ArgumentParser(
        description='Fix exception chains by adding "from err" to raise statements'
    )
    parser.add_argument(
        "--file", type=str, help="Specific file to fix (default: fix all files)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Ask before fixing each file"
    )

    args = parser.parse_args()

    if args.file:
        # Fix single file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {args.file}")
            return 1

        print(f"Checking {args.file} for B904 errors...")
        fixes = fix_file(file_path, dry_run=args.dry_run)

        if args.dry_run:
            print(f"\nFound {fixes} issues")
        else:
            print(f"\nApplied {fixes} fixes")

        return 0

    # Find all Python files with B904 errors
    print("Scanning for B904 errors...")
    import subprocess

    result = subprocess.run(
        ["ruff", "check", "app/", "--select", "B904", "--output-format=json"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ No B904 errors found!")
        return 0

    import json

    errors = json.loads(result.stdout)

    # Group errors by file
    files_with_errors = {}
    for error in errors:
        filename = error["filename"]
        if filename not in files_with_errors:
            files_with_errors[filename] = []
        files_with_errors[filename].append(error)

    print(f"\nFound {len(errors)} B904 errors in {len(files_with_errors)} files\n")

    # Fix each file
    total_fixes = 0
    for file_path_str, file_errors in files_with_errors.items():
        file_path = Path(file_path_str)

        if args.interactive:
            response = input(
                f"\nFix {len(file_errors)} errors in {file_path_str}? [y/N] "
            )
            if response.lower() != "y":
                continue

        print(f"\n{file_path_str}:")
        fixes = fix_file(file_path, dry_run=args.dry_run)
        total_fixes += fixes

    if args.dry_run:
        print(f"\n=== DRY RUN COMPLETE ===")
        print(f"Would fix {total_fixes} issues")
    else:
        print(f"\n=== FIXED {total_fixes} EXCEPTION CHAINS ===")

    return 0


if __name__ == "__main__":
    exit(main())
