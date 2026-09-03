"""
Test suite for refactored GAD-7 scorer.

Tests verify the refactored scoring system works correctly
with proper separation of concerns.
"""

import pytest

from app.services.clinical.scoring.config import GAD7_CONFIG
from app.services.clinical.scoring.strategies.gad7_scorer import GAD7Scorer


class TestGAD7Config:
    """Test GAD-7 configuration"""

    def test_config_structure(self):
        """Verify GAD7_CONFIG is properly defined"""
        assert GAD7_CONFIG.name == "GAD-7"
        assert GAD7_CONFIG.items == 7
        assert GAD7_CONFIG.response_range == (0, 3)

    def test_thresholds(self):
        """Verify scoring thresholds"""
        thresholds = GAD7_CONFIG.scoring_thresholds

        # Test each threshold
        assert thresholds.get_severity(0).value == "minimal"
        assert thresholds.get_severity(4).value == "minimal"
        assert thresholds.get_severity(5).value == "mild"
        assert thresholds.get_severity(9).value == "mild"
        assert thresholds.get_severity(10).value == "moderate"
        assert thresholds.get_severity(14).value == "moderate"
        assert thresholds.get_severity(15).value == "severe"
        assert thresholds.get_severity(21).value == "severe"


class TestGAD7ScorerValidation:
    """Test input validation"""

    @pytest.fixture
    def scorer(self):
        return GAD7Scorer()

    def test_valid_response_count(self, scorer):
        """Should accept exactly 7 responses"""
        responses = {i: 0 for i in range(1, 8)}
        # Should not raise
        scorer.score(responses)

    def test_invalid_response_count_too_few(self, scorer):
        """Should reject fewer than 7 responses"""
        responses = {i: 0 for i in range(1, 6)}  # Only 5 items

        with pytest.raises(ValueError, match="requires 7 responses"):
            scorer.score(responses)

    def test_invalid_response_count_too_many(self, scorer):
        """Should reject more than 7 responses"""
        responses = {i: 0 for i in range(1, 10)}  # 9 items

        with pytest.raises(ValueError, match="requires 7 responses"):
            scorer.score(responses)

    def test_invalid_response_value_negative(self, scorer):
        """Should reject negative values"""
        responses = {i: 0 for i in range(1, 8)}
        responses[3] = -1

        with pytest.raises(ValueError, match="must be 0-3"):
            scorer.score(responses)

    def test_invalid_response_value_too_high(self, scorer):
        """Should reject values > 3"""
        responses = {i: 0 for i in range(1, 8)}
        responses[5] = 5

        with pytest.raises(ValueError, match="must be 0-3"):
            scorer.score(responses)

    def test_invalid_response_type(self, scorer):
        """Should reject non-integer responses"""
        responses = {i: 0 for i in range(1, 8)}
        responses[2] = "2"  # String instead of int

        with pytest.raises(ValueError, match="must be int"):
            scorer.score(responses)


class TestGAD7ScorerScoring:
    """Test scoring logic"""

    @pytest.fixture
    def scorer(self):
        return GAD7Scorer()

    def test_minimal_anxiety(self, scorer):
        """Score minimal anxiety (all 0s)"""
        responses = {i: 0 for i in range(1, 8)}

        result = scorer.score(responses)

        assert result.total_score == 0
        assert result.severity_level == "minimal"
        assert result.risk_level == "low"
        assert not result.crisis_alert
        assert len(result.risk_flags) == 0

    def test_mild_anxiety(self, scorer):
        """Score mild anxiety"""
        responses = {i: 1 for i in range(1, 8)}  # All 1s = score 7

        result = scorer.score(responses)

        assert result.total_score == 7
        assert result.severity_level == "mild"
        assert result.risk_level == "low"

    def test_moderate_anxiety(self, scorer):
        """Score moderate anxiety"""
        responses = {i: 2 for i in range(1, 8)}  # All 2s = score 14

        result = scorer.score(responses)

        assert result.total_score == 14
        assert result.severity_level == "moderate"
        assert result.risk_level == "moderate"

    def test_severe_anxiety(self, scorer):
        """Score severe anxiety"""
        responses = {i: 2 for i in range(1, 7)}  # Items 1-6 = 12
        responses[7] = 3  # Item 7 = 3, total = 15

        result = scorer.score(responses)

        assert result.total_score == 15
        assert result.severity_level == "severe"
        assert result.risk_level == "critical"

    def test_very_severe_anxiety(self, scorer):
        """Score very severe anxiety (all 3s)"""
        responses = {i: 3 for i in range(1, 8)}  # All 3s = score 21

        result = scorer.score(responses)

        assert result.total_score == 21
        assert result.severity_level == "severe"
        assert result.risk_level == "critical"
        assert result.crisis_alert  # Should trigger crisis alert
        assert "SEVERE_ANXIETY" in result.risk_flags
        assert "URGENT_CLINICAL_ATTENTION_RECOMMENDED" in result.risk_flags


class TestGAD7PanicSymptoms:
    """Test panic symptom detection"""

    @pytest.fixture
    def scorer(self):
        return GAD7Scorer()

    def test_high_restlessness(self, scorer):
        """Item 6 high score should trigger panic flag"""
        responses = {i: 0 for i in range(1, 8)}
        responses[6] = 3  # High restlessness

        result = scorer.score(responses)

        assert "PANIC_SYMPTOMS_DETECTED" in result.risk_flags

    def test_high_fear(self, scorer):
        """Item 7 high score should trigger panic flag"""
        responses = {i: 0 for i in range(1, 8)}
        responses[7] = 3  # High fear

        result = scorer.score(responses)

        assert "PANIC_SYMPTOMS_DETECTED" in result.risk_flags

    def test_both_panic_symptoms(self, scorer):
        """Both items 6 and 7 high should trigger panic flag"""
        responses = {i: 0 for i in range(1, 8)}
        responses[6] = 2
        responses[7] = 2

        result = scorer.score(responses)

        # Should only appear once
        assert result.risk_flags.count("PANIC_SYMPTOMS_DETECTED") == 1


class TestGAD7Interpretations:
    """Test interpretation generation"""

    @pytest.fixture
    def scorer(self):
        return GAD7Scorer()

    def test_minimal_interpretation(self, scorer):
        """Minimal anxiety interpretation"""
        responses = {i: 0 for i in range(1, 8)}
        result = scorer.score(responses)

        assert "minimal" in result.interpretation.lower()
        assert "anxiety" in result.interpretation.lower()

    def test_severe_interpretation(self, scorer):
        """Severe anxiety interpretation"""
        responses = {i: 3 for i in range(1, 8)}
        result = scorer.score(responses)

        assert "severe" in result.interpretation.lower()

    def test_boundary_scores(self, scorer):
        """Test boundary scores between severity levels"""
        # Score 4 (minimal/mild boundary)
        responses = {i: 0 for i in range(1, 8)}
        responses[1] = 1
        responses[2] = 1
        responses[3] = 1
        responses[4] = 1
        result = scorer.score(responses)
        assert result.severity_level == "minimal"

        # Score 5 (minimal/mild boundary)
        responses = {i: 0 for i in range(1, 8)}
        responses[1] = 1
        responses[2] = 1
        responses[3] = 1
        responses[4] = 1
        responses[5] = 1
        result = scorer.score(responses)
        assert result.severity_level == "mild"


class TestGAD7Recommendations:
    """Test recommendation generation"""

    @pytest.fixture
    def scorer(self):
        return GAD7Scorer()

    def test_minimal_recommendations(self, scorer):
        """Minimal anxiety recommendations"""
        responses = {i: 0 for i in range(1, 8)}
        result = scorer.score(responses)

        assert len(result.recommendations) > 0
        assert any("monitoring" in r.lower() for r in result.recommendations)
        assert any("healthy" in r.lower() for r in result.recommendations)

    def test_mild_recommendations(self, scorer):
        """Mild anxiety recommendations"""
        responses = {i: 1 for i in range(1, 8)}
        result = scorer.score(responses)

        assert len(result.recommendations) > 0
        assert any("self-help" in r.lower() for r in result.recommendations)

    def test_moderate_recommendations(self, scorer):
        """Moderate anxiety recommendations"""
        responses = {i: 2 for i in range(1, 7)}  # Score 12
        responses[7] = 0
        result = scorer.score(responses)

        assert len(result.recommendations) > 0
        assert any("clinical" in r.lower() for r in result.recommendations)
        assert any("cbt" in r.lower() for r in result.recommendations)

    def test_severe_recommendations(self, scorer):
        """Severe anxiety recommendations"""
        responses = {i: 2 for i in range(1, 7)}  # Score 12
        responses[7] = 3  # Score 15 total
        result = scorer.score(responses)

        assert len(result.recommendations) > 0
        assert any("strongly" in r.lower() for r in result.recommendations)
        assert any("psychotherapy" in r.lower() for r in result.recommendations)

    def test_crisis_recommendations(self, scorer):
        """Crisis recommendations for severe anxiety"""
        responses = {i: 3 for i in range(1, 8)}  # Score 21
        result = scorer.score(responses)

        assert result.crisis_alert
        assert any("⚠️" in r for r in result.recommendations)
        assert any("prompt" in r.lower() for r in result.recommendations)


class TestGAD7ScorerIntegration:
    """Integration tests for complete scoring flow"""

    @pytest.fixture
    def scorer(self):
        return GAD7Scorer()

    def test_complete_scoring_flow_minimal(self, scorer):
        """Test complete flow with minimal anxiety"""
        responses = {1: 0, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 0}  # Score 2

        result = scorer.score(responses)

        # Verify result structure
        assert isinstance(result.total_score, float)
        assert result.total_score == 2.0
        assert result.severity_level in ["minimal", "mild", "moderate", "severe"]
        assert result.risk_level in ["low", "moderate", "high", "critical"]
        assert isinstance(result.interpretation, str)
        assert len(result.interpretation) > 0
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
        assert isinstance(result.risk_flags, list)

    def test_complete_scoring_flow_severe_with_panic(self, scorer):
        """Test complete flow with severe anxiety and panic symptoms"""
        responses = {i: 2 for i in range(1, 8)}  # All 2s = score 14
        responses[6] = 3  # High restlessness (+1)
        responses[7] = 3  # High fear (+1)

        result = scorer.score(responses)

        assert result.total_score == 16.0  # 14 + 1 + 1
        assert result.severity_level == "severe"
        assert "PANIC_SYMPTOMS_DETECTED" in result.risk_flags
        assert "SEVERE_ANXIETY" in result.risk_flags


# Property-based tests
class TestGAD7Properties:
    """Property-based tests for GAD-7"""

    @pytest.mark.parametrize("score", range(0, 22))
    def test_all_valid_scores(self, score):
        """Every valid score should produce a valid result"""
        scorer = GAD7Scorer()

        # Distribute score across 7 items
        responses = {}
        for i in range(1, 8):
            responses[i] = min(3, score)
            score -= responses[i]

        result = scorer.score(responses)

        # Verify result structure
        assert isinstance(result.total_score, float)
        assert result.severity_level in [
            "minimal",
            "mild",
            "moderate",
            "moderately_severe",
            "severe",
        ]
        assert result.risk_level in ["low", "moderate", "high", "critical"]
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0

    def test_no_suicide_crisis_detection(self):
        """GAD-7 should not detect suicide crisis (no suicide item)"""
        scorer = GAD7Scorer()
        responses = {i: 3 for i in range(1, 8)}  # Maximum severity

        result = scorer.score(responses)

        # Should not have suicide-related flags
        assert not any("suicide" in flag.lower() for flag in result.risk_flags)
        assert not any("ideation" in flag.lower() for flag in result.risk_flags)

    def test_anxiety_focused_recommendations(self):
        """Recommendations should be anxiety-focused, not depression-focused"""
        scorer = GAD7Scorer()
        responses = {i: 2 for i in range(1, 8)}  # Moderate-severe (score 14)

        result = scorer.score(responses)

        # Should mention anxiety or stress, not depression
        recommendations_text = " ".join(result.recommendations).lower()
        assert "anxiety" in recommendations_text or "stress" in recommendations_text
        # Should NOT mention depression
        assert "depression" not in recommendations_text
