from app.core.database import get_async_db
from app.core.security import create_access_token
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


def get_csrf_token(client):
    """
    Test GET /token
    Get a CSRF token for use in API requests
    """
    # TODO: Implement test logic
    response = client.get(
        "/token"

    )

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)
