#!/usr/bin/env python3
"""
Async Consistency Fix Script

This script systematically fixes async/sync consistency issues in the PsychSync codebase.
It focuses on the most critical patterns that are causing architecture validation failures.
"""

import asyncio
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

class AsyncConsistencyFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.fixed_files = []
        self.issues_found = []

    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a Python file for async/sync issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            issues = []

            # Find async functions with sync database operations
            sync_patterns_in_async = [
                r'\.query\(',
                r'\.add\(',
                r'\.commit\(',
                r'\.execute\(',
                r'SessionLocal\(\)'
            ]

            lines = content.split('\n')
            in_async_func = False
            async_func_name = None
            async_func_indent = 0

            for i, line in enumerate(lines, 1):
                # Check for async function definition
                async_def_match = re.match(r'^(\s*)async\s+def\s+(\w+)', line)
                if async_def_match:
                    in_async_func = True
                    async_func_name = async_def_match.group(2)
                    async_func_indent = len(async_def_match.group(1))
                    continue

                # Check for function/class definition at same or lower indent level
                if line.strip() and not line.startswith(' ' * (async_func_indent + 1)):
                    if any(line.strip().startswith(prefix) for prefix in ['def ', 'async def ', 'class ', '@']):
                        in_async_func = False
                        async_func_name = None
                        continue

                # Check for sync patterns in async function
                if in_async_func:
                    for pattern in sync_patterns_in_async:
                        if re.search(pattern, line) and 'await' not in line:
                            issues.append({
                                'file': str(file_path),
                                'function': async_func_name,
                                'line': i,
                                'line_content': line.strip(),
                                'pattern': pattern,
                                'type': 'sync_in_async'
                            })

            return issues

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

    def fix_database_operations(self, file_path: Path, issues: List[Dict[str, Any]]) -> bool:
        """Fix database operations in async functions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            modified = False

            # Common replacements for async database operations
            replacements = {
                r'(\w+)\.query\(([^)]+)\)\.first\(\)': r'await self.db.execute(select(\1).where(\2).limit(1)).scalar_one_or_none()',
                r'(\w+)\.query\(([^)]+)\)\.all\(\)': r'await self.db.execute(select(\1).where(\2)).scalars().all()',
                r'(\w+)\.query\(([^)]+)\)': r'select(\1).where(\2)',
                r'SessionLocal\(\)': r'AsyncSessionLocal()',
                r'self\.db\.add\(([^)]+)\)': r'self.db.add(\1)',
                r'self\.db\.commit\(\)': r'await self.db.commit()',
                r'self\.db\.refresh\(([^)]+)\)': r'await self.db.refresh(\1)',
            }

            for issue in issues:
                if issue['line'] - 1 < len(lines):
                    line = lines[issue['line'] - 1]
                    original_line = line

                    # Apply replacements
                    for pattern, replacement in replacements.items():
                        if re.search(pattern, line):
                            line = re.sub(pattern, replacement, line)
                            modified = True

                    if modified and line != original_line:
                        lines[issue['line'] - 1] = line

            if modified:
                # Add async imports if needed
                if 'from sqlalchemy.ext.asyncio import' not in content:
                    for i, line in enumerate(lines):
                        if 'from sqlalchemy.orm import Session' in line:
                            lines[i] = line.replace(
                                'from sqlalchemy.orm import Session',
                                'from sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy.orm import Session'
                            )
                            modified = True
                            break

                if 'from sqlalchemy import select' not in content:
                    for i, line in enumerate(lines):
                        if 'from sqlalchemy import' in line and 'select' not in line:
                            lines[i] = line.rstrip() + ', select'
                            modified = True
                            break

                # Write back the modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))

                self.fixed_files.append(str(file_path))
                return True

            return False

        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False

    def fix_service_layer(self):
        """Fix the service layer files"""
        print("🔧 Fixing service layer async consistency...")

        service_files = [
            "app/services/wellness_monitoring_service.py",
            "app/services/anonymous_feedback.py",
            "app/services/Analytics_service.py",
            "app/services/team_dynamics_service.py",
            "app/services/assessment_integration_service.py"
        ]

        for service_file in service_files:
            file_path = self.project_root / service_file
            if file_path.exists():
                print(f"   📝 Analyzing {service_file}...")
                issues = self.analyze_file(file_path)

                if issues:
                    print(f"      Found {len(issues)} issues")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"         - Line {issue['line']}: {issue['line_content']}")

                    self.issues_found.extend(issues)

                    if self.fix_database_operations(file_path, issues):
                        print(f"      ✅ Fixed {service_file}")
                    else:
                        print(f"      ⚠️  No fixes applied to {service_file}")
                else:
                    print(f"      ✅ No issues found in {service_file}")

    def fix_api_layer(self):
        """Fix the API layer files"""
        print("\n🔧 Fixing API layer async consistency...")

        api_files = [
            "app/api/v1/endpoints/assessments.py",
            "app/api/v1/endpoints/psychometrics_routes.py",
            "app/api/v1/endpoints/nlp_routes.py",
            "app/api/v1/endpoints/optimizer.py"
        ]

        for api_file in api_files:
            file_path = self.project_root / api_file
            if file_path.exists():
                print(f"   📝 Analyzing {api_file}...")
                issues = self.analyze_file(file_path)

                if issues:
                    print(f"      Found {len(issues)} issues")
                    self.issues_found.extend(issues)

                    if self.fix_database_operations(file_path, issues):
                        print(f"      ✅ Fixed {api_file}")
                    else:
                        print(f"      ⚠️  No fixes applied to {api_file}")
                else:
                    print(f"      ✅ No issues found in {api_file}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate a fix report"""
        return {
            'fixed_files': len(self.fixed_files),
            'issues_found': len(self.issues_found),
            'files_modified': self.fixed_files,
            'summary': f"Fixed {len(self.fixed_files)} files with {len(self.issues_found)} async consistency issues"
        }

def main():
    """Main execution function"""
    print("🚀 Starting Async Consistency Fix...")
    print("=" * 50)

    fixer = AsyncConsistencyFixer()

    # Fix service layer
    fixer.fix_service_layer()

    # Fix API layer
    fixer.fix_api_layer()

    # Generate report
    report = fixer.generate_report()

    print(f"\n📊 Fix Results:")
    print(f"   Files Fixed: {report['fixed_files']}")
    print(f"   Issues Found: {report['issues_found']}")
    print(f"   Summary: {report['summary']}")

    if report['fixed_files'] > 0:
        print(f"\n✅ Fixed Files:")
        for file in report['files_modified']:
            print(f"   - {file}")

        print(f"\n🎯 Next Steps:")
        print(f"   1. Run: python tests/devops_architecture_validation.py")
        print(f"   2. Check for any remaining syntax errors")
        print(f"   3. Test the fixed functionality")
    else:
        print(f"\n⚠️  No files were fixed. Manual review may be needed.")

if __name__ == "__main__":
    main()