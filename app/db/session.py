"""
Database session management

This module provides backward compatibility by re-exporting database session
functions from app.core.database.

All database configuration has been consolidated into app.core.database.
"""

from app.core.database import AsyncSessionLocal, SessionLocal
from app.core.database import async_engine as engine
from app.core.database import get_async_db
from app.core.database import get_sync_db as get_db  # Alias for backward compatibility

async_session = AsyncSessionLocal

__all__ = [
    "get_db",
    "get_async_db",
    "SessionLocal",
    "AsyncSessionLocal",
    "engine",
    "async_session",
]
