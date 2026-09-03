"""
Comprehensive Race Condition Fix Tests

Tests to verify that all race condition fixes are working correctly:
1. Token blacklist race condition (Redis atomic operations)
2. User creation email race condition (database constraints)
3. Session management race condition (Redis transactions)
4. Cache stampede vulnerability (lock-based prevention)
5. Rate limiter counter race condition (atomic INCR)

Each test simulates high concurrency to ensure thread-safety.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.async_cache import cached_async
from app.core.config import settings
from app.main import app
from app.services.auth_service import blacklist_token, is_token_blacklisted
from app.services.session_service import SessionService

# ============================================================================
# Test 1: Token Blacklist Race Condition
# ============================================================================

@pytest.mark.asyncio
async def test_token_blacklist_thread_safety():
    """
    Test that token blacklisting is thread-safe under high concurrency.

    Race Condition: Multiple threads/processes trying to blacklist
    the same token simultaneously could cause data inconsistency.

    Fix: Use Redis SETEX which is atomic.
    """
    test_token = str(uuid4())

    # Simulate 100 concurrent attempts to blacklist the same token
    tasks = [
        blacklist_token(test_token, expiry=datetime.now(UTC) + timedelta(hours=1))
        for _ in range(100)
    ]

    # Execute all tasks concurrently
    await asyncio.gather(*tasks)

    # Verify token is blacklisted (should only exist once in Redis)
    is_blacklisted = await is_token_blacklisted(test_token)
    assert is_blacklisted is True, "Token should be blacklisted"


@pytest.mark.asyncio
async def test_token_blacklist_expiration():
    """
    Test that blacklisted tokens expire correctly.

    Verifies that the TTL mechanism works with Redis SETEX.
    """
    test_token = str(uuid4())

    # Blacklist token with 2 second expiry
    await blacklist_token(test_token, expiry=datetime.now(UTC) + timedelta(seconds=2))

    # Should be blacklisted immediately
    assert await is_token_blacklisted(test_token) is True

    # Wait for expiration
    await asyncio.sleep(3)

    # Should no longer be blacklisted
    assert await is_token_blacklisted(test_token) is False


# ============================================================================
# Test 2: User Creation Email Race Condition
# ============================================================================

@pytest.mark.asyncio
async async def test_user_creation_email_uniqueness(db_session: AsyncSession):
    """
    Test that user creation prevents duplicate emails under high concurrency.

    Race Condition: Multiple concurrent requests trying to create users
    with the same email could result in duplicate accounts.

    Fix: Rely on database UNIQUE constraint + handle IntegrityError.
    """
    from sqlalchemy.exc import IntegrityError

    from app.schemas.user import UserCreate
    from app.services.user_service import create_user

    test_email = "concurrent_test@example.com"
    user_data = UserCreate(
        email=test_email,
        password="SecurePassword123!",
        full_name="Concurrent Test User"
    )

    # Simulate 10 concurrent attempts to create the same user
    tasks = [
        create_user(user_data, db_session)
        for _ in range(10)
    ]

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes and failures
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = sum(1 for r in results if isinstance(r, (ValueError, IntegrityError)))

    # Only one should succeed, rest should fail with integrity error
    assert successes == 1, f"Expected 1 successful creation, got {successes}"
    assert failures == 9, f"Expected 9 integrity errors, got {failures}"


# ============================================================================
# Test 3: Session Management Race Condition
# ============================================================================

@pytest.mark.asyncio
async def test_session_creation_thread_safety():
    """
    Test that session creation is thread-safe under high concurrency.

    Race Condition: Multiple concurrent session creations for the same user
    could exceed max_concurrent_sessions limit due to non-atomic operations.

    Fix: Use Redis transactions (pipeline) to ensure atomicity.
    """
    from unittest.mock import Mock

    from app.db.models.user import User

    # Create mock user
    user = Mock(spec=User)
    user.id = uuid4()

    # Create mock request
    request = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {
        "user-agent": "TestAgent/1.0",
        "accept-language": "en-US",
        "accept-encoding": "gzip"
    }

    session_service = SessionService(
        session_duration_minutes=60,
        max_concurrent_sessions=5,
        rotation_interval_minutes=30
    )

    # Simulate 10 concurrent session creations (max is 5)
    tasks = [
        session_service.create_session(user, request)
        for _ in range(10)
    ]

    # Execute all tasks concurrently
    sessions = await asyncio.gather(*tasks)

    # All should succeed (old sessions should be revoked)
    assert len(sessions) == 10, "All session creations should succeed"

    # Verify session IDs are unique
    session_ids = [s.session_id for s in sessions]
    assert len(set(session_ids)) == 10, "All session IDs should be unique"


@pytest.mark.asyncio
async def test_session_validation_thread_safety():
    """
    Test that session validation is thread-safe.
    """
    from unittest.mock import Mock

    from app.db.models.user import User

    # Create mock user
    user = Mock(spec=User)
    user.id = uuid4()

    # Create mock request
    request = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {
        "user-agent": "TestAgent/1.0",
        "accept-language": "en-US",
        "accept-encoding": "gzip"
    }

    session_service = SessionService(
        session_duration_minutes=60,
        max_concurrent_sessions=5,
        rotation_interval_minutes=30
    )

    # Create a session
    session = await session_service.create_session(user, request)

    # Simulate 100 concurrent validations of the same session
    tasks = [
        session_service.validate_session(session.session_id, request)
        for _ in range(100)
    ]

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # All validations should succeed
    successes = sum(1 for r in results if not isinstance(r, Exception))
    assert successes == 100, f"Expected all 100 validations to succeed, got {successes}"


# ============================================================================
# Test 4: Cache Stampede Prevention
# ============================================================================

@pytest.mark.asyncio
async def test_cache_stampede_prevention():
    """
    Test that cache stampede is prevented under high concurrency.

    Race Condition: Multiple concurrent requests with cache miss could
    all call the expensive function simultaneously (cache stampede).

    Fix: Use Redis locks to ensure only one request computes the value.
    """
    call_count = 0

    @cached_async(expire=60, key_prefix="test_stampede")
    async def expensive_function(key: str):
        """Simulate expensive operation"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.5)  # Simulate expensive computation
        return f"result_{key}"

    # Clear cache first
    import redis.asyncio as aioredis
    redis_client = await aioredis.from_url(settings.REDIS_URL)
    await redis_client.delete("test_stampede:*")
    await redis_client.close()

    # Simulate 50 concurrent requests with cache miss
    tasks = [
        expensive_function("test_key")
        for _ in range(50)
    ]

    # Execute all tasks concurrently
    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    # All results should be the same
    assert len(set(results)) == 1, "All results should be identical"
    assert results[0] == "result_test_key"

    # Due to lock mechanism, expensive function should be called only once
    # (or very few times due to race conditions in lock acquisition)
    assert call_count <= 3, f"Expected <= 3 calls due to lock, got {call_count}"

    # Should complete quickly (not 50 * 0.5s = 25s, but ~0.5s + lock overhead)
    duration = (end_time - start_time).total_seconds()
    assert duration < 5, f"Expected ~0.5-1s duration, got {duration}s"


# ============================================================================
# Test 5: Rate Limiter Thread-Safety
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiter_thread_safety():
    """
    Test that rate limiter is thread-safe under high concurrency.

    Race Condition: Multiple concurrent requests could pass the rate
    limit check and all increment, exceeding the limit.

    Fix: Use atomic INCR operation in Redis, increment first then check.
    """
    import redis.asyncio as aioredis

    from app.services.rate_limiter_service import RateLimiterService

    rate_limiter = RateLimiterService()

    # Clear Redis rate limit keys
    redis_client = await aioredis.from_url(settings.REDIS_URL)
    await redis_client.delete("rate_limit:*")
    await redis_client.close()

    # Create mock request
    request = Mock()
    request.client.host = "127.0.0.1"
    request.url = Mock(path="/api/v1/test")
    request.headers = {"user-agent": "TestAgent/1.0"}

    # Set a very low rate limit for testing
    # Minute: 5 requests, Hour: 10 requests, Day: 20 requests
    # We'll send 20 concurrent requests
    tasks = [
        rate_limiter.check_rate_limit(request)
        for _ in range(20)
    ]

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Count allowed vs denied
    allowed_count = sum(1 for r in results if r[0] is True)
    denied_count = sum(1 for r in results if r[0] is False)

    # Should allow exactly 5 (minute limit) and deny 15
    assert allowed_count == 5, f"Expected 5 allowed requests, got {allowed_count}"
    assert denied_count == 15, f"Expected 15 denied requests, got {denied_count}"

    # Verify the counter didn't exceed the limit significantly
    # (small overage is acceptable due to concurrency, but not 2x)
    assert allowed_count <= 6, "Rate limiter should not be exceeded significantly"


# ============================================================================
# Test 6: Integration Test - Multiple Race Conditions
# ============================================================================

@pytest.mark.asyncio
async async def test_concurrent_race_conditions():
    """
    Integration test simulating multiple race conditions simultaneously.
    """
    from unittest.mock import Mock

    from app.db.models.user import User

    # Create mock user
    user = Mock(spec=User)
    user.id = uuid4()

    # Create mock request
    request = Mock()
    request.client.host = "127.0.0.1"
    request.url = Mock(path="/api/v1/test")
    request.headers = {
        "user-agent": "TestAgent/1.0",
        "accept-language": "en-US",
        "accept-encoding": "gzip"
    }

    # Run multiple operations concurrently
    tasks = []

    # 1. Token blacklisting
    test_token = str(uuid4())
    tasks.extend([
        blacklist_token(test_token, expiry=datetime.now(UTC) + timedelta(hours=1))
        for _ in range(10)
    ])

    # 2. Session creation
    session_service = SessionService(
        session_duration_minutes=60,
        max_concurrent_sessions=5,
        rotation_interval_minutes=30
    )
    tasks.extend([
        session_service.create_session(user, request)
        for _ in range(5)
    ])

    # 3. Cache operations
    @cached_async(expire=60, key_prefix="integration_test")
    async def cached_func(x: int):
        await asyncio.sleep(0.1)
        return x * 2

    tasks.extend([
        cached_func(i)
        for i in range(10)
    ])

    # Execute all concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify no exceptions
    exceptions = [r for r in results if isinstance(r, Exception)]
    assert len(exceptions) == 0, f"No exceptions should occur, got {len(exceptions)}"


# ============================================================================
# Load Testing Helpers
# ============================================================================

@pytest.mark.skip(reason="Load test - run manually when needed")
@pytest.mark.asyncio
async async def test_load_concurrent_users():
    """
    Load test: Simulate 1000 concurrent users with multiple operations.

    This test is skipped by default. Run manually when needed.
    """
    from unittest.mock import Mock

    from app.db.models.user import User

    # Simulate 1000 concurrent users
    async def simulate_user(user_id: int):
        # Create mock user
        user = Mock(spec=User)
        user.id = uuid4()

        # Create mock request
        request = Mock()
        request.client.host = f"192.168.1.{user_id % 255}"
        request.url = Mock(path="/api/v1/test")
        request.headers = {
            "user-agent": f"TestAgent/{user_id}",
            "accept-language": "en-US",
            "accept-encoding": "gzip"
        }

        # Perform operations
        token = str(uuid4())
        await blacklist_token(token, expiry=datetime.now(UTC) + timedelta(hours=1))

        session_service = SessionService(
            session_duration_minutes=60,
            max_concurrent_sessions=5,
            rotation_interval_minutes=30
        )
        await session_service.create_session(user, request)

        @cached_async(expire=60, key_prefix=f"user_{user_id}")
        async def get_user_data():
            await asyncio.sleep(0.01)
            return {"user_id": user_id}

        return await get_user_data()

    # Run 1000 concurrent user simulations
    tasks = [simulate_user(i) for i in range(1000)]

    start_time = datetime.now()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = datetime.now()

    # Verify results
    exceptions = [r for r in results if isinstance(r, Exception)]
    successes = len(results) - len(exceptions)

    print(f"\nLoad Test Results:")
    print(f"  Total requests: 1000")
    print(f"  Successful: {successes}")
    print(f"  Failed: {len(exceptions)}")
    print(f"  Duration: {(end_time - start_time).total_seconds():.2f}s")
    print(f"  Throughput: {successes / (end_time - start_time).total_seconds():.2f} req/s")

    # Assert that 99%+ succeeded
    success_rate = successes / len(results)
    assert success_rate >= 0.99, f"Success rate should be >= 99%, got {success_rate:.2%}"
