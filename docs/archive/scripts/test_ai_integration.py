#!/usr/bin/env python3
"""
Test script to verify AI Engine Integration
"""

import json
import time

import requests


def test_ai_integration():
    """Test complete AI integration"""
    base_url = "http://localhost:8000/api/v1"

    print("🚀 TESTING AI ENGINE INTEGRATION")
    print("=" * 50)

    # Test 1: Frameworks Endpoint
    print("\n1️⃣ Testing Frameworks Endpoint...")
    try:
        response = requests.get(
            f"{base_url}/personality-assessments/frameworks", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            frameworks = data.get("frameworks", [])
            print(f"   ✅ SUCCESS: {len(frameworks)} frameworks available")
            for fw in frameworks[:3]:
                print(f"      - {fw['name']}: {fw['questions']} questions")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    # Test 2: AI Processing - MBTI
    print("\n2️⃣ Testing AI Processing - MBTI...")
    try:
        mbti_data = {"framework": "mbti", "data": {"type": "ENFP", "confidence": 0.92}}
        response = requests.post(
            f"{base_url}/personality-assessments/process-public",
            json=mbti_data,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data.get("results", {})
                print(
                    f"   ✅ SUCCESS: {result.get('type')} - {result.get('processed_by')}"
                )
                print(
                    f"      📝 Description: {result.get('description', 'N/A')[:50]}..."
                )
                print(
                    f"      💡 Insights: {len(result.get('ai_insights', []))} generated"
                )
            else:
                print(f"   ❌ FAILED: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    # Test 3: AI Processing - Enneagram
    print("\n3️⃣ Testing AI Processing - Enneagram...")
    try:
        enneagram_data = {
            "framework": "enneagram",
            "data": {"type": "Type 7", "confidence": 0.88},
        }
        response = requests.post(
            f"{base_url}/personality-assessments/process-public",
            json=enneagram_data,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data.get("results", {})
                print(
                    f"   ✅ SUCCESS: {result.get('type')} - {result.get('framework')}"
                )
                print(f"      🔍 Public Access: {result.get('public_access', False)}")
            else:
                print(f"   ❌ FAILED: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    # Test 4: Performance Check
    print("\n4️⃣ Testing Performance...")
    try:
        start_time = time.time()
        test_data = {"framework": "mbti", "data": {"type": "INTJ", "confidence": 0.9}}
        response = requests.post(
            f"{base_url}/personality-assessments/process-public",
            json=test_data,
            timeout=5,
        )
        end_time = time.time()

        if response.status_code == 200:
            response_time = (end_time - start_time) * 1000
            print(f"   ✅ SUCCESS: Response time {response_time:.1f}ms")
            if response_time < 200:
                print("   🚀 EXCELLENT: Under 200ms")
            elif response_time < 500:
                print("   ⚡ GOOD: Under 500ms")
            else:
                print("   ⚠️ SLOW: Above 500ms")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    # Test 5: Frontend Accessibility
    print("\n5️⃣ Testing Frontend Accessibility...")
    try:
        frontend_response = requests.get("http://localhost:5173", timeout=5)
        if frontend_response.status_code == 200:
            print("   ✅ SUCCESS: Frontend accessible at localhost:5173")
        else:
            print(f"   ❌ FAILED: Frontend status {frontend_response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: Frontend not accessible - {e}")

    print("\n" + "=" * 50)
    print("🎯 AI INTEGRATION TEST COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    test_ai_integration()
