# app/core/database.py
"""
Single authoritative database configuration for PsychSync AI
Uses async SQLAlchemy 2.0 with asyncpg driver
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
import logging

from app.core.config import settings, get_database_url

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass

# Create async database engine
async_engine = create_async_engine(
    get_database_url(async_driver=True),
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

async def get_async_db() -> AsyncSession:
    """
    Async database dependency for FastAPI
    Provides a database session for each request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Legacy compatibility - DEPRECATED
def get_db():
    """
    Legacy sync database dependency - DEPRECATED
    Will be removed in future versions
    """
    raise DeprecationWarning(
        "get_db() is deprecated. Use get_async_db() instead. "
        "This function will be removed in the next major version."
    )

# Database initialization function
async def init_db():
    """Initialize database tables"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Database health check
async def check_db_health() -> bool:
    """Check database connectivity"""
    try:
        async with async_engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Database connection close for graceful shutdown
async def close_db_connections():
    """Close all database connections"""
    try:
        await async_engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")