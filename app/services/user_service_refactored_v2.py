"""
Refactored User Service

This is the CORRECT service layer implementation.
It focuses ONLY on user-related business logic.

Responsibilities:
- User CRUD operations business rules
- Password validation business rules
- User authentication business logic

NOT responsible for:
- Database queries (that's UserRepository's job)
- HTTP requests/responses (that's API layer's job)
- Password hashing mechanics (infrastructure concern)
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import AuditLogger, SecurityEventType
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.db.models.user import User
from app.services.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


class WeakPasswordError(ValueError):
    """Business rule exception for weak passwords"""

    pass


class InvalidCredentialsError(ValueError):
    """Business rule exception for invalid credentials"""

    pass


class UserService:
    """
    User business logic service

    This service orchestrates user operations by:
    1. Using UserRepository for data access
    2. Applying business rules
    3. Using domain services (password hashing)

    It does NOT contain:
    - Database queries (delegated to UserRepository)
    - HTTP handling (API layer's job)
    - Caching logic (infrastructure concern)
    """

    def __init__(self, user_repo: UserRepository):
        """
        Initialize user service with repository dependency

        Args:
            user_repo: Repository for user data access
        """
        self._user_repo = user_repo

    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password meets security requirements

        This is a BUSINESS RULE about password strength.
        The rule itself is defined here, but hashing is delegated.

        Args:
            password: Password to validate

        Raises:
            WeakPasswordError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise WeakPasswordError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            raise WeakPasswordError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )

        # Business rule: check for common weak patterns
        common_patterns = ["password", "123456", "qwerty", "admin", "user"]
        if any(pattern in password.lower() for pattern in common_patterns):
            raise WeakPasswordError("Password contains common weak patterns")

    async def create_user(
        self,
        user_data: UserCreate,
        created_by: UUID | None = None,
    ) -> User:
        """
        Create a new user with business rule validation

        BUSINESS LOGIC:
        - Password strength validation
        - Email format validation (via repository)
        - Default settings

        DATA ACCESS (delegated to repository):
        - Checking email uniqueness
        - Creating user record
        - Handling organizations

        Args:
            user_data: User creation data
            created_by: ID of user creating this account

        Returns:
            Created User entity

        Raises:
            WeakPasswordError: If password doesn't meet strength requirements
            ValueError: If email already exists
        """
        try:
            # Business rule: validate password strength
            self._validate_password_strength(user_data.password)

            # Business rule: hash password (delegated to infrastructure service)
            hashed_password = get_password_hash(user_data.password)

            # Update user data with hashed password
            # Note: We need to convert to dict to update the password
            user_dict = user_data.dict()
            user_dict["password_hash"] = hashed_password
            # Remove plain text password
            user_dict.pop("password", None)

            # Create updated schema without plain password
            from pydantic import BaseModel

            class UserCreateHashed(BaseModel):
                email: str
                full_name: str | None = None
                password_hash: str
                organization_id: int | None = None

            hashed_data = UserCreateHashed(**user_dict)

            # Data access: delegate to repository
            user = await self._user_repo.create(hashed_data, created_by=created_by)

            # Business event: audit log
            AuditLogger.log_security_event(
                event_type=SecurityEventType.USER_REGISTRATION,
                details=f"User account created: {user.email}",
                additional_data={
                    "email": user.email,
                    "organization_id": (
                        str(user.organization_id) if user.organization_id else None
                    ),
                    "created_by": str(created_by) if created_by else "system",
                },
            )

            logger.info(f"Created user: {user.email} (ID: {user.id})")
            return user

        except WeakPasswordError:
            raise
        except ValueError as e:
            # Re-raise value errors (e.g., duplicate email)
            AuditLogger.log_security_event(
                event_type=SecurityEventType.USER_REGISTRATION_FAILED,
                details=f"User creation failed: {str(e)}",
                additional_data={"email": user_data.email},
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            AuditLogger.log_security_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                details=f"Unexpected user creation error: {str(e)}",
            )
            raise ValueError("An unexpected error occurred. Please try again.") from e

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:
        """
        Authenticate user with credentials

        BUSINESS LOGIC:
        - Authentication rules
        - Account status validation

        Args:
            email: User email
            password: Plain text password

        Returns:
            Authenticated User entity

        Raises:
            InvalidCredentialsError: If credentials are invalid
            ValueError: If account is inactive/locked
        """
        try:
            # Data access: find user by email
            user = await self._user_repo.get_by_email(email)

            if not user:
                # Business rule: don't reveal if user exists
                raise InvalidCredentialsError("Invalid email or password")

            # Business rule: check if account is active
            if not user.is_active:
                raise ValueError("Account is inactive. Please contact support.")

            # Business rule: verify password
            if not verify_password(password, user.password_hash):
                # Business rule: log failed attempt
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.INVALID_INPUT,
                    details=f"Failed authentication attempt for email: {email}",
                )
                raise InvalidCredentialsError("Invalid email or password")

            # Business rule: successful authentication
            AuditLogger.log_security_event(
                event_type=SecurityEventType.DATA_ACCESS,
                details=f"User authenticated: {email}",
                additional_data={"user_id": str(user.id)},
            )

            return user

        except InvalidCredentialsError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise InvalidCredentialsError("Authentication failed") from e

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change user password

        BUSINESS LOGIC:
        - Verify current password
        - Validate new password strength
        - Update password

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Raises:
            InvalidCredentialsError: If current password is incorrect
            WeakPasswordError: If new password doesn't meet requirements
        """
        try:
            # Data access: get user
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Business rule: verify current password
            if not verify_password(current_password, user.password_hash):
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.INVALID_INPUT,
                    details=f"Failed password change attempt for user {user_id}",
                )
                raise InvalidCredentialsError("Current password is incorrect")

            # Business rule: validate new password strength
            self._validate_password_strength(new_password)

            # Business rule: hash new password
            new_hashed_password = get_password_hash(new_password)

            # Data access: update user
            update_data = UserUpdate(password_hash=new_hashed_password)
            await self._user_repo.update(user_id, update_data)

            # Business event: audit log
            AuditLogger.log_security_event(
                event_type=SecurityEventType.DATA_ACCESS,
                details=f"Password changed for user {user_id}",
                additional_data={"user_id": str(user_id)},
            )

            logger.info(f"Password changed for user: {user.email} (ID: {user_id})")

        except (InvalidCredentialsError, WeakPasswordError, ValueError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error changing password for user {user_id}: {e}")
            raise ValueError("Failed to change password") from e

    async def deactivate_user(
        self,
        user_id: UUID,
        reason: str | None = None,
        deactivated_by: UUID | None = None,
    ) -> None:
        """
        Deactivate user account

        BUSINESS LOGIC:
        - Account deactivation rules
        - Audit logging

        Args:
            user_id: User ID to deactivate
            reason: Reason for deactivation
            deactivated_by: Admin user ID performing deactivation

        Raises:
            ValueError: If user not found
        """
        try:
            # Data access: delegate to repository
            success = await self._user_repo.deactivate_user(
                user_id, reason=reason, deactivated_by=deactivated_by
            )

            if not success:
                raise ValueError(f"User {user_id} not found")

            # Business event: audit log
            AuditLogger.log_security_event(
                event_type=SecurityEventType.DATA_ACCESS,
                details=f"User deactivated: {user_id}",
                additional_data={
                    "user_id": str(user_id),
                    "reason": reason,
                    "deactivated_by": str(deactivated_by) if deactivated_by else None,
                },
            )

            logger.info(f"Deactivated user: {user_id}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deactivating user {user_id}: {e}")
            raise ValueError("Failed to deactivate user") from e

    async def reactivate_user(
        self,
        user_id: UUID,
        reactivated_by: UUID | None = None,
    ) -> None:
        """
        Reactivate user account

        Args:
            user_id: User ID to reactivate
            reactivated_by: Admin user ID performing reactivation

        Raises:
            ValueError: If user not found
        """
        try:
            # Data access: delegate to repository
            success = await self._user_repo.reactivate_user(
                user_id, reactivated_by=reactivated_by
            )

            if not success:
                raise ValueError(f"User {user_id} not found")

            # Business event: audit log
            AuditLogger.log_security_event(
                event_type=SecurityEventType.DATA_ACCESS,
                details=f"User reactivated: {user_id}",
                additional_data={
                    "user_id": str(user_id),
                    "reactivated_by": str(reactivated_by) if reactivated_by else None,
                },
            )

            logger.info(f"Reactivated user: {user_id}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error reactivating user {user_id}: {e}")
            raise ValueError("Failed to reactivate user") from e


# Factory function to create service instance with repository
def create_user_service(db: AsyncSession) -> UserService:
    """
    Factory function to create user service with repository dependency

    Args:
        db: Database session

    Returns:
        UserService instance with injected repository
    """
    return UserService(user_repo=UserRepository(db))
