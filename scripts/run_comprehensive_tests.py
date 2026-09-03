#!/usr/bin/env python3
"""
COMPREHENSIVE TEST EXECUTION SCRIPT
Enterprise test runner with reporting and analytics

TEST EXECUTION FEATURES:
- Multi-category test execution
- Coverage reporting and analysis
- Performance benchmarking
- Security vulnerability scanning
- Test result analytics
- HTML report generation
- Integration with CI/CD pipelines

Author: Security Team
Version: 2.0 Enterprise Security
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("test_execution.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@dataclass
class TestSuiteResult:
    """Test suite execution result"""

    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    execution_time: float
    coverage_percent: float
    details: Dict[str, Any] = None


@dataclass
class ComprehensiveTestReport:
    """Comprehensive test execution report"""

    timestamp: datetime
    total_execution_time: float
    test_suites: List[TestSuiteResult]
    overall_passed: int
    overall_failed: int
    overall_total: int
    overall_coverage: float
    performance_metrics: Dict[str, Any]
    security_scan_results: Dict[str, Any]
    recommendations: List[str]


class TestExecutor:
    """Enterprise test execution engine"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[TestSuiteResult] = []
        self.start_time = datetime.utcnow()

    async def run_unit_tests(self) -> TestSuiteResult:
        """Run unit test suite"""
        logger.info("Executing unit test suite...")
        start_time = time.time()

        try:
            # Run pytest with coverage for unit tests
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/",
                "tests/services/",
                "tests/repositories/",
                "-v",
                "--tb=short",
                "--cov=app",
                "--cov-report=json:reports/coverage_unit.json",
                "--cov-report=html:reports/htmlcov_unit",
                "--cov-report=term-missing",
                "--junitxml=reports/unit_tests.xml",
                "-m",
                "unit",
            ]

            # Ensure reports directory exists
            (self.project_root / "reports").mkdir(exist_ok=True)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            execution_time = time.time() - start_time

            # Parse results
            result = self._parse_pytest_output(
                process.returncode, stdout.decode(), stderr.decode()
            )
            coverage_data = self._parse_coverage_report("reports/coverage_unit.json")

            suite_result = TestSuiteResult(
                name="Unit Tests",
                total_tests=result.get("total", 0),
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", 0),
                execution_time=execution_time,
                coverage_percent=coverage_data.get("percent_covered", 0),
                details={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "coverage_data": coverage_data,
                },
            )

            self.results.append(suite_result)
            logger.info(
                f"Unit tests completed: {suite_result.passed}/{suite_result.total} passed"
            )

            return suite_result

        except Exception as e:
            logger.error(f"Unit test execution failed: {e}")
            error_result = TestSuiteResult(
                name="Unit Tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                execution_time=time.time() - start_time,
                coverage_percent=0,
                details={"error": str(e)},
            )
            self.results.append(error_result)
            return error_result

    async def run_integration_tests(self) -> TestSuiteResult:
        """Run integration test suite"""
        logger.info("Executing integration test suite...")
        start_time = time.time()

        try:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/",
                "tests/api/",
                "test_api_integration.py",
                "-v",
                "--tb=short",
                "--cov=app",
                "--cov-report=json:reports/coverage_integration.json",
                "--cov-report=html:reports/htmlcov_integration",
                "--cov-append",
                "--junitxml=reports/integration_tests.xml",
                "-m",
                "integration",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time

            result = self._parse_pytest_output(
                process.returncode, stdout.decode(), stderr.decode()
            )
            coverage_data = self._parse_coverage_report(
                "reports/coverage_integration.json"
            )

            suite_result = TestSuiteResult(
                name="Integration Tests",
                total_tests=result.get("total", 0),
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", 0),
                execution_time=execution_time,
                coverage_percent=coverage_data.get("percent_covered", 0),
                details={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "coverage_data": coverage_data,
                },
            )

            self.results.append(suite_result)
            logger.info(
                f"Integration tests completed: {suite_result.passed}/{suite_result.total} passed"
            )

            return suite_result

        except Exception as e:
            logger.error(f"Integration test execution failed: {e}")
            error_result = TestSuiteResult(
                name="Integration Tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                execution_time=time.time() - start_time,
                coverage_percent=0,
                details={"error": str(e)},
            )
            self.results.append(error_result)
            return error_result

    async def run_security_tests(self) -> TestSuiteResult:
        """Run security test suite"""
        logger.info("Executing security test suite...")
        start_time = time.time()

        try:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_auth_security.py",
                "tests/test_penetration_security.py",
                "tests/test_security_integration.py",
                "-v",
                "--tb=short",
                "--junitxml=reports/security_tests.xml",
                "-m",
                "security",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time

            result = self._parse_pytest_output(
                process.returncode, stdout.decode(), stderr.decode()
            )

            suite_result = TestSuiteResult(
                name="Security Tests",
                total_tests=result.get("total", 0),
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", 0),
                execution_time=execution_time,
                coverage_percent=0,  # Coverage not primary for security tests
                details={"stdout": stdout.decode(), "stderr": stderr.decode()},
            )

            self.results.append(suite_result)
            logger.info(
                f"Security tests completed: {suite_result.passed}/{suite_result.total} passed"
            )

            return suite_result

        except Exception as e:
            logger.error(f"Security test execution failed: {e}")
            error_result = TestSuiteResult(
                name="Security Tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                execution_time=time.time() - start_time,
                coverage_percent=0,
                details={"error": str(e)},
            )
            self.results.append(error_result)
            return error_result

    async def run_performance_tests(self) -> TestSuiteResult:
        """Run performance test suite"""
        logger.info("Executing performance test suite...")
        start_time = time.time()

        try:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/performance/",
                "--benchmark-only",
                "--benchmark-json=reports/performance_results.json",
                "--benchmark-sort=mean",
                "-v",
                "-m",
                "performance",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time

            # Parse performance results
            performance_data = self._parse_performance_report(
                "reports/performance_results.json"
            )

            result = self._parse_pytest_output(
                process.returncode, stdout.decode(), stderr.decode()
            )

            suite_result = TestSuiteResult(
                name="Performance Tests",
                total_tests=result.get("total", 0),
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", 0),
                execution_time=execution_time,
                coverage_percent=0,
                details={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "performance_data": performance_data,
                },
            )

            self.results.append(suite_result)
            logger.info(
                f"Performance tests completed: {suite_result.passed}/{suite_result.total} passed"
            )

            return suite_result

        except Exception as e:
            logger.error(f"Performance test execution failed: {e}")
            error_result = TestSuiteResult(
                name="Performance Tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                execution_time=time.time() - start_time,
                coverage_percent=0,
                details={"error": str(e)},
            )
            self.results.append(error_result)
            return error_result

    async def run_end_to_end_tests(self) -> TestSuiteResult:
        """Run end-to-end test suite"""
        logger.info("Executing end-to-end test suite...")
        start_time = time.time()

        try:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_end_to_end.py",
                "-v",
                "--tb=short",
                "--junitxml=reports/e2e_tests.xml",
                "-m",
                "e2e",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time

            result = self._parse_pytest_output(
                process.returncode, stdout.decode(), stderr.decode()
            )

            suite_result = TestSuiteResult(
                name="End-to-End Tests",
                total_tests=result.get("total", 0),
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", 0),
                execution_time=execution_time,
                coverage_percent=0,
                details={"stdout": stdout.decode(), "stderr": stderr.decode()},
            )

            self.results.append(suite_result)
            logger.info(
                f"E2E tests completed: {suite_result.passed}/{suite_result.total} passed"
            )

            return suite_result

        except Exception as e:
            logger.error(f"E2E test execution failed: {e}")
            error_result = TestSuiteResult(
                name="End-to-End Tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                execution_time=time.time() - start_time,
                coverage_percent=0,
                details={"error": str(e)},
            )
            self.results.append(error_result)
            return error_result

    def _parse_pytest_output(
        self, returncode: int, stdout: str, stderr: str
    ) -> Dict[str, int]:
        """Parse pytest output to extract test counts"""
        result = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}

        # Try to parse from stdout
        lines = stdout.split("\n") + stderr.split("\n")

        for line in lines:
            if "passed" in line and ("failed" in line or "error" in line):
                # Example: "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit() and i + 1 < len(parts):
                        count = int(part)
                        if i + 1 < len(parts):
                            next_part = parts[i + 1].lower()
                            if "passed" in next_part:
                                result["passed"] = count
                            elif "failed" in next_part:
                                result["failed"] = count
                            elif "skipped" in next_part:
                                result["skipped"] = count
                            elif "error" in next_part or "errors" in next_part:
                                result["errors"] = count

        result["total"] = (
            result["passed"] + result["failed"] + result["skipped"] + result["errors"]
        )

        # If parsing failed, use return code as fallback
        if result["total"] == 0:
            if returncode == 0:
                result["passed"] = 1
                result["total"] = 1
            else:
                result["failed"] = 1
                result["total"] = 1

        return result

    def _parse_coverage_report(self, coverage_file: str) -> Dict[str, Any]:
        """Parse coverage JSON report"""
        try:
            coverage_path = self.project_root / coverage_file
            if coverage_path.exists():
                with open(coverage_path, "r") as f:
                    coverage_data = json.load(f)

                return {
                    "percent_covered": coverage_data.get("totals", {}).get(
                        "percent_covered", 0
                    ),
                    "lines_covered": coverage_data.get("totals", {}).get(
                        "covered_lines", 0
                    ),
                    "lines_missing": coverage_data.get("totals", {}).get(
                        "missing_lines", 0
                    ),
                    "total_lines": coverage_data.get("totals", {}).get(
                        "num_statements", 0
                    ),
                }
        except Exception as e:
            logger.warning(f"Failed to parse coverage report {coverage_file}: {e}")

        return {"percent_covered": 0}

    def _parse_performance_report(self, perf_file: str) -> Dict[str, Any]:
        """Parse performance benchmark report"""
        try:
            perf_path = self.project_root / perf_file
            if perf_path.exists():
                with open(perf_path, "r") as f:
                    perf_data = json.load(f)

                return {
                    "benchmarks": perf_data.get("benchmarks", {}),
                    "machine_info": perf_data.get("machine_info", {}),
                    "commit_info": perf_data.get("commit_info", {}),
                }
        except Exception as e:
            logger.warning(f"Failed to parse performance report {perf_file}: {e}")

        return {}

    def generate_comprehensive_report(self) -> ComprehensiveTestReport:
        """Generate comprehensive test report"""
        total_passed = sum(suite.passed for suite in self.results)
        total_failed = sum(suite.failed for suite in self.results)
        total_tests = sum(suite.total for suite in self.results)
        total_time = sum(suite.execution_time for suite in self.results)

        # Calculate overall coverage (average of coverage-enabled suites)
        coverage_suites = [
            suite for suite in self.results if suite.coverage_percent > 0
        ]
        overall_coverage = (
            sum(suite.coverage_percent for suite in coverage_suites)
            / len(coverage_suites)
            if coverage_suites
            else 0
        )

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return ComprehensiveTestReport(
            timestamp=datetime.utcnow(),
            total_execution_time=total_time,
            test_suites=self.results,
            overall_passed=total_passed,
            overall_failed=total_failed,
            overall_total=total_tests,
            overall_coverage=overall_coverage,
            performance_metrics=self._aggregate_performance_metrics(),
            security_scan_results=self._aggregate_security_results(),
            recommendations=recommendations,
        )

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        for suite in self.results:
            if suite.failed > 0:
                failure_rate = suite.failed / suite.total if suite.total > 0 else 0
                if failure_rate > 0.1:  # More than 10% failure rate
                    recommendations.append(
                        f"High failure rate in {suite.name}: {failure_rate:.1%} - investigate failing tests"
                    )

            if suite.coverage_percent > 0 and suite.coverage_percent < 80:
                recommendations.append(
                    f"Low test coverage in {suite.name}: {suite.coverage_percent:.1f}% - aim for >80%"
                )

            if suite.execution_time > 300:  # More than 5 minutes
                recommendations.append(
                    f"Slow test execution in {suite.name}: {suite.execution_time:.1f}s - consider optimization"
                )

        # Overall recommendations
        overall_coverage = (
            sum(
                suite.coverage_percent
                for suite in self.results
                if suite.coverage_percent > 0
            )
            / len([s for s in self.results if s.coverage_percent > 0])
            if self.results
            else 0
        )
        if overall_coverage < 80:
            recommendations.append(
                f"Overall test coverage is low: {overall_coverage:.1f}% - target >90%"
            )

        if not recommendations:
            recommendations.append("All test suites are performing well!")

        return recommendations

    def _aggregate_performance_metrics(self) -> Dict[str, Any]:
        """Aggregate performance metrics from all test suites"""
        performance_data = {}

        for suite in self.results:
            if suite.details and "performance_data" in suite.details:
                perf_data = suite.details["performance_data"]
                if "benchmarks" in perf_data:
                    performance_data[suite.name] = perf_data["benchmarks"]

        return performance_data

    def _aggregate_security_results(self) -> Dict[str, Any]:
        """Aggregate security test results"""
        security_results = {}

        security_suite = next(
            (suite for suite in self.results if suite.name == "Security Tests"), None
        )
        if security_suite and security_suite.details:
            security_results = {
                "total_security_tests": security_suite.total,
                "security_tests_passed": security_suite.passed,
                "security_tests_failed": security_suite.failed,
                "security_coverage": "N/A",
            }

        return security_results

    async def generate_html_report(self, report: ComprehensiveTestReport):
        """Generate HTML test report"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>PsychSync AI - Comprehensive Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
        .metric h3 {{ margin: 0; color: #2c3e50; }}
        .metric .value {{ font-size: 2em; font-weight: bold; }}
        .pass {{ color: #27ae60; }}
        .fail {{ color: #e74c3c; }}
        .coverage {{ color: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeaa7; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PsychSync AI - Comprehensive Test Report</h1>
        <p>Generated: {timestamp}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div class="value">{total_tests}</div>
        </div>
        <div class="metric">
            <h3>Passed</h3>
            <div class="value pass">{passed}</div>
        </div>
        <div class="metric">
            <h3>Failed</h3>
            <div class="value fail">{failed}</div>
        </div>
        <div class="metric">
            <h3>Coverage</h3>
            <div class="value coverage">{coverage:.1f}%</div>
        </div>
        <div class="metric">
            <h3>Execution Time</h3>
            <div class="value">{execution_time:.1f}s</div>
        </div>
    </div>

    <h2>Test Suite Results</h2>
    <table>
        <tr>
            <th>Test Suite</th>
            <th>Total</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Skipped</th>
            <th>Errors</th>
            <th>Execution Time</th>
            <th>Coverage</th>
        </tr>
        {test_suite_rows}
    </table>

    <h2>Recommendations</h2>
    <div class="recommendations">
        <ul>
            {recommendations}
        </ul>
    </div>
</body>
</html>
        """

        # Generate test suite rows
        test_suite_rows = ""
        for suite in report.test_suites:
            status_class = "pass" if suite.failed == 0 else "fail"
            test_suite_rows += f"""
        <tr>
            <td>{suite.name}</td>
            <td>{suite.total}</td>
            <td class="pass">{suite.passed}</td>
            <td class="fail">{suite.failed}</td>
            <td>{suite.skipped}</td>
            <td>{suite.errors}</td>
            <td>{suite.execution_time:.1f}s</td>
            <td>{suite.coverage_percent:.1f}%</td>
        </tr>
        """

        # Generate recommendations
        recommendations = "\n".join(f"<li>{rec}</li>" for rec in report.recommendations)

        # Generate HTML
        html_content = html_template.format(
            timestamp=report.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_tests=report.overall_total,
            passed=report.overall_passed,
            failed=report.overall_failed,
            coverage=report.overall_coverage,
            execution_time=report.total_execution_time,
            test_suite_rows=test_suite_rows,
            recommendations=recommendations,
        )

        # Write HTML report
        report_path = self.project_root / "reports" / "comprehensive_test_report.html"
        with open(report_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {report_path}")

    async def run_all_tests(
        self, test_categories: List[str] = None
    ) -> ComprehensiveTestReport:
        """Run all specified test categories"""
        if test_categories is None:
            test_categories = ["unit", "integration", "security", "performance", "e2e"]

        logger.info(
            f"Starting comprehensive test execution for categories: {test_categories}"
        )

        # Create reports directory
        (self.project_root / "reports").mkdir(exist_ok=True)

        # Run test suites based on categories
        if "unit" in test_categories:
            await self.run_unit_tests()

        if "integration" in test_categories:
            await self.run_integration_tests()

        if "security" in test_categories:
            await self.run_security_tests()

        if "performance" in test_categories:
            await self.run_performance_tests()

        if "e2e" in test_categories:
            await self.run_end_to_end_tests()

        # Generate comprehensive report
        report = self.generate_comprehensive_report()

        # Generate HTML report
        await self.generate_html_report(report)

        # Save JSON report
        report_path = self.project_root / "reports" / "comprehensive_test_report.json"
        with open(report_path, "w") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(
            f"Comprehensive test execution completed: {report.overall_passed}/{report.overall_total} tests passed"
        )

        return report


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Runner for PsychSync AI"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["unit", "integration", "security", "performance", "e2e"],
        help="Test categories to run (default: all)",
    )
    parser.add_argument(
        "--output-dir", default="reports", help="Output directory for test reports"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize test executor
    project_root = Path(__file__).parent.parent
    executor = TestExecutor(project_root)

    try:
        # Run tests
        report = await executor.run_all_tests(args.categories)

        # Print summary
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {report.overall_total}")
        print(f"Passed: {report.overall_passed}")
        print(f"Failed: {report.overall_failed}")
        print(
            f"Success Rate: {(report.overall_passed / report.overall_total * 100):.1f}%"
            if report.overall_total > 0
            else "N/A"
        )
        print(f"Overall Coverage: {report.overall_coverage:.1f}%")
        print(f"Total Execution Time: {report.total_execution_time:.1f}s")
        print("\nTest Suite Results:")
        for suite in report.test_suites:
            status = "✅" if suite.failed == 0 else "❌"
            print(
                f"  {status} {suite.name}: {suite.passed}/{suite.total} ({suite.coverage_percent:.1f}% coverage)"
            )

        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")

        print(f"\nDetailed reports saved to: {project_root}/reports/")
        print("=" * 80)

        # Exit with appropriate code
        sys.exit(0 if report.overall_failed == 0 else 1)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
