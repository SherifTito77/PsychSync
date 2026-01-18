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


def get_jira_issues(client, auth_headers):
    """
    Test GET /issues
    Get Jira issues with filtering
    """
    # TODO: Implement test logic
    response = client.get("/issues",
        params={'skip': 'test_value', 'limit': 'test_value', 'project_key': 'test_value', 'issue_type': 'test_value', 'status': 'test_value', 'is_bug': 'test_value', 'sprint_id': 'test_value'}
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


def get_latest_bug_summary(client, auth_headers):
    """
    Test GET /bugs/summary/latest
    Get the latest bug summary for a project
    """
    # TODO: Implement test logic
    response = client.get("/bugs/summary/latest",
        params={'project_key': 'test_value'}
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


def get_bug_summaries(client, auth_headers):
    """
    Test GET /bugs/summary
    Get bug summaries for a date range
    """
    # TODO: Implement test logic
    response = client.get("/bugs/summary",
        params={'project_key': 'test_value', 'days': 'test_value'}
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


def get_bug_trends(client, auth_headers):
    """
    Test GET /bugs/trends
    Get bug trend data over time
    """
    # TODO: Implement test logic
    response = client.get("/bugs/trends",
        params={'project_key': 'test_value', 'days': 'test_value'}
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


def get_sprints(client, auth_headers):
    """
    Test GET /sprints
    Get sprint metrics
    """
    # TODO: Implement test logic
    response = client.get("/sprints",
        params={'project_key': 'test_value', 'state': 'test_value'}
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


def get_sprint_details(client, auth_headers):
    """
    Test GET /sprints/{sprint_id}
    Get detailed sprint metrics
    """
    # TODO: Implement test logic
    response = client.get("/sprints/{sprint_id}",
        params={'sprint_id': 'test_value'}
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


def get_performance_report(client, auth_headers):
    """
    Test GET /reports/performance
    Generate engineering performance report
    """
    # TODO: Implement test logic
    response = client.get("/reports/performance",
        params={'project_key': 'test_value', 'days': 'test_value'}
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


def health_check(client, auth_headers):
    """
    Test GET /health
    Health check endpoint for Jira integration
    """
    # TODO: Implement test logic
    response = client.get(
        "/health"

    )

    assert response.status_code in [200, 201]
    # TODO: Validate response data structure
    data = response.json()
    assert isinstance(data, dict)
