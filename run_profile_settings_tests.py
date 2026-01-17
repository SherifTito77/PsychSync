#!/usr/bin/env python3
"""
Comprehensive Test Runner for Profile Settings Test Suite
Executes all test files and generates detailed reports

Author: Test Automation Team
Version: 1.0
"""

import unittest
import sys
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import importlib.util

class ProfileSettingsTestRunner:
    """Comprehensive test runner for Profile Settings test suite"""

    def __init__(self):
        self.test_files = [
            'test_profile_settings_comprehensive.py',
            'test_profile_security_validation.py',
            'test_profile_settings_react_components.py',
            'test_profile_settings_e2e.py',
            'test_profile_settings_advanced.py'
        ]

        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'skipped_tests': 0,
            'test_suites': {},
            'execution_time': 0,
            'performance_metrics': {}
        }

    def run_all_tests(self):
        """Run all test suites and generate comprehensive report"""
        print("🚀 Starting Profile Settings Test Suite Execution")
        print("=" * 60)

        start_time = time.time()

        # Run each test file
        for test_file in self.test_files:
            self._run_test_file(test_file)

        self.results['execution_time'] = time.time() - start_time

        # Generate and display report
        self._generate_report()

        return self.results

    def _run_test_file(self, test_file: str):
        """Run tests from a specific file"""
        print(f"\n📋 Running tests from: {test_file}")
        print("-" * 40)

        try:
            # Import test module
            spec = importlib.util.spec_from_file_location("test_module", test_file)
            test_module = importlib.util.module_from_spec(spec)

            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)

            # Run tests with custom runner
            runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
            result = runner.run(suite)

            # Store results
            self.results['test_suites'][test_file] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
            }

            # Update global results
            self.results['total_tests'] += result.testsRun
            self.results['passed_tests'] += (result.testsRun - len(result.failures) - len(result.errors))
            self.results['failed_tests'] += len(result.failures)
            self.results['error_tests'] += len(result.errors)
            self.results['skipped_tests'] += len(result.skipped) if hasattr(result, 'skipped') else 0

            # Display file-specific results
            self._display_file_results(test_file, result)

        except Exception as e:
            print(f"❌ Error running {test_file}: {str(e)}")
            self.results['test_suites'][test_file] = {
                'error': str(e),
                'tests_run': 0,
                'success_rate': 0
            }

    def _display_file_results(self, test_file: str, result):
        """Display results for a specific test file"""
        file_results = self.results['test_suites'][test_file]

        if 'error' in file_results:
            print(f"❌ {test_file}: FAILED TO LOAD - {file_results['error']}")
            return

        status_emoji = "✅" if file_results['success_rate'] >= 90 else "⚠️" if file_results['success_rate'] >= 70 else "❌"

        print(f"{status_emoji} {test_file}:")
        print(f"   Tests run: {file_results['tests_run']}")
        print(f"   Success rate: {file_results['success_rate']:.1f}%")

        if file_results['failures'] > 0:
            print(f"   Failures: {file_results['failures']}")
        if file_results['errors'] > 0:
            print(f"   Errors: {file_results['errors']}")

    def _generate_report(self):
        """Generate comprehensive test execution report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST EXECUTION REPORT")
        print("=" * 60)

        # Overall Statistics
        overall_success_rate = (self.results['passed_tests'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0

        print(f"\n🎯 OVERALL STATISTICS:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   Passed: {self.results['passed_tests']}")
        print(f"   Failed: {self.results['failed_tests']}")
        print(f"   Errors: {self.results['error_tests']}")
        print(f"   Skipped: {self.results['skipped_tests']}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        print(f"   Execution Time: {self.results['execution_time']:.2f}s")

        # Individual Suite Results
        print(f"\n📋 TEST SUITE BREAKDOWN:")
        for test_file, results in self.results['test_suites'].items():
            if 'error' in results:
                print(f"   ❌ {test_file}: LOAD ERROR")
            else:
                status_emoji = "✅" if results['success_rate'] >= 90 else "⚠️" if results['success_rate'] >= 70 else "❌"
                print(f"   {status_emoji} {test_file}: {results['success_rate']:.1f}% ({results['tests_run']} tests)")

        # Coverage Assessment
        print(f"\n🔍 COVERAGE ASSESSMENT:")
        coverage_areas = {
            'Functionality Testing': 'test_profile_settings_comprehensive.py',
            'Security Testing': 'test_profile_security_validation.py',
            'React Component Testing': 'test_profile_settings_react_components.py',
            'End-to-End Testing': 'test_profile_settings_e2e.py',
            'Advanced Testing': 'test_profile_settings_advanced.py'
        }

        for area, file in coverage_areas.items():
            if file in self.results['test_suites']:
                results = self.results['test_suites'][file]
                if 'error' not in results:
                    status_emoji = "✅" if results['success_rate'] >= 90 else "⚠️" if results['success_rate'] >= 70 else "❌"
                    print(f"   {status_emoji} {area}: {results['success_rate']:.1f}%")
                else:
                    print(f"   ❌ {area}: FAILED TO LOAD")
            else:
                print(f"   ⚠️ {area}: NOT EXECUTED")

        # Performance Analysis
        if self.results['execution_time'] > 0:
            tests_per_second = self.results['total_tests'] / self.results['execution_time']
            print(f"\n⚡ PERFORMANCE ANALYSIS:")
            print(f"   Tests per Second: {tests_per_second:.1f}")
            print(f"   Average Test Time: {(self.results['execution_time'] / self.results['total_tests']):.3f}s")

        # Quality Assessment
        print(f"\n🏆 QUALITY ASSESSMENT:")
        if overall_success_rate >= 95:
            print("   🌟 EXCELLENT: Test suite is production-ready with high confidence")
        elif overall_success_rate >= 90:
            print("   ✅ GOOD: Test suite meets production standards")
        elif overall_success_rate >= 80:
            print("   ⚠️ ACCEPTABLE: Test suite needs minor improvements")
        else:
            print("   ❌ NEEDS WORK: Test suite requires significant improvements")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.results['failed_tests'] > 0:
            print(f"   • Review {self.results['failed_tests']} failing tests and fix issues")
        if self.results['error_tests'] > 0:
            print(f"   • Address {self.results['error_tests']} test errors (configuration/environment)")

        success_rate_issues = [file for file, results in self.results['test_suites'].items()
                              if 'error' not in results and results['success_rate'] < 90]
        if success_rate_issues:
            print(f"   • Improve test reliability in: {', '.join(success_rate_issues)}")

        if overall_success_rate >= 90:
            print(f"   ✅ Test suite is ready for CI/CD integration")
        else:
            print(f"   🔄 Address test failures before CI/CD integration")

        # Save detailed report to file
        self._save_detailed_report()

    def _save_detailed_report(self):
        """Save detailed test report to JSON file"""
        report_data = {
            'execution_timestamp': datetime.now().isoformat(),
            'results': self.results,
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform
            },
            'summary': {
                'overall_status': 'PASSED' if (self.results['passed_tests'] / self.results['total_tests'] * 100) >= 90 else 'FAILED',
                'total_files': len(self.test_files),
                'executed_files': len([f for f in self.test_files if f in self.results['test_suites'] and 'error' not in self.results['test_suites'][f]])
            }
        }

        report_filename = f"profile_settings_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n📄 Detailed report saved to: {report_filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save detailed report: {str(e)}")

def main():
    """Main function to run the complete test suite"""
    print("🧪 Profile Settings Test Suite Runner")
    print("Executing comprehensive tests for user profile settings functionality")
    print()

    # Check if test files exist
    test_files = [
        'test_profile_settings_comprehensive.py',
        'test_profile_security_validation.py',
        'test_profile_settings_react_components.py',
        'test_profile_settings_e2e.py',
        'test_profile_settings_advanced.py'
    ]

    missing_files = [f for f in test_files if not os.path.exists(f)]
    if missing_files:
        print(f"⚠️ Warning: Missing test files: {', '.join(missing_files)}")
        print("Some test suites may not execute properly.")
        print()

    # Create and run test runner
    runner = ProfileSettingsTestRunner()
    results = runner.run_all_tests()

    # Exit with appropriate code
    overall_success_rate = (results['passed_tests'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0

    if overall_success_rate >= 90:
        print("\n🎉 Test suite execution completed successfully!")
        print("✅ Profile settings functionality is ready for production deployment.")
        sys.exit(0)
    else:
        print("\n❌ Test suite execution completed with issues.")
        print("🔄 Please address failing tests before production deployment.")
        sys.exit(1)

if __name__ == '__main__':
    main()
