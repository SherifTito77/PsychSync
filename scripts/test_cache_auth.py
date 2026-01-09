#!/usr/bin/env python3
"""
Test Async Cache with Authentication
Creates a test user and makes authenticated requests to populate cache
"""

import requests
import subprocess
import time
import json

BASE_URL = "http://localhost:8000"

def register_test_user():
    """Register a test user"""
    print("📝 Registering test user...")

    headers = {
        "User-Agent": "CacheTest/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    user_data = {
        "email": "cache_test@example.com",
        "password": "TestPassword123!",
        "full_name": "Cache Test User",
        "is_active": True
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data, headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ User registered successfully")
            return True
        elif response.status_code == 400:
            print("ℹ️  User already exists (that's okay)")
            return True
        else:
            print(f"⚠️  Registration failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error registering user: {e}")
        return False

def login_test_user():
    """Login and get JWT token"""
    print("\n🔑 Logging in...")

    headers = {
        "User-Agent": "CacheTest/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    login_data = {
        "email": "cache_test@example.com",
        "password": "TestPassword123!"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token")
            if token:
                print("✅ Login successful")
                return token
            else:
                print("❌ No token in response")
                return None
        else:
            print(f"❌ Login failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error logging in: {e}")
        return None

def make_authenticated_request(token, endpoint):
    """Make authenticated request to cached endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "CacheTest/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
        return response.status_code
    except Exception as e:
        return None

def test_cache_endpoints(token):
    """Test all cached endpoints"""
    print("\n🔄 Testing cached endpoints (50 iterations)...")
    print()

    endpoints = [
        "/api/v1/users/me",
        "/api/v1/users/",
        "/api/v1/teams/",
        "/api/v1/assessments/",
    ]

    for i in range(50):
        for endpoint in endpoints:
            status = make_authenticated_request(token, endpoint)
            if status and status == 200:
                print(f"  Iteration {i+1}/50: {endpoint} - HTTP {status}", end="\r")

        time.sleep(0.1)  # Small delay between iterations

    print("\n\n✅ Cache warming complete!")

def show_cache_stats():
    """Display cache statistics"""
    print("\n📊 Current Cache Statistics:")
    print()

    result = subprocess.run(
        ["redis-cli", "INFO", "stats"],
        capture_output=True,
        text=True
    )

    hits = misses = 0
    for line in result.stdout.split('\n'):
        if 'keyspace_hits' in line:
            hits = int(line.split(':')[1])
        elif 'keyspace_misses' in line:
            misses = int(line.split(':')[1])

    total = hits + misses
    hit_rate = (hits / total * 100) if total > 0 else 0

    print(f"   Cache Hits:   {hits:,}")
    print(f"   Cache Misses: {misses:,}")
    print(f"   Hit Rate:     {hit_rate:.1f}%")
    print()

    if hit_rate >= 70:
        print("   ✅ EXCELLENT - Cache is working perfectly!")
    elif hit_rate >= 50:
        print("   ⚠️  GOOD - Cache is building up...")
    else:
        print("   ℹ️  Cache still warming up, make more requests")

def main():
    """Main test function"""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🧪 ASYNC CACHE AUTH TEST                                  ║")
    print("║           Testing cache with authenticated requests                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=2)
        print(f"✅ Server is running (HTTP {response.status_code})")
    except:
        print("❌ Server not running! Start it first:")
        print("   uvicorn app.main:app --reload")
        return

    # Register user
    if not register_test_user():
        return

    # Login
    token = login_test_user()
    if not token:
        return

    # Test cached endpoints
    test_cache_endpoints(token)

    # Show results
    show_cache_stats()

    print()
    print("💡 Next steps:")
    print("   1. Keep monitoring: python3 scripts/cache-monitor.py")
    print("   2. Use your frontend app with real users")
    print("   3. Watch hit rate climb to 70-90%")

if __name__ == "__main__":
    main()
