from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine("postgresql+asyncpg://psychsync_user@localhost/psychsync_db")

async def test():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT * FROM information_schema.tables WHERE table_schema='public';"))
        tables = await result.fetchall()
        print(tables)

import asyncio
asyncio.run(test())
