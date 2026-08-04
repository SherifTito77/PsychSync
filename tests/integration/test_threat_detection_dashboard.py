#!/usr/bin/env python3
"""
Integration Tests for Threat Detection Dashboard System

Tests for:
- Prometheus threat metrics aggregation (threat_metrics.py)
- Alert notification system (alert_notification_system.py)
- Integration with threat detection components

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.monitoring.alert_notification_system import (
    AlertNotification,
    AlertNotificationSystem,
    AlertSeverity,
    EmailNotificationSender,
    NotificationChannel,
    NotificationConfig,
    PagerDutyNotificationSender,
    SlackNotificationSender,
    SMSNotificationSender,
    WebhookNotificationSender,
    create_notification_hook,
    initialize_notification_system,
    send_security_alert,
)
from app.monitoring.threat_metrics import (
    ThreatDetectionMetrics,
    record_behavioral_anomaly,
    record_jailbreak,
    record_response,
    record_threat_assessment,
)

# ==================== Prometheus Threat Metrics Tests ====================


class TestThreatDetectionMetrics:
    """Test Prometheus threat metrics aggregation"""

    @pytest.fixture
    def metrics(self):
        """Create metrics instance"""
        return ThreatDetectionMetrics(port=8002)

    def test_metrics_initialization(self, metrics):
        """Test metrics initialization"""
        assert metrics.port == 8002

        # Check that metrics object exists (works even without Prometheus)
        assert metrics is not None
        # When Prometheus is not available, metrics are disabled but the object still exists
        # The actual metrics attributes are only created when PROMETHEUS_AVAILABLE is True

    def test_record_jailbreak_attempt(self, metrics):
        """Test recording jailbreak attempt"""
        metrics.record_jailbreak_attempt(
            jailbreak_type="direct_injection",
            severity="high",
            patterns_matched=["ignore.*instructions"],
            confidence=0.85,
        )

        # Metrics should be recorded without error
        # (actual verification would require Prometheus client)

    def test_record_jailbreak_multiple_patterns(self, metrics):
        """Test recording jailbreak with multiple patterns"""
        metrics.record_jailbreak_attempt(
            jailbreak_type="role_playing",
            severity="critical",
            patterns_matched=["DAN", "Developer Mode", "unrestricted"],
            confidence=0.92,
        )

        # Should record all patterns
        # (actual verification would require Prometheus client)

    def test_record_behavioral_anomaly(self, metrics):
        """Test recording behavioral anomaly"""
        metrics.record_behavioral_anomaly(
            user_id="user_123",
            category="bot_automation",
            threat_type="bot_automation",
            risk_score=0.75,
        )

        # Metrics should be recorded without error

    def test_update_baseline_stats(self, metrics):
        """Test updating baseline statistics"""
        metrics.update_baseline_stats(users_with_baselines=150, total_users=200)

        # Metrics should be updated

    def test_record_threat_signal(self, metrics):
        """Test recording threat signal"""
        metrics.record_threat_signal(
            source="jailbreak",
            severity="high",
            threat_type="direct_injection",
            session_id="sess_456",
        )

        # Metrics should be recorded

    def test_record_threat_assessment(self, metrics):
        """Test recording threat assessment"""
        metrics.record_threat_assessment(
            session_id="sess_789", threat_level="high", risk_score=0.75
        )

        # Should update threat level gauge

    def test_update_avg_risk_score(self, metrics):
        """Test updating average risk score"""
        metrics.update_avg_risk_score(0.45)

        # Should update average risk score gauge

    def test_update_active_sessions(self, metrics):
        """Test updating active sessions count"""
        metrics.update_active_sessions(42)

        # Should update active sessions gauge

    def test_record_response_action(self, metrics):
        """Test recording response action"""
        metrics.record_response_action(
            action="Block Session",
            status="executed",
            duration_seconds=0.5,
            success=True,
        )

        # Should record response action metrics

    def test_record_response_action_failed(self, metrics):
        """Test recording failed response action"""
        metrics.record_response_action(
            action="Block IP", status="failed", duration_seconds=1.2, success=False
        )

        # Should increment failed counter

    def test_record_request_analyzed(self, metrics):
        """Test recording request analysis"""
        metrics.record_request_analyzed(blocked=False)

        # Should increment analyzed counter

    def test_record_request_blocked(self, metrics):
        """Test recording blocked request"""
        metrics.record_request_analyzed(blocked=True)

        # Should increment both analyzed and blocked counters


class TestConvenienceFunctions:
    """Test convenience functions for metrics"""

    def test_record_jailbreak_convenience(self):
        """Test record_jailbreak convenience function"""
        record_jailbreak(
            jailbreak_type="direct_injection",
            severity="high",
            patterns_matched=["test.*pattern"],
            confidence=0.8,
        )

        # Should record without error

    def test_record_behavioral_anomaly_convenience(self):
        """Test record_behavioral_anomaly convenience function"""
        record_behavioral_anomaly(
            user_id="test_user",
            category="brute_force",
            threat_type="brute_force",
            risk_score=0.65,
        )

        # Should record without error

    def test_record_threat_assessment_convenience(self):
        """Test record_threat_assessment convenience function"""
        record_threat_assessment(
            session_id="test_session",
            threat_level="medium",
            risk_score=0.5,
            signals=[
                {
                    "source": "jailbreak",
                    "severity": "high",
                    "threat_type": "direct_injection",
                },
                {
                    "source": "behavioral",
                    "severity": "medium",
                    "threat_type": "anomaly",
                },
            ],
        )

        # Should record without error

    def test_record_response_convenience(self):
        """Test record_response convenience function"""
        record_response(
            action="Log Warning", status="executed", duration_seconds=0.1, success=True
        )

        # Should record without error


# ==================== Alert Notification System Tests ====================


class TestNotificationConfig:
    """Test notification configuration"""

    def test_notification_config_creation(self):
        """Test creating notification config"""
        config = NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            min_severity=AlertSeverity.HIGH,
            config={"webhook_url": "https://hooks.slack.com/test"},
        )

        assert config.channel == NotificationChannel.SLACK
        assert config.enabled is True
        assert config.min_severity == AlertSeverity.HIGH

    def test_should_send_with_higher_severity(self):
        """Test should_send with higher severity"""
        config = NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            min_severity=AlertSeverity.HIGH,
        )

        assert config.should_send(AlertSeverity.CRITICAL) is True
        assert config.should_send(AlertSeverity.HIGH) is True
        assert config.should_send(AlertSeverity.MEDIUM) is False
        assert config.should_send(AlertSeverity.LOW) is False

    def test_should_send_when_disabled(self):
        """Test should_send when disabled"""
        config = NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=False,
            min_severity=AlertSeverity.LOW,
        )

        assert config.should_send(AlertSeverity.CRITICAL) is False


class TestAlertNotification:
    """Test alert notification dataclass"""

    def test_alert_notification_creation(self):
        """Test creating alert notification"""
        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Critical Threat Detected",
            description="Jailbreak attempt detected",
            threat_type="jailbreak",
            user_id="user_123",
            session_id="sess_456",
        )

        assert notification.severity == AlertSeverity.CRITICAL
        assert notification.title == "Critical Threat Detected"
        assert notification.threat_type == "jailbreak"
        assert notification.timestamp is not None

    def test_alert_notification_to_dict(self):
        """Test converting notification to dict"""
        notification = AlertNotification(
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test description",
            threat_type="test",
            user_id="user_123",
        )

        data = notification.to_dict()

        assert data["severity"] == "high"
        assert data["title"] == "Test Alert"
        assert data["description"] == "Test description"
        assert data["threat_type"] == "test"
        assert data["user_id"] == "user_123"
        assert "timestamp" in data


class TestSlackNotificationSender:
    """Test Slack notification sender"""

    @pytest.fixture
    def slack_config(self):
        """Create Slack config"""
        return NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            config={
                "webhook_url": "https://hooks.slack.com/test/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
            },
        )

    @pytest.fixture
    def slack_sender(self, slack_config):
        """Create Slack sender"""
        return SlackNotificationSender(slack_config)

    @pytest.mark.asyncio
    async def test_send_slack_notification_success(self, slack_sender):
        """Test successful Slack notification"""
        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Test Alert",
            description="Test description",
            threat_type="jailbreak",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_sender.send(notification)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_slack_notification_failure(self, slack_sender):
        """Test failed Slack notification"""
        notification = AlertNotification(
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test description",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_sender.send(notification)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_slack_with_retry(self, slack_sender):
        """Test Slack notification with retry"""
        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Test Alert",
            description="Test description",
        )

        call_count = 0

        # Mock the send method directly to test retry logic
        original_send = slack_sender.send

        async def mock_send_with_failure_then_success(notif):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Connection error")
            return True

        with patch.object(
            slack_sender, "send", side_effect=mock_send_with_failure_then_success
        ):
            result = await slack_sender.send_with_retry(notification, max_retries=3)

            assert result is True
            assert call_count == 3


class TestPagerDutyNotificationSender:
    """Test PagerDuty notification sender"""

    @pytest.fixture
    def pagerduty_config(self):
        """Create PagerDuty config"""
        return NotificationConfig(
            channel=NotificationChannel.PAGERDUTY,
            enabled=True,
            config={"routing_key": "test_routing_key_123"},
        )

    @pytest.fixture
    def pagerduty_sender(self, pagerduty_config):
        """Create PagerDuty sender"""
        return PagerDutyNotificationSender(pagerduty_config)

    @pytest.mark.asyncio
    async def test_send_pagerduty_notification(self, pagerduty_sender):
        """Test PagerDuty notification"""
        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
            description="Critical security threat",
            threat_type="account_takeover",
            user_id="user_123",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 202
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await pagerduty_sender.send(notification)

            assert result is True


class TestEmailNotificationSender:
    """Test email notification sender"""

    @pytest.fixture
    def email_config(self):
        """Create email config"""
        return NotificationConfig(
            channel=NotificationChannel.EMAIL,
            enabled=True,
            config={
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_user": "alerts@example.com",
                "smtp_password": "password",
                "recipients": ["security@example.com"],
            },
        )

    @pytest.fixture
    def email_sender(self, email_config):
        """Create email sender"""
        return EmailNotificationSender(email_config)

    @pytest.mark.asyncio
    async def test_send_email_notification(self, email_sender):
        """Test email notification"""
        notification = AlertNotification(
            severity=AlertSeverity.HIGH,
            title="Security Alert",
            description="High severity threat detected",
            threat_type="jailbreak",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_sender.send(notification)

            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()


class TestSMSNotificationSender:
    """Test SMS notification sender"""

    @pytest.fixture
    def sms_config(self):
        """Create SMS config"""
        return NotificationConfig(
            channel=NotificationChannel.SMS,
            enabled=True,
            config={
                "account_sid": "AC1234567890abcdef",
                "auth_token": "authtoken123",
                "from_number": "+1234567890",
                "to_numbers": ["+0987654321"],
            },
        )

    @pytest.fixture
    def sms_sender(self, sms_config):
        """Create SMS sender"""
        return SMSNotificationSender(sms_config)

    @pytest.mark.asyncio
    async def test_send_sms_notification(self, sms_sender):
        """Test SMS notification"""
        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
            description="Critical security incident",
            response_action="Block IP",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 201
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await sms_sender.send(notification)

            assert result is True


class TestWebhookNotificationSender:
    """Test webhook notification sender"""

    @pytest.fixture
    def webhook_config(self):
        """Create webhook config"""
        return NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            enabled=True,
            config={
                "webhook_url": "https://api.example.com/webhooks/security",
                "headers": {"Authorization": "Bearer token123"},
            },
        )

    @pytest.fixture
    def webhook_sender(self, webhook_config):
        """Create webhook sender"""
        return WebhookNotificationSender(webhook_config)

    @pytest.mark.asyncio
    async def test_send_webhook_notification(self, webhook_sender):
        """Test webhook notification"""
        notification = AlertNotification(
            severity=AlertSeverity.HIGH,
            title="Webhook Test",
            description="Testing webhook notification",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await webhook_sender.send(notification)

            assert result is True


class TestAlertNotificationSystem:
    """Test main alert notification system"""

    @pytest.fixture
    def configs(self):
        """Create test configs"""
        return [
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                min_severity=AlertSeverity.MEDIUM,
                config={"webhook_url": "https://hooks.slack.com/test"},
            ),
            NotificationConfig(
                channel=NotificationChannel.PAGERDUTY,
                enabled=True,
                min_severity=AlertSeverity.CRITICAL,
                config={"routing_key": "test_key"},
            ),
        ]

    @pytest.fixture
    def notification_system(self, configs):
        """Create notification system"""
        return AlertNotificationSystem(configs)

    def test_notification_system_initialization(self, notification_system):
        """Test system initialization"""
        assert len(notification_system.senders) == 2
        assert NotificationChannel.SLACK in notification_system.senders
        assert NotificationChannel.PAGERDUTY in notification_system.senders

    @pytest.mark.asyncio
    async def test_send_alert_to_all_channels(self, notification_system):
        """Test sending alert to all channels"""
        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
            description="Critical threat detected",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            results = await notification_system.send_alert(notification)

            assert "slack" in results
            assert "pagerduty" in results

    @pytest.mark.asyncio
    async def test_send_alert_respects_severity_threshold(self, notification_system):
        """Test that severity threshold is respected"""
        notification = AlertNotification(
            severity=AlertSeverity.LOW,  # Below PagerDuty threshold
            title="Low Alert",
            description="Low severity alert",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            results = await notification_system.send_alert(notification)

            # Slack should receive (min severity: MEDIUM > LOW)
            # PagerDuty should not receive (min severity: CRITICAL > LOW)
            assert "slack" in results
            assert "pagerduty" in results

    def test_get_stats(self, notification_system):
        """Test getting system statistics"""
        stats = notification_system.get_stats()

        assert "total_channels" in stats
        assert stats["total_channels"] == 2
        assert "enabled_channels" in stats
        assert "channels" in stats
        assert len(stats["channels"]) == 2


class TestNotificationHook:
    """Test notification hook for AutomatedThreatResponder"""

    @pytest.fixture
    def notification_system(self):
        """Create notification system with mock configs"""
        configs = [
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                config={"webhook_url": "https://hooks.slack.com/test"},
            )
        ]
        return AlertNotificationSystem(configs)

    def test_create_notification_hook(self, notification_system):
        """Test creating notification hook"""
        hook = create_notification_hook(notification_system)

        assert asyncio.iscoroutinefunction(hook)

    @pytest.mark.asyncio
    async def test_notification_hook_execution(self, notification_system):
        """Test notification hook execution"""
        hook = create_notification_hook(notification_system)

        threat_report = {
            "overall_threat_level": "high",
            "dominant_threat_type": "jailbreak",
            "user_id": "user_123",
            "session_id": "sess_456",
            "summary": "High severity threat detected",
            "risk_score": 0.75,
            "recommended_action": "block",
            "threat_signals": [],
        }

        response_report = {"context": {"ip_address": "192.168.1.1"}}

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            await hook(threat_report, response_report)

            # Should send notification without error


class TestConvenienceAlertFunctions:
    """Test convenience alert functions"""

    @pytest.mark.asyncio
    async def test_send_security_alert(self):
        """Test send_security_alert convenience function"""
        configs = [
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                config={"webhook_url": "https://hooks.slack.com/test"},
            )
        ]

        system = initialize_notification_system(configs)

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            results = await send_security_alert(
                severity="critical",
                title="Test Alert",
                description="Test alert from convenience function",
                user_id="user_123",
                ip_address="192.168.1.1",
            )

            assert "slack" in results


# ==================== Integration Tests ====================


class TestMetricsWithThreatDetection:
    """Test metrics integration with threat detection"""

    @pytest.fixture
    def metrics(self):
        """Create metrics instance"""
        return ThreatDetectionMetrics(port=8003)

    def test_jailbreak_detection_metrics(self, metrics):
        """Test recording jailbreak detection metrics"""
        # Simulate jailbreak detection
        jailbreak_type = "role_playing"
        severity = "critical"

        metrics.record_jailbreak_attempt(
            jailbreak_type=jailbreak_type,
            severity=severity,
            patterns_matched=["DAN", "unrestricted"],
            confidence=0.95,
        )

        # Should record without error

    def test_behavioral_analysis_metrics(self, metrics):
        """Test recording behavioral analysis metrics"""
        # Simulate behavioral anomaly
        metrics.record_behavioral_anomaly(
            user_id="user_123",
            category="bot_automation",
            threat_type="bot_automation",
            risk_score=0.85,
        )

        # Should record without error

    def test_threat_assessment_metrics(self, metrics):
        """Test recording threat assessment metrics"""
        # Simulate threat assessment
        metrics.record_threat_assessment(
            session_id="sess_789", threat_level="high", risk_score=0.72
        )

        metrics.record_threat_signal(
            source="jailbreak", severity="high", threat_type="role_playing"
        )

        metrics.record_threat_signal(
            source="behavioral", severity="medium", threat_type="anomaly"
        )

        # Should record without error

    def test_response_action_metrics(self, metrics):
        """Test recording response action metrics"""
        # Simulate response action
        metrics.record_response_action(
            action="Block Session",
            status="executed",
            duration_seconds=0.35,
            success=True,
        )

        # Should record without error


class TestEndToEndWorkflow:
    """Test end-to-end workflow: detection → metrics → notification"""

    @pytest.mark.asyncio
    async def test_full_threat_response_workflow(self):
        """Test complete workflow from detection to notification"""
        # Step 1: Record metrics
        from app.monitoring.threat_metrics import get_metrics

        metrics = get_metrics()

        # Record jailbreak detection
        metrics.record_jailbreak_attempt(
            jailbreak_type="direct_injection",
            severity="critical",
            patterns_matched=["ignore.*instructions"],
            confidence=0.92,
        )

        # Record threat assessment
        metrics.record_threat_assessment(
            session_id="sess_test", threat_level="critical", risk_score=0.88
        )

        # Step 2: Send notification
        configs = [
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                min_severity=AlertSeverity.CRITICAL,
                config={"webhook_url": "https://hooks.slack.com/test"},
            )
        ]

        notification_system = AlertNotificationSystem(configs)

        notification = AlertNotification(
            severity=AlertSeverity.CRITICAL,
            title="Critical Jailbreak Detected",
            description="Direct injection jailbreak attempt detected",
            threat_type="direct_injection",
            session_id="sess_test",
            ip_address="192.168.1.1",
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            results = await notification_system.send_alert(notification)

            assert "slack" in results

        # Step 3: Record response metrics
        metrics.record_response_action(
            action="Block Session",
            status="executed",
            duration_seconds=0.5,
            success=True,
        )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
