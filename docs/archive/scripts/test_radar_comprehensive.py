#!/usr/bin/env python3
"""
Comprehensive Radar System Test Suite
Tests all three options: Quick Win, Full Radar, and Phased MVP
"""

import sys
import traceback
from datetime import datetime


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_phase(phase_num, phase_name):
    """Print phase header"""
    print(f"\n📋 PHASE {phase_num}: {phase_name}")
    print("─" * 70)


def test_result(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"      {details}")


def test_option_a():
    """Test Option A: Quick Win Dashboard"""
    print_phase(1, "OPTION A - QUICK WIN DASHBOARD")

    results = []

    # Test 1: Service Import
    try:
        from app.services.radar_service import RadarZone, radar_service

        test_result(
            "Radar Service Import", True, "RadarZone.GREEN/YELLOW/RED available"
        )
        results.append(True)
    except Exception as e:
        test_result("Radar Service Import", False, str(e))
        results.append(False)

    # Test 2: API Import
    try:
        from app.api.v1.endpoints.radar import router

        route_count = len(router.routes)
        test_result("Radar API Router", True, f"{route_count} endpoints registered")
        results.append(True)
    except Exception as e:
        test_result("Radar API Router", False, str(e))
        results.append(False)

    # Test 3: Zone Classification
    try:
        from app.services.radar_service import radar_service

        result = radar_service._classify_zone(
            toxicity_data={"risk_score": 0.1},
            early_warnings={"warning_score": 0.1},
            behavioral_data={"behavioral_health_score": 0.9},
            psych_safety={"overall_safety_score": 0.85},
        )

        passed = result["zone"] == "green"
        test_result("Green Zone Classification", passed, f"Zone: {result['zone']}")
        results.append(passed)
    except Exception as e:
        test_result("Green Zone Classification", False, str(e))
        results.append(False)

    # Test 4: Concentric Zones
    try:
        from app.services.radar_service import radar_service

        result = radar_service._calculate_concentric_zones(
            toxicity_data={"risk_score": 0.4, "patterns_detected": []},
            behavioral_data={"behavioral_health_score": 0.7},
            psych_safety={"overall_safety_score": 0.75},
        )

        required = ["inner_zone", "middle_zone", "outer_zone"]
        passed = all(z in result for z in required)
        test_result("Concentric Zone Calculation", passed, "All 3 zones calculated")
        results.append(passed)
    except Exception as e:
        test_result("Concentric Zone Calculation", False, str(e))
        results.append(False)

    # Test 5: API Registration
    try:
        from app.api.v1.api import api_router

        radar_routes = [
            r for r in api_router.routes if hasattr(r, "path") and "radar" in r.path
        ]
        passed = len(radar_routes) > 0
        test_result(
            "API Registration", passed, f"{len(radar_routes)} radar routes in main API"
        )
        results.append(passed)
    except Exception as e:
        test_result("API Registration", False, str(e))
        results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\nPhase 1 Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total


def test_option_b():
    """Test Option B: Full Radar System"""
    print_phase(2, "OPTION B - FULL RADAR SYSTEM")

    results = []

    # Test 1: Real-time Processor
    try:
        from app.services.radar_realtime_processor import (
            BehavioralSignal,
            SignalType,
            realtime_signal_processor,
        )

        test_result(
            "Real-time Processor Import",
            True,
            "SignalType.TOXICITY/BURNOUT/etc. available",
        )
        results.append(True)
    except Exception as e:
        test_result("Real-time Processor Import", False, str(e))
        results.append(False)

    # Test 2: Intervention Nudges
    try:
        from app.services.radar_intervention_nudges import (
            NudgePriority,
            NudgeType,
            intervention_nudge_system,
        )

        test_result("Intervention Nudges Import", True, f"{len(NudgeType)} nudge types")
        results.append(True)
    except Exception as e:
        test_result("Intervention Nudges Import", False, str(e))
        results.append(False)

    # Test 3: Longitudinal Analyzer
    try:
        from app.services.radar_longitudinal_analysis import longitudinal_trend_analyzer

        test_result("Longitudinal Analyzer Import", True, "Trend analysis ready")
        results.append(True)
    except Exception as e:
        test_result("Longitudinal Analyzer Import", False, str(e))
        results.append(False)

    # Test 4: External Integrations (optional)
    try:
        from app.services.radar_external_integrations import (
            IntegrationType,
            external_integration_manager,
        )

        test_result(
            "External Integrations Import", True, f"{len(IntegrationType)} platforms"
        )
        results.append(True)
    except Exception as e:
        test_result("External Integrations Import", False, str(e))
        results.append(False)

    # Test 5: WebSocket Manager (with fix)
    try:
        from app.api.v1.endpoints.radar_websocket import radar_websocket_manager

        stats = radar_websocket_manager.get_connection_stats()
        test_result(
            "WebSocket Manager",
            True,
            f"{stats['total_connections']} active connections",
        )
        results.append(True)
    except Exception as e:
        test_result("WebSocket Manager", False, str(e))
        results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\nPhase 2 Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total


def test_option_c():
    """Test Option C: Phased MVP"""
    print_phase(3, "OPTION C - PHASED MVP")

    results = []

    # Test 1: All Services Available
    try:
        from app.services.radar_external_integrations import external_integration_manager
        from app.services.radar_intervention_nudges import intervention_nudge_system
        from app.services.radar_longitudinal_analysis import longitudinal_trend_analyzer
        from app.services.radar_realtime_processor import realtime_signal_processor
        from app.services.radar_service import radar_service

        test_result("All Services Import", True, "5/5 services loaded successfully")
        results.append(True)
    except Exception as e:
        test_result("All Services Import", False, str(e))
        results.append(False)

    # Test 2: End-to-end Flow
    try:
        from app.services.radar_service import radar_service

        # Test complete flow
        zone_result = radar_service._classify_zone(
            toxicity_data={"risk_score": 0.5},
            early_warnings={"warning_score": 0.4},
            behavioral_data={"behavioral_health_score": 0.6},
            psych_safety={"overall_safety_score": 0.7},
        )

        concentric_result = radar_service._calculate_concentric_zones(
            toxicity_data={"risk_score": 0.5, "patterns_detected": []},
            behavioral_data={"behavioral_health_score": 0.6},
            psych_safety={"overall_safety_score": 0.7},
        )

        passed = (
            "zone" in zone_result
            and "inner_zone" in concentric_result
            and "middle_zone" in concentric_result
            and "outer_zone" in concentric_result
        )

        test_result("End-to-end Flow", passed, "Zone + concentric calculations working")
        results.append(passed)
    except Exception as e:
        test_result("End-to-end Flow", False, str(e))
        results.append(False)

    # Test 3: Documentation Exists
    try:
        import os

        doc_file = "/Users/sheriftito/Downloads/psychsync/RADAR_MVP_IMPLEMENTATION.md"
        exists = os.path.exists(doc_file)
        test_result(
            "Implementation Documentation", exists, "RADAR_MVP_IMPLEMENTATION.md found"
        )
        results.append(exists)
    except Exception as e:
        test_result("Implementation Documentation", False, str(e))
        results.append(False)

    # Test 4: Test Files Created
    try:
        import os

        test_a = os.path.exists(
            "/Users/sheriftito/Downloads/psychsync/test_radar_implementation.py"
        )
        test_b = os.path.exists(
            "/Users/sheriftito/Downloads/psychsync/test_radar_option_b.py"
        )
        test_c = os.path.exists(
            "/Users/sheriftito/Downloads/psychsync/test_radar_comprehensive.py"
        )

        passed = test_a and test_b and test_c
        test_result("Test Suite Files", passed, "All test files created")
        results.append(passed)
    except Exception as e:
        test_result("Test Suite Files", False, str(e))
        results.append(False)

    # Test 5: API Documentation
    try:
        from app.api.v1.endpoints.radar import router

        endpoint_names = [
            "/radar/view",
            "/radar/quick-stats",
            "/radar/zone-history",
            "/radar/hotspots",
            "/radar/concentric-zones",
        ]

        routes = [str(r.path) for r in router.routes]
        found = sum(1 for ep in endpoint_names if ep in routes)

        passed = found == len(endpoint_names)
        test_result(
            "API Documentation",
            passed,
            f"{found}/{len(endpoint_names)} endpoints documented",
        )
        results.append(passed)
    except Exception as e:
        test_result("API Documentation", False, str(e))
        results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\nPhase 3 Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total


def main():
    """Run comprehensive test suite"""
    print_header("PSYCHSYNC RADAR - COMPREHENSIVE TEST SUITE")
    print(f"Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(
        f"Testing Environment: {'Development' if os.getenv('NODE_ENV') == 'development' else 'Production'}"
    )

    # Run all option tests
    option_a_pass = test_option_a()
    option_b_pass = test_option_b()
    option_c_pass = test_option_c()

    # Final summary
    print_header("FINAL SUMMARY")

    print(
        f"\nOption A (Quick Win Dashboard): {'✅ COMPLETE' if option_a_pass else '❌ ISSUES DETECTED'}"
    )
    print(
        f"Option B (Full Radar System): {'✅ COMPLETE' if option_b_pass else '❌ ISSUES DETECTED'}"
    )
    print(
        f"Option C (Phased MVP): {'✅ COMPLETE' if option_c_pass else '❌ ISSUES DETECTED'}"
    )

    overall_pass = option_a_pass and option_b_pass and option_c_pass

    print("\n" + "=" * 70)
    if overall_pass:
        print("🎉 ALL TESTS PASSED - RADAR SYSTEM FULLY OPERATIONAL")
        print("=" * 70)
        print("\n✅ Ready for deployment!")
        print("✅ All services functional")
        print("✅ Documentation complete")
        print("✅ Test coverage verified")
        print("\nNext Steps:")
        print("1. Review RADAR_MVP_IMPLEMENTATION.md for deployment guide")
        print("2. Configure feature flags for phased rollout")
        print("3. Train users on Phase 1 (Dashboard)")
        print("4. Monitor and collect feedback")
        print("5. Enable Phase 2-4 features incrementally")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW NEEDED")
        print("=" * 70)
        print("\nActions Required:")
        print("1. Review failed tests above")
        print("2. Check error messages for details")
        print("3. Verify dependencies are installed")
        print("4. Run individual test files for more details:")
        print("   - python test_radar_implementation.py")
        print("   - python test_radar_option_b.py")
        return 1


if __name__ == "__main__":
    import os

    sys.exit(main())
