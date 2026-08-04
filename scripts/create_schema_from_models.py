#!/usr/bin/env python3
"""
Create database schema directly from SQLAlchemy models.
This script creates all tables based on the current model definitions.
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base  # Import Base with all models


async def create_schema():
    """Create all tables from SQLAlchemy models."""
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL, echo=True  # Print SQL statements for verification
    )

    print("Creating database schema from models...")
    print("=" * 60)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("=" * 60)
    print("✅ Schema creation complete!")

    # List created tables
    async with engine.begin() as conn:
        result = await conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"\n📊 Total tables created: {len(tables)}")
        print("\nTables:")
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_schema())
