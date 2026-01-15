#!/usr/bin/env python3
"""
Test script for clinical screening endpoints
Tests the complete workflow: consent → screening → crisis intervention if needed
"""

import asyncio
import json
from datetime import datetime

import httpx


BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test_clinical@example.com",
    "password": "TestPassword123!",
    "full_name": "Clinical Test User"
}


async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Get auth token for testing"""
    # Try to register/login
    try:
        # Register
        response = await client.post(
            f"{BASE_URL}/api/v1/simple-auth/register",
            json=TEST_USER
        )
        print(f"Register response: {response.status_code}")
    except Exception as e:
        print(f"Register failed (might exist): {e}")

    # Login
    response = await client.post(
        f"{BASE_URL}/api/v1/simple-auth/login",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ Login successful, token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None


async def test_consent(client: httpx.AsyncClient, token: str) -> bool:
    """Test consent endpoint"""
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"{BASE_URL}/api/v1/screening/consent",
        headers=headers,
        json={
            "consent_type": "screening",
            "screening_types": ["PHQ9", "GAD7", "CSSRS"]
        }
    )

    if response.status_code in [200, 201]:
        print(f"✅ Consent submitted successfully")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Consent failed: {response.status_code} - {response.text}")
        return False


async def test_phq9_low_risk(client: httpx.AsyncClient, token: str) -> bool:
    """Test PHQ-9 with low risk responses"""
    headers = {"Authorization": f"Bearer {token}"}

    # Low risk PHQ-9 responses
    responses = {
        "q1_interest": 1,
        "q2_depressed": 1,
        "q3_sleep": 1,
        "q4_energy": 1,
        "q5_appetite": 0,
        "q6_self_worth": 1,
        "q7_concentration": 1,
        "q8_motor": 0,
        "q9_suicide": 0  # CRITICAL: No suicide ideation
    }

    response = await client.post(
        f"{BASE_URL}/api/v1/screening/phq9",
        headers=headers,
        json=responses
    )

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ PHQ-9 screening successful")
        print(f"  Score: {data.get('total_score')}")
        print(f"  Severity: {data.get('severity_level')}")
        print(f"  Risk: {data.get('risk_level')}")
        print(f"  Crisis Alert: {data.get('crisis_alert')}")
        print(f"  Recommendations: {data.get('recommendations', [])[:2]}")
        return data.get('crisis_alert') == False
    else:
        print(f"❌ PHQ-9 failed: {response.status_code} - {response.text}")
        return False


async def test_phq9_crisis(client: httpx.AsyncClient, token: str) -> bool:
    """Test PHQ-9 with crisis indicators (suicide ideation)"""
    headers = {"Authorization": f"Bearer {token}"}

    # High risk PHQ-9 responses with suicide ideation
    responses = {
        "q1_interest": 3,
        "q2_depressed": 3,
        "q3_sleep": 3,
        "q4_energy": 3,
        "q5_appetite": 3,
        "q6_self_worth": 3,
        "q7_concentration": 3,
        "q8_motor": 3,
        "q9_suicide": 2  # CRITICAL: Triggers crisis alert
    }

    response = await client.post(
        f"{BASE_URL}/api/v1/screening/phq9",
        headers=headers,
        json=responses
    )

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ PHQ-9 crisis screening successful")
        print(f"  Score: {data.get('total_score')}")
        print(f"  Severity: {data.get('severity_level')}")
        print(f"  Risk: {data.get('risk_level')}")
        print(f"  Crisis Alert: {data.get('crisis_alert')}")
        print(f"  Risk Flags: {data.get('risk_flags')}")
        return data.get('crisis_alert') == True
    else:
        print(f"❌ PHQ-9 crisis failed: {response.status_code} - {response.text}")
        return False


async def test_gad7(client: httpx.AsyncClient, token: str) -> bool:
    """Test GAD-7 anxiety screening"""
    headers = {"Authorization": f"Bearer {token}"}

    responses = {
        "q1_nervous": 2,
        "q2_control_worry": 2,
        "q3_worry_too_much": 2,
        "q4_trouble_relaxing": 1,
        "q5_restless": 1,
        "q6_irritable": 1,
        "q7_afraid": 0
    }

    response = await client.post(
        f"{BASE_URL}/api/v1/screening/gad7",
        headers=headers,
        json=responses
    )

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ GAD-7 screening successful")
        print(f"  Score: {data.get('total_score')}")
        print(f"  Severity: {data.get('severity_level')}")
        print(f"  Risk: {data.get('risk_level')}")
        return True
    else:
        print(f"❌ GAD-7 failed: {response.status_code} - {response.text}")
        return False


async def test_cssrs(client: httpx.AsyncClient, token: str) -> bool:
    """Test C-SSRS suicide risk screening"""
    headers = {"Authorization": f"Bearer {token}"}

    # Low risk responses
    responses = {
        "q1_wish_dead": False,
        "q2_nonspecific_thoughts": False,
        "q3_active_ideation": False,
        "q4_intent": False,
        "q5_plan": False,
        "q11_actual_attempt": False,
        "q12_preparatory_acts": False,
        "q13_aborted_attempt": False
    }

    response = await client.post(
        f"{BASE_URL}/api/v1/screening/cssrs",
        headers=headers,
        json=responses
    )

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ C-SSRS screening successful")
        print(f"  Risk Level: {data.get('risk_level')}")
        print(f"  Crisis Alert: {data.get('crisis_alert')}")
        return True
    else:
        print(f"❌ C-SSRS failed: {response.status_code} - {response.text}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Clinical Screening System Test")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get auth token
        print("\n1. Getting authentication token...")
        token = await get_auth_token(client)
        if not token:
            print("❌ Failed to get auth token, aborting tests")
            return

        # Test consent
        print("\n2. Testing consent endpoint...")
        consent_ok = await test_consent(client, token)

        # Test PHQ-9 low risk
        print("\n3. Testing PHQ-9 (low risk)...")
        phq9_low_ok = await test_phq9_low_risk(client, token)

        # Test PHQ-9 crisis
        print("\n4. Testing PHQ-9 (crisis)...")
        phq9_crisis_ok = await test_phq9_crisis(client, token)

        # Test GAD-7
        print("\n5. Testing GAD-7...")
        gad7_ok = await test_gad7(client, token)

        # Test C-SSRS
        print("\n6. Testing C-SSRS...")
        cssrs_ok = await test_cssrs(client, token)

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Consent: {'✅' if consent_ok else '❌'}")
        print(f"PHQ-9 (low risk): {'✅' if phq9_low_ok else '❌'}")
        print(f"PHQ-9 (crisis): {'✅' if phq9_crisis_ok else '❌'}")
        print(f"GAD-7: {'✅' if gad7_ok else '❌'}")
        print(f"C-SSRS: {'✅' if cssrs_ok else '❌'}")

        all_ok = all([consent_ok, phq9_low_ok, phq9_crisis_ok, gad7_ok, cssrs_ok])
        print(f"\nOverall: {'✅ All tests passed!' if all_ok else '⚠️ Some tests failed'}")


if __name__ == "__main__":
    asyncio.run(main())
