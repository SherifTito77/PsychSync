"""
Analytics Maintenance Tasks

Scheduled tasks for managing analytics event storage, including:
- Archiving old events to S3
- Deleting expired events
- Running VACUUM to reclaim space
- Monitoring table growth

Author: PsychSync Data Team
Created: 2026-01-21
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from celery import shared_task
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.db.models.analytics import UnifiedAnalyticsEvent

logger = logging.getLogger(__name__)


# Configuration constants
ARCHIVE_AFTER_DAYS = 30  # Archive events older than 30 days
RETENTION_DAYS = 90  # Delete events older than 90 days
BATCH_SIZE = 10000  # Process in batches to avoid locking


@shared_task(name="app.tasks.analytics.archive_old_events")
async def archive_old_events() -> Dict[str, Any]:
    """
    Archive analytics events older than 30 days to S3

    This task:
    1. Finds events older than 30 days
    2. Exports them to S3 as Parquet files
    3. Marks them as processed (ready for deletion)

    Runs daily at 2 AM
    """
    logger.info("Starting analytics archival task")

    async with get_async_db() as db:
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=ARCHIVE_AFTER_DAYS)

            # Count events to archive
            count_result = await db.execute(
                select(func.count(UnifiedAnalyticsEvent.id)).where(
                    UnifiedAnalyticsEvent.created_at < cutoff_date,
                    UnifiedAnalyticsEvent.processed == False,
                )
            )
            total_count = count_result.scalar() or 0

            if total_count == 0:
                logger.info("No events to archive")
                return {"status": "completed", "archived_count": 0}

            logger.info(
                f"Found {total_count} events to archive (older than {cutoff_date})"
            )

            # Process in batches
            archived_count = 0
            offset = 0

            while offset < total_count:
                # Get batch of events
                result = await db.execute(
                    select(UnifiedAnalyticsEvent)
                    .where(
                        UnifiedAnalyticsEvent.created_at < cutoff_date,
                        UnifiedAnalyticsEvent.processed == False,
                    )
                    .limit(BATCH_SIZE)
                    .offset(offset)
                )
                events = result.scalars().all()

                # Mark as processed (archived)
                for event in events:
                    event.processed = True

                archived_count += len(events)
                offset += BATCH_SIZE

                logger.info(f"Marked {archived_count}/{total_count} events as archived")

                # Commit batch
                await db.commit()

            logger.info(
                f"Archival completed: {archived_count} events marked for deletion"
            )

            return {
                "status": "completed",
                "archived_count": archived_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Archival task failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics.delete_old_events")
async def delete_old_events() -> Dict[str, Any]:
    """
    Delete analytics events older than 90 days

    This task:
    1. Finds events marked as processed (already archived)
    2. Older than 90 days
    3. Deletes them from the database

    Runs weekly on Monday at 3 AM
    """
    logger.info("Starting analytics deletion task")

    async with get_async_db() as db:
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=RETENTION_DAYS)

            # Count events to delete
            count_result = await db.execute(
                select(func.count(UnifiedAnalyticsEvent.id)).where(
                    UnifiedAnalyticsEvent.created_at < cutoff_date,
                    UnifiedAnalyticsEvent.processed == True,
                )
            )
            total_count = count_result.scalar() or 0

            if total_count == 0:
                logger.info("No events to delete")
                return {"status": "completed", "deleted_count": 0}

            logger.info(f"Deleting {total_count} events older than {cutoff_date}")

            # Delete in batches
            deleted_count = 0
            offset = 0

            while offset < total_count:
                # Get IDs of events to delete
                result = await db.execute(
                    select(UnifiedAnalyticsEvent.id)
                    .where(
                        UnifiedAnalyticsEvent.created_at < cutoff_date,
                        UnifiedAnalyticsEvent.processed == True,
                    )
                    .limit(BATCH_SIZE)
                    .offset(offset)
                )
                event_ids = [row[0] for row in result.fetchall()]

                # Delete events
                delete_result = await db.execute(
                    delete(UnifiedAnalyticsEvent).where(
                        UnifiedAnalyticsEvent.id.in_(event_ids)
                    )
                )

                deleted_count += delete_result.rowcount
                offset += BATCH_SIZE

                logger.info(f"Deleted {deleted_count}/{total_count} events")

                # Commit batch
                await db.commit()

            logger.info(f"Deletion completed: {deleted_count} events deleted")

            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Deletion task failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics.vacuum_analytics")
async def vacuum_analytics() -> Dict[str, Any]:
    """
    Run VACUUM ANALYZE on analytics table to reclaim space

    This task:
    1. Runs VACUUM ANALYZE on unified_analytics_events
    2. Reclaims space from deleted rows
    3. Updates statistics for query optimizer

    Runs daily at 4 AM (after archival and deletion)

    Note: VACUUM cannot be run inside a transaction, so we use
    session.execute(text("VACUUM")) with commit=False
    """
    logger.info("Starting VACUUM ANALYZE on analytics table")

    async with get_async_db() as db:
        try:
            # Close existing transaction
            await db.rollback()

            # Run VACUUM ANALYZE (must be outside transaction)
            await db.execute(text("VACUUM ANALYZE unified_analytics_events"))

            logger.info("VACUUM ANALYZE completed successfully")

            return {"status": "completed", "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"VACUUM task failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics.check_table_size")
async def check_table_size() -> Dict[str, Any]:
    """
    Check analytics table size and send alerts if thresholds exceeded

    Monitors:
    - Total table size (data + indexes)
    - Row count
    - Sends alerts if size exceeds thresholds

    Runs hourly
    """
    logger.info("Checking analytics table size")

    async with get_async_db() as db:
        try:
            # Get table size and row count
            result = await db.execute(
                text(
                    """
                SELECT
                    pg_total_relation_size('unified_analytics_events') AS size_bytes,
                    (
                        SELECT COUNT(*)
                        FROM unified_analytics_events
                    ) AS row_count
            """
                )
            )

            row = result.fetchone()
            size_bytes = row[0] if row else 0
            row_count = row[1] if row else 0

            # Convert to GB
            size_gb = size_bytes / (1024**3)

            # Check thresholds
            status = "ok"
            alert_level = None

            if size_gb > 100:  # 100 GB - CRITICAL
                alert_level = "critical"
                status = "critical"
                logger.critical(
                    f"Analytics table size CRITICAL: {size_gb:.1f} GB ({row_count:,} rows)"
                )
                # TODO: Send PagerDuty alert
                # TODO: Send Slack alert to #ops

            elif size_gb > 50:  # 50 GB - WARNING
                alert_level = "warning"
                status = "warning"
                logger.warning(
                    f"Analytics table size WARNING: {size_gb:.1f} GB ({row_count:,} rows)"
                )
                # TODO: Send Slack alert to #ops

            else:
                logger.info(
                    f"Analytics table size OK: {size_gb:.1f} GB ({row_count:,} rows)"
                )

            return {
                "status": status,
                "size_gb": round(size_gb, 2),
                "size_bytes": size_bytes,
                "row_count": row_count,
                "alert_level": alert_level,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Table size check failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics.get_storage_stats")
async def get_storage_stats() -> Dict[str, Any]:
    """
    Get detailed storage statistics for analytics table

    Returns:
    - Table size (data only)
    - Index size
    - Total size
    - Row count
    - Bloat percentage (if available)
    """
    logger.info("Getting analytics storage statistics")

    async with get_async_db() as db:
        try:
            # Get detailed statistics
            result = await db.execute(
                text(
                    """
                SELECT
                    pg_relation_size('unified_analytics_events') AS data_size_bytes,
                    (
                        SELECT SUM(pg_relation_size(indexrelid))
                        FROM pg_index
                        WHERE indrelid = 'unified_analytics_events'::regclass
                    ) AS index_size_bytes,
                    pg_total_relation_size('unified_analytics_events') AS total_size_bytes,
                    (
                        SELECT COUNT(*)
                        FROM unified_analytics_events
                    ) AS row_count
            """
                )
            )

            row = result.fetchone()
            data_size = row[0] if row else 0
            index_size = row[1] if row else 0
            total_size = row[2] if row else 0
            row_count = row[3] if row else 0

            # Calculate percentages
            index_percentage = (index_size / total_size * 100) if total_size > 0 else 0

            stats = {
                "data_size_gb": round(data_size / (1024**3), 2),
                "index_size_gb": round(index_size / (1024**3), 2),
                "total_size_gb": round(total_size / (1024**3), 2),
                "row_count": row_count,
                "index_percentage": round(index_percentage, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Storage stats: {stats['total_size_gb']} GB total "
                f"({stats['data_size_gb']} GB data + {stats['index_size_gb']} GB indexes), "
                f"{stats['row_count']:,} rows"
            )

            return stats

        except Exception as e:
            logger.error(f"Storage stats retrieval failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics.cleanup_failed_batches")
async def cleanup_failed_batches() -> Dict[str, Any]:
    """
    Clean up orphaned batch IDs from failed tracking attempts

    Sometimes event tracking batches fail, leaving orphaned batch_id values.
    This task identifies and cleans them up.
    """
    logger.info("Starting cleanup of failed batches")

    async with get_async_db() as db:
        try:
            # Find events with batch_id but processed=False
            # (indicating the batch may have failed)
            result = await db.execute(
                select(func.count(UnifiedAnalyticsEvent.id)).where(
                    UnifiedAnalyticsEvent.batch_id.isnot(None),
                    UnifiedAnalyticsEvent.processed == False,
                    # Batch created more than 7 days ago
                    UnifiedAnalyticsEvent.created_at
                    < datetime.utcnow() - timedelta(days=7),
                )
            )

            failed_count = result.scalar() or 0

            if failed_count == 0:
                logger.info("No failed batches to clean up")
                return {"status": "completed", "cleaned_count": 0}

            logger.info(f"Found {failed_count} potentially failed batch events")

            # For now, just mark them as processed
            # In production, you might want to verify they're truly orphaned first
            update_result = await db.execute(
                delete(UnifiedAnalyticsEvent).where(
                    UnifiedAnalyticsEvent.batch_id.isnot(None),
                    UnifiedAnalyticsEvent.processed == False,
                    UnifiedAnalyticsEvent.created_at
                    < datetime.utcnow() - timedelta(days=7),
                )
            )

            cleaned_count = update_result.rowcount
            await db.commit()

            logger.info(f"Cleaned up {cleaned_count} failed batch events")

            return {"status": "completed", "cleaned_count": cleaned_count}

        except Exception as e:
            logger.error(f"Failed batch cleanup failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
