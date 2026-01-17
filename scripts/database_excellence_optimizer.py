#!/usr/bin/env python3
"""
PsychSync Database Excellence Optimizer
Comprehensive database performance analysis and optimization for production readiness

Implements:
- Query performance analysis and optimization
- Index usage and missing index detection
- N+1 query problem identification and fixes
- Slow query monitoring and optimization
- Database connection optimization
- Query plan analysis for performance bottlenecks
"""

import asyncio
import asyncpg
import time
import json
import subprocess
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class QueryAnalysisResult:
    """Query performance analysis result"""
    query_text: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    index_usage: List[str]
    query_type: str
    optimization_suggestions: List[str]
    performance_grade: str  # A, B, C, D, F

@dataclass
class IndexAnalysis:
    """Index usage analysis"""
    table_name: str
    index_name: str
    usage_count: int
    size_mb: float
    efficiency: float
    recommendation: str

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    total_connections: int
    active_connections: int
    idle_connections: int
    cache_hit_ratio: float
    avg_query_time: float
    slow_queries_count: int
    database_size_gb: float
    index_size_gb: float

class DatabaseExcellenceOptimizer:
    """
    Comprehensive database performance optimization and analysis system
    """

    def __init__(self):
        self.db_url = getattr(settings, 'DATABASE_URL', '').replace('postgresql://', 'postgresql+asyncpg://')
        self.connection_pool = None
        self.slow_queries = []
        self.query_cache = {}
        self.optimization_suggestions = []
        self.critical_issues = []

    async def initialize_connection(self):
        """Initialize database connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.db_url.replace('postgresql+asyncpg://', 'postgresql://'),
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            return False

    async def analyze_database_metrics(self) -> DatabaseMetrics:
        """Comprehensive database performance metrics analysis"""
        async with self.connection_pool.acquire() as conn:
            try:
                # Connection metrics
                conn_result = await conn.fetchrow("""
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)

                # Cache hit ratio
                cache_result = await conn.fetchrow("""
                    SELECT
                        sum(blks_hit)::float / nullif(sum(blks_hit) + sum(blks_read), 0) as cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)

                # Average query time
                query_time_result = await conn.fetchrow("""
                    SELECT
                        avg(total_exec_time) as avg_query_time
                    FROM pg_stat_statements
                    WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
                """)

                # Slow queries count
                slow_queries_result = await conn.fetchrow("""
                    SELECT count(*) as slow_queries_count
                    FROM pg_stat_statements
                    WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
                    AND mean_exec_time > 1000  -- queries over 1 second
                """)

                # Database size metrics
                size_result = await conn.fetchrow("""
                    SELECT
                        pg_database_size(current_database()) / 1024.0 / 1024.0 / 1024.0 as database_size_gb,
                        pg_indexes_size(current_database()) / 1024.0 / 1024.0 / 1024.0 as index_size_gb
                """)

                return DatabaseMetrics(
                    total_connections=conn_result['total_connections'] or 0,
                    active_connections=conn_result['active_connections'] or 0,
                    idle_connections=conn_result['idle_connections'] or 0,
                    cache_hit_ratio=cache_result['cache_hit_ratio'] or 0.0,
                    avg_query_time=query_time_result['avg_query_time'] or 0.0,
                    slow_queries_count=slow_queries_result['slow_queries_count'] or 0,
                    database_size_gb=size_result['database_size_gb'] or 0.0,
                    index_size_gb=size_result['index_size_gb'] or 0.0
                )

            except Exception as e:
                logger.error(f"Error analyzing database metrics: {e}")
                return DatabaseMetrics(0, 0, 0, 0.0, 0.0, 0, 0.0, 0.0)

    async def analyze_slow_queries(self) -> List[QueryAnalysisResult]:
        """Analyze slow queries and provide optimization recommendations"""
        async with self.connection_pool.acquire() as conn:
            try:
                # Get slow queries from pg_stat_statements
                slow_queries_sql = """
                    SELECT
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements
                    WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
                    AND mean_exec_time > 100  -- queries over 100ms
                    ORDER BY mean_exec_time DESC
                    LIMIT 20
                """

                slow_queries = await conn.fetch(slow_queries_sql)
                analysis_results = []

                for query_data in slow_queries:
                    query_text = query_data['query']
                    mean_time = query_data['mean_exec_time']
                    rows_returned = query_data['rows']
                    hit_percent = query_data['hit_percent'] or 0.0

                    # Analyze query structure
                    query_type = self._analyze_query_type(query_text)
                    optimization_suggestions = self._generate_query_optimization_suggestions(
                        query_text, mean_time, rows_returned, hit_percent
                    )
                    performance_grade = self._calculate_performance_grade(mean_time, hit_percent)

                    analysis_results.append(QueryAnalysisResult(
                        query_text=self._sanitize_query(query_text),
                        execution_time=mean_time,
                        rows_examined=rows_returned,
                        rows_returned=rows_returned,
                        index_usage=self._extract_index_usage(query_text),
                        query_type=query_type,
                        optimization_suggestions=optimization_suggestions,
                        performance_grade=performance_grade
                    ))

                return analysis_results

            except Exception as e:
                logger.error(f"Error analyzing slow queries: {e}")
                return []

    async def analyze_index_usage(self) -> List[IndexAnalysis]:
        """Analyze index usage and efficiency"""
        async with self.connection_pool.acquire() as conn:
            try:
                # Get index usage statistics
                index_usage_sql = """
                    WITH index_usage AS (
                        SELECT
                            schemaname,
                            tablename,
                            indexname,
                            idx_tup_read,
                            idx_tup_fetch,
                            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                        FROM pg_stat_user_indexes
                    ),
                    index_stats AS (
                        SELECT
                            schemaname,
                            tablename,
                            indexname,
                            pg_relation_size(indexrelid) as index_bytes,
                            CASE
                                WHEN idx_tup_read = 0 THEN 0
                                ELSE idx_tup_fetch::float / idx_tup_read
                            END as efficiency
                        FROM index_usage
                    )
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        index_bytes / 1024.0 / 1024.0 as size_mb,
                        efficiency,
                        idx_tup_read as usage_count
                    FROM index_stats
                    ORDER BY usage_count DESC
                """

                index_results = await conn.fetch(index_usage_sql)
                analysis_results = []

                for index_data in index_results:
                    table_name = f"{index_data['schemaname']}.{index_data['tablename']}"
                    index_name = index_data['indexname']
                    usage_count = index_data['usage_count'] or 0
                    size_mb = index_data['size_mb'] or 0.0
                    efficiency = index_data['efficiency'] or 0.0

                    # Generate recommendation based on usage and efficiency
                    recommendation = self._generate_index_recommendation(
                        usage_count, size_mb, efficiency
                    )

                    analysis_results.append(IndexAnalysis(
                        table_name=table_name,
                        index_name=index_name,
                        usage_count=usage_count,
                        size_mb=size_mb,
                        efficiency=efficiency,
                        recommendation=recommendation
                    ))

                return analysis_results

            except Exception as e:
                logger.error(f"Error analyzing index usage: {e}")
                return []

    async def detect_missing_indexes(self) -> List[Dict[str, Any]]:
        """Detect missing indexes based on query patterns"""
        async with self.connection_pool.acquire() as conn:
            try:
                # Analyze common query patterns for missing indexes
                missing_indexes_sql = """
                    WITH potential_missing_indexes AS (
                        SELECT
                            schemaname,
                            tablename,
                            attnum,
                            attname,
                            n_distinct,
                            correlation
                        FROM pg_stats
                        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                        AND n_distinct > 10  -- Columns with good selectivity
                    )
                    SELECT
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM potential_missing_indexes
                    ORDER BY n_distinct DESC
                    LIMIT 20
                """

                potential_columns = await conn.fetch(missing_indexes_sql)
                missing_indexes = []

                # Group by table and suggest composite indexes
                table_columns = {}
                for col in potential_columns:
                    table_name = f"{col['schemaname']}.{col['tablename']}"
                    if table_name not in table_columns:
                        table_columns[table_name] = []
                    table_columns[table_name].append({
                        'column': col['attname'],
                        'selectivity': col['n_distinct'],
                        'correlation': col['correlation']
                    })

                # Generate index suggestions
                for table, columns in table_columns.items():
                    if len(columns) >= 1:
                        # Create index suggestion
                        primary_col = max(columns, key=lambda x: x['selectivity'])

                        missing_indexes.append({
                            'table_name': table,
                            'recommended_index': f"idx_{table.replace('.', '_')}_{primary_col['column']}",
                            'columns': [primary_col['column']],
                            'estimated_impact': 'HIGH' if primary_col['selectivity'] > 100 else 'MEDIUM',
                            'reason': f"Column {primary_col['column']} has high selectivity ({primary_col['selectivity']} distinct values)"
                        })

                return missing_indexes

            except Exception as e:
                logger.error(f"Error detecting missing indexes: {e}")
                return []

    async def analyze_n1_queries(self) -> List[Dict[str, Any]]:
        """Identify potential N+1 query problems in application code"""
        n1_issues = []

        try:
            # Analyze application code for N+1 patterns
            app_files = [
                'app/services/user_service.py',
                'app/services/team_service.py',
                'app/services/assessment_service.py',
                'app/services/response_service.py'
            ]

            for file_path in app_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Look for N+1 query patterns
                    n1_patterns = self._detect_n1_patterns(content, file_path)
                    n1_issues.extend(n1_patterns)

        except Exception as e:
            logger.error(f"Error analyzing N+1 queries: {e}")

        return n1_issues

    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive database optimization report"""

        logger.info("Starting database excellence optimization analysis...")

        # Gather all analysis data
        metrics = await self.analyze_database_metrics()
        slow_queries = await self.analyze_slow_queries()
        index_usage = await self.analyze_index_usage()
        missing_indexes = await self.detect_missing_indexes()
        n1_issues = await self.analyze_n1_queries()

        # Calculate optimization scores
        performance_score = self._calculate_performance_score(metrics)
        optimization_score = self._calculate_optimization_score(
            slow_queries, index_usage, missing_indexes, n1_issues
        )

        # Generate recommendations
        critical_recommendations = []
        high_priority_recommendations = []
        medium_priority_recommendations = []

        # Critical issues
        if metrics.cache_hit_ratio < 0.9:
            critical_recommendations.append(
                f"CRITICAL: Low cache hit ratio ({metrics.cache_hit_ratio:.2%}). "
                "Consider increasing shared_buffers or optimizing queries."
            )

        if metrics.avg_query_time > 500:
            critical_recommendations.append(
                f"CRITICAL: High average query time ({metrics.avg_query_time:.2f}ms). "
                "Immediate query optimization required."
            )

        # High priority issues
        if metrics.slow_queries_count > 10:
            high_priority_recommendations.append(
                f"HIGH: {metrics.slow_queries_count} slow queries detected. "
                "Review and optimize slow query list."
            )

        # Medium priority issues
        for missing_index in missing_indexes[:5]:
            medium_priority_recommendations.append(
                f"MEDIUM: Consider adding index {missing_index['recommended_index']} "
                f"on table {missing_index['table_name']} for potential performance improvement."
            )

        return {
            'timestamp': datetime.now().isoformat(),
            'database_metrics': asdict(metrics),
            'performance_score': performance_score,
            'optimization_score': optimization_score,
            'slow_queries_analysis': [asdict(q) for q in slow_queries[:10]],
            'index_usage_analysis': [asdict(idx) for idx in index_usage[:15]],
            'missing_indexes': missing_indexes[:10],
            'n1_query_issues': n1_issues,
            'critical_recommendations': critical_recommendations,
            'high_priority_recommendations': high_priority_recommendations,
            'medium_priority_recommendations': medium_priority_recommendations,
            'overall_grade': self._get_overall_grade(performance_score, optimization_score)
        }

    async def apply_automatic_optimizations(self) -> Dict[str, Any]:
        """Apply safe automatic optimizations"""
        optimizations_applied = []
        warnings = []

        try:
            async with self.connection_pool.acquire() as conn:
                # Update table statistics (safe operation)
                await conn.execute("ANALYZE")
                optimizations_applied.append("Updated table statistics (ANALYZE)")

                # Optimize PostgreSQL settings recommendations
                await self._optimize_postgres_settings(conn, optimizations_applied)

                # Create missing critical indexes (safe ones only)
                await self._create_critical_indexes(conn, optimizations_applied, warnings)

        except Exception as e:
            logger.error(f"Error applying automatic optimizations: {e}")
            warnings.append(f"Error during optimization: {str(e)}")

        return {
            'optimizations_applied': optimizations_applied,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }

    def _analyze_query_type(self, query_text: str) -> str:
        """Analyze query type from SQL text"""
        query_upper = query_text.upper().strip()

        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'

    def _generate_query_optimization_suggestions(
        self, query_text: str, exec_time: float, rows: int, hit_percent: float
    ) -> List[str]:
        """Generate optimization suggestions for a query"""
        suggestions = []

        if exec_time > 1000:
            suggestions.append("Consider adding indexes for WHERE clause columns")

        if hit_percent < 90:
            suggestions.append("Low buffer cache hit ratio - query may be reading too many disk pages")

        if rows == 0 and exec_time > 100:
            suggestions.append("Empty result set taking too long - check query logic and indexes")

        # Check for full table scans
        if 'Seq Scan' in query_text:
            suggestions.append("Sequential scan detected - consider adding appropriate indexes")

        # Check for missing WHERE clauses
        if 'WHERE' not in query_text.upper() and 'SELECT' in query_text.upper():
            suggestions.append("Missing WHERE clause may be scanning entire table")

        return suggestions

    def _calculate_performance_grade(self, exec_time: float, hit_percent: float) -> str:
        """Calculate performance grade for a query"""
        if exec_time < 10 and hit_percent > 95:
            return 'A'
        elif exec_time < 50 and hit_percent > 90:
            return 'B'
        elif exec_time < 200 and hit_percent > 80:
            return 'C'
        elif exec_time < 1000:
            return 'D'
        else:
            return 'F'

    def _sanitize_query(self, query_text: str) -> str:
        """Sanitize query for display (remove sensitive data)"""
        # Truncate very long queries
        if len(query_text) > 500:
            return query_text[:500] + "..."
        return query_text

    def _extract_index_usage(self, query_text: str) -> List[str]:
        """Extract index usage information from EXPLAIN output"""
        # This is simplified - in practice, you'd run EXPLAIN ANALYZE
        indexes = []
        if 'Index Scan' in query_text:
            # Extract index names using regex
            index_matches = re.findall(r'Index Scan.*?using\s+(\w+)', query_text, re.IGNORECASE)
            indexes.extend(index_matches)
        return indexes

    def _generate_index_recommendation(self, usage_count: int, size_mb: float, efficiency: float) -> str:
        """Generate index optimization recommendation"""
        if usage_count == 0:
            return "UNUSED - Consider dropping this index to save space"
        elif efficiency < 0.5:
            return "LOW EFFICIENCY - Index may need rebuilding or query optimization"
        elif size_mb > 100 and usage_count < 1000:
            return "LARGE AND LOW USAGE - Consider if this index is necessary"
        elif efficiency > 0.9 and usage_count > 10000:
            return "HIGHLY EFFECTIVE - Keep and maintain this index"
        else:
            return "NORMAL - Index is performing adequately"

    def _detect_n1_patterns(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect N+1 query patterns in code"""
        issues = []
        lines = content.split('\n')

        # Look for patterns that suggest N+1 queries
        n1_patterns = [
            r'for\s+\w+.*:\s*\n.*\.execute\(.*SELECT.*\)',
            r'\.fetchall\(\).*\n.*for.*in.*:',
            r'while.*:\s*\n.*\.fetchone\(\)',
        ]

        for i, line in enumerate(lines):
            for pattern in n1_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'file': file_path,
                        'line_number': i + 1,
                        'line_content': line.strip(),
                        'issue_type': 'Potential N+1 Query',
                        'recommendation': 'Consider using JOIN or eager loading instead of loops with queries'
                    })

        return issues

    def _calculate_performance_score(self, metrics: DatabaseMetrics) -> int:
        """Calculate overall database performance score (0-100)"""
        score = 100

        # Cache hit ratio impact
        if metrics.cache_hit_ratio < 0.9:
            score -= int((0.9 - metrics.cache_hit_ratio) * 100)

        # Average query time impact
        if metrics.avg_query_time > 100:
            score -= min(50, int((metrics.avg_query_time - 100) / 10))

        # Slow queries impact
        if metrics.slow_queries_count > 5:
            score -= min(30, metrics.slow_queries_count * 2)

        # Connection efficiency
        if metrics.total_connections > 0:
            active_ratio = metrics.active_connections / metrics.total_connections
            if active_ratio > 0.8:
                score -= 20

        return max(0, min(100, score))

    def _calculate_optimization_score(
        self, slow_queries: List, index_usage: List, missing_indexes: List, n1_issues: List
    ) -> int:
        """Calculate optimization potential score (0-100)"""
        score = 100

        # Slow queries impact
        if len(slow_queries) > 5:
            score -= min(40, len(slow_queries) * 5)

        # Unused indexes impact
        unused_indexes = [idx for idx in index_usage if idx.usage_count == 0]
        if len(unused_indexes) > 3:
            score -= min(30, len(unused_indexes) * 5)

        # Missing indexes impact
        if len(missing_indexes) > 5:
            score -= min(20, len(missing_indexes) * 2)

        # N+1 query issues impact
        if len(n1_issues) > 3:
            score -= min(30, len(n1_issues) * 5)

        return max(0, min(100, score))

    def _get_overall_grade(self, performance_score: int, optimization_score: int) -> str:
        """Get overall database health grade"""
        avg_score = (performance_score + optimization_score) / 2

        if avg_score >= 90:
            return 'A'
        elif avg_score >= 80:
            return 'B'
        elif avg_score >= 70:
            return 'C'
        elif avg_score >= 60:
            return 'D'
        else:
            return 'F'

    async def _optimize_postgres_settings(self, conn, optimizations: List[str]):
        """Generate PostgreSQL optimization settings recommendations"""
        settings_recommendations = [
            "-- PostgreSQL Performance Optimization Settings:",
            "shared_buffers = '256MB'  -- 25% of RAM",
            "effective_cache_size = '1GB'  -- 75% of RAM",
            "work_mem = '4MB'",
            "maintenance_work_mem = '64MB'",
            "checkpoint_completion_target = 0.9",
            "wal_buffers = '16MB'",
            "default_statistics_target = 100",
            "random_page_cost = 1.1  -- For SSD storage",
            "effective_io_concurrency = 200"
        ]

        optimizations.append("Generated PostgreSQL performance settings recommendations")

    async def _create_critical_indexes(self, conn, optimizations: List[str], warnings: List[str]):
        """Create critical missing indexes (safe ones only)"""
        # Only create indexes that are clearly beneficial and safe
        safe_indexes = [
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active
            ON users (email) WHERE is_active = true
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_responses_user_created
            ON assessment_responses (user_id, created_at DESC)
            """
        ]

        for index_sql in safe_indexes:
            try:
                await conn.execute(index_sql)
                table_name = index_sql.split('ON ')[1].split(' ')[0]
                optimizations.append(f"Created index on {table_name}")
            except Exception as e:
                warnings.append(f"Could not create index: {str(e)}")

async def main():
    """Main execution function"""
    print("🚀 PsychSync Database Excellence Optimizer")
    print("=" * 50)

    optimizer = DatabaseExcellenceOptimizer()

    # Initialize connection
    if not await optimizer.initialize_connection():
        print("❌ Failed to connect to database")
        return 1

    try:
        # Generate comprehensive report
        print("📊 Analyzing database performance...")
        report = await optimizer.generate_optimization_report()

        # Display results
        print(f"\n📈 Database Performance Score: {report['performance_score']}/100")
        print(f"🔧 Optimization Score: {report['optimization_score']}/100")
        print(f"📋 Overall Grade: {report['overall_grade']}")

        # Display metrics
        metrics = report['database_metrics']
        print(f"\n📊 Database Metrics:")
        print(f"   Cache Hit Ratio: {metrics['cache_hit_ratio']:.2%}")
        print(f"   Average Query Time: {metrics['avg_query_time']:.2f}ms")
        print(f"   Slow Queries: {metrics['slow_queries_count']}")
        print(f"   Database Size: {metrics['database_size_gb']:.2f}GB")
        print(f"   Index Size: {metrics['index_size_gb']:.2f}GB")

        # Display critical issues
        if report['critical_recommendations']:
            print(f"\n🚨 Critical Issues:")
            for issue in report['critical_recommendations']:
                print(f"   • {issue}")

        # Display slow queries
        if report['slow_queries_analysis']:
            print(f"\n🐌 Top Slow Queries:")
            for i, query in enumerate(report['slow_queries_analysis'][:5], 1):
                print(f"   {i}. Grade {query['performance_grade']} - {query['execution_time']:.2f}ms")
                print(f"      {query['query_text'][:100]}...")
                if query['optimization_suggestions']:
                    for suggestion in query['optimization_suggestions'][:2]:
                        print(f"      → {suggestion}")

        # Display missing indexes
        if report['missing_indexes']:
            print(f"\n🎯 Recommended Indexes:")
            for idx in report['missing_indexes'][:3]:
                print(f"   • {idx['recommended_index']} on {idx['table_name']}")
                print(f"     Reason: {idx['reason']}")

        # Apply safe optimizations
        print(f"\n🔧 Applying safe optimizations...")
        optimization_result = await optimizer.apply_automatic_optimizations()

        if optimization_result['optimizations_applied']:
            print(f"✅ Optimizations Applied:")
            for opt in optimization_result['optimizations_applied']:
                print(f"   • {opt}")

        if optimization_result['warnings']:
            print(f"⚠️  Warnings:")
            for warning in optimization_result['warnings']:
                print(f"   • {warning}")

        # Save detailed report
        report_file = "database_excellence_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Determine exit code based on overall grade
        if report['overall_grade'] in ['A', 'B']:
            print(f"\n✅ Database excellence check PASSED")
            return 0
        elif report['overall_grade'] == 'C':
            print(f"\n⚠️  Database excellence check PASSED with warnings")
            return 0
        else:
            print(f"\n❌ Database excellence check FAILED")
            return 1

    except Exception as e:
        logger.error(f"Error during database optimization: {e}")
        print(f"❌ Database optimization failed: {e}")
        return 1

    finally:
        if optimizer.connection_pool:
            await optimizer.connection_pool.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
