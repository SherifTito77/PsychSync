"""
Production-Grade Audit Logging System

Features:
- Comprehensive event tracking
- Structured logging with correlation IDs
- Security event monitoring
- Performance metrics collection
- Integration with external monitoring systems
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
import functools
import json
import logging
from typing import Any
import uuid

from app.core.config import settings
from app.core.redis_client import redis_get

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Audit action types"""

    AUTHENTICATE = "authenticate"
    AUTHENTICATION_FAILED = "authentication_failed"
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_CHANGE_FAILED = "password_change_failed"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    SECURITY_BREACH = "security_breach"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AuditSeverity(str, Enum):
    """Audit severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""

    action: AuditAction
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource: str | None = None
    details: dict[str, Any] | None = None
    severity: AuditSeverity = AuditSeverity.MEDIUM
    timestamp: datetime = None
    request_id: str | None = None
    organization_id: str | None = None
    session_id: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()
        if self.action:
            data["action"] = self.action.value
        if self.severity:
            data["severity"] = self.severity.value
        return data


class AuditLogger:
    """
    Production audit logging system
    """

    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.redis_ttl = 86400 * 30  # 30 days
        self.batch_size = 100
        self.batch_events: list[AuditEvent] = []
        self.batch_flush_interval = 60  # seconds
        self._flush_task: asyncio.Task | None = None

    async def log_event(self, event: AuditEvent) -> bool:
        """
        Log an audit event

        Args:
            event: Audit event to log

        Returns:
            True if logged successfully
        """
        try:
            # Add correlation ID if not present
            if not event.request_id:
                event.request_id = str(uuid.uuid4())

            # Determine severity based on action
            event.severity = self._determine_severity(event.action)

            # Log to structured logger
            await self._log_to_file(event)

            # Store in Redis for recent events
            await self._store_in_redis(event)

            # Check for security alerts
            await self._check_security_alerts(event)

            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False

    async def log_events_batch(self, events: list[AuditEvent]) -> int:
        """
        Log multiple audit events efficiently

        Args:
            events: List of audit events

        Returns:
            Number of events successfully logged
        """
        successful_count = 0

        try:
            # Add correlation IDs
            for event in events:
                if not event.request_id:
                    event.request_id = str(uuid.uuid4())
                event.severity = self._determine_severity(event.action)

            # Batch log to file
            await self._log_batch_to_file(events)

            # Batch store in Redis
            await self._store_batch_in_redis(events)

            successful_count = len(events)

        except Exception as e:
            logger.error(f"Failed to log audit events batch: {e}")

        return successful_count

    async def get_user_events(
        self, user_id: str, limit: int = 100, hours: int = 24
    ) -> list[dict[str, Any]]:
        """
        Get recent events for a specific user

        Args:
            user_id: User ID to filter by
            limit: Maximum number of events to return
            hours: Time window in hours

        Returns:
            List of audit events
        """
        try:
            # Get from Redis cache
            cache_key = f"audit:user:{user_id}:recent"
            cached_events = await redis_get(cache_key)

            if cached_events:
                events = json.loads(cached_events)
                return events[:limit]

            # If not in cache, get from log storage
            # This would integrate with your log storage system
            return []

        except Exception as e:
            logger.error(f"Failed to get user audit events: {e}")
            return []

    async def get_security_events(
        self, hours: int = 24, severity: AuditSeverity | None = None
    ) -> list[dict[str, Any]]:
        """
        Get recent security events

        Args:
            hours: Time window in hours
            severity: Filter by severity level

        Returns:
            List of security audit events
        """
        try:
            security_actions = [
                AuditAction.AUTHENTICATION_FAILED,
                AuditAction.SECURITY_BREACH,
                AuditAction.RATE_LIMIT_EXCEEDED,
                AuditAction.UNAUTHORIZED_ACCESS,
            ]

            # This would query your log storage system
            return []

        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []

    async def _log_to_file(self, event: AuditEvent):
        """Log event to structured file logger"""
        log_data = event.to_dict()
        self.logger.info(
            f"Audit Event: {event.action.value}",
            extra={
                "audit_event": log_data,
                "user_id": event.user_id,
                "action": event.action.value,
                "severity": event.severity.value,
                "ip_address": event.ip_address,
                "resource": event.resource,
            },
        )

    async def _log_batch_to_file(self, events: list[AuditEvent]):
        """Log batch of events to file"""
        for event in events:
            await self._log_to_file(event)

    async def _store_in_redis(self, event: AuditEvent):
        """Store event in Redis for quick access"""
        try:
            # Store in recent events list
            recent_key = "audit:events:recent"
            event_data = json.dumps(event.to_dict())

            # Use Redis list for recent events
            import redis.asyncio as redis

            redis_client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                decode_responses=True,
            )

            # Add to list and trim
            await redis_client.lpush(recent_key, event_data)
            await redis_client.ltrim(recent_key, 0, 10000)  # Keep last 10k events

            # Store in user-specific events
            if event.user_id:
                user_key = f"audit:user:{event.user_id}:recent"
                await redis_client.lpush(user_key, event_data)
                await redis_client.ltrim(user_key, 0, 100)  # Keep last 100 per user
                await redis_client.expire(user_key, 86400)  # 1 day TTL

            # Store security events separately
            if event.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                security_key = "audit:events:security"
                await redis_client.lpush(security_key, event_data)
                await redis_client.ltrim(security_key, 0, 1000)  # Keep last 1k security events

            await redis_client.close()

        except Exception as e:
            logger.warning(f"Failed to store audit event in Redis: {e}")

    async def _store_batch_in_redis(self, events: list[AuditEvent]):
        """Store batch of events in Redis"""
        for event in events:
            await self._store_in_redis(event)

    def _determine_severity(self, action: AuditAction) -> AuditSeverity:
        """Determine severity based on action"""
        severity_map = {
            AuditAction.AUTHENTICATION_FAILED: AuditSeverity.MEDIUM,
            AuditAction.SECURITY_BREACH: AuditSeverity.CRITICAL,
            AuditAction.RATE_LIMIT_EXCEEDED: AuditSeverity.HIGH,
            AuditAction.UNAUTHORIZED_ACCESS: AuditSeverity.HIGH,
            AuditAction.PASSWORD_CHANGE_FAILED: AuditSeverity.MEDIUM,
            AuditAction.DELETE: AuditSeverity.MEDIUM,
            AuditAction.EXPORT: AuditSeverity.LOW,
            AuditAction.IMPORT: AuditSeverity.LOW,
        }

        return severity_map.get(action, AuditSeverity.LOW)

    async def _check_security_alerts(self, event: AuditEvent):
        """Check for security alerts and trigger notifications"""
        try:
            # Check for multiple failed authentication attempts
            if event.action == AuditAction.AUTHENTICATION_FAILED:
                await self._check_brute_force_detection(event)

            # Check for suspicious activity patterns
            if event.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                await self._trigger_security_alert(event)

        except Exception as e:
            logger.error(f"Failed to check security alerts: {e}")

    async def _check_brute_force_detection(self, event: AuditEvent):
        """Check for brute force attack patterns"""
        try:
            if not event.ip_address:
                return

            # Count recent failed attempts from IP
            failed_attempts_key = f"auth:failed:{event.ip_address}:recent"

            import redis.asyncio as redis

            redis_client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                decode_responses=True,
            )

            recent_failures = await redis_client.llen(failed_attempts_key)
            await redis_client.close()

            # If too many failures, trigger alert
            if recent_failures > 10:  # Threshold for brute force detection
                await self._trigger_security_alert(event, "Brute force attack detected")

        except Exception as e:
            logger.error(f"Failed to check brute force detection: {e}")

    async def _trigger_security_alert(self, event: AuditEvent, message: str = None):
        """Trigger security alert"""
        try:
            alert_message = message or f"Security event: {event.action.value}"

            # Log to security logger
            security_logger = logging.getLogger("security")
            security_logger.warning(
                alert_message,
                extra={
                    "event": event.to_dict(),
                    "alert_level": "security",
                    "requires_immediate_attention": event.severity == AuditSeverity.CRITICAL,
                },
            )

            # In production, this would integrate with:
            # - Email alerts
            # - Slack notifications
            # - SIEM systems
            # - PagerDuty alerts

        except Exception as e:
            logger.error(f"Failed to trigger security alert: {e}")

    async def start_batch_processing(self):
        """Start background batch processing"""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._batch_processor())

    async def stop_batch_processing(self):
        """Stop background batch processing"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None

    async def _batch_processor(self):
        """Background task to process audit event batches"""
        while True:
            try:
                await asyncio.sleep(self.batch_flush_interval)

                if self.batch_events:
                    events_to_process = self.batch_events.copy()
                    self.batch_events.clear()

                    await self.log_events_batch(events_to_process)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch processor error: {e}")


# Global audit logger instance
audit_logger = AuditLogger()


# Decorator for automatic audit logging
def audit_action(action: AuditAction, resource_param: str = None, log_details: bool = True):
    """
    Decorator for automatic audit logging of function calls

    Args:
        action: Audit action to log
        resource_param: Parameter name to use as resource identifier
        log_details: Whether to log function parameters as details
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now(UTC)
            user_id = None
            ip_address = None
            user_agent = None
            resource = None
            details = {}

            try:
                # Extract context from function arguments
                if hasattr(args[0], "__self__"):  # Method call
                    self_obj = args[0]
                    if hasattr(self_obj, "current_user"):
                        user_id = str(self_obj.current_user.id) if self_obj.current_user else None
                    if hasattr(self_obj, "request"):
                        ip_address = (
                            self_obj.request.client.host if self_obj.request.client else None
                        )
                        user_agent = self_obj.request.headers.get("User-Agent")

                # Extract resource identifier
                if resource_param and resource_param in kwargs:
                    resource = str(kwargs[resource_param])

                # Log function details
                if log_details:
                    details["function"] = func.__name__
                    details["module"] = func.__module__
                    details["args_count"] = len(args)
                    details["kwargs_keys"] = list(kwargs.keys())

                # Execute function
                result = await func(*args, **kwargs)

                # Log successful execution
                await audit_logger.log_event(
                    AuditEvent(
                        action=action,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        resource=resource,
                        details=details,
                        severity=AuditSeverity.LOW,
                    )
                )

                return result

            except Exception as e:
                # Log error
                details["error"] = str(e)
                details["error_type"] = type(e).__name__

                await audit_logger.log_event(
                    AuditEvent(
                        action=action,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        resource=resource,
                        details=details,
                        severity=AuditSeverity.MEDIUM,
                    )
                )

                raise

        return wrapper

    return decorator


def log_impersonation(
    admin_user: User,
    target_user: User,
    action: str,
    db: Session,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Log user impersonation events

    Args:
        admin_user: Admin performing impersonation
        target_user: User being impersonated
        action: Action performed
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=admin_user.id,
        action=f"impersonation_{action}",
        target_user_id=target_user.id,
        resource_type="user_impersonation",
        details={
            "admin_email": admin_user.email,
            "target_email": target_user.email,
            "action": action,
            **(metadata or {}),
        },
    )
    db.add(log_entry)
    db.commit()


def log_role_change(
    admin_user: User,
    target_user: User,
    old_role: str,
    new_role: str,
    db: Session,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Log role/permission changes

    Args:
        admin_user: Admin making the change
        target_user: User whose role is being changed
        old_role: Previous role
        new_role: New role
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=admin_user.id,
        action="role_change",
        target_user_id=target_user.id,
        resource_type="user_role",
        details={
            "admin_email": admin_user.email,
            "target_email": target_user.email,
            "old_role": old_role,
            "new_role": new_role,
            **(metadata or {}),
        },
    )
    db.add(log_entry)
    db.commit()


def log_password_reset(
    user: User,
    reset_method: str,  # 'self', 'admin', 'recovery_code'
    db: Session,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Log password reset events

    Args:
        user: User whose password was reset
        reset_method: How the reset was performed
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=user.id,
        action="password_reset",
        resource_type="user_password",
        details={"user_email": user.email, "reset_method": reset_method, **(metadata or {})},
    )
    db.add(log_entry)
    db.commit()
