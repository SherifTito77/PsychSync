#!/usr/bin/env python3
"""
Initialize PsychSync Database
This script creates all necessary database tables and runs initial setup.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.db.session import async_engine
from app.db.base import Base
from app.db.models import *  # Import all models


async def check_database_connection():
    """Check if we can connect to the database"""
    print("🔌 Checking database connection...")
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def check_tables_exist():
    """Check which tables exist in the database"""
    print("\n📋 Checking existing tables...")
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✅ Found {len(tables)} existing tables:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No tables found in database")
            
            return tables
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return []


async def create_tables():
    """Create all database tables"""
    print("\n🏗️  Creating database tables...")
    try:
        async with async_engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


async def verify_user_table():
    """Verify the users table was created correctly"""
    print("\n🔍 Verifying users table...")
    try:
        async with async_engine.connect() as conn:
            # Check if users table exists
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            columns = list(result)
            
            if columns:
                print("✅ Users table structure:")
                for col_name, data_type in columns:
                    print(f"   - {col_name}: {data_type}")
                return True
            else:
                print("❌ Users table not found")
                return False
    except Exception as e:
        print(f"❌ Error verifying users table: {e}")
        return False


async def create_test_user():
    """Create a test user for authentication testing"""
    print("\n👤 Creating test user...")
    try:
        from app.core.security import get_password_hash
        
        async with async_engine.begin() as conn:
            # Check if test user already exists
            result = await conn.execute(text("""
                SELECT id FROM users WHERE email = 'testme@gmail.com';
            """))
            existing_user = result.first()
            
            if existing_user:
                print("ℹ️  Test user already exists")
                return True
            
            # Create test user
            hashed_password = get_password_hash("testpassword123")
            
            await conn.execute(text("""
                INSERT INTO users (email, password_hash, full_name, is_active)
                VALUES (:email, :password_hash, :full_name, :is_active)
            """), {
                "email": "testme@gmail.com",
                "password_hash": hashed_password,
                "full_name": "Test User",
                "is_active": True
            })
            
            print("✅ Test user created:")
            print("   Email: testme@gmail.com")
            print("   Password: testpassword123")
            return True
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False


async def main():
    """Main initialization function"""
    print("=" * 60)
    print("🚀 PsychSync Database Initialization")
    print("=" * 60)
    
    # Step 1: Check database connection
    if not await check_database_connection():
        print("\n❌ Cannot proceed without database connection")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure PostgreSQL is running:")
        print("      brew services start postgresql@14")
        print("   2. Check your DATABASE_URL in .env file")
        print("   3. Verify database credentials")
        return False
    
    # Step 2: Check existing tables
    existing_tables = await check_tables_exist()
    
    # Step 3: Create tables if they don't exist
    if not existing_tables or 'users' not in existing_tables:
        print("\n⚠️  Tables need to be created")
        if not await create_tables():
            print("\n❌ Failed to create tables")
            return False
    else:
        print("\n✅ Tables already exist")
    
    # Step 4: Verify critical tables
    if not await verify_user_table():
        print("\n❌ Users table verification failed")
        return False
    
    # Step 5: Create test user
    if not await create_test_user():
        print("\n⚠️  Could not create test user (non-critical)")
    
    # Final check
    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print("\n🎉 You can now start the application:")
    print("   uvicorn app.main:app --reload")
    print("\n📝 Test credentials:")
    print("   Email: testme@gmail.com")
    print("   Password: testpassword123")
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        