import asyncio

import redis.asyncio as redis

from app.core.cache import cache_get
from app.core.enhanced_cache import init_cache


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    await init_cache(r)
    try:
        val = await cache_get("test")
        print(f"Result: {val}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


asyncio.run(main())
