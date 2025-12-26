#!/usr/bin/env python3
"""
Fix UTF-8 encoding errors in Python files
"""

import os
import sys
from pathlib import Path

# Files with encoding issues
FILES_TO_FIX = [
    "app/services/alerts_service.py",
    "app/services/apm_service.py",
    "app/services/deployment_service.py",
    "app/services/performance_monitoring_service.py"
]

def fix_file_encoding(file_path: Path) -> bool:
    """Fix encoding issues in a file"""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None
        encoding_used = None

        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                encoding_used = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            print(f"❌ Could not decode {file_path}")
            return False

        # Write back as UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Fixed {file_path} (was: {encoding_used})")
        return True

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    project_root = Path(os.path.dirname(os.path.abspath(__file__)))

    print("🔧 Fixing UTF-8 encoding issues...")
    print("=" * 60)

    fixed = 0
    failed = 0

    for file_rel in FILES_TO_FIX:
        file_path = project_root / file_rel

        if not file_path.exists():
            print(f"⚠️  File not found: {file_rel}")
            continue

        if fix_file_encoding(file_path):
            fixed += 1
        else:
            failed += 1

    print()
    print("=" * 60)
    print(f"Fixed: {fixed}, Failed: {failed}")

    if fixed > 0:
        print("\n✅ Encoding fixed! Files can now be read properly.")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
