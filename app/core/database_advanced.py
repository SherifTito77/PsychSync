# app/core/database_advanced.py
"""
Advanced database optimizations for PsychSync
Includes connection pooling, query optimization, and performance monitoring
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy import text, event, DDL
from sqlalchemy.engine import Engine
from app.core.config import settings
from app.core.constants import Database

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models with advanced features"""

    __abstract__ = True

    # Global query timeout
    query_timeout = 30

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary with smart exclusions"""
        exclude = exclude or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if value is not None:
                    # Handle UUID serialization
                    if hasattr(value, 'hex'):
                        result[column.name] = str(value)
                    # Handle datetime serialization
                    elif hasattr(value, 'isoformat'):
                        result[column.name] = value.isoformat()
                    else:
                        result[column.name] = value

        return result


# Create optimized async database engine with advanced settings
async_engine = create_async_engine(
    settings.get_database_url(async_driver=True),
    # Advanced pool configuration
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,

    # Connection timeout and retry settings
    pool_timeout=30,  # Wait 30 seconds for connection
    connect_args={
        "command_timeout": 30,
        "server_settings": {
            "application_name": "psychsync_api",
            "jit": "off",  # Disable JIT for consistent performance
        }
    },

    # Query optimization settings
    echo=settings.DB_ECHO,
    echo_pool=False,  # Don't log pool messages in production
    future=True,

    # Performance optimizations
    isolation_level="READ_COMMITTED",
    executemany_mode="values",
    executemany_values_page_size=1000,
)

# Create async session factory with optimized settings
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    # Enable savepoints for nested transactions
    join_transaction_mode="savepoint",
)

# Database performance monitor
class DatabaseMonitor:
    """Advanced database performance monitoring"""

    def __init__(self):
        self.query_stats: Dict[str, Any] = {
            'total_queries': 0,
            'total_time': 0.0,
            'slow_queries': 0,
            'error_queries': 0,
            'query_types': {},
            'slow_threshold': 1.0  # seconds
        }

    def record_query(self, query: str, duration: float, error: bool = False):
        """Record query performance statistics"""
        self.query_stats['total_queries'] += 1
        self.query_stats['total_time'] += duration

        if error:
            self.query_stats['error_queries'] += 1
        elif duration > self.query_stats['slow_threshold']:
            self.query_stats['slow_queries'] += 1
            logger.warning(f"Slow query detected: {duration:.2f}s - {query[:100]}...")

        # Track query types
        query_type = query.strip().split()[0].upper() if query else 'UNKNOWN'
        self.query_stats['query_types'][query_type] = \
            self.query_stats['query_types'].get(query_type, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_queries = self.query_stats['total_queries']
        if total_queries == 0:
            return self.query_stats

        avg_time = self.query_stats['total_time'] / total_queries

        return {
            **self.query_stats,
            'avg_query_time': avg_time,
            'slow_query_percentage': (self.query_stats['slow_queries'] / total_queries) * 100,
            'error_query_percentage': (self.query_stats['error_queries'] / total_queries) * 100,
        }

# Global database monitor instance
db_monitor = DatabaseMonitor()

# Performance monitoring event listeners
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query completion and performance stats"""
    total = time.time() - context._query_start_time
    db_monitor.record_query(str(statement), total)

@event.listens_for(Engine, "handle_error")
def handle_error(exception_context):
    """Record database errors"""
    context = exception_context.execution_context
    if context:
        db_monitor.record_query(
            str(context.statement) if context.statement else "UNKNOWN",
            0.0,
            error=True
        )

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Advanced async database dependency with performance monitoring
    """
    async with AsyncSessionLocal() as session:
        session.begin()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction failed: {str(e)}")
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_async_db_with_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions with advanced error handling
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise

# Advanced query optimization functions
class QueryOptimizer:
    """Advanced query optimization utilities"""

    @staticmethod
    async def analyze_table(db: AsyncSession, table_name: str) -> Dict[str, Any]:
        """Analyze table statistics and suggest optimizations"""
        try:
            result = await db.execute(text(f"""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE tablename = '{table_name}'
            """))

            stats = result.mappings().first()

            # Get index usage statistics
            index_result = await db.execute(text(f"""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE tablename = '{table_name}'
                ORDER BY idx_scan DESC
            """))

            index_stats = index_result.mappings().all()

            return {
                'table_stats': dict(stats) if stats else {},
                'index_stats': [dict(row) for row in index_stats],
                'optimization_suggestions': QueryOptimizer._get_suggestions(stats, index_stats)
            }

        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            return {}

    @staticmethod
    def _get_suggestions(table_stats, index_stats) -> List[str]:
        """Generate optimization suggestions based on statistics"""
        suggestions = []

        if table_stats:
            # Check for high dead tuple ratio
            live_tuples = table_stats.get('live_tuples', 0)
            dead_tuples = table_stats.get('dead_tuples', 0)

            if live_tuples > 0 and dead_tuples / live_tuples > 0.2:
                suggestions.append("Consider running VACUUM ANALYZE on this table")

            # Check for unused indexes
            unused_indexes = [
                idx['indexname'] for idx in index_stats
                if idx.get('index_scans', 0) == 0
            ]

            if unused_indexes:
                suggestions.append(f"Unused indexes detected: {', '.join(unused_indexes[:3])}")

        return suggestions

# Database health and performance monitoring
async def get_database_health() -> Dict[str, Any]:
    """Comprehensive database health check"""
    health_info = {
        'status': 'unknown',
        'connections': 0,
        'active_connections': 0,
        'idle_connections': 0,
        'database_size': 0,
        'performance_stats': db_monitor.get_stats(),
        'slow_queries': 0,
        'cache_hit_ratio': 0.0
    }

    try:
        async with AsyncSessionLocal() as session:
            # Connection statistics
            result = await session.execute(text("""
                SELECT
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))

            conn_stats = result.mappings().first()
            if conn_stats:
                health_info.update({
                    'status': 'healthy',
                    'connections': conn_stats['total_connections'],
                    'active_connections': conn_stats['active_connections'],
                    'idle_connections': conn_stats['idle_connections']
                })

            # Database size
            result = await session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """))

            size_result = result.scalar()
            health_info['database_size'] = size_result

            # Cache hit ratio
            result = await session.execute(text("""
                SELECT
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                FROM pg_statio_user_tables
                WHERE (sum(heap_blks_hit) + sum(heap_blks_read)) > 0
            """))

            cache_ratio = result.scalar()
            health_info['cache_hit_ratio'] = float(cache_ratio) if cache_ratio else 0.0

            # Slow queries (pg_stat_statements extension)
            try:
                result = await session.execute(text("""
                    SELECT count(*) as slow_queries
                    FROM pg_stat_statements
                    WHERE mean_time > 1000  -- queries taking more than 1 second
                """))

                slow_queries = result.scalar()
                health_info['slow_queries'] = slow_queries or 0

            except Exception:
                # pg_stat_statements extension not available
                health_info['slow_queries'] = -1

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_info['status'] = 'error'
        health_info['error'] = str(e)

    return health_info

# Advanced database maintenance
class DatabaseMaintenance:
    """Advanced database maintenance operations"""

    @staticmethod
    async def vacuum_analyze_table(db: AsyncSession, table_name: str) -> bool:
        """Run VACUUM ANALYZE on a specific table"""
        try:
            await db.execute(text(f"VACUUM ANALYZE {table_name}"))
            await db.commit()
            logger.info(f"VACUUM ANALYZE completed for table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"VACUUM ANALYZE failed for {table_name}: {str(e)}")
            return False

    @staticmethod
    async def update_table_statistics(db: AsyncSession, table_name: str) -> bool:
        """Update table statistics"""
        try:
            await db.execute(text(f"ANALYZE {table_name}"))
            await db.commit()
            logger.info(f"Statistics updated for table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Statistics update failed for {table_name}: {str(e)}")
            return False

    @staticmethod
    async def reindex_table(db: AsyncSession, table_name: str) -> bool:
        """Rebuild indexes on a table"""
        try:
            await db.execute(text(f"REINDEX TABLE {table_name}"))
            await db.commit()
            logger.info(f"Indexes rebuilt for table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Reindex failed for {table_name}: {str(e)}")
            return False

# Connection pool monitoring
async def get_connection_pool_stats() -> Dict[str, Any]:
    """Get connection pool statistics"""
    pool = async_engine.pool

    return {
        'pool_size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'status': f"{pool.checkedout()}/{pool.size() + pool.overflow()} connections in use"
    }

# Graceful shutdown
async def close_database_connections():
    """Gracefully close all database connections"""
    try:
        await async_engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")

# Database initialization with advanced features
async def init_advanced_db():
    """Initialize database with advanced features"""
    try:
        async with async_engine.begin() as conn:
            # Create tables with optimizations
            await conn.run_sync(Base.metadata.create_all)

            # Create performance monitoring extensions
            await conn.execute(text("""
                CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
            """))

            # Set performance optimizations
            await conn.execute(text("""
                -- Improve performance for large tables
                ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
                ALTER SYSTEM SET track_activity_query_size = 2048;
                ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
            """))

        logger.info("Advanced database initialization completed successfully")

    except Exception as e:
        logger.error(f"Advanced database initialization failed: {str(e)}")
        raise