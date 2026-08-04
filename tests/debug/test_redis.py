import asyncio

import redis.asyncio as redis


async def main():
    r = redis.Redis(host="localhost", port=6379, db=0)
    print(f"Connection type: {type(r)}")
    print(f"Result type: {type(await r.get('test'))}")


asyncio.run(main())
