"""
API Performance Optimization Module
Provides comprehensive performance monitoring and optimization for API endpoints
"""

import time
import asyncio
import functools
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from collections import defaultdict
import logging
import json

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.query_optimizer import query_optimizer

logger = logging.getLogger(__name__)

@dataclass
class APIMetrics:
    """Metrics for API endpoint performance"""
    endpoint: str
    method: str
    execution_time_ms: float
    database_time_ms: float = 0.0
    response_size_bytes: int = 0
    status_code: int = 200
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    ip_address: str = ""
    user_agent: str = ""
    query_count: int = 0
    cache_hits: int = 0
    memory_usage_mb: float = 0.0

@dataclass
class PerformanceThresholds:
    """Performance thresholds for alerts"""
    response_time_warning: float = 500.0  # ms
    response_time_critical: float = 2000.0  # ms
    database_time_warning: float = 200.0  # ms
    memory_usage_warning: float = 100.0  # MB
    error_rate_warning: float = 5.0  # percentage
    query_count_warning: int = 10

class PerformanceMonitor:
    """
    Comprehensive API performance monitoring and analysis
    """

    def __init__(self):
        self.metrics: List[APIMetrics] = []
        self.thresholds = PerformanceThresholds()
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_calls': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf'),
            'error_count': 0,
            'slow_calls': 0,
            'database_time': 0.0,
            'query_count': 0
        })
        self.active_requests: Dict[str, float] = {}

    def record_request_start(self, request_id: str, endpoint: str):
        """Record the start of a request"""
        self.active_requests[request_id] = time.time()

    def record_request_end(
        self,
        request_id: str,
        request: Request,
        response: Response,
        execution_time_ms: float,
        database_time_ms: float = 0.0,
        query_count: int = 0,
        cache_hits: int = 0
    ):
        """Record the completion of a request"""
        if request_id in self.active_requests:
            del self.active_requests[request_id]

        metrics = APIMetrics(
            endpoint=request.url.path,
            method=request.method,
            execution_time_ms=execution_time_ms,
            database_time_ms=database_time_ms,
            response_size_bytes=len(response.body) if hasattr(response, 'body') else 0,
            status_code=response.status_code,
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            query_count=query_count,
            cache_hits=cache_hits
        )

        # Extract user ID if available
        if hasattr(request.state, 'user') and request.state.user:
            metrics.user_id = str(request.state.user.id)

        self.metrics.append(metrics)
        self._update_endpoint_stats(metrics)
        self._check_performance_alerts(metrics)

    def _update_endpoint_stats(self, metrics: APIMetrics):
        """Update endpoint statistics"""
        key = f"{metrics.method} {metrics.endpoint}"
        stats = self.endpoint_stats[key]

        stats['total_calls'] += 1
        stats['total_time'] += metrics.execution_time_ms
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
        stats['max_time'] = max(stats['max_time'], metrics.execution_time_ms)
        stats['min_time'] = min(stats['min_time'], metrics.execution_time_ms)
        stats['database_time'] += metrics.database_time_ms
        stats['query_count'] += metrics.query_count

        if metrics.status_code >= 400:
            stats['error_count'] += 1

        if metrics.execution_time_ms > self.thresholds.response_time_warning:
            stats['slow_calls'] += 1

    def _check_performance_alerts(self, metrics: APIMetrics):
        """Check for performance alerts"""
        if metrics.execution_time_ms > self.thresholds.response_time_critical:
            logger.critical(
                f"CRITICAL: Slow API response - {metrics.method} {metrics.endpoint} "
                f"took {metrics.execution_time_ms:.2f}ms"
            )
        elif metrics.execution_time_ms > self.thresholds.response_time_warning:
            logger.warning(
                f"WARNING: Slow API response - {metrics.method} {metrics.endpoint} "
                f"took {metrics.execution_time_ms:.2f}ms"
            )

        if metrics.database_time_ms > self.thresholds.database_time_warning:
            logger.warning(
                f"WARNING: High database time - {metrics.method} {metrics.endpoint} "
                f"database took {metrics.database_time_ms:.2f}ms"
            )

        if metrics.query_count > self.thresholds.query_count_warning:
            logger.warning(
                f"WARNING: High query count - {metrics.method} {metrics.endpoint} "
                f"executed {metrics.query_count} queries"
            )

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"message": "No metrics available for the specified time range"}

        total_requests = len(recent_metrics)
        avg_response_time = sum(m.execution_time_ms for m in recent_metrics) / total_requests
        error_rate = sum(1 for m in recent_metrics if m.status_code >= 400) / total_requests * 100

        # Calculate slowest endpoints
        endpoint_performance = {}
        for metrics in recent_metrics:
            key = f"{metrics.method} {metrics.endpoint}"
            if key not in endpoint_performance:
                endpoint_performance[key] = []
            endpoint_performance[key].append(metrics.execution_time_ms)

        slowest_endpoints = sorted([
            (endpoint, sum(times) / len(times))
            for endpoint, times in endpoint_performance.items()
        ], key=lambda x: x[1], reverse=True)[:10]

        return {
            "time_range_hours": hours,
            "total_requests": total_requests,
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate_percent": round(error_rate, 2),
            "slowest_endpoints": [
                {"endpoint": ep, "avg_time_ms": round(time_ms, 2)}
                for ep, time_ms in slowest_endpoints
            ],
            "active_requests": len(self.active_requests),
            "total_database_queries": sum(m.query_count for m in recent_metrics),
            "cache_hit_rate": self._calculate_cache_hit_rate(recent_metrics)
        }

    def _calculate_cache_hit_rate(self, metrics_list: List[APIMetrics]) -> float:
        """Calculate cache hit rate"""
        total_queries = sum(m.query_count for m in metrics_list)
        total_hits = sum(m.cache_hits for m in metrics_list)

        return (total_hits / total_queries * 100) if total_queries > 0 else 0.0

    def get_slow_queries_report(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get report of slow database queries"""
        slow_queries = query_optimizer.get_slow_queries(hours=hours)

        return [
            {
                "query": q.query_text[:200] + "..." if len(q.query_text) > 200 else q.query_text,
                "execution_time_ms": q.execution_time_ms,
                "complexity": q.complexity.value,
                "optimization_suggestions": [s.value for s in q.optimization_suggestions]
            }
            for q in slow_queries
        ]

class PerformanceOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically monitor and optimize API performance
    """

    def __init__(self, app, monitor: PerformanceMonitor):
        super().__init__(app)
        self.monitor = monitor

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = f"{id(request)}-{int(time.time())}"

        # Record start time
        start_time = time.time()
        database_start = 0.0
        database_end = 0.0
        query_count = 0

        # Track database queries
        original_execute = None

        # Wrap database session if available
        if hasattr(request.state, 'db') and request.state.db:
            original_execute = request.state.db.execute

            async def track_queries(sql, *args, **kwargs):
                nonlocal query_count, database_start, database_end

                db_start = time.time()
                query_count += 1

                try:
                    result = await original_execute(sql, *args, **kwargs)
                    return result
                finally:
                    database_end += time.time() - db_start

            request.state.db.execute = track_queries

        try:
            # Process request
            response = await call_next(request)

            # Calculate timing
            execution_time_ms = (time.time() - start_time) * 1000
            database_time_ms = database_end * 1000

            # Record metrics
            self.monitor.record_request_end(
                request_id=request_id,
                request=request,
                response=response,
                execution_time_ms=execution_time_ms,
                database_time_ms=database_time_ms,
                query_count=query_count
            )

            # Add performance headers
            response.headers["X-Response-Time"] = f"{execution_time_ms:.2f}ms"
            if database_time_ms > 0:
                response.headers["X-Database-Time"] = f"{database_time_ms:.2f}ms"
            if query_count > 0:
                response.headers["X-Query-Count"] = str(query_count)

            return response

        except Exception as e:
            # Record error metrics
            execution_time_ms = (time.time() - start_time) * 1000

            # Create error response
            from fastapi.responses import JSONResponse
            error_response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id}
            )

            # Record metrics for failed request
            self.monitor.record_request_end(
                request_id=request_id,
                request=request,
                response=error_response,
                execution_time_ms=execution_time_ms,
                database_time_ms=database_end * 1000,
                query_count=query_count
            )

            raise

def performance_monitor(monitor: PerformanceMonitor):
    """
    Decorator to monitor function performance
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000

                logger.debug(f"Function {function_name} executed in {execution_time:.2f}ms")

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Function {function_name} failed after {execution_time:.2f}ms: {e}")
                raise

        return wrapper
    return decorator

class DatabaseConnectionPool:
    """
    Enhanced database connection pool management
    """

    def __init__(self, engine):
        self.engine = engine
        self.pool_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'overflow_connections': 0
        }

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status"""
        pool = self.engine.pool

        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid(),
            'total_connections': pool.size() + pool.overflow(),
            'active_connections': pool.checkedout(),
            'idle_connections': pool.checkedin(),
            'utilization_percent': (pool.checkedout() / (pool.size() + pool.overflow()) * 100) if (pool.size() + pool.overflow()) > 0 else 0
        }

    @asynccontextmanager
    async def get_monitored_session(self):
        """Get database session with performance monitoring"""
        async with self.engine.begin() as session:
            start_time = time.time()

            try:
                yield session
            finally:
                execution_time = (time.time() - start_time) * 1000

                if execution_time > 1000:  # Log slow transactions
                    logger.warning(f"Slow database transaction: {execution_time:.2f}ms")

# Global performance monitor instance
performance_monitor_instance = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor_instance

def optimize_api_response(response_data: Any, endpoint: str) -> Any:
    """
    Optimize API response for better performance
    """
    # Remove unnecessary fields from common response types
    if isinstance(response_data, dict):
        # Remove debug fields in production
        debug_fields = ['debug_info', 'internal_metadata', 'query_explain']
        for field in debug_fields:
            response_data.pop(field, None)

        # Optimize datetime formatting
        for key, value in response_data.items():
            if isinstance(value, datetime):
                response_data[key] = value.isoformat()

    elif isinstance(response_data, list):
        # Optimize list responses by limiting size for large datasets
        if len(response_data) > 1000:
            logger.warning(f"Large response detected for {endpoint}: {len(response_data)} items")

    return response_data

class ResponseCacheManager:
    """
    Intelligent response caching system with multi-layered strategy
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0
        }
        self.max_memory_size = 1000  # Max items in memory cache
        self.cache_key_prefix = "api_cache"

        # TTL configurations for different endpoint types (seconds)
        self.ttl_config = {
            'public_data': 300,      # 5 minutes - public assessments, templates
            'user_profile': 600,     # 10 minutes - user profiles, preferences
            'analytics': 900,        # 15 minutes - analytics reports
            'assessment_list': 180,   # 3 minutes - assessment listings
            'team_data': 300,        # 5 minutes - team information
            'lookup_data': 3600,     # 1 hour - static lookup data
            'search_results': 60,    # 1 minute - search results
        }

    def _generate_cache_key(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Generate cache key based on request parameters"""
        import hashlib

        # Sort params for consistent key generation
        sorted_params = sorted(params.items())
        param_string = json.dumps(sorted_params, sort_keys=True)

        # Create hash of parameters
        param_hash = hashlib.md5(param_string.encode()).hexdigest()

        # Include user ID for user-specific data
        user_prefix = f"user_{user_id}:" if user_id else "public:"

        return f"{self.cache_key_prefix}:{user_prefix}{method}:{endpoint}:{param_hash}"

    def _get_ttl_for_endpoint(self, endpoint: str, method: str) -> int:
        """Get appropriate TTL for endpoint"""
        if method != 'GET':
            return 0  # Don't cache non-GET requests

        endpoint_lower = endpoint.lower()

        # Determine cache category based on endpoint patterns
        if any(pattern in endpoint_lower for pattern in ['lookup', 'enum', 'static']):
            return self.ttl_config['lookup_data']
        elif any(pattern in endpoint_lower for pattern in ['profile', 'me']):
            return self.ttl_config['user_profile']
        elif any(pattern in endpoint_lower for pattern in ['analytics', 'stats', 'metrics']):
            return self.ttl_config['analytics']
        elif any(pattern in endpoint_lower for pattern in ['assessment', 'survey']):
            return self.ttl_config['assessment_list']
        elif any(pattern in endpoint_lower for pattern in ['team', 'organization']):
            return self.ttl_config['team_data']
        elif any(pattern in endpoint_lower for pattern in ['search']):
            return self.ttl_config['search_results']
        else:
            return self.ttl_config['public_data']

    async def get_cached_response(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        cache_key = self._generate_cache_key(endpoint, method, params, user_id)

        # Try memory cache first
        if cache_key in self.in_memory_cache:
            cached_data = self.in_memory_cache[cache_key]
            if cached_data['expires_at'] > time.time():
                self.cache_stats['hits'] += 1
                return cached_data['response']
            else:
                # Remove expired entry
                del self.in_memory_cache[cache_key]

        # Try Redis cache if available
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    response = json.loads(cached_data)

                    # Also store in memory for faster access
                    self._store_in_memory(cache_key, response, 60)  # 1 minute in memory
                    return response
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")

        self.cache_stats['misses'] += 1
        return None

    async def cache_response(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        response_data: Any,
        user_id: Optional[str] = None
    ):
        """Cache response data"""
        ttl = self._get_ttl_for_endpoint(endpoint, method)
        if ttl == 0:
            return  # Don't cache non-GET requests

        cache_key = self._generate_cache_key(endpoint, method, params, user_id)

        # Store in memory
        self._store_in_memory(cache_key, response_data, min(ttl, 300))  # Max 5 minutes in memory

        # Store in Redis
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(response_data, default=str)
                )
                self.cache_stats['sets'] += 1
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")

    def _store_in_memory(self, cache_key: str, response_data: Any, ttl_seconds: int):
        """Store data in memory cache with LRU eviction"""
        # Remove oldest entries if cache is full
        if len(self.in_memory_cache) >= self.max_memory_size:
            self._evict_oldest_memory_entry()

        self.in_memory_cache[cache_key] = {
            'response': response_data,
            'expires_at': time.time() + ttl_seconds,
            'cached_at': time.time()
        }

    def _evict_oldest_memory_entry(self):
        """Evict the oldest entry from memory cache"""
        if not self.in_memory_cache:
            return

        oldest_key = min(
            self.in_memory_cache.keys(),
            key=lambda k: self.in_memory_cache[k]['cached_at']
        )
        del self.in_memory_cache[oldest_key]

    async def invalidate_cache_patterns(self, patterns: List[str]):
        """Invalidate cache entries matching patterns"""
        invalidated_count = 0

        # Invalidate memory cache entries
        keys_to_remove = []
        for cache_key in self.in_memory_cache.keys():
            if any(pattern in cache_key for pattern in patterns):
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self.in_memory_cache[key]
            invalidated_count += 1

        # Invalidate Redis cache entries
        if self.redis:
            try:
                # Get all cache keys matching patterns
                for pattern in patterns:
                    search_pattern = f"{self.cache_key_prefix}:*{pattern}*"
                    keys = await self.redis.keys(search_pattern)
                    if keys:
                        await self.redis.delete(*keys)
                        invalidated_count += len(keys)
            except Exception as e:
                logger.warning(f"Redis cache invalidation error: {e}")

        self.cache_stats['invalidations'] += invalidated_count
        logger.info(f"Invalidated {invalidated_count} cache entries for patterns: {patterns}")

    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a specific user"""
        await self.invalidate_cache_patterns([f"user_{user_id}:"])

    async def invalidate_endpoint_cache(self, endpoint: str):
        """Invalidate cache for a specific endpoint"""
        patterns = [
            f":GET:{endpoint}:",
            f":POST:{endpoint}:",
            f":PUT:{endpoint}:",
            f":PATCH:{endpoint}:",
        ]
        await self.invalidate_cache_patterns(patterns)

    async def warm_cache(self, endpoint_data: List[Dict[str, Any]]):
        """Warm cache with precomputed responses"""
        logger.info(f"Warming cache with {len(endpoint_data)} endpoints")

        for data in endpoint_data:
            try:
                await self.cache_response(
                    endpoint=data['endpoint'],
                    method=data.get('method', 'GET'),
                    params=data.get('params', {}),
                    response_data=data['response'],
                    user_id=data.get('user_id')
                )
            except Exception as e:
                logger.warning(f"Cache warming failed for {data.get('endpoint', 'unknown')}: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'memory_cache_size': len(self.in_memory_cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'invalidations': self.cache_stats['invalidations'],
            'hit_rate_percent': round(hit_rate, 2),
            'memory_usage_mb': round(
                len(json.dumps(self.in_memory_cache, default=str)) / (1024 * 1024), 2
            )
        }

# Global cache manager instance
cache_manager = ResponseCacheManager()

def get_cache_manager() -> ResponseCacheManager:
    """Get the global cache manager instance"""
    return cache_manager