"""
Comprehensive AI Assessment Framework Test
Tests all personality framework processors for bugs and performance issues
"""

import pytest
from typing import Dict, Any
from ai.processors.mbti_processor import MBTIProcessor
from ai.processors.big_five import BigFiveProcessor
from ai.processors.enneagram import EnneagramProcessor
from ai.processors.predictive_index import PredictiveIndexProcessor
from ai.processors.strengths import StrengthsProcessor
from ai.processors.social_styles import SocialStylesProcessor


class TestAssessmentProcessors:
    """Test all AI assessment processors for bugs and issues"""

    def test_mbti_processor_valid_data(self):
        """Test MBTI processor with valid data"""
        processor = MBTIProcessor()

        # Test valid MBTI types
        valid_types = ["INTJ", "ENFP", "ISTJ", "ESFJ"]

        for mbti_type in valid_types:
            data = {"type": mbti_type, "confidence": 0.85}
            result = processor._safe_process(data)

            assert result["success"] == True
            assert result["type"] == mbti_type
            assert result["confidence"] == 0.85
            assert "dimensions" in result
            assert "description" in result
            assert "strengths" in result
            assert "blind_spots" in result

    def test_mbti_processor_invalid_data(self):
        """Test MBTI processor with invalid data"""
        processor = MBTIProcessor()

        # Test invalid MBTI types
        invalid_data = [
            {"type": "INVALID"},
            {"type": "XYZ"},
            {"type": ""},  # Empty string
            {},  # Missing type
            None  # None data
        ]

        for data in invalid_data:
            result = processor._safe_process(data)

            assert result["success"] == False or result.get("fallback") == True
            assert "error" in result

    def test_big_five_processor_valid_data(self):
        """Test Big Five processor with valid data"""
        processor = BigFiveProcessor()

        # Test valid Big Five data
        data = {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.9,
            "neuroticism": 0.3,
            "confidence": 0.9
        }

        result = processor._safe_process(data)

        assert result["success"] == True
        assert "dimensions" in result
        assert "interpretations" in result
        assert "percentiles" in result
        assert "strengths" in result
        assert "development_areas" in result

        # Check dimension values are clamped correctly
        for dim, value in result["dimensions"].items():
            assert 0.0 <= value <= 1.0

    def test_big_five_processor_edge_cases(self):
        """Test Big Five processor with edge cases"""
        processor = BigFiveProcessor()

        # Test extreme values
        edge_cases = [
            {"openness": -1.0, "conscientiousness": 2.0},  # Out of bounds
            {"extraversion": "invalid", "agreeableness": None},  # Invalid types
            {}  # Empty data
        ]

        for data in edge_cases:
            result = processor._safe_process(data)
            assert "dimensions" in result or result.get("fallback") == True

    def test_processor_framework_info(self):
        """Test that all processors provide framework info"""
        processors = [
            MBTIProcessor(),
            BigFiveProcessor(),
            EnneagramProcessor(),
            PredictiveIndexProcessor(),
            StrengthsProcessor(),
            SocialStylesProcessor()
        ]

        for processor in processors:
            info = processor.get_framework_info()

            assert "name" in info
            assert "class_name" in info
            assert "description" in info
            assert isinstance(info["name"], str)
            assert len(info["name"]) > 0

    def test_mbti_big_five_mapping(self):
        """Test MBTI to Big Five dimension mapping"""
        processor = MBTIProcessor()

        # Test all MBTI types have valid mappings
        mbti_types = [
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP"
        ]

        for mbti_type in mbti_types:
            dimensions = processor._mbti_to_big_five(mbti_type)

            assert isinstance(dimensions, dict)
            assert len(dimensions) == 5

            for dim, value in dimensions.items():
                assert isinstance(value, float)
                assert 0.0 <= value <= 1.0

    def test_fallback_results_consistency(self):
        """Test that fallback results have consistent structure"""
        processor = MBTIProcessor()

        fallback = processor._fallback_result("mbti", "Test error")

        assert "error" in fallback
        assert "confidence" in fallback
        assert "dimensions" in fallback
        assert "framework" in fallback
        assert "processed_at" in fallback
        assert "fallback" in fallback

        assert fallback["confidence"] == 0.1
        assert fallback["framework"] == "mbti"
        assert fallback["fallback"] == True

    def test_confidence_ensuring(self):
        """Test confidence score handling"""
        processor = MBTIProcessor()

        # Test without confidence
        data_without_conf = {"type": "INTJ"}
        result = processor._ensure_confidence(data_without_conf)
        assert result["confidence"] == 0.8

        # Test with confidence
        data_with_conf = {"type": "INTJ", "confidence": 0.95}
        result = processor._ensure_confidence(data_with_conf)
        assert result["confidence"] == 0.95

        # Test custom default
        data_empty = {}
        result = processor._ensure_confidence(data_empty, default=0.7)
        assert result["confidence"] == 0.7

    def test_input_validation(self):
        """Test input validation across processors"""
        processors = [
            MBTIProcessor(),
            BigFiveProcessor()
        ]

        for processor in processors:
            # Valid data
            assert processor._validate_input({"type": "INTJ"}) == True
            assert processor._validate_input({"openness": 0.5}) == True

            # Invalid data
            assert processor._validate_input({}) == False
            assert processor._validate_input("") == False
            assert processor._validate_input(None) == False
            assert processor._validate_data("string") == False

    def test_error_handling_robustness(self):
        """Test that processors handle errors gracefully"""
        processor = MBTIProcessor()

        # Test with malformed data that could cause exceptions
        problematic_data = [
            {"type": ["INTJ"]},  # List instead of string
            {"type": object()},  # Object
            {"confidence": "not_a_number"},  # String confidence
            {"nested": {"invalid": "structure"}}  # Wrong structure
        ]

        for data in problematic_data:
            result = processor._safe_process(data)
            assert result is not None
            assert "error" in result or result.get("success") == True

    def test_dimension_clamping(self):
        """Test value clamping functionality"""
        processor = BigFiveProcessor()

        test_values = [
            (-1.0, 0.0),   # Below minimum
            (0.5, 0.5),    # Within range
            (1.5, 1.0),    # Above maximum
            (0.0, 0.0),    # At minimum
            (1.0, 1.0)     # At maximum
        ]

        for input_val, expected_val in test_values:
            clamped = processor._clamp_value(input_val)
            assert clamped == expected_val
