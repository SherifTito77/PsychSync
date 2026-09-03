"""
Atomic Database Operations Utility

Provides thread-safe, race-condition-free database operations for common
patterns that are vulnerable to race conditions.

Includes:
- Atomic counter increments
- Check-and-update operations
- Idempotent inserts
- Optimistic locking utilities
"""

import logging
from typing import Any, Dict, Optional, TypeVar
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


T = TypeVar("T")


class AtomicOperationError(Exception):
    """Base exception for atomic operation failures."""


class InsufficientResourcesError(AtomicOperationError):
    """Raised when atomic check-then-update fails due to insufficient resources."""


class AlreadyExistsError(AtomicOperationError):
    """Raised when idempotent insert detects existing record."""


async def atomic_increment(
    db: AsyncSession,
    model: type,
    record_id: UUID,
    field_name: str,
    increment: int = 1,
    minimum: Optional[int] = None,
) -> int:
    """
    Atomically increment a counter field in a database record.

    This prevents race conditions in check-then-update patterns like:
        record = await db.get(model, id)
        record.count += 1  # NOT ATOMIC!

    Args:
        db: Database session
        model: SQLAlchemy model class
        record_id: Primary key of the record
        field_name: Name of the counter field to increment
        increment: Amount to increment by (default: 1)
        minimum: Minimum value allowed (raises InsufficientResourcesError if would go below)

    Returns:
        The new value of the counter

    Raises:
        InsufficientResourcesError: If minimum check fails
        AtomicOperationError: If operation fails

    Example:
        new_count = await atomic_increment(
            db, User, user_id, "credits", increment=-10, minimum=0
        )
    """
    try:
        # Build the update statement
        stmt = (
            update(model)
            .where(model.id == record_id)
            .values(**{field_name: getattr(model, field_name) + increment})
            .returning(getattr(model, field_name))
        )

        # If minimum specified, add a WHERE clause to enforce it
        if minimum is not None:
            stmt = stmt.where(getattr(model, field_name) >= minimum)

        result = await db.execute(stmt)
        new_value = result.scalar_one_or_none()

        if new_value is None:
            if minimum is not None:
                raise InsufficientResourcesError(
                    f"Cannot decrement {field_name} below {minimum}"
                )
            raise AtomicOperationError(
                f"Record {record_id} not found in {model.__name__}"
            )

        await db.commit()
        return new_value

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error in atomic_increment: {e}")
        raise AtomicOperationError(f"Database integrity violation: {e}") from e
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in atomic_increment: {e}")
        raise


async def atomic_check_and_update(
    db: AsyncSession,
    model: type,
    record_id: UUID,
    check_field: str,
    check_value: Any,
    update_fields: Dict[str, Any],
    must_exist: bool = True,
) -> bool:
    """
    Atomically check a field's value and update if it matches.

    Prevents race conditions in patterns like:
        record = await db.get(model, id)
        if record.status == "pending":  # RACE: Another request might change this
            record.status = "processing"
            await db.commit()

    Args:
        db: Database session
        model: SQLAlchemy model class
        record_id: Primary key of the record
        check_field: Name of field to check
        check_value: Value that field must have
        update_fields: Dictionary of fields to update
        must_exist: If True, raises error if record doesn't exist

    Returns:
        True if record was updated, False if check failed

    Raises:
        AtomicOperationError: If must_exist=True and record not found

    Example:
        success = await atomic_check_and_update(
            db, Assessment, assessment_id,
            check_field="status", check_value="draft",
            update_fields={"status": "published"}
        )
    """
    try:
        # Build update statement with WHERE clause for check
        stmt = (
            update(model)
            .where(model.id == record_id, getattr(model, check_field) == check_value)
            .values(**update_fields)
            .returning(model.id)
        )

        result = await db.execute(stmt)
        updated_id = result.scalar_one_or_none()

        if updated_id:
            await db.commit()
            return True

        if must_exist:
            raise AtomicOperationError(f"Record {record_id} not found or check failed")
        return False

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error in atomic_check_and_update: {e}")
        raise AtomicOperationError(f"Database integrity violation: {e}") from e
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in atomic_check_and_update: {e}")
        raise


async def idempotent_insert(
    db: AsyncSession,
    model: type,
    unique_fields: Dict[str, Any],
    data: Dict[str, Any],
    on_conflict: str = "ignore",  # or "update"
) -> Any:
    """
    Insert a record idempotently, handling duplicates gracefully.

    Prevents race conditions where concurrent requests try to insert
    the same record simultaneously.

    Args:
        db: Database session
        model: SQLAlchemy model class
        unique_fields: Dictionary of fields that must be unique
        data: Dictionary of all fields to insert
        on_conflict: "ignore" to skip if exists, "update" to update if exists

    Returns:
        The created or existing record

    Raises:
        AlreadyExistsError: If on_conflict="ignore" and record exists
        AtomicOperationError: If operation fails

    Example:
        response = await idempotent_insert(
            db, Response,
            unique_fields={"assessment_id": assessment_id, "user_id": user_id},
            data={"status": "in_progress", "created_at": datetime.utcnow()}
        )
    """
    try:
        # Try to insert first
        stmt = insert(model).values(**data)
        result = await db.execute(stmt)

        # Check if insert succeeded
        if result.rowcount > 0:
            await db.commit()
            # Fetch the inserted record
            unique_query = select(model).where(
                **{getattr(model, k): v for k, v in unique_fields.items()}
            )
            result = await db.execute(unique_query)
            return result.scalar_one()

        # Record already exists
        if on_conflict == "update":
            # Update existing record
            stmt = (
                update(model)
                .where(**{getattr(model, k): v for k, v in unique_fields.items()})
                .values(**data)
            )
            await db.execute(stmt)
            await db.commit()

            # Fetch updated record
            unique_query = select(model).where(
                **{getattr(model, k): v for k, v in unique_fields.items()}
            )
            result = await db.execute(unique_query)
            return result.scalar_one()
        else:
            # on_conflict == "ignore" - fetch and return existing
            await db.rollback()
            unique_query = select(model).where(
                **{getattr(model, k): v for k, v in unique_fields.items()}
            )
            result = await db.execute(unique_query)
            existing = result.scalar_one_or_none()
            if existing:
                raise AlreadyExistsError(
                    f"{model.__name__} with {unique_fields} already exists"
                )
            raise AtomicOperationError(
                f"Failed to insert {model.__name__}: unexpected state"
            )

    except IntegrityError as e:
        await db.rollback()
        if on_conflict == "ignore":
            # Try to fetch existing record
            try:
                unique_query = select(model).where(
                    **{getattr(model, k): v for k, v in unique_fields.items()}
                )
                result = await db.execute(unique_query)
                existing = result.scalar_one_or_none()
                if existing:
                    raise AlreadyExistsError(
                        f"{model.__name__} with {unique_fields} already exists"
                    ) from e
            except Exception:
                pass
        raise AtomicOperationError(f"Database integrity violation: {e}") from e
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in idempotent_insert: {e}")
        raise


async def select_for_update(db: AsyncSession, model: type, record_id: UUID) -> Any:
    """
    Select a record with row-level lock for update.

    Prevents race conditions when you need to:
    1. Read a record
    2. Make decisions based on its values
    3. Update it

    The lock ensures no other transaction can modify the record
    until your transaction completes.

    Args:
        db: Database session
        model: SQLAlchemy model class
        record_id: Primary key of the record

    Returns:
        The locked record

    Raises:
        AtomicOperationError: If record not found

    Example:
        async with database_transaction(db):
            assessment = await select_for_update(db, Assessment, assessment_id)
            # Make decisions based on assessment state
            if assessment.status == "draft":
                assessment.status = "published"
                # Update is safe - no other transaction can modify this row
    """
    try:
        stmt = (
            select(model)
            .where(model.id == record_id)
            .with_for_update()  # CRITICAL: Row-level lock
        )

        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            raise AtomicOperationError(
                f"{model.__name__} with id {record_id} not found"
            )

        return record

    except Exception as e:
        logger.error(f"Error in select_for_update: {e}")
        raise


async def atomic_get_or_create(
    db: AsyncSession, model: type, defaults: Dict[str, Any], **lookup_fields
) -> tuple[Any, bool]:
    """
    Atomically get a record or create it if it doesn't exist.

    Prevents race conditions in patterns like:
        user = await get_user_by_email(email)
        if not user:
            user = await create_user(email)  # RACE: Another request might create it

    Args:
        db: Database session
        model: SQLAlchemy model class
        defaults: Dictionary of fields for new record if created
        **lookup_fields: Fields to lookup existing record by

    Returns:
        Tuple of (record, created) where created is True if new record created

    Example:
        user, created = await atomic_get_or_create(
            db, User,
            defaults={"name": "John Doe"},
            email="john@example.com"
        )
    """
    try:
        # Try to find existing record
        stmt = select(model).where(
            **{getattr(model, k): v for k, v in lookup_fields.items()}
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            return record, False

        # Create new record
        new_record = model(**defaults, **lookup_fields)
        db.add(new_record)

        try:
            await db.commit()
            await db.refresh(new_record)
            return new_record, True
        except IntegrityError:
            # Record was created by another request
            await db.rollback()
            result = await db.execute(stmt)
            record = result.scalar_one()
            return record, False

    except Exception as e:
        await db.rollback()
        logger.error(f"Error in atomic_get_or_create: {e}")
        raise AtomicOperationError(f"Failed to get or create: {e}") from e
