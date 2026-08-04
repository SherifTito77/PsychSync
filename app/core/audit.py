"""
Legacy audit module adapter.
Redirects to new audit_logger and audit_logging modules.
"""

import logging

from app.core.audit_logging import AuditAction, AuditLogger, audit_action

# Initialize logger
logger = logging.getLogger(__name__)


# Standardize log_security_event to AuditLogger method
def log_security_event(*args, **kwargs):
    """Legacy wrapper for log_security_event"""
    return AuditLogger.log_security_event(*args, **kwargs)


# Export names for backward compatibility
__all__ = ["audit_action", "log_security_event", "AuditAction"]
