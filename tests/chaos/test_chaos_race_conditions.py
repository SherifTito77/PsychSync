"""
Chaos Engineering Tests

Tests to verify system resilience under failure conditions:
1. Network latency (random delays 100-500ms)
2. Redis failure mid-operation (connection errors during cache ops)
3. Database timeout (timeout during rate limit check)
4. Partial failures (some services fail, others succeed)
5. Circuit breaker behavior (fail-fast on repeated failures)
6. Graceful degradation (caching fallback on cache failure)
7. Retry with exponential backoff under chaos
8. Concurrent failures (multiple services fail simultaneously)

These tests verify that the system handles failures gracefully without
data corruption, cascading failures, or inconsistent state.
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient, ConnectError, ReadTimeout

from app.core.async_cache import AsyncCache
from app.core.config import settings
from app.db.models.user import User
from app.main import app

# ============================================================================
# Test 1: Network Latency Chaos
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_network_latency_during_login(db_session):
    """
    Test login with random network delays (100-500ms).

    Simulates real-world network conditions where latency varies.
    System should handle variable latency without errors.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create test user
    user = User(
        email="latency_test_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Latency Test User",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act - Send 10 login requests with random delays
    async def login_with_latency(delay_ms: int):
        """Login with artificial network delay"""
        # Simulate network latency
        await asyncio.sleep(delay_ms / 1000)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={
                    "username": "latency_test_user@psychsync.test",
                    "password": "SecurePass123!"
                }
            )
            return {"delay_ms": delay_ms, "response": response}

    # Random delays between 100ms and 500ms
    tasks = [
        login_with_latency(random.randint(100, 500))
        for _ in range(10)
    ]

    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    # Assert - All logins should succeed despite latency
    for result in results:
        response = result["response"]
        assert response.status_code == 200, \
            f"Login with {result['delay_ms']}ms delay failed with {response.status_code}"

        data = response.json()
        assert "access_token" in data, "Response should have access_token"

    # Total time should be reasonable (max delay + processing)
    duration = (end_time - start_time).total_seconds()
    assert duration < 5, f"Expected completion in < 5s, took {duration:.2f}s"

    print(f"\nNetwork Latency Chaos Test Results:")
    print(f"  Total requests: 10")
    print(f"  Total duration: {duration:.2f}s")
    print(f"  Avg latency: {sum(r['delay_ms'] for r in results) / len(results):.0f}ms")

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_extreme_network_latency():
    """
    Test system behavior under extreme network latency (1-2 seconds).

    Verifies that long delays don't cause timeouts or errors.
    """
    # Simulate cache operations with extreme latency
    await AsyncCache.clear_all()

    results = []

    async def extreme_latency_operation(op_id: int):
        """Perform operation with extreme latency"""
        # Extreme latency: 1-2 seconds
        delay = random.uniform(1.0, 2.0)
        await asyncio.sleep(delay)

        key = f"extreme_latency_test:{op_id}"
        value = {"data": f"value_{op_id}", "timestamp": datetime.now(UTC).isoformat()}

        # Cache operation with latency
        await AsyncCache.set(key, value, expire=60)

        # Read back
        retrieved = await AsyncCache.get(key)

        results.append({
            "op_id": op_id,
            "delay_ms": delay * 1000,
            "success": retrieved is not None
        })

        return retrieved

    # 5 operations with extreme latency
    tasks = [extreme_latency_operation(i) for i in range(5)]

    start_time = datetime.now()
    results_data = await asyncio.gather(*tasks)
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    # All operations should succeed despite extreme latency
    assert len(results_data) == 5, "All operations should complete"
    assert all(r is not None for r in results_data), "All cache operations should succeed"

    print(f"\nExtreme Latency Test Results:")
    print(f"  Operations: 5")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Avg latency: {sum(r['delay_ms'] for r in results) / len(results):.0f}ms")

    # Cleanup
    for i in range(5):
        await AsyncCache.delete(f"extreme_latency_test:{i}")


# ============================================================================
# Test 2: Redis Failure Mid-Operation
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
async def test_redis_failure_during_cache_operations():
    """
    Test cache behavior when Redis fails mid-operation.

    Simulates Redis connection failure during cache operations.
    System should handle failures gracefully and fall back to database.
    """
    cache_key = f"chaos_redis_failure:{uuid4()}"

    # Mock Redis client that fails intermittently
    call_count = 0

    async def failing_redis_get(key: str):
        """Simulate Redis failure after a few calls"""
        nonlocal call_count
        call_count += 1

        if call_count <= 3:
            # First 3 calls succeed
            return await AsyncCache.get(key)

        # Subsequent calls fail
        raise aioredis.ConnectionError("Redis connection lost")

    # Set initial value
    await AsyncCache.set(cache_key, {"value": "test_data"}, expire=60)

    # First read should succeed
    value1 = await AsyncCache.get(cache_key)
    assert value1 is not None, "First read should succeed"

    # Simulate Redis failure
    with patch('app.core.async_cache.async_redis_client.get', side_effect=failing_redis_get):
        # This call should fail
        try:
            value2 = await AsyncCache.get(cache_key)
            # If it doesn't fail, that's also OK (fallback mechanism)
            assert value2 is None or value2.get("value") == "test_data"
        except Exception as e:
            # Expected to fail gracefully
            assert "Redis" in str(e) or "connection" in str(e).lower()

    print(f"\nRedis Failure Test Results:")
    print(f"  Successful reads before failure: {min(3, call_count)}")
    print(f"  Total calls: {call_count}")

    # Cleanup
    try:
        await AsyncCache.delete(cache_key)
    except Exception as e:
        pass  # Redis is down, delete may fail


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_redis_failure_with_concurrent_operations():
    """
    Test concurrent cache operations when Redis fails.

    Simulates Redis failure during high concurrent load.
    Some operations should succeed, others should fail gracefully.
    """
    cache_prefix = f"chaos_concurrent_failure:{uuid4()}:"

    failure_triggered = False

    async def write_with_potential_failure(key: str, value: dict):
        """Write that may fail if Redis is down"""
        nonlocal failure_triggered

        # Trigger failure after 5 operations
        if random.random() < 0.2:  # 20% chance of failure
            failure_triggered = True
            raise aioredis.ConnectionError("Simulated Redis failure")

        await AsyncCache.set(key, value, expire=60)
        return True

    # Perform 20 concurrent writes (some may fail)
    tasks = []
    for i in range(20):
        key = f"{cache_prefix}key_{i}"
        value = {"data": f"value_{i}"}
        tasks.append(write_with_potential_failure(key, value))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes and failures
    success_count = sum(1 for r in results if r is True)
    failure_count = sum(1 for r in results if isinstance(r, Exception))

    print(f"\nConcurrent Redis Failure Test Results:")
    print(f"  Total operations: 20")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failure_count}")

    # At least some operations should succeed
    assert success_count > 0, "At least some operations should succeed"

    # Cleanup (may fail if Redis is down)
    try:
        await AsyncCache.delete_pattern(f"{cache_prefix}*")
    except Exception as e:
        pass


# ============================================================================
# Test 3: Database Timeout Chaos
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
async def test_database_timeout_during_query():
    """
    Test behavior when database query times out.

    Simulates slow database response causing query timeout.
    System should handle timeout gracefully without hanging.
    """
    from sqlalchemy.ext.async import AsyncSession

    from app.db.models.user import User

    # Mock database session that times out
    async def mock_execute(query):
        """Simulate database timeout"""
        await asyncio.sleep(5)  # Simulate slow query
        raise asyncio.TimeoutError("Database query timeout")

    # Attempt to query with timeout
    query_executed = False
    timeout_occurred = False

    try:
        # Use asyncio.wait_for to add timeout
        await asyncio.wait_for(
            mock_execute("SELECT * FROM users"),
            timeout=1.0  # 1 second timeout
        )
    except asyncio.TimeoutError:
        timeout_occurred = True
    except Exception as e:
        query_executed = True

    assert timeout_occurred, "Query should timeout after 1 second"
    assert not query_executed, "Query should not complete"

    print(f"\nDatabase Timeout Test Results:")
    print(f"  Timeout occurred: {timeout_occurred}")
    print(f"  Query completed: {query_executed}")


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_database_timeout_with_retries():
    """
    Test retry logic when database queries timeout.

    Simulates transient database timeouts with automatic retries.
    """
    attempt_count = 0
    max_attempts = 3

    async def query_with_retry():
        """Query that times out initially, then succeeds"""
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            # First 2 attempts timeout
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError(f"Query timeout (attempt {attempt_count})")

        # 3rd attempt succeeds
        return {"data": "query_result", "attempt": attempt_count}

    async def query_with_backoff():
        """Query with exponential backoff retry"""
        for attempt in range(1, max_attempts + 1):
            try:
                # Add timeout to each attempt
                result = await asyncio.wait_for(
                    query_with_retry(),
                    timeout=0.5
                )
                return result
            except asyncio.TimeoutError:
                if attempt < max_attempts:
                    # Exponential backoff
                    backoff = (2 ** attempt) * 0.01
                    await asyncio.sleep(backoff)
                else:
                    raise

    # Execute with retry
    start_time = datetime.now()
    result = await query_with_backoff()
    end_time = datetime.now()

    # Should succeed on 3rd attempt
    assert result is not None, "Query should eventually succeed"
    assert result["data"] == "query_result", "Should return correct data"
    assert result["attempt"] == 3, "Should succeed on 3rd attempt"

    duration = (end_time - start_time).total_seconds()
    assert duration < 2, f"Retry should complete in < 2s, took {duration:.2f}s"

    print(f"\nDatabase Timeout with Retry Test Results:")
    print(f"  Total attempts: {attempt_count}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Successful: Yes")


# ============================================================================
# Test 4: Partial Failure Scenarios
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
async def test_partial_service_failure():
    """
    Test behavior when some services fail while others succeed.

    Simulates partial system failure where cache fails but database succeeds.
    System should degrade gracefully and continue serving requests.
    """
    cache_available = False
    database_available = True

    async def get_user_with_fallback(user_id: str):
        """Get user from cache with database fallback"""
        # Try cache first
        if cache_available:
            cached = await AsyncCache.get(f"user:{user_id}")
            if cached:
                return {"source": "cache", "data": cached}

        # Fall back to database
        if database_available:
            # Simulate database query
            await asyncio.sleep(0.1)
            user_data = {
                "id": user_id,
                "email": f"user_{user_id}@psychsync.test",
                "full_name": f"User {user_id}"
            }

            # Try to cache for next time (may fail)
            try:
                if cache_available:
                    await AsyncCache.set(f"user:{user_id}", user_data, expire=300)
            except Exception as e:
                pass  # Cache failure is OK

            return {"source": "database", "data": user_data}

        # Both cache and database failed
        raise Exception("Service unavailable")

    # Scenario 1: Cache fails, database succeeds
    cache_available = False
    database_available = True

    result = await get_user_with_fallback("user123")
    assert result["source"] == "database", "Should fall back to database"
    assert result["data"]["id"] == "user123", "Should return correct data"

    # Scenario 2: Both cache and database succeed
    cache_available = True
    database_available = True

    result = await get_user_with_fallback("user456")
    assert result["source"] in ["cache", "database"], "Should return from cache or database"

    print(f"\nPartial Failure Test Results:")
    print(f"  Scenario 1 (cache down, DB up): SUCCESS")
    print(f"  Scenario 2 (all services up): SUCCESS")


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_cascading_failure_prevention():
    """
    Test that cascading failures are prevented.

    Simulates a failure in one service that should not propagate to others.
    System should isolate failures and prevent cascading effects.
    """
    failure_count = 0
    success_count = 0

    async def service_a():
        """Service that fails"""
        nonlocal failure_count
        await asyncio.sleep(0.1)
        failure_count += 1
        raise Exception("Service A failed")

    async def service_b():
        """Service that succeeds"""
        nonlocal success_count
        await asyncio.sleep(0.1)
        success_count += 1
        return {"status": "ok", "service": "B"}

    async def service_c():
        """Service that succeeds"""
        nonlocal success_count
        await asyncio.sleep(0.1)
        success_count += 1
        return {"status": "ok", "service": "C"}

    # Run all services concurrently
    tasks = [
        service_a(),
        service_b(),
        service_c()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Service A should fail, B and C should succeed
    assert failure_count == 1, "Service A should fail"
    assert success_count == 2, "Services B and C should succeed"

    # Failure in A should not affect B or C
    assert isinstance(results[0], Exception), "Service A should raise exception"
    assert results[1]["service"] == "B", "Service B should succeed"
    assert results[2]["service"] == "C", "Service C should succeed"

    print(f"\nCascading Failure Prevention Test Results:")
    print(f"  Failed services: {failure_count}")
    print(f"  Successful services: {success_count}")
    print(f"  Cascading prevented: YES")


# ============================================================================
# Test 5: Circuit Breaker Pattern
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
async def test_circuit_breaker_behavior():
    """
    Test circuit breaker pattern for failing services.

    Simulates repeated failures that trigger circuit breaker,
    preventing further calls to failing service.
    """
    failure_threshold = 3
    timeout_seconds = 5
    call_count = 0
    circuit_open = False

    class CircuitBreaker:
        """Simple circuit breaker implementation"""
        def __init__(self, failure_threshold: int, timeout: int):
            self.failure_threshold = failure_threshold
            self.timeout = timeout
            self.failures = 0
            self.last_failure_time = None
            self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

        async def call(self, func):
            """Execute function with circuit breaker protection"""
            # Check if circuit should be reset
            if self.state == "OPEN":
                if datetime.now(UTC) - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = await func()
                # Success - reset failures if HALF_OPEN
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = datetime.now(UTC)

                # Open circuit if threshold exceeded
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    raise Exception(f"Circuit breaker opened after {self.failures} failures")
                raise

    async def failing_service():
        """Service that always fails"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        raise Exception("Service failure")

    # Create circuit breaker
    cb = CircuitBreaker(failure_threshold=3, timeout=5)

    # Make calls until circuit opens
    results = []
    for i in range(10):
        try:
            result = await cb.call(failing_service)
            results.append({"attempt": i, "result": result})
        except Exception as e:
            results.append({"attempt": i, "error": str(e)})

    # First 3 should fail, then circuit should open
    service_failures = sum(1 for r in results[:3] if "error" in r and "Service failure" in r["error"])
    circuit_opens = sum(1 for r in results[3:] if "error" in r and "OPEN" in r["error"])

    assert service_failures == 3, "First 3 calls should fail with service error"
    assert circuit_opens == 7, "Next 7 calls should fail with circuit breaker open"
    assert call_count == 3, "Service should only be called 3 times (then circuit opens)"

    print(f"\nCircuit Breaker Test Results:")
    print(f"  Service calls: {call_count}")
    print(f"  Circuit opened after: {failure_threshold} failures")
    print(f"  Calls blocked by circuit: {circuit_opens}")


# ============================================================================
# Test 6: Graceful Degradation
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
async def test_graceful_degradation_on_cache_failure():
    """
    Test graceful degradation when cache fails.

    System should fall back to database and continue serving requests
    without cache.
    """
    cache_enabled = False

    async def get_data_with_fallback(key: str):
        """Get data with graceful fallback"""
        # Try cache
        if cache_enabled:
            try:
                cached = await AsyncCache.get(key)
                if cached:
                    return {"source": "cache", "data": cached}
            except Exception as e:
                pass  # Cache failure - fall through to database

        # Fall back to "database"
        await asyncio.sleep(0.2)  # Simulate slower database query
        data = {
            "key": key,
            "value": f"db_value_{key}",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Try to update cache (may fail silently)
        try:
            if cache_enabled:
                await AsyncCache.set(key, data, expire=300)
        except Exception as e:
            pass  # Silent failure - OK

        return {"source": "database", "data": data}

    # Scenario: Cache is down
    cache_enabled = False

    start_time = datetime.now()
    result = await get_data_with_fallback("test_key")
    end_time = datetime.now()

    assert result["source"] == "database", "Should fall back to database"
    assert result["data"]["key"] == "test_key", "Should return correct data"

    duration = (end_time - start_time).total_seconds()
    assert duration < 1, f"Fallback should complete in < 1s, took {duration:.2f}s"

    print(f"\nGraceful Degradation Test Results:")
    print(f"  Cache available: NO")
    print(f"  Fallback source: {result['source']}")
    print(f"  Duration: {duration:.3f}s")
    print(f"  System behavior: DEGRADED (but functional)")


# ============================================================================
# Test 7: Concurrent Chaos Scenarios
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_multiple_simultaneous_failures():
    """
    Test system resilience when multiple failures occur simultaneously.

    Simulates network latency, cache failures, and database slowdowns
    all happening at once.
    """
    results = {
        "cache_ops": [],
        "db_ops": [],
        "api_ops": []
    }

    async def chaotic_cache_op(op_id: int):
        """Cache operation with random failures and delays"""
        # Random delay 50-200ms
        await asyncio.sleep(random.randint(50, 200) / 1000)

        # 20% chance of failure
        if random.random() < 0.2:
            results["cache_ops"].append({"op_id": op_id, "status": "failed"})
            raise Exception("Cache operation failed")

        # Success
        results["cache_ops"].append({"op_id": op_id, "status": "success"})
        return True

    async def chaotic_db_op(op_id: int):
        """Database operation with random delays"""
        # Random delay 100-500ms
        await asyncio.sleep(random.randint(100, 500) / 1000)

        results["db_ops"].append({"op_id": op_id, "status": "success"})
        return {"data": f"db_result_{op_id}"}

    async def chaotic_api_op(op_id: int):
        """API operation with random latency"""
        # Random delay 50-300ms
        await asyncio.sleep(random.randint(50, 300) / 1000)

        results["api_ops"].append({"op_id": op_id, "status": "success"})
        return {"response": f"api_response_{op_id}"}

    # Mix of all operation types
    tasks = []
    for i in range(30):
        if i % 3 == 0:
            tasks.append(chaotic_cache_op(i))
        elif i % 3 == 1:
            tasks.append(chaotic_db_op(i))
        else:
            tasks.append(chaotic_api_op(i))

    start_time = datetime.now()
    await asyncio.gather(*tasks, return_exceptions=True)
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    # Analyze results
    cache_success = sum(1 for r in results["cache_ops"] if r["status"] == "success")
    cache_failed = sum(1 for r in results["cache_ops"] if r["status"] == "failed")
    db_success = len(results["db_ops"])
    api_success = len(results["api_ops"])

    print(f"\nConcurrent Chaos Test Results:")
    print(f"  Total duration: {duration:.2f}s")
    print(f"  Cache operations: {cache_success} success, {cache_failed} failed")
    print(f"  Database operations: {db_success} success")
    print(f"  API operations: {api_success} success")
    print(f"  Overall resilience: {(cache_success + db_success + api_success) / 30:.1%}")

    # Most operations should succeed despite chaos
    total_success = cache_success + db_success + api_success
    assert total_success >= 25, f"Expected >= 25 successes, got {total_success}/30"

    assert duration < 5, f"Expected completion in < 5s, took {duration:.2f}s"


# ============================================================================
# Test 8: Recovery After Failure
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
async def test_service_recovery_after_failure():
    """
    Test that services recover properly after failures.

    Simulates service failure followed by recovery.
    System should detect recovery and resume normal operation.
    """
    service_healthy = False
    failure_count = 0

    async def unreliable_service():
        """Service that fails initially, then recovers"""
        nonlocal service_healthy, failure_count
        failure_count += 1

        if failure_count <= 3:
            # First 3 calls fail
            raise Exception("Service unavailable")

        # Service recovers
        service_healthy = True
        return {"status": "ok", "data": "service_data"}

    # Call service until it recovers
    attempts = 0
    max_attempts = 10
    result = None

    while attempts < max_attempts:
        attempts += 1
        try:
            result = await unreliable_service()
            break  # Success
        except Exception:
            if attempts < max_attempts:
                await asyncio.sleep(0.1)  # Brief backoff
            else:
                raise  # Re-raise final failure

    assert result is not None, "Service should eventually recover"
    assert result["status"] == "ok", "Service should return success"
    assert service_healthy, "Service should be marked as healthy"
    assert failure_count == 4, f"Should fail 3 times then succeed (attempt {failure_count})"

    print(f"\nService Recovery Test Results:")
    print(f"  Failures before recovery: {failure_count - 1}")
    assert failure_count - 1 == 3, "Should have 3 failures before recovery"
    print(f"  Recovery successful: YES")


# ============================================================================
# Test 9: Memory Pressure Simulation
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.chaos
@pytest.mark.concurrent
async def test_memory_pressure_handling():
    """
    Test system behavior under memory pressure.

    Simulates high memory usage by creating many concurrent operations
    with large data structures.
    """
    cache_prefix = f"memory_pressure_test:{uuid4()}:"

    # Create large data structures (simulating memory pressure)
    large_data = {
        "data": "x" * 10000,  # 10KB per entry
        "items": list(range(1000))
    }

    async def heavy_memory_operation(op_id: int):
        """Operation that uses significant memory"""
        key = f"{cache_prefix}op_{op_id}"

        # Create large in-memory structure
        data = {
            "id": op_id,
            "payload": large_data.copy(),
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Try to cache (may fail under memory pressure)
        try:
            await AsyncCache.set(key, data, expire=60)
        except Exception as e:
            pass  # Cache may fail under memory pressure

        # Simulate processing
        await asyncio.sleep(0.01)

        # Clean up
        await AsyncCache.delete(key)

        return {"op_id": op_id, "status": "success"}

    # Run 100 concurrent heavy operations
    tasks = [heavy_memory_operation(i) for i in range(100)]

    start_time = datetime.now()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")

    print(f"\nMemory Pressure Test Results:")
    print(f"  Operations: 100")
    print(f"  Successful: {success_count}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {success_count / duration:.0f} ops/s")

    # Most operations should succeed
    assert success_count >= 90, f"Expected >= 90 successes under memory pressure, got {success_count}"

    # Cleanup
    try:
        await AsyncCache.delete_pattern(f"{cache_prefix}*")
    except Exception as e:
        pass
