#!/usr/bin/env python3
"""
Comprehensive B904 fixer that handles syntax errors and adds 'from e' clauses.
Processes all files with proper error handling and validation.
"""

import ast
import json
import re
import subprocess
from pathlib import Path


def fix_common_syntax_errors(content: str) -> str:
    """Fix common syntax error patterns found in the codebase."""

    # Fix corrupted f-strings with extra parameters
    content = re.sub(
        r"\{str\((e|err|error|ex),\s*dependencies=\[Depends\([^)]+\)\]\)\}",
        r"str(\1)",
        content,
    )

    # Fix misplaced decorators in raise statements
    # Pattern: @check_rate_limit appearing inside a raise statement
    content = re.sub(
        r"(raise\s+\w+Exception\(\s*)\n\s*status_code=[^\n]+\n\n@check_rate_limit\([^)]+\)\s*\n\s+(detail=[^\n]+\n)",
        r"\1            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n            \2",
        content,
        flags=re.MULTILINE,
    )

    # Fix unterminated string literals (triple quotes)
    content = re.sub(r'f"([^"]*)$', r'f"\1"', content, flags=re.MULTILINE)
    content = re.sub(r"f'([^']*)$", r"f'\1'", content, flags=re.MULTILINE)

    # Fix misplaced decorator lines in general
    content = re.sub(r"\n\n(@check_rate_limit\([^)]+\))\s*\n\s+", r"\n\n", content)

    return content


def add_exception_chaining(content: str) -> str:
    """Add 'from e' to raise statements in except blocks."""

    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Check for except block
        except_match = re.match(r"^(\s*)except\s+\w+\s+as\s+(\w+):", line)
        if except_match:
            indent = except_match.group(1)
            exception_var = except_match.group(2)

            # Look for raise statements in this except block
            j = i + 1
            while j < len(lines):
                next_line = lines[j]

                # Check if we've left the except block
                if next_line.strip() and not next_line.startswith(indent + " " * 4):
                    break

                # Check for raise statement
                if re.match(r"^\s*raise\s+\w+Exception\(", next_line):
                    # Find the end of the raise statement
                    if ")" in next_line and not next_line.strip().endswith(","):
                        # Single-line raise
                        if " from " not in next_line:
                            # Add 'from exception_var' before closing paren
                            modified = re.sub(
                                r"\)(\s*)$", f" from {exception_var})\\1", next_line
                            )
                            result[-1] = modified
                    else:
                        # Multi-line raise - find closing paren
                        k = j
                        paren_count = next_line.count("(") - next_line.count(")")
                        while k < len(lines):
                            paren_count += lines[k].count("(") - lines[k].count(")")
                            if ")" in lines[k] and paren_count == 0:
                                # Add 'from exception_var' before closing paren
                                modified = re.sub(
                                    r"\)(\s*)$", f" from {exception_var})\\1", result[k]
                                )
                                result[k] = modified
                                break
                            k += 1

                j += 1

        i += 1

    return "\n".join(result)


def fix_file(file_path: Path) -> bool:
    """Fix all issues in a file. Returns True if successful."""

    try:
        content = file_path.read_text()

        # Step 1: Fix syntax errors
        content = fix_common_syntax_errors(content)

        # Validate syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            print(f"  ⚠ Syntax error not fixable: {e}")
            return False

        # Step 2: Add exception chaining
        content = add_exception_chaining(content)

        # Validate syntax again
        ast.parse(content)

        # Write back
        file_path.write_text(content)

        # Step 3: Apply ruff fix for any remaining simple cases
        subprocess.run(
            ["ruff", "check", str(file_path), "--select", "B904", "--fix", "--quiet"],
            capture_output=True,
        )

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    # Get all files with B904 errors
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
    fixed_count = 0
    for file_path_str in sorted(files_with_errors.keys()):
        file_path = Path(file_path_str)
        error_count = len(files_with_errors[file_path_str])
        print(f"Fixing: {file_path} ({error_count} errors)")

        # Backup
        backup = file_path.read_text()

        if fix_file(file_path):
            print(f"  ✓ Fixed")
            fixed_count += 1
        else:
            print(f"  ✗ Failed, reverting...")
            file_path.write_text(backup)

    print(f"\n=== Summary ===")
    print(f"Fixed: {fixed_count}/{len(files_with_errors)} files")

    # Verify
    print("\nVerifying...")
    result = subprocess.run(
        ["ruff", "check", "app/", "--select", "B904"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ All B904 errors fixed!")
        return 0
    else:
        errors = result.stdout.count("\n")
        print(f"Remaining B904 errors: {errors}")
        return 1


if __name__ == "__main__":
    exit(main())
