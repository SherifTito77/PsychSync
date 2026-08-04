import asyncio
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async def seed_org():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if default org exists
        result = await session.execute(
            text("SELECT id FROM organizations WHERE name = :name"),
            {"name": "default-org"},
        )
        org = result.fetchone()

        if org:
            print(f"✅ Organization 'default-org' exists with ID: {org[0]}")
        else:
            new_id = uuid4()
            await session.execute(
                text(
                    "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (:id, :name, datetime('now'), datetime('now'))"
                ),
                {"id": str(new_id), "name": "default-org"},
            )
            await session.commit()
            print(f"✅ Created organization 'default-org' with ID: {new_id}")


if __name__ == "__main__":
    asyncio.run(seed_org())
