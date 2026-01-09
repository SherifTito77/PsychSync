# app/repositories/base_repository.py

"""
ENTERPRISE-GRADE BASE REPOSITORY
Abstract base repository with common CRUD operations and security features

REPOSITORY PATTERN BENEFITS:
- Abstraction over database operations
- Consistent data access patterns
- Built-in security and validation
- Performance monitoring
- Error handling standardization
- Audit logging integration

Author: Security Team
Version: 2.0 Enterprise Security
"""

from abc import ABC
from datetime import datetime
import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Initialize repository logger
repo_logger = logging.getLogger("app.repositories.base")

# Generic type for model classes
ModelType = TypeVar("ModelType")
# Generic type for Pydantic schemas
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Abstract base repository with common CRUD operations and enterprise features
    """

    def __init__(self, db: AsyncSession, model_class: type[ModelType]):
        """
        Initialize repository

        Args:
            db: Database session
            model_class: SQLAlchemy model class
        """
        self.db = db
        self.model_class = model_class
        self.logger = logging.getLogger(f"app.repositories.{model_class.__name__.lower()}")

    async def get_by_id(self, id: Any, include_deleted: bool = False) -> ModelType | None:
        """
        Get entity by ID with optional soft-delete filtering

        Args:
            id: Entity ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            Entity instance or None
        """
        try:
            query = select(self.model_class).where(self.model_class.id == id)

            # Apply soft-delete filter if model supports it
            if hasattr(self.model_class, "deleted_at") and not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            result = await self.db.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                self.logger.debug(f"Entity found: {self.model_class.__name__} {id}")
            else:
                self.logger.debug(f"Entity not found: {self.model_class.__name__} {id}")

            return entity

        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by ID {id}: {e}")
            raise

    async def get_by_field(
        self, field_name: str, field_value: Any, include_deleted: bool = False
    ) -> ModelType | None:
        """
        Get entity by field value

        Args:
            field_name: Name of the field
            field_value: Value to search for
            include_deleted: Whether to include soft-deleted records

        Returns:
            Entity instance or None
        """
        try:
            if not hasattr(self.model_class, field_name):
                raise ValueError(f"Model {self.model_class.__name__} has no field {field_name}")

            field = getattr(self.model_class, field_name)
            query = select(self.model_class).where(field == field_value)

            # Apply soft-delete filter if model supports it
            if hasattr(self.model_class, "deleted_at") and not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            self.logger.error(
                f"Error getting {self.model_class.__name__} by {field_name}={field_value}: {e}"
            )
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        order_by: str | None = None,
    ) -> list[ModelType]:
        """
        Get all entities with pagination and filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records
            order_by: Field to order by (with optional direction)

        Returns:
            List of entity instances
        """
        try:
            query = select(self.model_class)

            # Apply soft-delete filter if model supports it
            if hasattr(self.model_class, "deleted_at") and not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            # Apply ordering
            if order_by:
                if order_by.startswith("-"):
                    field_name = order_by[1:]
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        query = query.order_by(field.desc())
                elif hasattr(self.model_class, order_by):
                    field = getattr(self.model_class, order_by)
                    query = query.order_by(field)

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            entities = result.scalars().all()

            self.logger.debug(
                f"Retrieved {len(entities)} {self.model_class.__name__} records",
                extra={"skip": skip, "limit": limit, "total": len(entities)},
            )

            return entities

        except Exception as e:
            self.logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            raise

    async def count(
        self, include_deleted: bool = False, filters: dict[str, Any] | None = None
    ) -> int:
        """
        Count entities with optional filtering

        Args:
            include_deleted: Whether to include soft-deleted records
            filters: Dictionary of field filters

        Returns:
            Count of entities
        """
        try:
            query = select(func.count(self.model_class.id))

            # Apply soft-delete filter if model supports it
            if hasattr(self.model_class, "deleted_at") and not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            # Apply additional filters
            if filters:
                for field_name, field_value in filters.items():
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        query = query.where(field == field_value)

            result = await self.db.execute(query)
            count = result.scalar()

            self.logger.debug(
                f"Counted {count} {self.model_class.__name__} records",
                extra={"filters": filters, "include_deleted": include_deleted},
            )

            return count

        except Exception as e:
            self.logger.error(f"Error counting {self.model_class.__name__}: {e}")
            raise

    async def create(
        self, create_data: CreateSchemaType, created_by: Any | None = None
    ) -> ModelType:
        """
        Create new entity with audit fields

        Args:
            create_data: Data for creating the entity
            created_by: ID of user creating the entity

        Returns:
            Created entity instance
        """
        try:
            # Convert Pydantic schema to dictionary
            entity_data = create_data.dict(exclude_unset=True)

            # Add audit fields if model supports them
            if hasattr(self.model_class, "created_at"):
                entity_data["created_at"] = datetime.utcnow()
            if hasattr(self.model_class, "updated_at"):
                entity_data["updated_at"] = datetime.utcnow()
            if hasattr(self.model_class, "created_by") and created_by:
                entity_data["created_by"] = created_by

            # Create entity instance
            entity = self.model_class(**entity_data)

            # Save to database
            self.db.add(entity)
            await self.db.flush()  # Get ID without committing

            self.logger.info(
                f"Created {self.model_class.__name__} with ID {entity.id}",
                extra={"entity_id": entity.id, "created_by": created_by},
            )

            return entity

        except Exception as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {e}")
            await self.db.rollback()
            raise

    async def update(
        self, id: Any, update_data: UpdateSchemaType, updated_by: Any | None = None
    ) -> ModelType | None:
        """
        Update entity with audit fields

        Args:
            id: Entity ID
            update_data: Data for updating the entity
            updated_by: ID of user updating the entity

        Returns:
            Updated entity instance or None
        """
        try:
            # Get existing entity
            entity = await self.get_by_id(id)
            if not entity:
                self.logger.warning(f"Cannot update {self.model_class.__name__} {id}: not found")
                return None

            # Convert Pydantic schema to dictionary
            entity_update_data = update_data.dict(exclude_unset=True)

            # Add audit fields if model supports them
            if hasattr(self.model_class, "updated_at"):
                entity_update_data["updated_at"] = datetime.utcnow()
            if hasattr(self.model_class, "updated_by") and updated_by:
                entity_update_data["updated_by"] = updated_by

            # Update entity
            for field, value in entity_update_data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)

            # Save to database
            await self.db.flush()

            self.logger.info(
                f"Updated {self.model_class.__name__} with ID {id}",
                extra={
                    "entity_id": id,
                    "updated_by": updated_by,
                    "updated_fields": list(entity_update_data.keys()),
                },
            )

            return entity

        except Exception as e:
            self.logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            await self.db.rollback()
            raise

    async def delete(
        self, id: Any, deleted_by: Any | None = None, hard_delete: bool = False
    ) -> bool:
        """
        Delete entity (soft delete by default)

        Args:
            id: Entity ID
            deleted_by: ID of user deleting the entity
            hard_delete: Whether to perform hard delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Get existing entity
            entity = await self.get_by_id(id)
            if not entity:
                self.logger.warning(f"Cannot delete {self.model_class.__name__} {id}: not found")
                return False

            if hard_delete:
                # Perform hard delete
                await self.db.delete(entity)
                self.logger.info(
                    f"Hard deleted {self.model_class.__name__} with ID {id}",
                    extra={"entity_id": id, "deleted_by": deleted_by},
                )
            # Perform soft delete if model supports it
            elif hasattr(entity, "deleted_at"):
                entity.deleted_at = datetime.utcnow()
                if hasattr(entity, "deleted_by") and deleted_by:
                    entity.deleted_by = deleted_by
                self.logger.info(
                    f"Soft deleted {self.model_class.__name__} with ID {id}",
                    extra={"entity_id": id, "deleted_by": deleted_by},
                )
            else:
                # Model doesn't support soft delete, fall back to hard delete
                await self.db.delete(entity)
                self.logger.warning(
                    f"Model {self.model_class.__name__} doesn't support soft delete, using hard delete"
                )

            await self.db.flush()
            return True

        except Exception as e:
            self.logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            await self.db.rollback()
            raise

    async def exists(self, id: Any, include_deleted: bool = False) -> bool:
        """
        Check if entity exists

        Args:
            id: Entity ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            True if entity exists, False otherwise
        """
        try:
            query = select(func.count(self.model_class.id)).where(self.model_class.id == id)

            # Apply soft-delete filter if model supports it
            if hasattr(self.model_class, "deleted_at") and not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            result = await self.db.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            self.logger.error(f"Error checking {self.model_class.__name__} existence {id}: {e}")
            raise

    async def bulk_create(
        self, create_data_list: list[CreateSchemaType], created_by: Any | None = None
    ) -> list[ModelType]:
        """
        Create multiple entities efficiently

        Args:
            create_data_list: List of creation data
            created_by: ID of user creating the entities

        Returns:
            List of created entity instances
        """
        try:
            entities = []
            current_time = datetime.utcnow()

            for create_data in create_data_list:
                # Convert Pydantic schema to dictionary
                entity_data = create_data.dict(exclude_unset=True)

                # Add audit fields if model supports them
                if hasattr(self.model_class, "created_at"):
                    entity_data["created_at"] = current_time
                if hasattr(self.model_class, "updated_at"):
                    entity_data["updated_at"] = current_time
                if hasattr(self.model_class, "created_by") and created_by:
                    entity_data["created_by"] = created_by

                # Create entity instance
                entity = self.model_class(**entity_data)
                entities.append(entity)

            # Bulk insert
            self.db.add_all(entities)
            await self.db.flush()

            self.logger.info(
                f"Bulk created {len(entities)} {self.model_class.__name__} records",
                extra={"count": len(entities), "created_by": created_by},
            )

            return entities

        except Exception as e:
            self.logger.error(f"Error bulk creating {self.model_class.__name__}: {e}")
            await self.db.rollback()
            raise

    async def apply_filters(self, query, filters: dict[str, Any]):
        """
        Apply filters to a query

        Args:
            query: SQLAlchemy query
            filters: Dictionary of field filters

        Returns:
            Query with filters applied
        """
        for field_name, field_value in filters.items():
            if hasattr(self.model_class, field_name) and field_value is not None:
                field = getattr(self.model_class, field_name)

                # Handle different filter types
                if isinstance(field_value, list):
                    # Handle list filters (IN clause)
                    query = query.where(field.in_(field_value))
                elif isinstance(field_value, dict):
                    # Handle complex filters
                    if "operator" in field_value:
                        operator = field_value["operator"]
                        value = field_value["value"]

                        if operator == "!=":
                            query = query.where(field != value)
                        elif operator == ">":
                            query = query.where(field > value)
                        elif operator == "<":
                            query = query.where(field < value)
                        elif operator == ">=":
                            query = query.where(field >= value)
                        elif operator == "<=":
                            query = query.where(field <= value)
                        elif operator == "like":
                            query = query.where(field.like(f"%{value}%"))
                        elif operator == "ilike":
                            query = query.where(field.ilike(f"%{value}%"))
                        # Add more operators as needed
                else:
                    # Simple equality filter
                    query = query.where(field == field_value)

        return query

    async def get_with_relations(
        self, id: Any, relations: list[str], include_deleted: bool = False
    ) -> ModelType | None:
        """
        Get entity with related objects loaded

        Args:
            id: Entity ID
            relations: List of relation names to load
            include_deleted: Whether to include soft-deleted records

        Returns:
            Entity instance with relations loaded
        """
        try:
            # Build select query with relations
            query = (
                select(self.model_class)
                .options(
                    *[selectinload(getattr(self.model_class, relation)) for relation in relations]
                )
                .where(self.model_class.id == id)
            )

            # Apply soft-delete filter if model supports it
            if hasattr(self.model_class, "deleted_at") and not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            result = await self.db.execute(query)
            entity = result.scalar_one_or_none()

            if entity:
                self.logger.debug(
                    f"Entity with relations loaded: {self.model_class.__name__} {id}",
                    extra={"relations": relations},
                )

            return entity

        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} with relations {id}: {e}")
            raise
