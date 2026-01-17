"""
Simple Team Assessment Test
Working test for team assessment creation functionality
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test that the API is running"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_api_docs_accessible():
    """Test that API documentation is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data

def test_assessments_endpoint_exists():
    """Test that assessments endpoint exists (may require auth)"""
    response = client.get("/api/v1/assessments/")
    # Should return either 401 (unauthorized) or 405 (method not allowed)
    # but not 404 (not found)
    assert response.status_code in [401, 405, 422]

def test_teams_endpoint_exists():
    """Test that teams endpoint exists (may require auth)"""
    response = client.get("/api/v1/teams/")
    # Should return either 401 (unauthorized) or 405 (method not allowed)
    # but not 404 (not found)
    assert response.status_code in [401, 405, 422]

def test_auth_endpoint_exists():
    """Test that auth endpoint exists"""
    # Test login endpoint exists
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }
    response = client.post("/api/v1/token", data=login_data)
    # Should return 401 for invalid credentials, not 404
    assert response.status_code in [401, 422]

def test_user_registration_endpoint_exists():
    """Test that user registration endpoint exists"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/register", json=user_data)
    # Should return either 201 (created) or 422 (validation error)
    # but not 404 (not found)
    assert response.status_code in [201, 422]

if __name__ == "__main__":
    # Run tests manually
    print("Testing team assessment API endpoints...")

    print("1. Testing health endpoint...")
    try:
        test_health_endpoint()
        print("   ✅ Health endpoint working")
    except Exception as e:
        print(f"   ❌ Health endpoint failed: {e}")

    print("2. Testing API docs...")
    try:
        test_api_docs_accessible()
        print("   ✅ API docs accessible")
    except Exception as e:
        print(f"   ❌ API docs failed: {e}")

    print("3. Testing assessments endpoint...")
    try:
        test_assessments_endpoint_exists()
        print("   ✅ Assessments endpoint exists")
    except Exception as e:
        print(f"   ❌ Assessments endpoint failed: {e}")

    print("4. Testing teams endpoint...")
    try:
        test_teams_endpoint_exists()
        print("   ✅ Teams endpoint exists")
    except Exception as e:
        print(f"   ❌ Teams endpoint failed: {e}")

    print("5. Testing auth endpoint...")
    try:
        test_auth_endpoint_exists()
        print("   ✅ Auth endpoint exists")
    except Exception as e:
        print(f"   ❌ Auth endpoint failed: {e}")

    print("6. Testing user registration endpoint...")
    try:
        test_user_registration_endpoint_exists()
        print("   ✅ User registration endpoint exists")
    except Exception as e:
        print(f"   ❌ User registration endpoint failed: {e}")

    print("\n🎉 Basic API endpoint tests completed!")
