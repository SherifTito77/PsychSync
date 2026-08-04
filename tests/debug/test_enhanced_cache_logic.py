import asyncio

import redis.asyncio as redis

from app.core.enhanced_cache import get_cache_manager, init_cache


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    await init_cache(r)
    manager = get_cache_manager()

    # Try calling get on the manager itself
    try:
        val = await manager.get("test")
        print(f"Result type: {type(val)}")
    except Exception as e:
        print(f"Error calling get on manager: {e}")
        import traceback

        traceback.print_exc()


asyncio.run(main())
