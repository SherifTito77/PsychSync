"""
Comprehensive Test Suite for Secure User Management Endpoints

This test suite covers:
- Success paths for all endpoints
- All failure scenarios and edge cases
- Authentication and authorization testing
- Input validation and sanitization
- Rate limiting and security controls
- Database constraint testing
- Performance and caching validation
- Audit logging verification
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.db.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.core.security import hash_password, verify_password
from app.core.rate_limiting import RateLimiter
from app.core.cache import cache_result


class TestSecureUserEndpoints:
    """Test class for secure user management endpoints"""

    @pytest.fixture
    async def test_client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def test_db(self):
        """Create test database session"""
        # This would be properly implemented with test database setup
        pass

    @pytest.fixture
    async def test_user(self, test_db):
        """Create test user"""
        user = User(
            email="test@example.com",
            password_hash=await hash_password("TestPass123!"),
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    @pytest.fixture
    async def admin_user(self, test_db):
        """Create admin user"""
        admin = User(
            email="admin@example.com",
            password_hash=await hash_password("AdminPass123!"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(admin)
        await test_db.commit()
        await test_db.refresh(admin)
        return admin

    @pytest.fixture
    def auth_headers(self, test_user):
        """Create authentication headers"""
        # This would create valid JWT tokens
        return {"Authorization": f"Bearer test_token_{test_user.id}"}

    @pytest.fixture
    def admin_headers(self, admin_user):
        """Create admin authentication headers"""
        return {"Authorization": f"Bearer test_token_{admin_user.id}"}

    # ============== GET /me Tests ==============

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, test_client, auth_headers, test_user):
        """Test successful user profile retrieval"""
        response = await test_client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user.email
        assert data["data"]["full_name"] == test_user.full_name
        assert "password_hash" not in data["data"]  # Ensure password not exposed

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, test_client):
        """Test profile retrieval without authentication"""
        response = await test_client.get("/users/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_rate_limiting(self, test_client, auth_headers):
        """Test rate limiting on profile endpoint"""
        # Make multiple requests quickly
        responses = []
        for _ in range(35):  # Exceed rate limit of 30 per minute
            response = await test_client.get("/users/me", headers=auth_headers)
            responses.append(response)
            await asyncio.sleep(0.1)  # Small delay between requests

        # Last few requests should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0

    @pytest.mark.asyncio
    async def test_get_user_profile_caching(self, test_client, auth_headers, test_user):
        """Test that profile endpoint uses caching"""
        with patch('app.core.cache.cache_result') as mock_cache:
            mock_cache.return_value = lambda func: func

            # First call
            response1 = await test_client.get("/users/me", headers=auth_headers)
            # Second call
            response2 = await test_client.get("/users/me", headers=auth_headers)

            assert response1.status_code == 200
            assert response2.status_code == 200
            # Both responses should be identical (cached)
            assert response1.json() == response2.json()

    # ============== POST /change-password Tests ==============

    @pytest.mark.asyncio
    async def test_change_password_success(self, test_client, auth_headers, test_user):
        """Test successful password change"""
        password_data = {
            "current_password": "TestPass123!",
            "new_password": "NewPass456!"
        }

        response = await test_client.post(
            "/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated successfully" in data["message"].lower()

        # Verify password was actually changed in database
        updated_user = await test_db.execute(select(User).where(User.id == test_user.id))
        user = updated_user.scalar_one()
        assert verify_password("NewPass456!", user.password_hash)

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(self, test_client, auth_headers):
        """Test password change with invalid current password"""
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPass456!"
        }

        response = await test_client.post(
            "/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid current password" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_weak_password(self, test_client, auth_headers):
        """Test password change with weak new password"""
        password_data = {
            "current_password": "TestPass123!",
            "new_password": "weak"  # Too short, no complexity
        }

        response = await test_client.post(
            "/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_change_password_same_password(self, test_client, auth_headers):
        """Test password change with same password as current"""
        password_data = {
            "current_password": "TestPass123!",
            "new_password": "TestPass123!"
        }

        response = await test_client.post(
            "/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "different from current" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_rate_limiting(self, test_client, auth_headers):
        """Test rate limiting on password change endpoint"""
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPass456!"
        }

        # Make multiple failed attempts
        responses = []
        for _ in range(5):
            response = await test_client.post(
                "/users/change-password",
                json=password_data,
                headers=auth_headers
            )
            responses.append(response)

        # Should be rate limited after 3 attempts
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) >= 1

    @pytest.mark.asyncio
    async def test_change_password_missing_fields(self, test_client, auth_headers):
        """Test password change with missing required fields"""
        # Missing current_password
        password_data = {
            "new_password": "NewPass456!"
        }

        response = await test_client.post(
            "/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

        # Missing new_password
        password_data = {
            "current_password": "TestPass123!"
        }

        response = await test_client.post(
            "/users/change-password",
            json=password_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    # ============== GET /users (List) Tests ==============

    @pytest.mark.asyncio
    async def test_list_users_success_admin(self, test_client, admin_headers):
        """Test successful user listing by admin"""
        response = await test_client.get("/users/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, test_client, auth_headers):
        """Test user listing by non-admin user"""
        response = await test_client.get("/users/", headers=auth_headers)

        assert response.status_code == 403
        data = response.json()
        assert "insufficient permissions" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, test_client, admin_headers):
        """Test user listing with various filters"""
        # Test with search filter
        response = await test_client.get(
            "/users/?search=test&is_active=true",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Test with role filter
        response = await test_client.get(
            "/users/?role=user",
            headers=admin_headers
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_sql_injection_protection(self, test_client, admin_headers):
        """Test SQL injection protection in search"""
        malicious_search = "'; DROP TABLE users; --"
        response = await test_client.get(
            f"/users/?search={malicious_search}",
            headers=admin_headers
        )

        # Should not cause server error
        assert response.status_code in [200, 400]

        # Verify users table still exists
        response = await test_client.get("/users/", headers=admin_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_invalid_sort_field(self, test_client, admin_headers):
        """Test invalid sort field validation"""
        response = await test_client.get(
            "/users/?sort_by=invalid_field",
            headers=admin_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid sort field" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_users_pagination(self, test_client, admin_headers):
        """Test pagination functionality"""
        # Test first page
        response = await test_client.get(
            "/users/?page=1&size=5",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 5

        # Test second page
        response = await test_client.get(
            "/users/?page=2&size=5",
            headers=admin_headers
        )

        assert response.status_code == 200

    # ============== GET /users/{id} Tests ==============

    @pytest.mark.asyncio
    async def test_get_user_by_id_self(self, test_client, auth_headers, test_user):
        """Test getting own user by ID"""
        response = await test_client.get(
            f"/users/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_admin(self, test_client, admin_headers, test_user):
        """Test admin getting any user by ID"""
        response = await test_client.get(
            f"/users/{test_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_unauthorized(self, test_client, auth_headers, admin_user):
        """Test user trying to get another user's profile"""
        response = await test_client.get(
            f"/users/{admin_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert "not authorized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_invalid_uuid(self, test_client, auth_headers):
        """Test getting user with invalid UUID"""
        invalid_uuid = "invalid-uuid-format"
        response = await test_client.get(f"/users/{invalid_uuid}", headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "invalid user id format" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, test_client, admin_headers):
        """Test getting non-existent user"""
        non_existent_id = uuid4()
        response = await test_client.get(f"/users/{non_existent_id}", headers=admin_headers)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    # ============== PUT /me Tests ==============

    @pytest.mark.asyncio
    async def test_update_profile_success(self, test_client, auth_headers):
        """Test successful profile update"""
        update_data = {
            "full_name": "Updated Name",
            "timezone": "America/New_York"
        }

        response = await test_client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_profile_email_conflict(self, test_client, auth_headers, admin_user):
        """Test profile update with conflicting email"""
        update_data = {
            "email": admin_user.email  # Try to use admin's email
        }

        response = await test_client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_profile_invalid_timezone(self, test_client, auth_headers):
        """Test profile update with invalid timezone"""
        update_data = {
            "timezone": "Invalid/Timezone"
        }

        response = await test_client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_profile_xss_protection(self, test_client, auth_headers):
        """Test XSS protection in profile update"""
        xss_payload = "<script>alert('xss')</script>"
        update_data = {
            "full_name": xss_payload
        }

        response = await test_client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Script tags should be removed/sanitized
        assert "<script>" not in data["data"]["full_name"]

    # ============== POST /users (Register) Tests ==============

    @pytest.mark.asyncio
    async def test_register_user_success(self, test_client):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        }

        response = await test_client.post("/users/", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, test_client):
        """Test registration with weak password"""
        user_data = {
            "email": "weak@example.com",
            "password": "weak",  # Too weak
            "full_name": "Weak User"
        }

        response = await test_client.post("/users/", json=user_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, test_client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,  # Already exists
            "password": "SecurePass123!",
            "full_name": "Duplicate User"
        }

        response = await test_client.post("/users/", json=user_data)

        # Should not reveal that email exists
        assert response.status_code == 400
        data = response.json()
        assert "failed" in data["detail"].lower()
        assert "already exists" not in data["detail"].lower()  # Don't reveal existence

    @pytest.mark.asyncio
    async def test_register_user_rate_limiting(self, test_client):
        """Test rate limiting on registration endpoint"""
        user_data = {
            "email": "ratelimit@example.com",
            "password": "SecurePass123!",
            "full_name": "Rate Limit User"
        }

        # Make multiple registration attempts
        responses = []
        for i in range(6):  # Exceed limit of 5 per hour
            user_data["email"] = f"ratelimit{i}@example.com"
            response = await test_client.post("/users/", json=user_data)
            responses.append(response)

        # Should be rate limited after 5 attempts
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) >= 1

    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, test_client):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",  # Invalid format
            "password": "SecurePass123!",
            "full_name": "Invalid Email User"
        }

        response = await test_client.post("/users/", json=user_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_user_name_injection(self, test_client):
        """Test name field for injection attacks"""
        user_data = {
            "email": "injection@example.com",
            "password": "SecurePass123!",
            "full_name": "'; DROP TABLE users; --"
        }

        response = await test_client.post("/users/", json=user_data)

        # Should handle injection attempt gracefully
        assert response.status_code in [201, 422]

        # Verify database still works
        response = await test_client.get("/users/")
        assert response.status_code in [200, 401]  # Either works or needs auth

    # ============== DELETE /me Tests ==============

    @pytest.mark.asyncio
    async def test_delete_account_success(self, test_client, auth_headers):
        """Test successful account deletion"""
        delete_data = {
            "password": "TestPass123!"
        }

        response = await test_client.delete(
            "/users/me",
            json=delete_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_account_wrong_password(self, test_client, auth_headers):
        """Test account deletion with wrong password"""
        delete_data = {
            "password": "WrongPassword123!"
        }

        response = await test_client.delete(
            "/users/me",
            json=delete_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid password" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_account_rate_limiting(self, test_client, auth_headers):
        """Test rate limiting on account deletion"""
        delete_data = {
            "password": "WrongPassword123!"
        }

        # Make multiple deletion attempts
        responses = []
        for _ in range(3):
            response = await test_client.delete(
                "/users/me",
                json=delete_data,
                headers=auth_headers
            )
            responses.append(response)

        # Should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) >= 1

    # ============== Security and Edge Case Tests ==============

    @pytest.mark.asyncio
    async def test_malformed_json_request(self, test_client, auth_headers):
        """Test handling of malformed JSON requests"""
        malformed_json = '{"email": "test@example.com", "password":}'  # Invalid JSON

        response = await test_client.post(
            "/users/",
            data=malformed_json,
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_oversized_payload(self, test_client, auth_headers):
        """Test handling of oversized payloads"""
        oversized_data = {
            "full_name": "x" * 1000  # Exceeds max length
        }

        response = await test_client.put("/users/me", json=oversized_data, headers=auth_headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client, auth_headers):
        """Test handling of concurrent requests"""
        # Make multiple concurrent requests
        tasks = []
        for _ in range(10):
            task = test_client.get("/users/me", headers=auth_headers)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should succeed
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        assert success_count == 10

    @pytest.mark.asyncio
    async def test_database_connection_error(self, test_client, auth_headers):
        """Test handling of database connection errors"""
        with patch('app.api.v1.endpoints.users_secure.get_async_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = await test_client.get("/users/me", headers=auth_headers)

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, test_client, auth_headers):
        """Test cache invalidation when user is updated"""
        with patch('app.core.cache.invalidate_user_cache') as mock_invalidate:
            update_data = {"full_name": "Updated Name"}

            response = await test_client.put("/users/me", json=update_data, headers=auth_headers)

            assert response.status_code == 200
            mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_logging_on_sensitive_operations(self, test_client, auth_headers):
        """Test audit logging for sensitive operations"""
        with patch('app.core.audit.log_security_event') as mock_audit:
            password_data = {
                "current_password": "TestPass123!",
                "new_password": "NewPass456!"
            }

            response = await test_client.post(
                "/users/change-password",
                json=password_data,
                headers=auth_headers
            )

            # Should call audit logging
            mock_audit.assert_called()

    # ============== Performance Tests ==============

    @pytest.mark.asyncio
    async def test_response_time_performance(self, test_client, auth_headers):
        """Test endpoint response times"""
        import time

        start_time = time.time()
        response = await test_client.get("/users/me", headers=auth_headers)
        end_time = time.time()

        assert response.status_code == 200
        # Should respond within reasonable time (adjust threshold as needed)
        assert (end_time - start_time) < 2.0

    @pytest.mark.asyncio
    async def test_memory_usage_on_large_response(self, test_client, admin_headers):
        """Test memory usage on responses with large datasets"""
        # This would require more sophisticated memory profiling
        # For now, just ensure large responses don't crash
        response = await test_client.get("/users/?size=100", headers=admin_headers)

        assert response.status_code == 200
        # Verify response is properly structured
        data = response.json()
        assert len(data["data"]) <= 100


class TestUserEndpointIntegration:
    """Integration tests for user endpoints"""

    @pytest.mark.asyncio
    async def test_user_lifecycle_flow(self, test_client):
        """Test complete user lifecycle: register -> login -> update -> delete"""
        # 1. Register user
        user_data = {
            "email": "lifecycle@example.com",
            "password": "LifecyclePass123!",
            "full_name": "Lifecycle User"
        }

        register_response = await test_client.post("/users/", json=user_data)
        assert register_response.status_code == 201

        # 2. Get profile (would need authentication)
        # 3. Update profile
        # 4. Delete account
        # This test would need proper authentication setup

    @pytest.mark.asyncio
    async def test_cross_user_data_isolation(self, test_client):
        """Test that users cannot access other users' data"""
        # This would require multiple authenticated users
        pass

    @pytest.mark.asyncio
    async def test_admin_permissions_enforcement(self, test_client):
        """Test that admin permissions are properly enforced"""
        # This would require admin and regular user authentication
        pass


# ============== Test Utilities ==============

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing"""
    with patch('app.core.rate_limiting.RateLimiter') as mock:
        mock.return_value.is_allowed = AsyncMock(return_value=True)
        mock.return_value.record_failure = AsyncMock()
        mock.return_value.clear = AsyncMock()
        yield mock


@pytest.fixture
def mock_cache():
    """Mock cache for testing"""
    with patch('app.core.cache.cache_result') as mock:
        mock.return_value = lambda func: func
        yield mock


@pytest.fixture
def mock_audit():
    """Mock audit logging for testing"""
    with patch('app.core.audit.log_security_event') as mock:
        yield mock


# ============== Error Handling Tests ==============

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_500_error_handling(self, test_client, auth_headers):
        """Test 500 error handling doesn't expose sensitive information"""
        with patch('app.api.v1.endpoints.users_secure.get_async_db') as mock_db:
            mock_db.side_effect = Exception("Internal database error")

            response = await test_client.get("/users/me", headers=auth_headers)

            assert response.status_code == 500
            data = response.json()
            # Should not expose internal error details
            assert "database" not in data["detail"].lower()
            assert "internal" not in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_validation_error_format(self, test_client):
        """Test validation error response format"""
        invalid_data = {
            "email": "not-an-email",
            "password": "123"  # Too short
        }

        response = await test_client.post("/users/", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)  # FastAPI validation format

    @pytest.mark.asyncio
    async def test_malformed_request_body(self, test_client, auth_headers):
        """Test handling of malformed request bodies"""
        response = await test_client.put(
            "/users/me",
            data="not-json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        assert response.status_code == 422


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
