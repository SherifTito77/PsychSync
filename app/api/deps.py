# app/api/deps.py
"""
Authentication and authorization dependencies for FastAPI endpoints
Single source of truth for auth dependencies
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

# Import database dependencies
from app.core.database import get_async_db

# Import security dependencies
from app.core.security import (
    get_current_user,
    get_current_active_user
)

# Aliases for backward compatibility
get_db = get_async_db

# TODO: Implement admin-specific functions when needed
async def get_current_active_superuser():
    """Placeholder for superuser authentication"""
    # For now, just return active user check
    # In production, this would check admin/superuser role
    return await get_current_active_user()

async def get_current_admin_user():
    """Placeholder for admin user authentication"""
    # For now, just return active user check
    # In production, this would check admin role
    return await get_current_active_user()

# Export all dependencies for backward compatibility
__all__ = [
    'get_async_db',
    'get_db',  # Alias for get_async_db
    'get_current_user',
    'get_current_active_user',
    'get_current_active_superuser',
    'get_current_admin_user'
]