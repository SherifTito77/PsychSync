#!/usr/bin/env python3
"""
Fix indentation issues in health.py
"""

import re


def fix_health_py():
    """Fix all indentation issues in health.py"""
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/health.py", "r"
    ) as f:
        content = f.read()

    # Fix pattern 1: except on wrong line/indentation
    # Pattern: except Exception as e:        return 0
    fixed = re.sub(
        r"except Exception as e:\s+return ([\w\[\]{}\", ()\d]+)\n",
        r"except Exception as e:\n        return \1\n",
        content,
    )

    # Fix pattern 2: except on wrong indentation
    # Pattern: except Exception as e:        return {...}
    fixed = re.sub(
        r"except Exception as e:\s+return ({[^}]+})\n",
        r"except Exception as e:\n        return \1\n",
        fixed,
    )

    # Write back
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/health.py", "w"
    ) as f:
        f.write(fixed)

    # Verify
    import ast

    try:
        ast.parse(fixed)
        print("✅ health.py syntax is now correct!")
        return True
    except SyntaxError as e:
        print(f"❌ Still has syntax error on line {e.lineno}")
        return False


if __name__ == "__main__":
    fix_health_py()
