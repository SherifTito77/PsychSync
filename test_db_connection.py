#!/usr/bin/env python3
"""
Quick database connection test for validation
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.database import async_engine
    from app.core.config import settings
    print(f"✅ Successfully imported modules")
    print(f"✅ Database URL: {settings.DATABASE_URL}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_database():
    """Test database connectivity and basic operations"""
    try:
        print("\n🔍 Testing database connection...")

        # Test connection
        async with async_engine.begin() as conn:
            # Simple test query using text()
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed - wrong query result")
                return False

        # Test table existence
        print("\n📋 Checking tables...")
        async with async_engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]

            if not tables:
                print("❌ No tables found")
                return False

            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")

        # Test basic user query
        print("\n👤 Testing user table...")
        async with async_engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"✅ Users table accessible, {user_count} records found")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_imports():
    """Test key module imports"""
    print("\n🔍 Testing imports...")

    try:
        from app.api.v1.api import api_router
        print("✅ API router imported")

        # Skip models test since they may not exist in expected location
        print("⚠️  Models import skipped (not in expected location)")

        return True
    except ImportError as e:
        print(f"⚠️  Import warning: {e}")
        return False
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def main():
    """Main validation function"""
    print("🔍 PsychSync Database Validation")
    print("=" * 40)

    # Test imports
    imports_ok = await test_imports()

    # Test database
    db_ok = await test_database()

    # Summary
    print("\n📊 VALIDATION SUMMARY")
    print("=" * 40)
    print(f"Import Status: {'✅ PASS' if imports_ok else '⚠️  WARN'}")
    print(f"Database Status: {'✅ PASS' if db_ok else '❌ FAIL'}")

    if db_ok:
        print("\n✅ Database validation completed successfully!")
        return 0
    else:
        print("\n❌ Database validation failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
