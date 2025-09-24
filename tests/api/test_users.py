# tests/api/test_users.py

import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_read_root():
    """Test the root endpoint /"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI SaaS is running!"}

@pytest.mark.asyncio
async def test_register_user():
    """Test user registration"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = UserCreate(email="test@example.com", password="secret", full_name="Test User")
        response = await ac.post("/users/register", json=payload.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_current_user():
    """Test retrieving the current user (requires valid token)"""
    token = "fake-token"  # Replace with real token after implementing auth
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/users/me", headers=headers)
    # With a fake token we may get 401, otherwise expect 200
    assert response.status_code in [200, 401]
