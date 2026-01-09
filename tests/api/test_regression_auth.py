"""
Comprehensive Regression Tests for Authentication Endpoints
tests/api/test_regression_auth.py

This module contains regression tests for all authentication endpoints:
- /api/v1/auth/token-fixed (login)
- /api/v1/auth/register-fixed (registration)
- /api/v1/auth/me-fixed (get current user)
- /api/v1/auth/logout (logout)
- /api/v1/auth/refresh-token-fixed (token refresh)

Test Categories:
- P0: Critical authentication flows (must pass)
- P1: High-priority edge cases
- Security: OWASP Top 10 protections

Priority: P0 (Critical)
Coverage Target: 90% lines, 85% branches, 95% functions
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import json

from app.main import app
from app.db.models.user import User, UserRole
from app.core.security import create_access_token, verify_password
from tests.conftest import fake


class TestAuthLoginRegression:
    """
    Regression tests for login endpoint
    Endpoint: POST /api/v1/auth/token-fixed
    """

    @pytest.mark.asyncio
    async def test_login_success_valid_credentials(self, client: AsyncClient, test_user: User):
        """
        Test: Verify successful login with valid email/password

        Input: Valid user credentials
        Expected: 200 status, access_token and refresh_token in httpOnly cookies
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"  # Must match fixture
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Login successful"
        assert "user" in data
        assert data["user"]["email"] == test_user.email

        # Verify cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "csrf_token" in cookies

    @pytest.mark.asyncio
    async def test_login_failure_invalid_email(self, client: AsyncClient):
        """
        Test: Verify login rejection with non-existent email

        Input: Non-existent email
        Expected: 401 status, generic error message
        Security: No user enumeration in error message
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        # Generic error message (no user enumeration)
        assert "email" not in data["detail"].lower() or "incorrect" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_failure_invalid_password(self, client: AsyncClient, test_user: User):
        """
        Test: Verify login rejection with wrong password

        Input: Valid email, invalid password
        Expected: 401 status, generic error message
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_failure_inactive_account(self, client: AsyncClient, test_db):
        """
        Test: Verify rejection of inactive accounts

        Input: Credentials for inactive user
        Expected: 401 status, account inactive message
        Priority: P0
        """
        # Create inactive user
        from app.schemas.user import UserCreate
        from app.services.user_service import create_user

        user_data = UserCreate(
            email=fake.email(),
            full_name=fake.name(),
            role=UserRole.USER,
            is_active=False,  # Inactive
            password="TestPassword123!"
        )
        user = await create_user(user_data, test_db)

        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": user.email,
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, client: AsyncClient, test_user: User):
        """
        Test: Verify rate limiting after 5 failed attempts

        Input: 6 consecutive failed login attempts
        Expected: 429 status on 6th attempt
        Priority: P0
        """
        # Attempt 5 failed logins
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/token-fixed",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401

        # 6th attempt should be rate limited
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 429

    @pytest.mark.asyncio
    @pytest.mark.parametrize("sql_payload", [
        "admin'--",
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "admin' UNION SELECT * FROM users--",
        "'; INSERT INTO users VALUES('hacker','pass'); --"
    ])
    async def test_login_sql_injection_protection(self, client: AsyncClient, sql_payload: str):
        """
        Test: Verify SQL injection protection in email field

        Input: Email with SQL injection patterns
        Expected: 400 status (validation error) or 401 (auth failure)
        Security: No SQL errors exposed
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": sql_payload,
                "password": "TestPassword123!"
            }
        )

        # Should not return 500 (SQL error)
        assert response.status_code in [400, 401]
        # Error message should not contain SQL details
        if response.status_code == 500:
            pytest.fail("SQL injection vulnerability detected")

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, client: AsyncClient):
        """
        Test: Verify rejection of missing credentials

        Input: Empty email/password
        Expected: 400 status, validation error
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": "",
                "password": ""
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_updates_last_login(self, client: AsyncClient, test_user: User, test_db):
        """
        Test: Verify last_login timestamp is updated

        Input: Valid credentials
        Expected: last_login updated to recent timestamp
        Priority: P1
        """
        old_login = test_user.last_login

        await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )

        # Refresh user from database
        from sqlalchemy import select
        result = await test_db.execute(select(User).where(User.id == test_user.id))
        updated_user = result.scalar_one_or_none()

        assert updated_user.last_login is not None
        assert updated_user.last_login > (old_login or datetime.min)


class TestAuthRegistrationRegression:
    """
    Regression tests for registration endpoint
    Endpoint: POST /api/v1/auth/register-fixed
    """

    @pytest.mark.asyncio
    async def test_register_success_valid_data(self, client: AsyncClient):
        """
        Test: Verify successful user registration

        Input: Valid email, strong password, full name
        Expected: 201 status, user object with id, email, is_active fields
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": fake.email(),
                "password": "StrongPassword123!",
                "full_name": fake.name()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] is not None
        assert data["user"]["is_active"] is True
        assert data["user"]["is_verified"] is False

    @pytest.mark.asyncio
    async def test_register_failure_duplicate_email(self, client: AsyncClient, test_user: User):
        """
        Test: Verify rejection of duplicate email

        Input: Email already in database
        Expected: 409 status, "Email already registered"
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": test_user.email,  # Already exists
                "password": "StrongPassword123!",
                "full_name": fake.name()
            }
        )

        assert response.status_code == 409
        data = response.json()
        assert "already registered" in data.get("detail", "").lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("weak_password", [
        "short",  # Too short
        "alllowercase123",  # No uppercase
        "ALLUPPERCASE123",  # No lowercase
        "NoNumbers!",  # No numbers
        "Nospecial123",  # No special chars
    ])
    async def test_register_failure_weak_password(self, client: AsyncClient, weak_password: str):
        """
        Test: Verify password strength validation

        Input: Passwords < 8 chars, no uppercase, no numbers, no special chars
        Expected: 400 status, detailed password requirements
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": fake.email(),
                "password": weak_password,
                "full_name": fake.name()
            }
        )

        assert response.status_code == 400
        data = response.json()
        # Should contain password requirements
        assert "password" in str(data).lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_email", [
        "notanemail",
        "@example.com",
        "user@",
        "user@.com",
        "user..name@example.com"
    ])
    async def test_register_failure_invalid_email_format(self, client: AsyncClient, invalid_email: str):
        """
        Test: Verify email format validation

        Input: Invalid email formats
        Expected: 400 status, "Invalid email format"
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": invalid_email,
                "password": "StrongPassword123!",
                "full_name": fake.name()
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "email" in str(data).lower()

    @pytest.mark.asyncio
    async def test_register_rate_limiting(self, client: AsyncClient):
        """
        Test: Verify registration rate limiting

        Input: 4 registration attempts within 1 hour
        Expected: 429 status on 4th attempt
        Priority: P0
        """
        # Attempt 3 registrations
        for i in range(3):
            response = await client.post(
                "/api/v1/auth/register-fixed",
                data={
                    "email": fake.email(),
                    "password": "StrongPassword123!",
                    "full_name": fake.name()
                }
            )
            # First 3 may succeed or fail (duplicate), but not rate limited
            assert response.status_code != 429

        # 4th attempt should be rate limited
        response = await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": fake.email(),
                "password": "StrongPassword123!",
                "full_name": fake.name()
            }
        )
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_register_password_hashing(self, client: AsyncClient, test_db):
        """
        Test: Verify passwords are hashed, not stored plaintext

        Input: Valid registration
        Expected: password_hash is bcrypt hash, password not stored
        Priority: P0
        Security: Critical
        """
        email = fake.email()
        password = "StrongPassword123!"

        await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": email,
                "password": password,
                "full_name": fake.name()
            }
        )

        # Retrieve user from database
        from sqlalchemy import select
        result = await test_db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.password_hash is not None
        # Verify it's a bcrypt hash (starts with $2b$)
        assert user.password_hash.startswith("$2b$")
        # Verify password not stored plaintext
        assert password not in user.password_hash
        assert not hasattr(user, 'password') or user.password is None


class TestAuthTokenManagementRegression:
    """
    Regression tests for token management endpoints
    Endpoints: GET /api/v1/auth/me-fixed, POST /api/v1/auth/refresh-token-fixed, POST /api/v1/auth/logout
    """

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Verify user info retrieval with valid token

        Input: Valid JWT in Authorization header or cookie
        Expected: 200 status, user object
        Priority: P0
        """
        response = await client.get(
            "/api/v1/auth/me-fixed",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """
        Test: Verify rejection of invalid tokens

        Input: Malformed token
        Expected: 401 status
        Priority: P0
        """
        response = await client.get(
            "/api/v1/auth/me-fixed",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """
        Test: Verify rejection of requests without token

        Input: No Authorization header or cookie
        Expected: 401 status
        Priority: P0
        """
        response = await client.get("/api/v1/auth/me-fixed")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_refresh_valid_refresh_token(self, client: AsyncClient, test_user: User):
        """
        Test: Verify token refresh works

        Input: Valid refresh token
        Expected: 200 status, new access_token
        Priority: P0
        """
        # First, login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )

        refresh_token = login_response.cookies.get("refresh_token")

        # Use refresh token to get new access token
        response = await client.post(
            "/api/v1/auth/refresh-token-fixed",
            data={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, client: AsyncClient):
        """
        Test: Verify rejection of invalid refresh tokens

        Input: Invalid/expired refresh token
        Expected: 401 status
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/refresh-token-fixed",
            data={"refresh_token": "invalid_refresh_token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Verify logout clears cookies

        Input: Valid token
        Expected: 200 status, cookies cleared (expired)
        Priority: P0
        """
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == 200
        # Verify cookies are cleared (expired)
        cookies = response.cookies
        for cookie_name in ["access_token", "refresh_token", "csrf_token"]:
            if cookie_name in cookies:
                # Cookie should be set with max-age=0 or expires in past
                assert cookies[cookie_name] == "" or cookies.get(cookie_name, "") == ""

    @pytest.mark.asyncio
    async def test_logout_token_blacklist(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Verify logout blacklists token

        Input: Valid token
        Expected: Token added to blacklist, subsequent use fails
        Priority: P0
        Security: Critical
        """
        # Logout
        await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        # Try to use the same token
        response = await client.get(
            "/api/v1/auth/me-fixed",
            headers=auth_headers
        )

        # Should fail (token is blacklisted)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_expiration(self, client: AsyncClient, test_user: User):
        """
        Test: Verify token expiration enforced (requires time manipulation or short-lived tokens)

        Input: Expired token
        Expected: 401 status
        Priority: P0
        """
        # Create token with very short expiration
        from app.core.security_fixes import create_secure_token_for_user, timedelta

        expired_token = create_secure_token_for_user(
            str(test_user.id),
            test_user.email,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = await client.get(
            "/api/v1/auth/me-fixed",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401


class TestAuthSessionSecurityRegression:
    """
    Regression tests for session security features
    CSRF tokens, cookie security attributes, session management
    """

    @pytest.mark.asyncio
    async def test_session_csrf_token_generation(self, client: AsyncClient, test_user: User):
        """
        Test: Verify CSRF token generation on login

        Expected: csrf_token cookie set (non-httpOnly)
        Priority: P0
        Security: Required for CSRF protection
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200
        cookies = response.cookies
        assert "csrf_token" in cookies

    @pytest.mark.asyncio
    async def test_session_cookie_security_flags(self, client: AsyncClient, test_user: User):
        """
        Test: Verify cookie security attributes

        Expected: httpOnly=True, secure=True, sameSite=lax
        Priority: P0
        Security: Critical for XSS and CSRF protection
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )

        # Check cookie attributes in response headers
        set_cookie_headers = response.headers.get_list("set-cookie")
        cookie_str = " ".join(set_cookie_headers)

        # Verify security flags
        assert "HttpOnly" in cookie_str
        assert "Secure" in cookie_str
        assert "SameSite=lax" in cookie_str or "SameSite=Lax" in cookie_str


class TestAuthEdgeCasesRegression:
    """
    Regression tests for edge cases and error handling
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_concurrent_login_requests(self, client: AsyncClient, test_user: User):
        """
        Test: Verify system handles multiple concurrent logins

        Input: 10 concurrent login requests from same IP
        Expected: All processed correctly, rate limiting enforced
        Priority: P1
        """
        import asyncio

        async def login_attempt():
            return await client.post(
                "/api/v1/auth/token-fixed",
                data={
                    "username": test_user.email,
                    "password": "TestPassword123!"
                }
            )

        # Send 10 concurrent requests
        responses = await asyncio.gather(*[login_attempt() for _ in range(10)])

        # All should succeed (rate limiting allows success after valid login)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1  # At least some should succeed

    @pytest.mark.asyncio
    async def test_login_unicode_email(self, client: AsyncClient, test_db):
        """
        Test: Verify Unicode email support

        Input: Email with Unicode characters
        Expected: Successful registration and login
        Priority: P1
        """
        from app.schemas.user import UserCreate
        from app.services.user_service import create_user

        unicode_email = "tëst@exãmple.com"
        user_data = UserCreate(
            email=unicode_email,
            full_name="Tëst Üser",
            role=UserRole.USER,
            is_active=True,
            password="TestPassword123!"
        )
        user = await create_user(user_data, test_db)

        # Try to login
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": unicode_email,
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_case_insensitive_email(self, client: AsyncClient, test_user: User):
        """
        Test: Verify email login is case-insensitive

        Input: Email with different case than registration
        Expected: Successful login
        Priority: P1
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email.upper(),  # Uppercase
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200


# Test class markers for easy filtering
TestAuthLoginRegression = pytest.mark.P0(TestAuthLoginRegression)
TestAuthRegistrationRegression = pytest.mark.P0(TestAuthRegistrationRegression)
TestAuthTokenManagementRegression = pytest.mark.P0(TestAuthTokenManagementRegression)
TestAuthSessionSecurityRegression = pytest.mark.P0(TestAuthSessionSecurityRegression)
TestAuthEdgeCasesRegression = pytest.mark.P1(TestAuthEdgeCasesRegression)
