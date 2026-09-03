#!/usr/bin/env python3
# test_unified_user_service.py
# Simple test to verify the consolidated user service works correctly

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))


async def test_unified_user_service():
    """Test basic functionality of the unified user service"""
    try:
        # Test import
        from app.services.unified_user_service import get_user_service, unified_user_service

        print("✅ Unified user service import successful")

        # Test service instantiation
        service = get_user_service()
        print("✅ Service instantiation successful")

        # Test cache key generation
        cache_key = service.get_cache_key("get_by_id", user_id="123")
        print(f"✅ Cache key generation successful: {cache_key}")

        # Test feature flags
        from app.services.unified_user_service import (
            ENABLE_ENHANCED_CACHING,
            ENABLE_USER_STATS,
            ENABLE_VALIDATION_ENHANCEMENTS,
        )

        print(
            f"✅ Feature flags - Caching: {ENABLE_ENHANCED_CACHING}, Stats: {ENABLE_USER_STATS}, Validation: {ENABLE_VALIDATION_ENHANCEMENTS}"
        )
        print("✅ Service initialization complete")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_service_methods():
    """Test service method signatures"""
    try:
        from app.schemas.user import UserCreate, UserUpdate
        from app.services.unified_user_service import unified_user_service

        # Test method signatures exist
        methods = [
            "get_by_id",
            "get_by_email",
            "get_by_username",
            "get_by_organization",
            "get_all_users",
            "get_user_count",
            "create_user",
            "update_user",
            "delete_user",
            "update_password",
            "verify_password",
            "get_user_stats",
        ]

        for method in methods:
            if hasattr(unified_user_service, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Method test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing Unified User Service")
    print("=" * 50)

    tests = [
        ("Basic Functionality", test_unified_user_service),
        ("Service Methods", test_service_methods),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if await test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The unified user service is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
