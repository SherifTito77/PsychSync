#!/usr/bin/env python3
"""
Fix Syntax Issues After Async Fixes

This script fixes syntax issues introduced by the async consistency fix script.
"""

import re
from pathlib import Path

def fix_syntax_issues():
    """Fix common syntax issues from async fixes"""

    files_to_fix = [
        "app/services/Analytics_service.py",
        "app/services/wellness_monitoring_service.py",
        "app/services/team_dynamics_service.py",
        "app/services/assessment_integration_service.py",
        "app/services/anonymous_feedback.py"
    ]

    project_root = Path(__file__).parent

    for file_path in files_to_fix:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        print(f"🔧 Fixing syntax in {file_path}...")

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix self.select(db) -> select(TableName)
        content = re.sub(r'self\.select\(db\)\.where\(([^)]+)\)\.filter\(', r'select(\1).filter(', content)
        content = re.sub(r'self\.select\(db\)\.where\(([^)]+)\)', r'await self.db.execute(select(\1))', content)
        content = re.sub(r'self\.select\(db\)\.filter\(([^)]+)\)', r'await self.db.execute(select(\1))', content)
        content = re.sub(r'self\.select\(db\)\.get\(([^)]+)\)', r'await self.db.get(\1)', content)

        # Fix incomplete query patterns
        content = re.sub(r'select\(([^)]+)\)\.all\(\)', r'(await self.db.execute(select(\1))).scalars().all()', content)
        content = re.sub(r'select\(([^)]+)\)\.first\(\)', r'(await self.db.execute(select(\1))).scalar_one_or_none()', content)

        # Fix .filter( followed by .where(
        content = re.sub(r'\.filter\(([^)]+)\)\.where\(', r'.filter(\1).where(', content)

        # Fix .add() and .commit() patterns
        content = re.sub(r'self\.db\.add\(([^)]+)\)', r'self.db.add(\1)', content)
        content = re.sub(r'self\.db\.refresh\(([^)]+)\)', r'await self.db.refresh(\1)', content)

        if content != original_content:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Fixed syntax issues in {file_path}")
        else:
            print(f"   ✅ No syntax issues found in {file_path}")

if __name__ == "__main__":
    fix_syntax_issues()
    print("\n🎯 Syntax fixing complete!")