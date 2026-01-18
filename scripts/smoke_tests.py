#!/usr/bin/env python3
"""
PsychSync Production Smoke Tests

Comprehensive smoke tests to verify deployment health and critical functionality.
These tests run after deployment to ensure the system is working correctly.
"""

import asyncio
import aiohttp
import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.exceptions import RequestException


@dataclass
class TestResult:
    """Test result data structure"""
    name: str
    status: str
    response_time: float
    details: str
    timestamp: datetime


class SmokeTestSuite:
    """Comprehensive smoke test suite for PsychSync deployment"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
        self.results: List[TestResult] = []

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'PsychSync-SmokeTests/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def run_test(self, name: str, method: str, path: str,
                      expected_status: int = 200, **kwargs) -> TestResult:
        """Run individual smoke test"""
        start_time = time.time()
        url = f"{self.base_url}{path}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                status = "PASS" if response.status == expected_status else "FAIL"

                details = {
                    "status_code": response.status,
                    "expected_status": expected_status,
                    "headers": dict(response.headers),
                    "response_time": f"{response_time:.3f}s"
                }

                # Try to get response body
                try:
                    response_data = await response.json()
                    details["response_data"] = response_data
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    response_text = await response.text()
                    details["response_text"] = response_text[:500]  # Limit length

                result = TestResult(
                    name=name,
                    status=status,
                    response_time=response_time,
                    details=json.dumps(details, indent=2, default=str),
                    timestamp=datetime.now()
                )

        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                name=name,
                status="FAIL",
                response_time=response_time,
                details=f"Exception: {str(e)}",
                timestamp=datetime.now()
            )

        self.results.append(result)
        return result

    async def test_health_endpoints(self) -> List[TestResult]:
        """Test health check endpoints"""
        tests = [
            ("Basic Health Check", "GET", "/api/v1/health"),
            ("Detailed Health Check", "GET", "/api/v1/health/detailed"),
            ("API Root", "GET", "/api/v1/"),
        ]

        results = []
        for name, method, path in tests:
            result = await self.run_test(name, method, path)
            results.append(result)

        return results

    async def test_auth_endpoints(self) -> List[TestResult]:
        """Test authentication endpoints (public ones only)"""
        tests = [
            ("Auth Status", "GET", "/api/v1/auth/status"),
            ("Login Endpoint Exists", "POST", "/api/v1/auth/login", None, 401),  # Should fail without credentials
        ]

        results = []
        for name, method, path, expected_status, *rest in tests:
            exp_status = expected_status if expected_status else 200
            result = await self.run_test(name, method, path, expected_status=exp_status)
            results.append(result)

        return results

    async def test_api_endpoints(self) -> List[TestResult]:
        """Test key API endpoints (public ones only)"""
        tests = [
            ("User Schema", "GET", "/api/v1/users/schema"),
            ("Assessment Templates", "GET", "/api/v1/assessments/templates", None, 401),  # Requires auth
            ("Analytics Endpoints", "GET", "/api/v1/analytics/summary", None, 401),  # Requires auth
        ]

        results = []
        for name, method, path, expected_status, *rest in tests:
            exp_status = expected_status if expected_status else 200
            result = await self.run_test(name, method, path, expected_status=exp_status)
            results.append(result)

        return results

    async def test_static_assets(self) -> List[TestResult]:
        """Test static asset serving"""
        tests = [
            ("Favicon", "GET", "/favicon.ico", None, 404),  # May not exist
            ("Robots.txt", "GET", "/robots.txt", None, 404),  # May not exist
        ]

        results = []
        for name, method, path, expected_status, *rest in tests:
            exp_status = expected_status if expected_status else 200
            result = await self.run_test(name, method, path, expected_status=exp_status)
            results.append(result)

        return results

    async def test_error_handling(self) -> List[TestResult]:
        """Test error handling"""
        tests = [
            ("404 Error", "GET", "/api/v1/nonexistent", 404),
            ("Invalid Method", "PATCH", "/api/v1/health", 405),
            ("Invalid JSON", "POST", "/api/v1/auth/login", None, 401, json={"invalid": "data"}),
        ]

        results = []
        for name, method, path, expected_status, *rest in tests:
            kwargs = {}
            if rest and rest[0] == "json":
                kwargs["json"] = rest[1]

            result = await self.run_test(name, method, path, expected_status=expected_status, **kwargs)
            results.append(result)

        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests and return summary"""
        print("🚀 Starting PsychSync Smoke Tests...")
        print(f"📍 Target: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        print("=" * 60)

        # Run test suites
        await self.test_health_endpoints()
        await self.test_auth_endpoints()
        await self.test_api_endpoints()
        await self.test_static_assets()
        await self.test_error_handling()

        # Calculate summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        summary = {
            "timestamp": datetime.now().isoformat(),
            "target_url": self.base_url,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": pass_rate,
            "overall_status": "PASS" if pass_rate >= 90 else "FAIL",
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "response_time": r.response_time,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }

        return summary

    def print_results(self, summary: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print("📊 SMOKE TEST RESULTS")
        print("=" * 60)

        print(f"📍 Target: {summary['target_url']}")
        print(f"🕐 Completed: {summary['timestamp']}")
        print(f"📈 Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"✅ Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}/{summary['total_tests']}")

        status_emoji = "✅" if summary['overall_status'] == "PASS" else "❌"
        print(f"\n{status_emoji} Overall Status: {summary['overall_status']}")

        print("\n📋 Test Details:")
        print("-" * 60)

        for result in summary["results"]:
            emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"{emoji} {result['name']}")
            print(f"   ⏱️  {result['response_time']:.3f}s")

            # Show abbreviated details for failures
            if result["status"] == "FAIL":
                details_lines = result["details"].split('\n')
                print(f"   📝 {details_lines[0] if details_lines else 'No details'}")
            print()

        # Performance summary
        response_times = [r["response_time"] for r in summary["results"]]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            min_response = min(response_times)

            print("⚡ Performance Summary:")
            print(f"   📊 Average: {avg_response:.3f}s")
            print(f"   🐌 Slowest: {max_response:.3f}s")
            print(f"   🚀 Fastest: {min_response:.3f}s")

    def save_results(self, summary: Dict[str, Any], output_file: str = None):
        """Save test results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"smoke_test_results_{timestamp}.json"

        output_path = Path(output_file)
        output_path.write_text(json.dumps(summary, indent=2, default=str))
        print(f"\n💾 Results saved to: {output_path.absolute()}")

        return output_path

    def generate_slack_message(self, summary: Dict[str, Any]) -> str:
        """Generate Slack notification message"""
        status_emoji = "✅" if summary['overall_status'] == "PASS" else "❌"
        status_color = "good" if summary['overall_status'] == "PASS' else "danger"

        message = f"""
{status_emoji} PsychSync Smoke Test Results

*Target:* {summary['target_url']}
*Status:* {summary['overall_status']}
*Pass Rate:* {summary['pass_rate']:.1f}%
*Passed:* {summary['passed_tests']}/{summary['total_tests']}
*Failed:* {summary['failed_tests']}/{summary['total_tests']}

*Completed:* {summary['timestamp']}

"""

        # Add failed tests if any
        failed_tests = [r for r in summary["results"] if r["status"] == "FAIL"]
        if failed_tests:
            message += "*Failed Tests:*\n"
            for test in failed_tests[:5]:  # Limit to first 5 failures
                message += f"• {test['name']} ({test['response_time']:.3f}s)\n"

            if len(failed_tests) > 5:
                message += f"• ... and {len(failed_tests) - 5} more failures\n"

        return message


async def main():
    """Main smoke test execution"""
    parser = argparse.ArgumentParser(description="PsychSync Smoke Tests")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        default="staging",
        help="Target environment for smoke tests"
    )
    parser.add_argument(
        "--url",
        help="Custom base URL for testing"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds"
    )
    parser.add_argument(
        "--output",
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--slack-webhook",
        help="Slack webhook URL for notifications"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with non-zero code on test failures"
    )

    args = parser.parse_args()

    # Determine target URL
    if args.url:
        base_url = args.url
    elif args.environment == "production":
        base_url = "https://api.psychsync.com"
    else:
        base_url = "https://psychsync-staging.azurewebsites.net"

    # Run smoke tests
    async with SmokeTestSuite(base_url, args.timeout) as suite:
        summary = await suite.run_all_tests()

        # Print results
        suite.print_results(summary)

        # Save results
        if args.output:
            suite.save_results(summary, args.output)
        else:
            suite.save_results(summary)

        # Send Slack notification
        if args.slack_webhook and summary['overall_status'] == "FAIL":
            try:
                message = suite.generate_slack_message(summary)
                response = requests.post(args.slack_webhook, json={"text": message})
                if response.status_code == 200:
                    print("📢 Slack notification sent successfully")
                else:
                    print(f"⚠️  Failed to send Slack notification: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Error sending Slack notification: {e}")

        # Exit with appropriate code
        if args.fail_on_error and summary['overall_status'] == "FAIL":
            print(f"\n❌ Smoke tests failed with {summary['failed_tests']} failures")
            sys.exit(1)
        else:
            print(f"\n✅ Smoke tests completed successfully")
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
