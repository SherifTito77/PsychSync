"""
Corporate Psychology Encoding System Tests

Tests for:
- Service layer encoding calculations (CLI, TSC, EVS, CFS, PDA, RRC)
- API endpoints for metrics, signals, and interventions
- System-level analysis (NOT individual diagnostics)

All tests verify SYSTEM-LEVEL organizational psychology analysis.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.corporate_psychology import (
    CorporatePsychologyMetrics,
    InterventionCategory,
    InterventionStatus,
    RiskHorizon,
)
from app.main import app
from app.services.corporate_psychology_service import (
    CorporatePsychologyService,
    EncodingCalculation,
    InterventionRecommendation,
    SystemSignal,
)

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def psychology_service():
    return CorporatePsychologyService()


@pytest.fixture
def sample_organization_id():
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def sample_data_sources():
    """Sample data sources for encoding calculations."""
    return {
        "culture_metrics": {
            "psychological_safety_score": 65,
            "transparency_score": 60,
            "collaboration_effectiveness": 70,
            "trust_indicators": {"honesty": 65, "information_sharing": 60},
            "conflict_level": "medium",
            "trust_variance": 15,
        },
        "wellness_metrics": {
            "average_stress_level": 55,
            "average_exhaustion": 45,
            "chronic_workload_score": 60,
            "recovery_deficit": 40,
            "wellness_deterioration_rate": 30,
            "recovery_rate": 55,
            "support_quality": 60,
            "resilience_buffer": 45,
            "debt_accumulation_rate": 2.5,
            "debt_paydown_capacity": 35,
            "avg_recovery_days": 3.0,
        },
        "behavioral_metrics": {
            "handoff_efficiency": 65,
            "bottleneck_score": 50,
            "dependency_complexity": 55,
            "dependency_loop_count": 2,
            "cross_team_score": 60,
            "primary_bottleneck": "decision_making",
            "decision_latency": 40,
            "adaptation_score": 55,
        },
        "communication_metrics": {
            "daily_message_volume": 150,
            "message_complexity": 55,
            "sentiment_variance": 35,
            "response_delay_score": 45,
            "emotional_volatility": 40,
            "daily_info_items": 120,
            "processing_capacity": 100,
        },
        "team_metrics": {
            "adaptation_score": 55,
            "resource_availability": 60,
            "learning_orientation": 55,
        },
        "baseline_cli": 55.0,
        "baseline_tsc": 60.0,
        "baseline_evs": 45.0,
        "baseline_cfs": 50.0,
        "baseline_pda": 55.0,
        "baseline_rrc": 55.0,
        "data_quality": 75.0,
        "confidence": 70.0,
        "sample_size": 85,
    }


@pytest.fixture
def measurement_period():
    """Standard measurement period for tests."""
    start = date(2025, 12, 1)
    end = date(2025, 12, 31)
    return start, end


# ═══════════════════════════════════════════════════════════════
# Service Layer Tests - Encoding Calculations
# ═══════════════════════════════════════════════════════════════


class TestCognitiveLoadIndex:
    """Tests for Cognitive Load Index (CLI) calculation."""

    def test_cli_calculation_normal_conditions(
        self,
        psychology_service,
        sample_organization_id,
        measurement_period,
        sample_data_sources,
    ):
        """Test CLI calculation under normal organizational conditions."""
        start, end = measurement_period

        result = psychology_service.calculate_cognitive_load_index(
            sample_organization_id, start, end, sample_data_sources
        )

        assert isinstance(result, EncodingCalculation)
        assert 0 <= result.value <= 100
        assert result.trend in ["increasing", "stable", "decreasing"]
        assert isinstance(result.slope, float)
        assert result.confidence > 0
        assert result.drivers is not None
        assert "primary_driver" in result.drivers

    def test_cli_calculation_high_load(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test CLI calculation with high cognitive load conditions."""
        start, end = measurement_period
        high_load_data = {
            "communication_metrics": {
                "daily_message_volume": 300,  # Very high
                "message_complexity": 80,
                "daily_decisions": 60,
                "decision_stakes_score": 75,
                "daily_info_items": 250,
                "processing_capacity": 100,
            },
            "meeting_metrics": {
                "weekly_meeting_hours": 30,  # Very high
                "avg_meeting_attendees": 12,
            },
            "workload_metrics": {
                "daily_context_switches": 40,  # Very high
            },
            "baseline_cli": 50.0,
            "data_quality": 80.0,
            "confidence": 75.0,
            "sample_size": 100,
        }

        result = psychology_service.calculate_cognitive_load_index(
            sample_organization_id, start, end, high_load_data
        )

        assert result.value > 60  # Should indicate high cognitive load
        assert result.trend in ["increasing", "stable", "decreasing"]

    def test_cli_calculation_low_load(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test CLI calculation with low cognitive load conditions."""
        start, end = measurement_period
        low_load_data = {
            "communication_metrics": {
                "daily_message_volume": 50,  # Low
                "message_complexity": 30,
                "daily_decisions": 10,
                "decision_stakes_score": 30,
                "daily_info_items": 40,
                "processing_capacity": 100,
            },
            "meeting_metrics": {
                "weekly_meeting_hours": 5,  # Low
                "avg_meeting_attendees": 3,
            },
            "workload_metrics": {
                "daily_context_switches": 5,  # Low
            },
            "baseline_cli": 50.0,
            "data_quality": 80.0,
            "confidence": 75.0,
            "sample_size": 100,
        }

        result = psychology_service.calculate_cognitive_load_index(
            sample_organization_id, start, end, low_load_data
        )

        assert result.value < 50  # Should indicate low cognitive load


class TestTrustStabilityCurve:
    """Tests for Trust Stability Curve (TSC) calculation."""

    def test_tsc_calculation_normal_conditions(
        self,
        psychology_service,
        sample_organization_id,
        measurement_period,
        sample_data_sources,
    ):
        """Test TSC calculation under normal conditions."""
        start, end = measurement_period

        result = psychology_service.calculate_trust_stability_curve(
            sample_organization_id, start, end, sample_data_sources
        )

        assert isinstance(result, EncodingCalculation)
        assert 0 <= result.value <= 100
        assert result.trend in ["strengthening", "stable", "eroding"]
        assert result.drivers is not None
        assert "volatility" in result.drivers

    def test_tsc_calculation_high_trust(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test TSC calculation with high trust conditions."""
        start, end = measurement_period
        high_trust_data = {
            "culture_metrics": {
                "psychological_safety_score": 85,
                "transparency_score": 80,
                "collaboration_effectiveness": 85,
                "trust_indicators": {"honesty": 85, "information_sharing": 80},
                "trust_variance": 5,  # Low volatility
            },
            "behavioral_metrics": {
                "cross_team_score": 80,
            },
            "baseline_tsc": 70.0,
            "data_quality": 80.0,
            "confidence": 75.0,
        }

        result = psychology_service.calculate_trust_stability_curve(
            sample_organization_id, start, end, high_trust_data
        )

        assert result.value > 70  # Should indicate high trust
        assert result.drivers["volatility"] < 20  # Low volatility

    def test_tsc_calculation_low_trust(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test TSC calculation with low trust conditions."""
        start, end = measurement_period
        low_trust_data = {
            "culture_metrics": {
                "psychological_safety_score": 30,
                "transparency_score": 35,
                "collaboration_effectiveness": 35,
                "trust_indicators": {"honesty": 30, "information_sharing": 35},
                "trust_variance": 40,  # High volatility
            },
            "behavioral_metrics": {
                "cross_team_score": 30,
            },
            "baseline_tsc": 40.0,
            "data_quality": 80.0,
            "confidence": 75.0,
        }

        result = psychology_service.calculate_trust_stability_curve(
            sample_organization_id, start, end, low_trust_data
        )

        assert result.value < 50  # Should indicate low trust
        assert result.trend in ["eroding", "stable"]


class TestEmotionalVolatilitySignal:
    """Tests for Emotional Volatility Signal (EVS) calculation."""

    def test_evs_calculation_normal_conditions(
        self,
        psychology_service,
        sample_organization_id,
        measurement_period,
        sample_data_sources,
    ):
        """Test EVS calculation under normal conditions."""
        start, end = measurement_period

        result = psychology_service.calculate_emotional_volatility_signal(
            sample_organization_id, start, end, sample_data_sources
        )

        assert isinstance(result, EncodingCalculation)
        assert 0 <= result.value <= 100
        assert result.trend in ["increasing", "stable", "decreasing"]
        assert result.drivers is not None
        assert "identified_triggers" in result.drivers

    def test_evs_calculation_high_volatility(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test EVS calculation with high volatility conditions."""
        start, end = measurement_period
        high_volatility_data = {
            "wellness_metrics": {
                "average_stress_level": 80,
                "average_exhaustion": 70,
                "avg_recovery_days": 7.0,
            },
            "communication_metrics": {
                "sentiment_variance": 70,
                "emotional_volatility": 75,
            },
            "culture_metrics": {
                "conflict_level": "high",
            },
            "baseline_evs": 60.0,
            "data_quality": 80.0,
            "confidence": 75.0,
        }

        result = psychology_service.calculate_emotional_volatility_signal(
            sample_organization_id, start, end, high_volatility_data
        )

        assert result.value > 60  # Should indicate high volatility
        assert len(result.drivers["identified_triggers"]) > 0


class TestCoordinationFrictionScore:
    """Tests for Coordination Friction Score (CFS) calculation."""

    def test_cfs_calculation_normal_conditions(
        self,
        psychology_service,
        sample_organization_id,
        measurement_period,
        sample_data_sources,
    ):
        """Test CFS calculation under normal conditions."""
        start, end = measurement_period

        result = psychology_service.calculate_coordination_friction_score(
            sample_organization_id, start, end, sample_data_sources
        )

        assert isinstance(result, EncodingCalculation)
        assert 0 <= result.value <= 100
        assert result.trend in ["increasing", "stable", "decreasing"]

    def test_cfs_calculation_high_friction(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test CFS calculation with high friction conditions."""
        start, end = measurement_period
        high_friction_data = {
            "behavioral_metrics": {
                "handoff_efficiency": 30,  # Poor
                "bottleneck_score": 80,  # High
                "dependency_complexity": 75,
                "dependency_loop_count": 8,
                "primary_bottleneck": "approval_process",
                "decision_latency": 75,
            },
            "communication_metrics": {
                "response_delay_score": 70,
            },
            "baseline_cfs": 60.0,
            "data_quality": 80.0,
            "confidence": 75.0,
        }

        result = psychology_service.calculate_coordination_friction_score(
            sample_organization_id, start, end, high_friction_data
        )

        assert result.value > 60  # Should indicate high friction


class TestPsychologicalDebtAccumulation:
    """Tests for Psychological Debt Accumulation (PDA) calculation."""

    def test_pda_calculation_normal_conditions(
        self,
        psychology_service,
        sample_organization_id,
        measurement_period,
        sample_data_sources,
    ):
        """Test PDA calculation under normal conditions."""
        start, end = measurement_period

        result = psychology_service.calculate_psychological_debt_accumulation(
            sample_organization_id, start, end, sample_data_sources
        )

        assert isinstance(result, EncodingCalculation)
        assert 0 <= result.value <= 100
        assert result.trend in ["accumulating", "stable", "paying_down"]
        assert result.drivers is not None
        assert "debt_categories" in result.drivers

    def test_pda_calculation_high_debt(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test PDA calculation with high debt conditions."""
        start, end = measurement_period
        high_debt_data = {
            "wellness_metrics": {
                "chronic_workload_score": 85,
                "recovery_deficit": 75,
                "accumulated_stress": 80,
                "wellness_deterioration_rate": 65,
                "debt_accumulation_rate": 5.0,
                "debt_paydown_capacity": 20,
            },
            "culture_metrics": {
                "unresolved_conflict_score": 70,
            },
            "baseline_pda": 65.0,
            "data_quality": 80.0,
            "confidence": 75.0,
        }

        result = psychology_service.calculate_psychological_debt_accumulation(
            sample_organization_id, start, end, high_debt_data
        )

        assert result.value > 65  # Should indicate high debt
        assert result.drivers["debt_rate"] > 0


class TestRecoveryResilienceCapacity:
    """Tests for Recovery & Resilience Capacity (RRC) calculation."""

    def test_rrc_calculation_normal_conditions(
        self,
        psychology_service,
        sample_organization_id,
        measurement_period,
        sample_data_sources,
    ):
        """Test RRC calculation under normal conditions."""
        start, end = measurement_period

        result = psychology_service.calculate_recovery_resilience_capacity(
            sample_organization_id, start, end, sample_data_sources
        )

        assert isinstance(result, EncodingCalculation)
        assert 0 <= result.value <= 100
        assert result.trend in ["strengthening", "stable", "weakening"]
        assert result.drivers is not None
        assert "resilience_buffer" in result.drivers

    def test_rrc_calculation_high_resilience(
        self, psychology_service, sample_organization_id, measurement_period
    ):
        """Test RRC calculation with high resilience conditions."""
        start, end = measurement_period
        high_resilience_data = {
            "wellness_metrics": {
                "recovery_rate": 80,
                "support_quality": 75,
                "resilience_buffer": 70,
            },
            "team_metrics": {
                "adaptation_score": 75,
                "resource_availability": 80,
                "learning_orientation": 80,
            },
            "culture_metrics": {
                "learning_orientation": 80,
            },
            "baseline_rrc": 70.0,
            "data_quality": 80.0,
            "confidence": 75.0,
        }

        result = psychology_service.calculate_recovery_resilience_capacity(
            sample_organization_id, start, end, high_resilience_data
        )

        assert result.value > 65  # Should indicate high resilience
        assert result.drivers["resilience_buffer"] > 50


# ═══════════════════════════════════════════════════════════════
# Aggregate Metrics Tests
# ═══════════════════════════════════════════════════════════════


class TestAggregateMetrics:
    """Tests for aggregate organizational health metrics."""

    @pytest.fixture
    def sample_encodings(self):
        """Sample encoding calculations for testing."""
        from app.services.corporate_psychology_service import EncodingCalculation

        return {
            "cli": EncodingCalculation(
                value=60, trend="stable", slope=5.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=58, trend="stable", slope=-2.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=45, trend="stable", slope=0.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=55, trend="stable", slope=5.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=48, trend="stable", slope=-2.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=65, trend="stable", slope=0.0, confidence=75.0
            ),
        }

    def test_organizational_health_index_calculation(
        self, psychology_service, sample_encodings
    ):
        """Test organizational health index calculation."""
        health_index = psychology_service.calculate_organizational_health_index(
            cli=sample_encodings["cli"],
            tsc=sample_encodings["tsc"],
            evs=sample_encodings["evs"],
            cfs=sample_encodings["cfs"],
            pda=sample_encodings["pda"],
            rrc=sample_encodings["rrc"],
        )

        assert 0 <= health_index <= 100
        # Health should be moderate given the sample values
        assert 50 <= health_index <= 75

    def test_overall_risk_score_calculation(self, psychology_service, sample_encodings):
        """Test overall risk score calculation."""
        health_index = 62.0
        risk_score = psychology_service.calculate_overall_risk_score(
            health_index=health_index,
            encodings=sample_encodings,
        )

        assert 0 <= risk_score <= 100
        # Risk should be inverse of health
        assert risk_score > 30
        assert risk_score < 60

    def test_high_risk_conditions(self, psychology_service):
        """Test risk score under high-risk conditions."""
        from app.services.corporate_psychology_service import EncodingCalculation

        high_risk_encodings = {
            "cli": EncodingCalculation(
                value=85, trend="increasing", slope=15.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=30, trend="eroding", slope=-10.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=75, trend="increasing", slope=12.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=70, trend="increasing", slope=10.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=80, trend="accumulating", slope=15.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=30, trend="weakening", slope=-15.0, confidence=75.0
            ),
        }

        health_index = psychology_service.calculate_organizational_health_index(
            **{k: v for k, v in high_risk_encodings.items()}
        )

        risk_score = psychology_service.calculate_overall_risk_score(
            health_index=health_index,
            encodings=high_risk_encodings,
        )

        # Should indicate high risk
        assert risk_score > 50


# ═══════════════════════════════════════════════════════════════
# System Signal Generation Tests
# ═══════════════════════════════════════════════════════════════


class TestSystemSignalGeneration:
    """Tests for system signal (alert) generation."""

    @pytest.fixture
    def sample_encodings(self):
        """Sample encodings for signal generation testing."""
        from app.services.corporate_psychology_service import EncodingCalculation

        return {
            "cli": EncodingCalculation(
                value=78, trend="increasing", slope=12.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=60, trend="stable", slope=0.0, confidence=75.0
            ),
        }

    def test_signal_generation_cli_critical(
        self, psychology_service, sample_organization_id, sample_encodings
    ):
        """Test signal generation when CLI is critical."""
        health_index = 55.0
        risk_score = 45.0

        signals = psychology_service.generate_system_signals(
            sample_organization_id,
            sample_encodings,
            health_index,
            risk_score,
        )

        # Should generate a cognitive_overload signal
        cognitive_signals = [s for s in signals if s.alert_type == "cognitive_overload"]
        assert len(cognitive_signals) > 0

        signal = cognitive_signals[0]
        assert signal.severity in ["high", "critical"]
        assert signal.risk_horizon in ["immediate", "emerging", "structural"]
        assert len(signal.recommended_actions) > 0

    def test_signal_generation_all_healthy(
        self, psychology_service, sample_organization_id
    ):
        """Test signal generation when all encodings are healthy."""
        from app.services.corporate_psychology_service import EncodingCalculation

        healthy_encodings = {
            "cli": EncodingCalculation(
                value=40, trend="stable", slope=0.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=75, trend="stable", slope=0.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=35, trend="stable", slope=0.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=40, trend="stable", slope=0.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=35, trend="stable", slope=0.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=75, trend="stable", slope=0.0, confidence=75.0
            ),
        }

        health_index = 80.0
        risk_score = 20.0

        signals = psychology_service.generate_system_signals(
            sample_organization_id,
            healthy_encodings,
            health_index,
            risk_score,
        )

        # Should generate no signals
        assert len(signals) == 0


# ═══════════════════════════════════════════════════════════════
# Intervention Recommendation Tests
# ═══════════════════════════════════════════════════════════════


class TestInterventionRecommendations:
    """Tests for intervention recommendation generation."""

    @pytest.fixture
    def sample_signals(self):
        """Sample signals for intervention testing."""
        from app.services.corporate_psychology_service import SystemSignal

        return [
            SystemSignal(
                alert_type="cognitive_overload",
                severity="high",
                risk_horizon="emerging",
                summary="Elevated cognitive load",
                description="CLI is at 78/100",
                rate_of_change=12.0,
                operational_impact="Increased execution risk",
                affected_encodings=["CLI", "EVS"],
                current_value=78.0,
                baseline_value=66.0,
                probability_range="60-75%",
                recommended_actions=[
                    "Reduce meetings",
                    "Implement async communication",
                ],
                urgency="high",
            )
        ]

    @pytest.fixture
    def sample_encodings(self):
        """Sample encodings for intervention testing."""
        from app.services.corporate_psychology_service import EncodingCalculation

        return {
            "cli": EncodingCalculation(
                value=78, trend="increasing", slope=12.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=60, trend="stable", slope=0.0, confidence=75.0
            ),
        }

    def test_intervention_generation_for_cognitive_overload(
        self, psychology_service, sample_signals, sample_encodings
    ):
        """Test intervention generation for cognitive overload signal."""
        interventions = psychology_service.generate_intervention_recommendations(
            sample_signals,
            sample_encodings,
        )

        # Should generate at least one intervention
        assert len(interventions) > 0

        intervention = interventions[0]
        assert isinstance(intervention, InterventionRecommendation)
        assert intervention.category in [
            InterventionCategory.PROCESS,
            InterventionCategory.CADENCE,
            InterventionCategory.WORKLOAD,
        ]
        assert len(intervention.expected_outcomes) > 0
        assert len(intervention.business_rationale) > 0
        assert intervention.estimated_duration_weeks > 0

    def test_intervention_business_rationale(
        self, psychology_service, sample_signals, sample_encodings
    ):
        """Test that interventions include business rationale."""
        interventions = psychology_service.generate_intervention_recommendations(
            sample_signals,
            sample_encodings,
        )

        for intervention in interventions:
            # Business rationale should use business language
            assert "psychological" not in intervention.business_rationale.lower()
            assert "therapy" not in intervention.business_rationale.lower()
            # Should focus on operational outcomes
            assert any(
                term in intervention.business_rationale.lower()
                for term in [
                    "efficiency",
                    "velocity",
                    "risk",
                    "delivery",
                    "performance",
                ]
            )


# ═══════════════════════════════════════════════════════════════
# API Endpoint Tests (Integration Tests)
# ═══════════════════════════════════════════════════════════════


class TestCorporatePsychologyAPI:
    """Integration tests for Corporate Psychology API endpoints."""

    @pytest.mark.asyncio
    async def test_get_metrics_no_data(self, client, sample_organization_id):
        """Test GET /metrics when no metrics exist."""
        response = client.get(
            f"/api/v1/corporate-psychology/metrics/{sample_organization_id}"
        )

        # Should return 404 when no metrics exist
        assert response.status_code in [404, 422]  # 404 or validation error

    @pytest.mark.asyncio
    async def test_get_signals_no_data(self, client, sample_organization_id):
        """Test GET /signals when no signals exist."""
        response = client.get(
            f"/api/v1/corporate-psychology/signals/{sample_organization_id}"
        )

        # Should return empty list
        assert response.status_code in [200, 401, 422]  # May require auth

    @pytest.mark.asyncio
    async def test_get_interventions_no_data(self, client, sample_organization_id):
        """Test GET /interventions when no interventions exist."""
        response = client.get(
            f"/api/v1/corporate-psychology/interventions/{sample_organization_id}"
        )

        # Should return empty list
        assert response.status_code in [200, 401, 422]  # May require auth


# ═══════════════════════════════════════════════════════════════
# Ethical Guardrail Tests
# ═══════════════════════════════════════════════════════════════


class TestEthicalGuardrails:
    """Tests to ensure system operates at organizational level, not individual."""

    def test_no_individual_diagnostics_in_service(self, psychology_service):
        """Verify service methods don't accept individual user IDs."""
        import inspect

        # Check that service methods don't have user_id parameters
        methods_to_check = [
            "calculate_cognitive_load_index",
            "calculate_trust_stability_curve",
            "calculate_emotional_volatility_signal",
            "calculate_coordination_friction_score",
            "calculate_psychological_debt_accumulation",
            "calculate_recovery_resilience_capacity",
        ]

        for method_name in methods_to_check:
            method = getattr(psychology_service, method_name)
            sig = inspect.signature(method)

            # Should have organization_id but not user_id
            params = sig.parameters
            assert "organization_id" in params
            assert "user_id" not in params

    def test_system_level_framing_in_signals(
        self, psychology_service, sample_organization_id
    ):
        """Verify signals use system-level framing."""
        from app.services.corporate_psychology_service import EncodingCalculation

        encodings = {
            "cli": EncodingCalculation(
                value=80, trend="increasing", slope=15.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=60, trend="stable", slope=0.0, confidence=75.0
            ),
        }

        signals = psychology_service.generate_system_signals(
            sample_organization_id,
            encodings,
            55.0,  # health_index
            45.0,  # risk_score
        )

        for signal in signals:
            # Should use organizational language
            assert "people" not in signal.summary.lower()
            assert "person" not in signal.summary.lower()
            # Should use system language
            assert any(
                term in signal.summary.lower()
                for term in ["organizational", "system", "operational", "patterns"]
            )

    def test_interventions_are_structural(
        self, psychology_service, sample_organization_id
    ):
        """Verify interventions are structural, not personal."""
        from app.services.corporate_psychology_service import (
            EncodingCalculation,
            SystemSignal,
        )

        signals = [
            SystemSignal(
                alert_type="cognitive_overload",
                severity="high",
                risk_horizon="emerging",
                summary="High cognitive load",
                description="CLI elevated",
                rate_of_change=10.0,
                operational_impact="Execution risk",
                affected_encodings=["CLI"],
                current_value=78.0,
                baseline_value=66.0,
                probability_range="60-75%",
                recommended_actions=["Implement process changes"],
                urgency="high",
            )
        ]

        encodings = {
            "cli": EncodingCalculation(
                value=78, trend="increasing", slope=12.0, confidence=75.0
            ),
            "tsc": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "evs": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "cfs": EncodingCalculation(
                value=55, trend="stable", slope=0.0, confidence=75.0
            ),
            "pda": EncodingCalculation(
                value=50, trend="stable", slope=0.0, confidence=75.0
            ),
            "rrc": EncodingCalculation(
                value=60, trend="stable", slope=0.0, confidence=75.0
            ),
        }

        interventions = psychology_service.generate_intervention_recommendations(
            signals,
            encodings,
        )

        for intervention in interventions:
            # Should not recommend individual coaching
            assert "coaching" not in intervention.title.lower()
            assert "therapy" not in intervention.title.lower()
            # Should recommend structural changes
            assert any(
                term in intervention.description.lower()
                for term in [
                    "process",
                    "cadence",
                    "structural",
                    "workload",
                    "communication",
                ]
            )
