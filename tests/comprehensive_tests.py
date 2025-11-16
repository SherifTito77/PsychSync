# tests/comprehensive_tests.py
# FIXED IMPORTS for PsychSync project

import sys
import os
import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# =================================================================
# FIXTURES
# =================================================================

@pytest.fixture
def db_session():
    """Mock database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
async def api_client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from app.main import app  # FIXED: Changed from 'main' to 'app.main'
    
    client = TestClient(app)
    yield client

# =================================================================
# API ENDPOINT TESTS
# =================================================================

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200
        # Adjust assertion based on your actual health check response
        data = response.json()
        assert 'status' in data or 'message' in data

# NOTE: The rest of the tests reference NBA-specific modules that don't exist
# in PsychSync. You should either:
# 1. Remove these tests entirely
# 2. Rewrite them to test your actual PsychSync endpoints

# EXAMPLE: Test PsychSync-specific endpoints instead
class TestPsychSyncEndpoints:
    """Test PsychSync API endpoints"""
    
    def test_user_endpoints(self, api_client):
        """Test user-related endpoints exist"""
        # Test registration endpoint
        response = api_client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "Test1234"
        })
        # May succeed or fail based on validation, but shouldn't crash
        assert response.status_code in [200, 201, 400, 422]
    
    def test_auth_endpoints(self, api_client):
        """Test authentication endpoints"""
        response = api_client.post("/api/v1/auth/login/json", json={
            "email": "test@example.com",
            "password": "Test1234"
        })
        # Should return 401 for invalid credentials or 200 for valid
        assert response.status_code in [200, 401, 422]

# =================================================================
# DATABASE TESTS
# =================================================================

class TestDatabase:
    """Test database operations"""
    
    def test_user_model_creation(self, db_session):
        """Test creating a user in the database"""
        from app.db.models.user import User
        from app.core.database import Base
        
        # Create tables
        Base.metadata.create_all(bind=db_session.bind)
        
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed_password",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved is not None
        assert retrieved.email == "test@example.com"

# =================================================================
# PYTEST CONFIGURATION
# =================================================================

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# =================================================================
# RUN TESTS
# =================================================================

if __name__ == '__main__':
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
    ])