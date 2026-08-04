#!/usr/bin/env python3
"""
Fix JSONB imports across the codebase for cross-database compatibility.

Replaces PostgreSQL-specific JSONB with the dialect-agnostic JSONType from app.db.types
"""

import os
import re
from pathlib import Path

# Files to process
TARGET_DIRS = [
    "app/db/models",
    "app/services",
    "alembic/versions",
]

# Skip files/directories
SKIP_PATTERNS = [
    "__pycache__",
    ".pyc",
    "backup",
    ".backup",
    "types.py",  # Don't modify our new types file
]


def should_process_file(filepath: Path) -> bool:
    """Check if file should be processed."""
    # Check skip patterns
    for pattern in SKIP_PATTERNS:
        if pattern in str(filepath):
            return False

    # Only process Python files
    if not filepath.suffix == ".py":
        return False

    return True


def fix_jsonb_imports(content: str) -> tuple[str, int]:
    """
    Fix JSONB imports in file content.

    Returns:
        tuple: (fixed_content, number_of_changes)
    """
    changes = 0
    original_content = content

    # Pattern 1: from sqlalchemy.dialects.postgresql import ... JSONB
    # Capture everything before JSONB to preserve other imports
    pattern1 = r"from sqlalchemy\.dialects\.postgresql import ([^\n]*?)JSONB"

    def replace_import1(match):
        nonlocal changes
        changes += 1
        other_imports = match.group(1).strip()
        if other_imports and other_imports != ",":
            # Keep other imports from postgresql dialect
            if other_imports.endswith(","):
                other_imports = other_imports[:-1].strip()
            return f"from sqlalchemy.dialects.postgresql import {other_imports}\nfrom app.db.types import JSONType as JSON"
        else:
            # Only JSONB was imported
            return "from app.db.types import JSONType as JSON"

    content = re.sub(pattern1, replace_import1, content, flags=re.MULTILINE)

    # Pattern 2: Direct JSONB column usage
    # sa.Column(JSONB, ...) -> sa.Column(JSON, ...)
    # Column(JSONB, ...) -> Column(JSON, ...)
    # Note: We use 'JSON' as the alias in imports above
    content = content.replace(" Column(JSONB", " Column(JSON")
    content = content.replace("Column(JSONB", " Column(JSON")
    content = content.replace(" Column(JSON", " Column(JSONType")
    content = content.replace("Column(JSON", "Column(JSONType")

    # Count replacements
    changes += original_content.count("JSONB") - content.count("JSONB")

    return content, changes


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent

    total_files = 0
    total_changes = 0

    for target_dir in TARGET_DIRS:
        dir_path = root_dir / target_dir
        if not dir_path.exists():
            print(f"⚠️  Skipping non-existent directory: {target_dir}")
            continue

        # Process all Python files in directory
        for py_file in dir_path.rglob("*.py"):
            if not should_process_file(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    original_content = f.read()

                # Check if file contains JSONB
                if "JSONB" not in original_content:
                    continue

                # Fix the file
                fixed_content, changes = fix_jsonb_imports(original_content)

                if changes > 0:
                    # Write back
                    with open(py_file, "w", encoding="utf-8") as f:
                        f.write(fixed_content)

                    print(
                        f"✅ Fixed {py_file.relative_to(root_dir)} ({changes} changes)"
                    )
                    total_files += 1
                    total_changes += changes
                else:
                    print(
                        f"⏭️  Skipped {py_file.relative_to(root_dir)} (no changes needed)"
                    )

            except Exception as e:
                print(f"❌ Error processing {py_file}: {e}")

    print(f"\n{'='*60}")
    print(f"✨ Summary: {total_files} files updated, {total_changes} total changes")
    print(f"{'='*60}")

    if total_files > 0:
        print("\n✅ JSONB imports successfully migrated to JSONType!")
        print("📝 Note: Tests should now work on SQLite and PostgreSQL.")
    else:
        print("\n✅ No files needed updating!")


if __name__ == "__main__":
    main()
