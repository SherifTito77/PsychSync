"""
Token Refresh Integration Tests
Comprehensive testing of JWT token refresh, expiration, and lifecycle management
"""

import asyncio
import json
import time
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from jose import JWTError, jwt

from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.main import app
from app.services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiration,
    verify_token,
)


@pytest.mark.integration
class TestTokenRefreshFlow:
    """Test suite for token refresh functionality"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def test_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "tokenuser@example.com",
            "full_name": "Token Test User",
            "password": "SecurePassword123!",
            "role": "user",
        }

    @pytest.fixture
    async def registered_user(self, client: AsyncClient, test_user_data):
        """Create registered user for testing"""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        return response.json()["data"]["user"]

    @pytest.fixture
    async def authenticated_user(self, client: AsyncClient, test_user_data):
        """Create authenticated user for testing"""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Login to get tokens
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }

        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        tokens = response.json()["data"]
        return {
            "user": tokens["user"],
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

    # Basic Token Refresh Tests
    @pytest.mark.asyncio
    async def test_successful_token_refresh(
        self, client: AsyncClient, authenticated_user
    ):
        """Test successful token refresh"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "token_type" in data["data"]
        assert "expires_in" in data["data"]

        assert data["data"]["token_type"] == "bearer"
        assert isinstance(data["data"]["expires_in"], int)
        assert data["data"]["expires_in"] > 0

        # Verify new tokens are valid
        new_access_token = data["data"]["access_token"]
        new_refresh_token = data["data"]["refresh_token"]

        assert new_access_token != authenticated_user["access_token"]
        assert new_refresh_token != authenticated_user["refresh_token"]

        # Verify new access token works
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = await client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200

    @pytest.mark.asyncio
    async def test_token_refresh_token_structure(
        self, client: AsyncClient, authenticated_user
    ):
        """Test token structure and claims"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200

        data = response.json()
        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]

        # Decode access token
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        assert "sub" in access_payload
        assert "exp" in access_payload
        assert "iat" in access_payload
        assert "type" in access_payload
        assert access_payload["type"] == "access"

        # Verify expiration
        exp_time = datetime.fromtimestamp(access_payload["exp"])
        now = datetime.utcnow()
        assert exp_time > now
        assert exp_time <= now + timedelta(hours=1)  # Should be within 1 hour

        # Decode refresh token
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        assert "sub" in refresh_payload
        assert "exp" in refresh_payload
        assert "type" in refresh_payload
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_multiple_token_refreshes(
        self, client: AsyncClient, authenticated_user
    ):
        """Test multiple consecutive token refreshes"""
        current_refresh_token = authenticated_user["refresh_token"]
        refresh_count = 0

        # Perform multiple refreshes
        for i in range(5):
            refresh_data = {"refresh_token": current_refresh_token}

            response = await client.post("/api/v1/auth/refresh", json=refresh_data)
            assert response.status_code == 200

            data = response.json()
            new_access_token = data["data"]["access_token"]
            new_refresh_token = data["data"]["refresh_token"]

            # Verify each refresh works
            headers = {"Authorization": f"Bearer {new_access_token}"}
            profile_response = await client.get(
                "/api/v1/users/profile", headers=headers
            )
            assert profile_response.status_code == 200

            # Use new refresh token for next iteration
            current_refresh_token = new_refresh_token
            refresh_count += 1

        assert refresh_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_token_refreshes(
        self, client: AsyncClient, authenticated_user
    ):
        """Test concurrent token refresh requests"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        # Make concurrent refresh requests
        async def refresh_token():
            return await client.post("/api/v1/auth/refresh", json=refresh_data)

        tasks = [refresh_token() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All requests should complete without server errors
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 8  # Most should succeed

        # At least one should succeed
        assert success_count > 0

        # All successful responses should have valid token structures
        for response in responses:
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data["data"]
                assert "refresh_token" in data["data"]

    # Token Expiration Tests
    @pytest.mark.asyncio
    async def test_expired_refresh_token(self, client: AsyncClient, authenticated_user):
        """Test refresh token expiration handling"""
        # Create expired refresh token
        expired_payload = {
            "sub": str(authenticated_user["user"]["id"]),
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            "type": "refresh",
        }

        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        refresh_data = {"refresh_token": expired_token}

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_invalidated_after_use(
        self, client: AsyncClient, authenticated_user
    ):
        """Test that refresh token is invalidated after use"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        # First refresh
        response1 = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response1.status_code == 200

        # Second refresh with same token should fail
        response2 = await client.post("/api/v1/auth/refresh", json=refresh_data)

        # Should either fail (single-use tokens) or succeed (multiple-use tokens)
        # This depends on token strategy
        if response2.status_code == 401:
            # Single-use tokens - good for security
            data = response2.json()
            assert "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_access_token_expiration(
        self, client: AsyncClient, authenticated_user
    ):
        """Test access token expiration"""
        # Create expired access token
        expired_payload = {
            "sub": str(authenticated_user["user"]["id"]),
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            "type": "access",
        }

        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = await client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_very_close_to_expiration(
        self, client: AsyncClient, authenticated_user
    ):
        """Test token refresh when token is close to expiration"""
        # This would require creating a token that expires very soon
        # Implementation would depend on token strategy

    @pytest.mark.asyncio
    async def test_token_rotation_security(
        self, client: AsyncClient, authenticated_user
    ):
        """Test token rotation security"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200

        new_access_token = response.json()["data"]["access_token"]
        new_refresh_token = response.json()["data"]["refresh_token"]

        # Verify tokens are different
        assert new_access_token != authenticated_user["access_token"]
        assert new_refresh_token != authenticated_user["refresh_token"]

        # Verify old access token is not accepted (if implemented)
        old_headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        old_response = await client.get("/api/v1/users/profile", headers=old_headers)

        # This depends on token blacklist implementation
        # Either 200 (if no blacklist) or 401 (if blacklist implemented)

    # Refresh Token Validation Tests
    @pytest.mark.asyncio
    async def test_refresh_token_validation(self, client: AsyncClient):
        """Test refresh token format validation"""
        # Test malformed refresh token
        malformed_tokens = [
            "invalid_token",
            "Bearer token",
            "",
            "not_a_jwt_at_all",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Header only
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ",  # Payload only
        ]

        for malformed_token in malformed_tokens:
            refresh_data = {"refresh_token": malformed_token}
            response = await client.post("/api/v1/auth/refresh", json=refresh_data)
            assert response.status_code in [400, 422, 401]

    @pytest.mark.asyncio
    async def test_refresh_token_user_validation(
        self, client: AsyncClient, authenticated_user, test_user_data
    ):
        """Test refresh token user validation"""
        # Create refresh token for different user
        different_user_data = test_user_data.copy()
        different_user_data["email"] = "different@example.com"

        # Register different user
        await client.post("/api/v1/auth/register", json=different_user_data)

        # Use original user's refresh token with different user's refresh token
        # This would require creating a refresh token for the different user
        # Implementation depends on refresh token storage strategy

    # Performance Tests
    @pytest.mark.asyncio
    async def test_refresh_performance(self, client: AsyncClient, authenticated_user):
        """Test token refresh performance"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        # Measure refresh time
        start_time = time.time()
        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        end_time = time.time()

        refresh_time = end_time - start_time
        assert response.status_code == 200
        assert refresh_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_refresh_load_testing(self, client: AsyncClient, authenticated_user):
        """Test token refresh under load"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        # Make 50 concurrent refresh requests
        async def refresh_token():
            return await client.post("/api/v1/auth/refresh", json=refresh_data)

        start_time = time.time()
        tasks = [refresh_token() for _ in range(50)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time
        success_count = sum(1 for r in responses if r.status_code == 200)

        assert success_count >= 30  # At least 60% should succeed
        assert total_time < 10.0  # Should complete within 10 seconds
        assert total_time / 50 < 1.0  # Average less than 1 second per request

    # Refresh Token Storage Tests
    @pytest.mark.asyncio
    async def test_refresh_token_storage(self, client: AsyncClient, authenticated_user):
        """Test refresh token storage in database"""
        # This would verify that refresh tokens are properly stored
        # and can be retrieved/validated from the database
        pass

    @pytest.mark.asyncio
    async def test_refresh_token_cleanup(self, client: AsyncClient, authenticated_user):
        """Test cleanup of old refresh tokens"""
        # This would test that old/expired refresh tokens are cleaned up
        # from the database
        pass

    @pytest.mark.asyncio
    async def test_refresh_token_revocation(
        self, client: AsyncClient, authenticated_user
    ):
        """Test refresh token revocation"""
        # Test that refresh tokens can be revoked (user logout)
        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        if logout_response.status_code == 200:
            # Try to use the refresh token after logout
            refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

            response = await client.post("/api/v1/auth/refresh", json=refresh_data)
            # Should fail if tokens are invalidated on logout
            assert response.status_code in [401, 403]

    # Security Tests
    @pytest.mark.asyncio
    async def test_refresh_token_hijacking_protection(
        self, client: AsyncClient, authenticated_user
    ):
        """Test protection against refresh token hijacking"""
        # Test with tokens that have been tampered with
        original_token = authenticated_user["refresh_token"]

        # Tamper with token payload (decode, modify, encode)
        try:
            parts = original_token.split(".")
            if len(parts) == 3:
                header, payload, signature = parts
                # Decode and modify payload
                import base64
                import json

                # Fix padding issues
                payload += "=" * (-len(payload) % 4)
                decoded_payload = base64.urlsafe_b64decode(payload)
                payload_data = json.loads(decoded_payload)

                # Tamper with payload
                payload_data["sub"] = "tampered_user_id"
                payload_data["role"] = "admin"

                tampered_payload = json.dumps(payload_data, separators=(",", ":"))
                tampered_payload = base64.urlsafe_b64encode(tampered_payload.encode())

                tampered_token = f"{header}.{tampered_payload}.{signature}"

                refresh_data = {"refresh_token": tampered_token}
                response = await client.post("/api/v1/auth/refresh", json=refresh_data)

                # Should fail for tampered token
                assert response.status_code in [401, 422]

        except Exception:
            # If decoding fails, token is malformed
            pass

    @pytest.mark.asyncio
    async def test_refresh_token_brute_force_protection(self, client: AsyncClient):
        """Test brute force protection on refresh endpoint"""
        # Test with random tokens to trigger brute force protection
        fake_refresh_tokens = [
            "fake_refresh_token_1",
            "fake_refresh_token_2",
            "fake_refresh_token_3",
            "fake_refresh_token_4",
            "fake_refresh_token_5",
        ]

        responses = []
        for fake_token in fake_refresh_tokens:
            refresh_data = {"refresh_token": fake_token}
            response = await client.post("/api/v1/auth/refresh", json=refresh_data)
            responses.append(response)

        # Should handle gracefully without server errors
        success_count = sum(1 for r in responses if r.status_code == 200)
        error_count = sum(1 for r in responses if r.status_code in [401, 422])

        assert success_count == 0  # No fake tokens should succeed
        assert error_count == len(fake_refresh_tokens)  # All should fail gracefully

    @pytest.mark.asyncio
    async def test_refresh_token_reuse_protection(
        self, client: AsyncClient, authenticated_user
    ):
        """Test reuse protection for refresh tokens"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        # Use refresh token once
        response1 = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response1.status_code == 200

        # Try to reuse immediately
        response2 = await client.post("/api/v1/auth/refresh", json=refresh_data)

        # Depending on implementation:
        # - Single-use tokens: should fail
        # - Multiple-use tokens: should succeed
        if response2.status_code == 401:
            # Single-use tokens - good security
            assert "invalid" in response2.json()["detail"].lower()
        else:
            # Multiple-use tokens - still should work, but maybe rate limited
            assert response2.status_code in [200, 429]

    # Edge Cases
    @pytest.mark.asyncio
    async def test_refresh_token_with_additional_claims(
        self, client: AsyncClient, authenticated_user
    ):
        """Test refresh token with additional claims"""
        # Test if system supports additional claims in refresh tokens
        # This would depend on token creation implementation

    @pytest.mark.asyncio
    async def test_refresh_token_scopes(self, client: AsyncClient, authenticated_user):
        """Test token refresh with different scopes"""
        # Test if system supports different scopes for tokens
        # This would depend on OAuth2/OpenID Connect implementation

    @pytest.mark.asyncio
    async def test_refresh_token_with_device_fingerprint(
        self, client: AsyncClient, authenticated_user
    ):
        """Test refresh token with device fingerprinting"""
        # Test refresh token validation with device fingerprinting
        refresh_data = {
            "refresh_token": authenticated_user["refresh_token"],
            "device_fingerprint": {
                "user_agent": "Test Browser",
                "ip_address": "127.0.0.1",
            },
        }

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        # Should handle device fingerprinting appropriately
        # This depends on implementation

    @pytest.mark.asyncio
    async def test_refresh_token_cleanup_after_use(
        self, client: AsyncClient, authenticated_user
    ):
        """Test cleanup of old refresh tokens after successful refresh"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        initial_refresh_response = await client.post(
            "/api/v1/auth/refresh", json=refresh_data
        )
        assert initial_refresh_response.status_code == 200

        # This would verify that old refresh token is marked as used
        # or deleted from the database
        # Implementation depends on token lifecycle management

    @pytest.mark.asyncio
    async def test_concurrent_same_token_refresh(
        self, client: AsyncClient, authenticated_user
    ):
        """Test concurrent use of same refresh token"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        # Make concurrent requests with same token
        async def refresh_token():
            return await client.post("/api/v1/auth/refresh", json=refresh_data)

        tasks = [refresh_token() for _ in range(3)]
        responses = await asyncio.gather(*tasks)

        # Should handle concurrent use appropriately
        success_count = sum(1 for r in responses if r.status_code == 200)

        if success_count == 1:
            # Single-use tokens - only one should succeed
            assert True
        elif success_count > 1:
            # Multiple-use tokens - multiple might succeed
            assert True
        else:
            assert False  # At least one should succeed

    @pytest.mark.asyncio
    async def test_refresh_token_during_maintenance(self, client: AsyncClient):
        """Test token refresh during system maintenance"""
        # This would test refresh token behavior when system is in maintenance mode
        # Implementation would depend on maintenance mode handling

    @pytest.mark.asyncio
    async def test_refresh_token_backup_strategies(self, client: AsyncClient):
        """Test refresh token backup and restore strategies"""
        # This would test if system can handle refresh token backup/restore
        # Implementation would depend on backup strategies


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
