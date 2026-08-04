"""
Health Monitoring & Intervention System Tests

Tests for:
- StressMonitoringService - health risk analysis
- HealthInterventionSystem - automated interventions
- API endpoints - health monitoring endpoints
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.services.health.intervention_system import (
    HealthInterventionSystem,
    InterventionAction,
    InterventionType,
    InterventionUrgency,
)
from app.services.health.stress_monitoring_service import (
    BiometricData,
    BurnoutStage,
    HealthRiskIndicators,
    StressLevel,
    StressMonitoringService,
)

# ============================================================================
# StressMonitoringService Tests
# ============================================================================


class TestStressMonitoringService:
    """Test suite for StressMonitoringService"""

    @pytest.fixture
    def db_session(self):
        """Create mock database session"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def monitoring_service(self, db_session):
        """Create stress monitoring service instance"""
        return StressMonitoringService(db_session)

    @pytest.fixture
    def sample_biometric_data(self):
        """Create sample biometric data"""
        return BiometricData(
            resting_heart_rate=88,
            heart_rate_variability=42,
            heart_rate_avg=78,
            blood_pressure_systolic=145,
            blood_pressure_diastolic=95,
            sleep_hours=5.5,
            sleep_quality=0.4,
            steps_per_day=4000,
            activity_minutes=20,
        )

    @pytest.mark.asyncio
    async def test_analyze_health_risks_with_high_biometric_risk(
        self, monitoring_service, db_session, sample_biometric_data
    ):
        """Test health risk analysis with high biometric risk factors"""
        user_id = str(uuid4())
        organization_id = str(uuid4())

        # Mock email query results
        mock_emails = []
        for i in range(100):  # 100 emails in 30 days = high email volume
            email = Mock()
            base_date = datetime.utcnow() - timedelta(days=i % 30)
            hour = 20 if i % 2 == 0 else 10  # Half after hours
            email.sent_at = base_date.replace(hour=hour)
            mock_emails.append(email)

        # Mock communication analysis results
        mock_analyses = []
        for i in range(50):
            analysis = Mock()
            analysis.urgency_level = "high" if i % 3 == 0 else "low"
            analysis.conflict_probability = 0.7 if i % 4 == 0 else 0.2
            analysis.sentiment_score = -0.6 if i % 5 == 0 else 0.2
            mock_analyses.append(analysis)

        # Mock wellness metrics
        mock_wellness = Mock()
        mock_wellness.stress_level = 8
        mock_wellness.exhaustion_level = 7
        mock_wellness.engagement_level = 4
        mock_wellness.cynicism_level = 7
        mock_wellness.professional_efficacy = 3
        mock_wellness.professional_wellness = 3
        mock_wellness.physical_wellness = 3
        mock_wellness.mental_wellness = 3
        mock_wellness.emotional_wellness = 3
        mock_wellness.social_wellness = 3
        mock_wellness.resilience_score = 3
        mock_wellness.support_systems_quality = 3
        mock_wellness.sleep_disruption = 0.7
        mock_wellness.social_withdrawal = 0.6

        with patch.object(monitoring_service, "_analyze_work_patterns") as mock_work:
            with patch.object(
                monitoring_service, "_analyze_communication_stress"
            ) as mock_comm:
                with patch.object(
                    monitoring_service, "_get_wellness_metrics"
                ) as mock_wellness_query:

                    mock_work.return_value = {
                        "weekly_hours": 65,
                        "after_hours_count": 60,
                        "weekend_work_percentage": 0.7,
                        "continuous_days": 18,
                        "avg_emails_per_day": 100 / 30,
                        "data_available": True,
                    }

                    mock_comm.return_value = {
                        "urgency_emails": 25,
                        "conflict_indicators": 8,
                        "negative_sentiment_avg": -0.5,
                        "sentiment_volatility": 0.7,
                        "data_available": True,
                    }

                    mock_wellness_query.return_value = mock_wellness

                    # Execute analysis
                    health_risks = await monitoring_service.analyze_health_risks(
                        user_id=user_id,
                        organization_id=organization_id,
                        time_window_days=30,
                        biometric_data=sample_biometric_data,
                    )

                    # Assertions
                    assert health_risks.stress_level in [
                        StressLevel.HIGH,
                        StressLevel.CRITICAL,
                    ]
                    assert (
                        health_risks.cardiovascular_risk_score > 0.7
                    )  # High due to biometric data
                    assert health_risks.urgent_intervention_needed == True
                    assert (
                        health_risks.recommend_medical_evaluation == True
                    )  # Due to high BP
                    assert len(health_risks.primary_risk_factors) > 0
                    assert any(
                        "blood pressure" in factor.lower()
                        for factor in health_risks.primary_risk_factors
                    )
                    assert any(
                        "heart rate" in factor.lower()
                        for factor in health_risks.primary_risk_factors
                    )

    @pytest.mark.asyncio
    async def test_analyze_health_risks_normal(self, monitoring_service):
        """Test health risk analysis with normal health indicators"""
        user_id = str(uuid4())
        organization_id = str(uuid4())

        normal_biometric = BiometricData(
            resting_heart_rate=60,
            heart_rate_variability=65,
            heart_rate_avg=70,
            blood_pressure_systolic=115,
            blood_pressure_diastolic=75,
            sleep_hours=8,
            sleep_quality=0.9,
            steps_per_day=10000,
            activity_minutes=60,
        )

        with patch.object(monitoring_service, "_analyze_work_patterns") as mock_work:
            with patch.object(
                monitoring_service, "_analyze_communication_stress"
            ) as mock_comm:
                with patch.object(
                    monitoring_service, "_get_wellness_metrics"
                ) as mock_wellness_query:

                    mock_work.return_value = {
                        "weekly_hours": 40,
                        "after_hours_count": 5,
                        "weekend_work_percentage": 0.1,
                        "continuous_days": 5,
                        "avg_emails_per_day": 20 / 30,
                        "data_available": True,
                    }

                    mock_comm.return_value = {
                        "urgency_emails": 2,
                        "conflict_indicators": 0,
                        "negative_sentiment_avg": 0.1,
                        "sentiment_volatility": 0.2,
                        "data_available": True,
                    }

                    mock_wellness_query.return_value = None

                    health_risks = await monitoring_service.analyze_health_risks(
                        user_id=user_id,
                        organization_id=organization_id,
                        time_window_days=30,
                        biometric_data=normal_biometric,
                    )

                    # Should be normal or elevated
                    assert health_risks.stress_level in [
                        StressLevel.NORMAL,
                        StressLevel.ELEVATED,
                    ]
                    assert health_risks.cardiovascular_risk_score < 0.3  # Low risk
                    assert health_risks.urgent_intervention_needed == False
                    assert health_risks.recommend_medical_evaluation == False

    @pytest.mark.asyncio
    async def test_determine_burnout_stage_habitual(self, monitoring_service):
        """Test burnout stage determination - habitual burnout"""
        work_patterns = {"weekly_hours": 70, "continuous_days": 25}

        communication_stress = {
            "negative_sentiment_avg": -0.8,
            "conflict_indicators": 15,
        }

        mock_wellness = Mock()
        mock_wellness.engagement_level = 2
        mock_wellness.exhaustion_level = 9
        mock_wellness.cynicism_level = 8
        mock_wellness.professional_efficacy = 3

        stage = monitoring_service._determine_burnout_stage(
            work_patterns, communication_stress, mock_wellness
        )

        assert stage in [BurnoutStage.BURNOUT, BurnoutStage.HABITUAL_BURNOUT]

    @pytest.mark.asyncio
    async def test_calculate_cardiovascular_risk_with_biometrics(
        self, monitoring_service
    ):
        """Test cardiovascular risk calculation with biometric data"""
        work_patterns = {"weekly_hours": 60, "continuous_days": 15}

        high_risk_biometric = BiometricData(
            resting_heart_rate=90,
            heart_rate_variability=35,
            blood_pressure_systolic=150,
            blood_pressure_diastolic=100,
            sleep_hours=4,
        )

        risk = monitoring_service._calculate_cardiovascular_risk(
            work_patterns=work_patterns,
            stress_level=StressLevel.HIGH,
            biometric_data=high_risk_biometric,
            wellness_metrics=None,
        )

        # Should be very high risk
        assert risk > 0.8

    def test_identify_risk_factors_comprehensive(
        self, monitoring_service, sample_biometric_data
    ):
        """Test risk factor identification"""
        work_patterns = {
            "weekly_hours": 65,
            "continuous_days": 18,
            "after_hours_count": 70,
            "late_night_work_days": 15,
        }

        communication_stress = {
            "conflict_indicators": 12,
            "urgency_emails": 35,
            "negative_sentiment_avg": -0.7,
        }

        mock_wellness = Mock()
        mock_wellness.engagement_level = 3
        mock_wellness.social_wellness = 4

        risk_factors = monitoring_service._identify_risk_factors(
            work_patterns=work_patterns,
            communication_stress=communication_stress,
            wellness_metrics=mock_wellness,
            biometric_data=sample_biometric_data,
        )

        # Should identify multiple risk factors
        assert len(risk_factors) > 5

        # Check for expected factors
        factor_text = " ".join(risk_factors).lower()
        assert "work hours" in factor_text or "cardiovascular" in factor_text
        assert "blood pressure" in factor_text


# ============================================================================
# HealthInterventionSystem Tests
# ============================================================================


class TestHealthInterventionSystem:
    """Test suite for HealthInterventionSystem"""

    @pytest.fixture
    def db_session(self):
        """Create mock database session"""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def intervention_system(self, db_session):
        """Create intervention system instance"""
        return HealthInterventionSystem(db_session)

    @pytest.fixture
    def sample_health_risks(self):
        """Create sample health risk indicators"""
        return HealthRiskIndicators(
            stress_level=StressLevel.CRITICAL,
            burnout_stage=BurnoutStage.BURNOUT,
            cardiovascular_risk_score=0.85,
            mental_health_risk=0.75,
            work_life_imbalance=0.8,
            sleep_disruption_score=0.7,
            social_isolation_score=0.6,
            urgent_intervention_needed=True,
            recommend_medical_evaluation=True,
            recommend_immediate_break=True,
            recommend_workload_reduction=True,
            primary_risk_factors=[
                "Excessive work hours (>60/week)",
                "High blood pressure",
                "Severe sleep deprivation",
            ],
            warning_signs=["Working most weekends", "Emotional instability"],
            protective_factors=[],
            data_sources=["email_metadata", "communication_analysis", "biometric_data"],
            confidence_level=0.85,
        )

    @pytest.mark.asyncio
    async def test_create_medical_alert_intervention(self, intervention_system):
        """Test creation of medical alert intervention"""
        user_id = str(uuid4())
        organization_id = str(uuid4())

        health_risks = HealthRiskIndicators(
            stress_level=StressLevel.CRITICAL,
            burnout_stage=BurnoutStage.BURNOUT,
            cardiovascular_risk_score=0.9,
            mental_health_risk=0.5,
            work_life_imbalance=0.5,
            sleep_disruption_score=0.5,
            social_isolation_score=0.5,
            urgent_intervention_needed=True,
            recommend_medical_evaluation=True,
            recommend_immediate_break=False,
            recommend_workload_reduction=False,
            primary_risk_factors=["High blood pressure - 150/100"],
            warning_signs=[],
            protective_factors=[],
            data_sources=[],
            confidence_level=0.8,
        )

        intervention = intervention_system._create_medical_alert_intervention(
            user_id=user_id, organization_id=organization_id, health_risks=health_risks
        )

        assert intervention.intervention_type == InterventionType.MEDICAL_ALERT
        assert intervention.urgency == InterventionUrgency.CRITICAL
        assert intervention.notify_user == True
        assert intervention.notify_manager == True
        assert intervention.notify_hr == True
        assert (
            "medical" in intervention.title.lower()
            or "urgent" in intervention.title.lower()
        )
        assert len(intervention.actions_required) > 0
        assert len(intervention.resources) > 0

    @pytest.mark.asyncio
    async def test_create_immediate_break_intervention(self, intervention_system):
        """Test creation of immediate break intervention"""
        user_id = str(uuid4())
        organization_id = str(uuid4())

        health_risks = HealthRiskIndicators(
            stress_level=StressLevel.CRITICAL,
            burnout_stage=BurnoutStage.CHRONIC_STRESS,
            cardiovascular_risk_score=0.5,
            mental_health_risk=0.8,
            work_life_imbalance=0.6,
            sleep_disruption_score=0.5,
            social_isolation_score=0.5,
            urgent_intervention_needed=True,
            recommend_medical_evaluation=False,
            recommend_immediate_break=True,
            recommend_workload_reduction=False,
            primary_risk_factors=[],
            warning_signs=[],
            protective_factors=[],
            data_sources=[],
            confidence_level=0.7,
        )

        intervention = intervention_system._create_immediate_break_intervention(
            user_id=user_id, organization_id=organization_id, health_risks=health_risks
        )

        assert intervention.intervention_type == InterventionType.IMMEDIATE_BREAK
        assert intervention.urgency == InterventionUrgency.CRITICAL
        assert "break" in intervention.title.lower()
        assert len(intervention.automated_actions) > 0
        assert any(
            "calendar" in action.lower() for action in intervention.automated_actions
        )

    @pytest.mark.asyncio
    async def test_create_workload_reduction_intervention(self, intervention_system):
        """Test creation of workload reduction intervention"""
        user_id = str(uuid4())
        organization_id = str(uuid4())
        team_id = str(uuid4())

        work_patterns = {"weekly_hours": 70, "continuous_days": 21}

        intervention = intervention_system._create_workload_reduction_intervention(
            user_id=user_id,
            organization_id=organization_id,
            team_id=team_id,
            work_patterns=work_patterns,
        )

        assert intervention.intervention_type == InterventionType.WORKLOAD_REDUCTION
        assert intervention.urgency == InterventionUrgency.HIGH
        assert intervention.notify_manager == True
        assert intervention.notify_hr == True
        assert len(intervention.actions_required) > 0
        assert any(
            "workload" in action.lower() for action in intervention.actions_required
        )

    @pytest.mark.asyncio
    async def test_create_intervention_plan_comprehensive(
        self, intervention_system, db_session, sample_health_risks
    ):
        """Test creation of comprehensive intervention plan"""
        user_id = str(uuid4())
        organization_id = str(uuid4())
        team_id = str(uuid4())

        work_patterns = {"weekly_hours": 65, "continuous_days": 18}

        with patch.object(intervention_system, "_persist_interventions"):
            with patch.object(intervention_system, "_execute_interventions"):
                interventions = await intervention_system.create_intervention_plan(
                    user_id=user_id,
                    organization_id=organization_id,
                    team_id=team_id,
                    health_risks=sample_health_risks,
                    work_patterns=work_patterns,
                )

                # Should create multiple interventions
                assert len(interventions) > 0

                # Check for critical interventions
                intervention_types = [intv.intervention_type for intv in interventions]
                assert InterventionType.MEDICAL_ALERT in intervention_types
                assert InterventionType.IMMEDIATE_BREAK in intervention_types

                # Check workload reduction
                assert InterventionType.WORKLOAD_REDUCTION in intervention_types


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestHealthMonitoringIntegration:
    """Integration tests for health monitoring system"""

    @pytest.mark.asyncio
    async def test_full_health_monitoring_workflow(self):
        """Test complete workflow from data analysis to intervention"""
        # This would be a full integration test with actual database
        # For now, it's a placeholder showing the intended workflow
        pass

    @pytest.mark.asyncio
    async def test_email_metadata_integration(self):
        """Test integration with email metadata for work pattern analysis"""
        # Test actual email metadata query and analysis
        pass

    @pytest.mark.asyncio
    async def test_communication_analysis_integration(self):
        """Test integration with communication analysis"""
        # Test actual communication analysis integration
        pass


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestHealthMonitoringAPI:
    """Test suite for health monitoring API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_analyze_health_risks_endpoint(self, client):
        """Test POST /api/v1/health-monitoring/analyze endpoint"""
        # This would test the actual API endpoint
        # Requires authentication setup
        pass

    def test_submit_biometric_data_endpoint(self, client):
        """Test POST /api/v1/health-monitoring/biometric endpoint"""
        # Test biometric data submission
        pass

    def test_manager_dashboard_endpoint(self, client):
        """Test GET /api/v1/health-monitoring/manager-dashboard endpoint"""
        # Test anonymized manager dashboard
        pass

    def test_consent_management_endpoint(self, client):
        """Test POST /api/v1/health-monitoring/consent endpoint"""
        # Test consent preferences management
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
