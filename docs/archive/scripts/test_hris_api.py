#!/usr/bin/env python3
"""
HRIS API Integration Test Script
Tests all HRIS connector endpoints with the demo OrangeHRM connector
"""

import json
from typing import Any, Dict

import requests

# Configuration
BASE_URL = "http://localhost:8000"
HRIS_PREFIX = "/api/v1/hris"


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


def print_response(response: requests.Response, title: str = ""):
    """Print formatted API response"""
    print(f"\n{title}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)


def test_health():
    """Test 1: Backend Health Check"""
    print_section("Test 1: Backend Health Check")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        print_response(response, "Health Endpoint Response")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_hris_connection_setup():
    """Test 2: HRIS Connection Setup"""
    print_section("Test 2: HRIS Connection Setup (Demo Mode)")

    payload = {
        "provider": "orangehrm-demo",
        "organization_id": "demo-org-123",
        "connection_parameters": {"demo_mode": True},
    }

    try:
        response = requests.post(
            f"{BASE_URL}{HRIS_PREFIX}/connection/setup", json=payload, timeout=10
        )
        print_response(response, "Connection Setup Response")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Connection setup failed: {e}")
        return False


def test_get_employees():
    """Test 3: Get Employee Data"""
    print_section("Test 3: Get Employee Data")

    payload = {
        "provider": "orangehrm-demo",
        "organization_id": "demo-org-123",
        "filters": {},
        "include_terminated": False,
    }

    try:
        response = requests.post(
            f"{BASE_URL}{HRIS_PREFIX}/employees", json=payload, timeout=10
        )
        print_response(response, "Employee Data Response")

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("employees"):
                print(f"\n✅ Found {len(data['data']['employees'])} employees")
                return True

        return False
    except Exception as e:
        print(f"❌ Get employees failed: {e}")
        return False


def test_hris_analytics():
    """Test 4: HRIS Analytics"""
    print_section("Test 4: HRIS Analytics")

    payload = {
        "provider": "orangehrm-demo",
        "organization_id": "demo-org-123",
        "analytics_types": ["headcount", "turnover", "department_distribution"],
        "time_period_days": 30,
    }

    try:
        response = requests.post(
            f"{BASE_URL}{HRIS_PREFIX}/analytics", json=payload, timeout=10
        )
        print_response(response, "Analytics Response")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Analytics request failed: {e}")
        return False


def main():
    """Run all HRIS API tests"""
    print_section("PsychSync HRIS Connector API Test Suite")
    print("Testing OrangeHRM Demo Connector Integration")
    print(f"Backend: {BASE_URL}")

    tests = [
        ("Health Check", test_health),
        ("Connection Setup", test_hris_connection_setup),
        ("Get Employees", test_get_employees),
        ("HRIS Analytics", test_hris_analytics),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print_section("Test Results Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
