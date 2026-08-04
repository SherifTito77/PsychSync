# tests/ai/test_ai_processors_comprehensive.py
"""
Comprehensive AI Processor Testing Suite

Critical Priority: Prevents algorithmic errors in personality assessment
Business Impact: Core IP protection, assessment accuracy
ROI: 10x - Prevents costly algorithmic mistakes affecting user insights
"""

import os
import sys

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from ai.processors.mbti_processor import MBTIProcessor
from ai.processors.processors_base import PsychSyncProcessorError


class TestMBTIProcessor:
    """Comprehensive MBTI Processor Tests with Edge Cases"""

    @pytest.fixture
    def processor(self):
        """Create MBTI processor instance"""
        return MBTIProcessor()

    @pytest.fixture
    def valid_mbti_data(self):
        """Valid MBTI test data"""
        return {
            "type": "INTJ",
            "confidence": 0.85,
            "responses": [1, 2, 3, 4, 5],  # Mock response data
            "completion_time": 120.5,
        }

    # ✅ Basic Functionality Tests
    def test_process_valid_mbti_type(self, processor, valid_mbti_data):
        """Test processing of valid MBTI type"""
        result = processor.process(valid_mbti_data)

        assert result["type"] == "INTJ"
        assert result["confidence"] == 0.85
        assert "dimensions" in result
        assert "preferences" in result
        assert "description" in result
        assert "strengths" in result
        assert "blind_spots" in result
        assert result["success"] is True

    def test_all_valid_mbti_types(self, processor):
        """Test all 16 valid MBTI types"""
        valid_types = [
            "INTJ",
            "INTP",
            "ENTJ",
            "ENTP",
            "INFJ",
            "INFP",
            "ENFJ",
            "ENFP",
            "ISTJ",
            "ISFJ",
            "ESTJ",
            "ESFJ",
            "ISTP",
            "ISFP",
            "ESTP",
            "ESFP",
        ]

        for mbti_type in valid_types:
            data = {"type": mbti_type, "confidence": 0.8}
            result = processor.process(data)
            assert result["type"] == mbti_type
            assert "dimensions" in result

    # 🔥 Critical Edge Cases Tests
    def test_invalid_mbti_type_formats(self, processor):
        """Test handling of invalid MBTI type formats"""
        invalid_types = [
            "INT",  # Too short
            "INTJJ",  # Too long
            "ABC",  # Wrong letters
            "1234",  # Numbers
            "intj",  # Lowercase (should be handled)
            "",  # Empty string
            None,  # None value
        ]

        for invalid_type in invalid_types:
            data = {"type": invalid_type, "confidence": 0.8}
            result = processor.process(data)

            # Should fallback to default or handle gracefully
            assert result["type"] == "INTJ"  # Default fallback
            assert result.get("fallback", True) is not False

    def test_case_insensitive_handling(self, processor):
        """Test that MBTI types are case insensitive"""
        test_cases = [
            ("intj", "INTJ"),
            ("entp", "ENTP"),
            ("Infj", "INFJ"),
            ("esFP", "ESFP"),
        ]

        for input_type, expected_output in test_cases:
            data = {"type": input_type, "confidence": 0.8}
            result = processor.process(data)
            assert result["type"] == expected_output

    def test_boundary_confidence_values(self, processor):
        """Test extreme confidence values"""
        boundary_cases = [
            ("confidence", 0.0, 0.8),  # Should clamp to default
            ("confidence", -0.5, 0.8),  # Should clamp to default
            ("confidence", 1.0, 1.0),  # Should accept
            ("confidence", 1.5, 1.0),  # Should clamp
            ("confidence", None, 0.8),  # Should use default
        ]

        for field, invalid_value, expected_value in boundary_cases:
            data = {"type": "INTJ", field: invalid_value}
            result = processor.process(data)
            assert result["confidence"] == expected_value

    def test_missing_and_extra_fields(self, processor):
        """Test handling of missing and unexpected fields"""
        # Missing confidence
        data_missing_confidence = {"type": "ENFP"}
        result = processor.process(data_missing_confidence)
        assert result["confidence"] == 0.8  # Default value

        # Extra fields should be ignored
        data_with_extra = {
            "type": "ISTJ",
            "confidence": 0.9,
            "extra_field": "ignored",
            "another_extra": 12345,
        }
        result = processor.process(data_with_extra)
        assert result["type"] == "ISTJ"
        assert "extra_field" not in result

    # 🔢 Algorithmic Accuracy Tests
    def test_mbti_to_big_five_mapping_accuracy(self, processor):
        """Test MBTI to Big Five mapping mathematical accuracy"""
        test_mappings = [
            # Extraversion dimension
            ("INTJ", 0.25, "extraversion"),  # Introvert
            ("ENTJ", 0.75, "extraversion"),  # Extravert
            ("ISFP", 0.25, "extraversion"),  # Introvert
            ("ESFP", 0.75, "extraversion"),  # Extravert
            # Openness dimension (N vs S)
            ("INTJ", 0.75, "openness"),  # Intuitive
            ("ISTJ", 0.35, "openness"),  # Sensing
            ("ENFP", 0.75, "openness"),  # Intuitive
            ("ESFJ", 0.35, "openness"),  # Sensing
        ]

        for mbti_type, expected_value, dimension in test_mappings:
            data = {"type": mbti_type, "confidence": 0.9}
            result = processor.process(data)
            actual_value = result["dimensions"][dimension]
            assert (
                abs(actual_value - expected_value) < 0.01
            ), f"{mbti_type}: Expected {dimension}={expected_value}, got {actual_value}"

    def test_big_five_dimension_ranges(self, processor):
        """Test all Big Five dimensions are within valid ranges"""
        data = {"type": "ENFJ", "confidence": 0.8}
        result = processor.process(data)

        for dimension, value in result["dimensions"].items():
            assert (
                0.0 <= value <= 1.0
            ), f"Dimension {dimension} value {value} outside [0,1] range"

    # 🧠 Edge Case Personality Scenarios
    def test_balanced_personality_types(self, processor):
        """Test types that might be more balanced/ambiguous"""
        # These types might fall near boundaries in real assessments
        balanced_types = ["INTP", "ENFP", "ISFJ", "ESTP"]

        for mbti_type in balanced_types:
            data = {"type": mbti_type, "confidence": 0.5}  # Lower confidence
            result = processor.process(data)

            # Should still produce valid results even with low confidence
            assert result["type"] == mbti_type
            assert isinstance(result["dimensions"], dict)
            assert len(result["strengths"]) > 0
            assert len(result["blind_spots"]) > 0

    def test_extreme_personality_profiles(self, processor):
        """Test processing of extreme personality profiles"""
        extreme_types = ["INTJ", "ESFP"]  # Often considered opposites

        for mbti_type in extreme_types:
            data = {"type": mbti_type, "confidence": 0.95}  # Very high confidence
            result = processor.process(data)

            assert result["confidence"] >= 0.9
            assert len(result["strengths"]) >= 3
            assert len(result["blind_spots"]) >= 2

    # 🚨 Error Handling and Resilience
    def test_corrupted_data_handling(self, processor):
        """Test handling of corrupted or malformed data"""
        corrupted_cases = [
            {},  # Empty dict
            {"type": None},  # Null type
            {"type": ""},  # Empty type
            {"confidence": "not_a_number"},  # Invalid confidence type
            {"type": {"nested": "object"}},  # Object instead of string
            [],  # List instead of dict
            "string_instead_of_dict",  # Wrong type entirely
        ]

        for corrupted_data in corrupted_cases:
            result = processor.process(corrupted_data)
            assert "error" in result or result.get("fallback", False)
            assert result.get("confidence", 0.1) <= 0.1

    def test_performance_with_large_dataset(self, processor):
        """Test processor performance with large datasets"""
        import time

        # Simulate processing many assessments
        large_dataset = [
            {"type": mbti_type, "confidence": 0.8}
            for mbti_type in ["INTJ", "ENFP", "ISTJ", "ESFP"] * 1000
        ]

        start_time = time.time()

        for data in large_dataset:
            result = processor.process(data)
            assert result["success"] is True

        processing_time = time.time() - start_time

        # Should process 4000 assessments in under 5 seconds
        assert (
            processing_time < 5.0
        ), f"Too slow: {processing_time:.2f}s for 4000 assessments"

    # 🔍 Data Validation Tests
    def test_type_description_completeness(self, processor):
        """Test all MBTI types have complete descriptions"""
        for mbti_type in ["INTJ", "ENFP", "ISTJ", "ESFP"]:
            data = {"type": mbti_type, "confidence": 0.8}
            result = processor.process(data)

            assert result["description"] != "Unknown type"
            assert len(result["description"]) > 20
            assert isinstance(result["strengths"], list)
            assert len(result["strengths"]) >= 3
            assert isinstance(result["blind_spots"], list)
            assert len(result["blind_spots"]) >= 2

    def test_preferences_structure(self, processor):
        """Test preferences data structure consistency"""
        data = {"type": "INFJ", "confidence": 0.8}
        result = processor.process(data)

        preferences = result["preferences"]
        assert "energy" in preferences
        assert "information" in preferences
        assert "decisions" in preferences
        assert "lifestyle" in preferences

        # All preference values should be strings
        for key, value in preferences.items():
            assert isinstance(value, str)
            assert len(value) > 0

    # 📊 Statistical Validity Tests
    def test_dimension_distribution(self, processor):
        """Test statistical validity of dimension distributions"""
        all_types = [
            "INTJ",
            "INTP",
            "ENTJ",
            "ENTP",
            "INFJ",
            "INFP",
            "ENFJ",
            "ENFP",
            "ISTJ",
            "ISFJ",
            "ESTJ",
            "ESFJ",
            "ISTP",
            "ISFP",
            "ESTP",
            "ESFP",
        ]

        dimensions_by_type = {}

        for mbti_type in all_types:
            data = {"type": mbti_type, "confidence": 0.8}
            result = processor.process(data)
            dimensions_by_type[mbti_type] = result["dimensions"]

        # Test extraversion distribution (8 E types vs 8 I types)
        extraverted_dims = [
            dims["extraversion"]
            for t, dims in dimensions_by_type.items()
            if t[0] == "E"
        ]
        introverted_dims = [
            dims["extraversion"]
            for t, dims in dimensions_by_type.items()
            if t[0] == "I"
        ]

        assert all(
            e > 0.5 for e in extraverted_dims
        ), "All extraverted types should have high extraversion"
        assert all(
            i < 0.5 for i in introverted_dims
        ), "All introverted types should have low extraversion"


class TestMBTIProcessorIntegration:
    """Integration tests for MBTI processor with real-world scenarios"""

    @pytest.fixture
    def processor(self):
        return MBTIProcessor()

    def test_assessment_completion_workflow(self, processor):
        """Test complete assessment workflow from responses to personality type"""
        # Simulate user responses leading to INFP result
        assessment_data = {
            "responses": [2, 4, 1, 5, 3, 2, 4, 1],  # Mock responses
            "completion_time": 180.5,
            "question_count": 90,
            "skipped_questions": 2,
            "type": "INFP",
            "confidence": 0.78,
        }

        result = processor.process(assessment_data)

        assert result["type"] == "INFP"
        assert 0.7 <= result["confidence"] <= 0.8
        assert "mediator" in result["description"].lower()
        assert len(result["strengths"]) >= 3
        assert len(result["blind_spots"]) >= 2

    def test_team_compatibility_calculation(self, processor):
        """Test processor for team compatibility calculations"""
        team_members = ["INTJ", "ENFP", "ISTJ", "ESFP"]

        results = []
        for mbti_type in team_members:
            data = {"type": mbti_type, "confidence": 0.8}
            result = processor.process(data)
            results.append(result)

        # All should have valid Big Five dimensions for compatibility analysis
        for result in results:
            assert all(0 <= dim <= 1 for dim in result["dimensions"].values())
            assert len(result["dimensions"]) == 5  # Big Five


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
