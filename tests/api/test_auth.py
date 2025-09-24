# tests/api/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        payload = UserCreate(email="login@test.com", password="secret", full_name="Login Test")
        reg_resp = await ac.post("/auth/register", json=payload.dict())
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        assert data["email"] == "login@test.com"

        # Login
        login_resp = await ac.post("/auth/login", data={"username": "login@test.com", "password": "secret"})
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
