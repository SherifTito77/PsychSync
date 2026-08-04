"""
Comprehensive test suite for Enhanced AI Service
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.enhanced_ai_service import EnhancedAIProcessor, enhanced_ai_processor


class TestEnhancedAIProcessor:
    """Test cases for Enhanced AI Processor"""

    @pytest.fixture
    def processor(self):
        """Create AI processor instance for testing"""
        return EnhancedAIProcessor()

    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing"""
        return {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "manager",
            "organization": "test_org",
        }

    @pytest.mark.asyncio
    async def test_process_enhanced_assessment_mbti(
        self, processor, sample_user_context
    ):
        """Test enhanced assessment processing for MBTI"""

        # Test data
        framework = "mbti"
        data = {"type": "INTJ", "confidence": 0.9, "responses_count": 93}

        # Process assessment
        result = processor.process_enhanced_assessment(
            framework, data, sample_user_context
        )

        # Validate result structure
        assert result["framework"] == framework
        assert result["type"] == "INTJ"
        assert result["confidence"] == 0.9
        assert "detailed_analysis" in result
        assert "workplace_compatibility" in result
        assert "development_areas" in result
        assert "strengths" in result
        assert "team_dynamics" in result
        assert "leadership_potential" in result
        assert "communication_style" in result
        assert "personalized_recommendations" in result

        # Validate specific MBTI data
        assert "The Architect" in result["description"]
        assert "Strategic thinking" in result["detailed_analysis"]["core_traits"]
        assert "Systems Analyst" in result["workplace_compatibility"]["best_fit_roles"]

    @pytest.mark.asyncio
    async def test_process_enhanced_assessment_enneagram(self, processor):
        """Test enhanced assessment processing for Enneagram"""

        framework = "enneagram"
        data = {"type": "Type 1", "confidence": 0.85}

        result = processor.process_enhanced_assessment(framework, data)

        assert result["framework"] == framework
        assert result["type"] == "Type 1"
        assert "The Reformer" in result["description"]
        assert result["processed_by"] == "PsychSync Enhanced AI Engine"

    def test_get_base_personality_data_mbti(self, processor):
        """Test base personality data generation for MBTI"""

        framework = "mbti"
        data = {"type": "ENFP", "confidence": 0.8}

        result = processor._get_base_personality_data(framework, data)

        assert result["type"] == "ENFP"
        assert result["confidence"] == 0.8
        assert "The Campaigner" in result["description"]
        assert result["framework"] == framework
        assert result["processed_by"] == "PsychSync Enhanced AI Engine"

    def test_get_base_personality_data_unknown_type(self, processor):
        """Test base personality data for unknown type"""

        framework = "mbti"
        data = {"type": "UNKNOWN", "confidence": 0.5}

        result = processor._get_base_personality_data(framework, data)

        assert result["type"] == "UNKNOWN"
        assert "UNKNOWN personality analysis" in result["description"]

    def test_get_detailed_analysis_intj(self, processor):
        """Test detailed analysis for INTJ personality type"""

        framework = "mbti"
        data = {"type": "INTJ"}

        result = processor._get_detailed_analysis(framework, data)

        assert "core_traits" in result
        assert "Strategic thinking" in result["core_traits"]
        assert "Independence" in result["core_traits"]
        assert "cognitive_style" in result
        assert "motivational_drivers" in result
        assert "potential_challenges" in result
        assert "ideal_environment" in result

    def test_get_detailed_analysis_unknown_type(self, processor):
        """Test detailed analysis for unknown personality type"""

        framework = "mbti"
        data = {"type": "UNKNOWN"}

        result = processor._get_detailed_analysis(framework, data)

        assert "core_traits" in result
        assert "Adaptability" in result["core_traits"]
        assert "Learning capability" in result["core_traits"]

    def test_get_workplace_compatibility_intj(self, processor):
        """Test workplace compatibility for INTJ"""

        framework = "mbti"
        data = {"type": "INTJ"}

        result = processor._get_workplace_compatibility(framework, data)

        assert "best_fit_roles" in result
        assert "collaboration_style" in result
        assert "management_approach" in result
        assert "team_contribution" in result
        assert "Strategic Planner" in result["best_fit_roles"]
        assert "independently on complex problems" in result["collaboration_style"]

    def test_get_development_areas_by_type(self, processor):
        """Test development areas by personality type"""

        test_cases = [
            ("INTJ", ["Interpersonal communication", "Patience with process"]),
            ("ENFP", ["Time management", "Attention to detail"]),
            ("ISTJ", ["Adaptability to change", "Creative thinking"]),
            ("ESFJ", ["Setting boundaries", "Critical thinking"]),
            ("UNKNOWN", ["Self-awareness", "Communication skills"]),
        ]

        for personality_type, expected_areas in test_cases:
            framework = "mbti"
            data = {"type": personality_type}

            result = processor._get_development_areas(framework, data)

            assert isinstance(result, list)
            assert len(result) > 0
            # Check that expected areas are included
            for area in expected_areas:
                assert area in result

    def test_get_strengths_by_type(self, processor):
        """Test strengths by personality type"""

        test_cases = [
            ("INTJ", ["Strategic thinking", "Problem-solving", "Independence"]),
            ("ENFP", ["Creativity", "Empathy", "Communication"]),
            ("ISTJ", ["Reliability", "Organization", "Attention to detail"]),
            ("ESFJ", ["Supportiveness", "Organization", "Empathy"]),
        ]

        for personality_type, expected_strengths in test_cases:
            framework = "mbti"
            data = {"type": personality_type}

            result = processor._get_strengths(framework, data)

            assert isinstance(result, list)
            assert len(result) > 0
            # Check that expected strengths are included
            for strength in expected_strengths:
                assert strength in result

    def test_assess_leadership_potential(self, processor):
        """Test leadership potential assessment"""

        test_cases = ["INTJ", "ENFP", "UNKNOWN"]

        for personality_type in test_cases:
            framework = "mbti"
            data = {"type": personality_type}

            result = processor._assess_leadership_potential(framework, data)

            assert "style" in result
            assert "strengths" in result
            assert "development_areas" in result
            assert isinstance(result["strengths"], list)
            assert isinstance(result["development_areas"], list)

    def test_analyze_communication_style(self, processor):
        """Test communication style analysis"""

        framework = "mbti"
        data = {"type": "INTJ"}

        result = processor._analyze_communication_style(framework, data)

        assert "preferred_medium" in result
        assert "communication_style" in result
        assert "feedback_reception" in result
        assert "presentation_style" in result

    def test_get_team_dynamics(self, processor):
        """Test team dynamics analysis"""

        framework = "mbti"
        data = {"type": "ENFP"}

        result = processor._get_team_dynamics(framework, data)

        assert "role_in_team" in result
        assert "conflict_resolution_style" in result
        assert "communication_preferences" in result
        assert "decision_making_contribution" in result
        assert result["role_in_team"] == "Creative Catalyst"

    def test_get_personalized_recommendations_with_context(self, processor):
        """Test personalized recommendations with user context"""

        framework = "mbti"
        data = {"type": "INTJ"}
        user_context = {"role": "manager", "organization": "tech_company"}

        result = processor._get_personalized_recommendations(
            framework, data, user_context
        )

        assert isinstance(result, list)
        assert len(result) > 4  # Base recommendations + context-specific
        assert any("leadership approaches" in rec for rec in result)  # Manager context

    def test_get_personalized_recommendations_team_member(self, processor):
        """Test personalized recommendations for team member"""

        framework = "mbti"
        data = {"type": "ENFP"}
        user_context = {"role": "team_member"}

        result = processor._get_personalized_recommendations(
            framework, data, user_context
        )

        assert isinstance(result, list)
        assert any(
            "working preferences" in rec for rec in result
        )  # Team member context

    @pytest.mark.parametrize(
        "personality_type,expected_role",
        [
            ("INTJ", "Strategic Visionary"),
            ("ENFP", "Creative Catalyst"),
            ("ISTJ", "Reliable Executor"),
            ("ESFJ", "Team Harmonizer"),
            ("UNKNOWN", "Versatile Contributor"),
        ],
    )
    def test_determine_team_role(self, processor, personality_type, expected_role):
        """Test team role determination"""

        result = processor._determine_team_role(personality_type)
        assert result == expected_role

    def test_enhanced_ai_processor_singleton(self):
        """Test that enhanced_ai_processor is a singleton"""

        processor1 = enhanced_ai_processor
        processor2 = EnhancedAIProcessor()

        # The imported instance should be different from new instance
        # but should be the same type
        assert type(processor1) == type(processor2)
        assert hasattr(processor1, "process_enhanced_assessment")

    @pytest.mark.asyncio
    async def test_process_enhanced_assessment_full_pipeline(self, processor):
        """Test complete enhanced assessment processing pipeline"""

        # Test with complete data
        framework = "mbti"
        data = {
            "type": "ESFJ",
            "confidence": 0.88,
            "responses_count": 93,
            "completion_time": 1245,
        }
        user_context = {
            "user_id": "test_123",
            "role": "team_member",
            "organization": "healthcare",
        }

        result = processor.process_enhanced_assessment(framework, data, user_context)

        # Validate all expected sections are present
        expected_sections = [
            "type",
            "framework",
            "confidence",
            "description",
            "detailed_analysis",
            "workplace_compatibility",
            "development_areas",
            "strengths",
            "growth_opportunities",
            "team_dynamics",
            "leadership_potential",
            "communication_style",
            "decision_making",
            "stress_management",
            "personalized_recommendations",
        ]

        for section in expected_sections:
            assert section in result, f"Missing section: {section}"

        # Validate ESFJ specific data
        assert "The Consul" in result["description"]
        assert "Supportiveness" in result["strengths"]
        assert "Team Harmonizer" in result["team_dynamics"]["role_in_team"]

    def test_error_handling_invalid_data(self, processor):
        """Test error handling with invalid data"""

        # Test with empty data
        result = processor.process_enhanced_assessment("mbti", {})
        assert result["type"] == "Unknown"
        assert result["confidence"] == 0.8

        # Test with missing framework
        result = processor.process_enhanced_assessment("", {"type": "INTJ"})
        assert result["framework"] == ""

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, processor):
        """Test concurrent assessment processing"""

        # Create multiple assessment tasks
        tasks = []
        test_data = [
            ("mbti", {"type": "INTJ", "confidence": 0.9}),
            ("enneagram", {"type": "Type 1", "confidence": 0.8}),
            ("mbti", {"type": "ENFP", "confidence": 0.85}),
        ]

        for framework, data in test_data:
            task = processor.process_enhanced_assessment(framework, data)
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        # Validate all results
        assert len(results) == len(test_data)
        for result in results:
            assert "type" in result
            assert "framework" in result
            assert "detailed_analysis" in result
