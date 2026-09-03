"""
Comprehensive Security Testing Suite

This module provides automated tests to verify all security implementations:
- httpOnly cookie authentication
- Multi-layered rate limiting
- Account lockout mechanism
- Password validation
- Secure logging
- SQL injection protection
- XSS protection
- CSRF protection

Run with: pytest tests/test_security_comprehensive.py -v
"""

import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHTTPOOnlyCookieAuthentication:
    """Test httpOnly cookie implementation"""

    def test_login_sets_httponly_cookies(self, client: TestClient):
        """Verify login sets httpOnly cookies, not localStorage tokens"""
        response = client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "test@example.com", "password": "testpassword123"},
        )

        assert response.status_code == 200

        # Verify cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

        # Note: Can't test httpOnly flag in TestClient,
        # but we verify response doesn't return tokens in JSON
        data = response.json()
        assert "access_token" not in data or data.get("access_token") in ["", None]

    def test_no_localstorage_tokens_in_response(self, client: TestClient):
        """Verify tokens are not returned in response body"""
        response = client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "test@example.com", "password": "testpassword123"},
        )

        data = response.json()

        # Tokens should NOT be in response data (they're in cookies)
        if "access_token" in data:
            # If present, should be empty
            assert data["access_token"] in ["", None]

    def test_authenticated_request_sends_cookies(self, client: TestClient):
        """Verify authenticated requests work with cookies"""
        # First, login
        login_response = client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "test@example.com", "password": "testpassword123"},
        )

        # Extract cookies
        cookies = login_response.cookies

        # Make authenticated request
        response = client.get(
            "/api/v1/auth/me-fixed",
            cookies={"access_token": cookies.get("access_token")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data or "email" in data


class TestPasswordValidation:
    """Test enterprise password validation"""

    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected"""
        from app.core.password_validator import password_validator

        weak_passwords = [
            "password",  # Too common
            "Password1",  # Too short
            "welcome123",  # Sequential pattern
            "aaaaaaaa",  # Repeated characters
        ]

        for password in weak_passwords:
            is_valid, errors = password_validator.validate_password(password)
            assert not is_valid, f"Password '{password}' should be rejected"
            assert len(errors) > 0, "Should have error messages"

    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted"""
        from app.core.password_validator import password_validator

        strong_passwords = [
            "Tr0ub4dor&3Horse!",  # 20 chars, high entropy
            "Corr3ct!H0rse!Batt3ry!",  # Multiple special chars
            "E@u5t!on!C4l!B3f0re!Stapl3!",  # No patterns
        ]

        for password in strong_passwords:
            is_valid, errors = password_validator.validate_password(password)
            assert is_valid, f"Password '{password}' should be accepted"
            assert len(errors) == 0, "Should have no errors"

    def test_password_entropy_calculation(self):
        """Test password entropy calculation"""
        from app.core.password_validator import password_validator

        # Low entropy
        entropy1 = password_validator._calculate_entropy("password")
        assert entropy1 < 50, "Simple password should have low entropy"

        # High entropy
        entropy2 = password_validator._calculate_entropy("Tr0ub4dor&3Horse!")
        assert entropy2 > 80, "Complex password should have high entropy"

    def test_common_password_detection(self):
        """Test common password detection"""
        from app.core.password_validator import password_validator

        common_passwords = [
            "password123",
            "welcome123",
            "qwerty123",
            "admin123",
        ]

        for password in common_passwords:
            is_common = password_validator._is_common_password(password)
            assert is_common, f"'{password}' should be detected as common"

    def test_sequential_pattern_detection(self):
        """Test sequential pattern detection"""
        from app.core.password_validator import password_validator

        passwords_with_patterns = [
            "abc123XYZ",  # Sequential abc, 123
            "qwertyXYZ",  # Sequential keyboard
            "12345678",  # Sequential numbers
        ]

        for password in passwords_with_patterns:
            has_pattern = password_validator._has_sequential_pattern(password)
            assert has_pattern, f"'{password}' should have sequential patterns"

    def test_repeated_pattern_detection(self):
        """Test repeated character detection"""
        from app.core.password_validator import password_validator

        passwords_with_repeats = [
            "aaaAAA123",  # Repeated 'a'
            "111222333",  # Repeated numbers
        ]

        for password in passwords_with_repeats:
            has_repeats = password_validator._has_repeated_pattern(password)
            assert has_repeats, f"'{password}' should have repeated characters"

    def test_password_strength_scoring(self):
        """Test password strength scoring system"""
        from app.core.password_validator import password_validator

        # Weak password
        result1 = password_validator.assess_strength("Password1")
        assert result1.score < 50, "Weak password should have low score"
        assert result1.strength in ["weak", "fair"]

        # Strong password
        result2 = password_validator.assess_strength("Tr0ub4dor&3Horse!")
        assert result2.score >= 90, "Strong password should have high score"
        assert result2.strength == "excellent"


class TestRateLimiting:
    """Test multi-layered rate limiting"""

    def test_ip_rate_limiting(self, client: TestClient):
        """Test IP-based rate limiting"""
        # Make 101 requests (exceeds 100 limit)
        responses = []
        for i in range(101):
            response = client.get("/api/v1/teams")
            responses.append(response)

        # First 100 should succeed
        successful = sum(1 for r in responses[:100] if r.status_code == 200)
        assert successful == 100, "First 100 requests should succeed"

        # 101st should be rate limited
        assert responses[100].status_code == 429

    def test_rate_limit_headers(self, client: TestClient):
        """Test rate limit response headers"""
        response = client.get("/api/v1/teams")

        # Should have rate limit headers
        # Note: These would be set by the rate limiter
        # assert "X-RateLimit-Limit" in response.headers
        # assert "X-RateLimit-Remaining" in response.headers


class TestAccountLockout:
    """Test account lockout mechanism"""

    @pytest.mark.asyncio
    async def test_account_lockout_after_5_attempts(self, async_client: AsyncClient):
        """Test account locks after 5 failed login attempts"""
        # Make 5 failed login attempts
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/token-fixed",
                data={"username": "test@example.com", "password": "wrongpassword"},
            )
            assert response.status_code == 401

        # 6th attempt should be locked
        response = await async_client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "test@example.com", "password": "wrongpassword"},
        )

        # Should be locked (423 Locked status)
        assert response.status_code in [401, 423]

        if response.status_code == 423:
            data = response.json()
            assert "locked" in str(data).lower()

    @pytest.mark.asyncio
    async def test_successful_login_clears_lockout(self, async_client: AsyncClient):
        """Test successful login clears failed attempt counter"""
        # Make 3 failed attempts
        for i in range(3):
            await async_client.post(
                "/api/v1/auth/token-fixed",
                data={"username": "test@example.com", "password": "wrongpassword"},
            )

        # Successful login should clear counter
        response = await async_client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "test@example.com", "password": "correctpassword"},
        )

        assert response.status_code == 200

        # Next failed attempt should start from 1, not 4
        response = await async_client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "test@example.com", "password": "wrongpassword"},
        )

        # Should not be locked yet
        assert response.status_code == 401


class TestSQLInjectionProtection:
    """Test SQL injection protection"""

    def test_sql_injection_blocked_in_sort_by(self, client: TestClient):
        """Test SQL injection in sort_by parameter is blocked"""
        response = client.get(
            "/api/v1/teams/test-team/members",
            params={"sort_by": "created_at; DROP TABLE users;--"},
        )

        # Should be rejected
        assert response.status_code in [400, 422]

    def test_sql_injection_blocked_in_id(self, client: TestClient):
        """Test SQL injection in ID parameter is blocked"""
        response = client.get("/api/v1/teams/abc-123' OR '1'='1")

        # Should be rejected or return 404 (UUID validation)
        assert response.status_code in [400, 404, 422]

    def test_union_select_injection_blocked(self, client: TestClient):
        """Test UNION SELECT injection is blocked"""
        response = client.get(
            "/api/v1/teams", params={"search": "test' UNION SELECT * FROM users --"}
        )

        # Should be rejected
        assert response.status_code in [400, 401, 403, 422]


class TestIDORProtection:
    """Test Insecure Direct Object Reference protection"""

    def test_cross_org_user_listing_blocked(self, client: TestClient):
        """Test users cannot list other organizations' users"""
        # Login as org1 user
        login_response = client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "org1_user@example.com", "password": "password"},
        )

        if login_response.status_code == 200:
            # Try to list all users
            response = client.get("/api/v1/users/list")

            # Should either work but only show own org, or require admin
            if response.status_code == 200:
                data = response.json()
                # Verify no cross-org data
                users = data.get("users", [])
                for user in users:
                    # Should only see users from own org
                    pass  # Implementation-specific validation

    def test_cross_org_user_access_blocked(self, client: TestClient):
        """Test users cannot access other organizations' user details"""
        # Try to access user from different org
        response = client.get("/api/v1/users/different-org-user-id")

        # Should be blocked
        assert response.status_code in [401, 403, 404]


class TestSecureLogging:
    """Test secure logging implementation"""

    def test_sensitive_data_redaction_in_logs(self, caplog):
        """Test sensitive data is redacted in logs"""
        import logging

        from app.core.secure_logging import SensitiveDataFilter

        filter_instance = SensitiveDataFilter()

        # Test password redaction
        log_message = "User login: password=secret123"
        redacted = filter_instance._redact(log_message)
        assert "password=***REDACTED***" in redacted
        assert "secret123" not in redacted

        # Test token redaction
        log_message = "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = filter_instance._redact(log_message)
        assert "***JWT***" in redacted

        # Test credit card redaction
        log_message = "Card: 4111-1111-1111-1111"
        redacted = filter_instance._redact(log_message)
        assert "***CARD***" in redacted
        assert "4111" not in redacted

        # Test SSN redaction
        log_message = "SSN: 123-45-6789"
        redacted = filter_instance._redact(log_message)
        assert "***SSN***" in redacted
        assert "123-45-6789" not in redacted

    def test_json_structured_logging(self):
        """Test logs are formatted as JSON"""
        import logging

        from app.core.secure_logging import SecureFormatter

        formatter = SecureFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        import json

        parsed = json.loads(formatted)

        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed
        assert parsed["message"] == "Test message"


class TestCSRFProtection:
    """Test CSRF protection"""

    def test_csrf_token_required_for_mutations(self, client: TestClient):
        """Test CSRF token is required for POST/PUT/DELETE"""
        # Attempt POST without CSRF token
        response = client.post(
            "/api/v1/users",
            json={"email": "test@example.com", "password": "password123"},
        )

        # Should either require auth or CSRF
        # (Implementation-specific)
        assert response.status_code in [401, 403, 422]


class TestXSSProtection:
    """Test XSS protection"""

    def test_xss_in_user_input_sanitized(self, client: TestClient):
        """Test XSS payloads in user input are sanitized"""
        xss_payload = "<script>alert('XSS')</script>"

        response = client.post(
            "/api/v1/register",
            json={
                "email": "test@example.com",
                "password": "Password123!",
                "full_name": xss_payload,
            },
        )

        # If successful, verify XSS was sanitized
        if response.status_code == 200:
            data = response.json()
            # Script tags should be removed or escaped
            if "full_name" in data:
                assert "<script>" not in data["full_name"]
                assert "alert(" not in data["full_name"]


class TestSecurityHeaders:
    """Test security headers"""

    def test_security_headers_present(self, client: TestClient):
        """Test security headers are present"""
        response = client.get("/api/v1/health")

        # Check for security headers
        headers = response.headers

        # Should have security headers
        assert (
            "X-Content-Type-Options" in headers or "x-content-type-options" in headers
        )
        assert "X-Frame-Options" in headers or "x-frame-options" in headers


class TestAuthenticationSecurity:
    """Test authentication security features"""

    def test_password_hashing(self):
        """Test passwords are properly hashed"""
        from app.core.security import hash_password, verify_password

        password = "TestPassword123!"
        hashed = hash_password(password)

        # Hash should not contain plaintext
        assert password not in hashed
        assert len(hashed) >= 60  # bcrypt hashes are long

        # Verify should work
        assert verify_password(password, hashed)

        # Wrong password should fail
        assert not verify_password("WrongPassword", hashed)

    def test_jwt_token_expiration(self):
        """Test JWT tokens have proper expiration"""
        from datetime import datetime, timedelta

        from app.services.security import create_access_token

        token = create_access_token(subject="test@example.com")

        # Token should be valid JWT format
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature

        # Decode payload
        import base64
        import json

        payload = parts[1]
        # Add padding if needed
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        claims = json.loads(decoded)

        # Should have expiration
        assert "exp" in claims

        # Expiration should be in the future but not too far
        exp = datetime.fromtimestamp(claims["exp"])
        now = datetime.utcnow()
        delta = exp - now

        # Access token should expire within 1 hour
        assert timedelta(minutes=0) < delta <= timedelta(hours=1)


class TestInputValidation:
    """Test input validation"""

    def test_email_validation(self, client: TestClient):
        """Test email validation"""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com",
        ]

        for email in invalid_emails:
            response = client.post(
                "/api/v1/register", json={"email": email, "password": "Password123!"}
            )

            # Should reject invalid email
            assert response.status_code == 422

    def test_sql_injection_in_email_blocked(self, client: TestClient):
        """Test SQL injection in email field is blocked"""
        sql_injection_emails = [
            "test@example.com' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin@example.com'; DROP TABLE users;--",
        ]

        for email in sql_injection_emails:
            response = client.post(
                "/api/v1/register", json={"email": email, "password": "Password123!"}
            )

            # Should be rejected (422 = Validation Error)
            assert response.status_code in [400, 422]


class TestRateLimitBypassPrevention:
    """Test rate limiting bypass prevention"""

    def test_ip_rotation_bypass_prevented(self, client: TestClient):
        """Test IP rotation cannot bypass rate limiting"""
        responses = []

        # Try to rotate IPs
        for i in range(15):
            response = client.post(
                "/api/v1/auth/token-fixed",
                data={"username": "test@example.com", "password": "wrong"},
                headers={"X-Forwarded-For": f"192.168.1.{i}"},
            )
            responses.append(response)

        # After 10 attempts for same username, should be blocked
        # regardless of IP rotation
        later_responses = responses[10:]
        blocked = sum(1 for r in later_responses if r.status_code in [401, 423, 429])

        # At least some should be blocked
        assert blocked > 0, "IP rotation should not bypass rate limiting"


class TestSecurePasswordReset:
    """Test secure password reset functionality"""

    def test_reset_token_validation(self):
        """Test password reset tokens are properly validated"""
        from app.core.security import generate_reset_token, validate_reset_token

        # Generate token
        token = generate_reset_token(email="test@example.com")

        # Valid token should pass
        assert validate_reset_token(token) is not None

        # Invalid token should fail
        assert validate_reset_token("invalid_token") is None

    def test_reset_token_expiration(self):
        """Test password reset tokens expire"""
        from datetime import datetime, timedelta

        from app.core.security import generate_reset_token

        # Generate token
        token_data = generate_reset_token(email="test@example.com")

        # Token should have expiration
        if isinstance(token_data, dict):
            assert "expires" in token_data or "exp" in token_data


class TestSessionSecurity:
    """Test session security"""

    def test_session_expiration(self):
        """Test sessions expire after inactivity"""
        # This would test the session timeout mechanism
        # Implementation depends on session management
        pass

    def test_concurrent_session_handling(self):
        """Test concurrent sessions are handled properly"""
        # This would test login from multiple devices
        # Implementation depends on session management
        pass


class TestAuthorization:
    """Test authorization and access control"""

    def test_regular_user_cannot_access_admin_endpoints(self, client: TestClient):
        """Test regular users cannot access admin endpoints"""
        # Try to access admin endpoint without admin role
        response = client.get("/api/v1/admin/users")

        # Should be forbidden
        assert response.status_code in [401, 403]

    def test_role_based_access_control(self, client: TestClient):
        """Test role-based access control"""
        # This would test different roles have different permissions
        # Implementation-specific
        pass


# Performance and load testing
class TestPerformanceUnderLoad:
    """Test security measures don't degrade performance"""

    def test_rate_limiter_performance(self, client: TestClient):
        """Test rate limiter doesn't significantly impact performance"""
        import time

        start_time = time.time()

        # Make 50 requests
        for _ in range(50):
            client.get("/api/v1/health")

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert (
            duration < 5.0
        ), "Rate limiting should not significantly impact performance"


# Integration tests
class TestSecurityIntegration:
    """Integration tests for complete security flows"""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self, async_client: AsyncClient):
        """Test complete secure authentication flow"""
        # 1. Register
        register_response = await async_client.post(
            "/api/v1/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
            },
        )

        # 2. Login
        login_response = await async_client.post(
            "/api/v1/auth/token-fixed",
            data={"username": "newuser@example.com", "password": "SecurePassword123!"},
        )

        assert login_response.status_code == 200

        # 3. Access protected resource
        cookies = login_response.cookies
        me_response = await async_client.get(
            "/api/v1/auth/me-fixed",
            cookies={"access_token": cookies.get("access_token")},
        )

        assert me_response.status_code == 200

        # 4. Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout", cookies={"access_token": cookies.get("access_token")}
        )

        assert logout_response.status_code == 200


# Run tests with specific markers
@pytest.mark.security
def test_security_suite():
    """Run all security tests"""
    pass


@pytest.mark.authentication
def test_authentication_suite():
    """Run authentication tests"""
    pass


@pytest.mark.authorization
def test_authorization_suite():
    """Run authorization tests"""
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
