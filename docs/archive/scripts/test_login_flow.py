#!/usr/bin/env python3
"""
Test login to see what token is generated
"""
import asyncio

import httpx
from jose import jwt

from app.core.config.settings import settings


async def test_login():
    """Test login and check the generated token"""

    print("=" * 60)
    print("TESTING LOGIN FLOW")
    print("=" * 60)

    # Get password
    import sys

    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Enter password for sherif.tito.77@gmail.com: ")

    async with httpx.AsyncClient() as client:
        # Step 1: Login
        print("\n1. Testing login...")
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "sherif.tito.77@gmail.com", "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   {response.text}")
            return

        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        print(f"✅ Login successful!")
        print(f"   Access token (first 50 chars): {access_token[:50]}...")
        print(
            f"   Refresh token (first 50 chars): {refresh_token[:50] if refresh_token else 'None'}..."
        )

        # Step 2: Decode the access token
        print("\n2. Decoding access token...")
        try:
            payload = jwt.decode(
                access_token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM]
            )
            print(f"✅ Token decoded successfully!")
            print(f"\n   Token payload:")
            for key, value in payload.items():
                if key == "user_id" or key == "sub":
                    print(f"   - {key}: {value}")
                    print(f"     Length: {len(value)}")
                    print(f"     Expected: 36 chars")
                    print(f"     Valid UUID: {len(value) == 36}")

                    # Check if it's the corrupted UUID
                    if "fc6-f998" in value and "afc6-f998" not in value:
                        print(f"     ❌ CORRUPTED UUID DETECTED!")
                        print(f"     Missing 'a' in 'afc6'")
                    elif "afc6-f998" in value:
                        print(f"     ✅ CORRECT UUID!")
        except Exception as e:
            print(f"❌ Failed to decode token: {e}")

        # Step 3: Test email connector endpoint
        print("\n3. Testing email connector endpoint...")
        response = await client.get(
            "http://localhost:8000/api/v1/email-connector/connections",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email connector works!")
            print(f"   Connections: {data.get('total_connections', 0)}")
        else:
            print(f"❌ Email connector failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")


if __name__ == "__main__":
    asyncio.run(test_login())
