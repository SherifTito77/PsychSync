#!/usr/bin/env python3
"""
PsychSync Synthetic Monitoring
Automated testing of critical user journeys and system dependencies
"""

import asyncio
import aiohttp
import time
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configuration
BASE_URL = "https://api.psychsync.com"
FRONTEND_URL = "https://app.psychsync.com"
STRIPE_API = "https://api.stripe.com/v1"
MONITORING_PORT = 8082
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
PAGERDUTY_KEY = os.getenv("PAGERDUTY_INTEGRATION_KEY")

# Monitoring metrics
SYNTHETIC_TESTS_TOTAL = Counter('psychsync_synthetic_tests_total', 'Total synthetic tests', ['test_name', 'status'])
SYNTHETIC_TEST_DURATION = Histogram('psychsync_synthetic_test_duration_seconds', 'Synthetic test duration', ['test_name'])
CRITICAL_PATH_HEALTH = Gauge('psychsync_critical_path_health', 'Critical path health score', ['path_name'])
EXTERNAL_DEPENDENCY_HEALTH = Gauge('psychsync_external_dependency_health', 'External dependency health', ['dependency'])

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, WARN
    response_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SyntheticTestSuite:
    """Comprehensive synthetic monitoring test suite"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'PsychSync-Synthetic-Monitoring/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def record_metric(self, test_name: str, status: str, duration: float):
        """Record Prometheus metrics"""
        SYNTHETIC_TESTS_TOTAL.labels(test_name=test_name, status=status).inc()
        SYNTHETIC_TEST_DURATION.labels(test_name=test_name).observe(duration)

    async def run_test(self, test_name: str, test_func) -> TestResult:
        """Run individual synthetic test with metrics"""
        start_time = time.time()

        try:
            result = await test_func()
            duration = time.time() - start_time

            if isinstance(result, TestResult):
                result.response_time = duration
                self.record_metric(result.test_name, result.status, duration)
            else:
                # If test_func returns something else, assume success
                result = TestResult(
                    test_name=test_name,
                    status="PASS",
                    response_time=duration
                )
                self.record_metric(test_name, "PASS", duration)

        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                response_time=duration,
                error_message=str(e)
            )
            self.record_metric(test_name, "FAIL", duration)

        self.results.append(result)
        return result

    # Critical User Journey Tests
    async def test_api_health_check(self) -> TestResult:
        """Test API health check endpoint"""
        async with self.session.get(f"{BASE_URL}/api/v1/health") as response:
            if response.status == 200:
                data = await response.json()
                return TestResult(
                    test_name="api_health_check",
                    status="PASS",
                    details={
                        "status": data.get("status"),
                        "version": data.get("version"),
                        "timestamp": data.get("timestamp")
                    }
                )
            else:
                return TestResult(
                    test_name="api_health_check",
                    status="FAIL",
                    error_message=f"HTTP {response.status}"
                )

    async def test_user_registration_flow(self) -> TestResult:
        """Test complete user registration flow"""
        timestamp = int(time.time())
        test_email = f"synthetic_{timestamp}@test.psychsync.com"

        try:
            # Step 1: Check registration endpoint is accessible
            async with self.session.get(f"{BASE_URL}/api/v1/auth/register") as response:
                if response.status not in [200, 405]:  # 405 is acceptable for GET
                    return TestResult(
                        test_name="user_registration_flow",
                        status="FAIL",
                        error_message=f"Registration endpoint inaccessible: {response.status}"
                    )

            # Step 2: Test registration data validation
            registration_data = {
                "email": test_email,
                "password": "testPassword123!",
                "first_name": "Synthetic",
                "last_name": "Test"
            }

            async with self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=registration_data
            ) as response:
                if response.status == 201:
                    return TestResult(
                        test_name="user_registration_flow",
                        status="PASS",
                        details={"test_email": test_email}
                    )
                elif response.status == 400:
                    # Expected validation error is acceptable
                    return TestResult(
                        test_name="user_registration_flow",
                        status="PASS",
                        details={"validation_working": True}
                    )
                else:
                    return TestResult(
                        test_name="user_registration_flow",
                        status="FAIL",
                        error_message=f"Unexpected status: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="user_registration_flow",
                status="FAIL",
                error_message=str(e)
            )

    async def test_assessment_start_flow(self) -> TestResult:
        """Test assessment initialization and question retrieval"""
        try:
            # Test available assessment templates
            async with self.session.get(f"{BASE_URL}/api/v1/assessments/templates") as response:
                if response.status == 200:
                    templates = await response.json()
                    if not templates.get("templates"):
                        return TestResult(
                            test_name="assessment_start_flow",
                            status="WARN",
                            error_message="No assessment templates available"
                        )

                    template_id = templates["templates"][0]["id"]

                    # Test starting an assessment
                    start_data = {
                        "template_id": template_id,
                        "user_id": "synthetic-test-user"
                    }

                    async with self.session.post(
                        f"{BASE_URL}/api/v1/assessments",
                        json=start_data
                    ) as response:
                        if response.status in [201, 200]:
                            return TestResult(
                                test_name="assessment_start_flow",
                                status="PASS",
                                details={"template_id": template_id}
                            )
                        elif response.status == 401:
                            # Expected for unauthenticated request
                            return TestResult(
                                test_name="assessment_start_flow",
                                status="PASS",
                                details={"auth_required": True}
                            )
                        else:
                            return TestResult(
                                test_name="assessment_start_flow",
                                status="FAIL",
                                error_message=f"Assessment start failed: {response.status}"
                            )
                else:
                    return TestResult(
                        test_name="assessment_start_flow",
                        status="FAIL",
                        error_message=f"Cannot fetch templates: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="assessment_start_flow",
                status="FAIL",
                error_message=str(e)
            )

    async def test_team_creation_flow(self) -> TestResult:
        """Test team creation and management functionality"""
        try:
            team_data = {
                "name": "Synthetic Test Team",
                "description": "Team for synthetic monitoring tests",
                "organization_id": "test-org"
            }

            async with self.session.post(f"{BASE_URL}/api/v1/teams", json=team_data) as response:
                if response.status == 401:
                    # Expected for unauthenticated request
                    return TestResult(
                        test_name="team_creation_flow",
                        status="PASS",
                        details={"auth_required": True}
                    )
                elif response.status in [201, 200]:
                    return TestResult(
                        test_name="team_creation_flow",
                        status="PASS",
                        details={"team_creation_working": True}
                    )
                else:
                    return TestResult(
                        test_name="team_creation_flow",
                        status="FAIL",
                        error_message=f"Team creation failed: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="team_creation_flow",
                status="FAIL",
                error_message=str(e)
            )

    async def test_frontend_loading(self) -> TestResult:
        """Test frontend application loading"""
        try:
            async with self.session.get(FRONTEND_URL) as response:
                if response.status == 200:
                    content = await response.text()

                    # Check for critical elements
                    critical_elements = [
                        '<div id="root">',
                        'react',
                        'javascript'
                    ]

                    missing_elements = []
                    for element in critical_elements:
                        if element not in content.lower():
                            missing_elements.append(element)

                    if missing_elements:
                        return TestResult(
                            test_name="frontend_loading",
                            status="WARN",
                            error_message=f"Missing elements: {missing_elements}",
                            details={"content_length": len(content)}
                        )
                    else:
                        return TestResult(
                            test_name="frontend_loading",
                            status="PASS",
                            details={"content_length": len(content)}
                        )
                else:
                    return TestResult(
                        test_name="frontend_loading",
                        status="FAIL",
                        error_message=f"Frontend not loading: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="frontend_loading",
                status="FAIL",
                error_message=str(e)
            )

    # External Dependency Tests
    async def test_stripe_connectivity(self) -> TestResult:
        """Test Stripe API connectivity"""
        try:
            # Test Stripe API status endpoint
            async with self.session.get(f"{STRIPE_API}/account") as response:
                if response.status == 401:
                    # Expected without proper authentication
                    return TestResult(
                        test_name="stripe_connectivity",
                        status="PASS",
                        details={"stripe_reachable": True}
                    )
                else:
                    return TestResult(
                        test_name="stripe_connectivity",
                        status="FAIL",
                        error_message=f"Unexpected Stripe response: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="stripe_connectivity",
                status="FAIL",
                error_message=str(e)
            )

    async def test_email_service_connectivity(self) -> TestResult:
        """Test email service connectivity (simulated)"""
        try:
            # This would test your email service endpoint
            # For now, we'll simulate a connectivity test

            test_email_data = {
                "to": "test@psychsync.com",
                "subject": "Synthetic Monitor Test",
                "body": "Test email from synthetic monitoring"
            }

            # Replace with your actual email service endpoint
            async with self.session.post(
                f"{BASE_URL}/api/v1/emails/test",
                json=test_email_data,
                timeout=10
            ) as response:
                if response.status in [200, 202, 401]:  # 401 acceptable if auth required
                    return TestResult(
                        test_name="email_service_connectivity",
                        status="PASS",
                        details={"email_service_reachable": True}
                    )
                else:
                    return TestResult(
                        test_name="email_service_connectivity",
                        status="FAIL",
                        error_message=f"Email service error: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="email_service_connectivity",
                status="FAIL",
                error_message=str(e)
            )

    async def test_database_connectivity(self) -> TestResult:
        """Test database connectivity via API"""
        try:
            async with self.session.get(f"{BASE_URL}/api/v1/health/database") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "healthy":
                        return TestResult(
                            test_name="database_connectivity",
                            status="PASS",
                            details=data
                        )
                    else:
                        return TestResult(
                            test_name="database_connectivity",
                            status="FAIL",
                            error_message=f"Database unhealthy: {data.get('message')}"
                        )
                else:
                    return TestResult(
                        test_name="database_connectivity",
                        status="FAIL",
                        error_message=f"Health check failed: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="database_connectivity",
                status="FAIL",
                error_message=str(e)
            )

    async def test_redis_connectivity(self) -> TestResult:
        """Test Redis connectivity via API"""
        try:
            async with self.session.get(f"{BASE_URL}/api/v1/health/cache") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "healthy":
                        return TestResult(
                            test_name="redis_connectivity",
                            status="PASS",
                            details=data
                        )
                    else:
                        return TestResult(
                            test_name="redis_connectivity",
                            status="FAIL",
                            error_message=f"Redis unhealthy: {data.get('message')}"
                        )
                else:
                    return TestResult(
                        test_name="redis_connectivity",
                        status="FAIL",
                        error_message=f"Cache health check failed: {response.status}"
                    )

        except Exception as e:
            return TestResult(
                test_name="redis_connectivity",
                status="FAIL",
                error_message=str(e)
            )

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all synthetic tests and return summary"""
        logger.info("Starting synthetic monitoring test suite")
        self.results = []  # Reset results

        tests = [
            ("API Health Check", self.test_api_health_check),
            ("User Registration Flow", self.test_user_registration_flow),
            ("Assessment Start Flow", self.test_assessment_start_flow),
            ("Team Creation Flow", self.test_team_creation_flow),
            ("Frontend Loading", self.test_frontend_loading),
            ("Stripe Connectivity", self.test_stripe_connectivity),
            ("Email Service Connectivity", self.test_email_service_connectivity),
            ("Database Connectivity", self.test_database_connectivity),
            ("Redis Connectivity", self.test_redis_connectivity),
        ]

        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            result = await self.run_test(test_name, test_func)
            logger.info(f"Test {test_name}: {result.status} ({result.response_time:.2f}s)")

        # Calculate summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        warned_tests = len([r for r in self.results if r.status == "WARN"])

        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_status = "PASS" if pass_rate >= 90 and failed_tests == 0 else "FAIL"

        # Update critical path health metrics
        CRITICAL_PATH_HEALTH.labels(path_name="api").set(
            1.0 if any(r.test_name == "api_health_check" and r.status == "PASS" for r in self.results) else 0.0
        )
        CRITICAL_PATH_HEALTH.labels(path_name="frontend").set(
            1.0 if any(r.test_name == "frontend_loading" and r.status == "PASS" for r in self.results) else 0.0
        )
        CRITICAL_PATH_HEALTH.labels(path_name="user_flow").set(
            1.0 if all(r.status in ["PASS", "WARN"] for r in self.results
                     if "registration" in r.test_name or "assessment" in r.test_name) else 0.0
        )

        # Update external dependency health metrics
        for result in self.results:
            if "stripe" in result.test_name:
                EXTERNAL_DEPENDENCY_HEALTH.labels(dependency="stripe").set(
                    1.0 if result.status == "PASS" else 0.0
                )
            elif "email" in result.test_name:
                EXTERNAL_DEPENDENCY_HEALTH.labels(dependency="email").set(
                    1.0 if result.status == "PASS" else 0.0
                )
            elif "database" in result.test_name:
                EXTERNAL_DEPENDENCY_HEALTH.labels(dependency="database").set(
                    1.0 if result.status == "PASS" else 0.0
                )
            elif "redis" in result.test_name:
                EXTERNAL_DEPENDENCY_HEALTH.labels(dependency="redis").set(
                    1.0 if result.status == "PASS" else 0.0
                )

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warned_tests": warned_tests,
            "pass_rate": pass_rate,
            "overall_status": overall_status,
            "results": [asdict(r) for r in self.results]
        }

        logger.info(f"Test suite completed: {passed_tests}/{total_tests} passed ({pass_rate:.1f}%)")
        return summary

    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate human-readable test report"""
        report = f"""
# PsychSync Synthetic Monitoring Report

**Timestamp:** {summary['timestamp']}
**Overall Status:** {summary['overall_status']}
**Pass Rate:** {summary['pass_rate']:.1f}%

## Test Results Summary

- **Total Tests:** {summary['total_tests']}
- **Passed:** {summary['passed_tests']}
- **Failed:** {summary['failed_tests']}
- **Warnings:** {summary['warned_tests']}

## Detailed Results

"""
        for result in summary["results"]:
            status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            report += f"{status_emoji} **{result['test_name']}** - {result['status']} ({result['response_time']:.2f}s)\n"

            if result["error_message"]:
                report += f"   - Error: {result['error_message']}\n"

            if result["details"]:
                report += f"   - Details: {json.dumps(result['details'], indent=2)}\n"

            report += "\n"

        return report

    async def send_alert(self, summary: Dict[str, Any]):
        """Send alert if critical failures detected"""
        critical_failures = [
            r for r in self.results
            if r.status == "FAIL" and any(keyword in r.test_name.lower()
                                         for keyword in ["health", "api", "frontend", "database"])
        ]

        if not critical_failures:
            return

        message = f"""
🚨 **CRITICAL SYNTHETIC MONITORING ALERT**

**Timestamp:** {summary['timestamp']}
**Failures:** {len(critical_failures)} critical failures

**Failed Tests:**
"""
        for result in critical_failures:
            message += f"- {result['test_name']}: {result.get('error_message', 'Unknown error')}\n"

        # Send to Slack
        if SLACK_WEBHOOK:
            try:
                response = requests.post(
                    SLACK_WEBHOOK,
                    json={"text": message},
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info("Alert sent to Slack")
                else:
                    logger.error(f"Failed to send Slack alert: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending Slack alert: {e}")

        # Send to PagerDuty for critical issues
        if PAGERDUTY_KEY and len(critical_failures) >= 2:
            try:
                from pdpyras import EventsAPISession
                pagerduty = EventsAPISession(PAGERDUTY_KEY)
                pagerduty.trigger(
                    "PsychSync Critical Synthetic Monitoring Failure",
                    severity="critical",
                    source="synthetic-monitoring",
                    component="psychsync-platform",
                    custom_details={"summary": summary, "critical_failures": len(critical_failures)}
                )
                logger.info("Alert sent to PagerDuty")
            except Exception as e:
                logger.error(f"Error sending PagerDuty alert: {e}")


async def main():
    """Main function to run synthetic monitoring"""
    logger.info("Starting PsychSync Synthetic Monitoring")

    # Start metrics server
    start_http_server(MONITORING_PORT)
    logger.info(f"Metrics server started on port {MONITORING_PORT}")

    try:
        async with SyntheticTestSuite() as test_suite:
            while True:
                # Run all tests
                summary = await test_suite.run_all_tests()

                # Generate and save report
                report = test_suite.generate_report(summary)

                # Save report to file
                report_path = Path("/tmp/synthetic_monitoring_report.md")
                report_path.write_text(report)

                logger.info(f"Report saved to {report_path}")

                # Send alerts if needed
                await test_suite.send_alert(summary)

                # Wait for next run (5 minutes)
                await asyncio.sleep(300)

    except KeyboardInterrupt:
        logger.info("Shutting down synthetic monitoring")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
