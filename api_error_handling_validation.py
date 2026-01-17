#!/usr/bin/env python3
"""
API Error Handling Validation Suite
Tests graceful error messages and response handling for all failure scenarios
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_validation_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ErrorTestResult:
    """Error test result data structure"""
    test_name: str
    endpoint: str
    method: str
    expected_status_code: int
    actual_status_code: int
    response_time_ms: float
    error_message: str
    response_body: Dict[str, Any]
    graceful_handling: bool
    timestamp: datetime
    validation_passed: bool

class APIErrorValidator:
    """
    Comprehensive API error handling validation suite
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Error-Validator/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_auth_token(self) -> str:
        """Get authentication token for protected endpoints"""
        if not self.auth_token:
            try:
                # Try to login with test credentials
                async with self.session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "testpassword123"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.auth_token = data.get("access_token", "test_token")
                    else:
                        self.auth_token = "test_token"  # Use test token for validation
            except Exception:
                self.auth_token = "test_token"  # Use test token on any error
        return self.auth_token

    async def test_error_scenario(self, test_name: str, endpoint: str, method: str,
                                 payload: Optional[Dict] = None, headers: Optional[Dict] = None,
                                 expected_status_code: int = 400) -> ErrorTestResult:
        """Test a specific error scenario"""
        start_time = time.time()
        url = f"{self.base_url}{endpoint}"

        try:
            # Prepare request headers
            request_headers = {}
            if headers:
                request_headers.update(headers)
            if self.auth_token:
                request_headers["Authorization"] = f"Bearer {self.auth_token}"

            # Make request
            if method == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    content = await response.read()
                    response_body = json.loads(content.decode()) if content else {}
                    actual_status = response.status

            elif method == "POST":
                async with self.session.post(url, json=payload, headers=request_headers) as response:
                    content = await response.read()
                    response_body = json.loads(content.decode()) if content else {}
                    actual_status = response.status

            elif method == "PUT":
                async with self.session.put(url, json=payload, headers=request_headers) as response:
                    content = await response.read()
                    response_body = json.loads(content.decode()) if content else {}
                    actual_status = response.status

            elif method == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    content = await response.read()
                    response_body = json.loads(content.decode()) if content else {}
                    actual_status = response.status

            response_time = (time.time() - start_time) * 1000

            # Validate graceful error handling
            graceful_handling, error_message, validation_passed = self._validate_error_response(
                actual_status, expected_status_code, response_body, test_name
            )

            return ErrorTestResult(
                test_name=test_name,
                endpoint=endpoint,
                method=method,
                expected_status_code=expected_status_code,
                actual_status_code=actual_status,
                response_time_ms=response_time,
                error_message=error_message,
                response_body=response_body,
                graceful_handling=graceful_handling,
                timestamp=datetime.utcnow(),
                validation_passed=validation_passed
            )

        except asyncio.TimeoutError:
            return ErrorTestResult(
                test_name=f"{test_name}_TIMEOUT",
                endpoint=endpoint,
                method=method,
                expected_status_code=expected_status_code,
                actual_status_code=0,
                response_time_ms=30000,
                error_message="Request timeout",
                response_body={"error": "Request timeout"},
                graceful_handling=False,
                timestamp=datetime.utcnow(),
                validation_passed=False
            )

        except Exception as e:
            return ErrorTestResult(
                test_name=f"{test_name}_EXCEPTION",
                endpoint=endpoint,
                method=method,
                expected_status_code=expected_status_code,
                actual_status_code=0,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
                response_body={"error": str(e)},
                graceful_handling=False,
                timestamp=datetime.utcnow(),
                validation_passed=False
            )

    def _validate_error_response(self, actual_status: int, expected_status: int,
                                response_body: Dict[str, Any], test_name: str) -> Tuple[bool, str, bool]:
        """Validate that error response is graceful and proper"""
        error_message = ""
        graceful_handling = True
        validation_passed = True

        # Check if status code matches expected
        if actual_status != expected_status:
            if actual_status == 500 and expected_status in [400, 401, 403, 404]:
                # 500 error for client-side errors is not graceful
                graceful_handling = False
                validation_passed = False
                error_message += f"Expected {expected_status} but got {actual_status} (server error). "
            elif actual_status != expected_status:
                # Different status code but not necessarily ungraceful
                error_message += f"Expected {expected_status} but got {actual_status}. "

        # Validate error response structure
        if not response_body:
            graceful_handling = False
            validation_passed = False
            error_message += "Empty response body. "
        else:
            # Check for proper error response fields
            required_fields = ["error", "message"]
            missing_fields = [field for field in required_fields if field not in response_body]

            if missing_fields:
                graceful_handling = False
                validation_passed = False
                error_message += f"Missing error fields: {missing_fields}. "

            # Check for helpful error message
            if "message" in response_body:
                message = response_body["message"]
                if not message or len(message.strip()) < 10:
                    graceful_handling = False
                    validation_passed = False
                    error_message += "Error message too short or empty. "

                # Check for generic/unhelpful messages
                generic_messages = ["error", "bad request", "internal server error", "failed"]
                if message.lower().strip() in generic_messages:
                    graceful_handling = False
                    validation_passed = False
                    error_message += f"Generic error message: '{message}'. "

            # Check for additional helpful fields
            helpful_fields = ["details", "error_code", "path", "timestamp"]
            has_helpful_fields = any(field in response_body for field in helpful_fields)
            if not has_helpful_fields and actual_status >= 400:
                error_message += "Missing additional context (details, error_code, etc.). "

        return graceful_handling, error_message.strip(), validation_passed

    async def test_invalid_endpoints(self) -> List[ErrorTestResult]:
        """Test requests to invalid endpoints"""
        tests = [
            ("nonexistent_endpoint", "/api/v1/nonexistent", "GET"),
            ("invalid_api_version", "/api/v2/users", "GET"),
            ("malformed_endpoint", "/api/v1/users/invalid/path", "GET"),
            ("endpoint_with_special_chars", "/api/v1/users/test<script>", "GET"),
            ("very_long_endpoint", "/api/v1/" + "a" * 1000, "GET")
        ]

        results = []
        for test_name, endpoint, method in tests:
            result = await self.test_error_scenario(
                f"invalid_endpoint_{test_name}",
                endpoint,
                method,
                expected_status_code=404
            )
            results.append(result)

        return results

    async def test_authentication_errors(self) -> List[ErrorTestResult]:
        """Test authentication and authorization errors"""
        tests = [
            # Missing authentication
            ("missing_auth", "/api/v1/users/me", "GET", None, {"Authorization": ""}, 401),

            # Invalid authentication
            ("invalid_token", "/api/v1/users/me", "GET", None, {"Authorization": "Bearer invalid_token"}, 401),

            # Malformed auth header
            ("malformed_auth", "/api/v1/users/me", "GET", None, {"Authorization": "InvalidFormat"}, 401),

            # Expired token simulation
            ("expired_token", "/api/v1/users/me", "GET", None, {"Authorization": "Bearer expired_token_12345"}, 401),

            # Unauthorized access to protected resources
            ("unauthorized_access", "/api/v1/admin/users", "GET", None, None, 403)
        ]

        results = []
        for test_name, endpoint, method, payload, headers, expected_status in tests:
            result = await self.test_error_scenario(
                f"auth_error_{test_name}",
                endpoint,
                method,
                payload,
                headers,
                expected_status
            )
            results.append(result)

        return results

    async def test_validation_errors(self) -> List[ErrorTestResult]:
        """Test input validation errors"""
        tests = [
            # Invalid JSON
            ("invalid_json", "/api/v1/auth/login", "POST", {"invalid": "json"}, None, 400),

            # Missing required fields
            ("missing_required_fields", "/api/v1/auth/login", "POST", {}, None, 400),

            # Invalid email format
            ("invalid_email", "/api/v1/auth/login", "POST", {"email": "invalid-email", "password": "test123"}, None, 400),

            # Password too short
            ("short_password", "/api/v1/auth/register", "POST", {
                "email": "test@example.com",
                "password": "123",
                "username": "testuser"
            }, None, 400),

            # Invalid data types
            ("invalid_data_types", "/api/v1/assessments", "POST", {
                "title": 123,  # Should be string
                "description": None  # Should be string
            }, None, 400),

            # Extra large payload
            ("large_payload", "/api/v1/assessments", "POST", {
                "title": "x" * 10000,  # Very long title
                "description": "y" * 50000  # Very long description
            }, None, 400),

            # Special characters in text fields
            ("special_characters", "/api/v1/users/profile", "PUT", {
                "username": "<script>alert('xss')</script>",
                "bio": "Test with unicode: ñáéíóú 🚀"
            }, None, 400)
        ]

        results = []
        for test_name, endpoint, method, payload, headers, expected_status in tests:
            result = await self.test_error_scenario(
                f"validation_error_{test_name}",
                endpoint,
                method,
                payload,
                headers,
                expected_status
            )
            results.append(result)

        return results

    async def test_business_logic_errors(self) -> List[ErrorTestResult]:
        """Test business logic and constraint errors"""
        tests = [
            # Duplicate resource
            ("duplicate_user", "/api/v1/auth/register", "POST", {
                "email": "duplicate@example.com",
                "username": "duplicateuser",
                "password": "ValidPass123!"
            }, None, 409),

            # Resource not found
            ("nonexistent_user", "/api/v1/users/99999", "GET", None, None, 404),

            # Invalid operation on resource
            ("invalid_assessment_update", "/api/v1/assessments/99999/complete", "POST", {}, None, 404),

            # Permission denied
            ("access_denied", "/api/v1/admin/users", "DELETE", None, None, 403),

            # Rate limiting (if implemented)
            ("rate_limit_test", "/api/v1/auth/login", "POST", {
                "email": "ratelimit@example.com",
                "password": "test123"
            }, None, 429)
        ]

        results = []
        for test_name, endpoint, method, payload, headers, expected_status in tests:
            result = await self.test_error_scenario(
                f"business_error_{test_name}",
                endpoint,
                method,
                payload,
                headers,
                expected_status
            )
            results.append(result)

        return results

    async def test_concurrent_access_errors(self) -> List[ErrorTestResult]:
        """Test concurrent access and race condition errors"""
        # Test multiple requests to the same resource simultaneously
        concurrent_requests = []
        user_id = 99998  # Non-existent user ID

        for i in range(10):
            request = self.test_error_scenario(
                f"concurrent_access_{i}",
                f"/api/v1/users/{user_id}",
                "GET",
                None,
                None,
                404
            )
            concurrent_requests.append(request)

        results = await asyncio.gather(*concurrent_requests, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results = [r for r in results if isinstance(r, ErrorTestResult)]
        return valid_results

    async def test_method_not_allowed(self) -> List[ErrorTestResult]:
        """Test HTTP method not allowed errors"""
        tests = [
            ("get_on_create", "/api/v1/auth/register", "GET"),
            ("post_on_health", "/api/v1/health", "POST"),
            ("delete_on_users", "/api/v1/users", "DELETE"),
            ("put_on_login", "/api/v1/auth/login", "PUT"),
            ("patch_on_assessments", "/api/v1/assessments", "PATCH")
        ]

        results = []
        for test_name, endpoint, method in tests:
            result = await self.test_error_scenario(
                f"method_not_allowed_{test_name}",
                endpoint,
                method,
                None,
                None,
                405
            )
            results.append(result)

        return results

    async def test_content_type_errors(self) -> List[ErrorTestResult]:
        """Test content-type related errors"""
        tests = [
            # Wrong content type
            ("wrong_content_type", "/api/v1/auth/login", "POST",
             {"email": "test@example.com", "password": "test123"},
             {"Content-Type": "text/plain"}, 400),

            # Missing content type for POST
            ("missing_content_type", "/api/v1/auth/login", "POST",
             {"email": "test@example.com", "password": "test123"},
             {"Content-Type": ""}, 400),

            # Invalid JSON format
            ("invalid_json_format", "/api/v1/auth/login", "POST",
             "invalid json string",
             {"Content-Type": "application/json"}, 400)
        ]

        results = []
        for test_name, endpoint, method, payload, headers, expected_status in tests:
            result = await self.test_error_scenario(
                f"content_type_error_{test_name}",
                endpoint,
                method,
                payload,
                headers,
                expected_status
            )
            results.append(result)

        return results

    async def generate_error_validation_report(self, all_results: List[ErrorTestResult]) -> Dict[str, Any]:
        """Generate comprehensive error validation report"""
        total_tests = len(all_results)
        passed_tests = len([r for r in all_results if r.validation_passed])
        graceful_handled = len([r for r in all_results if r.graceful_handling])

        # Group results by test type
        test_types = {}
        for result in all_results:
            test_type = result.test_name.split('_')[0]
            if test_type not in test_types:
                test_types[test_type] = []
            test_types[test_type].append(result)

        # Calculate metrics
        avg_response_time = statistics.mean([r.response_time_ms for r in all_results if r.response_time_ms > 0])

        # Identify common issues
        failed_tests = [r for r in all_results if not r.validation_passed]
        common_issues = {}
        for test in failed_tests:
            issue_type = test.test_name.split('_')[0]
            if issue_type not in common_issues:
                common_issues[issue_type] = []
            common_issues[issue_type].append(test.error_message)

        return {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "pass_rate_percentage": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "graceful_handling_rate_percentage": (graceful_handled / total_tests) * 100 if total_tests > 0 else 0,
                "average_response_time_ms": avg_response_time,
                "test_run_at": datetime.utcnow().isoformat()
            },
            "test_type_breakdown": {
                test_type: {
                    "total": len(results),
                    "passed": len([r for r in results if r.validation_passed]),
                    "failed": len([r for r in results if not r.validation_passed]),
                    "pass_rate": (len([r for r in results if r.validation_passed]) / len(results)) * 100
                }
                for test_type, results in test_types.items()
            },
            "common_issues": {
                issue_type: list(set(messages))[:3] for issue_type, messages in common_issues.items()
            },
            "failed_tests": [
                {
                    "test_name": test.test_name,
                    "endpoint": test.endpoint,
                    "expected_status": test.expected_status_code,
                    "actual_status": test.actual_status_code,
                    "error_message": test.error_message,
                    "response_body": test.response_body
                }
                for test in failed_tests
            ],
            "recommendations": self._generate_error_recommendations(passed_tests, total_tests, common_issues)
        }

    def _generate_error_recommendations(self, passed_tests: int, total_tests: int, common_issues: Dict[str, List[str]]) -> List[str]:
        """Generate recommendations for improving error handling"""
        recommendations = []

        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        if pass_rate < 80:
            recommendations.append("🚨 Low error handling pass rate. Implement comprehensive error responses for all endpoints.")

        if "generic" in str(common_issues).lower():
            recommendations.append("💬 Replace generic error messages with specific, actionable error descriptions.")

        if "missing" in str(common_issues).lower():
            recommendations.append("📋 Add consistent error response structure with 'error', 'message', and 'details' fields.")

        if "timeout" in str(common_issues).lower():
            recommendations.append("⏱️ Implement proper timeout handling and return appropriate timeout error responses.")

        if "empty" in str(common_issues).lower():
            recommendations.append("📄 Ensure all error responses include meaningful JSON content.")

        if "internal_server" in str(common_issues).lower():
            recommendations.append("🔧 Convert internal server errors to appropriate client error codes where possible.")

        if pass_rate >= 90:
            recommendations.append("✅ Excellent error handling! Most scenarios are handled gracefully.")

        if pass_rate >= 80 and pass_rate < 90:
            recommendations.append("👍 Good error handling. Address the remaining failed tests for full compliance.")

        return recommendations

    async def run_all_error_tests(self) -> Dict[str, Any]:
        """Run all error handling validation tests"""
        logger.info("Starting comprehensive API error handling validation")

        # Get auth token for protected endpoints
        await self.get_auth_token()

        # Run all test suites
        test_suites = [
            ("Invalid Endpoints", self.test_invalid_endpoints),
            ("Authentication Errors", self.test_authentication_errors),
            ("Validation Errors", self.test_validation_errors),
            ("Business Logic Errors", self.test_business_logic_errors),
            ("Method Not Allowed", self.test_method_not_allowed),
            ("Content Type Errors", self.test_content_type_errors),
            ("Concurrent Access", self.test_concurrent_access_errors)
        ]

        all_results = []
        suite_results = {}

        for suite_name, test_func in test_suites:
            logger.info(f"Running {suite_name} tests...")
            try:
                results = await test_func()
                all_results.extend(results)
                suite_results[suite_name] = results
                logger.info(f"✅ {suite_name}: {len(results)} tests completed")
            except Exception as e:
                logger.error(f"❌ {suite_name} failed: {e}")
                logger.error(traceback.format_exc())

        # Generate comprehensive report
        report = await self.generate_error_validation_report(all_results)
        report["test_suite_details"] = suite_results

        return report

async def main():
    """Main error validation execution"""
    print("🔍 Starting API Error Handling Validation Suite")
    print("=" * 60)

    BASE_URL = "http://localhost:8000"

    # Check if server is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/v1/health") as response:
                if response.status in [200, 401]:
                    print("✅ API server is running")
                else:
                    print(f"⚠️  API server returned status {response.status}")
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("Please ensure the API server is running on http://localhost:8000")
        sys.exit(1)

    # Create and run error validator
    async with APIErrorValidator(BASE_URL) as validator:
        print(f"\n🎯 Validating error handling against: {BASE_URL}")
        print("⏱️  Starting comprehensive error validation...\n")

        start_time = time.time()

        try:
            report = await validator.run_all_error_tests()
            test_duration = time.time() - start_time

            print(f"✅ Error validation completed in {test_duration:.1f}s")
            print("=" * 60)

            # Display results
            summary = report["test_summary"]
            print(f"\n📊 VALIDATION SUMMARY:")
            print(f"   • Total Tests: {summary['total_tests']}")
            print(f"   • Passed: {summary['passed_tests']} ({summary['pass_rate_percentage']:.1f}%)")
            print(f"   • Failed: {summary['failed_tests']}")
            print(f"   • Graceful Handling: {summary['graceful_handling_rate_percentage']:.1f}%")
            print(f"   • Avg Response Time: {summary['average_response_time_ms']:.0f}ms")

            print(f"\n📋 TEST TYPE BREAKDOWN:")
            for test_type, stats in report["test_type_breakdown"].items():
                status = "✅" if stats["pass_rate"] >= 80 else "⚠️" if stats["pass_rate"] >= 60 else "❌"
                print(f"   {status} {test_type.title()}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")

            if report["failed_tests"]:
                print(f"\n❌ FAILED TESTS ({len(report['failed_tests'])}):")
                for i, test in enumerate(report["failed_tests"][:5], 1):  # Show first 5
                    print(f"   {i}. {test['test_name']}: {test['error_message']}")

                if len(report["failed_tests"]) > 5:
                    print(f"   ... and {len(report['failed_tests']) - 5} more")

            print(f"\n💡 RECOMMENDATIONS:")
            for i, recommendation in enumerate(report["recommendations"], 1):
                print(f"   {i}. {recommendation}")

            # Save detailed report
            report_file = f"error_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n📄 Detailed report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Error validation failed: {e}")
            logger.error(traceback.format_exc())
            print(f"\n❌ Error validation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
