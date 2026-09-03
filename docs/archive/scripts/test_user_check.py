#!/usr/bin/env python3
import sys

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
                "SELECT id, email, full_name, role, is_active, password_hash IS NOT NULL as has_password FROM users WHERE email = :email"
            ),
            {"email": "sherif.tito.77@gmail.com"},
        )
        user = result.fetchone()
        if user:
            print(
                f"User found: {user.email}, Role: {user.role}, Active: {user.is_active}, Has Password: {user.has_password}"
            )
        else:
            print("User NOT found in database")
except Exception as e:
    print(f"Database error: {type(e).__name__}: {e}")
finally:
    engine.dispose()
