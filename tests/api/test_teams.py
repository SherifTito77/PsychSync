from app.core.database import get_async_db
from app.services.security import create_access_token
from app.db.models.user import User
from app.main import app
from app.schemas.team import TeamCreate
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session
import pytest
@pytest.mark.asyncio
async def test_create_team():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = TeamCreate(name="Dev Team", members=[1, 2])
        response = await ac.post("/teams/", json=payload.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dev Team"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_team():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/teams/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1




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


def get_team(client, auth_headers):
    """
    Test GET /{team_id}
    Get a specific team by ID with its members
    """
    # TODO: Implement test logic
    response = client.get("/{team_id}",
        params={'team_id': 'test_value'}
    )

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)
