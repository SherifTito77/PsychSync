"""
Monitoring package initialization

This module initializes all monitoring systems when the application starts.
"""

from app.monitoring.database_error_monitor import (
    DatabaseErrorMonitor,
    db_monitor,
    monitor_db_errors,
    monitored_db_operation,
    start_database_error_monitoring,
)

__all__ = [
    "DatabaseErrorMonitor",
    "db_monitor",
    "monitor_db_errors",
    "monitored_db_operation",
    "start_database_error_monitoring",
]
