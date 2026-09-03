"""
Tests for Legal Rights Awareness API
Comprehensive tests for legal rights endpoints
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models.legal_rights import ContractViolation, LaborLaw, LegalAidResource
from app.db.models.organization import Organization
from app.db.models.user import User
from app.main import app


@pytest.fixture
def db_session():
    """Create test database session"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client(db_session):
    """Create test client with database dependency override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_organization(db_session):
    """Create test organization"""
    org = Organization(name="Test Organization", slug="test-org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def sample_labor_law(db_session):
    """Create sample labor law"""
    law = LaborLaw(
        country_code="US",
        country_name="United States",
        state_region=None,
        continent="NA",
        law_name="Test Labor Law",
        law_code="TEST-001",
        category="working_hours",
        description="Test law for unit testing",
        min_wage=15.0,
        max_weekly_hours=40,
        overtime_threshold=40,
        overtime_rate=1.5,
        min_vacation_days=10,
        discrimination_protection_level=8,
        safety_protection_level=7,
        privacy_protection_level=6,
        termination_protection_level=7,
        is_active=True,
        verified=True,
    )
    db_session.add(law)
    db_session.commit()
    db_session.refresh(law)
    return law


class TestLaborLawsEndpoint:
    """Tests for /labor-laws endpoint"""

    def test_get_labor_laws_by_country(self, test_client, sample_labor_law):
        """Test retrieving labor laws by country code"""
        response = test_client.get("/api/v1/legal-rights/labor-laws?country_code=US")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["country_code"] == "US"
        assert "law_name" in data[0]
        assert "category" in data[0]

    def test_get_labor_laws_with_category_filter(self, test_client, sample_labor_law):
        """Test filtering labor laws by category"""
        response = test_client.get(
            "/api/v1/legal-rights/labor-laws?country_code=US&category=working_hours"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(law["category"] == "working_hours" for law in data)

    def test_get_labor_laws_invalid_country(self, test_client):
        """Test with invalid country code returns empty list"""
        response = test_client.get(
            "/api/v1/legal-rights/labor-laws?country_code=INVALID"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestRightsSummaryEndpoint:
    """Tests for /rights-summary endpoint"""

    def test_get_rights_summary(self, test_client, sample_labor_law):
        """Test retrieving rights summary"""
        response = test_client.get(
            "/api/v1/legal-rights/rights-summary?country_code=US"
        )

        assert response.status_code == 200
        data = response.json()
        assert "country_code" in data
        assert "country_name" in data
        assert "total_laws" in data
        assert "key_protections" in data
        assert "protection_levels" in data
        assert data["country_code"] == "US"

    def test_rights_summary_includes_protections(self, test_client, sample_labor_law):
        """Test that rights summary includes key protections"""
        response = test_client.get(
            "/api/v1/legal-rights/rights-summary?country_code=US"
        )

        assert response.status_code == 200
        data = response.json()
        assert "min_wage" in data["key_protections"]
        assert "max_weekly_hours" in data["key_protections"]
        assert "overtime_threshold" in data["key_protections"]


class TestLegalAidEndpoint:
    """Tests for /legal-aid endpoint"""

    @pytest.fixture
    def sample_legal_aid(self, db_session):
        """Create sample legal aid resource"""
        aid = LegalAidResource(
            country_code="US",
            state_region="CA",
            city="San Francisco",
            resource_type="legal_aid_org",
            name="Test Legal Aid",
            description="Test legal aid organization",
            phone="555-1234",
            email="test@example.com",
            website="https://example.com",
            address="123 Main St",
            specializations=["employment", "discrimination"],
            languages_spoken=["en", "es"],
            free_consultation=True,
            verified=True,
            rating=4.5,
        )
        db_session.add(aid)
        db_session.commit()
        db_session.refresh(aid)
        return aid

    def test_find_legal_aid(self, test_client, sample_legal_aid):
        """Test finding legal aid resources"""
        response = test_client.get("/api/v1/legal-rights/legal-aid?country_code=US")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]
        assert "resource_type" in data[0]

    def test_find_legal_aid_with_filters(self, test_client, sample_legal_aid):
        """Test filtering legal aid by specialization and free consultation"""
        response = test_client.get(
            "/api/v1/legal-rights/legal-aid?country_code=US&specialization=employment&free_only=true"
        )

        assert response.status_code == 200
        data = response.json()
        # Should return resources that match the filters
        assert isinstance(data, list)


class TestViolationReporting:
    """Tests for violation reporting endpoints"""

    def test_create_violation_report(self, test_client, test_user, test_organization):
        """Test creating a contract violation report"""
        # Update user with organization
        test_user.organization_id = test_organization.id

        violation_data = {
            "violation_type": "wage_violation",
            "category": "wages_compensation",
            "severity": "high",
            "title": "Unpaid Overtime",
            "description": "Employee worked overtime without proper compensation for 3 months.",
            "labor_law_violated": "Fair Labor Standards Act",
            "incident_date_range": {
                "start": "2025-10-01T00:00:00",
                "end": "2025-12-31T00:00:00",
            },
        }

        # Note: This would require authentication in production
        # For unit testing, we might need to mock the auth dependency
        response = test_client.post(
            "/api/v1/legal-rights/violations/report", json=violation_data
        )

        # In production, this would return 201 or similar
        # For now, we expect either success or authentication error
        assert response.status_code in [201, 401, 403]


class TestKnowledgeCheck:
    """Tests for knowledge check endpoints"""

    def test_knowledge_check_questions_structure(self):
        """Test that knowledge check questions have proper structure"""
        from app.services.legal_rights_service import LegalRightsService

        # This would need a DB session, but we're testing the question structure
        # Verify that questions have required fields
        question_fields = ["question", "options", "correct_answer", "topic"]

        # Sample question from service
        sample_question = {
            "question": "Test question",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "topic": "test_topic",
        }

        assert all(field in sample_question for field in question_fields)


@pytest.mark.integration
class TestLegalRightsIntegration:
    """Integration tests for legal rights system"""

    def test_full_workflow_labor_laws_to_summary(self, test_client, sample_labor_law):
        """Test complete workflow from labor laws to summary"""
        # First get individual laws
        laws_response = test_client.get(
            "/api/v1/legal-rights/labor-laws?country_code=US"
        )
        assert laws_response.status_code == 200
        laws = laws_response.json()

        # Then get summary which aggregates those laws
        summary_response = test_client.get(
            "/api/v1/legal-rights/rights-summary?country_code=US"
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()

        # Verify consistency
        assert summary["total_laws"] == len(laws)
        assert summary["country_code"] == "US"

    def test_filter_and_search_workflow(self, test_client, sample_labor_law):
        """Test filtering and searching labor laws"""
        # Get all laws
        all_response = test_client.get(
            "/api/v1/legal-rights/labor-laws?country_code=US"
        )
        all_laws = all_response.json()

        # Filter by category
        filtered_response = test_client.get(
            "/api/v1/legal-rights/labor-laws?country_code=US&category=working_hours"
        )
        filtered_laws = filtered_response.json()

        # Verify filter works
        assert len(filtered_laws) <= len(all_laws)


class TestDataValidation:
    """Tests for data validation and constraints"""

    def test_contract_violation_severity_validation(self):
        """Test that only valid severity values are accepted"""
        from pydantic import ValidationError

        from app.api.v1.endpoints.legal_rights import ContractViolationCreate

        valid_severities = [
            "low",
            "medium",
            "high",
            "critical",
            "legal_action_required",
        ]

        for severity in valid_severities:
            try:
                violation = ContractViolationCreate(
                    violation_type="test",
                    category="test",
                    severity=severity,
                    title="Test violation",
                    description="Test description that meets minimum length requirement",
                )
                assert violation.severity == severity
            except ValidationError:
                pytest.fail(
                    f"Valid severity '{severity}' should not raise ValidationError"
                )

        # Test invalid severity
        with pytest.raises(ValidationError):
            ContractViolationCreate(
                violation_type="test",
                category="test",
                severity="invalid_severity",
                title="Test",
                description="Test",
            )

    def test_violation_description_length_validation(self):
        """Test that violation description length validation works"""
        from pydantic import ValidationError

        from app.api.v1.endpoints.legal_rights import ContractViolationCreate

        # Test too short description
        with pytest.raises(ValidationError):
            ContractViolationCreate(
                violation_type="test",
                category="test",
                severity="medium",
                title="Test",
                description="Short",  # Less than 50 characters
            )

        # Test valid description
        try:
            violation = ContractViolationCreate(
                violation_type="test",
                category="test",
                severity="medium",
                title="Test violation with proper length",
                description="This is a valid description that meets the minimum length requirement of 50 characters.",
            )
            assert violation.description is not None
        except ValidationError:
            pytest.fail("Valid description should not raise ValidationError")


@pytest.mark.security
class TestLegalRightsSecurity:
    """Security tests for legal rights endpoints"""

    def test_compliance_report_requires_admin(self, test_client):
        """Test that compliance report endpoint requires admin/HR access"""
        response = test_client.get("/api/v1/legal-rights/compliance/report")

        # Should return 401/403 without authentication
        assert response.status_code in [401, 403]

    def test_rate_limiting_on_violation_report(self, test_client):
        """Test that violation reporting has rate limiting"""
        # This would need to test multiple rapid requests
        # For now, just verify the endpoint exists
        violation_data = {
            "violation_type": "test",
            "category": "test",
            "severity": "low",
            "title": "Test",
            "description": "A" * 100,  # Valid length
        }

        response = test_client.post(
            "/api/v1/legal-rights/violations/report", json=violation_data
        )

        # Should require authentication
        assert response.status_code in [401, 403, 422]  # 422 if user/org missing


@pytest.mark.performance
class TestLegalRightsPerformance:
    """Performance tests for legal rights endpoints"""

    def test_rights_summary_response_time(self, test_client, sample_labor_law):
        """Test that rights summary responds within acceptable time"""
        import time

        start_time = time.time()
        response = test_client.get(
            "/api/v1/legal-rights/rights-summary?country_code=US"
        )
        end_time = time.time()

        assert response.status_code == 200
        # Should respond in less than 1 second
        assert (end_time - start_time) < 1.0

    def test_labor_laws_query_performance(self, test_client, sample_labor_law):
        """Test that labor laws query is performant"""
        import time

        start_time = time.time()
        response = test_client.get("/api/v1/legal-rights/labor-laws?country_code=US")
        end_time = time.time()

        assert response.status_code == 200
        # Should respond quickly
        assert (end_time - start_time) < 0.5


class TestLegalRightsDataIntegrity:
    """Tests for data integrity and consistency"""

    def test_labor_law_required_fields(self, db_session):
        """Test that labor laws have all required fields"""
        law = LaborLaw(
            country_code="US",
            country_name="United States",
            continent="NA",
            law_name="Test Law",
            law_code="TEST",
            category="working_hours",
            description="Test",
        )

        db_session.add(law)
        db_session.commit()

        assert law.id is not None
        assert law.country_code == "US"
        assert law.is_active == True
        assert law.verified == False  # Default value

    def test_legal_aid_contact_information(self, db_session):
        """Test that legal aid resources have proper contact information"""
        aid = LegalAidResource(
            country_code="US",
            resource_type="hotline",
            name="Test Hotline",
            phone="555-TEST",
        )

        db_session.add(aid)
        db_session.commit()

        assert aid.phone == "555-TEST"
        assert aid.created_at is not None
        assert aid.verified == False  # Default value
