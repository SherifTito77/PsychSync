"""
Full Stack Integration Test
Tests the complete user journey from registration to assessment completion.
Runs in-process using ASGITransport and AsyncClient.
"""

import time

import httpx
import pytest

from app.main import app


@pytest.fixture
async def client():
    # Use ASGITransport to test the app in-process
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver", timeout=30
    ) as client:
        yield client


@pytest.fixture
def test_user():
    return {
        # Using .com to avoid reserved TLD issues
        "email": f"user_{int(time.time())}@example.com",
        # Using a password that doesn't contain 'test' to pass security checks
        "password": "SecurePass123!",
        "full_name": "Integration Test User",
    }


@pytest.mark.asyncio
class TestCoreJourney:

    async def test_01_server_is_running(self, client):
        r = await client.get("/")
        assert r.status_code == 200
        assert "PsychSync" in r.json().get("message", "")

    async def test_02_health_check(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"

    async def test_03_register_user(self, client, test_user):
        r = await client.post("/api/v1/register", json=test_user)
        assert r.status_code < 400, f"Register failed: {r.text}"

    async def test_04_login_user(self, client, test_user):
        # First register
        await client.post("/api/v1/register", json=test_user)
        # Then login
        r = await client.post(
            "/api/v1/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        assert r.status_code == 200, f"Login failed: {r.text}"
        print(f"Login response: {r.json()}")
        data = r.json()
        assert "access_token" in data

    async def test_05_get_profile(self, client, test_user):
        await client.post("/api/v1/register", json=test_user)
        login_r = await client.post(
            "/api/v1/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        token = login_r.json()["access_token"]

        r = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        assert test_user["email"].lower() in str(r.json()).lower()

    async def test_06_list_assessments(self, client, test_user):
        await client.post("/api/v1/register", json=test_user)
        login_r = await client.post(
            "/api/v1/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        token = login_r.json()["access_token"]

        r = await client.get(
            "/api/v1/assessments", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
