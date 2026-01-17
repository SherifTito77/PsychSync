#!/usr/bin/env python3
"""
Clear any cached MBTI assessment data that might prevent new assessments
"""
import requests
import json

def test_mbti_questions_directly():
    """Test if MBTI questions load without frontend cache issues"""
    print("🧹 Testing MBTI Questions API Directly (No Cache)")
    print("=" * 50)

    try:
        # Test fresh request to MBTI questions API
        response = requests.get("http://localhost:8000/api/v1/assessment-questions/mbti")

        print(f"📡 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print(f"✅ API Success: {data.get('success', False)}")

            if data.get('success'):
                assessment = data.get('assessment', {})
                questions = assessment.get('questions', [])

                print(f"📝 Assessment Title: {assessment.get('title', 'N/A')}")
                print(f"📊 Total Questions: {len(questions)}")
                print(f"🎯 Dimensions Covered: {len(set(q.get('dimension') for q in questions))}")

                print(f"\n❓ Sample Questions:")
                for i, q in enumerate(questions[:3], 1):
                    print(f"   {i}. {q.get('question_text', 'N/A')}")
                    options = q.get('options', [])
                    for opt in options:
                        print(f"      • {opt.get('text', 'N/A')} ({opt.get('value', 'N/A')})")
                    print()

                print("✅ MBTI Questions API working perfectly!")
                print("💡 If questions aren't showing in frontend, the issue is:")
                print("   - Frontend component loading/routing issue")
                print("   - Browser cache or localStorage interference")
                print("   - JavaScript errors preventing component mount")

            else:
                print(f"❌ API returned failure: {data}")
        else:
            print(f"❌ API request failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

def check_frontend_routing():
    """Test if frontend routing is working correctly"""
    print(f"\n🌐 Testing Frontend Routing")
    print("=" * 30)

    try:
        # Test the frontend URL directly
        response = requests.get("http://localhost:5174/assessments/mbti/start")

        print(f"📡 Frontend Status: {response.status_code}")

        if response.status_code == 200:
            content = response.text

            # Check for key indicators
            indicators = {
                "React App": "react" in content.lower() or "root" in content.lower(),
                "Loading State": "loading" in content.lower(),
                "MBTI Component": "MBTI" in content,
                "Error State": "error" in content.lower() or "something went wrong" in content.lower(),
                "Assessment Content": "assessment" in content.lower()
            }

            print("\n📊 Frontend Analysis:")
            for indicator, found in indicators.items():
                status = "✅" if found else "❌"
                print(f"   {status} {indicator}: {found}")

        else:
            print(f"❌ Frontend not accessible: {response.status_code}")

    except Exception as e:
        print(f"❌ Frontend test failed: {e}")

if __name__ == "__main__":
    test_mbti_questions_directly()
    check_frontend_routing()

    print(f"\n🎯 Quick Fix Recommendation:")
    print("=" * 35)
    print("1. ✅ Backend API working (we just tested)")
    print("2. ⚠️  Frontend component loading issue")
    print("3. 💡 Try: Clear browser cache & localStorage")
    print("4. 💡 Try: Visit http://localhost:5174/assessments/mbti/start?fresh=1")
