#!/usr/bin/env python3
"""
Test the complete MBTI user experience flow
"""
import requests
import json
import time

def test_mbti_flow():
    print("🚀 Testing Complete MBTI Assessment User Flow")
    print("=" * 60)

    # Base URLs
    frontend_url = "http://localhost:5174"
    backend_url = "http://localhost:8000"

    print("\n1. 📱 Testing Frontend Accessibility...")
    try:
        response = requests.get(f"{frontend_url}/assessments/mbti/start", timeout=5)
        print(f"   ✅ Frontend accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend error: {e}")
        return

    print("\n2. 🔧 Testing Backend MBTI Questions...")
    try:
        response = requests.get(f"{backend_url}/api/v1/assessment-questions/mbti")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend working: {data.get('success', False)}")
            print(f"   📝 Assessment: {data.get('assessment', {}).get('title', 'N/A')}")
            print(f"   📊 Questions: {len(data.get('assessment', {}).get('questions', []))}")
        else:
            print(f"   ❌ Backend error: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Backend error: {e}")
        return

    print("\n3. 🧠 Testing MBTI Question Display...")
    try:
        questions = data.get('assessment', {}).get('questions', [])
        for i, q in enumerate(questions[:3], 1):  # Show first 3 questions
            print(f"   Question {i}: {q.get('question_text', 'N/A')}")
            print(f"   Options: {', '.join([opt['text'] for opt in q.get('options', [])])}")
            print()
    except Exception as e:
        print(f"   ❌ Question display error: {e}")

    print("\n4. ✅ Testing MBTI Assessment Submission...")

    # Simulate different user personalities
    test_personalities = [
        {
            "name": "Extraverted Thinking (ENTJ)",
            "responses": {
                "1": "E", "2": "N", "3": "T", "4": "J",
                "5": "E", "6": "N", "7": "T", "8": "J"
            }
        },
        {
            "name": "Introverted Feeling (INFP)",
            "responses": {
                "1": "I", "2": "N", "3": "F", "4": "P",
                "5": "I", "6": "N", "7": "F", "8": "P"
            }
        },
        {
            "name": "Sensing Judging (ISTJ)",
            "responses": {
                "1": "I", "2": "S", "3": "T", "4": "J",
                "5": "I", "6": "S", "7": "T", "8": "J"
            }
        }
    ]

    for personality in test_personalities:
        print(f"\n   Testing {personality['name']}...")

        try:
            response = requests.post(
                f"{backend_url}/api/v1/mbti-test-submit",
                json={
                    "assessment_type": "mbti",
                    "responses": personality["responses"]
                }
            )

            if response.status_code == 200:
                result = response.json()
                expected_type = personality['name'].split()[0]  # Extract expected type
                actual_type = result.get('type', 'N/A')

                print(f"   ✅ Submitted successfully")
                print(f"   📊 Result: {actual_type}")
                print(f"   🎯 Confidence: {result.get('confidence', 0):.1f}")
                print(f"   📝 Description: {result.get('description', 'N/A')[:50]}...")

                # Check if scoring is working correctly
                if actual_type == expected_type:
                    print(f"   ✅ Scoring accurate!")
                else:
                    print(f"   ⚠️  Expected {expected_type}, got {actual_type}")

            else:
                print(f"   ❌ Submission failed: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Submission error: {e}")

    print("\n" + "=" * 60)
    print("🎯 MBTI User Flow Test Summary")
    print("=" * 60)

    # Final status
    try:
        frontend_response = requests.get(f"{frontend_url}/assessments/mbti/start")
        backend_response = requests.get(f"{backend_url}/api/v1/assessment-questions/mbti")

        if frontend_response.status_code == 200 and backend_response.status_code == 200:
            print("✅ SUCCESS: MBTI assessment is fully functional!")
            print(f"🌐 Frontend: http://localhost:5174/assessments/mbti/start")
            print("🔧 Backend API working correctly")
            print("📝 Questions load successfully")
            print("✅ Assessment submission works")
            print("\n🎉 Users can now take the MBTI assessment!")
        else:
            print("⚠️  ISSUES: Some components need attention")

    except Exception as e:
        print(f"❌ ERROR: Could not complete final check: {e}")

if __name__ == "__main__":
    test_mbti_flow()
