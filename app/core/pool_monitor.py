# app/core/pool_monitor.py
"""
Database connection pool health monitoring with leak detection.
Exposes pool statistics and alerts on unhealthy thresholds.
"""

import logging
import time
from dataclasses import dataclass, field

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger("app.database.pool_monitor")

# Thresholds
POOL_UTILIZATION_WARNING = 0.75  # 75% usage triggers warning
POOL_UTILIZATION_CRITICAL = 0.90  # 90% usage triggers critical alert
LEAK_DETECTION_THRESHOLD_SECONDS = 300  # 5 min checkout = potential leak


@dataclass
class PoolHealthSnapshot:
    """Point-in-time snapshot of connection pool state."""

    timestamp: float
    pool_size: int
    checked_out: int
    checked_in: int
    overflow: int
    max_overflow: int
    utilization_pct: float
    status: str  # "healthy", "warning", "critical", "degraded"
    potential_leaks: int = 0
    total_connections: int = 0
    available_connections: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "pool_size": self.pool_size,
            "checked_out": self.checked_out,
            "checked_in": self.checked_in,
            "overflow": self.overflow,
            "max_overflow": self.max_overflow,
            "utilization_pct": round(self.utilization_pct, 2),
            "total_connections": self.total_connections,
            "available_connections": self.available_connections,
            "potential_leaks": self.potential_leaks,
            "status": self.status,
        }


@dataclass
class CheckoutRecord:
    """Tracks a single connection checkout for leak detection."""

    checkout_time: float
    stack_hint: str = ""


class PoolMonitor:
    """
    Monitors SQLAlchemy async engine pool health.

    Usage:
        monitor = PoolMonitor(async_engine)
        snapshot = monitor.get_health()
        leaks = monitor.detect_leaks()
    """

    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._checkouts: dict[int, CheckoutRecord] = {}
        self._total_checkouts: int = 0
        self._total_checkins: int = 0
        self._total_overflows: int = 0
        self._attach_events()

    def _attach_events(self) -> None:
        """Attach SQLAlchemy pool event listeners."""
        sync_engine = self._engine.sync_engine

        @event.listens_for(sync_engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            conn_id = id(dbapi_conn)
            self._checkouts[conn_id] = CheckoutRecord(checkout_time=time.monotonic())
            self._total_checkouts += 1

        @event.listens_for(sync_engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            conn_id = id(dbapi_conn)
            self._checkouts.pop(conn_id, None)
            self._total_checkins += 1

    def _get_pool(self) -> QueuePool | None:
        pool = self._engine.sync_engine.pool
        if isinstance(pool, QueuePool):
            return pool
        return None

    def get_health(self) -> PoolHealthSnapshot:
        """Capture current pool health snapshot."""
        pool = self._get_pool()
        if pool is None:
            return PoolHealthSnapshot(
                timestamp=time.time(),
                pool_size=0,
                checked_out=0,
                checked_in=0,
                overflow=0,
                max_overflow=0,
                utilization_pct=0.0,
                status="unknown",
            )

        pool_size = pool.size()
        checked_out = pool.checkedout()
        checked_in = pool.checkedin()
        overflow = pool.overflow()
        max_overflow = getattr(pool, "max_overflow", getattr(pool, "_max_overflow", 0))

        total_capacity = pool_size + max_overflow
        utilization = checked_out / total_capacity if total_capacity > 0 else 0.0

        potential_leaks = len(self.detect_leaks())

        if potential_leaks > 0:
            status = "degraded"
        elif utilization >= POOL_UTILIZATION_CRITICAL:
            status = "critical"
        elif utilization >= POOL_UTILIZATION_WARNING:
            status = "warning"
        else:
            status = "healthy"

        snapshot = PoolHealthSnapshot(
            timestamp=time.time(),
            pool_size=pool_size,
            checked_out=checked_out,
            checked_in=checked_in,
            overflow=overflow,
            max_overflow=max_overflow,
            utilization_pct=utilization * 100,
            status=status,
            potential_leaks=potential_leaks,
            total_connections=checked_out + checked_in,
            available_connections=total_capacity - checked_out,
        )

        if status in ("critical", "degraded"):
            logger.warning(
                "Pool health %s: %.1f%% utilization, %d potential leaks",
                status,
                snapshot.utilization_pct,
                potential_leaks,
            )

        return snapshot

    def detect_leaks(self) -> list[dict]:
        """Return connections held longer than the leak threshold."""
        now = time.monotonic()
        leaks = []
        for conn_id, record in self._checkouts.items():
            held_seconds = now - record.checkout_time
            if held_seconds > LEAK_DETECTION_THRESHOLD_SECONDS:
                leaks.append(
                    {
                        "connection_id": conn_id,
                        "held_seconds": round(held_seconds, 1),
                        "checkout_time": record.checkout_time,
                    }
                )
        return leaks

    def get_stats(self) -> dict:
        """Return cumulative pool statistics."""
        health = self.get_health()
        return {
            "health": health.to_dict(),
            "cumulative": {
                "total_checkouts": self._total_checkouts,
                "total_checkins": self._total_checkins,
                "currently_checked_out": len(self._checkouts),
            },
            "leaks": self.detect_leaks(),
        }


# Singleton instance (initialized after engine creation)
_monitor: PoolMonitor | None = None


def init_pool_monitor(engine: AsyncEngine) -> PoolMonitor:
    """Initialize the global pool monitor."""
    global _monitor
    _monitor = PoolMonitor(engine)
    logger.info("Pool monitor initialized")
    return _monitor


def get_pool_monitor() -> PoolMonitor | None:
    """Get the global pool monitor instance."""
    return _monitor
