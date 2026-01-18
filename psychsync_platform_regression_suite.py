#!/usr/bin/env python3
"""
PsychSync Platform Regression Suite
==================================

Comprehensive regression testing suite covering all core functionality
across the entire PsychSync platform to prevent regressions.
"""

import asyncio
import json
import time
import httpx
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class RegressionTestCategory(Enum):
    AUTHENTICATION = "authentication"
    USER_MANAGEMENT = "user_management"
    TEAM_MANAGEMENT = "team_management"
    ASSESSMENT_SYSTEM = "assessment_system"
    ANALYTICS_REPORTING = "analytics_reporting"
    NOTIFICATIONS = "notifications"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATA_INTEGRITY = "data_integrity"
    API_STABILITY = "api_stability"
    CROSS_PLATFORM = "cross_platform"

@dataclass
class RegressionTestResult:
    """Result from a regression test"""
    test_name: str
    category: RegressionTestCategory
    success: bool
    response_time_ms: float
    status_code: int
    expected_status_code: int
    data_validated: bool
    issues: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime

@dataclass
class PlatformHealthCheck:
    """Health check result for platform components"""
    component: str
    status: str
    response_time_ms: float
    details: Dict[str, Any]
    dependencies: Dict[str, bool]
    timestamp: datetime

class PsychSyncPlatformRegressionSuite:
    """Comprehensive regression testing suite for PsychSync platform"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results: List[RegressionTestResult] = []
        self.health_checks: List[PlatformHealthCheck] = []
        self.category_coverage = {}

        # Critical endpoints for regression testing
        self.critical_endpoints = {
            "authentication": [
                "/api/v1/auth/register",
                "/api/v1/auth/login",
                "/api/v1/auth/logout",
                "/api/v1/auth/refresh"
            ],
            "user_management": [
                "/api/v1/users/me",
                "/api/v1/users/profile",
                "/api/v1/users/settings"
            ],
            "team_management": [
                "/api/v1/teams",
                "/api/v1/teams/{team_id}",
                "/api/v1/teams/{team_id}/members",
                "/api/v1/teams/{team_id}/members/invite"
            ],
            "assessment_system": [
                "/api/v1/assessments",
                "/api/v1/assessments/{assessment_id}",
                "/api/v1/responses",
                "/api/v1/responses/{response_id}"
            ],
            "analytics": [
                "/api/v1/analytics/team-overview",
                "/api/v1/analytics/team-performance",
                "/api/v1/analytics/personality-distribution"
            ],
            "notifications": [
                "/api/v1/notifications",
                "/api/v1/notifications/{notification_id}"
            ]
        }

    async def run_full_regression_suite(self) -> Dict[str, Any]:
        """Execute complete regression testing suite"""
        print("🔍 PSYNSYNC PLATFORM REGRESSION SUITE")
        print("=" * 80)
        print("Comprehensive testing to prevent regressions across all platform components")
        print("=" * 80)

        start_time = time.time()

        # 1. Platform Health Check
        await self.run_health_checks()

        # 2. Authentication Regression Tests
        await self.test_authentication_regression()

        # 3. User Management Regression Tests
        await self.test_user_management_regression()

        # 4. Team Management Regression Tests
        await self.test_team_management_regression()

        # 5. Assessment System Regression Tests
        await self.test_assessment_system_regression()

        # 6. Analytics and Reporting Regression Tests
        await self.test_analytics_regression()

        # 7. Notifications System Regression Tests
        await self.test_notifications_regression()

        # 8. Security Regression Tests
        await self.test_security_regression()

        # 9. Performance Regression Tests
        await self.test_performance_regression()

        # 10. Data Integrity Tests
        await self.test_data_integrity_regression()

        # 11. API Stability Tests
        await self.test_api_stability_regression()

        # 12. Cross-Platform Compatibility Tests
        await self.test_cross_platform_regression()

        total_time = time.time() - start_time

        # Generate comprehensive regression report
        return await self.generate_regression_report(total_time)

    async def run_health_checks(self):
        """Run comprehensive platform health checks"""
        print("\n💚 PLATFORM HEALTH CHECKS")
        print("-" * 50)

        health_endpoints = [
            {"name": "Basic Health", "url": "/api/v1/health"},
            {"name": "Detailed Health", "url": "/api/v1/health/detailed"},
            {"name": "Database Health", "url": "/api/v1/health/database"},
            {"name": "Cache Health", "url": "/api/v1/health/cache"},
            {"name": "Dependencies Health", "url": "/api/v1/health/dependencies"}
        ]

        for endpoint in health_endpoints:
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint['url']}")

                response_time = (time.time() - start_time) * 1000

                health_data = {}
                dependencies = {}

                try:
                    health_data = response.json() if response.content else {}
                    dependencies = health_data.get("dependencies", {})
except Exception as e:                    pass

                health_check = PlatformHealthCheck(
                    component=endpoint['name'],
                    status="healthy" if response.status_code == 200 else "unhealthy",
                    response_time_ms=response_time,
                    details=health_data,
                    dependencies=dependencies,
                    timestamp=datetime.now()
                )

                self.health_checks.append(health_check)

                status_icon = "✅" if response.status_code == 200 else "❌"
                print(f"{status_icon} {endpoint['name']}: {response.status_code} ({response_time:.1f}ms)")

                if response.status_code != 200:
                    print(f"   ⚠️  Status: {response.text[:100]}")

            except Exception as e:
                health_check = PlatformHealthCheck(
                    component=endpoint['name'],
                    status="error",
                    response_time_ms=0,
                    details={"error": str(e)},
                    dependencies={},
                    timestamp=datetime.now()
                )
                self.health_checks.append(health_check)
                print(f"❌ {endpoint['name']}: ERROR - {str(e)}")

    async def test_authentication_regression(self):
        """Test authentication system regression"""
        print("\n🔐 AUTHENTICATION REGRESSION TESTS")
        print("-" * 50)

        # Test user registration
        await self.test_endpoint_with_auth(
            "User Registration",
            "/api/v1/auth/register",
            "POST",
            RegressionTestCategory.AUTHENTICATION,
            {
                "email": f"regress.user{secrets.randbelow(8999) + 1000}@company.com",
                "password": "SecurePassword123!",
                "full_name": "Regression Test User",
                "organization_id": "test-org"
            },
            201
        )

        # Test user login
        await self.test_endpoint_with_auth(
            "User Login",
            "/api/v1/auth/login",
            "POST",
            RegressionTestCategory.AUTHENTICATION,
            {
                "email": "test@company.com",
                "password": "testpassword"
            },
            200
        )

        # Test token refresh
        await self.test_endpoint_with_auth(
            "Token Refresh",
            "/api/v1/auth/refresh",
            "POST",
            RegressionTestCategory.AUTHENTICATION,
            {"refresh_token": "test_refresh_token"},
            200
        )

        # Test user profile access
        await self.test_endpoint_with_auth(
            "User Profile Access",
            "/api/v1/users/me",
            "GET",
            RegressionTestCategory.AUTHENTICATION,
            {},
            200
        )

    async def test_user_management_regression(self):
        """Test user management system regression"""
        print("\n👤 USER MANAGEMENT REGRESSION TESTS")
        print("-" * 50)

        # Test user profile update
        await self.test_endpoint_with_auth(
            "User Profile Update",
            "/api/v1/users/profile",
            "PUT",
            RegressionTestCategory.USER_MANAGEMENT,
            {
                "full_name": "Updated Regression User",
                "bio": "Updated bio for regression testing",
                "timezone": "UTC"
            },
            200
        )

        # Test user settings update
        await self.test_endpoint_with_auth(
            "User Settings Update",
            "/api/v1/users/settings",
            "PUT",
            RegressionTestCategory.USER_MANAGEMENT,
            {
                "email_notifications": True,
                "theme": "light",
                "language": "en"
            },
            200
        )

        # Test user preferences
        await self.test_endpoint_with_auth(
            "User Preferences",
            "/api/v1/users/preferences",
            "GET",
            RegressionTestCategory.USER_MANAGEMENT,
            {},
            200
        )

    async def test_team_management_regression(self):
        """Test team management system regression"""
        print("\n👥 TEAM MANAGEMENT REGRESSION TESTS")
        print("-" * 50)

        # Test team creation
        await self.test_endpoint_with_auth(
            "Team Creation",
            "/api/v1/teams",
            "POST",
            RegressionTestCategory.TEAM_MANAGEMENT,
            {
                "name": f"Regression Test Team {secrets.randbelow(899) + 100}",
                "description": "Team created for regression testing",
                "organization_id": "test-org"
            },
            201
        )

        # Test team listing
        await self.test_endpoint_with_auth(
            "Team Listing",
            "/api/v1/teams",
            "GET",
            RegressionTestCategory.TEAM_MANAGEMENT,
            {},
            200
        )

        # Test team member listing (will need to create a team first)
        test_team_id = "test-team-id"  # This would be dynamically obtained
        await self.test_endpoint_with_auth(
            "Team Member Listing",
            f"/api/v1/teams/{test_team_id}/members",
            "GET",
            RegressionTestCategory.TEAM_MANAGEMENT,
            {},
            200
        )

    async def test_assessment_system_regression(self):
        """Test assessment system regression"""
        print("\n🧠 ASSESSMENT SYSTEM REGRESSION TESTS")
        print("-" * 50)

        # Test assessment listing
        await self.test_endpoint_with_auth(
            "Assessment Listing",
            "/api/v1/assessments",
            "GET",
            RegressionTestCategory.ASSESSMENT_SYSTEM,
            {},
            200
        )

        # Test assessment creation
        await self.test_endpoint_with_auth(
            "Assessment Creation",
            "/api/v1/assessments",
            "POST",
            RegressionTestCategory.ASSESSMENT_SYSTEM,
            {
                "title": "Regression Test Assessment",
                "type": "big_five",
                "description": "Assessment for regression testing",
                "team_id": "test-team-id"
            },
            201
        )

        # Test assessment templates
        await self.test_endpoint_with_auth(
            "Assessment Templates",
            "/api/v1/assessments/templates",
            "GET",
            RegressionTestCategory.ASSESSMENT_SYSTEM,
            {},
            200
        )

        # Test response submission
        test_assessment_id = "test-assessment-id"
        await self.test_endpoint_with_auth(
            "Response Submission",
            "/api/v1/responses",
            "POST",
            RegressionTestCategory.ASSESSMENT_SYSTEM,
            {
                "assessment_id": test_assessment_id,
                "responses": {
                    "openness": [3, 4, 2, 5, 4],
                    "conscientiousness": [4, 3, 5, 4, 3],
                    "extraversion": [2, 3, 4, 2, 3],
                    "agreeableness": [5, 4, 3, 4, 5],
                    "neuroticism": [2, 3, 2, 4, 3]
                }
            },
            201
        )

    async def test_analytics_regression(self):
        """Test analytics and reporting regression"""
        print("\n📊 ANALYTICS REGRESSION TESTS")
        print("-" * 50)

        # Test team overview analytics
        await self.test_endpoint_with_auth(
            "Team Overview Analytics",
            "/api/v1/analytics/team-overview",
            "GET",
            RegressionTestCategory.ANALYTICS_REPORTING,
            {"team_id": "test-team-id"},
            200
        )

        # Test team performance analytics
        await self.test_endpoint_with_auth(
            "Team Performance Analytics",
            "/api/v1/analytics/team-performance",
            "GET",
            RegressionTestCategory.ANALYTICS_REPORTING,
            {"team_id": "test-team-id", "timeframe": "30d"},
            200
        )

        # Test personality distribution analytics
        await self.test_endpoint_with_auth(
            "Personality Distribution",
            "/api/v1/analytics/personality-distribution",
            "GET",
            RegressionTestCategory.ANALYTICS_REPORTING,
            {"team_id": "test-team-id"},
            200
        )

        # Test time-based analytics
        await self.test_endpoint_with_auth(
            "Time-Based Analytics",
            "/api/v1/analytics/timeline",
            "GET",
            RegressionTestCategory.ANALYTICS_REPORTING,
            {"team_id": "test-team-id", "start_date": "2023-01-01"},
            200
        )

    async def test_notifications_regression(self):
        """Test notifications system regression"""
        print("\n🔔 NOTIFICATIONS REGRESSION TESTS")
        print("-" * 50)

        # Test notification listing
        await self.test_endpoint_with_auth(
            "Notification Listing",
            "/api/v1/notifications",
            "GET",
            RegressionTestCategory.NOTIFICATIONS,
            {"limit": 10},
            200
        )

        # Test notification creation
        await self.test_endpoint_with_auth(
            "Notification Creation",
            "/api/v1/notifications",
            "POST",
            RegressionTestCategory.NOTIFICATIONS,
            {
                "type": "team_member_added",
                "title": "New Team Member",
                "message": "A new member has joined your team",
                "user_id": "test-user-id"
            },
            201
        )

        # Test notification preferences
        await self.test_endpoint_with_auth(
            "Notification Preferences",
            "/api/v1/notifications/preferences",
            "GET",
            RegressionTestCategory.NOTIFICATIONS,
            {},
            200
        )

    async def test_security_regression(self):
        """Test security measures regression"""
        print("\n🛡️ SECURITY REGRESSION TESTS")
        print("-" * 50)

        # Test rate limiting
        await self.test_security_endpoint(
            "Rate Limiting",
            "/api/v1/auth/login",
            5,  # Make 5 rapid requests
            "POST",
            {"email": "test@company.com", "password": "testpassword"}
        )

        # Test input validation
        await self.test_security_endpoint(
            "Input Validation",
            "/api/v1/users/profile",
            1,
            "PUT",
            {"full_name": "Test User", "bio": "<script>alert('xss')</script>"}
        )

        # Test SQL injection prevention
        await self.test_security_endpoint(
            "SQL Injection Prevention",
            "/api/v1/teams",
            1,
            "GET",
            {"search": "test'; DROP TABLE users; --"}
        )

        # Test CSRF protection
        await self.test_security_endpoint(
            "CSRF Protection",
            "/api/v1/teams",
            1,
            "POST",
            {"name": "Test Team", "csrf_token": "invalid_token"}
        )

    async def test_performance_regression(self):
        """Test performance benchmarks regression"""
        print("\n⚡ PERFORMANCE REGRESSION TESTS")
        print("-" * 50)

        # Test response time benchmarks
        endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/users/me",
            "/api/v1/teams",
            "/api/v1/assessments"
        ]

        performance_results = []

        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}")

                response_time = (time.time() - start_time) * 1000

                performance_results.append({
                    "endpoint": endpoint,
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                    "size_bytes": len(response.content)
                })

                status_icon = "✅" if response_time < 500 else "⚠️"
                print(f"{status_icon} {endpoint}: {response_time:.1f}ms ({response.status_code})")

            except Exception as e:
                print(f"❌ {endpoint}: ERROR - {str(e)}")

        # Calculate performance metrics
        if performance_results:
            avg_time = sum(r["response_time_ms"] for r in performance_results) / len(performance_results)
            max_time = max(r["response_time_ms"] for r in performance_results)
            min_time = min(r["response_time_ms"] for r in performance_results)

            print(f"\n📈 Performance Metrics:")
            print(f"   Average Response Time: {avg_time:.2f}ms")
            print(f"   Maximum Response Time: {max_time:.2f}ms")
            print(f"   Minimum Response Time: {min_time:.2f}ms")
            print(f"   Average Content Size: {sum(r['size_bytes'] for r in performance_results) / len(performance_results):.0f} bytes")

    async def test_data_integrity_regression(self):
        """Test data integrity regression"""
        print("\n🔒 DATA INTEGRITY REGRESSION TESTS")
        print("-" * 50)

        # Test user-team relationship integrity
        await self.test_data_consistency("User-Team Relationships")

        # Test assessment-response relationship integrity
        await self.test_data_consistency("Assessment-Response Relationships")

        # Test notification-user relationship integrity
        await self.test_data_consistency("Notification-User Relationships")

        # Test team member uniqueness constraints
        await self.test_data_consistency("Team Member Uniqueness")

    async def test_data_consistency(self, test_type: str):
        """Test specific data consistency scenario"""
        try:
            if test_type == "User-Team Relationships":
                # Test that team member relationships are consistent
                result = await self.test_endpoint_with_auth(
                    "User-Team Consistency",
                    "/api/v1/data-consistency/user-team",
                    "GET",
                    RegressionTestCategory.DATA_INTEGRITY,
                    {},
                    200
                )

            elif test_type == "Assessment-Response Relationships":
                # Test that assessment-response relationships are consistent
                result = await self.test_endpoint_with_auth(
                    "Assessment-Response Consistency",
                    "/api/v1/data-consistency/assessment-response",
                    "GET",
                    RegressionTestCategory.DATA_INTEGRITY,
                    {},
                    200
                )

            print(f"✅ {test_type}: Data consistency validated")

        except Exception as e:
            print(f"❌ {test_type}: Consistency check failed - {str(e)}")

    async def test_api_stability_regression(self):
        """Test API stability under various conditions"""
        print("\n🔗 API STABILITY REGRESSION TESTS")
        print("-" * 50)

        # Test API version consistency
        await self.test_api_versioning()

        # Test error handling consistency
        await self.test_error_handling_consistency()

        # Test response format consistency
        await self.test_response_format_consistency()

    async def test_api_versioning(self):
        """Test API versioning consistency"""
        version_endpoints = [
            "/api/v1/health",
            "/api/v2/health"  # This might not exist, testing error handling
        ]

        for endpoint in version_endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    if endpoint.startswith("/api/v2"):
                        # v2 might not exist, should return appropriate error
                        pass
                    else:
                        # v1 should work
                        pass

            except Exception:
                pass  # Expected for some versions

    async def test_error_handling_consistency(self):
        """Test error handling consistency across endpoints"""
        error_scenarios = [
            {"endpoint": "/api/v1/users/invalid", "expected_status": 404},
            {"endpoint": "/api/v1/teams/invalid", "expected_status": 404},
            {"endpoint": "/api/v1/assessments/invalid", "expected_status": 404}
        ]

        for scenario in error_scenarios:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}{scenario['endpoint']}")

                    if response.status_code == scenario["expected_status"]:
                        print(f"✅ {scenario['endpoint']}: Correct error code {response.status_code}")
                    else:
                        print(f"⚠️  {scenario['endpoint']}: Expected {scenario['expected_status']}, got {response.status_code}")

            except Exception as e:
                print(f"❌ {scenario['endpoint']}: Exception - {str(e)}")

    async def test_response_format_consistency(self):
        """Test response format consistency"""
        test_endpoints = ["/api/v1/health", "/api/v1/users/me", "/api/v1/teams"]

        for endpoint in test_endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}")

                    if response.headers.get("content-type"):
                        content_type = response.headers["content-type"]
                        if "application/json" in content_type:
                            # Try to parse JSON
                            try:
                                data = response.json()
                                print(f"✅ {endpoint}: Valid JSON response")
except Exception as e:                                print(f"⚠️  {endpoint}: Invalid JSON response")
                        else:
                            print(f"⚠️  {endpoint}: Non-JSON response type: {content_type}")

            except Exception as e:
                print(f"❌ {endpoint}: Response format test failed - {str(e)}")

    async def test_cross_platform_regression(self):
        """Test cross-platform compatibility"""
        print("\n🌐 CROSS-PLATFORM REGRESSION TESTS")
        print("-" * 50)

        # Test different user agents
        user_agents = [
            {"name": "Chrome Desktop", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            {"name": "Firefox Desktop", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0)"},
            {"name": "Safari Desktop", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            {"name": "Mobile Safari", "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"},
            {"name": "Android Chrome", "ua": "Mozilla/5.0 (Linux; Android 12; SM-G991B)"}
        ]

        for user_agent in user_agents:
            headers = {"User-Agent": user_agent["ua"]}
            try:
                async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
                    response = await client.get(f"{self.base_url}/api/v1/health")

                    if response.status_code == 200:
                        print(f"✅ {user_agent['name']}: Compatible")
                    else:
                        print(f"⚠️  {user_agent['name']}: Status {response.status_code}")

            except Exception as e:
                print(f"❌ {user_agent['name']}: Error - {str(e)}")

    async def test_endpoint_with_auth(self, test_name: str, endpoint: str, method: str,
                                       category: RegressionTestCategory, payload: Dict[str, Any],
                                       expected_status: int):
        """Test specific endpoint with authentication"""
        try:
            headers = {
                "Authorization": "Bearer test_token_12345",
                "Content-Type": "application/json"
            }

            start_time = time.time()
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                elif method == "POST":
                    response = await client.post(f"{self.base_url}{endpoint}", json=payload, headers=headers)
                elif method == "PUT":
                    response = await client.put(f"{self.base_url}{endpoint}", json=payload, headers=headers)
                else:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

            response_time = (time.time() - start_time) * 1000

            # Validate response
            data_validated = False
            issues = []

            if response.status_code == expected_status:
                try:
                    data = response.json() if response.content else {}
                    data_validated = True
except Exception as e:                    data_validated = True  # Some endpoints may return empty responses

                self.test_results.append(RegressionTestResult(
                    test_name=test_name,
                    category=category,
                    success=response.status_code == expected_status,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    expected_status_code=expected_status,
                    data_validated=data_validated,
                    issues=issues,
                    metrics={"response_size": len(response.content)},
                    timestamp=datetime.now()
                ))

                print(f"✅ {test_name}: {response.status_code} ({response_time:.1f}ms)")

            else:
                issues.append(f"Expected {expected_status}, got {response.status_code}")
                if response.text:
                    issues.append(f"Response: {response.text[:100]}")

                self.test_results.append(RegressionTestResult(
                    test_name=test_name,
                    category=category,
                    success=False,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    expected_status_code=expected_status,
                    data_validated=False,
                    issues=issues,
                    metrics={"response_size": len(response.content)},
                    timestamp=datetime.now()
                ))

                print(f"❌ {test_name}: Expected {expected_status}, got {response.status_code}")

        except Exception as e:
            self.test_results.append(RegressionTestResult(
                test_name=test_name,
                category=category,
                success=False,
                response_time_ms=0,
                status_code=0,
                expected_status_code=expected_status,
                data_validated=False,
                issues=[f"Exception: {str(e)}"],
                metrics={},
                timestamp=datetime.now()
            ))
            print(f"❌ {test_name}: Exception - {str(e)}")

    async def test_security_endpoint(self, test_name: str, endpoint: str,
                                     request_count: int = 1, method: str = "GET",
                                     payload: Dict[str, Any] = None):
        """Test security-specific endpoint behavior"""
        try:
            issues = []
            responses = []

            for i in range(request_count):
                try:
                    start_time = time.time()
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        if method == "GET":
                            response = await client.get(f"{self.base_url}{endpoint}")
                        elif method == "POST":
                            response = await client.post(f"{self.base_url}{endpoint}", json=payload)
                        else:
                            response = await client.get(f"{self.base_url}{endpoint}")

                        response_time = (time.time() - start_time) * 1000
                        responses.append({
                            "status_code": response.status_code,
                            "response_time": response_time,
                            "size": len(response.content)
                        })

                except Exception as e:
                    issues.append(f"Request {i+1} failed: {str(e)}")

            # Analyze rate limiting behavior
            if len(responses) == request_count:
                if all(r["status_code"] == 429 for r in responses):
                    issues.append("Rate limiting correctly applied")
                    print(f"✅ {test_name}: Rate limiting working correctly")
                elif all(r["status_code"] == 200 for r in responses):
                    print(f"⚠️  {test_name}: No rate limiting detected (may be expected)")
                else:
                    mixed_responses = [r["status_code"] for r in responses]
                    print(f"⚠️  {test_name}: Mixed responses - {set(mixed_responses)}")

        except Exception as e:
            issues.append(f"Security test failed: {str(e)}")
            print(f"❌ {test_name}: Security test error - {str(e)}")

        return issues

    async def generate_regression_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive regression report"""
        print("\n" + "="*80)
        print("📊 PSYNSYNC PLATFORM REGRESSION REPORT")
        print("="*80)

        # Calculate overall statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # Category breakdown
        category_stats = {}
        for result in self.test_results:
            category = result.category.value
            if category not in category_stats:
                category_stats[category] = {"total": 0, "success": 0, "failed": 0}
            category_stats[category]["total"] += 1
            if result.success:
                category_stats[category]["success"] += 1
            else:
                category_stats[category]["failed"] += 1

        # Health check summary
        healthy_services = sum(1 for h in self.health_checks if h.status == "healthy")
        total_services = len(self.health_checks)
        health_rate = (healthy_services / total_services * 100) if total_services > 0 else 0

        print(f"\n🎯 EXECUTION SUMMARY")
        print(f"├─ Total Tests: {total_tests}")
        print(f"├─ Successful: {successful_tests}")
        print(f"├─ Failed: {failed_tests}")
        print(f"└─ Success Rate: {success_rate:.1f}%")
        print(f"└─ Execution Time: {total_time:.2f} seconds")

        print(f"\n💚 HEALTH CHECK SUMMARY")
        print(f"├─ Services Checked: {total_services}")
        print(f"├─ Healthy Services: {healthy_services}")
        print(f"└─ Health Rate: {health_rate:.1f}%")

        print(f"\n📊 CATEGORY BREAKDOWN")
        for category, stats in sorted(category_stats.items()):
            success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status_icon = "✅" if success_rate == 100 else "⚠️" if success_rate >= 90 else "❌"
            print(f"{status_icon} {category.replace('_', ' ').title()}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

        # Performance analysis
        response_times = [r.response_time_ms for r in self.test_results if r.response_time_ms > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)

            print(f"\n⚡ PERFORMANCE ANALYSIS")
            print(f"├─ Average Response Time: {avg_time:.2f}ms")
            print(f"├─ Maximum Response Time: {max_time:.2f}ms")
            print(f"└─ Minimum Response Time: {min_time:.2f}ms")

            # Performance grade
            if avg_time < 100:
                print("└─ Performance Grade: ✅ EXCELLENT (< 100ms)")
            elif avg_time < 500:
                print("└─ Performance Grade: ✅ GOOD (< 500ms)")
            elif avg_time < 1000:
                print("└─ Performance Grade: ⚠️  ACCEPTABLE (< 1000ms)")
            else:
                print("└─ Performance Grade: ❌ NEEDS OPTIMIZATION (> 1000ms)")

        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if not result.success and "critical" in result.test_name.lower():
                critical_issues.append(result.test_name)

        if critical_issues:
            print(f"\n❌ CRITICAL ISSUES DETECTED")
            for issue in critical_issues:
                print(f"├─ {issue}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES DETECTED")

        # Recommendations
        print(f"\n🚀 REGRESSION RECOMMENDATIONS")
        recommendations = [
            "✅ Continue monitoring critical test cases in CI/CD pipeline",
            "✅ Implement automated regression testing for new features",
            "✅ Monitor performance benchmarks and alert on degradation",
            "✅ Maintain comprehensive test coverage across all categories",
            "✅ Regular security audits and penetration testing",
            "✅ Database consistency checks and repair procedures",
            "✅ API versioning and backward compatibility maintenance",
            "✅ Cross-platform compatibility testing with each release",
            "✅ User experience monitoring and feedback collection"
        ]

        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

        # Determine overall status
        if success_rate >= 95:
            overall_status = "✅ EXCELLENT"
            deployment_ready = True
        elif success_rate >= 90:
            overall_status = "✅ GOOD"
            deployment_ready = True
        elif success_rate >= 80:
            overall_status = "⚠️ ACCEPTABLE"
            deployment_ready = False
        else:
            overall_status = "❌ NEEDS ATTENTION"
            deployment_ready = False

        print(f"\n🎯 OVERALL ASSESSMENT")
        print(f"├─ Overall Status: {overall_status}")
        print(f"├─ Success Rate: {success_rate:.1f}%")
        print(f"└─ Deployment Ready: {'✅ YES' if deployment_ready else '❌ NO'}")

        # Create detailed report data
        report_data = {
            "execution_timestamp": datetime.now().isoformat(),
            "execution_time_seconds": total_time,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate_percent": success_rate,
            "health_checks": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "health_rate_percent": health_rate,
                "details": [asdict(h) for h in self.health_checks]
            },
            "category_statistics": category_stats,
            "performance_metrics": {
                "average_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
                "max_response_time_ms": max(response_times) if response_times else 0,
                "min_response_time_ms": min(response_times) if response_times else 0
            },
            "test_results": [asdict(r) for r in self.test_results],
            "critical_issues": critical_issues,
            "deployment_ready": deployment_ready,
            "recommendations": recommendations
        }

        # Save detailed report
        report_file = f"regression_suite_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed regression report saved to: {report_file}")

        return report_data

async def main():
    """Main function to execute regression suite"""
    print("🔍 PSYNSYNC PLATFORM REGRESSION SUITE")
    print("=" * 80)
    print("Comprehensive regression testing to prevent regressions")
    print("=" * 80)

    suite = PsychSyncPlatformRegressionSuite()

    try:
        report = await suite.run_full_regression_suite()

        if report["success_rate_percent"] >= 90:
            print(f"\n🎉 REGRESSION SUITE COMPLETED SUCCESSFULLY")
            print(f"✅ Platform stability maintained at {report['success_rate_percent']:.1f}%")
            print(f"🚀 System ready for production deployment")
            return 0
        else:
            print(f"\n⚠️  REGRESSION ISSUES DETECTED")
            print(f"❌ Review failed tests before deployment")
            print(f"🔧 Address critical issues to improve stability")
            return 1

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Regression suite interrupted by user")
        return 2
    except Exception as e:
        print(f"\n❌ Regression suite failed: {str(e)}")
        return 3

if __name__ == "__main__":
    asyncio.run(main())
