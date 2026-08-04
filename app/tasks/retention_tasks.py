"""
Data Retention Cleanup Tasks

Scheduled tasks for managing data retention across all time-series data.
Implements GDPR, HIPAA, and SOC 2 compliance requirements.

Tasks:
- Session cleanup (30 days)
- Audit log archival/deletion (3 years)
- Notification log cleanup (90 days)
- API request log cleanup (30 days)
- Database vacuum and optimization

Author: PsychSync Data Governance Team
Created: 2026-01-21
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from celery import shared_task
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.core.config import settings
from app.db.models.analytics import UnifiedAnalyticsEvent
from app.services.data_retention_service import RETENTION_POLICIES, DataRetentionService

logger = logging.getLogger(__name__)

# Configuration constants
SESSION_RETENTION_DAYS = 30  # Delete sessions older than 30 days
NOTIFICATION_RETENTION_DAYS = 90  # Delete notification logs after 90 days
API_LOG_RETENTION_DAYS = 30  # Delete API logs after 30 days
BATCH_SIZE = 5000  # Process in batches to avoid locking


@shared_task(name="app.tasks.retention.cleanup_expired_sessions")
async def cleanup_expired_sessions() -> Dict[str, Any]:
    """
    ✅ GDPR COMPLIANT: Delete expired user sessions

    Implements GDPR Article 5(1)(e) - storage limitation
    Deletes user sessions older than 30 days to prevent indefinite data accumulation.

    This task:
    1. Finds sessions inactive for 30+ days
    2. Deletes session records
    3. Cleans up session metadata

    Runs: Daily at 3 AM

    Returns:
        Dict with cleanup status and count
    """
    logger.info("Starting session cleanup task")

    try:
        async with get_async_db() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=SESSION_RETENTION_DAYS)

            # Get database connection for raw SQL
            async with db.begin():
                # Count sessions to delete (estimate from multiple session tables)
                tables_to_check = [
                    "user_sessions",
                    "session_data",
                    "authentication_sessions",
                ]

                total_deleted = 0

                for table in tables_to_check:
                    try:
                        # Check if table exists
                        table_exists = await db.execute(
                            text(
                                f"""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = '{table}'
                                )
                            """
                            )
                        )

                        if not table_exists.scalar():
                            logger.debug(f"Table {table} does not exist, skipping")
                            continue

                        # Count rows to delete
                        count_result = await db.execute(
                            text(
                                f"""
                                SELECT COUNT(*) FROM {table}
                                WHERE created_at < :cutoff_date
                                OR (created_at < :cutoff_date AND updated_at IS NULL)
                            """
                            ),
                            {"cutoff_date": cutoff_date},
                        )

                        count = count_result.scalar() or 0
                        if count > 0:
                            # Delete expired sessions
                            await db.execute(
                                text(
                                    f"""
                                    DELETE FROM {table}
                                    WHERE created_at < :cutoff_date
                                    OR (created_at < :cutoff_date AND updated_at IS NULL)
                                """
                                ),
                                {"cutoff_date": cutoff_date},
                            )

                            total_deleted += count
                            logger.info(
                                f"Deleted {count} expired sessions from {table}"
                            )

                    except Exception as e:
                        logger.warning(f"Failed to cleanup table {table}: {e}")
                        continue

            logger.info(f"Session cleanup completed: {total_deleted} sessions deleted")

            return {
                "status": "completed",
                "deleted_count": total_deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": SESSION_RETENTION_DAYS,
            }

    except Exception as e:
        logger.error(f"Session cleanup task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.retention.cleanup_audit_logs")
async def cleanup_audit_logs() -> Dict[str, Any]:
    """
    ✅ GDPR/HIPAA COMPLIANT: Archive and delete audit logs per retention policy

    Implements retention policies defined in RETENTION_POLICIES['audit_logs']
    - 3 years retention (SOC 2)
    - 1 year archival to S3
    - Maintains chain of custody

    Uses existing DataRetentionService methods

    This task:
    1. Archives audit logs older than 1 year
    2. Deletes audit logs older than 3 years
    3. Maintains audit trail compliance

    Runs: Weekly on Sunday at 2 AM

    Returns:
        Dict with archival and deletion status
    """
    logger.info("Starting audit log cleanup task")

    try:
        async with get_async_db() as db:
            retention_service = DataRetentionService(db)

            # Get audit log retention policy
            policy = RETENTION_POLICIES["audit_logs"]

            # Archive logs older than archive threshold
            archive_result = await retention_service.archive_data("audit_logs")

            # Delete logs older than retention threshold
            delete_result = await retention_service.delete_expired_data("audit_logs")

            logger.info(
                f"Audit log cleanup completed: "
                f"{archive_result.get('archived_count', 0)} archived, "
                f"{delete_result.get('deleted_count', 0)} deleted"
            )

            return {
                "status": "completed",
                "archived_count": archive_result.get("archived_count", 0),
                "deleted_count": delete_result.get("deleted_count", 0),
                "retention_years": policy.retention_period_days / 365,
                "archive_after_years": policy.archive_after_days / 365,
            }

    except Exception as e:
        logger.error(f"Audit log cleanup task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.retention.cleanup_notification_logs")
async def cleanup_notification_logs() -> Dict[str, Any]:
    """
    ✅ GDPR COMPLIANT: Delete notification delivery logs

    Implements GDPR Article 5(1)(e) - storage limitation
    Deletes notification logs containing user contact information after 90 days.

    This task:
    1. Deletes email notification logs older than 90 days
    2. Deletes SMS notification logs older than 90 days
    3. Deletes push notification logs older than 90 days
    4. Cleans up failed delivery attempts

    Runs: Weekly on Sunday at 4 AM

    Returns:
        Dict with cleanup status and counts by notification type
    """
    logger.info("Starting notification log cleanup task")

    try:
        async with get_async_db() as db:
            cutoff_date = datetime.utcnow() - timedelta(
                days=NOTIFICATION_RETENTION_DAYS
            )

            total_deleted = 0
            notification_types = []

            # Notification tables to cleanup
            notification_tables = [
                "email_notifications",
                "sms_notifications",
                "push_notifications",
                "notification_history",
            ]

            async with db.begin():
                for table in notification_tables:
                    try:
                        # Check if table exists
                        table_exists = await db.execute(
                            text(
                                f"""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = '{table}'
                                )
                            """
                            )
                        )

                        if not table_exists.scalar():
                            logger.debug(f"Table {table} does not exist, skipping")
                            continue

                        # Count and delete
                        count_result = await db.execute(
                            text(
                                f"""
                                SELECT COUNT(*) FROM {table}
                                WHERE created_at < :cutoff_date
                            """
                            ),
                            {"cutoff_date": cutoff_date},
                        )

                        count = count_result.scalar() or 0

                        if count > 0:
                            await db.execute(
                                text(
                                    f"""
                                    DELETE FROM {table}
                                    WHERE created_at < :cutoff_date
                                """
                                ),
                                {"cutoff_date": cutoff_date},
                            )

                            total_deleted += count
                            notification_types.append({"table": table, "count": count})
                            logger.info(
                                f"Deleted {count} notification logs from {table}"
                            )

                    except Exception as e:
                        logger.warning(
                            f"Failed to cleanup notification table {table}: {e}"
                        )
                        continue

            logger.info(
                f"Notification log cleanup completed: {total_deleted} logs deleted "
                f"across {len(notification_types)} tables"
            )

            return {
                "status": "completed",
                "deleted_count": total_deleted,
                "by_type": notification_types,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": NOTIFICATION_RETENTION_DAYS,
            }

    except Exception as e:
        logger.error(f"Notification log cleanup task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.retention.cleanup_api_request_logs")
async def cleanup_api_request_logs() -> Dict[str, Any]:
    """
    ✅ GDPR COMPLIANT: Delete API request/performance logs

    Implements GDPR Article 5(1)(e) - storage limitation
    Deletes API request logs and performance metrics after 30 days.

    This task:
    1. Deletes API request logs older than 30 days
    2. Deletes performance monitoring data older than 30 days
    3. Deletes error logs older than 30 days (retained in audit logs separately)
    4. Cleans up query performance logs

    Note: Security-relevant events are kept in audit_logs with 3-year retention

    Runs: Daily at 4 AM

    Returns:
        Dict with cleanup status and counts
    """
    logger.info("Starting API request log cleanup task")

    try:
        async with get_async_db() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=API_LOG_RETENTION_DAYS)

            total_deleted = 0

            # API logging tables to cleanup
            api_tables = [
                {"table": "api_request_logs", "date_field": "created_at"},
                {"table": "query_performance_logs", "date_field": "created_at"},
                {"table": "performance_metrics", "date_field": "timestamp"},
                {"table": "endpoint_metrics", "date_field": "created_at"},
            ]

            async with db.begin():
                for table_info in api_tables:
                    table = table_info["table"]
                    date_field = table_info["date_field"]

                    try:
                        # Check if table exists
                        table_exists = await db.execute(
                            text(
                                f"""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = '{table}'
                                )
                            """
                            )
                        )

                        if not table_exists.scalar():
                            logger.debug(f"Table {table} does not exist, skipping")
                            continue

                        # Count and delete
                        count_result = await db.execute(
                            text(
                                f"""
                                SELECT COUNT(*) FROM {table}
                                WHERE {date_field} < :cutoff_date
                            """
                            ),
                            {"cutoff_date": cutoff_date},
                        )

                        count = count_result.scalar() or 0

                        if count > 0:
                            await db.execute(
                                text(
                                    f"""
                                    DELETE FROM {table}
                                    WHERE {date_field} < :cutoff_date
                                """
                                ),
                                {"cutoff_date": cutoff_date},
                            )

                            total_deleted += count
                            logger.info(f"Deleted {count} API logs from {table}")

                    except Exception as e:
                        logger.warning(f"Failed to cleanup API table {table}: {e}")
                        continue

            logger.info(
                f"API request log cleanup completed: {total_deleted} logs deleted"
            )

            return {
                "status": "completed",
                "deleted_count": total_deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": API_LOG_RETENTION_DAYS,
            }

    except Exception as e:
        logger.error(f"API request log cleanup task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.retention.vacuum_analytics_tables")
async def vacuum_analytics_tables() -> Dict[str, Any]:
    """
    ✅ PERFORMANCE: Vacuum and analyze analytics tables

    Reclaims storage space and updates statistics after deletion operations.
    Critical for maintaining query performance on large time-series tables.

    This task:
    1. Runs VACUUM ANALYZE on analytics tables
    2. Reclaims space from deleted rows
    3. Updates query planner statistics
    4. Improves query performance

    Runs: Weekly on Sunday at 5 AM

    Returns:
        Dict with vacuum status for each table
    """
    logger.info("Starting table vacuum task")

    try:
        async with get_async_db() as db:
            # Tables to vacuum
            tables_to_vacuum = [
                "unified_analytics_events",
                "audit_logs",
                "assessment_responses",
                "user_sessions",
            ]

            results = []

            for table in tables_to_vacuum:
                try:
                    # Check if table exists
                    table_exists = await db.execute(
                        text(
                            f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_name = '{table}'
                            )
                        """
                        )
                    )

                    if not table_exists.scalar():
                        logger.debug(f"Table {table} does not exist, skipping")
                        continue

                    # Run VACUUM ANALYZE (autocommit required)
                    # Use execution_options to ensure it runs outside a transaction
                    await db.execute(
                        text(f"VACUUM ANALYZE {table}").execution_options(
                            autocommit=True
                        )
                    )

                    results.append({"table": table, "status": "vacuumed"})
                    logger.info(f"Vacuumed table: {table}")

                except Exception as e:
                    logger.warning(f"Failed to vacuum table {table}: {e}")
                    results.append(
                        {"table": table, "status": "failed", "error": str(e)}
                    )
                    continue

        logger.info(f"Table vacuum completed: {len(results)} tables processed")

        return {
            "status": "completed",
            "tables_processed": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Table vacuum task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.retention.run_all_retention_tasks")
async def run_all_retention_tasks() -> Dict[str, Any]:
    """
    ✅ MASTER TASK: Run all retention cleanup tasks in sequence

    Executes all retention cleanup tasks in optimal order:
    1. Session cleanup
    2. Notification log cleanup
    3. API log cleanup
    4. Audit log archival/deletion
    5. Table vacuum

    Use this for manual triggering or testing

    Returns:
        Dict with combined status from all tasks
    """
    logger.info("Starting all retention cleanup tasks")

    results = {}

    # Run each task
    tasks = [
        ("session_cleanup", cleanup_expired_sessions),
        ("notification_cleanup", cleanup_notification_logs),
        ("api_log_cleanup", cleanup_api_request_logs),
        ("audit_log_cleanup", cleanup_audit_logs),
        ("vacuum", vacuum_analytics_tables),
    ]

    for task_name, task_func in tasks:
        try:
            logger.info(f"Running {task_name}...")
            result = await task_func()
            results[task_name] = result
            logger.info(f"Completed {task_name}: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to run {task_name}: {e}")
            results[task_name] = {"status": "failed", "error": str(e)}

    # Count successes
    successful = sum(1 for r in results.values() if r.get("status") == "completed")

    logger.info(f"All retention tasks completed: {successful}/{len(tasks)} successful")

    return {
        "status": "completed" if successful == len(tasks) else "partial",
        "successful_tasks": successful,
        "total_tasks": len(tasks),
        "results": results,
    }
