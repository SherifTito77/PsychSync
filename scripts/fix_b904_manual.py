#!/usr/bin/env python3
"""
Carefully fix B904 errors by reading files and properly handling multi-line raise statements.
"""

import re
from pathlib import Path


def fix_file_carefully(file_path: Path) -> int:
    """
    Fix B904 errors in a file by carefully handling multi-line raise statements.
    """
    content = file_path.read_text()
    lines = content.split('\n')
    fixes = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for except blocks
        except_match = re.match(r'^(\s*)except\s+\w+\s+as\s+(\w+):', line)
        if except_match:
            indent = except_match.group(1)
            exception_var = except_match.group(2)

            # Look for raise statements within this except block
            j = i + 1
            while j < len(lines):
                next_line = lines[j]

                # Check if we've left the except block (dedent or empty line followed by dedent)
                if next_line.strip() and not next_line.startswith(indent + ' '):
                    break

                # Look for raise statement
                raise_match = re.match(r'^(\s*)raise\s+\w+Exception\(', next_line)
                if raise_match:
                    # Check if it already has 'from'
                    if ' from ' not in next_line and ' from' not in next_line:
                        # This might be a multi-line raise statement
                        # Find the closing parenthesis
                        raise_start = j
                        k = j
                        found_closing = False

                        # Scan forward to find the closing paren
                        open_parens = next_line.count('(') - next_line.count(')')
                        while k < len(lines):
                            open_parens += lines[k].count('(') - lines[k].count(')')
                            if open_parens == 0 and ')' in lines[k]:
                                found_closing = True
                                break
                            k += 1

                        if found_closing:
                            # Found the closing paren at line k
                            # Insert 'from exception_var' before the closing paren
                            closing_line = lines[k]
                            # Find the closing paren and insert before it
                            modified = re.sub(r'\)(\s*)$', f' from {exception_var})\\1', closing_line)
                            if modified != closing_line:
                                lines[k] = modified
                                fixes += 1
                                j = k + 1
                                continue

                j += 1

        i += 1

    if fixes > 0:
        file_path.write_text('\n'.join(lines))

    return fixes


def main():
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

        fixes = fix_file_carefully(file_path)
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

    if result.returncode == 0:
        print("✅ All B904 errors fixed!")
        return 0
    else:
        remaining = result.stdout.count('\n') if result.stdout else 0
        print(f"Remaining B904 errors: {remaining}")
        return 1


if __name__ == '__main__':
    exit(main())
