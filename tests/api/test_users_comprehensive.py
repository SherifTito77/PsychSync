# tests/api/test_users_comprehensive.py
"""
Comprehensive test suite for user endpoints with standardized response testing
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import PasswordChange
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
import json


class TestUserEndpoints:
    """Comprehensive test suite for user endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return AsyncClient(app=app, base_url="http://test")

    @pytest.fixture
    def valid_user_data(self):
        """Valid user creation data"""
        return {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }

    @pytest.fixture
    def user_update_data(self):
        """Valid user update data"""
        return {
            "full_name": "Updated Name",
            "timezone": "America/New_York",
            "locale": "en-US"
        }

    @pytest.fixture
    def password_change_data(self):
        """Valid password change data"""
        return {
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }

    # =============================================================================
    # USER REGISTRATION TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_register_user_success(self, client, valid_user_data):
        """Test successful user registration returns standardized response"""
        with patch('app.services.async_user_service.get_user_by_email_async', return_value=None), \
             patch('app.services.async_user_service.create_user_async') as mock_create:

            # Mock the created user
            mock_user = {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": valid_user_data["email"],
                "full_name": valid_user_data["full_name"],
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-01T00:00:00Z"
            }
            mock_create.return_value = mock_user

            response = await client.post("/users/register", json=valid_user_data)

            assert response.status_code == 201
            data = response.json()

            # Test standardized response format
            assert data["success"] is True
            assert data["message"] == "User created successfully"
            assert data["data"]["email"] == valid_user_data["email"]
            assert "timestamp" in data
            assert data["error_code"] is None

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client, valid_user_data):
        """Test registration with duplicate email returns proper error response"""
        with patch('app.services.async_user_service.get_user_by_email_async') as mock_get:
            mock_get.return_value = {"email": valid_user_data["email"]}

            response = await client.post("/users/register", json=valid_user_data)

            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_user_invalid_data(self, client):
        """Test registration with invalid data returns validation error"""
        invalid_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "full_name": ""  # Empty name
        }

        response = await client.post("/users/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "errors" in data["data"]
        assert len(data["data"]["errors"]) > 0

    # =============================================================================
    # GET USER PROFILE TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, client):
        """Test successful user profile retrieval"""
        mock_user = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True
        }

        with patch('app.api.deps.get_current_active_user', return_value=mock_user):
            response = await client.get("/users/me")

            assert response.status_code == 200
            data = response.json()

            # Test standardized response format
            assert data["success"] is True
            assert data["message"] == "User profile retrieved successfully"
            assert data["data"]["email"] == "test@example.com"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, client):
        """Test getting profile without authentication"""
        with patch('app.api.deps.get_current_active_user', side_effect=Exception("Unauthorized")):
            response = await client.get("/users/me")
            # Should return 500 due to unhandled exception, which our global handler will catch
            assert response.status_code == 500

    # =============================================================================
    # LIST USERS TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_list_users_success(self, client):
        """Test successful user listing with pagination"""
        mock_users = [
            {"id": "1", "email": "user1@example.com", "full_name": "User 1"},
            {"id": "2", "email": "user2@example.com", "full_name": "User 2"},
        ]

        with patch('app.api.deps.get_current_active_user', return_value={"id": "admin"}), \
             patch('app.services.async_user_service.get_all_users_async', return_value=mock_users):

            response = await client.get("/users/?skip=0&limit=100")

            assert response.status_code == 200
            data = response.json()

            # Test paginated response format
            assert data["success"] is True
            assert data["message"] == "Users retrieved successfully"
            assert data["data"] == mock_users
            assert data["total"] == 2
            assert data["page"] == 1
            assert data["size"] == 100
            assert data["pages"] == 1
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_list_users_pagination(self, client):
        """Test user listing pagination parameters"""
        mock_users = [{"id": str(i), "email": f"user{i}@example.com"} for i in range(5)]

        with patch('app.api.deps.get_current_active_user', return_value={"id": "admin"}), \
             patch('app.services.async_user_service.get_all_users_async', return_value=mock_users):

            response = await client.get("/users/?skip=2&limit=2")

            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2  # (2 // 2) + 1
            assert data["size"] == 2

    # =============================================================================
    # GET USER BY ID TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, client):
        """Test successful user retrieval by ID"""
        mock_user = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "full_name": "Test User"
        }

        with patch('app.api.deps.get_current_active_user', return_value={"id": "admin"}), \
             patch('app.services.async_user_service.get_user_by_id_async', return_value=mock_user):

            response = await client.get("/users/550e8400-e29b-41d4-a716-446655440000")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "User retrieved successfully"
            assert data["data"]["id"] == "550e8400-e29b-41d4-a716-446655440000"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, client):
        """Test retrieving non-existent user returns 404"""
        with patch('app.api.deps.get_current_active_user', return_value={"id": "admin"}), \
             patch('app.services.async_user_service.get_user_by_id_async', return_value=None):

            response = await client.get("/users/550e8400-e29b-41d4-a716-446655440000")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "User not found"

    # =============================================================================
    # UPDATE USER PROFILE TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, client, user_update_data):
        """Test successful user profile update"""
        mock_updated_user = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "full_name": "Updated Name",
            "timezone": "America/New_York"
        }

        with patch('app.api.deps.get_current_active_user', return_value={"id": "550e8400-e29b-41d4-a716-446655440000"}), \
             patch('app.services.async_user_service.update_user_async', return_value=mock_updated_user):

            response = await client.put("/users/me", json=user_update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "User profile updated successfully"
            assert data["data"]["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, client, user_update_data):
        """Test updating user that doesn't exist"""
        with patch('app.api.deps.get_current_active_user', return_value={"id": "550e8400-e29b-41d4-a716-446655440000"}), \
             patch('app.services.async_user_service.update_user_async', return_value=None):

            response = await client.put("/users/me", json=user_update_data)

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "User not found"

    # =============================================================================
    # CHANGE PASSWORD TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_change_password_success(self, client, password_change_data):
        """Test successful password change"""
        mock_user = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "password_hash": "$2b$12$hashedpassword"
        }

        with patch('app.api.deps.get_current_active_user', return_value=mock_user), \
             patch('app.core.security.verify_password', return_value=True), \
             patch('app.services.async_user_service.update_user_async', return_value=mock_user):

            response = await client.post("/users/me/change-password", json=password_change_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Password updated successfully"
            assert data["data"] is None

    @pytest.mark.asyncio
    async def test_change_password_incorrect_current(self, client, password_change_data):
        """Test password change with incorrect current password"""
        mock_user = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "password_hash": "$2b$12$hashedpassword"
        }

        with patch('app.api.deps.get_current_active_user', return_value=mock_user), \
             patch('app.core.security.verify_password', return_value=False):

            response = await client.post("/users/me/change-password", json=password_change_data)

            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Incorrect current password"

    @pytest.mark.asyncio
    async def test_change_password_invalid_data(self, client):
        """Test password change with invalid data"""
        invalid_data = {
            "current_password": "short",
            "new_password": "123"  # Too short
        }

        with patch('app.api.deps.get_current_active_user', return_value={"id": "user"}):
            response = await client.post("/users/me/change-password", json=invalid_data)

            assert response.status_code == 422
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "VALIDATION_ERROR"

    # =============================================================================
    # ERROR HANDLING TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_database_error_handling(self, client, valid_user_data):
        """Test that database errors are properly handled"""
        with patch('app.services.async_user_service.get_user_by_email_async', return_value=None), \
             patch('app.services.async_user_service.create_user_async', side_effect=Exception("Database connection failed")):

            response = await client.post("/users/register", json=valid_user_data)

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "INTERNAL_ERROR"
            assert "unexpected error occurred" in data["message"]

    @pytest.mark.asyncio
    async def test_custom_service_exception_handling(self, client, valid_user_data):
        """Test that custom service exceptions are properly handled"""
        with patch('app.services.async_user_service.get_user_by_email_async', return_value=None), \
             patch('app.services.async_user_service.create_user_async', side_effect=UserAlreadyExistsError("email", "test@example.com")):

            response = await client.post("/users/register", json=valid_user_data)

            assert response.status_code == 400
            data = response.json()
            assert "already exists" in data["detail"]


# =============================================================================
    # INTEGRATION TESTS
# =============================================================================

    @pytest.mark.asyncio
    async def test_user_registration_and_profile_flow(self, client, valid_user_data):
        """Test complete user registration and profile retrieval flow"""
        mock_user = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": valid_user_data["email"],
            "full_name": valid_user_data["full_name"],
            "is_active": True,
            "is_verified": False
        }

        # Step 1: Register user
        with patch('app.services.async_user_service.get_user_by_email_async', return_value=None), \
             patch('app.services.async_user_service.create_user_async', return_value=mock_user):

            register_response = await client.post("/users/register", json=valid_user_data)
            assert register_response.status_code == 201

        # Step 2: Get user profile
        with patch('app.api.deps.get_current_active_user', return_value=mock_user):
            profile_response = await client.get("/users/me")
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            assert profile_data["data"]["email"] == valid_user_data["email"]

        # Step 3: Update profile
        update_data = {"full_name": "Updated Name"}
        mock_updated_user = {**mock_user, "full_name": "Updated Name"}

        with patch('app.api.deps.get_current_active_user', return_value=mock_user), \
             patch('app.services.async_user_service.update_user_async', return_value=mock_updated_user):

            update_response = await client.put("/users/me", json=update_data)
            assert update_response.status_code == 200
            update_data_response = update_response.json()
            assert update_data_response["data"]["full_name"] == "Updated Name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])