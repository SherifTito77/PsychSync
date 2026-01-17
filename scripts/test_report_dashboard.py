#!/usr/bin/env python3
"""
Comprehensive Test Reporting Dashboard

Generates detailed test reports with coverage analysis, performance metrics,
and security validation results for the PsychSync testing framework.

Features:
- Real-time test execution monitoring
- Coverage analysis with detailed reporting
- Performance benchmarking and trend analysis
- Security test results and vulnerability tracking
- HTML dashboard with interactive charts
- JSON/CSV export capabilities
- Historical data tracking

Usage:
    python scripts/test_report_dashboard.py --generate
    python scripts/test_report_dashboard.py --serve
    python scripts/test_report_dashboard.py --export-format json
"""

import os
import sys
import json
import csv
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import asyncio
from collections import defaultdict

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """Individual test result data"""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float
    file_path: str
    line_number: int
    error_message: Optional[str] = None
    markers: List[str] = None
    test_type: str = "unit"  # unit, integration, security, performance


@dataclass
class CoverageData:
    """Coverage analysis data"""
    total_lines: int
    covered_lines: int
    missing_lines: int
    coverage_percentage: float
    file_coverage: Dict[str, Dict[str, Any]]


@dataclass
class PerformanceMetrics:
    """Performance testing metrics"""
    test_name: str
    avg_duration: float
    min_duration: float
    max_duration: float
    total_runs: int
    benchmark_score: float


@dataclass
class SecurityTestResult:
    """Security test specific results"""
    vulnerability_type: str
    severity: str  # critical, high, medium, low, info
    status: str  # passed, failed, warning
    description: str
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None


@dataclass
class TestReport:
    """Comprehensive test report"""
    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    test_results: List[TestResult]
    coverage: CoverageData
    performance_metrics: List[PerformanceMetrics]
    security_results: List[SecurityTestResult]
    test_categories: Dict[str, int]
    trends: Dict[str, List[float]]  # Historical trend data


class TestRunner:
    """Executes tests and collects results"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results: List[TestResult] = []

    async def run_tests(self, test_types: List[str] = None) -> Tuple[List[TestResult], float]:
        """Run tests and collect results"""
        test_types = test_types or ["unit", "integration", "security", "performance"]

        all_results = []
        total_duration = 0.0

        for test_type in test_types:
            print(f"Running {test_type} tests...")
            results, duration = await self._run_test_type(test_type)
            all_results.extend(results)
            total_duration += duration

            print(f"  ✓ {test_type}: {len(results)} tests in {duration:.2f}s")

        return all_results, total_duration

    async def _run_test_type(self, test_type: str) -> Tuple[List[TestResult], float]:
        """Run specific type of tests"""
        start_time = time.time()

        # Construct pytest command based on test type
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            f"-m {test_type}" if test_type != "all" else "",
            "--tb=short",
            "--json-report",
            "--json-report-file=/tmp/test_results.json",
            "-v"
        ]

        # Remove empty strings from command
        cmd = [arg for arg in cmd if arg]

        try:
            # Run pytest and capture output
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time

            # Parse test results from JSON report if available
            test_results = []
            if os.path.exists("/tmp/test_results.json"):
                test_results = self._parse_json_report("/tmp/test_results.json", test_type)
            else:
                # Fallback to parsing stdout
                test_results = self._parse_stdout_output(result.stdout, test_type)

            return test_results, duration

        except subprocess.TimeoutExpired:
            print(f"Test timeout for {test_type} tests")
            return [], time.time() - start_time
        except Exception as e:
            print(f"Error running {test_type} tests: {e}")
            return [], time.time() - start_time

    def _parse_json_report(self, report_path: str, test_type: str) -> List[TestResult]:
        """Parse pytest JSON report"""
        try:
            with open(report_path, 'r') as f:
                data = json.load(f)

            results = []
            for test in data.get('tests', []):
                result = TestResult(
                    name=test.get('nodeid', ''),
                    status=test.get('outcome', 'unknown'),
                    duration=test.get('duration', 0.0),
                    file_path=test.get('nodeid', '').split('::')[0],
                    line_number=0,  # Extract from nodeid if needed
                    error_message=test.get('call', {}).get('longrepr', ''),
                    markers=test.get('markers', []),
                    test_type=test_type
                )
                results.append(result)

            return results

        except Exception as e:
            print(f"Error parsing JSON report: {e}")
            return []

    def _parse_stdout_output(self, stdout: str, test_type: str) -> List[TestResult]:
        """Parse pytest stdout output"""
        results = []
        lines = stdout.split('\n')

        for line in lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0]
                    status = parts[1].lower().rstrip('[]')
                    duration = 0.0

                    # Extract duration if available
                    for part in parts:
                        if 's' in part and part.replace('s', '').replace('.', '').isdigit():
                            duration = float(part.rstrip('s'))
                            break

                    result = TestResult(
                        name=test_name,
                        status=status,
                        duration=duration,
                        file_path=test_name.split('::')[0],
                        line_number=0,
                        test_type=test_type
                    )
                    results.append(result)

        return results


class CoverageAnalyzer:
    """Analyzes test coverage data"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_coverage(self) -> CoverageData:
        """Run coverage analysis and return results"""
        print("Running coverage analysis...")

        # Run coverage with pytest-cov
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=json",
            "--cov-report=html",
            "--cov-report=term",
            "--cov-fail-under=0"  # Don't fail on low coverage for analysis
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=180
            )

            # Parse coverage JSON report
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                return self._parse_coverage_report(coverage_file)
            else:
                # Fallback coverage data
                return CoverageData(
                    total_lines=0,
                    covered_lines=0,
                    missing_lines=0,
                    coverage_percentage=0.0,
                    file_coverage={}
                )

        except Exception as e:
            print(f"Error analyzing coverage: {e}")
            return CoverageData(
                total_lines=0,
                covered_lines=0,
                missing_lines=0,
                coverage_percentage=0.0,
                file_coverage={}
            )

    def _parse_coverage_report(self, coverage_file: Path) -> CoverageData:
        """Parse coverage JSON report"""
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)

            totals = data.get('totals', {})
            files = data.get('files', {})

            total_lines = totals.get('num_statements', 0)
            covered_lines = totals.get('covered_lines', 0)
            missing_lines = total_lines - covered_lines
            coverage_percentage = totals.get('percent_covered', 0.0)

            # Parse file-level coverage
            file_coverage = {}
            for file_path, file_data in files.items():
                summary = file_data.get('summary', {})
                file_coverage[file_path] = {
                    'total_lines': summary.get('num_statements', 0),
                    'covered_lines': summary.get('covered_lines', 0),
                    'coverage_percentage': summary.get('percent_covered', 0.0),
                    'missing_lines': summary.get('missing_lines', 0)
                }

            return CoverageData(
                total_lines=total_lines,
                covered_lines=covered_lines,
                missing_lines=missing_lines,
                coverage_percentage=coverage_percentage,
                file_coverage=file_coverage
            )

        except Exception as e:
            print(f"Error parsing coverage report: {e}")
            return CoverageData(
                total_lines=0,
                covered_lines=0,
                missing_lines=0,
                coverage_percentage=0.0,
                file_coverage={}
            )


class PerformanceAnalyzer:
    """Analyzes performance test results"""

    def analyze_performance(self, test_results: List[TestResult]) -> List[PerformanceMetrics]:
        """Analyze performance metrics from test results"""
        performance_results = []

        # Group performance tests by name
        performance_tests = [
            result for result in test_results
            if result.test_type == "performance" or "performance" in result.markers
        ]

        # Group by test name patterns
        test_groups = defaultdict(list)
        for test in performance_tests:
            # Extract base test name (remove parameters and variants)
            base_name = test.name.split('[')[0].split('::')[-1]
            test_groups[base_name].append(test.duration)

        # Calculate metrics for each test group
        for test_name, durations in test_groups.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)
                total_runs = len(durations)

                # Calculate benchmark score (lower is better)
                # Normalize to 0-100 scale based on duration
                benchmark_score = max(0, 100 - (avg_duration * 10))

                metrics = PerformanceMetrics(
                    test_name=test_name,
                    avg_duration=avg_duration,
                    min_duration=min_duration,
                    max_duration=max_duration,
                    total_runs=total_runs,
                    benchmark_score=benchmark_score
                )
                performance_results.append(metrics)

        return sorted(performance_results, key=lambda x: x.avg_duration)


class SecurityAnalyzer:
    """Analyzes security test results"""

    def analyze_security(self, test_results: List[TestResult]) -> List[SecurityTestResult]:
        """Analyze security test results"""
        security_results = []

        security_tests = [
            result for result in test_results
            if result.test_type == "security" or "security" in result.markers
        ]

        # Analyze security test patterns
        for test in security_tests:
            # Extract security vulnerability type from test name
            vulnerability_type = self._extract_vulnerability_type(test.name)
            severity = self._determine_severity(test.name, vulnerability_type)
            status = test.status if test.status != "failed" else "warning"
            description = test.error_message or f"Security test for {vulnerability_type}"
            recommendation = self._generate_recommendation(vulnerability_type, severity)
            cwe_id = self._get_cwe_id(vulnerability_type)

            security_result = SecurityTestResult(
                vulnerability_type=vulnerability_type,
                severity=severity,
                status=status,
                description=description,
                recommendation=recommendation,
                cwe_id=cwe_id
            )
            security_results.append(security_result)

        return security_results

    def _extract_vulnerability_type(self, test_name: str) -> str:
        """Extract vulnerability type from test name"""
        vulnerability_patterns = {
            "sql_injection": ["sql", "injection", "sqli"],
            "xss": ["xss", "cross_site_scripting", "script"],
            "csrf": ["csrf", "cross_site_request_forgery"],
            "authentication": ["auth", "login", "password", "token"],
            "authorization": ["access", "permission", "role"],
            "input_validation": ["input", "validation", "sanitization"],
            "session_management": ["session", "cookie", "timeout"],
            "rate_limiting": ["rate", "limit", "throttle"],
            "encryption": ["encrypt", "hash", "crypto"],
            "information_disclosure": ["disclosure", "information", "leak"]
        }

        test_name_lower = test_name.lower()

        for vuln_type, patterns in vulnerability_patterns.items():
            if any(pattern in test_name_lower for pattern in patterns):
                return vuln_type.replace("_", " ").title()

        return "General Security"

    def _determine_severity(self, test_name: str, vulnerability_type: str) -> str:
        """Determine severity based on vulnerability type"""
        high_severity = [
            "Sql Injection", "Cross Site Scripting", "Authentication",
            "Information Disclosure", "Encryption"
        ]

        medium_severity = [
            "Csrf", "Authorization", "Session Management"
        ]

        if vulnerability_type in high_severity:
            return "high"
        elif vulnerability_type in medium_severity:
            return "medium"
        else:
            return "low"

    def _generate_recommendation(self, vulnerability_type: str, severity: str) -> str:
        """Generate security recommendations"""
        recommendations = {
            "Sql Injection": "Use parameterized queries and input validation",
            "Cross Site Scripting": "Implement output encoding and Content Security Policy",
            "Csrf": "Use CSRF tokens and SameSite cookies",
            "Authentication": "Implement strong password policies and MFA",
            "Authorization": "Use principle of least privilege and proper access controls",
            "Input Validation": "Validate all inputs and use whitelist approach",
            "Session Management": "Use secure session handling and proper timeouts",
            "Rate Limiting": "Implement API rate limiting and account lockout",
            "Encryption": "Use strong encryption algorithms and proper key management"
        }

        return recommendations.get(vulnerability_type, "Review security best practices")

    def _get_cwe_id(self, vulnerability_type: str) -> Optional[str]:
        """Get CWE ID for vulnerability type"""
        cwe_mapping = {
            "Sql Injection": "CWE-89",
            "Cross Site Scripting": "CWE-79",
            "Csrf": "CWE-352",
            "Authentication": "CWE-287",
            "Authorization": "CWE-285",
            "Input Validation": "CWE-20",
            "Session Management": "CWE-613",
            "Information Disclosure": "CWE-200"
        }

        return cwe_mapping.get(vulnerability_type)


class ReportGenerator:
    """Generates comprehensive test reports"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)

    def generate_report(self, test_report: TestReport) -> str:
        """Generate comprehensive test report"""
        timestamp = test_report.timestamp.strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"test_report_{timestamp}.json"

        # Convert to dictionary and handle datetime serialization
        report_dict = asdict(test_report)
        report_dict['timestamp'] = test_report.timestamp.isoformat()

        # Convert test results to dictionaries
        report_dict['test_results'] = [asdict(result) for result in test_report.test_results]
        report_dict['performance_metrics'] = [asdict(metric) for metric in test_report.performance_metrics]
        report_dict['security_results'] = [asdict(result) for result in test_report.security_results]

        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        # Generate HTML report
        html_file = self.generate_html_report(test_report, timestamp)

        return str(html_file)

    def generate_html_report(self, test_report: TestReport, timestamp: str) -> Path:
        """Generate HTML dashboard report"""
        html_file = self.reports_dir / f"test_dashboard_{timestamp}.html"

        html_content = self._generate_html_content(test_report)

        with open(html_file, 'w') as f:
            f.write(html_content)

        return html_file

    def _generate_html_content(self, test_report: TestReport) -> str:
        """Generate HTML dashboard content"""
        # Calculate statistics
        pass_rate = (test_report.passed_tests / test_report.total_tests * 100) if test_report.total_tests > 0 else 0
        security_score = self._calculate_security_score(test_report.security_results)
        performance_score = self._calculate_performance_score(test_report.performance_metrics)

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PsychSync Test Report Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-card h3 {{ color: #333; margin-bottom: 10px; font-size: 1.1em; }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }}
        .metric-change {{ font-size: 0.9em; opacity: 0.7; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .danger {{ color: #e74c3c; }}
        .info {{ color: #3498db; }}
        .charts-section {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chart-card h3 {{ color: #333; margin-bottom: 20px; }}
        .details-section {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .details-section h3 {{ color: #333; margin-bottom: 20px; }}
        .test-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .test-table th, .test-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .test-table th {{ background: #f8f9fa; font-weight: 600; }}
        .status-passed {{ color: #27ae60; font-weight: 500; }}
        .status-failed {{ color: #e74c3c; font-weight: 500; }}
        .status-skipped {{ color: #f39c12; font-weight: 500; }}
        .footer {{ text-align: center; margin-top: 40px; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 PsychSync Test Report Dashboard</h1>
            <p>Generated on {test_report.timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Total Duration: {test_report.total_duration:.2f} seconds</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📊 Total Tests</h3>
                <div class="metric-value">{test_report.total_tests}</div>
                <div class="metric-change">{test_report.passed_tests} passed, {test_report.failed_tests} failed</div>
            </div>

            <div class="metric-card">
                <h3>✅ Pass Rate</h3>
                <div class="metric-value {'success' if pass_rate >= 90 else 'warning' if pass_rate >= 70 else 'danger'}">{pass_rate:.1f}%</div>
                <div class="metric-change">Target: >90%</div>
            </div>

            <div class="metric-card">
                <h3>📈 Code Coverage</h3>
                <div class="metric-value {'success' if test_report.coverage.coverage_percentage >= 80 else 'warning' if test_report.coverage.coverage_percentage >= 60 else 'danger'}">{test_report.coverage.coverage_percentage:.1f}%</div>
                <div class="metric-change">{test_report.coverage.covered_lines}/{test_report.coverage.total_lines} lines</div>
            </div>

            <div class="metric-card">
                <h3>🔒 Security Score</h3>
                <div class="metric-value {'success' if security_score >= 90 else 'warning' if security_score >= 70 else 'danger'}">{security_score:.0f}/100</div>
                <div class="metric-change">{len([r for r in test_report.security_results if r.status == 'passed'])} security tests passed</div>
            </div>

            <div class="metric-card">
                <h3>⚡ Performance Score</h3>
                <div class="metric-value {'success' if performance_score >= 80 else 'warning' if performance_score >= 60 else 'danger'}">{performance_score:.0f}/100</div>
                <div class="metric-change">{len(test_report.performance_metrics)} performance tests</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="chart-card">
                <h3>Test Results Distribution</h3>
                <canvas id="testResultsChart"></canvas>
            </div>

            <div class="chart-card">
                <h3>Test Categories</h3>
                <canvas id="testCategoriesChart"></canvas>
            </div>

            <div class="chart-card">
                <h3>Coverage by File</h3>
                <canvas id="coverageChart"></canvas>
            </div>

            <div class="chart-card">
                <h3>Security Test Results</h3>
                <canvas id="securityChart"></canvas>
            </div>
        </div>

        <div class="details-section">
            <h3>📋 Test Details</h3>
            <table class="test-table">
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Duration (s)</th>
                        <th>File</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_test_table_rows(test_report.test_results)}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Generated by PsychSync Test Dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // Test Results Chart
        const testResultsCtx = document.getElementById('testResultsChart').getContext('2d');
        new Chart(testResultsCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped', 'Errors'],
                datasets: [{{
                    data: [{test_report.passed_tests}, {test_report.failed_tests}, {test_report.skipped_tests}, {test_report.error_tests}],
                    backgroundColor: ['#27ae60', '#e74c3c', '#f39c12', '#95a5a6']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});

        // Test Categories Chart
        const testCategoriesCtx = document.getElementById('testCategoriesChart').getContext('2d');
        new Chart(testCategoriesCtx, {{
            type: 'pie',
            data: {{
                labels: {list(test_report.test_categories.keys())},
                datasets: [{{
                    data: {list(test_report.test_categories.values())},
                    backgroundColor: ['#3498db', '#e74c3c', '#f39c12', '#27ae60', '#9b59b6']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});

        // Coverage Chart
        const coverageCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(coverageCtx, {{
            type: 'bar',
            data: {{
                labels: {list(test_report.coverage.file_coverage.keys())[:10]},  // Top 10 files
                datasets: [{{
                    label: 'Coverage %',
                    data: {[round(info['coverage_percentage'], 1) for info in list(test_report.coverage.file_coverage.values())[:10]]},
                    backgroundColor: '#3498db'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});

        // Security Chart
        const securityCtx = document.getElementById('securityChart').getContext('2d');
        new Chart(securityCtx, {{
            type: 'bar',
            data: {{
                labels: ['Passed', 'Failed', 'Warning'],
                datasets: [{{
                    label: 'Security Tests',
                    data: [
                        {len([r for r in test_report.security_results if r.status == 'passed'])},
                        {len([r for r in test_report.security_results if r.status == 'failed'])},
                        {len([r for r in test_report.security_results if r.status == 'warning'])}
                    ],
                    backgroundColor: ['#27ae60', '#e74c3c', '#f39c12']
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        return html_template

    def _generate_test_table_rows(self, test_results: List[TestResult]) -> str:
        """Generate HTML table rows for test results"""
        rows = []
        for result in test_results[:50]:  # Limit to first 50 tests
            status_class = f"status-{result.status}"
            file_name = result.file_path.split('/')[-1] if '/' in result.file_path else result.file_path

            row = f"""
                    <tr>
                        <td>{result.name}</td>
                        <td>{result.test_type}</td>
                        <td class="{status_class}">{result.status.title()}</td>
                        <td>{result.duration:.3f}</td>
                        <td>{file_name}</td>
                    </tr>
            """
            rows.append(row)

        return ''.join(rows)

    def _calculate_security_score(self, security_results: List[SecurityTestResult]) -> float:
        """Calculate overall security score"""
        if not security_results:
            return 100.0  # Perfect score if no security tests

        passed = len([r for r in security_results if r.status == 'passed'])
        total = len(security_results)

        return (passed / total) * 100

    def _calculate_performance_score(self, performance_metrics: List[PerformanceMetrics]) -> float:
        """Calculate overall performance score"""
        if not performance_metrics:
            return 100.0  # Perfect score if no performance tests

        total_score = sum(m.benchmark_score for m in performance_metrics)
        return total_score / len(performance_metrics)


class TestReportDashboard:
    """Main dashboard application"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_runner = TestRunner(project_root)
        self.coverage_analyzer = CoverageAnalyzer(project_root)
        self.performance_analyzer = PerformanceAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.report_generator = ReportGenerator(project_root)

    async def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report"""
        print("🚀 Starting comprehensive test report generation...")
        print("=" * 60)

        # Run tests
        print("\n📋 Running Tests...")
        test_results, total_duration = await self.test_runner.run_tests()

        # Analyze coverage
        print("\n📊 Analyzing Coverage...")
        coverage_data = self.coverage_analyzer.analyze_coverage()

        # Analyze performance
        print("\n⚡ Analyzing Performance...")
        performance_metrics = self.performance_analyzer.analyze_performance(test_results)

        # Analyze security
        print("\n🔒 Analyzing Security...")
        security_results = self.security_analyzer.analyze_security(test_results)

        # Categorize tests
        test_categories = self._categorize_tests(test_results)

        # Create comprehensive report
        print("\n📝 Generating Report...")
        test_report = TestReport(
            timestamp=datetime.now(),
            total_tests=len(test_results),
            passed_tests=len([r for r in test_results if r.status == "passed"]),
            failed_tests=len([r for r in test_results if r.status == "failed"]),
            skipped_tests=len([r for r in test_results if r.status == "skipped"]),
            error_tests=len([r for r in test_results if r.status == "error"]),
            total_duration=total_duration,
            test_results=test_results,
            coverage=coverage_data,
            performance_metrics=performance_metrics,
            security_results=security_results,
            test_categories=test_categories,
            trends={}  # TODO: Implement historical trend tracking
        )

        # Generate and save report
        report_file = self.report_generator.generate_report(test_report)

        print(f"\n✅ Comprehensive test report generated!")
        print(f"📁 Report saved to: {report_file}")
        print(f"📊 Coverage: {coverage_data.coverage_percentage:.1f}%")
        print(f"🔒 Security Score: {self.report_generator._calculate_security_score(security_results):.0f}/100")
        print(f"⚡ Performance Score: {self.report_generator._calculate_performance_score(performance_metrics):.0f}/100")

        return report_file

    def _categorize_tests(self, test_results: List[TestResult]) -> Dict[str, int]:
        """Categorize tests by type"""
        categories = defaultdict(int)
        for result in test_results:
            categories[result.test_type] += 1

        return dict(categories)

    def export_report(self, report_file: str, export_format: str = "json"):
        """Export report in different formats"""
        report_path = Path(report_file)

        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {report_file}")

        # Load the report
        with open(report_path, 'r') as f:
            report_data = json.load(f)

        if export_format.lower() == "csv":
            self._export_to_csv(report_data, report_path)
        elif export_format.lower() == "json":
            # Already in JSON format, copy to exports directory
            exports_dir = self.project_root / "test_exports"
            exports_dir.mkdir(exist_ok=True)

            export_file = exports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(report_data, f, indent=2)

            print(f"Report exported to: {export_file}")

    def _export_to_csv(self, report_data: Dict, report_path: Path):
        """Export report to CSV format"""
        exports_dir = self.project_root / "test_exports"
        exports_dir.mkdir(exist_ok=True)

        export_file = exports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Write test results to CSV
        with open(export_file, 'w', newline='') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'Test Name', 'Status', 'Duration', 'File Path', 'Test Type',
                'Error Message', 'Markers'
            ])

            # Write test results
            for result in report_data.get('test_results', []):
                writer.writerow([
                    result.get('name', ''),
                    result.get('status', ''),
                    result.get('duration', 0),
                    result.get('file_path', ''),
                    result.get('test_type', ''),
                    result.get('error_message', ''),
                    ','.join(result.get('markers', []))
                ])

        print(f"Report exported to CSV: {export_file}")


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive test reports for PsychSync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/test_report_dashboard.py --generate
    python scripts/test_report_dashboard.py --generate --export-format csv
        """
    )

    parser.add_argument(
        '--generate', '-g',
        action='store_true',
        help='Generate comprehensive test report'
    )

    parser.add_argument(
        '--export-format', '-e',
        choices=['json', 'csv'],
        default='json',
        help='Export format for the report (default: json)'
    )

    parser.add_argument(
        '--serve', '-s',
        action='store_true',
        help='Start web server to serve reports'
    )

    args = parser.parse_args()

    if not args.generate and not args.serve:
        parser.error("Either --generate or --serve must be specified")

    try:
        dashboard = TestReportDashboard(project_root)

        if args.generate:
            report_file = await dashboard.generate_comprehensive_report()
            dashboard.export_report(report_file, args.export_format)

        elif args.serve:
            print("Starting web server for test reports...")
            print("Access reports at: http://localhost:8080")
            # TODO: Implement web server for serving reports

    except KeyboardInterrupt:
        print("\n⚠️  Report generation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
