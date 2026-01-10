# app/services/base_service.py
"""
Base Service Class for Common CRUD Patterns
Provides abstract base class with common operations and standardized patterns
"""

from abc import ABC, abstractmethod
import builtins
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache_strategy import CacheStrategy, cache_invalidation_manager
from app.core.database_transactions import transaction_manager
from app.core.error_handling import ValidationException, handle_database_errors
from app.core.structured_logging import EventType, get_logger

T = TypeVar("T")  # Model type
C = TypeVar("C", bound=BaseModel)  # Create schema type
U = TypeVar("U", bound=BaseModel)  # Update schema type

class BaseService(Generic[T, C, U], ABC):
    """
    Abstract base service providing common CRUD operations
    with standardized error handling, caching, and logging
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__module__)

    @property
    @abstractmethod
    def model(self) -> type[T]:
        """Return the SQLAlchemy model class"""

    @property
    @abstractmethod
    def cache_strategy(self) -> CacheStrategy:
        """Return the caching strategy for this service"""

    @abstractmethod
    def get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operations"""

    @abstractmethod
    def validate_create_data(self, data: C) -> None:
        """Validate data before creation"""

    @abstractmethod
    def validate_update_data(self, data: U, existing: T) -> None:
        """Validate data before update"""

    # CRUD Operations with Standard Patterns

    async def get_by_id(
        self,
        db: AsyncSession,
        id: str | UUID,
        include_relations: bool = False,
        relations: list[str] = None
    ) -> T | None:
        """
        Get entity by ID with optional eager loading
        """
        try:
            query = select(self.model).where(self.model.id == id)

            # Add eager loading if requested
            if include_relations and relations:
                for relation in relations:
                    query = query.options(selectinload(getattr(self.model, relation)))

            result = await db.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                self.logger.debug(
                    EventType.DATABASE_OPERATION,
                    f"Retrieved {self.model.__name__} by ID",
                    operation_name="get_by_id",
                    entity_id=str(id),
                    entity_type=self.model.__name__
                )

            return entity

        except Exception as e:
            self.logger.log_error(e, operation="get_by_id", entity_id=str(id))
            raise

    @handle_database_errors(f"{__name__}_list")
    async def list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        filters: dict[str, Any] = None,
        include_relations: bool = False,
        relations: list[str] = None
    ) -> list[T]:
        """
        List entities with pagination, sorting, and filtering
        """
        try:
            query = select(self.model)

            # Apply filters
            if filters:
                filter_conditions = []
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            filter_conditions.append(getattr(self.model, field).in_(value))
                        elif isinstance(value, str) and "%" in value:
                            filter_conditions.append(getattr(self.model, field).ilike(f"%{value}%"))
                        else:
                            filter_conditions.append(getattr(self.model, field) == value)

                if filter_conditions:
                    query = query.where(and_(*filter_conditions))

            # Add sorting
            if hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                query = query.order_by(desc(sort_column) if sort_desc else asc(sort_column))

            # Add eager loading
            if include_relations and relations:
                for relation in relations:
                    query = query.options(selectinload(getattr(self.model, relation)))

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            entities = result.scalars().all()

            self.logger.debug(
                EventType.DATABASE_OPERATION,
                f"Listed {len(entities)} {self.model.__name__} entities",
                operation_name="list",
                entity_count=len(entities),
                filters=filters,
                sort_by=sort_by,
                skip=skip,
                limit=limit
            )

            return entities

        except Exception as e:
            self.logger.log_error(e, operation="list", filters=filters)
            raise

    @handle_database_errors(f"{__name__}_count")
    async def count(self, db: AsyncSession, filters: dict[str, Any] = None) -> int:
        """
        Count entities with optional filtering
        """
        try:
            query = select(func.count(self.model.id))

            # Apply filters
            if filters:
                filter_conditions = []
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            filter_conditions.append(getattr(self.model, field).in_(value))
                        elif isinstance(value, str) and "%" in value:
                            filter_conditions.append(getattr(self.model, field).ilike(f"%{value}%"))
                        else:
                            filter_conditions.append(getattr(self.model, field) == value)

                if filter_conditions:
                    query = query.where(and_(*filter_conditions))

            result = await db.execute(query)
            count = result.scalar()

            self.logger.debug(
                EventType.DATABASE_OPERATION,
                f"Counted {count} {self.model.__name__} entities",
                operation_name="count",
                entity_count=count,
                filters=filters
            )

            return count

        except Exception as e:
            self.logger.log_error(e, operation="count", filters=filters)
            raise

    @handle_database_errors(f"{__name__}_create")
    @transaction_manager.transaction
    async def create(self, db: AsyncSession, data: C, **kwargs) -> T:
        """
        Create new entity with validation and caching
        """
        try:
            # Validate input data
            self.validate_create_data(data)

            # Convert to dictionary and add additional fields
            entity_data = data.dict()
            entity_data.update(kwargs)

            # Add timestamps if model supports them
            if hasattr(self.model, "created_at"):
                entity_data["created_at"] = datetime.utcnow()
            if hasattr(self.model, "updated_at"):
                entity_data["updated_at"] = datetime.utcnow()

            # Create entity
            entity = self.model(**entity_data)
            db.add(entity)
            await db.flush()

            # Log business event
            self.logger.log_business_event(
                event_name=f"{self.model.__name__.lower()}_created",
                user_id=str(getattr(entity_data, "created_by_id", "system")),
                resource_id=str(entity.id),
                entity_type=self.model.__name__
            )

            # Invalidate related caches
            await self._invalidate_related_caches(entity, "create")

            self.logger.info(
                EventType.DATABASE_OPERATION,
                f"Created {self.model.__name__}: {getattr(entity, 'name', entity.id)}",
                operation_name="create",
                entity_id=str(entity.id),
                entity_type=self.model.__name__
            )

            return entity

        except IntegrityError as e:
            raise ValidationException(
                f"Integrity error: {e!s}",
                field="integrity"
            ) from e
        except Exception as e:
            self.logger.log_error(e, operation="create", data=entity_data)
            raise

    @handle_database_errors(f"{__name__}_update")
    @transaction_manager.transaction
    async def update(
        self,
        db: AsyncSession,
        id: str | UUID,
        data: U,
        **kwargs
    ) -> T | None:
        """
        Update entity by ID with validation and cache invalidation
        """
        try:
            # Get existing entity
            entity = await self.get_by_id(db, id)
            if not entity:
                raise ValidationException(
                    f"{self.model.__name__} not found",
                    field="id"
                )

            # Validate update data
            self.validate_update_data(data, entity)

            # Update fields
            update_data = data.dict(exclude_unset=True)
            update_data.update(kwargs)

            for field, value in update_data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)

            # Update timestamp if model supports it
            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.utcnow()

            await db.flush()

            # Log business event
            self.logger.log_business_event(
                event_name=f"{self.model.__name__.lower()}_updated",
                user_id=str(getattr(update_data, "updated_by_id", "system")),
                resource_id=str(entity.id),
                entity_type=self.model.__name__
            )

            # Invalidate related caches
            await self._invalidate_related_caches(entity, "update")

            self.logger.info(
                EventType.DATABASE_OPERATION,
                f"Updated {self.model.__name__}: {getattr(entity, 'name', entity.id)}",
                operation_name="update",
                entity_id=str(entity.id),
                entity_type=self.model.__name__
            )

            return entity

        except ValidationException:
            raise
        except Exception as e:
            self.logger.log_error(e, operation="update", entity_id=str(id), data=update_data)
            raise

    @handle_database_errors(f"{__name__}_delete")
    @transaction_manager.transaction
    async def delete(
        self,
        db: AsyncSession,
        id: str | UUID,
        deleted_by_id: str | UUID = None
    ) -> bool:
        """
        Delete entity by ID with cache invalidation
        """
        try:
            # Get existing entity
            entity = await self.get_by_id(db, id)
            if not entity:
                return False

            # Store info for logging
            entity_info = {
                "id": str(entity.id),
                "name": getattr(entity, "name", None)
            }

            # Delete entity
            await db.delete(entity)
            await db.flush()

            # Log business event
            self.logger.log_business_event(
                event_name=f"{self.model.__name__.lower()}_deleted",
                user_id=str(deleted_by_id) if deleted_by_id else "system",
                resource_id=str(entity.id),
                entity_type=self.model.__name__
            )

            # Invalidate related caches
            await self._invalidate_related_caches(entity, "delete")

            self.logger.info(
                EventType.DATABASE_OPERATION,
                f"Deleted {self.model.__name__}: {entity_info['name'] or entity_info['id']}",
                operation_name="delete",
                entity_id=entity_info["id"],
                entity_type=self.model.__name__
            )

            return True

        except Exception as e:
            self.logger.log_error(e, operation="delete", entity_id=str(id))
            raise

    @handle_database_errors(f"{__name__}_bulk_create")
    @transaction_manager.transaction
    async def bulk_create(
        self,
        db: AsyncSession,
        data_list: builtins.list[C],
        **kwargs
    ) -> builtins.list[T]:
        """
        Create multiple entities efficiently
        """
        try:
            entities = []

            for data in data_list:
                # Validate each item
                self.validate_create_data(data)

                # Convert to dictionary and add additional fields
                entity_data = data.dict()
                entity_data.update(kwargs)

                # Add timestamps
                if hasattr(self.model, "created_at"):
                    entity_data["created_at"] = datetime.utcnow()
                if hasattr(self.model, "updated_at"):
                    entity_data["updated_at"] = datetime.utcnow()

                # Create entity
                entity = self.model(**entity_data)
                entities.append(entity)
                db.add(entity)

            await db.flush()

            # Log business event
            self.logger.log_business_event(
                event_name=f"{self.model.__name__.lower()}_bulk_created",
                user_id=str(getattr(kwargs, "created_by_id", "system")),
                resource_id=f"bulk_{len(entities)}",
                entity_type=self.model.__name__,
                entity_count=len(entities)
            )

            # Invalidate related caches
            if entities:
                await self._invalidate_related_caches(entities[0], "bulk_create")

            self.logger.info(
                EventType.DATABASE_OPERATION,
                f"Bulk created {len(entities)} {self.model.__name__} entities",
                operation_name="bulk_create",
                entity_count=len(entities),
                entity_type=self.model.__name__
            )

            return entities

        except Exception as e:
            self.logger.log_error(e, operation="bulk_create", entity_count=len(data_list))
            raise

    # Utility Methods

    async def _invalidate_related_caches(self, entity: T | builtins.list[T], operation: str):
        """
        Invalidate caches related to this entity
        """
        try:
            if isinstance(entity, list):
                # Handle bulk operations
                for single_entity in entity:
                    await self._invalidate_entity_cache(single_entity, operation)
            else:
                # Handle single entity
                await self._invalidate_entity_cache(entity, operation)

        except Exception as e:
            self.logger.log_error(e, operation="cache_invalidation", entity_type=self.model.__name__)

    async def _invalidate_entity_cache(self, entity: T, operation: str):
        """Invalidate cache for a single entity"""
        entity_id = str(entity.id)

        # Use cache invalidation manager based on entity type
        if "user" in self.model.__name__.lower():
            await cache_invalidation_manager.invalidate_user_caches(entity_id)
        elif "team" in self.model.__name__.lower():
            await cache_invalidation_manager.invalidate_team_caches(entity_id)
        elif "assessment" in self.model.__name__.lower():
            await cache_invalidation_manager.invalidate_assessment_caches(entity_id)
        else:
            # Generic invalidation
            await cache_invalidation_manager.invalidate_related_caches(
                self.model.__name__.lower(),
                entity_id,
                operation
            )

    def validate_id(self, id: str | UUID) -> str:
        """Validate and standardize ID"""
        if isinstance(id, str):
            try:
                UUID(id)
                return id
            except ValueError:
                raise ValidationException("Invalid UUID format", field="id")
        elif isinstance(id, UUID):
            return str(id)
        else:
            raise ValidationException("ID must be string or UUID", field="id")

    async def exists(self, db: AsyncSession, id: str | UUID) -> bool:
        """Check if entity exists"""
        try:
            result = await db.execute(
                select(func.count(self.model.id)).where(self.model.id == self.validate_id(id))
            )
            return result.scalar() > 0
        except Exception:
            return False

    async def get_or_404(self, db: AsyncSession, id: str | UUID) -> T:
        """Get entity or raise 404"""
        entity = await self.get_by_id(db, id)
        if not entity:
            raise ValidationException(
                f"{self.model.__name__} not found",
                field="id"
            )
        return entity

    # TODO(human): Implement advanced query builder
    # This should provide a fluent interface for building complex queries
    # with joins, subqueries, and advanced filtering capabilities

    class QueryBuilder:
        """
        Fluent query builder for complex database queries
        """

        def __init__(self, db: AsyncSession, model: type[T]):
            self.db = db
            self.model = model
            self.query = select(model)
            self.joins = []
            self.filters = []
            self.order_clauses = []

        def join(self, relationship: str, outer: bool = False):
            """Add join to query"""
            join_func = sqlalchemy.orm.outerjoin if outer else sqlalchemy.orm.join
            self.query = self.query.join_func(getattr(self.model, relationship))
            self.joins.append(relationship)
            return self

        def filter(self, *conditions):
            """Add filter conditions"""
            self.query = self.query.where(and_(*conditions))
            self.filters.extend(conditions)
            return self

        def or_filter(self, *conditions):
            """Add OR filter conditions"""
            self.query = self.query.where(or_(*conditions))
            self.filters.extend(conditions)
            return self

        def order_by(self, column: str, desc: bool = False):
            """Add ordering"""
            sort_column = getattr(self.model, column)
            order_clause = desc(sort_column) if desc else asc(sort_column)
            self.query = self.query.order_by(order_clause)
            self.order_clauses.append((column, desc))
            return self

        def limit(self, limit: int):
            """Add limit"""
            self.query = self.query.limit(limit)
            return self

        def offset(self, offset: int):
            """Add offset"""
            self.query = self.query.offset(offset)
            return self

        async def execute(self) -> list[T]:
            """Execute query and return results"""
            result = await self.db.execute(self.query)
            return result.scalars().all()

        async def first(self) -> T | None:
            """Execute query and return first result"""
            self.query = self.query.limit(1)
            result = await self.db.execute(self.query)
            return result.scalar_one_or_none()

        async def count(self) -> int:
            """Execute count query"""
            count_query = select(func.count(self.model.id))
            # Apply same filters
            for condition in self.filters:
                count_query = count_query.where(condition)

            result = await self.db.execute(count_query)
            return result.scalar()

    def query(self, db: AsyncSession) -> QueryBuilder:
        """Create new query builder instance"""
        return self.QueryBuilder(db, self.model)
