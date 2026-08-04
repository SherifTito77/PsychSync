import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def check_user():
    db_url = "postgresql+asyncpg://psychsync_user:C8Vsywo9yXRQSOaGwxjVVQ-Secure9@localhost:5432/psychsync_db"
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    email = "sherif.tito.77@gmail.com"

    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT id, email, role, is_superuser, is_active FROM users WHERE email = :email"
            ),
            {"email": email},
        )
        user = result.fetchone()

        if user:
            print(f"User found: {user.email}")
            print(f"ID: {user.id}")
            print(f"Role: {user.role}")
            print(f"Is Superuser: {user.is_superuser}")
            print(f"Is Active: {user.is_active}")
        else:
            print(f"User {email} not found.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_user())
