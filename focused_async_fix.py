#!/usr/bin/env python3
"""
Focused Async Fix - Target the most critical async/await patterns
"""

import re
from pathlib import Path

def apply_critical_fixes():
    """Apply the most critical async fixes"""
    project_root = Path(__file__).parent

    critical_fixes = [
        # Update Session imports to AsyncSession
        {
            'file_pattern': '*.py',
            'find': r'from sqlalchemy\.orm import Session',
            'replace': r'from sqlalchemy.ext.asyncio import AsyncSession',
            'files': ['app/services/']
        },

        # Add select import
        {
            'file_pattern': '*.py',
            'find': r'from sqlalchemy import (func, and_, or_)',
            'replace': r'from sqlalchemy import func, and_, or_, select',
            'files': ['app/services/']
        },

        # Fix method signatures
        {
            'file_pattern': '*.py',
            'find': r'def ([^(]+)\([^)]*db: Session[^)]*\):',
            'replace': r'def \1(...db: AsyncSession...):',
            'files': ['app/services/']
        },

        # Fix db.query patterns
        {
            'file_pattern': '*.py',
            'find': r'return db\.query\(([^)]+)\)\.filter\(([^)]+)\)\.order_by\([^)]+\)\.limit\([^)]+\)\.all\(\)',
            'replace': r'result = await db.execute(select(\1).where(\2).order_by(\1.created_at.desc()).limit(\3))\n        return result.scalars().all()',
            'files': ['app/services/']
        },

        # Fix simple db.query.all() patterns
        {
            'file_pattern': '*.py',
            'find': r'db\.query\(([^)]+)\)\.filter\(([^)]+)\)\.all\(\)',
            'replace': r'result = await db.execute(select(\1).where(\2))\n        return result.scalars().all()',
            'files': ['app/services/']
        },

        # Fix db.query.first() patterns
        {
            'file_pattern': '*.py',
            'find': r'db\.query\(([^)]+)\)\.filter\(([^)]+)\)\.first\(\)',
            'replace': r'result = await db.execute(select(\1).where(\2))\n        return result.scalar()',
            'files': ['app/services/']
        },

        # Fix db.add() and db.commit() patterns
        {
            'file_pattern': '*.py',
            'find': r'db\.add\(([^)]+)\)\s+db\.commit\(\)',
            'replace': r'db.add(\1)\n        await db.commit()',
            'files': ['app/services/', 'app/api/']
        },

        # Fix standalone db.commit()
        {
            'file_pattern': '*.py',
            'find': r'db\.commit\(\)',
            'replace': r'await db.commit()',
            'files': ['app/services/', 'app/api/']
        },

        # Fix db.refresh()
        {
            'file_pattern': '*.py',
            'find': r'db\.refresh\(([^)]+)\)',
            'replace': r'await db.refresh(\1)',
            'files': ['app/services/', 'app/api/']
        },

        # Fix db.rollback()
        {
            'file_pattern': '*.py',
            'find': r'db\.rollback\(\)',
            'replace': r'await db.rollback()',
            'files': ['app/services/', 'app/api/']
        }
    ]

    files_fixed = 0
    fixes_applied = 0

    for fix in critical_fixes:
        print(f"🔧 Applying: {fix['find'][:50]}...")

        for service_dir in fix['files']:
            search_path = project_root / service_dir
            if not search_path.exists():
                continue

            for py_file in search_path.rglob(fix['file_pattern']):
                if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'migrations']):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if re.search(fix['find'], content):
                        new_content = re.sub(fix['find'], fix['replace'], content)

                        if new_content != content:
                            with open(py_file, 'w', encoding='utf-8') as f:
                                f.write(new_content)

                            files_fixed += 1
                            fixes_applied += 1
                            print(f"   ✅ Fixed: {py_file.relative_to(project_root)}")

                except Exception as e:
                    print(f"   ❌ Error fixing {py_file}: {e}")

    print(f"\n🎯 Critical fixes complete!")
    print(f"   📁 Files fixed: {files_fixed}")
    print(f"   🔧 Fixes applied: {fixes_applied}")

    return files_fixed, fixes_applied

if __name__ == "__main__":
    print("🚀 Starting focused async consistency fixes...")
    apply_critical_fixes()
    print("\n✅ Focused async fixing complete!")