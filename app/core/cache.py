# app/core/cache.py
import redis.asyncio as redis
from app.core.config import settings




# Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
)




# Async helpers
async def set_key(key: str, value: str, expire: int = 3600):
    """Set a key with optional expiration (default: 1 hour)."""
    await redis_client.set(key, value, ex=expire)

async def get_key(key: str):
    """Get a key value from Redis."""
    return await redis_client.get(key)


# Create a Redis client instance
redis_client = redis.Redis(
    host=getattr(settings, "REDIS_HOST", "localhost"),
    port=getattr(settings, "REDIS_PORT", 6379),
    db=0,
    decode_responses=True  # Makes get() return str instead of bytes
)

# Example async helper functions
async def set_key(key: str, value: str, expire: int = 3600):
    """Set a key with optional expiration (default: 1 hour)."""
    await redis_client.set(key, value, ex=expire)

async def get_key(key: str):
    """Retrieve a value by key."""
    return await redis_client.get(key)

async def delete_key(key: str):
    """Delete a key from Redis."""
    return await redis_client.delete(key)

