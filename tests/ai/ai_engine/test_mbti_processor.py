# tests/app.ai/test_mbti_processor.py
"""
Unit Tests for MBTI Processor

Tests the standalone AI engine without FastAPI dependencies.
"""

import pytest

from ai.models.processing_result import ProcessingResult
from ai.processors.mbti_processor import MBTIProcessor


class TestMBTIProcessor:
    """Test MBTI assessment processor"""

    @pytest.fixture
    def processor(self):
        """Get MBTI processor instance"""
        return MBTIProcessor()

    # ========================================================================
    # VALIDATION TESTS
    # ========================================================================

    def test_validate_input_valid_data(self, processor):
        """Should accept valid input data"""
        data = {"responses": [1, 2, 3, 4, 5, 6, 7], "assessment_id": "test-123"}

        assert processor.validate_input(data) is True

    def test_validate_input_missing_responses(self, processor):
        """Should reject input without responses"""
        data = {"assessment_id": "test-123"}

        assert processor.validate_input(data) is False

    def test_validate_input_invalid_response_values(self, processor):
        """Should reject invalid response values"""
        data = {
            "responses": [1, 2, 10, 4],  # 10 is invalid
            "assessment_id": "test-123",
        }

        assert processor.validate_input(data) is False

    def test_validate_input_non_list_responses(self, processor):
        """Should reject non-list responses"""
        data = {"responses": "not a list", "assessment_id": "test-123"}

        assert processor.validate_input(data) is False

    # ========================================================================
    # PROCESSING TESTS
    # ========================================================================

    def test_process_success(self, processor):
        """Should successfully process valid MBTI responses"""
        data = {
            "responses": [1, 2, 3, 4] * 10,  # 40 responses
            "assessment_id": "test-123",
        }

        result = processor.process(data)

        assert result.is_successful()
        assert result.framework == "mbti"
        assert "type" in result.data
        assert "dimensions" in result.data
        assert result.confidence > 0.0

    def test_process_returns_four_letter_type(self, processor):
        """Should return four-letter MBTI type"""
        data = {"responses": [1, 2, 3, 4] * 10, "assessment_id": "test-123"}

        result = processor.process(data)

        assert result.is_successful()
        mbti_type = result.data["type"]
        assert len(mbti_type) == 4
        assert mbti_type.isalpha()

    def test_process_includes_all_dimensions(self, processor):
        """Should include all four MBTI dimensions"""
        data = {"responses": [1, 2, 3, 4] * 10, "assessment_id": "test-123"}

        result = processor.process(data)

        assert result.is_successful()
        dimensions = result.data["dimensions"]

        assert "EI" in dimensions
        assert "SN" in dimensions
        assert "TF" in dimensions
        assert "JP" in dimensions

    def test_process_includes_confidence(self, processor):
        """Should include confidence score"""
        data = {"responses": [1, 2, 3, 4, 5, 6, 7] * 10, "assessment_id": "test-123"}

        result = processor.process(data)

        assert result.is_successful()
        assert 0.0 <= result.confidence <= 1.0

    def test_process_includes_interpretations(self, processor):
        """Should include interpretations"""
        data = {"responses": [1, 2, 3, 4] * 10, "assessment_id": "test-123"}

        result = processor.process(data)

        assert result.is_successful()
        assert "interpretations" in result.data
        assert "type" in result.data["interpretations"]
        assert "description" in result.data["interpretations"]

    def test_process_invalid_input(self, processor):
        """Should return failure result for invalid input"""
        data = {"responses": [], "assessment_id": "test-123"}  # Empty responses

        result = processor.process(data)

        assert result.is_failed()
        assert len(result.errors) > 0

    # ========================================================================
    # DIMENSION CALCULATION TESTS
    # ========================================================================

    def test_calculate_dimensions_returns_scores(self, processor):
        """Should calculate scores for each dimension"""
        responses = [1, 2, 3, 4] * 10

        dimensions = processor._calculate_dimensions(responses)

        for dim in ["EI", "SN", "TF", "JP"]:
            assert dim in dimensions
            assert "E" in dimensions[dim] or "I" in dimensions[dim]
            assert 0.0 <= dimensions[dim]["dominant_score"] <= 1.0

    def test_determine_type_returns_valid_type(self, processor):
        """Should determine valid four-letter type"""
        dimension_scores = {
            "EI": {"E": 0.3, "I": 0.7, "dominant": "I"},
            "SN": {"S": 0.6, "N": 0.4, "dominant": "S"},
            "TF": {"T": 0.8, "F": 0.2, "dominant": "T"},
            "JP": {"J": 0.4, "P": 0.6, "dominant": "P"},
        }

        mbti_type = processor._determine_type(dimension_scores)

        assert len(mbti_type) == 4
        assert mbti_type == "ISTJ"

    def test_calculate_confidence_with_variance(self, processor):
        """Should calculate higher confidence with varied responses"""
        varied_responses = [1, 2, 3, 4, 5, 6, 7] * 10
        same_responses = [4, 4, 4, 4] * 10

        confidence_varied = processor._calculate_confidence(varied_responses)
        confidence_same = processor._calculate_confidence(same_responses)

        assert confidence_varied > confidence_same


class TestBigFiveProcessor:
    """Test Big Five assessment processor"""

    @pytest.fixture
    def processor(self):
        """Get Big Five processor instance"""
        from ai.processors.big_five import BigFiveProcessor

        return BigFiveProcessor()

    def test_validate_input_valid_data(self, processor):
        """Should accept valid Big Five input"""
        data = {
            "responses": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.5,
                "neuroticism": 0.3,
            }
        }

        assert processor.validate_input(data) is True

    def test_validate_input_missing_trait(self, processor):
        """Should reject input missing a trait"""
        data = {
            "responses": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                # Missing other traits
            }
        }

        assert processor.validate_input(data) is False

    def test_process_success(self, processor):
        """Should successfully process Big Five responses"""
        data = {
            "responses": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.5,
                "neuroticism": 0.3,
            }
        }

        result = processor.process(data)

        assert result.is_successful()
        assert result.framework == "big_five"
        assert "dimensions" in result.data

    def test_process_includes_percentiles(self, processor):
        """Should include percentile scores"""
        data = {
            "responses": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.5,
                "neuroticism": 0.3,
            }
        }

        result = processor.process(data)

        assert result.is_successful()
        assert "percentiles" in result.data

        # Check percentiles are 0-100
        for trait, percentile in result.data["percentiles"].items():
            assert 0 <= percentile <= 100

    def test_process_identifies_strengths(self, processor):
        """Should identify strengths from high scores"""
        data = {
            "responses": {
                "openness": 0.8,  # High - should be strength
                "conscientiousness": 0.4,
                "extraversion": 0.3,
                "agreeableness": 0.2,
                "neuroticism": 0.1,
            }
        }

        result = processor.process(data)

        assert result.is_successful()
        assert "strengths" in result.data

        # Openness should be identified as strength
        assert any("openness" in s.lower() for s in result.data["strengths"])

    def test_process_identifies_development_areas(self, processor):
        """Should identify development areas from low scores"""
        data = {
            "responses": {
                "openness": 0.2,  # Low - should be development area
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.8,
                "neuroticism": 0.9,
            }
        }

        result = processor.process(data)

        assert result.is_successful()
        assert "development_areas" in result.data

        # Openness should be identified as development area
        assert any("openness" in a.lower() for a in result.data["development_areas"])


class TestProcessingResult:
    """Test ProcessingResult dataclass"""

    def test_success_result(self):
        """Should create successful result"""
        result = ProcessingResult.success(
            framework="mbti", data={"type": "INTJ"}, confidence=0.95
        )

        assert result.is_successful()
        assert result.is_failed() is False
        assert result.framework == "mbti"
        assert result.data["type"] == "INTJ"
        assert result.confidence == 0.95

    def test_failure_result(self):
        """Should create failure result"""
        result = ProcessingResult.failure(framework="mbti", errors=["Invalid input"])

        assert result.is_failed()
        assert result.is_successful() is False
        assert len(result.errors) == 1
        assert result.confidence == 0.0

    def test_to_dict(self):
        """Should convert to dictionary"""
        result = ProcessingResult.success(
            framework="mbti", data={"type": "INTJ"}, confidence=0.95
        )

        result_dict = result.to_dict()

        assert result_dict["framework"] == "mbti"
        assert result_dict["status"] == "success"
        assert "data" in result_dict
        assert "processed_at" in result_dict
