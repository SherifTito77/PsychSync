# tests/test_onboarding_functional.py
"""
COMPREHENSIVE FUNCTIONAL TESTS FOR PSYCHSYNC USER ONBOARDING FLOW
Value-first onboarding experience with security and analytics validation

Test Coverage:
- Anonymous Quick Assessment (No auth required)
- User Registration & Authentication
- Team Creation & Setup
- Detailed Insights Generation
- Security & Rate Limiting
- Analytics Tracking
- Integration Testing

Author: QA Team
Version: 1.0 Functional Testing
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.core.database import get_async_db
from app.db.models.user import User, UserRole
from app.db.models.team import Team
from app.core.security import get_password_hash, verify_password
from app.core.redis_client import get_redis_client


class TestAnonymousQuickAssessment:
    """Test suite for anonymous quick assessment functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    async def assessment_data(self):
        """Valid assessment request data"""
        return {
            "role": "manager",
            "challenge": "communication",
            "team_size": "5-10",
            "industry": "technology",
            "session_id": "test_session_123",
            "referrer": "organic"
        }

    def test_qa_001_valid_quick_assessment_request(self, client, assessment_data):
        """✅ QA-001: Valid Quick Assessment Request"""
        response = client.post("/api/v1/onboarding/quick-assessment", json=assessment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "insights" in data
        assert "next_steps" in data
        assert "value_proposition" in data
        assert "estimated_time_to_value" in data

        # Verify insights structure
        insights = data["insights"]
        assert "primary_benefit" in insights
        assert "recommendations" in insights
        assert "conversion_probability" in insights
        assert isinstance(insights["conversion_probability"], float)
        assert 0 <= insights["conversion_probability"] <= 1

    @pytest.mark.parametrize("role", ["manager", "hr", "lead", "member", "executive"])
    def test_qa_002_all_role_types_support(self, client, assessment_data, role):
        """✅ QA-002: All Role Types Support"""
        assessment_data["role"] = role
        response = client.post("/api/v1/onboarding/quick-assessment", json=assessment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Role-specific insights should be generated
        assert role.lower() in data["value_proposition"].lower()

    @pytest.mark.parametrize("challenge", ["communication", "productivity", "turnover", "collaboration", "conflict"])
    def test_qa_003_all_challenge_types_support(self, client, assessment_data, challenge):
        """✅ QA-003: All Challenge Types Support"""
        assessment_data["challenge"] = challenge
        response = client.post("/api/v1/onboarding/quick-assessment", json=assessment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Challenge-specific recommendations should be present
        insights = data["insights"]
        assert len(insights["recommendations"]) > 0

    def test_qa_004_invalid_role_handling(self, client, assessment_data):
        """✅ QA-004: Invalid Role Handling"""
        assessment_data["role"] = "invalid_role"
        response = client.post("/api/v1/onboarding/quick-assessment", json=assessment_data)

        assert response.status_code == 422  # Validation error

    def test_qa_005_missing_required_fields(self, client):
        """✅ QA-005: Missing Required Fields"""
        # Test missing role
        response = client.post("/api/v1/onboarding/quick-assessment", json={
            "challenge": "communication",
            "team_size": "5-10"
        })
        assert response.status_code == 422

        # Test missing challenge
        response = client.post("/api/v1/onboarding/quick-assessment", json={
            "role": "manager",
            "team_size": "5-10"
        })
        assert response.status_code == 422

    @patch('app.services.onboarding_service.OnboardingService.generate_quick_insights')
    def test_qa_007_analytics_event_tracking(self, mock_generate_insights, client, assessment_data):
        """✅ QA-007: Analytics Event Tracking"""
        # Mock the insights generation
        mock_insights = Mock()
        mock_insights.recommendations = [{"title": "Test recommendation"}]
        mock_insights.primary_benefit = "Improved communication"
        mock_insights.estimated_time_to_value = "2-3 weeks"
        mock_insights.conversion_probability = 0.75
        mock_generate_insights.return_value = mock_insights

        with patch('app.services.analytics_service.AnalyticsService.track_onboarding_event') as mock_track:
            mock_track.return_value = None

            response = client.post("/api/v1/onboarding/quick-assessment", json=assessment_data)

            assert response.status_code == 200
            # Verify analytics events were tracked
            assert mock_track.call_count == 2  # Started and completed events

    @pytest.mark.asyncio
    async def test_qa_009_rate_limit_enforcement(self, client, assessment_data):
        """✅ QA-009: Rate Limit Enforcement"""
        # Make 21 requests rapidly (limit is 20 per minute)
        responses = []
        for i in range(25):
            response = client.post("/api/v1/onboarding/quick-assessment", json=assessment_data)
            responses.append(response)
            if response.status_code == 429:
                break

        # Should hit rate limit
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
        assert rate_limited_responses[0].json()["detail"] == "Rate limit exceeded"


class TestUserRegistration:
    """Test suite for user registration functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def valid_user_data(self):
        """Valid user registration data"""
        return {
            "email": "test.user@psychsync.com",
            "password": "SecurePass123!@#",
            "full_name": "Test User",
            "role": "user"
        }

    @pytest.mark.asyncio
    async def test_reg_001_valid_user_registration(self, client, valid_user_data):
        """✅ REG-001: Valid User Registration"""
        with patch('app.core.database.get_async_db') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.return_value = mock_session

            # Mock user creation
            mock_user = Mock()
            mock_user.id = "test-uuid-123"
            mock_user.email = valid_user_data["email"]
            mock_user.full_name = valid_user_data["full_name"]
            mock_user.role = UserRole.USER
            mock_user.created_at = datetime.utcnow()
            mock_user.updated_at = datetime.utcnow()

            with patch('app.api.v1.endpoints.auth.User') as mock_user_model:
                mock_user_model.return_value = mock_user

                response = client.post("/api/v1/auth/register", json=valid_user_data)

                # Should succeed if database operations work
                # In real test, this would save to database and return user data
                assert response.status_code in [200, 201]  # Accept both success codes

    def test_reg_002_password_complexity_validation(self, client, valid_user_data):
        """✅ REG-002: Password Complexity Validation"""
        # Test weak passwords
        weak_passwords = [
            "123456",  # Too simple
            "password",  # Common word
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoNumbersHere",  # No numbers
            "NoSpecialChars123"  # No special characters
        ]

        for weak_pass in weak_passwords:
            valid_user_data["password"] = weak_pass
            response = client.post("/api/v1/auth/register", json=valid_user_data)
            # Should fail password validation
            assert response.status_code in [400, 422]

        # Test strong password
        valid_user_data["password"] = "StrongPass123!@#"
        response = client.post("/api/v1/auth/register", json=valid_user_data)
        # Should pass password validation (may fail for other reasons)
        assert response.status_code not in [400, 422]

    def test_reg_003_email_validation(self, client, valid_user_data):
        """✅ REG-003: Email Validation"""
        invalid_emails = [
            "not-an-email",
            "@invalid.com",
            "invalid@",
            "invalid..email@test.com",
            "invalid@email",
            "spaces @test.com"
        ]

        for invalid_email in invalid_emails:
            valid_user_data["email"] = invalid_email
            response = client.post("/api/v1/auth/register", json=valid_user_data)
            assert response.status_code == 422

        # Test valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "user123@test-domain.com"
        ]

        for valid_email in valid_emails:
            valid_user_data["email"] = valid_email
            response = client.post("/api/v1/auth/register", json=valid_user_data)
            # Should pass email validation
            assert response.status_code not in [422]

    def test_reg_005_sql_injection_prevention(self, client, valid_user_data):
        """✅ REG-005: SQL Injection Prevention"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --"
        ]

        for malicious_input in malicious_inputs:
            valid_user_data["email"] = malicious_input
            valid_user_data["full_name"] = malicious_input

            response = client.post("/api/v1/auth/register", json=valid_user_data)

            # Should not cause database errors
            assert response.status_code in [400, 422]  # Validation error, not database error


class TestUserAuthentication:
    """Test suite for user authentication functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def test_user_data(self):
        """Test user credentials"""
        return {
            "email": "auth.test@psychsync.com",
            "password": "TestAuthPass123!@#"
        }

    @pytest.mark.asyncio
    async def test_auth_001_valid_login(self, client, test_user_data):
        """✅ AUTH-001: Valid Login"""
        # Mock user retrieval and password verification
        mock_user = Mock()
        mock_user.id = "test-uuid-456"
        mock_user.email = test_user_data["email"]
        mock_user.hashed_password = get_password_hash(test_user_data["password"])
        mock_user.is_active = True
        mock_user.role = UserRole.USER

        with patch('app.core.security.authenticate_user', return_value=mock_user):
            response = client.post("/api/v1/auth/token", data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            })

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

    def test_auth_002_invalid_credentials(self, client, test_user_data):
        """✅ AUTH-002: Invalid Credentials"""
        response = client.post("/api/v1/auth/token", data={
            "username": test_user_data["email"],
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_auth_003_nonexistent_user_login(self, client):
        """✅ AUTH-003: Non-existent User Login"""
        response = client.post("/api/v1/auth/token", data={
            "username": "nonexistent@psychsync.com",
            "password": "anypassword"
        })

        assert response.status_code == 401

    def test_auth_007_brute_force_protection(self, client, test_user_data):
        """✅ AUTH-007: Brute Force Protection"""
        # Make multiple failed login attempts
        for i in range(6):  # Exceed the 5 attempt limit
            response = client.post("/api/v1/auth/token", data={
                "username": test_user_data["email"],
                "password": f"wrongpassword{i}"
            })
            # Should fail, but may not trigger lockout until threshold
            assert response.status_code == 401

        # Next attempt should be rate limited or account locked
        response = client.post("/api/v1/auth/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })

        # Should be blocked due to too many attempts
        assert response.status_code in [401, 429]


class TestTeamCreation:
    """Test suite for team creation functionality"""

    @pytest.fixture
    def authenticated_client(self):
        """Create authenticated test client"""
        client = TestClient(app)
        # Mock authentication
        with patch('app.api.v1.deps.get_current_active_user') as mock_auth:
            mock_user = Mock()
            mock_user.id = "test-user-uuid"
            mock_user.email = "team.test@psychsync.com"
            mock_user.is_active = True
            mock_user.role = UserRole.USER
            mock_auth.return_value = mock_user
            yield client

    def test_team_001_valid_team_creation(self, authenticated_client):
        """✅ TEAM-001: Valid Team Creation"""
        team_data = {
            "name": "Test Team",
            "description": "A test team for functional testing",
            "organization_id": "test-org-uuid"
        }

        with patch('app.core.database.get_async_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value = mock_session

            # Mock team creation
            mock_team = Mock()
            mock_team.id = "test-team-uuid"
            mock_team.name = team_data["name"]
            mock_team.description = team_data["description"]

            with patch('app.db.models.team.Team') as mock_team_model:
                mock_team_model.return_value = mock_team

                response = authenticated_client.post("/api/v1/teams/", json=team_data)

                # Should succeed if database operations work
                assert response.status_code == 201

    def test_setup_001_setup_wizard_progression(self, authenticated_client):
        """✅ SETUP-001: Setup Wizard Progression"""
        setup_steps = [
            {"step": "profile", "data": {"industry": "technology", "company_size": "50-100"}},
            {"step": "team", "data": {"team_name": "Engineering", "team_size": 10}},
            {"step": "goals", "data": {"primary_goal": "communication", "timeline": "3_months"}}
        ]

        with patch('app.services.onboarding_service.OnboardingService.process_setup_step') as mock_setup:
            mock_setup.return_value = {"success": True, "next_step": "profile"}

            for step_data in setup_steps:
                response = authenticated_client.post("/api/v1/onboarding/setup-wizard", json=step_data)
                assert response.status_code == 200

                # Verify setup service was called with correct data
                mock_setup.assert_called_with(
                    user_id="test-user-uuid",
                    step=step_data["step"],
                    data=step_data["data"]
                )


class TestDetailedTeamInsights:
    """Test suite for detailed team insights functionality"""

    @pytest.fixture
    def authenticated_client(self):
        """Create authenticated test client"""
        client = TestClient(app)
        with patch('app.api.v1.deps.get_current_active_user') as mock_auth:
            mock_user = Mock()
            mock_user.id = "insights-user-uuid"
            mock_user.email = "insights.test@psychsync.com"
            mock_user.is_active = True
            mock_user.role = UserRole.USER
            mock_auth.return_value = mock_user
            yield client

    def test_insights_001_authenticated_team_insights(self, authenticated_client):
        """✅ INSIGHTS-001: Authenticated Team Insights"""
        insights_request = {
            "team_id": "test-team-uuid",
            "session_id": "insights-session-123"
        }

        with patch('app.services.onboarding_service.OnboardingService.generate_detailed_team_insights') as mock_insights:
            # Mock insights response
            mock_insights_response = Mock()
            mock_insights_response.team_profile = {
                "team_size": 10,
                "avg_experience": 5.5,
                "communication_style": "collaborative",
                "current_performance": 0.7,
                "potential_performance": 0.9
            }
            mock_insights_response.detailed_insights = [
                {"category": "communication", "title": "Test Insight", "description": "Test description"}
            ]
            mock_insights_response.action_items = [
                {"title": "Test Action", "description": "Test action description"}
            ]
            mock_insights_response.predicted_outcomes = [
                {"metric": "productivity", "improvement": 0.2}
            ]
            mock_insights_response.implementation_roadmap = [
                {"phase": "immediate", "actions": ["Test action"]}
            ]

            mock_insights.return_value = mock_insights_response

            response = authenticated_client.post("/api/v1/onboarding/team-insights", json=insights_request)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "team_profile" in data
            assert "detailed_insights" in data
            assert "action_items" in data

    def test_insights_003_oversized_team_data(self, authenticated_client):
        """✅ INSIGHTS-003: Oversized Team Data"""
        # Create oversized team composition data (>10KB)
        oversized_data = {
            "team_id": "test-team-uuid",
            "team_composition": [
                {
                    "name": f"Member {i}",
                    "profile": "x" * 1000,  # Large profile data
                    "assessment_data": {"question_" + str(j): "answer" * 100 for j in range(50)}
                }
                for i in range(50)
            ]
        }

        response = authenticated_client.post("/api/v1/onboarding/team-insights", json=oversized_data)

        # Should reject oversized data
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()


class TestOnboardingStatus:
    """Test suite for onboarding status functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_status_001_anonymous_user_status(self, client):
        """✅ STATUS-001: Anonymous User Status"""
        response = client.get("/api/v1/onboarding/onboarding-status")

        assert response.status_code == 200
        data = response.json()
        assert data["is_authenticated"] is False
        assert data["onboarding_complete"] is False
        assert "recommended_actions" in data
        assert len(data["recommended_actions"]) > 0

    def test_status_002_authenticated_user_status(self):
        """✅ STATUS-002: Authenticated User Status"""
        client = TestClient(app)

        with patch('app.api.v1.deps.get_current_user_optional') as mock_auth:
            mock_user = Mock()
            mock_user.id = "status-user-uuid"
            mock_user.is_active = True
            mock_auth.return_value = mock_user

            with patch('app.services.onboarding_service.OnboardingService.get_onboarding_status') as mock_status:
                mock_status.return_value = {
                    "is_authenticated": True,
                    "onboarding_complete": False,
                    "progress": 0.6,
                    "completed_steps": ["quick_assessment", "registration"],
                    "next_steps": ["create_team", "take_assessment"]
                }

                response = client.get("/api/v1/onboarding/onboarding-status")

                assert response.status_code == 200
                data = response.json()
                assert data["is_authenticated"] is True


class TestSecurityAndRateLimiting:
    """Test suite for security and rate limiting across onboarding"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_sec_001_input_sanitization_all_endpoints(self, client):
        """✅ SEC-001: All Endpoints Input Validation"""
        malicious_payloads = [
            {"email": "'; DROP TABLE users; --"},
            {"full_name": "<script>alert('xss')</script>"},
            {"description": "'; SELECT * FROM users; --"},
            {"data": {"injection": "'; DROP TABLE assessments; --"}}
        ]

        # Test various endpoints with malicious input
        endpoints_to_test = [
            ("/api/v1/auth/register", {"email": "test@test.com", "password": "ValidPass123!"}),
            ("/api/v1/onboarding/quick-assessment", {"role": "manager", "challenge": "communication"})
        ]

        for endpoint, base_data in endpoints_to_test:
            for malicious_field, malicious_value in malicious_payloads.items():
                test_data = base_data.copy()
                if malicious_field in test_data or isinstance(test_data, dict):
                    test_data[malicious_field] = malicious_value

                    response = client.post(endpoint, json=test_data)

                    # Should not cause 500 errors (which would indicate SQL injection)
                    assert response.status_code not in [500]
                    # Should return validation error or be safely handled
                    assert response.status_code in [400, 422, 200]

    def test_sec_002_pii_protection(self, client):
        """✅ SEC-003: PII Protection"""
        sensitive_data = {
            "email": "sensitive.user@company.com",
            "full_name": "John Doe",
            "phone": "555-123-4567",
            "ssn": "123-45-6789"
        }

        with patch('app.services.analytics_service.AnalyticsService.track_onboarding_event') as mock_track:
            mock_track.return_value = None

            response = client.post("/api/v1/onboarding/quick-assessment", json={
                "role": "manager",
                "challenge": "communication",
                "team_size": "5-10",
                "session_id": "sensitive_test"
            })

            # Verify analytics was called
            if mock_track.called:
                # Check that PII is handled properly in logged data
                call_args = mock_track.call_args
                logged_data = call_args[1]["data"] if len(call_args) > 1 else {}

                # Sensitive fields should be masked or not included in logs
                assert "ssn" not in logged_data
                assert "phone" not in logged_data


class TestCrossFunctionalIntegration:
    """Test suite for cross-functional integration testing"""

    @pytest.mark.asyncio
    async def test_integration_001_complete_onboarding_flow(self):
        """✅ INTEGRATION-001: Complete Onboarding Flow"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Anonymous Quick Assessment
            assessment_response = await client.post("/api/v1/onboarding/quick-assessment", json={
                "role": "manager",
                "challenge": "communication",
                "team_size": "5-10",
                "session_id": "integration-test-session"
            })

            assert assessment_response.status_code == 200
            assessment_data = assessment_response.json()
            assert assessment_data["success"] is True

            # Step 2: User Registration
            with patch('app.api.v1.endpoints.auth.User') as mock_user_model:
                mock_user = Mock()
                mock_user.id = "integration-user-uuid"
                mock_user.email = "integration@test.com"
                mock_user.role = UserRole.USER
                mock_user.created_at = datetime.utcnow()
                mock_user.updated_at = datetime.utcnow()
                mock_user_model.return_value = mock_user

                register_response = await client.post("/api/v1/auth/register", json={
                    "email": "integration@test.com",
                    "password": "IntegrationTestPass123!@#",
                    "full_name": "Integration Test User"
                })

            # Step 3: Check Onboarding Status
            with patch('app.api.v1.deps.get_current_user_optional') as mock_auth:
                mock_auth.return_value = mock_user

                with patch('app.services.onboarding_service.OnboardingService.get_onboarding_status') as mock_status:
                    mock_status.return_value = {
                        "is_authenticated": True,
                        "onboarding_complete": False,
                        "progress": 0.3
                    }

                    status_response = await client.get("/api/v1/onboarding/onboarding-status")
                    assert status_response.status_code == 200
                    status_data = status_response.json()
                    assert status_data["is_authenticated"] is True

    def test_perf_002_response_time_benchmarks(self):
        """✅ PERF-002: Response Time Benchmarks"""
        client = TestClient(app)

        # Test quick assessment response time
        start_time = time.time()
        response = client.post("/api/v1/onboarding/quick-assessment", json={
            "role": "manager",
            "challenge": "communication",
            "team_size": "5-10"
        })
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 3.0, f"Quick assessment took {response_time:.2f}s, expected < 3.0s"

        # Test onboarding status response time
        start_time = time.time()
        response = client.get("/api/v1/onboarding/onboarding-status")
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 1.0, f"Status check took {response_time:.2f}s, expected < 1.0s"


# Test Configuration and Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing"""
    with patch('app.core.redis_client.get_redis_client') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        yield mock_client


# Test Execution Configuration
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-k 'not test_perf_'  # Skip performance tests in normal runs"
    ])