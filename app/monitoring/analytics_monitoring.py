"""
Analytics Table Monitoring Service

Comprehensive monitoring for analytics table bloat and performance.
Provides alerts, metrics, and recommendations for maintaining healthy table size.

Author: PsychSync Data Team
Created: 2026-01-21
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db

logger = logging.getLogger(__name__)


class AnalyticsTableMonitor:
    """
    Monitor analytics table size, bloat, and performance.

    Provides:
    - Table size tracking
    - Bloat detection
    - Alerting on thresholds
    - Growth rate analysis
    - Recommendations
    """

    # Alert thresholds
    WARNING_THRESHOLD_GB = 50  # 50 GB
    CRITICAL_THRESHOLD_GB = 100  # 100 GB

    # Performance thresholds
    SLOW_QUERY_THRESHOLD_MS = 1000  # 1 second
    HIGH_BLOAT_THRESHOLD_PCT = 30  # 30% bloat

    def __init__(self):
        self.db: Optional[AsyncSession] = None

    async def get_table_health(self) -> Dict[str, Any]:
        """
        Get comprehensive table health metrics

        Returns:
            Dict containing:
            - size_metrics: Table size information
            - row_counts: Current row counts
            - bloat_metrics: Bloat percentage
            - index_metrics: Index size and efficiency
            - growth_metrics: Growth rate over time
            - alert_level: Current alert status (ok/warning/critical)
            - recommendations: List of actionable recommendations
        """
        self.db = get_async_db()

        try:
            # Gather all metrics
            size_metrics = await self._get_size_metrics()
            row_metrics = await self._get_row_metrics()
            bloat_metrics = await self._get_bloat_metrics()
            index_metrics = await self._get_index_metrics()
            growth_metrics = await self._get_growth_metrics()

            # Determine alert level
            alert_level = self._calculate_alert_level(size_metrics)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                size_metrics, bloat_metrics, index_metrics, growth_metrics
            )

            health_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "size_metrics": size_metrics,
                "row_metrics": row_metrics,
                "bloat_metrics": bloat_metrics,
                "index_metrics": index_metrics,
                "growth_metrics": growth_metrics,
                "alert_level": alert_level,
                "recommendations": recommendations,
            }

            # Log status
            self._log_health_status(health_report)

            return health_report

        finally:
            await self.db.close()

    async def _get_size_metrics(self) -> Dict[str, Any]:
        """Get table size metrics"""
        result = await self.db.execute(
            text(
                """
            SELECT
                pg_total_relation_size('unified_analytics_events') AS total_size_bytes,
                pg_relation_size('unified_analytics_events') AS data_size_bytes,
                (
                    pg_total_relation_size('unified_analytics_events') -
                    pg_relation_size('unified_analytics_events')
                ) AS index_size_bytes
        """
            )
        )

        row = result.fetchone()
        total_size = row[0] if row else 0
        data_size = row[1] if row else 0
        index_size = row[2] if row else 0

        return {
            "total_size_gb": round(total_size / (1024**3), 2),
            "data_size_gb": round(data_size / (1024**3), 2),
            "index_size_gb": round(index_size / (1024**3), 2),
            "index_percentage": round(
                (index_size / total_size * 100) if total_size > 0 else 0, 2
            ),
        }

    async def _get_row_metrics(self) -> Dict[str, Any]:
        """Get row count metrics"""
        result = await self.db.execute(
            text(
                """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) AS recent_7_days,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) AS recent_30_days,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '90 days' THEN 1 END) AS recent_90_days,
                MIN(created_at) AS oldest_event,
                MAX(created_at) AS newest_event
            FROM unified_analytics_events
        """
            )
        )

        row = result.fetchone()

        return {
            "total_rows": row[0] if row else 0,
            "recent_7_days": row[1] if row else 0,
            "recent_30_days": row[2] if row else 0,
            "recent_90_days": row[3] if row else 0,
            "oldest_event": row[4].isoformat() if row and row[4] else None,
            "newest_event": row[5].isoformat() if row and row[5] else None,
        }

    async def _get_bloat_metrics(self) -> Dict[str, Any]:
        """Get table and index bloat metrics"""
        result = await self.db.execute(
            text(
                """
            SELECT
                pg_size_pretty(pg_total_relation_size('unified_analytics_events')) AS total_size,
                pg_stat_get_dead_tuples(c.oid) AS dead_tuples
            FROM pg_class c
            WHERE c.relname = 'unified_analytics_events'
        """
            )
        )

        row = result.fetchone()

        # Estimate bloat percentage
        dead_tuples = row[1] if row else 0

        # Get total tuples
        total_result = await self.db.execute(
            text(
                """
            SELECT reltuples::bigint AS total_tuples
            FROM pg_class
            WHERE relname = 'unified_analytics_events'
        """
            )
        )
        total_tuples = total_result.scalar() or 1

        bloat_percentage = (
            round((dead_tuples / total_tuples * 100), 2) if total_tuples > 0 else 0
        )

        return {
            "dead_tuples": dead_tuples,
            "total_tuples_estimated": total_tuples,
            "bloat_percentage": bloat_percentage,
            "needs_vacuum": bloat_percentage > self.HIGH_BLOAT_THRESHOLD_PCT,
        }

    async def _get_index_metrics(self) -> Dict[str, Any]:
        """Get index usage and size metrics"""
        result = await self.db.execute(
            text(
                """
            SELECT
                indexrelname AS index_name,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
                idx_scan AS index_scans,
                idx_tup_read AS tuples_read,
                idx_tup_fetch AS tuples_fetched
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
              AND relname = 'unified_analytics_events'
            ORDER BY pg_relation_size(indexrelid) DESC
        """
            )
        )

        indexes = []
        for row in result:
            indexes.append(
                {
                    "name": row[0],
                    "size": row[1],
                    "scans": row[2],
                    "tuples_read": row[3],
                    "tuples_fetched": row[4],
                    "unused": row[2] == 0,  # Never scanned
                }
            )

        return {
            "total_indexes": len(indexes),
            "unused_indexes": len([i for i in indexes if i["unused"]]),
            "indexes": indexes[:10],  # Top 10 largest
        }

    async def _get_growth_metrics(self) -> Dict[str, Any]:
        """Calculate growth rate over time"""
        result = await self.db.execute(
            text(
                """
            WITH daily_counts AS (
                SELECT
                    DATE_TRUNC('day', created_at) AS day,
                    COUNT(*) AS daily_count
                FROM unified_analytics_events
                WHERE created_at > NOW() - INTERVAL '30 days'
                GROUP BY day
                ORDER BY day DESC
                LIMIT 30
            )
            SELECT
                AVG(daily_count) AS avg_daily_rows,
                MAX(daily_count) AS max_daily_rows,
                MIN(daily_count) AS min_daily_rows
            FROM daily_counts
        """
            )
        )

        row = result.fetchone()

        # Calculate growth per day
        avg_daily = row[0] if row else 0

        return {
            "avg_daily_rows": round(avg_daily) if avg_daily else 0,
            "max_daily_rows": row[1] if row else 0,
            "min_daily_rows": row[2] if row else 0,
            "estimated_monthly_growth_gb": round(
                (avg_daily * 0.001) if avg_daily else 0, 2  # Assume 1 KB per row
            ),
        }

    def _calculate_alert_level(self, size_metrics: Dict[str, Any]) -> str:
        """Calculate alert level based on table size"""
        total_size_gb = size_metrics.get("total_size_gb", 0)

        if total_size_gb >= self.CRITICAL_THRESHOLD_GB:
            return "critical"
        elif total_size_gb >= self.WARNING_THRESHOLD_GB:
            return "warning"
        else:
            return "ok"

    def _generate_recommendations(
        self,
        size_metrics: Dict[str, Any],
        bloat_metrics: Dict[str, Any],
        index_metrics: Dict[str, Any],
        growth_metrics: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []

        # Size-based recommendations
        total_size_gb = size_metrics.get("total_size_gb", 0)
        if total_size_gb > self.WARNING_THRESHOLD_GB:
            recommendations.append(
                f"Table size ({total_size_gb} GB) exceeds warning threshold. "
                f"Consider running archival and deletion tasks."
            )

        # Bloat-based recommendations
        if bloat_metrics.get("needs_vacuum", False):
            recommendations.append(
                f"High bloat detected ({bloat_metrics['bloat_percentage']}%). "
                f"Run VACUUM ANALYZE immediately."
            )

        # Index-based recommendations
        unused_count = index_metrics.get("unused_indexes", 0)
        if unused_count > 0:
            recommendations.append(
                f"Found {unused_count} unused indexes. "
                f"Consider dropping them to improve write performance."
            )

        # Growth-based recommendations
        monthly_growth = growth_metrics.get("estimated_monthly_growth_gb", 0)
        if monthly_growth > 5:  # Growing more than 5 GB per month
            recommendations.append(
                f"High growth rate detected ({monthly_growth} GB/month). "
                f"Consider implementing table partitioning or reducing retention period."
            )

        # Index size recommendation
        index_percentage = size_metrics.get("index_percentage", 0)
        if index_percentage > 50:
            recommendations.append(
                f"Indexes are {index_percentage}% of total size. "
                f"Review index necessity and consider partial indexes."
            )

        if not recommendations:
            recommendations.append("Table health is good. No immediate action needed.")

        return recommendations

    def _log_health_status(self, health_report: Dict[str, Any]):
        """Log health status with appropriate level"""
        alert_level = health_report.get("alert_level", "ok")
        size_gb = health_report["size_metrics"]["total_size_gb"]
        row_count = health_report["row_metrics"]["total_rows"]

        if alert_level == "critical":
            logger.critical(
                f"Analytics table CRITICAL: {size_gb} GB, {row_count:,} rows. "
                f"Recommendations: {health_report['recommendations']}"
            )
        elif alert_level == "warning":
            logger.warning(
                f"Analytics table WARNING: {size_gb} GB, {row_count:,} rows. "
                f"Recommendations: {health_report['recommendations']}"
            )
        else:
            logger.info(f"Analytics table OK: {size_gb} GB, {row_count:,} rows")


# Singleton instance
_analytics_monitor: Optional[AnalyticsTableMonitor] = None


def get_analytics_monitor() -> AnalyticsTableMonitor:
    """Get singleton analytics monitor instance"""
    global _analytics_monitor
    if _analytics_monitor is None:
        _analytics_monitor = AnalyticsTableMonitor()
    return _analytics_monitor


# Standalone functions for quick checks
async def check_table_size() -> Dict[str, Any]:
    """Quick check of table size (for alerts)"""
    monitor = AnalyticsTableMonitor()
    metrics = await monitor.get_table_health()
    return {
        "size_gb": metrics["size_metrics"]["total_size_gb"],
        "alert_level": metrics["alert_level"],
    }


async def check_needs_vacuum() -> bool:
    """Check if table needs VACUUM"""
    monitor = AnalyticsTableMonitor()
    metrics = await monitor.get_table_health()
    return metrics["bloat_metrics"]["needs_vacuum"]


async def get_unused_indexes() -> List[str]:
    """Get list of unused indexes"""
    monitor = AnalyticsTableMonitor()
    metrics = await monitor.get_table_health()

    unused_indexes = []
    for index in metrics["index_metrics"]["indexes"]:
        if index.get("unused", False):
            unused_indexes.append(index["name"])

    return unused_indexes
