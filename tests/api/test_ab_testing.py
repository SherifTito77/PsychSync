from app.core.database import get_async_db
from app.core.security import create_access_token
from app.db.models.user import User
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
@pytest.fixture

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


def test_assign_variant(client, auth_headers):
    """
    Test POST /assign
    Assign user to a variant for the given experiment.
    """
    response = client.post(
        "/api/v1/ab/assign",
        json={
            "experiment_name": "test_experiment",
            "user_id": "test_user_123"
        },
        headers=auth_headers
    )

    # Assert response is successful
    assert response.status_code in [200, 201, 202]

    # Assert response has expected structure
    data = response.json()
    assert "variant" in data or "success" in data or "message" in data




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


def test_track_event(client, auth_headers):
    """
    Test POST /track
    Track an event for an A/B test variant.
    """
    response = client.post(
        "/api/v1/ab/track",
        json={
            "experiment_name": "test_experiment",
            "event_type": "click",
            "user_id": "test_user_123",
            "variant": "A"
        },
        headers=auth_headers
    )

    # Assert response is successful
    assert response.status_code in [200, 201, 202]

    # Assert response has expected structure
    data = response.json()
    assert "success" in data or "message" in data or "event_id" in data




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


def list_experiments(client, auth_headers):
    """
    Test GET /experiments
    List all A/B experiments.
    """
    # TODO: Implement test logic
    response = client.get("/experiments",
        params={'status': 'test_value', 'limit': 'test_value', 'offset': 'test_value'}
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


def get_experiment_results(client):
    """
    Test GET /results/{experiment_name}
    Get results for an experiment including conversion rates and statistical significance.
    """
    # TODO: Implement test logic
    response = client.get("/results/{experiment_name}",
        params={'experiment_name': 'test_value'}
    )

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)
