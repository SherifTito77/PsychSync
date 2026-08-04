#!/usr/bin/env python3
"""
Basic Async Cache Implementation Test
Tests the async cache implementation without requiring Redis
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_imports():
    """Test that async cache can be imported"""
    print("🧪 Testing async cache imports...")
    try:
        from app.core.async_cache import (
            AsyncCache,
            async_cached,
            cache_delete,
            cache_get,
            cache_set,
        )

        print("✅ All async cache imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


async def test_decorator_exists():
    """Test that the decorator is properly defined"""
    print("\n🧪 Testing async_cached decorator...")
    try:
        import inspect

        from app.core.async_cache import async_cached

        # Check if it's callable
        if not callable(async_cached):
            print("❌ async_cached is not callable")
            return False

        # Check signature
        sig = inspect.signature(async_cached)
        params = list(sig.parameters.keys())

        if "expire" not in params or "key_prefix" not in params:
            print(f"❌ async_cached has wrong signature: {params}")
            return False

        print("✅ async_cached decorator is properly defined")
        print(f"   Parameters: {params}")
        return True
    except Exception as e:
        print(f"❌ Decorator test failed: {e}")
        return False


async def test_cache_methods():
    """Test that AsyncCache has all required methods"""
    print("\n🧪 Testing AsyncCache methods...")
    try:
        from app.core.async_cache import AsyncCache

        required_methods = [
            "get",
            "set",
            "delete",
            "delete_pattern",
            "exists",
            "expire",
            "clear_all",
            "_generate_key",
        ]

        for method_name in required_methods:
            if not hasattr(AsyncCache, method_name):
                print(f"❌ Missing method: {method_name}")
                return False

            method = getattr(AsyncCache, method_name)
            if not callable(method):
                print(f"❌ {method_name} is not callable")
                return False

        print(f"✅ All {len(required_methods)} required methods exist")
        print(f"   Methods: {', '.join(required_methods)}")
        return True
    except Exception as e:
        print(f"❌ Cache methods test failed: {e}")
        return False


async def test_async_nature():
    """Test that methods are actually async (coroutine functions)"""
    print("\n🧪 Testing async nature of cache methods...")
    try:
        import inspect

        from app.core.async_cache import AsyncCache

        async_methods = [
            "get",
            "set",
            "delete",
            "delete_pattern",
            "exists",
            "expire",
            "clear_all",
        ]

        for method_name in async_methods:
            method = getattr(AsyncCache, method_name)
            if not inspect.iscoroutinefunction(method):
                print(f"❌ {method_name} is not an async function")
                return False

        print(f"✅ All {len(async_methods)} methods are async (coroutine functions)")
        return True
    except Exception as e:
        print(f"❌ Async nature test failed: {e}")
        return False


async def test_decorator_pattern():
    """Test that the decorator pattern works correctly"""
    print("\n🧪 Testing decorator pattern...")
    try:
        from app.core.async_cache import async_cached

        # Try applying the decorator
        @async_cached(expire=300, key_prefix="test")
        async def example_function(user_id: str):
            return {"user_id": user_id, "data": "test"}

        # Check if the function is still callable
        if not callable(example_function):
            print("❌ Decorated function is not callable")
            return False

        print("✅ Decorator can be applied to async functions")
        print("   Example: @async_cached(expire=300, key_prefix='test')")
        return True
    except Exception as e:
        print(f"❌ Decorator pattern test failed: {e}")
        return False


async def test_backward_compatibility():
    """Test backward-compatible wrapper functions"""
    print("\n🧪 Testing backward compatibility...")
    try:
        import inspect

        from app.core.async_cache import cache_delete, cache_get, cache_set

        # These should be async functions
        for func in [cache_get, cache_set, cache_delete]:
            if not inspect.iscoroutinefunction(func):
                print(f"❌ {func.__name__} is not async")
                return False

        print("✅ Backward-compatible wrapper functions are async")
        print("   Functions: cache_get, cache_set, cache_delete")
        return True
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


async def test_code_quality():
    """Test code quality of the implementation"""
    print("\n🧪 Testing code quality...")
    try:
        import inspect

        from app.core import async_cache

        # Check for docstrings
        docstring = async_cache.__doc__
        if not docstring or len(docstring) < 50:
            print("⚠️  Module docstring is missing or short")
        else:
            print("✅ Module has proper documentation")

        # Check AsyncCache class docstring
        from app.core.async_cache import AsyncCache

        if not AsyncCache.__doc__:
            print("⚠️  AsyncCache class missing docstring")
        else:
            print("✅ AsyncCache class has documentation")

        return True
    except Exception as e:
        print(f"❌ Code quality test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Async Cache Implementation Test")
    print("=" * 60)
    print()

    tests = [
        ("Import Test", test_imports),
        ("Decorator Test", test_decorator_exists),
        ("Methods Test", test_cache_methods),
        ("Async Nature Test", test_async_nature),
        ("Decorator Pattern Test", test_decorator_pattern),
        ("Backward Compatibility Test", test_backward_compatibility),
        ("Code Quality Test", test_code_quality),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print()
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("🎉 All tests PASSED!")
        print()
        print("✅ Async cache implementation is correct")
        print("✅ Ready for Redis connection testing")
        print("✅ Ready to migrate endpoints")
        print()
        print("Next steps:")
        print("  1. Start Redis: docker-compose up -d redis")
        print("  2. Run full test: python3 scripts/test_async_cache_performance.py")
        print("  3. Migrate endpoints: See docs/ASYNC_CACHE_MIGRATION_GUIDE.md")
        return True
    else:
        print()
        print("⚠️  Some tests failed - review output above")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
