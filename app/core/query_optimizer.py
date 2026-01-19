"""
Query Optimization Utilities

Provides utilities to optimize database queries and prevent N+1 query patterns.
"""

import logging
import time
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.db.models.response import Response
from app.db.models.assessment import Assessment
from app.db.models.user import User

logger = logging.getLogger(__name__)


def log_slow_query(threshold_ms: float = 100):
    """
    Decorator to log slow queries.

    Usage:
        @log_slow_query(threshold_ms=100)
        async def get_user_data(db, user_id):
            ...

    Args:
        threshold_ms: Log queries that take longer than this (milliseconds)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow query detected in {func.__name__}: {duration_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
        return wrapper
    return decorator


async def get_user_with_responses(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 100
) -> User | None:
    """
    Get user with their responses pre-loaded (prevents N+1 query).

    BEFORE (N+1 pattern):
        user = await db.get(User, user_id)
        responses = user.responses  # Triggers separate query!

    AFTER (1 query):
        user = await get_user_with_responses(db, user_id)
        responses = user.responses  # Already loaded, no query!
    """
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.responses)  # Eager load responses
        )
    )
    return result.scalar_one_or_none()


async def get_users_with_responses_by_ids(
    db: AsyncSession,
    user_ids: List[UUID],
    limit_per_user: int = 100
) -> List[User]:
    """
    Get multiple users with their responses pre-loaded.

    Prevents N+1 queries when loading multiple users.
    """
    if not user_ids:
        return []

    result = await db.execute(
        select(User)
        .where(User.id.in_(user_ids))
        .options(
            selectinload(User.responses)
        )
    )
    return result.scalars().all()


async def get_responses_with_assessments(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 100
) -> List[Response]:
    """
    Get user's responses with assessment data pre-loaded.

    Prevents N+1 queries when accessing response.assessment.
    """
    result = await db.execute(
        select(Response)
        .where(Response.user_id == user_id)
        .options(
            joinedload(Response.assessment)
        )
        .order_by(Response.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
