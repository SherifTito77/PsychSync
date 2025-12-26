#!/usr/bin/env python3
"""
Business Logic Bypass Testing for PsychSync
Tests for authentication bypass, privilege escalation, and parameter manipulation
"""

import requests
import json
from datetime import datetime

def test_business_logic_bypass():
    """Test business logic bypass vulnerabilities"""
    base_url = "http://localhost:8000"

    print("🧪 Testing Business Logic Bypass Vulnerabilities")

    test_cases = [
        # Authentication bypass attempts
        {
            "name": "Authentication Bypass - SQL Injection in Login",
            "method": "POST",
            "url": f"{base_url}/api/v1/auth/login",
            "data": {"email": "' OR '1'='1' --", "password": "anything"},
            "expected_failure": True
        },

        # Privilege escalation attempts
        {
            "name": "Privilege Escalation - Admin Role in Registration",
            "method": "POST",
            "url": f"{base_url}/api/v1/auth/register",
            "data": {
                "email": "admin@test.com",
                "password": "test123",
                "full_name": "Test Admin",
                "role": "admin"
            },
            "expected_failure": True
        },

        {
            "name": "Privilege Escalation - Is Admin Flag",
            "method": "POST",
            "url": f"{base_url}/api/v1/auth/register",
            "data": {
                "email": "admin2@test.com",
                "password": "test123",
                "full_name": "Test Admin 2",
                "is_admin": True
            },
            "expected_failure": True
        },

        # ID manipulation tests
        {
            "name": "ID Manipulation - Non-existent User",
            "method": "GET",
            "url": f"{base_url}/api/v1/users/99999",
            "expected_failure": True
        },

        {
            "name": "ID Manipulation - Invalid User ID",
            "method": "GET",
            "url": f"{base_url}/api/v1/users/-1",
            "expected_failure": True
        },

        # Limit bypass attempts
        {
            "name": "Limit Bypass - Excessive Limit Parameter",
            "method": "GET",
            "url": f"{base_url}/api/v1/assessments?limit=999999",
            "expected_failure": True
        },

        {
            "name": "Limit Bypass - Negative Limit",
            "method": "GET",
            "url": f"{base_url}/api/v1/assessments?limit=-1",
            "expected_failure": True
        },

        # Status manipulation
        {
            "name": "Status Manipulation - Approved Status",
            "method": "POST",
            "url": f"{base_url}/api/v1/assessments",
            "data": {
                "title": "Test Assessment",
                "description": "Test Description",
                "status": "approved"
            },
            "expected_failure": True
        }
    ]

    results = []
    vulnerabilities_found = 0

    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")

        try:
            if test_case["method"] == "POST":
                response = requests.post(
                    test_case["url"],
                    json=test_case.get("data", {}),
                    timeout=10
                )
            else:
                response = requests.get(test_case["url"], timeout=10)

            # Check if test should have failed but didn't
            if test_case["expected_failure"] and response.status_code not in [400, 401, 403, 404, 422]:
                print(f"🚨 VULNERABILITY DETECTED: Expected failure but got {response.status_code}")
                vulnerabilities_found += 1
                is_vulnerable = True
            else:
                print(f"✅ Protected: Got expected {response.status_code}")
                is_vulnerable = False

            results.append({
                "test_name": test_case["name"],
                "status_code": response.status_code,
                "vulnerable": is_vulnerable,
                "expected_failure": test_case["expected_failure"],
                "response_preview": response.text[:200] if response.text else None
            })

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test_name": test_case["name"],
                "error": str(e),
                "vulnerable": False
            })

    print(f"\n📊 Business Logic Bypass Test Summary:")
    print(f"Total Tests: {len(test_cases)}")
    print(f"Vulnerabilities Found: {vulnerabilities_found}")

    if vulnerabilities_found > 0:
        print("🚨 BUSINESS LOGIC VULNERABILITIES DETECTED!")
    else:
        print("✅ No business logic bypass vulnerabilities found")

    return {
        "total_tests": len(test_cases),
        "vulnerabilities_found": vulnerabilities_found,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    test_business_logic_bypass()