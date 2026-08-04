"""
Performance Monitoring API Endpoints

Provides real-time visibility into application performance metrics.

Endpoints:
- GET /api/v1/monitoring/performance - Current performance snapshot
- GET /api/v1/monitoring/health - Performance health status
- GET /api/v1/monitoring/slow-queries - Recent slow queries
- GET /api/v1/monitoring/metrics - Detailed metrics

Access: Admin only (protect with authentication middleware)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.monitoring.performance_dashboard import (
    PerformanceMonitor,
    get_performance_health_status,
    get_performance_monitor,
)

router = APIRouter()


@router.get("/performance")
async def get_performance_snapshot(
    current_user: User = Depends(get_current_active_user),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get current performance metrics snapshot.

    Returns:
        - Query metrics (execution counts, avg/max times)
        - Slow queries (last 20)
        - Connection pool metrics
        - System metrics (memory, CPU)
        - Response time percentiles (P50, P95, P99)
        - Issues detected (N+1 queries, unbounded queries)

    Requires: Admin role
    """
    # Check admin permission (case-insensitive)
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=403, detail="Performance metrics require admin access"
        )

    snapshot = monitor.get_snapshot()
    return snapshot.to_dict()


@router.get("/health")
async def get_performance_health(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get performance health status with alerts.
    """
    # For demo, allow access to authenticated users
    return get_performance_health_status()


@router.get("/slow-queries")
async def get_slow_queries(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get recent slow queries for analysis.

    Query parameters:
        - limit: Number of queries to return (default: 50, max: 200)

    Returns:
        - Query text
        - Execution time
        - Timestamp
        - Result size
        - Endpoint (if available)

    Requires: Admin role
    """
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=403, detail="Slow query log requires admin access"
        )

    limit = min(limit, 200)  # Cap at 200
    snapshot = monitor.get_snapshot()

    return {
        "total_slow_queries": len(snapshot.slow_queries),
        "showing_last": min(limit, len(snapshot.slow_queries)),
        "slow_queries": [q.to_dict() for q in list(snapshot.slow_queries)[-limit:]],
    }


@router.get("/performance-metrics")
async def get_detailed_metrics(
    current_user: User = Depends(get_current_active_user),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get detailed performance metrics for analysis.

    Includes all available metrics in raw format for
    custom analysis and dashboarding.

    Requires: Admin role
    """
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=403, detail="Detailed metrics require admin access"
        )

    snapshot = monitor.get_snapshot()

    return {
        "timestamp": (
            snapshot.query_metrics.get(
                list(snapshot.query_metrics.keys())[0],
                type("obj", (object,), {"last_executed": None}),
            ).last_executed.isoformat()
            if snapshot.query_metrics
            else None
        ),
        "query_metrics": {
            name: {
                "execution_count": m.execution_count,
                "total_time": round(m.total_time, 3),
                "max_time": round(m.max_time, 3),
                "avg_time": round(m.avg_time, 3),
                "result_size_mb": (
                    round(sum(m.result_sizes) / 1024 / 1024, 2) if m.result_sizes else 0
                ),
                "last_executed": (
                    m.last_executed.isoformat() if m.last_executed else None
                ),
            }
            for name, m in snapshot.query_metrics.items()
        },
        "slow_queries": {
            "count": len(snapshot.slow_queries),
            "queries": [q.to_dict() for q in list(snapshot.slow_queries)[-100:]],
        },
        "connection_pool": {
            "pool_size": snapshot.pool_metrics.pool_size,
            "checked_out": snapshot.pool_metrics.checked_out,
            "overflow": snapshot.pool_metrics.overflow,
            "total_connections": snapshot.pool_metrics.total_connections,
        },
        "system": {
            "memory_usage_mb": round(snapshot.memory_usage_mb, 2),
            "memory_usage_gb": round(snapshot.memory_usage_mb / 1024, 2),
            "cpu_usage_percent": round(snapshot.cpu_usage_percent, 2),
        },
        "response_times": {
            "p50_ms": round(snapshot.p50_response_time * 1000, 2),
            "p95_ms": round(snapshot.p95_response_time * 1000, 2),
            "p99_ms": round(snapshot.p99_response_time * 1000, 2),
            "p50_s": round(snapshot.p50_response_time, 3),
            "p95_s": round(snapshot.p95_response_time, 3),
            "p99_s": round(snapshot.p99_response_time, 3),
        },
        "scalability_issues": {
            "n_plus_1_queries": len(snapshot.potential_n_plus_1_queries),
            "unbounded_queries": len(snapshot.unbounded_queries),
            "queries_exceeding_threshold": len(
                [
                    m
                    for m in snapshot.query_metrics.values()
                    if m.max_time > monitor.SLOW_QUERY_THRESHOLD
                ]
            ),
        },
    }


@router.post("/reset")
async def reset_metrics(
    current_user: User = Depends(get_current_active_user),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Reset performance metrics.

    Use this to clear metrics after deployment or during testing.

    Requires: Admin role
    """
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=403, detail="Metrics reset requires admin access"
        )

    # Create a new monitor instance (effectively resetting)
    monitor.__init__()

    return {
        "status": "success",
        "message": "Performance metrics reset successfully",
        "timestamp": (
            monitor.get_snapshot()
            .query_metrics.get("reset", type("obj", (object,), {"last_executed": None}))
            .last_executed.isoformat()
            if monitor.get_snapshot().query_metrics
            else None
        ),
    }
