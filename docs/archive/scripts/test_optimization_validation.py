#!/usr/bin/env python3
"""Team optimization functionality validation for PsychSync"""

import json

import requests

API_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjM1MTkxNjEsInN1YiI6ImYwZWIyMjNiLTgzMTgtNDYxMS1iODljLTBjY2NmYTI0NDY0ZCIsInR5cGUiOiJhY2Nlc3MifQ.J1Xg9QZBeKIuAPVAKnDGj2MmQLDzSqjrIJHrL6dwJqY"


def get_headers():
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def test_optimization_health():
    """Test team optimization health"""
    print("🧠 Testing Team Optimization Health")
    print("=" * 50)

    try:
        response = requests.get(
            f"{API_URL}/api/v1/team-optimizer/health", headers=get_headers()
        )

        print(f"Health check status: {response.status_code}")
        print(f"Health response: {response.text}")

        if response.status_code == 200:
            print("✅ Team optimizer health check passed")
            return True
        else:
            print("❌ Team optimizer health check failed")
            return False

    except Exception as e:
        print(f"❌ Team optimizer health check error: {e}")
        return False


def test_team_optimization():
    """Test AI-powered team optimization"""
    print("\n🚀 Testing Team Optimization")
    print("=" * 50)

    optimization_request = {
        "members": [
            {
                "id": "f0eb223b-8318-4611-b89c-0cccfa24464d",  # Our test user ID
                "name": "Alice Johnson",
                "traits": {
                    "openness": 0.8,
                    "conscientiousness": 0.9,
                    "extraversion": 0.6,
                    "agreeableness": 0.7,
                    "neuroticism": 0.3,
                },
            },
            {
                "id": "team-member-2",
                "name": "Bob Smith",
                "traits": {
                    "openness": 0.6,
                    "conscientiousness": 0.7,
                    "extraversion": 0.9,
                    "agreeableness": 0.8,
                    "neuroticism": 0.4,
                },
            },
        ],
        "project_requirements": {
            "project_type": "web_app",
            "duration_weeks": 12,
            "complexity": "high",
            "required_skills": ["frontend", "backend", "devops"],
        },
    }

    try:
        response = requests.post(
            f"{API_URL}/api/v1/team-optimizer/optimize",
            headers=get_headers(),
            json=optimization_request,
        )

        print(f"Optimization status: {response.status_code}")
        print(f"Optimization response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if "overall_score" in result:
                print(f"✅ Team optimization successful")
                print(f"   Overall Score: {result['overall_score']}")
                return True
            else:
                print("❌ Optimization response missing expected data")
                return False
        else:
            print("❌ Team optimization failed")
            return False

    except Exception as e:
        print(f"❌ Team optimization error: {e}")
        return False


def test_available_endpoints():
    """Test available optimization endpoints"""
    print("\n🔍 Testing Available Endpoints")
    print("=" * 50)

    endpoints = [
        "/api/v1/team-optimizer/",
        "/api/v1/team-optimizer/algorithms",
        "/api/v1/team-optimizer/recommendations",
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_URL}{endpoint}", headers=get_headers())
            print(
                f"{endpoint:40} {response.status_code:4} {'✅' if response.status_code == 200 else '❌'}"
            )
        except Exception as e:
            print(f"{endpoint:40} ERROR {e}")


def main():
    """Run team optimization validation tests"""
    print("🧠 PsychSync Team Optimization Validation")
    print("=" * 50)

    health_success = test_optimization_health()
    optimization_success = test_team_optimization()
    test_available_endpoints()

    print("\n" + "=" * 50)
    print("📊 TEAM OPTIMIZATION VALIDATION SUMMARY")
    print("=" * 50)

    results = [
        ("Optimizer Health", health_success),
        ("Team Optimization", optimization_success),
    ]

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 ALL TEAM OPTIMIZATION TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TEAM OPTIMIZATION TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
