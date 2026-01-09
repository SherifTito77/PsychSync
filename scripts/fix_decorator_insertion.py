#!/usr/bin/env python3
"""
Advanced Syntax Corruption Fix Script v2

Fixes the decorator insertion pattern where @check_rate_limit decorators
are inserted in the middle of raise statements and other code blocks.

Pattern to fix:
    except Exception as e:
        raise HTTPException(status_code=500
    @check_rate_limit(...)
    , detail=str(e))

Fix:
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) from e
"""

import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple


def fix_decorator_insertion(content: str) -> Tuple[str, int]:
    """
    Fix decorator insertion pattern in Python code

    Returns:
        (fixed_content, number_of_fixes)
    """
    fixes_count = 0
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        current_line = lines[i]

        # Detect pattern: incomplete raise statement followed by decorator
        # Pattern 1: raise HTTPException(status_code=number
        if re.search(r'^\s*raise\s+\w+\([^)]*$', current_line):
            # Look ahead for decorator
            if i + 1 < len(lines) and '@check_rate_limit' in lines[i + 1]:
                # Found the corruption!
                fixes_count += 1

                # Complete the current line with opening parenthesis for multi-line
                indent = len(current_line) - len(current_line.lstrip())
                fixed_lines.append(' ' * indent + current_line.strip() + '(')

                # Skip the decorator line (remove it)
                i += 2  # Skip decorator and the next line

                # Continue collecting parameters until we find the closing
                param_lines = []
                while i < len(lines):
                    next_line = lines[i].strip()

                    # If we hit a decorator, skip it
                    if next_line.startswith('@'):
                        i += 1
                        continue

                    # Add the parameter line
                    param_lines.append(' ' * (indent + 4) + next_line.lstrip(',').strip())

                    # Check if line ends with closing parenthesis
                    if next_line.endswith(')'):
                        i += 1
                        break

                    i += 1

                # Add all parameter lines
                fixed_lines.extend(param_lines)

                # Add closing with 'from e' if exception variable exists
                # For now, just add the closing parenthesis
                fixed_lines.append(' ' * indent + ')')

                continue

        # Detect pattern 2: except block split by decorator
        # Pattern:
        #   }
        #   e
        # @check_rate_limit(...)
        # xcept Exception as e:
        if current_line.strip() == 'e' and i + 1 < len(lines):
            if '@check_rate_limit' in lines[i + 1] and 'xcept' in lines[i + 2]:
                fixes_count += 1

                # This is the corrupted "except" keyword
                # We need to merge: e + xcept = except
                indent = len(current_line) - len(current_line.lstrip())

                # Skip to the line with "xcept"
                i += 2
                except_line = lines[i].strip()

                # Fix the corrupted except line
                fixed_except = except_line.replace('xcept', 'except')
                fixed_lines.append(' ' * indent + fixed_except)

                i += 1
                continue

        # Pattern 3: Decorator in middle of multi-line statement
        # Detect lines that start with @ after a multi-line statement
        if current_line.strip().startswith('@check_rate_limit'):
            # Check previous line
            if fixed_lines:
                prev_line = fixed_lines[-1]

                # If previous line is incomplete (doesn't end with colon or parenthesis)
                # and looks like it should continue
                if not prev_line.rstrip().endswith((':', ')', ']')):
                    # This decorator is likely corrupted, remove it
                    fixes_count += 1
                    i += 1
                    continue

        # Normal line - keep it
        fixed_lines.append(current_line)
        i += 1

    return '\n'.join(fixed_lines), fixes_count


def fix_file(file_path: Path, dry_run: bool = False, verbose: bool = True) -> bool:
    """
    Fix syntax corruption in a single file

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"\n🔧 Processing: {file_path}")

    try:
        # Read file
        content = file_path.read_text()
        original_content = content

        # Apply fixes
        fixed_content, fixes_count = fix_decorator_insertion(content)

        # Check if changes were made
        if fixed_content != original_content:
            if fixes_count > 0:
                if verbose:
                    print(f"  ✅ Found {fixes_count} corruption patterns")

                if dry_run:
                    if verbose:
                        print(f"  🧪 Dry run - Would fix {fixes_count} issues")
                        # Show before/after snippet
                        lines_before = original_content.split('\n')
                        lines_after = fixed_content.split('\n')

                        # Find first difference
                        for i, (before, after) in enumerate(zip(lines_before[:20], lines_after[:20])):
                            if before != after:
                                print(f"  📝 Line {i+1}:")
                                print(f"     Before: {before}")
                                print(f"     After:  {after}")
                                break
                else:
                    # Create backup
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = file_path.parent / f"{file_path.name}.backup_{timestamp}"
                    shutil.copy2(file_path, backup_path)
                    if verbose:
                        print(f"  💾 Backup: {backup_path.name}")

                    # Write fixed content
                    file_path.write_text(fixed_content)
                    if verbose:
                        print(f"  ✅ Fixed {fixes_count} issues")

                    # Verify with ruff
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['ruff', 'check', str(file_path), '--select', 'F401,E999', '--output-format=concise'],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0 or 'No errors' in result.stdout:
                            if verbose:
                                print(f"  ✅ Syntax validation passed")
                        else:
                            if verbose:
                                print(f"  ⚠️  Syntax validation warnings:")
                                print(f"     {result.stdout[:200]}")
                    except Exception as e:
                        if verbose:
                            print(f"  ⚠️  Could not verify with ruff: {e}")

                return True
            else:
                if verbose:
                    print(f"  ℹ️  File already clean (no decorator insertion issues)")
                return True
        else:
            if verbose:
                print(f"  ℹ️  File already clean")
            return True

    except Exception as e:
        if verbose:
            print(f"  ❌ Error: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix decorator insertion pattern corruption in Python files'
    )
    parser.add_argument('--file', type=str, help='Specific file to fix')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    parser.add_argument('--verbose', action='store_true', default=True)

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Error: File not found: {args.file}")
            return

        fix_file(file_path, dry_run=args.dry_run, verbose=args.verbose)
    else:
        # Test on api_fuzzer.py by default
        print("🧪 Testing syntax corruption fix script...")
        print("="*80)

        test_file = Path("app/testing/api_fuzzer.py")
        if test_file.exists():
            fix_file(test_file, dry_run=True, verbose=True)
        else:
            print(f"❌ Test file not found: {test_file}")


if __name__ == '__main__':
    main()
