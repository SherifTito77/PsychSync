# scripts/init_dev_db.py
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import Base, async_engine
from app.db.models import (  # Import models to ensure they are registered with Base
    refresh_token,
    team,
    team_member,
    user,
)


async def init_db():
    print("Initializing database...")
    async with async_engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
