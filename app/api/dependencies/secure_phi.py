"""
Secure PHI Access Layer for Clinical Endpoints

Provides helpers that resolve user PII from the encrypted SecureUser store,
with automatic fallback to the regular User model when a SecureUser record
doesn't exist yet (gradual migration support).

Usage in endpoints:
    from app.api.dependencies.secure_phi import resolve_user_phi

    phi = await resolve_user_phi(db, current_user)
    # phi.email, phi.full_name — sourced from SecureUser when available
"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.security.phi")


@dataclass(frozen=True)
class UserPHI:
    """Resolved user PII — may come from SecureUser or regular User."""

    user_id: UUID
    email: str
    full_name: Optional[str]
    source: str  # "secure" or "legacy"


async def resolve_user_phi(db: AsyncSession, user) -> UserPHI:
    """
    Resolve user PII from the encrypted SecureUser table.
    Falls back to the regular User model if no SecureUser record exists.

    This allows gradual migration: as users get SecureUser records,
    their PII is automatically served from the encrypted store.
    """
    try:
        from app.db.models.user_secure import SecureUser

        result = await db.execute(select(SecureUser).where(SecureUser.id == user.id))
        secure_user = result.scalar_one_or_none()

        if secure_user is not None:
            # hybrid_property handles decryption automatically;
            # fall back to legacy if decryption returns None
            email = secure_user.email or getattr(user, "email", "")
            full_name = secure_user.full_name or getattr(user, "full_name", None)
            return UserPHI(
                user_id=user.id,
                email=email,
                full_name=full_name,
                source="secure",
            )
    except Exception as e:
        logger.warning("SecureUser lookup failed, using legacy: %s", e)

    return UserPHI(
        user_id=user.id,
        email=getattr(user, "email", ""),
        full_name=getattr(user, "full_name", None),
        source="legacy",
    )
