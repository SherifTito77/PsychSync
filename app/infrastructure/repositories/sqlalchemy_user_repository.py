# app/infrastructure/repositories/sqlalchemy_user_repository.py

"""
INFRASTRUCTURE ADAPTER - SQLALCHEMY USER REPOSITORY
SQLAlchemy implementation of the UserRepository interface

INFRASTRUCTURE PRINCIPLES:
- Implements repository interface using SQLAlchemy
- Handles database-specific concerns
- Maps domain entities to database models
- Manages transactions and connections
- Converts between domain and persistence models

Author: Security Team
Version: 2.0 Enterprise Security
"""

from datetime import datetime
import logging
from typing import Any

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository as IUserRepository
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.models.user_model import UserModel

# Initialize infrastructure logger
infra_logger = logging.getLogger("app.infrastructure.user_repository")


class SQLAlchemyUserRepository(IUserRepository):
    """
    SQLAlchemy implementation of UserRepository interface
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.mapper = UserMapper()

    async def save(self, user: User) -> User:
        """Save user to database"""
        try:
            # Convert domain entity to persistence model
            user_model = self.mapper.to_persistence_model(user)

            # Set audit fields
            now = datetime.utcnow()
            if not user_model.created_at:
                user_model.created_at = now
            user_model.updated_at = now

            # Save to database
            self.db.add(user_model)
            await self.db.flush()  # Get ID without committing

            # Convert back to domain entity
            saved_user = self.mapper.to_domain_entity(user_model)

            infra_logger.info(f"User saved to database: {saved_user.id}")
            return saved_user

        except Exception as e:
            infra_logger.error(f"Failed to save user: {e}")
            await self.db.rollback()
            raise

    async def find_by_id(self, user_id: str) -> User | None:
        """Find user by ID"""
        try:
            result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
            user_model = result.scalar_one_or_none()

            if user_model:
                return self.mapper.to_domain_entity(user_model)

            return None

        except Exception as e:
            infra_logger.error(f"Failed to find user by ID {user_id}: {e}")
            raise

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email"""
        try:
            result = await self.db.execute(
                select(UserModel).where(func.lower(UserModel.email) == func.lower(email))
            )
            user_model = result.scalar_one_or_none()

            if user_model:
                return self.mapper.to_domain_entity(user_model)

            return None

        except Exception as e:
            infra_logger.error(f"Failed to find user by email {email}: {e}")
            raise

    async def find_all(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[User]:
        """Find all users with pagination and filtering"""
        try:
            query = select(UserModel)

            # Apply filters
            if filters:
                if "role" in filters:
                    query = query.where(UserModel.role == filters["role"])
                if "status" in filters:
                    query = query.where(UserModel.status == filters["status"])
                if "organization_id" in filters:
                    query = query.where(UserModel.organization_id == filters["organization_id"])
                if "is_active" in filters:
                    query = query.where(UserModel.is_active == filters["is_active"])

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            user_models = result.scalars().all()

            # Convert to domain entities
            users = []
            for user_model in user_models:
                users.append(self.mapper.to_domain_entity(user_model))

            return users

        except Exception as e:
            infra_logger.error(f"Failed to find all users: {e}")
            raise

    async def update(self, user: User) -> User:
        """Update existing user"""
        try:
            # Find existing user model
            result = await self.db.execute(select(UserModel).where(UserModel.id == user.id))
            user_model = result.scalar_one_or_none()

            if not user_model:
                raise ValueError(f"User not found: {user.id}")

            # Update fields
            if user.full_name:
                user_model.full_name = user.full_name
            if user.phone:
                user_model.phone = user.phone
            if user.role:
                user_model.role = user.role.value
            if user.status:
                user_model.status = user.status.value

            # Update security metadata
            if user.security_metadata:
                user_model.last_login_at = user.security_metadata.last_login_at
                user_model.last_login_ip = user.security_metadata.last_login_ip
                user_model.failed_login_attempts = user.security_metadata.failed_login_attempts
                user_model.mfa_enabled = user.security_metadata.mfa_enabled
                user_model.device_trusted = user.security_metadata.device_trusted

            # Update preferences
            if user.preferences:
                user_model.timezone = user.preferences.timezone
                user_model.language = user.preferences.language
                user_model.notifications_enabled = user.preferences.notifications_enabled

            # Update audit fields
            user_model.updated_at = datetime.utcnow()

            await self.db.flush()

            # Convert back to domain entity
            updated_user = self.mapper.to_domain_entity(user_model)

            infra_logger.info(f"User updated: {updated_user.id}")
            return updated_user

        except Exception as e:
            infra_logger.error(f"Failed to update user {user.id}: {e}")
            await self.db.rollback()
            raise

    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        try:
            result = await self.db.execute(delete(UserModel).where(UserModel.id == user_id))

            success = result.rowcount > 0
            if success:
                infra_logger.info(f"User deleted: {user_id}")
            else:
                infra_logger.warning(f"User not found for deletion: {user_id}")

            return success

        except Exception as e:
            infra_logger.error(f"Failed to delete user {user_id}: {e}")
            await self.db.rollback()
            raise

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count users with optional filters"""
        try:
            query = select(func.count(UserModel.id))

            # Apply filters
            if filters:
                if "role" in filters:
                    query = query.where(UserModel.role == filters["role"])
                if "status" in filters:
                    query = query.where(UserModel.status == filters["status"])
                if "organization_id" in filters:
                    query = query.where(UserModel.organization_id == filters["organization_id"])

            result = await self.db.execute(query)
            count = result.scalar()
            return count

        except Exception as e:
            infra_logger.error(f"Failed to count users: {e}")
            raise

    async def email_exists(self, email: str, exclude_user_id: str | None = None) -> bool:
        """Check if email already exists"""
        try:
            query = select(func.count(UserModel.id)).where(
                func.lower(UserModel.email) == func.lower(email)
            )

            if exclude_user_id:
                query = query.where(UserModel.id != exclude_user_id)

            result = await self.db.execute(query)
            return result.scalar() > 0

        except Exception as e:
            infra_logger.error(f"Failed to check email existence {email}: {e}")
            raise

    async def organization_exists(self, organization_id: str) -> bool:
        """Check if organization exists"""
        try:
            from app.infrastructure.models.organization_model import OrganizationModel

            result = await self.db.execute(
                select(func.count(OrganizationModel.id)).where(
                    OrganizationModel.id == organization_id
                )
            )
            return result.scalar() > 0

        except Exception as e:
            infra_logger.error(f"Failed to check organization existence {organization_id}: {e}")
            raise

    async def find_by_organization(
        self, organization_id: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """Find users by organization"""
        try:
            query = (
                select(UserModel)
                .where(UserModel.organization_id == organization_id)
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            user_models = result.scalars().all()

            users = []
            for user_model in user_models:
                users.append(self.mapper.to_domain_entity(user_model))

            return users

        except Exception as e:
            infra_logger.error(f"Failed to find users by organization {organization_id}: {e}")
            raise

    async def update_last_login(self, user_id: str, ip_address: str, user_agent: str):
        """Update user's last login information"""
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    last_login_at=datetime.utcnow(),
                    last_login_ip=ip_address,
                    last_login_user_agent=user_agent,
                    failed_login_attempts=0,
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.execute(stmt)
            infra_logger.info(f"Last login updated for user {user_id}")

        except Exception as e:
            infra_logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise

    async def increment_failed_login(self, user_id: str) -> int:
        """Increment failed login attempts"""
        try:
            # Get current attempts
            result = await self.db.execute(
                select(UserModel.failed_login_attempts).where(UserModel.id == user_id)
            )
            current_attempts = result.scalar() or 0

            # Increment and update
            new_attempts = current_attempts + 1
            suspension_threshold = 5

            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    failed_login_attempts=new_attempts,
                    updated_at=datetime.utcnow(),
                    status="suspended" if new_attempts >= suspension_threshold else None,
                )
            )

            await self.db.execute(stmt)

            infra_logger.warning(
                f"Failed login attempts incremented for user {user_id}: {new_attempts}"
            )
            return new_attempts

        except Exception as e:
            infra_logger.error(f"Failed to increment failed login for user {user_id}: {e}")
            raise

    async def find_active_users_by_role(
        self, role: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """Find active users by role"""
        try:
            query = (
                select(UserModel)
                .where(and_(UserModel.role == role, UserModel.status == "active"))
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            user_models = result.scalars().all()

            users = []
            for user_model in user_models:
                users.append(self.mapper.to_domain_entity(user_model))

            return users

        except Exception as e:
            infra_logger.error(f"Failed to find active users by role {role}: {e}")
            raise

    async def search_users(self, search_term: str, limit: int = 20) -> list[User]:
        """Search users by email or full name"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            query = (
                select(UserModel)
                .where(
                    or_(
                        func.lower(UserModel.email).like(search_pattern),
                        func.lower(UserModel.full_name).like(search_pattern),
                    )
                )
                .limit(limit)
            )

            result = await self.db.execute(query)
            user_models = result.scalars().all()

            users = []
            for user_model in user_models:
                users.append(self.mapper.to_domain_entity(user_model))

            return users

        except Exception as e:
            infra_logger.error(f"Failed to search users: {e}")
            raise


# Factory function for creating repository
def create_sqlalchemy_user_repository(db_session: AsyncSession) -> SQLAlchemyUserRepository:
    """Factory function to create SQLAlchemyUserRepository"""
    return SQLAlchemyUserRepository(db_session)
