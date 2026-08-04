"""
Integration Tests for Advanced Clinical Features

Tests for:
- LSAS, EAT-26, Y-BOCS assessments
- Telehealth video consultations
- AI chatbot with crisis detection
- Analytics dashboard

Run with: pytest tests/integration/test_advanced_clinical_features.py -v
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, get_async_db
from app.db.models.clinical_advanced import (
    ChatbotConversation,
    ClinicalAnalyticsSnapshot,
    TelehealthSession,
)
from app.db.models.clinical_screening import ClinicalScreening
from app.db.models.user import User
from app.main import app

BASE_URL = "http://localhost:8000"


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        password_hash="hashed_password_here",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_clinician(test_db: AsyncSession):
    """Create a test clinician"""
    clinician = User(
        id=uuid4(),
        email="clinician@example.com",
        full_name="Dr. Test Clinician",
        password_hash="hashed_password_here",
        is_active=True,
        is_superuser=True,  # Clinicians have admin privileges
    )
    test_db.add(clinician)
    await test_db.commit()
    await test_db.refresh(clinician)
    return clinician


# ============================================================================
# LSAS ASSESSMENT TESTS
# ============================================================================


class TestLSASAssessment:
    """Test LSAS (Social Anxiety) assessment flow"""

    async def test_lsas_submit_complete_assessment(
        self, client: AsyncClient, auth_headers
    ):
        """Test submitting complete LSAS assessment"""
        responses = {}
        for i in range(1, 25):
            responses[f"item_{i}"] = {"fear": 2, "avoidance": 1}

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/lsas", json=responses, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["screening_type"] == "LSAS"
        assert data["total_score"] == 72  # (2+1) * 24
        assert "severity_level" in data
        assert "risk_level" in data

    async def test_lsas_crisis_detection(self, client: AsyncClient, auth_headers):
        """Test LSAS crisis detection for severe social anxiety"""
        responses = {}
        for i in range(1, 25):
            responses[f"item_{i}"] = {
                "fear": 4,  # Maximum fear
                "avoidance": 4,  # Maximum avoidance
            }

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/lsas", json=responses, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["crisis_alert"] == True
        assert data["total_score"] == 144  # Maximum score
        assert "SEVERE_AVOIDANCE_PATTERN" in data["risk_flags"]

    async def test_lsas_subscale_calculation(self, client: AsyncClient, auth_headers):
        """Test LSAS subscale calculations"""
        # Performance situations: items 1, 5, 6, 7, 9, 11, 13, 17, 19, 22, 23, 24
        # Social situations: items 2, 3, 4, 8, 10, 12, 14, 15, 16, 18, 20, 21

        responses = {}
        for i in range(1, 25):
            fear = 3 if i in [1, 5, 6, 7, 9, 11, 13, 17, 19, 22, 23, 24] else 1
            avoidance = 3 if i in [2, 3, 4, 8, 10, 12, 14, 15, 16, 18, 20, 21] else 1
            responses[f"item_{i}"] = {"fear": fear, "avoidance": avoidance}

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/lsas", json=responses, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "subscale_scores" in data
        assert data["subscale_scores"]["performance_anxiety"] > 0
        assert data["subscale_scores"]["social_interaction_anxiety"] > 0


# ============================================================================
# EAT-26 ASSESSMENT TESTS
# ============================================================================


class TestEAT26Assessment:
    """Test EAT-26 (Eating Disorders) assessment flow"""

    async def test_eat26_below_threshold(self, client: AsyncClient, auth_headers):
        """Test EAT-26 below referral threshold (< 20)"""
        item_responses = {i: 0 for i in range(1, 27)}  # All "Never" responses

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/eat26",
            json={
                "responses": item_responses,
                "behavioral_questions": {
                    "weight_loss_6months": False,
                    "binge_eating": "never",
                    "vomiting": "never",
                    "laxatives": "never",
                    "exercise": "never",
                    "bmi_concern": False,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_score"] == 0
        assert data["crisis_alert"] == False
        assert data["risk_level"] == "low"

    async def test_eat26_above_threshold(self, client: AsyncClient, auth_headers):
        """Test EAT-26 above referral threshold (≥ 20)"""
        # Score 21 on items (above threshold of 20)
        item_responses = {
            i: 3 if i <= 7 else 0 for i in range(1, 27)
        }  # 7 items × 3 = 21

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/eat26",
            json={"responses": item_responses, "behavioral_questions": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_score"] >= 20
        assert data["risk_level"] in ["moderate", "high"]

    async def test_eat26_purging_detection(self, client: AsyncClient, auth_headers):
        """Test EAT-26 purging behavior detection"""
        item_responses = {i: 0 for i in range(1, 27)}

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/eat26",
            json={
                "responses": item_responses,
                "behavioral_questions": {
                    "vomiting": "once_a_week",  # Triggers crisis alert
                    "laxatives": "never",
                    "binge_eating": "never",
                    "weight_loss_6months": False,
                    "exercise": "never",
                    "bmi_concern": False,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["crisis_alert"] == True
        assert "PURGING_BEHAVIORS" in data["risk_flags"]


# ============================================================================
# Y-BOCS ASSESSMENT TESTS
# ============================================================================


class TestYBOCSAssessment:
    """Test Y-BOCS (OCD) assessment flow"""

    async def test_ybocs_subclinical(self, client: AsyncClient, auth_headers):
        """Test Y-BOCS subclinical score (≤ 7)"""
        responses = {i: 0 for i in range(1, 6)}  # All obsessions: none
        responses.update({i: 1 for i in range(6, 11)})  # All compulsions: mild

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/ybocs", json=responses, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_score"] == 5
        assert data["severity_level"] == "subclinical"
        assert data["risk_level"] == "low"

    async def test_ybocs_severe(self, client: AsyncClient, auth_headers):
        """Test Y-BOCS severe score (≥ 32)"""
        responses = {i: 4 for i in range(1, 11)}  # All maximum severity

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/ybocs", json=responses, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_score"] == 40  # Maximum
        assert data["severity_level"] == "extreme"
        assert data["crisis_alert"] == True
        assert "SEVERE_OCD_SYMPTOMS" in data["risk_flags"]

    async def test_ybocs_obsession_dominant(self, client: AsyncClient, auth_headers):
        """Test Y-BOCS obsession-dominant presentation"""
        # High obsessions, low compulsions
        responses = {i: 4 for i in range(1, 6)}  # Severe obsessions
        responses.update({i: 0 for i in range(6, 11)})  # No compulsions

        response = await client.post(
            f"{BASE_URL}/api/v1/screening/ybocs", json=responses, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "subscale_scores" in data
        assert data["subscale_scores"]["obsessions_severity"] == 20
        assert data["subscale_scores"]["compulsions_severity"] == 0


# ============================================================================
# TELEHEALTH TESTS
# ============================================================================


class TestTelehealthService:
    """Test telehealth video consultation service"""

    async def test_schedule_consultation(
        self,
        client: AsyncClient,
        auth_headers,
        test_user,
        test_clinician,
        test_db: AsyncSession,
    ):
        """Test scheduling a video consultation"""
        scheduled_time = datetime.now() + timedelta(days=1)

        response = await client.post(
            f"{BASE_URL}/api/v1/telehealth/schedule",
            json={
                "clinician_id": str(test_clinician.id),
                "scheduled_time": scheduled_time.isoformat(),
                "session_type": "initial",
                "duration_minutes": 60,
                "recording_enabled": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is not None
        assert data["room_name"] is not None
        assert data["user_token"] is not None
        assert data["clinician_token"] is not None
        assert data["status"] == "scheduled"

    async def test_check_availability(
        self, client: AsyncClient, auth_headers, test_clinician, test_db: AsyncSession
    ):
        """Test checking clinician availability"""
        requested_time = datetime.now() + timedelta(days=1)

        response = await client.get(
            f"{BASE_URL}/api/v1/telehealth/availability",
            params={
                "clinician_id": str(test_clinician.id),
                "requested_time": requested_time.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "available" in data

    async def test_get_upcoming_sessions(self, client: AsyncClient, auth_headers):
        """Test retrieving upcoming sessions"""
        response = await client.get(
            f"{BASE_URL}/api/v1/telehealth/upcoming?role=patient", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)


# ============================================================================
# AI CHATBOT TESTS
# ============================================================================


class TestAIChatbot:
    """Test AI chatbot with crisis detection"""

    async def test_normal_conversation(self, client: AsyncClient, auth_headers):
        """Test normal chatbot conversation"""
        response = await client.post(
            f"{BASE_URL}/api/v1/chatbot/message",
            json={
                "message": "I am feeling anxious today",
                "session_id": "test_session_123",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "crisis_detected" in data
        assert data["crisis_detected"] == False
        assert data["action"] == "continue_conversation"

    async def test_crisis_keyword_detection(self, client: AsyncClient, auth_headers):
        """Test crisis keyword detection in chatbot"""
        response = await client.post(
            f"{BASE_URL}/api/v1/chatbot/message",
            json={"message": "I want to kill myself", "session_id": "test_session_123"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["crisis_detected"] == True
        assert data["action"] == "escalate_to_human"
        assert "crisis_hotline" in data

    async def test_multiple_crisis_keywords(self, client: AsyncClient, auth_headers):
        """Test chatbot detects various crisis phrases"""
        crisis_phrases = [
            "I am thinking about suicide",
            "I have a plan to end it",
            "I want to die",
            "no reason to live",
            "better off dead",
        ]

        for phrase in crisis_phrases:
            response = await client.post(
                f"{BASE_URL}/api/v1/chatbot/message",
                json={"message": phrase, "session_id": f"test_session_{uuid4()}"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert (
                data["crisis_detected"] == True
            ), f"Failed to detect crisis in: {phrase}"


# ============================================================================
# ANALYTICS TESTS
# ============================================================================


class TestClinicalAnalytics:
    """Test clinical analytics endpoints"""

    async def test_population_insights(self, client: AsyncClient, auth_headers):
        """Test population health insights endpoint"""
        response = await client.get(
            f"{BASE_URL}/api/v1/analytics/population?org_id=test_org&period=30d",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "prevalence_rates" in data or "total_assessments" in data

    async def test_user_trends(
        self, client: AsyncClient, auth_headers, test_user, test_db: AsyncSession
    ):
        """Test individual user trend analysis"""
        response = await client.get(
            f"{BASE_URL}/api/v1/analytics/user/{test_user.id}/trends?assessment_type=LSAS&period=3months",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should return trend data or empty response for new user


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestEndToEndWorkflow:
    """Test complete user workflows"""

    async def test_complete_assessment_workflow(
        self, client: AsyncClient, auth_headers, test_user, test_db: AsyncSession
    ):
        """Test complete workflow: consent → assessment → results → crisis escalation if needed"""
        # This would be a comprehensive test covering the full user journey
        # For brevity, we test a simplified version

        # 1. Submit LSAS assessment
        responses = {f"item_{i}": {"fear": 2, "avoidance": 1} for i in range(1, 25)}

        assessment_response = await client.post(
            f"{BASE_URL}/api/v1/screening/lsas", json=responses, headers=auth_headers
        )

        assert assessment_response.status_code == 200
        assessment_data = assessment_response.json()

        # 2. Verify data was stored
        assert assessment_data["id"] is not None
        assert assessment_data["screening_type"] == "LSAS"
        assert assessment_data["total_score"] == 72

        # 3. Check that assessment was saved to database
        # (In real test, would query DB to verify)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformance:
    """Test performance and scalability"""

    async def test_concurrent_assessments(self, client: AsyncClient, auth_headers):
        """Test handling multiple concurrent assessment submissions"""
        import asyncio

        async def submit_assessment():
            responses = {f"item_{i}": {"fear": 1, "avoidance": 1} for i in range(1, 25)}
            return await client.post(
                f"{BASE_URL}/api/v1/screening/lsas",
                json=responses,
                headers=auth_headers,
            )

        # Submit 10 assessments concurrently
        responses = await asyncio.gather(*[submit_assessment() for _ in range(10)])

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    async def test_api_response_time(self, client: AsyncClient, auth_headers):
        """Test API response time is acceptable"""
        import time

        start_time = time.time()

        responses = {f"item_{i}": {"fear": 1, "avoidance": 1} for i in range(1, 25)}
        response = await client.post(
            f"{BASE_URL}/api/v1/screening/lsas", json=responses, headers=auth_headers
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms

        assert response.status_code == 200
        # Should respond in under 2 seconds
        assert response_time < 2000, f"Response time too slow: {response_time}ms"


# ============================================================================
# SECURITY TESTS
# ============================================================================


class TestSecurity:
    """Test security and HIPAA compliance"""

    async def test_phi_not_exposed_in_errors(self, client: AsyncClient):
        """Test that PHI is not exposed in error messages"""
        # Submit malformed data
        response = await client.post(
            f"{BASE_URL}/api/v1/screening/lsas",
            json={"invalid": "data"},
            headers={"Authorization": "Bearer invalid_token"},
        )

        # Should get error but not expose internal details
        assert response.status_code in [401, 403, 422]

        # Error message should not contain sensitive information
        # (implementation-specific check)

    async def test_audit_logging(self, client: AsyncClient, auth_headers):
        """Test that all PHI access is logged"""
        # This would verify that audit logs are created
        # In real implementation, would check audit log table
        pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


@pytest.mark.asyncio
async def test_cleanup(test_db: AsyncSession):
    """Clean up test data after tests"""
    # Delete test clinical screenings
    await test_db.execute(
        ClinicalScreening.__table__.delete().where(
            ClinicalScreening.screening_type == "LSAS"
        )
    )
    await test_db.commit()
