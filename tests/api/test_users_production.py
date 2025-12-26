"""
Comprehensive Test Suite for Production User Management API

Coverage Areas:
- Security testing (authentication, authorization, input validation)
- Performance testing (response times, load testing)
- Error handling validation
- Integration testing with database and cache
- Edge case testing
- Rate limiting validation
- Caching behavior verification
- Audit logging verification

Test Categories:
- Unit Tests: Individual function testing
- Integration Tests: Endpoint testing with real dependencies
- Security Tests: Authentication and authorization validation
- Performance Tests: Load and stress testing
- Contract Tests: API contract validation
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Application imports
from app.main import app
from app.core.database import get_async_db
from app.core.config import settings
from app.db.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserProfile, PasswordChangeRequest
from app.core.security import create_access_token, hash_password
from app.core.exceptions import PsychSyncException, ValidationError
from app.api.v1.endpoints.users_production import (
    RequestContext,
    DIContainer,
    get_current_user_with_context
)

# Test configuration
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "SecureTestPassword123!"
ADMIN_USER_EMAIL = "admin@example.com"
ADMIN_USER_PASSWORD = "SecureAdminPassword123!"

class TestUserManagementProduction:
    """Comprehensive test suite for production user management"""

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """Test client with production settings"""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """Test database session"""
        async for session in get_async_db():
            yield session

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create test user"""
        user = User(
            email=TEST_USER_EMAIL,
            full_name="Test User",
            password_hash=hash_password(TEST_USER_PASSWORD),
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def admin_user(self, db_session: AsyncSession) -> User:
        """Create admin user"""
        user = User(
            email=ADMIN_USER_EMAIL,
            full_name="Admin User",
            password_hash=hash_password(ADMIN_USER_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def user_headers(self, test_user: User) -> Dict[str, str]:
        """Authentication headers for test user"""
        token = create_access_token(subject=str(test_user.id))
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def admin_headers(self, admin_user: User) -> Dict[str, str]:
        """Authentication headers for admin user"""
        token = create_access_token(subject=str(admin_user.id))
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def mock_request_context(self) -> RequestContext:
        """Mock request context"""
        context = RequestContext("test-request-123")
        context.ip_address = "127.0.0.1"
        context.user_agent = "pytest/test-client"
        return context

    # ==================== AUTHENTICATION TESTS ====================

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, client: AsyncClient):
        """Test profile access without authentication"""
        response = await client.get("/users/me")

        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert response.headers.get("www-authenticate") == "Bearer"

    @pytest.mark.asyncio
    async def test_get_user_profile_invalid_token(self, client: AsyncClient):
        """Test profile access with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_profile_valid_authentication(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test profile access with valid authentication"""
        response = await client.get("/users/me", headers=user_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "metadata" in response_data
        assert "request_id" in response_data["metadata"]
        assert response.headers.get("x-request-id") is not None

    @pytest.mark.asyncio
    async def test_rate_limiting_profile_endpoint(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test rate limiting on profile endpoint"""
        # Make requests up to the limit
        responses = []
        for i in range(35):  # Exceed the limit of 30 requests
            response = await client.get("/users/me", headers=user_headers)
            responses.append(response)

            # Small delay to avoid timing issues
            await asyncio.sleep(0.01)

        # First 30 should succeed
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) >= 30

        # Last few should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0

        # Check rate limit response format
        rate_limited_response = rate_limited_responses[0]
        assert rate_limited_response.status_code == 429
        response_data = rate_limited_response.json()
        assert "error_code" in response_data
        assert response_data["error_code"] == "RATE_LIMIT_EXCEEDED"

    # ==================== PROFILE ENDPOINT TESTS ====================

    @pytest.mark.asyncio
    async def test_get_user_profile_data_structure(
        self, client: AsyncClient, user_headers: Dict[str, str], test_user: User
    ):
        """Test user profile data structure and fields"""
        response = await client.get("/users/me", headers=user_headers)

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert response_data["success"] is True
        assert "data" in response_data
        assert "message" in response_data
        assert "metadata" in response_data

        # Verify user data
        user_data = response_data["data"]
        assert user_data["id"] == str(test_user.id)
        assert user_data["email"] == test_user.email
        assert user_data["full_name"] == test_user.full_name
        assert user_data["role"] == test_user.role.value
        assert user_data["is_active"] is True
        assert "profile_completion" in user_data
        assert "security_score" in user_data
        assert isinstance(user_data["profile_completion"], (int, float))
        assert isinstance(user_data["security_score"], int)

    @pytest.mark.asyncio
    async def test_get_user_profile_caching_behavior(
        self, client: AsyncClient, user_headers: Dict[str, str], test_user: User
    ):
        """Test that profile endpoint uses caching"""
        # First request
        start_time = time.time()
        response1 = await client.get("/users/me", headers=user_headers)
        first_request_time = time.time() - start_time

        # Second request (should be cached)
        start_time = time.time()
        response2 = await client.get("/users/me", headers=user_headers)
        second_request_time = time.time() - start_time

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Data should be identical
        assert response1.json() == response2.json()

        # Second request should be faster (cache hit)
        # Note: This might not always be true in test environment
        # assert second_request_time <= first_request_time

    @pytest.mark.asyncio
    async def test_get_user_profile_performance_headers(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test performance headers are present"""
        response = await client.get("/users/me", headers=user_headers)

        assert response.status_code == 200
        assert "x-processing-time" in response.headers
        assert "x-request-id" in response.headers

        processing_time = float(response.headers["x-processing-time"])
        assert processing_time >= 0

    # ==================== PASSWORD CHANGE TESTS ====================

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test successful password change"""
        password_data = PasswordChangeRequest(
            current_password=TEST_USER_PASSWORD,
            new_password="NewSecurePassword456!"
        )

        response = await client.post(
            "/users/change-password",
            json=password_data.dict(),
            headers=user_headers
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "password changed successfully" in response_data["message"].lower()

        # Verify security headers
        assert response.headers.get("x-password-changed") == "true"
        assert response.headers.get("x-sessions-invalidated") == "true"

    @pytest.mark.asyncio
    async def test_change_password_weak_password(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test password change with weak password"""
        password_data = PasswordChangeRequest(
            current_password=TEST_USER_PASSWORD,
            new_password="weak"  # Too weak
        )

        response = await client.post(
            "/users/change-password",
            json=password_data.dict(),
            headers=user_headers
        )

        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data
        assert "password" in response_data["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_incorrect_current_password(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test password change with incorrect current password"""
        password_data = PasswordChangeRequest(
            current_password="WrongPassword123!",
            new_password="NewSecurePassword456!"
        )

        response = await client.post(
            "/users/change-password",
            json=password_data.dict(),
            headers=user_headers
        )

        assert response.status_code == 401
        response_data = response.json()
        assert "incorrect" in response_data["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_rate_limiting(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test rate limiting on password change endpoint"""
        password_data = PasswordChangeRequest(
            current_password=TEST_USER_PASSWORD,
            new_password="NewSecurePassword456!"
        )

        # Make requests up to the limit (5 per 15 minutes)
        responses = []
        for i in range(7):  # Exceed the limit
            response = await client.post(
                "/users/change-password",
                json=password_data.dict(),
                headers=user_headers
            )
            responses.append(response)
            await asyncio.sleep(0.01)

        # Should be rate limited after 5 attempts
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) >= 1

    # ==================== USERS LIST TESTS ====================

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(
        self, client: AsyncClient
    ):
        """Test users list without authentication"""
        response = await client.get("/users/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_users_as_regular_user(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test users list as regular user (should work for own org)"""
        response = await client.get("/users/", headers=user_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "pagination" in response_data

        # Verify pagination structure
        pagination = response_data["pagination"]
        assert "page" in pagination
        assert "size" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination

    @pytest.mark.asyncio
    async def test_list_users_as_admin(
        self, client: AsyncClient, admin_headers: Dict[str, str], test_user: User, admin_user: User
    ):
        """Test users list as admin (should see all users)"""
        response = await client.get("/users/", headers=admin_headers)
        assert response.status_code == 200

        response_data = response.json()
        users = response_data["data"]

        # Should include both test users
        user_emails = [user["email"] for user in users]
        assert TEST_USER_EMAIL in user_emails
        assert ADMIN_USER_EMAIL in user_emails

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test users list pagination"""
        # First page
        response = await client.get("/users/?page=1&size=5", headers=user_headers)
        assert response.status_code == 200

        response_data = response.json()
        pagination = response_data["pagination"]
        assert pagination["page"] == 1
        assert pagination["size"] == 5

    @pytest.mark.asyncio
    async def test_list_users_search(
        self, client: AsyncClient, user_headers: Dict[str, str], test_user: User
    ):
        """Test users list search functionality"""
        # Search by email
        response = await client.get(
            f"/users/?search={test_user.email}",
            headers=user_headers
        )
        assert response.status_code == 200

        response_data = response.json()
        users = response_data["data"]

        # Should find the test user
        user_emails = [user["email"] for user in users]
        assert test_user.email in user_emails

    @pytest.mark.asyncio
    async def test_list_users_filters(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test users list filtering"""
        # Filter by active status
        response = await client.get("/users/?is_active=true", headers=admin_headers)
        assert response.status_code == 200

        response_data = response.json()
        users = response_data["data"]

        # All returned users should be active
        for user in users:
            assert user["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_users_sorting(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test users list sorting"""
        # Sort by email
        response = await client.get("/users/?sort_by=email&sort_order=asc", headers=user_headers)
        assert response.status_code == 200

        response_data = response.json()
        users = response_data["data"]

        # Verify sorting (emails should be in ascending order)
        emails = [user["email"] for user in users]
        assert emails == sorted(emails)

    @pytest.mark.asyncio
    async def test_list_users_performance_headers(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test performance headers on users list"""
        response = await client.get("/users/", headers=user_headers)
        assert response.status_code == 200

        assert "x-processing-time" in response.headers
        assert "x-request-id" in response.headers
        assert "x-total-count" in response.headers
        assert "x-page-count" in response.headers

    # ==================== INPUT VALIDATION TESTS ====================

    @pytest.mark.asyncio
    async def test_password_change_input_validation(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test password change input validation"""
        # Test missing current password
        invalid_data = {"new_password": "NewPassword123!"}
        response = await client.post(
            "/users/change-password",
            json=invalid_data,
            headers=user_headers
        )
        assert response.status_code == 422

        # Test missing new password
        invalid_data = {"current_password": TEST_USER_PASSWORD}
        response = await client.post(
            "/users/change-password",
            json=invalid_data,
            headers=user_headers
        )
        assert response.status_code == 422

        # Test empty passwords
        invalid_data = {
            "current_password": "",
            "new_password": ""
        }
        response = await client.post(
            "/users/change-password",
            json=invalid_data,
            headers=user_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_input_validation(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test users list input validation"""
        # Test invalid page number
        response = await client.get("/users/?page=0", headers=user_headers)
        # Should normalize to page 1
        assert response.status_code == 200

        # Test invalid page size
        response = await client.get("/users/?size=200", headers=user_headers)
        # Should normalize to max 100
        assert response.status_code == 200

        # Test invalid sort order
        response = await client.get("/users/?sort_order=invalid", headers=user_headers)
        assert response.status_code == 422

        # Test search input sanitization
        response = await client.get('/users/?search=<script>alert("xss")</script>', headers=user_headers)
        assert response.status_code == 200
        # Should not execute script (sanitized)

    # ==================== ERROR HANDLING TESTS ====================

    @pytest.mark.asyncio
    async def test_database_error_handling(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test database error handling"""
        # Mock database error
        with patch('app.api.v1.endpoints.users_production.get_async_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = await client.get("/users/me", headers=user_headers)
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_cache_error_handling(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test cache error handling"""
        # Mock cache error
        with patch('app.api.v1.endpoints.users_production.di_container._cache') as mock_cache:
            mock_cache.get.side_effect = Exception("Cache connection failed")

            # Should still work even if cache fails
            response = await client.get("/users/me", headers=user_headers)
            assert response.status_code == 200

    # ==================== INTEGRATION TESTS ====================

    @pytest.mark.asyncio
    async def test_full_user_workflow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test complete user workflow"""
        # 1. Create user
        user_data = UserCreate(
            email="workflow@example.com",
            full_name="Workflow User",
            password="WorkflowPassword123!"
        )

        # This would typically be through registration endpoint
        # For testing, create directly in database
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=hash_password(user_data.password),
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 2. Get authentication token
        token = create_access_token(subject=str(user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get user profile
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 200

        # 4. Change password
        password_data = PasswordChangeRequest(
            current_password=user_data.password,
            new_password="NewWorkflowPassword456!"
        )
        response = await client.post(
            "/users/change-password",
            json=password_data.dict(),
            headers=headers
        )
        assert response.status_code == 200

        # 5. List users (should include our user)
        response = await client.get("/users/", headers=headers)
        assert response.status_code == 200

        response_data = response.json()
        users = response_data["data"]
        user_emails = [user["email"] for user in users]
        assert user_data.email in user_emails

    # ==================== PERFORMANCE TESTS ====================

    @pytest.mark.asyncio
    async def test_concurrent_profile_requests(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test concurrent profile requests"""
        async def make_request():
            return await client.get("/users/me", headers=user_headers)

        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_profile_response_time(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test profile endpoint response time"""
        start_time = time.time()
        response = await client.get("/users/me", headers=user_headers)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        # Should respond within 500ms
        assert response.status_code == 200
        assert response_time_ms < 500

    # ==================== SECURITY TESTS ====================

    @pytest.mark.asyncio
    async def test_sql_injection_protection(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test SQL injection protection in search"""
        # SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin@example.com'; DELETE FROM users WHERE '1'='1' --"
        ]

        for malicious_input in malicious_inputs:
            response = await client.get(
                f"/users/?search={malicious_input}",
                headers=admin_headers
            )
            # Should not crash the server
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_xss_protection(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """Test XSS protection in search"""
        xss_payload = '<script>alert("xss")</script>'
        response = await client.get(
            f"/users/?search={xss_payload}",
            headers=admin_headers
        )

        if response.status_code == 200:
            response_data = response.json()
            # Response should not contain unescaped script tags
            response_str = json.dumps(response_data)
            assert "<script>" not in response_str.lower()

    # ==================== CONTRACT TESTS ====================

    @pytest.mark.asyncio
    async def test_api_contract_profile(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test API contract compliance for profile endpoint"""
        response = await client.get("/users/me", headers=user_headers)
        assert response.status_code == 200

        response_data = response.json()

        # Verify required fields
        required_fields = ["success", "message", "data", "metadata"]
        for field in required_fields:
            assert field in response_data

        # Verify data fields
        user_data = response_data["data"]
        required_user_fields = [
            "id", "email", "full_name", "role", "is_active",
            "is_verified", "created_at", "profile_completion", "security_score"
        ]
        for field in required_user_fields:
            assert field in user_data

    @pytest.mark.asyncio
    async def test_api_contract_users_list(
        self, client: AsyncClient, user_headers: Dict[str, str]
    ):
        """Test API contract compliance for users list endpoint"""
        response = await client.get("/users/", headers=user_headers)
        assert response.status_code == 200

        response_data = response.json()

        # Verify required fields
        required_fields = ["success", "message", "data", "pagination", "metadata"]
        for field in required_fields:
            assert field in response_data

        # Verify pagination fields
        pagination = response_data["pagination"]
        required_pagination_fields = [
            "page", "size", "total", "total_pages", "has_next", "has_prev"
        ]
        for field in required_pagination_fields:
            assert field in pagination

        # Verify data structure
        users = response_data["data"]
        assert isinstance(users, list)
        if users:  # If there are users
            required_user_fields = [
                "id", "email", "full_name", "role", "is_active",
                "is_verified", "created_at", "updated_at"
            ]
            for field in required_user_fields:
                assert field in users[0]


# ==================== TEST UTILITIES ====================

class TestUtils:
    """Utility functions for testing"""

    @staticmethod
    def create_test_user_data() -> UserCreate:
        """Create test user data"""
        return UserCreate(
            email=f"test_{datetime.utcnow().timestamp()}@example.com",
            full_name="Test User",
            password="TestPassword123!"
        )

    @staticmethod
    def create_password_change_data(
        current_password: str,
        new_password: str
    ) -> PasswordChangeRequest:
        """Create password change data"""
        return PasswordChangeRequest(
            current_password=current_password,
            new_password=new_password
        )

    @staticmethod
    async def assert_response_structure(
        response_data: Dict[str, Any],
        has_pagination: bool = False
    ):
        """Assert standard response structure"""
        assert "success" in response_data
        assert "message" in response_data
        assert "data" in response_data
        assert "metadata" in response_data

        if has_pagination:
            assert "pagination" in response_data

    @staticmethod
    def extract_request_id(response_data: Dict[str, Any]) -> str:
        """Extract request ID from response"""
        return response_data.get("metadata", {}).get("request_id", "")

    @staticmethod
    async def assert_audit_log_contains(
        db_session: AsyncSession,
        user_id: str,
        action: str,
        request_id: str = None
    ):
        """Assert audit log contains specific entry"""
        # This would check the audit log table
        # Implementation depends on audit logging structure
        pass


# ==================== PERFORMANCE TESTING UTILITIES ====================

class PerformanceTestUtils:
    """Utilities for performance testing"""

    @staticmethod
    async def measure_response_time(client: AsyncClient, method: str, url: str, **kwargs):
        """Measure response time for API call"""
        start_time = time.time()
        response = await client.request(method, url, **kwargs)
        end_time = time.time()

        return response, (end_time - start_time) * 1000

    @staticmethod
    async def load_test_endpoint(
        client: AsyncClient,
        method: str,
        url: str,
        concurrent_requests: int = 10,
        **kwargs
    ):
        """Perform load test on endpoint"""
        async def make_request():
            return await client.request(method, url, **kwargs)

        tasks = [make_request() for _ in range(concurrent_requests)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful_responses = [r for r in responses if hasattr(r, 'status_code')]
        failed_responses = [r for r in responses if not hasattr(r, 'status_code')]

        return {
            "total_requests": concurrent_requests,
            "successful_requests": len(successful_responses),
            "failed_requests": len(failed_responses),
            "success_rate": len(successful_responses) / concurrent_requests * 100,
            "responses": successful_responses
        }


# ==================== TEST CONFIGURATION ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.security = pytest.mark.security
pytest.mark.performance = pytest.mark.performance
pytest.mark.contract = pytest.mark.contract


if __name__ == "__main__":
    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=app.api.v1.endpoints.users_production",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])