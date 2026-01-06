#!/usr/bin/env python3
"""
Automated Threat Response System

Executes automated responses to detected threats based on severity and type.
Provides graduated response actions from monitoring to blocking and alerting.

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Status of automated response"""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ActionPriority(Enum):
    """Priority of response actions"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ResponseAction:
    """Individual response action"""
    action_id: str
    name: str
    description: str
    priority: ActionPriority
    execute_func: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    status: ResponseStatus = ResponseStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed_at: Optional[datetime] = None


@dataclass
class ResponseExecutionReport:
    """Report of automated response execution"""
    incident_id: str
    threat_report: Dict[str, Any]
    actions_executed: List[ResponseAction]
    total_actions: int
    successful_actions: int
    failed_actions: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    overall_status: ResponseStatus = ResponseStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "incident_id": self.incident_id,
            "threat_summary": {
                "threat_level": self.threat_report.get("overall_threat_level"),
                "risk_score": self.threat_report.get("risk_score"),
                "recommended_action": self.threat_report.get("recommended_action")
            },
            "actions_total": self.total_actions,
            "actions_successful": self.successful_actions,
            "actions_failed": self.failed_actions,
            "duration_seconds": self.duration_seconds,
            "overall_status": self.overall_status.value,
            "actions": [
                {
                    "name": a.name,
                    "status": a.status.value,
                    "result": a.result,
                    "error": a.error
                }
                for a in self.actions_executed
            ]
        }


class AutomatedThreatResponder:
    """
    Automated threat response system.

    Executes predefined response actions based on threat assessment.
    """

    def __init__(
        self,
        enable_auto_response: bool = True,
        dry_run: bool = False,
        notification_hooks: Optional[List[Callable]] = None
    ):
        """
        Initialize automated threat responder.

        Args:
            enable_auto_response: Enable automatic response execution
            dry_run: If True, simulate actions without executing
            notification_hooks: List of notification functions to call
        """
        self.enable_auto_response = enable_auto_response
        self.dry_run = dry_run
        self.notification_hooks = notification_hooks or []

        # Response history
        self.response_history: List[ResponseExecutionReport] = []

        # Action registry
        self.action_registry: Dict[str, Callable] = {}

        # Register default actions
        self._register_default_actions()

        logger.info(f"AutomatedThreatResponder initialized (dry_run={dry_run})")

    def _register_default_actions(self):
        """Register default response actions"""
        self.action_registry = {
            'log_warning': self._action_log_warning,
            'add_response_header': self._action_add_response_header,
            'throttle_requests': self._action_throttle_requests,
            'require_mfa': self._action_require_mfa,
            'block_session': self._action_block_session,
            'block_user': self._action_block_user,
            'block_ip': self._action_block_ip,
            'revoke_sessions': self._action_revoke_sessions,
            'send_alert': self._action_send_alert,
            'quarantine_user': self._action_quarantine_user,
            'notify_security_team': self._action_notify_security_team,
        }

    async def execute_response(
        self,
        threat_report: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ResponseExecutionReport:
        """
        Execute automated response based on threat report.

        Args:
            threat_report: Unified threat report from monitoring system
            context: Additional context for response execution

        Returns:
            ResponseExecutionReport with execution results
        """
        incident_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now(timezone.utc)
        context = context or {}

        logger.info(f"Executing automated response for incident {incident_id}")

        # Determine actions to execute based on threat level
        actions = self._plan_response_actions(threat_report, context)

        # Execute actions
        executed_actions = []
        successful = 0
        failed = 0

        for action in actions:
            if not self.enable_auto_response:
                action.status = ResponseStatus.SKIPPED
                action.error = "Auto-response disabled"
                executed_actions.append(action)
                continue

            try:
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would execute: {action.name}")
                    action.status = ResponseStatus.EXECUTED
                    action.result = {"dry_run": True}
                else:
                    await self._execute_action(action)

                if action.status == ResponseStatus.EXECUTED:
                    successful += 1
                else:
                    failed += 1

                executed_actions.append(action)

            except Exception as e:
                logger.error(f"Error executing action {action.name}: {e}")
                action.status = ResponseStatus.FAILED
                action.error = str(e)
                failed += 1
                executed_actions.append(action)

        # Determine overall status
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        if failed == 0:
            overall_status = ResponseStatus.EXECUTED
        elif successful > 0:
            overall_status = ResponseStatus.PARTIAL
        else:
            overall_status = ResponseStatus.FAILED

        # Create report
        report = ResponseExecutionReport(
            incident_id=incident_id,
            threat_report=threat_report,
            actions_executed=executed_actions,
            total_actions=len(actions),
            successful_actions=successful,
            failed_actions=failed,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            overall_status=overall_status
        )

        # Store in history
        self.response_history.append(report)

        # Send notifications
        await self._send_notifications(report)

        # Log completion
        self._log_response_report(report)

        return report

    def _plan_response_actions(
        self,
        threat_report: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ResponseAction]:
        """Plan which actions to execute based on threat"""
        actions = []
        recommended_action = threat_report.get('recommended_action')
        threat_level = threat_report.get('overall_threat_level')
        risk_score = threat_report.get('risk_score', 0.0)

        # Action 1: Always log the threat
        actions.append(ResponseAction(
            action_id=f"log_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            name="Log Warning",
            description="Log threat detection to security logs",
            priority=ActionPriority.LOW,
            execute_func=self.action_registry['log_warning'],
            params={'threat_report': threat_report}
        ))

        # Action 2: Add security headers to response
        if threat_level in ['low', 'medium']:
            actions.append(ResponseAction(
                action_id=f"header_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Add Security Headers",
                description="Add security warning headers to response",
                priority=ActionPriority.MEDIUM,
                execute_func=self.action_registry['add_response_header'],
                params={'threat_level': threat_level}
            ))

        # Action 3: Throttle requests
        if threat_level == 'medium' or risk_score >= 0.4:
            actions.append(ResponseAction(
                action_id=f"throttle_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Throttle Requests",
                description="Apply rate limiting to user/session",
                priority=ActionPriority.MEDIUM,
                execute_func=self.action_registry['throttle_requests'],
                params={
                    'user_id': threat_report.get('user_id'),
                    'session_id': threat_report.get('session_id'),
                    'requests_per_minute': 10
                }
            ))

        # Action 4: Require MFA
        if threat_level == 'medium' or risk_score >= 0.5:
            actions.append(ResponseAction(
                action_id=f"mfa_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Require MFA",
                description="Require multi-factor authentication",
                priority=ActionPriority.HIGH,
                execute_func=self.action_registry['require_mfa'],
                params={'user_id': threat_report.get('user_id')}
            ))

        # Action 5: Block session
        if threat_level == 'high' or recommended_action == 'block':
            actions.append(ResponseAction(
                action_id=f"block_session_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Block Session",
                description="Block current session",
                priority=ActionPriority.HIGH,
                execute_func=self.action_registry['block_session'],
                params={'session_id': threat_report.get('session_id')}
            ))

        # Action 6: Block user temporarily
        if threat_level == 'high' or risk_score >= 0.7:
            actions.append(ResponseAction(
                action_id=f"block_user_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Block User",
                description="Temporarily block user account",
                priority=ActionPriority.HIGH,
                execute_func=self.action_registry['block_user'],
                params={
                    'user_id': threat_report.get('user_id'),
                    'duration_minutes': 30
                }
            ))

        # Action 7: Block IP address
        if threat_level == 'critical' or risk_score >= 0.8:
            actions.append(ResponseAction(
                action_id=f"block_ip_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Block IP",
                description="Block IP address at firewall",
                priority=ActionPriority.CRITICAL,
                execute_func=self.action_registry['block_ip'],
                params={
                    'ip_address': context.get('ip_address'),
                    'duration_hours': 24
                }
            ))

        # Action 8: Revoke all user sessions
        if threat_level == 'critical':
            actions.append(ResponseAction(
                action_id=f"revoke_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Revoke Sessions",
                description="Revoke all user sessions",
                priority=ActionPriority.CRITICAL,
                execute_func=self.action_registry['revoke_sessions'],
                params={'user_id': threat_report.get('user_id')}
            ))

        # Action 9: Send alert to security team
        if threat_level in ['high', 'critical']:
            actions.append(ResponseAction(
                action_id=f"alert_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Send Alert",
                description="Send alert to security team",
                priority=ActionPriority.CRITICAL,
                execute_func=self.action_registry['send_alert'],
                params={
                    'threat_report': threat_report,
                    'severity': threat_level
                }
            ))

        # Action 10: Notify security team directly for critical
        if threat_level == 'critical':
            actions.append(ResponseAction(
                action_id=f"notify_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                name="Notify Security Team",
                description="Page/on-call security team",
                priority=ActionPriority.CRITICAL,
                execute_func=self.action_registry['notify_security_team'],
                params={'incident_id': f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"}
            ))

        # Sort by priority
        actions.sort(key=lambda a: a.priority.value, reverse=True)

        return actions

    async def _execute_action(self, action: ResponseAction):
        """Execute a single response action"""
        logger.info(f"Executing action: {action.name}")

        if asyncio.iscoroutinefunction(action.execute_func):
            result = await action.execute_func(**action.params)
        else:
            result = action.execute_func(**action.params)

        action.result = result
        action.status = ResponseStatus.EXECUTED
        action.executed_at = datetime.now(timezone.utc)

        logger.info(f"Action completed: {action.name}")

    async def _send_notifications(self, report: ResponseExecutionReport):
        """Send notifications via registered hooks"""
        for hook in self.notification_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(report)
                else:
                    hook(report)
            except Exception as e:
                logger.error(f"Error in notification hook: {e}")

    def _log_response_report(self, report: ResponseExecutionReport):
        """Log response execution report"""
        log_data = {
            "incident_id": report.incident_id,
            "overall_status": report.overall_status.value,
            "actions_total": report.total_actions,
            "actions_successful": report.successful_actions,
            "actions_failed": report.failed_actions,
            "duration_seconds": report.duration_seconds
        }

        if report.overall_status in [ResponseStatus.FAILED, ResponseStatus.PARTIAL]:
            logger.warning(f"Response execution: {log_data}")
        else:
            logger.info(f"Response execution: {log_data}")

    # ==================== Default Action Implementations ====================

    def _action_log_warning(self, threat_report: Dict[str, Any]) -> Dict[str, Any]:
        """Log warning to security logs"""
        logger.warning(
            f"Security threat detected: {threat_report.get('overall_threat_level')} "
            f"(risk: {threat_report.get('risk_score', 0):.2%})"
        )
        return {"logged": True}

    async def _action_add_response_header(self, threat_level: str) -> Dict[str, Any]:
        """Add security headers to response (would be done in middleware)"""
        # In production, this would set headers on the HTTP response
        headers = {
            'X-Threat-Detected': 'true',
            'X-Threat-Level': threat_level,
            'X-Security-Monitor': 'active'
        }
        return {"headers": headers}

    async def _action_throttle_requests(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        requests_per_minute: int
    ) -> Dict[str, Any]:
        """Apply rate limiting"""
        # In production, this would update rate limit rules in Redis/database
        logger.info(f"Rate limiting applied: {requests_per_minute} req/min "
                   f"(user: {user_id}, session: {session_id})")
        return {"throttled": True, "limit": requests_per_minute}

    async def _action_require_mfa(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Require multi-factor authentication"""
        # In production, this would set a flag requiring MFA on next login
        logger.info(f"MFA required for user: {user_id}")
        return {"mfa_required": True, "user_id": user_id}

    async def _action_block_session(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Block current session"""
        # In production, this would invalidate the session in Redis/database
        logger.info(f"Session blocked: {session_id}")
        return {"session_blocked": True, "session_id": session_id}

    async def _action_block_user(
        self,
        user_id: Optional[str],
        duration_minutes: int
    ) -> Dict[str, Any]:
        """Block user account temporarily"""
        # In production, this would set account status in database
        logger.info(f"User blocked for {duration_minutes} minutes: {user_id}")
        return {
            "user_blocked": True,
            "user_id": user_id,
            "duration_minutes": duration_minutes
        }

    async def _action_block_ip(
        self,
        ip_address: Optional[str],
        duration_hours: int
    ) -> Dict[str, Any]:
        """Block IP address at firewall/load balancer"""
        # In production, this would update firewall rules or use CDN blocking
        logger.warning(f"IP blocked for {duration_hours} hours: {ip_address}")
        return {
            "ip_blocked": True,
            "ip_address": ip_address,
            "duration_hours": duration_hours
        }

    async def _action_revoke_sessions(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Revoke all user sessions"""
        # In production, this would delete all sessions from Redis/database
        logger.warning(f"All sessions revoked for user: {user_id}")
        return {"sessions_revoked": True, "user_id": user_id}

    async def _action_send_alert(
        self,
        threat_report: Dict[str, Any],
        severity: str
    ) -> Dict[str, Any]:
        """Send alert to security monitoring"""
        # In production, this would send to SIEM, Slack, PagerDuty, etc.
        alert_data = {
            "severity": severity,
            "threat_level": threat_report.get('overall_threat_level'),
            "risk_score": threat_report.get('risk_score'),
            "user_id": threat_report.get('user_id'),
            "session_id": threat_report.get('session_id'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.critical(f"Security alert: {json.dumps(alert_data)}")
        return {"alert_sent": True, "alert_data": alert_data}

    async def _action_notify_security_team(self, incident_id: str) -> Dict[str, Any]:
        """Page/on-call security team"""
        # In production, this would call PagerDuty, Opsgenie, etc.
        logger.critical(f"CRITICAL: Security team notified for incident {incident_id}")
        return {"notified": True, "incident_id": incident_id}

    async def _action_quarantine_user(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Quarantine user account for investigation"""
        # In production, this would set quarantine flag in database
        logger.warning(f"User quarantined for investigation: {user_id}")
        return {"quarantined": True, "user_id": user_id}

    # ==================== Public API Methods ====================

    def register_action(self, name: str, func: Callable):
        """Register a custom response action"""
        self.action_registry[name] = func
        logger.info(f"Registered custom action: {name}")

    def get_response_history(
        self,
        limit: int = 50
    ) -> List[ResponseExecutionReport]:
        """Get recent response execution history"""
        return self.response_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get responder statistics"""
        total = len(self.response_history)
        if total == 0:
            return {
                "total_responses": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0
            }

        successful = sum(1 for r in self.response_history if r.overall_status == ResponseStatus.EXECUTED)
        avg_duration = sum(r.duration_seconds for r in self.response_history) / total

        return {
            "total_responses": total,
            "successful": successful,
            "success_rate": successful / total,
            "avg_duration_seconds": avg_duration,
            "dry_run": self.dry_run
        }


# Global responder instance
auto_responder = AutomatedThreatResponder(dry_run=False)


async def execute_response(
    threat_report: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> ResponseExecutionReport:
    """
    Convenience function to execute automated response.

    Usage:
        from ai.security.auto_response import execute_response

        threat_report = {
            "overall_threat_level": "high",
            "risk_score": 0.75,
            "recommended_action": "block",
            "user_id": "user_123",
            "session_id": "sess_456"
        }

        report = await execute_response(threat_report)

        print(f"Actions executed: {report.successful_actions}/{report.total_actions}")
        print(f"Status: {report.overall_status}")
    """
    return await auto_responder.execute_response(threat_report, context)


# CLI interface
def main():
    """CLI interface for automated threat responder"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated Threat Response System"
    )
    parser.add_argument(
        '--threat-level',
        required=True,
        choices=['safe', 'low', 'medium', 'high', 'critical'],
        help='Threat level'
    )
    parser.add_argument(
        '--risk-score',
        type=float,
        help='Risk score (0.0 to 1.0)'
    )
    parser.add_argument(
        '--user-id',
        help='User ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate actions without executing'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Build threat report
    threat_report = {
        "overall_threat_level": args.threat_level,
        "risk_score": args.risk_score or 0.5,
        "recommended_action": "block" if args.threat_level in ["high", "critical"] else "monitor",
        "user_id": args.user_id,
        "session_id": "test_session"
    }

    # Set dry run mode
    if args.dry_run:
        auto_responder.dry_run = True

    # Run async execution
    async def run_response():
        report = await execute_response(threat_report)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print("\n" + "="*80)
            print("AUTOMATED RESPONSE EXECUTION RESULTS")
            print("="*80)
            print(f"Incident ID: {report.incident_id}")
            print(f"Overall Status: {report.overall_status.value.upper()}")
            print(f"Actions: {report.successful_actions}/{report.total_actions} successful")
            print(f"Duration: {report.duration_seconds:.2f}s")
            print(f"\nActions Executed:")
            for action in report.actions_executed:
                status_icon = "✓" if action.status == ResponseStatus.EXECUTED else "✗"
                print(f"  {status_icon} {action.name}: {action.status.value}")
            print("="*80 + "\n")

    asyncio.run(run_response())


if __name__ == '__main__':
    main()
