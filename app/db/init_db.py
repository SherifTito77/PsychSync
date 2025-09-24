
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


# #app/init_db.py

# # app/db/init_db.py
# import os
# from sqlalchemy.ext.asyncio import create_async_engine
# from dotenv import load_dotenv
# from app.db.base import Base


# from app.db.session import async_session  # your async session


# load_dotenv()

# DB_URL = os.getenv("DATABASE_URL")
# if not DB_URL:
#     raise ValueError("DATABASE_URL environment variable is not set")

# engine = create_async_engine(DB_URL, echo=True)

# async def init_db():
#     """Initialize database tables asynchronously."""
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


# # If using SQLAlchemy 2.0 Async API
# from app.db.session import async_session

# async def init_db():
#     async with async_session() as session:
#         async with session.begin():
#             # Create tables
#             await session.run_sync(Base.metadata.create_all)


# # async def init_db():
# #     """
# #     Initialize database tables asynchronously.
# #     """
# #     async with async_session() as session:
# #         # run_sync ensures the sync operation (create_all) runs safely in async context
# #         await session.run_sync(Base.metadata.create_all)


# # # app/create_db.py
# # from app.db.models import Base
# # from sqlalchemy import create_engine
# # import os

# # from app.db.session import engine
# # from app.db.base import Base
# #   # import all models so Base.metadata sees them
# # from dotenv import load_dotenv

# # load_dotenv()
# # DB_URL = os.getenv("DATABASE_URL")  # Get the actual value

# # engine = create_engine(DB_URL, echo=True)

# # def init_db():
# #     Base.metadata.create_all(bind=engine)

# # # Path to your DATABASE_URL database
# # DB_PATH = os.path.join(os.path.dirname(__file__), "data", "psychsync.db")
# # DB_URL = f"DATABASE_URL:///{DB_PATH}"

# # # Create engine
# # engine = create_engine(DB_URL, echo=True)

# # # Create all tables
# # Base.metadata.create_all(engine)

# # print(f"Database created at {DB_PATH}")
