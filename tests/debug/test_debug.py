import asyncio

import redis.asyncio as redis

from app.core.enhanced_cache import get_cache_manager, init_cache


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    await init_cache(r)
    manager = get_cache_manager()
    print(f"Manager redis: {manager.redis}")
    # The error is 'coroutine' object has no attribute 'get' when calling manager.redis.get
    # If I just printed manager.redis, would it be a coroutine?

    # Let's inspect the object
    print(f"Manager redis type: {type(manager.redis)}")

    # Try to reproduce the 'coroutine' error
    try:
        # If manager.redis is a coroutine, then this will fail
        # But our test says it is Redis client.
        await manager.redis.get("test")
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")


asyncio.run(main())
