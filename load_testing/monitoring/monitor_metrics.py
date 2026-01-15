"""
Real-time Metrics Collector for PsychSync Load Testing
Collects and exports metrics during load tests
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
import psutil
import psycopg2
import redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server, CollectorRegistry

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect metrics from various sources during load testing"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.registry = CollectorRegistry()

        # Prometheus metrics
        self.setup_prometheus_metrics()

        # Database connection
        self.db_conn = None
        self.redis_client = None

        # Metrics history
        self.metrics_history = []

    def setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""

        # API metrics
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['endpoint', 'method', 'status'],
            registry=self.registry
        )

        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['endpoint', 'method'],
            buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0],
            registry=self.registry
        )

        self.api_active_connections = Gauge(
            'api_active_connections',
            'Active API connections',
            registry=self.registry
        )

        # Database metrics
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self.registry
        )

        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['query_type'],
            buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1.0, 2.5, 5.0],
            registry=self.registry
        )

        self.db_connections_pool_size = Gauge(
            'db_connections_pool_size',
            'Database connection pool size',
            registry=self.registry
        )

        # Cache metrics
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate',
            registry=self.registry
        )

        self.cache_memory_usage = Gauge(
            'cache_memory_bytes',
            'Cache memory usage in bytes',
            registry=self.registry
        )

        # System metrics
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_usage = Gauge(
            'system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )

        self.system_disk_io = Gauge(
            'system_disk_io_bytes',
            'System disk I/O in bytes',
            ['direction'],
            registry=self.registry
        )

        # Load test specific
        self.load_test_active_users = Gauge(
            'load_test_active_users',
            'Number of active load test users',
            registry=self.registry
        )

        self.load_test_rps = Gauge(
            'load_test_requests_per_second',
            'Load test requests per second',
            registry=self.registry
        )

    def start_metrics_server(self, port: int = 9091):
        """Start Prometheus metrics HTTP server"""
        try:
            start_http_server(port, registry=self.registry)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

    def connect_database(self, connection_string: str):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(connection_string)
            logger.info("Connected to database for metrics collection")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")

    def connect_redis(self, host: str = 'localhost', port: int = 6379, password: str = None):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected to Redis for metrics collection")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    async def collect_database_metrics(self):
        """Collect database metrics"""
        if not self.db_conn:
            return

        try:
            with self.db_conn.cursor() as cursor:
                # Active connections
                cursor.execute("""
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """)
                active_connections = cursor.fetchone()[0]
                self.db_connections_active.set(active_connections)

                # Connection pool info
                cursor.execute("SHOW max_connections")
                max_connections = cursor.fetchone()[0]
                self.db_connections_pool_size.set(max_connections)

                # Slow queries
                cursor.execute("""
                    SELECT query, mean_exec_time, calls
                    FROM pg_stat_statements
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """)
                slow_queries = cursor.fetchall()

                return {
                    "active_connections": active_connections,
                    "max_connections": max_connections,
                    "slow_queries": [
                        {
                            "query": query[:100],
                            "mean_time": mean_time,
                            "calls": calls
                        }
                        for query, mean_time, calls in slow_queries
                    ]
                }

        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return None

    async def collect_redis_metrics(self):
        """Collect Redis metrics"""
        if not self.redis_client:
            return

        try:
            info = self.redis_client.info('stats')
            memory_info = self.redis_client.info('memory')

            # Calculate hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0

            self.cache_hit_rate.set(hit_rate)
            self.cache_memory_usage.set(memory_info.get('used_memory', 0))

            return {
                "hit_rate": hit_rate,
                "memory_used": memory_info.get('used_memory', 0),
                "memory_max": memory_info.get('maxmemory', 0),
                "total_keys": self.redis_client.dbsize(),
            }

        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
            return None

    async def collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.system_disk_io.labels(direction='read').set(disk_io.read_bytes)
                self.system_disk_io.labels(direction='write').set(disk_io.write_bytes)

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_io_read_mb": disk_io.read_bytes / (1024**2) if disk_io else 0,
                "disk_io_write_mb": disk_io.write_bytes / (1024**2) if disk_io else 0,
            }

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return None

    def record_api_request(self, endpoint: str, method: str, status: int, duration: float):
        """Record API request metrics"""
        self.api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=status
        ).inc()

        self.api_request_duration.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)

    def update_load_test_metrics(self, active_users: int, rps: float):
        """Update load test specific metrics"""
        self.load_test_active_users.set(active_users)
        self.load_test_rps.set(rps)

    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics and return as dictionary"""

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": await self.collect_database_metrics(),
            "redis": await self.collect_redis_metrics(),
            "system": await self.collect_system_metrics(),
        }

        self.metrics_history.append(metrics)

        # Keep only last 1000 samples
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

        return metrics

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics_history:
            return {}

        latest = self.metrics_history[-1]

        return {
            "latest_metrics": latest,
            "samples_collected": len(self.metrics_history),
            "collection_start": self.metrics_history[0]["timestamp"] if self.metrics_history else None,
            "collection_end": self.metrics_history[-1]["timestamp"] if self.metrics_history else None,
        }

    def save_metrics_to_file(self, filepath: str):
        """Save metrics history to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
            logger.info(f"Metrics saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    async def start_continuous_collection(self, interval: int = 5):
        """Continuously collect metrics at specified interval (seconds)"""
        logger.info(f"Starting continuous metrics collection every {interval}s")

        while True:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Metrics collection stopped")
                break
            except Exception as e:
                logger.error(f"Error during metrics collection: {e}")
                await asyncio.sleep(interval)

    def close(self):
        """Close connections"""
        if self.db_conn:
            self.db_conn.close()
        if self.redis_client:
            self.redis_client.close()


async def main():
    """Main execution for standalone metrics collector"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect metrics during load testing")
    parser.add_argument("--db-url", type=str, help="PostgreSQL connection string")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--interval", type=int, default=5, help="Collection interval (seconds)")
    parser.add_argument("--port", type=int, default=9091, help="Metrics server port")
    parser.add_argument("--output", type=str, help="Output JSON file path")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    collector = MetricsCollector()

    # Start metrics server
    collector.start_metrics_server(args.port)

    # Connect to data sources
    if args.db_url:
        collector.connect_database(args.db_url)

    collector.connect_redis(args.redis_host, args.redis_port)

    try:
        # Start continuous collection
        await collector.start_continuous_collection(args.interval)
    except KeyboardInterrupt:
        logger.info("Stopping metrics collection...")

        # Save metrics if output specified
        if args.output:
            collector.save_metrics_to_file(args.output)

        # Print summary
        summary = collector.get_metrics_summary()
        print("\n" + "=" * 60)
        print("METRICS COLLECTION SUMMARY")
        print("=" * 60)
        print(f"Samples collected: {summary.get('samples_collected', 0)}")
        print(f"Duration: {summary.get('collection_start', 'N/A')} to {summary.get('collection_end', 'N/A')}")
        print("=" * 60)

    finally:
        collector.close()


if __name__ == "__main__":
    asyncio.run(main())
