#scripts/create_user.py   - Script to create a user in the database
import asyncio
from app.db.session import async_session
from app.db.models.user import User  # adjust import if your User model is elsewhere
from app.db.schemas.user import UserCreate  # your Pydantic schema
from app.core.security import get_password_hash  # if you have password hashing

async def main():
    async with async_session() as session:
        async with session.begin():
            # Replace with your details
            user_data = UserCreate(
                email="test@example.com",
                password="Test1234",
                full_name="Test User"
            )
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name
            )
            
            session.add(user)

        await session.commit()
        print("User created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
