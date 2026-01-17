#!/usr/bin/env python3
"""Test available working endpoints"""

import requests
import json

API_URL = "http://localhost:8000"

# Get token from environment variable for security
import os
TOKEN = os.getenv('TEST_JWT_TOKEN', '')
if not TOKEN:
    print("WARNING: TEST_JWT_TOKEN environment variable not set. Tests will fail.")
    print("Run: export TEST_JWT_TOKEN=your_valid_jwt_token")

def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

def test_endpoints():
    """Test various endpoints to see what works"""
    print("🔍 Testing Available Endpoints")
    print("=" * 60)

    endpoints = [
        ("GET", "/api/v1/health/", "Health Check"),
        ("GET", "/api/v1/users/me", "User Profile"),
        ("GET", "/api/v1/admin/users", "Admin Users"),
        ("GET", "/api/v1/admin/dashboard", "Admin Dashboard"),
        ("GET", "/api/v1/teams/", "Teams List"),
        ("POST", "/api/v1/teams/", "Teams Create"),
        ("GET", "/api/v1/predictions/", "Predictions"),
        ("GET", "/api/v1/reliability-validity/", "Reliability Validity"),
    ]

    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", headers=get_headers())
            elif method == "POST":
                response = requests.post(f"{API_URL}{endpoint}", headers=get_headers(), json={"test": "data"})

            status_icon = "✅" if response.status_code == 200 else "❌" if response.status_code == 404 else "⚠️"
            print(f"{method:4} {endpoint:40} {response.status_code:4} {status_icon} {description}")

            if response.status_code not in [200, 404]:
                print(f"     Response: {response.text[:100]}...")

        except Exception as e:
            print(f"{method:4} {endpoint:40} ERR  ❌ {description}")
            print(f"     Error: {e}")

def main():
    test_endpoints()

if __name__ == "__main__":
    main()
