import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def test_user(client):
    user_data = {
        "email": "smoke_test_user@psychsync.ai",
        "password": "SecurePassword123!",
        "full_name": "Smoke Test User",
    }
    # Register
    client.post("/api/v1/auth/register", json=user_data)
    # Login to get token
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/api/v1/login", data=login_data)
    token = response.json()["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture(scope="module")
def auth_client(client, test_user):
    client.headers.update(test_user["headers"])
    return client
