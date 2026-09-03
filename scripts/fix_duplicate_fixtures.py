#!/usr/bin/env python3
"""
Fix duplicate @pytest.fixture decorators in test files.

This script removes duplicate @pytest.fixture decorators that were
accidentally applied to the same function multiple times.
"""

import re
from pathlib import Path


def fix_duplicate_fixture_decorators(file_path: Path) -> bool:
    """
    Remove duplicate @pytest.fixture decorators from a file.

    Returns True if changes were made, False otherwise.
    """
    content = file_path.read_text()

    # Pattern to match duplicate @pytest.fixture decorators
    # Matches: @pytest.fixture\n\n@pytest.fixture\ndef client(
    pattern = r"@pytest\.fixture\n\n@pytest\.fixture\n"

    # Replace single duplicate with single decorator
    fixed_content = re.sub(pattern, "@pytest.fixture\n", content)

    if fixed_content != content:
        file_path.write_text(fixed_content)
        return True
    return False


def main():
    """Fix all test files with duplicate fixtures."""
    tests_dir = Path("tests/api")

    # Find all Python files in tests/api
    test_files = list(tests_dir.glob("test_*.py"))

    fixed_count = 0

    for test_file in test_files:
        if fix_duplicate_fixture_decorators(test_file):
            print(f"✅ Fixed: {test_file.name}")
            fixed_count += 1

    print(f"\n🎉 Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
