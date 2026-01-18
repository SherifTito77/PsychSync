"""
Automated Import Migration Script
=================================

Migrates all imports from app.core.security to app.services.security

This script automatically updates Python files to use the new SOLID-compliant
security service architecture.

Usage:
    python scripts/migrate_security_imports.py

Author: Development Team
Version: 1.0 (Phase 2 - Service Layer Refactoring)
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set


# =============================================================================
# Configuration
# =============================================================================


# Import mapping: old_import_pattern -> replacement
# Order matters! More specific patterns should come first
IMPORT_MIGRATIONS: Dict[str, str] = {
    # Password functions
    "from app.services.security import get_password_hash":
        "from app.services.security import get_password_hash",
    "from app.services.security import verify_password":
        "from app.services.security import verify_password",
    "from app.services.security import validate_password":
        "from app.services.security import validate_password",

    # Token functions
    "from app.services.security import create_access_token":
        "from app.services.security import create_access_token",
    "from app.services.security import create_refresh_token":
        "from app.services.security import create_refresh_token",
    "from app.services.security import create_token_pair":
        "from app.services.security import create_token_pair",
    "from app.services.security import verify_token":
        "from app.services.security import verify_token",

    # Auth functions (FastAPI dependencies)
    "from app.services.security import get_current_user":
        "from app.services.security import get_current_user",
    "from app.services.security import get_current_active_user":
        "from app.services.security import get_current_active_user",

    # Authorization functions
    "from app.services.security import has_role":
        "from app.services.security import has_role",
    "from app.services.security import is_owner":
        "from app.services.security import is_owner",
    "from app.services.security import require_permissions":
        "from app.services.security import require_permissions",

    # Input sanitization functions
    "from app.services.security import sanitize_input":
        "from app.services.security import sanitize_input",
    "from app.services.security import escape_html":
        "from app.services.security import escape_html",
    "from app.services.security import validate_email":
        "from app.services.security import validate_email",
    "from app.services.security import validate_url":
        "from app.services.security import validate_url",
    "from app.services.security import validate_username":
        "from app.services.security import validate_username",

    # CSRF functions
    "from app.services.security import generate_csrf_token":
        "from app.services.security import generate_csrf_token",
    "from app.services.security import validate_csrf_token":
        "from app.services.security import validate_csrf_token",

    # Other utility functions
    "from app.services.security import generate_secure_token":
        "from app.services.security import generate_secure_token",
    "from app.services.security import constant_time_compare":
        "from app.services.security import constant_time_compare",
    "from app.services.security import hash_string":
        "from app.services.security import hash_string",
}

# Files and directories to exclude from migration
EXCLUDE_PATTERNS = [
    "*.backup*",
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "venv/",
    ".venv/",
    "env/",
    ".env/",
    "node_modules/",
    "migrations/",
    ".git/",
    "dist/",
    "build/",
    ".tox/",
    "coverage/",
    ".pytest_cache/",
]

# Files that should never be migrated
EXPLICIT_EXCLUDES = [
    "scripts/migrate_security_imports.py",  # Don't migrate self
    "scripts/verify_migration.py",  # Don't migrate verifier
    "PHASE2_IMPLEMENTATION_PLAN.md",  # Documentation
    "SOLID_REMEDIATION_IMPLEMENTATION.md",  # Documentation
]


# =============================================================================
# Helper Functions
# =============================================================================


def should_migrate_file(file_path: Path) -> bool:
    """
    Check if a file should be migrated.

    Args:
        file_path: Path to file to check

    Returns:
        True if file should be migrated, False otherwise
    """
    # Check explicit excludes
    if file_path.name in EXPLICIT_EXCLUDES:
        return False

    # Check exclude patterns
    file_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_str:
            return False

    # Only process Python files
    if file_path.suffix != ".py":
        return False

    # Skip __pycache__ directories
    if "__pycache__" in file_path.parts:
        return False

    return True


def migrate_single_line_imports(content: str) -> Tuple[str, int]:
    """
    Migrate single-line imports.

    Args:
        content: File content

    Returns:
        (updated_content, changes_count)
    """
    updated_content = content
    changes_count = 0

    for old_import, new_import in IMPORT_MIGRATIONS.items():
        if old_import in updated_content:
            updated_content = updated_content.replace(old_import, new_import)
            changes_count += 1

    return updated_content, changes_count


def migrate_multiline_imports(content: str) -> Tuple[str, int]:
    """
    Migrate multi-line imports from app.core.security.

    Handles:
        from app.services.security import (
get_password_hash,
            verify_password,
            ...
)

    Args:
        content: File content

    Returns:
        (updated_content, changes_count)
    """
    updated_content = content
    changes_count = 0

    # Pattern 1: from app.core.sefrom app.services.security import (
...
)attern_1 = r"from app\.core\.security import \(\s*(.*?)\s*\)"
    matches_1 = re.finditer(multiline_pattern_1, content, re.DOTALL)

    for match in matches_1:
        imported_items = match.group(1)
        new_import = f"from app.services.security import (\n{imported_items}\n)"
        updated_content = updated_content[:match.start()] + new_import + updated_content[match.end():]
        changes_count += 1

    # Pattern 2: from app.corfrom app.services.security import \
    mtern_2 = r"from app\.core\.security import \\(\s+.+?)"
    matches_2 = re.finditer(multiline_pattern_2, content, re.DOTALL)

    for match in matches_2:
        old_line = match.group(0)
        new_line = old_line.replace("from app.core.security import", "from app.services.security import")
        updated_content = updated_content[:match.start()] + new_line + updated_content[match.end():]
        changes_count += 1

    return updated_content, changes_count


def migrate_file(file_path: Path) -> Tuple[bool, int, List[str]]:
    """
    Migrate imports in a single file.

    Args:
        file_path: Path to file to migrate

    Returns:
        (was_modified, changes_count, changes_made)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        changes_made = []
        total_changes = 0

        # Migrate single-line imports
        content, single_line_changes = migrate_single_line_imports(content)
        if single_line_changes > 0:
            changes_made.append(f"Single-line imports: {single_line_changes}")
            total_changes += single_line_changes

        # Migrate multi-line imports
        content, multiline_changes = migrate_multiline_imports(content)
        if multiline_changes > 0:
            changes_made.append(f"Multi-line imports: {multiline_changes}")
            total_changes += multiline_changes

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, total_changes, changes_made

        return False, 0, []

    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return False, 0, []


def find_files_to_migrate(project_root: Path) -> List[Path]:
    """
    Find all Python files that should be migrated.

    Args:
        project_root: Root directory of project

    Returns:
        List of file paths to migrate
    """
    all_python_files = list(project_root.rglob("*.py"))
    files_to_migrate = [f for f in all_python_files if should_migrate_file(f)]

    return files_to_migrate


def print_summary(
    files_checked: int,
    files_migrated: int,
    total_changes: int,
    execution_time: float,
):
    """Print migration summary."""
    print("\n" + "=" * 70)
    print("🎉 MIGRATION SUMMARY")
    print("=" * 70)
    print(f"📊 Files checked:     {files_checked}")
    print(f"✅ Files migrated:    {files_migrated}")
    print(f"📝 Total changes:     {total_changes}")
    print(f"⏱️  Execution time:    {execution_time:.2f} seconds")
    print("=" * 70)

    if files_migrated > 0:
        success_rate = (files_migrated / files_checked) * 100 if files_checked > 0 else 0
        print(f"📈 Success rate:      {success_rate:.1f}%")

    print("\n" + "=" * 70)
    print("🚨 NEXT STEPS")
    print("=" * 70)
    print("1. Run verification script:")
    print("   python scripts/verify_migration.py")
    print()
    print("2. Check for any remaining old imports:")
    print("   grep -r 'from app.core.security import' --include='*.py' . | grep -v '.backup'")
    print()
    print("3. Run tests to ensure nothing broke:")
    print("   pytest tests/ -v --tb=short")
    print()
    print("4. Commit changes:")
    print("   git add .")
    print("   git commit -m 'feat: migrate to app.services.security'")
    print("=" * 70 + "\n")


# =============================================================================
# Main
# =============================================================================


def main():
    """Main migration function."""
    import time

    start_time = time.time()
    project_root = Path.cwd()

    print("=" * 70)
    print("🔧 SECURITY IMPORT MIGRATION SCRIPT")
    print("=" * 70)
    print(f"📁 Project root: {project_root}")
    print()

    # Find all files to migrate
    print("🔍 Scanning for Python files...")
    files_to_migrate = find_files_to_migrate(project_root)
    print(f"📝 Found {len(files_to_migrate)} Python files to check")
    print()

    if not files_to_migrate:
        print("⚠️  No files found to migrate!")
        return

    print("🔄 Migrating imports from app.core.security to app.services.security...")
    print("-" * 70)
    print()

    # Migrate each file
    migrated_count = 0
    total_changes = 0
    failed_files = []

    for file_path in files_to_migrate:
        was_modified, changes, changes_made = migrate_file(file_path)

        if was_modified:
            migrated_count += 1
            total_changes += changes
            relative_path = file_path.relative_to(project_root)

            # Print success message
            print(f"✅ {relative_path}")
            for change_desc in changes_made:
                print(f"   → {change_desc}")

        elif changes == -1:  # Error occurred
            failed_files.append(file_path)

    # Print failed files if any
    if failed_files:
        print()
        print("⚠️  Failed to migrate files:")
        for file_path in failed_files:
            relative_path = file_path.relative_to(project_root)
            print(f"   ❌ {relative_path}")

    # Calculate execution time
    execution_time = time.time() - start_time

    # Print summary
    print()
    print_summary(
        files_checked=len(files_to_migrate),
        files_migrated=migrated_count,
        total_changes=total_changes,
        execution_time=execution_time,
    )

    # Exit with appropriate code
    if failed_files:
        print(f"❌ Migration completed with {len(failed_files)} errors")
        sys.exit(1)
    else:
        print("✅ Migration completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
