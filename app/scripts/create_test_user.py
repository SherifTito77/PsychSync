"""Create a test user for development"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.db.models.user import User
from app.core.security_fixes import hash_password


async def create_test_user():
    """Create a test user with known credentials"""
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == "admin@psychsync.test")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("✅ Test user already exists!")
            print("\nTest User Credentials:")
            print("  Email: admin@psychsync.test")
            print("  Password: TestPassword123!")
            return

        # Create test user
        password_hash = hash_password("TestPassword123!")

        user = User(
            email="admin@psychsync.test",
            password_hash=password_hash,
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            created_at=datetime.utcnow()
        )

        db.add(user)
        await db.commit()

        print("✅ Test user created successfully!")
        print("\nTest User Credentials:")
        print("  Email: admin@psychsync.test")
        print("  Password: TestPassword123!")
        print("\nYou can now log in at: http://localhost:5177/login")


if __name__ == "__main__":
    asyncio.run(create_test_user())
