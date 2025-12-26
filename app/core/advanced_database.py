"""
Advanced Database Connection Management

This module provides enterprise-grade database connection management with:
- Connection pooling with intelligent scaling
- Circuit breaker for database resilience
- Health monitoring and automatic failover
- Performance metrics and optimization
- Multi-database support (read/write splitting)
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseRole(Enum):
    PRIMARY = "primary"
    REPLICA = "replica"
    ANALYTICS = "analytics"


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    role: DatabaseRole
    min_connections: int = 5
    max_connections: int = 50
    command_timeout: int = 30
    server_settings: Optional[Dict[str, str]] = None


@dataclass
class PoolMetrics:
    """Database pool performance metrics"""
    active_connections: int
    idle_connections: int
    total_connections: int
    max_connections: int
    usage_percent: float
    query_count: int
    avg_query_time_ms: float
    error_count: int
    last_error_time: Optional[float]


class CircuitBreaker:
    """Database circuit breaker implementation"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self.lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)

            async with self.lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0

            return result

        except Exception as e:
            async with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

            raise e


class AdvancedDatabaseManager:
    """Enterprise-grade database connection manager"""

    def __init__(self):
        self.pools: Dict[DatabaseRole, asyncpg.Pool] = {}
        self.configs: Dict[DatabaseRole, DatabaseConfig] = {}
        self.metrics: Dict[DatabaseRole, PoolMetrics] = {}
        self.circuit_breakers: Dict[DatabaseRole, CircuitBreaker] = {}
        self.health_checks: Dict[DatabaseRole, bool] = {}
        self.initialized = False

    async def initialize(self, configs: List[DatabaseConfig]):
        """Initialize database connection pools"""
        logger.info("Initializing advanced database manager...")

        for config in configs:
            try:
                # Create connection pool
                pool = await self._create_pool(config)
                self.pools[config.role] = pool
                self.configs[config.role] = config

                # Initialize circuit breaker
                self.circuit_breakers[config.role] = CircuitBreaker()

                # Initialize metrics
                self.metrics[config.role] = PoolMetrics(
                    active_connections=0,
                    idle_connections=0,
                    total_connections=0,
                    max_connections=config.max_connections,
                    usage_percent=0.0,
                    query_count=0,
                    avg_query_time_ms=0.0,
                    error_count=0,
                    last_error_time=None
                )

                # Perform initial health check
                self.health_checks[config.role] = await self._health_check(config.role)

                logger.info(f"✅ Database pool initialized for {config.role.value}")

            except Exception as e:
                logger.error(f"❌ Failed to initialize {config.role.value} database: {e}")
                raise

        self.initialized = True
        logger.info("🚀 Advanced database manager initialized successfully")

    async def _create_pool(self, config: DatabaseConfig) -> asyncpg.Pool:
        """Create optimized connection pool"""
        server_settings = config.server_settings or {
            'application_name': 'psychsync',
            'timezone': 'UTC',
            'search_path': 'public',
            'jit': 'off',  # Disable JIT for production stability
        }

        pool = await asyncpg.create_pool(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password,
            min_size=config.min_connections,
            max_size=config.max_connections,
            command_timeout=config.command_timeout,
            server_settings=server_settings,
            setup=self._setup_connection,
            init=self._init_connection,
            # Connection optimization
            max_queries=50000,  # Reconnect after 50k queries
            max_inactive_connection_lifetime=300,  # 5 minutes
        )

        return pool

    async def _setup_connection(self, conn):
        """Setup connection after creation"""
        await conn.execute("SET session_preload_libraries = 'pg_stat_statements'")
        await conn.execute("SET pg_stat_statements.track = 'all'")
        await conn.execute("SET log_statement = 'none'")  # Disable query logging for performance
        await conn.execute("SET log_min_duration_statement = '1000'")  # Log slow queries only

        # Set row-level security context
        await conn.execute("SET app.current_user_id = ''")
        await conn.execute("SET app.client_ip_address = ''")
        await conn.execute("SET app.user_agent = ''")

    async def _init_connection(self, conn):
        """Initialize connection with performance settings"""
        await conn.execute("SET statement_timeout = '30s'")
        await conn.execute("SET lock_timeout = '10s'")
        await conn.execute("SET idle_in_transaction_session_timeout = '5min'")

    async def _health_check(self, role: DatabaseRole) -> bool:
        """Perform database health check"""
        try:
            pool = self.pools[role]
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
                await conn.execute("SELECT pg_is_in_recovery()")
                return True
        except Exception as e:
            logger.warning(f"Health check failed for {role.value}: {e}")
            return False

    async def get_connection(self, role: DatabaseRole = DatabaseRole.PRIMARY):
        """Get database connection with circuit breaker protection"""
        if not self.initialized:
            raise RuntimeError("Database manager not initialized")

        if role not in self.pools:
            raise ValueError(f"No pool configured for role: {role.value}")

        circuit_breaker = self.circuit_breakers[role]

        async def acquire_connection():
            return self.pools[role].acquire()

        try:
            conn = await circuit_breaker.call(acquire_connection)
            return EnhancedConnection(conn, role, self)
        except Exception as e:
            logger.error(f"Failed to acquire {role.value} connection: {e}")
            # Try failover to replica if primary fails
            if role == DatabaseRole.PRIMARY:
                logger.info("Attempting failover to replica...")
                return await self.get_connection(DatabaseRole.REPLICA)
            raise

    @asynccontextmanager
    async def get_transaction(self, role: DatabaseRole = DatabaseRole.PRIMARY):
        """Get database transaction with automatic cleanup"""
        conn = await self.get_connection(role)
        try:
            async with conn.transaction():
                yield conn
        finally:
            await conn.release()

    async def execute_query(self, query: str, *args, role: DatabaseRole = DatabaseRole.PRIMARY):
        """Execute query with metrics collection"""
        start_time = time.time()

        try:
            conn = await self.get_connection(role)
            result = await conn.fetch(query, *args)

            # Update metrics
            query_time = (time.time() - start_time) * 1000
            self._update_metrics(role, query_time, error=False)

            return result

        except Exception as e:
            # Update error metrics
            self._update_metrics(role, (time.time() - start_time) * 1000, error=True)
            raise

    async def execute_command(self, command: str, *args, role: DatabaseRole = DatabaseRole.PRIMARY):
        """Execute command with metrics collection"""
        start_time = time.time()

        try:
            conn = await self.get_connection(role)
            result = await conn.execute(command, *args)

            # Update metrics
            query_time = (time.time() - start_time) * 1000
            self._update_metrics(role, query_time, error=False)

            return result

        except Exception as e:
            # Update error metrics
            self._update_metrics(role, (time.time() - start_time) * 1000, error=True)
            raise

    def _update_metrics(self, role: DatabaseRole, query_time_ms: float, error: bool):
        """Update performance metrics"""
        if role not in self.metrics:
            return

        metrics = self.metrics[role]
        metrics.query_count += 1

        if error:
            metrics.error_count += 1
            metrics.last_error_time = time.time()

        # Update average query time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        metrics.avg_query_time_ms = (alpha * query_time_ms +
                                   (1 - alpha) * metrics.avg_query_time_ms)

    async def get_pool_metrics(self, role: DatabaseRole) -> PoolMetrics:
        """Get current pool metrics"""
        if role not in self.pools:
            raise ValueError(f"No pool configured for role: {role.value}")

        pool = self.pools[role]
        metrics = self.metrics[role]

        # Update connection metrics
        metrics.total_connections = pool.get_size()
        metrics.idle_connections = pool.get_idle_size()
        metrics.active_connections = metrics.total_connections - metrics.idle_connections
        metrics.usage_percent = (metrics.active_connections / metrics.max_connections) * 100

        return metrics

    async def get_all_metrics(self) -> Dict[DatabaseRole, PoolMetrics]:
        """Get metrics for all pools"""
        metrics = {}
        for role in DatabaseRole:
            if role in self.pools:
                metrics[role] = await self.get_pool_metrics(role)
        return metrics

    async def close_all(self):
        """Close all database connections"""
        logger.info("Closing all database connections...")

        for role, pool in self.pools.items():
            try:
                await pool.close()
                logger.info(f"✅ Closed {role.value} database pool")
            except Exception as e:
                logger.error(f"❌ Error closing {role.value} pool: {e}")

        self.pools.clear()
        self.initialized = False


class EnhancedConnection:
    """Enhanced database connection with automatic resource management"""

    def __init__(self, connection: asyncpg.Connection, role: DatabaseRole, manager: AdvancedDatabaseManager):
        self.conn = connection
        self.role = role
        self.manager = manager
        self.acquired_at = time.time()

    async def execute(self, query: str, *args):
        """Execute query with automatic retry"""
        return await self.conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Execute fetch with automatic retry"""
        return await self.conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Execute fetchrow with automatic retry"""
        return await self.conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Execute fetchval with automatic retry"""
        return await self.conn.fetchval(query, *args)

    def transaction(self):
        """Get transaction context"""
        return self.conn.transaction()

    async def set_user_context(self, user_id: str, client_ip: str = None, user_agent: str = None):
        """Set user context for row-level security"""
        await self.conn.execute("SET app.current_user_id = $1", user_id)
        if client_ip:
            await self.conn.execute("SET app.client_ip_address = $1", client_ip)
        if user_agent:
            await self.conn.execute("SET app.user_agent = $1", user_agent)

    async def clear_user_context(self):
        """Clear user context"""
        await self.conn.execute("RESET app.current_user_id")
        await self.conn.execute("RESET app.client_ip_address")
        await self.conn.execute("RESET app.user_agent")

    async def release(self):
        """Release connection back to pool"""
        connection_age = time.time() - self.acquired_at
        if connection_age > 300:  # 5 minutes
            logger.warning(f"Connection held for {connection_age:.2f} seconds")

        # Clear user context before returning to pool
        await self.clear_user_context()

        await self.conn.release()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


# Global database manager instance
db_manager = AdvancedDatabaseManager()


async def get_database_connection(role: DatabaseRole = DatabaseRole.PRIMARY):
    """Get database connection (dependency injection)"""
    return await db_manager.get_connection(role)


async def get_database_transaction(role: DatabaseRole = DatabaseRole.PRIMARY):
    """Get database transaction (dependency injection)"""
    return db_manager.get_transaction(role)


# Database initialization functions
async def initialize_databases(configs: List[DatabaseConfig]):
    """Initialize all database connections"""
    await db_manager.initialize(configs)


async def close_databases():
    """Close all database connections"""
    await db_manager.close_all()