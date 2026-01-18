#!/usr/bin/env python3
"""
Incremental Linting Fixes for PsychSync
Automatically fixes common linting issues in batches

Usage:
    python scripts/fix_linting_incremental.py [--batch-size 100]
"""

import subprocess
import sys
import argparse
from pathlib import Path
import time

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*70}")
    print(f"🔧 {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}")

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start

    if result.returncode == 0:
        print(f"✅ Success in {duration:.1f}s")
        if result.stdout:
            print(result.stdout[:500])
    else:
        print(f"⚠️  Exit code {result.returncode} in {duration:.1f}s")
        if result.stderr:
            print(result.stderr[:500])

    return result

def count_issues():
    """Count total linting issues"""
    result = subprocess.run(
        ["ruff", "check", "app/", "--output-format=json"],
        capture_output=True,
        text=True
    )

    if result.returncode in [0, 1]:
        import json
        try:
            data = json.loads(result.stdout)
            return len(data)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            pass

    return "unknown"

def main():
    parser = argparse.ArgumentParser(description="Fix linting issues incrementally")
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Number of files to process per batch")
    parser.add_argument("--unsafe", action="store_true",
                       help="Apply unsafe fixes as well")
    args = parser.parse_args()

    print("🚀 Incremental Linting Fixes for PsychSync")
    print("="*70)

    # Count initial issues
    initial_count = count_issues()
    print(f"📊 Initial linting issues: {initial_count}")

    # Define fix batches in order of safety
    fix_batches = [
        {
            "name": "Import organization and deprecated type hints",
            "args": ["--fix"],
            "description": "Fix imports and type annotations"
        },
        {
            "name": "Quote style (Q000 - double quotes)",
            "args": ["--fix", "--select", "Q"],
            "description": "Standardize to double quotes"
        },
        {
            "name": "Modern type hints (UP006, UP035, UP045)",
            "args": ["--fix", "--select", "UP"],
            "description": "Use modern type annotations"
        },
        {
            "name": "Unused imports (F401)",
            "args": ["--fix", "--select", "F401"],
            "description": "Remove unused imports"
        },
        {
            "name": "Whitespace cleanup (W293, E501)",
            "args": ["--fix", "--select", "W,E501"],
            "description": "Fix whitespace and line length"
        },
    ]

    if args.unsafe:
        fix_batches.append({
            "name": "Logging best practices (G004, TRY400)",
            "args": ["--fix", "--unsafe-fixes", "--select", "G,TRY4"],
            "description": "Fix logging statements"
        })

    # Apply fixes in batches
    for i, batch in enumerate(fix_batches, 1):
        print(f"\n📍 Batch {i}/{len(fix_batches)}: {batch['name']}")
        print(f"   {batch['description']}")

        cmd = ["ruff", "check", "app/"] + batch["args"]
        result = run_command(cmd, batch['description'])

    # Count final issues
    final_count = count_issues()
    improvements = initial_count - final_count if isinstance(initial_count, int) and isinstance(final_count, int) else "many"

    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    print(f"Initial issues:  {initial_count}")
    print(f"Remaining issues: {final_count}")
    print(f"Issues resolved: {improvements}")

    # Show remaining top issues
    print("\n🔍 Top remaining issues:")
    result = subprocess.run(
        ["ruff", "check", "app/", "--output-format=json"],
        capture_output=True,
        text=True
    )

    if result.returncode in [0, 1]:
        import json
        try:
            data = json.loads(result.stdout)
            codes = {}
            for item in data:
                codes[item['code']] = codes.get(item['code'], 0) + 1

            top_issues = sorted(codes.items(), key=lambda x: -x[1])[:5]
            for code, count in top_issues:
                print(f"  {code}: {count}")
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            pass

    print("\n✅ Linting fixes complete!")
    print("\n💡 Next steps:")
    print("  1. Review the changes with: git diff")
    print("  2. Run tests to ensure nothing broke: pytest tests/")
    print("  3. Commit the fixes: git add . && git commit -m 'fix: apply linting improvements'")

if __name__ == "__main__":
    main()
