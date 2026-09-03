"""
Database Health Check Script for PsychSync
Tests database connectivity and shows basic information
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def test_database_connection():
    """Test database connection and show basic info"""
    try:
        print("🔍 PsychSync Database Health Check")
        print("=" * 50)

        # Get database URL from settings
        database_url = settings.get_database_url()
        print(f"📊 Database URL: {database_url}")

        # Create engine
        engine = create_async_engine(database_url)

        print("🔄 Testing database connection...")
        async with engine.begin() as conn:
            # Test basic connectivity
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")

            # Show database info
            if "sqlite" in database_url:
                # SQLite specific queries
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = result.fetchall()
                print(f"📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                # PostgreSQL specific queries
                result = await conn.execute(
                    text(
                        "SELECT * FROM information_schema.tables WHERE table_schema='public'"
                    )
                )
                tables = result.fetchall()
                print(f"📋 Found {len(tables)} tables in public schema:")
                for table in tables:
                    print(f"   - {table[2]}")  # table_name is at index 2

        print("🎉 Database health check completed successfully!")

    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Provide helpful suggestions
        if "does not exist" in str(e):
            print(
                "\n💡 Suggestion: Check if database user exists or create the database"
            )
        elif "Connection refused" in str(e):
            print("\n💡 Suggestion: Make sure database server is running")
        elif "No such file" in str(e):
            print("\n💡 Suggestion: SQLite database file will be created automatically")

        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_database_connection())
