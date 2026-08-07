# app/infrastructure/repositories/base.py
"""
Base Repository Implementation

Provides generic CRUD operations for all repositories.
Follows the Repository Pattern to separate data access from business logic.
"""

from abc import ABC
from typing import Any, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import NotFoundError

# Generic types for repository
ModelType = TypeVar("ModelType", bound=Any)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Abstract base repository with generic CRUD operations.

    Type Parameters:
        ModelType: SQLAlchemy model type
        CreateSchemaType: Pydantic schema for creation
        UpdateSchemaType: Pydantic schema for updates

    Example:
        class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
            def __init__(self, db: AsyncSession):
                super().__init__(User, db)
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository with model and database session.

        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self._model = model
        self._db = db

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get entity by ID.

        Args:
            id: Entity UUID

        Returns:
            Model instance or None if not found

        Example:
            user = await user_repository.get(user_id)
        """
        result = await self._db.execute(select(self._model).where(self._model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, id: UUID) -> ModelType:
        """
        Get entity by ID or raise NotFoundError.

        Args:
            id: Entity UUID

        Returns:
            Model instance

        Raises:
            NotFoundError: If entity not found

        Example:
            user = await user_repository.get_or_404(user_id)
        """
        entity = await self.get(id)
        if not entity:
            raise NotFoundError(f"{self._model.__name__} with id {id} not found")
        return entity

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
    ) -> tuple[List[ModelType], int]:
        """
        List entities with pagination and filtering.

        Args:
            skip: Number of records to skip (pagination offset)
            limit: Maximum number of records to return
            filters: Dictionary of field: value pairs for filtering
            order_by: Field name to order by (prefix with - for descending)

        Returns:
            Tuple of (list of entities, total count)

        Example:
            users, total = await user_repository.list(
                skip=0,
                limit=10,
                filters={"is_active": True},
                order_by="-created_at"
            )
        """
        # Build query
        query = select(self._model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self._model, key):
                    query = query.where(getattr(self._model, key) == value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                field = order_by[1:]
                if hasattr(self._model, field):
                    query = query.order_by(getattr(self._model, field).desc())
            else:
                if hasattr(self._model, order_by):
                    query = query.order_by(getattr(self._model, order_by))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self._db.execute(query)
        entities = result.scalars().all()

        return list(entities), total

    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: Entity UUID

        Returns:
            True if exists, False otherwise

        Example:
            if await user_repository.exists(user_id):
                print("User exists")
        """
        result = await self._db.execute(
            select(func.count()).select_from(self._model).where(self._model.id == id)
        )
        return result.scalar() > 0

    # ========================================================================
    # WRITE OPERATIONS
    # ========================================================================

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """
        Create new entity from schema.

        Args:
            schema: Pydantic schema with creation data

        Returns:
            Created model instance

        Example:
            user = await user_repository.create(UserCreate(email="..."))
        """
        # Convert schema to dict
        entity_data = schema.model_dump()

        # Create instance
        entity = self._model(**entity_data)

        # Add to session
        self._db.add(entity)

        # Flush to get ID but don't commit yet
        await self._db.flush()

        return entity

    async def update(
        self, id: UUID, schema: UpdateSchemaType, partial: bool = True
    ) -> ModelType:
        """
        Update entity by ID.

        Args:
            id: Entity UUID
            schema: Pydantic schema with update data
            partial: If True, only update provided fields (default)

        Returns:
            Updated model instance

        Raises:
            NotFoundError: If entity not found

        Example:
            user = await user_repository.update(
                user_id,
                UserUpdate(full_name="New Name")
            )
        """
        # Get entity
        entity = await self.get_or_404(id)

        # Get update data
        update_data = schema.model_dump(exclude_unset=partial)

        # Update fields
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        # Flush changes
        await self._db.flush()

        return entity

    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity UUID

        Returns:
            True if deleted, False if not found

        Example:
            deleted = await user_repository.delete(user_id)
        """
        # Check existence
        if not await self.exists(id):
            return False

        # Delete
        await self._db.execute(delete(self._model).where(self._model.id == id))

        return True

    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================

    async def bulk_create(self, schemas: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple entities in a single operation.

        Args:
            schemas: List of Pydantic schemas

        Returns:
            List of created model instances

        Example:
            users = await user_repository.bulk_create([
                UserCreate(email="user1@example.com"),
                UserCreate(email="user2@example.com")
            ])
        """
        entities = [self._model(**schema.model_dump()) for schema in schemas]

        self._db.add_all(entities)
        await self._db.flush()

        return entities

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Dictionary of field: value pairs for filtering

        Returns:
            Count of matching entities

        Example:
            count = await user_repository.count({"is_active": True})
        """
        query = select(func.count()).select_from(self._model)

        if filters:
            for key, value in filters.items():
                if hasattr(self._model, key):
                    query = query.where(getattr(self._model, key) == value)

        result = await self._db.execute(query)
        return result.scalar() or 0


# ============================================================================
# CUSTOM REPOSITORY EXCEPTIONS
# ============================================================================


class RepositoryError(Exception):
    """Base exception for repository errors"""


class DuplicateError(RepositoryError):
    """Raised when trying to create duplicate entity"""


class InvalidOperationError(RepositoryError):
    """Raised when invalid operation is attempted"""
