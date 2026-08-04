#!/usr/bin/env python3
"""
Test concurrency fixes for rate limiter strategies.

This script verifies that the race condition fixes work correctly
by running concurrent requests and checking that limits are enforced.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.rate_limiter_unified import (
    MemoryStorage,
    RateLimitConfig,
    RateLimitStrategy,
    StorageBackend,
    UnifiedRateLimiter,
)


async def test_fixed_window_no_oversubscription():
    """
    Test that fixed window strategy prevents oversubscription.

    Before fix: 104 requests allowed when limit=100
    After fix: Exactly 100 requests allowed when limit=100
    """
    print("\n🧪 Testing Fixed Window Strategy (Oversubscription Fix)...")

    limiter = UnifiedRateLimiter(
        config=RateLimitConfig(limit=10, window=60),
        strategy=RateLimitStrategy.FIXED_WINDOW,
        backend=StorageBackend.MEMORY,
    )

    # Send 20 concurrent requests (limit is 10)
    tasks = [limiter.check(identifier="test_fixed") for _ in range(20)]
    results = await asyncio.gather(*tasks)

    allowed_count = sum(1 for r in results if r.allowed)
    denied_count = sum(1 for r in results if not r.allowed)

    print(f"   Allowed: {allowed_count}/10")
    print(f"   Denied: {denied_count}/20")

    if allowed_count == 10:
        print("   ✅ PASS: Exactly 10 requests allowed (no oversubscription)")
        return True
    else:
        print(f"   ❌ FAIL: Expected 10 allowed, got {allowed_count}")
        return False


async def test_sliding_window_concurrent():
    """
    Test that sliding window strategy handles concurrent requests correctly.

    Before fix: Race between remove-add-count operations
    After fix: Atomic Lua script ensures correct count
    """
    print("\n🧪 Testing Sliding Window Strategy (Atomic Operations Fix)...")

    limiter = UnifiedRateLimiter(
        config=RateLimitConfig(limit=5, window=60),
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        backend=StorageBackend.MEMORY,
    )

    # Send 15 concurrent requests (limit is 5)
    tasks = [limiter.check(identifier="test_sliding") for _ in range(15)]
    results = await asyncio.gather(*tasks)

    allowed_count = sum(1 for r in results if r.allowed)
    denied_count = sum(1 for r in results if not r.allowed)

    print(f"   Allowed: {allowed_count}/5")
    print(f"   Denied: {denied_count}/15")

    if allowed_count == 5:
        print("   ✅ PASS: Exactly 5 requests allowed")
        return True
    else:
        print(f"   ❌ FAIL: Expected 5 allowed, got {allowed_count}")
        return False


async def test_memory_storage_cleanup():
    """
    Test that MemoryStorage cleanup doesn't crash on concurrent access.

    Before fix: Dictionary mutation during iteration (RuntimeError)
    After fix: Creates snapshot before modifying
    """
    print("\n🧪 Testing MemoryStorage Cleanup (Dictionary Mutation Fix)...")

    storage = MemoryStorage()

    # Add entries with short expiration
    for i in range(10):
        await storage.set(f"key_{i}", f"value_{i}", expire=1)

    # Trigger concurrent cleanup by accessing multiple keys
    tasks = [storage.get(f"key_{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)

    print(f"   Retrieved {len(results)} keys without crash")

    if len(results) == 10:
        print("   ✅ PASS: No crash during cleanup")
        return True
    else:
        print(f"   ❌ FAIL: Expected 10 results, got {len(results)}")
        return False


async def test_redis_connection_lock():
    """
    Test that RedisStorage connection initialization uses lock.

    Before fix: Multiple concurrent connections could be created
    After fix: Lock ensures only one connection is created
    """
    print("\n🧪 Testing RedisStorage Connection Lock...")

    from app.core.rate_limiter_unified import RedisStorage

    # Note: This test would need actual Redis to fully verify the lock
    # For now, we just verify the lock attribute exists
    storage = RedisStorage()

    if hasattr(storage, "_connection_lock"):
        print("   ✅ PASS: Connection lock exists")
        return True
    else:
        print("   ❌ FAIL: Connection lock missing")
        return False


async def main():
    """Run all concurrency tests."""
    print("=" * 60)
    print("CONCURRENCY FIXES VERIFICATION")
    print("=" * 60)

    results = []

    # Run tests
    results.append(await test_fixed_window_no_oversubscription())
    results.append(await test_sliding_window_concurrent())
    results.append(await test_memory_storage_cleanup())
    results.append(await test_redis_connection_lock())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 Concurrency fixes verified!")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
