"""
Security Logging System

Provides structured, tamper-evident logging for security events with:
- Multiple log schemas (auth, privilege, tool, data, model events)
- Automatic data redaction for PII and sensitive information
- Hash-chain integrity verification
- SIEM streaming integration
- Real-time threat detection

Usage:
    from app.security.logging import security_logger

    # Log authentication event
    await security_logger.log_auth_event(
        event_type="login_success",
        user_id="user_123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0..."
    )

    # Log privilege change
    await security_logger.log_privilege_change(
        user_id="user_123",
        action="role_granted",
        old_role="user",
        new_role="admin",
        changed_by="admin_456"
    )
"""

from app.security.logging.detection import SecurityEventDetector, get_detector
from app.security.logging.integrity import LogIntegrityManager, get_integrity_manager
from app.security.logging.logger import SecurityLogger, get_security_logger, security_logger
from app.security.logging.redaction import DataRedactor, get_redactor
from app.security.logging.schemas import (
    AuthEvent,
    DataAccessEvent,
    EventSeverity,
    EventType,
    ModelEvent,
    PrivilegeChangeEvent,
    SecurityEvent,
    ToolInvocationEvent,
)
from app.security.logging.siem import SIEMConfig, SIEMStreamer, SIEMType

__all__ = [
    "AuthEvent",
    "DataAccessEvent",
    "DataRedactor",
    "EventSeverity",
    "EventType",
    "LogIntegrityManager",
    "ModelEvent",
    "PrivilegeChangeEvent",
    "SIEMConfig",
    "SIEMStreamer",
    "SIEMType",
    "SecurityEvent",
    "SecurityEventDetector",
    "SecurityLogger",
    "ToolInvocationEvent",
    "get_detector",
    "get_integrity_manager",
    "get_redactor",
    "get_security_logger",
    "security_logger",
]
