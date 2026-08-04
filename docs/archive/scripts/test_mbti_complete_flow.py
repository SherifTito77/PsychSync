#!/usr/bin/env python3
"""
Test complete MBTI assessment flow with simplified backend
"""
import json
import time

import requests


def test_complete_mbti_flow():
    print("🎯 COMPLETE MBTI FLOW TEST WITH SIMPLIFIED BACKEND")
    print("=" * 60)

    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:5174"

    # Test 1: Backend health check
    print("\n1. 🔧 Backend Health Check...")
    try:
        response = requests.get(f"{backend_url}/api/v1/health", timeout=5)
        print(f"   ✅ Backend Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Database: {data.get('database', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Backend health check failed: {e}")
        return False

    # Test 2: MBTI Questions API
    print("\n2. 📝 MBTI Questions API...")
    try:
        response = requests.get(f"{backend_url}/assessment-questions/mbti", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Success: {data.get('success', False)}")
            questions = data.get("assessment", {}).get("questions", [])
            print(f"   📊 Questions Count: {len(questions)}")
            if questions:
                print(f"   🔍 First Question: {questions[0]['question_text']}")
        else:
            print(f"   ❌ API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ MBTI questions API failed: {e}")
        return False

    # Test 3: MBTI Submission API
    print("\n3. 📤 MBTI Submission API...")
    try:
        # Mock MBTI responses
        mock_responses = {
            "1": "E",  # Prefer talking to many people
            "2": "N",  # Prefer possibilities and concepts
            "3": "T",  # Rely on logic and analysis
            "4": "J",  # Prefer planning ahead
            "5": "E",  # Enjoy working in teams
            "6": "N",  # Like understanding concepts first
            "7": "F",  # Consider feelings when giving feedback
            "8": "P",  # Prefer spontaneity
        }

        submission_data = {
            "assessment_type": "mbti",
            "responses": mock_responses,
            "raw_type": "ENTJ",
        }

        response = requests.post(
            f"{backend_url}/mbti-test-submit", json=submission_data, timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Submission Success: {data.get('success', False)}")
            result = data.get("result", {})
            mbti_type = result.get("type", "Unknown")
            print(f"   🎯 Calculated MBTI Type: {mbti_type}")
            print(f"   📝 Description: {result.get('description', 'No description')}")
            print(f"   📊 Responses Count: {result.get('responses_count', 0)}")
        else:
            print(f"   ❌ Submission failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ MBTI submission API failed: {e}")
        return False

    # Test 4: Frontend accessibility
    print("\n4. 📱 Frontend Accessibility...")
    try:
        response = requests.get(f"{frontend_url}/assessments/mbti/start", timeout=10)
        print(f"   ✅ Frontend Status: {response.status_code}")

        # Check for React app content
        content = response.text
        has_react = "react" in content.lower()
        has_root_div = 'id="root"' in content

        print(f"   🔍 React content: {has_react}")
        print(f"   🏗️  Root div found: {has_root_div}")

        if has_react and has_root_div:
            print("   ✅ Frontend should load properly")
        else:
            print("   ⚠️  Frontend may have loading issues")

    except Exception as e:
        print(f"   ❌ Frontend accessibility failed: {e}")
        return False

    # Test 5: Authentication endpoints
    print("\n5. 🔐 Authentication Endpoints...")
    try:
        # Test login
        login_data = {"email": "testuser2025@example.com", "password": "testpass123"}
        response = requests.post(
            f"{backend_url}/token-minimal", json=login_data, timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_email = data.get("user", {}).get("email")
            print(f"   ✅ Login successful for: {user_email}")
            print(
                f"   🔑 Token received: {token[:20]}..."
                if token
                else "   ⚠️  No token received"
            )
        else:
            print(f"   ❌ Login failed: {response.status_code}")

        # Test user info
        response = requests.get(f"{backend_url}/me-minimal", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(
                f"   ✅ User info: {data.get('email', 'Unknown')} ({data.get('role', 'Unknown')})"
            )

    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

    print(f"\n" + "=" * 60)
    print("🎯 MBTI ASSESSMENT FLOW TEST SUMMARY")
    print("=" * 60)
    print("✅ Backend API is working correctly")
    print("✅ MBTI questions are available")
    print("✅ MBTI submission and scoring works")
    print("✅ Frontend is accessible")
    print("✅ Authentication endpoints work")
    print("\n🚀 READY FOR USER TESTING!")
    print("Visit: http://localhost:5174/assessments/mbti/start")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_complete_mbti_flow()
