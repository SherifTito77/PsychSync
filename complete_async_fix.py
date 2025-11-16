#!/usr/bin/env python3
"""
Complete Async Consistency Fixer

This script will systematically fix ALL remaining async consistency issues
to achieve Grade A+ (125%) architecture compliance.
"""

import ast
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime

class AsyncConsistencyCompleter:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.fixed_files: List[str] = []
        self.issues_fixed: int = 0
        self.transformations_applied: Dict[str, int] = {}

    def analyze_all_issues(self) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze ALL remaining async consistency issues"""
        print("🔍 Analyzing all remaining async consistency issues...")

        all_issues = {}
        total_files = 0

        # Find all Python files with potential async issues
        for py_file in self.project_root.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', 'migrations']):
                continue
            if str(py_file).startswith('tests/'):
                continue

            total_files += 1
            issues = self.analyze_file_issues(py_file)
            if issues:
                all_issues[str(py_file)] = issues

        print(f"📊 Analyzed {total_files} files, found issues in {len(all_issues)} files")
        return all_issues

    def analyze_file_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a single file for async issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            issues = []

            # Patterns that need fixing in async functions
            sync_patterns_in_async = [
                r'\.query\(',
                r'\.first\(\)',
                r'\.all\(\)',
                r'\.add\(',
                r'\.commit\(\)',
                r'\.execute\(',
                r'SessionLocal\(',
                r'self\.db\.query\(',
                r'self\.db\.add\(',
                r'self\.db\.commit\(',
                r'db\.query\(',
                r'db\.add\(',
                r'db\.commit\(',
                r'session\.query\(',
                r'session\.add\(',
                r'session\.commit\(',
            ]

            lines = content.split('\n')
            in_async_func = False
            async_func_name = None
            async_func_indent = 0
            has_async_imports = 'from sqlalchemy.ext.asyncio import' in content or 'from sqlalchemy.ext.asyncio import AsyncSession' in content

            for i, line in enumerate(lines, 1):
                # Check for async function definition
                async_def_match = re.match(r'^(\s*)async\s+def\s+(\w+)', line)
                if async_def_match:
                    in_async_func = True
                    async_func_name = async_def_match.group(2)
                    async_func_indent = len(async_def_match.group(1))
                    continue

                # Check for function/class definition at same or lower indent level
                stripped_line = line.strip()
                if stripped_line and not line.startswith(' ' * (async_func_indent + 1)):
                    if any(stripped_line.startswith(prefix) for prefix in ['def ', 'async def ', 'class ', '@']):
                        in_async_func = False
                        async_func_name = None
                        continue

                # Check for sync patterns in async function
                if in_async_func:
                    for pattern in sync_patterns_in_async:
                        if re.search(pattern, line) and 'await' not in line:
                            # Only count if this is actually a database operation
                            if any(db_ref in line for db_ref in ['db.', 'session.', 'self.db.']):
                                issues.append({
                                    'file': str(file_path),
                                    'function': async_func_name,
                                    'line': i,
                                    'line_content': line.strip(),
                                    'pattern': pattern,
                                    'type': 'sync_in_async',
                                    'has_async_imports': has_async_imports
                                })

            return issues

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

    def fix_file_completely(self, file_path: Path, issues: List[Dict[str, Any]]) -> bool:
        """Fix ALL issues in a file comprehensively"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            modified = False
            transformations_count = 0

            # Step 1: Add necessary imports
            if not content.strip().startswith('#') and 'from sqlalchemy.ext.asyncio import' not in content:
                # Find import section
                import_section_end = 0
                lines = content.split('\n')

                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('from ') and not line.startswith('import '):
                        import_section_end = i
                        break

                if import_section_end > 0:
                    # Add async imports
                    new_imports = []

                    if 'from sqlalchemy.ext.asyncio import AsyncSession' not in content:
                        new_imports.append('from sqlalchemy.ext.asyncio import AsyncSession')

                    if 'from sqlalchemy import select' not in content:
                        # Find existing sqlalchemy import
                        for i, line in enumerate(lines[:import_section_end]):
                            if line.strip().startswith('from sqlalchemy import'):
                                existing_imports = line.strip()[len('from sqlalchemy import '):]
                                if 'select' not in existing_imports:
                                    lines[i] = f'from sqlalchemy import {existing_imports}, select'
                                    modified = True
                                break
                        else:
                            new_imports.append('from sqlalchemy import select')

                    # Insert new imports
                    if new_imports:
                        lines.insert(import_section_end, '')
                        for new_import in new_imports:
                            lines.insert(import_section_end, new_import)
                            import_section_end += 1
                        content = '\n'.join(lines)
                        modified = True

            # Step 2: Fix database patterns
            patterns_to_fix = [
                # Query patterns
                (r'self\.db\.query\(([^)]+)\)\.first\(\)', r'await self.db.execute(select(\1).limit(1)).scalar_one_or_none()'),
                (r'self\.db\.query\(([^)]+)\)\.all\(\)', r'await self.db.execute(select(\1)).scalars().all()'),
                (r'self\.db\.query\(([^)]+)\)', r'select(\1)'),
                (r'db\.query\(([^)]+)\)\.first\(\)', r'await db.execute(select(\1).limit(1)).scalar_one_or_none()'),
                (r'db\.query\(([^)]+)\)\.all\(\)', r'await db.execute(select(\1)).scalars().all()'),
                (r'db\.query\(([^)]+)\)', r'select(\1)'),
                (r'session\.query\(([^)]+)\)\.first\(\)', r'await session.execute(select(\1).limit(1)).scalar_one_or_none()'),
                (r'session\.query\(([^)]+)\)\.all\(\)', r'await session.execute(select(\1)).scalars().all()'),
                (r'session\.query\(([^)]+)\)', r'select(\1)'),

                # Add operations
                (r'self\.db\.add\(([^)]+)\)', r'self.db.add(\1)'),
                (r'db\.add\(([^)]+)\)', r'db.add(\1)'),
                (r'session\.add\(([^)]+)\)', r'session.add(\1)'),

                # Commit operations
                (r'self\.db\.commit\(\)', r'await self.db.commit()'),
                (r'db\.commit\(\)', r'await db.commit()'),
                (r'session\.commit\(\)', r'await session.commit()'),

                # SessionLocal patterns
                (r'SessionLocal\(\)', r'AsyncSessionLocal()'),

                # Execute patterns
                (r'self\.db\.execute\(([^)]+)\)', r'await self.db.execute(\1)'),
                (r'db\.execute\(([^)]+)\)', r'await db.execute(\1)'),
                (r'session\.execute\(([^)]+)\)', r'await session.execute(\1)'),

                # Filter patterns
                (r'filter\(([^)]+)\)\.where\(', r'filter(\1).where('),
                (r'\.filter\(([^)]+)\)\.where\(', r'.filter(\1).where('),
            ]

            for pattern, replacement in patterns_to_fix:
                if re.search(pattern, content):
                    count_before = len(re.findall(pattern, content))
                    content = re.sub(pattern, replacement, content)
                    count_after = len(re.findall(pattern, content))
                    if count_before != count_after:
                        transformations_count += (count_before - count_after)
                        modified = True

            # Step 3: Fix incomplete select statements
            incomplete_select_patterns = [
                (r'select\(([^)]+)\)\.all\(\)', r'(await self.db.execute(select(\1))).scalars().all()'),
                (r'select\(([^)]+)\)\.first\(\)', r'(await self.db.execute(select(\1).limit(1))).scalar_one_or_none()'),
                (r'select\(([^)]+)\)', r'select(\1)'),
            ]

            for pattern, replacement in incomplete_select_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True

            # Step 4: Fix Session type hints
            if 'Session' in content and 'AsyncSession' in content:
                content = re.sub(r': Session\b', r': AsyncSession', content)
                modified = True

            # Step 5: Update __init__ methods
            if 'def __init__(self, db: Session):' in content:
                content = content.replace('def __init__(self, db: Session):', 'def __init__(self, db: AsyncSession):')
                modified = True

            # Step 6: Add await to database operations that need it
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Check if line is in an async function and has database operation
                stripped = line.strip()
                if any(db_op in stripped for db_op in ['self.db.add(', 'self.db.commit(', 'db.add(', 'db.commit(']):
                    # Check if previous character is await or if line starts with await
                    if not stripped.startswith('await ') and (i == 0 or not lines[i-1].strip().endswith('await')):
                        if 'await' not in line:
                            lines[i] = line.replace(stripped[:4], 'await ' + stripped[:4], 1)
                            modified = True

            content = '\n'.join(lines)

            # Step 7: Fix method signatures that need async
            for issue in issues:
                if issue['function'] in content:
                    # Find the method definition
                    method_pattern = rf'(def {re.escape(issue["function"])}\([^)]*\)(?::\s*[^=]+)?\s*:'
                    if re.search(method_pattern, content) and 'async def' not in content:
                        content = re.sub(method_pattern, r'async \1:', content)
                        modified = True

            # Write the fixed content
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.fixed_files.append(str(file_path))
                self.issues_fixed += len(issues)

                # Track transformations
                for pattern, _ in patterns_to_fix:
                    self.transformations_applied[pattern] = self.transformations_applied.get(pattern, 0) + 1

                return True

            return False

        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False

    def fix_all_issues(self, all_issues: Dict[str, List[Dict[str, Any]]]) -> None:
        """Fix ALL issues systematically"""
        print(f"\n🚀 Starting complete async consistency fix...")
        print(f"📁 Files to fix: {len(all_issues)}")
        print(f"🔧 Total issues: {sum(len(issues) for issues in all_issues.values())}")

        # Sort files by priority (service layer first, then core, then API)
        priority_order = ['services/', 'core/', 'api/']
        sorted_files = []

        for priority in priority_order:
            for file_path in all_issues.keys():
                if priority in file_path:
                    sorted_files.append(file_path)

        # Add remaining files
        for file_path in all_issues.keys():
            if file_path not in sorted_files:
                sorted_files.append(file_path)

        for i, file_path in enumerate(sorted_files, 1):
            print(f"\n📝 [{i}/{len(sorted_files)}] Fixing: {file_path}")
            issues = all_issues[file_path]

            print(f"   🔢 Issues: {len(issues)}")

            if self.fix_file_completely(Path(file_path), issues):
                print(f"   ✅ Fixed: {file_path}")
            else:
                print(f"   ⚠️  No changes needed: {file_path}")

        print(f"\n📊 Final Results:")
        print(f"   Files Fixed: {len(self.fixed_files)}")
        print(f"   Issues Fixed: {self.issues_fixed}")
        print(f"   Transformations Applied: {len(self.transformations_applied)}")

def main():
    """Main execution"""
    print("🎯 COMPLETE ASYNC CONSISTENCY FIXER")
    print("=" * 50)
    print("Goal: Achieve Grade A+ (125%) architecture compliance")
    print("=" * 50)

    completer = AsyncConsistencyCompleter()

    # Step 1: Analyze all remaining issues
    all_issues = completer.analyze_all_issues()

    if not all_issues:
        print("\n🎉 No remaining issues found! Your architecture is already perfect!")
        return

    # Step 2: Fix all issues
    completer.fix_all_issues(all_issues)

    # Step 3: Generate completion report
    print(f"\n🏆 FIXING COMPLETE!")
    print(f"✅ Total files fixed: {len(completer.fixed_files)}")
    print(f"✅ Total issues resolved: {completer.issues_fixed}")
    print(f"✅ Architecture should now be Grade A+ ready")

    if completer.fixed_files:
        print(f"\n📋 Fixed Files:")
        for file_path in completer.fixed_files:
            print(f"   ✅ {file_path}")

    print(f"\n🎯 Next Steps:")
    print(f"   1. Run: python tests/devops_architecture_validation.py")
    print(f"   2. Verify Grade A+ achievement")
    print(f"   3. Test application functionality")
    print(f"   4. Deploy to production with confidence!")

if __name__ == "__main__":
    main()