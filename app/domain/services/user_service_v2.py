# app/domain/services/user_service_v2.py
"""
User Service - Refactored with Repository Pattern

This is the REFACTORED version that demonstrates clean separation:
- Business logic lives here
- Data access delegated to UserRepository
- Testable with mocked repositories

Compare this to app/services/user_service.py to see the improvement.
"""

from uuid import UUID

from app.domain.entities.user_entity import User, UserRole
from app.domain.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    User business logic service.

    This service contains all user-related business logic.
    It uses UserRepository for data access, keeping concerns separated.

    Example:
        >>> repo = UserRepository(db_session)
        >>> service = UserService(repo)
        >>> user = await service.create_user(UserCreate(...))
    """

    def __init__(self, repository):
        """
        Initialize user service.

        Args:
            repository: UserRepository instance (can be mocked for testing)
        """
        self._repository = repository

    # ========================================================================
    # USER CREATION
    # ========================================================================

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Business Rules:
        - Email must be unique
        - Email must be valid format
        - Password must meet strength requirements

        Args:
            user_data: User creation data

        Returns:
            Created User domain entity

        Raises:
            ValidationError: If validation fails

        Example:
            >>> user = await user_service.create_user(
            ...     UserCreate(
            ...         email="user@example.com",
            ...         password="SecurePassword123!"
            ...     )
            ... )
        """
        # Business rule: Check if email already exists
        existing = await self._repository.get_by_email(user_data.email)
        if existing:
            raise ValidationError(f"User with email {user_data.email} already exists")

        # Business rule: Validate email format
        try:
            email = Email(user_data.email)
        except ValueError as e:
            raise ValidationError(f"Invalid email: {e}")

        # Business rule: Validate password strength
        try:
            password = Password.create(user_data.password)
        except ValueError as e:
            raise ValidationError(f"Invalid password: {e}")

        # Business rule: Create user entity
        user = User.create(
            email=email,
            password=password,
            full_name=user_data.full_name,
            role=user_data.role if hasattr(user_data, "role") else UserRole.USER,
        )

        # Save to database (via repository)
        # Note: We convert domain entity to DB model here
        # This mapping could be moved to a mapper class
        from app.db.models.user import User as UserModel

        db_user = UserModel(
            email=str(user.email),
            password_hash=user.password.hash_value,  # Already hashed by Password VO
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
        )

        created_user = await self._repository.create(db_user)

        # Convert back to domain entity
        return User.from_db(
            id=created_user.id,
            email_str=created_user.email,
            password_hash=created_user.password_hash,
            full_name=created_user.full_name,
            role=UserRole(created_user.role),
            is_active=created_user.is_active,
            is_verified=created_user.is_verified,
            is_superuser=created_user.is_superuser,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
        )

    # ========================================================================
    # USER RETRIEVAL
    # ========================================================================

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User domain entity

        Raises:
            NotFoundError: If user not found

        Example:
            >>> user = await user_service.get_user_by_id(user_id)
            >>> print(user.full_name)
        """
        db_user = await self._repository.get(user_id)

        if not db_user:
            raise NotFoundError(f"User with ID {user_id} not found")

        return self._db_to_domain(db_user)

    async def get_user_by_email(self, email: str) -> User:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User domain entity

        Raises:
            NotFoundError: If user not found

        Example:
            >>> user = await user_service.get_user_by_email("user@example.com")
        """
        db_user = await self._repository.get_by_email(email)

        if not db_user:
            raise NotFoundError(f"User with email {email} not found")

        return self._db_to_domain(db_user)

    # ========================================================================
    # USER UPDATES
    # ========================================================================

    async def update_user(self, user_id: UUID, update_data: UserUpdate) -> User:
        """
        Update user information.

        Business Rules:
        - Cannot change email to existing email
        - Full name must be at least 2 characters if provided

        Args:
            user_id: User ID
            update_data: Update data

        Returns:
            Updated User domain entity

        Raises:
            NotFoundError: If user not found
            ValidationError: If validation fails

        Example:
            >>> updated = await user_service.update_user(
            ...     user_id,
            ...     UserUpdate(full_name="New Name")
            ... )
        """
        # Business rule: User must exist
        await self.get_user_by_id(user_id)

        # Business rule: Check email uniqueness if changing email
        if update_data.email:
            existing = await self._repository.get_by_email(update_data.email)
            if existing and existing.id != user_id:
                raise ValidationError("Email already in use")

        # Business rule: Validate full name
        if update_data.full_name and len(update_data.full_name.strip()) < 2:
            raise ValidationError("Full name must be at least 2 characters")

        # Update via repository
        # Convert update_data to dict for repository
        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle password separately (needs hashing)
        if "password" in update_dict:
            from app.services.security import get_password_hash

            update_dict["password_hash"] = get_password_hash(
                update_dict.pop("password")
            )

        db_user = await self._repository.update(user_id, update_dict)

        return self._db_to_domain(db_user)

    # ========================================================================
    # USER DELETION
    # ========================================================================

    async def delete_user(self, user_id: UUID, requesting_user: User) -> bool:
        """
        Delete a user.

        Business Rules:
        - Users can delete themselves
        - Admins can delete anyone
        - Cannot delete other users without admin privileges

        Args:
            user_id: ID of user to delete
            requesting_user: User making the request

        Returns:
            True if deleted

        Raises:
            NotFoundError: If user not found
            AuthorizationError: If not authorized

        Example:
            >>> await user_service.delete_user(target_id, current_user)
        """
        # Business rule: Check authorization
        if user_id != requesting_user.id and not requesting_user.is_admin():
            raise AuthorizationError(
                "You can only delete yourself (unless you're an admin)"
            )

        # Business rule: User must exist
        await self.get_user_by_id(user_id)

        # Delete via repository
        return await self._repository.delete(user_id)

    # ========================================================================
    # PASSWORD MANAGEMENT
    # ========================================================================

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> None:
        """
        Change user password.

        Business Rules:
        - Current password must be correct
        - New password must meet strength requirements

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Raises:
            NotFoundError: If user not found
            ValidationError: If passwords are invalid

        Example:
            >>> await user_service.change_password(
            ...     user_id,
            ...     "OldPassword123!",
            ...     "NewPassword456!"
            ... )
        """
        # Get user
        user = await self.get_user_by_id(user_id)

        # Business rule: Verify current password
        if not user.password.verify(current_password):
            raise ValidationError("Incorrect current password")

        # Business rule: Validate new password
        try:
            new_password_obj = Password.create(new_password)
        except ValueError as e:
            raise ValidationError(f"Invalid new password: {e}")

        # Update password via repository
        await self._repository.update_password(user_id, new_password_obj.hash_value)

    async def reset_password(self, user_id: UUID, new_password: str) -> None:
        """
        Reset user password (admin action).

        Args:
            user_id: User ID
            new_password: New password

        Raises:
            NotFoundError: If user not found
            ValidationError: If password is invalid

        Example:
            >>> await user_service.reset_password(user_id, "TemporaryPassword123!")
        """
        # Get user
        await self.get_user_by_id(user_id)

        # Business rule: Validate new password
        try:
            new_password_obj = Password.create(new_password)
        except ValueError as e:
            raise ValidationError(f"Invalid password: {e}")

        # Update password via repository
        await self._repository.update_password(user_id, new_password_obj.hash_value)

    # ========================================================================
    # USER STATUS
    # ========================================================================

    async def activate_user(self, user_id: UUID) -> User:
        """
        Activate user account.

        Args:
            user_id: User ID

        Returns:
            Updated User

        Example:
            >>> user = await user_service.activate_user(user_id)
            >>> assert user.is_active is True
        """
        # Get user first (ensures existence)
        await self.get_user_by_id(user_id)

        # Activate via repository
        db_user = await self._repository.activate(user_id)

        return self._db_to_domain(db_user)

    async def deactivate_user(self, user_id: UUID) -> User:
        """
        Deactivate user account.

        Args:
            user_id: User ID

        Returns:
            Updated User

        Example:
            >>> user = await user_service.deactivate_user(user_id)
            >>> assert user.is_active is False
        """
        # Get user first (ensures existence)
        await self.get_user_by_id(user_id)

        # Deactivate via repository
        db_user = await self._repository.deactivate(user_id)

        return self._db_to_domain(db_user)

    async def verify_user_email(self, user_id: UUID) -> User:
        """
        Verify user's email address.

        Args:
            user_id: User ID

        Returns:
            Updated User

        Example:
            >>> user = await user_service.verify_user_email(user_id)
            >>> assert user.is_verified is True
        """
        # Get user first (ensures existence)
        await self.get_user_by_id(user_id)

        # Verify via repository
        db_user = await self._repository.verify_email(user_id)

        return self._db_to_domain(db_user)

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Business Rules:
        - Credentials must be correct
        - User must be active
        - User must be verified (depending on settings)

        Args:
            email: User email
            password: User password

        Returns:
            Authenticated User

        Raises:
            ValidationError: If authentication fails

        Example:
            >>> user = await user_service.authenticate_user(
            ...     "user@example.com",
            ...     "Password123!"
            ... )
        """
        # Get user by email
        try:
            user = await self.get_user_by_email(email)
        except NotFoundError:
            # Security: Don't reveal whether user exists
            raise ValidationError("Invalid credentials")

        # Business rule: Verify password
        if not user.password.verify(password):
            raise ValidationError("Invalid credentials")

        # Business rule: Check if account is active
        if not user.is_active:
            raise ValidationError("Account is inactive. Please contact support.")

        # Business rule: Check if email is verified
        if not user.is_verified:
            # This could be configurable (allow unverified login during development)
            raise ValidationError("Please verify your email address first")

        return user

    # ========================================================================
    # BUSINESS RULE QUERIES
    # ========================================================================

    async def can_user_login(self, user_id: UUID) -> bool:
        """
        Check if user is allowed to login.

        Args:
            user_id: User ID

        Returns:
            True if user can login

        Example:
            >>> if await user_service.can_user_login(user_id):
            ...     print("User can login")
        """
        try:
            user = await self.get_user_by_id(user_id)
            return user.can_login()
        except NotFoundError:
            return False

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _db_to_domain(self, db_user) -> User:
        """
        Convert database model to domain entity.

        Args:
            db_user: SQLAlchemy User model

        Returns:
            User domain entity

        Example:
            >>> user = user_service._db_to_domain(db_user)
            >>> print(user.email)
            Email(value='user@example.com')
        """
        return User.from_db(
            id=db_user.id,
            email_str=db_user.email,
            password_hash=db_user.password_hash,
            full_name=db_user.full_name,
            role=UserRole(db_user.role),
            is_active=db_user.is_active,
            is_verified=getattr(db_user, "is_verified", False),
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )
