"""
File: test_cache_setup.py (place in project root)
Test script to verify Redis caching is working correctly
Run this after setting up Redis: python test_cache_setup.py
"""

import sys
import time
from app.core.cache import (
    redis_client, 
    cache_set, 
    cache_get, 
    cache_delete,
    cache_delete_pattern,
    cached,
    redis_health_check
)


def test_redis_connection():
    """Test 1: Redis Connection"""
    print("\n" + "="*60)
    print("TEST 1: Redis Connection")
    print("="*60)
    
    if redis_client is None:
        print("❌ FAILED: Redis client is None")
        print("   Make sure Redis is installed and running:")
        print("   brew install redis")
        print("   brew services start redis")
        return False
    
    try:
        response = redis_client.ping()
        if response:
            print("✅ PASSED: Redis is connected and responsive")
            return True
        else:
            print("❌ FAILED: Redis ping returned False")
            return False
    except Exception as e:
        print(f"❌ FAILED: Redis connection error: {e}")
        return False


def test_basic_cache_operations():
    """Test 2: Basic Cache Operations"""
    print("\n" + "="*60)
    print("TEST 2: Basic Cache Operations")
    print("="*60)
    
    # Test SET
    key = "test:basic_operation"
    value = {"message": "Hello from cache!", "timestamp": time.time()}
    
    print(f"Setting cache: {key} = {value}")
    success = cache_set(key, value, expire=60)
    
    if not success:
        print("❌ FAILED: Could not set cache value")
        return False
    
    print("✅ Cache set successfully")
    
    # Test GET
    print(f"Getting cache: {key}")
    retrieved = cache_get(key)
    
    if retrieved is None:
        print("❌ FAILED: Could not retrieve cache value")
        return False
    
    if retrieved == value:
        print(f"✅ Retrieved correct value: {retrieved}")
    else:
        print(f"❌ FAILED: Retrieved value doesn't match. Got: {retrieved}")
        return False
    
    # Test DELETE
    print(f"Deleting cache: {key}")
    cache_delete(key)
    
    retrieved_after_delete = cache_get(key)
    if retrieved_after_delete is None:
        print("✅ Cache deleted successfully")
        return True
    else:
        print("❌ FAILED: Cache value still exists after delete")
        return False


def test_cached_decorator():
    """Test 3: @cached Decorator"""
    print("\n" + "="*60)
    print("TEST 3: @cached Decorator")
    print("="*60)
    
    call_count = 0
    
    @cached(expire=60, key_prefix="test")
    def expensive_function(x, y):
        nonlocal call_count
        call_count += 1
        print(f"  → Function called (call #{call_count})")
        time.sleep(0.1)  # Simulate expensive operation
        return x + y
    
    # First call - should execute function
    print("First call to expensive_function(5, 10):")
    start = time.time()
    result1 = expensive_function(5, 10)
    time1 = time.time() - start
    print(f"  Result: {result1}, Time: {time1:.3f}s, Calls: {call_count}")
    
    # Second call - should use cache
    print("\nSecond call to expensive_function(5, 10):")
    start = time.time()
    result2 = expensive_function(5, 10)
    time2 = time.time() - start
    print(f"  Result: {result2}, Time: {time2:.3f}s, Calls: {call_count}")
    
    # Verify results
    if result1 == result2 == 15:
        print("✅ Results are correct")
    else:
        print(f"❌ FAILED: Incorrect results. Got {result1} and {result2}")
        return False
    
    if call_count == 1:
        print("✅ Function only called once (cache working)")
    else:
        print(f"❌ FAILED: Function called {call_count} times (cache not working)")
        return False
    
    if time2 < time1 * 0.5:  # Cached call should be much faster
        print(f"✅ Cached call is faster ({time2:.3f}s vs {time1:.3f}s)")
    else:
        print(f"⚠️  WARNING: Cached call not significantly faster")
    
    # Clean up
    expensive_function.invalidate()
    return True


def test_pattern_deletion():
    """Test 4: Pattern-based Deletion"""
    print("\n" + "="*60)
    print("TEST 4: Pattern-based Deletion")
    print("="*60)
    
    # Set multiple keys with pattern
    keys = [
        "test:user:1",
        "test:user:2",
        "test:user:3",
        "test:team:1"
    ]
    
    for key in keys:
        cache_set(key, {"data": f"value for {key}"}, expire=60)
    
    print(f"Set {len(keys)} cache keys")
    
    # Delete pattern
    pattern = "test:user:*"
    deleted_count = cache_delete_pattern(pattern)
    
    print(f"Deleted {deleted_count} keys matching pattern '{pattern}'")
    
    # Verify
    user_keys_exist = any(cache_get(key) for key in keys[:3])
    team_key_exists = cache_get(keys[3]) is not None
    
    if not user_keys_exist and team_key_exists:
        print("✅ Pattern deletion working correctly")
        cache_delete(keys[3])  # Clean up
        return True
    else:
        print("❌ FAILED: Pattern deletion not working correctly")
        return False


def test_health_check():
    """Test 5: Health Check"""
    print("\n" + "="*60)
    print("TEST 5: Health Check")
    print("="*60)
    
    health = redis_health_check()
    print(f"Health check result: {health}")
    
    if health.get("status") == "healthy":
        print("✅ Redis health check passed")
        if "version" in health:
            print(f"   Redis version: {health['version']}")
        if "used_memory" in health:
            print(f"   Memory used: {health['used_memory']}")
        return True
    else:
        print("❌ FAILED: Redis health check failed")
        return False


def test_expiration():
    """Test 6: Cache Expiration"""
    print("\n" + "="*60)
    print("TEST 6: Cache Expiration")
    print("="*60)
    
    key = "test:expiration"
    value = {"expires": "soon"}
    
    print("Setting cache with 2 second expiration...")
    cache_set(key, value, expire=2)
    
    # Immediately retrieve
    retrieved1 = cache_get(key)
    if retrieved1 == value:
        print("✅ Value retrieved immediately after set")
    else:
        print("❌ FAILED: Could not retrieve value immediately")
        return False
    
    # Wait for expiration
    print("Waiting 3 seconds for expiration...")
    time.sleep(3)
    
    retrieved2 = cache_get(key)
    if retrieved2 is None:
        print("✅ Value expired correctly")
        return True
    else:
        print("❌ FAILED: Value did not expire")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PSYCHSYNC REDIS CACHE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Basic Cache Operations", test_basic_cache_operations),
        ("@cached Decorator", test_cached_decorator),
        ("Pattern Deletion", test_pattern_deletion),
        ("Health Check", test_health_check),
        ("Cache Expiration", test_expiration)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Redis caching is working correctly.")
        print("\nNext steps:")
        print("1. Update your service files to use caching")
        print("2. Test with your actual application")
        print("3. Monitor cache hit rates in production")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed.")
        print("\nTroubleshooting:")
        print("1. Make sure Redis is installed: brew install redis")
        print("2. Make sure Redis is running: brew services start redis")
        print("3. Check Redis status: redis-cli ping (should return PONG)")
        print("4. Check your .env file has correct REDIS_HOST and REDIS_PORT")
        return 1


if __name__ == "__main__":
    sys.exit(main())
    
    
    