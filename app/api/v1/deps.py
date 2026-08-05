# app/core/deps.py — single source of truth for auth dependencies.
from fastapi import Depends, HTTPException, status

from app.core.database import get_async_db as get_db  # noqa: F401
from app.core.security import (  # noqa: F401
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
)


async def get_current_user_optional(token: str = Depends(oauth2_scheme)):
    """Return current user or None if unauthenticated."""
    try:
        return await get_current_user(token=token)
    except Exception:
        return None


async def get_current_admin_user(current_user=Depends(get_current_user)):
    """Require admin role."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin required"
        )
    return current_user


async def get_current_user_with_mfa(current_user=Depends(get_current_user)):
    """Placeholder: require MFA-verified user."""
    return current_user


async def get_admin_user_with_mfa(current_user=Depends(get_current_admin_user)):
    """Placeholder: require MFA-verified admin."""
    return current_user


async def get_team_or_404(team_id: int, current_user=Depends(get_current_user)):
    """Stub: return team_id; real impl would query DB."""
    return team_id


async def check_team_member(team_id: int, current_user=Depends(get_current_user)):
    """Stub: verify current user is a team member."""
    return current_user


async def check_team_admin(team_id: int, current_user=Depends(get_current_user)):
    """Stub: verify current user is a team admin."""
    return current_user
