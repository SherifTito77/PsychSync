#!/usr/bin/env python3
"""
Create a test user for the mobile app
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.db.models.user import User
from app.services.security.password_service import get_password_service


async def create_test_user():
    """Create a test user"""
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == "testuser@psychsync.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ User already exists: {existing_user.email}")
            print(f"   ID: {existing_user.id}")
            print(f"   Name: {existing_user.full_name}")
            return

        # Create new user
        password_service = get_password_service()
        password_hash = password_service.hash_password("PsychSync!2026")

        new_user = User(
            email="testuser@psychsync.com",
            full_name="Test User",
            hashed_password=password_hash,
            is_active=True,
            is_verified=False,  # Email not verified yet
        )

        session.add(new_user)
        await session.commit()

        print(f"✅ Test user created successfully!")
        print(f"   Email: testuser@psychsync.com")
        print(f"   Password: PsychSync!2026")
        print(f"   User ID: {new_user.id}")
        print(f"   Name: {new_user.full_name}")
        print(f"   Verified: {new_user.is_verified}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_user())
