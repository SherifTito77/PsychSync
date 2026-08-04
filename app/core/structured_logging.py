# app/core/structured_logging.py
"""
Structured Logging System for PsychSync
Provides consistent, searchable logs for production monitoring and debugging
"""

import json
import logging
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """Log levels for structured logging"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Event types for categorization"""

    API_CALL = "api_call"
    BUSINESS_EVENT = "business_event"
    DATABASE_OPERATION = "database_operation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_EVENT = "system_event"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_EVENT = "error_event"
    INFO_EVENT = "info_event"
    WARNING_EVENT = "warning_event"
    CRITICAL_EVENT = "critical_event"


@dataclass
class LogContext:
    """Context information for log entries"""

    request_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    method: str | None = None
    organization_id: str | None = None
    team_id: str | None = None


class LogEvent:
    """Structured log event"""

    def __init__(
        self,
        timestamp: str,
        level: str,
        event_type: str,
        message: str,
        context: dict[str, Any],
        operation_name: str | None = None,
        duration_ms: float | None = None,
        error_details: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ):
        self.timestamp = timestamp
        self.level = level
        self.event_type = event_type
        self.message = message
        self.context = context.copy() if context else {}
        self.operation_name = operation_name
        self.duration_ms = duration_ms
        self.error_details = error_details
        self.metadata = metadata

        # Add any additional keyword arguments to context
        for key, value in kwargs.items():
            if key not in self.context:
                self.context[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert log event to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "event_type": self.event_type,
            "message": self.message,
            "context": self.context,
            "operation_name": self.operation_name,
            "duration_ms": self.duration_ms,
            "error_details": self.error_details,
            "metadata": self.metadata,
        }


class StructuredLogger:
    """
    Enhanced logger with structured output and context management
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.logger = logging.getLogger(module_name)
        self._context = LogContext()

    def set_context(self, **kwargs):
        """Set context information for subsequent log entries"""
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)

    def clear_context(self):
        """Clear all context information"""
        self._context = LogContext()

    def _create_log_entry(
        self, level: LogLevel, event_type: EventType, message: str, **kwargs
    ) -> LogEvent:
        """Create a structured log entry"""
        return LogEvent(
            timestamp=datetime.utcnow().isoformat(),
            level=level.value,
            event_type=event_type.value,
            message=message,
            context=asdict(self._context),
            **kwargs,
        )

    def _log(self, level: LogLevel, event_type: EventType, message: str, **kwargs):
        """Internal logging method"""
        log_entry = self._create_log_entry(level, event_type, message, **kwargs)
        log_line = json.dumps(log_entry.to_dict(), default=str)

        # Map to standard logging levels
        if level == LogLevel.DEBUG:
            self.logger.debug(log_line)
        elif level == LogLevel.INFO:
            self.logger.info(log_line)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_line)
        elif level == LogLevel.ERROR:
            self.logger.error(log_line)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_line)

    def debug(self, event_type: EventType, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, event_type, message, **kwargs)

    def info(self, event_type: EventType, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, event_type, message, **kwargs)

    def warning(self, event_type: EventType, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, event_type, message, **kwargs)

    def error(self, event_type_or_message, message=None, **kwargs):
        """Log error message with compatibility for both structured and standard logging"""
        if message is None:
            # Called with standard logging interface: error(message)
            message = event_type_or_message
            event_type = EventType.ERROR_EVENT
        else:
            # Called with structured interface: error(event_type, message)
            event_type = event_type_or_message
        self._log(LogLevel.ERROR, event_type, message, **kwargs)

    def critical(self, event_type_or_message, message=None, **kwargs):
        """Log critical message with compatibility for both structured and standard logging"""
        if message is None:
            # Called with standard logging interface: critical(message)
            message = event_type_or_message
            event_type = EventType.CRITICAL_EVENT
        else:
            # Called with structured interface: critical(event_type, message)
            event_type = event_type_or_message
        self._log(LogLevel.CRITICAL, event_type, message, **kwargs)

    def info(self, event_type_or_message, message=None, **kwargs):
        """Log info message with compatibility for both structured and standard logging"""
        if message is None:
            # Called with standard logging interface: info(message)
            message = event_type_or_message
            event_type = EventType.INFO_EVENT
        else:
            # Called with structured interface: info(event_type, message)
            event_type = event_type_or_message
        self._log(LogLevel.INFO, event_type, message, **kwargs)

    def warning(self, event_type_or_message, message=None, **kwargs):
        """Log warning message with compatibility for both structured and standard logging"""
        if message is None:
            # Called with standard logging interface: warning(message)
            message = event_type_or_message
            event_type = EventType.WARNING_EVENT
        else:
            # Called with structured interface: warning(event_type, message)
            event_type = event_type_or_message
        self._log(LogLevel.WARNING, event_type, message, **kwargs)

    # Specific logging methods for common operations

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        user_id: str,
        status_code: int,
        duration_ms: float,
        **kwargs,
    ):
        """Log API call with structured data"""
        self.info(
            EventType.API_CALL,
            f"{method} {endpoint}",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_business_event(
        self, event_name: str, user_id: str, resource_id: str = None, **kwargs
    ):
        """Log business events with structured data"""
        self.info(
            EventType.BUSINESS_EVENT,
            f"Business event: {event_name}",
            operation_name=event_name,
            resource_id=resource_id,
            **kwargs,
        )

    def log_database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float = None,
        record_count: int = None,
        success: bool = True,
        **kwargs,
    ):
        """Log database operations"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Database operation: {operation} on {table}"

        self._log(
            level,
            EventType.DATABASE_OPERATION,
            message,
            operation_name=operation,
            table=table,
            duration_ms=duration_ms,
            record_count=record_count,
            success=success,
            **kwargs,
        )

    def log_authentication_event(
        self,
        event_name: str,
        user_id: str = None,
        email: str = None,
        success: bool = True,
        ip_address: str = None,
        **kwargs,
    ):
        """Log authentication events"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Authentication: {event_name}"

        self._log(
            level,
            EventType.AUTHENTICATION,
            message,
            operation_name=event_name,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            success=success,
            **kwargs,
        )

    def log_authorization_event(
        self, resource: str, action: str, user_id: str, success: bool = True, **kwargs
    ):
        """Log authorization events"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Authorization: {action} on {resource}"

        self._log(
            level,
            EventType.AUTHORIZATION,
            message,
            operation_name=action,
            resource=resource,
            user_id=user_id,
            success=success,
            **kwargs,
        )

    def log_validation_error(
        self, field: str, value: Any, constraint: str, operation: str = None, **kwargs
    ):
        """Log validation errors"""
        self.warning(
            EventType.VALIDATION_ERROR,
            f"Validation failed for field: {field}",
            operation_name=operation,
            field=field,
            value=str(value),
            constraint=constraint,
            **kwargs,
        )

    def log_error(
        self, error: Exception, operation: str = None, user_id: str = None, **kwargs
    ):
        """Log errors with full context"""
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

        self.error(
            EventType.ERROR_EVENT,
            f"Error in operation: {operation or 'unknown'}",
            operation_name=operation,
            user_id=user_id,
            error_details=error_details,
            **kwargs,
        )

    def log_performance_metric(
        self, metric_name: str, value: float | int, unit: str = None, **kwargs
    ):
        """Log performance metrics"""
        self.info(
            EventType.PERFORMANCE_METRIC,
            f"Performance metric: {metric_name}",
            operation_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs,
        )

    def log_system_event(self, event_name: str, **kwargs):
        """Log system events"""
        self.info(
            EventType.SYSTEM_EVENT,
            f"System event: {event_name}",
            operation_name=event_name,
            **kwargs,
        )


# Global logger factory
def get_logger(module_name: str) -> StructuredLogger:
    """Get a structured logger for the given module"""
    return StructuredLogger(module_name)


# Convenience function for getting logger with __name__
def get_module_logger() -> StructuredLogger:
    """Get structured logger for current module"""
    import inspect

    frame = inspect.currentframe().f_back
    module_name = frame.f_globals["__name__"]
    return get_logger(module_name)


# Enhanced log aggregation and alerting system
# Collects error logs, analyzes patterns, and sends alerts for critical issues


class LogAnalyzer:
    """
    Analyzes log patterns and generates alerts for critical issues
    """

    def __init__(self):
        self.error_threshold = 10  # Alert after 10 errors in 5 minutes
        self.error_count = {}
        self.last_alert_time = {}

    def analyze_log_entry(self, log_entry: dict[str, Any]):
        """Analyze a log entry and generate alerts if needed"""
        if log_entry.get("level") == "error":
            self._track_error(log_entry)

        # Additional analysis logic here
        # - Error rate monitoring
        # - Performance degradation detection
        # - Security event monitoring
        # - Resource utilization tracking

    def _track_error(self, log_entry: dict[str, Any]):
        """Track error occurrences and alert if threshold exceeded"""
        import time

        error_type = log_entry.get("error_details", {}).get("error_type", "unknown")
        current_time = time.time()

        if error_type not in self.error_count:
            self.error_count[error_type] = []

        # Add current error timestamp
        self.error_count[error_type].append(current_time)

        # Remove old errors (older than 5 minutes)
        self.error_count[error_type] = [
            timestamp
            for timestamp in self.error_count[error_type]
            if current_time - timestamp < 300  # 5 minutes
        ]

        # Check if threshold exceeded
        if len(self.error_count[error_type]) >= self.error_threshold:
            self._send_alert(error_type, len(self.error_count[error_type]))

    def _send_alert(self, error_type: str, count: int):
        """Send alert for high error rate"""
        import time

        current_time = time.time()

        # Prevent alert spam (max one alert per hour per error type)
        if (
            error_type in self.last_alert_time
            and current_time - self.last_alert_time[error_type] < 3600
        ):
            return

        self.last_alert_time[error_type] = current_time

        # Send alert (implementation depends on your alerting system)
        alert_message = (
            f"High error rate detected: {count} {error_type} errors in 5 minutes"
        )

        # This could integrate with:
        # - Email notifications
        # - Slack alerts
        # - PagerDuty
        # - Monitoring systems
        # - Error tracking services

        print(f"ALERT: {alert_message}")  # Replace with actual alerting system


# Global log analyzer instance
log_analyzer = LogAnalyzer()
