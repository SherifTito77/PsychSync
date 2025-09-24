# # app/core/redis.py
# import redis.asyncio as redis
# from app.core.config import settings  # if you want to read host/port from .env

# # Create a Redis client instance
# redis_client = redis.Redis(
#     host="localhost",  # or settings.REDIS_HOST
#     port=6379,         # or settings.REDIS_PORT
#     db=0,
#     decode_responses=True  # optional, makes get() return str instead of bytes
# )




# # Example async helper functions
# async def set_key(key: str, value: str):
#     await redis_client.set(key, value)

# async def get_key(key: str):
#     return await redis_client.get(key)
