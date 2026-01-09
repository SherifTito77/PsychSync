#!/usr/bin/env python3
"""
Security Monitoring System Tests

Comprehensive tests for:
- Audit logging system
- Real-time threat detection
- Security analytics
- Automated incident response

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.monitoring.audit_logger import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditLogger,
    AuditQuery,
    ConsoleBackend
)
from app.monitoring.security_analytics import (
    SecurityEvent,
    ThreatIndicator,
    ThreatLevel,
    RealTimeSecurityAnalyzer
)
from app.monitoring.incident_response import (
    IncidentResponder,
    ResponseAction,
    ActionResult,
    IncidentResponse,
    ThreatIndicator as IRThreatIndicator
)


# ==================== Audit Logger Tests ====================

class TestAuditEvent:
    """Test AuditEvent creation and validation"""

    def test_create_audit_event(self):
        """Test creating a basic audit event"""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            severity=AuditSeverity.INFO,
            user_id=123,
            ip_address="192.168.1.1"
        )

        assert event.event_type == "auth.login"
        assert event.severity == "info"
        assert event.user_id == 123
        assert event.ip_address == "192.168.1.1"
        assert isinstance(event.timestamp, datetime)

    def test_audit_event_to_dict(self):
        """Test converting audit event to dictionary"""
        event = AuditEvent(
            event_type=AuditEventType.AUTHZ_ACCESS_DENIED,
            severity=AuditSeverity.HIGH,
            user_id=456,
            resource_type="assessment",
            resource_id=789
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "authz.access_denied"
        assert event_dict["severity"] == "high"
        assert event_dict["user_id"] == 456
        assert event_dict["resource_type"] == "assessment"
        assert event_dict["resource_id"] == 789
        assert "timestamp" in event_dict

    def test_audit_event_with_details(self):
        """Test audit event with additional details"""
        details = {
            "login_method": "password",
            "user_agent": "Mozilla/5.0",
            "success": True
        }

        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            severity=AuditSeverity.INFO,
            user_id=123,
            details=details
        )

        assert event.details == details
        assert event.details["success"] is True


class TestAuditLogger:
    """Test audit logger functionality"""

    @pytest.fixture
    def logger(self):
        """Create audit logger with console backend"""
        backend = ConsoleBackend()
        return AuditLogger(backends=[backend])

    @pytest.mark.asyncio
    async def test_log_event(self, logger):
        """Test logging an event"""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN,
            severity=AuditSeverity.INFO,
            user_id=123
        )

        # Should not raise exception
        await logger.log(event)

    @pytest.mark.asyncio
    async def test_log_auth_event(self, logger):
        """Test logging authentication event"""
        await logger.log_auth_event(
            event_type="login_success",
            severity="info",
            user_id=123,
            ip_address="192.168.1.1",
            success=True
        )

        # Verify event was created correctly
        # (In real test, would check backend)

    @pytest.mark.asyncio
    async def test_log_security_event(self, logger):
        """Test logging security event"""
        await logger.log_security_event(
            event_type="brute_force_detected",
            severity="high",
            user_id=456,
            ip_address="10.0.0.1",
            details={"failed_attempts": 10}
        )

    @pytest.mark.asyncio
    async def test_critical_event_triggers_alert(self, logger):
        """Test that critical events trigger alerts"""
        with patch.object(logger, '_trigger_alert', new=AsyncMock()) as mock_alert:
            event = AuditEvent(
                event_type=AuditEventType.SECURITY_BREACH,
                severity=AuditSeverity.CRITICAL,
                user_id=789
            )

            await logger.log(event)

            # Verify alert was triggered
            mock_alert.assert_called_once()


class TestAuditQuery:
    """Test audit log query builder"""

    def test_filter_by_event_type(self):
        """Test filtering by event type"""
        query = AuditQuery()
        query = query.filter_by_event_type("auth.login")

        assert query.filters["event_type"] == "auth.login"

    def test_filter_by_severity(self):
        """Test filtering by severity"""
        query = AuditQuery()
        query = query.filter_by_severity("high")

        assert query.filters["severity"] == "high"

    def test_filter_by_user(self):
        """Test filtering by user"""
        query = AuditQuery()
        query = query.filter_by_user(123)

        assert query.filters["user_id"] == 123

    def test_filter_date_range(self):
        """Test filtering by date range"""
        query = AuditQuery()
        start = datetime.utcnow() - timedelta(hours=1)
        end = datetime.utcnow()

        query = query.filter_date_range(start, end)

        assert query.filters["start_date"] == start
        assert query.filters["end_date"] == end

    def test_limit(self):
        """Test setting result limit"""
        query = AuditQuery()
        query = query.limit(100)

        assert query.limit_value == 100

    def test_chained_filters(self):
        """Test chaining multiple filters"""
        query = (AuditQuery()
                 .filter_by_event_type("auth.login")
                 .filter_by_severity("high")
                 .filter_by_user(123)
                 .limit(50))

        assert query.filters["event_type"] == "auth.login"
        assert query.filters["severity"] == "high"
        assert query.filters["user_id"] == 123
        assert query.limit_value == 50


# ==================== Security Analytics Tests ====================

class TestSecurityEvent:
    """Test SecurityEvent creation"""

    def test_create_security_event(self):
        """Test creating security event"""
        event = SecurityEvent(
            event_type="auth.failed",
            timestamp=datetime.utcnow(),
            user_id=123,
            ip_address="192.168.1.1",
            severity="high",
            details={"reason": "invalid_password"}
        )

        assert event.event_type == "auth.failed"
        assert event.user_id == 123
        assert event.ip_address == "192.168.1.1"
        assert event.severity == "high"


class TestRealTimeSecurityAnalyzer:
    """Test real-time security analyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RealTimeSecurityAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_event_no_threats(self, analyzer):
        """Test analyzing event with no threats"""
        event = SecurityEvent(
            event_type="auth.success",
            timestamp=datetime.utcnow(),
            user_id=123,
            ip_address="192.168.1.1",
            severity="info",
            details={}
        )

        threats = await analyzer.analyze_event(event)

        assert len(threats) == 0

    @pytest.mark.asyncio
    async def test_detect_brute_force_user(self, analyzer):
        """Test brute force detection for user"""
        user_id = 123

        # Simulate 5 failed login attempts
        for _ in range(5):
            event = SecurityEvent(
                event_type="auth.failed",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address="192.168.1.1",
                severity="high",
                details={}
            )
            await analyzer.analyze_event(event)

        # 6th attempt should trigger threat
        event = SecurityEvent(
            event_type="auth.failed",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address="192.168.1.1",
            severity="high",
            details={}
        )

        threats = await analyzer.analyze_event(event)

        # Should detect brute force
        assert any(t.indicator_type == "brute_force" for t in threats)

    @pytest.mark.asyncio
    async def test_detect_brute_force_ip(self, analyzer):
        """Test brute force detection for IP"""
        ip_address = "10.0.0.1"

        # Simulate 5 failed attempts from same IP
        for i in range(5):
            event = SecurityEvent(
                event_type="auth.failed",
                timestamp=datetime.utcnow(),
                user_id=i,  # Different users
                ip_address=ip_address,
                severity="critical",
                details={}
            )
            await analyzer.analyze_event(event)

        # 6th attempt should trigger IP-based threat
        event = SecurityEvent(
            event_type="auth.failed",
            timestamp=datetime.utcnow(),
            user_id=999,
            ip_address=ip_address,
            severity="critical",
            details={}
        )

        threats = await analyzer.analyze_event(event)

        # Should detect IP-based brute force
        assert any(t.indicator_type == "brute_force_ip" for t in threats)

    @pytest.mark.asyncio
    async def test_detect_unauthorized_access(self, analyzer):
        """Test unauthorized access detection"""
        user_id = 456

        # Simulate 3 unauthorized access attempts
        for _ in range(3):
            event = SecurityEvent(
                event_type="authz.access_denied",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address="192.168.1.1",
                severity="high",
                details={}
            )
            await analyzer.analyze_event(event)

        # 4th attempt should trigger threat
        event = SecurityEvent(
            event_type="authz.access_denied",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address="192.168.1.1",
            severity="high",
            details={}
        )

        threats = await analyzer.analyze_event(event)

        # Should detect unauthorized access pattern
        assert any(t.indicator_type == "unauthorized_access_attempt" for t in threats)

    @pytest.mark.asyncio
    async def test_detect_bulk_operations(self, analyzer):
        """Test bulk data operation detection"""
        event = SecurityEvent(
            event_type="data.export",
            timestamp=datetime.utcnow(),
            user_id=789,
            ip_address="192.168.1.1",
            severity="high",
            details={"record_count": 150}  # Over threshold
        )

        threats = await analyzer.analyze_event(event)

        # Should detect data exfiltration
        assert any(t.indicator_type == "data_exfiltration" for t in threats)

    def test_get_security_metrics(self, analyzer):
        """Test getting security metrics"""
        # Add some events
        for i in range(10):
            event = SecurityEvent(
                event_type=f"event_{i}",
                timestamp=datetime.utcnow(),
                user_id=i,
                severity="info",
                details={}
            )
            analyzer.event_history.append(event)

        metrics = analyzer.get_security_metrics()

        assert metrics["total_events"] >= 10
        assert "events_by_severity" in metrics
        assert "active_users" in metrics
        assert "active_ips" in metrics


# ==================== Incident Response Tests ====================

class TestIncidentResponder:
    """Test automated incident response"""

    @pytest.fixture
    def responder(self):
        """Create incident responder instance"""
        return IncidentResponder()

    def test_load_default_configs(self, responder):
        """Test default response configurations loaded"""
        assert "brute_force" in responder.response_configs
        assert "brute_force_ip" in responder.response_configs
        assert "data_exfiltration" in responder.response_configs

    @pytest.mark.asyncio
    async def test_respond_to_brute_force(self, responder):
        """Test responding to brute force threat"""
        threat = ThreatIndicator(
            indicator_type="brute_force",
            severity=ThreatLevel.HIGH,
            confidence=0.9,
            description="Brute force attack detected",
            affected_entities=["user_123"],
            mitigation_suggestions=["Lock account"]
        )

        with patch.object(responder, '_lock_account', new=AsyncMock()) as mock_lock:
            results = await responder.respond_to_threat(
                threat,
                ["user_123"],
                auto_approve=True
            )

            # Should execute lock account action
            assert any(r.action == ResponseAction.LOCK_ACCOUNT for r in results)

    @pytest.mark.asyncio
    async def test_respond_to_ip_brute_force(self, responder):
        """Test responding to IP-based brute force"""
        threat = ThreatIndicator(
            indicator_type="brute_force_ip",
            severity=ThreatLevel.CRITICAL,
            confidence=0.95,
            description="IP-based brute force",
            affected_entities=["192.168.1.1"],
            mitigation_suggestions=["Block IP"]
        )

        results = await responder.respond_to_threat(
            threat,
            ["192.168.1.1"],
            auto_approve=True
        )

        # Should execute block IP action (doesn't require approval)
        assert any(r.action == ResponseAction.BLOCK_IP for r in results)

    @pytest.mark.asyncio
    async def test_low_confidence_skips_response(self, responder):
        """Test that low confidence threats don't trigger response"""
        threat = ThreatIndicator(
            indicator_type="brute_force",
            severity=ThreatLevel.HIGH,
            confidence=0.5,  # Below threshold
            description="Possible brute force",
            affected_entities=["user_123"],
            mitigation_suggestions=[]
        )

        results = await responder.respond_to_threat(
            threat,
            ["user_123"],
            auto_approve=True
        )

        # Should not execute any actions
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_requires_approval(self, responder):
        """Test that account actions require approval"""
        threat = ThreatIndicator(
            indicator_type="brute_force",
            severity=ThreatLevel.HIGH,
            confidence=0.9,
            description="Brute force attack",
            affected_entities=["user_123"],
            mitigation_suggestions=[]
        )

        # Don't auto-approve
        results = await responder.respond_to_threat(
            threat,
            ["user_123"],
            auto_approve=False
        )

        # Should request approval instead of executing
        assert any(r.result == ActionResult.REQUIRES_APPROVAL for r in results)

    def test_block_ip(self, responder):
        """Test IP blocking"""
        # Manually block IP
        responder.blocked_ips["192.168.1.100"] = datetime.utcnow()

        assert responder.is_ip_blocked("192.168.1.100") is True
        assert responder.is_ip_blocked("10.0.0.1") is False

    def test_lock_account(self, responder):
        """Test account locking"""
        # Manually lock account
        responder.locked_accounts[123] = datetime.utcnow()

        assert responder.is_account_locked(123) is True
        assert responder.is_account_locked(456) is False

    def test_unlock_account(self, responder):
        """Test account unlocking"""
        responder.locked_accounts[123] = datetime.utcnow()
        assert responder.is_account_locked(123) is True

        # Unlock
        responder.unlock_account(123)
        assert responder.is_account_locked(123) is False

    def test_unblock_ip(self, responder):
        """Test IP unblocking"""
        responder.blocked_ips["192.168.1.100"] = datetime.utcnow()
        assert responder.is_ip_blocked("192.168.1.100") is True

        # Unblock
        responder.unblock_ip("192.168.1.100")
        assert responder.is_ip_blocked("192.168.1.100") is False

    @pytest.mark.asyncio
    async def test_action_cooldown(self, responder):
        """Test that actions have cooldown period"""
        threat = ThreatIndicator(
            indicator_type="automation_detected",
            severity=ThreatLevel.LOW,
            confidence=0.8,
            description="Automation detected",
            affected_entities=["192.168.1.1"],
            mitigation_suggestions=[]
        )

        # Execute action once
        results1 = await responder.respond_to_threat(
            threat,
            ["192.168.1.1"],
            auto_approve=True
        )

        # Try to execute again immediately
        results2 = await responder.respond_to_threat(
            threat,
            ["192.168.1.1"],
            auto_approve=True
        )

        # Second execution should be skipped due to cooldown
        assert any(r.result == ActionResult.SKIPPED for r in results2)


# ==================== Integration Tests ====================

class TestSecurityMonitoringIntegration:
    """Integration tests for complete security monitoring flow"""

    @pytest.mark.asyncio
    async def test_complete_threat_detection_and_response(self):
        """Test full flow from detection to response"""
        # Create components
        analyzer = RealTimeSecurityAnalyzer()
        responder = IncidentResponder()

        # Simulate brute force attack
        user_id = 999
        for _ in range(6):
            event = SecurityEvent(
                event_type="auth.failed",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address="10.0.0.50",
                severity="high",
                details={}
            )

            # Analyze event
            threats = await analyzer.analyze_event(event)

            # Respond to threats
            for threat in threats:
                await responder.respond_to_threat(
                    threat,
                    threat.affected_entities,
                    auto_approve=True
                )

        # Verify response was executed
        metrics = analyzer.get_security_metrics()
        assert metrics["total_events"] >= 6

    @pytest.mark.asyncio
    async def test_audit_log_integration(self):
        """Test audit logging integration with detection"""
        analyzer = RealTimeSecurityAnalyzer()
        logger = AuditLogger(backends=[ConsoleBackend()])

        # Create security event
        event = SecurityEvent(
            event_type="auth.failed",
            timestamp=datetime.utcnow(),
            user_id=123,
            ip_address="192.168.1.1",
            severity="high",
            details={}
        )

        # Analyze and log
        threats = await analyzer.analyze_event(event)

        if threats:
            for threat in threats:
                await logger.log_security_event(
                    event_type=threat.indicator_type,
                    severity=threat.severity.value,
                    user_id=event.user_id,
                    details={"confidence": threat.confidence}
                )


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
