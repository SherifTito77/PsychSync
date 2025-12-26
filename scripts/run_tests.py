#!/usr/bin/env python3
"""
Comprehensive test runner script for PsychSync
- Multiple test scenarios and configurations
- Performance monitoring and reporting
- Test result analysis and notifications
- Parallel execution support
- Integration with CI/CD pipelines
"""

import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import multiprocessing


class TestRunner:
    """Comprehensive test runner with multiple configurations"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}
        self.start_time = time.time()

    def run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """Run a command and capture results"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            print(f"\n✅ {'SUCCESS' if success else 'FAILED'} - {duration:.2f}s")
            if not success:
                print(f"❌ Return code: {result.returncode}")
                print("STDOUT:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
                print("STDERR:", result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)

            return {
                "success": success,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT after 300 seconds")
            return {
                "success": False,
                "duration": 300,
                "stdout": "",
                "stderr": "Test run timed out after 300 seconds",
                "returncode": -1
            }

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {
                "success": False,
                "duration": 0,
                "stdout": "",
                "stderr": str(e),
                "returncode": -2
            }

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests only"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "unit",
            "--tb=short",
            "-v",
            "--cov=app",
            "--cov-report=term-missing:skip-covered",
            "--cov-report=html:htmlcov_unit",
            "tests/"
        ]
        return self.run_command(cmd, "Unit Tests")

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "integration",
            "--tb=short",
            "-v",
            "--cov=app",
            "--cov-append",
            "--cov-report=html:htmlcov_integration",
            "tests/"
        ]
        return self.run_command(cmd, "Integration Tests")

    def run_auth_tests(self) -> Dict[str, Any]:
        """Run authentication tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "auth",
            "--tb=short",
            "-v",
            "tests/test_auth_comprehensive.py"
        ]
        return self.run_command(cmd, "Authentication Tests")

    def run_api_tests(self) -> Dict[str, Any]:
        """Run API endpoint tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "api",
            "--tb=short",
            "-v",
            "tests/test_api_endpoints_comprehensive.py"
        ]
        return self.run_command(cmd, "API Endpoint Tests")

    def run_service_tests(self) -> Dict[str, Any]:
        """Run service layer tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "service",
            "--tb=short",
            "-v",
            "tests/test_services_comprehensive.py"
        ]
        return self.run_command(cmd, "Service Layer Tests")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests with full coverage"""
        cmd = [
            sys.executable, "-m", "pytest",
            "--tb=short",
            "-v",
            "--cov=app",
            "--cov-report=html:htmlcov_full",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--junit-xml=test-results.xml",
            "tests/"
        ]
        return self.run_command(cmd, "All Tests")

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "performance",
            "--tb=short",
            "-v",
            "--durations=0",
            "tests/"
        ]
        return self.run_command(cmd, "Performance Tests")

    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "security",
            "--tb=short",
            "-v",
            "tests/"
        ]
        return self.run_command(cmd, "Security Tests")

    def run_slow_tests(self) -> Dict[str, Any]:
        """Run slow tests (for CI/nightly runs)"""
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "slow",
            "--tb=short",
            "-v",
            "tests/"
        ]
        return self.run_command(cmd, "Slow Tests")

    def run_specific_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run a specific test file"""
        cmd = [
            sys.executable, "-m", "pytest",
            "--tb=short",
            "-v",
            test_file
        ]
        return self.run_command(cmd, f"Specific Test File: {test_file}")

    def run_parallel_tests(self, workers: Optional[int] = None) -> Dict[str, Any]:
        """Run tests in parallel"""
        if workers is None:
            workers = multiprocessing.cpu_count()

        cmd = [
            sys.executable, "-m", "pytest",
            "--tb=short",
            "-v",
            f"-n={workers}",
            "--dist=loadscope",
            "tests/"
        ]
        return self.run_command(cmd, f"Parallel Tests ({workers} workers)")

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        total_tests = 0
        total_passed = 0
        total_failed = 0

        report = [
            "\n" + "="*80,
            "PSYCHSYNC TEST SUITE REPORT",
            "="*80,
            f"Total Duration: {total_duration:.2f} seconds",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        for test_name, result in self.results.items():
            if result["success"]:
                status = "✅ PASSED"
                total_passed += 1
            else:
                status = "❌ FAILED"
                total_failed += 1

            total_tests += 1
            report.append(f"{test_name:30} {status:10} {result['duration']:.2f}s")

        report.extend([
            "",
            "-"*80,
            f"SUMMARY: {total_passed}/{total_tests} test suites passed",
            f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A",
            f"Total Failed: {total_failed}",
            "="*80
        ])

        return "\n".join(report)

    def save_results(self, filename: str = "test_results.json"):
        """Save test results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_duration": time.time() - self.start_time,
                "results": self.results
            }, f, indent=2)
        print(f"📊 Test results saved to {filename}")

    def run_ci_pipeline(self) -> bool:
        """Run complete CI test pipeline"""
        print("🚀 Starting CI Test Pipeline")

        test_sequence = [
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),
            ("auth", self.run_auth_tests),
            ("api", self.run_api_tests),
            ("service", self.run_service_tests),
        ]

        all_passed = True
        for test_name, test_func in test_sequence:
            result = test_func()
            self.results[test_name] = result
            if not result["success"]:
                all_passed = False
                print(f"❌ CI Pipeline failed at {test_name} stage")
                break

        # Generate report
        print(self.generate_test_report())
        self.save_results("ci_test_results.json")

        return all_passed

    def run_development_checks(self) -> bool:
        """Run quick development checks"""
        print("⚡ Running Development Test Checks")

        test_sequence = [
            ("unit", self.run_unit_tests),
            ("auth", self.run_auth_tests),
        ]

        all_passed = True
        for test_name, test_func in test_sequence:
            result = test_func()
            self.results[test_name] = result
            if not result["success"]:
                all_passed = False

        print(self.generate_test_report())
        return all_passed

    def run_pre_commit_checks(self, file_path: str) -> bool:
        """Run tests relevant to changed files"""
        print(f"🔍 Running Pre-commit Checks for {file_path}")

        if "auth" in file_path or "user" in file_path:
            result = self.run_auth_tests()
        elif "api" in file_path:
            result = self.run_api_tests()
        elif "service" in file_path:
            result = self.run_service_tests()
        else:
            result = self.run_unit_tests()

        self.results["pre_commit"] = result
        print(self.generate_test_report())
        return result["success"]


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="PsychSync Test Runner")
    parser.add_argument(
        "command",
        choices=[
            "unit", "integration", "auth", "api", "service",
            "all", "performance", "security", "slow", "ci", "dev", "parallel"
        ],
        help="Test command to run"
    )
    parser.add_argument(
        "--file", "-f",
        help="Run specific test file"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        help="Number of parallel workers (for parallel command)"
    )
    parser.add_argument(
        "--output", "-o",
        default="test_results.json",
        help="Output file for test results"
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Skip coverage reporting"
    )

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Initialize test runner
    runner = TestRunner(project_root)

    # Set environment variables
    os.environ["TESTING"] = "true"
    if args.no_cov:
        os.environ["SKIP_COVERAGE"] = "true"

    # Run requested tests
    success = True

    try:
        if args.command == "unit":
            result = runner.run_unit_tests()
            runner.results["unit"] = result
            success = result["success"]

        elif args.command == "integration":
            result = runner.run_integration_tests()
            runner.results["integration"] = result
            success = result["success"]

        elif args.command == "auth":
            result = runner.run_auth_tests()
            runner.results["auth"] = result
            success = result["success"]

        elif args.command == "api":
            result = runner.run_api_tests()
            runner.results["api"] = result
            success = result["success"]

        elif args.command == "service":
            result = runner.run_service_tests()
            runner.results["service"] = result
            success = result["success"]

        elif args.command == "all":
            result = runner.run_all_tests()
            runner.results["all"] = result
            success = result["success"]

        elif args.command == "performance":
            result = runner.run_performance_tests()
            runner.results["performance"] = result
            success = result["success"]

        elif args.command == "security":
            result = runner.run_security_tests()
            runner.results["security"] = result
            success = result["success"]

        elif args.command == "slow":
            result = runner.run_slow_tests()
            runner.results["slow"] = result
            success = result["success"]

        elif args.command == "ci":
            success = runner.run_ci_pipeline()

        elif args.command == "dev":
            success = runner.run_development_checks()

        elif args.command == "parallel":
            result = runner.run_parallel_tests(args.workers)
            runner.results["parallel"] = result
            success = result["success"]

        elif args.file:
            result = runner.run_specific_test_file(args.file)
            runner.results["specific"] = result
            success = result["success"]

        # Generate and save results
        if runner.results:
            print(runner.generate_test_report())
            runner.save_results(args.output)

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        success = False

    except Exception as e:
        print(f"\n❌ Test runner error: {str(e)}")
        success = False

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()