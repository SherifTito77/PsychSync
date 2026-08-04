"""
PsychSync Enterprise Database - Core Configuration
Authoritative database engine and session configuration.
"""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_database_url, settings

# Logger setup
logger = logging.getLogger("app.database.config")
db_pool_logger = logging.getLogger("app.database.pool")

# Database security constants
QUERY_TIMEOUT = 30
SLOW_QUERY_THRESHOLD = 5.0
MAX_QUERY_RESULT_SIZE = 10000


class Base(DeclarativeBase):
    """Authoritative Base Model"""

    __table_args__ = {"extend_existing": True}


# =============================================================================
# ENGINE CONFIGURATION
# =============================================================================

# Create optimized async database engine
db_url = get_database_url(async_driver=True, test_mode=settings.TESTING)
logger.info(f"Connecting to database: {db_url}")
async_engine = create_async_engine(
    db_url,
    pool_size=20 if not settings.TESTING else 5,
    max_overflow=40 if not settings.TESTING else 10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_use_lifo=True,
    echo=settings.DB_ECHO and settings.DEBUG,
    future=True,
    connect_args={"timeout": 10},
)

# =============================================================================
# SQLITE COMPATIBILITY
# =============================================================================


@event.listens_for(async_engine.sync_engine, "connect")
def register_sqlite_functions(dbapi_connection, connection_record):
    """Register PostgreSQL-specific functions for SQLite development"""
    try:
        # Check if we are using SQLite
        if "sqlite" in str(async_engine.url):
            # Register gen_random_uuid()
            dbapi_connection.create_function(
                "gen_random_uuid", 0, lambda: str(uuid.uuid4())
            )
            # Register NOW() - use ISO format for SQLite compatibility with DateTime columns
            dbapi_connection.create_function(
                "NOW", 0, lambda: datetime.now().isoformat()
            )
            logger.info(
                "Registered gen_random_uuid() and NOW() for SQLite compatibility"
            )
    except Exception as e:
        logger.warning(f"Failed to register SQLite functions: {e}")


# =============================================================================
# SESSION FACTORY
# =============================================================================

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    join_transaction_mode="create_savepoint",
)

# =============================================================================
# DEPENDENCIES
# =================================================)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Authoritative database dependency"""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
