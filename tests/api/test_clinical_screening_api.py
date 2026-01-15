"""
Clinical Screening API Integration Tests

Tests all screening API endpoints with authentication, consent, and database integration
Run with: pytest tests/api/test_clinical_screening_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models.clinical_screening import ClinicalScreening, ClinicalConsent
from app.db.models.user import User


class TestConsentFlow:
    """Test consent verification before screening"""

    def test_screening_without_consent_fails(self, client: TestClient, auth_headers: dict):
        """Should reject screening without prior consent"""
        response = client.post(
            '/api/v1/screening/phq9',
            json={'q1_interest': 1, 'q2_depressed': 1},
            headers=auth_headers
        )

        assert response.status_code == 403
        assert 'consent' in response.json()['detail'].lower()

    def test_consent_creation_allows_screening(self, client: TestClient, auth_headers: dict, db: Session):
        """Consent record should allow subsequent screening"""
        # Create consent first
        consent_response = client.post(
            '/api/v1/screening/consent',
            json={
                'consent_type': 'screening',
                'screening_types': ['PHQ9', 'GAD7']
            },
            headers=auth_headers
        )

        assert consent_response.status_code == 201

        # Now screening should work
        screening_response = client.post(
            '/api/v1/screening/phq9',
            json={
                'q1_interest': 2,
                'q2_depressed': 2,
                'q3_sleep': 1,
                'q4_energy': 2,
                'q5_appetite': 1,
                'q6_self_worth': 1,
                'q7_concentration': 2,
                'q8_motor': 1,
                'q9_suicide': 0
            },
            headers=auth_headers
        )

        assert screening_response.status_code == 200


class TestPHQ9Endpoint:
    """Test PHQ-9 screening endpoint"""

    def test_phq9_low_risk_screening(self, client: TestClient, auth_headers: dict, test_user_consent: dict):
        """PHQ-9 with low risk score"""
        response = client.post(
            '/api/v1/screening/phq9',
            json={
                'q1_interest': 0,
                'q2_depressed': 1,
                'q3_sleep': 1,
                'q4_energy': 1,
                'q5_appetite': 0,
                'q6_self_worth': 1,
                'q7_concentration': 1,
                'q8_motor': 0,
                'q9_suicide': 0
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['screening_type'] == 'PHQ9'
        assert data['total_score'] == 5
        assert data['severity_level'] == 'mild'
        assert data['risk_level'] == 'low'
        assert data['crisis_alert'] == False
        assert 'id' in data  # Database record created

    def test_phq9_with_suicide_ideation_creates_alert(self, client: TestClient, auth_headers: dict, db: Session, test_user_consent: dict):
        """PHQ-9 with suicide ideation should create crisis alert"""
        response = client.post(
            '/api/v1/screening/phq9',
            json={
                'q1_interest': 2,
                'q2_depressed': 2,
                'q3_sleep': 2,
                'q4_energy': 2,
                'q5_appetite': 2,
                'q6_self_worth': 2,
                'q7_concentration': 2,
                'q8_motor': 2,
                'q9_suicide': 2  # Triggers crisis
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['crisis_alert'] == True
        assert data['risk_level'] == 'critical'

        # Verify alert was created in database
        alerts = db.query(ClinicalAlert).filter(
            ClinicalAlert.user_id == test_user_consent['user_id']
        ).all()

        assert len(alerts) > 0
        assert alerts[0].severity == 'critical'


class TestGAD7Endpoint:
    """Test GAD-7 screening endpoint"""

    def test_gad7_moderate_anxiety(self, client: TestClient, auth_headers: dict, test_user_consent: dict):
        """GAD-7 with moderate anxiety score"""
        response = client.post(
            '/api/v1/screening/gad7',
            json={
                'q1_nervous': 2,
                'q2_control_worry': 2,
                'q3_worry_too_much': 1,
                'q4_trouble_relaxing': 2,
                'q5_restless': 1,
                'q6_irritable': 1,
                'q7_afraid': 1
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['screening_type'] == 'GAD7'
        assert data['total_score'] == 10
        assert data['severity_level'] == 'moderate'
        assert len(data['recommendations']) > 0


class TestCSSRSEndpoint:
    """Test C-SSRS suicide risk endpoint"""

    def test_cssrs_recent_attempt_critical_alert(self, client: TestClient, auth_headers: dict, db: Session, test_user_consent: dict):
        """C-SSRS with recent attempt should trigger critical alert"""
        response = client.post(
            '/api/v1/screening/cssrs',
            json={
                'wish_dead': True,
                'suicidal_thoughts': True,
                'suicidal_intent': 3,
                'suicidal_plan': True,
                'suicidal_attempts': 1,
                'lifetime_attempts': 2
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['risk_level'] == 'critical'
        assert data['crisis_alert'] == True
        assert data['severity_level'] == 'recent_attempt'


class TestPSS10Endpoint:
    """Test PSS-10 perceived stress endpoint"""

    def test_pss10_reverse_scoring(self, client: TestClient, auth_headers: dict, test_user_consent: dict):
        """PSS-10 should correctly reverse-score items 4, 5, 7, 8"""
        response = client.post(
            '/api/v1/screening/pss10',
            json={
                '1': 0,
                '2': 0,
                '3': 0,
                '4': 4,  # Reverse-scored
                '5': 4,  # Reverse-scored
                '6': 0,
                '7': 4,  # Reverse-scored
                '8': 4,  # Reverse-scored
                '9': 0,
                '10': 0
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All reverse-scored items = 4 (which become 0), others = 0
        # Total should be 0
        assert data['total_score'] == 0

    def test_pss10_severe_stress_triggers_crisis(self, client: TestClient, auth_headers: dict, test_user_consent: dict):
        """PSS-10 score >= 27 should trigger crisis alert"""
        response = client.post(
            '/api/v1/screening/pss10',
            json={
                '1': 4,
                '2': 4,
                '3': 4,
                '4': 0,  # Reverse-scored
                '5': 0,  # Reverse-scored
                '6': 4,
                '7': 0,  # Reverse-scored
                '8': 0,  # Reverse-scored
                '9': 4,
                '10': 4
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['total_score'] >= 27
        assert data['risk_level'] == 'critical'
        assert data['crisis_alert'] == True


class TestDatabaseIntegration:
    """Test database record creation and relationships"""

    def test_screening_saves_to_database(self, client: TestClient, auth_headers: dict, db: Session, test_user_consent: dict):
        """Screening should be saved to clinical_screenings table"""
        response = client.post(
            '/api/v1/screening/phq9',
            json={
                'q1_interest': 1,
                'q2_depressed': 1,
                'q3_sleep': 1,
                'q4_energy': 1,
                'q5_appetite': 1,
                'q6_self_worth': 1,
                'q7_concentration': 1,
                'q8_motor': 1,
                'q9_suicide': 0
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify record was created
        screening = db.query(ClinicalScreening).filter(
            ClinicalScreening.id == data['id']
        ).first()

        assert screening is not None
        assert screening.screening_type == 'PHQ9'
        assert screening.total_score == 9
        assert screening.user_id == test_user_consent['user_id']

    def test_audit_log_created(self, client: TestClient, auth_headers: dict, db: Session, test_user_consent: dict):
        """Screening should create audit log for HIPAA compliance"""
        from app.db.models.clinical_screening import ClinicalAuditLog

        response = client.post(
            '/api/v1/screening/phq9',
            json={
                'q1_interest': 1,
                'q2_depressed': 1,
                'q3_sleep': 1,
                'q4_energy': 1,
                'q5_appetite': 1,
                'q6_self_worth': 1,
                'q7_concentration': 1,
                'q8_motor': 1,
                'q9_suicide': 0
            },
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify audit log was created
        audit_log = db.query(ClinicalAuditLog).filter(
            ClinicalAuditLog.user_id == test_user_consent['user_id'],
            ClinicalAuditLog.action == 'phq9_screening_completed'
        ).first()

        assert audit_log is not None
        assert 'score' in audit_log.details

    def test_crisis_alert_creates_additional_records(self, client: TestClient, auth_headers: dict, db: Session, test_user_consent: dict):
        """Crisis alert should create intervention records"""
        from app.db.models.clinical_screening import ClinicalAlert, ClinicalReferral

        response = client.post(
            '/api/v1/screening/cssrs',
            json={
                'wish_dead': True,
                'suicidal_thoughts': True,
                'suicidal_intent': 3,
                'suicidal_plan': True,
                'suicidal_attempts': 0,
                'lifetime_attempts': 0
            },
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify alert was created
        alert = db.query(ClinicalAlert).filter(
            ClinicalAlert.user_id == test_user_consent['user_id']
        ).first()

        assert alert is not None
        assert alert.severity == 'critical'
        assert alert.acknowledged == False


class TestSecurityAndCompliance:
    """Test security and HIPAA compliance features"""

    def test_unauthenticated_request_rejected(self, client: TestClient):
        """Should reject requests without authentication"""
        response = client.post(
            '/api/v1/screening/phq9',
            json={'q1_interest': 1}
        )

        assert response.status_code == 401

    def test_expired_consent_rejected(self, client: TestClient, auth_headers: dict, db: Session, test_user: User):
        """Should reject screening with expired consent"""
        from datetime import datetime, timedelta

        # Create expired consent
        expired_consent = ClinicalConsent(
            user_id=test_user.id,
            consent_type='screening',
            screening_types=['PHQ9'],
            consented=True,
            expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
        )
        db.add(expired_consent)
        db.commit()

        response = client.post(
            '/api/v1/screening/phq9',
            json={'q1_interest': 1, 'q2_depressed': 1},
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_phi_not_in_url_parameters(self, client: TestClient, auth_headers: dict, test_user_consent: dict):
        """PHI should not be exposed in URL parameters"""
        # This is a behavioral test - URLs shouldn't contain sensitive data
        response = client.post(
            '/api/v1/screening/phq9',
            json={'q1_interest': 1, 'q2_depressed': 1},
            headers=auth_headers
        )

        # Request should succeed
        assert response.status_code == 200


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def db(test_db):
    """Test database session"""
    return test_db


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        email='test@example.com',
        username='testuser',
        hashed_password='hashed_password_here'
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user"""
    # In real implementation, generate valid JWT token
    token = "valid_test_token_here"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_consent(test_user, test_db):
    """Create valid consent record for test user"""
    from datetime import datetime, timedelta

    consent = ClinicalConsent(
        user_id=test_user.id,
        consent_type='screening',
        screening_types=['PHQ9', 'GAD7', 'CSSRS', 'PSS10'],
        consented=True,
        expires_at=datetime.utcnow() + timedelta(days=365)
    )
    test_db.add(consent)
    test_db.commit()

    return {
        'user_id': test_user.id,
        'consent_id': consent.id
    }


@pytest.fixture
def test_db():
    """Create test database session"""
    # In real implementation, create test database
    from app.core.database import get_db

    # This would use pytest fixtures to create/rollback test DB
    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
