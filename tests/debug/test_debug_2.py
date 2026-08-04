import asyncio

import redis.asyncio as redis

from app.core.enhanced_cache import get_cache_manager, init_cache


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    await init_cache(r)
    manager = get_cache_manager()
    print(f"Manager type: {type(manager)}")
    # The error was 'coroutine' object has no attribute 'get'
    # This means when 'await cache.get(key)' was called, 'cache' was a coroutine.
    # How could 'cache' be a coroutine?
    # 'cache = get_cache_manager()'
    # If get_cache_manager() returned a coroutine, then 'cache' would be a coroutine.
    # But I checked, get_cache_manager() is a regular function returning _cache_manager.
    # Unless... _cache_manager itself is set to a coroutine?
    # _cache_manager = EnhancedCacheManager(redis_client)
    # This is a class instantiation, it returns an object.

    # Could it be an issue with how pytest runs async tests?


asyncio.run(main())
