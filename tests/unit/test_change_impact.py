"""Tests for Change Impact Predictor — vulnerability and risk calculations."""

import pytest

from app.services.change_impact_service import (
    CHANGE_STRESS_MAP,
    ChangeImpactService,
)


@pytest.fixture
def service():
    return ChangeImpactService()


# ─── Vulnerability Multiplier ──────────────────────────────────


class TestVulnerability:
    def test_high_resilience_low_multiplier(self, service):
        """Team with high readiness/safety should absorb change well."""
        bi = {"change_readiness": 90, "psychological_safety": 85, "team_health": 80}
        v = service._compute_vulnerability(bi)
        assert v < 0.8  # low multiplier

    def test_low_resilience_high_multiplier(self, service):
        """Fragile team should get hit harder."""
        bi = {"change_readiness": 15, "psychological_safety": 20, "team_health": 25}
        v = service._compute_vulnerability(bi)
        assert v > 1.5  # high multiplier

    def test_average_team_near_one(self, service):
        """50/50/50 team should have multiplier near 1.0."""
        bi = {"change_readiness": 50, "psychological_safety": 50, "team_health": 50}
        v = service._compute_vulnerability(bi)
        assert 0.9 <= v <= 1.3

    def test_missing_scores_default_to_50(self, service):
        """Empty BI should behave like average team."""
        v_empty = service._compute_vulnerability({})
        v_avg = service._compute_vulnerability(
            {"change_readiness": 50, "psychological_safety": 50, "team_health": 50}
        )
        assert v_empty == v_avg

    def test_vulnerability_range(self, service):
        """Multiplier should stay within 0.5-2.0 bounds."""
        # Perfect scores
        v_best = service._compute_vulnerability(
            {"change_readiness": 100, "psychological_safety": 100, "team_health": 100}
        )
        assert v_best == 0.5

        # Zero scores
        v_worst = service._compute_vulnerability(
            {"change_readiness": 0, "psychological_safety": 0, "team_health": 0}
        )
        assert v_worst == 2.0

    def test_change_readiness_weighted_highest(self, service):
        """change_readiness (45%) should matter more than team_health (20%)."""
        # High CR, low TH
        v1 = service._compute_vulnerability(
            {"change_readiness": 90, "psychological_safety": 50, "team_health": 20}
        )
        # Low CR, high TH
        v2 = service._compute_vulnerability(
            {"change_readiness": 20, "psychological_safety": 50, "team_health": 90}
        )
        assert v1 < v2  # high CR team is more resilient


# ─── Risk Score ────────────────────────────────────────────────


class TestRiskScore:
    def test_no_deltas_zero_risk(self, service):
        assert service._compute_risk_score({}, 1.0) == 0.0

    def test_larger_deltas_higher_risk(self, service):
        small = service._compute_risk_score({"collaboration": -5}, 1.0)
        large = service._compute_risk_score({"collaboration": -25, "culture": -20}, 1.0)
        assert large > small

    def test_risk_capped_at_100(self, service):
        massive = {
            "collaboration": -50, "culture": -50, "engagement": -50,
            "manager_health": -50, "turnover_risk": -50,
        }
        risk = service._compute_risk_score(massive, 2.0)
        assert risk <= 100.0


# ─── Recommendations ──────────────────────────────────────────


class TestRecommendations:
    def test_critical_risk_gets_readiness_assessment(self, service):
        recs = service._generate_recommendations(
            "critical",
            {"collaboration": -15, "culture": -10},
            {"change_readiness": 60},
        )
        assert any("readiness assessment" in r.lower() for r in recs)

    def test_low_change_readiness_suggests_phased_rollout(self, service):
        recs = service._generate_recommendations(
            "moderate",
            {"collaboration": -5},
            {"change_readiness": 30},
        )
        assert any("phased rollout" in r.lower() for r in recs)

    def test_collaboration_drop_suggests_sync_meetings(self, service):
        recs = service._generate_recommendations(
            "high",
            {"collaboration": -15},
            {"change_readiness": 60},
        )
        assert any("sync meetings" in r.lower() for r in recs)

    def test_turnover_risk_drop_suggests_retention(self, service):
        recs = service._generate_recommendations(
            "high",
            {"turnover_risk": -15},
            {"change_readiness": 60},
        )
        assert any("retention" in r.lower() for r in recs)

    def test_low_risk_gets_monitoring_fallback(self, service):
        recs = service._generate_recommendations(
            "low",
            {"collaboration": -3},
            {"change_readiness": 80},
        )
        assert any("monitor" in r.lower() for r in recs)


# ─── Stress Map Validation ─────────────────────────────────────


class TestStressMap:
    def test_all_change_types_have_stress_entries(self):
        expected = {"reorg", "tool_migration", "policy_shift", "leadership_change", "layoff", "expansion"}
        assert set(CHANGE_STRESS_MAP.keys()) == expected

    def test_all_impacts_are_negative(self):
        """Change stress should always be negative (it's stress, not benefit)."""
        for change_type, dimensions in CHANGE_STRESS_MAP.items():
            for dim, impact in dimensions.items():
                assert impact < 0, f"{change_type}.{dim} should be negative, got {impact}"

    def test_layoff_is_most_severe(self):
        """Layoff should have the largest total impact."""
        totals = {
            ct: sum(abs(v) for v in dims.values())
            for ct, dims in CHANGE_STRESS_MAP.items()
        }
        assert totals["layoff"] == max(totals.values())


# ─── Magnitude Scaling ─────────────────────────────────────────


class TestMagnitude:
    def test_magnitude_scales_impact(self, service):
        """Higher magnitude should produce larger deltas."""
        bi = {"change_readiness": 50, "psychological_safety": 50, "team_health": 50}
        vuln = service._compute_vulnerability(bi)

        stress = CHANGE_STRESS_MAP["reorg"]
        deltas_normal = {d: v * 1.0 * vuln for d, v in stress.items()}
        deltas_major = {d: v * 2.0 * vuln for d, v in stress.items()}

        for dim in stress:
            assert abs(deltas_major[dim]) > abs(deltas_normal[dim])
