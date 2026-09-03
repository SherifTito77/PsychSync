# tests/unit/domain/services/test_user_service_v2.py
"""
Unit Tests for UserService (Refactored with Repository Pattern)

These tests demonstrate the key benefit of the Repository Pattern:
we can test business logic WITHOUT a database using mocked repositories.

Run with:
    pytest tests/unit/domain/services/test_user_service_v2.py -v
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.domain.entities.user_entity import User, UserRole
from app.domain.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.domain.services.user_service_v2 import UserService
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password
from app.schemas.user import UserCreate, UserUpdate

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing"""
    repo = AsyncMock()
    repo.get = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.update_password = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    repo.activate = AsyncMock()
    repo.deactivate = AsyncMock()
    repo.verify_email = AsyncMock()
    return repo


@pytest.fixture
def sample_user():
    """Sample user domain entity"""
    return User.create(
        email=Email("test@example.com"),
        password=Password.create("SecurePassword123!"),
        full_name="Test User",
        role=UserRole.USER,
    )


@pytest.fixture
def sample_db_user(sample_user):
    """Sample database user model"""
    db_user = Mock()
    db_user.id = sample_user.id
    db_user.email = str(sample_user.email)
    db_user.password_hash = sample_user.password.hash_value
    db_user.full_name = sample_user.full_name
    db_user.role = sample_user.role.value
    db_user.is_active = sample_user.is_active
    db_user.is_verified = sample_user.is_verified
    db_user.is_superuser = sample_user.is_superuser
    db_user.created_at = sample_user.created_at
    db_user.updated_at = sample_user.updated_at
    return db_user


@pytest.fixture
def user_service(mock_user_repository):
    """UserService with mocked repository"""
    return UserService(mock_user_repository)


# ============================================================================
# USER CREATION TESTS
# ============================================================================


class TestUserCreation:
    """Test user creation business logic"""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should successfully create user with valid data"""
        # Arrange
        mock_user_repository.get_by_email.return_value = None  # Email doesn't exist
        mock_user_repository.create.return_value = sample_db_user

        user_data = UserCreate(
            email="test@example.com",
            password="SecurePassword123!",
            full_name="Test User",
        )

        # Act
        user = await user_service.create_user(user_data)

        # Assert
        assert user.email.normalized == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
        mock_user_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should raise error when email already exists"""
        # Arrange
        mock_user_repository.get_by_email.return_value = sample_db_user  # Email exists

        user_data = UserCreate(email="test@example.com", password="SecurePassword123!")

        # Act & Assert
        with pytest.raises(ValidationError, match="already exists"):
            await user_service.create_user(user_data)

        mock_user_repository.create.assert_not_called()  # Should not create

    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, user_service, mock_user_repository):
        """Should raise error for weak password"""
        # Arrange
        mock_user_repository.get_by_email.return_value = None

        user_data = UserCreate(email="test@example.com", password="weak")  # Too short

        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid password"):
            await user_service.create_user(user_data)

        mock_user_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_service, mock_user_repository):
        """Should raise error for invalid email format"""
        # Arrange
        mock_user_repository.get_by_email.return_value = None

        user_data = UserCreate(email="not-an-email", password="SecurePassword123!")

        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid email"):
            await user_service.create_user(user_data)


# ============================================================================
# USER RETRIEVAL TESTS
# ============================================================================


class TestUserRetrieval:
    """Test user retrieval business logic"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should retrieve user by ID"""
        # Arrange
        mock_user_repository.get.return_value = sample_db_user

        # Act
        user = await user_service.get_user_by_id(sample_db_user.id)

        # Assert
        assert user.id == sample_db_user.id
        assert user.email.normalized == "test@example.com"
        mock_user_repository.get.assert_called_once_with(sample_db_user.id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repository):
        """Should raise NotFoundError when user doesn't exist"""
        # Arrange
        mock_user_repository.get.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError, match="not found"):
            await user_service.get_user_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should retrieve user by email"""
        # Arrange
        mock_user_repository.get_by_email.return_value = sample_db_user

        # Act
        user = await user_service.get_user_by_email("test@example.com")

        # Assert
        assert user.email.normalized == "test@example.com"
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")


# ============================================================================
# USER UPDATE TESTS
# ============================================================================


class TestUserUpdates:
    """Test user update business logic"""

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should update user profile"""
        # Arrange - Set up chain of mock responses
        # First call: get_user_by_id needs the user
        user_service.get_user_by_id = AsyncMock(return_value=sample_db_user)
        # Second call: get_by_email for uniqueness check (if email changed)
        mock_user_repository.get_by_email.return_value = None  # Email not taken
        # Third call: update returns updated user
        updated_db_user = Mock(
            **{**sample_db_user.__dict__, "full_name": "Updated Name"}
        )
        mock_user_repository.update.return_value = updated_db_user

        update_data = UserUpdate(full_name="Updated Name")

        # Act
        updated_user = await user_service.update_user(sample_db_user.id, update_data)

        # Assert
        assert updated_user.full_name == "Updated Name"
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_short_name(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should reject too short name"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_db_user)

        update_data = UserUpdate(full_name="X")

        # Act & Assert
        with pytest.raises(ValidationError, match="at least 2 characters"):
            await user_service.update_user(sample_db_user.id, update_data)

        mock_user_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should reject email that already exists"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_db_user)

        other_user_id = uuid4()
        other_db_user = Mock(**{**sample_db_user.__dict__, "id": other_user_id})
        mock_user_repository.get_by_email.return_value = other_db_user  # Email taken

        update_data = UserUpdate(email="other@example.com")

        # Act & Assert
        with pytest.raises(ValidationError, match="already in use"):
            await user_service.update_user(sample_db_user.id, update_data)

        mock_user_repository.update.assert_not_called()


# ============================================================================
# USER DELETION TESTS
# ============================================================================


class TestUserDeletion:
    """Test user deletion business logic"""

    @pytest.mark.asyncio
    async def test_delete_user_self(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should allow user to delete themselves"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)
        mock_user_repository.delete.return_value = True

        # Act
        result = await user_service.delete_user(sample_user.id, sample_user)

        # Assert
        assert result is True
        mock_user_repository.delete.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_delete_user_by_admin(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should allow admin to delete any user"""
        # Arrange
        admin = User.create(
            email=Email("admin@example.com"),
            password=Password.create("AdminPass123!"),
            role=UserRole.ADMIN,
        )

        target_user = sample_user
        user_service.get_user_by_id = AsyncMock(return_value=target_user)
        mock_user_repository.delete.return_value = True

        # Act
        result = await user_service.delete_user(target_user.id, admin)

        # Assert
        assert result is True
        mock_user_repository.delete.assert_called_once_with(target_user.id)

    @pytest.mark.asyncio
    async def test_delete_user_unauthorized(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should prevent non-admin from deleting other users"""
        # Arrange
        other_user = User.create(
            email=Email("other@example.com"), password=Password.create("Pass123!")
        )

        user_service.get_user_by_id = AsyncMock(return_value=other_user)

        # Act & Assert
        with pytest.raises(AuthorizationError, match="can only delete yourself"):
            await user_service.delete_user(sample_user.id, other_user)

        mock_user_repository.delete.assert_not_called()


# ============================================================================
# PASSWORD MANAGEMENT TESTS
# ============================================================================


class TestPasswordManagement:
    """Test password change business logic"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should successfully change password"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)
        mock_user_repository.update_password.return_value = Mock()

        # Act
        await user_service.change_password(
            sample_user.id,
            "SecurePassword123!",  # Current password
            "NewPassword456!",  # New password
        )

        # Assert
        mock_user_repository.update_password.assert_called_once()
        call_args = mock_user_repository.update_password.call_args
        assert call_args[0][0] == sample_user.id  # user_id
        # Password should be hashed
        assert len(call_args[0][1]) > 50  # Hash is longer than plain password

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should reject incorrect current password"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)

        # Act & Assert
        with pytest.raises(ValidationError, match="Incorrect current password"):
            await user_service.change_password(
                sample_user.id,
                "WrongPassword123!",  # Wrong current password
                "NewPassword456!",
            )

        mock_user_repository.update_password.assert_not_called()

    @pytest.mark.asyncio
    async def test_change_password_weak_new(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should reject weak new password"""
        # Arrange
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)

        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid new password"):
            await user_service.change_password(
                sample_user.id,
                "SecurePassword123!",  # Correct current password
                "weak",  # Weak new password
            )

        mock_user_repository.update_password.assert_not_called()


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


class TestAuthentication:
    """Test authentication business logic"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should authenticate user with correct credentials"""
        # Arrange
        user_service.get_user_by_email = AsyncMock(return_value=sample_user)

        # Act
        authenticated_user = await user_service.authenticate_user(
            "test@example.com", "SecurePassword123!"
        )

        # Assert
        assert authenticated_user.id == sample_user.id

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should reject authentication with wrong password"""
        # Arrange
        user_service.get_user_by_email = AsyncMock(return_value=sample_user)

        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid credentials"):
            await user_service.authenticate_user(
                "test@example.com", "WrongPassword123!"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, user_service, mock_user_repository):
        """Should reject authentication for inactive user"""
        # Arrange - Create inactive user
        inactive_user = User.create(
            email=Email("inactive@example.com"),
            password=Password.create("SecurePassword123!"),
        )
        inactive_user.deactivate()

        user_service.get_user_by_email = AsyncMock(return_value=inactive_user)

        # Act & Assert
        with pytest.raises(ValidationError, match="Account is inactive"):
            await user_service.authenticate_user(
                "inactive@example.com", "SecurePassword123!"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_not_verified(
        self, user_service, mock_user_repository
    ):
        """Should reject authentication for unverified user"""
        # Arrange - Create unverified user (is_verified defaults to False)
        unverified_user = User.create(
            email=Email("unverified@example.com"),
            password=Password.create("SecurePassword123!"),
        )

        user_service.get_user_by_email = AsyncMock(return_value=unverified_user)

        # Act & Assert
        with pytest.raises(ValidationError, match="verify your email"):
            await user_service.authenticate_user(
                "unverified@example.com", "SecurePassword123!"
            )


# ============================================================================
# USER STATUS TESTS
# ============================================================================


class TestUserStatus:
    """Test user status management"""

    @pytest.mark.asyncio
    async def test_activate_user(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should activate user"""
        # Arrange
        user_service.get_user_by_id = AsyncMock()
        mock_user_repository.activate.return_value = sample_db_user

        # Act
        user = await user_service.activate_user(uuid4())

        # Assert
        assert user.is_active is True
        mock_user_repository.activate.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_user(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should deactivate user"""
        # Arrange
        user_service.get_user_by_id = AsyncMock()
        mock_user_repository.deactivate.return_value = sample_db_user

        # Act
        user = await user_service.deactivate_user(uuid4())

        # Assert
        assert user.is_active is False
        mock_user_repository.deactivate.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email(
        self, user_service, mock_user_repository, sample_db_user
    ):
        """Should verify user email"""
        # Arrange
        user_service.get_user_by_id = AsyncMock()
        mock_user_repository.verify_email.return_value = sample_db_user

        # Act
        user = await user_service.verify_user_email(uuid4())

        # Assert
        assert user.is_verified is True
        mock_user_repository.verify_email.assert_called_once()


# ============================================================================
# BUSINESS RULE TESTS
# ============================================================================


class TestBusinessRules:
    """Test business rule validation"""

    @pytest.mark.asyncio
    async def test_can_login_active_verified(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should allow active and verified user to login"""
        # Arrange
        sample_user.activate()
        sample_user.verify_email()
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)

        # Act
        can_login = await user_service.can_user_login(sample_user.id)

        # Assert
        assert can_login is True

    @pytest.mark.asyncio
    async def test_cannot_login_inactive(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should prevent inactive user from logging in"""
        # Arrange
        sample_user.deactivate()
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)

        # Act
        can_login = await user_service.can_user_login(sample_user.id)

        # Assert
        assert can_login is False

    @pytest.mark.asyncio
    async def test_cannot_login_unverified(
        self, user_service, mock_user_repository, sample_user
    ):
        """Should prevent unverified user from logging in"""
        # Arrange
        sample_user.activate()
        # Don't verify email - is_verified defaults to False
        user_service.get_user_by_id = AsyncMock(return_value=sample_user)

        # Act
        can_login = await user_service.can_user_login(sample_user.id)

        # Assert
        assert can_login is False
