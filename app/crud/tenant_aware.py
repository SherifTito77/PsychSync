"""
Tenant-Aware CRUD Base Class

Provides base CRUD operations with automatic tenant scoping for all queries.
Ensures data isolation by automatically filtering by tenant_id in all queries.

Created: 2025-01-12
Author: Architecture Team
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeMeta
import logging

from app.core.tenant_database import get_tenant_router, TenantTier

logger = logging.getLogger(__name__)


ModelType = TypeVar("ModelType", bound=Any)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class TenantAwareCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class with automatic tenant scoping.

    Features:
    - All queries automatically filter by tenant_id
    - Tenant ID automatically injected on create
    - Prevents cross-tenant data access
    - Supports PostgreSQL Row-Level Security (RLS)

    Usage:
        class UserCRUD(TenantAwareCRUDBase[User, UserCreate, UserUpdate]):
            pass

        user_crud = UserCRUD(User)

        # All operations automatically scoped to tenant
        user = await user_crud.get(db, user_id, tenant_id)
        users = await user_crud.get_multi(db, tenant_id, skip=0, limit=10)
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD base with model.

        Args:
            model: SQLAlchemy model class (must have tenant_id column)
        """
        self.model = model
        logger.debug(f"Initialized TenantAwareCRUD for {model.__name__}")

    async def get(
        self,
        db: AsyncSession,
        id: UUID,
        tenant_id: UUID,
    ) -> Optional[ModelType]:
        """
        Get single record by ID (tenant-scoped).

        Args:
            db: Database session
            id: Record UUID
            tenant_id: Tenant UUID for scoping

        Returns:
            Model instance if found, None otherwise

        Security:
            Query automatically filters by tenant_id to prevent cross-tenant access
        """
        try:
            statement = select(self.model).where(
                self.model.id == id,
                self.model.tenant_id == tenant_id,
            )

            result = await db.execute(statement)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} {id}: {e}")
            raise

    async def get_multi(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination (tenant-scoped).

        Args:
            db: Database session
            tenant_id: Tenant UUID for scoping
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Additional filter criteria

        Returns:
            List of model instances
        """
        try:
            statement = select(self.model).where(
                self.model.tenant_id == tenant_id,
            )

            # Apply additional filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        statement = statement.where(getattr(self.model, key) == value)

            # Apply pagination
            statement = statement.offset(skip).limit(limit)

            result = await db.execute(statement)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        tenant_id: UUID,
        **kwargs,
    ) -> ModelType:
        """
        Create new record (tenant-scoped).

        Args:
            db: Database session
            obj_in: Pydantic schema with creation data
            tenant_id: Tenant UUID to inject
            **kwargs: Additional fields to set

        Returns:
            Created model instance

        Security:
            tenant_id is automatically set, cannot be overridden
        """
        try:
            # Convert schema to dict
            obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in

            # Inject tenant_id
            obj_in_data["tenant_id"] = tenant_id

            # Add additional fields
            obj_in_data.update(kwargs)

            # Create instance
            db_obj = self.model(**obj_in_data)

            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)

            logger.info(f"Created {self.model.__name__} {db_obj.id} for tenant {tenant_id}")

            return db_obj

        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        tenant_id: UUID,
    ) -> ModelType:
        """
        Update existing record (tenant-scoped).

        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Pydantic schema with update data
            tenant_id: Tenant UUID for verification

        Returns:
            Updated model instance

        Security:
            Verifies record belongs to tenant before updating
        """
        try:
            # Verify tenant ownership
            if db_obj.tenant_id != tenant_id:
                raise ValueError(
                    f"Security violation: Attempting to update {self.model.__name__} "
                    f"from different tenant (expected {tenant_id}, got {db_obj.tenant_id})"
                )

            # Convert schema to dict
            obj_in_data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, BaseModel) else obj_in

            # Update fields
            for field, value in obj_in_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await db.flush()
            await db.refresh(db_obj)

            logger.info(f"Updated {self.model.__name__} {db_obj.id} for tenant {tenant_id}")

            return db_obj

        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} {db_obj.id}: {e}")
            await db.rollback()
            raise

    async def delete(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: UUID,
    ) -> Optional[ModelType]:
        """
        Delete record by ID (tenant-scoped).

        Args:
            db: Database session
            id: Record UUID
            tenant_id: Tenant UUID for verification

        Returns:
            Deleted model instance if found, None otherwise

        Security:
            Verifies record belongs to tenant before deleting
        """
        try:
            # Get record (automatically scoped to tenant)
            db_obj = await self.get(db, id, tenant_id)

            if not db_obj:
                return None

            await db.delete(db_obj)
            await db.flush()

            logger.info(f"Deleted {self.model.__name__} {id} for tenant {tenant_id}")

            return db_obj

        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            await db.rollback()
            raise

    async def count(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count records matching criteria (tenant-scoped).

        Args:
            db: Database session
            tenant_id: Tenant UUID for scoping
            filters: Additional filter criteria

        Returns:
            Count of matching records
        """
        try:
            statement = select(func.count(self.model.id)).where(
                self.model.tenant_id == tenant_id,
            )

            # Apply additional filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        statement = statement.where(getattr(self.model, key) == value)

            result = await db.execute(statement)
            return result.scalar_one()

        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise

    async def exists(
        self,
        db: AsyncSession,
        id: UUID,
        tenant_id: UUID,
    ) -> bool:
        """
        Check if record exists (tenant-scoped).

        Args:
            db: Database session
            id: Record UUID
            tenant_id: Tenant UUID for scoping

        Returns:
            True if record exists, False otherwise
        """
        try:
            statement = select(func.count(self.model.id)).where(
                self.model.id == id,
                self.model.tenant_id == tenant_id,
            )

            result = await db.execute(statement)
            count = result.scalar_one()

            return count > 0

        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} {id}: {e}")
            raise

    async def bulk_create(
        self,
        db: AsyncSession,
        *,
        objs_in: List[CreateSchemaType],
        tenant_id: UUID,
    ) -> List[ModelType]:
        """
        Bulk create records (tenant-scoped).

        Args:
            db: Database session
            objs_in: List of Pydantic schemas
            tenant_id: Tenant UUID to inject

        Returns:
            List of created model instances
        """
        try:
            db_objs = []

            for obj_in in objs_in:
                obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
                obj_in_data["tenant_id"] = tenant_id

                db_obj = self.model(**obj_in_data)
                db_objs.append(db_obj)

            db.add_all(db_objs)
            await db.flush()

            # Refresh all objects
            for db_obj in db_objs:
                await db.refresh(db_obj)

            logger.info(f"Bulk created {len(db_objs)} {self.model.__name__} for tenant {tenant_id}")

            return db_objs

        except Exception as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def get_by_tenant(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Get all records for a tenant (convenience method).

        Args:
            db: Database session
            tenant_id: Tenant UUID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of model instances for tenant
        """
        return await self.get_multi(db, tenant_id, skip=skip, limit=limit)


class TenantAwareCRUDWithSoftDelete(TenantAwareCRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class with soft delete support.

    Instead of hard-deleting records, marks them as deleted.
    Useful for audit trails and data recovery.

    Usage:
        class UserCRUD(TenantAwareCRUDWithSoftDelete[User, UserCreate, UserUpdate]):
            pass
    """

    async def get(
        self,
        db: AsyncSession,
        id: UUID,
        tenant_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        """Get record by ID, optionally including deleted records."""
        try:
            statement = select(self.model).where(
                self.model.id == id,
                self.model.tenant_id == tenant_id,
            )

            if not include_deleted:
                statement = statement.where(self.model.is_deleted == False)

            result = await db.execute(statement)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} {id}: {e}")
            raise

    async def get_multi(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """Get multiple records, optionally including deleted records."""
        try:
            statement = select(self.model).where(
                self.model.tenant_id == tenant_id,
            )

            if not include_deleted:
                statement = statement.where(self.model.is_deleted == False)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        statement = statement.where(getattr(self.model, key) == value)

            statement = statement.offset(skip).limit(limit)

            result = await db.execute(statement)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise

    async def delete(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: UUID,
        hard_delete: bool = False,
    ) -> Optional[ModelType]:
        """
        Delete record (soft delete by default).

        Args:
            db: Database session
            id: Record UUID
            tenant_id: Tenant UUID for verification
            hard_delete: If True, permanently delete record

        Returns:
            Deleted/updated model instance
        """
        try:
            db_obj = await self.get(db, id, tenant_id, include_deleted=True)

            if not db_obj:
                return None

            if hard_delete:
                # Permanent delete
                await db.delete(db_obj)
                logger.info(f"Hard deleted {self.model.__name__} {id} for tenant {tenant_id}")
            else:
                # Soft delete
                db_obj.is_deleted = True
                logger.info(f"Soft deleted {self.model.__name__} {id} for tenant {tenant_id}")

            await db.flush()

            return db_obj

        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            await db.rollback()
            raise
