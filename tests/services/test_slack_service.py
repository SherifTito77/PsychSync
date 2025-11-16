"""
Unit Tests for Slack Service

Tests all Slack functionality without requiring actual Slack workspace
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.slack_service import SlackServiceStub


@pytest.fixture
def slack_service():
    """Create Slack service in test mode"""
    service = SlackServiceStub(test_mode=True)
    service.clear_sent_messages()
    return service


class TestSlackServiceBasics:
    """Test basic Slack service functionality"""
    
    @pytest.mark.asyncio
    async def test_send_message_to_channel(self, slack_service):
        """Test sending message to channel"""
        response = await slack_service.send_message_to_channel(
            channel="#general",
            message="Test message"
        )
        
        assert response["ok"] is True
        assert response["channel"] == "#general"
        assert "ts" in response
        
        # Verify message was logged
        sent = slack_service.get_sent_messages()
        assert len(sent) == 1
        assert sent[0]["channel"] == "#general"
        assert sent[0]["message"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_send_message_with_blocks(self, slack_service):
        """Test sending rich message with blocks"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello *world*!"
                }
            }
        ]
        
        response = await slack_service.send_message_to_channel(
            channel="#general",
            message="Fallback text",
            blocks=blocks
        )
        
        assert response["ok"] is True
        
        sent = slack_service.get_sent_messages()
        assert sent[0]["blocks"] == blocks
    
    @pytest.mark.asyncio
    async def test_send_direct_message(self, slack_service):
        """Test sending DM to user"""
        response = await slack_service.send_direct_message(
            user_id="U12345",
            message="Private message"
        )
        
        assert response["ok"] is True
        assert "D_" in response["channel"]
    
    @pytest.mark.asyncio
    async def test_thread_reply(self, slack_service):
        """Test sending message in thread"""
        response = await slack_service.send_message_to_channel(
            channel="#general",
            message="Thread reply",
            thread_ts="1234567890.123456"
        )
        
        assert response["ok"] is True
        
        sent = slack_service.get_sent_messages()
        assert sent[0]["thread_ts"] == "1234567890.123456"


class TestSlackNotifications:
    """Test notification formatting and sending"""
    
    @pytest.mark.asyncio
    async def test_assessment_complete_notification(self, slack_service):
        """Test assessment completion notification"""
        success = await slack_service.send_notification(
            team_id=1,
            notification_type="assessment_complete",
            data={
                "user_name": "John Doe",
                "assessment_type": "Burnout Assessment",
                "score": 78
            }
        )
        
        assert success is True
        
        sent = slack_service.get_sent_messages()
        assert len(sent) == 1
        assert "John Doe" in sent[0]["message"]
        assert "Burnout Assessment" in sent[0]["message"]
        assert sent[0]["blocks"] is not None
    
    @pytest.mark.asyncio
    async def test_wellbeing_alert_notification(self, slack_service):
        """Test wellbeing alert notification"""
        success = await slack_service.send_notification(
            team_id=1,
            notification_type="wellbeing_alert",
            data={
                "message": "Team member showing high stress",
                "url": "https://app.psychsync.com/alerts/123"
            }
        )
        
        assert success is True
        
        sent = slack_service.get_sent_messages()
        assert "⚠️" in sent[0]["message"]
        assert "high stress" in sent[0]["message"]
    
    @pytest.mark.asyncio
    async def test_report_ready_notification(self, slack_service):
        """Test report ready notification"""
        success = await slack_service.send_notification(
            team_id=1,
            notification_type="report_ready",
            data={
                "report_type": "Weekly Wellness Report",
                "download_url": "https://app.psychsync.com/reports/download/123"
            }
        )
        
        assert success is True
        
        sent = slack_service.get_sent_messages()
        assert "📊" in sent[0]["message"]
        assert "Weekly Wellness Report" in sent[0]["message"]
    
    @pytest.mark.asyncio
    async def test_team_member_joined_notification(self, slack_service):
        """Test new member notification"""
        success = await slack_service.send_notification(
            team_id=1,
            notification_type="team_member_joined",
            data={
                "member_name": "Jane Smith",
                "team_name": "Development Team"
            }
        )
        
        assert success is True
        
        sent = slack_service.get_sent_messages()
        assert "👋" in sent[0]["message"]
        assert "Jane Smith" in sent[0]["message"]


class TestSlashCommands:
    """Test slash command handling"""
    
    @pytest.mark.asyncio
    async def test_psychsync_help_command(self, slack_service):
        """Test /psychsync help"""
        response = await slack_service.handle_slash_command(
            command="/psychsync",
            user_id="U12345",
            channel_id="C12345",
            text="help"
        )
        
        assert response["response_type"] == "ephemeral"
        assert "Commands" in response["text"]
        assert "/checkin" in response["text"]
    
    @pytest.mark.asyncio
    async def test_psychsync_status_command(self, slack_service):
        """Test /psychsync status"""
        response = await slack_service.handle_slash_command(
            command="/psychsync",
            user_id="U12345",
            channel_id="C12345",
            text="status"
        )
        
        assert response["response_type"] == "ephemeral"
        assert "Wellness Status" in response["text"]
        assert "Score" in response["text"]
    
    @pytest.mark.asyncio
    async def test_psychsync_team_command(self, slack_service):
        """Test /psychsync team"""
        response = await slack_service.handle_slash_command(
            command="/psychsync",
            user_id="U12345",
            channel_id="C12345",
            text="team"
        )
        
        assert response["response_type"] == "in_channel"
        assert "Team Wellness" in response["text"]
        assert "Average Score" in response["text"]
    
    @pytest.mark.asyncio
    async def test_checkin_command(self, slack_service):
        """Test /checkin command"""
        response = await slack_service.handle_slash_command(
            command="/checkin",
            user_id="U12345",
            channel_id="C12345",
            text=""
        )
        
        assert response["response_type"] == "ephemeral"
        assert "check-in" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_wellness_command_personal(self, slack_service):
        """Test /wellness command (personal stats)"""
        response = await slack_service.handle_slash_command(
            command="/wellness",
            user_id="U12345",
            channel_id="C12345",
            text=""
        )
        
        assert response["response_type"] == "ephemeral"
        assert "Score" in response["text"]
    
    @pytest.mark.asyncio
    async def test_wellness_command_team(self, slack_service):
        """Test /wellness team command"""
        response = await slack_service.handle_slash_command(
            command="/wellness",
            user_id="U12345",
            channel_id="C12345",
            text="team"
        )
        
        assert response["response_type"] == "in_channel"
        assert "Team Wellness" in response["text"]
    
    @pytest.mark.asyncio
    async def test_assess_command(self, slack_service):
        """Test /assess command"""
        response = await slack_service.handle_slash_command(
            command="/assess",
            user_id="U12345",
            channel_id="C12345",
            text=""
        )
        
        assert response["response_type"] == "ephemeral"
        assert "assessment" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, slack_service):
        """Test unknown command"""
        response = await slack_service.handle_slash_command(
            command="/unknown",
            user_id="U12345",
            channel_id="C12345",
            text=""
        )
        
        assert "Unknown command" in response["text"]


class TestUtilityMethods:
    """Test utility methods"""
    
    def test_get_sent_messages(self, slack_service):
        """Test retrieving sent messages"""
        messages = slack_service.get_sent_messages()
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_clear_sent_messages(self, slack_service):
        """Test clearing sent messages"""
        # Send a message
        await slack_service.send_message_to_channel("#test", "test")
        assert len(slack_service.get_sent_messages()) == 1
        
        # Clear
        slack_service.clear_sent_messages()
        assert len(slack_service.get_sent_messages()) == 0
    
    def test_is_test_mode(self, slack_service):
        """Test checking test mode"""
        assert slack_service.is_test_mode() is True


class TestMessageFormatting:
    """Test message formatting helpers"""
    
    @pytest.mark.asyncio
    async def test_assessment_complete_high_score(self, slack_service):
        """Test formatting with high score (green)"""
        await slack_service.send_notification(
            team_id=1,
            notification_type="assessment_complete",
            data={
                "user_name": "John",
                "assessment_type": "Test",
                "score": 85
            }
        )
        
        sent = slack_service.get_sent_messages()
        assert "🟢" in sent[0]["message"]
    
    @pytest.mark.asyncio
    async def test_assessment_complete_medium_score(self, slack_service):
        """Test formatting with medium score (yellow)"""
        await slack_service.send_notification(
            team_id=1,
            notification_type="assessment_complete",
            data={
                "user_name": "John",
                "assessment_type": "Test",
                "score": 65
            }
        )
        
        sent = slack_service.get_sent_messages()
        assert "🟡" in sent[0]["message"]
    
    @pytest.mark.asyncio
    async def test_assessment_complete_low_score(self, slack_service):
        """Test formatting with low score (red)"""
        await slack_service.send_notification(
            team_id=1,
            notification_type="assessment_complete",
            data={
                "user_name": "John",
                "assessment_type": "Test",
                "score": 45
            }
        )
        
        sent = slack_service.get_sent_messages()
        assert "🔴" in sent[0]["message"]


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_missing_notification_data(self, slack_service):
        """Test handling missing notification data"""
        # Should not crash, use defaults
        success = await slack_service.send_notification(
            team_id=1,
            notification_type="assessment_complete",
            data={}  # Empty data
        )
        
        assert success is True
        sent = slack_service.get_sent_messages()
        assert len(sent) == 1


# Integration test (mocked Slack SDK)
class TestProductionMode:
    """Test production mode with mocked Slack SDK"""
    
    @pytest.mark.asyncio
    @patch('app.services.slack_service.settings.SLACK_BOT_TOKEN', 'xoxb-test-token')
    @patch('slack_sdk.WebClient')
    async def test_send_message_production_mode(self, mock_client):
        """Test sending message in production mode"""
        # Mock Slack SDK response
        mock_instance = Mock()
        mock_instance.chat_postMessage.return_value.data = {
            "ok": True,
            "channel": "C12345",
            "ts": "1234567890.123456"
        }
        mock_client.return_value = mock_instance
        
        # Create service in production mode
        service = SlackServiceStub(test_mode=False)
        
        response = await service.send_message_to_channel(
            channel="#general",
            message="Production test"
        )
        
        # Verify Slack SDK was called
        mock_instance.chat_postMessage.assert_called_once()
        assert response["ok"] is True


# Performance test
class TestPerformance:
    """Test performance with many messages"""
    
    @pytest.mark.asyncio
    async def test_send_many_messages(self, slack_service):
        """Test sending many messages quickly"""
        import time
        
        start = time.time()
        
        for i in range(100):
            await slack_service.send_message_to_channel(
                channel="#test",
                message=f"Message {i}"
            )
        
        duration = time.time() - start
        
        # Should be very fast in test mode
        assert duration < 1.0  # Less than 1 second for 100 messages
        assert len(slack_service.get_sent_messages()) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])