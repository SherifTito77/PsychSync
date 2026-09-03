"""
Unit tests for clinical scoring algorithms.
Uses published clinical cutoff values as ground truth.

IMPORTANT: These tests validate safety-critical clinical logic.
Cutoffs sourced from validated publications:
  - PHQ-9: Kroenke et al. (2001)
  - GAD-7: Spitzer et al. (2006)
  - C-SSRS: Posner et al. (2011)
"""

import pytest

from app.services.clinical.scoring_algorithms import (
    CSSRSScorer,
    GAD7Scorer,
    PHQ9Scorer,
    RiskLevel,
    SeverityLevel,
    score_gad7,
    score_phq9,
)


# ============================================================================
# PHQ-9 Tests
# ============================================================================

class TestPHQ9Scorer:
    """PHQ-9 Depression Severity — cutoffs: 0-4 minimal, 5-9 mild, 10-14 moderate,
    15-19 moderately severe, 20-27 severe."""

    def _make_responses(self, total: int, item9: int = 0) -> dict:
        """Build a valid 9-item response dict with a given total."""
        per_item = total // 9
        remainder = total % 9
        responses = {i: per_item for i in range(1, 10)}
        responses[9] = item9
        # Distribute remainder across items 1-8
        for i in range(1, remainder + 1):
            responses[i] = min(3, responses[i] + 1)
        # Ensure total is correct
        responses[9] = item9
        current = sum(responses.values())
        diff = total - current
        if diff != 0:
            for i in range(1, 9):
                if diff == 0:
                    break
                add = min(diff, 3 - responses[i])
                responses[i] += add
                diff -= add
        return responses

    def test_minimal_score(self):
        responses = {i: 0 for i in range(1, 10)}
        result = PHQ9Scorer.score(responses)
        assert result.total_score == 0
        assert result.severity_level == SeverityLevel.MINIMAL.value
        assert result.risk_level == RiskLevel.LOW.value
        assert result.crisis_alert is False

    def test_mild_boundary_5(self):
        responses = {i: 0 for i in range(1, 10)}
        responses[1] = 3; responses[2] = 2  # total = 5
        result = PHQ9Scorer.score(responses)
        assert result.total_score == 5
        assert result.severity_level == SeverityLevel.MILD.value

    def test_moderate_boundary_10(self):
        responses = {i: 1 for i in range(1, 10)}
        responses[1] = 2  # total = 10
        result = PHQ9Scorer.score(responses)
        assert result.total_score == 10
        assert result.severity_level == SeverityLevel.MODERATE.value

    def test_moderately_severe_boundary_15(self):
        responses = {i: 1 for i in range(1, 10)}
        for i in range(1, 7):
            responses[i] = 2  # total = 15
        result = PHQ9Scorer.score(responses)
        assert result.total_score == 15
        assert result.severity_level == SeverityLevel.MODERATELY_SEVERE.value
        assert result.risk_level == RiskLevel.HIGH.value

    def test_severe_score_27(self):
        responses = {i: 3 for i in range(1, 10)}
        result = PHQ9Scorer.score(responses)
        assert result.total_score == 27
        assert result.severity_level == SeverityLevel.SEVERE.value
        assert result.risk_level == RiskLevel.CRITICAL.value

    def test_suicide_item9_any_positive_triggers_crisis_alert(self):
        responses = {i: 0 for i in range(1, 10)}
        responses[9] = 1  # mild suicidal ideation
        result = PHQ9Scorer.score(responses)
        assert result.crisis_alert is True
        assert "SUICIDE_IDEATION_MILD" in result.risk_flags

    def test_suicide_item9_moderate_escalates_risk(self):
        responses = {i: 0 for i in range(1, 10)}
        responses[9] = 2
        result = PHQ9Scorer.score(responses)
        assert result.crisis_alert is True
        assert result.risk_level == RiskLevel.CRITICAL.value
        assert "SUICIDE_IDEATION_MODERATE" in result.risk_flags

    def test_item9_zero_no_crisis(self):
        responses = {i: 3 for i in range(1, 10)}
        responses[9] = 0  # severe depression but no suicidal ideation
        result = PHQ9Scorer.score(responses)
        assert result.crisis_alert is False

    def test_invalid_response_count_raises(self):
        with pytest.raises(ValueError, match="PHQ-9 requires"):
            PHQ9Scorer.score({1: 0, 2: 1})  # only 2 items

    def test_invalid_response_value_raises(self):
        responses = {i: 0 for i in range(1, 10)}
        responses[1] = 4  # out of range
        with pytest.raises(ValueError, match="Response must be 0-3"):
            PHQ9Scorer.score(responses)

    def test_score_phq9_wrapper_returns_expected_keys(self):
        responses = {f"q{i}_item": 0 for i in range(1, 10)}
        result = score_phq9(responses)
        assert result["screening_type"] == "PHQ9"
        assert "total_score" in result
        assert "severity_level" in result
        assert "crisis_alert" in result


# ============================================================================
# GAD-7 Tests
# ============================================================================

class TestGAD7Scorer:
    """GAD-7 Anxiety Severity — cutoffs: 0-4 minimal, 5-9 mild, 10-14 moderate, 15+ severe."""

    def test_minimal_all_zeros(self):
        responses = {i: 0 for i in range(1, 8)}
        result = GAD7Scorer.score(responses)
        assert result.total_score == 0
        assert result.severity_level == SeverityLevel.MINIMAL.value
        assert result.crisis_alert is False

    def test_mild_score_7(self):
        responses = {i: 1 for i in range(1, 8)}
        result = GAD7Scorer.score(responses)
        assert result.total_score == 7
        assert result.severity_level == SeverityLevel.MILD.value

    def test_moderate_score_10(self):
        responses = {i: 1 for i in range(1, 8)}
        responses[1] = 3; responses[2] = 3  # total = 11
        result = GAD7Scorer.score(responses)
        assert result.total_score >= 10
        assert result.severity_level == SeverityLevel.MODERATE.value

    def test_severe_all_threes(self):
        responses = {i: 3 for i in range(1, 8)}
        result = GAD7Scorer.score(responses)
        assert result.total_score == 21
        assert result.severity_level == SeverityLevel.SEVERE.value
        assert result.risk_level == RiskLevel.HIGH.value

    def test_invalid_item_count_raises(self):
        with pytest.raises(ValueError):
            GAD7Scorer.score({1: 0})

    def test_score_gad7_wrapper(self):
        responses = {f"q{i}_item": 0 for i in range(1, 8)}
        result = score_gad7(responses)
        assert result["screening_type"] == "GAD7"
        assert "total_score" in result


# ============================================================================
# C-SSRS Tests (Columbia Suicide Severity Rating Scale)
# ============================================================================

class TestCSSRSScorer:
    """C-SSRS uses q1-q5 for ideation levels (1=passive, 4+=plan+intent)
    and q11 for recent attempt. ANY positive ideation triggers crisis alert."""

    def _no_ideation(self) -> dict:
        return {f"q{i}": False for i in range(1, 13)}

    def test_no_ideation_no_crisis(self):
        result = CSSRSScorer.score(self._no_ideation())
        assert result.crisis_alert is False
        assert result.risk_level == RiskLevel.LOW.value

    def test_passive_ideation_q1_triggers_alert(self):
        responses = self._no_ideation()
        responses["q1"] = True  # passive ideation level 1
        result = CSSRSScorer.score(responses)
        assert result.crisis_alert is True
        assert result.risk_level == RiskLevel.MODERATE.value

    def test_active_ideation_q3_is_high_risk(self):
        responses = self._no_ideation()
        responses["q1"] = True
        responses["q2"] = True
        responses["q3"] = True  # ideation_level = 3 → HIGH
        result = CSSRSScorer.score(responses)
        assert result.crisis_alert is True
        assert result.risk_level == RiskLevel.HIGH.value

    def test_plan_and_intent_q4_is_critical(self):
        responses = self._no_ideation()
        responses["q1"] = True
        responses["q2"] = True
        responses["q3"] = True
        responses["q4"] = True  # ideation_level = 4 → CRITICAL
        result = CSSRSScorer.score(responses)
        assert result.crisis_alert is True
        assert result.risk_level == RiskLevel.CRITICAL.value

    def test_recent_attempt_q11_always_critical(self):
        responses = self._no_ideation()
        responses["q11"] = True  # recent suicide attempt
        result = CSSRSScorer.score(responses)
        assert result.crisis_alert is True
        assert result.risk_level == RiskLevel.CRITICAL.value

    def test_result_has_required_fields(self):
        result = CSSRSScorer.score(self._no_ideation())
        assert hasattr(result, "total_score")
        assert hasattr(result, "severity_level")
        assert hasattr(result, "risk_level")
        assert hasattr(result, "crisis_alert")
        assert hasattr(result, "recommendations")


# ============================================================================
# Re-export consistency: ai/clinical re-exports must match services/clinical
# ============================================================================

class TestReExportConsistency:
    """Verify ai/clinical/scoring_algorithms re-exports the same objects."""

    def test_phq9_scorer_is_same_object(self):
        from app.ai.clinical.scoring_algorithms import PHQ9Scorer as AIPHQScorer
        from app.services.clinical.scoring_algorithms import PHQ9Scorer as SvcPHQScorer
        assert AIPHQScorer is SvcPHQScorer

    def test_gad7_scorer_is_same_object(self):
        from app.ai.clinical.scoring_algorithms import GAD7Scorer as AIGADScorer
        from app.services.clinical.scoring_algorithms import GAD7Scorer as SvcGADScorer
        assert AIGADScorer is SvcGADScorer

    def test_cssrs_scorer_is_same_object(self):
        from app.ai.clinical.scoring_algorithms import CSSRSScorer as AICSSRSScorer
        from app.services.clinical.scoring_algorithms import CSSRSScorer as SvcCSSRSScorer
        assert AICSSRSScorer is SvcCSSRSScorer
