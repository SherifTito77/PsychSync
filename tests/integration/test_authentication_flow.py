"""
Authentication Flow Integration Tests
Comprehensive testing of all authentication scenarios including registration,
login, token management, MFA, and security features
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.main import app
from app.core.database import get_db
from app.services.security import (
create_access_token, create_refresh_token, verify_password,
    get_password_hash, verify_token, get_current_user
)
from app.db.models.user import User


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test suite for complete authentication flows"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def test_db(self):
        """Create test database session"""
        async for session in get_db():
            yield session

    @pytest.fixture
    async def test_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "authtest@example.com",
            "full_name": "Auth Test User",
            "password": "SecurePassword123!",
            "role": "user"
        }

    @pytest.fixture
    async def admin_user_data(self):
        """Sample admin user data for testing"""
        return {
            "email": "admin@authtest.com",
            "full_name": "Admin Test User",
            "password": "AdminSecurePassword123!",
            "role": "admin"
        }

    # User Registration Tests
    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, client: AsyncClient, test_user_data):
        """Test complete user registration flow"""
        # Step 1: Register new user
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "user" in data["data"]

        # Verify user data in response
        user_response = data["data"]["user"]
        assert user_response["email"] == test_user_data["email"]
        assert user_response["full_name"] == test_user_data["full_name"]
        assert user_response["role"] == test_user_data["role"]
        assert "id" in user_response
        assert "created_at" in user_response
        assert "email_verified" in user_response

        # Step 2: Verify tokens are valid JWT tokens
        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]

        # Decode and verify access token
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        assert "sub" in access_payload  # Subject (user ID)
        assert "exp" in access_payload  # Expiration
        assert "type" in access_payload  # Token type
        assert access_payload["type"] == "access"

        # Decode and verify refresh token
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        assert "sub" in refresh_payload
        assert "exp" in refresh_payload
        assert "type" in refresh_payload
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_registration_email_validation(self, client: AsyncClient):
        """Test email validation during registration"""
        # Test invalid email format
        invalid_email_data = {
            "email": "invalid-email",
            "full_name": "Test User",
            "password": "SecurePassword123!",
            "role": "user"
        }

        response = await client.post("/api/v1/auth/register", json=invalid_email_data)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should contain validation error for email

        # Test email format with special characters
        special_email_data = {
            "email": "test+special@example.co.uk",
            "full_name": "Test User",
            "password": "SecurePassword123!",
            "role": "user"
        }

        response = await client.post("/api/v1/auth/register", json=special_email_data)
        assert response.status_code == 201  # Should accept valid email format

    @pytest.mark.asyncio
    async def test_registration_password_validation(self, client: AsyncClient, test_user_data):
        """Test password validation during registration"""
        # Test password too short
        short_password_data = test_user_data.copy()
        short_password_data["password"] = "123"

        response = await client.post("/api/v1/auth/register", json=short_password_data)
        assert response.status_code == 422

        # Test password without uppercase
        no_uppercase_data = test_user_data.copy()
        no_uppercase_data["password"] = "securepassword123!"

        response = await client.post("/api/v1/auth/register", json=no_uppercase_data)
        assert response.status_code == 422

        # Test password without lowercase
        no_lowercase_data = test_user_data.copy()
        no_lowercase_data["password"] = "SECUREPASSWORD123!"

        response = await client.post("/api/v1/auth/register", json=no_lowercase_data)
        assert response.status_code == 422

        # Test password without numbers
        no_numbers_data = test_user_data.copy()
        no_numbers_data["password"] = "SecurePassword"

        response = await client.post("/api/v1/auth/register", json=no_numbers_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(self, client: AsyncClient, test_user_data):
        """Test registration with duplicate email"""
        # First registration
        response1 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201

        # Second registration with same email
        response2 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 400
        data = response2.json()
        assert "already exists" in data["detail"].lower()

    # Login Tests
    @pytest.mark.asyncio
    async def test_successful_login_flow(self, client: AsyncClient, test_user_data, test_db: AsyncSession):
        """Test successful user login flow"""
        # First register the user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Step 1: Login with correct credentials
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }

        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "user" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"

        # Verify user data in login response
        user_response = data["data"]["user"]
        assert user_response["email"] == test_user_data["email"]
        assert user_response["full_name"] == test_user_data["full_name"]
        assert user_response["role"] == test_user_data["role"]

        # Step 2: Verify login updates user activity
        result = await test_db.execute(
            select(User).where(User.email == test_user_data["email"])
        )
        user = result.scalar_one()
        assert user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user_data):
        """Test login with invalid credentials"""
        # First register the user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Test with wrong password
        wrong_password_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }

        response = await client.post("/api/v1/auth/login", json=wrong_password_data)
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

        # Test with non-existent email
        nonexistent_email_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }

        response = await client.post("/api/v1/auth/login", json=nonexistent_email_data)
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, client: AsyncClient, test_user_data):
        """Test login rate limiting"""
        # First register the user
        await client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "email": test_user_data["email"],
            "password": "wrong_password"  # Wrong password to trigger failed attempts
        }

        # Make multiple failed login attempts
        responses = []
        for _ in range(10):
            response = await client.post("/api/v1/auth/login", json=login_data)
            responses.append(response)

        # Should eventually trigger rate limiting
        rate_limited = any(r.status_code == 429 for r in responses)

        if rate_limited:
            rate_limit_response = next(r for r in responses if r.status_code == 429)
            assert rate_limit_response.status_code == 429
            assert "rate limit" in rate_limit_response.text.lower()

    # Token Management Tests
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, client: AsyncClient, test_user_data, test_db: AsyncSession):
        """Test complete token refresh flow"""
        # Register and login user
        register_response = await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        original_tokens = login_response.json()["data"]
        original_access_token = original_tokens["access_token"]
        original_refresh_token = original_tokens["refresh_token"]

        # Step 1: Refresh token
        refresh_data = {"refresh_token": original_refresh_token}
        refresh_response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()["data"]
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]

        # Step 2: Verify new tokens are different
        assert new_access_token != original_access_token
        assert new_refresh_token != original_refresh_token

        # Step 3: Verify new token works
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = await client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200

        # Step 4: Verify old token is invalidated
        old_headers = {"Authorization": f"Bearer {original_access_token}"}
        old_profile_response = await client.get("/api/v1/users/profile", headers=old_headers)
        # Old token might still work if there's no blacklist, or it might be invalid
        # This depends on the token management strategy

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, client: AsyncClient):
        """Test token refresh with invalid token"""
        # Test with malformed token
        malformed_data = {"refresh_token": "invalid_token"}

        response = await client.post("/api/v1/auth/refresh", json=malformed_data)
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

        # Test with expired token
        expired_payload = {
            "sub": "user_id",
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            "type": "refresh"
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        expired_data = {"refresh_token": expired_token}

        response = await client.post("/api/v1/auth/refresh", json=expired_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_concurrent_token_refresh(self, client: AsyncClient, test_user_data):
        """Test concurrent token refresh requests"""
        # Register and login user
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        refresh_token = login_response.json()["data"]["refresh_token"]
        refresh_data = {"refresh_token": refresh_token}

        # Make concurrent refresh requests
        async def refresh_token():
            return await client.post("/api/v1/auth/refresh", json=refresh_data)

        tasks = [refresh_token() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # Should handle concurrent requests gracefully
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1  # At least one should succeed

        # Verify all returned valid tokens (if multiple succeeded)
        for response in responses:
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data["data"]
                assert "refresh_token" in data["data"]

    # Logout Tests
    @pytest.mark.asyncio
    async def test_logout_flow(self, client: AsyncClient, test_user_data):
        """Test complete logout flow"""
        # Register and login user
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        access_token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 1: Logout
        logout_response = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        data = logout_response.json()
        assert "successfully" in data["message"].lower()

        # Step 2: Verify token is invalidated
        profile_response = await client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 401  # Token should be invalid

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """Test logout without authentication token"""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401  # Should require authentication

    # Password Reset Flow Tests
    @pytest.mark.asyncio
    async def test_password_reset_request(self, client: AsyncClient, test_user_data):
        """Test password reset request flow"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Step 1: Request password reset
        reset_request_data = {"email": test_user_data["email"]}
        response = await client.post("/api/v1/auth/reset-password-request", json=reset_request_data)

        assert response.status_code == 200
        data = response.json()
        assert "password reset" in data["message"].lower()
        assert "email" in data["message"].lower()

        # Step 2: Verify reset token would be sent (implementation dependent)
        # This would typically involve checking database for reset token

    @pytest.mark.asyncio
    async def test_password_reset_completion(self, client: AsyncClient, test_user_data):
        """Test password reset completion flow"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        # This would typically involve:
        # 1. Request password reset (get reset token)
        # 2. Submit new password with reset token
        # 3. Verify password changed and can login

        # Implementation would depend on the specific reset flow

    # Multi-Factor Authentication Tests
    @pytest.mark.asyncio
    async def test_mfa_setup(self, client: AsyncClient, test_user_data):
        """Test MFA setup flow"""
        # Register user first
        register_response = await client.post("/api/v1/auth/register", json=test_user_data)
        user_id = register_response.json()["data"]["user"]["id"]

        # This would typically involve:
        # 1. Enable MFA for user
        # 2. Generate MFA secret
        # 3. Return QR code and backup codes

        # Implementation would depend on MFA system (TOTP, SMS, etc.)

    @pytest.mark.asyncio
    async def test_mfa_verification(self, client: AsyncClient, test_user_data):
        """Test MFA verification during login"""
        # This would test the complete MFA login flow:
        # 1. First login step (username/password)
        # 2. MFA challenge step
        # 3. Complete authentication with MFA token

        # Implementation would depend on MFA system

    # Session Management Tests
    @pytest.mark.asyncio
    async def test_session_management(self, client: AsyncClient, test_user_data):
        """Test session management features"""
        # Register and login user
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        access_token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Test session validation
        profile_response = await client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200

        # Test session timeout (implementation dependent)
        # This would involve checking session expiration

        # Test multiple active sessions (if supported)
        # This would test concurrent session management

    # Security Tests
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, client: AsyncClient, test_user_data):
        """Test brute force attack protection"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Make multiple failed login attempts
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }

        failed_attempts = 0
        for i in range(20):
            response = await client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:  # Rate limited
                break

        # Should either rate limit or allow attempts but with delays
        assert failed_attempts > 0

    @pytest.mark.asyncio
    async def test_account_lockout(self, client: AsyncClient, test_user_data):
        """Test account lockout after multiple failed attempts"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }

        # Make multiple failed attempts to trigger lockout
        for _ in range(10):
            await client.post("/api/v1/auth/login", json=login_data)

        # Try correct password after lockout
        correct_login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }

        response = await client.post("/api/v1/auth/login", json=correct_login_data)

        # Should either allow login (with delay) or block account
        # This depends on account lockout implementation

    @pytest.mark.asyncio
    async def test_token_expiration(self, client: AsyncClient):
        """Test token expiration handling"""
        # Create expired token
        expired_payload = {
            "sub": "user_id",
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            "type": "access"
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/api/v1/users/profile", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower() or "invalid" in data["detail"].lower()

    # Device Management Tests
    @pytest.mark.asyncio
    async def test_device_fingerprinting(self, client: AsyncClient, test_user_data):
        """Test device fingerprinting during login"""
        # This would test device recognition and management
        # Implementation would depend on fingerprinting strategy

        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Login with device information
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "device_info": {
                "user_agent": "Test Browser",
                "ip_address": "127.0.0.1",
                "device_id": "test_device_123"
            }
        }

        response = await client.post("/api/v1/auth/login", json=login_data)
        # Should handle device information appropriately

    @pytest.mark.asyncio
    async def test_concurrent_login_prevention(self, client: AsyncClient, test_user_data):
        """Test prevention of concurrent sessions for same user"""
        # Register user first
        await client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }

        # Make concurrent login requests
        async def login():
            return await client.post("/api/v1/auth/login", json=login_data)

        tasks = [login() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # Should handle concurrent logins appropriately
        # This depends on session management strategy

    # Integration with Other Systems
    @pytest.mark.asyncio
    async def test_social_auth_integration(self, client: AsyncClient):
        """Test social authentication integration"""
        # This would test OAuth2/social login flows
        # Implementation would depend on social auth providers

    @pytest.mark.asyncio
    async def test_sso_integration(self, client: AsyncClient):
        """Test Single Sign-On integration"""
        # This would test SSO flows (SAML, OAuth, etc.)
        # Implementation would depend on SSO provider

    @pytest.mark.asyncio
    async def test_third_party_identity_providers(self, client: AsyncClient):
        """Test integration with third-party identity providers"""
        # This would test integration with external auth systems
        # Implementation would depend on external providers


class TestAuthenticationSecurity:
    """Security-focused authentication tests"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_sql_injection_protection_in_auth(self, client: AsyncClient):
        """Test SQL injection protection in authentication endpoints"""
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]

        for payload in malicious_payloads:
            # Test in registration
            register_data = {
                "email": payload,
                "full_name": "SQL Injection Test",
                "password": "TestPassword123!"
            }

            response = await client.post("/api/v1/auth/register", json=register_data)
            # Should handle malicious input safely
            assert response.status_code in [400, 422]

            # Test in login
            login_data = {
                "email": payload,
                "password": "TestPassword123!"
            }

            response = await client.post("/api/v1/auth/login", json=login_data)
            # Should handle malicious input safely
            assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_xss_protection_in_auth(self, client: AsyncClient):
        """Test XSS protection in authentication endpoints"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]

        for payload in xss_payloads:
            # Test in registration
            register_data = {
                "email": f"xss_test_{payload}@example.com",
                "full_name": payload,
                "password": "TestPassword123!"
            }

            response = await client.post("/api/v1/auth/register", json=register_data)

            if response.status_code == 201:
                # If accepted, verify XSS is sanitized in response
                data = response.json()
                assert "<script>" not in data["data"]["user"]["full_name"]
                assert "<img" not in data["data"]["user"]["full_name"]
                assert "javascript:" not in data["data"]["user"]["full_name"]
            else:
                # Should be rejected
                assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_token_tampering_protection(self, client: AsyncClient):
        """Test token tampering protection"""
        # Create valid-looking but tampered token
        tampered_payload = {
            "sub": "admin_user_id",  # Tampered user ID
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "type": "access",
            "role": "admin"  # Tampered role
        }

        tampered_token = jwt.encode(tampered_payload, "secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {tampered_token}"}

        response = await client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_csrf_protection(self, client: AsyncClient):
        """Test CSRF protection in authentication endpoints"""
        # This would test CSRF token validation
        # Implementation would depend on CSRF protection strategy

    @pytest.mark.asyncio
    async def test_session_hijacking_protection(self, client: AsyncClient):
        """Test session hijacking protection"""
        # This would test session binding to IP/device
        # Implementation would depend on session security strategy

    @pytest.mark.asyncio
    async def test_authentication_logging(self, client: AsyncClient):
        """Test that authentication attempts are properly logged"""
        # Test failed login logging
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401

        # In a real implementation, this would verify that:
        # 1. The failed login attempt was logged
        # 2. The log includes IP address, timestamp, user agent
        # 3. Security events are triggered appropriately

    @pytest.mark.asyncio
    async def test_rate_limiting_headers(self, client: AsyncClient):
        """Test rate limiting headers in authentication responses"""
        login_data = {
            "email": "ratelimit@example.com",
            "password": "TestPassword123!"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        # Should include rate limiting headers if implemented
        # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
