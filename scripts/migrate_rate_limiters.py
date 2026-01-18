#!/usr/bin/env python3
"""
Rate Limiter Migration Script

Automatically updates imports and usage of old rate limiters to the new unified rate limiter.

Usage:
    python scripts/migrate_rate_limiters.py --dry-run  # Preview changes
    python scripts/migrate_rate_limiters.py            # Apply changes
    python scripts/migrate_rate_limiters.py --file app/api/v1/endpoints/users.py  # Migrate single file
"""

import argparse
import os
import re
import sys
from pathlib import Path


# Import mapping: old imports -> new imports
IMPORT_MAPPINGS = {
    r'from app\.middleware\.rate_limiter import': 'from app.core.rate_limiter_unified import',
    r'from app\.core\.rate_limiter import': 'from app.core.rate_limiter_unified import',
    r'from app\.core\.simple_rate_limiter import': 'from app.core.rate_limiter_unified import',
    r'from app\.core\.advanced_rate_limiter import': 'from app.core.rate_limiter_unified import',
}

# Decorator mappings
DECORATOR_MAPPINGS = {
    r'@RateLimiter\(': '@rate_limit(',
    r'@rate_limit\(max_requests=(\d+), window_seconds=(\+)\)': r'@rate_limit(limit=\1, window=\2)',
    r'rate_limit\(max_requests=(\d+), window_seconds=(\+)\)': r'rate_limit(limit=\1, window=\2)',
}

# Function call mappings
FUNCTION_MAPPINGS = {
    r'get_rate_limiter\(\)': 'unified_rate_limiter',
    r'init_rate_limiter\(': '# init_rate_limiter(  # TODO: Replace with UnifiedRateLimiter()',
    r'RateLimiter\(': 'UnifiedRateLimiter(',
}


def migrate_imports(content: str) -> tuple[str, list[str]]:
    """
    Update import statements to use unified rate limiter.

    Returns:
        tuple of (updated_content, list_of_changes)
    """
    changes = []
    new_content = content

    # Track which imports to add
    imports_to_add = set()

    # Check for old imports and replace them
    for old_pattern, new_import in IMPORT_MAPPINGS.items():
        if re.search(old_pattern, content):
            changes.append(f"Found old import pattern: {old_pattern}")
            new_content = re.sub(old_pattern, new_import, new_content)
            changes.append(f"  -> Replaced with: {new_import}")

    # Check for specific usage and add required imports
    if re.search(r'@rate_limit\(', new_content) or re.search(r'RateLimiter\(', new_content):
        if 'RateLimitStrategy' not in new_content:
            imports_to_add.update(['RateLimitStrategy'])
            changes.append("  -> Will add: RateLimitStrategy import")

    if re.search(r'UnifiedRateLimiter\(', new_content) or re.search(r'StorageBackend', new_content):
        if 'StorageBackend' not in new_content:
            imports_to_add.update(['StorageBackend'])
            changes.append("  -> Will add: StorageBackend import")

    if re.search(r'RateLimitConfig', new_content):
        if 'RateLimitConfig' not in new_content:
            imports_to_add.update(['RateLimitConfig'])
            changes.append("  -> Will add: RateLimitConfig import")

    # Add imports if needed
    if imports_to_add:
        # Find the import line and add missing imports
        import_match = re.search(r'from app\.core\.rate_limiter_unified import ([^\n]+)', new_content)
        if import_match:
            existing_imports = import_match.group(1)
            all_imports = existing_imports + ', ' + ', '.join(sorted(imports_to_add))
            new_content = re.sub(
                r'from app\.core\.rate_limiter_unified import [^\n]+',
                f'from app.core.rate_limiter_unified import {all_imports}',
                new_content
            )
            changes.append(f"  -> Added imports: {', '.join(imports_to_add)}")

    return new_content, changes


def migrate_decorators(content: str) -> tuple[str, list[str]]:
    """
    Update decorator usage to use new decorator parameters.

    Returns:
        tuple of (updated_content, list_of_changes)
    """
    changes = []
    new_content = content

    for old_pattern, new_replacement in DECORATOR_MAPPINGS.items():
        if re.search(old_pattern, content):
            matches = re.findall(old_pattern, content)
            for match in matches:
                changes.append(f"Found decorator: {match}")
            new_content = re.sub(old_pattern, new_replacement, new_content)
            changes.append(f"  -> Replaced with: {new_replacement}")

    return new_content, changes


def migrate_function_calls(content: str) -> tuple[str, list[str]]:
    """
    Update function calls to use new API.

    Returns:
        tuple of (updated_content, list_of_changes)
    """
    changes = []
    new_content = content

    for old_pattern, new_replacement in FUNCTION_MAPPINGS.items():
        if re.search(old_pattern, content):
            changes.append(f"Found function call: {old_pattern}")
            new_content = re.sub(old_pattern, new_replacement, new_content)
            changes.append(f"  -> Replaced with: {new_replacement}")

    return new_content, changes


def migrate_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Migrate a single file to use the unified rate limiter.

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        all_changes = []

        # Apply migrations
        content, import_changes = migrate_imports(content)
        all_changes.extend(import_changes)

        content, decorator_changes = migrate_decorators(content)
        all_changes.extend(decorator_changes)

        content, function_changes = migrate_function_calls(content)
        all_changes.extend(function_changes)

        # Check if anything changed
        if content != original_content:
            print(f"\n{'='*60}")
            print(f"File: {file_path}")
            print(f"{'='*60}")

            for change in all_changes:
                print(change)

            if dry_run:
                print("\n[DRY RUN] Would make these changes")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("\n✅ File updated successfully")

            return True

        return False

    except Exception as e:
        print(f"\n❌ Error processing {file_path}: {e}")
        return False


def find_files_to_migrate(root_dir: Path, single_file: str = None) -> list[Path]:
    """
    Find all Python files that import old rate limiters.

    Returns:
        List of file paths
    """
    if single_file:
        return [Path(single_file)]

    files_to_migrate = []

    # Search for files with old imports
    for root, dirs, files in os.walk(root_dir):
        # Skip common directories to ignore
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__',
            '.git',
            'venv',
            'env',
            'node_modules',
            '.pytest_cache',
            'comprehensive_sec_fix_backups',
            'api_sec_fix_backups',
            'payment_fix_backups',
            '*.egg-info',
        }]

        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check if file has old imports
                    for pattern in IMPORT_MAPPINGS.keys():
                        if re.search(pattern, content):
                            files_to_migrate.append(file_path)
                            break

                except Exception:
                    continue

    return files_to_migrate


def main():
    parser = argparse.ArgumentParser(
        description='Migrate rate limiter imports to unified rate limiter'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Migrate a single file instead of searching'
    )
    parser.add_argument(
        '--root',
        type=str,
        default='.',
        help='Root directory to search for files (default: current directory)'
    )

    args = parser.parse_args()

    root_dir = Path(args.root).resolve()

    # Find files to migrate
    print(f"🔍 Searching for files to migrate in {root_dir}...")
    files_to_migrate = find_files_to_migrate(root_dir, args.file)

    if not files_to_migrate:
        print("✅ No files found that need migration")
        return 0

    print(f"📝 Found {len(files_to_migrate)} file(s) to migrate")

    # Migrate files
    modified_count = 0
    for file_path in files_to_migrate:
        if migrate_file(file_path, args.dry_run):
            modified_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files scanned: {len(files_to_migrate)}")
    print(f"  Files to modify: {modified_count}")
    if args.dry_run:
        print(f"  ⚠️  DRY RUN - No files were modified")
        print(f"  Run without --dry-run to apply changes")
    print(f"{'='*60}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
