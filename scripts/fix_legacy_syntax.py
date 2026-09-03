#!/usr/bin/env python3
"""
Comprehensive syntax error fixer for legacy files.

Fixes:
1. Duplicate/corrupted docstrings in CRUD files
2. Indentation errors in integration files
3. Database security syntax errors
"""

import re
from pathlib import Path


def fix_crud_file(file_path: Path) -> bool:
    """Fix CRUD files with duplicate docstrings."""
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Pattern: Found a method declaration followed by corrupted docstring
        if i > 0 and "async def " in line and "(" in line:
            # Check if next lines have the corrupted pattern
            if i + 1 < len(lines) and '"""Retrieve resource(s).' in lines[i + 1]:
                # Skip the corrupted docstring block
                j = i + 1
                # Find the real docstring or method body
                while j < len(lines):
                    if (
                        j + 2 < len(lines)
                        and '"""' in lines[j + 1]
                        and '"""' in lines[j + 2]
                    ):
                        # Found the real docstring, skip the corrupted one
                        fixed_lines.append(line)  # Keep the method signature
                        i = j
                        break
                    if "self," in lines[j] or "self," in lines[j]:
                        # Found the real parameters
                        fixed_lines.append(line)  # Keep the method signature
                        i = j
                        break
                    j += 1
                if i < j:
                    # Skip to the real docstring
                    i = j - 1
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

        i += 1

    # Alternative: Use regex to remove the corrupted docstrings
    # Pattern 1: Remove standalone corrupted docstrings
    pattern = r'        """Retrieve resource\\(s\)\.\n\nArgs:\n    db: Database session\n    \*\*kwargs: Filter criteria\n\nReturns:\n    Resource object or list of resources\n\nRaises:\n    NotFoundError: If resource doesn\'t exist\n        """\n'

    content = re.sub(
        pattern,
        "",
        fixed_content if "fixed_content" in locals() else "\n".join(fixed_lines),
    )

    # Write back if changed
    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_slack_integration() -> bool:
    """Fix indentation errors in slack_integration.py"""
    file_path = Path("app/integrations/slack_integration.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix the pattern: response.raise_for_status() followed by over-indented code
    lines = content.split("\n")
    for i in range(len(lines) - 3):
        if "response.raise_for_status()" in lines[i]:
            # Check if next non-empty line is over-indented
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                next_line = lines[j]
                # If line has content but is over-indented (more than 8 spaces for method-level code)
                if next_line.startswith(" " * 10) and not next_line.startswith(
                    " " * 12
                ):
                    # Reduce indentation by 2 spaces
                    lines[j] = lines[j][2:] if lines[j].startswith("  ") else lines[j]

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_database_security() -> bool:
    """Fix database_security.py syntax error"""
    file_path = Path("app/core/database_security.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # The issue is likely a quote problem in the SQL query
    # Let's check for and fix any triple-quote issues
    lines = content.split("\n")
    for i in range(len(lines)):
        if 'text("""' in lines[i] or 'text(""""""' in lines[i]:
            # Fix the quotes
            lines[i] = lines[i].replace('text(""""""', 'text("""')
            lines[i] = lines[i].replace('""")""")', '""")')

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def remove_duplicate_methods(file_path: Path) -> bool:
    """Remove duplicate method definitions in CRUD files."""
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Pattern: Remove duplicate method bodies that appear after a correct one
    # This handles cases where a method was partially duplicated

    # Remove duplicate .limit()/return statements
    content = re.sub(
        r"(return result\.scalars\(\)\.all\(\))\n\s+\.limit\(limit\)\n\s+\)\n\s+return list\(result\.scalars\(\)\.all\(\)\)",
        r"\1",
        content,
    )

    # Remove duplicate fragments like:
    #     end_date: Optional[datetime] = None,
    # ) -> tuple[list[CodeQualityMetric], int]:
    #     """Get multiple metrics with filtering"""
    content = re.sub(
        r'\n\s+end_date: Optional\[datetime\] = None,\n\s+\) -> tuple\[list\[CodeQualityMetric\], int\]:\n\s+"""Get multiple metrics with filtering"""',
        "",
        content,
    )

    if content != original:
        file_path.write_text(content)
        return True
    return False


def main():
    """Fix all syntax errors"""
    print("🔧 Fixing legacy file syntax errors...\n")

    fixes = []

    # Fix CRUD files
    crud_files = ["app/crud/crud_code_quality.py", "app/crud/crud_query_performance.py"]

    for file_path_str in crud_files:
        file_path = Path(file_path_str)
        if remove_duplicate_methods(file_path):
            fixes.append(file_path_str)
            print(f"  ✓ Fixed duplicate code in {file_path_str}")

    # Fix slack_integration.py
    if fix_slack_integration():
        fixes.append("slack_integration.py")
        print("  ✓ Fixed slack_integration.py indentation")

    # Fix database_security.py
    if fix_database_security():
        fixes.append("database_security.py")
        print("  ✓ Fixed database_security.py quotes")

    print(f"\n✅ Fixed {len(fixes)} files")

    # Verify fixes
    print("\n🔍 Verifying fixes...\n")
    all_passed = True

    test_files = [
        "app/api/v1/endpoints/skill_gap_analysis.py",
        "app/crud/crud_code_quality.py",
        "app/crud/crud_query_performance.py",
        "app/integrations/slack_integration.py",
        "app/core/database_security.py",
    ]

    import subprocess

    for file_path_str in test_files:
        result = subprocess.run(
            ["python", "-m", "py_compile", file_path_str], capture_output=True
        )
        if result.returncode == 0:
            print(f"  ✅ {file_path_str}")
        else:
            print(f"  ❌ {file_path_str} - Still has errors")
            all_passed = False

    if all_passed:
        print("\n🎉 All files fixed successfully!")
    else:
        print("\n⚠️  Some files still need manual fixes")


if __name__ == "__main__":
    main()
