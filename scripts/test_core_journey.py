import sys
import time

import requests

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


def test_core_journey():
    print("🚀 Starting PsychSync Core Journey Test")

    # 0. Check if server is running
    try:
        requests.get(BASE_URL)
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Server is not running at {BASE_URL}")
        print("Please start the server first:")
        print("PYTHONPATH=. uvicorn app.main:app --reload")
        sys.exit(1)

    print("✅ Server is running")

    # 1. Register a new user
    timestamp = int(time.time())
    email = f"journey_test_{timestamp}@gmail.com"
    password = "Complex_Auth_99!"

    print(f"📝 Registering user: {email}...")
    reg_data = {"email": email, "password": password, "full_name": "Journey Test User"}
    response = requests.post(f"{API_V1}/register", json=reg_data)
    if response.status_code not in [201, 200]:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        # If 500, it might be the database/redis issue we saw earlier
        sys.exit(1)
    print("✅ Registration successful")

    # 2. Login
    print("🔑 Logging in...")
    login_data = {"username": email, "password": password}
    response = requests.post(f"{API_V1}/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        sys.exit(1)

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # 3. Get user profile
    print("👤 Getting user profile...")
    response = requests.get(f"{API_V1}/users/me", headers=headers)
    if response.status_code != 200:
        print(f"❌ Get profile failed: {response.status_code}")
        sys.exit(1)
    user_id = response.json()["id"]
    print(f"✅ Profile retrieved (ID: {user_id})")

    # 4. Create a team
    print("👥 Creating a team...")
    team_data = {
        "name": f"Test Team {timestamp}",
        "description": "Automated journey test team",
    }
    response = requests.post(f"{API_V1}/teams", json=team_data, headers=headers)
    if response.status_code in [200, 201]:
        team_id = response.json()["id"]
        print(f"✅ Team created (ID: {team_id})")
    else:
        print(f"❌ Team creation failed: {response.status_code} - {response.text}")
        sys.exit(1)

    # 5. Get assessments
    print("📋 Fetching available assessments...")
    response = requests.get(f"{API_V1}/assessments/", headers=headers)
    if response.status_code == 200:
        assessments = response.json()
        print(f"✅ Found {len(assessments)} assessments")
    else:
        print(f"⚠️ Fetching assessments failed: {response.status_code}")

    print("\n✨ Core journey test completed!")


if __name__ == "__main__":
    test_core_journey()
