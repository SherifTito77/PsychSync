#!/usr/bin/env python3
"""
Incrementally fix B904 errors, processing only files without syntax errors first.
"""

import ast
import subprocess
import json
from pathlib import Path


def has_syntax_errors(file_path: Path) -> bool:
    """Check if a file has syntax errors."""
    try:
        ast.parse(file_path.read_text())
        return False
    except SyntaxError:
        return True


def main():
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

    # Separate files with and without syntax errors
    clean_files = []
    dirty_files = []

    for file_path_str in sorted(files_with_errors.keys()):
        file_path = Path(file_path_str)
        if has_syntax_errors(file_path):
            dirty_files.append(file_path_str)
        else:
            clean_files.append(file_path_str)

    print(f"Files without syntax errors: {len(clean_files)}")
    print(f"Files with syntax errors: {len(dirty_files)}\n")

    # Fix clean files using ruff --fix
    print("=== Fixing files without syntax errors ===\n")
    fixed_count = 0

    for file_path_str in clean_files:
        file_path = Path(file_path_str)
        error_count = len(files_with_errors[file_path_str])
        print(f"Fixing: {file_path} ({error_count} errors)")

        result = subprocess.run(
            ['ruff', 'check', str(file_path), '--select', 'B904', '--fix'],
            capture_output=True,
            text=True
        )

        # Validate syntax after fix
        if not has_syntax_errors(file_path):
            print(f"  ✓ Fixed successfully")
            fixed_count += 1
        else:
            print(f"  ⚠ Introduced syntax error, reverting...")
            # Revert using git
            subprocess.run(['git', 'checkout', '--', str(file_path)],
                         capture_output=True)

    print(f"\n=== Summary ===")
    print(f"Successfully fixed: {fixed_count}/{len(clean_files)} files")
    print(f"\nFiles with syntax errors (need manual fixing):")
    for f in dirty_files[:10]:
        error_count = len(files_with_errors[f])
        print(f"  - {f}: {error_count} errors")
    if len(dirty_files) > 10:
        print(f"  ... and {len(dirty_files) - 10} more")

    # Check remaining B904 errors
    print("\nVerifying remaining B904 errors...")
    result = subprocess.run(
        ['ruff', 'check', 'app/', '--select', 'B904', '--output-format=json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ All B904 errors in clean files fixed!")
        return 0
    else:
        errors = json.loads(result.stdout)
        print(f"Remaining B904 errors: {len(errors)}")
        return 1


if __name__ == '__main__':
    exit(main())
