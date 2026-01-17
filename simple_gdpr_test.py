#!/usr/bin/env python3
"""
Simple GDPR Compliance Test
Tests the basic GDPR endpoints we've implemented
"""

import requests
import json
from datetime import datetime

def test_gdpr_endpoints():
    """Test GDPR compliance endpoints"""
    base_url = "http://localhost:8000"

    print("🔒 Testing GDPR Compliance Endpoints")
    print("=" * 50)

    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
        else:
            print(f"❌ Backend server returned: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return

    # Test 2: Basic GDPR endpoints that should work
    gdpr_endpoints = [
        "/api/v1/gdpr/data-retention-policy",
        "/api/v1/gdpr/processing-activities",
        "/api/v1/cookies/categories"
    ]

    results = []

    for endpoint in gdpr_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)

            result = {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": response.status_code in [200, 201],
                "response_size": len(response.content)
            }

            if response.status_code == 200:
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = "Invalid JSON"
            else:
                result["error"] = response.text[:200]

            results.append(result)

            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {endpoint}: HTTP {response.status_code} ({len(response.content)} bytes)")

        except Exception as e:
            results.append({
                "endpoint": endpoint,
                "status_code": None,
                "success": False,
                "error": str(e)
            })
            print(f"❌ {endpoint}: Error - {str(e)[:100]}")

    # Test 3: Data summary endpoint (requires auth)
    print("\n📊 Testing Data Summary (Public Version)")
    try:
        # Create a simplified data summary endpoint that doesn't require authentication
        response = requests.get(f"{base_url}/api/v1/gdpr/data-summary-public", timeout=10)

        if response.status_code == 200:
            print("✅ Public data summary endpoint working")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print("   Response: Invalid JSON format")
        else:
            print(f"❌ Public data summary endpoint: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ Public data summary test failed: {str(e)[:100]}")

    # Test 4: Cookie consent endpoint
    print("\n🍪 Testing Cookie Consent")
    try:
        consent_data = {
            "analytics": True,
            "marketing": False,
            "functional": True,
            "statistics": False,
            "user_agent": "GDPR Test Suite",
            "ip_address": "127.0.0.1"
        }

        response = requests.post(
            f"{base_url}/api/v1/cookies/consent",
            json=consent_data,
            timeout=10
        )

        if response.status_code in [200, 201]:
            print("✅ Cookie consent endpoint working")
            try:
                data = response.json()
                print(f"   Consent ID: {data.get('consent_id', 'N/A')}")
                print(f"   Status: {data.get('status', 'N/A')}")
            except:
                print("   Response: Invalid JSON format")
        else:
            print(f"❌ Cookie consent endpoint: HTTP {response.status_code}")
            print(f"   Error: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Cookie consent test failed: {str(e)[:100]}")

    # Summary
    print("\n📋 GDPR Compliance Test Summary")
    print("=" * 30)

    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)

    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")

    if successful_tests >= 3:
        print("✅ Basic GDPR compliance infrastructure is working")
    else:
        print("❌ GDPR compliance infrastructure needs improvement")

    print(f"\nTest completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    test_gdpr_endpoints()
