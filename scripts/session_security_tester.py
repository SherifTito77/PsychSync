#!/usr/bin/env python3
"""
PsychSync Session Security Tester
Tests session management security vulnerabilities
"""

import hashlib
import json
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


@dataclass
class SessionTestResult:
    """Session security test result"""

    test_name: str
    vulnerability_found: bool
    risk_level: str
    details: Dict[str, Any]
    recommendations: List[str]
    evidence: Optional[str] = None


class SessionSecurityTester:
    """Comprehensive session security testing suite"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[SessionTestResult] = []
        self.session = requests.Session()
        self.concurrent_sessions: List[requests.Session] = []

        # Test credentials
        self.test_credentials = {
            "email": "test@example.com",
            "password": "testpassword123",
        }

        print("🔒 Session Security Tester Initialized")
        print(f"🎯 Target: {base_url}")

    def create_test_user(self) -> bool:
        """Create a test user for session testing"""
        try:
            # Try to register a test user
            register_data = {
                "email": self.test_credentials["email"],
                "password": self.test_credentials["password"],
                "first_name": "Test",
                "last_name": "User",
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/register", json=register_data, timeout=10
            )

            # User might already exist, that's okay
            return response.status_code in [200, 201, 400]

        except Exception as e:
            print(f"⚠️ Could not create test user: {e}")
            return False

    def authenticate_user(self, session_obj: requests.Session = None) -> Optional[str]:
        """Authenticate user and return session token"""
        if session_obj is None:
            session_obj = self.session

        try:
            auth_data = {
                "username": self.test_credentials["email"],
                "password": self.test_credentials["password"],
            }

            response = session_obj.post(
                f"{self.base_url}/api/v1/token", data=auth_data, timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")

        except Exception as e:
            print(f"⚠️ Authentication failed: {e}")

        return None

    def test_session_fixation(self) -> SessionTestResult:
        """Test for session fixation vulnerabilities"""
        print("\n🔍 Testing Session Fixation...")
        print("=" * 60)

        try:
            # Step 1: Get initial session token from login page or unauthenticated request
            initial_session = requests.Session()

            # Check if session cookie is set before authentication
            response1 = initial_session.get(
                f"{self.base_url}/api/v1/health", timeout=10
            )
            pre_auth_cookies = dict(initial_session.cookies)

            # Step 2: Authenticate with the same session
            token = self.authenticate_user(initial_session)

            # Step 3: Check if session identifier changed after login
            post_auth_cookies = dict(initial_session.cookies)

            session_changed = False
            cookie_analysis = {}

            for cookie_name in pre_auth_cookies:
                if cookie_name in post_auth_cookies:
                    if pre_auth_cookies[cookie_name] != post_auth_cookies[cookie_name]:
                        session_changed = True
                    cookie_analysis[cookie_name] = {
                        "pre_auth": pre_auth_cookies[cookie_name][:20] + "...",
                        "post_auth": post_auth_cookies[cookie_name][:20] + "...",
                        "changed": pre_auth_cookies[cookie_name]
                        != post_auth_cookies[cookie_name],
                    }

            # Step 4: Test if old session token can be used
            old_session = requests.Session()
            for cookie_name, cookie_value in pre_auth_cookies.items():
                old_session.cookies.set(cookie_name, cookie_value)

            old_session_response = old_session.get(
                f"{self.base_url}/api/v1/me", timeout=10
            )

            # Step 5: Try session fixation attack by forcing session ID
            forced_session = requests.Session()
            forced_session.cookies.set("sessionid", "attacker-controlled-id")

            # Try to authenticate with forced session
            try:
                auth_response = forced_session.post(
                    f"{self.base_url}/api/v1/token",
                    data={
                        "username": self.test_credentials["email"],
                        "password": self.test_credentials["password"],
                    },
                    timeout=10,
                )

                forced_cookie_after_auth = dict(forced_session.cookies)
                attack_successful = (
                    forced_cookie_after_auth.get("sessionid")
                    == "attacker-controlled-id"
                )
            except Exception as e:
                attack_successful = False

            vulnerability_found = (
                not session_changed
                or attack_successful
                or old_session_response.status_code == 200
            )

            risk_level = (
                "CRITICAL"
                if attack_successful
                else "HIGH" if not session_changed else "LOW"
            )

            recommendations = []
            if not session_changed:
                recommendations.append(
                    "Session identifiers should be regenerated after authentication"
                )
            if old_session_response.status_code == 200:
                recommendations.append(
                    "Old session tokens should be invalidated after login"
                )
            if attack_successful:
                recommendations.append(
                    "Application should reject forced session identifiers"
                )

            if not vulnerability_found:
                recommendations.append(
                    "Session fixation protection appears to be working correctly"
                )

            return SessionTestResult(
                test_name="Session Fixation Test",
                vulnerability_found=vulnerability_found,
                risk_level=risk_level,
                details={
                    "pre_auth_cookies": len(pre_auth_cookies),
                    "post_auth_cookies": len(post_auth_cookies),
                    "session_changed_after_auth": session_changed,
                    "old_session_still_valid": old_session_response.status_code == 200,
                    "forced_session_attack_successful": attack_successful,
                    "cookie_analysis": cookie_analysis,
                },
                recommendations=recommendations,
                evidence=f"Session change: {session_changed}, Forced attack: {attack_successful}",
            )

        except Exception as e:
            return SessionTestResult(
                test_name="Session Fixation Test",
                vulnerability_found=True,
                risk_level="MEDIUM",
                details={"error": str(e)},
                recommendations=[
                    "Session fixation test failed - manual review recommended"
                ],
                evidence=str(e),
            )

    def test_session_timeout(self) -> SessionTestResult:
        """Test session timeout behavior"""
        print("\n⏰ Testing Session Timeout...")
        print("=" * 60)

        try:
            # Step 1: Authenticate and get session
            token = self.authenticate_user()

            if not token:
                return SessionTestResult(
                    test_name="Session Timeout Test",
                    vulnerability_found=True,
                    risk_level="HIGH",
                    details={"authentication_failed": True},
                    recommendations=["Authentication system not working properly"],
                    evidence="Could not authenticate test user",
                )

            # Step 2: Test immediate access (should work)
            immediate_response = self.session.get(
                f"{self.base_url}/api/v1/me", timeout=10
            )
            immediate_access = immediate_response.status_code == 200

            # Step 3: Wait for potential timeout (simulate different durations)
            timeout_durations = [60, 300, 1800]  # 1min, 5min, 30min
            timeout_results = {}

            for duration in timeout_durations:
                print(f"   ⏳ Waiting {duration} seconds to test timeout...")
                time.sleep(min(duration, 10))  # Cap at 10 seconds for demo

                # Test access after wait
                timeout_response = self.session.get(
                    f"{self.base_url}/api/v1/me", timeout=10
                )
                timeout_results[f"{duration}s"] = {
                    "status_code": timeout_response.status_code,
                    "access_granted": timeout_response.status_code == 200,
                }

            # Step 4: Test session refresh mechanism
            refresh_response = self.session.post(
                f"{self.base_url}/api/v1/refresh", timeout=10
            )
            refresh_works = refresh_response.status_code == 200

            # Step 5: Test abrupt access after simulated timeout
            # Create new session with same token
            abrupt_session = requests.Session()
            abrupt_session.headers.update({"Authorization": f"Bearer {token}"})

            abrupt_response = abrupt_session.get(
                f"{self.base_url}/api/v1/me", timeout=10
            )
            abrupt_access = abrupt_response.status_code == 200

            # Step 6: Check for proper timeout headers
            auth_response = self.session.get(f"{self.base_url}/api/v1/me", timeout=10)
            timeout_headers = {}

            for header in ["Expires", "Cache-Control", "Pragma"]:
                if header in auth_response.headers:
                    timeout_headers[header] = auth_response.headers[header]

            # Analyze results
            vulnerabilities = []
            risk_level = "LOW"

            if immediate_access and len(
                [r for r in timeout_results.values() if r["access_granted"]]
            ) == len(timeout_results):
                # Session never times out - could be a security risk
                vulnerabilities.append("Session appears to have infinite timeout")
                risk_level = "MEDIUM"

            if abrupt_access and len(timeout_results) > 0:
                # Check if session should have timed out but didn't
                longest_test = max(timeout_durations)
                if timeout_results[f"{longest_test}s"]["access_granted"]:
                    vulnerabilities.append(
                        "Session timeout may be too long or disabled"
                    )
                    risk_level = "MEDIUM"

            if not refresh_works:
                vulnerabilities.append("Session refresh mechanism not working")
                risk_level = "HIGH"

            recommendations = []
            if "Session appears to have infinite timeout" in vulnerabilities:
                recommendations.append(
                    "Implement reasonable session timeout (30 minutes to 2 hours)"
                )
            if "Session timeout may be too long" in vulnerabilities:
                recommendations.append("Review and adjust session timeout duration")
            if not refresh_works:
                recommendations.append("Implement or fix session refresh mechanism")

            if not vulnerabilities:
                recommendations.extend(
                    [
                        "Session timeout appears to be working correctly",
                        "Consider implementing sliding session timeout",
                        "Provide clear user feedback when sessions expire",
                    ]
                )

            return SessionTestResult(
                test_name="Session Timeout Test",
                vulnerability_found=len(vulnerabilities) > 0,
                risk_level=risk_level,
                details={
                    "immediate_access": immediate_access,
                    "timeout_test_results": timeout_results,
                    "refresh_works": refresh_works,
                    "abrupt_access_after_timeout": abrupt_access,
                    "timeout_headers": timeout_headers,
                    "vulnerabilities_found": vulnerabilities,
                },
                recommendations=recommendations,
                evidence=f"Timeout results: {timeout_results}",
            )

        except Exception as e:
            return SessionTestResult(
                test_name="Session Timeout Test",
                vulnerability_found=True,
                risk_level="MEDIUM",
                details={"error": str(e)},
                recommendations=[
                    "Session timeout test failed - manual review recommended"
                ],
                evidence=str(e),
            )

    def test_concurrent_sessions(self) -> SessionTestResult:
        """Test concurrent session policies"""
        print("\n🔄 Testing Concurrent Sessions...")
        print("=" * 60)

        try:
            # Step 1: Create multiple simultaneous sessions
            concurrent_tokens = []
            session_ids = []

            for i in range(5):
                session_obj = requests.Session()
                token = self.authenticate_user(session_obj)

                if token:
                    concurrent_tokens.append(token)
                    # Extract session identifier if available
                    session_cookies = dict(session_obj.cookies)
                    session_id = hashlib.md5(str(session_cookies).encode()).hexdigest()[
                        :8
                    ]
                    session_ids.append(session_id)
                    self.concurrent_sessions.append(session_obj)

            # Step 2: Test if all concurrent sessions are valid
            valid_sessions = 0
            session_statuses = {}

            for i, (session_obj, token) in enumerate(
                zip(self.concurrent_sessions, concurrent_tokens)
            ):
                try:
                    response = session_obj.get(f"{self.base_url}/api/v1/me", timeout=10)
                    is_valid = response.status_code == 200
                    valid_sessions += 1
                    session_statuses[f"session_{i+1}"] = {
                        "valid": is_valid,
                        "session_id": session_ids[i],
                        "status_code": response.status_code,
                    }
                except Exception as e:
                    session_statuses[f"session_{i+1}"] = {
                        "valid": False,
                        "error": str(e),
                        "session_id": session_ids[i],
                    }

            # Step 3: Test session invalidation from other session
            if len(concurrent_sessions) >= 2:
                # Try to logout from one session
                logout_response = self.concurrent_sessions[0].post(
                    f"{self.base_url}/api/v1/logout", timeout=10
                )

                # Check if other sessions are invalidated
                sessions_invalidated = 0
                for i, session_obj in enumerate(self.concurrent_sessions[1:], 1):
                    try:
                        response = session_obj.get(
                            f"{self.base_url}/api/v1/me", timeout=10
                        )
                        if response.status_code != 200:
                            sessions_invalidated += 1
                            session_statuses[f"session_{i+1}"][
                                "invalidated_by_logout"
                            ] = True
                    except Exception as e:
                        pass

            # Step 4: Test session limit enforcement
            session_limit_reached = False
            if len(concurrent_tokens) >= 3:
                # Try to create one more session
                extra_session = requests.Session()
                extra_token = self.authenticate_user(extra_session)
                if extra_token:
                    # All sessions allowed - no limit
                    session_limit_reached = False
                else:
                    # Session limit enforced
                    session_limit_reached = True

            # Step 5: Test concurrent access from same user
            def concurrent_access_test(session_obj, session_id):
                try:
                    start_time = time.time()
                    response = session_obj.get(f"{self.base_url}/api/v1/me", timeout=10)
                    end_time = time.time()
                    return {
                        "session_id": session_id,
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "success": response.status_code == 200,
                    }
                except Exception as e:
                    return {"session_id": session_id, "error": str(e), "success": False}

            # Run concurrent access test
            concurrent_results = []
            with ThreadPoolExecutor(
                max_workers=len(self.concurrent_sessions)
            ) as executor:
                futures = [
                    executor.submit(concurrent_access_test, session_obj, i)
                    for i, session_obj in enumerate(self.concurrent_sessions)
                ]

                for future in as_completed(futures):
                    concurrent_results.append(future.result())

            # Analyze results
            vulnerabilities = []
            recommendations = []
            risk_level = "LOW"

            # Check session limit policies
            if len(concurrent_tokens) > 3 and not session_limit_reached:
                vulnerabilities.append("No apparent limit on concurrent sessions")
                risk_level = "MEDIUM"
                recommendations.append(
                    "Consider implementing concurrent session limits"
                )

            # Check session isolation
            failed_sessions = len(
                [r for r in concurrent_results if not r.get("success", False)]
            )
            if failed_sessions > 0:
                vulnerabilities.append(f"{failed_sessions} concurrent sessions failed")
                risk_level = "HIGH"
                recommendations.append(
                    "Investigate concurrent session stability issues"
                )

            # Check logout invalidation
            sessions_invalidated = sum(
                1
                for s in session_statuses.values()
                if s.get("invalidated_by_logout", False)
            )
            if sessions_invalidated == 0 and logout_response.status_code == 200:
                vulnerabilities.append("Logout may not invalidate other sessions")
                risk_level = "MEDIUM"
                recommendations.append("Implement session invalidation on logout")

            # Add general recommendations
            if not vulnerabilities:
                recommendations.extend(
                    [
                        "Concurrent session management appears secure",
                        "Consider implementing session limit notifications",
                        "Monitor for unusual concurrent access patterns",
                    ]
                )

            return SessionTestResult(
                test_name="Concurrent Sessions Test",
                vulnerability_found=len(vulnerabilities) > 0,
                risk_level=risk_level,
                details={
                    "concurrent_sessions_created": len(concurrent_tokens),
                    "valid_sessions": valid_sessions,
                    "session_statuses": session_statuses,
                    "concurrent_access_results": concurrent_results,
                    "session_limit_enforced": session_limit_reached,
                    "vulnerabilities_found": vulnerabilities,
                },
                recommendations=recommendations,
                evidence=f"Concurrent sessions: {valid_sessions}/{len(concurrent_tokens)}",
            )

        except Exception as e:
            return SessionTestResult(
                test_name="Concurrent Sessions Test",
                vulnerability_found=True,
                risk_level="MEDIUM",
                details={"error": str(e)},
                recommendations=[
                    "Concurrent session test failed - manual review recommended"
                ],
                evidence=str(e),
            )

    def test_token_rotation(self) -> SessionTestResult:
        """Test session token rotation after privilege changes"""
        print("\n🔄 Testing Token Rotation...")
        print("=" * 60)

        try:
            # Step 1: Authenticate and get initial token
            initial_token = self.authenticate_user()

            if not initial_token:
                return SessionTestResult(
                    test_name="Token Rotation Test",
                    vulnerability_found=True,
                    risk_level="HIGH",
                    details={"authentication_failed": True},
                    recommendations=["Authentication system not working properly"],
                    evidence="Could not authenticate test user",
                )

            # Step 2: Record initial token details
            token_parts = initial_token.split(".")
            token_analysis = {
                "has_header": len(token_parts) >= 1,
                "has_payload": len(token_parts) >= 2,
                "has_signature": len(token_parts) >= 3,
                "header_length": len(token_parts[0]) if len(token_parts) >= 1 else 0,
                "payload_length": len(token_parts[1]) if len(token_parts) >= 2 else 0,
            }

            # Step 3: Test token refresh mechanism
            refresh_session = requests.Session()
            refresh_session.headers.update({"Authorization": f"Bearer {initial_token}"})

            refresh_response = refresh_session.post(
                f"{self.base_url}/api/v1/refresh", timeout=10
            )
            refresh_works = refresh_response.status_code == 200

            new_token = None
            if refresh_works:
                refresh_data = refresh_response.json()
                new_token = refresh_data.get("access_token")

            # Step 4: Test token rotation after privilege change
            # Simulate privilege change by updating user profile
            profile_update_data = {
                "first_name": "Updated",
                "last_name": "User",
                "role": "admin",  # Try to escalate privileges
            }

            update_response = self.session.put(
                f"{self.base_url}/api/v1/me", json=profile_update_data, timeout=10
            )

            # Check if token changed after update
            post_update_headers = dict(self.session.headers)
            token_changed_after_update = False

            # Step 5: Test old token invalidation
            old_token_session = requests.Session()
            old_token_session.headers.update(
                {"Authorization": f"Bearer {initial_token}"}
            )

            old_token_response = old_token_session.get(
                f"{self.base_url}/api/v1/me", timeout=10
            )
            old_token_valid = old_token_response.status_code == 200

            # Step 6: Test token expiration handling
            # Create a fake expired token
            expired_token_parts = (
                token_parts.copy() if len(token_parts) >= 3 else ["", "", ""]
            )
            if len(expired_token_parts) >= 2:
                # Create expired payload
                import base64
                import json

                try:
                    # Decode and modify payload to set expiration in the past
                    payload_data = json.loads(
                        base64.urlsafe_b64decode(expired_token_parts[1] + "==").decode()
                    )
                    payload_data["exp"] = int(time.time()) - 3600  # Expired 1 hour ago

                    expired_payload = (
                        base64.urlsafe_b64encode(json.dumps(payload_data).encode())
                        .decode()
                        .rstrip("=")
                    )
                    expired_token = f"{expired_token_parts[0]}.{expired_payload}.{expired_token_parts[2]}"

                    expired_session = requests.Session()
                    expired_session.headers.update(
                        {"Authorization": f"Bearer {expired_token}"}
                    )

                    expired_response = expired_session.get(
                        f"{self.base_url}/api/v1/me", timeout=10
                    )
                    token_properly_expired = expired_response.status_code != 200
                except Exception as e:
                    token_properly_expired = False
                    expired_token = None
            else:
                token_properly_expired = False
                expired_token = None

            # Analyze results
            vulnerabilities = []
            recommendations = []
            risk_level = "LOW"

            if not refresh_works:
                vulnerabilities.append("Token refresh mechanism not working")
                risk_level = "HIGH"
                recommendations.append("Implement token refresh mechanism")

            if old_token_valid and new_token:
                vulnerabilities.append("Old token not invalidated after refresh")
                risk_level = "HIGH"
                recommendations.append("Invalidate old tokens when issuing new ones")

            if not token_properly_expired and expired_token:
                vulnerabilities.append("Expired token acceptance")
                risk_level = "CRITICAL"
                recommendations.append("Implement proper token expiration validation")

            # Check for token uniqueness
            if new_token and new_token == initial_token:
                vulnerabilities.append("Token does not change after refresh")
                risk_level = "MEDIUM"
                recommendations.append("Generate new tokens on refresh")

            if not vulnerabilities:
                recommendations.extend(
                    [
                        "Token rotation mechanisms appear secure",
                        "Consider implementing short-lived tokens with refresh",
                        "Monitor for token reuse patterns",
                    ]
                )

            return SessionTestResult(
                test_name="Token Rotation Test",
                vulnerability_found=len(vulnerabilities) > 0,
                risk_level=risk_level,
                details={
                    "initial_token_analysis": token_analysis,
                    "refresh_works": refresh_works,
                    "new_token_generated": new_token is not None,
                    "token_changed_after_refresh": (
                        new_token != initial_token if new_token else False
                    ),
                    "old_token_still_valid": old_token_valid,
                    "token_properly_expired": token_properly_expired,
                    "profile_update_status": update_response.status_code,
                    "vulnerabilities_found": vulnerabilities,
                },
                recommendations=recommendations,
                evidence=f"Refresh works: {refresh_works}, Old token valid: {old_token_valid}",
            )

        except Exception as e:
            return SessionTestResult(
                test_name="Token Rotation Test",
                vulnerability_found=True,
                risk_level="MEDIUM",
                details={"error": str(e)},
                recommendations=[
                    "Token rotation test failed - manual review recommended"
                ],
                evidence=str(e),
            )

    def test_session_store_leakage(self) -> SessionTestResult:
        """Test session store information leakage"""
        print("\n💾 Testing Session Store Leakage...")
        print("=" * 60)

        try:
            # Step 1: Check for session information in responses
            auth_response = self.session.get(f"{self.base_url}/api/v1/me", timeout=10)

            # Analyze response for session information leakage
            response_text = auth_response.text
            response_headers = dict(auth_response.headers)

            leaked_info = []

            # Check for sensitive session data in response
            sensitive_patterns = [
                "session",
                "token",
                "jwt",
                "secret",
                "key",
                "password",
                "sessionid",
                "csrf",
                "auth",
                "credential",
            ]

            for pattern in sensitive_patterns:
                if pattern.lower() in response_text.lower():
                    # Check if it's actually sensitive data
                    if any(x in response_text.lower() for x in [":", "=", '"', "'"]):
                        leaked_info.append(
                            f"Potential {pattern} information in response"
                        )

            # Check response headers for sensitive information
            sensitive_headers = [
                "Set-Cookie",
                "Authorization",
                "X-Session-ID",
                "X-Auth-Token",
            ]
            header_leakage = {}

            for header in sensitive_headers:
                if header in response_headers:
                    header_value = response_headers[header]
                    if (
                        len(header_value) > 50
                    ):  # Long header values might contain sensitive data
                        header_leakage[header] = header_value[:50] + "..."

            # Step 2: Test session cookie attributes
            cookie_security = {}

            for cookie_name, cookie_value in self.session.cookies.items():
                cookie_security[cookie_name] = {
                    "has_secure": False,  # Would need to check actual cookie attributes
                    "has_httponly": False,
                    "has_samesite": False,
                    "value_length": len(cookie_value),
                    "value_prefix": (
                        cookie_value[:10] + "..."
                        if len(cookie_value) > 10
                        else cookie_value
                    ),
                }

            # Step 3: Test error responses for information disclosure
            error_endpoints = [
                "/api/v1/nonexistent",
                "/api/v1/invalid-token",
                "/api/v1/forbidden",
            ]

            error_responses = {}
            for endpoint in error_endpoints:
                try:
                    error_response = self.session.get(
                        f"{self.base_url}{endpoint}", timeout=5
                    )
                    error_responses[endpoint] = {
                        "status_code": error_response.status_code,
                        "response_length": len(error_response.text),
                        "contains_stack_trace": "traceback"
                        in error_response.text.lower(),
                        "contains_session_info": any(
                            p in error_response.text.lower() for p in sensitive_patterns
                        ),
                    }
                except Exception as e:
                    error_responses[endpoint] = {"error": "Request failed"}

            # Step 4: Test session ID predictability
            session_ids = []
            for i in range(5):
                test_session = requests.Session()
                token = self.authenticate_user(test_session)
                if token:
                    # Extract session identifier from token or cookies
                    session_id = hashlib.md5(
                        str(dict(test_session.cookies)).encode()
                    ).hexdigest()[:8]
                    session_ids.append(session_id)

            # Check for predictable patterns
            session_entropy = (
                len(set(session_ids)) / len(session_ids) if session_ids else 0
            )
            session_predictable = session_entropy < 0.8

            # Step 5: Test session storage in URLs
            url_parameters = []
            for url in [self.base_url + "/api/v1/me", self.base_url + "/api/v1/health"]:
                if "session" in url.lower() or "token" in url.lower():
                    url_parameters.append("Session data in URL")

            # Analyze results
            vulnerabilities = []
            recommendations = []
            risk_level = "LOW"

            if leaked_info:
                vulnerabilities.extend(leaked_info)
                risk_level = "MEDIUM"
                recommendations.append(
                    "Remove sensitive session information from API responses"
                )

            if any(
                resp.get("contains_stack_trace", False)
                for resp in error_responses.values()
            ):
                vulnerabilities.append("Error responses contain stack traces")
                risk_level = "HIGH"
                recommendations.append(
                    "Remove detailed error information from responses"
                )

            if session_predictable:
                vulnerabilities.append("Session identifiers may be predictable")
                risk_level = "HIGH"
                recommendations.append("Improve session ID randomness and entropy")

            if url_parameters:
                vulnerabilities.extend(url_parameters)
                risk_level = "MEDIUM"
                recommendations.append("Avoid storing session data in URLs")

            # Check cookie security
            cookie_recommendations = []
            for cookie_name, security_info in cookie_security.items():
                if security_info["value_length"] < 20:
                    cookie_recommendations.append(
                        f"Cookie {cookie_name} may have insufficient entropy"
                    )

            if cookie_recommendations:
                vulnerabilities.extend(cookie_recommendations)
                risk_level = max(risk_level, "MEDIUM")
                recommendations.extend(cookie_recommendations)

            if not vulnerabilities:
                recommendations.extend(
                    [
                        "Session information appears to be properly protected",
                        "Consider implementing additional session monitoring",
                        "Regular session store security reviews recommended",
                    ]
                )

            return SessionTestResult(
                test_name="Session Store Leakage Test",
                vulnerability_found=len(vulnerabilities) > 0,
                risk_level=risk_level,
                details={
                    "response_leakage": leaked_info,
                    "header_leakage": header_leakage,
                    "cookie_security": cookie_security,
                    "error_responses": error_responses,
                    "session_entropy": session_entropy,
                    "session_predictable": session_predictable,
                    "url_parameters": url_parameters,
                    "vulnerabilities_found": vulnerabilities,
                },
                recommendations=recommendations,
                evidence=f"Leakage detected: {len(leaked_info) > 0}, Predictable sessions: {session_predictable}",
            )

        except Exception as e:
            return SessionTestResult(
                test_name="Session Store Leakage Test",
                vulnerability_found=True,
                risk_level="MEDIUM",
                details={"error": str(e)},
                recommendations=[
                    "Session leakage test failed - manual review recommended"
                ],
                evidence=str(e),
            )

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all session security tests"""
        print("🚀 Starting Comprehensive Session Security Test")
        print("=" * 80)

        try:
            # Create test user
            self.create_test_user()

            # Run all session security tests
            tests = [
                self.test_session_fixation(),
                self.test_session_timeout(),
                self.test_concurrent_sessions(),
                self.test_token_rotation(),
                self.test_session_store_leakage(),
            ]

            self.results.extend(tests)

            # Generate report
            total_tests = len(self.results)
            vulnerabilities_found = len(
                [r for r in self.results if r.vulnerability_found]
            )

            # Risk level breakdown
            risk_counts = {}
            for result in self.results:
                risk_counts[result.risk_level] = (
                    risk_counts.get(result.risk_level, 0) + 1
                )

            # Determine overall risk
            overall_risk = "LOW"
            if risk_counts.get("CRITICAL", 0) > 0:
                overall_risk = "CRITICAL"
            elif risk_counts.get("HIGH", 0) > 0:
                overall_risk = "HIGH"
            elif risk_counts.get("MEDIUM", 0) > 0:
                overall_risk = "MEDIUM"

            # Collect all recommendations
            all_recommendations = []
            for result in self.results:
                all_recommendations.extend(result.recommendations)

            # Remove duplicates
            unique_recommendations = list(set(all_recommendations))
            critical_recommendations = [
                r
                for r in unique_recommendations
                if any(x in r.lower() for x in ["critical", "immediate", "urgent"])
            ]

            print("\n" + "=" * 80)
            print("📊 Session Security Test Results")
            print("=" * 80)

            print(f"🎯 Overall Risk Level: {overall_risk}")
            print(f"📋 Total Tests: {total_tests}")
            print(f"🚨 Vulnerabilities Found: {vulnerabilities_found}")

            print(f"\n📈 Risk Level Breakdown:")
            for risk_level, count in risk_counts.items():
                print(f"   {risk_level}: {count}")

            print(f"\n🔍 Test Results:")
            for result in self.results:
                status_icon = "🚨" if result.vulnerability_found else "✅"
                print(f"   {status_icon} {result.test_name}: {result.risk_level}")

            if critical_recommendations:
                print(f"\n🚨 Critical Recommendations:")
                for i, rec in enumerate(critical_recommendations, 1):
                    print(f"   {i}. {rec}")

            # Save detailed report
            report_data = {
                "scan_timestamp": datetime.now().isoformat(),
                "target_url": self.base_url,
                "overall_risk_level": overall_risk,
                "statistics": {
                    "total_tests": total_tests,
                    "vulnerabilities_found": vulnerabilities_found,
                    "risk_level_breakdown": risk_counts,
                },
                "test_results": [
                    {
                        "test_name": result.test_name,
                        "vulnerability_found": result.vulnerability_found,
                        "risk_level": result.risk_level,
                        "details": result.details,
                        "recommendations": result.recommendations,
                        "evidence": result.evidence,
                    }
                    for result in self.results
                ],
                "critical_recommendations": critical_recommendations,
                "all_recommendations": unique_recommendations,
            }

            report_file = f"session_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2)

            print(f"\n📄 Detailed report saved: {report_file}")

            return report_data

        finally:
            # Cleanup sessions
            self.session.close()
            for session_obj in self.concurrent_sessions:
                session_obj.close()


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Session Security Tester")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Target base URL"
    )
    parser.add_argument(
        "--test",
        choices=["fixation", "timeout", "concurrent", "rotation", "leakage"],
        help="Run specific test",
    )

    args = parser.parse_args()

    tester = SessionSecurityTester(args.url)

    if args.test == "fixation":
        result = tester.test_session_fixation()
        tester.results.append(result)
    elif args.test == "timeout":
        result = tester.test_session_timeout()
        tester.results.append(result)
    elif args.test == "concurrent":
        result = tester.test_concurrent_sessions()
        tester.results.append(result)
    elif args.test == "rotation":
        result = tester.test_token_rotation()
        tester.results.append(result)
    elif args.test == "leakage":
        result = tester.test_session_store_leakage()
        tester.results.append(result)
    else:
        # Run comprehensive test
        report = tester.run_comprehensive_test()

        # Exit with appropriate code based on findings
        if report["overall_risk_level"] in ["CRITICAL", "HIGH"]:
            sys.exit(1)
        elif report["overall_risk_level"] == "MEDIUM":
            sys.exit(2)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
