#!/usr/bin/env python3
"""Test Redis connection for infrastructure validation"""

import asyncio
import sys
from app.core.config import settings

async def test_redis():
    try:
        # Try to import and test Redis
        try:
            import redis.asyncio as redis
        except ImportError:
            import aioredis as redis

        # Create Redis client
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )

        # Test connection
        await redis_client.ping()
        await redis_client.close()

        print("✅ Redis Connected")
        return 0

    except Exception as e:
        print(f"❌ Redis Failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_redis())
    sys.exit(exit_code)