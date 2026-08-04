# app/domain/entities/user_entity.py
"""
User Domain Entity

Pure business object representing a User in the system.
Independent of infrastructure (database, API frameworks).
Contains business logic and validation rules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from app.domain.exceptions import ValidationError
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password


class UserRole(Enum):
    """User role enumeration"""

    ADMIN = "ADMIN"
    USER = "USER"
    TEAM_LEAD = "TEAM_LEAD"


@dataclass
class User:
    """
    User domain entity.

    This is a pure business object that encapsulates user-related
    business logic and validation rules. It's independent of any
    infrastructure concerns (database, API frameworks).

    Attributes:
        id: Unique identifier (auto-generated on creation)
        email: User's email address (validated)
        full_name: User's full name
        password: Password value object (contains hashed password)
        role: User's role in the system
        is_active: Whether the user is active
        is_verified: Whether email has been verified
        is_superuser: Admin privileges
        created_at: Account creation timestamp
        updated_at: Last update timestamp

    Example:
        >>> user = User.create(
        ...     email=Email("user@example.com"),
        ...     password=Password.create("SecurePass123!"),
        ...     full_name="John Doe"
        ... )
        >>> user.is_active
        True
    """

    # Primary identifier
    id: UUID = field(default_factory=uuid4)

    # User information
    email: Email
    full_name: Optional[str] = None
    password: Password

    # Role and status
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create(
        cls,
        email: Email,
        password: Password,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
    ) -> "User":
        """
        Create a new user with validation.

        Args:
            email: Validated email value object
            password: Validated password value object
            full_name: User's full name (optional)
            role: User role (defaults to USER)

        Returns:
            New User instance

        Raises:
            ValidationError: If validation fails

        Example:
            >>> user = User.create(
            ...     email=Email("user@example.com"),
            ...     password=Password.create("SecurePass123!"),
            ...     full_name="John Doe"
            ... )
        """
        # Validate full name if provided
        if full_name and len(full_name.strip()) < 2:
            raise ValidationError("Full name must be at least 2 characters")

        return cls(
            email=email,
            password=password,
            full_name=full_name.strip() if full_name else None,
            role=role,
        )

    @classmethod
    def from_db(
        cls,
        id: UUID,
        email_str: str,
        password_hash: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        is_verified: bool = False,
        is_superuser: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> "User":
        """
        Reconstruct User from database representation.

        This method is used by repositories to convert database models
        back into domain entities.

        Args:
            id: User ID from database
            email_str: Email string
            password_hash: Hashed password from database
            full_name: User's full name
            role: User role
            is_active: Active status
            is_verified: Email verification status
            is_superuser: Superuser status
            created_at: Creation timestamp
            updated_at: Update timestamp

        Returns:
            User domain entity

        Example:
            >>> user = User.from_db(
            ...     id=user_id,
            ...     email_str="user@example.com",
            ...     password_hash="$2b$12$..."
            ... )
        """
        return cls(
            id=id,
            email=Email(email_str),  # Validation happens in Email VO
            password=Password.from_hash(password_hash),
            full_name=full_name,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            is_superuser=is_superuser,
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )

    # ========================================================================
    # BUSINESS LOGIC METHODS
    # ========================================================================

    def verify_email(self) -> None:
        """
        Mark user's email as verified.

        Example:
            >>> user.verify_email()
            >>> user.is_verified
            True
        """
        self.is_verified = True
        self._touch()

    def activate(self) -> None:
        """
        Activate user account.

        Example:
            >>> user.activate()
            >>> user.is_active
            True
        """
        self.is_active = True
        self._touch()

    def deactivate(self) -> None:
        """
        Deactivate user account.

        Example:
            >>> user.deactivate()
            >>> user.is_active
            False
        """
        self.is_active = False
        self._touch()

    def promote_to_admin(self) -> None:
        """
        Promote user to admin role.

        Raises:
            ValidationError: If user is not a superuser

        Example:
            >>> user.promote_to_admin()
            >>> user.role
            <UserRole.ADMIN: 'ADMIN'>
        """
        if not self.is_superuser:
            raise ValidationError("Only superusers can be promoted to admin")

        self.role = UserRole.ADMIN
        self._touch()

    def change_password(self, new_password: Password) -> None:
        """
        Change user's password.

        Args:
            new_password: New password value object

        Example:
            >>> new_password = Password.create("NewSecurePass123!")
            >>> user.change_password(new_password)
        """
        self.password = new_password
        self._touch()

    def update_profile(self, full_name: Optional[str] = None) -> None:
        """
        Update user's profile information.

        Args:
            full_name: New full name (optional)

        Raises:
            ValidationError: If full name is too short

        Example:
            >>> user.update_profile(full_name="Jane Smith")
        """
        if full_name:
            if len(full_name.strip()) < 2:
                raise ValidationError("Full name must be at least 2 characters")
            self.full_name = full_name.strip()

        self._touch()

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def can_login(self) -> bool:
        """
        Check if user is allowed to login.

        Returns:
            True if user can login (active and verified)

        Example:
            >>> if user.can_login():
            ...     print("User can login")
        """
        return self.is_active and self.is_verified

    def is_admin(self) -> bool:
        """
        Check if user has admin privileges.

        Returns:
            True if user is admin or superuser

        Example:
            >>> if user.is_admin():
            ...     print("User has admin privileges")
        """
        return self.role == UserRole.ADMIN or self.is_superuser

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _touch(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(self) -> dict:
        """
        Convert user to dictionary (for API responses).

        Excludes sensitive data like password hash.

        Returns:
            Dictionary representation of user

        Example:
            >>> data = user.to_dict()
            >>> print(data['email'])
            'user@example.com'
        """
        return {
            "id": str(self.id),
            "email": str(self.email),
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        """String representation of user"""
        return f"User(id={self.id}, email={self.email}, role={self.role.value})"
