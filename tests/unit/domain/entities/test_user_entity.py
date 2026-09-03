"""
Unit Tests for User Domain Entity

Tests the User domain entity which encapsulates user-related business logic.
This is a pure unit test - no database or external dependencies.
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.domain.entities.user_entity import User, UserRole
from app.domain.exceptions import ValidationError
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password


class TestUserEntity:
    """Test User domain entity"""

    # ========================================================================
    # FACTORY METHOD TESTS
    # ========================================================================

    def test_create_user_with_required_fields(self):
        """Should create user with email and password"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        assert user.email == email
        assert user.password == password
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False
        assert user.role == UserRole.USER

    def test_create_user_with_full_name(self):
        """Should create user with full name"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, full_name="John Doe")

        assert user.full_name == "John Doe"

    def test_create_user_with_role(self):
        """Should create user with specific role"""
        email = Email(value="admin@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, role=UserRole.ADMIN)

        assert user.role == UserRole.ADMIN

    def test_create_user_auto_generates_id(self):
        """Should auto-generate UUID for new user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        assert isinstance(user.id, UUID)
        assert user.id.version == 4  # UUID v4

    def test_create_user_auto_generates_timestamps(self):
        """Should auto-generate creation and update timestamps"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.created_at <= user.updated_at

    def test_create_user_trims_full_name(self):
        """Should trim whitespace from full name"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, full_name="  John Doe  ")

        assert user.full_name == "John Doe"

    def test_create_user_rejects_short_full_name(self):
        """Should reject full name shorter than 2 characters"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        with pytest.raises(ValidationError, match="at least 2 characters"):
            User.create(email=email, password=password, full_name="J")

    def test_create_user_allows_none_full_name(self):
        """Should allow None for optional full name"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, full_name=None)

        assert user.full_name is None

    # ========================================================================
    # FROM_DB FACTORY TESTS
    # ========================================================================

    def test_from_db_reconstructs_user(self):
        """Should reconstruct user from database representation"""
        user_id = uuid4()
        password_hash = "$2b$12$exampleHash"

        user = User.from_db(
            id=user_id,
            email_str="user@example.com",
            password_hash=password_hash,
            full_name="John Doe",
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
            is_superuser=False,
        )

        assert user.id == user_id
        assert str(user.email) == "user@example.com"
        assert user.password.hash_value == password_hash
        assert user.full_name == "John Doe"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False

    def test_from_db_with_timestamps(self):
        """Should reconstruct user with timestamps"""
        user_id = uuid4()
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)

        user = User.from_db(
            id=user_id,
            email_str="user@example.com",
            password_hash="$2b$12$hash",
            created_at=created_at,
            updated_at=updated_at,
        )

        assert user.created_at == created_at
        assert user.updated_at == updated_at

    def test_from_db_defaults_timestamps(self):
        """Should default timestamps to now if not provided"""
        user_id = uuid4()

        user = User.from_db(
            id=user_id, email_str="user@example.com", password_hash="$2b$12$hash"
        )

        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_from_db_validates_email(self):
        """Should validate email when reconstructing from DB"""
        user_id = uuid4()

        with pytest.raises(ValidationError):
            User.from_db(
                id=user_id, email_str="invalid-email", password_hash="$2b$12$hash"
            )

    # ========================================================================
    # BUSINESS LOGIC TESTS
    # ========================================================================

    def test_verify_email(self):
        """Should mark email as verified"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")
        user = User.create(email=email, password=password)

        assert user.is_verified is False

        user.verify_email()

        assert user.is_verified is True

    def test_verify_email_updates_timestamp(self):
        """Should update timestamp when verifying email"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")
        user = User.create(email=email, password=password)
        original_updated_at = user.updated_at

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.01)

        user.verify_email()

        assert user.updated_at > original_updated_at

    def test_activate_user(self):
        """Should activate user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")
        user = User.create(email=email, password=password, is_active=False)

        user.activate()

        assert user.is_active is True

    def test_deactivate_user(self):
        """Should deactivate user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")
        user = User.create(email=email, password=password, is_active=True)

        user.deactivate()

        assert user.is_active is False

    def test_change_password(self):
        """Should change password"""
        email = Email(value="user@example.com")
        old_password = Password.create(plaintext="OldP@ss99!")
        new_password = Password.create(plaintext="NewP@ss99!")

        user = User.create(email=email, password=old_password)

        assert user.password.verify("OldP@ss99!") is True
        assert user.password.verify("NewP@ss99!") is False

        user.change_password(new_password)

        assert user.password.verify("OldP@ss99!") is False
        assert user.password.verify("NewP@ss99!") is True

    def test_change_password_updates_timestamp(self):
        """Should update timestamp when changing password"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")
        new_password = Password.create(plaintext="NewP@ss99!")

        user = User.create(email=email, password=password)
        original_updated_at = user.updated_at

        import time

        time.sleep(0.01)

        user.change_password(new_password)

        assert user.updated_at > original_updated_at

    def test_update_profile_full_name(self):
        """Should update full name"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, full_name="John Doe")

        user.update_profile(full_name="Jane Smith")

        assert user.full_name == "Jane Smith"

    def test_update_profile_trims_name(self):
        """Should trim whitespace when updating profile"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        user.update_profile(full_name="  Jane Smith  ")

        assert user.full_name == "Jane Smith"

    def test_update_profile_rejects_short_name(self):
        """Should reject full name shorter than 2 characters"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        with pytest.raises(ValidationError, match="at least 2 characters"):
            user.update_profile(full_name="J")

    def test_update_profile_no_change(self):
        """Should handle updating with None (no change)"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, full_name="John Doe")
        original_updated_at = user.updated_at

        import time

        time.sleep(0.01)

        user.update_profile(full_name=None)

        # Timestamp should still be updated
        assert user.updated_at > original_updated_at
        assert user.full_name == "John Doe"

    def test_promote_to_admin_as_superuser(self):
        """Should promote superuser to admin"""
        email = Email(value="admin@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, role=UserRole.USER, is_superuser=True
        )

        user.promote_to_admin()

        assert user.role == UserRole.ADMIN

    def test_promote_to_admin_as_regular_user_fails(self):
        """Should not allow regular user to promote to admin"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, role=UserRole.USER, is_superuser=False
        )

        with pytest.raises(ValidationError, match="Only superusers"):
            user.promote_to_admin()

    # ========================================================================
    # QUERY METHOD TESTS
    # ========================================================================

    def test_can_login_with_active_verified_user(self):
        """Should allow login for active and verified user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, is_active=True, is_verified=True
        )

        assert user.can_login() is True

    def test_cannot_login_with_inactive_user(self):
        """Should not allow login for inactive user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, is_active=False, is_verified=True
        )

        assert user.can_login() is False

    def test_cannot_login_with_unverified_user(self):
        """Should not allow login for unverified user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, is_active=True, is_verified=False
        )

        assert user.can_login() is False

    def test_cannot_login_with_inactive_and_unverified(self):
        """Should not allow login for inactive and unverified user"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, is_active=False, is_verified=False
        )

        assert user.can_login() is False

    def test_is_admin_with_admin_role(self):
        """Should identify admin users"""
        email = Email(value="admin@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, role=UserRole.ADMIN)

        assert user.is_admin() is True

    def test_is_admin_with_superuser(self):
        """Should identify superuser as admin"""
        email = Email(value="super@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, role=UserRole.USER, is_superuser=True
        )

        assert user.is_admin() is True

    def test_is_not_admin_regular_user(self):
        """Should not identify regular user as admin"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, role=UserRole.USER, is_superuser=False
        )

        assert user.is_admin() is False

    # ========================================================================
    # SERIALIZATION TESTS
    # ========================================================================

    def test_to_dict_excludes_password(self):
        """Should exclude password hash from dictionary"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        data = user.to_dict()

        assert "password" not in data
        assert "hash_value" not in data

    def test_to_dict_includes_all_fields(self):
        """Should include all non-sensitive fields"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(
            email=email, password=password, full_name="John Doe", role=UserRole.ADMIN
        )

        data = user.to_dict()

        assert data["id"] == str(user.id)
        assert data["email"] == "user@example.com"
        assert data["full_name"] == "John Doe"
        assert data["role"] == "ADMIN"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert data["is_superuser"] is False
        assert "created_at" in data
        assert "updated_at" in data

    def test_to_dict_serializes_dates(self):
        """Should serialize dates to ISO format"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        data = user.to_dict()

        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

        # Should be valid ISO format
        datetime.fromisoformat(data["created_at"])
        datetime.fromisoformat(data["updated_at"])

    # ========================================================================
    # STRING REPRESENTATION TESTS
    # ========================================================================

    def test_repr(self):
        """Should provide useful string representation"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password, role=UserRole.ADMIN)

        repr_str = repr(user)

        assert "User" in repr_str
        assert "user@example.com" in repr_str
        assert "ADMIN" in repr_str

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    def test_user_equality(self):
        """Should compare users by ID"""
        email1 = Email(value="user1@example.com")
        email2 = Email(value="user2@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user1 = User.create(email=email1, password=password)
        user2 = User.create(email=email2, password=password)

        # Different IDs, not equal
        assert user1 != user2

        # Same ID, equal (dataclass behavior)
        user3 = User(id=user1.id, email=email1, password=password)
        assert user1 == user3

    def test_multiple_users_same_email_different_ids(self):
        """Should allow multiple users with same email (different IDs)"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user1 = User.create(email=email, password=password)
        user2 = User.create(email=email, password=password)

        # Different IDs
        assert user1.id != user2.id

        # Same email value
        assert user1.email == user2.email

    def test_user_role_enum_values(self):
        """UserRole enum should have correct values"""
        assert UserRole.ADMIN.value == "ADMIN"
        assert UserRole.USER.value == "USER"
        assert UserRole.TEAM_LEAD.value == "TEAM_LEAD"

    # ========================================================================
    # TIMESTAMP UPDATE TESTS
    # ========================================================================

    def test_touch_updates_timestamp(self):
        """Touch method should update timestamp"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)
        original_updated_at = user.updated_at

        import time

        time.sleep(0.01)

        user._touch()

        assert user.updated_at > original_updated_at

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_password_never_exposed(self):
        """Should never expose plaintext password"""
        email = Email(value="user@example.com")
        password = Password.create(plaintext="SecureP@ss99!")

        user = User.create(email=email, password=password)

        # Check password is not stored in plaintext
        assert not hasattr(user, "plaintext_password")
        assert not hasattr(user.password, "plaintext")

        # Check to_dict doesn't expose it
        data = user.to_dict()
        assert "password" not in data
        assert "hash" not in data

        # Check repr doesn't expose it
        repr_str = repr(user)
        assert "SecureP@ss99!" not in repr_str
