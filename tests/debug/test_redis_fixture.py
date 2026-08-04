import asyncio

import pytest
import redis.asyncio as redis


@pytest.fixture
async def redis_client():
    r = redis.Redis(host="localhost", port=6379, db=0)
    return r


@pytest.mark.asyncio
async def test_redis_type(redis_client):
    print(f"Type in test: {type(redis_client)}")
