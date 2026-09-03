#!/usr/bin/env python3
"""
Test script for Performance Monitoring System

Tests the monitoring endpoints and generates sample traffic for validation.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_monitoring_imports():
    """Test that all monitoring modules import correctly"""
    print("🔍 Testing monitoring module imports...")

    try:
        from app.monitoring.performance_dashboard import (
            PerformanceMonitor,
            PerformanceMonitoringMiddleware,
            get_performance_health_status,
            setup_sqlalchemy_monitoring,
        )

        print("✅ Performance monitoring imports successful")

        from app.api.v1.endpoints.performance_monitoring import router

        print("✅ Performance monitoring router imports successful")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_performance_monitor():
    """Test the PerformanceMonitor class"""
    print("\n🔍 Testing PerformanceMonitor class...")

    try:
        from app.monitoring.performance_dashboard import PerformanceMonitor

        monitor = PerformanceMonitor()

        # Test query tracking
        monitor.track_query("test_query", 0.05, 100)
        monitor.track_query("test_query", 0.08, 150)
        monitor.track_query("slow_query", 6.0, 10000)  # Should trigger alert

        # Test response time tracking
        monitor.track_response_time(0.1)
        monitor.track_response_time(0.2)
        monitor.track_response_time(0.15)

        # Test slow query tracking
        monitor.track_slow_query("SELECT * FROM huge_table", 8.5, 50000)

        # Get snapshot
        snapshot = monitor.get_snapshot()

        print(f"✅ Tracked {len(snapshot.query_metrics)} query patterns")
        print(f"✅ Detected {len(snapshot.slow_queries)} slow queries")
        print(f"✅ P50 response time: {snapshot.p50_response_time:.3f}s")

        return True
    except Exception as e:
        print(f"❌ PerformanceMonitor test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_health_status():
    """Test the health status function"""
    print("\n🔍 Testing performance health status...")

    try:
        from app.monitoring.performance_dashboard import get_performance_health_status

        status = get_performance_health_status()

        print(f"✅ Health status: {status['status']}")
        print(f"✅ Alerts: {len(status['alerts'])}")
        print(f"✅ Metrics available: {len(status['metrics'])} categories")

        return True
    except Exception as e:
        print(f"❌ Health status test failed: {e}")
        return False


async def test_endpoints_with_server():
    """Test endpoints against running server"""
    print("\n🔍 Testing monitoring endpoints...")

    import httpx

    base_url = "http://localhost:8000"

    # Test endpoints (without auth first, will likely get 403)
    endpoints = [
        ("/health", "Health check"),
        ("/api/v1/monitoring/health", "Performance health"),
        ("/api/v1/monitoring/performance", "Performance snapshot"),
        ("/api/v1/monitoring/slow-queries", "Slow queries"),
    ]

    results = []
    for endpoint, name in endpoints:
        try:
            response = httpx.get(f"{base_url}{endpoint}", timeout=5.0)

            if response.status_code == 200:
                print(f"✅ {name}: {response.status_code} OK")
                results.append(True)
            elif response.status_code == 403:
                print(
                    f"⚠️  {name}: {response.status_code} (expected - needs admin auth)"
                )
                results.append(True)  # Expected behavior
            elif response.status_code == 404:
                print(f"❌ {name}: {response.status_code} (endpoint not found)")
                results.append(False)
            else:
                print(f"⚠️  {name}: {response.status_code}")
                results.append(True)
        except httpx.ConnectError:
            print(f"⚠️  {name}: Server not running (skipping endpoint tests)")
            return None
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results.append(False)

    return all(results) if results else None


def generate_sample_traffic():
    """Generate sample traffic to populate metrics"""
    print("\n🔍 Generating sample traffic...")

    try:
        from app.monitoring.performance_dashboard import PerformanceMonitor

        monitor = PerformanceMonitor()

        # Simulate various query patterns
        queries = [
            ("SELECT", 0.01, 10),
            ("SELECT", 0.015, 15),
            ("SELECT", 0.02, 20),
            ("INSERT", 0.03, 1),
            ("UPDATE", 0.025, 5),
            ("DELETE", 0.015, 3),
        ]

        for query, time_taken, rows in queries:
            monitor.track_query(query, time_taken, rows)

        # Simulate slow queries
        monitor.track_slow_query(
            "SELECT * FROM responses WHERE user_id = ...", 5.2, 15000
        )
        monitor.track_slow_query("SELECT * FROM assessments", 6.8, 5000)

        # Simulate response times
        import random

        for _ in range(100):
            response_time = random.uniform(0.05, 0.3)
            monitor.track_response_time(response_time)

        snapshot = monitor.get_snapshot()

        print(f"✅ Generated {len(snapshot.query_metrics)} query patterns")
        print(f"✅ Generated {len(snapshot.slow_queries)} slow queries")
        print(f"✅ Generated sample response times")
        print(
            f"✅ P50: {snapshot.p50_response_time:.3f}s, P95: {snapshot.p95_response_time:.3f}s"
        )

        return True
    except Exception as e:
        print(f"❌ Traffic generation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Performance Monitoring System Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(test_monitoring_imports())

    # Test 2: PerformanceMonitor class
    results.append(test_performance_monitor())

    # Test 3: Health status
    results.append(test_health_status())

    # Test 4: Generate sample traffic
    results.append(generate_sample_traffic())

    # Test 5: Endpoints (if server is running)
    endpoint_result = asyncio.run(test_endpoints_with_server())
    if endpoint_result is not None:
        results.append(endpoint_result)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
