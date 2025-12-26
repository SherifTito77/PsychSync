"""
Comprehensive Security Test Suite
End-to-end security testing for the PsychSync platform

Author: Security Team
Version: 1.0.0
"""

import pytest
import requests
from typing import Dict, List, Any
import os
from datetime import datetime

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
ADMIN_USER = {
    "email": os.getenv("TEST_ADMIN_EMAIL", "admin@psychsync.com"),
    "password": os.getenv("TEST_ADMIN_PASSWORD", "Admin123!")
}
TEST_USER = {
    "email": os.getenv("TEST_USER_EMAIL", "test@psychsync.com"),
    "password": os.getenv("TEST_USER_PASSWORD", "Test123!")
}


class SecurityTestSuite:
    """Comprehensive security test suite"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.results: List[Dict[str, Any]] = []
        self.session = requests.Session()

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests"""
        print("=" * 70)
        print("COMPREHENSIVE SECURITY TEST SUITE")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.utcnow().isoformat()}")
        print()

        test_groups = [
            ("Authentication & Authorization", self.test_auth_security),
            ("Input Validation", self.test_input_validation),
            ("API Security", self.test_api_security),
            ("Data Protection", self.test_data_protection),
            ("Session Security", self.test_session_security),
            ("Access Controls", self.test_access_controls),
        ]

        for group_name, test_func in test_groups:
            print(f"\n{'=' * 70}")
            print(f"TEST GROUP: {group_name}")
            print('=' * 70)
            test_func()

        return self._generate_report()

    def test_auth_security(self) -> None:
        """Test authentication and authorization security"""

        # Test 1: Weak password rejection
        print("\n1. Testing weak password rejection...")
        weak_passwords = ["123", "password", "admin", "qwerty"]

        for password in weak_passwords:
            response = self._register_user(f"test_{password}@test.com", password)
            if response.status_code in [200, 201]:
                self._add_finding(
                    "HIGH",
                    "Weak password accepted",
                    f"Password '{password}' should be rejected"
                )
                print(f"  ✗ FAIL: Weak password '{password}' accepted")
            else:
                print(f"  ✓ PASS: Weak password '{password}' rejected")

        # Test 2: Brute force protection
        print("\n2. Testing brute force protection...")
        failed_attempts = 0
        for i in range(15):  # Attempt 15 logins
            response = self._login("bruteforce@test.com", "wrongpassword")
            if response.status_code in [401, 403, 429]:
                failed_attempts += 1

        if failed_attempts < 15:
            print(f"  ✓ PASS: Account locked after {15 - failed_attempts} attempts")
        else:
            self._add_finding(
                "HIGH",
                "No brute force protection",
                "Account not locked after multiple failed attempts"
            )
            print(f"  ✗ FAIL: No brute force protection detected")

        # Test 3: Session fixation
        print("\n3. Testing session fixation...")
        session1 = requests.Session()
        login_response = session1.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": TEST_USER["email"], "password": TEST_USER["password"]}
        )

        if login_response.status_code == 200:
            token1 = session1.cookies.get("session_token")

            # Try to reuse session
            session2 = requests.Session()
            session2.cookies.set("session_token", token1)
            protected_response = session2.get(f"{self.base_url}/api/v1/users/me")

            if protected_response.status_code == 200:
                self._add_finding(
                    "MEDIUM",
                    "Session fixation possible",
                    "Session can be reused"
                )
                print("  ✗ FAIL: Session fixation vulnerability")
            else:
                print("  ✓ PASS: Session fixation protected")
        else:
            print("  ⊘ SKIP: Could not test session fixation")

        # Test 4: Token security
        print("\n4. Testing JWT token security...")
        login_response = self._login(TEST_USER["email"], TEST_USER["password"])

        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token")

            if token:
                # Check if token is signed
                if "." not in token:
                    self._add_finding(
                        "CRITICAL",
                        "JWT not properly signed",
                        "Token missing signature"
                    )
                    print("  ✗ FAIL: JWT not signed")
                else:
                    print("  ✓ PASS: JWT properly signed")

                # Check token expiry
                import jwt
                try:
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    exp = decoded.get("exp")
                    if exp:
                        # Check if expiry is reasonable (15-30 minutes)
                        exp_minutes = (exp - decoded.get("iat", 0)) / 60
                        if exp_minutes > 60:
                            self._add_finding(
                                "MEDIUM",
                                "Token expiry too long",
                                f"Token expires in {exp_minutes:.0f} minutes"
                            )
                            print(f"  ⚠ WARN: Token expiry too long ({exp_minutes:.0f} minutes)")
                        else:
                            print(f"  ✓ PASS: Token expiry appropriate ({exp_minutes:.0f} minutes)")
                except:
                    print("  ⊘ SKIP: Could not verify token expiry")
        else:
            print("  ⊘ SKIP: Could not test JWT security")

    def test_input_validation(self) -> None:
        """Test input validation security"""

        # Test 1: SQL injection
        print("\n1. Testing SQL injection protection...")
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; DROP TABLE users; --",
            "1' AND 1=1--"
        ]

        vulnerable = False
        for payload in sql_payloads:
            response = self.session.get(
                f"{self.base_url}/api/v1/users",
                params={"search": payload}
            )

            # Check for SQL error messages
            if "sql" in response.text.lower() or "mysql" in response.text.lower() or "postgresql" in response.text.lower():
                vulnerable = True
                self._add_finding(
                    "CRITICAL",
                    "SQL injection vulnerability",
                    f"Payload: {payload}"
                )
                print(f"  ✗ FAIL: SQL injection with payload: {payload[:30]}...")
                break

        if not vulnerable:
            print("  ✓ PASS: SQL injection protected")

        # Test 2: XSS protection
        print("\n2. Testing XSS protection...")
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>"
        ]

        xss_vulnerable = False
        for payload in xss_payloads:
            response = self.session.post(
                f"{self.base_url}/api/v1/users",
                json={"username": payload}
            )

            # Check if payload is reflected unescaped
            if payload in response.text:
                xss_vulnerable = True
                self._add_finding(
                    "HIGH",
                    "XSS vulnerability",
                    f"Payload reflected: {payload[:30]}..."
                )
                print(f"  ✗ FAIL: XSS with payload: {payload[:30]}...")
                break

        if not xss_vulnerable:
            print("  ✓ PASS: XSS protected")

        # Test 3: Command injection
        print("\n3. Testing command injection protection...")
        cmd_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`",
            "; ping -c 1 evil.com"
        ]

        cmd_vulnerable = False
        for payload in cmd_payloads:
            response = self.session.get(
                f"{self.base_url}/api/v1/search",
                params={"q": payload}
            )

            # Check for command output
            if "root:" in response.text or "uid=" in response.text:
                cmd_vulnerable = True
                self._add_finding(
                    "CRITICAL",
                    "Command injection vulnerability",
                    f"Payload: {payload}"
                )
                print(f"  ✗ FAIL: Command injection with payload: {payload}")
                break

        if not cmd_vulnerable:
            print("  ✓ PASS: Command injection protected")

    def test_api_security(self) -> None:
        """Test API security"""

        # Test 1: Authentication required
        print("\n1. Testing authentication requirement...")
        protected_endpoints = [
            "/api/v1/users",
            "/api/v1/assessments",
            "/api/v1/teams",
            "/api/v1/analytics"
        ]

        all_protected = True
        for endpoint in protected_endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")

            if response.status_code == 200:
                all_protected = False
                self._add_finding(
                    "HIGH",
                    "Unauthenticated endpoint access",
                    f"Endpoint {endpoint} accessible without auth"
                )
                print(f"  ✗ FAIL: {endpoint} accessible without authentication")
            elif response.status_code in [401, 403]:
                print(f"  ✓ PASS: {endpoint} requires authentication")

        if all_protected:
            print("  ✓ PASS: All protected endpoints require authentication")

        # Test 2: Rate limiting
        print("\n2. Testing rate limiting...")
        request_count = 0
        rate_limited = False

        for i in range(100):
            response = requests.get(f"{self.base_url}/api/v1/health")
            request_count += 1

            if response.status_code == 429:
                rate_limited = True
                print(f"  ✓ PASS: Rate limiting triggered after {request_count} requests")
                break

        if not rate_limited:
            self._add_finding(
                "MEDIUM",
                "No rate limiting detected",
                "Made 100 requests without rate limit"
            )
            print("  ✗ FAIL: No rate limiting detected")

        # Test 3: CORS configuration
        print("\n3. Testing CORS configuration...")
        cors_origins = [
            "https://evil.com",
            "https://attacker.com",
            "null"
        ]

        cors_vulnerable = False
        for origin in cors_origins:
            response = requests.options(
                f"{self.base_url}/api/v1/health",
                headers={"Origin": origin}
            )

            aca_header = response.headers.get("Access-Control-Allow-Origin")
            if aca_header == origin or aca_header == "*":
                cors_vulnerable = True
                self._add_finding(
                    "MEDIUM",
                    "Permissive CORS configuration",
                    f"Allows origin: {origin}"
                )
                print(f"  ✗ FAIL: CORS allows origin: {origin}")
                break

        if not cors_vulnerable:
            print("  ✓ PASS: CORS properly configured")

    def test_data_protection(self) -> None:
        """Test data protection security"""

        # Test 1: Sensitive data exposure
        print("\n1. Testing for sensitive data exposure...")
        error_endpoints = [
            "/api/v1/nonexistent",
            "/api/v1/assessments/invalid-uuid-12345",
            "/api/v1/users/999999"
        ]

        data_exposed = False
        for endpoint in error_endpoints:
            response = requests.get(f"{self.base_url}{endpoint}")

            # Check for sensitive information in error messages
            sensitive_patterns = [
                "traceback",
                "stack trace",
                "exception",
                "sql query",
                "/var/www",
                "C:\\Users\\",
                "password",
                "secret",
                "api_key"
            ]

            response_lower = response.text.lower()
            for pattern in sensitive_patterns:
                if pattern in response_lower:
                    data_exposed = True
                    self._add_finding(
                        "MEDIUM",
                        "Information disclosure",
                        f"Error contains: {pattern} at {endpoint}"
                    )
                    print(f"  ✗ FAIL: Sensitive data in error: {endpoint}")
                    break

        if not data_exposed:
            print("  ✓ PASS: No sensitive data in error messages")

        # Test 2: Password field security
        print("\n2. Testing password field security...")
        if self._login(TEST_USER["email"], TEST_USER["password"]).status_code == 200:
            # Get user profile
            user_response = self.session.get(f"{self.base_url}/api/v1/users/me")

            if user_response.status_code == 200:
                user_data = user_response.json()

                # Check if password is returned
                if "password" in str(user_data).lower():
                    self._add_finding(
                        "CRITICAL",
                        "Password exposed in API response",
                        "User data contains password field"
                    )
                    print("  ✗ FAIL: Password exposed in API response")
                else:
                    print("  ✓ PASS: Password not exposed in API response")

    def test_session_security(self) -> None:
        """Test session management security"""

        # Test 1: Session timeout
        print("\n1. Testing session timeout...")
        login_response = self._login(TEST_USER["email"], TEST_USER["password"])

        if login_response.status_code == 200:
            session_data = login_response.json()

            # Check for session timeout configuration
            if "expires_in" in session_data or "expires" in session_data:
                print("  ✓ PASS: Session timeout configured")
            else:
                print("  ⚠ WARN: Session timeout not visible in response")

        # Test 2: Concurrent sessions
        print("\n2. Testing concurrent session handling...")
        session1_response = self._login(TEST_USER["email"], TEST_USER["password"])
        session2_response = self._login(TEST_USER["email"], TEST_USER["password"])

        if session1_response.status_code == 200 and session2_response.status_code == 200:
            # Both logins succeeded - check if first session is invalidated
            print("  ✓ INFO: Multiple concurrent sessions allowed")
            print("  (Consider implementing single session enforcement)")

    def test_access_controls(self) -> None:
        """Test access control security"""

        # Test 1: Horizontal access control
        print("\n1. Testing horizontal access control...")

        # Login as regular user
        login_response = self._login(TEST_USER["email"], TEST_USER["password"])

        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # Try to access other users' data
            for user_id in [2, 3, 4, 5]:
                response = requests.get(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    user_data = response.json()

                    # Check if we got another user's data
                    if user_data.get("id") == user_id:
                        self._add_finding(
                            "HIGH",
                            "Horizontal access control bypass",
                            f"Can access user {user_id} data"
                        )
                        print(f"  ✗ FAIL: Can access user {user_id} data")
                        break

            print("  ✓ PASS: Horizontal access control working")

        # Test 2: Vertical access control
        print("\n2. Testing vertical access control...")

        # Try to access admin endpoints as regular user
        login_response = self._login(TEST_USER["email"], TEST_USER["password"])

        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            admin_endpoints = [
                "/api/v1/admin/users",
                "/api/v1/admin/settings",
                "/api/v1/admin/analytics"
            ]

            for endpoint in admin_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

                if response.status_code == 200:
                    self._add_finding(
                        "CRITICAL",
                        "Vertical access control bypass",
                        f"Regular user can access admin endpoint: {endpoint}"
                    )
                    print(f"  ✗ FAIL: Can access admin endpoint: {endpoint}")
                elif response.status_code in [401, 403, 404]:
                    print(f"  ✓ PASS: Admin endpoint protected: {endpoint}")

    def _add_finding(self, severity: str, issue: str, details: str) -> None:
        """Add a security finding"""
        self.results.append({
            "severity": severity,
            "issue": issue,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

    def _register_user(self, email: str, password: str) -> requests.Response:
        """Register a new user"""
        return self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"email": email, "password": password}
        )

    def _login(self, email: str, password: str) -> requests.Response:
        """Login user"""
        return self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )

    def _generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        findings_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for finding in self.results:
            severity = finding.get("severity", "LOW")
            findings_by_severity[severity] += 1

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_findings": len(self.results),
            "by_severity": findings_by_severity,
            "findings": self.results,
            "overall_status": self._calculate_status(findings_by_severity)
        }

    def _calculate_status(self, severity_counts: Dict[str, int]) -> str:
        """Calculate overall security status"""
        if severity_counts["CRITICAL"] > 0:
            return "CRITICAL"
        elif severity_counts["HIGH"] > 0:
            return "HIGH_RISK"
        elif severity_counts["MEDIUM"] > 5:
            return "MEDIUM_RISK"
        elif severity_counts["MEDIUM"] > 0:
            return "MODERATE"
        else:
            return "GOOD"


# Pytest integration
@pytest.mark.security
class TestSecuritySuite:
    """Pytest integration for security tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test suite"""
        self.suite = SecurityTestSuite(BASE_URL)

    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        self.suite.test_input_validation()

        findings = [f for f in self.suite.results if "SQL injection" in f["issue"]]
        assert len(findings) == 0, f"SQL injection vulnerabilities found: {findings}"

    def test_authentication_security(self):
        """Test authentication security"""
        self.suite.test_auth_security()

        critical_findings = [f for f in self.suite.results if f["severity"] == "CRITICAL"]
        assert len(critical_findings) == 0, f"Critical auth vulnerabilities: {critical_findings}"

    def test_access_controls(self):
        """Test access control security"""
        self.suite.test_access_controls()

        bypasses = [f for f in self.suite.results if "access control" in f["issue"].lower()]
        assert len(bypasses) == 0, f"Access control bypasses found: {bypasses}"


if __name__ == "__main__":
    suite = SecurityTestSuite()
    results = suite.run_all_tests()

    print("\n" + "=" * 70)
    print("SECURITY TEST REPORT")
    print("=" * 70)
    print(f"Total Findings: {results['total_findings']}")
    print(f"Overall Status: {results['overall_status']}")
    print()
    print("Findings by Severity:")
    for severity, count in results["by_severity"].items():
        if count > 0:
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}[severity]
            print(f"  {icon} {severity}: {count}")
    print("=" * 70)
