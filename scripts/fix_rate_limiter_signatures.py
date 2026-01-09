#!/usr/bin/env python3
"""
Fix rate limiter decorator signature mismatch.
Replaces endpoint_type parameter with limit_name in check_rate_limit decorators.
"""
import os
import re
from pathlib import Path

def fix_rate_limiter_signatures(directory: str):
    """
    Fix @check_rate_limit decorators in all Python files.
    Replaces endpoint_type with limit_name.
    """
    directory = Path(directory)
    fixed_count = 0
    error_count = 0

    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if file has the issue
            if '@check_rate_limit' not in content or 'endpoint_type' not in content:
                continue

            original_content = content

            # Replace endpoint_type with limit_name in check_rate_limit decorators
            # Pattern: @check_rate_limit(identifier="...", endpoint_type="...")
            # Replace with: @check_rate_limit(identifier="...", limit_name="...")

            # Use regex to replace only in decorator lines
            lines = content.split('\n')
            fixed_lines = []

            for line in lines:
                if '@check_rate_limit' in line and 'endpoint_type=' in line:
                    # Replace endpoint_type with limit_name
                    fixed_line = line.replace('endpoint_type=', 'limit_name=')
                    fixed_lines.append(fixed_line)
                    print(f"Fixed: {py_file}:{line.strip()}")
                else:
                    fixed_lines.append(line)

            content = '\n'.join(fixed_lines)

            # Only write if content changed
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"✓ Fixed: {py_file}")

        except Exception as e:
            error_count += 1
            print(f"✗ Error processing {py_file}: {e}")

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} files")
    if error_count > 0:
        print(f"Errors in {error_count} files")
    print(f"{'='*60}")

if __name__ == "__main__":
    endpoints_dir = Path("app/api/v1/endpoints")
    if not endpoints_dir.exists():
        print(f"Directory not found: {endpoints_dir}")
        exit(1)

    print("Fixing rate limiter signatures...")
    fix_rate_limiter_signatures(endpoints_dir)
    print("Done!")
