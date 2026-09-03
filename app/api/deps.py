# app/api/deps.py
"""
Authentication and authorization dependencies for FastAPI endpoints
Single source of truth for auth dependencies

Phase 2: Updated to use new service architecture with dependency injection
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

# Import database dependencies
from app.core.database import get_async_db

# Import new service dependencies
from app.core.service_provider import (
    get_authorization_service_dep,
    get_input_sanitizer_service_dep,
    get_password_service_dep,
    get_scoring_strategy_registry_dep,
    get_token_service_dep,
)
from app.services.assessment_scoring_strategies import ScoringStrategyRegistry

# Import security dependencies (maintained for backward compatibility)
from app.services.security import get_current_active_user, get_current_user
from app.services.security.authorization_service import AuthorizationService
from app.services.security.input_sanitizer_service import InputSanitizerService
from app.services.security.password_service import PasswordService
from app.services.security.token_service import TokenService

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


# =============================================================================
# New Service Dependencies (Phase 2)
# =============================================================================

# Re-export service dependencies for convenient importing
# These can be used directly in FastAPI endpoints with Depends()

# Example usage:
# from fastapi import Depends, APIRouter
# from app.api import deps
#
# @router.post("/login")
# async def login(
#     password_service: PasswordService = Depends(deps.get_password_service_dep),
#     token_service: TokenService = Depends(deps.get_token_service_dep),
# ):
#     # Use injected services
#     pass


# Export all dependencies for backward compatibility
__all__ = [
    # Database dependencies
    "get_async_db",
    "get_db",  # Alias for get_async_db
    # Authentication dependencies (from app.core.security)
    "get_current_active_superuser",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_user",
    # Service dependencies (from app.core.service_provider)
    "get_password_service_dep",
    "get_token_service_dep",
    "get_authorization_service_dep",
    "get_input_sanitizer_service_dep",
    "get_scoring_strategy_registry_dep",
    # Service types (for type hints)
    "PasswordService",
    "TokenService",
    "AuthorizationService",
    "InputSanitizerService",
    "ScoringStrategyRegistry",
    "AsyncSession",
]
