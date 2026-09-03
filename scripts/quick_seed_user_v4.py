import asyncio
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.db.models.organization import Organization
from app.db.models.user import User
from app.services.security import get_password_hash


async def seed():
    async with AsyncSessionLocal() as db:
        org = Organization(name="Test Org")
        db.add(org)
        await db.commit()
        print(f"Organization created: {org.id}")
        # Use a very specific, compliant password
        password = "EnterpriseSecurity!2026"
        user = User(
            email="testme@gmail.com",
            password_hash=get_password_hash(password),
            full_name="Test User",
            organization_id=org.id,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        await db.commit()
        print("User created successfully")


if __name__ == "__main__":
    asyncio.run(seed())
