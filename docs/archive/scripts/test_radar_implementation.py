#!/usr/bin/env python3
"""
Test script to validate Radar Dashboard Implementation (Option A)

Tests:
1. Backend service imports
2. API endpoint registration
3. Basic data flow
"""

import sys
import traceback


def test_radar_service_import():
    """Test that radar service can be imported"""
    try:
        from app.services.radar_service import RadarService, RadarZone, radar_service

        print("✅ Radar service imported successfully")
        print(f"   - RadarZone.GREEN = {RadarZone.GREEN}")
        print(f"   - RadarZone.YELLOW = {RadarZone.YELLOW}")
        print(f"   - RadarZone.RED = {RadarZone.RED}")
        return True
    except Exception as e:
        print(f"❌ Failed to import radar service: {e}")
        traceback.print_exc()
        return False


def test_radar_api_import():
    """Test that radar API endpoint can be imported"""
    try:
        from app.api.v1.endpoints.radar import router

        print("✅ Radar API router imported successfully")
        print(f"   - Router has {len(router.routes)} routes")
        for route in router.routes:
            print(f"   - {route.methods} {route.path}")
        return True
    except Exception as e:
        print(f"❌ Failed to import radar API: {e}")
        traceback.print_exc()
        return False


def test_api_registration():
    """Test that radar endpoint is registered in main API"""
    try:
        from app.api.v1.api import api_router

        radar_routes = [
            r for r in api_router.routes if hasattr(r, "path") and "radar" in r.path
        ]
        if radar_routes:
            print(
                f"✅ Radar endpoint registered in main API ({len(radar_routes)} routes found)"
            )
            return True
        else:
            print("⚠️  Radar endpoint not found in main API routes")
            return False
    except Exception as e:
        print(f"❌ Failed to check API registration: {e}")
        traceback.print_exc()
        return False


def test_service_methods():
    """Test that radar service has required methods"""
    try:
        from app.services.radar_service import radar_service

        methods = [
            "get_radar_view",
            "_get_early_warnings",
            "_get_behavioral_patterns",
            "_get_psychological_safety",
            "_get_active_interventions",
            "_classify_zone",
            "_calculate_concentric_zones",
        ]

        all_present = True
        for method in methods:
            if hasattr(radar_service, method):
                print(f"   ✅ {method} exists")
            else:
                print(f"   ❌ {method} missing")
                all_present = False

        if all_present:
            print("✅ All required service methods present")
        return all_present
    except Exception as e:
        print(f"❌ Failed to check service methods: {e}")
        traceback.print_exc()
        return False


def test_zone_classification():
    """Test zone classification logic"""
    try:
        from app.services.radar_service import radar_service

        # Test green zone (low risk)
        result = radar_service._classify_zone(
            toxicity_data={"risk_score": 0.1},
            early_warnings={"warning_score": 0.1},
            behavioral_data={"behavioral_health_score": 0.9},
            psych_safety={"overall_safety_score": 0.85},
        )

        if result["zone"] == "green":
            print("✅ Green zone classification works correctly")
        else:
            print(f"❌ Expected green zone, got {result['zone']}")
            return False

        # Test red zone (high risk)
        result = radar_service._classify_zone(
            toxicity_data={"risk_score": 0.8},
            early_warnings={"warning_score": 0.9},
            behavioral_data={"behavioral_health_score": 0.2},
            psych_safety={"overall_safety_score": 0.3},
        )

        if result["zone"] == "red":
            print("✅ Red zone classification works correctly")
        else:
            print(f"❌ Expected red zone, got {result['zone']}")
            return False

        return True
    except Exception as e:
        print(f"❌ Zone classification test failed: {e}")
        traceback.print_exc()
        return False


def test_concentric_zones():
    """Test concentric zone calculation"""
    try:
        from app.services.radar_service import radar_service

        result = radar_service._calculate_concentric_zones(
            toxicity_data={
                "risk_score": 0.4,
                "patterns_detected": [{"severity_score": 0.5}],
            },
            behavioral_data={"behavioral_health_score": 0.7},
            psych_safety={"overall_safety_score": 0.75},
        )

        required_zones = ["inner_zone", "middle_zone", "outer_zone"]
        all_present = all(zone in result for zone in required_zones)

        if all_present:
            print("✅ Concentric zones calculated correctly")
            print(
                f"   - Inner zone: {result['inner_zone']['zone']} ({result['inner_zone']['risk_score']:.2f})"
            )
            print(
                f"   - Middle zone: {result['middle_zone']['zone']} ({result['middle_zone']['risk_score']:.2f})"
            )
            print(
                f"   - Outer zone: {result['outer_zone']['zone']} ({result['outer_zone']['risk_score']:.2f})"
            )
            return True
        else:
            print("❌ Missing required zones")
            return False
    except Exception as e:
        print(f"❌ Concentric zones test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("RADAR DASHBOARD IMPLEMENTATION TEST (Option A)")
    print("=" * 70)
    print()

    tests = [
        ("Service Import", test_radar_service_import),
        ("API Import", test_radar_api_import),
        ("API Registration", test_api_registration),
        ("Service Methods", test_service_methods),
        ("Zone Classification", test_zone_classification),
        ("Concentric Zones", test_concentric_zones),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'─' * 70}")
        print(f"Testing: {name}")
        print(f"{'─' * 70}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Option A implementation is complete.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
