"""
Database Error Monitoring and Alerting System

This module provides comprehensive monitoring for database operations:
- Tracks all database errors in real-time
- Provides alerting for critical failures
- Generates error reports and analytics
- Integrates with existing logging infrastructure

Usage:
    from app.monitoring.database_error_monitor import DatabaseErrorMonitor, monitor_db_errors

    # Enable monitoring for a function
    @monitor_db_errors
    async def my_function(db):
        pass

    # Or use the monitor directly
    monitor = DatabaseErrorMonitor()
    monitor.log_error("user_service", "create_user", error)
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
)
from sqlalchemy.exc import TimeoutError as DBTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseErrorMonitor:
    """
    Centralized database error monitoring system.

    Features:
    - Real-time error tracking
    - Error rate monitoring
    - Pattern detection (spikes, frequent errors)
    - Alert generation
    - Historical analysis
    """

    def __init__(self, max_history: int = 1000, alert_threshold: int = 10):
        """
        Initialize the database error monitor.

        Args:
            max_history: Maximum number of errors to keep in memory
            alert_threshold: Errors per minute before triggering alert
        """
        self.max_history = max_history
        self.alert_threshold = alert_threshold

        # Error tracking
        self.error_history = deque(maxlen=max_history)
        self.error_counts = defaultdict(int)
        self.error_by_service = defaultdict(lambda: defaultdict(int))
        self.error_by_operation = defaultdict(lambda: defaultdict(int))

        # Timing
        self.start_time = datetime.utcnow()
        self.last_alert_time = None
        self.alert_cooldown = timedelta(minutes=5)

        # Lock for thread safety
        self._lock = asyncio.Lock()

    def log_error(
        self,
        service: str,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a database error for monitoring.

        Args:
            service: Service name (e.g., "user_service", "assessment_service")
            operation: Operation name (e.g., "create", "update", "delete")
            error: The exception that occurred
            context: Additional context (user_id, record_id, etc.)
        """
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": service,
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        # Add to history
        self.error_history.append(error_info)

        # Update counts
        error_key = f"{service}:{operation}:{type(error).__name__}"
        self.error_counts[error_key] += 1
        self.error_by_service[service][type(error).__name__] += 1
        self.error_by_operation[operation][type(error).__name__] += 1

        # Log to standard logger
        logger.error(
            f"DB Error [{service}.{operation}]: {type(error).__name__}: {error}",
            extra={
                "service": service,
                "operation": operation,
                "error_type": type(error).__name__,
                **(context or {}),
            },
            exc_info=True,
        )

        # Check if we need to alert
        asyncio.create_task(self._check_and_alert(error_info))

    async def _check_and_alert(self, error_info: Dict[str, Any]):
        """Check if error rate exceeds threshold and send alerts."""
        async with self._lock:
            # Check recent error rate
            now = datetime.utcnow()
            recent_errors = [
                e
                for e in self.error_history
                if datetime.fromisoformat(e["timestamp"]) > now - timedelta(minutes=1)
            ]

            if len(recent_errors) >= self.alert_threshold:
                # Check cooldown
                if (
                    self.last_alert_time is None
                    or now - self.last_alert_time > self.alert_cooldown
                ):
                    self.last_alert_time = now
                    await self._send_alert(recent_errors)

    async def _send_alert(self, errors: List[Dict[str, Any]]):
        """Send alert for high error rate."""
        # Group by service/operation
        error_summary = defaultdict(int)
        for error in errors:
            key = f"{error['service']}.{error['operation']}"
            error_summary[key] += 1

        # Create alert message
        alert_message = f"🚨 DATABASE ERROR ALERT 🚨\n"
        alert_message += f"Time: {datetime.utcnow().isoformat()}\n"
        alert_message += f"Total Errors (last minute): {len(errors)}\n\n"
        alert_message += "Error Breakdown:\n"
        for key, count in sorted(error_summary.items(), key=lambda x: -x[1]):
            alert_message += f"  - {key}: {count} errors\n"

        # Log critical alert
        logger.critical(alert_message)

        # In production, send to external monitoring systems
        # - Slack/Teams webhook
        # - Email
        # - PagerDuty
        # - DataDog/NewRelic

        if settings.ENVIRONMENT == "production":
            await self._send_external_alert(alert_message, error_summary)

    async def _send_external_alert(self, message: str, error_summary: Dict[str, int]):
        """Send alert to external monitoring systems."""
        # TODO: Implement external alert integrations
        # - Slack webhook
        # - Email notification
        # - PagerDuty
        # - Monitoring platforms
        pass

    def get_error_stats(self, minutes: int = 5) -> Dict[str, Any]:
        """
        Get error statistics for the last N minutes.

        Args:
            minutes: Time window to analyze

        Returns:
            Dictionary with error statistics
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent_errors = [
            e
            for e in self.error_history
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        # Calculate stats
        total_errors = len(recent_errors)
        errors_per_minute = total_errors / max(minutes, 1)

        # Top errors
        error_types = defaultdict(int)
        for error in recent_errors:
            error_types[error["error_type"]] += 1

        top_errors = sorted(error_types.items(), key=lambda x: -x[1])[:10]

        # Top services
        services = defaultdict(int)
        for error in recent_errors:
            services[error["service"]] += 1

        top_services = sorted(services.items(), key=lambda x: -x[1])[:10]

        return {
            "time_window_minutes": minutes,
            "total_errors": total_errors,
            "errors_per_minute": errors_per_minute,
            "top_error_types": top_errors,
            "top_services": top_services,
            "uptime_percentage": (
                (1 - errors_per_minute / 100) * 100 if errors_per_minute > 0 else 100
            ),
        }

    def generate_report(self) -> str:
        """Generate a comprehensive error report."""
        stats = self.get_error_stats(minutes=60)

        report = "\n" + "=" * 80 + "\n"
        report += "DATABASE ERROR MONITORING REPORT\n"
        report += "=" * 80 + "\n\n"

        report += f"Report Generated: {datetime.utcnow().isoformat()}\n"
        report += f"Monitor Uptime: {datetime.utcnow() - self.start_time}\n\n"

        report += "LAST 60 MINUTES:\n"
        report += f"  Total Errors: {stats['total_errors']}\n"
        report += f"  Errors/Minute: {stats['errors_per_minute']:.2f}\n"
        report += f"  Uptime: {stats['uptime_percentage']:.2f}%\n\n"

        if stats["top_error_types"]:
            report += "TOP ERROR TYPES:\n"
            for error_type, count in stats["top_error_types"]:
                report += f"  {error_type}: {count}\n"
            report += "\n"

        if stats["top_services"]:
            report += "TOP SERVICES WITH ERRORS:\n"
            for service, count in stats["top_services"]:
                report += f"  {service}: {count}\n"
            report += "\n"

        # Recent errors
        report += "RECENT ERRORS (Last 10):\n"
        for error in list(self.error_history)[-10:]:
            report += f"  [{error['timestamp']}] {error['service']}.{error['operation']}: {error['error_type']}\n"

        report += "\n" + "=" * 80 + "\n"

        return report

    def clear_history(self):
        """Clear error history."""
        self.error_history.clear()
        self.error_counts.clear()
        self.error_by_service.clear()
        self.error_by_operation.clear()
        logger.info("Database error monitor history cleared")


# Global monitor instance
db_monitor = DatabaseErrorMonitor(
    max_history=10000, alert_threshold=getattr(settings, "DB_ERROR_ALERT_THRESHOLD", 10)
)


def monitor_db_errors(service: str):
    """
    Decorator to automatically monitor database errors in a function.

    Usage:
        @monitor_db_errors("user_service")
        async def create_user(db, user_data):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (
                IntegrityError,
                OperationalError,
                ProgrammingError,
                SQLAlchemyError,
            ) as e:
                db_monitor.log_error(
                    service=service,
                    operation=func.__name__,
                    error=e,
                    context={"args": str(args)[:200]},  # Limit context size
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (
                IntegrityError,
                OperationalError,
                ProgrammingError,
                SQLAlchemyError,
            ) as e:
                db_monitor.log_error(
                    service=service,
                    operation=func.__name__,
                    error=e,
                    context={"args": str(args)[:200]},
                )
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@asynccontextmanager
async def monitored_db_operation(
    service: str,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for monitoring database operations.

    Usage:
        async with monitored_db_operation("user_service", "create_user", {"user_id": user_id}):
            result = await db.execute(...)
            await db.commit()
    """
    try:
        yield
    except (IntegrityError, OperationalError, ProgrammingError, SQLAlchemyError) as e:
        db_monitor.log_error(
            service=service,
            operation=operation,
            error=e,
            context=context,
        )
        raise


async def start_database_error_monitoring(
    report_interval_minutes: int = 60,
    alert_on_patterns: bool = True,
):
    """
    Start background database error monitoring.

    This function runs in the background and:
    - Generates periodic reports
    - Checks for error patterns
    - Sends alerts when needed

    Args:
        report_interval_minutes: How often to generate reports
        alert_on_patterns: Whether to alert on error patterns
    """
    logger.info("Starting database error monitoring...")

    while True:
        try:
            await asyncio.sleep(report_interval_minutes * 60)

            # Generate report
            report = db_monitor.generate_report()
            logger.info(report)

            # Check for patterns
            if alert_on_patterns:
                stats = db_monitor.get_error_stats(minutes=10)

                # Alert on high error rate
                if stats["errors_per_minute"] > 5:
                    logger.warning(
                        f"High database error rate detected: {stats['errors_per_minute']:.2f} errors/min"
                    )

        except asyncio.CancelledError:
            logger.info("Database error monitoring stopped")
            break
        except Exception as e:
            logger.error(f"Error in database monitoring: {e}", exc_info=True)


# Convenience functions for common operations


def log_integrity_error(service: str, operation: str, error: IntegrityError, **context):
    """Log an integrity error (constraint violation)."""
    db_monitor.log_error(service, operation, error, context=context)


def log_operational_error(
    service: str, operation: str, error: OperationalError, **context
):
    """Log an operational error (connection issue, timeout, etc.)."""
    db_monitor.log_error(service, operation, error, context=context)


def log_timeout_error(service: str, operation: str, error: DBTimeoutError, **context):
    """Log a timeout error."""
    db_monitor.log_error(service, operation, error, context=context)


def log_generic_db_error(
    service: str, operation: str, error: SQLAlchemyError, **context
):
    """Log a generic database error."""
    db_monitor.log_error(service, operation, error, context=context)
