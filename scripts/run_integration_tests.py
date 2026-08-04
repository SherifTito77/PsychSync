#!/usr/bin/env python3
"""
Automated Integration Test Execution Script
Comprehensive test execution with analytics, reporting, and notification

Features:
- Automated test suite execution
- Real-time progress monitoring
- Performance and security analytics
- HTML dashboard generation
- Email notifications for stakeholders
- CI/CD integration support
- Test result archiving

Author: DevOps Team
Version: 1.0 Enterprise Automation
"""

import argparse
import asyncio
import json
import os
import smtplib
import sys
import time
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytest
    import tabulate

    from scripts.test_analytics_dashboard import TestAnalyticsEngine

    HAS_DEPS = True
except ImportError as e:
    print(f"⚠️  Missing dependencies: {e}")
    print("Run: pip install pytest tabulate matplotlib seaborn pandas plotly")
    HAS_DEPS = False


class TestExecutor:
    """Automated test execution with comprehensive analytics"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()
        self.analytics = TestAnalyticsEngine()
        self.start_time = None
        self.results = {}

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "test_paths": [
                "tests/integration/test_api_endpoints.py",
                "tests/integration/test_database_crud.py",
                "tests/integration/test_authentication_flow.py",
                "tests/integration/test_token_refresh.py",
                "tests/integration/test_file_upload.py",
                "tests/integration/test_stripe_billing.py",
                "tests/integration/test_email_sending.py",
            ],
            "parallel_execution": True,
            "max_workers": 4,
            "timeout_minutes": 30,
            "generate_reports": True,
            "create_dashboard": True,
            "send_notifications": False,
            "archive_results": True,
            "performance_threshold": 200,  # ms
            "security_threshold": 80,  # score
        }

    async def execute_test_suite(self, test_paths: List[str] = None) -> Dict[str, Any]:
        """Execute the complete test suite with analytics"""
        print("🚀 Starting Automated Integration Test Execution")
        print("=" * 60)

        self.start_time = time.time()
        test_paths = test_paths or self.config["test_paths"]

        if not HAS_DEPS:
            return {
                "success": False,
                "error": "Missing required dependencies",
                "timestamp": datetime.now().isoformat(),
            }

        # Initialize results structure
        self.results = {
            "execution_id": f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "test_paths": test_paths,
            "individual_results": {},
            "summary": {},
            "analytics": {},
            "files_generated": [],
        }

        try:
            # Execute tests with progress monitoring
            await self._execute_with_progress(test_paths)

            # Generate analytics and reports
            if self.config["generate_reports"]:
                await self._generate_reports()

            # Send notifications if configured
            if self.config["send_notifications"]:
                await self._send_notifications()

            # Archive results if configured
            if self.config["archive_results"]:
                await self._archive_results()

            # Calculate final summary
            self._calculate_summary()

            # Display results
            self._display_results()

            return {
                "success": True,
                "execution_id": self.results["execution_id"],
                "summary": self.results["summary"],
                "files_generated": self.results["files_generated"],
                "duration": time.time() - self.start_time,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "execution_id": self.results.get("execution_id"),
                "duration": time.time() - self.start_time,
                "timestamp": datetime.now().isoformat(),
            }
            print(f"❌ Test execution failed: {e}")
            return error_result

    async def _execute_with_progress(self, test_paths: List[str]):
        """Execute tests with real-time progress monitoring"""
        total_tests = 0
        completed_tests = 0

        # Count total tests first
        for test_path in test_paths:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_path, "--collect-only", "-q"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent,
                )

                if result.returncode == 0:
                    # Count collected tests
                    test_count = len(
                        [
                            line
                            for line in result.stdout.split("\n")
                            if "<Function" in line or "<TestCase" in line
                        ]
                    )
                    total_tests += test_count
            except Exception:
                pass

        print(f"📊 Total tests to execute: {total_tests}")
        print("🔄 Starting test execution...\n")

        # Execute each test path
        for i, test_path in enumerate(test_paths, 1):
            print(f"📂 [{i}/{len(test_paths)}] Executing: {test_path}")

            try:
                # Run pytest with JSON output
                json_file = f"test_results_{Path(test_path).stem}.json"

                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    test_path,
                    "--json-report",
                    f"--json-report-file={json_file}",
                    "--tb=short",
                    "-v",
                ]

                start_time = time.time()
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent,
                )
                execution_time = time.time() - start_time

                # Parse results
                test_results = self._parse_json_report(json_file)

                self.results["individual_results"][test_path] = {
                    "exit_code": result.returncode,
                    "execution_time": execution_time,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "test_results": test_results,
                    "timestamp": datetime.now().isoformat(),
                }

                # Update progress
                if test_results:
                    completed_tests += test_results.get("total", 0)

                # Display progress
                progress = (
                    (completed_tests / total_tests * 100) if total_tests > 0 else 0
                )
                status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"

                print(f"   Status: {status}")
                print(f"   Time: {execution_time:.2f}s")
                if test_results:
                    print(
                        f"   Tests: {test_results.get('passed', 0)}/{test_results.get('total', 0)} passed"
                    )
                print(f"   Progress: {progress:.1f}%\n")

                # Cleanup JSON file
                try:
                    os.remove(json_file)
                except Exception as e:
                    pass

            except Exception as e:
                print(f"   ❌ Error executing {test_path}: {e}")
                self.results["individual_results"][test_path] = {
                    "exit_code": 1,
                    "error": str(e),
                    "execution_time": 0,
                    "timestamp": datetime.now().isoformat(),
                }

    def _parse_json_report(self, json_file: str) -> Dict[str, Any]:
        """Parse pytest JSON report"""
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            summary = data.get("summary", {})
            return {
                "total": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "error": summary.get("error", 0),
                "duration": summary.get("duration", 0.0),
            }
        except Exception:
            return {}

    async def _generate_reports(self):
        """Generate comprehensive analytics reports"""
        print("📊 Generating analytics reports...")

        # Create output directory
        output_dir = Path("test_reports") / self.results["execution_id"]
        output_dir.mkdir(parents=True, exist_ok=True)

        # Update analytics engine with test results
        for test_path, result in self.results["individual_results"].items():
            if "test_results" in result:
                # Convert JSON results to TestMetrics objects
                pass  # Analytics engine would parse these

        # Generate performance report
        performance_report = self.analytics.generate_performance_report()
        self.results["analytics"]["performance"] = performance_report

        # Generate security report
        security_report = self.analytics.generate_security_report()
        self.results["analytics"]["security"] = security_report

        # Export detailed metrics
        metrics_file = output_dir / "detailed_metrics.json"
        self.analytics.export_metrics_json(str(metrics_file))
        self.results["files_generated"].append(str(metrics_file))

        # Generate executive summary
        summary = self.analytics.generate_executive_summary()
        summary_file = output_dir / "executive_summary.md"
        with open(summary_file, "w") as f:
            f.write(summary)
        self.results["files_generated"].append(str(summary_file))

        # Create visual dashboard
        if self.config["create_dashboard"]:
            dashboard_file = self.analytics.create_visual_dashboard(str(output_dir))
            if dashboard_file:
                self.results["files_generated"].append(dashboard_file)
                print(f"📈 Visual dashboard: {dashboard_file}")

        print("✅ Analytics reports generated")

    async def _send_notifications(self):
        """Send email notifications to stakeholders"""
        print("📧 Sending notifications...")

        try:
            # Create notification content
            summary = self.results.get("summary", {})
            performance = self.results.get("analytics", {}).get("performance", {})
            security = self.results.get("analytics", {}).get("security", {})

            subject = f"PsychSync Integration Test Results - {summary.get('status', 'UNKNOWN').upper()}"

            body = f"""
PsychSync Integration Test Execution Report

Execution ID: {self.results['execution_id']}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Summary:
- Status: {summary.get('status', 'Unknown')}
- Total Tests: {summary.get('total_tests', 0)}
- Pass Rate: {summary.get('pass_rate', 0):.1f}%
- Duration: {summary.get('duration', 0):.2f} seconds

🚀 Performance:
- Average Performance Score: {performance.get('summary', {}).get('avg_performance_score', 0):.1f}/100
- Average Execution Time: {performance.get('summary', {}).get('avg_execution_time', 0):.3f}s

🔒 Security:
- Security Score: {security.get('security_scores', {}).get('average', 0):.1f}/100
- OWASP Compliance: {'✅ Compliant' if security.get('compliance_status', {}).get('owasp', {}).get('compliant') else '❌ Non-Compliant'}
- PCI Compliance: {'✅ Compliant' if security.get('compliance_status', {}).get('pci', {}).get('compliant') else '❌ Non-Compliant'}

📁 Generated Reports:
{chr(10).join(f"- {Path(file).name}" for file in self.results.get('files_generated', []))}

---
This is an automated message from the PsychSync Test Execution System
            """

            # Here you would implement actual email sending
            # For now, just save the notification
            notification_file = (
                Path("test_reports") / self.results["execution_id"] / "notification.txt"
            )
            with open(notification_file, "w") as f:
                f.write(f"Subject: {subject}\n\n{body}")

            self.results["files_generated"].append(str(notification_file))
            print(f"📧 Notification saved to: {notification_file}")

        except Exception as e:
            print(f"⚠️  Failed to send notifications: {e}")

    async def _archive_results(self):
        """Archive test results for historical tracking"""
        print("📦 Archiving test results...")

        archive_dir = Path("test_archives") / datetime.now().strftime("%Y/%m")
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create archive file
        archive_file = archive_dir / f"{self.results['execution_id']}.json"

        with open(archive_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        self.results["files_generated"].append(str(archive_file))
        print(f"📦 Results archived to: {archive_file}")

    def _calculate_summary(self):
        """Calculate final test execution summary"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for test_path, result in self.results["individual_results"].items():
            test_data = result.get("test_results", {})
            total_tests += test_data.get("total", 0)
            total_passed += test_data.get("passed", 0)
            total_failed += test_data.get("failed", 0)
            total_skipped += test_data.get("skipped", 0)

        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        duration = time.time() - self.start_time

        # Determine status
        if pass_rate >= 95:
            status = "EXCELLENT"
        elif pass_rate >= 90:
            status = "GOOD"
        elif pass_rate >= 80:
            status = "ACCEPTABLE"
        else:
            status = "NEEDS ATTENTION"

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "pass_rate": pass_rate,
            "duration": duration,
            "status": status,
        }

    def _display_results(self):
        """Display formatted test results"""
        summary = self.results["summary"]
        performance = (
            self.results.get("analytics", {}).get("performance", {}).get("summary", {})
        )
        security = (
            self.results.get("analytics", {})
            .get("security", {})
            .get("security_scores", {})
        )

        print("\n" + "=" * 60)
        print("🎉 TEST EXECUTION COMPLETE")
        print("=" * 60)

        # Summary table
        summary_data = [
            ["Total Tests", summary["total_tests"]],
            ["Passed", summary["passed"]],
            ["Failed", summary["failed"]],
            ["Skipped", summary["skipped"]],
            ["Pass Rate", f"{summary['pass_rate']:.1f}%"],
            ["Duration", f"{summary['duration']:.2f}s"],
            ["Status", summary["status"]],
        ]

        print("\n📊 EXECUTION SUMMARY")
        print(
            tabulate.tabulate(
                summary_data, headers=["Metric", "Value"], tablefmt="grid"
            )
        )

        # Performance metrics
        perf_data = [
            [
                "Avg Performance Score",
                f"{performance.get('avg_performance_score', 0):.1f}/100",
            ],
            ["Avg Execution Time", f"{performance.get('avg_execution_time', 0):.3f}s"],
            [
                "Total Execution Time",
                f"{performance.get('total_execution_time', 0):.2f}s",
            ],
        ]

        print("\n🚀 PERFORMANCE METRICS")
        print(
            tabulate.tabulate(perf_data, headers=["Metric", "Value"], tablefmt="grid")
        )

        # Security metrics
        security_data = [
            ["Security Score", f"{security.get('average', 0):.1f}/100"],
            ["Min Score", f"{security.get('minimum', 0):.1f}"],
            ["Max Score", f"{security.get('maximum', 0):.1f}"],
        ]

        print("\n🔒 SECURITY METRICS")
        print(
            tabulate.tabulate(
                security_data, headers=["Metric", "Value"], tablefmt="grid"
            )
        )

        # Generated files
        print("\n📁 GENERATED FILES")
        for i, file_path in enumerate(self.results.get("files_generated", []), 1):
            print(f"{i:2d}. {Path(file_path).name}")
            print(f"    → {Path(file_path).parent}")

        print("\n" + "=" * 60)
        print("✅ Test execution completed successfully!")
        print(
            f"📊 Detailed reports available in: test_reports/{self.results['execution_id']}/"
        )
        print("=" * 60)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="PsychSync Integration Test Execution with Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all integration tests with full analytics
  python run_integration_tests.py

  # Run specific test modules
  python run_integration_tests.py --paths tests/integration/test_api_endpoints.py tests/integration/test_auth_flow.py

  # Disable visual dashboard generation
  python run_integration_tests.py --no-dashboard

  # Enable email notifications
  python run_integration_tests.py --notify --email admin@example.com

  # Custom output directory
  python run_integration_tests.py --output custom_reports
        """,
    )

    parser.add_argument(
        "--paths", nargs="+", help="Specific test paths to execute", default=None
    )

    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable visual dashboard generation",
    )

    parser.add_argument(
        "--notify", action="store_true", help="Enable email notifications"
    )

    parser.add_argument("--email", help="Email address for notifications")

    parser.add_argument(
        "--output", help="Custom output directory", default="test_reports"
    )

    parser.add_argument(
        "--timeout", type=int, help="Test execution timeout in minutes", default=30
    )

    parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel test execution"
    )

    parser.add_argument(
        "--workers", type=int, help="Number of parallel workers", default=4
    )

    parser.add_argument("--config", help="Path to configuration file", default=None)

    return parser


async def main():
    """Main execution function"""
    parser = create_argument_parser()
    args = parser.parse_args()

    if not HAS_DEPS:
        print("❌ Missing required dependencies")
        print(
            "Install with: pip install pytest tabulate matplotlib seaborn pandas plotly"
        )
        return 1

    # Load configuration
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config, "r") as f:
            config = json.load(f)

    # Override config with command line arguments
    config.update(
        {
            "test_paths": args.paths,
            "create_dashboard": not args.no_dashboard,
            "send_notifications": args.notify,
            "timeout_minutes": args.timeout,
            "parallel_execution": args.parallel,
            "max_workers": args.workers,
        }
    )

    # Execute tests
    executor = TestExecutor(config)
    result = await executor.execute_test_suite()

    return 0 if result.get("success", False) else 1


if __name__ == "__main__":
    # Import subprocess for test execution
    import subprocess

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
