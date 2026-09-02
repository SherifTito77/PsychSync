"""Tests for Toxicity & Burnout Intelligence — composite engine, cross-contamination, and overlap detection."""

import math
from datetime import datetime

import pytest

from app.services.toxicity_burnout_engine import (
    BURNOUT_WEIGHTS,
    TOXICITY_WEIGHTS,
    BurnoutSignalInput,
    ToxicitySignalInput,
    ToxicityBurnoutResult,
    _detect_overlaps,
    _label,
    _weighted_score,
    compute_composite,
    compute_cross_contamination,
)
from app.services.git_metadata_service import (
    GitMetadataAnalyzer,
    PRMetadataRecord,
)


# ── Helpers ───────────────────────────────────────────────────

def _pr(pr_id: str, passed: int = 5, failed: int = 0, day_offset: int = 0) -> PRMetadataRecord:
    """Quick PR factory for CI quality degradation tests."""
    ts = datetime(2026, 8, 25, 10, 0)
    if day_offset:
        from datetime import timedelta
        ts = ts - timedelta(days=day_offset)
    return PRMetadataRecord(
        pr_id=pr_id,
        author_id="dev1",
        created_at=ts,
        first_review_at=ts,
        merged_at=ts,
        closed_at=ts,
        review_count=1,
        reviewer_count=1,
        comments_count=0,
        additions=50,
        deletions=10,
        files_changed=3,
        is_merged=True,
        ci_checks_passed=passed,
        ci_checks_failed=failed,
    )


# ── Labels ────────────────────────────────────────────────────


class TestLabels:
    def test_healthy(self):
        assert _label(0) == "Healthy"
        assert _label(24) == "Healthy"

    def test_monitor(self):
        assert _label(25) == "Monitor"
        assert _label(44) == "Monitor"

    def test_elevated(self):
        assert _label(45) == "Elevated"
        assert _label(69) == "Elevated"

    def test_critical(self):
        assert _label(70) == "Critical"
        assert _label(100) == "Critical"


# ── Weighted Score ────────────────────────────────────────────


class TestWeightedScore:
    def test_all_signals_present(self):
        signals = {k: 50.0 for k in BURNOUT_WEIGHTS}
        score, breakdown, count = _weighted_score(signals, BURNOUT_WEIGHTS)
        assert score == 50.0
        assert count == 6
        assert len(breakdown) == 6

    def test_no_signals(self):
        signals = {k: None for k in BURNOUT_WEIGHTS}
        score, breakdown, count = _weighted_score(signals, BURNOUT_WEIGHTS)
        assert score == 0.0
        assert count == 0

    def test_partial_signals_redistribute_weight(self):
        """With only 1 signal at 80, score should be 80 (weight redistributed to 100%)."""
        signals = {"pto_avoidance": 80.0}
        score, breakdown, count = _weighted_score(signals, BURNOUT_WEIGHTS)
        assert score == 80.0
        assert count == 1

    def test_two_signals_weighted_correctly(self):
        """pto_avoidance(25%) + login_span_expansion(20%) → redistributed to 55.6%/44.4%."""
        signals = {"pto_avoidance": 100.0, "login_span_expansion": 0.0}
        score, breakdown, count = _weighted_score(signals, BURNOUT_WEIGHTS)
        # pto_avoidance: 0.25/(0.25+0.20) = 0.556 * 100 = 55.6
        assert 55.0 <= score <= 56.0
        assert count == 2

    def test_unknown_keys_ignored(self):
        signals = {"fake_signal": 100.0, "pto_avoidance": 50.0}
        score, breakdown, count = _weighted_score(signals, BURNOUT_WEIGHTS)
        assert count == 1  # only pto_avoidance counted

    def test_weight_sums_to_one(self):
        assert abs(sum(BURNOUT_WEIGHTS.values()) - 1.0) < 0.001
        assert abs(sum(TOXICITY_WEIGHTS.values()) - 1.0) < 0.001


# ── Cross-Contamination ──────────────────────────────────────


class TestCrossContamination:
    def test_both_zero_gives_minimum(self):
        m = compute_cross_contamination(0, 0)
        assert m >= 1.0
        assert m < 1.05  # essentially no amplification

    def test_both_high_approaches_maximum(self):
        m = compute_cross_contamination(90, 90)
        assert m > 1.8  # strong amplification
        assert m <= 2.0

    def test_one_high_one_low_stays_low(self):
        """The feedback loop requires BOTH to be elevated."""
        m = compute_cross_contamination(90, 5)
        assert m < 1.3

    def test_symmetric(self):
        """Cross-contamination should be the same regardless of which is higher."""
        m1 = compute_cross_contamination(60, 30)
        m2 = compute_cross_contamination(30, 60)
        assert m1 == m2

    def test_monotonically_increasing(self):
        """As both scores rise together, multiplier should increase."""
        prev = 1.0
        for score in [10, 30, 50, 70, 90]:
            m = compute_cross_contamination(score, score)
            assert m >= prev
            prev = m

    def test_midpoint_transition(self):
        """Around the 45-45 mark, sigmoid should be near inflection."""
        m = compute_cross_contamination(45, 45)
        assert 1.4 <= m <= 1.6  # near the midpoint of 1.0-2.0

    def test_never_below_one(self):
        for b in range(0, 101, 20):
            for t in range(0, 101, 20):
                assert compute_cross_contamination(b, t) >= 1.0


# ── Overlap Detection ────────────────────────────────────────


class TestOverlapDetection:
    def test_no_overlaps_when_healthy(self):
        burnout = BurnoutSignalInput()
        toxicity = ToxicitySignalInput()
        assert _detect_overlaps(burnout, toxicity) == []

    def test_overwork_exclusion(self):
        burnout = BurnoutSignalInput(login_span_expansion=50)
        toxicity = ToxicitySignalInput(invite_exclusion=40)
        overlaps = _detect_overlaps(burnout, toxicity)
        assert len(overlaps) == 1
        assert "Overwork + Exclusion" in overlaps[0]

    def test_high_output_no_recognition(self):
        burnout = BurnoutSignalInput(after_hours_trend=50)
        toxicity = ToxicitySignalInput(reaction_asymmetry=50)
        overlaps = _detect_overlaps(burnout, toxicity)
        assert any("High output + No recognition" in o for o in overlaps)

    def test_manager_drought(self):
        burnout = BurnoutSignalInput(after_hours_trend=50)
        toxicity = ToxicitySignalInput(one_on_one_cancellation=50)
        overlaps = _detect_overlaps(burnout, toxicity)
        assert any("Manager 1:1 drought" in o for o in overlaps)

    def test_review_hostility_pto(self):
        burnout = BurnoutSignalInput(pto_avoidance=50)
        toxicity = ToxicitySignalInput(review_hostility=50)
        overlaps = _detect_overlaps(burnout, toxicity)
        assert any("Review hostility + PTO" in o for o in overlaps)

    def test_meeting_domination_attrition(self):
        burnout = BurnoutSignalInput()
        toxicity = ToxicitySignalInput(speaking_imbalance=60, attrition_clustering=40)
        overlaps = _detect_overlaps(burnout, toxicity)
        assert any("Meeting domination" in o for o in overlaps)

    def test_just_below_thresholds_no_overlap(self):
        burnout = BurnoutSignalInput(login_span_expansion=39)  # threshold is >40
        toxicity = ToxicitySignalInput(invite_exclusion=29)     # threshold is >30
        assert _detect_overlaps(burnout, toxicity) == []

    def test_multiple_overlaps_possible(self):
        burnout = BurnoutSignalInput(
            login_span_expansion=60, after_hours_trend=60, pto_avoidance=60,
        )
        toxicity = ToxicitySignalInput(
            invite_exclusion=50, reaction_asymmetry=50,
            one_on_one_cancellation=50, review_hostility=50,
        )
        overlaps = _detect_overlaps(burnout, toxicity)
        assert len(overlaps) >= 3  # at least overwork+exclusion, high output, manager drought, review+pto


# ── Composite Engine ──────────────────────────────────────────


class TestCompositeEngine:
    def test_all_healthy(self):
        result = compute_composite(BurnoutSignalInput(), ToxicitySignalInput())
        assert result.burnout_score == 0.0
        assert result.toxicity_score == 0.0
        assert result.combined_risk == 0.0
        assert result.burnout_label == "Healthy"
        assert result.toxicity_label == "Healthy"
        assert result.combined_label == "Healthy"
        assert result.overlap_patterns == []
        assert len(result.recommendations) >= 1  # "Continue monitoring"

    def test_burnout_only(self):
        burnout = BurnoutSignalInput(pto_avoidance=80, login_span_expansion=70)
        result = compute_composite(burnout, ToxicitySignalInput())
        assert result.burnout_score > 50
        assert result.toxicity_score == 0.0
        assert result.cross_contamination_multiplier < 1.05  # no loop without toxicity

    def test_toxicity_only(self):
        toxicity = ToxicitySignalInput(speaking_imbalance=90, review_hostility=80)
        result = compute_composite(BurnoutSignalInput(), toxicity)
        assert result.toxicity_score > 50
        assert result.burnout_score == 0.0

    def test_both_elevated_amplifies_combined(self):
        burnout = BurnoutSignalInput(
            pto_avoidance=70, login_span_expansion=60,
            break_deficit=65, after_hours_trend=55,
        )
        toxicity = ToxicitySignalInput(
            speaking_imbalance=75, review_hostility=70,
            reaction_asymmetry=60,
        )
        result = compute_composite(burnout, toxicity)

        base = (result.burnout_score + result.toxicity_score) / 2
        assert result.combined_risk > base  # cross-contamination amplified it
        assert result.cross_contamination_multiplier > 1.3

    def test_critical_combined_generates_urgent_recommendation(self):
        burnout = BurnoutSignalInput(
            pto_avoidance=90, login_span_expansion=85,
            break_deficit=80, calendar_fragmentation=75,
            after_hours_trend=70, quality_degradation=65,
        )
        toxicity = ToxicitySignalInput(
            speaking_imbalance=90, reaction_asymmetry=80,
            review_hostility=85, one_on_one_cancellation=75,
            invite_exclusion=70, response_asymmetry=65,
            attrition_clustering=60,
        )
        result = compute_composite(burnout, toxicity)
        assert result.combined_label == "Critical"
        assert any("URGENT" in r for r in result.recommendations)

    def test_result_fields_populated(self):
        burnout = BurnoutSignalInput(pto_avoidance=60, break_deficit=40)
        toxicity = ToxicitySignalInput(speaking_imbalance=50)
        result = compute_composite(burnout, toxicity)

        assert result.active_burnout_sources == 2
        assert result.active_toxicity_sources == 1
        assert "pto_avoidance" in result.burnout_signals
        assert "speaking_imbalance" in result.toxicity_signals
        assert isinstance(result.overlap_patterns, list)
        assert isinstance(result.recommendations, list)

    def test_combined_risk_capped_at_100(self):
        burnout = BurnoutSignalInput(
            pto_avoidance=100, login_span_expansion=100,
            break_deficit=100, calendar_fragmentation=100,
            after_hours_trend=100, quality_degradation=100,
        )
        toxicity = ToxicitySignalInput(
            speaking_imbalance=100, reaction_asymmetry=100,
            review_hostility=100, one_on_one_cancellation=100,
            invite_exclusion=100, response_asymmetry=100,
            attrition_clustering=100,
        )
        result = compute_composite(burnout, toxicity)
        assert result.combined_risk <= 100


# ── Recommendations ───────────────────────────────────────────


class TestRecommendations:
    def test_healthy_gets_continue_monitoring(self):
        result = compute_composite(BurnoutSignalInput(), ToxicitySignalInput())
        assert any("healthy" in r.lower() for r in result.recommendations)

    def test_high_pto_avoidance_gets_mandate_rec(self):
        burnout = BurnoutSignalInput(pto_avoidance=80)
        result = compute_composite(burnout, ToxicitySignalInput())
        assert any("PTO" in r for r in result.recommendations)

    def test_high_speaking_imbalance_gets_facilitation_rec(self):
        toxicity = ToxicitySignalInput(speaking_imbalance=80)
        result = compute_composite(BurnoutSignalInput(), toxicity)
        assert any("facilitation" in r.lower() or "round-robin" in r.lower() for r in result.recommendations)

    def test_overlap_generates_root_cause_rec(self):
        burnout = BurnoutSignalInput(login_span_expansion=60)
        toxicity = ToxicitySignalInput(invite_exclusion=50)
        result = compute_composite(burnout, toxicity)
        assert any("overlap" in r.lower() or "root cause" in r.lower() for r in result.recommendations)


# ── Git Quality Degradation ───────────────────────────────────


class TestQualityDegradation:
    @pytest.fixture
    def analyzer(self):
        return GitMetadataAnalyzer()

    def test_no_prs_returns_zero(self, analyzer):
        assert analyzer._quality_degradation_score([], 30) == 0.0

    def test_short_window_returns_zero(self, analyzer):
        prs = [_pr("pr1", passed=5, failed=2)]
        assert analyzer._quality_degradation_score(prs, 5) == 0.0

    def test_all_passing_low_score(self, analyzer):
        prs = [_pr(f"pr{i}", passed=10, failed=0, day_offset=i) for i in range(10)]
        score = analyzer._quality_degradation_score(prs, 30)
        assert score == 0.0

    def test_high_failure_rate(self, analyzer):
        prs = [_pr(f"pr{i}", passed=2, failed=8, day_offset=i) for i in range(10)]
        score = analyzer._quality_degradation_score(prs, 30)
        assert score > 50  # 80% failure rate should produce high score

    def test_worsening_trend_amplifies(self, analyzer):
        """More failures in second half should amplify the score."""
        # First half: low failures
        prs = [_pr(f"pr{i}", passed=9, failed=1, day_offset=20 - i) for i in range(5)]
        # Second half: high failures
        prs += [_pr(f"pr{i+5}", passed=3, failed=7, day_offset=5 - i) for i in range(5)]
        score = analyzer._quality_degradation_score(prs, 30)

        # Compare to uniform failures
        uniform_prs = [_pr(f"u{i}", passed=6, failed=4, day_offset=i) for i in range(10)]
        uniform_score = analyzer._quality_degradation_score(uniform_prs, 30)

        assert score > uniform_score  # worsening trend should score higher

    def test_no_ci_data_returns_zero(self, analyzer):
        prs = [_pr(f"pr{i}", passed=0, failed=0) for i in range(5)]
        score = analyzer._quality_degradation_score(prs, 30)
        assert score == 0.0
