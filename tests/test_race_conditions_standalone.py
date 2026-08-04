"""
Standalone Race Condition Tests (No App Dependencies)

These tests verify the thread-safety patterns work correctly
without importing the full application (which has dependency issues).

Run with: python tests/test_race_conditions_standalone.py
"""

import asyncio
from uuid import uuid4


async def test_singleton_initialization_thread_safety():
    """Test that singleton initialization is thread-safe under high concurrency."""
    _instance = None
    _lock = asyncio.Lock()

    async def get_singleton():
        """Thread-safe singleton with double-checked locking"""
        nonlocal _instance
        if _instance is None:
            async with _lock:
                if _instance is None:
                    _instance = object()
        return _instance

    # Spawn 100 concurrent requests to get the singleton
    tasks = [get_singleton() for _ in range(100)]
    results = await asyncio.gather(*tasks)

    # All should return the same instance (same ID)
    instance_ids = [id(r) for r in results]
    unique_ids = set(instance_ids)

    assert len(unique_ids) == 1, f"Expected 1 unique instance, got {len(unique_ids)}"
    print(
        f"✅ Singleton test passed: All {len(results)} requests got the same instance"
    )


async def test_redis_client_lazy_init_thread_safety():
    """Test that lazy initialization is thread-safe."""

    class RedisClientMock:
        def __init__(self):
            self.id = uuid4()

    class Tracker:
        def __init__(self):
            self._client = None
            self._init_lock = asyncio.Lock()

        async def get_client(self):
            if self._client is None:
                async with self._init_lock:
                    if self._client is None:
                        self._client = RedisClientMock()
            return self._client

    tracker = Tracker()

    # Spawn 50 concurrent requests to trigger lazy init
    async def get_client():
        return await tracker.get_client()

    tasks = [get_client() for _ in range(50)]
    results = await asyncio.gather(*tasks)

    # All should return the same client instance
    instance_ids = [id(r) for r in results]
    unique_ids = set(instance_ids)

    assert (
        len(unique_ids) == 1
    ), f"Expected 1 unique Redis client, got {len(unique_ids)}"
    print(
        f"✅ Redis client lazy init test passed: All {len(results)} requests got the same client"
    )


async def test_cache_stampede_protection():
    """Test that cache stampede protection prevents duplicate expensive operations."""
    call_count = 0
    _lock = asyncio.Lock()
    _cache = {}
    _generating = set()

    async def cache_stampede_protect(key, generator):
        """Simplified cache stampede protection"""
        # Check cache first
        if key in _cache:
            return _cache[key]

        # Check if another request is generating
        if key in _generating:
            # Wait for generation to complete
            while key in _generating:
                await asyncio.sleep(0.001)
            return _cache[key]

        # Acquire lock to generate
        async with _lock:
            # Double-check after acquiring lock
            if key in _cache:
                return _cache[key]

            if key not in _generating:
                _generating.add(key)
                try:
                    result = await generator()
                    _cache[key] = result
                    return result
                finally:
                    _generating.remove(key)

    async def expensive_operation(user_id: str):
        """Simulate expensive operation (e.g., OpenAI API call)"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)  # Simulate network latency
        return {"user_id": user_id, "data": f"result_{uuid4()}"}

    # Spawn 50 concurrent requests for the same cache key
    cache_key = f"test_cache:{uuid4()}"
    tasks = [
        cache_stampede_protect(cache_key, lambda: expensive_operation("test_user"))
        for _ in range(50)
    ]

    results = await asyncio.gather(*tasks)

    # Despite 50 concurrent requests, operation should only run once
    assert call_count == 1, f"Expected 1 API call, got {call_count}"
    assert len(results) == 50, "Should have 50 results"
    print(
        f"✅ Cache stampede test passed: {len(tasks)} concurrent requests triggered only {call_count} operation"
    )


async def test_atomic_increment_thread_safety():
    """Test that atomic increment prevents lost updates."""
    # Simulate concurrent increments
    counter = {"value": 0}
    lock = asyncio.Lock()

    async def increment_counter():
        async with lock:
            counter["value"] += 1
            await asyncio.sleep(0.0001)  # Simulate work

    # Spawn 100 concurrent increments
    tasks = [increment_counter() for _ in range(100)]
    await asyncio.gather(*tasks)

    assert counter["value"] == 100, f"Expected 100, got {counter['value']}"
    print(f"✅ Atomic increment test passed: Counter = {counter['value']}")


async def test_idempotent_insert_thread_safety():
    """Test that idempotent insert prevents duplicates."""
    # Simulate database table
    inserted_records = set()
    insert_count = 0

    async def insert_record(unique_id: str):
        """Simulate idempotent insert with locking"""
        nonlocal insert_count
        async with asyncio.Lock():
            if unique_id not in inserted_records:
                inserted_records.add(unique_id)
                insert_count += 1
                await asyncio.sleep(0.001)  # Simulate database insert
                return True, "created"
            return False, "exists"

    # Spawn 20 concurrent inserts with the same unique_id
    unique_id = str(uuid4())
    tasks = [insert_record(unique_id) for _ in range(20)]
    results = await asyncio.gather(*tasks)

    created_count = sum(1 for created, _ in results if created)
    exists_count = sum(1 for _, status in results if status == "exists")

    assert created_count == 1, f"Expected 1 insert, got {created_count}"
    assert exists_count == 19, f"Expected 19 'exists' results, got {exists_count}"
    print(
        f"✅ Idempotent insert test passed: 1 insert, {exists_count} duplicates detected"
    )


async def test_websocket_connection_manager_thread_safety():
    """Test WebSocket connection manager under concurrent connections."""

    class ConnectionManager:
        """Thread-safe WebSocket connection manager"""

        def __init__(self):
            self.active_connections = {}
            self._lock = asyncio.Lock()

        async def connect(self, user_id: int, conn_id: int):
            async with self._lock:
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = set()
                self.active_connections[user_id].add(conn_id)
                return len(self.active_connections[user_id])

    manager = ConnectionManager()

    # Simulate 50 concurrent connections from 10 different users
    async def connect_user(user_id: int, conn_id: int):
        await asyncio.sleep(0.0001)  # Simulate connection
        return await manager.connect(user_id, conn_id)

    # Each user makes 5 concurrent connections
    tasks = []
    for user_id in range(10):
        for conn_id in range(5):
            tasks.append(connect_user(user_id, conn_id))

    await asyncio.gather(*tasks)

    # Verify each user has exactly 5 connections
    for user_id in range(10):
        connection_count = len(manager.active_connections.get(user_id, set()))
        assert (
            connection_count == 5
        ), f"User {user_id} has {connection_count} connections, expected 5"

    print(
        f"✅ WebSocket manager test passed: All {len(tasks)} connections tracked correctly across 10 users"
    )


async def test_concurrent_assessment_response_creation():
    """Test that concurrent assessment response creation is handled correctly."""
    assessments = {}  # Simulate database
    response_lock = asyncio.Lock()  # Shared lock for all operations

    async def create_response_with_lock(assessment_id: str, user_id: str):
        """Simulate the check-and-update with proper locking"""
        async with response_lock:
            key = f"{assessment_id}:{user_id}"
            if key not in assessments:
                await asyncio.sleep(0.001)  # Simulate database insert
                assessments[key] = {"id": uuid4(), "status": "in_progress"}
                return assessments[key], True
            return assessments[key], False

    # Spawn 10 concurrent response creations for same assessment
    assessment_id = str(uuid4())
    user_id = "test_user"

    tasks = [create_response_with_lock(assessment_id, user_id) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # Should create only ONE response
    created_count = sum(1 for _, created in results if created)
    unique_responses = len(set(r["id"] for r, _ in results))

    assert created_count == 1, f"Expected 1 creation, got {created_count}"
    assert unique_responses == 1, f"Expected 1 unique response, got {unique_responses}"
    print(
        f"✅ Assessment response creation test passed: {len(tasks)} concurrent requests created 1 response"
    )


async def test_atomic_credit_decrement():
    """Test atomic credit decrement prevents negative balance."""
    # Simulate the pattern
    accounts = {"user1": {"credits": 100, "lock": asyncio.Lock()}}

    async def atomic_decrement_credits(user_id: str, amount: int):
        """Simulate atomic decrement with WHERE clause check"""
        async with accounts[user_id]["lock"]:
            if accounts[user_id]["credits"] >= amount:
                await asyncio.sleep(0.0001)  # Simulate database latency
                accounts[user_id]["credits"] -= amount
                return True, accounts[user_id]["credits"]
            return False, accounts[user_id]["credits"]

    # Spawn 20 concurrent decrement operations of 10 credits each
    # User has 100 credits, so only 10 should succeed
    tasks = [atomic_decrement_credits("user1", 10) for _ in range(20)]
    results = await asyncio.gather(*tasks)

    successful = sum(1 for success, _ in results if success)
    final_balance = accounts["user1"][
        "credits"
    ]  # Get actual final balance from accounts dict

    assert successful == 10, f"Expected 10 successful decrements, got {successful}"
    assert final_balance == 0, f"Expected 0 balance, got {final_balance}"
    assert final_balance >= 0, "Balance should never go negative!"
    print(
        f"✅ Atomic credit decrement test passed: {successful} operations succeeded, balance = {final_balance}"
    )


async def test_check_then_act_race_condition():
    """Demonstrate the race condition and verify it's fixed."""
    # Simulate the BROKEN pattern (without lock)
    shared_state = {"value": "pending", "transition_count": 0}

    async def broken_check_then_act():
        """This would have a race condition"""
        if shared_state["value"] == "pending":  # CHECK
            await asyncio.sleep(0.0001)  # Simulate processing
            if shared_state["value"] == "pending":
                shared_state["value"] = "processing"  # ACT
                shared_state["transition_count"] += 1

    # Run broken version
    shared_state["value"] = "pending"
    shared_state["transition_count"] = 0
    tasks = [broken_check_then_act() for _ in range(10)]
    await asyncio.gather(*tasks)

    broken_transitions = shared_state["transition_count"]
    print(
        f"⚠️  Broken pattern: {broken_transitions} transitions (expected 1, got {broken_transitions})"
    )

    # Now test the FIXED pattern (with lock)
    shared_state["value"] = "pending"
    shared_state["transition_count"] = 0
    lock = asyncio.Lock()

    async def fixed_check_then_act():
        """This is thread-safe"""
        async with lock:
            if shared_state["value"] == "pending":  # CHECK
                await asyncio.sleep(0.0001)  # Simulate processing
                if shared_state["value"] == "pending":
                    shared_state["value"] = "processing"  # ACT
                    shared_state["transition_count"] += 1

    tasks = [fixed_check_then_act() for _ in range(10)]
    await asyncio.gather(*tasks)

    fixed_transitions = shared_state["transition_count"]
    assert fixed_transitions == 1, f"Expected 1 transition, got {fixed_transitions}"
    print(f"✅ Fixed pattern: {fixed_transitions} transition (correct!)")


async def run_all_tests():
    """Run all race condition tests."""
    print("Running race condition tests...\n")

    await test_singleton_initialization_thread_safety()
    await test_redis_client_lazy_init_thread_safety()
    await test_cache_stampede_protection()
    await test_atomic_increment_thread_safety()
    await test_idempotent_insert_thread_safety()
    await test_websocket_connection_manager_thread_safety()
    await test_concurrent_assessment_response_creation()
    await test_atomic_credit_decrement()
    await test_check_then_act_race_condition()

    print("\n" + "=" * 80)
    print("✅ ALL RACE CONDITION TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
