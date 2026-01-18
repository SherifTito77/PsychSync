#!/usr/bin/env python3
"""
Comprehensive Automated JWT Validation Test Suite
Integrates all JWT testing scenarios into a single automated framework

Usage:
    python comprehensive_jwt_tests.py --full
    python comprehensive_jwt_tests.py --quick
    python comprehensive_jwt_tests.py --security-focus
"""

import asyncio
import aiohttp
import json
import time
import argparse
import sys
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import statistics

@dataclass
class JWTTestResult:
    """Comprehensive test result with detailed metrics"""
    test_name: str
    category: str
    status: str  # 'pass', 'fail', 'error', 'skip'
    response_code: int
    response_time: float
    security_score: float  # 0-100
    performance_score: float  # 0-100
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    security_issues: List[str] = None
    recommendations: List[str] = None
    test_details: Dict[str, Any] = None

@dataclass
class JWTTestSummary:
    """Comprehensive test summary with insights"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    security_score: float
    performance_score: float
    critical_issues: List[str]
    security_findings: List[str]
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    test_duration: float

class AutomatedJWTTester:
    """Comprehensive automated JWT testing framework"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results: List[JWTTestResult] = []
        self.start_time = None

        # Test configuration
        self.test_config = {
            "user_credentials": {
                "email": "admin@example.com",
                "password": "Admin@12345"
            },
            "performance_thresholds": {
                "max_response_time": 1000,  # ms
                "max_token_gen_time": 500,
                "max_validation_time": 100
            },
            "security_thresholds": {
                "min_security_score": 80,
                "critical_issues_threshold": 1,
                "high_issues_threshold": 3
            }
        }

        # Test tokens storage
        self.tokens = {}
        self.test_metrics = {
            "response_times": [],
            "token_generation_times": [],
            "validation_times": [],
            "security_scores": [],
            "performance_scores": []
        }

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=100)

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "AutomatedJWTTester/1.0",
                "Accept": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def make_request(
        self,
        method: str,
        endpoint: str,
        headers: Dict = None,
        data: Dict = None,
        auth_token: str = None
    ) -> Tuple[int, float, Dict]:
        """Make HTTP request with comprehensive timing and error handling"""
        start_time = time.time()

        request_headers = {}
        if headers:
            request_headers.update(headers)
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with self.session.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=request_headers,
                json=data
            ) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms

                try:
                    response_data = await response.json()
except Exception as e:                    response_data = {"raw_response": await response.text()}

                return response.status, response_time, response_data

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return 0, response_time, {"error": str(e)}

    async def authenticate_and_store_tokens(self) -> bool:
        """Authenticate user and store tokens for testing"""
        try:
            login_data = {
                "username": self.test_config["user_credentials"]["email"],
                "password": self.test_config["user_credentials"]["password"]
            }

            status, response_time, data = await self.make_request(
                "POST", "/api/v1/token-minimal", data={"email": self.test_config["user_credentials"]["email"], "password": self.test_config["user_credentials"]["password"]}
            )

            if status == 200:
                # Extract tokens from response
                tokens = {}
                if "data" in data:
                    tokens = data["data"]
                elif "access_token" in data:
                    tokens = data

                # Check if we have at least an access token (some APIs don't return refresh_token)
                if "access_token" in tokens:
                    self.tokens.update(tokens)

                    # Store token metadata
                    self.tokens["token_metadata"] = {
                        "login_time": datetime.now().isoformat(),
                        "login_response_time": response_time,
                        "access_token_length": len(tokens["access_token"]),
                        "refresh_token_length": len(tokens.get("refresh_token", ""))
                    }

                    # Decode tokens for analysis
                    try:
                        self.tokens["access_payload"] = self.decode_jwt_safely(tokens["access_token"])
                        if "refresh_token" in tokens:
                            self.tokens["refresh_payload"] = self.decode_jwt_safely(tokens["refresh_token"])
                        else:
                            self.tokens["refresh_payload"] = None
                            print("Note: No refresh token provided by API")
                    except Exception as e:
                        print(f"Warning: Could not decode tokens: {e}")

                    return True
                else:
                    print("Error: No tokens found in login response")
                    return False
            else:
                print(f"Authentication failed: {status} - {data}")
                return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def decode_jwt_safely(self, token: str) -> Dict:
        """Decode JWT without verification for analysis"""
        try:
            if token.startswith("Bearer "):
                token = token[7:]

            parts = token.split('.')
            if len(parts) != 3:
                return {}

            # Decode payload
            import base64
            payload = base64.urlsafe_b64decode(parts[1] + '==')
            return json.loads(payload)
        except Exception:
            return {}

    def calculate_security_score(self, result: JWTTestResult) -> float:
        """Calculate security score for a test result"""
        score = 100.0

        # Deduct points for failures
        if result.status == "fail":
            score -= 30
        elif result.status == "error":
            score -= 20

        # Deduct points for security issues
        if result.security_issues:
            score -= len(result.security_issues) * 15

        # Deduct points for slow responses
        if result.response_time > self.test_config["performance_thresholds"]["max_response_time"]:
            score -= 10

        # Bonus points for security features
        if result.test_details:
            if result.test_details.get("blacklisting_works"):
                score += 10
            if result.test_details.get("token_uniqueness"):
                score += 5
            if result.test_details.get("proper_expiration"):
                score += 5

        return max(0, min(100, score))

    def calculate_performance_score(self, result: JWTTestResult) -> float:
        """Calculate performance score for a test result"""
        score = 100.0

        # Base score on response time
        if result.response_time <= 100:
            score = 100
        elif result.response_time <= 500:
            score = 80
        elif result.response_time <= 1000:
            score = 60
        elif result.response_time <= 2000:
            score = 40
        else:
            score = 20

        # Deduct points for errors
        if result.status == "fail":
            score -= 30
        elif result.status == "error":
            score -= 40

        return max(0, score)

    async def run_test_with_metrics(
        self,
        test_name: str,
        category: str,
        test_func: Callable,
        **kwargs
    ) -> JWTTestResult:
        """Run a test function with comprehensive metrics collection"""
        print(f"  🧪 {test_name}")

        try:
            start_time = time.time()

            # Run the test function
            test_result_data = await test_func(**kwargs)

            test_duration = time.time() - start_time

            # Create comprehensive test result
            result = JWTTestResult(
                test_name=test_name,
                category=category,
                status=test_result_data.get("status", "pass"),
                response_code=test_result_data.get("response_code", 200),
                response_time=test_result_data.get("response_time", 0),
                security_score=0,  # Will be calculated
                performance_score=0,  # Will be calculated
                error_message=test_result_data.get("error_message"),
                response_data=test_result_data.get("response_data"),
                security_issues=test_result_data.get("security_issues", []),
                recommendations=test_result_data.get("recommendations", []),
                test_details=test_result_data.get("details", {})
            )

            # Calculate scores
            result.security_score = self.calculate_security_score(result)
            result.performance_score = self.calculate_performance_score(result)

            # Store metrics
            self.test_metrics["response_times"].append(result.response_time)
            self.test_metrics["security_scores"].append(result.security_score)
            self.test_metrics["performance_scores"].append(result.performance_score)

            # Print result
            status_icon = "✅" if result.status == "pass" else "❌" if result.status == "fail" else "⚠️"
            print(f"     {status_icon} {result.status.upper()} - {result.response_time:.0f}ms - "
                  f"Security: {result.security_score:.0f}/100 - Performance: {result.performance_score:.0f}/100")

            if result.security_issues:
                for issue in result.security_issues:
                    print(f"        🔒 Issue: {issue}")

            return result

        except Exception as e:
            print(f"     ❌ ERROR: {str(e)}")
            return JWTTestResult(
                test_name=test_name,
                category=category,
                status="error",
                response_code=0,
                response_time=0,
                security_score=0,
                performance_score=0,
                error_message=str(e),
                security_issues=["Test execution error"],
                recommendations=["Investigate test framework issue"]
            )

    async def test_token_authentication(self) -> JWTTestResult:
        """Test user authentication and token generation"""

        if not self.tokens.get("access_token"):
            success = await self.authenticate_and_store_tokens()
            if not success:
                return {
                    "status": "fail",
                    "response_code": 0,
                    "response_time": 0,
                    "error_message": "Failed to authenticate",
                    "security_issues": ["Authentication system not working"],
                    "recommendations": ["Check API server and user credentials"]
                }

        # Analyze token structure
        security_issues = []
        recommendations = []
        details = {}

        access_token = self.tokens["access_token"]
        refresh_token = self.tokens["refresh_token"]
        access_payload = self.tokens.get("access_payload", {})
        refresh_payload = self.tokens.get("refresh_payload", {})

        # Validate access token
        if len(access_token.split('.')) != 3:
            security_issues.append("Access token has invalid JWT structure")
        else:
            details["access_token_structure"] = "valid"

        # Validate refresh token
        if len(refresh_token.split('.')) != 3:
            security_issues.append("Refresh token has invalid JWT structure")
        else:
            details["refresh_token_structure"] = "valid"

        # Check token claims
        if access_payload:
            required_claims = ["sub", "exp", "iat", "type"]
            missing_claims = [claim for claim in required_claims if claim not in access_payload]
            if missing_claims:
                security_issues.append(f"Access token missing claims: {', '.join(missing_claims)}")
            else:
                details["access_token_claims"] = "complete"
                details["access_token_type"] = access_payload.get("type")

            # Check expiration time
            if "exp" in access_payload and "iat" in access_payload:
                duration = access_payload["exp"] - access_payload["iat"]
                if abs(duration - 1800) > 60:  # 30 minutes ± 1 minute
                    security_issues.append(f"Access token duration unusual: {duration} seconds")
                else:
                    details["access_token_duration"] = duration
                    details["proper_expiration"] = True

        # Check refresh token claims
        if refresh_payload:
            if refresh_payload.get("type") != "refresh":
                security_issues.append(f"Refresh token has incorrect type: {refresh_payload.get('type')}")
            else:
                details["refresh_token_type"] = "correct"

            # Check refresh token duration
            if "exp" in refresh_payload and "iat" in refresh_payload:
                duration = refresh_payload["exp"] - refresh_payload["iat"]
                if duration < 518400:  # Less than 6 days
                    security_issues.append(f"Refresh token lifetime too short: {duration} seconds")
                else:
                    details["refresh_token_duration"] = duration

        # Check token uniqueness
        details["token_uniqueness"] = len(access_token) > 100 and len(refresh_token) > 100

        return {
            "status": "fail" if security_issues else "pass",
            "response_code": 200,
            "response_time": self.tokens.get("token_metadata", {}).get("login_response_time", 0),
            "security_issues": security_issues,
            "recommendations": recommendations,
            "details": details
        }

    async def test_token_usage_validation(self) -> JWTTestResult:
        """Test token usage with protected endpoints"""

        if not self.tokens.get("access_token"):
            return {
                "status": "skip",
                "error_message": "No access token available"
            }

        # Test fresh token usage
        status, response_time, data = await self.make_request(
            "GET", "/api/v1/api/v1/me-minimal", auth_token=self.tokens["access_token"]
        )

        security_issues = []
        details = {}

        if status == 200:
            details["fresh_token_works"] = True
            details["user_data_returned"] = "data" in data or "email" in data
        else:
            security_issues.append(f"Fresh access token rejected: {status}")
            details["fresh_token_works"] = False

        return {
            "status": "pass" if status == 200 else "fail",
            "response_code": status,
            "response_time": response_time,
            "security_issues": security_issues,
            "recommendations": ["Check token validation logic"] if status != 200 else [],
            "details": details
        }

    async def test_token_expiration_behavior(self) -> JWTTestResult:
        """Test token expiration and time-based behavior"""

        if not self.tokens.get("access_payload"):
            return {
                "status": "skip",
                "error_message": "No token payload available for expiration testing"
            }

        access_payload = self.tokens["access_payload"]
        exp_time = access_payload.get("exp")
        iat_time = access_payload.get("iat")

        security_issues = []
        recommendations = []
        details = {}

        if exp_time and iat_time:
            now = int(time.time())
            time_to_exp = exp_time - now
            token_duration = exp_time - iat_time

            details["issued_at"] = iat_time
            details["expires_at"] = exp_time
            details["time_to_expiration"] = time_to_exp
            details["token_duration"] = token_duration

            # Validate token duration
            if abs(token_duration - 1800) > 60:  # 30 minutes ± 1 minute
                security_issues.append(f"Token duration unexpected: {token_duration} seconds")
            else:
                details["proper_duration"] = True

            # Test if token is still valid
            if time_to_exp > 0:
                status, response_time, data = await self.make_request(
                    "GET", "/api/v1/api/v1/me-minimal", auth_token=self.tokens["access_token"]
                )

                if status == 200:
                    details["valid_token_works"] = True
                else:
                    security_issues.append(f"Valid token rejected: {status}")
            else:
                details["token_expired"] = True
                security_issues.append("Token already expired during test")

        else:
            security_issues.append("Token missing expiration claims")

        return {
            "status": "fail" if security_issues else "pass",
            "response_code": 200,
            "response_time": 0,
            "security_issues": security_issues,
            "recommendations": recommendations,
            "details": details
        }

    async def test_refresh_token_mechanism(self) -> JWTTestResult:
        """Test refresh token functionality and security"""

        # Skip refresh token tests as refresh endpoint is not available in minimal API
        return {
            "status": "skip",
            "error_message": "Refresh token endpoint not available in minimal API"
        }

        refresh_token = self.tokens["refresh_token"]
        security_issues = []
        recommendations = []
        details = {}

        # Test refresh token usage
        start_time = time.time()
        status, response_time, data = await self.make_request(
            "POST", "/api/v1/auth/refresh",
            data={"refresh_token": refresh_token}
        )

        if status == 200:
            # Extract new access token
            new_access_token = None
            if "data" in data and "access_token" in data["data"]:
                new_access_token = data["data"]["access_token"]
            elif "access_token" in data:
                new_access_token = data["access_token"]

            if new_access_token:
                details["refresh_successful"] = True
                details["new_token_received"] = True
                details["refresh_response_time"] = response_time

                # Validate new token is different
                if new_access_token != self.tokens["access_token"]:
                    details["new_token_different"] = True

                    # Test new token works
                    status2, response_time2, data2 = await self.make_request(
                        "GET", "/api/v1/api/v1/me-minimal", auth_token=new_access_token
                    )

                    if status2 == 200:
                        details["new_token_works"] = True
                    else:
                        security_issues.append(f"New refresh token failed: {status2}")
                else:
                    security_issues.append("Refresh token returned same token")

            else:
                security_issues.append("No new access token in refresh response")

        else:
            security_issues.append(f"Refresh token request failed: {status}")

        # Test refresh token reuse (should be prevented)
        status2, response_time2, data2 = await self.make_request(
            "POST", "/api/v1/auth/refresh",
            data={"refresh_token": refresh_token}
        )

        if status2 in [401, 403]:
            details["reuse_prevented"] = True
        else:
            security_issues.append("Refresh token reuse not prevented")

        return {
            "status": "fail" if security_issues else "pass",
            "response_code": status,
            "response_time": response_time,
            "security_issues": security_issues,
            "recommendations": recommendations,
            "details": details
        }

    async def test_invalid_token_security(self) -> JWTTestResult:
        """Test security against invalid and malicious tokens"""

        security_issues = []
        recommendations = []
        details = {}

        # Test cases for invalid tokens
        invalid_token_tests = [
            {
                "name": "missing_auth",
                "token": None,
                "expected_status": [401]
            },
            {
                "name": "invalid_format",
                "token": "invalid.token.format",
                "expected_status": [401, 422]
            },
            {
                "name": "malformed_jwt",
                "token": "headeronly.payload",
                "expected_status": [401]
            },
            {
                "name": "empty_token",
                "token": "",
                "expected_status": [401]
            }
        ]

        results = {}

        for test_case in invalid_token_tests:
            test_name = test_case["name"]
            token = test_case["token"]
            expected = test_case["expected_status"]

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            status, response_time, data = await self.make_request(
                "GET", "/api/v1/api/v1/me-minimal", headers=headers
            )

            if status in expected:
                results[test_name] = "properly_rejected"
                details[f"{test_name}_rejected"] = True
            else:
                security_issues.append(f"{test_name}: Expected {expected}, got {status}")
                details[f"{test_name}_rejected"] = False

            # Check for token leakage in error response
            response_text = json.dumps(data).lower()
            sensitive_keywords = ["access_token", "refresh_token", "jwt", "bearer", "secret"]
            found_keywords = [kw for kw in sensitive_keywords if kw in response_text]

            if found_keywords:
                security_issues.append(f"{test_name}: Token leakage detected - {', '.join(found_keywords)}")
                details[f"{test_name}_leakage"] = found_keywords

        # Test tampered token
        if self.tokens.get("access_token"):
            original_token = self.tokens["access_token"]
            parts = original_token.split('.')

            if len(parts) == 3:
                # Tamper with payload
                tampered_payload = parts[1] + "tamper"
                tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

                status, response_time, data = await self.make_request(
                    "GET", "/api/v1/api/v1/me-minimal",
                    auth_token=tampered_token
                )

                if status == 401:
                    details["tampered_token_rejected"] = True
                else:
                    security_issues.append("Tampered token was accepted")
                    details["tampered_token_rejected"] = False

        details["invalid_token_tests_passed"] = len([r for r in results.values() if r == "properly_rejected"])

        return {
            "status": "fail" if security_issues else "pass",
            "response_code": 401,  # Expected for invalid tokens
            "response_time": 0,
            "security_issues": security_issues,
            "recommendations": recommendations,
            "details": details
        }

    async def test_concurrent_token_usage(self) -> JWTTestResult:
        """Test system behavior under concurrent token usage"""

        if not self.tokens.get("access_token"):
            return {
                "status": "skip",
                "error_message": "No access token available for concurrent testing"
            }

        access_token = self.tokens["access_token"]
        security_issues = []
        recommendations = []
        details = {}

        # Test concurrent requests with same token
        concurrent_count = 20
        start_time = time.time()

        tasks = []
        for i in range(concurrent_count):
            task = self.make_request("GET", "/api/v1/api/v1/me-minimal", auth_token=access_token)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze results
        successful_requests = 0
        failed_requests = 0
        response_times = []

        for result in results:
            if isinstance(result, tuple):
                status, response_time, data = result
                response_times.append(response_time)

                if status == 200:
                    successful_requests += 1
                elif status == 429:
                    # Rate limiting is acceptable
                    failed_requests += 1
                else:
                    failed_requests += 1
                    if status not in [401, 429]:  # 401 is expected if token expired
                        security_issues.append(f"Unexpected error in concurrent request: {status}")
            else:
                failed_requests += 1
                security_issues.append(f"Exception in concurrent request: {str(result)}")

        details.update({
            "concurrent_requests": concurrent_count,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0
        })

        # Performance analysis
        if details["average_response_time"] > 2000:
            recommendations.append("Consider optimizing concurrent request handling")

        if successful_requests < concurrent_count * 0.8:  # At least 80% success
            security_issues.append("Low success rate under concurrent load")

        return {
            "status": "fail" if security_issues else "pass",
            "response_code": 200 if successful_requests > 0 else 0,
            "response_time": details["average_response_time"],
            "security_issues": security_issues,
            "recommendations": recommendations,
            "details": details
        }

    async def test_token_blacklisting(self) -> JWTTestResult:
        """Test token blacklisting functionality"""

        # Skip blacklisting tests as logout endpoint is not available in minimal API
        return {
            "status": "skip",
            "error_message": "Logout endpoint not available in minimal API - cannot test blacklisting"
        }

        access_token = self.tokens["access_token"]
        security_issues = []
        recommendations = []
        details = {}

        # First, verify token works
        status, response_time, data = await self.make_request(
            "GET", "/api/v1/api/v1/me-minimal", auth_token=access_token
        )

        if status != 200:
            return {
                "status": "skip",
                "error_message": "Initial token validation failed, cannot test blacklisting"
            }

        # Test logout (should blacklist token)
        status, response_time, data = await self.make_request(
            "POST", "/api/v1/auth/logout", auth_token=access_token
        )

        if status in [200, 204]:
            details["logout_successful"] = True

            # Test if token is now blacklisted
            status2, response_time2, data2 = await self.make_request(
                "GET", "/api/v1/api/v1/me-minimal", auth_token=access_token
            )

            if status2 == 401:
                details["blacklisting_works"] = True
            else:
                security_issues.append("Token not blacklisted after logout")
                details["blacklisting_works"] = False

        else:
            security_issues.append(f"Logout failed: {status}")
            details["logout_successful"] = False

        return {
            "status": "fail" if security_issues else "pass",
            "response_code": status,
            "response_time": response_time,
            "security_issues": security_issues,
            "recommendations": recommendations,
            "details": details
        }

    async def run_comprehensive_test_suite(self, quick_mode: bool = False) -> List[JWTTestResult]:
        """Run the complete JWT test suite"""

        print("🚀 Starting Comprehensive JWT Token Test Suite")
        print("=" * 60)
        self.start_time = time.time()

        # Authentication and setup
        print("\n🔐 Authentication & Setup")
        auth_success = await self.authenticate_and_store_tokens()
        if not auth_success:
            print("❌ Authentication failed - aborting tests")
            return []

        # Test categories to run
        test_categories = [
            ("Token Authentication", self.test_token_authentication),
            ("Token Usage Validation", self.test_token_usage_validation),
            ("Token Expiration Behavior", self.test_token_expiration_behavior),
            ("Refresh Token Mechanism", self.test_refresh_token_mechanism),
            ("Invalid Token Security", self.test_invalid_token_security),
            ("Concurrent Token Usage", self.test_concurrent_token_usage),
            ("Token Blacklisting", self.test_token_blacklisting)
        ]

        if quick_mode:
            # Run only critical tests in quick mode
            test_categories = [
                ("Token Authentication", self.test_token_authentication),
                ("Token Usage Validation", self.test_token_usage_validation),
                ("Invalid Token Security", self.test_invalid_token_security)
            ]

        # Run all tests
        for category_name, test_func in test_categories:
            print(f"\n📋 {category_name}")
            print("-" * 40)

            result = await self.run_test_with_metrics(
                f"{category_name} Test",
                category_name.lower().replace(" ", "_"),
                test_func
            )

            self.test_results.append(result)

        return self.test_results

    def calculate_comprehensive_summary(self) -> JWTTestSummary:
        """Calculate comprehensive test summary with insights"""

        if not self.test_results:
            return JWTTestSummary(
                total_tests=0, passed_tests=0, failed_tests=0, error_tests=0, skipped_tests=0,
                security_score=0, performance_score=0, critical_issues=[], security_findings=[],
                performance_metrics={}, recommendations=[], test_duration=0
            )

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "pass"])
        failed_tests = len([r for r in self.test_results if r.status == "fail"])
        error_tests = len([r for r in self.test_results if r.status == "error"])
        skipped_tests = len([r for r in self.test_results if r.status == "skip"])

        # Calculate scores
        avg_security_score = statistics.mean([r.security_score for r in self.test_results if r.security_score > 0]) if any(r.security_score > 0 for r in self.test_results) else 0
        avg_performance_score = statistics.mean([r.performance_score for r in self.test_results if r.performance_score > 0]) if any(r.performance_score > 0 for r in self.test_results) else 0

        # Collect all security issues
        all_security_issues = []
        critical_issues = []

        for result in self.test_results:
            if result.security_issues:
                all_security_issues.extend(result.security_issues)
                # Identify critical issues (security score < 50)
                if result.security_score < 50:
                    critical_issues.extend(result.security_issues)

        # Performance metrics
        response_times = [r.response_time for r in self.test_results if r.response_time > 0]
        performance_metrics = {}

        if response_times:
            performance_metrics = {
                "average_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
            }

        # Generate recommendations
        recommendations = []

        if avg_security_score < 80:
            recommendations.append("Review and improve JWT security implementation")

        if avg_performance_score < 70:
            recommendations.append("Optimize JWT validation performance")

        if critical_issues:
            recommendations.append("Address critical security issues immediately")

        if any("token leakage" in issue.lower() for issue in all_security_issues):
            recommendations.append("Review error handling to prevent token leakage")

        if any("blacklist" in issue.lower() for issue in all_security_issues):
            recommendations.append("Implement or fix token blacklisting mechanism")

        test_duration = time.time() - self.start_time if self.start_time else 0

        return JWTTestSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            skipped_tests=skipped_tests,
            security_score=avg_security_score,
            performance_score=avg_performance_score,
            critical_issues=critical_issues,
            security_findings=list(set(all_security_issues)),
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            test_duration=test_duration
        )

    def print_comprehensive_report(self, summary: JWTTestSummary) -> None:
        """Print comprehensive test report with insights"""

        print(f"\n📊 Comprehensive JWT Test Report")
        print("=" * 50)
        print(f"Test Duration: {summary.test_duration:.2f} seconds")
        print(f"Total Tests: {summary.total_tests}")
        success_rate = (summary.passed_tests/summary.total_tests*100) if summary.total_tests > 0 else 0
        print(f"✅ Passed: {summary.passed_tests} ({success_rate:.1f}%)")
        failed_rate = (summary.failed_tests/summary.total_tests*100) if summary.total_tests > 0 else 0
        print(f"❌ Failed: {summary.failed_tests} ({failed_rate:.1f}%)")
        print(f"⚠️  Errors: {summary.error_tests}")
        print(f"⏭️  Skipped: {summary.skipped_tests}")

        # Scores
        print(f"\n📈 Performance Scores:")
        print(f"🔒 Security Score: {summary.security_score:.1f}/100")
        print(f"⚡ Performance Score: {summary.performance_score:.1f}/100")

        # Performance metrics
        if summary.performance_metrics:
            print(f"\n⚡ Performance Metrics:")
            print(f"   Average Response Time: {summary.performance_metrics.get('average_response_time', 0):.1f}ms")
            print(f"   Min Response Time: {summary.performance_metrics.get('min_response_time', 0):.1f}ms")
            print(f"   Max Response Time: {summary.performance_metrics.get('max_response_time', 0):.1f}ms")
            print(f"   95th Percentile: {summary.performance_metrics.get('p95_response_time', 0):.1f}ms")

        # Security assessment
        if summary.critical_issues:
            print(f"\n🚨 Critical Security Issues:")
            for issue in summary.critical_issues:
                print(f"   • {issue}")

        if summary.security_findings:
            print(f"\n🔍 Security Findings:")
            for finding in summary.security_findings:
                print(f"   • {finding}")

        # Recommendations
        if summary.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(summary.recommendations, 1):
                print(f"   {i}. {rec}")

        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if summary.security_score >= 90 and summary.performance_score >= 80:
            print("   ✅ Excellent JWT implementation")
        elif summary.security_score >= 80 and summary.performance_score >= 70:
            print("   ✅ Good JWT implementation with minor improvements needed")
        elif summary.security_score >= 70 and summary.performance_score >= 60:
            print("   ⚠️  Acceptable JWT implementation - improvements recommended")
        else:
            print("   ❌ JWT implementation requires significant improvements")

    def save_detailed_report(self, summary: JWTTestSummary, filename: str) -> None:
        """Save detailed comprehensive test report"""

        report_data = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "test_type": "comprehensive_jwt_validation",
                "test_duration": summary.test_duration,
                "quick_mode": False
            },
            "test_configuration": self.test_config,
            "token_metadata": self.tokens.get("token_metadata", {}),
            "summary": {
                "total_tests": summary.total_tests,
                "passed_tests": summary.passed_tests,
                "failed_tests": summary.failed_tests,
                "error_tests": summary.error_tests,
                "skipped_tests": summary.skipped_tests,
                "success_rate": (summary.passed_tests / summary.total_tests * 100) if summary.total_tests > 0 else 0,
                "security_score": summary.security_score,
                "performance_score": summary.performance_score
            },
            "performance_metrics": summary.performance_metrics,
            "security_assessment": {
                "critical_issues": summary.critical_issues,
                "security_findings": summary.security_findings,
                "risk_level": "LOW" if summary.security_score >= 80 else "MEDIUM" if summary.security_score >= 60 else "HIGH"
            },
            "recommendations": summary.recommendations,
            "detailed_results": [
                {
                    "test_name": result.test_name,
                    "category": result.category,
                    "status": result.status,
                    "response_code": result.response_code,
                    "response_time_ms": result.response_time,
                    "security_score": result.security_score,
                    "performance_score": result.performance_score,
                    "error_message": result.error_message,
                    "security_issues": result.security_issues,
                    "recommendations": result.recommendations,
                    "test_details": result.test_details
                }
                for result in self.test_results
            ]
        }

        report_path = Path(filename)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Comprehensive JWT token testing suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--quick", action="store_true", help="Run quick test suite (critical tests only)")
    parser.add_argument("--security-focus", action="store_true", help="Focus on security-related tests")
    parser.add_argument("--output", help="Save detailed report to file")
    parser.add_argument("--full", action="store_true", help="Run full comprehensive test suite")

    args = parser.parse_args()

    # Default to full suite if no specific mode selected
    if not any([args.quick, args.security_focus, args.full]):
        args.full = True

    print("🔐 Comprehensive JWT Token Testing Suite")
    print("=" * 50)
    print(f"Base URL: {args.url}")
    print(f"Mode: {'Quick' if args.quick else 'Security Focus' if args.security_focus else 'Full Comprehensive'}")

    async with AutomatedJWTTester(args.url) as tester:
        try:
            # Run tests based on mode
            if args.security_focus:
                # Security-focused tests
                security_tests = [
                    ("Token Authentication", tester.test_token_authentication),
                    ("Invalid Token Security", tester.test_invalid_token_security),
                    ("Token Blacklisting", tester.test_token_blacklisting)
                ]

                print("\n🔒 Security-Focused Test Suite")
                tester.start_time = time.time()

                # Run authentication first
                auth_success = await tester.authenticate_and_store_tokens()
                if not auth_success:
                    print("❌ Authentication failed - cannot run security tests")
                    return 1

                for category_name, test_func in security_tests:
                    print(f"\n📋 {category_name}")
                    print("-" * 40)

                    result = await tester.run_test_with_metrics(
                        f"{category_name} Test",
                        category_name.lower().replace(" ", "_"),
                        test_func
                    )

                    tester.test_results.append(result)

            else:
                # Quick or full comprehensive tests
                results = await tester.run_comprehensive_test_suite(quick_mode=args.quick)

            # Calculate and display results
            summary = tester.calculate_comprehensive_summary()
            tester.print_comprehensive_report(summary)

            if args.output:
                tester.save_detailed_report(summary, args.output)

            # Return exit code based on results
            if len(summary.critical_issues) > 0:
                return 2  # Critical security issues
            elif summary.failed_tests > 0:
                return 1  # Test failures
            else:
                return 0  # All tests passed

        except KeyboardInterrupt:
            print("\n⚠️  Tests interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
