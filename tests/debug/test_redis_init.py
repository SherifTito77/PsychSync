import asyncio

import redis.asyncio as redis


async def test_redis_init():
    r = redis.Redis(host="localhost", port=6379, db=0)
    print(f"Redis type: {type(r)}")
    # The error says "coroutine object has no attribute 'get'"
    # This implies that self.redis is a COROUTINE (the result of an async call that wasn't awaited),
    # not the Redis client object itself.


async def test_coroutine_bug():
    # Simulate the bug
    async def get_client():
        await asyncio.sleep(0.1)
        return redis.Redis(host="localhost", port=6379, db=0)

    # Bug: assigning the coroutine directly instead of awaiting it
    self_redis = get_client()
    print(f"self_redis type: {type(self_redis)}")
    try:
        await self_redis.get("test")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(test_coroutine_bug())
