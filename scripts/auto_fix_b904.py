#!/usr/bin/env python3
"""
Automated B904 Exception Chain Fixer

This script fixes B904 errors by adding 'from err' to exception raises.
It handles the common patterns found in the codebase.

Usage:
    python scripts/auto_fix_b904.py --file app/api/v1/endpoints/example.py
    python scripts/auto_fix_b904.py --all  # Fix all files in app directory
"""

import re
import sys
from pathlib import Path


def fix_exception_chains(content: str) -> tuple[str, int]:
    """
    Fix B904 errors by adding 'from err' to exception raises.

    Returns:
        tuple: (fixed_content, number_of_fixes)
    """
    fixes_count = 0
    lines = content.split("\n")
    i = 0
    fixed_lines = []

    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # Pattern 1: except Exception as e: followed by raise HTTPException
        if re.search(r"except\s+\w+\s+as\s+\w+:", line):
            # Look ahead for the raise statement
            j = i + 1
            while (
                j < len(lines)
                and not lines[j].strip().startswith("except")
                and not lines[j].strip().startswith("finally")
            ):
                if "raise HTTPException(" in lines[j] or "raise " in lines[j]:
                    # Check if this raise doesn't already have 'from'
                    if " from " not in lines[j] and not lines[j].strip().startswith(
                        "#"
                    ):
                        # Find the closing parenthesis
                        raise_line = lines[j]
                        if raise_line.strip().endswith(")"):
                            # Single line raise statement
                            indent = len(raise_line) - len(raise_line.lstrip())
                            fixed_lines[-1] = line  # Keep the except line as is

                            # Extract exception variable name
                    match = re.search(r"except\s+(\w+)\s+as\s+(\w+):", line)
                    if match:
                        exc_type, exc_var = match.groups()
                        # Modify the raise line
                        if (
                            "raise HTTPException(" in raise_line
                            or "raise " in raise_line
                        ):
                            # Add 'from exc_var' before the closing parenthesis
                            if raise_line.rstrip().endswith(")"):
                                raise_line_fixed = (
                                    raise_line.rstrip()[:-1] + f") from {exc_var}"
                                )
                                fixed_lines.pop()  # Remove the raise line we added
                                fixed_lines.append(raise_line_fixed)
                                fixes_count += 1
                            break
                j += 1

        i += 1

    # More robust pattern-based fixing
    content = "\n".join(fixed_lines)

    # Pattern: except Exception as e: \n ... \n raise HTTPException(...)
    # Replace with: except Exception as e: \n ... \n raise HTTPException(...) from e
    pattern1 = r"(except\s+(\w+)\s+as\s+(\w+):[\s\S]*?raise\s+HTTPException\([^)]*\))"

    def replacer1(match):
        nonlocal fixes_count
        exc_block = match.group(1)
        exc_var = match.group(3)

        # Only fix if 'from' is not already present
        if " from " not in exc_block:
            # Find the last closing parenthesis
            last_paren = exc_block.rfind(")")
            if last_paren != -1:
                # Insert 'from exc_var' before the closing paren
                fixed = (
                    exc_block[:last_paren]
                    + f") from {exc_var}"
                    + exc_block[last_paren + 1 :]
                )
                fixes_count += 1
                return fixed
        return exc_block

    content = re.sub(pattern1, replacer1, content, flags=re.MULTILINE)

    return content, fixes_count


def fix_file(file_path: Path, dry_run: bool = False) -> int:
    """Fix B904 errors in a single file."""
    print(f"\n🔧 Processing: {file_path}")

    try:
        content = file_path.read_text()
        fixed_content, fixes_count = fix_exception_chains(content)

        if fixes_count > 0:
            print(f"   ✅ Fixed {fixes_count} B904 errors")

            if not dry_run:
                file_path.write_text(fixed_content)
                print(f"   💾 Saved changes")
            else:
                print(f"   🧪 Dry run - changes not saved")
        else:
            print(f"   ℹ️  No B904 errors found or already fixed")

        return fixes_count

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix B904 exception handling errors")
    parser.add_argument("--file", type=str, help="Specific file to fix")
    parser.add_argument(
        "--all", action="store_true", help="Fix all files in app directory"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing"
    )

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        total_fixes = fix_file(file_path, args.dry_run)
        print(f"\n✨ Total fixes: {total_fixes}")

    elif args.all:
        print("🚀 Fixing all Python files in app directory...")
        total_fixes = 0

        for py_file in Path("app").rglob("*.py"):
            total_fixes += fix_file(py_file, args.dry_run)

        print(f"\n✨ Total fixes across all files: {total_fixes}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
