# app/core/secure_logging.py
"""
Secure logging system that prevents sensitive data leakage.

Features:
- Automatic redaction of sensitive patterns (passwords, tokens, SSNs, credit cards)
- JSON structured logging for log aggregation
- Request ID tracking for distributed tracing
- Security event categorization
"""

import json
import logging
import re
import sys
from contextlib import contextmanager
from typing import Any


class SensitiveDataFilter(logging.Filter):
    """
    Filter to prevent sensitive data from being logged.

    Redacts:
    - Passwords
    - JWT tokens
    - API keys
    - Credit card numbers
    - SSNs
    - Secret keys
    """

    # Patterns to redact (order matters - most specific first)
    SENSITIVE_PATTERNS = [
        # JWT tokens
        (r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "***JWT***"),
        # Passwords in various formats
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', "password=***REDACTED***"),
        (r'"password"\s*:\s*"[^"]*"', '"password": "***REDACTED***"'),
        (r"'password'\s*:\s*'[^']*'", "'password': '***REDACTED***'"),
        # Tokens
        (
            r'access_token["\']?\s*[:=]\s*["\']?[^"\'}\s]+',
            "access_token=***REDACTED***",
        ),
        (
            r'refresh_token["\']?\s*[:=]\s*["\']?[^"\'}\s]+',
            "refresh_token=***REDACTED***",
        ),
        (r'api_key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', "api_key=***REDACTED***"),
        (r'secret["\']?\s*[:=]\s*["\']?[^"\'}\s]+', "secret=***REDACTED***"),
        (r'key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', "key=***REDACTED***"),
        # Credit card numbers (16 digits with spaces/dashes)
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "***CARD***"),
        # SSN (###-##-#### format)
        (r"\b\d{3}-\d{2}-\d{4}\b", "***SSN***"),
        # API keys/secret patterns
        (r"\b[A-Za-z0-9]{32,}\b", "***SECRET***"),  # Long alphanumeric strings
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter sensitive data from log records.

        Args:
            record: Log record to filter

        Returns:
            True (log the record)
        """
        # Redact from message
        record.msg = self._redact(record.msg)

        # Redact from args if present
        if record.args:
            record.args = tuple(
                self._redact(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )

        return True

    def _redact(self, text: str) -> str:
        """
        Redact sensitive patterns from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text


class SecureFormatter(logging.Formatter):
    """
    Secure log formatter with JSON output and sanitization.

    Features:
    - JSON format for structured logging
    - Automatic sanitization of sensitive data
    - Request/user context tracking
    - Security event categorization
    """

    def __init__(self):
        super().__init__()
        self.filter = SensitiveDataFilter()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as sanitized JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Sanitize message
        sanitized_msg = self.filter._redact(record.getMessage())

        # Build structured log entry
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_msg,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add contextual information if available
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = self.filter._redact(record.ip_address)
        if hasattr(record, "security_event"):
            log_entry["security_event"] = record.security_event

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


@contextmanager
def log_context(**kwargs):
    """
    Add contextual information to log records within a context.

    Usage:
        with log_context(user_id="123", request_id="abc"):
            logger.info("Processing request")

    Args:
        **kwargs: Contextual key-value pairs
    """

    class ContextFilter(logging.Filter):
        def __init__(self, context):
            super().__init__()
            self.context = context

        def filter(self, record):
            for key, value in self.context.items():
                setattr(record, key, value)
            return True

    # Get root logger
    logger = logging.getLogger()
    context_filter = ContextFilter(kwargs)

    # Add temporary filter
    logger.addFilter(context_filter)

    try:
        yield
    finally:
        # Remove filter after context
        logger.removeFilter(context_filter)


def configure_secure_logging(log_level: str = "INFO", log_file: str | None = None):
    """
    Configure secure logging for the application.

    Rules:
    - No print() statements (use logging module)
    - All log output goes through sensitive data filter
    - JSON format for structured logging
    - Different log levels for different environments

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    # Remove default handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Create secure formatter
    formatter = SecureFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(file_handler)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Secure logging initialized at {log_level} level")

    return logger


class SecurityLogger:
    """
    Specialized logger for security events.

    Categories:
    - AUTH: Authentication events (login, logout, token refresh)
    - AUTHZ: Authorization events (permission checks, access denied)
    - DATA: Data access events (sensitive data access)
    - RATE_LIMIT: Rate limiting events
    - VALIDATION: Input validation failures
    - SYSTEM: System security events
    """

    CATEGORIES = {
        "AUTH": "Authentication",
        "AUTHZ": "Authorization",
        "DATA": "Data Access",
        "RATE_LIMIT": "Rate Limiting",
        "VALIDATION": "Input Validation",
        "SYSTEM": "System Security",
    }

    def __init__(self):
        self.logger = logging.getLogger("security")

    def log_security_event(
        self,
        user_id: Any,
        event_type: str,
        details: str,
        client_ip: str = "unknown",
        severity: str = "INFO",
    ):
        """
        Log a security event.

        Args:
            user_id: User ID (or None for anonymous)
            event_type: Type of security event
            details: Event details
            client_ip: Client IP address
            severity: Event severity (INFO, WARNING, ERROR)
        """
        level = getattr(logging, severity.upper(), logging.INFO)

        self.logger.log(
            level,
            details,
            extra={
                "user_id": str(user_id) if user_id else "anonymous",
                "security_event": event_type,
                "ip_address": client_ip,
            },
        )

    def log_auth_event(
        self, user_id: Any, action: str, success: bool, client_ip: str = "unknown"
    ):
        """Log authentication event."""
        severity = "INFO" if success else "WARNING"
        details = f"Authentication {action}: {'SUCCESS' if success else 'FAILED'}"

        self.log_security_event(
            user_id=user_id,
            event_type=f"AUTH_{action.upper()}",
            details=details,
            client_ip=client_ip,
            severity=severity,
        )

    def log_authz_event(
        self,
        user_id: Any,
        resource: str,
        action: str,
        success: bool,
        client_ip: str = "unknown",
    ):
        """Log authorization event."""
        severity = "INFO" if success else "WARNING"
        details = f"Authorization {action} on {resource}: {'GRANTED' if success else 'DENIED'}"

        self.log_security_event(
            user_id=user_id,
            event_type=f"AUTHZ_{action.upper()}",
            details=details,
            client_ip=client_ip,
            severity=severity,
        )

    def log_data_access(
        self,
        user_id: Any,
        resource_type: str,
        resource_id: Any,
        action: str,
        client_ip: str = "unknown",
    ):
        """Log sensitive data access."""
        details = f"Data access: {action} on {resource_type} {resource_id}"

        self.log_security_event(
            user_id=user_id,
            event_type="DATA_ACCESS",
            details=details,
            client_ip=client_ip,
            severity="INFO",
        )


# Singleton instance
security_logger = SecurityLogger()
