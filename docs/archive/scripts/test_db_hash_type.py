#!/usr/bin/env python3
from sqlalchemy import create_engine, text

from app.core.config.settings import settings

# Create synchronous engine
db_url = (
    str(settings.DATABASE_URL)
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("postgresql+psycopg://", "postgresql://")
)
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT id, email, password_hash, pg_typeof(password_hash) as hash_type FROM users WHERE email = :email LIMIT 1"
            ),
            {"email": "sherif.tito.77@gmail.com"},
        )
        user = result.fetchone()
        if user:
            print(f"User found: {user.email}")
            print(f"Hash value: {user.password_hash[:50]}...")
            print(f"Hash type: {type(user.password_hash)}")
        else:
            print("User NOT found in database")
except Exception as e:
    print(f"Database error: {type(e).__name__}: {e}")
finally:
    engine.dispose()
