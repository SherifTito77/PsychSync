from app.core.database import get_async_db
from app.services.security import create_access_token
from app.db.models.user import User
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
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


def list_all_users(client, auth_headers):
    """
    Test GET /users
    Retrieve all users. Requires superuser privileges.
    """
    # TODO: Implement test logic
    response = client.get("/users",
        params={'skip': 'test_value', 'limit': 'test_value', 'is_active': 'test_value'}
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


def soft_delete_user(client, auth_headers):
    """
    Test DELETE /users/{user_id}
    Soft-delete a user by deactivating them. Requires superuser privileges.
    """
    # TODO: Implement test logic
    response = client.delete("/users/{user_id}",
        params={'user_id': 'test_value'}
    )

    assert response.status_code in [200, 204]




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


def restore_user_endpoint(client, auth_headers):
    """
    Test POST /users/{user_id}/restore
    Restore a soft-deleted user. Requires superuser privileges.
    """
    # TODO: Implement test logic
    response = client.post(
        "/users/{user_id}/restore",
        json={},
        params={'user_id': 'test_value'}
    )

    assert response.status_code in [200, 201, 202]
