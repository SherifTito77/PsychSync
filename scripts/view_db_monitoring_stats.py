#!/usr/bin/env python3
"""
Database Monitoring Statistics Viewer

This script provides real-time visibility into database errors and system health.

Usage:
    # View current statistics (last 5 minutes)
    python scripts/view_db_monitoring_stats.py

    # View specific time window
    python scripts/view_db_monitoring_stats.py --minutes 15

    # Generate full report
    python scripts/view_db_monitoring_stats.py --full-report

    # Watch mode (updates every 10 seconds)
    python scripts/view_db_monitoring_stats.py --watch
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.monitoring.database_error_monitor import db_monitor


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_stats(stats: dict):
    """Print statistics in formatted table."""
    print(f"\n📊 TIME WINDOW: Last {stats['time_window_minutes']} minutes")
    print(f"   Total Errors: {stats['total_errors']}")
    print(f"   Errors/Minute: {stats['errors_per_minute']:.2f}")
    print(f"   Uptime: {stats['uptime_percentage']:.2f}%")

    if stats['top_error_types']:
        print("\n🔴 TOP ERROR TYPES:")
        for error_type, count in stats['top_error_types']:
            bar = "█" * min(50, count * 2)
            print(f"   {error_type}: {count} {bar}")

    if stats['top_services']:
        print("\n🔧 TOP SERVICES WITH ERRORS:")
        for service, count in stats['top_services']:
            bar = "█" * min(50, count * 2)
            print(f"   {service}: {count} {bar}")


def print_health_check(stats: dict):
    """Print system health assessment."""
    errors_per_min = stats['errors_per_minute']
    uptime = stats['uptime_percentage']

    print("\n🏥 SYSTEM HEALTH:")

    if errors_per_min == 0 and uptime >= 99.9:
        print("   ✅ EXCELLENT - No errors detected")
        health_score = 100
    elif errors_per_min < 1 and uptime >= 99:
        print("   ✅ GOOD - Minimal errors")
        health_score = 90 + (uptime - 99) * 10
    elif errors_per_min < 5 and uptime >= 95:
        print("   ⚠️  FAIR - Moderate error rate")
        health_score = 70 + (uptime - 95) * 5
    elif errors_per_min < 10 and uptime >= 90:
        print("   🟡 DEGRADED - High error rate")
        health_score = 50 + (uptime - 90) * 4
    else:
        print("   🔴 CRITICAL - Excessive errors")
        health_score = max(0, 50 - errors_per_min * 2)

    print(f"   Health Score: {health_score:.1f}/100")

    if health_score < 70:
        print("\n   🚨 RECOMMENDED ACTIONS:")
        print("   - Check database connectivity")
        print("   - Review recent application logs")
        print("   - Verify database capacity")
        print("   - Check for long-running transactions")


def print_recent_errors(count: int = 10):
    """Print most recent errors."""
    print(f"\n📋 RECENT ERRORS (Last {count}):")

    recent_errors = list(db_monitor.error_history)[-count:]

    if not recent_errors:
        print("   ✅ No recent errors")
        return

    for error in recent_errors:
        timestamp = error['timestamp'][:19]  # Strip microseconds
        print(f"\n   [{timestamp}] {error['service']}.{error['operation']}")
        print(f"   Type: {error['error_type']}")
        print(f"   Message: {error['error_message'][:80]}{'...' if len(error['error_message']) > 80 else ''}")

        if error.get('context'):
            print(f"   Context: {error['context']}")


def generate_actionable_insights(stats: dict):
    """Generate actionable insights from statistics."""
    print("\n💡 ACTIONABLE INSIGHTS:")

    insights = []

    # Check error rate
    if stats['errors_per_minute'] > 10:
        insights.append("🚨 CRITICAL: Error rate exceeds 10 errors/min")
        insights.append("   → Check database connection pool")
        insights.append("   → Review recent deployments")
        insights.append("   → Check database server health")
    elif stats['errors_per_minute'] > 5:
        insights.append("⚠️  WARNING: Elevated error rate detected")
        insights.append("   → Monitor for degradation")

    # Check specific error types
    error_types = dict(stats['top_error_types'])
    if 'IntegrityError' in error_types and error_types['IntegrityError'] > 5:
        insights.append("🔒 Multiple integrity errors (constraint violations)")
        insights.append("   → Review business logic for race conditions")
        insights.append("   → Check unique constraint violations")

    if 'OperationalError' in error_types and error_types['OperationalError'] > 5:
        insights.append("🔌 Multiple operational errors (connection issues)")
        insights.append("   → Check database connectivity")
        insights.append("   → Verify network stability")

    # Check top services
    if stats['top_services']:
        top_service, top_count = stats['top_services'][0]
        if top_count > stats['total_errors'] * 0.5:
            insights.append(f"🎯 {top_count}% of errors from {top_service}")
            insights.append(f"   → Review {top_service} for issues")

    if not insights:
        insights.append("✅ No specific issues detected")
        insights.append("   → System operating normally")

    for insight in insights:
        print(f"   {insight}")


def view_stats(minutes: int = 5, full_report: bool = False):
    """View current monitoring statistics."""
    print_header("DATABASE ERROR MONITORING DASHBOARD")
    print(f"Generated: {datetime.utcnow().isoformat()}")
    print(f"Monitor Uptime: {datetime.utcnow() - db_monitor.start_time}")
    print(f"Total Errors Tracked: {len(db_monitor.error_history)}")

    # Get statistics
    stats = db_monitor.get_error_stats(minutes=minutes)
    print_stats(stats)
    print_health_check(stats)
    print_recent_errors()
    generate_actionable_insights(stats)

    if full_report:
        print("\n" + db_monitor.generate_report())

    print("\n" + "=" * 80)


def watch_mode(interval: int = 10):
    """Continuously monitor and update statistics."""
    import time

    print_header("DATABASE MONITORING - WATCH MODE")
    print(f"Updating every {interval} seconds... (Ctrl+C to exit)\n")

    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n🔄 Update #{iteration} - {datetime.utcnow().strftime('%H:%M:%S')}")

            stats = db_monitor.get_error_stats(minutes=5)
            print_stats(stats)
            print_health_check(stats)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n✅ Watch mode stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View database error monitoring statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View last 5 minutes
  python scripts/view_db_monitoring_stats.py

  # View last 15 minutes
  python scripts/view_db_monitoring_stats.py --minutes 15

  # Full detailed report
  python scripts/view_db_monitoring_stats.py --full-report

  # Watch mode (auto-refresh)
  python scripts/view_db_monitoring_stats.py --watch

  # Watch mode with custom interval
  python scripts/view_db_monitoring_stats.py --watch --interval 30
        """
    )

    parser.add_argument(
        "--minutes",
        type=int,
        default=5,
        help="Time window in minutes (default: 5)"
    )

    parser.add_argument(
        "--full-report",
        action="store_true",
        help="Generate full detailed report"
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Enable watch mode (auto-refresh)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Watch mode refresh interval in seconds (default: 10)"
    )

    args = parser.parse_args()

    # Check if monitor has any data
    if len(db_monitor.error_history) == 0:
        print("⚠️  No monitoring data available yet.")
        print("   The monitoring system may not have started, or no errors have occurred.")
        print("   Start the application to begin monitoring.\n")
        print("   To start standalone monitoring:")
        print("   python scripts/start_db_monitoring.py\n")
        return

    # Run appropriate mode
    if args.watch:
        watch_mode(args.interval)
    else:
        view_stats(args.minutes, args.full_report)


if __name__ == "__main__":
    main()
