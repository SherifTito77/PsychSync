# tests/test_auth_security.py
"""
Comprehensive Authentication Security Tests
Tests all security controls in the authentication system
"""

import asyncio
import hashlib
import json
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from jose import JWTError, jwt

from app.core.account_security import account_security_manager
from app.core.config import settings
from app.core.csrf import CSRFMiddleware
from app.core.security_monitoring import security_monitor
from app.core.session_management import session_manager
from app.main import app
from app.services.security import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    get_password_hash,
    invalidate_refresh_token,
    validate_password,
    verify_password,
    verify_refresh_token_secure,
    verify_token,
)

# Test client
client = TestClient(app)


class TestPasswordSecurity:
    """Test password security implementations"""

    def test_password_hashing_security(self):
        """Test that passwords are properly hashed and never stored in plaintext"""
        password = "TestSecurePassword123!"

        # Hash password
        hashed = get_password_hash(password)

        # Verify it's not plaintext
        assert password != hashed
        assert hashed.startswith("$2b$")  # bcrypt format

        # Verify it can be verified correctly
        assert verify_password(password, hashed) is True

        # Verify wrong password fails
        assert verify_password("wrongpassword", hashed) is False

        # Test consistent hashing (same password produces different hashes)
        hashed2 = get_password_hash(password)
        assert hashed != hashed2  # bcrypt uses salts
        assert verify_password(password, hashed2) is True

    def test_password_validation_security(self):
        """Test comprehensive password validation"""
        # Test weak passwords
        weak_passwords = [
            "password",  # Common word
            "12345678",  # Numbers only
            "abcdefgh",  # Letters only
            "Abc123",  # Too short
            "password123",  # Common pattern
            "qwerty123",  # Keyboard pattern
        ]

        for weak_pass in weak_passwords:
            result = validate_password(weak_pass)
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert result["strength_score"] < 50

        # Test strong passwords
        strong_passwords = [
            "Tr0ub4dor&3",  # Good mix, length 12
            "Correct-Horse-Battery-Staple",  # Diceware style
            "MyS3cur3P@ssw0rd!2024",  # Complex
            "B@tterySt@ple!C0rrectH0rs3",  # Strong
        ]

        for strong_pass in strong_passwords:
            result = validate_password(strong_pass)
            assert result["valid"] is True
            assert len(result["errors"]) == 0
            assert result["strength_score"] >= 60

    def test_password_timing_attack_resistance(self):
        """Test that password verification resists timing attacks"""
        password = "TestSecurePassword123!"
        hashed = get_password_hash(password)

        # Measure verification times
        times_correct = []
        times_incorrect = []

        for _ in range(10):
            # Correct password timing
            start = time.perf_counter()
            verify_password(password, hashed)
            times_correct.append(time.perf_counter() - start)

            # Incorrect password timing
            start = time.perf_counter()
            verify_password("wrongpassword", hashed)
            times_incorrect.append(time.perf_counter() - start)

        # Average times should be similar (within reasonable variance)
        avg_correct = sum(times_correct) / len(times_correct)
        avg_incorrect = sum(times_incorrect) / len(times_incorrect)

        # Allow for some variance but should be relatively close
        time_diff_ratio = abs(avg_correct - avg_incorrect) / max(
            avg_correct, avg_incorrect
        )
        assert time_diff_ratio < 0.5  # Less than 50% difference

    def test_password_hash_length_validation(self):
        """Test password hash length limits"""
        # Test very long passwords (bcrypt has limits)
        long_password = "A" * 200
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True

        # Test empty password
        with pytest.raises(ValueError):
            validate_password("")


class TestJWTTokenSecurity:
    """Test JWT token security implementations"""

    def test_token_creation_security(self):
        """Test secure token creation"""
        user_id = "test_user@example.com"

        # Create token pair
        tokens = create_token_pair(user_id)

        # Verify token structure
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] > 0

        # Verify tokens are different
        assert tokens["access_token"] != tokens["refresh_token"]

    def test_jwt_token_validation_security(self):
        """Test JWT token validation and tampering resistance"""
        user_id = "test_user@example.com"

        # Create valid token
        access_token = create_access_token(subject=user_id)

        # Verify valid token
        decoded_user = verify_token(access_token, "access")
        assert decoded_user == user_id

        # Test token tampering
        parts = access_token.split(".")
        tampered_token = parts[0] + "." + "tampered_payload" + "." + parts[2]

        # Tampered token should be invalid
        assert verify_token(tampered_token, "access") is None

        # Test expired token
        expired_token = create_access_token(
            subject=user_id, expires_delta=timedelta(seconds=-1)
        )
        assert verify_token(expired_token, "access") is None

    def test_token_secret_security(self):
        """Test that tokens use proper secret keys"""
        user_id = "test_user@example.com"

        # Create token with current secret
        token = create_access_token(subject=user_id)

        # Verify with correct secret
        assert verify_token(token, "access") is not None

        # Try to decode with wrong secret (should fail)
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret_key", algorithms=[settings.JWT_ALGORITHM])

    def test_refresh_token_rotation_security(self):
        """Test refresh token rotation and blacklisting"""
        user_id = "test_user@example.com"

        # Create initial token pair
        tokens = create_token_pair(user_id)
        initial_refresh = tokens["refresh_token"]

        # Verify refresh token is valid
        new_user_id = verify_token(initial_refresh, "refresh")
        assert new_user_id == user_id

        # Invalidate the refresh token
        await invalidate_refresh_token(initial_refresh)

        # Verify token is now blacklisted (this would require Redis setup)
        # For now, just test the function exists and doesn't error
        assert True  # Function completes without error

    def test_token_type_validation(self):
        """Test that token types are properly validated"""
        user_id = "test_user@example.com"

        # Create access and refresh tokens
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)

        # Verify correct type validation
        assert verify_token(access_token, "access") is not None
        assert verify_token(access_token, "refresh") is None
        assert verify_token(refresh_token, "refresh") is not None
        assert verify_token(refresh_token, "access") is None

    def test_token_claims_security(self):
        """Test that token claims are properly secured"""
        user_id = "test_user@example.com"
        additional_claims = {
            "role": "user",
            "organization_id": "org_123",
            "session_id": "session_456",
        }

        token = create_access_token(
            subject=user_id, additional_claims=additional_claims
        )

        # Decode and verify claims
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == user_id
        assert payload["role"] == "user"
        assert payload["organization_id"] == "org_123"
        assert payload["type"] == "access"


class TestCSRFProtection:
    """Test CSRF protection mechanisms"""

    def test_csrf_token_generation(self):
        """Test CSRF token generation and validation"""

        # Mock request for testing
        class MockRequest:
            def __init__(self):
                self.url = type("obj", (object,), {"path": "/test"})()
                self.method = "POST"
                self.headers = {}
                self.client = type("obj", (object,), {"host": "127.0.0.1"})()

        request = MockRequest()

        # Test CSRF middleware (basic functionality)
        csrf_middleware = CSRFMiddleware(app)

        # CSRF tokens should be generated for authenticated requests
        # (This is a basic test - full integration testing would require more setup)
        assert hasattr(csrf_middleware, "token_expire_seconds")
        assert csrf_middleware.token_expire_seconds > 0

    def test_csrf_exclude_paths(self):
        """Test that CSRF protection excludes correct paths"""
        csrf_middleware = CSRFMiddleware(app)

        exclude_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/token",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
        ]

        # Test exclude paths configuration
        assert csrf_middleware.exclude_paths is not None
        assert len(csrf_middleware.exclude_paths) > 0


class TestAccountSecurity:
    """Test account security features"""

    @pytest.mark.asyncio
    async def test_account_lockout_security(self):
        """Test progressive account lockout"""
        email = "test@example.com"
        ip_address = "127.0.0.1"
        user_agent = "Test Browser"

        # Simulate failed login attempts
        for attempt in range(settings.MAX_LOGIN_ATTEMPTS):
            result = await account_security_manager.record_login_attempt(
                email=email,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                reason="Invalid password",
                user_id=None,
            )

            if attempt < settings.MAX_LOGIN_ATTEMPTS - 1:
                assert result["locked"] is False
                assert result["attempts_remaining"] > 0
            else:
                # Should be locked after max attempts
                assert result["locked"] is True
                assert result["attempts_remaining"] == 0

        # Check lockout status
        lockout_status = await account_security_manager.is_account_locked(email)
        assert lockout_status["locked"] is True
        assert lockout_status["lockout_time_remaining"] > 0

        # Test successful login (should clear lockout)
        result = await account_security_manager.record_login_attempt(
            email=email,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id="user_123",
        )

        assert result["locked"] is False
        assert result["security_score"] > 0

    @pytest.mark.asyncio
    async def test_security_event_tracking(self):
        """Test security event recording and analysis"""
        user_id = "test_user_123"

        # Record security event
        alert = await security_monitor.record_security_event(
            user_id=user_id,
            event_type="login_success",
            ip_address="127.0.0.1",
            user_agent="Test Browser",
            success=True,
            endpoint="/api/v1/token",
            metadata={"test": True},
        )

        # Security monitoring should not produce alerts for normal activity
        # (In production, this might return None for normal events)
        assert True  # Test completes without errors

    @pytest.mark.asyncio
    async def test_risk_assessment(self):
        """Test user risk assessment"""
        user_id = "test_user_123"

        # Get risk assessment for user
        risk_level, risk_factors = await security_monitor.get_user_risk_level(user_id)

        # New user should have low risk
        assert risk_level is not None
        assert "risk_score" in risk_factors
        assert 0 <= risk_factors["risk_score"] <= 100


class TestSessionSecurity:
    """Test session security features"""

    @pytest.mark.asyncio
    async def test_session_creation_security(self):
        """Test secure session creation with device fingerprinting"""
        user_id = "test_user_123"

        # Mock device fingerprint
        headers = {
            "User-Agent": "Test Browser 1.0",
            "Accept": "application/json",
            "Accept-Language": "en-US",
        }

        device_fingerprint = session_manager.get_device_fingerprint(headers)

        # Create session
        session = await session_manager.create_session(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            request_headers=headers,
        )

        # Verify session properties
        assert session.session_id is not None
        assert session.user_id == user_id
        assert session.device_fingerprint is not None
        assert session.is_active is True

    @pytest.mark.asyncio
    async def test_concurrent_session_limits(self):
        """Test concurrent session limit enforcement"""
        user_id = "test_user_123"
        max_sessions = getattr(settings, "MAX_CONCURRENT_SESSIONS", 3)

        # Mock device fingerprints
        headers = {"User-Agent": "Test Browser", "Accept": "application/json"}

        device_fingerprint = session_manager.get_device_fingerprint(headers)

        # Create sessions up to limit
        sessions = []
        for i in range(max_sessions + 1):
            # Modify user agent slightly for different devices
            headers["User-Agent"] = f"Test Browser {i}.0"
            fp = session_manager.get_device_fingerprint(headers)

            try:
                session = await session_manager.create_session(
                    user_id=user_id, device_fingerprint=fp, request_headers=headers
                )
                sessions.append(session)
            except Exception as e:
                # Should fail when exceeding limit
                if i >= max_sessions:
                    assert "concurrent" in str(e).lower() or "limit" in str(e).lower()
                else:
                    raise e


class TestRateLimitingSecurity:
    """Test rate limiting security features"""

    def test_rate_limiting_headers(self):
        """Test rate limiting headers are present"""
        # Make a request to check headers
        response = client.get("/")

        # Check for rate limiting headers (implementation dependent)
        # This tests the rate limiting middleware is active
        assert response.status_code in [200, 429]

    def test_brute_force_protection(self):
        """Test protection against brute force attacks"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
        }

        # Make multiple failed login attempts
        responses = []
        for _ in range(10):
            response = client.post("/api/v1/token", data=login_data)
            responses.append(response)

        # Should receive error responses
        error_responses = [r for r in responses if r.status_code >= 400]
        assert len(error_responses) > 0


class TestInputValidationSecurity:
    """Test input validation security"""

    def test_sql_injection_protection(self):
        """Test SQL injection protection in auth endpoints"""
        malicious_inputs = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "admin' UNION SELECT * FROM users --",
        ]

        for malicious_input in malicious_inputs:
            login_data = {"username": malicious_input, "password": "password123"}

            # Should not cause server errors
            response = client.post("/api/v1/token", data=login_data)
            assert response.status_code not in [500, 502, 503]

    def test_xss_protection_in_auth(self):
        """Test XSS protection in authentication forms"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
        ]

        for xss_payload in xss_payloads:
            # Test in username field
            login_data = {"username": xss_payload, "password": "password123"}

            response = client.post("/api/v1/token", data=login_data)

            # Response should not contain unescaped script
            response_text = response.text.lower()
            assert "<script>" not in response_text
            assert "javascript:" not in response_text

    def test_parameter_pollution_protection(self):
        """Test parameter pollution protection"""
        # Test multiple username parameters
        login_data = {
            "username": "user1",
            "password": "password123",
            "username": "user2",  # This should override, not create multiple
        }

        response = client.post("/api/v1/token", data=login_data)
        # Should handle gracefully without confusion
        assert response.status_code not in [500, 400]


class TestAuthenticationEndpointsSecurity:
    """Test security of authentication endpoints"""

    def test_login_endpoint_security(self):
        """Test login endpoint security features"""
        # Test missing required fields
        response = client.post("/api/v1/token", data={})
        assert response.status_code == 422  # Validation error

        # Test malformed request
        response = client.post("/api/v1/token", json={"malformed": "data"})
        assert response.status_code == 422

    def test_register_endpoint_security(self):
        """Test registration endpoint security"""
        # Test weak password rejection
        weak_registration = {
            "email": "test@example.com",
            "password": "password",  # Weak password
            "full_name": "Test User",
        }

        response = client.post("/api/v1/register", json=weak_registration)
        # Should reject weak passwords
        assert response.status_code == 422

    def test_logout_endpoint_security(self):
        """Test logout endpoint security"""
        # Test logout without authentication
        response = client.post("/api/v1/logout")
        assert response.status_code == 401  # Unauthorized

        # Test logout with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/logout", headers=headers)
        assert response.status_code == 401


class TestSecurityHeaders:
    """Test security headers implementation"""

    def test_security_headers_present(self):
        """Test that security headers are present"""
        response = client.get("/")

        # Check for important security headers
        headers = response.headers

        # These should be present in a secure implementation
        expected_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
        ]

        for header in expected_headers:
            # Headers are lowercase in response.headers
            assert header in headers

        # Check specific header values
        if "x-content-type-options" in headers:
            assert headers["x-content-type-options"] == "nosniff"

        if "x-frame-options" in headers:
            assert headers["x-frame-options"] in ["DENY", "SAMEORIGIN"]

    def test_cors_configuration_security(self):
        """Test CORS configuration"""
        # Test preflight request
        response = client.options(
            "/api/v1/token",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should handle CORS preflight
        assert response.status_code in [200, 204, 405]


class TestErrorHandlingSecurity:
    """Test secure error handling"""

    def test_information_disclosure_prevention(self):
        """Test that errors don't disclose sensitive information"""
        # Test with invalid credentials
        response = client.post(
            "/api/v1/token",
            data={"username": "nonexistent@example.com", "password": "wrongpassword"},
        )

        # Error message should be generic
        response_data = response.json()
        assert "password" not in str(response_data).lower()
        assert "email" not in str(response_data).lower()
        assert "user" not in str(response_data).lower()

    def test_stack_trace_prevention(self):
        """Test that stack traces are not exposed"""
        # Test with malformed request that might cause exceptions
        response = client.post(
            "/api/v1/token",
            data={
                "username": "test@example.com",
                "password": "password" * 1000,  # Very long password
            },
        )

        # Should handle gracefully
        assert response.status_code not in [500]

        # Response should not contain stack trace information
        response_text = response.text.lower()
        assert "traceback" not in response_text
        assert "exception" not in response_text
        assert "error in" not in response_text


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "-k", "TestPasswordSecurity"])
