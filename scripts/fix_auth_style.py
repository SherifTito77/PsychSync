#!/usr/bin/env python3
"""
Fix common style issues in auth_unified.py
- G004: Logging f-strings -> % formatting
- DTZ003: datetime.utcnow() -> datetime.now(UTC)
- E712: == False -> is False
"""

import re
from pathlib import Path


def fix_logging_fstrings(content):
    """Fix logger.warning(f"...) to logger.warning("..." % ...)"""
    patterns = [
        (r'logger\.(warning|error|info|debug)\(f"([^"]*?)"\)', r'logger.\1("\2")'),
        (r"logger\.(warning|error|info|debug)\(f\'([^\']*?)\'\)", r"logger.\1('\2')"),
    ]

    # Find all logger lines with f-strings
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if "logger." in line and 'f"' in line:
            # Extract the logger method and message
            match = re.search(r'(logger\.\w+)\(f"([^"]*){([^}]+)}[^"]*"\)', line)
            if match:
                logger_method = match.group(1)
                prefix = match.group(2)
                variable = match.group(3)
                # Convert to % formatting
                fixed_line = line.replace(
                    f'{logger_method}(f"{prefix}{{{variable}}}"',
                    f'{logger_method}("{prefix}%s", {variable}',
                )
                fixed_lines.append(fixed_line)
                continue

        # Try multiline pattern
        if "logger." in line and 'f"' in line:
            match = re.search(r'(logger\.\w+)\(\s*f"([^"]*?)\{([^}]+)\}([^"]*?")', line)
            if match:
                logger_method = match.group(1)
                prefix = match.group(2)
                variable = match.group(3)
                suffix = match.group(4)
                fixed_line = line.replace(
                    f'{logger_method}(f"{prefix}{{{variable}}}{suffix}"',
                    f'{logger_method}("{prefix}%s{suffix}", {variable}',
                )
                fixed_lines.append(fixed_line)
                continue

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_datetime_utcnow(content):
    """Fix datetime.utcnow() to datetime.now(UTC)"""
    content = content.replace("datetime.utcnow()", "datetime.now(UTC)")
    return content


def fix_false_comparison(content):
    """Fix == False to is False"""
    content = content.replace("== False", "is False")
    content = content.replace("!= False", "is not False")
    return content


def main():
    file_path = Path("app/api/v1/endpoints/auth_unified.py")

    print(f"Reading {file_path}...")
    content = file_path.read_text()

    print("Applying fixes...")

    # Fix datetime.utcnow()
    content = fix_datetime_utcnow(content)
    print("  ✓ Fixed datetime.utcnow() -> datetime.now(UTC)")

    # Fix == False
    content = fix_false_comparison(content)
    print("  ✓ Fixed == False -> is False")

    # Write back
    file_path.write_text(content)
    print(f"\n✅ Fixed {file_path}")

    # Run ruff to see remaining issues
    import subprocess

    result = subprocess.run(
        ["ruff", "check", str(file_path)], capture_output=True, text=True
    )

    print("\nRemaining issues:")
    if result.returncode == 0:
        print("  None! All issues fixed.")
    else:
        for line in result.stdout.split("\n")[:20]:  # Show first 20
            if line.strip():
                print(f"  {line}")


if __name__ == "__main__":
    main()
