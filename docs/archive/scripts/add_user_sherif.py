"""Add sherif.tito.77@gmail.com user to database"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security_fixes import hash_password


async def add_sherif_user():
    """Add sherif user directly to database"""

    # Database URL from environment
    db_url = "postgresql+asyncpg://psychsync_user:C8Vsywo9yXRQSOaGwxjVVQ-Secure9@localhost:5432/psychsync_db"

    # Create async engine
    engine = create_async_engine(db_url, echo=False)

    # Create async session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    email = "sherif.tito.77@gmail.com"
    password = "TestPassword123!"  # Using a default test password

    try:
        async with async_session() as session:
            # Check if user already exists
            result = await session.execute(
                text("SELECT id, email FROM users WHERE email = :email"),
                {"email": email},
            )
            existing_user = result.fetchone()

            if existing_user:
                print(f"✅ User {email} already exists!")
                print(f"   ID: {existing_user[0]}")
                return

            # Hash the password
            password_hash = hash_password(password)

            # Insert user
            await session.execute(
                text(
                    """
                    INSERT INTO users (email, password_hash, full_name, is_active, is_superuser, created_at, updated_at)
                    VALUES (:email, :password_hash, :full_name, :is_active, :is_superuser, :created_at, :updated_at)
                """
                ),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "full_name": "Sherif Tito",
                    "is_active": True,
                    "is_superuser": True,  # Making superuser for ease of access
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

            await session.commit()

            print(f"✅ User {email} created successfully!")
            print("\n📋 Login Credentials:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_sherif_user())
