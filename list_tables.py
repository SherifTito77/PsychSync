import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Get URL from env or fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://psychsync_user@localhost/psychsync_db"
)

async def list_tables():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.connect() as conn:
        # Use text() for raw SQL
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
        """))
        tables = [row[0] for row in result.fetchall()]
        print("Tables in DB:", tables)

if __name__ == "__main__":
    asyncio.run(list_tables())






# # list_tables.py
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy import inspect
# import asyncio

# # Update this URL to match your PostgreSQL credentials
# DATABASE_URL = "postgresql+asyncpg://psychsync_user@localhost/psychsync_db"

# async def list_tables():
#     engine = create_async_engine(DATABASE_URL, echo=True)
    
#     async with engine.begin() as conn:
#         inspector = inspect(conn.sync_engine)  # sync inspector works here
#         tables = inspector.get_table_names()
#         print("Tables in the database:")
#         for table in tables:
#             print(" -", table)
    
#     await engine.dispose()

# if __name__ == "__main__":
#     asyncio.run(list_tables())
