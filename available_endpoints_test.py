#!/usr/bin/env python3

import requests
import json

def test_available_endpoints():
    """Test all available endpoints to find working login routes"""

    base_url = "http://localhost:8000"

    print("🔍 Testing Available API Endpoints...\n")

    # Test the main API routes that should be available
    test_endpoints = [
        "/",
        "/api/v1/",
        "/api/v1/health",
        "/api/v1/auth/token",
        "/api/v1/auth/login",
        "/api/v1/auth/token-login",
        "/api/v1/token",
        "/api/v1/login",
        "/auth/token",
        "/auth/login",
        "/token",
        "/login"
    ]

    working_endpoints = []

    for endpoint in test_endpoints:
        try:
            print(f"📍 Testing {endpoint}...")

            # First try GET
            response = requests.get(f"{base_url}{endpoint}", timeout=5)

            if response.status_code != 404:
                method = "GET"
                status = response.status_code
                working_endpoints.append({
                    "endpoint": endpoint,
                    "method": method,
                    "status": status
                })
                print(f"   ✅ GET {endpoint} - Status: {status}")
            else:
                # Try POST if GET returns 404
                response = requests.post(f"{base_url}{endpoint}",
                                       data={"username": "test", "password": "test"},
                                       timeout=5)

                if response.status_code != 404:
                    method = "POST"
                    status = response.status_code
                    working_endpoints.append({
                        "endpoint": endpoint,
                        "method": method,
                        "status": status
                    })
                    print(f"   ✅ POST {endpoint} - Status: {status}")
                else:
                    print(f"   ❌ {endpoint} - Not Found")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ {endpoint} - Error: {str(e)[:50]}...")

    print(f"\n🎯 Found {len(working_endpoints)} working endpoints:\n")

    for endpoint in working_endpoints:
        print(f"   {endpoint['method']} {endpoint['endpoint']} (Status: {endpoint['status']})")

    # Test authentication endpoints specifically
    print(f"\n🔐 Testing Authentication Endpoints in detail:\n")

    auth_endpoints = [ep for ep in working_endpoints if 'auth' in ep['endpoint'] or 'token' in ep['endpoint'] or 'login' in ep['endpoint']]

    for auth_ep in auth_endpoints:
        print(f"🔍 Testing {auth_ep['method']} {auth_ep['endpoint']}...")

        try:
            if auth_ep['method'] == 'POST':
                # Try form data
                response = requests.post(f"{base_url}{auth_ep['endpoint']}",
                                       data={"username": "admin@example.com", "password": "admin123"},
                                       headers={"Content-Type": "application/x-www-form-urlencoded"},
                                       timeout=5)

                print(f"   📊 Form data - Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ Login successful!")
                    try:
                        data = response.json()
                        print(f"   📄 Response keys: {list(data.keys())}")
                        if 'access_token' in data:
                            print(f"   🔑 Token found: {data['access_token'][:20]}...")
                    except:
                        print(f"   📄 Response: {response.text[:100]}...")
                elif response.status_code != 404:
                    print(f"   📄 Response: {response.text[:100]}...")

                # Try JSON data
                response = requests.post(f"{base_url}{auth_ep['endpoint']}",
                                       json={"username": "admin@example.com", "password": "admin123"},
                                       timeout=5)

                print(f"   📊 JSON data - Status: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")

if __name__ == "__main__":
    test_available_endpoints()
