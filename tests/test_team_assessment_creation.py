"""
Team Assessment Creation Test Suite
Comprehensive test cases for creating new team assessments in PsychSync SaaS

Test Coverage:
- Authentication & Authorization
- Data Validation & Business Logic
- Error Handling & Edge Cases
- Database Operations & Constraints
- Performance & Security

Author: QA Team
Version: 1.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.main import app
from app.core.database import get_async_db, AsyncSessionLocal
from app.core.security import create_access_token, get_password_hash
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.db.models import TeamMember
from app.db.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssignmentCreate


class TeamAssessmentCreationTestCase:
    """
    Comprehensive test suite for team assessment creation functionality
    """

    @pytest.fixture
    async def client(self) -> TestClient:
        """FastAPI test client with dependency injection override"""
        from fastapi.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """Database session for test setup and teardown"""
        async for session in get_async_session():
            yield session
            await session.close()

    @pytest.fixture
    async def test_organization(self, db_session: AsyncSession) -> Organization:
        """Create test organization for team assessment tests"""
        org = Organization(
            name="Test Organization",
            description="Test organization for team assessments",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        return org

    @pytest.fixture
    async def test_team(self, db_session: AsyncSession, test_organization: Organization) -> Team:
        """Create test team for assessment tests"""
        team = Team(
            name="Test Team",
            description="Test team for assessments",
            organization_id=test_organization.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(team)
        await db_session.commit()
        await db_session.refresh(team)
        return team

    @pytest.fixture
    async def admin_user(self, db_session: AsyncSession, test_organization: Organization) -> User:
        """Create admin user with organization access"""
        user = User(
            email="admin@test.com",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123456"),
            is_active=True,
            is_verified=True,
            is_superuser=True,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        await db_session.commit()

        # Add as organization member with admin role
        org_member = TeamMember(
            user_id=user.id,
            organization_id=test_organization.id,
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(org_member)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def team_lead_user(self, db_session: AsyncSession, test_organization: Organization) -> User:
        """Create team lead user"""
        user = User(
            email="teamlead@test.com",
            full_name="Team Lead User",
            hashed_password=get_password_hash("lead123456"),
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        await db_session.commit()

        # Add as organization member with team lead role
        org_member = TeamMember(
            user_id=user.id,
            organization_id=test_organization.id,
            role="team_lead",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(org_member)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def regular_user(self, db_session: AsyncSession, test_organization: Organization) -> User:
        """Create regular user with limited permissions"""
        user = User(
            email="user@test.com",
            full_name="Regular User",
            hashed_password=get_password_hash("user123456"),
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        await db_session.commit()

        # Add as organization member with user role
        org_member = TeamMember(
            user_id=user.id,
            organization_id=test_organization.id,
            role="user",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(org_member)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def auth_headers_admin(self, admin_user: User) -> Dict[str, str]:
        """Authentication headers for admin user"""
        token = create_access_token(subject=admin_user.email)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def auth_headers_team_lead(self, team_lead_user: User) -> Dict[str, str]:
        """Authentication headers for team lead user"""
        token = create_access_token(subject=team_lead_user.email)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def auth_headers_regular(self, regular_user: User) -> Dict[str, str]:
        """Authentication headers for regular user"""
        token = create_access_token(subject=regular_user.email)
        return {"Authorization": f"Bearer {token}"}


class TestHappyPaths(TeamAssessmentCreationTestCase):
    """
    Test successful team assessment creation scenarios
    """

    @pytest.mark.asyncio
    async def test_create_team_assessment_as_admin_success(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test successful team assessment creation by admin user"""

        assessment_data = {
            "title": "Team Performance Assessment 2024",
            "description": "Annual team performance and psychological assessment",
            "assessment_type": "team_performance",
            "category": "performance",
            "is_active": True,
            "instructions": "Please complete this assessment honestly and thoroughly.",
            "estimated_duration_minutes": 45,
            "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "max_attempts": 3,
            "is_anonymous": False,
            "requires_proctoring": False,
            "configuration": {
                "scoring_algorithm": "weighted_average",
                "passing_score": 70,
                "show_results_immediately": True
            }
        }

        response = client.post(
            f"/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 201
        response_data = response.json()

        # Verify assessment creation response
        assert response_data["success"] is True
        assert "data" in response_data
        assert response_data["data"]["title"] == assessment_data["title"]
        assert response_data["data"]["assessment_type"] == assessment_data["assessment_type"]
        assert response_data["data"]["is_active"] is True
        assert "id" in response_data["data"]

    @pytest.mark.asyncio
    async def test_create_team_assessment_with_questions_success(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test successful team assessment creation with questions"""

        assessment_data = {
            "title": "Team Skills Assessment",
            "description": "Comprehensive team skills and capabilities assessment",
            "assessment_type": "team_skills",
            "category": "skills",
            "is_active": True,
            "instructions": "Complete all sections honestly.",
            "estimated_duration_minutes": 30,
            "deadline": (datetime.utcnow() + timedelta(days=60)).isoformat(),
            "max_attempts": 2,
            "sections": [
                {
                    "title": "Technical Skills",
                    "description": "Assess technical competencies",
                    "order": 1,
                    "is_required": True,
                    "questions": [
                        {
                            "question_text": "Rate your proficiency in database management",
                            "question_type": "rating",
                            "options": ["1 (Beginner)", "2 (Novice)", "3 (Intermediate)", "4 (Advanced)", "5 (Expert)"],
                            "required": True,
                            "order": 1,
                            "weight": 1.0
                        },
                        {
                            "question_text": "Describe your experience with API development",
                            "question_type": "text",
                            "required": True,
                            "order": 2,
                            "weight": 1.5,
                            "max_length": 500
                        }
                    ]
                },
                {
                    "title": "Soft Skills",
                    "description": "Assess communication and collaboration skills",
                    "order": 2,
                    "is_required": True,
                    "questions": [
                        {
                            "question_text": "How do you handle conflicts in team settings?",
                            "question_type": "essay",
                            "required": True,
                            "order": 1,
                            "weight": 2.0,
                            "min_length": 100,
                            "max_length": 1000
                        }
                    ]
                }
            ]
        }

        response = client.post(
            f"/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 201
        response_data = response.json()

        # Verify assessment with questions
        assert response_data["success"] is True
        assert response_data["data"]["title"] == assessment_data["title"]
        assert len(response_data["data"]["sections"]) == 2
        assert len(response_data["data"]["sections"][0]["questions"]) == 2

    @pytest.mark.asyncio
    async def test_assign_assessment_to_team_success(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test successful assessment assignment to team"""

        # First create an assessment
        assessment_data = {
            "title": "Team Assessment Assignment Test",
            "description": "Test assignment functionality",
            "assessment_type": "team_assignment",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 15
        }

        create_response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert create_response.status_code == 201
        assessment_id = create_response.json()["data"]["id"]

        # Assign assessment to team
        assignment_data = {
            "team_id": str(test_team.id),
            "assigned_by": str(uuid4()),  # Would be actual user ID in real scenario
            "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "notification_message": "Please complete this assessment by the due date.",
            "reminder_frequency_days": 3,
            "is_mandatory": True
        }

        assign_response = client.post(
            f"/api/v1/assessments/{assessment_id}/assignments",
            json=assignment_data,
            headers=auth_headers_admin
        )

        assert assign_response.status_code == 201
        assign_data = assign_response.json()
        assert assign_data["success"] is True
        assert assign_data["data"]["team_id"] == str(test_team.id)
        assert assign_data["data"]["is_mandatory"] is True


class TestAuthorizationAndPermissions(TeamAssessmentCreationTestCase):
    """
    Test authorization and permission scenarios
    """

    @pytest.mark.asyncio
    async def test_create_assessment_team_lead_success(
        self, client: TestClient, test_team: Team, auth_headers_team_lead: Dict[str, str]
    ):
        """Test team lead can create assessments for their team"""

        assessment_data = {
            "title": "Team Lead Assessment",
            "description": "Assessment created by team lead",
            "assessment_type": "team_lead_review",
            "category": "review",
            "is_active": True,
            "instructions": "Team assessment instructions",
            "estimated_duration_minutes": 25
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_team_lead
        )

        # Team lead should be able to create assessments
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_assessment(
        self, client: TestClient, test_team: Team, auth_headers_regular: Dict[str, str]
    ):
        """Test regular user cannot create team assessments"""

        assessment_data = {
            "title": "Unauthorized Assessment",
            "description": "This should fail",
            "assessment_type": "unauthorized",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 10
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_regular
        )

        # Regular user should be forbidden from creating assessments
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_create_assessment(
        self, client: TestClient, test_team: Team
    ):
        """Test unauthenticated user cannot create assessments"""

        assessment_data = {
            "title": "No Auth Assessment",
            "description": "This should fail without auth",
            "assessment_type": "no_auth",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 5
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data
        )

        # Should require authentication
        assert response.status_code == 401


class TestDataValidationAndBusinessRules(TeamAssessmentCreationTestCase):
    """
    Test data validation and business rule enforcement
    """

    @pytest.mark.asyncio
    async def test_empty_title_validation_error(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test validation error for empty title"""

        assessment_data = {
            "title": "",  # Empty title should fail validation
            "description": "Valid description",
            "assessment_type": "validation_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 10
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data

    @pytest.mark.asyncio
    async def test_invalid_assessment_type_validation_error(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test validation error for invalid assessment type"""

        assessment_data = {
            "title": "Invalid Type Assessment",
            "description": "Assessment with invalid type",
            "assessment_type": "invalid_type",  # Invalid type
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 10
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_past_deadline_validation_error(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test validation error for past deadline"""

        assessment_data = {
            "title": "Past Deadline Assessment",
            "description": "Assessment with invalid deadline",
            "assessment_type": "deadline_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 10,
            "deadline": (datetime.utcnow() - timedelta(days=1)).isoformat()  # Past deadline
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_duration_validation_error(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test validation error for negative duration"""

        assessment_data = {
            "title": "Negative Duration Assessment",
            "description": "Assessment with invalid duration",
            "assessment_type": "duration_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": -10  # Negative duration
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 422


class TestErrorHandlingAndEdgeCases(TeamAssessmentCreationTestCase):
    """
    Test error handling and edge cases
    """

    @pytest.mark.asyncio
    async def test_duplicate_assessment_name_handling(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test handling of duplicate assessment names within same team"""

        assessment_data = {
            "title": "Duplicate Test Assessment",
            "description": "First assessment",
            "assessment_type": "duplicate_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 15
        }

        # Create first assessment
        response1 = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )
        assert response1.status_code == 201

        # Try to create second assessment with same title
        response2 = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        # Should either succeed (if duplicates allowed) or return appropriate error
        assert response2.status_code in [201, 409, 422]

    @pytest.mark.asyncio
    async def test_assessment_creation_with_missing_optional_fields(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test assessment creation with only required fields"""

        # Minimal required assessment data
        minimal_data = {
            "title": "Minimal Assessment",
            "description": "Minimal description",
            "assessment_type": "minimal_test",
            "category": "test"
        }

        response = client.post(
            "/api/v1/assessments/",
            json=minimal_data,
            headers=auth_headers_admin
        )

        # Should succeed with default values for optional fields
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["data"]["title"] == minimal_data["title"]
        # Check that default values were applied
        assert response_data["data"]["is_active"] is True  # Default should be True

    @pytest.mark.asyncio
    async def test_very_long_description_handling(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test handling of very long descriptions"""

        very_long_description = "A" * 5000  # 5000 character description

        assessment_data = {
            "title": "Long Description Test",
            "description": very_long_description,
            "assessment_type": "length_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 10
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        # Should either succeed or fail due to length limits
        assert response.status_code in [201, 422]


class TestPerformanceAndSecurity(TeamAssessmentCreationTestCase):
    """
    Test performance and security aspects
    """

    @pytest.mark.asyncio
    async def test_assessment_creation_performance(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test assessment creation performance"""

        import time

        assessment_data = {
            "title": "Performance Test Assessment",
            "description": "Performance test description",
            "assessment_type": "performance_test",
            "category": "test",
            "is_active": True,
            "instructions": "Performance test instructions",
            "estimated_duration_minutes": 10
        }

        start_time = time.time()
        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )
        end_time = time.time()

        # Should complete within reasonable time (2 seconds)
        assert response.status_code == 201
        assert (end_time - start_time) < 2.0

    @pytest.mark.asyncio
    async def test_sql_injection_protection(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test SQL injection protection in assessment fields"""

        malicious_description = "'; DROP TABLE users; --"

        assessment_data = {
            "title": "SQL Injection Test",
            "description": malicious_description,
            "assessment_type": "security_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 10
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        # Should handle the input safely (either succeed or validation error, but not crash)
        assert response.status_code in [201, 422]

        # Verify database still exists by checking health
        health_response = client.get("/health")
        assert health_response.status_code == 200

    @pytest.mark.asyncio
    async def test_xss_protection_in_assessment_fields(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test XSS protection in assessment fields"""

        xss_payload = '<script>alert("XSS")</script>'

        assessment_data = {
            "title": "XSS Protection Test",
            "description": xss_payload,
            "assessment_type": "security_test",
            "category": "test",
            "is_active": True,
            "instructions": xss_payload,
            "estimated_duration_minutes": 10
        }

        response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )

        assert response.status_code == 201
        response_data = response.json()

        # Check that XSS payload is sanitized or properly escaped
        stored_description = response_data["data"]["description"]
        assert "<script>" not in stored_description.lower() or "alert(" not in stored_description.lower()


class TestDatabaseOperations(TeamAssessmentCreationTestCase):
    """
    Test database operations and constraints
    """

    @pytest.mark.asyncio
    async def test_assessment_database_persistence(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str],
        db_session: AsyncSession
    ):
        """Test that assessments are properly persisted in database"""

        assessment_data = {
            "title": "Database Persistence Test",
            "description": "Test database persistence",
            "assessment_type": "persistence_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 15
        }

        # Create assessment via API
        create_response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )
        assert create_response.status_code == 201

        assessment_id = create_response.json()["data"]["id"]

        # Verify assessment exists in database
        result = await db_session.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        )
        db_assessment = result.scalar_one_or_none()

        assert db_assessment is not None
        assert db_assessment.title == assessment_data["title"]
        assert db_assessment.description == assessment_data["description"]
        assert db_assessment.assessment_type == assessment_data["assessment_type"]

    @pytest.mark.asyncio
    async def test_assessment_cascade_operations(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str],
        db_session: AsyncSession
    ):
        """Test cascade operations when assessment is deleted"""

        # First create an assessment with sections
        assessment_data = {
            "title": "Cascade Test Assessment",
            "description": "Test cascade operations",
            "assessment_type": "cascade_test",
            "category": "test",
            "is_active": True,
            "instructions": "Test instructions",
            "estimated_duration_minutes": 20,
            "sections": [
                {
                    "title": "Test Section",
                    "description": "Test section for cascade",
                    "order": 1,
                    "is_required": True,
                    "questions": [
                        {
                            "question_text": "Test question",
                            "question_type": "text",
                            "required": True,
                            "order": 1,
                            "weight": 1.0
                        }
                    ]
                }
            ]
        }

        create_response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )
        assert create_response.status_code == 201

        assessment_id = create_response.json()["data"]["id"]

        # Delete assessment
        delete_response = client.delete(
            f"/api/v1/assessments/{assessment_id}",
            headers=auth_headers_admin
        )
        assert delete_response.status_code == 204

        # Verify assessment is deleted from database
        result = await db_session.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        )
        deleted_assessment = result.scalar_one_or_none()

        assert deleted_assessment is None or deleted_assessment.deleted_at is not None


# Integration Test Class
class TestTeamAssessmentIntegration(TeamAssessmentCreationTestCase):
    """
    Integration tests for complete team assessment workflow
    """

    @pytest.mark.asyncio
    async def test_complete_team_assessment_workflow(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str],
        db_session: AsyncSession
    ):
        """Test complete workflow: create assessment → assign → simulate responses"""

        # 1. Create comprehensive team assessment
        assessment_data = {
            "title": "Annual Team Performance Review 2024",
            "description": "Comprehensive annual assessment covering skills, collaboration, and goals",
            "assessment_type": "annual_review",
            "category": "performance",
            "is_active": True,
            "instructions": "Please complete this assessment honestly and thoughtfully. Your feedback helps us improve team dynamics and individual development plans.",
            "estimated_duration_minutes": 60,
            "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "max_attempts": 2,
            "is_anonymous": False,
            "requires_proctoring": False,
            "configuration": {
                "scoring_algorithm": "weighted_average",
                "passing_score": 75,
                "show_results_immediately": True,
                "allow_retake_after_days": 7
            },
            "sections": [
                {
                    "title": "Technical Competencies",
                    "description": "Evaluate technical skills and capabilities",
                    "order": 1,
                    "is_required": True,
                    "weight": 0.4,
                    "questions": [
                        {
                            "question_text": "How would you rate your proficiency in your primary technical skills?",
                            "question_type": "rating",
                            "options": ["1 - Beginner", "2 - Developing", "3 - Competent", "4 - Advanced", "5 - Expert"],
                            "required": True,
                            "order": 1,
                            "weight": 1.0
                        },
                        {
                            "question_text": "What technical skills would you like to develop further?",
                            "question_type": "text",
                            "required": True,
                            "order": 2,
                            "weight": 1.0,
                            "max_length": 300
                        }
                    ]
                },
                {
                    "title": "Team Collaboration",
                    "description": "Assess teamwork and communication effectiveness",
                    "order": 2,
                    "is_required": True,
                    "weight": 0.3,
                    "questions": [
                        {
                            "question_text": "How effectively do you communicate with team members?",
                            "question_type": "rating",
                            "options": ["1 - Poorly", "2 - Sometimes", "3 - Usually", "4 - Well", "5 - Excellently"],
                            "required": True,
                            "order": 1,
                            "weight": 1.0
                        },
                        {
                            "question_text": "Describe a recent successful collaboration experience.",
                            "question_type": "essay",
                            "required": True,
                            "order": 2,
                            "weight": 2.0,
                            "min_length": 100,
                            "max_length": 800
                        }
                    ]
                },
                {
                    "title": "Goals and Development",
                    "description": "Set personal and professional development goals",
                    "order": 3,
                    "is_required": True,
                    "weight": 0.3,
                    "questions": [
                        {
                            "question_text": "What are your top 3 professional goals for the next year?",
                            "question_type": "text",
                            "required": True,
                            "order": 1,
                            "weight": 1.5,
                            "max_length": 500
                        },
                        {
                            "question_text": "What support do you need to achieve these goals?",
                            "question_type": "text",
                            "required": True,
                            "order": 2,
                            "weight": 1.0,
                            "max_length": 300
                        }
                    ]
                }
            ]
        }

        # Create assessment
        create_response = client.post(
            "/api/v1/assessments/",
            json=assessment_data,
            headers=auth_headers_admin
        )
        assert create_response.status_code == 201
        assessment_id = create_response.json()["data"]["id"]

        # 2. Assign assessment to team
        assignment_data = {
            "team_id": str(test_team.id),
            "assigned_by": str(uuid4()),
            "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "notification_message": "Please complete your annual performance assessment by the deadline.",
            "reminder_frequency_days": 2,
            "is_mandatory": True,
            "allow_late_submission": True
        }

        assign_response = client.post(
            f"/api/v1/assessments/{assessment_id}/assignments",
            json=assignment_data,
            headers=auth_headers_admin
        )
        assert assign_response.status_code == 201

        # 3. Verify assessment details
        get_response = client.get(
            f"/api/v1/assessments/{assessment_id}",
            headers=auth_headers_admin
        )
        assert get_response.status_code == 200
        assessment_details = get_response.json()

        # Verify assessment structure
        assert assessment_details["data"]["title"] == assessment_data["title"]
        assert len(assessment_details["data"]["sections"]) == 3
        total_questions = sum(len(section["questions"]) for section in assessment_details["data"]["sections"])
        assert total_questions == 6

        # 4. Test assignment retrieval
        assignments_response = client.get(
            f"/api/v1/assessments/{assessment_id}/assignments",
            headers=auth_headers_admin
        )
        assert assignments_response.status_code == 200

        # 5. Verify database state
        result = await db_session.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        )
        db_assessment = result.scalar_one_or_none()

        assert db_assessment is not None
        assert db_assessment.title == assessment_data["title"]
        assert db_assessment.assessment_type == assessment_data["assessment_type"]
        assert db_assessment.is_active is True


# Test Data Factory
class AssessmentTestDataFactory:
    """Factory for creating test assessment data"""

    @staticmethod
    def create_valid_assessment_data(**overrides) -> Dict[str, Any]:
        """Create valid assessment data with optional overrides"""
        base_data = {
            "title": "Test Assessment",
            "description": "Test assessment description",
            "assessment_type": "test_type",
            "category": "test",
            "is_active": True,
            "instructions": "Please complete this assessment.",
            "estimated_duration_minutes": 30,
            "max_attempts": 3,
            "is_anonymous": False,
            "requires_proctoring": False,
            "configuration": {
                "scoring_algorithm": "weighted_average",
                "passing_score": 70,
                "show_results_immediately": True
            }
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_invalid_assessment_data() -> Dict[str, Any]:
        """Create invalid assessment data for testing validation"""
        return {
            "title": "",  # Empty title
            "description": "Invalid assessment",
            "assessment_type": "invalid_type",
            "category": "",  # Empty category
            "is_active": True,
            "instructions": "Invalid instructions",
            "estimated_duration_minutes": -10,  # Negative duration
            "max_attempts": 0,  # Invalid attempts
            "deadline": "invalid_date_format"  # Invalid date
        }


# Performance Benchmark Tests
class TestTeamAssessmentPerformanceBenchmarks(TeamAssessmentCreationTestCase):
    """
    Performance benchmark tests for team assessment operations
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_bulk_assessment_creation_performance(
        self, client: TestClient, test_team: Team, auth_headers_admin: Dict[str, str]
    ):
        """Test performance of creating multiple assessments"""

        import time
        import concurrent.futures

        def create_assessment(index: int) -> Dict[str, Any]:
            assessment_data = AssessmentTestDataFactory.create_valid_assessment_data(
                title=f"Bulk Assessment {index}",
                description=f"Assessment number {index} for performance testing"
            )

            start_time = time.time()
            response = client.post(
                "/api/v1/assessments/",
                json=assessment_data,
                headers=auth_headers_admin
            )
            end_time = time.time()

            return {
                "index": index,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 201
            }

        # Create 10 assessments concurrently
        num_assessments = 10
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(create_assessment, i)
                for i in range(num_assessments)
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # Performance assertions
        successful_assessments = sum(1 for result in results if result["success"])
        assert successful_assessments >= num_assessments * 0.9  # 90% success rate
        assert total_time < 30.0  # Should complete within 30 seconds
        assert len(results) == num_assessments

        # Log performance metrics
        avg_response_time = sum(result["response_time"] for result in results) / len(results)
        print(f"Created {successful_assessments}/{num_assessments} assessments")
        print(f"Total time: {total_time:.2f}s, Average response time: {avg_response_time:.2f}s")


# Test Execution Configuration
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
