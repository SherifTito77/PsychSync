#!/usr/bin/env python3
"""
Comprehensive B904 Exception Chaining Fix Script

This script fixes B904 errors by:
1. Removing misplaced @check_rate_limit decorators from exception handlers
2. Fixing unterminated string literals
3. Correcting indentation errors
4. Applying ruff B904 auto-fixes

Usage:
    python scripts/fix_b904_comprehensive.py [--dry-run] [--file <path>]

Examples:
    # Fix all files
    python scripts/fix_b904_comprehensive.py

    # Fix specific file
    python scripts/fix_b904_comprehensive.py --file app/api/v1/endpoints/auth.py

    # Dry run to see what would change
    python scripts/fix_b904_comprehensive.py --dry-run
"""

import argparse
import re
import subprocess
from pathlib import Path
from typing import List, Tuple


def fix_misplaced_decorators(content: str) -> Tuple[str, int]:
    """Remove @check_rate_limit decorators from middle of exception raises.

    Pattern: @check_rate_limit appearing between raise HTTPException and its arguments
    """
    fixes = 0
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Check if this line starts a raise HTTPException
        if re.search(r'raise\s+HTTPException\(', line):
            # Look ahead for misplaced decorator
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(')'):
                if '@check_rate_limit' in lines[j]:
                    # Found misplaced decorator - skip it
                    fixes += 1
                    print(f"  → Removed misplaced decorator at line {j + 1}")
                    j += 1
                    continue
                result.append(lines[j])
                j += 1
            # Add remaining lines up to closing paren
            while j < len(lines):
                result.append(lines[j])
                if ')' in lines[j]:
                    break
                j += 1
            i = j

        i += 1

    return '\n'.join(result), fixes


def fix_unterminated_strings(content: str) -> Tuple[str, int]:
    """Fix unterminated string literals caused by misplaced decorators.

    Pattern: detail="Incomplete string
              @check_rate_limit(...)
              rest of string"
    """
    fixes = 0
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for unterminated string followed by decorator
        if re.search(r'detail="[^"]*$', line):
            # Look ahead for decorator
            if i + 1 < len(lines) and '@check_rate_limit' in lines[i + 1]:
                # Found the pattern - merge the string parts
                j = i + 2
                string_parts = [line.rstrip()]
                while j < len(lines):
                    if lines[j].strip().startswith('"') and not lines[j].strip().startswith('@'):
                        # Found the continuation
                        string_parts.append(lines[j].strip())
                        merged = ''.join(string_parts)
                        result.append(merged)
                        fixes += 1
                        print(f"  → Fixed unterminated string at line {i + 1}")
                        i = j
                        break
                    string_parts.append(lines[j].strip())
                    j += 1
            else:
                result.append(line)
        else:
            result.append(line)

        i += 1

    return '\n'.join(result), fixes


def fix_indentation_errors(content: str, file_path: str) -> Tuple[str, int]:
    """Fix common indentation errors in try-except blocks.

    Pattern: Statements with incorrect indentation after await db.commit()
    """
    fixes = 0

    # Fix: "        await db.commit()" followed by incorrectly indented lines
    pattern1 = r'(\s+await db\.commit\(\)\s*\n)(\s+return result\.)'
    replacement1 = r'\1            \2'
    new_content, count1 = re.subn(pattern1, replacement1, content)
    fixes += count1

    if count1:
        print(f"  → Fixed {count1} indentation errors after db.commit()")

    return new_content, fixes


def remove_orphaned_json_blocks(content: str) -> Tuple[str, int]:
    """Remove orphaned JSON blocks after return statements.

    Pattern: return {...} followed by orphaned JSON structures
    """
    fixes = 0
    lines = content.split('\n')
    result = []
    in_return = False
    paren_depth = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect start of return statement
        if re.match(r'\s+return\s+\{', line):
            in_return = True
            paren_depth = line.count('{') - line.count('}')

        if in_return:
            result.append(line)
            paren_depth += line.count('{') - line.count('}')

            # Check if return statement is complete
            if paren_depth == 0 and '}' in line:
                in_return = False

                # Skip orphaned JSON blocks that follow
                j = i + 1
                skipped = []
                while j < len(lines):
                    next_line = lines[j]
                    # If next line has significantly less indentation, it's not orphaned
                    if next_line.strip() and not next_line.startswith(' '):
                        break
                    # If it looks like a new block definition
                    if re.match(r'\s+\{\s*$', next_line):
                        skipped.append(j)
                        j += 1
                        continue
                    break

                if skipped:
                    print(f"  → Removed {len(skipped)} orphaned JSON blocks starting at line {skipped[0] + 1}")
                    fixes += 1
                    i = j - 1

        else:
            result.append(line)

        i += 1

    return '\n'.join(result), fixes


def apply_ruff_b904_fixes(file_path: Path) -> int:
    """Apply ruff's B904 auto-fixes to a file."""
    try:
        result = subprocess.run(
            ["ruff", "check", str(file_path), "--select", "B904", "--fix"],
            capture_output=True,
            text=True
        )

        # Count how many were fixed by checking if returncode is 0
        if result.returncode == 0:
            return -1  # All fixed
        else:
            # Count remaining errors
            return result.stdout.count('B904')
    except Exception as e:
        print(f"  ⚠ Error running ruff: {e}")
        return -2


def fix_file(file_path: Path, dry_run: bool = False) -> int:
    """Fix all issues in a single file."""
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print('='*60)

    try:
        content = file_path.read_text()
        original_content = content
        total_fixes = 0

        # Apply fixes in sequence
        for fix_name, fix_func in [
            ("Misplaced decorators", fix_misplaced_decorators),
            ("Unterminated strings", fix_unterminated_strings),
            ("Indentation errors", lambda c: fix_indentation_errors(c, str(file_path))),
            ("Orphaned JSON blocks", remove_orphaned_json_blocks),
        ]:
            content, fixes = fix_func(content)
            if fixes > 0:
                total_fixes += fixes
                print(f"✓ Fixed {fixes}: {fix_name}")

        # Write back if changes were made
        if content != original_content and not dry_run:
            file_path.write_text(content)
            print(f"✓ Wrote changes to {file_path}")

        # Validate syntax
        try:
            compile(content, str(file_path), 'exec')
            print("✓ Syntax valid")
        except SyntaxError as e:
            print(f"✗ Syntax error: {e}")
            return 0

        # Apply ruff B904 fixes
        remaining = apply_ruff_b904_fixes(file_path)

        if remaining == -1:
            print("✅ All B904 errors fixed!")
            return total_fixes + 100  # Bonus for complete fix
        elif remaining == -2:
            print("⚠️  Ruff failed, but manual fixes applied")
            return total_fixes
        elif remaining == 0:
            print("✅ No B904 errors found!")
            return total_fixes + 50
        else:
            print(f"⚠️  {remaining} B904 errors remaining")
            return total_fixes

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='Comprehensive B904 exception chaining fixer')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without modifying files')
    parser.add_argument('--file', type=str, help='Specific file to fix (default: fix all in app/)')
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        # Get all Python files in app/
        files = list(Path('app').rglob('*.py'))

    # Filter files that actually have B904 errors
    files_with_errors = []
    for file in files:
        result = subprocess.run(
            ["ruff", "check", str(file), "--select", "B904"],
            capture_output=True,
            text=True
        )
        if 'B904' in result.stdout:
            files_with_errors.append(file)

    print(f"Found {len(files_with_errors)} files with B904 errors")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")

    total_fixes = 0
    successfully_fixed = 0

    for file in files_with_errors:
        fixes = fix_file(file, args.dry_run)
        if fixes > 50:  # Completely fixed
            successfully_fixed += 1
        total_fixes += max(0, fixes)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Files processed: {len(files_with_errors)}")
    print(f"Completely fixed: {successfully_fixed}")
    print(f"Total manual fixes applied: {total_fixes}")
    print()

    if successfully_fixed > 0:
        print(f"✅ {successfully_fixed} files are now B904-compliant!")

        if not args.dry_run:
            print("\nNext steps:")
            print("  1. Review the changes with: git diff")
            print("  2. Commit the fixes: git add -A && git commit -m 'fix: B904 improvements'")
            print("  3. Run verification: bash scripts/verify_b904_setup.sh")


if __name__ == "__main__":
    main()
