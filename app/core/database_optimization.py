# app/core/database_optimization.py
"""
Database optimization utilities for PsychSync
Provides query optimization, indexing strategies, and performance monitoring
"""
from sqlalchemy import text, Index, DDL
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization utilities for PsychSync"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # =============================================================================
    # INDEX OPTIMIZATIONS
    # =============================================================================

    async def create_performance_indexes(self):
        """Create strategic indexes for optimal query performance"""

        indexes = [
            # User table indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_verified
            ON users(email, is_verified) WHERE is_active = true;
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_org_created
            ON users(organization_id, created_at DESC);
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login_active
            ON users(last_login DESC NULLS LAST) WHERE is_active = true;
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_reset_token
            ON users(password_reset_token) WHERE password_reset_expires > NOW();
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_verification_token
            ON users(email_verification_token) WHERE email_verification_expires > NOW();
            """,

            # Team table indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_org_created
            ON teams(organization_id, created_at DESC);
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_creator
            ON teams(created_by_id, created_at DESC);
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_name_search
            ON teams USING gin(to_tsvector('english', name));
            """,

            # Team member indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_team_role
            ON team_members(team_id, role);
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_user_active
            ON team_members(user_id)
            WHERE team_id IN (
                SELECT id FROM teams WHERE organization_id IS NOT NULL
            );
            """,
            """
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_unique
            ON team_members(team_id, user_id);
            """,

            # Organization indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_created
            ON organizations(created_at DESC);
            """,

            # Assessment and response indexes (if they exist)
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_org_created
            ON assessments(organization_id, created_at DESC);
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_user_assessment
            ON responses(user_id, assessment_id, created_at DESC);
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_team_score
            ON responses(team_id, score DESC);
            """,
        ]

        for index_sql in indexes:
            try:
                await self.db.execute(text(index_sql))
                await self.db.commit()
                logger.info(f"Created index: {index_sql.split('IF NOT EXISTS')[1].split('ON')[1].strip()}")
            except Exception as e:
                await self.db.rollback()
                logger.warning(f"Failed to create index: {e}")

    # =============================================================================
    # QUERY OPTIMIZATION
    # =============================================================================

    async def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance and provide optimization suggestions"""

        try:
            # Get query execution plan
            explain_result = await self.db.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"))
            plan_data = explain_result.scalar()

            # Extract performance metrics
            metrics = self._extract_query_metrics(plan_data[0] if plan_data else {})

            # Generate optimization suggestions
            suggestions = self._generate_optimization_suggestions(metrics, query)

            return {
                "query": query,
                "metrics": metrics,
                "suggestions": suggestions,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return {"error": str(e), "query": query}

    def _extract_query_metrics(self, plan_data: Dict) -> Dict[str, Any]:
        """Extract key metrics from execution plan"""
        metrics = {
            "execution_time": 0,
            "planning_time": 0,
            "total_cost": 0,
            "rows_returned": 0,
            "index_scans": 0,
            "seq_scans": 0,
            "buffer_hits": 0,
            "buffer_reads": 0
        }

        def traverse_plan(node):
            if isinstance(node, dict):
                # Extract metrics from this node
                if "Execution Time" in node:
                    metrics["execution_time"] += node["Execution Time"]
                if "Planning Time" in node:
                    metrics["planning_time"] = max(metrics["planning_time"], node["Planning Time"])
                if "Total Cost" in node:
                    metrics["total_cost"] += node["Total Cost"]
                if "Actual Rows" in node:
                    metrics["rows_returned"] += node["Actual Rows"]

                # Count scan types
                if "Node Type" in node:
                    if "Index Scan" in node["Node Type"]:
                        metrics["index_scans"] += 1
                    elif "Seq Scan" in node["Node Type"]:
                        metrics["seq_scans"] += 1

                # Buffer information
                if "Shared Hit Blocks" in node:
                    metrics["buffer_hits"] += node["Shared Hit Blocks"]
                if "Shared Read Blocks" in node:
                    metrics["buffer_reads"] += node["Shared Read Blocks"]

                # Recursively traverse child nodes
                if "Plans" in node:
                    for child in node["Plans"]:
                        traverse_plan(child)

        traverse_plan(plan_data)
        return metrics

    def _generate_optimization_suggestions(self, metrics: Dict, query: str) -> List[str]:
        """Generate optimization suggestions based on query metrics"""
        suggestions = []

        # Execution time suggestions
        if metrics["execution_time"] > 1000:  # > 1 second
            suggestions.append("Query execution time is high (>1s). Consider optimization.")

        # Sequential scan warnings
        if metrics["seq_scans"] > 0:
            suggestions.append("Sequential scans detected. Consider adding appropriate indexes.")

        # Buffer efficiency
        total_buffers = metrics["buffer_hits"] + metrics["buffer_reads"]
        if total_buffers > 0:
            hit_ratio = metrics["buffer_hits"] / total_buffers
            if hit_ratio < 0.9:
                suggestions.append(f"Low buffer hit ratio ({hit_ratio:.2%}). Consider query or index optimization.")

        # Cost warnings
        if metrics["total_cost"] > 10000:
            suggestions.append("High query cost detected. Review query structure and indexes.")

        # Query-specific suggestions
        query_lower = query.lower()
        if "select *" in query_lower:
            suggestions.append("Avoid SELECT *. Specify only needed columns.")

        if "order by" in query_lower and "limit" not in query_lower:
            suggestions.append("ORDER BY without LIMIT may return large result sets. Consider pagination.")

        return suggestions

    # =============================================================================
    # VACUUM AND MAINTENANCE
    # =============================================================================

    async def optimize_table_maintenance(self, table_name: str):
        """Perform maintenance operations on a specific table"""

        maintenance_tasks = [
            f"VACUUM ANALYZE {table_name};",
            f"REINDEX TABLE CONCURRENTLY {table_name};",
            f"ANALYZE {table_name};"
        ]

        for task in maintenance_tasks:
            try:
                start_time = time.time()
                await self.db.execute(text(task))
                await self.db.commit()
                duration = time.time() - start_time
                logger.info(f"Completed maintenance on {table_name}: {task} ({duration:.2f}s)")
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Maintenance failed on {table_name}: {task} - {e}")

    async def update_table_statistics(self):
        """Update statistics for all tables for better query planning"""

        tables = [
            "users", "organizations", "teams", "team_members",
            "assessments", "responses", "templates", "questions"
        ]

        for table in tables:
            try:
                await self.db.execute(text(f"ANALYZE {table};"))
                await self.db.commit()
                logger.info(f"Updated statistics for table: {table}")
            except Exception as e:
                logger.warning(f"Failed to update statistics for {table}: {e}")

    # =============================================================================
    # MONITORING AND HEALTH CHECKS
    # =============================================================================

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""

        stats_queries = {
            "database_size": """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size;
            """,
            "table_sizes": """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                                  pg_relation_size(schemaname||'.'||tablename)) as index_size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """,
            "index_usage": """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC;
            """,
            "slow_queries": """
                SELECT
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_time > 100  -- queries taking more than 100ms on average
                ORDER BY mean_time DESC
                LIMIT 10;
            """,
            "connection_stats": """
                SELECT
                    state,
                    COUNT(*) as connection_count
                FROM pg_stat_activity
                GROUP BY state;
            """
        }

        results = {}
        for name, query in stats_queries.items():
            try:
                result = await self.db.execute(text(query))
                results[name] = [dict(row._mapping) for row in result]
            except Exception as e:
                results[name] = {"error": str(e)}
                logger.warning(f"Failed to get {name}: {e}")

        return results

    async def check_table_bloat(self) -> List[Dict[str, Any]]:
        """Check for table bloat that could affect performance"""

        bloat_query = """
        SELECT
            schemaname,
            tablename,
            ROUND(CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages/otta::numeric END,1) AS tbloat,
            CASE WHEN relpages < otta THEN 0 ELSE relpages::bigint - otta END AS wastedpages,
            CASE WHEN relpages < otta THEN 0 ELSE bs*(sml.relpages-otta)::bigint END AS wastedbytes,
            CASE WHEN relpages < otta THEN 0 ELSE (bs*(relpages-otta))::bigint END AS wastedsize,
            iname,
            ROUND(CASE WHEN iotta=0 OR ipages=0 THEN 0.0 ELSE ipages/iotta::numeric END,1) AS ibloat,
            CASE WHEN ipages < iotta THEN 0 ELSE ipages::bigint - iotta END AS wastedipages,
            CASE WHEN ipages < iotta THEN 0 ELSE bs*(ipages-iotta) END AS wastedibytes,
            CASE WHEN ipages < iotta THEN 0 ELSE bs*(ipages-iotta) END AS wastedisize
        FROM (
            SELECT
                i.schemaname,
                i.tablename,
                sml.relpages AS ipages,
                COALESCE(sml.reltuples,0) AS ituples,
                i.reltuples AS ituples,
                COALESCE(CASE WHEN i.reltuples=0 THEN 0 ELSE bs*(sml.relpages::float/i.reltuples::float) END,0) AS iotta,
                i.relname AS iname,
                sml.relpages,
                sml.reltuples,
                COALESCE(CASE WHEN sml.reltuples=0 THEN 0 ELSE bs*(sml.relpages::float/sml.reltuples::float) END,0) AS otta,
                sml.relname,
                bs
            FROM (
                SELECT
                    schemaname, tablename, cc.reltuples, cc.relpages, bs,
                    CEIL((cc.reltuples*((datahdr+ma-
                        (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END)+nullhdr2+4))/(bs-20)))::integer AS otta
                FROM (
                    SELECT
                        ma,bs,schemaname,tablename,
                        ((datawidth+(hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric+8)/(bs-20)::numeric AS reltuples,
                        ((hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END))::numeric+8)/(bs-20)::numeric AS datahdr,
                        (maxfracsum*(nullhdr+ma-(CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))::numeric+8)/(bs-20)::numeric AS nullhdr2,
                        ((hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END))::numeric+8)/(bs-20)::numeric AS datahdr
                    FROM (
                        SELECT
                            (23 + max(COALESCE(null_frac,0))) AS hdr,
                            (max(COALESCE(avg_width, 32))) AS ma,
                            (CASE WHEN substring(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 24 END) AS nullhdr,
                            8192 AS bs,
                            1 AS maxfracsum
                        FROM (
                            SELECT
                                table_schema,
                                table_name,
                                version() as v
                            FROM information_schema.tables
                            WHERE table_schema='public'
                        ) AS foo
                        CROSS JOIN (
                            SELECT
                                null_frac, avg_width,
                                SUM(1) * COALESCE(null_frac, 0) AS maxfracsum
                            FROM pg_stats
                            WHERE schemaname='public'
                        ) AS bar
                        WHERE table_schema='public'
                    ) AS rs
                ) AS foo
                CROSS JOIN (
                    SELECT
                        schemaname, tablename, cc.reltuples, cc.relpages, bs
                    FROM (
                        SELECT
                            schemaname, tablename, cc.reltuples, cc.relpages,
                            ((bs-20)*8192::float)/bs AS bs
                        FROM (
                            SELECT
                                schemaname, tablename, reltuples, relpages
                            FROM pg_class c
                            JOIN pg_namespace n ON (n.oid = c.relnamespace)
                            JOIN pg_stat_all_tables a ON (a.relname = c.relname)
                            WHERE c.relkind = 'r' AND n.nspname = 'public'
                        ) AS cc
                        CROSS JOIN (
                            SELECT current_setting('block_size')::integer AS bs
                        ) AS bs
                    ) AS cc
                ) AS sml
            ) AS sml
            JOIN pg_class i ON (i.relname = sml.iname)
            JOIN pg_namespace n ON (n.oid = i.relnamespace)
            WHERE i.relkind = 'i' AND n.nspname = 'public'
        ) AS sub
        WHERE tbloat > 1.5 OR ibloat > 1.5
        ORDER BY wastedibytes DESC, wastedsize DESC;
        """

        try:
            result = await self.db.execute(text(bloat_query))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Failed to check table bloat: {e}")
            return []

    # =============================================================================
    # AUTOMATED OPTIMIZATION
    # =============================================================================

    async def auto_optimize_database(self):
        """Run automated database optimization tasks"""

        logger.info("Starting automated database optimization...")

        # 1. Update statistics
        await self.update_table_statistics()

        # 2. Check for high bloat tables and optimize if needed
        bloat_tables = await self.check_table_bloat()
        for table_info in bloat_tables:
            if float(table_info.get('tbloat', 0)) > 2.0:  # > 200% expected size
                await self.optimize_table_maintenance(table_info['tablename'])

        # 3. Get performance stats
        stats = await self.get_database_stats()

        # 4. Identify slow queries needing optimization
        if 'slow_queries' in stats and stats['slow_queries']:
            logger.warning(f"Found {len(stats['slow_queries'])} slow queries that need optimization")

        logger.info("Automated database optimization completed")
        return stats


# =============================================================================
    # UTILITY FUNCTIONS
# =============================================================================

async def create_database_view_optimizer(db: AsyncSession):
    """Create optimized views for common queries"""

    views = [
        # Active users with organizations
        """
        CREATE OR REPLACE VIEW active_users_org AS
        SELECT
            u.id, u.email, u.full_name, u.is_active, u.is_verified, u.last_login,
            u.created_at, u.organization_id, o.name as organization_name
        FROM users u
        LEFT JOIN organizations o ON u.organization_id = o.id
        WHERE u.is_active = true AND u.deleted_at IS NULL;
        """,

        # Team member counts
        """
        CREATE OR REPLACE VIEW team_member_counts AS
        SELECT
            t.id as team_id, t.name as team_name,
            COUNT(tm.id) as total_members,
            COUNT(CASE WHEN tm.role = 'owner' THEN 1 END) as owners,
            COUNT(CASE WHEN tm.role = 'admin' THEN 1 END) as admins,
            COUNT(CASE WHEN tm.role = 'member' THEN 1 END) as members
        FROM teams t
        LEFT JOIN team_members tm ON t.id = tm.team_id
        GROUP BY t.id, t.name;
        """,

        # User activity summary
        """
        CREATE OR REPLACE VIEW user_activity_summary AS
        SELECT
            u.id, u.email, u.full_name,
            COUNT(DISTINCT t.id) as teams_count,
            COUNT(DISTINCT a.id) as assessments_count,
            COUNT(DISTINCT r.id) as responses_count,
            MAX(u.last_login) as last_activity
        FROM users u
        LEFT JOIN team_members tm ON u.id = tm.user_id
        LEFT JOIN teams t ON tm.team_id = t.id
        LEFT JOIN assessments a ON (a.created_by_id = u.id OR t.id = a.team_id)
        LEFT JOIN responses r ON r.user_id = u.id
        WHERE u.is_active = true
        GROUP BY u.id, u.email, u.full_name;
        """
    ]

    for view_sql in views:
        try:
            await db.execute(text(view_sql))
            await db.commit()
            logger.info("Created optimized database view")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create view: {e}")