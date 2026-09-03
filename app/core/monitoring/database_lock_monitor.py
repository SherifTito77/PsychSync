"""
Database Lock Contention Monitor

Tracks and alerts on database lock performance issues caused by row-level locking
(SELECT FOR UPDATE) and other locking operations.

This helps identify performance bottlenecks before they become production issues.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Configuration thresholds (in seconds)
LOCK_WARNING_THRESHOLD = 1.0  # Alert if lock held > 1 second
LOCK_CRITICAL_THRESHOLD = 5.0  # Alert critical if lock held > 5 seconds
LOCK_TIMEOUT_THRESHOLD = 10.0  # Lock timeout threshold


class LockMetrics:
    """Track lock operation metrics."""

    def __init__(self):
        self.total_locks = 0
        self.total_lock_time = 0.0
        self.slow_locks = 0  # Locks > WARNING_THRESHOLD
        self.critical_locks = 0  # Locks > CRITICAL_THRESHOLD
        self.timeouts = 0
        self.locks_by_operation = {}  # operation_name -> count

    def record_lock(self, operation: str, duration: float):
        """Record a lock operation."""
        self.total_locks += 1
        self.total_lock_time += duration

        if duration > LOCK_CRITICAL_THRESHOLD:
            self.critical_locks += 1
            logger.critical(
                f"CRITICAL: Database lock held for {duration:.2f}s in {operation}",
                extra={
                    "operation": operation,
                    "duration": duration,
                    "threshold": LOCK_CRITICAL_THRESHOLD,
                },
            )
        elif duration > LOCK_WARNING_THRESHOLD:
            self.slow_locks += 1
            logger.warning(
                f"WARNING: Database lock held for {duration:.2f}s in {operation}",
                extra={
                    "operation": operation,
                    "duration": duration,
                    "threshold": LOCK_WARNING_THRESHOLD,
                },
            )

        # Track by operation
        self.locks_by_operation[operation] = (
            self.locks_by_operation.get(operation, 0) + 1
        )

    def record_timeout(self, operation: str):
        """Record a lock timeout."""
        self.timeouts += 1
        logger.error(
            f"Database lock timeout in {operation}",
            extra={"operation": operation},
        )

    def get_stats(self) -> dict:
        """Get current statistics."""
        avg_lock_time = (
            self.total_lock_time / self.total_locks if self.total_locks > 0 else 0
        )

        return {
            "total_locks": self.total_locks,
            "average_lock_time_seconds": round(avg_lock_time, 3),
            "slow_locks": self.slow_locks,
            "critical_locks": self.critical_locks,
            "timeouts": self.timeouts,
            "locks_by_operation": self.locks_by_operation,
            "slow_lock_percentage": round(
                (
                    (self.slow_locks / self.total_locks * 100)
                    if self.total_locks > 0
                    else 0
                ),
                2,
            ),
        }


# Global metrics instance
_lock_metrics = LockMetrics()


def get_lock_metrics() -> LockMetrics:
    """Get the global lock metrics instance."""
    return _lock_metrics


@asynccontextmanager
async def monitor_lock(operation: str):
    """
    Context manager to monitor database lock operations.

    Usage:
        async with monitor_lock("user_update"):
            result = await db.execute(
                select(User).where(User.id == user_id).with_for_update()
            )

    This will track how long the lock is held and alert if it exceeds thresholds.
    """
    start_time = time.time()
    lock_acquired = False
    error_occurred = False

    try:
        yield
        lock_acquired = True
    finally:
        duration = time.time() - start_time

        if lock_acquired and not error_occurred:
            _lock_metrics.record_lock(operation, duration)
        elif duration > LOCK_TIMEOUT_THRESHOLD:
            _lock_metrics.record_timeout(operation)


def monitor_locks_async(operation: str):
    """
    Decorator to monitor async functions that use database locks.

    Usage:
        @monitor_locks_async("update_user_credits")
        async def update_user_credits(db: AsyncSession, user_id: UUID):
            result = await db.execute(
                select(User).where(User.id == user_id).with_for_update()
            )
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                _lock_metrics.record_lock(operation, duration)

                return result

            except Exception:
                duration = time.time() - start_time
                if duration > LOCK_TIMEOUT_THRESHOLD:
                    _lock_metrics.record_timeout(operation)
                raise

        return wrapper

    return decorator


async def check_lock_health() -> dict:
    """
    Check database lock health status.

    Returns health status with recommendations.
    """
    stats = _lock_metrics.get_stats()

    # Determine health status
    if stats["critical_locks"] > 0:
        status = "CRITICAL"
        message = "Database locks are experiencing critical delays. Immediate investigation required."
    elif stats["slow_lock_percentage"] > 10:
        status = "WARNING"
        message = f"{stats['slow_lock_percentage']}% of locks are slow. Consider optimizing queries."
    elif stats["timeouts"] > 0:
        status = "WARNING"
        message = "Database lock timeouts detected. Review transaction design."
    else:
        status = "HEALTHY"
        message = "Database lock performance is within acceptable thresholds."

    return {
        "status": status,
        "message": message,
        "metrics": stats,
        "thresholds": {
            "warning_seconds": LOCK_WARNING_THRESHOLD,
            "critical_seconds": LOCK_CRITICAL_THRESHOLD,
            "timeout_seconds": LOCK_TIMEOUT_THRESHOLD,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def reset_metrics():
    """Reset lock metrics (useful for testing or periodic monitoring)."""
    global _lock_metrics
    _lock_metrics = LockMetrics()
    logger.info("Database lock metrics reset")


# Export Prometheus-compatible metrics (if prometheus_client is available)
try:
    from prometheus_client import Counter, Histogram

    lock_duration = Histogram(
        "database_lock_duration_seconds",
        "Database lock duration in seconds",
        ["operation"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    )

    lock_timeouts = Counter(
        "database_lock_timeouts_total",
        "Total database lock timeouts",
        ["operation"],
    )

    slow_locks = Counter(
        "database_slow_locks_total",
        "Total slow database locks (>1 second)",
        ["operation"],
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:
    # Prometheus not available, use logger only
    PROMETHEUS_AVAILABLE = False

    logger.debug(
        "Prometheus client not available. Database lock metrics will be logged only."
    )


# Global instance
lock_metrics = LockMetrics()


def export_prometheus_metrics() -> Optional[str]:
    """
    Export metrics in Prometheus format.

    Returns None if Prometheus is not available.
    """
    if not PROMETHEUS_AVAILABLE:
        return None

    try:
        from prometheus_client import generate_latest

        return generate_latest()
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        return None
