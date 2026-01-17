#!/usr/bin/env python3
"""
Test MBTI loading issue by simulating browser behavior
"""
import requests
import time

def test_mbti_loading():
    print("🔍 Testing MBTI Loading Issue")
    print("=" * 50)

    # Test 1: Check if frontend is serving React content
    print("\n1. 📱 Testing Frontend Response...")
    try:
        response = requests.get("http://localhost:5174/assessments/mbti/start", timeout=10)
        print(f"   Status: {response.status_code}")

        # Look for React app indicators
        content = response.text
        react_indicators = [
            "react-dom",
            "React",
            "root",
            "id=\"root\""
        ]

        has_react = any(indicator in content for indicator in react_indicators)
        print(f"   React content detected: {has_react}")

        # Look for loading skeleton
        has_loading = "Loading MBTI Assessment" in content or "loading-skeleton" in content
        print(f"   Loading skeleton: {has_loading}")

        # Look for error content
        has_error = "error" in content.lower() or "something went wrong" in content.lower()
        print(f"   Error indicators: {has_error}")

    except Exception as e:
        print(f"   ❌ Frontend test failed: {e}")
        return

    # Test 2: Test backend API
    print("\n2. 🔧 Testing Backend API...")
    try:
        api_response = requests.get("http://localhost:8000/api/v1/assessment-questions/mbti", timeout=5)
        print(f"   API Status: {api_response.status_code}")

        if api_response.status_code == 200:
            data = api_response.json()
            print(f"   API Success: {data.get('success', False)}")
            print(f"   Questions: {len(data.get('assessment', {}).get('questions', []))}")
        else:
            print(f"   ❌ API failed: {api_response.status_code}")

    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return

    # Test 3: Test basic React app mounting
    print("\n3. ⚡ Testing Basic React App...")
    try:
        # Test root path
        root_response = requests.get("http://localhost:5174/", timeout=5)
        print(f"   Root Status: {root_response.status_code}")

        root_content = root_response.text
        has_root_div = 'id="root"' in root_content
        print(f"   Root div found: {has_root_div}")

        # Look for main script tag
        has_main_script = 'main.' in root_content and '.js' in root_content
        print(f"   Main script found: {has_main_script}")

    except Exception as e:
        print(f"   ❌ React app test failed: {e}")

    print(f"\n" + "=" * 50)
    print("🎯 Diagnosis Summary:")
    print("=" * 50)

    if not has_react:
        print("❌ React app not loading - this explains the infinite loading!")
        print("💡 Likely cause: TypeScript compilation errors preventing build")
    elif has_loading:
        print("⚠️  Still showing loading skeleton")
        print("💡 Component may have errors or import issues")
    else:
        print("✅ React app detected - issue likely in component logic")

if __name__ == "__main__":
    test_mbti_loading()
