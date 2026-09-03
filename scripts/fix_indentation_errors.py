#!/usr/bin/env python3
"""
Fix indentation errors in exception handling

This script fixes the specific indentation issues created by the automated fixer.
"""

import re
from pathlib import Path


def fix_indentation_errors(file_path: Path) -> bool:
    """Fix indentation errors in a file"""
    content = file_path.read_text()
    original = content

    # Pattern: "except Exception as e:" followed by unindented line
    # Fix: Add proper indentation after except clause

    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # Check if this is an "except Exception as e:" line
        if re.match(r"^(\s*)except Exception as e:\s*$", line):
            # Get the indentation
            indent_match = re.match(r"^(\s*)except Exception as e:", line)
            if indent_match:
                base_indent = indent_match.group(1)
                next_indent = base_indent + "    "

                # Look at next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # If next line is not indented more than the except line
                    if next_line and not next_line.startswith(next_indent):
                        # This line needs more indentation
                        # Check if it's already indented at all
                        if next_line.strip() and not next_line.startswith(
                            base_indent + " "
                        ):
                            # Add proper indentation
                            lines[i + 1] = next_indent + next_line.lstrip()

        i += 1

    content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def main():
    """Fix all files with indentation errors"""
    base_path = Path("/Users/sheriftito/Downloads/psychsync")

    files_to_fix = [
        "app/api/v1/endpoints/users.py",
        "app/api/v1/endpoints/auth_unified.py",
        "app/api/v1/endpoints/health.py",
        "app/api/v1/endpoints/intervention_effectiveness.py",
    ]

    print("🔧 Fixing indentation errors...")
    for file_str in files_to_fix:
        file_path = base_path / file_str
        if file_path.exists():
            if fix_indentation_errors(file_path):
                print(f"  ✅ Fixed {file_str}")
            else:
                print(f"  ℹ️  No changes needed for {file_str}")
        else:
            print(f"  ⚠️  File not found: {file_str}")

    print("\n✅ Indentation fixes complete!")


if __name__ == "__main__":
    main()
