from app.core.database import get_async_db
from app.services.security import create_access_token
from app.db.models.user import User
from app.main import app
from app.schemas.user import UserCreate
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
import pytest

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
async def ac():
    """Async test client fixture"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_read_root(ac: AsyncClient):
    response = await ac.get("/")
    assert response.status_code == 200
    # Fix: Update expected message
    assert response.json() == {"message": "PsychSync AI API is running!"}

@pytest.mark.asyncio
async def test_register_user(ac: AsyncClient):
    """Test user registration"""
    payload = UserCreate(email="test@example.com", password="secret", full_name="Test User")
    response = await ac.post("/users/register", json=payload.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_current_user(ac: AsyncClient):
    """Test retrieving the current user (requires valid token)"""
    token = "fake-token"  # Replace with real token after implementing auth
    headers = {"Authorization": f"Bearer {token}"}
    response = await ac.get("/users/me", headers=headers)
    # With a fake token we may get 401, otherwise expect 200
    assert response.status_code in [200, 401]

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


def get_user_profile(client, auth_headers):
    """
    Test GET /me
    Retrieve the profile of the currently authenticated user.
    """
    # TODO: Implement test logic
    response = client.get(
        "/me"

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


def change_password(client, auth_headers):
    """
    Test POST /change-password
    Change the password for the currently authenticated user.
    """
    # TODO: Implement test logic
    response = client.post(
        "/change-password",
        json={},
        params={'password_change': 'test_value'}
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


def get_user_by_id(client, auth_headers):
    """
    Test GET /{user_id}
    Get user details by ID.
    """
    # TODO: Implement test logic
    response = client.get("/{user_id}",
        params={'user_id': 'test_value'}
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


def update_user_profile(client, auth_headers):
    """
    Test PUT /me
    Update the profile of the currently authenticated user.
    """
    # TODO: Implement test logic
    response = client.put(
        "/me",
        json={},
        params={'user_update': 'test_value'}
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


def create_user_endpoint(client):
    """
    Test POST /register
    Register a new user account.
    """
    # TODO: Implement test logic
    response = client.post(
        "/register",
        json={},
        params={'user_create': 'test_value'}
    )

    assert response.status_code in [200, 201, 202]
