from app.core.database import get_async_db
from app.core.security import create_access_token
from app.db.models.user import User
from app.main import app
from app.schemas.user import UserCreate
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
import pytest
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





def test_register_user(client: TestClient, test_db):
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


def test_register_duplicate_email(client: TestClient, test_db: Session):
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


def test_register_weak_password(client: TestClient, test_db: Session):
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


def test_login_success(client: TestClient, test_db: Session):
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


def test_login_wrong_password(client: TestClient, test_db: Session):
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


def test_login_nonexistent_user(client: TestClient, test_db: Session):
    """Test login with nonexistent user"""
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": "nonexistent@example.com",
            "password": "Test1234"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client: TestClient, test_db: Session):
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


def test_get_current_user_invalid_token(client: TestClient, test_db: Session):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_get_current_user_no_token(client: TestClient, test_db: Session):
    """Test getting current user without token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401





@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def login_for_access_token_fixed(client):
    """
    Test POST /token-fixed
    Fixed authentication endpoint with proper security
    """
    # TODO: Implement test logic
    response = client.post(
        "/token-fixed",
        json={},
        params={'form_data': 'test_value'}
    )

    assert response.status_code in [200, 201, 202]




@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def register_user_fixed(client):
    """
    Test POST /register-fixed
    Fixed user registration with proper validation
    """
    # TODO: Implement test logic
    response = client.post(
        "/register-fixed",
        json={},
        params={'email': 'test_value', 'password': 'test_value', 'full_name': 'test_value'}
    )

    assert response.status_code in [200, 201, 202]




@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def get_current_user_info_fixed(client, auth_headers):
    """
    Test GET /me-fixed
    Fixed endpoint to get current user information with proper token validation
    """
    # TODO: Implement test logic
    response = client.get(
        "/me-fixed"

    )

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)




@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def logout(client, auth_headers):
    """
    Test POST /logout
    Logout endpoint that clears httpOnly cookies
    """
    # TODO: Implement test logic
    response = client.post(
        "/logout",
        json={}
    )

    assert response.status_code in [200, 201, 202]




@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def logout_user_fixed(client, auth_headers):
    """
    Test POST /logout-fixed
    Fixed logout endpoint that properly invalidates tokens and sessions
    """
    # TODO: Implement test logic
    response = client.post(
        "/logout-fixed",
        json={}
    )

    assert response.status_code in [200, 201, 202]




@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def refresh_token_fixed(client):
    """
    Test POST /refresh-token-fixed
    Fixed token refresh endpoint (simplified for demo)
    """
    # TODO: Implement test logic
    response = client.post(
        "/refresh-token-fixed",
        json={},
        params={'refresh_token': 'test_value'}
    )

    assert response.status_code in [200, 201, 202]




@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db_session():
    async for session in get_async_db():
        yield session

@pytest.fixture
def test_user(db_session: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def health_check_fixed(client):
    """
    Test GET /health-fixed
    Health check endpoint for authentication service
    """
    # TODO: Implement test logic
    response = client.get(
        "/health-fixed"

    )

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)
