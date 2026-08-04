#!/usr/bin/env python3
"""
Direct Database Initialization
Creates database schema using SQLAlchemy models (bypasses complex migration chains)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base


async def init_database():
    """Initialize database with all tables"""
    print("🚀 Direct Database Initialization")
    print("=" * 70)
    print()

    # Create async engine
    database_url = str(settings.DATABASE_URL).replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(database_url, echo=True)

    try:
        print("Step 1: Creating all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Tables created successfully!")
        print()

        # List created tables
        print("Step 2: Verifying created tables...")
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT LIKE 'alembic%'
                ORDER BY tablename;
            """
                )
            )
            tables = [row[0] for row in result]

            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")

        print()
        print("=" * 70)
        print("✅ Database initialization complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Create alembic_version entry: python scripts/stamp_alembic.py")
        print("  2. Run regression tests: pytest tests/api/test_regression*.py -v")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(init_database())
    sys.exit(exit_code)
