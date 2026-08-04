import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models.organization import Organization


async def list_orgs():
    print(f"Connecting to: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(Organization))
        orgs = result.scalars().all()
        if not orgs:
            print("No organizations found in database.")
        for org in orgs:
            print(f"ID: {org.id}, Name: {org.name}")


if __name__ == "__main__":
    asyncio.run(list_orgs())
