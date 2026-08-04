# app/domain/entities/user.py

"""
DOMAIN ENTITY - USER
Core domain entity representing a user in the system

DOMAIN ENTITY PRINCIPLES:
- Pure business logic with no infrastructure dependencies
- Rich domain model with behavior
- Domain invariants and validation
- No framework-specific code
- Clear separation from persistence concerns

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# Initialize domain logger
domain_logger = logging.getLogger("app.domain.user")


class UserRole(Enum):
    """User roles with business logic validation"""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MANAGER = "manager"

    @classmethod
    def has_permission(cls, role: "UserRole", permission: str) -> bool:
        """Check if role has specific permission"""
        permissions = {
            cls.USER: ["read_profile", "update_profile"],
            cls.MODERATOR: ["read_profile", "update_profile", "manage_users"],
            cls.MANAGER: [
                "read_profile",
                "update_profile",
                "manage_users",
                "view_reports",
            ],
            cls.ADMIN: ["all"],
        }
        return permission in permissions.get(role, [])


class UserStatus(Enum):
    """User status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class EmailAddress:
    """Value object for email address with validation"""

    value: str
    _is_verified: bool = False
    _verification_token: str | None = None

    def __post_init__(self):
        """Validate email on creation"""
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email address: {self.value}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def is_verified(self) -> bool:
        """Check if email is verified"""
        return self._is_verified

    def verify(self, token: str) -> bool:
        """Verify email with token"""
        if self._verification_token == token:
            self._is_verified = True
            self._verification_token = None
            return True
        return False

    def domain(self) -> str:
        """Get email domain"""
        return self.value.split("@")[-1].lower()


@dataclass
class UserPreferences:
    """User preferences value object"""

    timezone: str = "UTC"
    language: str = "en"
    notifications_enabled: bool = True
    email_notifications: bool = True
    two_factor_enabled: bool = False


@dataclass
class UserSecurityMetadata:
    """User security metadata"""

    failed_login_attempts: int = 0
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    password_changed_at: datetime | None = None
    mfa_enabled: bool = False
    device_trusted: list[str] = field(default_factory=list)


@dataclass
class User:
    """
    Core domain entity representing a user

    This entity contains only business logic and domain rules,
    with no infrastructure or persistence concerns.
    """

    # Core attributes
    id: str | None = None
    email: EmailAddress = field(default_factory=lambda: EmailAddress(value=""))
    full_name: str | None = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING_VERIFICATION

    # Audit fields
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    # Optional attributes
    organization_id: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    bio: str | None = None

    # Value objects
    preferences: UserPreferences = field(default_factory=UserPreferences)
    security_metadata: UserSecurityMetadata = field(
        default_factory=UserSecurityMetadata
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate user invariants after initialization"""
        self._validate_invariants()

    def _validate_invariants(self):
        """Validate business invariants"""
        # Email is required
        if not self.email or not self.email.value:
            raise ValueError("Email address is required")

        # Full name validation
        if self.full_name and len(self.full_name.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")

        # Phone number validation (if provided)
        if self.phone and not self._is_valid_phone(self.phone):
            raise ValueError("Invalid phone number format")

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone number format"""
        import re

        # Basic phone validation - can be enhanced
        pattern = r"^\+?[\d\s\-\(\)]{10,}$"
        return re.match(pattern, phone) is not None

    # Domain Methods - Business Logic

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE

    def can_login(self) -> bool:
        """Check if user can login based on status and verification"""
        return (
            self.status == UserStatus.ACTIVE
            and self.email.is_verified()
            and self.security_metadata.failed_login_attempts < 5
        )

    def increment_failed_login(self) -> bool:
        """Increment failed login attempts"""
        self.security_metadata.failed_login_attempts += 1
        self.updated_at = datetime.utcnow()

        # Check if account should be suspended
        if self.security_metadata.failed_login_attempts >= 5:
            self.status = UserStatus.SUSPENDED
            domain_logger.warning(
                f"User {self.id} suspended due to too many failed login attempts"
            )
            return True

        return False

    def reset_failed_login_attempts(self):
        """Reset failed login attempts after successful login"""
        self.security_metadata.failed_login_attempts = 0
        self.updated_at = datetime.utcnow()

    def record_login(self, ip_address: str, user_agent: str):
        """Record successful login"""
        self.security_metadata.last_login_at = datetime.utcnow()
        self.security_metadata.last_login_ip = ip_address
        self.reset_failed_login_attempts()

        # If user was suspended, reactivate them
        if self.status == UserStatus.SUSPENDED:
            self.status = UserStatus.ACTIVE
            domain_logger.info(f"User {self.id} reactivated after successful login")

    def change_password(self) -> None:
        """Record password change"""
        self.security_metadata.password_changed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Reset failed login attempts after password change
        self.reset_failed_login_attempts()

    def update_profile(self, full_name: str | None = None, phone: str | None = None):
        """Update user profile information"""
        if full_name:
            if len(full_name.strip()) < 2:
                raise ValueError("Full name must be at least 2 characters")
            self.full_name = full_name.strip()

        if phone and not self._is_valid_phone(phone):
            raise ValueError("Invalid phone number format")

        if phone:
            self.phone = phone

        self.updated_at = datetime.utcnow()

    def verify_email(self, token: str) -> bool:
        """Verify user email address"""
        if self.email.verify(token):
            # If email was the only thing preventing activation
            if self.status == UserStatus.PENDING_VERIFICATION:
                self.status = UserStatus.ACTIVE
            self.updated_at = datetime.utcnow()
            return True
        return False

    def suspend(self, reason: str = "Administrative action"):
        """Suspend user account"""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
        self.metadata["suspension_reason"] = reason
        domain_logger.info(f"User {self.id} suspended: {reason}")

    def activate(self):
        """Activate user account"""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        if "suspension_reason" in self.metadata:
            del self.metadata["suspension_reason"]

    def deactivate(self):
        """Deactivate user account"""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def has_role_permission(self, permission: str) -> bool:
        """Check if user has specific permission based on role"""
        return self.role.has_permission(self.role, permission)

    def is_admin(self) -> bool:
        """Check if user is an administrator"""
        return self.role == UserRole.ADMIN

    def is_manager(self) -> bool:
        """Check if user has management role"""
        return self.role in [UserRole.MANAGER, UserRole.ADMIN]

    def add_device_to_trusted(self, device_id: str):
        """Add device to trusted devices"""
        if device_id not in self.security_metadata.device_trusted:
            self.security_metadata.device_trusted.append(device_id)
            self.updated_at = datetime.utcnow()

    def remove_device_from_trusted(self, device_id: str):
        """Remove device from trusted devices"""
        if device_id in self.security_metadata.device_trusted:
            self.security_metadata.device_trusted.remove(device_id)
            self.updated_at = datetime.utcnow()

    def is_device_trusted(self, device_id: str) -> bool:
        """Check if device is trusted"""
        return device_id in self.security_metadata.device_trusted

    def enable_mfa(self):
        """Enable multi-factor authentication"""
        self.security_metadata.mfa_enabled = True
        self.preferences.two_factor_enabled = True
        self.updated_at = datetime.utcnow()

    def disable_mfa(self):
        """Disable multi-factor authentication"""
        self.security_metadata.mfa_enabled = False
        self.preferences.two_factor_enabled = False
        self.updated_at = datetime.utcnow()

    def update_preferences(self, **kwargs):
        """Update user preferences"""
        for key, value in kwargs.items():
            if hasattr(self.preferences, key):
                setattr(self.preferences, key, value)
        self.updated_at = datetime.utcnow()

    # Domain Events
    def get_domain_events(self) -> list[dict[str, Any]]:
        """Get domain events that occurred"""
        events = []

        if self.created_at:
            events.append(
                {
                    "type": "UserCreated",
                    "timestamp": self.created_at.isoformat(),
                    "user_id": self.id,
                    "email": self.email.value,
                    "role": self.role.value,
                }
            )

        if self.security_metadata.last_login_at:
            events.append(
                {
                    "type": "UserLoggedIn",
                    "timestamp": self.security_metadata.last_login_at.isoformat(),
                    "user_id": self.id,
                    "ip_address": self.security_metadata.last_login_ip,
                }
            )

        return events

    # Business Rules Validation
    def can_be_deleted_by(self, requesting_user_role: UserRole) -> bool:
        """Check if user can be deleted by requesting user"""
        # Users cannot delete themselves
        if requesting_user_role == UserRole.USER:
            return False

        # Admins can delete users, managers can delete non-admin users
        if requesting_user_role == UserRole.ADMIN:
            return True

        if requesting_user_role == UserRole.MANAGER:
            return self.role != UserRole.ADMIN

        return False

    def can_update_role(
        self, new_role: UserRole, requesting_user_role: UserRole
    ) -> bool:
        """Check if role can be updated by requesting user"""
        # Only admins can change roles
        if requesting_user_role != UserRole.ADMIN:
            return False

        # Admins cannot change their own role (safety check)
        if self.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            return False

        return True

    def get_security_score(self) -> int:
        """Calculate user security score (0-100)"""
        score = 0

        # Base score for having any security
        score += 20

        # Email verification
        if self.email.is_verified():
            score += 20

        # Strong password indication (based on last change)
        if (
            self.security_metadata.password_changed_at
            and (datetime.utcnow() - self.security_metadata.password_changed_at).days
            < 90
        ):
            score += 20

        # MFA enabled
        if self.security_metadata.mfa_enabled:
            score += 25

        # Trusted devices (not too many)
        trusted_devices = len(self.security_metadata.device_trusted)
        if 1 <= trusted_devices <= 3:
            score += 10

        # No recent failed login attempts
        if self.security_metadata.failed_login_attempts == 0:
            score += 5

        return min(score, 100)

    def to_dict(self) -> dict[str, Any]:
        """Convert user entity to dictionary (for API responses)"""
        return {
            "id": self.id,
            "email": self.email.value,
            "is_verified": self.email.is_verified(),
            "full_name": self.full_name,
            "role": self.role.value,
            "status": self.status.value,
            "organization_id": self.organization_id,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "preferences": {
                "timezone": self.preferences.timezone,
                "language": self.preferences.language,
                "notifications_enabled": self.preferences.notifications_enabled,
                "email_notifications": self.preferences.email_notifications,
                "two_factor_enabled": self.preferences.two_factor_enabled,
            },
            "security_metadata": {
                "last_login_at": (
                    self.security_metadata.last_login_at.isoformat()
                    if self.security_metadata.last_login_at
                    else None
                ),
                "failed_login_attempts": self.security_metadata.failed_login_attempts,
                "mfa_enabled": self.security_metadata.mfa_enabled,
                "trusted_devices_count": len(self.security_metadata.device_trusted),
                "security_score": self.get_security_score(),
            },
            "is_active": self.is_active(),
            "can_login": self.can_login(),
        }
