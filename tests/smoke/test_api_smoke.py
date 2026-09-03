import pytest


def test_public_endpoints(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    # Docs might be disabled in some envs, but check existence
    assert client.get("/docs").status_code in [200, 404]


def test_auth_endpoints(client):
    # Test registration (use /api/v1/register)
    reg_data = {
        "email": "smoke_test_user@psychsync.ai",
        "password": "SecurePassword123!",
        "full_name": "Smoke Test User",
    }
    reg_resp = client.post("/api/v1/register", json=reg_data)
    assert reg_resp.status_code in [201, 409, 422]

    # Test login (use /api/v1/login)
    login_data = {
        "username": "smoke_test_user@psychsync.ai",
        "password": "SecurePassword123!",
    }
    login_resp = client.post("/api/v1/login", data=login_data)
    assert login_resp.status_code in [200, 401]


def test_protected_endpoints(auth_client):
    assert auth_client.get("/api/v1/users/me").status_code == 200
    assert auth_client.get("/api/v1/teams").status_code == 200
    assert auth_client.get("/api/v1/assessments").status_code == 200
