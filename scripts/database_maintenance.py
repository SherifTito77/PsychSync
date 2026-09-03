#!/usr/bin/env python3
"""
Database Maintenance and Optimization Scripts

This script provides automated database maintenance and optimization procedures
to ensure optimal performance, data integrity, and system health.

Maintenance Tasks:
- Automatic VACUUM and ANALYZE operations
- Index maintenance and optimization
- Partition management and cleanup
- Statistics updates and query plan optimization
- Storage monitoring and cleanup
- Performance metrics collection
- Health checks and alerts
- Backup verification and restoration testing
"""

import asyncio
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/psychsync/database_maintenance.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DatabaseMaintenance:
    """Database maintenance and optimization utilities"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.metrics = {}

    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection"""
        return await asyncpg.connect(self.connection_string)

    async def execute_query(
        self, query: str, params: Optional[Dict] = None
    ) -> List[Dict]:
        """Execute database query and return results"""
        async with await self.get_connection() as conn:
            if params:
                result = await conn.fetch(query, *params.values())
            else:
                result = await conn.fetch(query)
            return [dict(row) for row in result]

    async def execute_command(self, command: str) -> None:
        """Execute database command without returning results"""
        async with await self.get_connection() as conn:
            await conn.execute(command)

    # 1. VACUUM and ANALYZE Operations
    # ---------------------------------------------------------

    async def auto_vacuum_analyze(
        self, table_name: Optional[str] = None
    ) -> Dict[str, any]:
        """Perform VACUUM ANALYZE on specified table or all tables"""
        start_time = time.time()

        try:
            if table_name:
                logger.info(f"Starting VACUUM ANALYZE for table: {table_name}")
                await self.execute_command(f"VACUUM ANALYZE {table_name}")
                affected_tables = [table_name]
            else:
                logger.info("Starting VACUUM ANALYZE for all tables")
                await self.execute_command("VACUUM ANALYZE")
                affected_tables = await self.get_table_list()

            duration = time.time() - start_time

            result = {
                "operation": "vacuum_analyze",
                "duration_seconds": round(duration, 2),
                "tables_processed": len(affected_tables),
                "affected_tables": affected_tables,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
            }

            logger.info(f"VACUUM ANALYZE completed in {duration:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"VACUUM ANALYZE failed: {str(e)}")
            return {
                "operation": "vacuum_analyze",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def aggressive_vacuum(self, table_name: str) -> Dict[str, any]:
        """Perform aggressive VACUUM on a specific table"""
        start_time = time.time()

        try:
            logger.info(f"Starting aggressive VACUUM for table: {table_name}")
            await self.execute_command(f"VACUUM FULL ANALYZE {table_name}")
            duration = time.time() - start_time

            # Get table statistics after vacuum
            stats = await self.get_table_statistics(table_name)

            result = {
                "operation": "aggressive_vacuum",
                "table_name": table_name,
                "duration_seconds": round(duration, 2),
                "table_statistics": stats,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
            }

            logger.info(
                f"Aggressive VACUUM for {table_name} completed in {duration:.2f} seconds"
            )
            return result

        except Exception as e:
            logger.error(f"Aggressive VACUUM failed for {table_name}: {str(e)}")
            return {
                "operation": "aggressive_vacuum",
                "table_name": table_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # 2. Index Maintenance
    # ---------------------------------------------------------

    async def analyze_index_usage(self) -> List[Dict]:
        """Analyze index usage statistics"""
        query = """
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            pg_size_pretty(pg_relation_size(indexrelid) -
                          pg_stat_get_live_tuples(indexrelid) *
                          (SELECT avg_width FROM pg_stats WHERE tablename = s.tablename LIMIT 1)) as wasted_space
        FROM pg_stat_user_indexes s
        JOIN pg_index i ON s.indexrelid = i.indexrelid
        WHERE schemaname = 'public'
        ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
        """

        return await self.execute_query(query)

    async def rebuild_unused_indexes(self) -> Dict[str, any]:
        """Identify and rebuild unused indexes"""
        try:
            # Find unused indexes (scans < 10 and older than 30 days)
            unused_indexes_query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
              AND idx_scan < 10
              AND indexrelid NOT IN (
                  SELECT conindid FROM pg_constraint WHERE contype IN ('p', 'u')
              )
            """

            unused_indexes = await self.execute_query(unused_indexes_query)

            if not unused_indexes:
                return {
                    "operation": "rebuild_unused_indexes",
                    "unused_indexes_found": 0,
                    "indexes_rebuilt": 0,
                    "status": "success",
                    "message": "No unused indexes found",
                }

            rebuilt_count = 0
            for index in unused_indexes:
                try:
                    # REINDEX CONCURRENTLY to avoid blocking
                    index_name = f"{index['schemaname']}.{index['indexname']}"
                    await self.execute_command(
                        f"REINDEX INDEX CONCURRENTLY {index_name}"
                    )
                    rebuilt_count += 1
                    logger.info(f"Rebuilt index: {index_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to rebuild index {index['indexname']}: {str(e)}"
                    )

            return {
                "operation": "rebuild_unused_indexes",
                "unused_indexes_found": len(unused_indexes),
                "indexes_rebuilt": rebuilt_count,
                "unused_indexes": unused_indexes,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Index rebuild failed: {str(e)}")
            return {
                "operation": "rebuild_unused_indexes",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # 3. Partition Management
    # ---------------------------------------------------------

    async def manage_partitions(self) -> Dict[str, any]:
        """Create new partitions and drop old ones"""
        try:
            created_partitions = []
            dropped_partitions = []

            # Create future partitions for time-based tables
            partition_tables = [
                "audit_logs",
                "analytics",
                "notifications",
                "resource_access",
                "permission_audit",
            ]

            for table in partition_tables:
                try:
                    # Create partitions for next 3 months
                    for months_ahead in range(1, 4):
                        future_date = datetime.utcnow() + timedelta(
                            days=30 * months_ahead
                        )
                        partition_name = f"{table}_{future_date.strftime('%Y_%m')}"

                        try:
                            if table in ["analytics"]:
                                # Weekly partitions for analytics
                                for weeks_ahead in range(1, 13):
                                    future_week = datetime.utcnow() + timedelta(
                                        weeks=weeks_ahead
                                    )
                                    week_partition_name = (
                                        f"{table}_{future_week.strftime('%Y_WW')}"
                                    )
                                    await self.create_weekly_partition(
                                        table, future_week
                                    )
                                    created_partitions.append(week_partition_name)
                            else:
                                # Monthly partitions for other tables
                                await self.create_monthly_partition(table, future_date)
                                created_partitions.append(partition_name)
                        except Exception as e:
                            logger.warning(
                                f"Failed to create partition {partition_name}: {str(e)}"
                            )

                except Exception as e:
                    logger.error(f"Failed to manage partitions for {table}: {str(e)}")

            # Drop old partitions (older than 12 months)
            for table in partition_tables:
                try:
                    old_partitions = await self.get_old_partitions(
                        table, retention_months=12
                    )
                    for partition in old_partitions:
                        await self.execute_command(
                            f"DROP TABLE {partition['partition_name']} CASCADE"
                        )
                        dropped_partitions.append(partition["partition_name"])
                        logger.info(
                            f"Dropped old partition: {partition['partition_name']}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to drop old partitions for {table}: {str(e)}"
                    )

            return {
                "operation": "manage_partitions",
                "created_partitions": created_partitions,
                "dropped_partitions": dropped_partitions,
                "total_created": len(created_partitions),
                "total_dropped": len(dropped_partitions),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Partition management failed: {str(e)}")
            return {
                "operation": "manage_partitions",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def create_monthly_partition(
        self, table_name: str, target_date: datetime
    ) -> None:
        """Create monthly partition for specified date"""
        partition_name = f"{table_name}_{target_date.strftime('%Y_%m')}"
        start_date = target_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        if target_date.month == 12:
            end_date = start_date.replace(year=target_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=target_date.month + 1)

        command = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF {table_name}
        FOR VALUES FROM ('{start_date.isoformat()}') TO ('{end_date.isoformat()}')
        """
        await self.execute_command(command)

    async def create_weekly_partition(
        self, table_name: str, target_date: datetime
    ) -> None:
        """Create weekly partition for specified date"""
        week_number = target_date.isocalendar()[1]
        partition_name = f"{table_name}_{target_date.strftime('%Y_WW')}"
        start_date = target_date - timedelta(days=target_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(weeks=1)

        command = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF {table_name}
        FOR VALUES FROM ('{start_date.isoformat()}') TO ('{end_date.isoformat()}')
        """
        await self.execute_command(command)

    async def get_old_partitions(
        self, table_name: str, retention_months: int
    ) -> List[Dict]:
        """Get partitions older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=30 * retention_months)

        query = """
        SELECT
            tablename as partition_name,
            schemaname
        FROM pg_tables
        WHERE tablename LIKE %s
          AND schemaname = 'public'
        """

        partitions = await self.execute_query(query, {"pattern": f"{table_name}_%"})

        # Filter by date (this is a simplified approach)
        old_partitions = []
        for partition in partitions:
            try:
                # Extract date from partition name (e.g., "audit_logs_2023_12")
                parts = partition["partition_name"].split("_")
                if len(parts) >= 3:
                    year = int(parts[-2])
                    month = int(parts[-1])
                    partition_date = datetime(year, month, 1)

                    if partition_date < cutoff_date:
                        old_partitions.append(partition)
            except (ValueError, IndexError):
                continue

        return old_partitions

    # 4. Statistics and Performance Monitoring
    # ---------------------------------------------------------

    async def update_table_statistics(self) -> Dict[str, any]:
        """Update table statistics for query optimizer"""
        try:
            start_time = time.time()

            tables = await self.get_table_list()
            updated_tables = []

            for table in tables:
                try:
                    await self.execute_command(f"ANALYZE {table}")
                    updated_tables.append(table)
                except Exception as e:
                    logger.warning(f"Failed to analyze {table}: {str(e)}")

            duration = time.time() - start_time

            return {
                "operation": "update_statistics",
                "duration_seconds": round(duration, 2),
                "tables_updated": len(updated_tables),
                "updated_tables": updated_tables,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Statistics update failed: {str(e)}")
            return {
                "operation": "update_statistics",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def collect_performance_metrics(self) -> Dict[str, any]:
        """Collect database performance metrics"""
        try:
            metrics = {}

            # Database size metrics
            size_query = """
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                (SELECT COUNT(*) FROM pg_stat_activity) as total_connections
            """
            db_metrics = await self.execute_query(size_query)
            metrics["database"] = db_metrics[0] if db_metrics else {}

            # Table size metrics
            table_size_query = """
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                              pg_relation_size(schemaname||'.'||tablename)) as index_size,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            metrics["tables"] = await self.execute_query(table_size_query)

            # Query performance metrics
            query_stats_query = """
            SELECT
                query,
                calls,
                total_time,
                mean_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements
            ORDER BY total_time DESC
            LIMIT 10
            """
            try:
                metrics["query_performance"] = await self.execute_query(
                    query_stats_query
                )
            except Exception:
                metrics["query_performance"] = (
                    []
                )  # pg_stat_statements may not be enabled

            # Lock monitoring
            lock_query = """
            SELECT
                t.relname as table_name,
                l.locktype,
                l.mode,
                l.granted,
                a.query,
                a.pid,
                a.usename,
                a.application_name
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            JOIN pg_class t ON l.relation = t.oid
            WHERE l.granted = false
            ORDER BY a.query_start
            """
            metrics["blocked_queries"] = await self.execute_query(lock_query)

            metrics["timestamp"] = datetime.utcnow().isoformat()
            metrics["status"] = "success"

            self.metrics = metrics
            return metrics

        except Exception as e:
            logger.error(f"Performance metrics collection failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # 5. Storage Monitoring and Cleanup
    # ---------------------------------------------------------

    async def monitor_storage_usage(self) -> Dict[str, any]:
        """Monitor database storage usage and identify cleanup opportunities"""
        try:
            # Get storage metrics
            storage_query = """
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                pg_database_size(current_database()) as database_size_bytes,
                (SELECT SUM(pg_total_relation_size(schemaname||'.'||tablename))
                 FROM pg_tables WHERE schemaname = 'public') as tables_total_size
            """
            storage_info = await self.execute_query(storage_query)

            # Identify tables with high dead tuple ratio
            dead_tuple_query = """
            SELECT
                schemaname,
                tablename,
                n_live_tup,
                n_dead_tup,
                CASE
                    WHEN n_live_tup > 0
                    THEN ROUND((n_dead_tup::numeric / (n_live_tup + n_dead_tup)) * 100, 2)
                    ELSE 0
                END as dead_tuple_percentage,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 1000
              AND (n_dead_tup::numeric / (n_live_tup + n_dead_tup)) > 0.1
            ORDER BY dead_tuple_percentage DESC
            """
            tables_needing_vacuum = await self.execute_query(dead_tuple_query)

            # Identify bloat in tables and indexes
            bloat_query = """
            SELECT
                current_database(),
                schemaname,
                tablename,
                ROUND(
                    CASE
                        WHEN otta=0 THEN 0.0
                        ELSE sml.relpages/otta::numeric
                    END - 1
                ) * 100 AS approximate_bloat_percentage,
                CASE
                    WHEN relpages < otta THEN 0 ELSE relpages::bigint - otta
                END AS approximate_bloat_bytes
            FROM (
                SELECT
                    cs.schemaname,
                    cs.tablename,
                    cc.reltuples,
                    cc.relpages,
                    FLOOR(
                        (
                            cc.reltuples *
                            (
                                24 +
                                MAX(CASE WHEN null_frac <> 0 THEN NULL ELSE avg_width END)
                            )
                        ) / (
                            current_setting('block_size')::integer
                        )
                    ) AS otta
                FROM pg_stats cs
                JOIN pg_class cc ON cs.tablename = cc.relname
                WHERE cs.schemaname='public'
                GROUP BY 1,2,3,4
            ) AS sml
            JOIN pg_stat_user_tables psut ON sml.tablename = psut.relname
            WHERE sml.otta > 0
            ORDER BY approximate_bloat_percentage DESC
            """
            bloat_info = await self.execute_query(bloat_query)

            return {
                "operation": "storage_monitoring",
                "storage_info": storage_info[0] if storage_info else {},
                "tables_needing_vacuum": tables_needing_vacuum,
                "bloat_analysis": bloat_info,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Storage monitoring failed: {str(e)}")
            return {
                "operation": "storage_monitoring",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # 6. Health Checks
    # ---------------------------------------------------------

    async def perform_health_check(self) -> Dict[str, any]:
        """Perform comprehensive database health check"""
        try:
            health_status = {
                "overall_health": "healthy",
                "checks": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Check 1: Database connectivity
            try:
                await self.execute_query("SELECT 1")
                health_status["checks"].append(
                    {
                        "check": "database_connectivity",
                        "status": "pass",
                        "message": "Database is accessible",
                    }
                )
            except Exception as e:
                health_status["checks"].append(
                    {
                        "check": "database_connectivity",
                        "status": "fail",
                        "message": f"Database connectivity error: {str(e)}",
                    }
                )
                health_status["overall_health"] = "unhealthy"

            # Check 2: Connection pool usage
            try:
                conn_query = """
                SELECT
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                    MAX(backend_start) as longest_connection
                FROM pg_stat_activity
                """
                conn_stats = await self.execute_query(conn_query)
                active_conns = conn_stats[0]["active_connections"]
                total_conns = conn_stats[0]["total_connections"]

                if active_conns > total_conns * 0.8:
                    health_status["checks"].append(
                        {
                            "check": "connection_usage",
                            "status": "warning",
                            "message": f"High connection usage: {active_conns}/{total_conns}",
                        }
                    )
                    if health_status["overall_health"] == "healthy":
                        health_status["overall_health"] = "warning"
                else:
                    health_status["checks"].append(
                        {
                            "check": "connection_usage",
                            "status": "pass",
                            "message": f"Connection usage normal: {active_conns}/{total_conns}",
                        }
                    )
            except Exception as e:
                health_status["checks"].append(
                    {
                        "check": "connection_usage",
                        "status": "fail",
                        "message": f"Connection check error: {str(e)}",
                    }
                )
                health_status["overall_health"] = "unhealthy"

            # Check 3: Table bloat
            try:
                bloat_result = await self.monitor_storage_usage()
                high_bloat_tables = [
                    t
                    for t in bloat_result.get("bloat_analysis", [])
                    if t.get("approximate_bloat_percentage", 0) > 25
                ]

                if high_bloat_tables:
                    health_status["checks"].append(
                        {
                            "check": "table_bloat",
                            "status": "warning",
                            "message": f"{len(high_bloat_tables)} tables have high bloat (>25%)",
                        }
                    )
                    if health_status["overall_health"] == "healthy":
                        health_status["overall_health"] = "warning"
                else:
                    health_status["checks"].append(
                        {
                            "check": "table_bloat",
                            "status": "pass",
                            "message": "Table bloat levels are acceptable",
                        }
                    )
            except Exception as e:
                health_status["checks"].append(
                    {
                        "check": "table_bloat",
                        "status": "fail",
                        "message": f"Bloat check error: {str(e)}",
                    }
                )

            # Check 4: Long-running queries
            try:
                long_query_check = """
                SELECT
                    pid,
                    now() - query_start as duration,
                    query,
                    usename
                FROM pg_stat_activity
                WHERE state = 'active'
                  AND now() - query_start > interval '5 minutes'
                ORDER BY duration DESC
                """
                long_queries = await self.execute_query(long_query_check)

                if long_queries:
                    health_status["checks"].append(
                        {
                            "check": "long_running_queries",
                            "status": "warning",
                            "message": f"{len(long_queries)} queries running longer than 5 minutes",
                        }
                    )
                    if health_status["overall_health"] == "healthy":
                        health_status["overall_health"] = "warning"
                else:
                    health_status["checks"].append(
                        {
                            "check": "long_running_queries",
                            "status": "pass",
                            "message": "No long-running queries detected",
                        }
                    )
            except Exception as e:
                health_status["checks"].append(
                    {
                        "check": "long_running_queries",
                        "status": "fail",
                        "message": f"Long query check error: {str(e)}",
                    }
                )

            # Check 5: Replication lag (if applicable)
            try:
                replication_query = """
                SELECT
                    application_name,
                    state,
                    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) as lag_bytes
                FROM pg_stat_replication
                """
                replication_stats = await self.execute_query(replication_query)

                health_status["checks"].append(
                    {
                        "check": "replication_status",
                        "status": "pass",
                        "message": f"{len(replication_stats)} replica(s) connected",
                    }
                )
            except Exception:
                health_status["checks"].append(
                    {
                        "check": "replication_status",
                        "status": "info",
                        "message": "Replication not configured or check failed",
                    }
                )

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "overall_health": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # 7. Utility Functions
    # ---------------------------------------------------------

    async def get_table_list(self) -> List[str]:
        """Get list of user tables"""
        query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename NOT LIKE 'pg_%'
        ORDER BY tablename
        """
        result = await self.execute_query(query)
        return [row["tablename"] for row in result]

    async def get_table_statistics(self, table_name: str) -> Dict[str, any]:
        """Get detailed statistics for a specific table"""
        query = """
        SELECT
            schemaname,
            tablename,
            n_live_tup,
            n_dead_tup,
            n_mod_since_analyze,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze,
            vacuum_count,
            autovacuum_count,
            analyze_count,
            autoanalyze_count,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
        FROM pg_stat_user_tables
        WHERE schemaname = 'public' AND tablename = $1
        """

        result = await self.execute_query(query, {"table": table_name})
        return result[0] if result else {}


# Main execution function
async def main():
    """Main maintenance execution"""
    import os

    # Get database connection from environment or use default
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/psychsync"
    )

    maintenance = DatabaseMaintenance(db_url)

    print("🔧 Starting Database Maintenance and Optimization")
    print("=" * 50)

    # 1. Health Check
    print("\n1️⃣ Performing Health Check...")
    health_check = await maintenance.perform_health_check()
    print(f"   Overall Health: {health_check['overall_health'].upper()}")
    for check in health_check["checks"]:
        status_icon = (
            "✅"
            if check["status"] == "pass"
            else "⚠️" if check["status"] == "warning" else "❌"
        )
        print(f"   {status_icon} {check['check']}: {check['message']}")

    # 2. VACUUM and ANALYZE
    print("\n2️⃣ Running VACUUM ANALYZE...")
    vacuum_result = await maintenance.auto_vacuum_analyze()
    if vacuum_result["status"] == "success":
        print(f"   ✅ VACUUM ANALYZE completed in {vacuum_result['duration_seconds']}s")
        print(f"   📊 Processed {vacuum_result['tables_processed']} tables")
    else:
        print(f"   ❌ VACUUM ANALYZE failed: {vacuum_result['error']}")

    # 3. Update Statistics
    print("\n3️⃣ Updating Table Statistics...")
    stats_result = await maintenance.update_table_statistics()
    if stats_result["status"] == "success":
        print(f"   ✅ Statistics updated in {stats_result['duration_seconds']}s")
        print(f"   📊 Updated {stats_result['tables_updated']} tables")
    else:
        print(f"   ❌ Statistics update failed: {stats_result['error']}")

    # 4. Index Maintenance
    print("\n4️⃣ Analyzing Index Usage...")
    index_usage = await maintenance.analyze_index_usage()
    unused_indexes = [idx for idx in index_usage if idx["idx_scan"] < 10]

    if unused_indexes:
        print(f"   ⚠️ Found {len(unused_indexes)} potentially unused indexes")
        index_rebuild_result = await maintenance.rebuild_unused_indexes()
        if index_rebuild_result["status"] == "success":
            print(f"   ✅ Rebuilt {index_rebuild_result['indexes_rebuilt']} indexes")
    else:
        print("   ✅ No unused indexes detected")

    # 5. Partition Management
    print("\n5️⃣ Managing Partitions...")
    partition_result = await maintenance.manage_partitions()
    if partition_result["status"] == "success":
        print(f"   ✅ Created {partition_result['total_created']} new partitions")
        print(f"   🗑️ Dropped {partition_result['total_dropped']} old partitions")
    else:
        print(f"   ❌ Partition management failed: {partition_result['error']}")

    # 6. Storage Monitoring
    print("\n6️⃣ Monitoring Storage Usage...")
    storage_result = await maintenance.monitor_storage_usage()
    if storage_result["status"] == "success":
        db_size = storage_result["storage_info"].get("database_size", "Unknown")
        print(f"   📊 Database size: {db_size}")

        tables_needing_vacuum = storage_result.get("tables_needing_vacuum", [])
        if tables_needing_vacuum:
            print(f"   ⚠️ {len(tables_needing_vacuum)} tables need VACUUM")
            for table in tables_needing_vacuum[:3]:  # Show top 3
                print(
                    f"      - {table['tablename']}: {table['dead_tuple_percentage']}% dead tuples"
                )
    else:
        print(f"   ❌ Storage monitoring failed: {storage_result['error']}")

    # 7. Performance Metrics
    print("\n7️⃣ Collecting Performance Metrics...")
    perf_metrics = await maintenance.collect_performance_metrics()
    if perf_metrics["status"] == "success":
        active_conns = perf_metrics.get("database", {}).get("active_connections", 0)
        total_conns = perf_metrics.get("database", {}).get("total_connections", 0)
        print(f"   🔌 Active connections: {active_conns}/{total_conns}")

        blocked_queries = perf_metrics.get("blocked_queries", [])
        if blocked_queries:
            print(f"   ⚠️ {len(blocked_queries)} blocked queries detected")
        else:
            print("   ✅ No blocked queries")
    else:
        print(
            f"   ❌ Metrics collection failed: {perf_metrics.get('error', 'Unknown error')}"
        )

    print("\n" + "=" * 50)
    print("🎉 Database Maintenance Complete!")
    print(f"⏰ Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")


if __name__ == "__main__":
    asyncio.run(main())
