# app/tests/conftest.py
import pytest
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from faker import Faker

from app.main import app
from app.core.database import Base
from app.api.deps import get_async_db as get_db
from app.db.models.user import User
from app.db.models.team import Team, TeamMember, TeamRole
# FIX: Import the function directly instead of a non-existent class
from app.services.user_service import create_user

# Initialize Faker
fake = Faker()

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user"""
    from app.schemas.user import UserCreate
    user_data = UserCreate(
        email=fake.email(),
        full_name=fake.name(),
        password="Test1234"
    )
    # FIX: Use the function directly instead of UserService.create
    user = create_user(db, user_data=user_data)
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_admin(db: Session) -> User:
    """Create a test admin user"""
    from app.schemas.user import UserCreate
    user_data = UserCreate(
        email=fake.email(),
        full_name="Admin User",
        password="Admin1234"
    )
    # FIX: Use the function directly instead of UserService.create
    user = create_user(db, user_data=user_data)
    user.is_verified = True
    user.role = UserRole.ADMIN
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> Dict[str, str]:
    """Get authentication headers"""
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": test_user.email,
            "password": "Test1234"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client: TestClient, test_admin: User) -> Dict[str, str]:
    """Get admin authentication headers"""
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": test_admin.email,
            "password": "Admin1234"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_team(db: Session, test_user: User) -> Team:
    """Create a test team"""
    from app.services.team_service import TeamService
    from app.schemas.team import TeamCreate
    
    team_data = TeamCreate(
        name=fake.company(),
        description=fake.text()
    )
    team = TeamService.create(db, team_in=team_data, creator_id=test_user.id)
    return team

@pytest.fixture
def test_assessment(db: Session, test_user: User):
    """Create a test assessment"""
    from app.db.models.assessment import Assessment, AssessmentSection, Question, AssessmentCategory, AssessmentStatus
    
    assessment = Assessment(
        title=fake.sentence(),
        description=fake.text(),
        category=AssessmentCategory.PERSONALITY,
        status=AssessmentStatus.DRAFT,
        created_by_id=test_user.id
    )
    db.add(assessment)
    db.flush()
    
    section = AssessmentSection(
        assessment_id=assessment.id,
        title="Test Section",
        order=0
    )
    db.add(section)
    db.flush()
    
    question = Question(
        section_id=section.id,
        question_type="likert",
        question_text="Test question?",
        order=0,
        is_required=True
    )
    db.add(question)
    db.commit()
    db.refresh(assessment)
    
    return assessment