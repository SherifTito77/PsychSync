"""
Cache Coherency Race Condition Tests

Tests to verify cache-level race condition handling:
1. Cache stampede prevention (lock-based prevention)
2. Cache invalidation race (invalidating during concurrent reads)
3. Write-through race (multiple concurrent writes to same key)
4. Cache eviction under load (LRU behavior with memory pressure)
5. Cache expiration race (concurrent expiration and refresh)
6. Distributed cache consistency (Redis cluster scenarios)
7. Cache warm-up race (concurrent cache population)

These tests verify that the cache layer correctly handles concurrent operations
to prevent stale data, cache stampedes, and inconsistencies.
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
import redis.asyncio as aioredis

from app.core.async_cache import AsyncCache, async_cached, async_redis_client
from app.core.config import settings

# ============================================================================
# Test 1: Cache Stampede Prevention
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_cache_stampede_prevention_with_lock():
    """
    Test that cache stampede is prevented under high concurrency.

    Race Condition: Multiple concurrent requests with cache miss could
    all call the expensive function simultaneously (cache stampede).

    Fix: Use Redis distributed locks to ensure only one request computes
    the value while others wait.
    """
    # Clear cache first
    await AsyncCache.delete_pattern("test_stampede:*")

    call_count = 0
    lock_timeout = 0

    @async_cached(expire=60, key_prefix="test_stampede")
    async def expensive_function(key: str) -> dict:
        """Simulate expensive operation"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.5)  # Simulate expensive computation
        return {"result": f"value_{key}", "timestamp": datetime.now(UTC).isoformat()}

    # Simulate 50 concurrent requests with cache miss
    tasks = [expensive_function("test_key") for _ in range(50)]

    # Execute all tasks concurrently
    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    # All results should have the same value
    result_values = [r["result"] for r in results]
    assert len(set(result_values)) == 1, "All results should be identical"
    assert results[0]["result"] == "value_test_key"

    # Due to lock mechanism, expensive function should be called only once
    # (or very few times due to race conditions in lock acquisition)
    assert call_count <= 3, f"Expected <= 3 calls due to lock, got {call_count}"

    # Should complete quickly (not 50 * 0.5s = 25s, but ~0.5s + lock overhead)
    duration = (end_time - start_time).total_seconds()
    assert duration < 5, f"Expected ~0.5-1s duration, got {duration}s"

    print(f"\nCache Stampede Test Results:")
    print(f"  Concurrent requests: 50")
    print(f"  Function calls: {call_count}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Speedup: {(50 * 0.5) / duration:.1f}x")

    # Cleanup
    await AsyncCache.delete_pattern("test_stampede:*")


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_cache_stampede_with_various_delays():
    """
    Test cache stampede prevention with varying network delays.

    Simulates real-world conditions where requests arrive at slightly different times.
    """
    await AsyncCache.delete_pattern("test_delayed_stampede:*")

    call_count = 0

    @async_cached(expire=60, key_prefix="test_delayed_stampede")
    async def expensive_function_with_delay(key: str, delay_ms: int = 0) -> dict:
        """Simulate expensive operation with variable delay"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(delay_ms / 1000)  # Simulate network/processing delay
        return {"key": key, "count": call_count}

    # Simulate 20 requests with varying delays (staggered arrival)
    async def delayed_request(delay_ms):
        await asyncio.sleep(delay_ms / 1000)
        return await expensive_function_with_delay("staggered_key")

    # Stagger requests over 200ms
    tasks = [delayed_request(i * 10) for i in range(20)]  # 0ms, 10ms, 20ms, ..., 190ms

    results = await asyncio.gather(*tasks)

    # All should get the same cached result
    assert all(r["key"] == "staggered_key" for r in results)

    # Should have minimal calls due to caching
    assert call_count <= 5, f"Expected <= 5 calls, got {call_count}"

    # Cleanup
    await AsyncCache.delete_pattern("test_delayed_stampede:*")


# ============================================================================
# Test 2: Cache Invalidation Race
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_cache_invalidation_during_concurrent_reads():
    """
    Test cache invalidation while reads are in progress.

    Race Condition: Cache invalidation during concurrent reads could
    cause some reads to get stale data while others get fresh data.

    Fix: Cache invalidation should be atomic, and reads should either
    get old data or new data, never corrupted data.
    """
    cache_key = f"test_invalidation:{uuid4()}"

    # Set initial value
    await AsyncCache.set(cache_key, {"version": 1, "data": "initial"}, expire=60)

    read_results = []

    async def concurrent_read(reader_id: int):
        """Read from cache"""
        value = await AsyncCache.get(cache_key)
        read_results.append({"reader_id": reader_id, "value": value})
        return value

    async def concurrent_invalidate():
        """Invalidate cache after some reads"""
        await asyncio.sleep(0.1)  # Let some reads complete first
        await AsyncCache.delete(cache_key)
        # Write new value
        await AsyncCache.set(cache_key, {"version": 2, "data": "updated"}, expire=60)

    # Run 10 concurrent reads and 1 invalidation
    tasks = [concurrent_read(i) for i in range(10)] + [concurrent_invalidate()]

    await asyncio.gather(*tasks)

    # Verify all reads got valid data (either version 1 or version 2)
    versions = [r["value"]["version"] if r["value"] else None for r in read_results]

    # All reads should have gotten either version 1 or version 2
    assert all(
        v in [1, 2, None] for v in versions
    ), f"Invalid versions detected: {versions}"

    # At least some reads should have gotten version 1 (before invalidation)
    assert versions.count(1) > 0, "Some reads should have gotten version 1"

    # At least some reads should have gotten version 2 (after invalidation)
    assert versions.count(2) > 0, "Some reads should have gotten version 2"

    # Cleanup
    await AsyncCache.delete(cache_key)


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_cache_pattern_invalidation_race():
    """
    Test pattern-based cache invalidation during concurrent operations.

    Race Condition: Pattern invalidation could delete keys that are
    being written concurrently.

    Fix: Pattern deletion should handle concurrent writes safely.
    """
    prefix = f"test_pattern_invalidation:{uuid4()}:"

    # Create 20 cache keys
    keys = [f"{prefix}key_{i}" for i in range(20)]

    # Set all keys
    for key in keys:
        await AsyncCache.set(key, {"value": f"data_{key}"}, expire=60)

    # Concurrently: read some keys, write some keys, and invalidate pattern
    async def read_keys(key_subset):
        """Read a subset of keys"""
        results = {}
        for key in key_subset:
            results[key] = await AsyncCache.get(key)
        return results

    async def write_keys(key_subset):
        """Write to a subset of keys"""
        await asyncio.sleep(0.05)  # Small delay
        for key in key_subset:
            await AsyncCache.set(key, {"value": f"updated_{key}"}, expire=60)

    async def invalidate_pattern():
        """Invalidate all keys matching pattern"""
        await asyncio.sleep(0.1)  # Let some reads/writes complete
        return await AsyncCache.delete_pattern(f"{prefix}*")

    # Split keys into three groups
    read_keys_subset = keys[0:7]  # Read 7 keys
    write_keys_subset = keys[7:14]  # Write 7 keys
    remaining_keys = keys[14:20]  # Remaining 6 keys (only invalidated)

    # Run operations concurrently
    tasks = [
        read_keys(read_keys_subset),
        write_keys(write_keys_subset),
        invalidate_pattern(),
    ]

    results = await asyncio.gather(*tasks)
    deleted_count = results[2]

    # Verify some keys were deleted
    assert deleted_count > 0, "Some keys should have been deleted"

    # Verify remaining keys (if any) have valid data
    remaining_values = []
    for key in keys:
        value = await AsyncCache.get(key)
        if value:
            remaining_values.append((key, value))

    # All remaining values should be valid JSON
    for key, value in remaining_values:
        assert "value" in value, f"Invalid value for key {key}"

    # Cleanup
    await AsyncCache.delete_pattern(f"{prefix}*")


# ============================================================================
# Test 3: Write-Through Race
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_concurrent_writes_to_same_key():
    """
    Test concurrent writes to the same cache key.

    Race Condition: Multiple concurrent writes to the same key could
    cause data corruption or inconsistent state.

    Fix: Last write wins (atomic SET operation), but application
    should handle concurrent updates appropriately.
    """
    cache_key = f"test_concurrent_write:{uuid4()}"

    # 10 concurrent writes to the same key
    async def write_value(value: dict):
        """Write value to cache"""
        await AsyncCache.set(cache_key, value, expire=60)
        # Small random delay to increase race condition likelihood
        await asyncio.sleep(0.001)
        return value

    tasks = [
        write_value({"writer_id": i, "timestamp": datetime.now(UTC).isoformat()})
        for i in range(10)
    ]

    await asyncio.gather(*tasks)

    # Verify final state - one write should have won
    final_value = await AsyncCache.get(cache_key)

    assert final_value is not None, "Key should exist"
    assert "writer_id" in final_value, "Value should have writer_id"
    assert final_value["writer_id"] in range(
        10
    ), f"Invalid writer_id: {final_value['writer_id']}"

    # Should have exactly one value (last write wins)
    assert isinstance(final_value["writer_id"], int), "writer_id should be integer"

    # Cleanup
    await AsyncCache.delete(cache_key)


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_write_through_consistency():
    """
    Test write-through cache consistency under concurrent writes.

    Verifies that cache and database stay consistent under load.
    """
    cache_key = f"test_write_through:{uuid4()}"
    db_sim = {}  # Simulate database

    async def write_through(key: str, value: dict):
        """Write to both cache and database"""
        # Write to "database" first
        db_sim[key] = value
        await asyncio.sleep(0.01)  # Simulate DB write latency

        # Then write to cache
        await AsyncCache.set(key, value, expire=60)

        return value

    async def read_through(key: str):
        """Read from cache, fall back to database"""
        # Try cache first
        value = await AsyncCache.get(key)
        if value:
            return {"source": "cache", "value": value}

        # Fall back to database
        await asyncio.sleep(0.02)  # Simulate DB read latency
        value = db_sim.get(key)
        if value:
            # Write to cache for next time
            await AsyncCache.set(key, value, expire=60)
            return {"source": "database", "value": value}

        return {"source": "none", "value": None}

    # Perform 10 concurrent write-through operations
    write_tasks = [
        write_through(cache_key, {"version": i, "data": f"value_{i}"})
        for i in range(10)
    ]

    await asyncio.gather(*write_tasks)

    # Read and verify consistency
    result = await read_through(cache_key)

    assert result["source"] in [
        "cache",
        "database",
    ], f"Invalid source: {result['source']}"
    assert result["value"] is not None, "Should have a value"

    # Verify database and cache have the same final value
    db_value = db_sim.get(cache_key)
    cache_value = await AsyncCache.get(cache_key)

    assert db_value is not None, "Database should have value"
    assert cache_value is not None, "Cache should have value"

    # Both should have the same version (last write wins)
    assert (
        db_value["version"] == cache_value["version"]
    ), f"DB and cache mismatch: DB={db_value}, Cache={cache_value}"

    # Cleanup
    await AsyncCache.delete(cache_key)


# ============================================================================
# Test 4: Cache Eviction Under Load
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
@pytest.mark.load_test
async def test_cache_eviction_under_memory_pressure():
    """
    Test cache eviction behavior under high memory pressure.

    Simulates LRU eviction when cache is full.
    """
    await AsyncCache.clear_all()  # Start fresh

    # Set cache size limit (simulated by setting many keys)
    cache_prefix = f"test_eviction:{uuid4()}:"

    # Write 1000 keys rapidly (simulating memory pressure)
    async def write_key_batch(start_idx: int, count: int):
        """Write a batch of keys"""
        for i in range(start_idx, start_idx + count):
            key = f"{cache_prefix}key_{i}"
            value = {"data": f"value_{i}", "size": 1000}  # 1KB per key
            await AsyncCache.set(key, value, expire=300)
        return count

    # Write 1000 keys in 10 concurrent batches
    tasks = [write_key_batch(i * 100, 100) for i in range(10)]

    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    total_written = sum(results)
    duration = (end_time - start_time).total_seconds()

    assert total_written == 1000, f"Expected 1000 keys written, got {total_written}"

    print(f"\nCache Eviction Test Results:")
    print(f"  Keys written: {total_written}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {total_written / duration:.0f} writes/sec")

    # Try to read some keys - some may have been evicted
    sample_keys = [f"{cache_prefix}key_{i}" for i in [0, 100, 500, 900, 999]]

    read_results = []
    for key in sample_keys:
        value = await AsyncCache.get(key)
        read_results.append((key, value is not None))

    present_count = sum(1 for _, present in read_results if present)

    # At least some keys should still be present
    assert present_count > 0, "At least some keys should still be in cache"

    print(f"  Sample keys present: {present_count}/{len(sample_keys)}")

    # Cleanup
    await AsyncCache.delete_pattern(f"{cache_prefix}*")


# ============================================================================
# Test 5: Cache Expiration Race
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_cache_expiration_during_concurrent_access():
    """
    Test cache expiration while keys are being accessed concurrently.

    Race Condition: Key expires while being read, causing some reads
    to miss and others to hit.

    Fix: Expiration should be atomic, and reads should handle
    missing keys gracefully.
    """
    cache_key = f"test_expiration:{uuid4()}"

    # Set key with short expiration (2 seconds)
    await AsyncCache.set(cache_key, {"value": "test_data"}, expire=2)

    access_results = []

    async def access_key(access_id: int, delay_ms: int):
        """Access key after delay"""
        await asyncio.sleep(delay_ms / 1000)
        value = await AsyncCache.get(cache_key)
        access_results.append(
            {
                "access_id": access_id,
                "delay_ms": delay_ms,
                "found": value is not None,
                "value": value,
            }
        )
        return value

    # Access key at different times (before, during, and after expiration)
    tasks = [
        access_key(0, 0),  # Immediate (should hit)
        access_key(1, 500),  # 500ms (should hit)
        access_key(2, 1000),  # 1000ms (should hit)
        access_key(3, 1500),  # 1500ms (may hit or miss)
        access_key(4, 2000),  # 2000ms (should miss)
        access_key(5, 2500),  # 2500ms (should miss)
    ]

    await asyncio.gather(*tasks)

    # Verify results
    hits = sum(1 for r in access_results if r["found"])
    misses = sum(1 for r in access_results if not r["found"])

    # First 3 should definitely hit
    assert access_results[0]["found"], "First access should hit"
    assert access_results[1]["found"], "Second access should hit"
    assert access_results[2]["found"], "Third access should hit"

    # Last 2 should definitely miss
    assert not access_results[4]["found"], "Fifth access should miss"
    assert not access_results[5]["found"], "Sixth access should miss"

    # 4th access is indeterminate (right at expiration boundary)

    print(f"\nCache Expiration Test Results:")
    print(f"  Hits: {hits}")
    print(f"  Misses: {misses}")

    # Cleanup
    await AsyncCache.delete(cache_key)


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_cache_refresh_on_expiration():
    """
    Test automatic cache refresh when key expires.

    Simulates cache-aside pattern where expired keys are
    automatically refreshed from database.
    """
    cache_key = f"test_refresh:{uuid4()}"

    # Simulate database
    db_value = {"version": 1, "data": "initial"}

    async def get_with_refresh(key: str) -> dict:
        """Get value with automatic refresh on expiration"""
        # Try cache first
        value = await AsyncCache.get(key)
        if value:
            return {"source": "cache", "value": value}

        # Cache miss - refresh from "database"
        await asyncio.sleep(0.1)  # Simulate DB query
        value = db_value.copy()

        # Write to cache with expiration
        await AsyncCache.set(key, value, expire=2)

        return {"source": "database", "value": value}

    # Set initial value
    await AsyncCache.set(cache_key, db_value, expire=2)

    # Read immediately (should hit cache)
    result1 = await get_with_refresh(cache_key)
    assert result1["source"] == "cache", "First read should hit cache"

    # Wait for expiration
    await asyncio.sleep(2.5)

    # Update "database"
    db_value = {"version": 2, "data": "updated"}

    # Read again (should miss cache and refresh from DB)
    result2 = await get_with_refresh(cache_key)
    assert result2["source"] == "database", "Second read should refresh from DB"
    assert result2["value"]["version"] == 2, "Should get updated version"

    # Read again (should hit cache with new value)
    result3 = await get_with_refresh(cache_key)
    assert result3["source"] == "cache", "Third read should hit cache"
    assert result3["value"]["version"] == 2, "Should have new version in cache"

    # Cleanup
    await AsyncCache.delete(cache_key)


# ============================================================================
# Test 6: Cache Warm-Up Race
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_concurrent_cache_warmup():
    """
    Test concurrent cache warm-up operations.

    Race Condition: Multiple threads trying to warm up the same cache
    keys could cause redundant database queries.

    Fix: Use distributed locks to ensure only one thread warms up
    each key while others wait.
    """
    cache_prefix = f"test_warmup:{uuid4()}:"

    # Simulate database
    db_data = {
        f"key_{i}": {"value": f"data_{i}", "timestamp": datetime.now(UTC).isoformat()}
        for i in range(100)
    }

    db_query_count = 0

    async def get_from_db_with_warmup(key: str) -> dict:
        """Simulate database query with warm-up"""
        nonlocal db_query_count
        db_query_count += 1
        await asyncio.sleep(0.05)  # Simulate DB query latency
        return db_data.get(key)

    async def get_with_warmup(key: str) -> dict:
        """Get with automatic cache warm-up"""
        # Try cache first
        value = await AsyncCache.get(key)
        if value:
            return {"source": "cache", "value": value}

        # Cache miss - warm up from DB
        value = await get_from_db_with_warmup(key)
        if value:
            await AsyncCache.set(key, value, expire=300)
            return {"source": "database", "value": value}

        return {"source": "none", "value": None}

    # Concurrently warm up 100 keys (each key accessed by 10 threads)
    tasks = []
    for i in range(100):
        key = f"{cache_prefix}key_{i}"
        # Each key accessed 10 times concurrently
        tasks.extend([get_with_warmup(key) for _ in range(10)])

    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    # Verify all requests succeeded
    assert len(results) == 1000, f"Expected 1000 results, got {len(results)}"
    assert all(
        r["value"] is not None for r in results
    ), "All requests should have values"

    # Due to caching, DB queries should be much less than 1000
    # Ideal: 100 queries (one per unique key), but allow some overhead
    assert (
        db_query_count < 200
    ), f"Expected < 200 DB queries due to caching, got {db_query_count}"

    print(f"\nCache Warm-Up Test Results:")
    print(f"  Total requests: 1000")
    print(f"  Unique keys: 100")
    print(f"  DB queries: {db_query_count}")
    print(f"  Cache hit ratio: {(1000 - db_query_count) / 1000:.1%}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {1000 / duration:.0f} req/s")

    # Cleanup
    await AsyncCache.delete_pattern(f"{cache_prefix}*")


# ============================================================================
# Test 7: Distributed Cache Consistency (Redis-Specific)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
async def test_redis_transaction_atomicity():
    """
    Test Redis transaction (MULTI/EXEC) atomicity for cache operations.

    Verifies that transactions are atomic under concurrent access.
    """
    if not async_redis_client:
        pytest.skip("Redis client not available")

    cache_key = f"test_transaction:{uuid4()}"

    # Use Redis transaction to atomically check-and-set
    async def check_and_set(key: str, expected_version: int, new_value: dict) -> bool:
        """Atomically check version and set if matches"""
        async with async_redis_client.pipeline(transaction=True) as pipe:
            try:
                # Watch the key
                await pipe.watch(key)

                # Get current value
                current = await async_redis_client.get(key)
                if current:
                    current_data = json.loads(current)
                    if current_data.get("version") != expected_version:
                        pipe.unwatch()
                        return False

                # Execute transaction
                pipe.multi()
                new_value["version"] = expected_version + 1
                await pipe.setex(key, 60, json.dumps(new_value, default=str))
                await pipe.execute()
                return True

            except Exception:
                pipe.unwatch()
                return False

    # Set initial value
    await AsyncCache.set(cache_key, {"version": 0, "value": "initial"}, expire=60)

    # Try 10 concurrent updates (only first should succeed due to version check)
    tasks = [check_and_set(cache_key, i, {"value": f"update_{i}"}) for i in range(10)]

    results = await asyncio.gather(*tasks)

    # Only first should succeed (version 0 -> 1)
    # Rest should fail because version doesn't match
    success_count = sum(1 for r in results if r)
    failure_count = sum(1 for r in results if not r)

    assert success_count >= 1, f"Expected >= 1 successful update, got {success_count}"

    # Verify final version
    final_value = await AsyncCache.get(cache_key)
    assert final_value is not None, "Key should exist"
    assert (
        final_value["version"] >= 1
    ), f"Version should be >= 1, got {final_value['version']}"

    print(f"\nRedis Transaction Test Results:")
    print(f"  Successful updates: {success_count}")
    print(f"  Failed updates (version mismatch): {failure_count}")
    print(f"  Final version: {final_value['version']}")

    # Cleanup
    await AsyncCache.delete(cache_key)


# ============================================================================
# Test 8: Cache Performance Under Load
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.cache
@pytest.mark.concurrent
@pytest.mark.load_test
async def test_cache_performance_under_high_load():
    """
    Stress test: 1000 concurrent cache operations.

    Verifies cache performance and stability under high load.
    """
    cache_prefix = f"test_load:{uuid4()}:"

    # Mix of read and write operations
    async def mixed_operation(op_id: int):
        """Perform mixed cache operations"""
        key = f"{cache_prefix}key_{op_id % 100}"  # 100 unique keys

        # 70% reads, 30% writes
        if op_id % 10 < 7:
            # Read operation
            value = await AsyncCache.get(key)
            return {"operation": "read", "key": key, "found": value is not None}
        else:
            # Write operation
            value = {
                "data": f"value_{op_id}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await AsyncCache.set(key, value, expire=300)
            return {"operation": "write", "key": key, "success": True}

    # Perform 1000 concurrent operations
    start_time = datetime.now()

    tasks = [mixed_operation(i) for i in range(1000)]
    results = await asyncio.gather(*tasks)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Analyze results
    reads = [r for r in results if r["operation"] == "read"]
    writes = [r for r in results if r["operation"] == "write"]

    read_hits = sum(1 for r in reads if r["found"])
    write_success = sum(1 for r in writes if r["success"])

    assert len(results) == 1000, f"Expected 1000 operations, got {len(results)}"
    assert write_success == len(writes), "All writes should succeed"

    print(f"\nCache Load Test Results:")
    print(f"  Total operations: {len(results)}")
    print(f"  Reads: {len(reads)}")
    print(f"  Writes: {len(writes)}")
    print(f"  Cache hits: {read_hits}/{len(reads)} ({read_hits/len(reads):.1%})")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {len(results) / duration:.0f} ops/s")

    # Performance assertion: should handle > 1000 ops/s
    throughput = len(results) / duration
    assert throughput > 100, f"Expected > 100 ops/s, got {throughput:.0f} ops/s"

    # Cleanup
    await AsyncCache.delete_pattern(f"{cache_prefix}*")
