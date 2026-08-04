"""
Tests for refactored ASRS scoring strategy.

These tests demonstrate the improved testability achieved through
the refactored architecture.
"""

import pytest

from app.services.clinical.scoring.strategies.asrs_scorer import (
    ADHDClassifier,
    ASRSScorer,
)


class TestADHDClassifier:
    """Test the ADHD classifier component in isolation"""

    def test_classify_combined_adhd(self):
        """Test classification of combined ADHD"""
        classifier = ADHDClassifier()

        # Create responses that trigger combined ADHD
        responses = {
            # Inattention items (1-9): all 4s = 36 (above threshold of 24)
            **{i: 4 for i in range(1, 10)},
            # Hyperactivity items (10-18): all 4s = 36 (above threshold of 24)
            **{i: 4 for i in range(10, 19)},
        }

        result = classifier.classify(responses)

        assert result["combined_adhd"] is True
        assert result["inattention_adhd"] is True
        assert result["hyperactive_adhd"] is True
        assert result["adhd_type"] == "combined_type"
        assert result["risk"] == "high"
        assert "severe_inattention" in result["risk_flags"]
        assert "severe_hyperactivity" in result["risk_flags"]

    def test_classify_inattentive_adhd(self):
        """Test classification of inattentive ADHD"""
        classifier = ADHDClassifier()

        # Inattention above threshold, hyperactivity below
        responses = {
            **{i: 4 for i in range(1, 10)},  # Inattention: 36
            **{i: 1 for i in range(10, 19)},  # Hyperactivity: 9
        }

        result = classifier.classify(responses)

        assert result["inattention_adhd"] is True
        assert result["hyperactive_adhd"] is False
        assert result["combined_adhd"] is False
        assert result["adhd_type"] == "inattentive_type"
        assert "inattention_adhd_indicators" in result["risk_flags"]

    def test_classify_hyperactive_adhd(self):
        """Test classification of hyperactive-impulsive ADHD"""
        classifier = ADHDClassifier()

        # Hyperactivity above threshold, inattention below
        responses = {
            **{i: 1 for i in range(1, 10)},  # Inattention: 9
            **{i: 4 for i in range(10, 19)},  # Hyperactivity: 36
        }

        result = classifier.classify(responses)

        assert result["inattention_adhd"] is False
        assert result["hyperactive_adhd"] is True
        assert result["combined_adhd"] is False
        assert result["adhd_type"] == "hyperactive_type"
        assert "hyperactivity_adhd_indicators" in result["risk_flags"]

    def test_classify_minimal_symptoms(self):
        """Test classification of minimal symptoms"""
        classifier = ADHDClassifier()

        # All scores below threshold
        responses = {
            **{i: 1 for i in range(1, 10)},  # Inattention: 9
            **{i: 1 for i in range(10, 19)},  # Hyperactivity: 9
        }

        result = classifier.classify(responses)

        assert result["combined_adhd"] is False
        assert result["adhd_type"] == "minimal_symptoms"
        assert result["risk"] == "low"
        assert len(result["risk_flags"]) == 0


class TestASRSScorer:
    """Test the ASRS scorer end-to-end"""

    def test_score_combined_adhd(self):
        """Test scoring for combined ADHD"""
        scorer = ASRSScorer()

        responses = {**{i: 4 for i in range(1, 10)}, **{i: 4 for i in range(10, 19)}}

        result = scorer.score(responses)

        assert result.total_score == 72.0
        assert result.severity_level == "combined_type"
        assert result.risk_level == "high"
        assert result.crisis_alert is False
        assert result.subscale_scores["inattention"] == 36.0
        assert result.subscale_scores["hyperactivity_impulsivity"] == 36.0
        assert len(result.recommendations) > 0
        assert "combined" in result.interpretation.lower()

    def test_score_minimal_symptoms(self):
        """Test scoring for minimal symptoms"""
        scorer = ASRSScorer()

        responses = {**{i: 1 for i in range(1, 10)}, **{i: 1 for i in range(10, 19)}}

        result = scorer.score(responses)

        assert result.total_score == 18.0
        assert result.severity_level == "minimal_symptoms"
        assert result.risk_level == "low"
        assert len(result.risk_flags) == 0

    def test_invalid_response_count(self):
        """Test that invalid response count raises error"""
        scorer = ASRSScorer()

        # Only 10 responses instead of 18
        responses = {i: 1 for i in range(1, 11)}

        with pytest.raises(ValueError, match="requires 18 responses"):
            scorer.score(responses)

    def test_invalid_response_value(self):
        """Test that invalid response values raise error"""
        scorer = ASRSScorer()

        responses = {
            **{i: 1 for i in range(1, 18)},
            18: 10,  # Invalid value (should be 0-4)
        }

        with pytest.raises(ValueError, match="must be 0-4"):
            scorer.score(responses)


class TestRecommendationEngine:
    """Test recommendation generation"""

    def test_combined_adhd_recommendations(self):
        """Test recommendations for combined ADHD"""
        from app.services.clinical.scoring.recommendations.recommendation_engine import (
            RecommendationEngine,
        )

        engine = RecommendationEngine.for_asrs()
        recommendations = engine.generate("combined_type", crisis_alert=False)

        assert len(recommendations) > 0
        assert any("clinical" in r.lower() for r in recommendations)
        assert any("evaluation" in r.lower() for r in recommendations)

    def test_minimal_symptoms_recommendations(self):
        """Test recommendations for minimal symptoms"""
        from app.services.clinical.scoring.recommendations.recommendation_engine import (
            RecommendationEngine,
        )

        engine = RecommendationEngine.for_asrs()
        recommendations = engine.generate("minimal_symptoms", crisis_alert=False)

        assert len(recommendations) > 0
        assert any("monitoring" in r.lower() for r in recommendations)
