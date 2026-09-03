# tests/unit/domain/services/test_user_service.py
"""
Unit Tests for UserService

Demonstrates testing domain services with mocked repositories.
No database required - pure business logic testing.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.entities.user_entity import User
from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.services.user_service import UserService
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password

# ============================================================================
# USER CREATION TESTS
# ============================================================================


class TestUserCreation:
    """Test user creation business logic"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_user_repository):
        """Should successfully create user with valid data"""
        # Arrange
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
            full_name="Test User",
            created_at=datetime.utcnow(),
        )

        service = UserService(mock_user_repository)

        # Act
        user = await service.create_user(
            {
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "full_name": "Test User",
            }
        )

        # Assert
        assert user.email.normalized == "test@example.com"
        assert user.full_name == "Test User"
        mock_user_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, mock_user_repository):
        """Should raise error when email already exists"""
        # Arrange
        existing_user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
        )
        mock_user_repository.get_by_email.return_value = existing_user

        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="already exists"):
            await service.create_user(
                {"email": "test@example.com", "password": "SecurePassword123!"}
            )

    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, mock_user_repository):
        """Should raise error for weak password"""
        # Arrange
        mock_user_repository.get_by_email.return_value = None
        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError):
            await service.create_user(
                {
                    "email": "test@example.com",
                    "password": "weak",  # Too short, no special chars
                }
            )


# ============================================================================
# USER RETRIEVAL TESTS
# ============================================================================


class TestUserRetrieval:
    """Test user retrieval business logic"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_user_repository):
        """Should retrieve user by ID"""
        # Arrange
        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
        )
        mock_user_repository.get.return_value = test_user

        service = UserService(mock_user_repository)

        # Act
        user = await service.get_user_by_id(user_id)

        # Assert
        assert user.id == user_id
        mock_user_repository.get.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_user_repository):
        """Should raise NotFoundError when user doesn't exist"""
        # Arrange
        mock_user_repository.get.return_value = None
        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.get_user_by_id(uuid4())


# ============================================================================
# USER UPDATE TESTS
# ============================================================================


class TestUserUpdates:
    """Test user update business logic"""

    @pytest.mark.asyncio
    async def test_update_user_profile(self, mock_user_repository):
        """Should update user profile"""
        # Arrange
        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
            full_name="Old Name",
        )
        mock_user_repository.get.return_value = test_user
        mock_user_repository.update.return_value = test_user

        service = UserService(mock_user_repository)

        # Act
        updated_user = await service.update_user(user_id, {"full_name": "New Name"})

        # Assert
        assert updated_user.full_name == "New Name"
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_email_too_short(self, mock_user_repository):
        """Should reject too short name"""
        # Arrange
        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
        )
        mock_user_repository.get.return_value = test_user

        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="at least 2 characters"):
            await service.update_user(user_id, {"full_name": "X"})


# ============================================================================
# PASSWORD CHANGE TESTS
# ============================================================================


class TestPasswordChanges:
    """Test password change business logic"""

    @pytest.mark.asyncio
    async def test_change_password_success(self, mock_user_repository):
        """Should successfully change password"""
        # Arrange
        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=Email("test@example.com"),
            password=Password.create("OldPassword123!"),
        )
        mock_user_repository.get.return_value = test_user
        mock_user_repository.update.return_value = test_user

        service = UserService(mock_user_repository)

        # Act
        await service.change_password(user_id, "OldPassword123!", "NewPassword456!")

        # Assert
        assert test_user.password.verify("NewPassword456!")
        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, mock_user_repository):
        """Should reject wrong current password"""
        # Arrange
        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=Email("test@example.com"),
            password=Password.create("CorrectPassword123!"),
        )
        mock_user_repository.get.return_value = test_user

        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="Incorrect password"):
            await service.change_password(
                user_id,
                "WrongPassword123!",  # Wrong current password
                "NewPassword456!",
            )


# ============================================================================
# USER DELETION TESTS
# ============================================================================


class TestUserDeletion:
    """Test user deletion business logic"""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_user_repository):
        """Should successfully delete user"""
        # Arrange
        user_id = uuid4()
        mock_user_repository.exists.return_value = True
        mock_user_repository.delete.return_value = True

        service = UserService(mock_user_repository)

        # Act
        result = await service.delete_user(user_id)

        # Assert
        assert result is True
        mock_user_repository.delete.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, mock_user_repository):
        """Should raise NotFoundError when user doesn't exist"""
        # Arrange
        mock_user_repository.exists.return_value = False
        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.delete_user(uuid4())


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


class TestAuthentication:
    """Test authentication business logic"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_user_repository):
        """Should authenticate user with correct credentials"""
        # Arrange
        password = Password.create("SecurePassword123!")
        test_user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=password,
            is_active=True,
            is_verified=True,
        )
        mock_user_repository.get_by_email.return_value = test_user

        service = UserService(mock_user_repository)

        # Act
        authenticated_user = await service.authenticate_user(
            "test@example.com", "SecurePassword123!"
        )

        # Assert
        assert authenticated_user.id == test_user.id

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_user_repository):
        """Should reject authentication with wrong password"""
        # Arrange
        password = Password.create("CorrectPassword123!")
        test_user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=password,
        )
        mock_user_repository.get_by_email.return_value = test_user

        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid credentials"):
            await service.authenticate_user("test@example.com", "WrongPassword123!")

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, mock_user_repository):
        """Should reject authentication for inactive user"""
        # Arrange
        test_user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
            is_active=False,  # Inactive user
        )
        mock_user_repository.get_by_email.return_value = test_user

        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="Account is inactive"):
            await service.authenticate_user("test@example.com", "SecurePassword123!")


# ============================================================================
# BUSINESS RULE TESTS
# ============================================================================


class TestBusinessRules:
    """Test business rules and validations"""

    @pytest.mark.asyncio
    async def test_user_can_login(self, mock_user_repository):
        """Should check if user can login"""
        # Arrange
        test_user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
            is_active=True,
            is_verified=True,
        )
        mock_user_repository.get.return_value = test_user

        service = UserService(mock_user_repository)

        # Act
        can_login = await service.can_user_login(test_user.id)

        # Assert
        assert can_login is True

    @pytest.mark.asyncio
    async def test_inactive_user_cannot_login(self, mock_user_repository):
        """Should prevent inactive user from logging in"""
        # Arrange
        test_user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=Password.create("SecurePassword123!"),
            is_active=False,  # Inactive
            is_verified=True,
        )
        mock_user_repository.get.return_value = test_user

        service = UserService(mock_user_repository)

        # Act
        can_login = await service.can_user_login(test_user.id)

        # Assert
        assert can_login is False
