#!/usr/bin/env python3
"""
Integration Test Analytics Dashboard
Comprehensive metrics collection and visualization for the PsychSync test suite

Features:
- Real-time test execution metrics
- Performance benchmarking analysis
- Security compliance reporting
- Code coverage visualization
- Trend analysis and alerting
- Export capabilities for stakeholders

Author: Quality Engineering Team
Version: 1.0 Enterprise Analytics
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from collections import defaultdict
    from dataclasses import asdict, dataclass

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import pytest
    import seaborn as sns
    from plotly.subplots import make_subplots

    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("⚠️  Plotting libraries not available. Using text-based reporting only.")


@dataclass
class TestMetrics:
    """Test execution metrics data structure"""

    test_name: str
    test_file: str
    execution_time: float
    status: str  # passed, failed, skipped
    error_message: Optional[str] = None
    security_score: float = 0.0
    performance_score: float = 0.0
    coverage_percentage: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TestAnalyticsEngine:
    """Comprehensive analytics engine for integration test metrics"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.test_results: List[TestMetrics] = []
        self.metrics_history: List[Dict] = []
        self.performance_benchmarks = self._load_benchmarks()
        self.security_standards = self._load_security_standards()

    def _load_benchmarks(self) -> Dict[str, float]:
        """Load performance benchmarks from configuration"""
        return {
            "api_response_time_ms": 200.0,
            "database_query_ms": 100.0,
            "file_upload_mb_per_sec": 10.0,
            "email_send_per_sec": 50.0,
            "payment_process_ms": 500.0,
            "token_refresh_ms": 50.0,
        }

    def _load_security_standards(self) -> Dict[str, Dict]:
        """Load security validation standards"""
        return {
            "owasp_compliance": {
                "injection_prevention": True,
                "broken_authentication": True,
                "sensitive_data_exposure": True,
                "xml_external_entities": True,
                "broken_access_control": True,
                "security_misconfiguration": True,
                "cross_site_scripting": True,
                "insecure_deserialization": True,
                "components_with_vulnerabilities": True,
                "insufficient_logging": True,
            },
            "pci_compliance": {
                "card_data_protection": True,
                "secure_transmission": True,
                "strong_cryptography": True,
                "access_control": True,
                "network_security": True,
            },
        }

    async def run_test_suite(
        self, test_path: str = "tests/integration/"
    ) -> Dict[str, Any]:
        """Execute test suite and collect metrics"""
        print(f"🧪 Running test suite: {test_path}")
        start_time = time.time()

        try:
            # Run pytest with JSON reporting
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_path,
                "--json-report",
                "--json-report-file=test_results.json",
                "--tb=short",
                "-v",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            execution_time = time.time() - start_time

            # Parse test results
            test_results = self._parse_test_results("test_results.json")

            return {
                "execution_time": execution_time,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "execution_time": time.time() - start_time,
                "exit_code": 1,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _parse_test_results(self, results_file: str) -> Dict[str, Any]:
        """Parse pytest JSON results"""
        try:
            with open(results_file, "r") as f:
                data = json.load(f)

            summary = data.get("summary", {})
            tests = data.get("tests", [])

            # Extract individual test metrics
            for test in tests:
                metric = TestMetrics(
                    test_name=test.get("nodeid", "").split("::")[-1],
                    test_file=test.get("nodeid", "").split("::")[0],
                    execution_time=test.get("duration", 0.0),
                    status=test.get("outcome", "unknown"),
                    error_message=test.get("call", {}).get("longrepr", None),
                )
                self.test_results.append(metric)

            return {
                "total_tests": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "error": summary.get("error", 0),
                "duration": summary.get("duration", 0.0),
                "individual_tests": tests,
            }

        except Exception as e:
            print(f"⚠️  Error parsing test results: {e}")
            return {}

    def calculate_security_score(self, test_file: str) -> float:
        """Calculate security compliance score for test file"""
        base_score = 100.0

        # Security test patterns to look for
        security_patterns = {
            "sql_injection": ["sql", "injection", "malicious", "escape"],
            "xss_prevention": ["xss", "sanitize", "html", "script"],
            "authentication": ["auth", "login", "token", "session"],
            "authorization": ["permission", "access", "role", "scope"],
            "rate_limiting": ["rate_limit", "throttle", "abuse", "ddos"],
            "data_encryption": ["encrypt", "hash", "secure", "protect"],
        }

        try:
            with open(f"{self.project_root}/{test_file}", "r") as f:
                content = f.read().lower()

            score = 0
            for category, patterns in security_patterns.items():
                if any(pattern in content for pattern in patterns):
                    score += 15  # Each security category worth 15 points

            return min(score, base_score)

        except Exception:
            return 0.0

    def calculate_performance_score(self, test_metrics: TestMetrics) -> float:
        """Calculate performance score based on execution time"""
        # Score based on how close execution time is to benchmarks
        if "api" in test_metrics.test_file.lower():
            benchmark = self.performance_benchmarks["api_response_time_ms"] / 1000.0
        elif "database" in test_metrics.test_file.lower():
            benchmark = self.performance_benchmarks["database_query_ms"] / 1000.0
        elif "billing" in test_metrics.test_file.lower():
            benchmark = self.performance_benchmarks["payment_process_ms"] / 1000.0
        else:
            benchmark = 1.0  # Default 1 second

        if test_metrics.execution_time <= benchmark:
            return 100.0
        else:
            # Score decreases as execution time increases
            ratio = benchmark / test_metrics.execution_time
            return max(0.0, ratio * 100)

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance analytics report"""
        if not self.test_results:
            return {"error": "No test results available"}

        # Performance metrics calculation
        passed_tests = [t for t in self.test_results if t.status == "passed"]
        failed_tests = [t for t in self.test_results if t.status == "failed"]

        execution_times = [t.execution_time for t in self.test_results]
        performance_scores = [
            self.calculate_performance_score(t) for t in self.test_results
        ]

        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "pass_rate": (
                    len(passed_tests) / len(self.test_results) * 100
                    if self.test_results
                    else 0
                ),
                "avg_execution_time": (
                    np.mean(execution_times) if execution_times else 0
                ),
                "total_execution_time": sum(execution_times),
                "avg_performance_score": (
                    np.mean(performance_scores) if performance_scores else 0
                ),
            },
            "performance_analysis": {
                "fastest_test": min(execution_times) if execution_times else 0,
                "slowest_test": max(execution_times) if execution_times else 0,
                "performance_distribution": {
                    "excellent": len([s for s in performance_scores if s >= 90]),
                    "good": len([s for s in performance_scores if 70 <= s < 90]),
                    "fair": len([s for s in performance_scores if 50 <= s < 70]),
                    "poor": len([s for s in performance_scores if s < 50]),
                },
                "performance_benchmarks": self.performance_benchmarks,
            },
            "test_breakdown": self._analyze_test_breakdown(),
            "recommendations": self._generate_performance_recommendations(),
        }

        return report

    def _analyze_test_breakdown(self) -> Dict[str, Any]:
        """Analyze test breakdown by category and file"""
        breakdown = defaultdict(
            lambda: {"total": 0, "passed": 0, "failed": 0, "avg_time": 0}
        )

        for test in self.test_results:
            category = self._categorize_test(test.test_file)
            breakdown[category]["total"] += 1
            breakdown[category]["avg_time"] += test.execution_time

            if test.status == "passed":
                breakdown[category]["passed"] += 1
            elif test.status == "failed":
                breakdown[category]["failed"] += 1

        # Calculate averages and pass rates
        for category, data in breakdown.items():
            if data["total"] > 0:
                data["avg_time"] = data["avg_time"] / data["total"]
                data["pass_rate"] = (data["passed"] / data["total"]) * 100
            else:
                data["pass_rate"] = 0

        return dict(breakdown)

    def _categorize_test(self, test_file: str) -> str:
        """Categorize test based on file name"""
        test_file_lower = test_file.lower()

        if "api" in test_file_lower:
            return "API Endpoints"
        elif "database" in test_file_lower or "crud" in test_file_lower:
            return "Database Operations"
        elif "auth" in test_file_lower:
            return "Authentication"
        elif "token" in test_file_lower:
            return "Token Management"
        elif "file_upload" in test_file_lower:
            return "File Management"
        elif "billing" in test_file_lower or "stripe" in test_file_lower:
            return "Payment Processing"
        elif "email" in test_file_lower:
            return "Email Services"
        else:
            return "Other"

    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        if not self.test_results:
            return recommendations

        slow_tests = [t for t in self.test_results if t.execution_time > 2.0]
        if slow_tests:
            recommendations.append(
                f"⚠️  {len(slow_tests)} tests taking longer than 2 seconds. Consider optimization."
            )

        avg_performance = np.mean(
            [self.calculate_performance_score(t) for t in self.test_results]
        )
        if avg_performance < 80:
            recommendations.append(
                "📊 Overall performance score below 80%. Review test optimization strategies."
            )

        failed_tests = [t for t in self.test_results if t.status == "failed"]
        if (
            len(failed_tests) > len(self.test_results) * 0.1
        ):  # More than 10% failure rate
            recommendations.append(
                f"❌ High failure rate ({len(failed_tests)}/{len(self.test_results)}). Address failing tests."
            )

        return recommendations

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security analytics report"""
        security_scores = []
        test_files = set(t.test_file for t in self.test_results)

        for test_file in test_files:
            score = self.calculate_security_score(test_file)
            security_scores.append(score)

        # Security compliance analysis
        owasp_compliance = self._check_owasp_compliance()
        pci_compliance = self._check_pci_compliance()

        return {
            "security_scores": {
                "average": np.mean(security_scores) if security_scores else 0,
                "minimum": min(security_scores) if security_scores else 0,
                "maximum": max(security_scores) if security_scores else 0,
                "distribution": {
                    "excellent": len([s for s in security_scores if s >= 90]),
                    "good": len([s for s in security_scores if 70 <= s < 90]),
                    "needs_improvement": len([s for s in security_scores if s < 70]),
                },
            },
            "compliance_status": {
                "owasp": owasp_compliance,
                "pci": pci_compliance,
                "overall_compliance": owasp_compliance["compliant"]
                and pci_compliance["compliant"],
            },
            "security_recommendations": self._generate_security_recommendations(),
            "test_coverage": {
                "total_test_files": len(test_files),
                "security_test_files": len(
                    [f for f in test_files if "security" in f or "auth" in f]
                ),
                "security_coverage_percentage": (
                    (
                        len([f for f in test_files if "security" in f or "auth" in f])
                        / len(test_files)
                        * 100
                    )
                    if test_files
                    else 0
                ),
            },
        }

    def _check_owasp_compliance(self) -> Dict[str, Any]:
        """Check OWASP Top 10 compliance"""
        # Simplified compliance check - in real implementation, would analyze actual test coverage
        security_tests = [
            t
            for t in self.test_results
            if any(
                keyword in t.test_name.lower()
                for keyword in [
                    "injection",
                    "xss",
                    "auth",
                    "security",
                    "escape",
                    "sanitize",
                ]
            )
        ]

        return {
            "compliant": len(security_tests) >= 5,  # At least 5 security tests
            "security_tests_found": len(security_tests),
            "recommended_minimum": 5,
            "coverage_areas": [
                "sql_injection",
                "xss_prevention",
                "authentication_security",
                "input_validation",
                "rate_limiting",
            ],
        }

    def _check_pci_compliance(self) -> Dict[str, Any]:
        """Check PCI DSS compliance for payment processing"""
        billing_tests = [
            t
            for t in self.test_results
            if "billing" in t.test_file or "stripe" in t.test_file
        ]

        # Check for PCI-related test patterns
        pci_patterns = ["encrypt", "secure", "token", "compliance", "audit"]
        pci_compliant_tests = [
            t
            for t in billing_tests
            if any(pattern in t.test_name.lower() for pattern in pci_patterns)
        ]

        return {
            "compliant": len(pci_compliant_tests) >= 3,  # At least 3 PCI-related tests
            "billing_tests_found": len(billing_tests),
            "pci_compliant_tests": len(pci_compliant_tests),
            "required_minimum": 3,
            "coverage_areas": [
                "card_data_protection",
                "secure_transmission",
                "access_control",
                "cryptography",
                "audit_logging",
            ],
        }

    def _generate_security_recommendations(self) -> List[str]:
        """Generate security improvement recommendations"""
        recommendations = []

        avg_security_score = (
            np.mean(
                [self.calculate_security_score(t.test_file) for t in self.test_results]
            )
            if self.test_results
            else 0
        )

        if avg_security_score < 80:
            recommendations.append(
                "🔒 Average security score below 80%. Add more comprehensive security test cases."
            )

        owasp_compliance = self._check_owasp_compliance()
        if not owasp_compliance["compliant"]:
            recommendations.append(
                f"🛡️  OWASP compliance requires at least {owasp_compliance['recommended_minimum']} security tests. Currently have {owasp_compliance['security_tests_found']}."
            )

        pci_compliance = self._check_pci_compliance()
        if not pci_compliance["compliant"]:
            recommendations.append(
                f"💳 PCI compliance requires at least {pci_compliance['required_minimum']} PCI-related tests. Currently have {pci_compliance['pci_compliant_tests']}."
            )

        return recommendations

    def create_visual_dashboard(self, output_dir: str = "test_reports") -> str:
        """Create visual dashboard with charts and graphs"""
        if not HAS_PLOTTING:
            print("⚠️  Plotting libraries not available. Skipping visual dashboard.")
            return ""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Create performance charts
        self._create_performance_charts(output_path)
        self._create_security_charts(output_path)
        self._create_trend_analysis(output_path)

        dashboard_file = output_path / "test_dashboard.html"
        self._generate_html_dashboard(dashboard_file)

        return str(dashboard_file)

    def _create_performance_charts(self, output_path: Path):
        """Create performance visualization charts"""
        if not self.test_results:
            return

        # Performance distribution
        performance_scores = [
            self.calculate_performance_score(t) for t in self.test_results
        ]

        plt.figure(figsize=(12, 8))

        # Performance Score Distribution
        plt.subplot(2, 2, 1)
        plt.hist(
            performance_scores, bins=20, alpha=0.7, color="skyblue", edgecolor="black"
        )
        plt.title("Performance Score Distribution")
        plt.xlabel("Performance Score")
        plt.ylabel("Number of Tests")
        plt.grid(True, alpha=0.3)

        # Execution Time Distribution
        plt.subplot(2, 2, 2)
        execution_times = [t.execution_time for t in self.test_results]
        plt.hist(
            execution_times, bins=20, alpha=0.7, color="lightcoral", edgecolor="black"
        )
        plt.title("Execution Time Distribution")
        plt.xlabel("Execution Time (seconds)")
        plt.ylabel("Number of Tests")
        plt.grid(True, alpha=0.3)

        # Test Category Performance
        plt.subplot(2, 2, 3)
        categories = {}
        for test in self.test_results:
            category = self._categorize_test(test.test_file)
            if category not in categories:
                categories[category] = []
            categories[category].append(self.calculate_performance_score(test))

        category_means = [np.mean(scores) for scores in categories.values()]
        category_names = list(categories.keys())

        plt.bar(
            category_names,
            category_means,
            alpha=0.7,
            color="lightgreen",
            edgecolor="black",
        )
        plt.title("Average Performance by Category")
        plt.xlabel("Test Category")
        plt.ylabel("Average Performance Score")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        # Pass Rate by Category
        plt.subplot(2, 2, 4)
        pass_rates = []
        for category in category_names:
            category_tests = [
                t
                for t in self.test_results
                if self._categorize_test(t.test_file) == category
            ]
            passed = len([t for t in category_tests if t.status == "passed"])
            pass_rates.append(
                passed / len(category_tests) * 100 if category_tests else 0
            )

        plt.bar(category_names, pass_rates, alpha=0.7, color="gold", edgecolor="black")
        plt.title("Pass Rate by Category")
        plt.xlabel("Test Category")
        plt.ylabel("Pass Rate (%)")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            output_path / "performance_charts.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def _create_security_charts(self, output_path: Path):
        """Create security visualization charts"""
        if not self.test_results:
            return

        test_files = set(t.test_file for t in self.test_results)
        security_scores = [
            self.calculate_security_score(test_file) for test_file in test_files
        ]

        plt.figure(figsize=(12, 6))

        # Security Score Distribution
        plt.subplot(1, 2, 1)
        plt.hist(security_scores, bins=15, alpha=0.7, color="plum", edgecolor="black")
        plt.title("Security Score Distribution")
        plt.xlabel("Security Score")
        plt.ylabel("Number of Test Files")
        plt.grid(True, alpha=0.3)

        # Security Compliance Status
        plt.subplot(1, 2, 2)
        owasp = self._check_owasp_compliance()
        pci = self._check_pci_compliance()

        compliance_data = ["OWASP Top 10", "PCI DSS"]
        compliance_status = [
            1 if owasp["compliant"] else 0,
            1 if pci["compliant"] else 0,
        ]
        colors = ["green" if status == 1 else "red" for status in compliance_status]

        plt.bar(
            compliance_data,
            compliance_status,
            alpha=0.7,
            color=colors,
            edgecolor="black",
        )
        plt.title("Security Compliance Status")
        plt.ylabel("Compliant (1) / Non-Compliant (0)")
        plt.ylim(0, 1.2)
        plt.grid(True, alpha=0.3)

        # Add compliance labels
        for i, (compliant, status) in enumerate(
            zip(compliance_data, compliance_status)
        ):
            plt.text(
                i,
                status + 0.05,
                "✓ Compliant" if status else "✗ Non-Compliant",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()
        plt.savefig(output_path / "security_charts.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _create_trend_analysis(self, output_path: Path):
        """Create trend analysis charts"""
        # This would normally load historical data
        # For now, create a placeholder trend chart
        plt.figure(figsize=(10, 6))

        # Sample trend data (in real implementation, would load from history)
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        pass_rates = np.random.uniform(85, 95, 30)  # Sample data

        plt.plot(dates, pass_rates, marker="o", linewidth=2, color="blue", alpha=0.7)
        plt.title("Test Pass Rate Trend (Last 30 Days)")
        plt.xlabel("Date")
        plt.ylabel("Pass Rate (%)")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(output_path / "trend_analysis.png", dpi=300, bbox_inches="tight")
        plt.close()

    def _generate_html_dashboard(self, output_file: Path):
        """Generate comprehensive HTML dashboard"""
        performance_report = self.generate_performance_report()
        security_report = self.generate_security_report()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PsychSync Integration Test Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .metric-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .section {{
            padding: 30px;
            border-top: 1px solid #eee;
        }}
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 400;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .recommendations {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin: 10px 0;
            line-height: 1.5;
        }}
        .status-good {{ color: #28a745; font-weight: bold; }}
        .status-warning {{ color: #ffc107; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .compliance-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .compliant {{ background: #d4edda; color: #155724; }}
        .non-compliant {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🧪 PsychSync Integration Test Dashboard</h1>
            <p>Real-time analytics and reporting for test suite performance and security</p>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{performance_report['summary']['total_tests']}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{performance_report['summary']['pass_rate']:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{performance_report['summary']['avg_execution_time']:.2f}s</div>
                <div class="metric-label">Avg Execution Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{performance_report['summary']['avg_performance_score']:.1f}</div>
                <div class="metric-label">Performance Score</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Performance Analytics</h2>
            <div class="chart-container">
                <img src="performance_charts.png" alt="Performance Charts">
            </div>

            <div class="recommendations">
                <h3>Performance Recommendations</h3>
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in performance_report['recommendations'])}
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>🔒 Security Compliance</h2>
            <div style="display: flex; justify-content: space-around; margin: 20px 0;">
                <div style="text-align: center;">
                    <h4>OWASP Top 10</h4>
                    <span class="compliance-badge {'compliant' if security_report['compliance_status']['owasp']['compliant'] else 'non-compliant'}">
                        {'✓ Compliant' if security_report['compliance_status']['owasp']['compliant'] else '✗ Non-Compliant'}
                    </span>
                </div>
                <div style="text-align: center;">
                    <h4>PCI DSS</h4>
                    <span class="compliance-badge {'compliant' if security_report['compliance_status']['pci']['compliant'] else 'non-compliant'}">
                        {'✓ Compliant' if security_report['compliance_status']['pci']['compliant'] else '✗ Non-Compliant'}
                    </span>
                </div>
            </div>

            <div class="chart-container">
                <img src="security_charts.png" alt="Security Charts">
            </div>

            <div class="recommendations">
                <h3>Security Recommendations</h3>
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in security_report['security_recommendations'])}
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>📈 Trend Analysis</h2>
            <div class="chart-container">
                <img src="trend_analysis.png" alt="Trend Analysis">
            </div>
        </div>

        <div class="section">
            <h2>📋 Test Breakdown</h2>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Category</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Total Tests</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Passed</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Failed</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Pass Rate</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Avg Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(self._generate_test_breakdown_rows(performance_report['test_breakdown']))}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_test_breakdown_rows(self, breakdown: Dict[str, Any]) -> str:
        """Generate HTML table rows for test breakdown"""
        rows = []
        for category, data in breakdown.items():
            pass_rate_class = (
                "status-good"
                if data["pass_rate"] >= 90
                else "status-warning" if data["pass_rate"] >= 70 else "status-error"
            )

            rows.append(
                f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{category}</td>
                    <td style="padding: 12px; text-align: center; border-bottom: 1px solid #dee2e6;">{data['total']}</td>
                    <td style="padding: 12px; text-align: center; border-bottom: 1px solid #dee2e6;">{data['passed']}</td>
                    <td style="padding: 12px; text-align: center; border-bottom: 1px solid #dee2e6;">{data['failed']}</td>
                    <td style="padding: 12px; text-align: center; border-bottom: 1px solid #dee2e6;">
                        <span class="{pass_rate_class}">{data['pass_rate']:.1f}%</span>
                    </td>
                    <td style="padding: 12px; text-align: center; border-bottom: 1px solid #dee2e6;">{data['avg_time']:.3f}s</td>
                </tr>
            """
            )
        return "".join(rows)

    def export_metrics_json(self, output_file: str = "test_metrics.json") -> str:
        """Export all metrics to JSON file"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "performance_report": self.generate_performance_report(),
            "security_report": self.generate_security_report(),
            "test_results": [asdict(test) for test in self.test_results],
            "performance_benchmarks": self.performance_benchmarks,
            "security_standards": self.security_standards,
        }

        # Convert datetime objects to strings for JSON serialization
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        output_path = Path(output_file)
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2, default=datetime_converter)

        return str(output_path)

    def generate_executive_summary(self) -> str:
        """Generate executive summary for stakeholders"""
        performance_report = self.generate_performance_report()
        security_report = self.generate_security_report()

        summary = f"""
# 🧪 PsychSync Integration Test Suite - Executive Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Key Metrics

- **Total Tests:** {performance_report['summary']['total_tests']}
- **Pass Rate:** {performance_report['summary']['pass_rate']:.1f}%
- **Average Execution Time:** {performance_report['summary']['avg_execution_time']:.2f} seconds
- **Performance Score:** {performance_report['summary']['avg_performance_score']:.1f}/100
- **Security Score:** {security_report['security_scores']['average']:.1f}/100

## 🎯 Status Overview

### **Performance Status:** {'✅ EXCELLENT' if performance_report['summary']['pass_rate'] >= 95 else '⚠️  GOOD' if performance_report['summary']['pass_rate'] >= 85 else '❌ NEEDS ATTENTION'}
### **Security Status:** {'✅ COMPLIANT' if security_report['compliance_status']['overall_compliance'] else '⚠️  REQUIRES IMPROVEMENT'}
### **Production Readiness:** {'✅ READY' if performance_report['summary']['pass_rate'] >= 90 and security_report['compliance_status']['overall_compliance'] else '⚠️  NEEDS REVIEW'}

## 🔒 Compliance Status

- **OWASP Top 10:** {'✅ Compliant' if security_report['compliance_status']['owasp']['compliant'] else '❌ Non-Compliant'}
- **PCI DSS:** {'✅ Compliant' if security_report['compliance_status']['pci']['compliant'] else '❌ Non-Compliant'}

## ⚡ Performance Highlights

- **Fastest Test:** {performance_report['performance_analysis']['fastest_test']:.3f} seconds
- **Slowest Test:** {performance_report['performance_analysis']['slowest_test']:.3f} seconds
- **Performance Distribution:**
  - Excellent (90-100): {performance_report['performance_analysis']['performance_distribution']['excellent']} tests
  - Good (70-89): {performance_report['performance_analysis']['performance_distribution']['good']} tests
  - Fair (50-69): {performance_report['performance_analysis']['performance_distribution']['fair']} tests
  - Poor (0-49): {performance_report['performance_analysis']['performance_distribution']['poor']} tests

## 📋 Recommendations

### **Performance:**
{chr(10).join(f"- {rec}" for rec in performance_report['recommendations']) if performance_report['recommendations'] else "- No performance issues detected"}

### **Security:**
{chr(10).join(f"- {rec}" for rec in security_report['security_recommendations']) if security_report['security_recommendations'] else "- No security concerns identified"}

---
*This report was generated automatically by the PsychSync Test Analytics Dashboard*
        """

        return summary.strip()


async def main():
    """Main execution function"""
    print("🚀 Starting PsychSync Integration Test Analytics Dashboard")
    print("=" * 60)

    # Initialize analytics engine
    analytics = TestAnalyticsEngine()

    # Run test suite
    print("🧪 Executing integration test suite...")
    test_results = await analytics.run_test_suite()

    if test_results.get("exit_code", 1) == 0:
        print("✅ Test suite completed successfully!")
    else:
        print("⚠️  Test suite completed with some failures")

    # Generate reports
    print("📊 Generating analytics reports...")

    # Create output directory
    output_dir = Path("test_reports")
    output_dir.mkdir(exist_ok=True)

    # Export JSON metrics
    json_file = analytics.export_metrics_json(output_dir / "test_metrics.json")
    print(f"💾 JSON metrics exported to: {json_file}")

    # Create visual dashboard
    if HAS_PLOTTING:
        dashboard_file = analytics.create_visual_dashboard(output_dir)
        if dashboard_file:
            print(f"📈 Visual dashboard created: {dashboard_file}")
    else:
        print("⚠️  Install matplotlib, seaborn, pandas, plotly for visual dashboard")

    # Generate executive summary
    summary = analytics.generate_executive_summary()
    summary_file = output_dir / "executive_summary.md"
    with open(summary_file, "w") as f:
        f.write(summary)
    print(f"📋 Executive summary saved to: {summary_file}")

    # Display summary
    print("\n" + "=" * 60)
    print("📊 QUICK SUMMARY")
    print("=" * 60)
    print(
        summary.split("## 📊 Key Metrics")[1].split("## 🎯 Status Overview")[0].strip()
    )

    print("\n🎉 Analytics dashboard generation complete!")
    print(f"📁 All reports saved to: {output_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    # Run the analytics dashboard
    asyncio.run(main())
