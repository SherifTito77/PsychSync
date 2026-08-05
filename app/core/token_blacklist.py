"""
Token blacklist utilities using Redis atomic operations.
Lives in core/ so auth modules don't need to import from services/.
"""

import redis.asyncio as aioredis

from app.core.config import settings


async def blacklist_token(token: str, expiry_seconds: int = 3600) -> None:
    """Add token to Redis blacklist. Atomic SETEX — thread-safe."""
    redis_client = await aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    try:
        await redis_client.setex(f"blacklist:{token}", expiry_seconds, "1")
    finally:
        await redis_client.close()


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted. Atomic EXISTS — thread-safe."""
    redis_client = await aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    try:
        result = await redis_client.exists(f"blacklist:{token}")
        return result == 1
    finally:
        await redis_client.close()
