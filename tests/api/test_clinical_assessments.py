"""
Test Suite for Clinical Assessment Endpoints

Tests for:
- LSAS (Social Anxiety) assessment
- EAT-26 (Eating Disorders) assessment
- Y-BOCS (OCD) assessment
- Crisis detection and alerting
- Assessment history retrieval
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from app.main import app
from app.db.session import get_async_db
from app.db.models.user import User
from app.services.clinical.scoring_algorithms import LSASScorer, EAT26Scorer, YBOCSScorer


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
async def test_user(db: AsyncSession):
    """Create test user"""
    from app.db.models.user import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email="test@example.com",
        password_hash=pwd_context.hash("testpass123"),
        full_name="Test User",
        is_active=True,
        role="user"
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@pytest.fixture
async def clinician_user(db: AsyncSession):
    """Create clinician user for testing"""
    from app.db.models.user import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    clinician = User(
        email="clinician@example.com",
        password_hash=pwd_context.hash("testpass123"),
        full_name="Dr. Test Clinician",
        is_active=True,
        role="clinician"
    )

    db.add(clinician)
    await db.commit()
    await db.refresh(clinician)

    return clinician


@pytest.fixture
def auth_headers(test_user: User):
    """Get authentication headers for test user"""
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


# =====================================================================
# LSAS Tests
# =====================================================================

class TestLSASAssessment:
    """Test LSAS (Social Anxiety) assessment endpoints"""

    def test_lsas_submit_valid_response(
        self,
        client: TestClient,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test submitting valid LSAS assessment"""

        # Prepare valid LSAS responses (24 items, fear + avoidance each)
        responses = {}
        for i in range(1, 25):
            responses[f'item_{i}'] = {
                'fear': 2,
                'avoidance': 1
            }

        response = client.post(
            "/api/v1/clinical/LSAS/submit",
            json={'responses': responses},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert data['assessment_type'] == 'LSAS'
        assert 'total_score' in data
        assert 'severity_level' in data
        assert 'risk_level' in data
        assert 'interpretation' in data
        assert 'recommendations' in data
        assert isinstance(data['recommendations'], list)
        assert 'crisis_alert' in data
        assert isinstance(data['crisis_alert'], bool)

        # Validate score range (should be 24-72 for our test data)
        assert 0 <= data['total_score'] <= 144
        assert data['subscale_scores']['fear'] >= 0
        assert data['subscale_scores']['avoidance'] >= 0

    def test_lsas_missing_items(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test LSAS submission with missing items"""

        # Only submit 10 items instead of 24
        responses = {}
        for i in range(1, 11):
            responses[f'item_{i}'] = {
                'fear': 1,
                'avoidance': 1
            }

        response = client.post(
            "/api/v1/clinical/LSAS/submit",
            json={'responses': responses},
            headers=auth_headers
        )

        # Should return validation error
        assert response.status_code == 400

    def test_lsas_invalid_rating_values(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test LSAS with invalid rating values (outside 0-3 range)"""

        responses = {}
        for i in range(1, 25):
            responses[f'item_{i}'] = {
                'fear': 5,  # Invalid: should be 0-3
                'avoidance': 2
            }

        response = client.post(
            "/api/v1/clinical/LSAS/submit",
            json={'responses': responses},
            headers=auth_headers
        )

        # Should return validation error
        assert response.status_code == 400

    def test_lsas_high_score_triggers_alert(
        self,
        client: TestClient,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test that high LSAS scores trigger crisis alert"""

        # Submit very high scores (all 3s)
        responses = {}
        for i in range(1, 25):
            responses[f'item_{i}'] = {
                'fear': 3,
                'avoidance': 3
            }

        response = client.post(
            "/api/v1/clinical/LSAS/submit",
            json={'responses': responses},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # High scores should trigger crisis alert
        assert data['total_score'] == 144  # Maximum possible
        assert data['crisis_alert'] == True
        assert data['risk_level'] in ['high', 'critical']

    def test_lsas_get_history(
        self,
        client: TestClient,
        auth_headers: dict,
        db: AsyncSession
    ):
        """Test retrieving LSAS assessment history"""

        response = client.get(
            "/api/v1/clinical/LSAS/history?limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 'assessments' key with list
        assert 'assessments' in data
        assert isinstance(data['assessments'], list)

        # Each assessment should have required fields
        for assessment in data['assessments']:
            assert 'id' in assessment
            assert 'total_score' in assessment
            assert 'severity_level' in assessment
            assert 'completed_at' in assessment


# =====================================================================
# EAT-26 Tests
# =====================================================================

class TestEAT26Assessment:
    """Test EAT-26 (Eating Disorders) assessment endpoints"""

    def test_eat26_submit_valid_response(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test submitting valid EAT-26 assessment"""

        # Prepare valid EAT-26 responses (26 items, 0-5 scale)
        responses = {str(i): 2 for i in range(1, 27)}

        behavioral = {
            'weight_loss_6months': 'no',
            'binge_eating': 'never',
            'vomiting': 'never',
            'laxatives': 'never',
            'exercise': 'moderate'
        }

        response = client.post(
            "/api/v1/clinical/EAT26/submit",
            json={
                'responses': responses,
                'behavioral': behavioral
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['assessment_type'] == 'EAT26'
        assert 0 <= data['total_score'] <= 78

    def test_eat26_frequent_vomiting_triggers_critical_alert(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that frequent vomiting triggers CRITICAL crisis alert"""

        responses = {str(i): 4 for i in range(1, 27)}

        behavioral = {
            'weight_loss_6months': 'yes',
            'binge_eating': 'weekly',
            'vomiting': 'daily',  # CRITICAL risk factor
            'laxatives': 'weekly',
            'exercise': 'excessive'
        }

        response = client.post(
            "/api/v1/clinical/EAT26/submit",
            json={
                'responses': responses,
                'behavioral': behavioral
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should trigger CRITICAL alert
        assert data['crisis_alert'] == True
        assert data['risk_level'] == 'critical'
        assert 'FREQUENT_PURGING' in data['risk_flags'] or 'DAILY_VOMITING' in data['risk_flags']


# =====================================================================
# Y-BOCS Tests
# =====================================================================

class TestYBOCSAssessment:
    """Test Y-BOCS (OCD) assessment endpoints"""

    def test_ybocs_submit_valid_response(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test submitting valid Y-BOCS assessment"""

        # Prepare valid Y-BOCS responses (10 items, 0-4 scale)
        responses = {str(i): 2 for i in range(1, 11)}

        response = client.post(
            "/api/v1/clinical/YBOCS/submit",
            json={'responses': responses},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['assessment_type'] == 'YBOCS'
        assert 0 <= data['total_score'] <= 40

        # Should have obsession and compulsion subscores
        assert 'obsessions' in data['subscale_scores']
        assert 'compulsions' in data['subscale_scores']

    def test_ybocs_extreme_score(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test Y-BOCS with maximum scores (Extreme OCD)"""

        responses = {str(i): 4 for i in range(1, 11)}

        response = client.post(
            "/api/v1/clinical/YBOCS/submit",
            json={'responses': responses},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['total_score'] == 40  # Maximum
        assert data['severity_level'] == 'extreme'
        assert data['crisis_alert'] == True


# =====================================================================
# Analytics Tests
# =====================================================================

class TestAnalyticsEndpoints:
    """Test advanced analytics endpoints"""

    def test_get_user_trends_insufficient_data(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test trend analysis with insufficient data points"""

        response = client.get(
            "/api/v1/clinical/analytics/user/trends?assessment_type=LSAS",
            headers=auth_headers
        )

        # Should return message about insufficient data
        assert response.status_code == 200
        data = response.json()
        assert 'trend' in data
        assert data['trend'] is None or 'insufficient' in data.get('message', '').lower()

    def test_get_population_metrics_unauthorized(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that regular users can't access population metrics"""

        response = client.get(
            "/api/v1/clinical/analytics/population-metrics?assessment_type=LSAS",
            headers=auth_headers
        )

        # Should be forbidden (only clinicians/admins)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_population_metrics_clinician(
        self,
        client: TestClient,
        db: AsyncSession,
        clinician_user: User
    ):
        """Test population metrics endpoint with clinician access"""
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": str(clinician_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/v1/clinical/analytics/population-metrics?assessment_type=LSAS&period_days=30",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'metrics' in data
        assert isinstance(data['metrics'], list)

        # Each metric should have required fields
        for metric in data['metrics']:
            assert 'total_assessments' in metric
            assert 'unique_users' in metric
            assert 'mean_score' in metric


# =====================================================================
# Integration Tests
# =====================================================================

class TestAssessmentIntegration:
    """Integration tests for complete assessment workflows"""

    def test_complete_lsas_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db: AsyncSession
    ):
        """Test complete LSAS workflow: submit → retrieve → analyze trend"""

        # 1. Submit LSAS assessment
        responses = {}
        for i in range(1, 25):
            responses[f'item_{i}'] = {
                'fear': 1,
                'avoidance': 1
            }

        submit_response = client.post(
            "/api/v1/clinical/LSAS/submit",
            json={'responses': responses},
            headers=auth_headers
        )
        assert submit_response.status_code == 200

        # 2. Retrieve history
        history_response = client.get(
            "/api/v1/clinical/LSAS/history",
            headers=auth_headers
        )
        assert history_response.status_code == 200
        assert len(history_response.json()['assessments']) > 0

        # 3. Check trends (should still be insufficient with 1 assessment)
        trend_response = client.get(
            "/api/v1/clinical/analytics/user/trends?assessment_type=LSAS",
            headers=auth_headers
        )
        assert trend_response.status_code == 200


# =====================================================================
# Performance Tests
# =====================================================================

class TestAssessmentPerformance:
    """Performance tests for assessment endpoints"""

    def test_lsas_submission_performance(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test LSAS submission completes in acceptable time"""
        import time

        responses = {}
        for i in range(1, 25):
            responses[f'item_{i}'] = {
                'fear': 2,
                'avoidance': 2
            }

        start_time = time.time()
        response = client.post(
            "/api/v1/clinical/LSAS/submit",
            json={'responses': responses},
            headers=auth_headers
        )
        duration = time.time() - start_time

        assert response.status_code == 200
        # Should complete in under 2 seconds
        assert duration < 2.0
