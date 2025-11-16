
# app/db/init_db.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.db.session import async_session  # AsyncSession factory

# Load environment variables
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Async engine (optional if you want to use engine directly)
engine = create_async_engine(DB_URL, echo=True)


async def init_db():
    """
    Initialize database tables asynchronously.
    
    Uses the async session to run create_all in a synchronous context.
    """
    async with async_session() as session:
        async with session.begin():
            # Use run_sync to safely run sync code in async context
            await session.run_sync(
                lambda sync_session: Base.metadata.create_all(bind=sync_session.bind)
            )

