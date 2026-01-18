#!/usr/bin/env python3
"""
Syntax Corruption Fix Script

Automatically fixes the decorator insertion pattern that corrupts Python files:
except Exception as e:
    raise HTTPException(status_code=500
@check_rate_limit(...)
, detail=str(e))

To:
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=str(e)
    ) from e

Usage:
    python scripts/fix_syntax_corruption.py --file app/testing/api_fuzzer.py
    python scripts/fix_syntax_corruption.py --dry-run --file app/testing/api_fuzzer.py
    python scripts/fix_syntax_corruption.py --all --pattern "api/v1/endpoints"
"""

import re
import sys
import shutil
from pathlib import Path
from typing import List, Tuple
from datetime import datetime


class SyntaxCorruptionFixer:
    """Fixes decorator insertion pattern in Python files"""

    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'files_processed': 0,
            'decorator_removals': 0,
            'syntax_fixes': 0,
            'errors': 0
        }

    def log(self, message: str):
        """Print message if verbose mode is on"""
        if self.verbose:
            print(message)

    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of the file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        self.log(f"  💾 Backup created: {backup_path.name}")
        return backup_path

    def fix_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Fix syntax corruption in a single file

        Returns:
            (success, number_of_fixes)
        """
        self.log(f"\n🔧 Processing: {file_path}")

        try:
            # Read file
            content = file_path.read_text()
            original_content = content
            fixes_count = 0

            # Pattern 1: Decorator inserted in middle of raise statement
            # Match: raise Exception(...\n@decorator\n, ...)
            pattern1 = r'(raise\s+\w+\([^)]+)\n(@\w+\([^)]*\))\n(,\s*[^)]+\))'
            def replacer1(match):
                nonlocal fixes_count
                fixes_count += 1
                self.stats['decorator_removals'] += 1
                # Remove the decorator line
                return match.group(1) + '\n' + match.group(3)

            content = re.sub(pattern1, replacer1, content, flags=re.MULTILINE)

            # Pattern 2: Fix incomplete raise statements
            # Match: raise Exception(status_code=number\n
            # Replace with: raise Exception(\n        status_code=number
            pattern2 = r'(raise\s+\w+)\(([^)]+)(\n)'
            def replacer2(match):
                # Only fix if it looks like a multi-line statement
                if len(match.group(2)) > 0 and match.group(2)[-1] != ',':
                    fixes_count += 1
                    self.stats['syntax_fixes'] += 1
                    return f"{match.group(1)}(\n{match.group(2)},\n"
                return match.group(0)

            content = re.sub(pattern2, replacer2, content)

            # Pattern 3: Fix lines that start with comma after decorator removal
            # Match: \n, detail
            # Replace with proper indentation
            pattern3 = r'\n(,)\s*'
            def replacer3(match):
                # Check if this comma appears after removed decorator
                fixes_count += 1
                self.stats['syntax_fixes'] += 1
                return '\n                '

            # Apply pattern more carefully to avoid false positives
            lines = content.split('\n')
            fixed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]

                # Skip decorator lines (they should have been removed by pattern1)
                if line.strip().startswith('@') and 'check_rate_limit' in line:
                    # This decorator should be removed
                    self.log(f"  ⚠️  Unexpected decorator found: {line.strip()}")
                    fixes_count += 1
                    self.stats['decorator_removals'] += 1
                    i += 1
                    continue

                # Fix lines starting with comma (after decorator removal)
                if line.strip().startswith(',') and i > 0:
                    # Indent properly and remove leading comma
                    fixed_lines.append('                ' + line.strip()[1:])
                    fixes_count += 1
                    self.stats['syntax_fixes'] += 1
                else:
                    fixed_lines.append(line)

                i += 1

            content = '\n'.join(fixed_lines)

            # Check if any changes were made
            if content != original_content:
                if fixes_count > 0:
                    self.stats['files_processed'] += 1

                    if self.dry_run:
                        self.log(f"  🧪 Dry run - Would make {fixes_count} fixes")
                        # Show first few changes
                        self.log(f"  📝 Changes preview (first 500 chars):")
                        self.log(f"     Before: {original_content[:200]}...")
                        self.log(f"     After:  {content[:200]}...")
                    else:
                        # Create backup
                        backup_path = self.backup_file(file_path)

                        # Write fixed content
                        file_path.write_text(content)
                        self.log(f"  ✅ Fixed {fixes_count} issues")

                        # Verify the fix
                        try:
                            import subprocess
                            result = subprocess.run(
                                ['ruff', 'check', str(file_path), '--select', 'B904'],
                                capture_output=True,
                                text=True
                            )
                            remaining = result.stdout.count('B904') if 'B904' in result.stdout else 0
                            self.log(f"  📊 Remaining B904 errors: {remaining}")
                        except Exception as e:
                            self.log(f"  ⚠️  Could not verify with ruff")

                        return True, fixes_count
                else:
                    self.log(f"  ℹ️  No syntax corruption found")
                    return True, 0
            else:
                self.log(f"  ℹ️  File already clean (no changes needed)")
                return True, 0

        except Exception as e:
            self.log(f"  ❌ Error processing {file_path}: {e}")
            self.stats['errors'] += 1
            return False, 0

    def fix_directory(self, directory: Path, pattern: str = "*.py") -> int:
        """
        Fix all Python files in a directory

        Returns:
            Total number of files processed
        """
        self.log(f"\n🚀 Processing directory: {directory}")
        self.log(f"📁 Pattern: {pattern}")

        total_fixes = 0
        files = list(directory.rglob(pattern))

        for file_path in files:
            success, fixes = self.fix_file(file_path)
            if success:
                total_fixes += fixes

        return total_fixes

    def print_summary(self):
        """Print summary of all fixes"""
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Decorators removed: {self.stats['decorator_removals']}")
        print(f"Syntax fixes: {self.stats['syntax_fixes']}")
        print(f"Errors: {self.stats['errors']}")

        if self.dry_run:
            print("\n🧪 DRY RUN MODE - No files were modified")
        else:
            print("\n✅ Files were modified - backups created with .backup_<timestamp> suffix")

        print("="*80)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix syntax corruption in Python files (decorator insertion pattern)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fix a single file
  python scripts/fix_syntax_corruption.py --file app/testing/api_fuzzer.py

  # Dry run (don't modify files)
  python scripts/fix_syntax_corruption.py --dry-run --file app/testing/api_fuzzer.py

  # Fix all files in a directory
  python scripts/fix_syntax_corruption.py --dir app/testing

  # Fix all files matching a pattern
  python scripts/fix_syntax_corruption.py --dir app/api/v1/endpoints --pattern "*.py"

  # Fix all corrupted files in the codebase
  python scripts/fix_syntax_corruption.py --all
        """
    )

    parser.add_argument('--file', type=str, help='Specific file to fix')
    parser.add_argument('--dir', type=str, help='Directory to fix all files in')
    parser.add_argument('--pattern', type=str, default='*.py', help='File pattern to match (default: *.py)')
    parser.add_argument('--all', action='store_true', help='Fix all known corrupted files')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing files')
    parser.add_argument('--verbose', action='store_true', default=True, help='Verbose output')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')

    args = parser.parse_args()

    # Check for ruff installation
    try:
        import subprocess
        subprocess.run(['ruff', '--version'], capture_output=True, check=True)
    except Exception as e:
        print("⚠️  Warning: ruff not found. Install with: pip install ruff")

    # Create fixer
    verbose = not args.quiet
    fixer = SyntaxCorruptionFixer(dry_run=args.dry_run, verbose=verbose)

    # Process files
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Error: File not found: {args.file}")
            sys.exit(1)
        fixer.fix_file(file_path)

    elif args.dir:
        directory = Path(args.dir)
        if not directory.exists():
            print(f"❌ Error: Directory not found: {args.dir}")
            sys.exit(1)
        fixer.fix_directory(directory, args.pattern)

    elif args.all:
        # Known corrupted files
        corrupted_files = [
            "app/testing/api_fuzzer.py",
            "app/api/v1/endpoints/assessment_results.py",
            "app/api/v1/endpoints/behavioral_patterns.py",
            "app/api/v1/endpoints/behavioral_analytics.py",
            "app/api/v1/endpoints/assessment_routes.py",
            "app/api/v1/endpoints/behavioral_analysis.py",
            "app/api/v1/endpoints/reports.py",
            "app/api/v1/endpoints/templates.py",
            "app/api/v1/endpoints/scoring.py",
            "app/api/v1/endpoints/anonymous_feedback.py",
            "app/api/v1/endpoints/backups.py",
            "app/api/v1/endpoints/billing.py",
            "app/api/v1/endpoints/clinical_assessments.py",
            "app/api/v1/endpoints/communication_analysis.py",
            "app/api/v1/endpoints/email_connections.py",
            "app/api/v1/endpoints/gdpr.py",
            "app/api/v1/endpoints/monitoring.py",
        ]

        print("🎯 Fixing all known corrupted files...")
        for file_path_str in corrupted_files:
            file_path = Path(file_path_str)
            if file_path.exists():
                fixer.fix_file(file_path)
            else:
                fixer.log(f"⚠️  File not found: {file_path}")

    else:
        parser.print_help()
        sys.exit(1)

    # Print summary
    if not args.quiet:
        fixer.print_summary()


if __name__ == '__main__':
    main()
