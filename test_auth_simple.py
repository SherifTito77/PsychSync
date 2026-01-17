#!/usr/bin/env python3
"""Simple authentication test"""

import requests
import json

API_URL = "http://localhost:8000"

def test_auth():
    print("Testing authentication...")

    # Test 1: Registration with correct schema
    print("\n1. Testing registration...")
    register_data = {
        "email": "simpletest@example.com",
        "password": "SecurePass123!",
        "full_name": "Simple Test User"
    }

    try:
        response = requests.post(f"{API_URL}/api/v1/register", json=register_data)
        print(f"Registration status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Registration successful")
        else:
            print("❌ Registration failed")

    except Exception as e:
        print(f"❌ Registration error: {e}")

    # Test 2: Login
    print("\n2. Testing login...")
    login_data = {
        "username": "simpletest@example.com",  # OAuth2 uses username field
        "password": "SecurePass123!"
    }

    try:
        response = requests.post(f"{API_URL}/api/v1/token", data=login_data)
        print(f"Login status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                token = token_data["access_token"]
                print(f"✅ Login successful, token: {token[:50]}...")

                # Test 3: Protected route
                print("\n3. Testing protected route...")
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{API_URL}/api/v1/users/me", headers=headers)
                print(f"Profile status: {profile_response.status_code}")
                print(f"Profile response: {profile_response.text}")

                if profile_response.status_code == 200:
                    print("✅ Protected route accessible")
                else:
                    print("❌ Protected route failed")
            else:
                print("❌ Login response missing token")
        else:
            print("❌ Login failed")

    except Exception as e:
        print(f"❌ Login error: {e}")

if __name__ == "__main__":
    test_auth()
