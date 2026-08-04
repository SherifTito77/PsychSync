#!/usr/bin/env python3
"""
Async test user creation script for PsychSync
Creates test users in the database using the new async database system
"""

import asyncio
import sys
import uuid

sys.path.insert(0, "/Users/sheriftito/Downloads/psychsync")

from sqlalchemy import select, text

from app.core.database import async_engine, get_async_db
from app.db.models.user import User
from app.services.security import get_password_hash


async def create_test_users():
    """Create test users for development/testing"""

    print("🚀 Creating test users...")

    try:
        async for db in get_async_db():
            # Check if test user already exists
            existing_user = await db.execute(
                select(User).where(User.email == "test@example.com")
            )
            existing = existing_user.scalar_one_or_none()

            if existing:
                print("📋 Deleting existing test user...")
                await db.delete(existing)
                await db.commit()

            # Create test users with different roles
            test_users = [
                {
                    "email": "test@example.com",
                    "password": "Test1234!",
                    "full_name": "Test User",
                    "is_active": True,
                },
                {
                    "email": "admin@example.com",
                    "password": "Admin1234!",
                    "full_name": "Admin User",
                    "is_active": True,
                },
                {
                    "email": "user@example.com",
                    "password": "User1234!",
                    "full_name": "Regular User",
                    "is_active": True,
                },
            ]

            for user_data in test_users:
                print(f"👤 Creating user: {user_data['email']}")

                new_user = User(
                    id=uuid.uuid4(),
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=user_data["is_active"],
                )

                db.add(new_user)

            await db.commit()

            print("✅ Test users created successfully!")
            print("\n🔐 Test Login Credentials:")
            print("├── Email: test@example.com")
            print("│   Password: Test1234!")
            print("├── Email: admin@example.com")
            print("│   Password: Admin1234!")
            print("└── Email: user@example.com")
            print("    Password: User1234!")
            print("\n🎯 Use these credentials to test the login endpoint!")

            break

    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_test_users())
