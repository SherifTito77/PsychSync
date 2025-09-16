# backend/app/db/session.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from .base import Base


DATABASE_URL = os.getenv(
"DATABASE_URL",
"postgresql+asyncpg://psychsync_user@localhost/psychsync_db",
)


# Async engine for FastAPI
engine = create_async_engine(DATABASE_URL, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Convenience: sync engine (for Alembic autogenerate if you prefer run_sync)
# from sqlalchemy import create_engine
# sync_engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))