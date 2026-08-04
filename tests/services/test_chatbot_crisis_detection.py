"""
Test Suite for AI Chatbot Crisis Detection

CRITICAL SAFETY TESTS:
- Crisis keyword detection (critical, high, moderate)
- False positive prevention
- Clinician notification on crisis
- PHI filtering before external API calls
- Fallback responses when OpenAI unavailable
"""

import pytest

from app.services.ai.mental_health_chatbot import MentalHealthChatbot, test_crisis_detection

# =====================================================================
# Crisis Detection Tests
# =====================================================================

class TestCrisisDetection:
    """Test crisis detection algorithm"""

    @pytest.fixture
    def chatbot(self):
        """Initialize chatbot instance"""
        return MentalHealthChatbot()

    # =================================================================
    # Critical Crisis Tests (immediate life threat)
    # =================================================================

    def test_critical_suicidal_intent_detected(self, chatbot):
        """Test detection of explicit suicidal intent"""

        test_messages = [
            "I want to kill myself",
            "I'm planning to die today",
            "I have a plan to end my life",
            "I'm ready to commit suicide right now",
            "I want to end it all",
        ]

        for message in test_messages:
            result = chatbot._detect_crisis(message)

            assert result['is_crisis'] == True, f"Failed to detect: {message}"
            assert result['severity'] == 'critical', f"Wrong severity for: {message}"
            assert len(result['keywords']) > 0
            assert result['confidence'] >= 0.95

    def test_critical_with_method_specified(self, chatbot):
        """Test detection when specific method mentioned"""

        message = "I have a bottle of pills and I'm going to take them all"
        result = chatbot._detect_crisis(message)

        assert result['is_crisis'] == True
        assert result['severity'] == 'critical'
        assert any('pill' in keyword.lower() for keyword in result['keywords'])

    def test_critical_multiple_attempts(self, chatbot):
        """Test detection of repeated suicidal references"""

        message = "I tried to kill myself last week and I'm going to try again"
        result = chatbot._detect_crisis(message)

        assert result['is_crisis'] == True
        assert result['severity'] == 'critical'

    # =================================================================
    # High Risk Tests (significant concern but not immediate)
    # =================================================================

    def test_high_thoughts_of_death(self, chatbot):
        """Test detection of passive death thoughts"""

        test_messages = [
            "I've been having thoughts about dying",
            "I wish I was dead",
            "I think about death all the time",
            "I don't want to be alive anymore",
        ]

        for message in test_messages:
            result = chatbot._detect_crisis(message)

            assert result['is_crisis'] == True, f"Failed to detect: {message}"
            assert result['severity'] == 'high', f"Wrong severity for: {message}"

    def test_high_self_harm_mentions(self, chatbot):
        """Test detection of self-harm references"""

        test_messages = [
            "I've been cutting myself",
            "I hurt myself when I'm stressed",
            "I'm thinking about self-harm",
            "I've been engaging in self-injury",
        ]

        for message in test_messages:
            result = chatbot._detect_crisis(message)

            assert result['is_crisis'] == True
            assert result['severity'] == 'high'

    # =================================================================
    # Moderate Concern Tests (concerning but not crisis)
    # =================================================================

    def test_moderate_feeling_overwhelmed(self, chatbot):
        """Test detection of overwhelming feelings"""

        test_messages = [
            "I feel completely overwhelmed",
            "Everything is too much right now",
            "I can't cope with all this stress",
            "I'm drowning in responsibilities",
        ]

        for message in test_messages:
            result = chatbot._detect_crisis(message)

            # Should detect crisis but at moderate level
            assert result['is_crisis'] == True, f"Failed to detect: {message}"
            assert result['severity'] == 'moderate', f"Wrong severity for: {message}"

    def test_moderate_feeling hopeless(self, chatbot):
        """Test detection of hopelessness"""

        test_messages = [
            "I feel hopeless",
            "Nothing matters anymore",
            "I see no point in anything",
            "Everything feels pointless",
        ]

        for message in test_messages:
            result = chatbot._detect_crisis(message)

            assert result['is_crisis'] == True
            assert result['severity'] == 'moderate'

    # =================================================================
    # False Negative Tests (catching subtle expressions)
    # =================================================================

    def test_crisis_slang_detected(self, chatbot):
        """Test detection of crisis expressed through slang"""

        test_messages = [
            "I wanna check out early",  # slang for suicide
            "Thinking about opting out",  # subtle suicidal reference
        ]

        for message in test_messages:
            result = chatbot._detect_crisis(message)

            # These should ideally be detected as at least high risk
            # May require NLP enhancement
            assert result['is_crisis'] == True or result['severity'] in ['high', 'moderate']

    # =================================================================
    # False Positive Prevention Tests
    # =================================================================

    def test_non_crisis_context_not_detected(self, chatbot):
        """Test that non-crisis contexts don't trigger alerts"""

        safe_messages = [
            "I died laughing at that movie",
            "That homework killed me",
            "I'm so dead if I fail this test",
            "I want to kill this bug in my room",
            "I'm cutting paper for art class",
            "I have butterflies in my stomach",  # anxiety metaphor
            "My stress levels are through the roof",  # normal stress
        ]

        for message in safe_messages:
            result = chatbot._detect_crisis(message)

            # Should NOT trigger crisis detection
            assert result['is_crisis'] == False, f"False positive for: {message}"

    def test_normal_mental_health_concerns(self, chatbot):
        """Test that normal concerns don't trigger crisis"""

        normal_concerns = [
            "I've been feeling anxious about my presentation",
            "I'm stressed about finals week",
            "I feel sad because my pet died",
            "I'm worried about my relationship",
        ]

        for message in normal_concerns:
            result = chatbot._detect_crisis(message)

            # Should not trigger crisis (may be normal anxiety/depression)
            assert result['is_crisis'] == False, f"False positive for: {message}"

    # =================================================================
    # Crisis Response Tests
    # =================================================================

    def test_critical_crisis_response_includes_resources(self, chatbot):
        """Test that critical crisis responses include immediate resources"""

        response = chatbot._generate_crisis_response('critical')

        assert '988' in response  # Suicide hotline
        assert '911' in response  # Emergency
        assert '741741' in response or 'Crisis Text Line' in response

    def test_high_crisis_response_shows_empathy(self, chatbot):
        """Test that high crisis responses are empathetic"""

        response = chatbot._generate_crisis_response('high')

        assert 'concerned' in response.lower()
        assert 'difficult' in response.lower()
        assert '988' in response  # Still provide crisis number

    def test_moderate_crisis_response_supportive(self, chatbot):
        """Test that moderate crisis responses are supportive"""

        response = chatbot._generate_crisis_response('moderate')

        assert 'difficult' in response.lower() or 'hard' in response.lower()
        assert 'resources' in response.lower() or 'help' in response.lower()


# =====================================================================
# PHI Filtering Tests
# =====================================================================

class TestPHIFiltering:
    """Test Protected Health Information filtering"""

    @pytest.fixture
    def chatbot(self):
        return MentalHealthChatbot()

    def test_context_contains_no_identifiable_info(self, chatbot):
        """Test that context building doesn't include PHI"""

        # This test would need to mock the database query
        # and verify the returned context doesn't contain:
        # - Names
        # - Email addresses
        # - Phone numbers
        # - Addresses
        # - Dates of birth
        # - Social security numbers

        # For now, test that context is aggregated (counts, not details)
        # This is implemented in _build_context method
        pass  # TODO: Implement with database mocking

    def test_conversation_history_filters_phi(self, chatbot):
        """Test that conversation history is filtered before sending to AI"""

        # This would verify that any messages containing PHI
        # are filtered or redacted before sending to OpenAI
        pass  # TODO: Implement with conversation mocking


# =====================================================================
# Integration Tests
# =====================================================================

class TestChatbotIntegration:
    """Integration tests for complete chatbot workflow"""

    @pytest.mark.asyncio
    async def test_crisis_workflow_end_to_end(self):
        """Test complete crisis detection workflow"""

        chatbot = MentalHealthChatbot()

        # Simulate crisis message
        crisis_message = "I want to kill myself right now"

        # This would need database mocking
        # result = await chatbot.respond(
        #     user_id="test-user-123",
        #     message=crisis_message,
        #     session_id="test-session-456"
        # )

        # Verify:
        # 1. Crisis detected
        # 2. Response includes crisis resources
        # 3. Action is 'escalate_to_human'
        # 4. Crisis alert created in database
        # 5. Clinician notification sent

        pass  # TODO: Implement with full database mocking

    @pytest.mark.asyncio
    async def test_normal_conversation_workflow(self):
        """Test normal (non-crisis) conversation flow"""

        chatbot = MentalHealthChatbot()

        normal_message = "I've been feeling anxious about my exams"

        # Would verify:
        # 1. No crisis detected
        # 2. AI response generated
        # 3. Intent classified correctly (e.g., 'anxiety_support')
        # 4. Sentiment analyzed
        # 5. Conversation stored in database

        pass  # TODO: Implement with database and OpenAI mocking


# =====================================================================
# Performance Tests
# =====================================================================

class TestChatbotPerformance:
    """Performance tests for chatbot"""

    def test_crisis_detection_speed(self):
        """Test that crisis detection completes in acceptable time"""
        import time

        chatbot = MentalHealthChatbot()

        message = "I want to kill myself"

        start_time = time.time()
        result = chatbot._detect_crisis(message)
        duration = time.time() - start_time

        assert result['is_crisis'] == True
        # Should complete in under 100ms for crisis detection
        assert duration < 0.1


# =====================================================================
# Helper Function Tests
# =====================================================================

class TestHelperFunctions:
    """Test helper functions"""

    def test_intent_classification(self):
        """Test message intent classification"""

        chatbot = MentalHealthChatbot()

        # Anxiety-related
        intent = chatbot._classify_intent("I've been feeling anxious")
        assert intent == 'anxiety_support'

        # Depression-related
        intent = chatbot._classify_intent("I feel sad and hopeless")
        assert intent == 'depression_support'

        # Stress-related
        intent = chatbot._classify_intent("I'm so stressed and overwhelmed")
        assert intent == 'stress_management'

        # General
        intent = chatbot._classify_intent("I'm not sure what I'm feeling")
        assert intent == 'general_support'

    def test_sentiment_analysis(self):
        """Test sentiment analysis"""

        chatbot = MentalHealthChatbot()

        # Positive sentiment
        sentiment = chatbot._analyze_sentiment("I'm feeling better today")
        assert sentiment > 0

        # Negative sentiment
        sentiment = chatbot._analyze_sentiment("I feel terrible and hopeless")
        assert sentiment < 0

        # Neutral
        sentiment = chatbot._analyze_sentiment("I have a meeting")
        assert sentiment == 0.0


# =====================================================================
# Safety-Critical Tests
# =====================================================================

class TestSafetyCriticalBehavior:
    """
    Safety-critical tests that MUST pass for production deployment.
    These tests verify that the chatbot never fails to detect crises.
    """

    @pytest.fixture
    def chatbot(self):
        return MentalHealthChatbot()

    @pytest.mark.safety_critical
    def test_never_misses_explicit_suicide(self, chatbot):
        """CRITICAL: Must never miss explicit suicidal statements"""

        explicit_suicide_messages = [
            "I want to kill myself",
            "I'm going to commit suicide",
            "I plan to end my life",
            "I'm ready to die",
            "I want to die",
        ]

        for message in explicit_suicide_messages:
            result = chatbot._detect_crisis(message)

            # SAFETY ASSERTION - MUST NOT FAIL
            assert result['is_crisis'] == True, \
                f"CRITICAL SAFETY FAILURE: Failed to detect crisis in '{message}'"
            assert result['severity'] == 'critical', \
                f"CRITICAL SAFETY FAILURE: Wrong severity for '{message}'"

    @pytest.mark.safety_critical
    def test_always_provides_crisis_resources(self, chatbot):
        """CRITICAL: Must always provide crisis resources when crisis detected"""

        # Test all severity levels
        for severity in ['critical', 'high', 'moderate']:
            response = chatbot._generate_crisis_response(severity)

            # SAFETY ASSERTION - Must include at least one crisis resource
            has_hotline = '988' in response
            has_text_line = '741741' in response or 'Crisis Text Line' in response
            has_emergency = '911' in response

            assert has_hotline or has_text_line or has_emergency, \
                f"CRITICAL SAFETY FAILURE: No crisis resources in {severity} response"

    @pytest.mark.safety_critical
    def test_safe_error_response_includes_resources(self, chatbot):
        """CRITICAL: Error responses must still provide crisis resources"""

        error_response = chatbot._get_safe_error_response()

        # SAFETY ASSERTION - Even errors must include crisis resources
        assert '988' in error_response or '911' in error_response, \
            "CRITICAL SAFETY FAILURE: Error response missing crisis resources"


if __name__ == "__main__":
    # Run safety-critical tests first
    pytest.main([__file__, '-m', 'safety_critical', '-v'])
