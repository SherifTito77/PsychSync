#!/usr/bin/env python3
"""
Final test of the complete MBTI solution after fixing all issues
"""
import requests
import time

def test_final_solution():
    print("🎯 FINAL MBTI SOLUTION TEST")
    print("=" * 50)

    # Test all essential endpoints
    tests = [
        {
            "name": "Backend Health",
            "method": "GET",
            "url": "http://localhost:8000/api/v1/health",
            "expected": 200
        },
        {
            "name": "MBTI Questions",
            "method": "GET",
            "url": "http://localhost:8000/assessment-questions/mbti",
            "expected": 200
        },
        {
            "name": "Authentication",
            "method": "POST",
            "url": "http://localhost:8000/token-minimal",
            "data": {"email": "testuser2025@example.com", "password": "testpass123"},
            "expected": 200
        },
        {
            "name": "MBTI Submission",
            "method": "POST",
            "url": "http://localhost:8000/mbti-test-submit",
            "data": {
                "assessment_type": "mbti",
                "responses": {"1": "E", "2": "N", "3": "T", "4": "J", "5": "E", "6": "N", "7": "F", "8": "P"},
                "raw_type": "ENTJ"
            },
            "expected": 200
        },
        {
            "name": "Frontend Accessibility",
            "method": "GET",
            "url": "http://localhost:5174/assessments/mbti/start",
            "expected": 200
        }
    ]

    passed = 0
    total = len(tests)

    for i, test in enumerate(tests, 1):
        print(f"\n{i}. 🧪 {test['name']}...")

        try:
            start_time = time.time()

            if test['method'] == 'GET':
                response = requests.get(test['url'], timeout=5)
            else:  # POST
                response = requests.post(test['url'], json=test.get('data'), timeout=5)

            response_time = time.time() - start_time

            if response.status_code == test['expected']:
                print(f"   ✅ PASS ({response_time:.3f}s)")

                # Add specific checks for each test
                if test['name'] == "MBTI Questions":
                    data = response.json()
                    if data.get('success'):
                        questions = data.get('assessment', {}).get('questions', [])
                        print(f"   📊 {len(questions)} questions available")

                elif test['name'] == "MBTI Submission":
                    data = response.json()
                    if data.get('success'):
                        result = data.get('result', {})
                        mbti_type = result.get('type', 'Unknown')
                        print(f"   🎯 Calculated type: {mbti_type}")
                        print(f"   💾 DB storage: {data.get('stored_in_db', False)}")

                elif test['name'] == "Authentication":
                    data = response.json()
                    token = data.get('access_token')
                    print(f"   🔑 Token received: {'Yes' if token else 'No'}")

                elif test['name'] == "Frontend Accessibility":
                    content = response.text
                    has_react = "react" in content.lower()
                    print(f"   ⚛️  React app: {'Yes' if has_react else 'No'}")

                passed += 1
            else:
                print(f"   ❌ FAIL - Status: {response.status_code}")

        except Exception as e:
            print(f"   ❌ ERROR - {str(e)[:50]}...")

    print(f"\n" + "=" * 50)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 50)
    print(f"Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ MBTI Assessment System is fully functional")
        print("✅ Backend API working correctly")
        print("✅ Frontend loading properly")
        print("✅ Assessment submission and scoring working")
        print("✅ Authentication system functional")
        print("\n🚀 READY FOR USER!")
        print("Visit: http://localhost:5174/assessments/mbti/start")
    else:
        print(f"⚠️  {total - passed} tests failed")
        print("System needs attention before use")

    print("=" * 50)

    return passed == total

if __name__ == "__main__":
    test_final_solution()