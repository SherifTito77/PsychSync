#!/usr/bin/env python3
"""
Safely fix B904 errors by processing files individually and validating syntax.
"""

import ast
import json
import subprocess
from pathlib import Path


def validate_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        ast.parse(file_path.read_text())
        return True
    except SyntaxError:
        return False


def fix_file_with_ruff(file_path: Path) -> bool:
    """
    Fix a single file using ruff --fix, validating syntax afterwards.
    Returns True if successful, False if syntax errors occurred.
    """
    # Backup the original
    original_content = file_path.read_text()

    # Try to fix with ruff
    result = subprocess.run(
        ["ruff", "check", str(file_path), "--select", "B904", "--fix"],
        capture_output=True,
        text=True,
    )

    # Validate syntax
    if not validate_syntax(file_path):
        print(f"  ⚠ Syntax error after fix, reverting...")
        file_path.write_text(original_content)
        return False

    return True


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

    # Fix each file individually
    success_count = 0
    failed_files = []

    for file_path_str in sorted(files_with_errors.keys()):
        file_path = Path(file_path_str)
        error_count = len(files_with_errors[file_path_str])
        print(f"Fixing: {file_path} ({error_count} errors)")

        if fix_file_with_ruff(file_path):
            print(f"  ✓ Fixed successfully")
            success_count += 1
        else:
            print(f"  ✗ Failed - needs manual fixing")
            failed_files.append(file_path_str)

    print(f"\n=== SUMMARY ===")
    print(f"Successfully fixed: {success_count}/{len(files_with_errors)} files")
    if failed_files:
        print(f"\nFailed files ({len(failed_files)}):")
        for f in failed_files:
            print(f"  - {f}")

    # Verify remaining errors
    print("\nVerifying remaining B904 errors...")
    result = subprocess.run(
        ["ruff", "check", "app/", "--select", "B904", "--output-format=json"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ All B904 errors fixed!")
        return 0
    else:
        errors = json.loads(result.stdout)
        print(f"Remaining B904 errors: {len(errors)}")
        return 1


if __name__ == "__main__":
    exit(main())
