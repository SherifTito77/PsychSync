# scripts/check_and_create_user.py
import asyncio
import os
import sys
import uuid

from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.db.models.user import User


async def check_user():
    email = "sherif.tito.77@gmail.com"
    print(f"Checking for user: {email}")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            print(f"User {email} already exists.")
            # Optionally update password if needed
            # user.password_hash = get_password_hash("new_password")
            # await session.commit()
        else:
            print(f"User {email} not found. Creating...")
            new_user = User(
                id=uuid.uuid4(),
                email=email,
                username=email,
                password_hash=get_password_hash("password123"),  # Default password
                full_name="Sherif Tito",
                is_active=True,
                is_superuser=True,
            )
            session.add(new_user)
            await session.commit()
            print(f"User {email} created successfully with password: password123")


if __name__ == "__main__":
    asyncio.run(check_user())
