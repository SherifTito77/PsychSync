#!/usr/bin/env python3
"""
Pagination Limit Optimization Script

This script fixes pagination limits across all API endpoints to improve performance
and reduce memory usage. It reduces high limits (1000+) to reasonable values (100).

Usage:
    python scripts/fix_pagination_limits.py --dry-run  # Preview changes
    python scripts/fix_pagination_limits.py           # Apply changes
"""

import argparse
import re
from pathlib import Path


def fix_pagination_limits(file_path: Path, dry_run: bool = False) -> dict:
    """
    Fix pagination limits in a Python file.

    Args:
        file_path: Path to the Python file
        dry_run: If True, don't actually modify files

    Returns:
        Dictionary with fix statistics
    """
    changes = {"file": str(file_path), "fixes": [], "total_reductions": 0}

    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Pattern 1: Fix limit=Query(..., le=1000)
    pattern1 = r"(limit\s*:\s*int\s*=\s*Query\([^)]*le\s*=\s*)1000"
    replacement1 = r"\g<1>100"

    matches1 = re.finditer(pattern1, content)
    for match in matches1:
        changes["fixes"].append(
            {
                "type": "limit parameter",
                "old": "le=1000",
                "new": "le=100",
                "line": content[: match.start()].count("\n") + 1,
            }
        )
        changes["total_reductions"] += 1

    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: Fix Field(..., le=1000) for non-pagination fields
    # Only fix if it's clearly a batch size or similar
    pattern2 = r"((batch_size|max_emails|parallel_analysis_samples)\s*:\s*.*Field\([^)]*le\s*=\s*)1000"
    replacement2 = r"\g<1>200"

    matches2 = re.finditer(pattern2, content)
    for match in matches2:
        changes["fixes"].append(
            {
                "type": "batch/field parameter",
                "old": "le=1000",
                "new": "le=200",
                "line": content[: match.start()].count("\n") + 1,
            }
        )
        changes["total_reductions"] += 1

    content = re.sub(pattern2, replacement2, content)

    # Pattern 3: Fix limit=Query(..., le=500)
    pattern3 = r"(limit\s*:\s*int\s*=\s*Query\([^)]*le\s*=\s*)500"
    replacement3 = r"\g<1>200"

    matches3 = re.finditer(pattern3, content)
    for match in matches3:
        changes["fixes"].append(
            {
                "type": "limit parameter",
                "old": "le=500",
                "new": "le=200",
                "line": content[: match.start()].count("\n") + 1,
            }
        )
        changes["total_reductions"] += 1

    content = re.sub(pattern3, replacement3, content)

    # Write changes if not dry run and content changed
    if not dry_run and content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")

    elif dry_run and changes["total_reductions"] > 0:
        print(f"🔍 Would fix {file_path}:")
        for fix in changes["fixes"]:
            print(f"   Line {fix['line']}: {fix['type']}: {fix['old']} → {fix['new']}")

    return changes


def scan_and_fix(endpoints_dir: Path, dry_run: bool = False) -> dict:
    """
    Scan all endpoint files and fix pagination limits.

    Args:
        endpoints_dir: Directory containing endpoint files
        dry_run: If True, don't actually modify files

    Returns:
        Summary statistics
    """
    summary = {
        "files_scanned": 0,
        "files_with_fixes": 0,
        "total_fixes": 0,
        "fixes_by_type": {},
    }

    # Get all Python files in endpoints directory
    py_files = list(endpoints_dir.glob("*.py"))

    for py_file in py_files:
        summary["files_scanned"] += 1
        changes = fix_pagination_limits(py_file, dry_run)

        if changes["total_reductions"] > 0:
            summary["files_with_fixes"] += 1
            summary["total_fixes"] += changes["total_reductions"]

            for fix in changes["fixes"]:
                fix_type = fix["type"]
                if fix_type not in summary["fixes_by_type"]:
                    summary["fixes_by_type"][fix_type] = 0
                summary["fixes_by_type"][fix_type] += 1

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Fix pagination limits across API endpoints"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--endpoints-dir",
        type=Path,
        default=Path("/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints"),
        help="Directory containing endpoint files",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Pagination Limit Optimization")
    print("=" * 80)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print()

    summary = scan_and_fix(args.endpoints_dir, args.dry_run)

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files scanned: {summary['files_scanned']}")
    print(f"Files with fixes: {summary['files_with_fixes']}")
    print(f"Total fixes: {summary['total_fixes']}")
    print()

    if summary["fixes_by_type"]:
        print("Fixes by type:")
        for fix_type, count in sorted(summary["fixes_by_type"].items()):
            print(f"  - {fix_type}: {count}")

    print()

    if args.dry_run:
        print("To apply these changes, run:")
        print("  python scripts/fix_pagination_limits.py")
    else:
        print("✅ All pagination limits have been optimized!")
        print()
        print("Benefits:")
        print("  - Reduced memory usage per request")
        print("  - Faster response times")
        print("  - Better user experience with incremental loading")
        print()
        print("Recommendation: Deploy to staging and test before production")


if __name__ == "__main__":
    main()
