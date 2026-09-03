import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_async_db
from app.db.models.user import User
from app.main import app
from app.services.security import create_access_token


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
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def simple_login(client):
    """
    Test POST /simple-login
    Simple login endpoint that works without complex dependencies
    """
    # TODO: Implement test logic
    response = client.post(
        "/simple-login",
        json={},
        params={"username": "test_value", "password": "test_value"},
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
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def verify_token(client, auth_headers):
    """
    Test GET /verify-token/{token}
    Simple token verification endpoint
    """
    # TODO: Implement test logic
    response = client.get("/verify-token/{token}")

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
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def get_current_user_info(client):
    """
    Test GET /me
    Simple endpoint to get current user info from Authorization header
    """
    # TODO: Implement test logic
    response = client.get("/me")

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)
