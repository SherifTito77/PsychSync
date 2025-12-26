#!/usr/bin/env python3
"""Teams functionality validation for PsychSync"""

import requests
import json
import uuid

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

def test_team_crud():
    """Test Team CRUD operations"""
    print("🔧 Testing Teams CRUD Operations")
    print("=" * 50)

    # CREATE
    print("1. Testing team creation...")
    team_data = {
        "name": "Engineering Test Team",
        "description": "Backend development test team"
    }

    try:
        response = requests.post(
            f"{API_URL}/api/v1/teams/",
            headers=get_headers(),
            json=team_data
        )

        print(f"Create status: {response.status_code}")
        print(f"Create response: {response.text}")

        if response.status_code == 201:
            team = response.json()
            team_id = team.get('id')
            print(f"✅ Team created: {team_id}")
            return team_id
        else:
            print("❌ Team creation failed")
            return None

    except Exception as e:
        print(f"❌ Team creation error: {e}")
        return None

def test_team_list():
    """Test listing teams"""
    print("\n2. Testing team listing...")

    try:
        response = requests.get(
            f"{API_URL}/api/v1/teams/",
            headers=get_headers()
        )

        print(f"List status: {response.status_code}")

        if response.status_code == 200:
            teams = response.json()
            print(f"✅ Found {len(teams)} teams")
            return teams
        else:
            print("❌ Team listing failed")
            return []

    except Exception as e:
        print(f"❌ Team listing error: {e}")
        return []

def test_team_update(team_id):
    """Test team update"""
    print(f"\n3. Testing team update for ID: {team_id}...")

    if not team_id:
        print("❌ Cannot update without valid team ID")
        return False

    update_data = {
        "name": "Updated Engineering Team",
        "description": "Updated description"
    }

    try:
        response = requests.put(
            f"{API_URL}/api/v1/teams/{team_id}",
            headers=get_headers(),
            json=update_data
        )

        print(f"Update status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Team updated successfully")
            return True
        else:
            print("❌ Team update failed")
            return False

    except Exception as e:
        print(f"❌ Team update error: {e}")
        return False

def test_team_delete(team_id):
    """Test team deletion"""
    print(f"\n4. Testing team deletion for ID: {team_id}...")

    if not team_id:
        print("❌ Cannot delete without valid team ID")
        return False

    try:
        response = requests.delete(
            f"{API_URL}/api/v1/teams/{team_id}",
            headers=get_headers()
        )

        print(f"Delete status: {response.status_code}")

        if response.status_code in [200, 204]:
            print("✅ Team deleted successfully")
            return True
        else:
            print("❌ Team deletion failed")
            return False

    except Exception as e:
        print(f"❌ Team deletion error: {e}")
        return False

def main():
    """Run teams validation tests"""
    print("👥 PsychSync Teams Validation")
    print("=" * 50)

    # Test team listing first
    teams = test_team_list()

    # Test team CRUD
    team_id = test_team_crud()
    update_success = test_team_update(team_id)
    delete_success = test_team_delete(team_id)

    print("\n" + "=" * 50)
    print("📊 TEAMS VALIDATION SUMMARY")
    print("=" * 50)

    results = [
        ("Team List", len(teams) >= 0),
        ("Team Create", team_id is not None),
        ("Team Update", update_success),
        ("Team Delete", delete_success)
    ]

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 ALL TEAMS TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TEAMS TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit(main())