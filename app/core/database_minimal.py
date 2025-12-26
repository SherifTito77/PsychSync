"""
Minimal database configuration for troubleshooting connection issues
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Simple database URL - no extra parameters
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://psychsync_user:C8Vsywo9yXRQSOaGwxjVVQ-Secure9@localhost:5432/psychsync_db")

class Base(DeclarativeBase):
    pass

# Create minimal async engine
async_engine_minimal = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
AsyncSessionLocalMinimal = async_sessionmaker(
    bind=async_engine_minimal,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_async_db_minimal():
    """Minimal async database session generator"""
    async with AsyncSessionLocalMinimal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

async def test_connection():
    """Test the minimal database connection"""
    try:
        async with async_engine_minimal.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1 as test"))
            print(f"✅ Minimal database connection successful: {result}")
            return True
    except Exception as e:
        print(f"❌ Minimal database connection failed: {e}")
        return False