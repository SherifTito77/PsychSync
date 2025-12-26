# app/api/v1/deps.py
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.core.config import settings
from app.core.database import get_async_db as get_db
from app.db.models.user import User
from app.db.models.team import Team, TeamMember, TeamRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided and valid, but don't raise exception for invalid/missing tokens.
    Useful for endpoints where authentication is optional.
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_team_or_404(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Team:
    """
    Get team by ID and verify current user is a member.
    Returns team object if user has access, raises HTTPException otherwise.
    """
    # Get team
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check if user is member
    member_result = await db.execute(
        select(TeamMember).where(and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ))
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this team"
        )

    return team


async def check_team_member(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """
    Check if current user is a member of the specified team.
    """
    result = await db.execute(
        select(TeamMember).where(and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ))
    )

    return result.scalar_one_or_none() is not None


async def check_team_admin(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """
    Check if current user has admin or owner privileges for the specified team.
    """
    result = await db.execute(
        select(TeamMember).where(and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
        ))
    )

    return result.scalar_one_or_none() is not None


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user (requires admin privileges)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# ============================================================================
# MFA-REQUIRED ADMIN DEPENDENCY
# ============================================================================

async def get_current_user_with_mfa(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user, requiring 2FA to be enabled

    Use for sensitive admin operations.
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Two-factor authentication must be enabled for this operation"
        )

    return current_user


async def get_admin_user_with_mfa(
    current_user: User = Depends(get_current_user_with_mfa),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user, requiring both admin role AND 2FA

    Use for highly sensitive admin operations.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user
