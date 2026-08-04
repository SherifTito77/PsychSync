#!/usr/bin/env python3
"""Simple test user creator using raw SQL"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os

os.chdir(project_root)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async def create_test_user():
    """Create test user: admin@psychsync.test / TestPassword123!"""

    DATABASE_URL = settings.DATABASE_URL

    if "asyncpg" not in DATABASE_URL:
        print("✗ Error: DATABASE_URL must use asyncpg driver")
        print(f"  Current: {DATABASE_URL}")
        return

    print(f"✓ Connecting to database...")

    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            async with session.begin():
                # Check if user exists
                result = await session.execute(
                    text("SELECT id, email FROM users WHERE email = :email"),
                    {"email": "admin@psychsync.test"},
                )
                existing_user = result.fetchone()

                if existing_user:
                    print("✅ Test user already exists!")
                    print("\nTest User Credentials:")
                    print("  Email: admin@psychsync.test")
                    print("  Password: TestPassword123!")
                    return

                # Import password hashing after DB connection to avoid model issues
                from app.core.security import get_password_hash

                # Hash password
                password_hash = get_password_hash("TestPassword123!")
                print(f"✓ Password hashed")

                # Insert user
                result = await session.execute(
                    text(
                        """
                        INSERT INTO users (email, password_hash, full_name, is_active, is_superuser, created_at)
                        VALUES (:email, :password_hash, :full_name, :is_active, :is_superuser, NOW())
                        RETURNING id, email
                    """
                    ),
                    {
                        "email": "admin@psychsync.test",
                        "password_hash": password_hash,
                        "full_name": "Admin User",
                        "is_active": True,
                        "is_superuser": True,
                    },
                )

                user = result.fetchone()

                print("✅ Test user created successfully!")
                print("\nTest User Credentials:")
                print(f"  Email: {user[1]}")
                print("  Password: TestPassword123!")
                print(f"  User ID: {user[0]}")
                print(f"\n✓ Login at: http://localhost:5004/login")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(create_test_user())
