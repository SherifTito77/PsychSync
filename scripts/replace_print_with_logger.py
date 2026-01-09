#!/usr/bin/env python3
"""
Replace print() statements with logger.info() calls
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def has_logger_import(content: str) -> bool:
    """Check if file already has logger imported"""
    return bool(re.search(r'(import logging|from logging import|logger\s*=)', content))


def add_logger_import(content: str) -> str:
    """Add logging import at the top of the file"""
    # Find the first import statement
    import_match = re.search(r'^import .+', content, re.MULTILINE)
    if import_match:
        insert_pos = import_match.end()
        return (
            content[:insert_pos]
            + '\nimport logging\nlogger = logging.getLogger(__name__)'
            + content[insert_pos:]
        )
    return content


def convert_print_to_logger(file_path: Path) -> Tuple[int, int]:
    """
    Convert print() statements to logger.info() calls
    Returns: (number of replacements, file size before)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        original_size = len(content)
        replacements = 0

        # Pattern to match print() statements
        # Handles: print("text"), print('text'), print(f"text"), print(variable)
        print_pattern = r'print\(([^)]+)\)'

        def replace_print(match):
            nonlocal replacements
            replacements += 1
            args = match.group(1).strip()

            # Determine appropriate log level
            if 'error' in args.lower() or 'exception' in args.lower():
                return f'logger.error({args})'
            elif 'warn' in args.lower():
                return f'logger.warning({args})'
            elif 'debug' in args.lower():
                return f'logger.debug({args})'
            else:
                return f'logger.info({args})'

        # Skip test files and __init__ files
        if 'test_' in file_path.name or file_path.name == '__init__.py':
            return 0, original_size

        # Replace print statements
        content = re.sub(print_pattern, replace_print, content)

        # Only modify if replacements were made
        if content != original_content:
            # Add logger import if needed
            if not has_logger_import(original_content):
                content = add_logger_import(content)

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return replacements, original_size

        return 0, original_size

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}", file=sys.stderr)
        return 0, 0


def main():
    """Process all Python files in app/"""
    app_path = Path('app')

    if not app_path.exists():
        print("❌ app/ directory not found")
        sys.exit(1)

    total_replacements = 0
    files_modified = 0
    total_size_processed = 0

    # Find all Python files
    py_files = list(app_path.rglob('*.py'))
    py_files = [f for f in py_files if '__pycache__' not in str(f)]

    print(f"🔍 Processing {len(py_files)} Python files...")
    print()

    for py_file in py_files:
        replacements, size = convert_print_to_logger(py_file)
        if replacements > 0:
            files_modified += 1
            total_replacements += replacements
            total_size_processed += size
            print(f"✅ {py_file}: {replacements} replacements")

    print()
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   Files processed: {len(py_files)}")
    print(f"   Files modified: {files_modified}")
    print(f"   Total replacements: {total_replacements}")
    print(f"   Code size processed: {total_size_processed:,} bytes")
    print("=" * 60)

    if files_modified > 0:
        print()
        print("⚠️  IMPORTANT: Review the changes with:")
        print(f"   git diff app/")
        print()
        print("   Commit with:")
        print(f"   git add app/ && git commit -m 'refactor: replace print() with logger'")

if __name__ == '__main__':
    main()
