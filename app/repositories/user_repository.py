# app/repositories/user_repository.py

"""
ENTERPRISE-GRADE USER REPOSITORY
User-specific data access operations with security and business rules

USER REPOSITORY FEATURES:
- Secure user data access
- Email uniqueness validation
- Role-based filtering
- Authentication-related queries
- User management operations
- Privacy protection

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.repositories.base_repository import BaseRepository
from app.db.models.user import User
from app.db.models.organization import Organization
from app.schemas.user import UserCreate, UserUpdate

# Initialize user repository logger
user_repo_logger = logging.getLogger("app.repositories.user")

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    User-specific repository with comprehensive user management operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize user repository

        Args:
            db: Database session
        """
        super().__init__(db, User)

    async def get_by_email(
        self,
        email: str,
        include_deleted: bool = False
    ) -> Optional[User]:
        """
        Get user by email address

        Args:
            email: Email address
            include_deleted: Whether to include soft-deleted records

        Returns:
            User instance or None
        """
        try:
            query = select(User).where(
                func.lower(User.email) == func.lower(email.strip())
            )

            # Apply soft-delete filter
            if not include_deleted:
                query = query.where(User.deleted_at.is_(None))

            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                user_repo_logger.debug(f"User found by email: {email}")
            else:
                user_repo_logger.debug(f"User not found by email: {email}")

            return user

        except Exception as e:
            user_repo_logger.error(f"Error getting user by email {email}: {e}")
            raise

    async def email_exists(
        self,
        email: str,
        exclude_user_id: Optional[Any] = None
    ) -> bool:
        """
        Check if email address already exists

        Args:
            email: Email address to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        try:
            query = select(func.count(User.id)).where(
                func.lower(User.email) == func.lower(email.strip())
            ).where(User.deleted_at.is_(None))

            # Exclude specific user ID if provided
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)

            result = await self.db.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            user_repo_logger.error(f"Error checking email existence {email}: {e}")
            raise

    async def get_active_users_by_organization(
        self,
        organization_id: Any,
        include_roles: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[User], int]:
        """
        Get active users by organization with pagination

        Args:
            organization_id: Organization ID
            include_roles: List of roles to include (None for all)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (users list, total count)
        """
        try:
            # Build base query
            base_query = select(User).where(
                and_(
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                    User.is_active == True
                )
            )

            # Apply role filter if specified
            if include_roles:
                base_query = base_query.where(User.role.in_(include_roles))

            # Get total count
            count_query = select(func.count(User.id)).where(
                and_(
                    User.organization_id == organization_id,
                    User.deleted_at.is_(None),
                    User.is_active == True
                )
            )
            if include_roles:
                count_query = count_query.where(User.role.in_(include_roles))

            # Execute queries
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

            # Apply pagination and ordering
            query = base_query.order_by(User.created_at.desc()).offset(skip).limit(limit)
            result = await self.db.execute(query)
            users = result.scalars().all()

            user_repo_logger.debug(
                f"Retrieved {len(users)} users for organization {organization_id}",
                extra={
                    "organization_id": organization_id,
                    "total_count": total_count,
                    "roles": include_roles
                }
            )

            return users, total_count

        except Exception as e:
            user_repo_logger.error(f"Error getting users by organization {organization_id}: {e}")
            raise

    async def get_users_by_role(
        self,
        role: str,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[User], int]:
        """
        Get users by role

        Args:
            role: User role
            include_inactive: Whether to include inactive users
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (users list, total count)
        """
        try:
            # Build base query
            base_query = select(User).where(User.role == role).where(User.deleted_at.is_(None))

            # Filter by active status if specified
            if not include_inactive:
                base_query = base_query.where(User.is_active == True)

            # Get total count
            count_query = select(func.count(User.id)).where(User.role == role).where(User.deleted_at.is_(None))
            if not include_inactive:
                count_query = count_query.where(User.is_active == True)

            # Execute queries
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

            # Apply pagination and ordering
            query = base_query.order_by(User.created_at.desc()).offset(skip).limit(limit)
            result = await self.db.execute(query)
            users = result.scalars().all()

            user_repo_logger.debug(
                f"Retrieved {len(users)} users with role {role}",
                extra={
                    "role": role,
                    "total_count": total_count,
                    "include_inactive": include_inactive
                }
            )

            return users, total_count

        except Exception as e:
            user_repo_logger.error(f"Error getting users by role {role}: {e}")
            raise

    async def search_users(
        self,
        search_term: str,
        organization_id: Optional[Any] = None,
        limit: int = 20
    ) -> List[User]:
        """
        Search users by email or full name

        Args:
            search_term: Search term
            organization_id: Optional organization filter
            limit: Maximum number of results

        Returns:
            List of matching users
        """
        try:
            # Build search query
            search_pattern = f"%{search_term.lower()}%"
            query = select(User).where(
                and_(
                    User.deleted_at.is_(None),
                    User.is_active == True,
                    or_(
                        func.lower(User.email).like(search_pattern),
                        func.lower(User.full_name).like(search_pattern)
                    )
                )
            )

            # Apply organization filter if specified
            if organization_id:
                query = query.where(User.organization_id == organization_id)

            # Apply limit and ordering
            query = query.order_by(User.full_name).limit(limit)

            result = await self.db.execute(query)
            users = result.scalars().all()

            user_repo_logger.debug(
                f"Search found {len(users)} users for term '{search_term}'",
                extra={
                    "search_term": search_term,
                    "organization_id": organization_id,
                    "results_count": len(users)
                }
            )

            return users

        except Exception as e:
            user_repo_logger.error(f"Error searching users with term '{search_term}': {e}")
            raise

    async def get_unverified_users(
        self,
        days_old: int = 30,
        limit: int = 100
    ) -> List[User]:
        """
        Get users who haven't verified their email

        Args:
            days_old: Number of days since registration
            limit: Maximum number of results

        Returns:
            List of unverified users
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            query = select(User).where(
                and_(
                    User.deleted_at.is_(None),
                    User.is_active == False,
                    User.is_verified == False,
                    User.created_at <= cutoff_date
                )
            ).order_by(User.created_at.asc()).limit(limit)

            result = await self.db.execute(query)
            users = result.scalars().all()

            user_repo_logger.debug(
                f"Found {len(users)} unverified users older than {days_old} days",
                extra={
                    "days_old": days_old,
                    "results_count": len(users)
                }
            )

            return users

        except Exception as e:
            user_repo_logger.error(f"Error getting unverified users: {e}")
            raise

    async def get_user_statistics(
        self,
        organization_id: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Get user statistics

        Args:
            organization_id: Optional organization filter

        Returns:
            Dictionary with user statistics
        """
        try:
            base_filters = [User.deleted_at.is_(None)]
            if organization_id:
                base_filters.append(User.organization_id == organization_id)

            # Total users
            total_query = select(func.count(User.id)).where(and_(*base_filters))
            total_result = await self.db.execute(total_query)
            total_users = total_result.scalar()

            # Active users
            active_filters = base_filters + [User.is_active == True]
            active_query = select(func.count(User.id)).where(and_(*active_filters))
            active_result = await self.db.execute(active_query)
            active_users = active_result.scalar()

            # Verified users
            verified_filters = base_filters + [User.is_verified == True]
            verified_query = select(func.count(User.id)).where(and_(*verified_filters))
            verified_result = await self.db.execute(verified_query)
            verified_users = verified_result.scalar()

            # Users by role
            role_query = select(User.role, func.count(User.id)).where(and_(*base_filters)).group_by(User.role)
            role_result = await self.db.execute(role_query)
            users_by_role = {row.role: row.count for row in role_result}

            # Recent registrations (last 30 days)
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_filters = base_filters + [User.created_at >= recent_date]
            recent_query = select(func.count(User.id)).where(and_(*recent_filters))
            recent_result = await self.db.execute(recent_query)
            recent_registrations = recent_result.scalar()

            statistics = {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "recent_registrations": recent_registrations,
                "users_by_role": users_by_role,
                "activation_rate": (active_users / total_users * 100) if total_users > 0 else 0,
                "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0
            }

            user_repo_logger.info(
                "User statistics retrieved",
                extra={
                    "organization_id": organization_id,
                    "statistics": statistics
                }
            )

            return statistics

        except Exception as e:
            user_repo_logger.error(f"Error getting user statistics: {e}")
            raise

    async def update_last_login(
        self,
        user_id: Any,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Update user's last login information

        Args:
            user_id: User ID
            client_ip: Client IP address
            user_agent: User agent string

        Returns:
            True if updated, False otherwise
        """
        try:
            # Get user
            user = await self.get_by_id(user_id)
            if not user:
                user_repo_logger.warning(f"Cannot update last login for user {user_id}: not found")
                return False

            # Update last login
            user.last_login_at = datetime.utcnow()
            if client_ip:
                user.last_login_ip = client_ip
            if user_agent:
                user.last_login_user_agent = user_agent

            # Increment login count
            user.login_count = (user.login_count or 0) + 1

            await self.db.flush()

            user_repo_logger.info(
                f"Updated last login for user {user_id}",
                extra={
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "login_count": user.login_count
                }
            )

            return True

        except Exception as e:
            user_repo_logger.error(f"Error updating last login for user {user_id}: {e}")
            await self.db.rollback()
            raise

    async def deactivate_user(
        self,
        user_id: Any,
        reason: Optional[str] = None,
        deactivated_by: Optional[Any] = None
    ) -> bool:
        """
        Deactivate user account

        Args:
            user_id: User ID
            reason: Reason for deactivation
            deactivated_by: Admin user ID performing deactivation

        Returns:
            True if deactivated, False otherwise
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                user_repo_logger.warning(f"Cannot deactivate user {user_id}: not found")
                return False

            # Update user
            user.is_active = False
            user.deactivated_at = datetime.utcnow()
            user.deactivated_by = deactivated_by
            if reason:
                user.deactivation_reason = reason

            await self.db.flush()

            user_repo_logger.info(
                f"Deactivated user {user_id}",
                extra={
                    "user_id": user_id,
                    "reason": reason,
                    "deactivated_by": deactivated_by
                }
            )

            return True

        except Exception as e:
            user_repo_logger.error(f"Error deactivating user {user_id}: {e}")
            await self.db.rollback()
            raise

    async def reactivate_user(
        self,
        user_id: Any,
        reactivated_by: Optional[Any] = None
    ) -> bool:
        """
        Reactivate user account

        Args:
            user_id: User ID
            reactivated_by: Admin user ID performing reactivation

        Returns:
            True if reactivated, False otherwise
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                user_repo_logger.warning(f"Cannot reactivate user {user_id}: not found")
                return False

            if user.is_active:
                user_repo_logger.debug(f"User {user_id} is already active")
                return True

            # Update user
            user.is_active = True
            user.reactivated_at = datetime.utcnow()
            user.reactivated_by = reactivated_by

            # Clear deactivation fields
            user.deactivated_at = None
            user.deactivated_by = None
            user.deactivation_reason = None

            await self.db.flush()

            user_repo_logger.info(
                f"Reactivated user {user_id}",
                extra={
                    "user_id": user_id,
                    "reactivated_by": reactivated_by
                }
            )

            return True

        except Exception as e:
            user_repo_logger.error(f"Error reactivating user {user_id}: {e}")
            await self.db.rollback()
            raise

    async def get_user_with_organization(
        self,
        user_id: Any
    ) -> Optional[User]:
        """
        Get user with their organization loaded

        Args:
            user_id: User ID

        Returns:
            User instance with organization loaded
        """
        try:
            query = select(User).options(
                selectinload(User.organization)
            ).where(
                and_(
                    User.id == user_id,
                    User.deleted_at.is_(None)
                )
            )

            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                user_repo_logger.debug(f"User with organization loaded: {user_id}")

            return user

        except Exception as e:
            user_repo_logger.error(f"Error getting user with organization {user_id}: {e}")
            raise