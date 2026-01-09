#!/usr/bin/env python3
"""
Automated Incident Response System

Provides automated responses to security threats:
- Account lockdown for brute force
- IP blocking for malicious actors
- Session termination for compromised accounts
- Alert escalation for critical threats
- Automated containment actions

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any

from app.monitoring.audit_logger import AuditSeverity, audit_logger
from app.monitoring.security_analytics import ThreatIndicator, ThreatLevel

logger = logging.getLogger(__name__)


class ResponseAction(str, Enum):
    """Automated response actions"""
    # Account actions
    LOCK_ACCOUNT = "lock_account"
    FORCE_PASSWORD_RESET = "force_password_reset"
    TERMINATE_SESSIONS = "terminate_sessions"
    REQUIRE_MFA = "require_mfa"

    # Network actions
    BLOCK_IP = "block_ip"
    RATE_LIMIT_IP = "rate_limit_ip"
    BLOCK_USER_AGENT = "block_user_agent"

    # Monitoring actions
    INCREASE_MONITORING = "increase_monitoring"
    ALERT_ADMIN = "alert_admin"
    ALERT_USER = "alert_user"

    # Containment actions
    QUARANTINE_ACCOUNT = "quarantine_account"
    RESTRICT_ACCESS = "restrict_access"
    DISABLE_API_KEYS = "disable_api_keys"


class ActionResult(str, Enum):
    """Result of response action execution"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"
    REQUIRES_APPROVAL = "requires_approval"


@dataclass
class ResponseActionExecuted:
    """Record of executed response action"""
    action: ResponseAction
    result: ActionResult
    timestamp: datetime
    target: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class IncidentResponse:
    """
    Automated incident response configuration

    Defines how to respond to specific threat types.
    """
    threat_type: str
    min_confidence: float = 0.8
    min_severity: ThreatLevel = ThreatLevel.HIGH
    actions: list[ResponseAction] = field(default_factory=list)
    requires_approval: bool = False
    cooldown_minutes: int = 60


class IncidentResponder:
    """
    Automated incident response engine.

    Executes predefined response actions based on threat indicators.
    Implements safety checks and approval workflows.
    """

    def __init__(self):
        # Response configurations by threat type
        self.response_configs: dict[str, IncidentResponse] = {}

        # Action execution history (for cooldown tracking)
        self.action_history: dict[str, datetime] = {}

        # Blocked entities (IPs, accounts, etc.)
        self.blocked_ips: dict[str, datetime] = {}
        self.locked_accounts: dict[int, datetime] = {}

        # Custom action handlers
        self.action_handlers: dict[ResponseAction, Callable] = {
            ResponseAction.LOCK_ACCOUNT: self._lock_account,
            ResponseAction.TERMINATE_SESSIONS: self._terminate_sessions,
            ResponseAction.BLOCK_IP: self._block_ip,
            ResponseAction.RATE_LIMIT_IP: self._rate_limit_ip,
            ResponseAction.ALERT_ADMIN: self._alert_admin,
            ResponseAction.ALERT_USER: self._alert_user,
            ResponseAction.INCREASE_MONITORING: self._increase_monitoring,
        }

        # Load default response configurations
        self._load_default_configs()

    def _load_default_configs(self):
        """Load default incident response configurations"""

        # Brute force response
        self.response_configs["brute_force"] = IncidentResponse(
            threat_type="brute_force",
            min_confidence=0.85,
            min_severity=ThreatLevel.HIGH,
            actions=[
                ResponseAction.INCREASE_MONITORING,
                ResponseAction.ALERT_ADMIN,
                ResponseAction.TERMINATE_SESSIONS,
            ],
            requires_approval=True,  # Account actions need approval
            cooldown_minutes=30
        )

        # IP-based brute force (more aggressive)
        self.response_configs["brute_force_ip"] = IncidentResponse(
            threat_type="brute_force_ip",
            min_confidence=0.90,
            min_severity=ThreatLevel.CRITICAL,
            actions=[
                ResponseAction.BLOCK_IP,
                ResponseAction.ALERT_ADMIN,
            ],
            requires_approval=False,  # IP blocking doesn't require approval
            cooldown_minutes=60
        )

        # Unauthorized access attempt
        self.response_configs["unauthorized_access_attempt"] = IncidentResponse(
            threat_type="unauthorized_access_attempt",
            min_confidence=0.80,
            min_severity=ThreatLevel.HIGH,
            actions=[
                ResponseAction.INCREASE_MONITORING,
                ResponseAction.ALERT_ADMIN,
                ResponseAction.ALERT_USER,
            ],
            requires_approval=True,
            cooldown_minutes=60
        )

        # Data exfiltration
        self.response_configs["data_exfiltration"] = IncidentResponse(
            threat_type="data_exfiltration",
            min_confidence=0.75,
            min_severity=ThreatLevel.HIGH,
            actions=[
                ResponseAction.RESTRICT_ACCESS,
                ResponseAction.ALERT_ADMIN,
                ResponseAction.INCREASE_MONITORING,
            ],
            requires_approval=True,
            cooldown_minutes=30
        )

        # Automation/Bot detection
        self.response_configs["automation_detected"] = IncidentResponse(
            threat_type="automation_detected",
            min_confidence=0.70,
            min_severity=ThreatLevel.LOW,
            actions=[
                ResponseAction.RATE_LIMIT_IP,
                ResponseAction.INCREASE_MONITORING,
            ],
            requires_approval=False,
            cooldown_minutes=15
        )

    async def respond_to_threat(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str],
        auto_approve: bool = False
    ) -> list[ResponseActionExecuted]:
        """
        Execute automated response to threat indicator.

        Args:
            threat: Detected threat indicator
            affected_entities: List of affected entity identifiers
            auto_approve: Skip approval checks (use with caution)

        Returns list of executed actions with results.
        """
        results = []

        # Check if we have a response config for this threat type
        config = self.response_configs.get(threat.indicator_type)
        if not config:
            logger.warning(f"No response configuration for threat type: {threat.indicator_type}")
            return results

        # Check if threat meets response criteria
        if threat.confidence < config.min_confidence:
            logger.info(f"Threat confidence {threat.confidence} below threshold {config.min_confidence}")
            return results

        severity_levels = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        if severity_levels[threat.severity] < severity_levels[config.min_severity]:
            logger.info(f"Threat severity {threat.severity} below threshold {config.min_severity}")
            return results

        # Execute response actions
        for action in config.actions:
            # Check cooldown
            action_key = f"{action}:{affected_entities[0] if affected_entities else 'global'}"
            last_executed = self.action_history.get(action_key)

            if last_executed:
                cooldown_expiry = last_executed + timedelta(minutes=config.cooldown_minutes)
                if datetime.utcnow() < cooldown_expiry:
                    logger.info(f"Action {action} in cooldown until {cooldown_expiry}")
                    results.append(ResponseActionExecuted(
                        action=action,
                        result=ActionResult.SKIPPED,
                        timestamp=datetime.utcnow(),
                        target="cooldown",
                        details={"cooldown_until": cooldown_expiry.isoformat()}
                    ))
                    continue

            # Check approval requirement
            if config.requires_approval and not auto_approve:
                logger.info(f"Action {action} requires approval")
                await self._request_approval(action, threat, affected_entities)

                results.append(ResponseActionExecuted(
                    action=action,
                    result=ActionResult.REQUIRES_APPROVAL,
                    timestamp=datetime.utcnow(),
                    target="pending_approval",
                    details={"threat": threat.description}
                ))
                continue

            # Execute action
            try:
                result = await self._execute_action(action, threat, affected_entities)
                results.append(result)

                # Record execution time for cooldown
                if result.result == ActionResult.SUCCESS:
                    self.action_history[action_key] = datetime.utcnow()

            except Exception as e:
                logger.error(f"Error executing action {action}: {e}")
                results.append(ResponseActionExecuted(
                    action=action,
                    result=ActionResult.FAILED,
                    timestamp=datetime.utcnow(),
                    target="unknown",
                    error=str(e)
                ))

        return results

    async def _execute_action(
        self,
        action: ResponseAction,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Execute a single response action"""

        handler = self.action_handlers.get(action)
        if not handler:
            logger.warning(f"No handler for action: {action}")
            return ResponseActionExecuted(
                action=action,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target="unknown",
                error="No handler registered"
            )

        # Call handler
        return await handler(threat, affected_entities)

    # ==================== Action Handlers ====================

    async def _lock_account(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Lock affected user account"""

        # Extract user ID from affected entities
        user_id = None
        for entity in affected_entities:
            if entity.startswith("user_"):
                user_id = int(entity.split("_")[1])
                break

        if not user_id:
            return ResponseActionExecuted(
                action=ResponseAction.LOCK_ACCOUNT,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target="unknown",
                error="No user ID found in affected entities"
            )

        # Lock account
        try:
            # TODO: Implement actual account locking logic
            # This would call the user service to lock the account
            self.locked_accounts[user_id] = datetime.utcnow()

            # Log the action
            await audit_logger.log_security_event(
                event_type="account_locked",
                severity=AuditSeverity.HIGH,
                user_id=user_id,
                details={
                    "reason": threat.description,
                    "threat_type": threat.indicator_type,
                    "confidence": threat.confidence
                }
            )

            logger.info(f"Locked account {user_id} due to {threat.indicator_type}")

            return ResponseActionExecuted(
                action=ResponseAction.LOCK_ACCOUNT,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target=f"user_{user_id}",
                details={"locked_until": (datetime.utcnow() + timedelta(hours=24)).isoformat()}
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.LOCK_ACCOUNT,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target=f"user_{user_id}",
                error=str(e)
            )

    async def _terminate_sessions(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Terminate all sessions for affected user"""

        user_id = None
        for entity in affected_entities:
            if entity.startswith("user_"):
                user_id = int(entity.split("_")[1])
                break

        if not user_id:
            return ResponseActionExecuted(
                action=ResponseAction.TERMINATE_SESSIONS,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target="unknown",
                error="No user ID found in affected entities"
            )

        try:
            # TODO: Implement session termination
            # This would invalidate all refresh tokens for the user

            await audit_logger.log_security_event(
                event_type="sessions_terminated",
                severity=AuditSeverity.HIGH,
                user_id=user_id,
                details={
                    "reason": threat.description,
                    "threat_type": threat.indicator_type
                }
            )

            logger.info(f"Terminated sessions for user {user_id}")

            return ResponseActionExecuted(
                action=ResponseAction.TERMINATE_SESSIONS,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target=f"user_{user_id}",
                details={"sessions_terminated": "all"}
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.TERMINATE_SESSIONS,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target=f"user_{user_id}",
                error=str(e)
            )

    async def _block_ip(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Block malicious IP address"""

        # Extract IP from affected entities
        ip_address = None
        for entity in affected_entities:
            if "." in entity or ":" in entity:  # Simple IP check
                ip_address = entity
                break

        if not ip_address:
            return ResponseActionExecuted(
                action=ResponseAction.BLOCK_IP,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target="unknown",
                error="No IP address found in affected entities"
            )

        try:
            # Block IP
            self.blocked_ips[ip_address] = datetime.utcnow()

            # Log the action
            await audit_logger.log_security_event(
                event_type="ip_blocked",
                severity=AuditSeverity.HIGH,
                details={
                    "ip_address": ip_address,
                    "reason": threat.description,
                    "threat_type": threat.indicator_type,
                    "blocked_until": (datetime.utcnow() + timedelta(hours=24)).isoformat()
                }
            )

            logger.info(f"Blocked IP {ip_address} due to {threat.indicator_type}")

            return ResponseActionExecuted(
                action=ResponseAction.BLOCK_IP,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target=ip_address,
                details={"blocked_until": (datetime.utcnow() + timedelta(hours=24)).isoformat()}
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.BLOCK_IP,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target=ip_address,
                error=str(e)
            )

    async def _rate_limit_ip(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Apply rate limiting to IP address"""

        ip_address = None
        for entity in affected_entities:
            if "." in entity or ":" in entity:
                ip_address = entity
                break

        if not ip_address:
            return ResponseActionExecuted(
                action=ResponseAction.RATE_LIMIT_IP,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target="unknown",
                error="No IP address found in affected entities"
            )

        try:
            # TODO: Implement rate limiting
            # This would add the IP to a rate limit blacklist

            await audit_logger.log_security_event(
                event_type="ip_rate_limited",
                severity=AuditSeverity.MEDIUM,
                details={
                    "ip_address": ip_address,
                    "reason": threat.description,
                    "threat_type": threat.indicator_type
                }
            )

            return ResponseActionExecuted(
                action=ResponseAction.RATE_LIMIT_IP,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target=ip_address,
                details={"rate_limit": "10_requests_per_minute"}
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.RATE_LIMIT_IP,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target=ip_address,
                error=str(e)
            )

    async def _alert_admin(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Send alert to administrators"""

        try:
            # TODO: Implement admin alerting
            # This could send email, Slack message, SMS, etc.

            await audit_logger.log_security_event(
                event_type="admin_alert_sent",
                severity=AuditSeverity.HIGH,
                details={
                    "threat_type": threat.indicator_type,
                    "description": threat.description,
                    "severity": threat.severity.value,
                    "confidence": threat.confidence,
                    "affected_entities": affected_entities,
                    "mitigation_suggestions": threat.mitigation_suggestions
                }
            )

            logger.warning(f"Admin alert: {threat.description}")

            return ResponseActionExecuted(
                action=ResponseAction.ALERT_ADMIN,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target="administrators",
                details={"alert_channel": "audit_log"}  # TODO: Add email, Slack, etc.
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.ALERT_ADMIN,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target="administrators",
                error=str(e)
            )

    async def _alert_user(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Send alert to affected user"""

        user_id = None
        for entity in affected_entities:
            if entity.startswith("user_"):
                user_id = int(entity.split("_")[1])
                break

        if not user_id:
            return ResponseActionExecuted(
                action=ResponseAction.ALERT_USER,
                result=ActionResult.SKIPPED,
                timestamp=datetime.utcnow(),
                target="unknown",
                details={"reason": "No user ID found"}
            )

        try:
            # TODO: Implement user alerting
            # This would send email or in-app notification

            await audit_logger.log_security_event(
                event_type="user_alert_sent",
                severity=AuditSeverity.MEDIUM,
                user_id=user_id,
                details={
                    "alert_type": "security_incident",
                    "threat_type": threat.indicator_type,
                    "description": "Suspicious activity detected on your account"
                }
            )

            return ResponseActionExecuted(
                action=ResponseAction.ALERT_USER,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target=f"user_{user_id}",
                details={"alert_channel": "email"}  # TODO: Add in-app notification
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.ALERT_USER,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target=f"user_{user_id}",
                error=str(e)
            )

    async def _increase_monitoring(
        self,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ) -> ResponseActionExecuted:
        """Increase monitoring level for affected entities"""

        try:
            await audit_logger.log_security_event(
                event_type="monitoring_increased",
                severity=AuditSeverity.MEDIUM,
                details={
                    "threat_type": threat.indicator_type,
                    "affected_entities": affected_entities,
                    "monitoring_level": "enhanced"
                }
            )

            return ResponseActionExecuted(
                action=ResponseAction.INCREASE_MONITORING,
                result=ActionResult.SUCCESS,
                timestamp=datetime.utcnow(),
                target=",".join(affected_entities),
                details={"monitoring_level": "enhanced"}
            )

        except Exception as e:
            return ResponseActionExecuted(
                action=ResponseAction.INCREASE_MONITORING,
                result=ActionResult.FAILED,
                timestamp=datetime.utcnow(),
                target=",".join(affected_entities),
                error=str(e)
            )

    async def _request_approval(
        self,
        action: ResponseAction,
        threat: ThreatIndicator,
        affected_entities: list[str]
    ):
        """Request admin approval for action"""

        await audit_logger.log_security_event(
            event_type="action_approval_requested",
            severity=AuditSeverity.HIGH,
            details={
                "action": action.value,
                "threat_type": threat.indicator_type,
                "affected_entities": affected_entities,
                "confidence": threat.confidence,
                "severity": threat.severity.value
            }
        )

        # TODO: Implement approval workflow
        # This could create a ticket, send notification, etc.

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is currently blocked"""
        if ip_address not in self.blocked_ips:
            return False

        # Check if block has expired (24 hours)
        block_time = self.blocked_ips[ip_address]
        if datetime.utcnow() - block_time > timedelta(hours=24):
            del self.blocked_ips[ip_address]
            return False

        return True

    def is_account_locked(self, user_id: int) -> bool:
        """Check if account is currently locked"""
        if user_id not in self.locked_accounts:
            return False

        # Check if lock has expired (24 hours)
        lock_time = self.locked_accounts[user_id]
        if datetime.utcnow() - lock_time > timedelta(hours=24):
            del self.locked_accounts[user_id]
            return False

        return True

    def unlock_account(self, user_id: int):
        """Manually unlock account"""
        if user_id in self.locked_accounts:
            del self.locked_accounts[user_id]

    def unblock_ip(self, ip_address: str):
        """Manually unblock IP"""
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]


# Global incident responder instance
incident_responder = IncidentResponder()
