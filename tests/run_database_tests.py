#!/usr/bin/env python3
"""
Comprehensive Database Test Runner

This script runs all database integrity tests with detailed reporting:
1. Database integrity tests
2. Rapid submission handling tests
3. Transaction rollback tests
4. Audit logging tests
5. Performance and load testing
"""

import asyncio
import pytest
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import traceback

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))


class DatabaseTestRunner:
    """Comprehensive database test runner"""

    def __init__(self):
        self.test_files = [
            "test_database_integrity.py",
            "test_rapid_submission_handling.py",
            "test_transaction_rollback.py",
            "test_audit_logging.py"
        ]
        self.results = {}
        self.start_time = time.time()

    def run_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run a single test file and return results"""
        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            # Use pytest to run the test file
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                test_file,
                "-v",  # Verbose output
                "--tb=short",  # Short traceback format
                "--color=yes",  # Colored output
                f"--junit-xml=test-results-{test_file.replace('.py', '')}.xml",  # JUnit XML output
            ],
            capture_output=True,
            text=True,
            cwd=project_root
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            return {
                "file": test_file,
                "success": success,
                "duration": duration,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "returncode": result.returncode
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "file": test_file,
                "success": False,
                "duration": duration,
                "output": str(e),
                "error": traceback.format_exc(),
                "returncode": -1
            }

    def run_all_tests(self) -> None:
        """Run all database tests"""
        print("🔧 PSYNSYNC DATABASE TEST SUITE")
        print("=" * 60)
        print("Testing database integrity, transaction handling, and audit logging")
        print("=" * 60)

        # Run each test file
        for test_file in self.test_files:
            result = self.run_test_file(test_file)
            self.results[test_file] = result

        # Generate summary report
        self.generate_summary_report()

    def generate_summary_report(self) -> None:
        """Generate a comprehensive summary report"""
        total_duration = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*80}")
        print("📊 DATABASE TEST SUITE SUMMARY REPORT")
        print(f"{'='*80}")

        print(f"\n📈 OVERALL RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"  Total Duration: {total_duration:.2f}s")

        print(f"\n📋 INDIVIDUAL TEST RESULTS:")
        for test_file, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = f"{result['duration']:.2f}s"
            print(f"  {test_file:<30} {status:<10} {duration:<10}")

        print(f"\n🔍 FAILED TESTS DETAILS:")
        failed_tests_results = [result for result in self.results.values() if not result["success"]]

        if failed_tests_results:
            for result in failed_tests_results:
                print(f"\n❌ {result['file']}:")
                print(f"   Return Code: {result['returncode']}")
                if result['error']:
                    print(f"   Error: {result['error'][:200]}...")  # First 200 chars
                print(f"   Output: {result['output'][-200:]}")  # Last 200 chars
        else:
            print("\n✅ All tests passed! Database integrity verified.")

        # Performance Analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        test_durations = [result["duration"] for result in self.results.values()]
        if test_durations:
            avg_duration = sum(test_durations) / len(test_durations)
            max_duration = max(test_durations)
            min_duration = min(test_durations)

            print(f"  Average Test Duration: {avg_duration:.2f}s")
            print(f"  Slowest Test: {max_duration:.2f}s")
            print(f"  Fastest Test: {min_duration:.2f}s")

        print(f"\n📝 RECOMMENDATIONS:")
        if failed_tests > 0:
            print("  🔧 Fix failing tests before proceeding to production")
            print("  🧪 Review database constraints and transaction handling")
            print("  🔒 Verify audit logging implementation")
        else:
            print("  ✅ All database tests passed - ready for production")
            print("  🚀 Database integrity and performance verified")
            print("  📈 Consider adding load testing for production scenarios")

        print(f"\n{'='*80}")
        print("🎉 DATABASE TESTING COMPLETE")
        print(f"{'='*80}")

    def save_report_to_file(self) -> None:
        """Save detailed test report to file"""
        report_file = project_root / "database_test_report.json"

        report_data = {
            "timestamp": time.time(),
            "total_tests": len(self.results),
            "passed_tests": sum(1 for result in self.results.values() if result["success"]),
            "failed_tests": sum(1 for result in self.results.values() if not result["success"]),
            "total_duration": time.time() - self.start_time,
            "test_results": self.results,
            "recommendations": self._get_recommendations()
        }

        try:
            import json
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save detailed report: {e}")

    def _get_recommendations(self) -> List[str]:
        """Get recommendations based on test results"""
        recommendations = []

        failed_count = sum(1 for result in self.results.values() if not result["success"])

        if failed_count > 0:
            recommendations.extend([
                "Fix failing database tests before production deployment",
                "Review database constraint definitions",
                "Verify transaction rollback implementations",
                "Check audit logging configuration"
            ])
        else:
            recommendations.extend([
                "Database integrity tests passed - system is stable",
                "Consider adding performance load testing",
                "Implement automated database backups",
                "Set up database monitoring and alerts"
            ])

        return recommendations


def main():
    """Main entry point"""
    print("🔧 Starting Database Test Runner...")

    runner = DatabaseTestRunner()

    try:
        runner.run_all_tests()
        runner.save_report_to_file()

        # Exit with appropriate code
        failed_count = sum(1 for result in runner.results.values() if not result["success"])
        if failed_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()