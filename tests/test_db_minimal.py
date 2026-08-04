"""
Minimal database test to verify fixes without full app initialization
"""

import asyncio
import os

import pytest

os.environ["ENVIRONMENT"] = "testing"
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://sheriftito@localhost:5432/psychsync_test"
)

# Import Base directly to avoid full app initialization
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base_class import Base


@pytest.mark.asyncio
async def test_database_extensions():
    """Verify citext and uuid-ossp extensions work"""
    engine = create_async_engine(
        "postgresql+asyncpg://sheriftito@localhost:5432/psychsync_test", echo=False
    )

    async with engine.begin() as conn:
        # Create extensions
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        print("✓ Extensions created successfully")

        # Test that they work
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("✓ Database connection works")

    await engine.dispose()
    print("✓ Test passed")


@pytest.mark.asyncio
async def test_schema_cleanup():
    """Verify schema cleanup works"""
    engine = create_async_engine(
        "postgresql+asyncpg://sheriftito@localhost:5432/psychsync_test", echo=False
    )

    async with engine.begin() as conn:
        # Drop and recreate schema
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

        # Create extensions
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables created after schema cleanup")

    await engine.dispose()
    print("✓ Schema cleanup test passed")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
