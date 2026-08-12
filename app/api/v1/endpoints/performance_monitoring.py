"""
Performance Monitoring API Endpoints

Reports real system metrics: CPU, memory, DB connection pool status,
and process-level resource usage via psutil.
"""

import time
from datetime import datetime
from typing import Any

import psutil
from fastapi import APIRouter, Depends

from app.core.database import async_engine
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/monitoring", tags=["Performance Monitoring"])

# Simple in-memory request timing tracker (lightweight, no external deps)
_request_times: list[float] = []
_MAX_SAMPLES = 500


def _record_request_time(duration: float) -> None:
    """Record a request duration for percentile calculation."""
    _request_times.append(duration)
    if len(_request_times) > _MAX_SAMPLES:
        del _request_times[: _MAX_SAMPLES // 2]


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _system_metrics() -> dict[str, Any]:
    """Gather real system metrics via psutil."""
    process = psutil.Process()
    mem_info = process.memory_info()
    cpu_pct = process.cpu_percent(interval=0)

    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "memory_usage_mb": round(mem_info.rss / (1024 * 1024), 1),
        "memory_vms_mb": round(mem_info.vms / (1024 * 1024), 1),
        "cpu_usage_percent": round(cpu_pct, 1),
        "system_memory_percent": round(vm.percent, 1),
        "system_memory_available_mb": round(vm.available / (1024 * 1024), 1),
        "disk_usage_percent": round(disk.percent, 1),
        "open_file_descriptors": (
            process.num_fds() if hasattr(process, "num_fds") else 0
        ),
        "thread_count": process.num_threads(),
    }


def _pool_metrics() -> dict[str, Any]:
    """Get SQLAlchemy connection pool status."""
    pool = async_engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
        "max_overflow": getattr(pool, "_max_overflow", 0),
    }


def _response_times() -> dict[str, float]:
    """Compute response time percentiles from recent samples."""
    return {
        "p50": round(_percentile(_request_times, 50), 3),
        "p95": round(_percentile(_request_times, 95), 3),
        "p99": round(_percentile(_request_times, 99), 3),
        "sample_count": len(_request_times),
    }


def _detect_issues(sys_metrics: dict, pool: dict) -> dict[str, int]:
    """Detect potential performance issues from current metrics."""
    issues = {
        "high_memory": 1 if sys_metrics["memory_usage_mb"] > 500 else 0,
        "high_cpu": 1 if sys_metrics["cpu_usage_percent"] > 80 else 0,
        "pool_exhaustion_risk": (
            1 if pool["checked_out"] > pool["pool_size"] * 0.8 else 0
        ),
        "high_disk_usage": 1 if sys_metrics["disk_usage_percent"] > 90 else 0,
    }
    return issues


@router.get("/health")
async def get_health_status(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """System health check with real metrics."""
    start = time.monotonic()

    sys_metrics = _system_metrics()
    pool = _pool_metrics()
    issues = _detect_issues(sys_metrics, pool)

    total_issues = sum(issues.values())
    if total_issues == 0:
        health_status = "healthy"
    elif total_issues <= 2:
        health_status = "degraded"
    else:
        health_status = "unhealthy"

    alerts = []
    if issues["high_memory"]:
        alerts.append(
            {
                "level": "warning",
                "message": f"Memory usage high: {sys_metrics['memory_usage_mb']}MB",
            }
        )
    if issues["high_cpu"]:
        alerts.append(
            {
                "level": "warning",
                "message": f"CPU usage high: {sys_metrics['cpu_usage_percent']}%",
            }
        )
    if issues["pool_exhaustion_risk"]:
        alerts.append(
            {
                "level": "critical",
                "message": f"DB pool near capacity: {pool['checked_out']}/{pool['pool_size']}",
            }
        )
    if issues["high_disk_usage"]:
        alerts.append(
            {
                "level": "warning",
                "message": f"Disk usage high: {sys_metrics['disk_usage_percent']}%",
            }
        )

    duration = time.monotonic() - start
    _record_request_time(duration)

    return {
        "status": health_status,
        "alerts": alerts,
        "metrics": {
            "pool_metrics": pool,
            "system_metrics": sys_metrics,
            "response_times": _response_times(),
            "issues_detected": issues,
        },
        "checked_at": datetime.utcnow().isoformat(),
    }


@router.get("/performance")
async def get_performance_snapshot(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Full performance snapshot with system and pool metrics."""
    start = time.monotonic()

    sys_metrics = _system_metrics()
    pool = _pool_metrics()
    issues = _detect_issues(sys_metrics, pool)

    total_issues = sum(issues.values())
    health = (
        "healthy"
        if total_issues == 0
        else ("degraded" if total_issues <= 2 else "unhealthy")
    )

    duration = time.monotonic() - start
    _record_request_time(duration)

    return {
        "status": health,
        "pool_metrics": pool,
        "system_metrics": sys_metrics,
        "response_times": _response_times(),
        "issues_detected": issues,
        "uptime_seconds": round(time.monotonic(), 1),
        "checked_at": datetime.utcnow().isoformat(),
    }
