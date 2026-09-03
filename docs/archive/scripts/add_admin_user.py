"""Add admin user to database - Direct SQL approach"""

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


async def add_admin_user():
    """Add admin user directly to database"""

    # Database URL from environment
    db_url = "postgresql+asyncpg://psychsync_user:C8Vsywo9yXRQSOaGwxjVVQ-Secure9@localhost:5432/psychsync_db"

    # Create async engine
    engine = create_async_engine(db_url, echo=False)

    # Create async session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Check if user already exists
            result = await session.execute(
                text("SELECT id, email FROM users WHERE email = :email"),
                {"email": "admin@psychsync.test"},
            )
            existing_user = result.fetchone()

            if existing_user:
                print("✅ Admin user already exists!")
                print(f"   ID: {existing_user[0]}")
                print(f"   Email: {existing_user[1]}")
                print("\n📋 Login Credentials:")
                print("   Email: admin@psychsync.test")
                print("   Password: TestPassword123!")
                return

            # Hash the password
            password_hash = hash_password("TestPassword123!")

            # Insert admin user
            await session.execute(
                text(
                    """
                    INSERT INTO users (email, password_hash, full_name, is_active, is_superuser, created_at, updated_at)
                    VALUES (:email, :password_hash, :full_name, :is_active, :is_superuser, :created_at, :updated_at)
                """
                ),
                {
                    "email": "admin@psychsync.test",
                    "password_hash": password_hash,
                    "full_name": "Admin User",
                    "is_active": True,
                    "is_superuser": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

            await session.commit()

            print("✅ Admin user created successfully!")
            print("\n📋 Login Credentials:")
            print("   Email: admin@psychsync.test")
            print("   Password: TestPassword123!")
            print("\n🌐 You can now log in at: http://localhost:5005/login")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_admin_user())
