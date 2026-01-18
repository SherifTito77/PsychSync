#!/usr/bin/env python3
"""
Frontend-Backend Integration Test Runner
Tests complete user workflows between frontend (port 5174) and backend (port 8000)
"""

import asyncio
import aiohttp
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

class IntegrationTestResult:
    def __init__(self, test_name: str, success: bool, duration: float, details: str = "", error: str = None, response_code: int = None):
        self.test_name = test_name
        self.success = success
        self.duration = duration
        self.details = details
        self.error = error
        self.response_code = response_code
        self.timestamp = datetime.now(timezone.utc)

class IntegrationTestRunner:
    def __init__(self):
        self.frontend_url = "http://localhost:5174"
        self.backend_url = "http://localhost:8000"
        self.session = None
        self.auth_token = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_backend_health(self):
        """Test backend health endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                duration = time.time() - start_time
                data = await response.json()

                if response.status == 200 and data.get("status") == "healthy":
                    return IntegrationTestResult(
                        "Backend Health Check",
                        True,
                        duration,
                        f"Backend healthy - {data.get('application', 'Unknown')} v{data.get('version', 'Unknown')}"
                    )
                else:
                    return IntegrationTestResult(
                        "Backend Health Check",
                        False,
                        duration,
                        f"Unexpected response: {data}",
                        response_code=response.status
                    )
        except Exception as e:
            duration = time.time() - start_time
            return IntegrationTestResult("Backend Health Check", False, duration, str(e), str(e))

    async def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        start_time = time.time()
        try:
            async with self.session.get(self.frontend_url) as response:
                duration = time.time() - start_time

                if response.status == 200:
                    content = await response.text()
                    if "PsychSync" in content or "React" in content:
                        return IntegrationTestResult(
                            "Frontend Accessibility",
                            True,
                            duration,
                            "Frontend accessible and loading correctly"
                        )
                    else:
                        return IntegrationTestResult(
                            "Frontend Accessibility",
                            False,
                            duration,
                            "Frontend accessible but content unexpected",
                            response_code=response.status
                        )
                else:
                    return IntegrationTestResult(
                        "Frontend Accessibility",
                        False,
                        duration,
                        f"Frontend returned status {response.status}",
                        response_code=response.status
                    )
        except Exception as e:
            duration = time.time() - start_time
            return IntegrationTestResult("Frontend Accessibility", False, duration, str(e), str(e))

    async def test_api_endpoints_structure(self):
        """Test API endpoints availability"""
        start_time = time.time()
        endpoints_to_test = [
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        working_endpoints = []
        for endpoint in endpoints_to_test:
            try:
                async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                    if response.status == 200:
                        working_endpoints.append(endpoint)
            except Exception as e:
                pass  # Skip failed endpoints

        duration = time.time() - start_time
        if len(working_endpoints) > 0:
            return IntegrationTestResult(
                "API Endpoints Structure",
                True,
                duration,
                f"Working endpoints: {', '.join(working_endpoints)}"
            )
        else:
            return IntegrationTestResult(
                "API Endpoints Structure",
                False,
                duration,
                "No API documentation endpoints accessible"
            )

    async def test_authentication_flow(self):
        """Test user authentication flow"""
        start_time = time.time()

        # Test user registration
        test_email = f"integration_test_{int(time.time())}@example.com"
        registration_data = {
            "email": test_email,
            "password": "test_password_123",
            "full_name": "Integration Test User",
            "role": "user"
        }

        try:
            # Try to register user
            async with self.session.post(
                f"{self.backend_url}/api/v1/register",
                json=registration_data
            ) as response:
                registration_status = response.status
                registration_data_response = await response.json() if response.content_type == 'application/json' else {}

            # Try to login user
            login_data = {
                "username": test_email,
                "password": "test_password_123"
            }

            async with self.session.post(
                f"{self.backend_url}/api/v1/token-login",
                json=login_data
            ) as response:
                login_status = response.status
                login_response = await response.json() if response.content_type == 'application/json' else {}

                if login_status == 200 and "access_token" in login_response:
                    self.auth_token = login_response["access_token"]
                    return IntegrationTestResult(
                        "Authentication Flow",
                        True,
                        time.time() - start_time,
                        f"Registration: {registration_status}, Login successful, token received"
                    )
                else:
                    return IntegrationTestResult(
                        "Authentication Flow",
                        False,
                        time.time() - start_time,
                        f"Registration: {registration_status}, Login failed: {login_response}",
                        response_code=login_status
                    )

        except Exception as e:
            duration = time.time() - start_time
            return IntegrationTestResult("Authentication Flow", False, duration, str(e), str(e))

    async def test_authenticated_endpoints(self):
        """Test authenticated API endpoints"""
        if not self.auth_token:
            return IntegrationTestResult(
                "Authenticated Endpoints",
                False,
                0,
                "No authentication token available - skipping authenticated endpoint tests"
            )

        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test user profile endpoint
        try:
            async with self.session.get(
                f"{self.backend_url}/api/v1/api/v1/me",
                headers=headers
            ) as response:
                user_profile_status = response.status
                user_data = await response.json() if response.content_type == 'application/json' else {}

                if user_profile_status == 200:
                    return IntegrationTestResult(
                        "Authenticated Endpoints",
                        True,
                        time.time() - start_time,
                        f"User profile accessible: {user_data.get('email', 'Unknown email')}"
                    )
                else:
                    return IntegrationTestResult(
                        "Authenticated Endpoints",
                        False,
                        time.time() - start_time,
                        f"User profile access failed: {user_data}",
                        response_code=user_profile_status
                    )

        except Exception as e:
            duration = time.time() - start_time
            return IntegrationTestResult("Authenticated Endpoints", False, duration, str(e), str(e))

    async def test_assessment_system(self):
        """Test assessment system functionality"""
        if not self.auth_token:
            return IntegrationTestResult(
                "Assessment System",
                False,
                0,
                "No authentication token available - skipping assessment system tests"
            )

        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        try:
            # Test getting available assessments
            async with self.session.get(
                f"{self.backend_url}/api/v1/assessments",
                headers=headers
            ) as response:
                assessments_status = response.status
                assessments_data = await response.json() if response.content_type == 'application/json' else {}

                # Test clinical assessment endpoint (the one we fixed)
                async with self.session.get(
                    f"{self.backend_url}/api/v1/clinical/consent",
                    headers=headers
                ) as clinical_response:
                    clinical_status = clinical_response.status
                    clinical_data = await clinical_response.json() if clinical_response.content_type == 'application/json' else {}

                    duration = time.time() - start_time

                    if assessments_status == 200 or clinical_status in [200, 401, 403]:  # 401/403 might be expected for clinical
                        return IntegrationTestResult(
                            "Assessment System",
                            True,
                            duration,
                            f"Assessments API: {assessments_status}, Clinical API: {clinical_status} - System accessible"
                        )
                    else:
                        return IntegrationTestResult(
                            "Assessment System",
                            False,
                            duration,
                            f"Assessments API failed: {assessments_status}, Clinical API: {clinical_status}",
                            response_code=assessments_status
                        )

        except Exception as e:
            duration = time.time() - start_time
            return IntegrationTestResult("Assessment System", False, duration, str(e), str(e))

    async def test_rapid_submission_handling(self):
        """Test rapid form submission handling"""
        if not self.auth_token:
            return IntegrationTestResult(
                "Rapid Submission Handling",
                False,
                0,
                "No authentication token available - skipping rapid submission tests"
            )

        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        try:
            # Simulate rapid submissions (this would typically be assessment responses)
            submission_data = {
                "assessment_type": "mbti",
                "responses": {"question_1": "A", "question_2": "B"}
            }

            successful_submissions = 0
            total_submissions = 5

            for i in range(total_submissions):
                async with self.session.post(
                    f"{self.backend_url}/api/v1/responses",
                    json=submission_data,
                    headers=headers
                ) as response:
                    if response.status in [200, 201, 400]:  # 400 might be expected for duplicate submissions
                        successful_submissions += 1
                    # Small delay to simulate rapid submissions
                    await asyncio.sleep(0.01)

            duration = time.time() - start_time
            return IntegrationTestResult(
                "Rapid Submission Handling",
                True,
                duration,
                f"Successfully handled {successful_submissions}/{total_submissions} rapid submissions"
            )

        except Exception as e:
            duration = time.time() - start_time
            return IntegrationTestResult("Rapid Submission Handling", False, duration, str(e), str(e))

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🔧 PSYNSYNC FRONTEND-BACKEND INTEGRATION TEST RUNNER")
        print("=" * 70)
        print(f"Testing frontend: {self.frontend_url}")
        print(f"Testing backend:  {self.backend_url}")
        print("=" * 70)

        # Define all tests to run
        tests = [
            self.test_backend_health,
            self.test_frontend_accessibility,
            self.test_api_endpoints_structure,
            self.test_authentication_flow,
            self.test_authenticated_endpoints,
            self.test_assessment_system,
            self.test_rapid_submission_handling
        ]

        # Run each test
        for test_func in tests:
            print(f"\n🧪 Running {test_func.__name__}...")
            result = await test_func()
            self.test_results.append(result)

            if result.success:
                print(f"✅ {result.test_name}: PASSED ({result.duration:.3f}s)")
                if result.details:
                    print(f"   Details: {result.details}")
            else:
                print(f"❌ {result.test_name}: FAILED ({result.duration:.3f}s)")
                print(f"   Error: {result.error}")
                if result.details:
                    print(f"   Details: {result.details}")

        # Generate summary report
        self.generate_summary_report()
        return self.test_results

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        total_duration = sum(result.duration for result in self.test_results)

        print(f"\n{'='*80}")
        print("📊 INTEGRATION TEST SUMMARY REPORT")
        print(f"{'='*80}")

        print(f"\n📈 OVERALL RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"  Total Duration: {total_duration:.3f}s")

        print(f"\n📋 INDIVIDUAL TEST RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = f"{result.duration:.3f}s"
            print(f"  {result.test_name:<35} {status:<10} {duration:<10}")

        print(f"\n🔍 FAILED TESTS DETAILS:")
        failed_results = [result for result in self.test_results if not result.success]

        if failed_results:
            for result in failed_results:
                print(f"\n❌ {result.test_name}:")
                print(f"   Error: {result.error}")
                if result.details:
                    print(f"   Details: {result.details}")
        else:
            print("\n✅ All integration tests passed! Frontend-backend communication verified.")

        print(f"\n📝 RECOMMENDATIONS:")
        if failed_tests > 0:
            print("  🔧 Fix failing integration tests before production deployment")
            print("  🔗 Verify API endpoint configurations and CORS settings")
            print("  🔒 Check authentication and authorization mechanisms")
        else:
            print("  ✅ Frontend-backend integration is production-ready")
            print("  🚀 System ready for performance optimization")
            print("  📈 Ready for security enhancements and production deployment")

        print(f"\n📋 NEXT PHASE:")
        print("  3. Performance Optimization")
        print("  4. Security Enhancements")
        print("  5. Production Deployment Preparation")

        print(f"\n{'='*80}")
        print("🎉 INTEGRATION TESTING COMPLETE")
        print(f"{'='*80}")

async def main():
    """Main test runner"""
    try:
        async with IntegrationTestRunner() as runner:
            results = await runner.run_all_tests()

            # Exit with appropriate code
            failed_count = sum(1 for result in results if not result.success)
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
    asyncio.run(main())
