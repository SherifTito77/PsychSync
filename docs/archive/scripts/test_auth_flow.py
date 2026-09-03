#!/usr/bin/env python3
"""
Test authentication flow to verify tokens are working correctly
"""
import asyncio
import sys
from datetime import datetime, timedelta

import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_login_and_tokens():
    """Test login endpoint and verify tokens are returned"""

    print("=" * 60)
    print("AUTHENTICATION FLOW TEST")
    print("=" * 60)

    # Get password from command line or environment
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Enter password for sherif.tito.77@gmail.com: ")

    # Test user credentials
    credentials = {"username": "sherif.tito.77@gmail.com", "password": password}

    async with httpx.AsyncClient() as client:
        # Step 1: Test login
        print("\n1️⃣  Testing Login Endpoint")
        print("-" * 60)

        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"   User: {data['user']['email']}")
            print(f"   Access token: {data['access_token'][:50]}...")
            print(
                f"   Refresh token: {data.get('refresh_token', 'NOT FOUND')[:50] if data.get('refresh_token') else 'NOT FOUND'}..."
            )
            print(f"   Expires in: {data.get('expires_in', 'N/A')} seconds")

            access_token = data["access_token"]
            refresh_token = data.get("refresh_token")

            if not refresh_token:
                print("\n❌ WARNING: No refresh token in response!")
                return False

            # Step 2: Test authenticated request
            print("\n2️⃣  Testing Authenticated Request")
            print("-" * 60)

            response = await client.get(
                f"{BASE_URL}/email-connector/connections",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Authenticated request successful!")
                print(f"   Total connections: {data.get('total_connections', 0)}")
                for conn in data.get("connections", []):
                    print(f"   - {conn['email_address']}: {conn['connection_status']}")
            else:
                print(f"❌ Authenticated request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False

            # Step 3: Test token refresh
            print("\n3️⃣  Testing Token Refresh")
            print("-" * 60)

            response = await client.post(
                f"{BASE_URL}/auth/refresh",
                data={"refresh_token": refresh_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Token refresh successful!")
                print(f"   New access token: {data['access_token'][:50]}...")
                print(
                    f"   New refresh token: {data.get('refresh_token', 'NOT FOUND')[:50] if data.get('refresh_token') else 'NOT FOUND'}..."
                )

                # Step 4: Test new token works
                print("\n4️⃣  Testing New Access Token")
                print("-" * 60)

                response = await client.get(
                    f"{BASE_URL}/email-connector/connections",
                    headers={"Authorization": f"Bearer {data['access_token']}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ New access token works!")
                    print(f"   Total connections: {data.get('total_connections', 0)}")
                else:
                    print(f"❌ New access token failed: {response.status_code}")
                    return False

            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False

            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            return True

        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")

            if response.status_code == 401:
                print("\n💡 TIP: Your password might be incorrect.")
                print("   You can reset it or create a test user using:")
                print("   python create_test_user.py")

            return False


if __name__ == "__main__":
    asyncio.run(test_login_and_tokens())
