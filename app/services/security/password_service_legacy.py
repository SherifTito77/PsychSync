"""
Password service with history tracking.
Prevents reuse of the last N passwords (NIST SP 800-63B).
"""

import logging
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    validate_password,
    _contains_common_words as core_contains,
    _get_strength_rating as core_get_strength,
    get_password_hash as core_hash_password,
    verify_password as core_verify_password,
)
from app.db.models.password_history import PASSWORD_HISTORY_DEPTH, PasswordHistory

logger = logging.getLogger("app.security.password_history")


async def check_password_history(
    db: AsyncSession, user_id: UUID, password: str
) -> bool:
    """
    Check if password was used in the last PASSWORD_HISTORY_DEPTH changes.

    Returns True if the password matches a previous one (i.e. reuse detected).
    """
    stmt = (
        select(PasswordHistory.password_hash)
        .where(PasswordHistory.user_id == user_id)
        .order_by(desc(PasswordHistory.changed_at))
        .limit(PASSWORD_HISTORY_DEPTH)
    )
    result = await db.execute(stmt)
    previous_hashes = result.scalars().all()

    for old_hash in previous_hashes:
        if core_verify_password(password, old_hash):
            return True  # Reuse detected
    return False


async def record_password_change(
    db: AsyncSession,
    user_id: UUID,
    password_hash: str,
    reason: str = "user_initiated",
) -> None:
    """Record a password change in history and prune old entries."""
    entry = PasswordHistory(
        user_id=user_id,
        password_hash=password_hash,
        change_reason=reason,
    )
    db.add(entry)

    # Prune entries beyond the history depth
    subq = (
        select(PasswordHistory.id)
        .where(PasswordHistory.user_id == user_id)
        .order_by(desc(PasswordHistory.changed_at))
        .offset(PASSWORD_HISTORY_DEPTH)
    )
    old_ids = (await db.execute(subq)).scalars().all()
    if old_ids:
        from sqlalchemy import delete

        await db.execute(delete(PasswordHistory).where(PasswordHistory.id.in_(old_ids)))

    await db.flush()
    logger.info("Password history recorded for user %s (reason: %s)", user_id, reason)


def validate_password_strength(password):
    result = validate_password(password)
    return result["valid"]


def hash_password(password):
    return core_hash_password(password)


def verify_password(password, hashed):
    return core_verify_password(password, hashed)


def _contains_common_words(password: str) -> bool:
    return core_contains(password)


def _get_strength_rating(score: int) -> str:
    return core_get_strength(score)
