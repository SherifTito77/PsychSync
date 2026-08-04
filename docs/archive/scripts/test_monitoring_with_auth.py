#!/usr/bin/env python3
"""
Test monitoring endpoints with proper authentication
Uses your browser's session or login credentials
"""

import getpass

print("=" * 60)
print("Performance Monitoring API Test")
print("=" * 60)
print()

# Get credentials
email = (
    input("Enter your email (press Enter for sherif.tito.77@gmail.com): ")
    or "sherif.tito.77@gmail.com"
)
password = getpass.getpass("Enter your password: ")

print()
print("Logging in...")

import requests

# Login to get token
try:
    response = requests.post(
        "http://localhost:8000/api/v1/simple-login",
        json={"email": email, "password": password},
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            token = data["data"]["access_token"]
            print(f"✅ Login successful!")
            print(f"Token: {token[:50]}...")
            print()

            # Test endpoints
            endpoints = [
                ("Health Check", "/api/v1/monitoring/health"),
                ("Performance Metrics", "/api/v1/monitoring/performance"),
                ("Slow Queries", "/api/v1/monitoring/slow-queries?limit=5"),
            ]

            headers = {"Authorization": f"Bearer {token}"}

            for name, endpoint in endpoints:
                print(f"\n🔍 Testing: {name}")
                print(f"   Endpoint: {endpoint}")

                response = requests.get(
                    f"http://localhost:8080{endpoint}", headers=headers
                )

                if response.status_code == 200:
                    print(f"   ✅ Status: {response.status_code} OK")
                    data = response.json()
                    print(f"   Status: {data.get('status', 'N/A')}")

                    if "alerts" in data:
                        print(f"   Alerts: {len(data['alerts'])}")

                    if "metrics" in data:
                        metrics = data["metrics"]
                        if "response_times" in metrics:
                            rt = metrics["response_times"]
                            print(
                                f"   P95 Response Time: {rt.get('p95', 0)*1000:.1f}ms"
                            )
                        if "system_metrics" in metrics:
                            sys = metrics["system_metrics"]
                            print(f"   Memory: {sys.get('memory_usage_mb', 0):.1f} MB")
                else:
                    print(f"   ❌ Status: {response.status_code}")
                    print(f"   Error: {response.text[:200]}")

            print()
            print("=" * 60)
            print("✅ All tests complete!")
            print()
            print("Now you can access the dashboard at:")
            print("  http://localhost:5173/admin/performance")

        else:
            print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
    else:
        print(f"❌ Login failed with status {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
