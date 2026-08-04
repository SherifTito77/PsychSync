import asyncio
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.db.models.user import User
from app.services.security import get_password_hash


async def add_user():
    async with AsyncSessionLocal() as db:
        user = User(
            email="sherif.tito.77@gmail.com",
            password_hash=get_password_hash(
                "ComplexPassword123!@#"
            ),  # Ensure it meets complexity requirements
            full_name="Sherif Tito",
            organization_id="6cefc5c1-7401-49ae-8906-9c532e8b4407",  # Use existing Org ID
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        await db.commit()
        print("User created successfully")


if __name__ == "__main__":
    asyncio.run(add_user())
