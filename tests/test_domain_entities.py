# tests/test_domain_entities.py

"""
DOMAIN ENTITIES UNIT TESTS
Comprehensive tests for domain entities and business logic

DOMAIN TESTS COVER:
- User entity business rules and invariants
- Email address validation
- Role-based permissions
- User security metadata
- Domain events
- Business logic edge cases

Author: Security Team
Version: 2.0 Enterprise Security
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.domain.entities.user import (
    User, EmailAddress, UserPreferences, UserSecurityMetadata,
    UserRole, UserStatus
)


class TestEmailAddress:
    """Test EmailAddress value object"""

    def test_valid_email_creation(self):
        """Test creating valid email addresses"""
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org",
            "user123@test-domain.com"
        ]

        for email in valid_emails:
            email_obj = EmailAddress(value=email)
            assert email_obj.value == email
            assert not email_obj.is_verified()

    def test_invalid_email_creation(self):
        """Test that invalid emails raise ValueError"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..name@example.com",
            "user@.com",
            "",
            "plainaddress"
        ]

        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email address"):
                EmailAddress(value=email)

    def test_email_domain_extraction(self):
        """Test extracting domain from email"""
        email = EmailAddress(value="user@example.com")
        assert email.domain() == "example.com"

        email = EmailAddress(value="test@sub.domain.co.uk")
        assert email.domain() == "sub.domain.co.uk"

    def test_email_verification(self):
        """Test email verification process"""
        email = EmailAddress(value="user@example.com")
        token = "verification_token_123"

        # Initially not verified
        assert not email.is_verified()

        # Verify with correct token
        assert email.verify(token)
        assert email.is_verified()

        # Verify again should return False
        assert not email.verify("wrong_token")

        # Token should be cleared after verification
        assert email._verification_token is None

    def test_email_verification_with_wrong_token(self):
        """Test email verification fails with wrong token"""
        email = EmailAddress(value="user@example.com")
        email._verification_token = "correct_token"

        # Wrong token should fail
        assert not email.verify("wrong_token")
        assert not email.is_verified()


class TestUserPreferences:
    """Test UserPreferences value object"""

    def test_default_preferences(self):
        """Test default preference values"""
        prefs = UserPreferences()
        assert prefs.timezone == "UTC"
        assert prefs.language == "en"
        assert prefs.notifications_enabled is True
        assert prefs.email_notifications is True
        assert prefs.two_factor_enabled is False

    def test_custom_preferences(self):
        """Test creating preferences with custom values"""
        prefs = UserPreferences(
            timezone="America/New_York",
            language="es",
            notifications_enabled=False,
            two_factor_enabled=True
        )
        assert prefs.timezone == "America/New_York"
        assert prefs.language == "es"
        assert prefs.notifications_enabled is False
        assert prefs.email_notifications is True  # Default value
        assert prefs.two_factor_enabled is True


class TestUserSecurityMetadata:
    """Test UserSecurityMetadata value object"""

    def test_default_security_metadata(self):
        """Test default security metadata values"""
        metadata = UserSecurityMetadata()
        assert metadata.failed_login_attempts == 0
        assert metadata.last_login_at is None
        assert metadata.last_login_ip is None
        assert metadata.password_changed_at is None
        assert metadata.mfa_enabled is False
        assert metadata.device_trusted == []

    def test_device_trusted_list(self):
        """Test trusted devices management"""
        metadata = UserSecurityMetadata()
        device_id = "device_123"

        # Add trusted device
        metadata.add_device_to_trusted(device_id)
        assert device_id in metadata.device_trusted

        # Add same device should not duplicate
        metadata.add_device_to_trusted(device_id)
        assert metadata.device_trusted.count(device_id) == 1

        # Remove trusted device
        metadata.remove_device_from_trusted(device_id)
        assert device_id not in metadata.device_trusted


class TestUserEntity:
    """Test User domain entity"""

    def test_user_creation_with_valid_data(self):
        """Test creating user with valid data"""
        email = EmailAddress(value="user@example.com")
        user = User(
            email=email,
            full_name="Test User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE
        )

        assert user.email == email
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.is_active()
        assert user.can_login()

    def test_user_creation_with_invalid_phone(self):
        """Test user creation fails with invalid phone"""
        email = EmailAddress(value="user@example.com")

        with pytest.raises(ValueError, match="Invalid phone number format"):
            User(
                email=email,
                full_name="Test User",
                phone="invalid-phone"
            )

    def test_user_creation_with_short_name(self):
        """Test user creation fails with short name"""
        email = EmailAddress(value="user@example.com")

        with pytest.raises(ValueError, match="Full name must be at least 2 characters"):
            User(
                email=email,
                full_name="A"  # Too short
            )

    def test_user_security_score(self):
        """Test user security score calculation"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User")

        # Base score (20)
        assert user.get_security_score() == 20

        # Email verification adds 20
        email._is_verified = True
        assert user.get_security_score() == 40

        # Recent password change adds 20
        user.security_metadata.password_changed_at = datetime.utcnow()
        assert user.get_security_score() == 60

        # MFA enabled adds 25
        user.enable_mfa()
        assert user.get_security_score() == 85

        # Trusted devices add 10
        user.add_device_to_trusted("device_1")
        assert user.get_security_score() == 95

        # No failed attempts adds 5
        assert user.get_security_score() == 100

        # Test score caps at 100
        user.add_device_to_trusted("device_2")  # Too many devices
        assert user.get_security_score() == 100  # Still capped

    def test_user_login_attempts(self):
        """Test failed login attempts tracking"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User")

        # Initial state
        assert user.can_login()
        assert user.security_metadata.failed_login_attempts == 0

        # Increment failed attempts
        assert not user.increment_failed_login()  # Should not suspend yet
        assert user.security_metadata.failed_login_attempts == 1
        assert user.can_login()

        # Add more failed attempts (up to suspension threshold)
        for i in range(4):  # Total will be 5
            user.increment_failed_login()

        # Should be suspended after 5 attempts
        assert not user.can_login()
        assert user.status == UserStatus.SUSPENDED

    def test_user_successful_login(self):
        """Test recording successful login"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User")

        # Set up some failed attempts
        for _ in range(3):
            user.increment_failed_login()

        assert user.security_metadata.failed_login_attempts == 3

        # Record successful login
        user.record_login("192.168.1.1", "Mozilla/5.0...")

        # Should reset failed attempts
        assert user.security_metadata.failed_login_attempts == 0
        assert user.security_metadata.last_login_at is not None
        assert user.security_metadata.last_login_ip == "192.168.1.1"

        # Should reactivate suspended user
        user.status = UserStatus.SUSPENDED
        user.record_login("192.168.1.1", "Mozilla/5.0...")
        assert user.status == UserStatus.ACTIVE

    def test_user_profile_update(self):
        """Test updating user profile"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User")

        # Update full name
        user.update_profile(full_name="New Name")
        assert user.full_name == "New Name"

        # Update phone
        user.update_profile(phone="+1234567890")
        assert user.phone == "+1234567890"

        # Invalid phone should raise error
        with pytest.raises(ValueError, match="Invalid phone number format"):
            user.update_profile(phone="invalid")

    def test_user_email_verification(self):
        """Test email verification process"""
        email = EmailAddress(value="user@example.com")
        user = User(
            email=email,
            full_name="Test User",
            status=UserStatus.PENDING_VERIFICATION
        )

        # Initially pending verification
        assert not user.is_active()
        assert not user.can_login()

        # Set up verification token
        email._verification_token = "token_123"

        # Verify email
        assert user.verify_email("token_123")
        assert user.status == UserStatus.ACTIVE
        assert user.email.is_verified()

        # Should now be able to login
        assert user.is_active()

    def test_user_role_permissions(self):
        """Test role-based permissions"""
        email = EmailAddress(value="user@example.com")

        # Test different roles
        roles_permissions = [
            (UserRole.USER, ["read_profile", "update_profile"]),
            (UserRole.MODERATOR, ["read_profile", "update_profile", "manage_users"]),
            (UserRole.MANAGER, ["read_profile", "update_profile", "manage_users", "view_reports"]),
            (UserRole.ADMIN, ["all"])
        ]

        for role, expected_permissions in roles_permissions:
            user = User(email=email, role=role)

            for permission in expected_permissions:
                assert user.has_role_permission(permission), f"Role {role} should have permission {permission}"

    def test_user_admin_and_manager_checks(self):
        """Test admin and manager role checks"""
        email = EmailAddress(value="user@example.com")

        roles = [
            (UserRole.USER, False, False),
            (UserRole.MODERATOR, False, False),
            (UserRole.MANAGER, False, True),
            (UserRole.ADMIN, True, True)
        ]

        for role, is_admin, is_manager in roles:
            user = User(email=email, role=role)
            assert user.is_admin() == is_admin
            assert user.is_manager() == is_manager

    def test_user_suspension_and_activation(self):
        """Test user suspension and activation"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User", status=UserStatus.ACTIVE)

        # Suspend user
        user.suspend("Violation of terms")
        assert user.status == UserStatus.SUSPENDED
        assert user.metadata["suspension_reason"] == "Violation of terms"

        # Should not be able to login when suspended
        assert not user.can_login()

        # Activate user
        user.activate()
        assert user.status == UserStatus.ACTIVE
        assert "suspension_reason" not in user.metadata

        # Should be able to login when active
        assert user.can_login()

    def test_user_deactivation(self):
        """Test user deactivation"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User", status=UserStatus.ACTIVE)

        # Deactivate user
        user.deactivate()
        assert user.status == UserStatus.INACTIVE

        # Should not be able to login when inactive
        assert not user.is_active()
        assert not user.can_login()

    def test_user_password_change(self):
        """Test password change recording"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User")

        # Set some failed attempts
        user.increment_failed_login()
        assert user.security_metadata.failed_login_attempts == 1

        # Change password
        user.change_password()

        # Should record password change time
        assert user.security_metadata.password_changed_at is not None

        # Should reset failed attempts
        assert user.security_metadata.failed_login_attempts == 0

    def test_user_domain_events(self):
        """Test domain event generation"""
        now = datetime.utcnow()
        email = EmailAddress(value="user@example.com")
        user = User(
            email=email,
            full_name="Test User",
            role=UserRole.USER,
            created_at=now
        )

        # Record login
        user.record_login("192.168.1.1", "Mozilla/5.0...")

        # Get domain events
        events = user.get_domain_events()

        assert len(events) == 2

        # Check user creation event
        creation_event = events[0]
        assert creation_event["type"] == "UserCreated"
        assert creation_event["user_id"] == user.id
        assert creation_event["email"] == email.value
        assert creation_event["role"] == UserRole.USER.value

        # Check login event
        login_event = events[1]
        assert login_event["type"] == "UserLoggedIn"
        assert login_event["user_id"] == user.id
        assert login_event["ip_address"] == "192.168.1.1"

    def test_user_to_dict_conversion(self):
        """Test converting user to dictionary"""
        now = datetime.utcnow()
        email = EmailAddress(value="user@example.com")
        email._is_verified = True

        user = User(
            email=email,
            full_name="Test User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            organization_id="org_123",
            phone="+1234567890",
            created_at=now
        )

        user_dict = user.to_dict()

        # Check required fields
        assert user_dict["email"] == email.value
        assert user_dict["is_verified"] is True
        assert user_dict["full_name"] == "Test User"
        assert user_dict["role"] == UserRole.USER.value
        assert user_dict["status"] == UserStatus.ACTIVE.value
        assert user_dict["organization_id"] == "org_123"
        assert user_dict["phone"] == "+1234567890"

        # Check computed fields
        assert user_dict["is_active"] is True
        assert user_dict["can_login"] is True

        # Check preferences structure
        assert "preferences" in user_dict
        assert user_dict["preferences"]["timezone"] == "UTC"

        # Check security metadata structure
        assert "security_metadata" in user_dict
        assert "security_score" in user_dict["security_metadata"]
        assert isinstance(user_dict["security_metadata"]["security_score"], int)

    def test_user_business_rules_validation(self):
        """Test business rules for user operations"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, full_name="Test User", role=UserRole.USER)

        # Test role change permissions
        assert user.can_update_role(UserRole.USER, UserRole.USER)
        assert user.can_update_role(UserRole.USER, UserRole.MODERATOR)  # User can be upgraded to moderator
        assert not user.can_update_role(UserRole.ADMIN, UserRole.USER)  # Admin can't be demoted by non-admin
        assert not user.can_update_role(UserRole.ADMIN, UserRole.USER)  # Users can't change their own role to admin

        # Test user deletion permissions
        assert not user.can_be_deleted_by(UserRole.USER)  # Users can't delete users
        assert user.can_be_deleted_by(UserRole.MANAGER)  # Managers can delete non-admin users
        assert user.can_be_deleted_by(UserRole.ADMIN)    # Admins can delete anyone

        # Test admin deletion protection
        admin_user = User(email=EmailAddress(value="admin@example.com"), role=UserRole.ADMIN)
        assert not admin_user.can_be_deleted_by(UserRole.MANAGER)  # Managers can't delete admins
        assert admin_user.can_be_deleted_by(UserRole.ADMIN)        # Admins can delete admins

    @pytest.mark.parametrize("status,can_login_expected", [
        (UserStatus.ACTIVE, False),  # Email not verified yet
        (UserStatus.INACTIVE, False),
        (UserStatus.SUSPENDED, False),
        (UserStatus.PENDING_VERIFICATION, False)
    ])
    def test_user_can_login_by_status(self, status, can_login_expected):
        """Test can_login logic based on user status"""
        email = EmailAddress(value="user@example.com")
        user = User(email=email, status=status)

        # Can't login without verified email regardless of status
        assert user.can_login() == False

        # Verify email and test again
        email._is_verified = True

        if status == UserStatus.ACTIVE:
            assert user.can_login() == True
        else:
            assert user.can_login() == False

    def test_user_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # User with maximum name length
        long_name = "A" * 1000  # Very long name
        email = EmailAddress(value="user@example.com")

        # Should handle long names gracefully
        user = User(email=email, full_name=long_name)
        assert user.full_name == long_name

        # User with many trusted devices
        for i in range(100):
            user.add_device_to_trusted(f"device_{i}")

        assert len(user.security_metadata.device_trusted) == 100

        # User with very old password change
        old_date = datetime.utcnow() - timedelta(days=365)
        user.security_metadata.password_changed_at = old_date

        # Security score should be lower for old password
        score = user.get_security_score()
        assert score < 60  # Should be penalized for old password
