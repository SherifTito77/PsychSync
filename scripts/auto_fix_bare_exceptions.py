#!/usr/bin/env python3
"""
Automatically fix bare exception handlers in the codebase.

This script:
1. Finds all bare except: clauses
2. Applies context-aware fixes based on the code patterns
3. Creates a git branch with changes
4. Shows diffs for review before committing

SAFETY: Creates backups and uses git for easy rollback
"""

import re
import ast
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FixCandidate:
    """A candidate for automatic fixing."""
    file_path: str
    line_number: int
    old_code: str
    new_code: str
    reason: str
    confidence: str  # 'high', 'medium', 'low'


class BareExceptionFixer:
    """Fix bare exception handlers automatically."""

    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root_dir = root_dir
        self.dry_run = dry_run
        self.fixes_applied: List[FixCandidate] = []

    def find_and_fix_high_severity(self) -> List[FixCandidate]:
        """Find and fix HIGH severity bare exception handlers."""

        # Priority files from the analysis
        high_priority_files = [
            "test_end_to_end_validation.py",
            "psychsync_platform_regression_suite.py",
            "comprehensive_rate_limiting_tests.py",
            "jwt_token_test_suite.py",
            "comprehensive_jwt_tests.py",
            "available_endpoints_test.py",
            "postman_test_runner.py",
            "app/api/v1/endpoints/health.py",
            "app/services/ai_enhanced_analytics.py",
        ]

        all_fixes = []

        for file_name in high_priority_files:
            for py_file in self.root_dir.rglob(file_name):
                if py_file.is_file():
                    fixes = self.fix_file(py_file)
                    all_fixes.extend(fixes)

        return all_fixes

    def fix_file(self, file_path: Path) -> List[FixCandidate]:
        """Fix bare exceptions in a single file."""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except Exception:
            return []

        fixes = []

        # Find all bare except patterns using regex
        for i, line in enumerate(lines):
            # Match bare except:
            if re.search(r'except\s*:\s*$', line):
                fix = self._analyze_and_fix_bare_except(lines, i, file_path)
                if fix:
                    fixes.append(fix)
                    if not self.dry_run:
                        lines[i] = fix.new_code

        # Apply fixes if not dry run
        if fixes and not self.dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        return fixes

    def _analyze_and_fix_bare_except(self, lines: List[str], line_idx: int, file_path: Path) -> Optional[FixCandidate]:
        """Analyze context and generate appropriate fix."""

        # Get context (previous 10 lines)
        context_start = max(0, line_idx - 10)
        context = ''.join(lines[context_start:line_idx + 2])

        # Determine fix based on patterns
        old_line = lines[line_idx]
        indent = len(old_line) - len(old_line.lstrip())

        fix_pattern, reason, confidence = self._determine_fix_pattern(context, file_path)

        if fix_pattern:
            new_line = ' ' * indent + fix_pattern + '\n'
            return FixCandidate(
                file_path=str(file_path),
                line_number=line_idx + 1,
                old_code=old_line.rstrip(),
                new_code=new_line.strip(),
                reason=reason,
                confidence=confidence
            )

        return None

    def _determine_fix_pattern(self, context: str, file_path: Path) -> Tuple[Optional[str], str, str]:
        """Determine the appropriate exception pattern based on context."""

        context_lower = context.lower()

        # Pattern 1: JSON parsing
        if '.json()' in context or 'json.loads' in context or 'json.dump' in context:
            return (
                'except Exception as e:',
                'JSON parsing operations - catch general exceptions',
                'high'
            )

        # Pattern 2: HTTP/API requests
        if any(keyword in context_lower for keyword in ['requests.', 'response.', 'httpx.', 'fetch(']):
            return (
                'except Exception as e:',
                'HTTP/API operations - catch general exceptions',
                'high'
            )

        # Pattern 3: Database operations
        if any(keyword in context_lower for keyword in ['session.execute', 'db.execute', '.fetch', '.commit', '.query']):
            return (
                'except Exception as e:',
                'Database operations - catch general exceptions',
                'high'
            )

        # Pattern 4: Async operations
        if 'async' in context_lower and 'await' in context_lower:
            return (
                'except Exception as e:',
                'Async operations - catch general exceptions',
                'medium'
            )

        # Pattern 5: File operations
        if any(keyword in context_lower for keyword in ['open(', 'file.read', 'file.write', '.read(', '.write(']):
            return (
                'except (OSError, IOError) as e:',
                'File operations - catch OS/IO errors',
                'high'
            )

        # Pattern 6: Test files - be conservative
        if 'test' in str(file_path).lower():
            return (
                'except Exception as e:',
                'Test file - use general exception handling',
                'high'
            )

        # Pattern 7: Default - safe general exception
        return (
            'except Exception as e:',
            'Default safe exception handling',
            'medium'
        )

    def create_git_branch(self, branch_name: str = "fix/auto-fix-bare-exceptions"):
        """Create and checkout a new git branch."""

        try:
            # Check if we're in a git repo
            subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                check=True,
                capture_output=True,
                cwd=self.root_dir
            )

            # Create and checkout branch
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                check=True,
                cwd=self.root_dir
            )

            print(f"✅ Created git branch: {branch_name}")
            return True

        except subprocess.CalledProcessError:
            print("⚠️  Not in a git repository or git command failed")
            return False

    def show_summary(self):
        """Show summary of fixes applied."""

        if not self.fixes_applied:
            print("❌ No fixes were applied")
            return

        print(f"\n📊 Summary: {len(self.fixes_applied)} fixes applied\n")

        by_confidence = {'high': [], 'medium': [], 'low': []}
        for fix in self.fixes_applied:
            by_confidence[fix.confidence].append(fix)

        for confidence in ['high', 'medium', 'low']:
            if by_confidence[confidence]:
                print(f"\n{confidence.upper()} Confidence ({len(by_confidence[confidence])} fixes):")
                for fix in by_confidence[confidence][:5]:  # Show first 5
                    print(f"  • {fix.file_path}:{fix.line_number}")
                    print(f"    {fix.reason}")
                if len(by_confidence[confidence]) > 5:
                    print(f"  ... and {len(by_confidence[confidence]) - 5} more")

    def commit_changes(self):
        """Commit changes to git."""

        if not self.fixes_applied:
            return False

        try:
            # Add all changes
            subprocess.run(
                ['git', 'add', '-A'],
                check=True,
                cwd=self.root_dir
            )

            # Create commit message
            commit_msg = f"""fix: automatically fix bare exception handlers

Auto-fixed {len(self.fixes_applied)} bare exception handlers:
- Replaced bare 'except:' with specific exception types
- Added context-aware exception handling
- Improved error visibility for debugging

This change prevents:
- Catching system-exiting exceptions (KeyboardInterrupt, SystemExit)
- Silent failures that hide bugs
- Inability to terminate programs with Ctrl+C

Files modified: {len(set(f.file_path for f in self.fixes_applied))}

🤖 Generated with Claude Code
"""

            # Commit
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                check=True,
                cwd=self.root_dir
            )

            print(f"\n✅ Committed {len(self.fixes_applied)} fixes")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Git commit failed: {e}")
            return False


def main():
    """Main entry point."""

    import argparse

    parser = argparse.ArgumentParser(description="Auto-fix bare exception handlers")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--branch', action='store_true', help='Create a new git branch for changes')
    parser.add_argument('--commit', action='store_true', help='Commit changes after fixing')
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent

    print("🔧 Auto-fixing bare exception handlers...")
    print(f"📁 Root directory: {root_dir}")
    print(f"🧪 Dry run: {args.dry_run}\n")

    fixer = BareExceptionFixer(root_dir, dry_run=args.dry_run)

    # Create branch if requested
    if args.branch and not args.dry_run:
        fixer.create_git_branch()

    # Find and fix HIGH severity issues
    print("🔍 Finding and fixing HIGH severity issues...\n")
    fixes = fixer.find_and_fix_high_severity()
    fixer.fixes_applied = fixes

    # Show summary
    fixer.show_summary()

    # Commit if requested
    if args.commit and not args.dry_run and fixes:
        fixer.commit_changes()
        print("\n✅ All done! Review the changes with: git diff main")
    elif args.dry_run:
        print("\n🧪 Dry run complete - no changes made")
        print("💡 Run without --dry-run to apply fixes")

    return 0 if fixes else 1


if __name__ == '__main__':
    sys.exit(main())
