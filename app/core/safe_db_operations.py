"""
Safe Database Operations Helper

Provides reusable functions for database operations with proper error handling,
transaction management, and race condition prevention.

Usage:
    from app.core.safe_db_operations import safe_create, safe_update, safe_delete

    # Create with error handling
    user = await safe_create(db, User, **user_data)

    # Update with row-level locking
    user = await safe_update(db, User, user_id, {"status": "active"})

    # Delete with error handling
    await safe_delete(db, User, user_id)
"""

import logging
from typing import TypeVar, Type, Any, Optional
from uuid import UUID

from sqlalchemy import select, update as sql_update, delete as sql_delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


async def safe_create(
    db: AsyncSession,
    model: Type[ModelType],
    **kwargs: Any
) -> ModelType:
    """
    Safely create a database record with proper error handling and rollback.

    Args:
        db: Async database session
        model: SQLAlchemy model class
        **kwargs: Field values for the new record

    Returns:
        Created model instance

    Raises:
        IntegrityError: If unique constraint violated
        SQLAlchemyError: For other database errors

    Example:
        user = await safe_create(db, User, email="test@example.com", name="Test")
    """
    try:
        obj = model(**kwargs)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

        logger.info(f"Created {model.__name__} ID: {obj.id}")
        return obj

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error creating {model.__name__}: {e}", exc_info=True)
        raise

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error creating {model.__name__}: {e}", exc_info=True)
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error creating {model.__name__}: {e}", exc_info=True)
        raise


async def safe_update(
    db: AsyncSession,
    model: Type[ModelType],
    record_id: UUID,
    update_data: dict[str, Any],
    lock_for_update: bool = True
) -> Optional[ModelType]:
    """
    Safely update a database record with row-level locking to prevent race conditions.

    Args:
        db: Async database session
        model: SQLAlchemy model class
        record_id: UUID of the record to update
        update_data: Dictionary of field values to update
        lock_for_update: If True, use SELECT FOR UPDATE to prevent concurrent modification

    Returns:
        Updated model instance, or None if not found

    Raises:
        SQLAlchemyError: For database errors

    Example:
        user = await safe_update(db, User, user_id, {"status": "active"})
    """
    try:
        # Build query
        query = select(model).where(model.id == record_id)

        # Add row-level locking if requested
        if lock_for_update:
            query = query.with_for_update()

        # Execute query
        result = await db.execute(query)
        obj = result.scalar_one_or_none()

        if not obj:
            logger.warning(f"{model.__name__} ID {record_id} not found for update")
            return None

        # Update fields
        for field, value in update_data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
            else:
                logger.warning(f"Field {field} does not exist on {model.__name__}")

        await db.commit()
        await db.refresh(obj)

        logger.info(f"Updated {model.__name__} ID: {record_id}")
        return obj

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error updating {model.__name__} {record_id}: {e}", exc_info=True)
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error updating {model.__name__} {record_id}: {e}", exc_info=True)
        raise


async def safe_delete(
    db: AsyncSession,
    model: Type[ModelType],
    record_id: UUID
) -> bool:
    """
    Safely delete a database record with proper error handling and rollback.

    Args:
        db: Async database session
        model: SQLAlchemy model class
        record_id: UUID of the record to delete

    Returns:
        True if deleted, False if not found

    Raises:
        SQLAlchemyError: For database errors

    Example:
        deleted = await safe_delete(db, User, user_id)
    """
    try:
        # Check if record exists
        result = await db.execute(select(model).where(model.id == record_id))
        obj = result.scalar_one_or_none()

        if not obj:
            logger.warning(f"{model.__name__} ID {record_id} not found for deletion")
            return False

        await db.delete(obj)
        await db.commit()

        logger.info(f"Deleted {model.__name__} ID: {record_id}")
        return True

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error deleting {model.__name__} {record_id}: {e}", exc_info=True)
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error deleting {model.__name__} {record_id}: {e}", exc_info=True)
        raise


async def safe_get_with_lock(
    db: AsyncSession,
    model: Type[ModelType],
    record_id: UUID
) -> Optional[ModelType]:
    """
    Get a record with row-level locking (SELECT FOR UPDATE).

    Use this when you need to read a record and then update it,
    to prevent race conditions with concurrent requests.

    Args:
        db: Async database session
        model: SQLAlchemy model class
        record_id: UUID of the record to fetch

    Returns:
        Model instance with lock, or None if not found

    Example:
        user = await safe_get_with_lock(db, User, user_id)
        user.status = "active"
        await db.commit()
    """
    try:
        result = await db.execute(
            select(model)
            .where(model.id == record_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching {model.__name__} {record_id} with lock: {e}", exc_info=True)
        raise


async def safe_bulk_create(
    db: AsyncSession,
    model: Type[ModelType],
    items: list[dict[str, Any]]
) -> list[ModelType]:
    """
    Safely create multiple records in a single transaction.

    All records will be created in one transaction - if any fails,
    all changes are rolled back.

    Args:
        db: Async database session
        model: SQLAlchemy model class
        items: List of dictionaries with field values

    Returns:
        List of created model instances

    Raises:
        IntegrityError: If any constraint violated
        SQLAlchemyError: For database errors

    Example:
        users = await safe_bulk_create(db, User, [
            {"email": "user1@example.com", "name": "User 1"},
            {"email": "user2@example.com", "name": "User 2"}
        ])
    """
    try:
        created_objects = []

        for item_data in items:
            obj = model(**item_data)
            db.add(obj)
            created_objects.append(obj)

        await db.commit()

        # Refresh all objects to get database-generated values
        for obj in created_objects:
            await db.refresh(obj)

        logger.info(f"Bulk created {len(created_objects)} {model.__name__} records")
        return created_objects

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error in bulk create of {model.__name__}: {e}", exc_info=True)
        raise

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error in bulk create of {model.__name__}: {e}", exc_info=True)
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error in bulk create of {model.__name__}: {e}", exc_info=True)
        raise


async def handle_integrity_error(
    db: AsyncSession,
    error: IntegrityError,
    context: str
) -> str:
    """
    Handle IntegrityError with user-friendly messages.

    Args:
        db: Async database session (for rollback if needed)
        error: The IntegrityError exception
        context: Description of what operation was being performed

    Returns:
        User-friendly error message

    Example:
        try:
            user = await safe_create(db, User, email="test@example.com")
        except IntegrityError as e:
            message = await handle_integrity_error(db, e, "user creation")
            raise HTTPException(400, detail=message)
    """
    await db.rollback()

    error_str = str(error).lower()

    if "unique" in error_str or "duplicate" in error_str:
        if "email" in error_str:
            return f"A record with this email already exists"
        elif "username" in error_str:
            return f"A record with this username already exists"
        elif "team" in error_str and "user" in error_str:
            return f"User is already a member of this team"
        else:
            return f"A duplicate record already exists"

    elif "foreign key" in error_str:
        return f"Referenced record does not exist"

    elif "check" in error_str:
        return f"Data validation failed"

    else:
        logger.error(f"Unexpected integrity error in {context}: {error}")
        return f"Database constraint violation"
