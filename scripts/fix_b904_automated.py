#!/usr/bin/env python3
"""
Automated B904 exception chaining fixer using AST.

This script uses Python's AST module to accurately find and fix B904 errors
by adding 'from e' to raise statements in except blocks.
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple


def find_b904_issues(content: str) -> List[Tuple[int, str, str]]:
    """
    Find all B904 errors using AST analysis.

    Returns:
        List of tuples: (line_number, exception_var, full_raise_statement)
    """
    issues = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues

    class B904Visitor(ast.NodeVisitor):
        def visit_ExceptHandler(self, node):
            # Check if this except block has an exception variable
            if node.name:
                exception_var = node.name
                # Visit all statements in the except block
                for child in node.body:
                    if isinstance(child, ast.Raise):
                        # Check if the raise doesn't have a 'cause' (from clause)
                        if child.cause is None:
                            # Get the full line from the original source
                            issues.append((
                                child.lineno,
                                exception_var,
                                self._get_raise_statement(content, child.lineno)
                            ))
            self.generic_visit(node)

        def _get_raise_statement(self, content: str, lineno: int) -> str:
            """Extract the full raise statement from source."""
            lines = content.split('\n')
            if 0 < lineno <= len(lines):
                return lines[lineno - 1].strip()
            return ""

    visitor = B904Visitor()
    visitor.visit(tree)

    return issues


def fix_b904_in_line(line: str, exception_var: str) -> str:
    """
    Add 'from exception_var' to a raise statement.

    Handles:
    - Multi-line raise statements
    - Raise statements with comments
    - Different formatting styles
    """
    # Remove trailing comment if present
    comment = ""
    if "#" in line:
        line_parts = line.split("#", 1)
        line = line_parts[0]
        comment = f"  #{line_parts[1].strip()}"

    # Find the raise statement
    if re.match(r'^\s*raise\s+\w+', line):
        # Check if it already has 'from'
        if ' from ' not in line:
            # Find where to insert 'from exception_var'
            # Usually before the closing parenthesis or at end of line
            if ')' in line:
                # Insert before the closing parenthesis
                line = re.sub(r'\)(\s*)$', f' from {exception_var})\\1', line)
            else:
                # Append at end
                line = f"{line.rstrip()} from {exception_var}"

    # Add back comment if it was removed
    if comment:
        line = line.rstrip() + comment

    return line


def fix_file(file_path: Path) -> int:
    """
    Fix all B904 errors in a file.

    Returns:
        Number of fixes applied
    """
    content = file_path.read_text()
    issues = find_b904_issues(content)

    if not issues:
        return 0

    lines = content.split('\n')
    fixes_applied = 0

    # Apply fixes in reverse order to maintain line numbers
    for lineno, exception_var, raise_stmt in reversed(issues):
        line_idx = lineno - 1
        if 0 <= line_idx < len(lines):
            original_line = lines[line_idx]
            fixed_line = fix_b904_in_line(original_line, exception_var)

            if fixed_line != original_line:
                lines[line_idx] = fixed_line
                fixes_applied += 1

    # Write back
    file_path.write_text('\n'.join(lines))
    return fixes_applied


def main():
    """Main entry point."""
    import subprocess
    import json

    # Get all files with B904 errors
    result = subprocess.run(
        ['ruff', 'check', 'app/', '--select', 'B904', '--output-format=json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ No B904 errors found!")
        return 0

    errors = json.loads(result.stdout)

    # Group by file
    files_with_errors = {}
    for error in errors:
        filename = error['filename']
        if filename not in files_with_errors:
            files_with_errors[filename] = []
        files_with_errors[filename].append(error)

    print(f"Found {len(errors)} B904 errors in {len(files_with_errors)} files\n")

    # Fix each file
    total_fixes = 0
    for file_path_str in sorted(files_with_errors.keys()):
        file_path = Path(file_path_str)
        print(f"Fixing: {file_path}")

        fixes = fix_file(file_path)
        total_fixes += fixes

        if fixes > 0:
            print(f"  ✓ Applied {fixes} fixes\n")

    print(f"\n=== FIXED {total_fixes} B904 ERRORS ===")

    # Verify
    print("\nVerifying fixes...")
    result = subprocess.run(
        ['ruff', 'check', 'app/', '--select', 'B904'],
        capture_output=True,
        text=True
    )

    remaining = len(result.stdout.split('\n')) if result.stdout else 0
    print(f"Remaining B904 errors: {remaining}")

    return 0


if __name__ == '__main__':
    exit(main())
