# tests/integration/test_corporate_integrations.py
"""
Integration tests for corporate data source integrations
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.integrations.calendar_integration import (
    CalendarEvent,
    CalendarMetadataExtractor,
    GoogleCalendarAPIIntegration,
    MeetingType,
    OutlookCalendarAPIIntegration,
)
from app.integrations.email_integration import (
    EmailMetadata,
    EmailMetadataExtractor,
    GmailAPIIntegration,
    OutlookAPIIntegration,
)
from app.integrations.slack_integration import (
    SlackAPIIntegration,
    SlackMessage,
    SlackMetadataExtractor,
)
from app.services.behavioral_pipeline import (
    BehavioralInsight,
    BehavioralPipelineOrchestrator,
    BehavioralProfile,
    InsightCategory,
    InsightSeverity,
)


class TestEmailIntegration:
    """Test email integration functionality"""

    @pytest.fixture
    def email_extractor(self):
        """Create email metadata extractor"""
        db = Mock()
        return EmailMetadataExtractor(db, "testcompany.com")

    @pytest.fixture
    def sample_gmail_message(self):
        """Sample Gmail API message"""
        return {
            "id": "123456789",
            "threadId": "987654321",
            "historyId": "1234",
            "internalDate": str(int(datetime.now().timestamp() * 1000)),
            "payload": {
                "headers": [
                    {"name": "From", "value": "john@example.com"},
                    {"name": "To", "value": "jane@testcompany.com"},
                    {
                        "name": "Subject",
                        "value": "URGENT: Project deadline approaching",
                    },
                    {"name": "Date", "value": "Mon, 14 Jan 2025 10:30:00 +0000"},
                ]
            },
        }

    def test_extract_from_gmail_message(self, email_extractor, sample_gmail_message):
        """Test Gmail message extraction"""
        metadata = email_extractor.extract_from_gmail_message(
            sample_gmail_message, user_id=1, connection_id=1, organization_id=1
        )

        assert metadata is not None
        assert metadata.message_id == "123456789"
        assert metadata.sender == "john@example.com"
        assert metadata.subject_length > 0
        assert metadata.is_urgent is True  # "URGENT" in subject
        assert metadata.urgency_level == "critical"

    def test_calculate_behavioral_signals(self, email_extractor):
        """Test behavioral signal calculation"""
        # Create sample emails
        emails = [
            EmailMetadata(
                message_id=f"msg_{i}",
                thread_id=f"thread_{i}",
                sender="sender@example.com",
                recipients=["recipient@testcompany.com"],
                cc_recipients=[],
                bcc_recipients=[],
                subject_length=20,
                sent_at=datetime.now() - timedelta(hours=i * 2),
                received_at=datetime.now() - timedelta(hours=i * 2),
                has_attachments=False,
                attachment_count=0,
                is_external=True,
                is_urgent=False,
                urgency_level="low",
                thread_size=1,
                in_reply_to=None,
                message_count_in_thread=1,
                response_time_seconds=None,
                is_after_hours=(i % 5 == 0),  # Every 5th email after hours
                is_weekend=(i % 7 == 0),  # Some on weekends
                hour_of_day=10 + i,
                day_of_week=i % 7,
                organization_id=1,
                user_id=1,
                connection_id=1,
            )
            for i in range(1, 101)  # 100 emails
        ]

        signals = email_extractor.calculate_behavioral_signals(
            emails, time_window_days=30
        )

        assert signals["communication_frequency"] > 0
        assert "after_hours_percentage" in signals
        assert "weekend_work_percentage" in signals
        assert "work_life_imbalance_score" in signals
        assert 0 <= signals["work_life_imbalance_score"] <= 1

    def test_detect_burnout_indicators(self, email_extractor):
        """Test burnout indicator detection"""
        signals = {
            "communication_frequency": 200,
            "after_hours_percentage": 35,
            "weekend_work_percentage": 25,
            "work_life_imbalance_score": 0.8,
            "communication_overload": True,
        }

        indicators = email_extractor.detect_burnout_indicators(signals)

        assert len(indicators) > 0
        assert any("after-hours" in ind.lower() for ind in indicators)
        assert any("weekend" in ind.lower() for ind in indicators)

    def test_urgency_analysis(self, email_extractor):
        """Test urgency keyword detection"""
        test_cases = [
            ("URGENT: Server down", ("critical", True)),
            ("Action Required: Review", ("high", True)),
            ("FYI: Update", ("medium", False)),
            ("Hello", ("low", False)),
        ]

        for subject, (expected_level, expected_urgent) in test_cases:
            level, is_urgent = email_extractor._analyze_urgency(subject)
            assert level == expected_level, f"Failed for subject: {subject}"
            assert is_urgent == expected_urgent, f"Failed for subject: {subject}"


class TestCalendarIntegration:
    """Test calendar integration functionality"""

    @pytest.fixture
    def calendar_extractor(self):
        """Create calendar metadata extractor"""
        return CalendarMetadataExtractor("testcompany.com")

    @pytest.fixture
    def sample_google_event(self):
        """Sample Google Calendar event"""
        return {
            "id": "event123",
            "status": "confirmed",
            "summary": "Team Standup",
            "start": {"dateTime": "2025-01-14T10:00:00Z"},
            "end": {"dateTime": "2025-01-14T10:30:00Z"},
            "organizer": {"email": "organizer@testcompany.com"},
            "attendees": [
                {"email": "attendee1@testcompany.com", "responseStatus": "accepted"},
                {"email": "attendee2@testcompany.com", "responseStatus": "accepted"},
            ],
        }

    def test_extract_from_google_event(self, calendar_extractor, sample_google_event):
        """Test Google Calendar event extraction"""
        event = calendar_extractor.extract_from_google_event(
            sample_google_event,
            user_email="organizer@testcompany.com",
            user_id=1,
            connection_id=1,
            organization_id=1,
        )

        assert event is not None
        assert event.event_id == "event123"
        assert event.title == "Team Standup"
        assert event.duration_minutes == 30
        assert event.attendees_count == 2
        assert event.is_organizer is True

    def test_calculate_behavioral_signals(self, calendar_extractor):
        """Test behavioral signal calculation"""
        # Create sample events
        events = [
            CalendarEvent(
                event_id=f"event_{i}",
                title="Meeting",
                start_time=datetime.now().replace(hour=10, minute=0)
                + timedelta(days=i),
                end_time=datetime.now().replace(hour=10, minute=30) + timedelta(days=i),
                duration_minutes=30,
                attendees_count=5,
                is_recurring=True,
                is_all_day=False,
                meeting_type=MeetingType.TEAM_MEETING,
                is_after_hours=False,
                is_weekend=False,
                is_back_to_back=(i % 2 == 0),
                gap_minutes_before=15 if i > 0 else 0,
                gap_minutes_after=15,
                organizer_email="organizer@testcompany.com",
                is_organizer=True,
                organization_id=1,
                user_id=1,
                connection_id=1,
            )
            for i in range(1, 31)  # 30 events
        ]

        signals = calendar_extractor.calculate_behavioral_signals(
            events, time_window_days=30
        )

        assert signals["total_meeting_hours"] > 0
        assert "meeting_load_percentage" in signals
        assert "back_to_back_percentage" in signals
        assert signals["focus_time_hours_per_day"] >= 0

    def test_detect_burnout_indicators(self, calendar_extractor):
        """Test burnout indicator detection"""
        signals = {
            "meeting_load_percentage": 85,
            "back_to_back_percentage": 75,
            "focus_time_hours_per_day": 0.5,
            "after_hours_meetings_count": 12,
            "meeting_marathons": 6,
        }

        indicators = calendar_extractor.detect_burnout_indicators(signals)

        assert len(indicators) > 0
        assert any("meeting load" in ind.lower() for ind in indicators)
        assert any("back-to-back" in ind.lower() for ind in indicators)

    def test_meeting_classification(self, calendar_extractor):
        """Test meeting type classification"""
        test_cases = [
            ("1:1 with John", 2, 30, MeetingType.ONE_ON_ONE),
            ("Team Standup", 10, 15, MeetingType.TEAM_MEETING),
            ("All Hands: Q1 Update", 50, 60, MeetingType.ALL_HANDS),
            ("Focus Time", 1, 120, MeetingType.FOCUS_TIME),
        ]

        for title, attendees, duration, expected_type in test_cases:
            meeting_type = calendar_extractor._classify_meeting_type(
                title, attendees, duration
            )
            assert meeting_type == expected_type, f"Failed for title: {title}"


class TestSlackIntegration:
    """Test Slack integration functionality"""

    @pytest.fixture
    def slack_extractor(self):
        """Create Slack metadata extractor"""
        return SlackMetadataExtractor()

    @pytest.fixture
    def sample_slack_message(self):
        """Sample Slack API message"""
        return {
            "client_msg_id": "client_msg_id_123",
            "type": "message",
            "ts": "1705251600.123456",
            "user": "U123456",
            "text": "Hello team! 👋",
            "reactions": [
                {"name": "thumbsup", "count": 3, "users": ["U1", "U2", "U3"]}
            ],
        }

    def test_extract_from_slack_message(self, slack_extractor, sample_slack_message):
        """Test Slack message extraction"""
        message = slack_extractor.extract_from_slack_message(
            sample_slack_message,
            channel_name="general",
            user_id="U123456",
            connection_id=1,
            organization_id=1,
        )

        assert message is not None
        assert message.message_id == sample_slack_message["ts"]
        assert message.user_id == "U123456"
        assert message.channel_name == "general"
        assert message.reaction_count == 3

    def test_calculate_behavioral_signals(self, slack_extractor):
        """Test behavioral signal calculation"""
        # Create sample messages
        messages = [
            SlackMessage(
                message_id=f"msg_{i}",
                channel_id=f"channel_{i % 5}",  # 5 different channels
                channel_name=f"channel_{i % 5}",
                user_id="U123456",
                timestamp=datetime.now() - timedelta(hours=i),
                message_type="message",
                reply_count=i % 3,
                reaction_count=i % 5,
                has_mentions=(i % 3 == 0),
                has_links=(i % 4 == 0),
                has_attachments=False,
                word_count=10 + i,
                emoji_count=i % 3,
                is_after_hours=(i % 5 == 0),
                is_weekend=(i % 7 == 0),
                hour_of_day=10 + (i % 8),
                day_of_week=i % 7,
                organization_id=1,
                connection_id=1,
            )
            for i in range(1, 51)  # 50 messages
        ]

        signals = slack_extractor.calculate_behavioral_signals(
            messages, time_window_days=30
        )

        assert signals["message_frequency_per_day"] > 0
        assert "channel_diversity_score" in signals
        assert "social_interaction_score" in signals
        assert 0 <= signals["social_interaction_score"] <= 1

    def test_detect_burnout_indicators(self, slack_extractor):
        """Test burnout indicator detection"""
        signals = {
            "message_frequency_per_day": 250,
            "after_hours_message_percentage": 35,
            "weekend_message_percentage": 25,
            "burnout_risk_score": 0.8,
            "communication_overload": True,
        }

        indicators = slack_extractor.detect_burnout_indicators(signals)

        assert len(indicators) > 0
        assert any(
            "after-hours" in ind.lower() or "slack" in ind.lower() for ind in indicators
        )


class TestBehavioralPipeline:
    """Test behavioral pipeline orchestrator"""

    @pytest.fixture
    def pipeline_orchestrator(self):
        """Create pipeline orchestrator"""
        db = Mock()
        return BehavioralPipelineOrchestrator(db, "testcompany.com")

    @pytest.mark.asyncio
    async def test_generate_behavioral_profile(self, pipeline_orchestrator):
        """Test behavioral profile generation"""
        # Mock credentials
        credentials = {
            "gmail": {"access_token": "mock_token"},
            "google_calendar": {"access_token": "mock_token"},
            "slack": {"bot_token": "mock_bot_token"},
        }

        # Mock API responses
        with patch(
            "app.integrations.email_integration.GmailAPIIntegration.fetch_recent_emails"
        ) as mock_emails:
            mock_emails.return_value = []

            with patch(
                "app.integrations.calendar_integration.GoogleCalendarAPIIntegration.fetch_events"
            ) as mock_events:
                mock_events.return_value = []

                with patch(
                    "app.integrations.slack_integration.SlackAPIIntegration.fetch_all_messages"
                ) as mock_messages:
                    mock_messages.return_value = {}

                    profile = await pipeline_orchestrator.generate_behavioral_profile(
                        user_id=1,
                        organization_id=1,
                        credentials=credentials,
                        time_window_days=30,
                    )

                    assert profile is not None
                    assert profile.user_id == 1
                    assert profile.organization_id == 1
                    assert 0 <= profile.burnout_risk_score <= 1
                    assert 0 <= profile.engagement_score <= 1
                    assert 0 <= profile.work_life_balance_score <= 1
                    assert profile.confidence_level >= 0

    def test_risk_score_calculations(self, pipeline_orchestrator):
        """Test risk score calculation logic"""
        all_signals = {
            "email": {"work_life_imbalance_score": 0.8, "communication_overload": True},
            "calendar": {
                "meeting_load_percentage": 85,
                "focus_time_hours_per_day": 0.5,
            },
            "slack": {"burnout_risk_score": 0.7},
        }

        burnout_risk = pipeline_orchestrator._calculate_burnout_risk(all_signals)
        wlb_score = pipeline_orchestrator._calculate_work_life_balance(all_signals)
        engagement = pipeline_orchestrator._calculate_engagement(all_signals)

        assert 0 <= burnout_risk <= 1
        assert 0 <= wlb_score <= 1
        assert 0 <= engagement <= 1
        # High burnout risk given the signals
        assert burnout_risk > 0.5

    def test_severity_determination(self, pipeline_orchestrator):
        """Test insight severity determination"""
        test_cases = [
            (["indicator1"], InsightSeverity.LOW),
            (["indicator1", "indicator2"], InsightSeverity.MEDIUM),
            (["indicator1", "indicator2", "indicator3"], InsightSeverity.HIGH),
            (
                ["indicator1", "indicator2", "indicator3", "indicator4", "indicator5"],
                InsightSeverity.CRITICAL,
            ),
        ]

        for indicators, expected_severity in test_cases:
            severity = pipeline_orchestrator._determine_severity(
                indicators, critical_threshold=4
            )
            assert (
                severity == expected_severity
            ), f"Failed for {len(indicators)} indicators"


class TestAPIEndpoints:
    """Test API endpoint functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_get_available_data_sources(self, client):
        """Test getting available data sources"""
        # Note: This test assumes the API is running with auth disabled or with valid auth
        # You may need to add authentication headers
        response = client.get("/api/v1/integrations/corporate/available")

        # Response could be 401 (unauthorized) or 200 (OK)
        # If 401, the endpoint exists but requires auth
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Check for known data sources
            source_types = [item.get("type") for item in data]
            assert "email_metadata" in source_types or len(data) > 0


# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
