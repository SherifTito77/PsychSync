#!/usr/bin/env python3
"""Authentication flow validation for PsychSync"""

import json
import random
import string

import requests

API_URL = "http://localhost:8000"


def generate_test_email():
    """Generate random test email"""
    return f"test_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"


def test_registration():
    """Test user registration"""
    print("1. Testing user registration...")

    test_email = generate_test_email()
    register_data = {
        "email": test_email,
        "password": "SecurePass123!",
        "name": "Test User",
    }

    try:
        response = requests.post(f"{API_URL}/api/v1/register", json=register_data)

        if response.status_code in [200, 201]:
            print("✅ Registration successful")
            return test_email
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None


def test_login(email):
    """Test user login"""
    print("2. Testing login...")

    login_data = {"username": email, "password": "SecurePass123!"}

    try:
        response = requests.post(f"{API_URL}/api/v1/token", data=login_data)

        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                print("✅ Login successful")
                return token_data["access_token"]
            else:
                print("❌ Login response missing token")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def test_protected_route(token):
    """Test access to protected route"""
    print("3. Testing protected route...")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(f"{API_URL}/api/v1/users/me", headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            if "email" in user_data:
                print("✅ Protected route accessible")
                return True
            else:
                print("❌ Protected route returned invalid data")
                return False
        else:
            print(f"❌ Protected route failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Protected route error: {e}")
        return False


def test_invalid_token():
    """Test that invalid tokens are rejected"""
    print("4. Testing invalid token rejection...")

    headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(f"{API_URL}/api/v1/users/me", headers=headers)

        if response.status_code == 401:
            print("✅ Invalid token properly rejected")
            return True
        else:
            print(f"❌ Invalid token not properly rejected: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Invalid token test error: {e}")
        return False


def main():
    """Run authentication validation tests"""
    print("🔐 PsychSync Authentication Validation")
    print("=" * 50)

    # Run tests
    test_email = test_registration()
    if not test_email:
        print("❌ Cannot proceed without successful registration")
        return 1

    token = test_login(test_email)
    if not token:
        print("❌ Cannot proceed without successful login")
        return 1

    protected_success = test_protected_route(token)
    invalid_token_success = test_invalid_token()

    print("\n" + "=" * 50)
    print("📊 AUTHENTICATION VALIDATION SUMMARY")
    print("=" * 50)

    results = [
        ("Registration", test_email is not None),
        ("Login", token is not None),
        ("Protected Route", protected_success),
        ("Invalid Token Rejection", invalid_token_success),
    ]

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 ALL AUTHENTICATION TESTS PASSED!")
        return 0
    else:
        print("❌ SOME AUTHENTICATION TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
