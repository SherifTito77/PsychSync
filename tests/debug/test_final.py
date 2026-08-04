import asyncio

import redis.asyncio as redis


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    print(f"Redis type: {type(r)}")
    val = await r.get("test")
    print(f"Result: {val}")


asyncio.run(main())
