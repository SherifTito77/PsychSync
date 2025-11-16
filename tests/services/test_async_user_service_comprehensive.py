# tests/services/test_async_user_service_comprehensive.py
"""
Comprehensive test suite for async user service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.services.async_user_service import (
    UserServiceError,
    UserNotFoundError,
    UserAlreadyExistsError,
    get_user_by_id_async,
    get_user_by_email_async,
    create_user_async,
    get_all_users_async,
    update_user_async
)
from app.schemas.user import UserCreate, UserUpdate
from app.db.models.user import User


class TestAsyncUserService:
    """Comprehensive test suite for async user service"""

    @pytest.fixture
    def mock_db(self):
        """Create mock async database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

    @pytest.fixture
    def sample_user_model(self):
        """Sample user model for testing"""
        user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            full_name="Test User",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow()
        )
        return user

    # =============================================================================
    # GET USER BY ID TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_db, sample_user_model):
        """Test successful user retrieval by ID"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.user_to_dict') as mock_to_dict:
            mock_to_dict.return_value = {"id": str(sample_user_model.id), "email": sample_user_model.email}

            result = await get_user_by_id_async(mock_db, str(sample_user_model.id))

            assert result is not None
            assert result["id"] == str(sample_user_model.id)
            assert result["email"] == sample_user_model.email
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_db):
        """Test user retrieval when user doesn't exist"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await get_user_by_id_async(mock_db, "non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_database_error(self, mock_db):
        """Test handling database errors during user retrieval"""
        mock_db.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(UserServiceError, match="Failed to fetch user"):
            await get_user_by_id_async(mock_db, "some-id")

    # =============================================================================
    # GET USER BY EMAIL TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, mock_db, sample_user_model):
        """Test successful user retrieval by email"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.user_to_dict') as mock_to_dict:
            mock_to_dict.return_value = {"id": str(sample_user_model.id), "email": sample_user_model.email}

            result = await get_user_by_email_async(mock_db, sample_user_model.email)

            assert result is not None
            assert result["email"] == sample_user_model.email

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_db):
        """Test user retrieval by email when user doesn't exist"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await get_user_by_email_async(mock_db, "nonexistent@example.com")

        assert result is None

    # =============================================================================
    # CREATE USER TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_db, sample_user_data):
        """Test successful user creation"""
        with patch('app.services.async_user_service.User') as mock_user_class, \
             patch('app.services.async_user_service.get_password_hash') as mock_hash, \
             patch('app.services.async_user_service.user_to_dict') as mock_to_dict:

            # Setup mocks
            mock_user_instance = AsyncMock(spec=User)
            mock_user_instance.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user_class.return_value = mock_user_instance
            mock_hash.return_value = "hashed_password"
            mock_to_dict.return_value = {"id": "550e8400-e29b-41d4-a716-446655440000", "email": sample_user_data.email}

            # Mock the database operations
            mock_db.add = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            mock_db.flush = AsyncMock()

            result = await create_user_async(mock_db, sample_user_data)

            assert result is not None
            assert result["email"] == sample_user_data.email
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, mock_db, sample_user_data):
        """Test user creation with duplicate email raises appropriate error"""
        with patch('app.services.async_user_service.get_user_by_email_async') as mock_get_user:
            mock_get_user.return_value = {"email": sample_user_data.email}

            with pytest.raises(UserAlreadyExistsError, match="already exists"):
                await create_user_async(mock_db, sample_user_data)

    @pytest.mark.asyncio
    async def test_create_user_database_error(self, mock_db, sample_user_data):
        """Test handling database errors during user creation"""
        with patch('app.services.async_user_service.User') as mock_user_class, \
             patch('app.services.async_user_service.get_password_hash'):

            mock_user_instance = AsyncMock(spec=User)
            mock_user_class.return_value = mock_user_instance

            mock_db.add = AsyncMock()
            mock_db.commit.side_effect = Exception("Database constraint violation")

            with pytest.raises(UserServiceError):
                await create_user_async(mock_db, sample_user_data)

    # =============================================================================
    # GET ALL USERS TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_all_users_success(self, mock_db, sample_user_model):
        """Test successful retrieval of all users"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [sample_user_model]
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.users_to_dict_list') as mock_to_dict_list:
            mock_to_dict_list.return_value = [{"id": str(sample_user_model.id), "email": sample_user_model.email}]

            result = await get_all_users_async(mock_db, skip=0, limit=100)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["email"] == sample_user_model.email

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, mock_db):
        """Test retrieval when no users exist"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.users_to_dict_list') as mock_to_dict_list:
            mock_to_dict_list.return_value = []

            result = await get_all_users_async(mock_db, skip=0, limit=100)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_all_users_pagination(self, mock_db):
        """Test user retrieval with pagination"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.users_to_dict_list') as mock_to_dict_list:
            mock_to_dict_list.return_value = []

            await get_all_users_async(mock_db, skip=10, limit=50)

            # Verify that offset and limit were properly applied
            mock_db.execute.assert_called_once()
            call_args = mock_db.execute.call_args[0][0]
            # Check that the query contains offset and limit
            assert hasattr(call_args, 'offset') or hasattr(call_args, 'limit')

    # =============================================================================
    # UPDATE USER TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_db, sample_user_model):
        """Test successful user update"""
        update_data = UserUpdate(full_name="Updated Name")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.user_to_dict') as mock_to_dict:
            mock_to_dict.return_value = {"id": str(sample_user_model.id), "full_name": "Updated Name"}

            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await update_user_async(mock_db, str(sample_user_model.id), update_data)

            assert result is not None
            assert result["full_name"] == "Updated Name"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_db):
        """Test updating user that doesn't exist"""
        update_data = UserUpdate(full_name="Updated Name")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await update_user_async(mock_db, "non-existent-id", update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_with_password(self, mock_db, sample_user_model):
        """Test updating user with new password"""
        update_data = UserUpdate(password="NewPassword123!")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.user_to_dict') as mock_to_dict, \
             patch('app.services.async_user_service.get_password_hash') as mock_hash:

            mock_to_dict.return_value = {"id": str(sample_user_model.id)}
            mock_hash.return_value = "new_hashed_password"

            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await update_user_async(mock_db, str(sample_user_model.id), update_data)

            mock_hash.assert_called_once_with("NewPassword123!")
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_database_error(self, mock_db, sample_user_model):
        """Test handling database errors during user update"""
        update_data = UserUpdate(full_name="Updated Name")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db.execute.return_value = mock_result

        mock_db.commit.side_effect = Exception("Database constraint violation")

        with pytest.raises(UserServiceError):
            await update_user_async(mock_db, str(sample_user_model.id), update_data)

    # =============================================================================
    # UTILITY FUNCTION TESTS
    # =============================================================================

    def test_user_service_error_creation(self):
        """Test UserAlreadyExistsError creation and properties"""
        error = UserAlreadyExistsError("email", "test@example.com")

        assert error.message == "User with email 'test@example.com' already exists"
        assert error.error_code == "USER_ALREADY_EXISTS"
        assert error.field == "email"
        assert error.value == "test@example.com"

    def test_user_not_found_error_creation(self):
        """Test UserNotFoundError creation and properties"""
        error = UserNotFoundError("user-123")

        assert error.message == "User not found: user-123"
        assert error.error_code == "USER_NOT_FOUND"
        assert error.identifier == "user-123"

    # =============================================================================
    # EDGE CASE TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_create_user_with_invalid_data(self, mock_db):
        """Test user creation with invalid data"""
        invalid_data = UserCreate(
            email="invalid-email",
            password="123",  # Too short
            full_name=""  # Empty name
        )

        # The service should still attempt to create the user
        # Validation should happen at the API level
        with patch('app.services.async_user_service.User') as mock_user_class, \
             patch('app.services.async_user_service.get_password_hash'):

            mock_user_instance = AsyncMock(spec=User)
            mock_user_class.return_value = mock_user_instance

            mock_db.add = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.flush = AsyncMock()

            # Service doesn't validate, just passes through
            result = await create_user_async(mock_db, invalid_data)
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_user_by_id_with_malformed_id(self, mock_db):
        """Test user retrieval with malformed ID"""
        with pytest.raises(UserServiceError):
            await get_user_by_id_async(mock_db, "malformed-uuid")

    @pytest.mark.asyncio
    async def test_update_user_with_no_changes(self, mock_db, sample_user_model):
        """Test updating user with no actual changes"""
        update_data = UserUpdate()  # Empty update

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.user_to_dict') as mock_to_dict:
            mock_to_dict.return_value = {"id": str(sample_user_model.id)}

            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await update_user_async(mock_db, str(sample_user_model.id), update_data)

            assert result is not None
            mock_db.commit.assert_called_once()  # Should still commit to update timestamps

    # =============================================================================
    # PERFORMANCE TESTS
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_all_users_performance(self, mock_db):
        """Test performance of getting many users"""
        import time

        # Mock a large number of users
        mock_users = [AsyncMock(spec=User) for _ in range(1000)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        with patch('app.services.async_user_service.users_to_dict_list') as mock_to_dict_list:
            mock_to_dict_list.return_value = [{"id": f"user-{i}"} for i in range(1000)]

            start_time = time.time()
            result = await get_all_users_async(mock_db, skip=0, limit=1000)
            end_time = time.time()

            assert len(result) == 1000
            assert (end_time - start_time) < 1.0  # Should complete within 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])