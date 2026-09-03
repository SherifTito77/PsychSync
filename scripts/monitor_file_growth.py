#!/usr/bin/env python3
"""
FILE GROWTH MONITORING
Tracks file size growth over time to detect code bloat

Maintains a history of file sizes and alerts when:
- Files exceed size thresholds
- Files grow rapidly between checks
- File complexity increases

Usage:
    python scripts/monitor_file_growth.py
    python scripts/monitor_file_growth.py --check app/api/v1/endpoints/users.py
    python scripts/monitor_file_growth.py --update-baseline
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class FileGrowthMonitor:
    """Monitors file growth over time"""

    def __init__(self, baseline_file: str = ".file_size_baseline.json"):
        self.baseline_file = Path(baseline_file)
        self.baseline = self._load_baseline()
        self.thresholds = {
            "warning": 500,  # Lines
            "critical": 1000,  # Lines
            "unmanageable": 1500,  # Lines
        }

    def _load_baseline(self) -> Dict:
        """Load baseline file sizes from JSON"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_baseline(self):
        """Save baseline to JSON"""
        with open(self.baseline_file, "w") as f:
            json.dump(self.baseline, f, indent=2)

    def count_lines(self, file_path: Path) -> int:
        """Count non-empty lines in a file"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(
                    1 for line in f if line.strip() and not line.strip().startswith("#")
                )
        except:
            return 0

    def check_file(self, file_path: str) -> Dict:
        """Check a single file for growth"""
        path = Path(file_path).resolve()
        if not path.exists():
            return None

        current_lines = self.count_lines(path)

        # Try to get relative path from current directory or parent directories
        try:
            relative_path = str(path.relative_to(Path.cwd()))
        except ValueError:
            # File not under current directory, use absolute path
            relative_path = str(path)

        # Get baseline data
        baseline_data = self.baseline.get(relative_path, {})
        previous_lines = baseline_data.get("lines", 0)
        previous_check = baseline_data.get("last_checked", "Never")

        # Calculate growth
        growth = current_lines - previous_lines
        growth_percent = (growth / previous_lines * 100) if previous_lines > 0 else 0

        # Determine status
        status = "✅"
        if current_lines > self.thresholds["unmanageable"]:
            status = "🔴"
        elif current_lines > self.thresholds["critical"]:
            status = "⚠️"
        elif current_lines > self.thresholds["warning"]:
            status = "📊"

        # Rapid growth detection
        rapid_growth = growth_percent > 50 and growth > 50

        return {
            "file": relative_path,
            "lines": current_lines,
            "previous_lines": previous_lines,
            "growth": growth,
            "growth_percent": growth_percent,
            "last_checked": previous_check,
            "status": status,
            "rapid_growth": rapid_growth,
            "recommendation": self._get_recommendation(current_lines, growth_percent),
        }

    def check_app_files(self, app_dir: str = "app/api/v1/endpoints") -> List[Dict]:
        """Check all files in a directory"""
        results = []
        app_path = Path(app_dir)

        if not app_path.exists():
            return results

        for file_path in app_path.rglob("*.py"):
            if "__pycache__" in str(file_path) or file_path.name.startswith("__"):
                continue

            result = self.check_file(file_path)
            if result:
                results.append(result)

        return sorted(results, key=lambda x: x["lines"], reverse=True)

    def update_baseline(self, app_dir: str = "app"):
        """Update baseline with current file sizes"""
        print("📝 Updating baseline file sizes...")
        print()

        app_path = Path(app_dir).resolve()
        count = 0

        for file_path in app_path.rglob("*.py"):
            if "__pycache__" in str(file_path) or file_path.name.startswith("__"):
                continue

            # Try to get relative path
            try:
                relative_path = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                relative_path = str(file_path)

            lines = self.count_lines(file_path)

            self.baseline[relative_path] = {
                "lines": lines,
                "last_checked": datetime.now().isoformat(),
            }
            count += 1

        self._save_baseline()
        print(f"✅ Baseline updated with {count} files")
        print(f"   Saved to: {self.baseline_file}")

    def _get_recommendation(self, lines: int, growth_percent: float) -> str:
        """Get recommendation based on file metrics"""
        if lines > self.thresholds["unmanageable"]:
            return "SPLIT IMMEDIATELY - File is too large to maintain"
        elif lines > self.thresholds["critical"]:
            return "Consider splitting into multiple modules"
        elif lines > self.thresholds["warning"]:
            return "Monitor growth - consider splitting if continues"
        elif growth_percent > 50 and growth_percent > 50:
            return f"Rapid growth ({growth_percent:.0f}%)- review recent changes"
        return "Size acceptable - continue monitoring"

    def print_report(self, results: List[Dict], show_all: bool = False):
        """Print file growth report"""
        print("=" * 80)
        print("FILE GROWTH MONITORING REPORT")
        print("=" * 80)
        print()

        if not results:
            print("No files to check")
            return

        # Summary
        total_lines = sum(r["lines"] for r in results)
        total_growth = sum(r["growth"] for r in results if r["growth"] > 0)

        critical = [r for r in results if r["status"] in ["🔴", "⚠️"]]
        rapid_growth = [r for r in results if r["rapid_growth"]]

        print(f"📊 SUMMARY:")
        print(f"   Files checked: {len(results)}")
        print(f"   Total lines: {total_lines}")
        print(f"   Total growth: {total_growth} lines")
        print()

        # Critical files
        if critical:
            print(f"⚠️  CRITICAL FILES ({len(critical)}):")
            print()
            for result in critical[:10]:
                print(f"   {result['status']} {result['file']}")
                print(
                    f"       {result['lines']} lines ({result['growth']:+d} from last check)"
                )
                print(f"       💡 {result['recommendation']}")
                print()

            if len(critical) > 10:
                print(f"   ... and {len(critical) - 10} more")
                print()
        else:
            print("✅ No critical files found!")
            print()

        # Rapid growth
        if rapid_growth:
            print(f"📈 RAPID GROWTH ({len(rapid_growth)}):")
            print()
            for result in rapid_growth[:5]:
                print(f"   {result['file']}")
                print(
                    f"       {result['growth']:+d} lines ({result['growth_percent']:+.0f}%)"
                )
                print(f"       💡 {result['recommendation']}")
                print()
            print()

        # All files (if requested)
        if show_all:
            print("=" * 80)
            print("ALL FILES (sorted by size)")
            print("=" * 80)
            print()

            for i, result in enumerate(results, 1):
                growth_str = f"({result['growth']:+d})" if result["growth"] != 0 else ""
                print(
                    f"   {i:3}. {result['status']} {result['lines']:4} lines {growth_str:>8}"
                )
                print(f"       {result['file']}")
                print()
        else:
            # Top 10 largest files
            print("=" * 80)
            print("TOP 10 LARGEST FILES")
            print("=" * 80)
            print()

            for i, result in enumerate(results[:10], 1):
                growth_str = f"({result['growth']:+d})" if result["growth"] != 0 else ""
                print(
                    f"   {i:2}. {result['status']} {result['lines']:4} lines {growth_str:>8}"
                )
                print(f"       {result['file']}")

            print()
            print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Monitor Python file growth")
    parser.add_argument("--check", help="Check specific file")
    parser.add_argument(
        "--app-dir",
        default="app/api/v1/endpoints",
        help="Directory to check (default: app/api/v1/endpoints)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline with current file sizes",
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Show all files, not just top 10"
    )

    args = parser.parse_args()

    monitor = FileGrowthMonitor()

    if args.update_baseline:
        monitor.update_baseline()
        return 0

    if args.check:
        result = monitor.check_file(args.check)
        if result:
            print(f"File: {result['file']}")
            print(f"Lines: {result['lines']}")
            print(f"Status: {result['status']}")
            print(f"Recommendation: {result['recommendation']}")
        return 0

    # Check all files in directory
    results = monitor.check_app_files(args.app_dir)
    monitor.print_report(results, show_all=args.all)

    # Return exit code based on critical files
    critical_count = len([r for r in results if r["status"] in ["🔴", "⚠️"]])
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
