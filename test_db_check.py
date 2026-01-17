#!/usr/bin/env python3
# test_db_check.py - Database table verification

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, '/Users/sheriftito/Downloads/psychsync')

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_database_tables():
    """Check if required database tables exist"""

    print("🔍 Database Table Verification")
    print("============================")

    try:
        async with AsyncSessionLocal() as db:
            # Check if organizations table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'organizations'
                );
            """))
            org_exists = result.scalar()
            print(f"Organizations table exists: {org_exists}")

            # Check if teams table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'teams'
                );
            """))
            teams_exists = result.scalar()
            print(f"Teams table exists: {teams_exists}")

            # Check if users table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'users'
                );
            """))
            users_exists = result.scalar()
            print(f"Users table exists: {users_exists}")

            # Try to count organizations
            if org_exists:
                try:
                    result = await db.execute(text("SELECT COUNT(*) FROM organizations"))
                    org_count = result.scalar()
                    print(f"Organizations count: {org_count}")

                    # List all organizations
                    result = await db.execute(text("SELECT id, name FROM organizations"))
                    orgs = result.fetchall()
                    print("Organizations:")
                    for org in orgs:
                        print(f"  - {org[0]}: {org[1]}")

                except Exception as e:
                    print(f"Error querying organizations: {e}")

            # Try to count teams
            if teams_exists:
                try:
                    result = await db.execute(text("SELECT COUNT(*) FROM teams"))
                    teams_count = result.scalar()
                    print(f"Teams count: {teams_count}")
                except Exception as e:
                    print(f"Error querying teams: {e}")

            # Try to create a test organization
            if org_exists and not org_exists or True:  # Always try to create one
                try:
                    await db.execute(text("""
                        INSERT INTO organizations (id, name, created_at, updated_at)
                        VALUES (gen_random_uuid(), 'Default Organization', NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """))
                    await db.commit()
                    print("✅ Default organization created successfully")
                except Exception as e:
                    print(f"❌ Error creating default organization: {e}")
                    # Try alternative UUID generation
                    try:
                        await db.execute(text("""
                            INSERT INTO organizations (id, name, created_at, updated_at)
                            VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Default Organization', NOW(), NOW())
                            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                        """))
                        await db.commit()
                        print("✅ Default organization created with explicit UUID")
                    except Exception as e2:
                        print(f"❌ Error creating organization with explicit UUID: {e2}")

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

    print("\n✅ Database check completed")
    return True

if __name__ == "__main__":
    asyncio.run(check_database_tables())
