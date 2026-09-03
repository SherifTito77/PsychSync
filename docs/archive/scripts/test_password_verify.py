#!/usr/bin/env python3
import asyncio
import sys

from sqlalchemy import create_engine, text

from app.core.config.settings import settings
from app.services.security import verify_password

# Create synchronous engine for getting password hash
db_url = (
    str(settings.DATABASE_URL)
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("postgresql+psycopg://", "postgresql://")
)
engine = create_engine(db_url)


async def test_password_verify():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, email, password_hash FROM users WHERE email = :email LIMIT 1"
                ),
                {"email": "sherif.tito.77@gmail.com"},
            )
            user = result.fetchone()
            if user:
                print(f"User found: {user.email}")
                print(f"Password hash present: {'Yes' if user.password_hash else 'No'}")
                if user.password_hash:
                    print(f"Password hash length: {len(user.password_hash)} chars")

                # Test password verification
                test_password = "test123"
                print(f"\nTesting password verification...")
                print(f"Test password: '{test_password}'")

                is_valid = await verify_password(test_password, user.password_hash)
                print(f"Password valid: {is_valid}")

            else:
                print("User NOT found in database")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_password_verify())
