#!/usr/bin/env python3
"""
Test OrangeHRM Connection to PsychSync HRIS Connector
Run this script to verify the connection setup
"""

import json

import requests

BASE_URL = "http://localhost:8000/api/v1/hris"
FRONTEND_URL = "http://localhost:5173/hris-connector"


def test_providers():
    """Test if OrangeHRM is in the providers list"""
    print("📋 Step 1: Checking available providers...")
    print("-" * 60)

    try:
        response = requests.get(f"{BASE_URL}/providers/available")
        data = response.json()

        if data.get("success") and "orangehrm" in data.get("providers", {}):
            orangehrm = data["providers"]["orangehrm"]
            print("✅ OrangeHRM is available!\n")
            print(f"   Name: {orangehrm['name']}")
            print(f"   API Type: {orangehrm['api_type']}")
            print(f"   Authentication: {orangehrm['authentication']}")
            print(f"   Features: {', '.join(orangehrm['features'])}")
            print(f"   Setup Difficulty: {orangehrm['setup_difficulty']}")
            print(f"   Data Freshness: {orangehrm['data_freshness']}")
            if "demo_url" in orangehrm:
                print(f"   Demo URL: {orangehrm['demo_url']}")
            if "docs" in orangehrm:
                print(f"   Documentation: {orangehrm['docs']}")
            return True
        else:
            print("❌ OrangeHRM not found in providers")
            print(f"   Available providers: {list(data.get('providers', {}).keys())}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_connection_example():
    """Show example connection request"""
    print("\n🔗 Step 2: Example OrangeHRM connection request...")
    print("-" * 60)

    example = {
        "provider": "orangehrm",
        "organization_id": 1,
        "connection_parameters": {
            "base_url": "https://your-orangehrm-instance.com",
            "client_id": "your-oauth-client-id",
            "client_secret": "your-oauth-client-secret",
            "db_host": "localhost",
            "db_name": "orangehrm",
            "db_user": "orangehrm_user",
            "db_password": "your-db-password",
        },
        "data_permissions": ["standard"],
        "sync_settings": {"frequency": "daily", "auto_sync": True},
        "auto_sync_enabled": True,
    }

    print("POST /api/v1/hris/connection/setup")
    print(json.dumps(example, indent=2))
    print("\n⚠️  Note: This requires:")
    print("   1. Authentication token (login to get it)")
    print("   2. Your own OrangeHRM instance")
    print("   3. OAuth credentials from OrangeHRM admin")


def test_frontend():
    """Test if frontend is accessible"""
    print("\n📊 Step 3: Testing frontend accessibility...")
    print("-" * 60)

    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            print(f"✅ Frontend is accessible: {FRONTEND_URL}")
            print("   Open this URL in your browser to see the HRIS Connector UI")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing frontend: {e}")
        return False


def show_next_steps():
    """Show next steps for the user"""
    print("\n🎯 Next Steps:")
    print("-" * 60)
    print(
        """
1. VIEW THE UI:
   Open http://localhost:5173/hris-connector in your browser

2. FOR YOUR OWN ORANGEHRM:
   a) Install dependencies: pip install pymysql python-dateutil
   b) Setup OAuth in OrangeHRM admin panel
   c) Get authentication token from PsychSync
   d) Create connection using API call

3. FOR DEMO/TESTING:
   Use the CSV connector to import exported OrangeHRM data

4. DOCUMENTATION:
   - API Docs: http://localhost:8000/docs
   - OrangeHRM API: https://orangehrm.github.io/orangehrm-api-doc/
   - Connector Code: app/integrations/hris/orangehrm_connector.py
"""
    )


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 OrangeHRM Connection Test for PsychSync HRIS Connector")
    print("=" * 60)
    print()

    results = []

    # Test 1: Check providers
    results.append(("Providers Check", test_providers()))

    # Test 2: Show connection example
    show_connection_example()

    # Test 3: Test frontend
    results.append(("Frontend Check", test_frontend()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your HRIS Connector is ready!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main()
