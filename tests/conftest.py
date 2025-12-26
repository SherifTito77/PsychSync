"""
Comprehensive test configuration with database fixtures and enhanced setup
- Async database testing with proper isolation
- Authentication fixtures for different user roles
- Mock services and external dependencies
- Test data factories with realistic data
- Performance testing utilities
- Integration test setup with proper environment
"""

import asyncio
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator, Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json
import tempfile
import os

# Set test environment before importing application modules
os.environ['ENVIRONMENT'] = 'testing'
os.environ['TESTING'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'  # Test database

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from faker import Faker
import redis.asyncio as redis
from aiofiles import tempfile as aiotempfile

from app.main import app
from app.core.database import Base, get_async_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.models.user import User, UserRole
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.organization import Organization
from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus
from app.schemas.user import UserCreate
from app.services.user_service import create_user
from app.services.team_service import TeamService

# Initialize Faker
fake = Faker()

# Test Database Configuration
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
SQLALCHEMY_SYNC_DATABASE_URL = "sqlite:///:memory:"

# Create async test engine
test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    },
)

# Create sync test engine for migrations
sync_test_engine = create_engine(
    SQLALCHEMY_SYNC_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    },
)

# Create session factories
TestSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

SyncTestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test function
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            # Clean up database
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def test_db_sync() -> Generator[Session, None, None]:
    """
    Create a fresh synchronous database session for each test function
    """
    # Create all tables
    Base.metadata.create_all(bind=sync_test_engine)

    # Create session
    session = SyncTestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up database
        Base.metadata.drop_all(bind=sync_test_engine)


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with database dependency override
    """
    app.dependency_overrides[get_async_db] = lambda: test_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client(test_db_sync: Session) -> Generator[TestClient, None, None]:
    """
    Create a synchronous test client for non-async tests
    """
    def override_get_db():
        try:
            yield test_db_sync
        finally:
            pass

    app.dependency_overrides[get_async_db] = override_get_db

    with TestClient(app=app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Generate sample user data for testing"""
    return {
        "email": fake.email(),
        "full_name": fake.name(),
        "role": UserRole.USER,
        "is_active": True,
        "password": "TestPassword123!"
    }


@pytest.fixture
def sample_organization_data():
    """Generate sample organization data for testing"""
    return {
        "name": fake.company(),
        "description": fake.text(max_nb_chars=200),
        "is_active": True,
        "settings": {}
    }


@pytest.fixture
def sample_team_data():
    """Generate sample team data for testing"""
    return {
        "name": f"Team {fake.company()}",
        "description": fake.text(max_nb_chars=200),
        "is_active": True
    }


@pytest.fixture
async def test_user(test_db: AsyncSession, sample_user_data: Dict[str, Any]) -> User:
    """Create a test user in the database"""
    user_data = UserCreate(**sample_user_data)
    user = await create_user(user_data, test_db)
    return user


@pytest.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """Create a test admin user in the database"""
    admin_data = UserCreate(
        email=fake.email(),
        full_name=fake.name(),
        role=UserRole.ADMIN,
        is_active=True,
        password="AdminPassword123!"
    )
    admin = await create_user(admin_data, test_db)
    return admin


@pytest.fixture
async def test_organization(test_db: AsyncSession, sample_organization_data: Dict[str, Any]) -> Organization:
    """Create a test organization in the database"""
    org = Organization(**sample_organization_data)
    test_db.add(org)
    await test_db.commit()
    await test_db.refresh(org)
    return org


@pytest.fixture
async def test_team(test_db: AsyncSession, sample_team_data: Dict[str, Any], test_organization: Organization) -> Team:
    """Create a test team in the database"""
    team_data = sample_team_data.copy()
    team_data["organization_id"] = test_organization.id
    team = Team(**team_data)
    test_db.add(team)
    await test_db.commit()
    await test_db.refresh(team)
    return team


@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """Generate authentication headers for a test user"""
    token_data = {"sub": test_user.email, "user_id": test_user.id}
    access_token = create_access_token(data=token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(test_admin: User) -> Dict[str, str]:
    """Generate authentication headers for a test admin"""
    token_data = {"sub": test_admin.email, "user_id": test_admin.id}
    access_token = create_access_token(data=token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_redis():
    """Create a test Redis connection"""
    try:
        redis_client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        # Test connection
        await redis_client.ping()
        yield redis_client
        # Clean up test data
        await redis_client.flushdb()
        await redis_client.close()
    except Exception:
        # Skip Redis tests if Redis is not available
        pytest.skip("Redis not available for testing")


@pytest.fixture
def mock_email_service():
    """Mock email service for testing"""
    with patch('app.services.email_service.send_email') as mock_send:
        mock_send.return_value = True
        yield mock_send


@pytest.fixture
def mock_ai_service():
    """Mock AI processing service for testing"""
    with patch('app.services.nlp_service.process_text') as mock_process:
        mock_process.return_value = {
            "personality_traits": {},
            "confidence_score": 0.85,
            "recommendations": []
        }
        yield mock_process


@pytest.fixture
def performance_monitor():
    """Monitor performance during tests"""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_usage = []

        def start(self):
            import time
            import psutil
            self.start_time = time.time()
            process = psutil.Process()
            self.memory_usage.append(process.memory_info().rss)

        def stop(self):
            import time
            import psutil
            self.end_time = time.time()
            process = psutil.Process()
            self.memory_usage.append(process.memory_info().rss)

        def get_duration(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def get_memory_delta(self) -> int:
            if len(self.memory_usage) >= 2:
                return self.memory_usage[-1] - self.memory_usage[0]
            return 0

    return PerformanceMonitor()


# Test Data Factories
@pytest.fixture
def user_factory():
    """Factory for creating multiple test users"""
    created_users = []

    async def create_user(test_db: AsyncSession, role: UserRole = UserRole.USER, **kwargs) -> User:
        user_data = {
            "email": fake.email(),
            "full_name": fake.name(),
            "role": role,
            "is_active": True,
            "password": "TestPassword123!",
            **kwargs
        }
        user_create = UserCreate(**user_data)
        user = await create_user(user_create, test_db)
        created_users.append(user)
        return user

    yield create_user

    # Cleanup
    # Note: Users are automatically cleaned up with test database


@pytest.fixture
def assessment_factory():
    """Factory for creating test assessments"""
    created_assessments = []

    async def create_assessment(
        test_db: AsyncSession,
        organization_id: int,
        created_by_id: int,
        **kwargs
    ) -> Assessment:
        assessment_data = {
            "title": fake.sentence(),
            "description": fake.text(max_nb_chars=500),
            "category": fake.choice(list(AssessmentCategory)),
            "status": AssessmentStatus.DRAFT,
            "organization_id": organization_id,
            "created_by_id": created_by_id,
            **kwargs
        }
        assessment = Assessment(**assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)
        created_assessments.append(assessment)
        return assessment

    yield create_assessment

    # Cleanup is handled by test database teardown


# Performance Testing Fixtures
@pytest.fixture
def load_test_config():
    """Configuration for load testing"""
    return {
        "concurrent_users": 10,
        "requests_per_user": 50,
        "ramp_up_time": 5,  # seconds
        "test_duration": 30,  # seconds
        "target_endpoints": [
            "/api/v1/health",
            "/api/v1/users/me",
            "/api/v1/assessments"
        ]
    }


@pytest.fixture
def stress_test_config():
    """Configuration for stress testing"""
    return {
        "max_concurrent_requests": 100,
        "duration": 60,  # seconds
        "memory_limit_mb": 512,
        "response_time_limit_ms": 2000
    }


# Security Testing Fixtures
@pytest.fixture
def security_test_vectors():
    """Security test vectors for various attack patterns"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "UNION SELECT * FROM users",
            "'; INSERT INTO users VALUES('hacker','pass'); --"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "';alert('xss');//",
            "<svg onload=alert('xss')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "& echo 'hack'",
            "`whoami`",
            "$(id)"
        ]
    }


# Error Handling Fixtures
@pytest.fixture
def error_simulation():
    """Simulate various error conditions"""
    class ErrorSimulator:
        def __init__(self):
            self.enabled_errors = {}

        def enable_error(self, error_type: str, exception: Exception):
            self.enabled_errors[error_type] = exception

        def disable_error(self, error_type: str):
            self.enabled_errors.pop(error_type, None)

        def should_raise(self, error_type: str) -> bool:
            return error_type in self.enabled_errors

        def get_exception(self, error_type: str) -> Exception:
            return self.enabled_errors.get(error_type)

    return ErrorSimulator()


# Monitoring and Logging Fixtures
@pytest.fixture
def log_capture():
    """Capture log messages during tests"""
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield log_stream

    # Cleanup
    logger.removeHandler(handler)
    handler.close()


# Environment Configuration Fixtures
@pytest.fixture
def test_environment_config():
    """Test-specific environment configuration"""
    return {
        "ENVIRONMENT": "testing",
        "TESTING": "True",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "EMAIL_VERIFICATION_ENABLED": "False",
        "RATE_LIMIT_ENABLED": "False"  # Disable for testing
    }