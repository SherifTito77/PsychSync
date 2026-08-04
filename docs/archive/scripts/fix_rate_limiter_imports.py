#!/usr/bin/env python3
"""
Fix rate limiter imports across all endpoint files.
Replaces old check_rate_limit imports with new rate_limit decorator.
"""

import re
from pathlib import Path


def fix_rate_limiter_imports(file_path: Path) -> bool:
    """Fix rate limiter imports in a single file."""
    try:
        content = file_path.read_text()
        original_content = content

        # Pattern 1: Replace check_rate_limit import
        pattern1 = r"from app\.core\.rate_limiter_unified import.*check_rate_limit"
        replacement1 = (
            "from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy"
        )
        content = re.sub(pattern1, replacement1, content)

        # Pattern 2: Replace @check_rate_limit decorator with new syntax
        # Old: @check_rate_limit(identifier="public", limit_name="public")
        # New: @rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
        pattern2 = r'@check_rate_limit\(identifier="([^"]+)", limit_name="([^"]+)"\)'
        replacement2 = r"@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)"
        content = re.sub(pattern2, replacement2, content)

        # Pattern 3: Replace old RateLimiter import if it exists
        pattern3 = r"from app\.middleware\.rate_limiter import.*RateLimiter"
        replacement3 = "from app.core.rate_limiter_unified import UnifiedRateLimiter"
        content = re.sub(pattern3, replacement3, content)

        if content != original_content:
            file_path.write_text(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Fix all rate limiter imports in the endpoints directory."""
    endpoints_dir = Path("app/api/v1/endpoints")

    if not endpoints_dir.exists():
        print(f"Directory {endpoints_dir} not found!")
        return

    py_files = list(endpoints_dir.glob("*.py"))
    print(f"Found {len(py_files)} Python files in {endpoints_dir}")

    fixed_count = 0
    for file_path in py_files:
        if fix_rate_limiter_imports(file_path):
            print(f"✓ Fixed: {file_path.name}")
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}/{len(py_files)}")


if __name__ == "__main__":
    main()
