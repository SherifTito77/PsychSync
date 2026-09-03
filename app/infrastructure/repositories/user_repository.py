# app/infrastructure/repositories/user_repository.py
"""
User Repository Implementation

Handles all data access operations for User entities.
Follows the Repository Pattern to separate data access from business logic.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User as UserModel
from app.infrastructure.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    """
    Repository for User entity.

    Provides data access methods for User operations.
    All database queries for User should go through this repository.

    Example:
        repo = UserRepository(db_session)
        user = await repo.get_by_email("user@example.com")
        users = await repo.list(skip=0, limit=10, filters={"is_active": True})
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize user repository.

        Args:
            db: Async database session
        """
        super().__init__(UserModel, db)

    # ========================================================================
    # FIND BY UNIQUE FIELDS
    # ========================================================================

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get user by email address.

        Args:
            email: User email (case-insensitive)

        Returns:
            User model or None if not found

        Example:
            >>> user = await user_repo.get_by_email("user@example.com")
            >>> if user:
            ...     print(f"Found user: {user.full_name}")
        """
        # Email is case-insensitive in database (citext type)
        result = await self._db.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        """
        Get user by username.

        Args:
            username: Username (maps to email in our system)

        Returns:
            User model or None if not found
        """
        return await self.get_by_email(username)

    # ========================================================================
    # EXISTS CHECKS
    # ========================================================================

    async def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check
            exclude_id: User ID to exclude from check (for updates)

        Returns:
            True if email exists

        Example:
            >>> if await user_repo.email_exists("new@example.com"):
            ...     raise ValidationError("Email already exists")
        """
        query = select(UserModel).where(UserModel.email == email.lower())

        if exclude_id:
            query = query.where(UserModel.id != exclude_id)

        result = await self._db.execute(query)
        return result.scalar_one_or_none() is not None

    # ========================================================================
    # FILTERED LISTS
    # ========================================================================

    async def list_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> tuple[list[UserModel], int]:
        """
        List users by organization.

        Args:
            organization_id: Organization ID
            skip: Pagination offset
            limit: Pagination limit
            is_active: Filter by active status

        Returns:
            Tuple of (users, total count)

        Example:
            >>> users, total = await user_repo.list_by_organization(
            ...     org_id,
            ...     skip=0,
            ...     limit=20,
            ...     is_active=True
            ... )
        """
        query = select(UserModel).where(UserModel.organization_id == organization_id)

        if is_active is not None:
            query = query.where(UserModel.is_active == is_active)

        # Get total count
        count_query = select(UserModel.id).where(
            UserModel.organization_id == organization_id
        )
        if is_active is not None:
            count_query = count_query.where(UserModel.is_active == is_active)

        result = await self._db.execute(
            select(func.count()).select_from(count_query.subquery())
        )
        total = result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        query = query.order_by(UserModel.created_at.desc())

        result = await self._db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def list_by_role(
        self, role: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserModel], int]:
        """
        List users by role.

        Args:
            role: User role filter
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (users, total count)
        """
        query = select(UserModel).where(UserModel.role == role)

        # Get total
        count_result = await self._db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        query = query.order_by(UserModel.created_at.desc())

        result = await self._db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def search(
        self, search_term: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserModel], int]:
        """
        Search users by email or full name.

        Args:
            search_term: Search query
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (users, total count)

        Example:
            >>> users, total = await user_repo.search("john")
            >>> # Returns users with "john" in email or name
        """
        search_pattern = f"%{search_term.lower()}%"

        query = select(UserModel).where(
            or_(
                UserModel.email.ilike(search_pattern),
                UserModel.full_name.ilike(search_pattern),
            )
        )

        # Get total
        count_result = await self._db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        query = query.order_by(UserModel.created_at.desc())

        result = await self._db.execute(query)
        users = result.scalars().all()

        return list(users), total

    # ========================================================================
    # STATUS OPERATIONS
    # ========================================================================

    async def activate(self, user_id: UUID) -> Optional[UserModel]:
        """
        Activate user account.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found

        Example:
            >>> user = await user_repo.activate(user_id)
            >>> assert user.is_active is True
        """
        user = await self.get(user_id)
        if user:
            user.is_active = True
            await self._db.flush()
        return user

    async def deactivate(self, user_id: UUID) -> Optional[UserModel]:
        """
        Deactivate user account.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        user = await self.get(user_id)
        if user:
            user.is_active = False
            await self._db.flush()
        return user

    async def verify_email(self, user_id: UUID) -> Optional[UserModel]:
        """
        Mark user email as verified.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        user = await self.get(user_id)
        if user:
            user.is_verified = True
            await self._db.flush()
        return user

    # ========================================================================
    # PASSWORD OPERATIONS
    # ========================================================================

    async def update_password(
        self, user_id: UUID, password_hash: str
    ) -> Optional[UserModel]:
        """
        Update user password.

        Args:
            user_id: User ID
            password_hash: New password hash

        Returns:
            Updated user or None if not found

        Example:
            >>> from app.services.security import get_password_hash
            >>> password_hash = get_password_hash("NewPassword123!")
            >>> user = await user_repo.update_password(user_id, password_hash)
        """
        user = await self.get(user_id)
        if user:
            user.password_hash = password_hash
            await self._db.flush()
        return user

    async def update_last_login(self, user_id: UUID) -> Optional[UserModel]:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        from datetime import datetime

        user = await self.get(user_id)
        if user and hasattr(user, "last_login"):
            user.last_login = datetime.utcnow()
            await self._db.flush()
        return user

    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================

    async def set_role(self, user_id: UUID, role: str) -> Optional[UserModel]:
        """
        Update user role.

        Args:
            user_id: User ID
            role: New role

        Returns:
            Updated user or None if not found
        """
        user = await self.get(user_id)
        if user:
            user.role = role
            await self._db.flush()
        return user

    async def make_superuser(self, user_id: UUID) -> Optional[UserModel]:
        """
        Grant superuser privileges.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        user = await self.get(user_id)
        if user:
            user.is_superuser = True
            await self._db.flush()
        return user

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    async def bulk_activate(self, user_ids: list[UUID]) -> int:
        """
        Activate multiple users at once.

        Args:
            user_ids: List of user IDs to activate

        Returns:
            Number of users activated

        Example:
            >>> count = await user_repo.bulk_activate([id1, id2, id3])
            >>> print(f"Activated {count} users")
        """
        result = await self._db.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        users = result.scalars().all()

        for user in users:
            user.is_active = True

        await self._db.flush()
        return len(users)

    async def bulk_deactivate(self, user_ids: list[UUID]) -> int:
        """
        Deactivate multiple users at once.

        Args:
            user_ids: List of user IDs to deactivate

        Returns:
            Number of users deactivated
        """
        result = await self._db.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        users = result.scalars().all()

        for user in users:
            user.is_active = False

        await self._db.flush()
        return len(users)

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def count_by_status(self, is_active: bool) -> int:
        """
        Count users by active status.

        Args:
            is_active: Active status to count

        Returns:
            Count of users with given status

        Example:
            >>> active_count = await user_repo.count_by_status(True)
            >>> inactive_count = await user_repo.count_by_status(False)
        """
        result = await self._db.execute(
            select(func.count()).select_from(
                select(UserModel).where(UserModel.is_active == is_active).subquery()
            )
        )
        return result.scalar() or 0

    async def count_by_role(self) -> dict[str, int]:
        """
        Count users grouped by role.

        Returns:
            Dictionary mapping role to count

        Example:
            >>> counts = await user_repo.count_by_role()
            >>> print(counts)
            {'ADMIN': 5, 'USER': 123, 'TEAM_LEAD': 12}
        """
        result = await self._db.execute(
            select(UserModel.role, func.count(UserModel.id)).group_by(UserModel.role)
        )

        return {row[0]: row[1] for row in result.all()}
