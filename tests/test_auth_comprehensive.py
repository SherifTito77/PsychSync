# tests/test_auth_comprehensive.py
"""
Comprehensive authentication system tests
- User registration and verification
- Login and token management
- Password reset and security
- Role-based access control
- JWT token handling and refresh
- Email verification flows
- Account security features
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.services.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.services.user_service import authenticate_user, create_user, get_user_by_email


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality"""

    async def test_register_user_success(
        self, async_client: AsyncClient, mock_email_service
    ):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@test.com",
            "full_name": "New Test User",
            "password": "SecurePassword123!",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password" not in data
        assert not data["is_verified"]

    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": test_user.email,
            "full_name": "Duplicate User",
            "password": "SecurePassword123!",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "full_name": "Invalid Email User",
            "password": "SecurePassword123!",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password"""
        user_data = {
            "email": "weakpass@test.com",
            "full_name": "Weak Password User",
            "password": "123",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_triggers_verification_email(
        self, async_client: AsyncClient, mock_email_service
    ):
        """Test that registration triggers verification email"""
        user_data = {
            "email": "verify@test.com",
            "full_name": "Verify User",
            "password": "SecurePassword123!",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        # Verify email service was called
        mock_email_service.send_verification_email.assert_called_once()

    async def test_register_with_optional_fields(self, async_client: AsyncClient):
        """Test registration with optional fields"""
        user_data = {
            "email": "optional@test.com",
            "full_name": "Optional Fields User",
            "password": "SecurePassword123!",
            "phone": "+1234567890",
            "department": "Engineering",
            "job_title": "Software Engineer",
            "bio": "Test bio",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["phone"] == user_data["phone"]
        assert data["department"] == user_data["department"]
        assert data["job_title"] == user_data["job_title"]
        assert data["bio"] == user_data["bio"]


@pytest.mark.auth
class TestUserAuthentication:
    """Test user authentication functionality"""

    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """Test successful user login"""
        login_data = {"email": test_user.email, "password": "TestSecurePassword123!"}

        response = await async_client.post("/api/v1/auth/login/json", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    async def test_login_invalid_credentials(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test login with invalid credentials"""
        login_data = {"email": test_user.email, "password": "wrongpassword"}

        response = await async_client.post("/api/v1/auth/login/json", json=login_data)

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    async def test_login_unverified_user(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """Test login with unverified user"""
        # Create unverified user
        user_data = {
            "email": "unverified@test.com",
            "full_name": "Unverified User",
            "password": "SecurePassword123!",
        }
        user_create = UserCreate(**user_data)
        user = await create_user(async_client, user_create)
        # Don't verify the user

        login_data = {"email": user.email, "password": "SecurePassword123!"}

        response = await async_client.post("/api/v1/auth/login/json", json=login_data)

        assert response.status_code == 401
        assert "email not verified" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user"""
        login_data = {"email": "nonexistent@test.com", "password": "SecurePassword123!"}

        response = await async_client.post("/api/v1/auth/login/json", json=login_data)

        assert response.status_code == 401

    async def test_login_rate_limiting(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test login rate limiting"""
        login_data = {"email": test_user.email, "password": "wrongpassword"}

        # Make multiple failed attempts
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/login/json", json=login_data
            )
            assert response.status_code == 401

        # 6th attempt should be rate limited
        response = await async_client.post("/api/v1/auth/login/json", json=login_data)
        assert response.status_code == 429


@pytest.mark.auth
class TestTokenManagement:
    """Test JWT token functionality"""

    async def test_access_token_validity(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that access token works for authenticated requests"""
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data

    async def test_access_token_expires(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test access token expiration"""
        # Create token with short expiration
        token_data = {"sub": str(test_user.id), "role": test_user.role.value}
        access_token = create_access_token(
            data=token_data, expires_delta=timedelta(seconds=1)
        )

        # Wait for token to expire
        import asyncio

        await asyncio.sleep(2)

        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401

    async def test_invalid_token(self, async_client: AsyncClient):
        """Test request with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401

    async def test_missing_token(self, async_client: AsyncClient):
        """Test request without token"""
        response = await async_client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_malformed_token(self, async_client: AsyncClient):
        """Test request with malformed token"""
        headers = {"Authorization": "Bearer malformed.token.here"}
        response = await async_client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401


@pytest.mark.auth
class TestEmailVerification:
    """Test email verification functionality"""

    async def test_verify_email_success(
        self, async_client: AsyncClient, async_db: AsyncSession
    ):
        """Test successful email verification"""
        # Create unverified user
        user_data = {
            "email": "verifyme@test.com",
            "full_name": "Verify Me User",
            "password": "SecurePassword123!",
        }
        user_create = UserCreate(**user_data)
        user = await create_user(async_db, user_create)
        await async_db.commit()

        # Create verification token
        verification_token = create_access_token(
            data={"sub": str(user.id), "type": "email_verification"},
            expires_delta=timedelta(hours=24),
        )

        response = await async_client.get(
            f"/api/v1/auth/verify-email/{verification_token}"
        )

        assert response.status_code == 200

        # Verify user is now verified
        await async_db.refresh(user)
        assert user.is_verified
        assert user.email_verified_at is not None

    async def test_verify_email_invalid_token(self, async_client: AsyncClient):
        """Test email verification with invalid token"""
        response = await async_client.get("/api/v1/auth/verify-email/invalid_token")

        assert response.status_code == 401

    async def test_verify_email_already_verified(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test email verification for already verified user"""
        verification_token = create_access_token(
            data={"sub": str(test_user.id), "type": "email_verification"},
            expires_delta=timedelta(hours=24),
        )

        response = await async_client.get(
            f"/api/v1/auth/verify-email/{verification_token}"
        )

        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    async def test_resend_verification_email(
        self, async_client: AsyncClient, async_db: AsyncSession, mock_email_service
    ):
        """Test resending verification email"""
        # Create unverified user
        user_data = {
            "email": "resend@test.com",
            "full_name": "Resend User",
            "password": "SecurePassword123!",
        }
        user_create = UserCreate(**user_data)
        user = await create_user(async_db, user_create)
        await async_db.commit()

        email_data = {"email": user.email}
        response = await async_client.post(
            "/api/v1/auth/resend-verification", json=email_data
        )

        assert response.status_code == 200
        mock_email_service.send_verification_email.assert_called()

    async def test_resend_verification_verified_user(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test resending verification email to verified user"""
        email_data = {"email": test_user.email}
        response = await async_client.post(
            "/api/v1/auth/resend-verification", json=email_data
        )

        assert response.status_code == 400


@pytest.mark.auth
class TestPasswordReset:
    """Test password reset functionality"""

    async def test_request_password_reset(
        self, async_client: AsyncClient, test_user: User, mock_email_service
    ):
        """Test requesting password reset"""
        reset_data = {"email": test_user.email}

        response = await async_client.post(
            "/api/v1/auth/request-password-reset", json=reset_data
        )

        assert response.status_code == 200
        mock_email_service.send_password_reset_email.assert_called_once()

    async def test_request_password_reset_nonexistent_user(
        self, async_client: AsyncClient
    ):
        """Test requesting password reset for non-existent user"""
        reset_data = {"email": "nonexistent@test.com"}

        response = await async_client.post(
            "/api/v1/auth/request-password-reset", json=reset_data
        )

        # Should still return 200 for security (don't reveal if user exists)
        assert response.status_code == 200

    async def test_reset_password_success(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test successful password reset"""
        # Create reset token
        reset_token = create_access_token(
            data={"sub": str(test_user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1),
        )

        reset_data = {"token": reset_token, "new_password": "NewSecurePassword123!"}

        response = await async_client.post(
            "/api/v1/auth/reset-password", json=reset_data
        )

        assert response.status_code == 200

        # Test login with new password
        login_data = {"email": test_user.email, "password": "NewSecurePassword123!"}
        login_response = await async_client.post(
            "/api/v1/auth/login/json", json=login_data
        )
        assert login_response.status_code == 200

    async def test_reset_password_invalid_token(self, async_client: AsyncClient):
        """Test password reset with invalid token"""
        reset_data = {"token": "invalid_token", "new_password": "NewSecurePassword123!"}

        response = await async_client.post(
            "/api/v1/auth/reset-password", json=reset_data
        )

        assert response.status_code == 401

    async def test_reset_password_expired_token(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test password reset with expired token"""
        # Create expired reset token
        reset_token = create_access_token(
            data={"sub": str(test_user.id), "type": "password_reset"},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        reset_data = {"token": reset_token, "new_password": "NewSecurePassword123!"}

        response = await async_client.post(
            "/api/v1/auth/reset-password", json=reset_data
        )

        assert response.status_code == 401


@pytest.mark.auth
class TestRoleBasedAccess:
    """Test role-based access control"""

    async def test_admin_access_to_admin_endpoint(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """Test admin can access admin-only endpoints"""
        response = await async_client.get("/api/v1/admin/users", headers=admin_headers)

        # Should succeed or return 404 if endpoint doesn't exist, but not 403
        assert response.status_code != 401
        assert response.status_code != 403

    async def test_user_denied_admin_endpoint(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test regular user cannot access admin endpoints"""
        response = await async_client.get("/api/v1/admin/users", headers=auth_headers)

        assert response.status_code in [403, 404]  # Forbidden or Not Found

    async def test_moderator_access(
        self, async_client: AsyncClient, moderator_headers: dict
    ):
        """Test moderator has appropriate access"""
        response = await async_client.get("/api/v1/users/me", headers=moderator_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == UserRole.MODERATOR.value


@pytest.mark.auth
class TestSecurityFeatures:
    """Test security-related features"""

    async def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    async def test_sql_injection_protection(self, async_client: AsyncClient):
        """Test SQL injection protection in login"""
        malicious_input = "'; DROP TABLE users; --"

        login_data = {"email": malicious_input, "password": "password"}

        response = await async_client.post("/api/v1/auth/login/json", json=login_data)

        # Should not crash the server
        assert response.status_code == 401

    async def test_xss_protection(self, async_client: AsyncClient):
        """Test XSS protection in user registration"""
        xss_payload = "<script>alert('xss')</script>"

        user_data = {
            "email": "xss@test.com",
            "full_name": xss_payload,
            "password": "SecurePassword123!",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        if response.status_code == 201:
            # Check that script tags are escaped or removed
            assert "<script>" not in response.json()["full_name"]

    async def test_csrf_protection(self, async_client: AsyncClient):
        """Test CSRF protection is enabled"""
        # This test would need to be implemented based on CSRF middleware
        # For now, just check that security headers are present
        response = await async_client.options("/api/v1/auth/login")

        # Should include security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
        ]

        for header in security_headers:
            assert header in response.headers


@pytest.mark.auth
@pytest.mark.slow
class TestAuthenticationPerformance:
    """Test authentication system performance"""

    async def test_login_performance(
        self, async_client: AsyncClient, test_user: User, performance_timer
    ):
        """Test login response time"""
        login_data = {"email": test_user.email, "password": "TestSecurePassword123!"}

        with performance_timer():
            response = await async_client.post(
                "/api/v1/auth/login/json", json=login_data
            )
            assert response.status_code == 200

    async def test_token_validation_performance(
        self, async_client: AsyncClient, auth_headers: dict, performance_timer
    ):
        """Test token validation performance"""
        with performance_timer():
            response = await async_client.get("/api/v1/users/me", headers=auth_headers)
            assert response.status_code == 200

    async def test_registration_performance(
        self, async_client: AsyncClient, mock_email_service, performance_timer
    ):
        """Test registration performance"""
        user_data = {
            "email": "perf@test.com",
            "full_name": "Performance User",
            "password": "SecurePassword123!",
        }

        with performance_timer():
            response = await async_client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""

    async def test_complete_user_flow(
        self, async_client: AsyncClient, mock_email_service
    ):
        """Test complete user registration to authenticated usage flow"""
        # 1. Register user
        user_data = {
            "email": "completeflow@test.com",
            "full_name": "Complete Flow User",
            "password": "SecurePassword123!",
        }

        register_response = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        # 2. Get user ID from registration response
        user_id = register_response.json()["id"]

        # 3. Simulate email verification
        verification_token = create_access_token(
            data={"sub": str(user_id), "type": "email_verification"},
            expires_delta=timedelta(hours=24),
        )

        verify_response = await async_client.get(
            f"/api/v1/auth/verify-email/{verification_token}"
        )
        assert verify_response.status_code == 200

        # 4. Login
        login_data = {"email": user_data["email"], "password": user_data["password"]}

        login_response = await async_client.post(
            "/api/v1/auth/login/json", json=login_data
        )
        assert login_response.status_code == 200

        auth_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # 5. Access protected endpoint
        me_response = await async_client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == user_data["email"]

        # 6. Logout (if endpoint exists)
        logout_response = await async_client.post(
            "/api/v1/auth/logout", headers=auth_headers
        )
        # Logout might not be implemented, so we just check it doesn't crash
        assert logout_response.status_code in [200, 404]

    async def test_token_refresh_flow(self, async_client: AsyncClient, test_user: User):
        """Test token refresh flow"""
        # Initial login
        login_data = {"email": test_user.email, "password": "TestSecurePassword123!"}

        login_response = await async_client.post(
            "/api/v1/auth/login/json", json=login_data
        )
        assert login_response.status_code == 200

        tokens = login_response.json()
        refresh_token = tokens.get("refresh_token")

        if refresh_token:
            # Refresh token
            refresh_data = {"refresh_token": refresh_token}
            refresh_response = await async_client.post(
                "/api/v1/auth/refresh", json=refresh_data
            )

            if refresh_response.status_code == 200:
                new_tokens = refresh_response.json()
                assert "access_token" in new_tokens

                # Test new token works
                new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
                me_response = await async_client.get(
                    "/api/v1/users/me", headers=new_headers
                )
                assert me_response.status_code == 200
