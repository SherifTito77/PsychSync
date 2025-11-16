
# tests/api/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.user import UserCreate

# app/tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        payload = UserCreate(email="login@test.com", password="secret", full_name="Login Test")
        reg_resp = await ac.post("/api/v1/auth/register", json=payload.model_dump())
        assert reg_resp.status_code == 200, reg_resp.text
        data = reg_resp.json()
        assert data["email"] == payload.email

        # Login
        login_resp = await ac.post(
            "/api/v1/auth/login",
            data={"username": payload.email, "password": payload.password}
        )
        assert login_resp.status_code == 200, login_resp.text
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data["token_type"].lower() == "bearer"
# @pytest.mark.asyncio
# async def test_register_and_login():
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         # Register
#         payload = UserCreate(email="login@test.com", password="secret", full_name="Login Test")
#         reg_resp = await ac.post("/auth/register", json=payload.dict())
#         assert reg_resp.status_code == 200
#         data = reg_resp.json()
#         assert data["email"] == "login@test.com"

#         # Login
#          # Fix: Add /api/v1 prefix
#         reg_resp = await ac.post("/api/v1/auth/register", json=payload.model_dump())
#         assert reg_resp.status_code == 200
#         # login_resp = await ac.post("/auth/login", data={"username": "login@test.com", "password": "secret"})
#         # assert login_resp.status_code == 200
#         token_data = login_resp.json()
#         assert "access_token" in token_data
#         assert token_data["token_type"] == "bearer"

       


def test_register_user(client: TestClient, db: Session):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Test1234"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "password" not in data


def test_register_duplicate_email(client: TestClient, db: Session):
    """Test registration with duplicate email"""
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Test1234"
        }
    )
    
    # Try to register with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Another User",
            "password": "Test1234"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_weak_password(client: TestClient, db: Session):
    """Test registration with weak password"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "weak"
        }
    )
    assert response.status_code == 422


def test_login_success(client: TestClient, db: Session):
    """Test successful login"""
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Test1234"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, db: Session):
    """Test login with wrong password"""
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Test1234"
        }
    )
    
    # Try to login with wrong password
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123"
        }
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient, db: Session):
    """Test login with nonexistent user"""
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": "nonexistent@example.com",
            "password": "Test1234"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client: TestClient, db: Session):
    """Test getting current user info"""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Test1234"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


def test_get_current_user_invalid_token(client: TestClient, db: Session):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_get_current_user_no_token(client: TestClient, db: Session):
    """Test getting current user without token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    
    