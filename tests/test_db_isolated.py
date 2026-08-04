"""
Completely isolated database test - verifies PostgreSQL extensions work
"""

import asyncio
import os

os.environ["ENVIRONMENT"] = "testing"
os.environ["TESTING"] = "True"

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

Base = DeclarativeBase()


async def test_extensions():
    """Direct test of PostgreSQL extensions"""
    engine = create_async_engine(
        "postgresql+asyncpg://sheriftito@localhost:5432/psychsync_test", echo=False
    )

    try:
        async with engine.begin() as conn:
            # Create extensions
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
            print("✓ citext extension created")

            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            print("✓ uuid-ossp extension created")

            # Test basic query
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("✓ Database query successful")

            # Test citext type works
            result = await conn.execute(text("SELECT 'hello'::citext = 'hello'"))
            assert result.scalar() is True
            print("✓ citext type works")

        print("\n✅ All database extension tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await engine.dispose()


if __name__ == "__main__":
    result = asyncio.run(test_extensions())
    exit(0 if result else 1)
