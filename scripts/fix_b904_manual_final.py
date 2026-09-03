#!/usr/bin/env python3
"""
Manually fix B904 errors by properly handling multi-line raise statements.
This script parses the source code and adds 'from e' before closing parentheses.
"""

import re
from pathlib import Path


def fix_multiline_raises(content: str) -> str:
    """
    Fix multi-line raise statements in except blocks by adding 'from e'
    before the closing parenthesis.
    """
    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Check if this line starts an except block
        except_match = re.match(r"^(\s*)except\s+\w+\s+as\s+(\w+):", line)
        if except_match:
            indent = except_match.group(1)
            exception_var = except_match.group(2)

            # Look for raise statements in the except block
            j = i + 1
            while j < len(lines):
                next_line = lines[j]

                # Check if we've left the except block
                if next_line.strip() and not next_line.startswith(indent + "    "):
                    break

                # Check if this line starts a raise statement
                raise_start = re.match(r"^(\s*)raise\s+\w+Exception\(", next_line)
                if raise_start and " from " not in next_line:
                    # This is a raise statement - find where it ends
                    # Check if it's multi-line
                    if ")" not in next_line or next_line.strip().endswith(","):
                        # Multi-line raise statement
                        # Find the closing paren
                        k = j
                        paren_count = next_line.count("(") - next_line.count(")")
                        while k < len(lines):
                            paren_count += lines[k].count("(") - lines[k].count(")")
                            if ")" in lines[k] and paren_count == 0:
                                # Found the closing line
                                closing_line = result[
                                    k
                                ]  # Use result to get our modified version
                                # Add 'from exception_var' before the closing paren
                                modified = re.sub(
                                    r"\)(\s*)$",
                                    f" from {exception_var})\\1",
                                    closing_line,
                                )
                                result[k] = modified
                                break
                            k += 1
                    else:
                        # Single-line raise statement
                        if " from " not in next_line and " from" not in next_line:
                            # Add 'from exception_var' before closing paren
                            modified = re.sub(
                                r"\)(\s*)$", f" from {exception_var})\\1", next_line
                            )
                            result[-1] = modified  # Replace the line we just added

                j += 1

        i += 1

    return "\n".join(result)


def main():
    import ast
    import subprocess
    import sys

    # Get list of files that still have B904 errors
    result = subprocess.run(
        ["ruff", "check", "app/", "--select", "B904", "--output-format=json"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ No B904 errors found!")
        return 0

    errors = json.loads(result.stdout)

    # Group by file
    files_with_errors = {}
    for error in errors:
        filename = error["filename"]
        if filename not in files_with_errors:
            files_with_errors[filename] = []
        files_with_errors[filename].append(error)

    print(f"Found {len(errors)} B904 errors in {len(files_with_errors)} files\n")

    # Fix each file
    for file_path_str in sorted(files_with_errors.keys()):
        file_path = Path(file_path_str)
        print(f"Fixing: {file_path}")

        try:
            content = file_path.read_text()
            fixed_content = fix_multiline_raises(content)

            # Validate syntax
            try:
                ast.parse(fixed_content)
                file_path.write_text(fixed_content)
                print(f"  ✓ Fixed")
            except SyntaxError as e:
                print(f"  ✗ Syntax error: {e}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Verify
    print("\nVerifying...")
    result = subprocess.run(
        ["ruff", "check", "app/", "--select", "B904"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ All B904 errors fixed!")
        return 0
    else:
        print(f"Remaining errors: {result.stdout.count(chr(10))}")
        return 1


if __name__ == "__main__":
    import json

    exit(main())
