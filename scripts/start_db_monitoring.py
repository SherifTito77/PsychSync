#!/usr/bin/env python3
"""
Database Monitoring Startup Script

This script starts the database error monitoring system as a background service.
It generates periodic reports and sends alerts when error thresholds are exceeded.

Usage:
    python scripts/start_db_monitoring.py

    # Or run in background:
    nohup python scripts/start_db_monitoring.py > /var/log/db_monitoring.log 2>&1 &

    # Or use systemd/supervisord for production
"""

import asyncio
import signal
import sys
from pathlib import path

# Add project root to path
project_root = path.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.monitoring.database_error_monitor import (
    db_monitor,
    start_database_error_monitoring,
)


async def main():
    """Main monitoring loop."""
    print("=" * 80)
    print("DATABASE ERROR MONITORING SYSTEM")
    print("=" * 80)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(
        f"Alert Threshold: {settings.get('DB_ERROR_ALERT_THRESHOLD', 10)} errors/minute"
    )
    print(f"Report Interval: 60 minutes")
    print("\nStarting monitoring...\n")

    # Create monitoring task
    monitor_task = asyncio.create_task(
        start_database_error_monitoring(
            report_interval_minutes=60,
            alert_on_patterns=True,
        )
    )

    # Setup graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down monitoring system...")
        monitor_task.cancel()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep running
    try:
        await monitor_task
    except asyncio.CancelledError:
        print("Monitoring stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)
