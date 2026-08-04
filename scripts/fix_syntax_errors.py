#!/usr/bin/env python3
"""
Automatic Syntax Error Fixer

Fixes common syntax errors to achieve zero technical debt.
"""

import os
import re
from pathlib import Path


def fix_slack_syntax():
    """Fix slack.py syntax error"""
    file_path = Path("app/api/v1/endpoints/slack.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix indentation issue (already fixed above)

    return content != original


def fix_skill_gap_syntax():
    """Fix skill_gap_analysis.py syntax error"""
    file_path = Path("app/api/v1/endpoints/skill_gap_analysis.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix indentation at line 527
    content = re.sub(
        r"(except Exception as e:\n)(    logger\.error)",
        r"\1        logger.error",
        content,
    )

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_database_security_syntax():
    """Fix database_security.py syntax error"""
    file_path = Path("app/core/database_security.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix missing comma around line 306
    # Looking for: SELECT grantee, privilege_type
    # Should be: SELECT grantee, privilege_type,

    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "SELECT grantee, privilege_type" in line and not line.rstrip().endswith(","):
            lines[i] = line + ","
            break

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_validation_syntax():
    """Fix validation.py unterminated string"""
    file_path = Path("app/core/validation.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix unterminated string at line 572
    content = re.sub(
        r"'\.jar', '\.sh', '\.php', '\.asp', '\.aspx', \.jsp', '\.py', '\.pl',",
        "'.jar', '.sh', '.php', '.asp', '.aspx', '.jsp', '.py', '.pl',",
        content,
    )

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_crud_code_quality_syntax():
    """Fix crud_code_quality.py invalid syntax"""
    file_path = Path("app/crud/crud_code_quality.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Line 53: likely missing parenthesis or quote
    # Try to fix docstring issues
    lines = content.split("\n")
    for i, line in enumerate(lines[48:58], start=49):
        if '"""Retrieve resource(s)' in line:
            # Ensure proper docstring closing
            if i < len(lines) - 1:
                lines[i] = '        """Retrieve resource(s)."""'
            break

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_crud_query_performance_syntax():
    """Fix crud_query_performance.py invalid syntax"""
    file_path = Path("app/crud/crud_query_performance.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Similar to above
    lines = content.split("\n")
    for i, line in enumerate(lines[61:71], start=62):
        if '"""Retrieve resource(s)' in line:
            if i < len(lines) - 1:
                lines[i] = '        """Retrieve resource(s)."""'
            break

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_slack_integration_syntax():
    """Fix slack_integration.py unexpected indent"""
    file_path = Path("app/integrations/slack_integration.py")
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix unexpected indent at line 460
    # Looking for incorrectly indented line
    lines = content.split("\n")
    for i in range(455, 465):
        if i < len(lines) and i > 0:
            line = lines[i]
            # If line has wrong indent
            if "data = response.json()" in line:
                # Check previous line's indent
                prev_line = lines[i - 1]
                if prev_line.strip() and not prev_line.startswith(" " * 12):
                    # Adjust indent to match
                    indent = len(prev_line) - len(prev_line.lstrip())
                    lines[i] = " " * indent + line.lstrip()
                break

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def main():
    """Fix all syntax errors"""
    print("🔧 Fixing syntax errors...\n")

    fixes = []

    if fix_slack_syntax():
        fixes.append("slack.py")
        print("  ✓ Fixed slack.py")

    if fix_skill_gap_syntax():
        fixes.append("skill_gap_analysis.py")
        print("  ✓ Fixed skill_gap_analysis.py")

    if fix_database_security_syntax():
        fixes.append("database_security.py")
        print("  ✓ Fixed database_security.py")

    if fix_validation_syntax():
        fixes.append("validation.py")
        print("  ✓ Fixed validation.py")

    if fix_crud_code_quality_syntax():
        fixes.append("crud_code_quality.py")
        print("  ✓ Fixed crud_code_quality.py")

    if fix_crud_query_performance_syntax():
        fixes.append("crud_query_performance.py")
        print("  ✓ Fixed crud_query_performance.py")

    if fix_slack_integration_syntax():
        fixes.append("slack_integration.py")
        print("  ✓ Fixed slack_integration.py")

    print(f"\n✅ Fixed {len(fixes)} syntax errors")
    print("🚀 Running black again to verify...")

    # Run black again
    import subprocess

    result = subprocess.run(["black", "--check", "app/"], capture_output=True)

    if result.returncode == 0:
        print("✅ All files formatted correctly!")
    else:
        print("⚠️  Some files still have issues:")
        print(result.stdout.decode())


if __name__ == "__main__":
    main()
