"""
Test suite for refactored PHQ-9 scorer.

These tests demonstrate how the refactored code is MUCH easier to test
because each component can be tested in isolation.
"""

import pytest

from app.services.clinical.scoring.classifiers.severity_classifier import (
    SeverityClassifier,
)
from app.services.clinical.scoring.config import CrisisThresholds, ScoringThresholds
from app.services.clinical.scoring.detectors.crisis_detector import CrisisDetector
from app.services.clinical.scoring.strategies.phq9_scorer import PHQ9Scorer


class TestScoringThresholds:
    """Test threshold configuration and classification logic"""

    def test_threshold_validation(self):
        """Thresholds must be in ascending order"""
        # Valid thresholds
        thresholds = ScoringThresholds(4, 9, 14, 19)
        thresholds.validate()  # Should not raise

        # Invalid thresholds
        with pytest.raises(ValueError):
            invalid = ScoringThresholds(20, 9, 14, 19)
            invalid.validate()

    def test_severity_classification(self):
        """Test score to severity mapping"""
        thresholds = ScoringThresholds(4, 9, 14, 19)

        assert thresholds.get_severity(0).value == "minimal"
        assert thresholds.get_severity(4).value == "minimal"
        assert thresholds.get_severity(5).value == "mild"
        assert thresholds.get_severity(10).value == "moderate"
        assert thresholds.get_severity(16).value == "moderately_severe"
        assert thresholds.get_severity(25).value == "severe"


class TestCrisisDetector:
    """Test crisis detection in isolation"""

    def test_no_crisis(self):
        """No suicide ideation = no crisis"""
        thresholds = CrisisThresholds(
            suicide_item_number=9,
            crisis_threshold=1,
            severe_crisis_threshold=2,
            requires_any_positive=True,
        )
        detector = CrisisDetector(thresholds)

        responses = {i: 0 for i in range(1, 10)}  # All zeros
        crisis_info = detector.detect(responses)

        assert not crisis_info.is_crisis
        assert not crisis_info.is_severe
        assert len(crisis_info.risk_flags) == 0

    def test_mild_crisis(self):
        """Item 9 = 1 triggers mild crisis"""
        thresholds = CrisisThresholds(
            suicide_item_number=9,
            crisis_threshold=1,
            severe_crisis_threshold=2,
            requires_any_positive=True,
        )
        detector = CrisisDetector(thresholds)

        responses = {i: 0 for i in range(1, 10)}
        responses[9] = 1  # Mild ideation

        crisis_info = detector.detect(responses)

        assert crisis_info.is_crisis
        assert not crisis_info.is_severe
        assert "SUICIDE_IDEATION_MILD" in crisis_info.risk_flags
        assert crisis_info.crisis_items[9] == 1

    def test_severe_crisis(self):
        """Item 9 >= 2 triggers severe crisis"""
        thresholds = CrisisThresholds(
            suicide_item_number=9,
            crisis_threshold=1,
            severe_crisis_threshold=2,
            requires_any_positive=True,
        )
        detector = CrisisDetector(thresholds)

        responses = {i: 0 for i in range(1, 10)}
        responses[9] = 3  # Severe ideation

        crisis_info = detector.detect(responses)

        assert crisis_info.is_crisis
        assert crisis_info.is_severe
        assert "SUICIDE_IDEATION_SEVERE" in crisis_info.risk_flags


class TestPHQ9ScorerIntegration:
    """Integration tests for the complete scoring flow"""

    @pytest.fixture
    def scorer(self):
        return PHQ9Scorer()

    def test_minimal_depression(self, scorer):
        """Score minimal depression (all 0s and 1s)"""
        responses = {i: 0 for i in range(1, 10)}

        result = scorer.score(responses)

        assert result.total_score == 0
        assert result.severity_level == "minimal"
        assert result.risk_level == "low"
        assert not result.crisis_alert
        assert len(result.risk_flags) == 0

    def test_moderate_depression(self, scorer):
        """Score moderate depression"""
        responses = {i: 1 for i in range(1, 10)}  # All 1s = score 9

        result = scorer.score(responses)

        assert result.total_score == 9
        assert result.severity_level == "mild"  # 9 is mild
        assert result.risk_level == "low"

    def test_severe_depression(self, scorer):
        """Score severe depression"""
        responses = {i: 2 for i in range(1, 10)}  # All 2s = score 18

        result = scorer.score(responses)

        assert result.total_score == 18
        assert result.severity_level == "moderately_severe"
        assert result.risk_level == "high"

    def test_severe_depression_with_crisis(self, scorer):
        """Test severe depression + suicide ideation"""
        responses = {i: 2 for i in range(1, 10)}  # Score 18
        responses[9] = 3  # Add severe suicide ideation

        result = scorer.score(responses)

        assert result.total_score == 20  # 18 + 2 more for item 9
        assert result.crisis_alert
        assert result.risk_level == "critical"
        assert "SUICIDE_IDEATION_SEVERE" in result.risk_flags
        assert "SEVERE_DEPRESSION" in result.risk_flags

    def test_invalid_response_count(self, scorer):
        """Should reject wrong number of responses"""
        responses = {i: 0 for i in range(1, 8)}  # Only 7 items

        with pytest.raises(ValueError, match="requires 9 responses"):
            scorer.score(responses)

    def test_invalid_response_value(self, scorer):
        """Should reject out-of-range values"""
        responses = {i: 0 for i in range(1, 10)}
        responses[5] = 5  # Invalid (should be 0-3)

        with pytest.raises(ValueError, match="must be 0-3"):
            scorer.score(responses)

    def test_recommendations_include_crisis_resources(self, scorer):
        """Crisis responses should include crisis resources"""
        responses = {i: 1 for i in range(1, 10)}
        responses[9] = 2  # Trigger crisis

        result = scorer.score(responses)

        assert result.crisis_alert
        assert any("988" in rec for rec in result.recommendations)
        assert any("CRISIS ALERT" in rec for rec in result.recommendations)


# Property-based tests (using hypothesis)
class TestPHQ9Properties:
    """Property-based tests to verify system behavior across all inputs"""

    @pytest.mark.parametrize("score", range(0, 28))
    def test_all_valid_scores_produce_results(self, scorer, score):
        """Every valid score should produce a valid result"""
        # Distribute score across items
        responses = {}
        for i in range(1, 10):
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
