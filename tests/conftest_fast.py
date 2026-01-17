# Fast test configuration with optimized fixtures
# Designed for rapid development feedback

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, Any, Generator, Optional
import time
from contextlib import contextmanager

# Test data fixtures
@pytest.fixture
def sample_assessment_data():
    """Sample valid assessment request data"""
    return {
        "role": "manager",
        "challenge": "communication",
        "team_size": 5,
        "industry": "technology"
    }

@pytest.fixture
def sample_user_data():
    """Sample valid user registration data"""
    return {
        "email": "test.user@psychsync.com",
        "password": "SecureTestPass123!",
        "full_name": "Test User",
        "organization": "Test Org"
    }

@pytest.fixture(params=["manager", "hr", "lead", "member", "executive"])
def all_roles(request):
    """Parametrized fixture for all user roles"""
    return request.param

@pytest.fixture(params=["communication", "productivity", "turnover", "engagement"])
def all_challenges(request):
    """Parametrized fixture for all team challenges"""
    return request.param

# Fast app fixture with mocked dependencies
@pytest.fixture
def fast_app():
    """
    Fast app fixture with mocked database and Redis
    Avoids slow external dependencies
    """
    # Mock the database dependencies before importing
    import sys
    from unittest.mock import patch

    # Create mocks for database operations
    mock_session = AsyncMock()
    mock_session.execute.return_value.scalar.return_value = 1
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None
    mock_session.close.return_value = None

    # Mock Redis operations
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.exists.return_value = False

    with patch('app.core.database.get_async_db') as mock_get_db:
        mock_get_db.return_value.__aenter__.return_value = mock_session
        mock_get_db.return_value.__aexit__.return_value = None

        with patch('app.core.redis_client.get_redis_client') as mock_get_redis:
            mock_get_redis.return_value = mock_redis

            with patch('redis.asyncio.from_url', return_value=mock_redis):
                # Import app after mocking dependencies
                from app.main import app
                yield app

@pytest.fixture
def fast_client(fast_app):
    """Fast test client with mocked dependencies"""
    return TestClient(fast_app)

# Validation-only fixtures (no API calls)
@pytest.fixture
def assessment_validator():
    """Fixture for testing assessment schema validation only"""
    from app.schemas.onboarding import QuickAssessmentRequest
    return QuickAssessmentRequest

@pytest.fixture
def user_validator():
    """Fixture for testing user schema validation only"""
    from app.schemas.user import UserCreate
    return UserCreate

# Performance measurement fixtures
@pytest.fixture
def performance_tracker():
    """Track test performance metrics"""
    start_time = time.time()

    class Tracker:
        def __init__(self):
            self.start_time = start_time
            self.checkpoints = []

        def checkpoint(self, name: str):
            self.checkpoints.append({
                "name": name,
                "elapsed": time.time() - self.start_time
            })

        def elapsed(self):
            return time.time() - self.start_time

    tracker = Tracker()
    yield tracker
    tracker.checkpoint("test_complete")

# Mock service fixtures
@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for testing"""
    service = AsyncMock()
    service.track_event.return_value = {"success": True, "event_id": "mock_event_123"}
    service.get_analytics.return_value = {"events": [], "total": 0}
    return service

@pytest.fixture
def mock_assessment_service():
    """Mock assessment service for testing"""
    service = AsyncMock()
    service.generate_insights.return_value = {
        "success": True,
        "insights": ["Mock insight 1", "Mock insight 2"],
        "recommendations": ["Mock recommendation"]
    }
    return service

# Error simulation fixtures
@pytest.fixture
def simulate_database_error():
    """Context manager to simulate database errors"""
    @contextmanager
    def error_context():
        import sys
        from unittest.mock import patch

        with patch('app.core.database.get_async_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            yield

    return error_context

@pytest.fixture
def simulate_redis_error():
    """Context manager to simulate Redis errors"""
    @contextmanager
    def error_context():
        from unittest.mock import patch

        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            yield

    return error_context

# Pytest configuration
def pytest_configure(config):
    """Configure pytest for fast testing"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup environment for fast testing"""
    # Set environment variables for testing
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ENVIRONMENT", "testing")

# Fast test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow

# Skip markers for faster testing
pytest.mark.skip_database = pytest.mark.skip(reason="Skipping database-dependent test for speed")
pytest.mark.skip_redis = pytest.mark.skip(reason="Skipping Redis-dependent test for speed")
