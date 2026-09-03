import asyncio

from sqlalchemy import select

from app.core.database import get_async_db
from app.db.models.user import User


async def verify_is_admin():
    async for db in get_async_db():
        email = "sherif.tito.77@gmail.com"
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            print(f"User: {user.email}")
            print(f"role: {user.role}")
            print(f"is_superuser: {user.is_superuser}")
            print(f"user.is_admin: {user.is_admin}")
            print(f"user.is_clinician: {user.is_clinician}")
        else:
            print("User not found")
        break


if __name__ == "__main__":
    asyncio.run(verify_is_admin())
