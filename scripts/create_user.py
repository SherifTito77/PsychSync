import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal
from app.db.models.user import User
import asyncio
from app.core.security import get_password_hash

async def main():
    # Create async session
    async with AsyncSessionLocal() as db:
        try:
            # Check if user exists
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == "admin@example.com"))
            existing = result.scalar_one_or_none()

            if existing:
                print("✅ User already exists")
                return

            # Create user
            user = User(
                email="admin@example.com",
                full_name="Admin User",
                password_hash=get_password_hash("admin123"),
                is_active=True
            )

            db.add(user)
            await db.commit()

            print("✅ Created user: admin@example.com / admin123")

        except Exception as e:
            print(f"❌ Error creating user: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())