#!/usr/bin/env python3
"""
Fix syntax errors introduced by async conversion
"""

import re
from pathlib import Path

def fix_syntax_errors():
    """Fix common syntax errors from async conversion"""
    project_root = Path(__file__).parent

    syntax_fixes = [
        # Fix duplicate await statements
        {
            'pattern': r'await\s+await\s+db\.',
            'replacement': 'await db.',
            'description': 'Duplicate await statements'
        },

        # Fix malformed query results
        {
            'pattern': r'result\s*=\s*await\s+db\.execute\(.*?\)\s*return\s+result\.',
            'replacement': 'result = await db.execute(...)\n        return result.scalars().all()',
            'description': 'Malformed query result return'
        },

        # Fix malformed scalar returns
        {
            'pattern': r'return\s+result\.\w+\(\)',
            'replacement': 'return result.scalar()',
            'description': 'Malformed scalar return'
        },

        # Fix broken method signatures
        {
            'pattern': r'def\s+__init__\(\.\.\.db:\s*AsyncSession\.\.\.\):',
            'replacement': 'def __init__(self):',
            'description': 'Broken constructor signature'
        },

        # Fix duplicate imports
        {
            'pattern': r'from sqlalchemy\.ext\.asyncio import AsyncSession\s+from sqlalchemy\.ext\.asyncio import AsyncSession',
            'replacement': 'from sqlalchemy.ext.asyncio import AsyncSession',
            'description': 'Duplicate AsyncSession imports'
        },

        # Fix duplicate select imports
        {
            'pattern': r'from sqlalchemy import .*select.*select.*',
            'replacement': r'from sqlalchemy import select, func, and_, or_',
            'description': 'Duplicate select imports'
        },

        # Fix broken query assignments
        {
            'pattern': r'patterns\s*=\s*result\s*=\s*await\s+db\.execute\(.*?\)\s*return\s+result\.',
            'replacement': 'result = await db.execute(...)\n        patterns = result.scalars().all()',
            'description': 'Broken query assignment'
        },

        # Fix early return in query methods
        {
            'pattern': r'return\s+result\.\w+\(\)\s*\n\s*if\s+not\s+\w+:',
            'replacement': 'patterns = result.scalars().all()\n        \n        if not patterns:',
            'description': 'Early return before assignment'
        }
    ]

    files_fixed = 0
    total_fixes = 0

    for fix in syntax_fixes:
        print(f"🔧 Fixing: {fix['description']}")

        for py_file in project_root.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'migrations', 'node_modules']):
                continue
            if not any(service in str(py_file) for service in ['app/services/', 'app/api/']):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if re.search(fix['pattern'], content, re.MULTILINE | re.DOTALL):
                    new_content = re.sub(fix['pattern'], fix['replacement'], content, flags=re.MULTILINE | re.DOTALL)

                    if new_content != content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                        files_fixed += 1
                        total_fixes += 1
                        print(f"   ✅ Fixed: {py_file.relative_to(project_root)}")

            except Exception as e:
                print(f"   ❌ Error fixing {py_file}: {e}")

    print(f"\n🎯 Syntax error fixes complete!")
    print(f"   📁 Files fixed: {files_fixed}")
    print(f"   🔧 Total fixes: {total_fixes}")

    return files_fixed, total_fixes

if __name__ == "__main__":
    print("🚀 Fixing async syntax errors...")
    fix_syntax_errors()
    print("\n✅ Syntax error fixing complete!")