#!/usr/bin/env python3
"""
Simple test user creation script
Creates test users directly using database connection
"""

import asyncio
import uuid
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.security import get_password_hash

async def create_simple_test_users():
    """Create test users using direct database connection"""

    print("🚀 Creating test users...")

    # Database URL from environment
    DATABASE_URL = "postgresql+asyncpg://psychsync_user:C8Vsywo9yXRQSOaGwxjVVQ-Secure9@localhost:5432/psychsync_db"

    try:
        # Create engine
        engine = create_async_engine(DATABASE_URL, echo=True)

        # Create session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Check if test user already exists and skip if it does
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "test@example.com"}
            )
            existing = result.fetchone()

            if existing:
                print("📋 Test user already exists, skipping creation...")
                print("✅ Test users already exist!")
                print("\n🔐 Test Login Credentials:")
                print("├── Email: test@example.com")
                print("│   Password: Test1234!")
                print("├── Email: admin@example.com")
                print("│   Password: Admin1234!")
                print("└── Email: user@example.com")
                print("    Password: User1234!")
                print("\n🎯 Use these credentials to test the login endpoint!")
                return

            # Create test users
            test_users = [
                {
                    "email": "test@example.com",
                    "password": "Test1234!",
                    "full_name": "Test User"
                },
                {
                    "email": "admin@example.com",
                    "password": "Admin1234!",
                    "full_name": "Admin User"
                },
                {
                    "email": "user@example.com",
                    "password": "User1234!",
                    "full_name": "Regular User"
                }
            ]

            for user_data in test_users:
                print(f"👤 Creating user: {user_data['email']}")

                user_id = uuid.uuid4()
                password_hash = get_password_hash(user_data["password"])

                await session.execute(
                    text("""
                        INSERT INTO users (id, email, password_hash, full_name, is_active, created_at, updated_at)
                        VALUES (:id, :email, :password_hash, :full_name, :is_active, NOW(), NOW())
                    """),
                    {
                        "id": user_id,
                        "email": user_data["email"],
                        "password_hash": password_hash,
                        "full_name": user_data["full_name"],
                        "is_active": True
                    }
                )

            await session.commit()
            print("✅ Test users created successfully!")
            print("\n🔐 Test Login Credentials:")
            print("├── Email: test@example.com")
            print("│   Password: Test1234!")
            print("├── Email: admin@example.com")
            print("│   Password: Admin1234!")
            print("└── Email: user@example.com")
            print("    Password: User1234!")
            print("\n🎯 Use these credentials to test the login endpoint!")

    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_simple_test_users())