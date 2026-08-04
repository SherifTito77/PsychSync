import asyncio

import redis.asyncio as redis

from app.core.enhanced_cache import get_cache_manager, init_cache


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    await init_cache(r)
    manager = get_cache_manager()
    print(f"Manager redis type: {type(manager.redis)}")

    # Try calling get on the manager's redis directly
    try:
        val = await manager.redis.get("test")
        print(f"Result type: {type(val)}")
    except Exception as e:
        print(f"Error calling get: {e}")


asyncio.run(main())
