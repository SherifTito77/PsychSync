from functools import wraps

from fastapi import APIRouter

router = APIRouter(prefix="/tracing", tags=["tracing"])


def trace_operation(name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


from fastapi import APIRouter

router = APIRouter(prefix="/tracing", tags=["tracing"])
"""
DISTRIBUTED TRACING FOR LOCK VISUALIZATION
==========================================

Track lock acquisition across services for real-time deadlock cycle visualization.

Features:
- Service-level lock tracking (who acquired what, when?)
- Cross-service transaction correlation (user:123 → assessment:456 → response:789)
- Deadlock cycle detection (A holds user:123, B holds assessment:456, C waits for user:123 → circular wait)
- Real-time event streaming (WebSocket updates to dashboard)
- Lock acquisition sequence logging with timestamps
- Circular wait graph visualization (who's waiting for whom?)

Author: Security Team
Created: February 14, 2026
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)


# Global state for distributed tracing
lock_transactions: Dict[str, List[Dict]] = defaultdict(list)
circular_waits: Dict[str, List[str]] = defaultdict(list)
service_locks: Dict[str, Dict[str, str]] = defaultdict(dict)
active_locks: Dict[str, Dict[str, datetime]] = defaultdict(dict)


class DistributedTracer:
    """
    Distributed tracing system for deadlock visualization.

    Tracks:
    - Lock acquisition across services
    - Cross-service transaction correlation
    - Deadlock cycle detection
    - Real-time event streaming

    Provides:
    - Lock acquisition history
    - Circular wait detection
    - Deadlock cycle visualization data
    """

    def __init__(self):
        # Statistics
        self.total_acquisitions = 0
        self.circular_waits_detected = 0
        self.deadlock_cycles_detected = 0

    logger.info("Distributed Tracing initialized")

    async def acquire_lock(
        self,
        service: str,
        resource_id: str,
        operation: str,
    ) -> None:
        """
        Record lock acquisition for tracing.

        Args:
            service: Service name (e.g., "user", "assessment", "response")
            resource_id: Resource identifier
            operation: Operation being performed

        Returns:
            Lock acquisition ID for tracking
        """
        timestamp = datetime.utcnow().isoformat()
        transaction_id = f"{service}:{resource_id}:{operation}"

        # Record lock acquisition
        lock_transactions[transaction_id].append(
            {
                "service": service,
                "resource_id": resource_id,
                "operation": operation,
                "timestamp": timestamp,
            }
        )

        # Update service locks
        if service not in service_locks[service]:
            service_locks[service] = {}
        service_locks[service][resource_id] = {
            "acquired_at": timestamp,
            "operation": operation,
        }
        self.service_locks[service] = service_locks[service]

        # Detect circular wait
        if self._detect_circular_wait(service, resource_id, operation):
            self.circular_waits_detected += 1

        self.total_acquisitions += 1

        logger.debug(f"Lock acquired: {service} - {resource_id} - {operation}")

        return transaction_id

    def _detect_circular_wait(
        self, service: str, resource_id: str, operation: str
    ) -> bool:
        """
        Detect circular wait conditions in lock acquisitions.

        Args:
            service: Service acquiring the lock
            resource_id: Resource being locked
            operation: Operation being performed

        Returns:
            True if circular wait detected
        """
        # Check if resource is held by another service
        for other_service, locks in service_locks.items():
            for locked_resource, lock_info in locks.items():
                if locked_resource == resource_id and other_service != service:
                    # Resource already held by another service - circular wait!
                    logger.warning(
                        f"⚠️  CIRCULAR WAIT DETECTED: {other_service} holds {resource_id} "
                        f"while {service} tries to acquire it for {operation}"
                    )
                    return True

        return False

    async def get_lock_history(
        self,
        service: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get lock acquisition history for tracing.

        Args:
            service: Filter by service name
            resource_id: Filter by resource ID
            limit: Maximum records to return

        Returns:
            List of lock acquisitions
        """
        history = []

        # Filter by service
        if service:
            service_transactions = lock_transactions.items()
        else:
            service_transactions = []
            for svc_txs in service_transactions.items():
                history.extend(svc_txs)

        # Filter by resource
        if resource_id:
            if service:
                service_history = [
                    tx
                    for tx in service_transactions.values()
                    if tx.get("resource_id") == resource_id
                ]
            else:
                service_history = []

        # Apply limit
        history = history[:limit]

        return {
            "service": service,
            "resource_id": resource_id,
            "limit": limit,
            "count": len(history),
            "history": history,
        }


@router.get(
    "/tracing/lock/{service}/{resource_id}", summary="Get lock history for resource"
)
async def get_lock_history_endpoint(
    service: str,
    resource_id: str,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Get lock acquisition history for a specific service and resource.

    Args:
        service: Service name
        resource_id: Resource identifier
        limit: Maximum records to return

    Returns:
        Lock acquisition history
    """
    history = []

    # Get service locks
    service_locks = service_locks.get(service, {})

    if service:
        transactions = list(service_locks.values())
    else:
        transactions = []

    for tx in transactions[:limit]:
        history.append(tx)

    return {
        "service": service,
        "resource_id": resource_id,
        "limit": limit,
        "count": len(history),
        "history": history,
    }


@router.get("/tracing/cycles/detect", summary="Detect deadlock cycles")
async def detect_deadlock_cycles(
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Analyze lock acquisitions to detect deadlock cycles.

    Args:
        limit: Number of recent transactions to analyze

    Returns:
        Detected deadlock cycles with statistics
    """
    cycles = []
    cycle_count = 0

    # Get all recent acquisitions
    all_transactions = []
    for service_txs in service_locks.values():
        all_transactions.extend(list(service_txs.values()))

        # Analyze for cycles
        for i in range(min(limit, len(all_transactions)), 2):
            tx = all_transactions[i]

            # Skip if only one transaction
            if len(tx) < 2:
                continue

            service = tx[0].get("service")
            resource = tx[0].get("resource_id")
            operation = tx[0].get("operation")

            # Check for circular wait (A holds B, B holds, C waits)
            holds_B = False
            holds_C = False
            waits_for_A = []

            for j in range(1, len(tx)):
                if j == len(tx):
                    break  # Current transaction is last

                tx_j = tx[j]
                service_j = tx_j[0].get("service")
                resource_j = tx_j[0].get("resource_id")
                operation_j = tx_j[0].get("operation")

                # Check if B holds while C waits
                if service_j == resource_j and operation_j == "acquire":
                    holds_B = True
                    break  # B is holding

                # Check if C waits for A
                if operation_j == "wait" and holds_C:
                    wait_info = {
                        "holder": service_j,
                        "waiting_for": operation_j,
                        "resource_id": resource_j,
                    }
                    waits_for_A.append(wait_info)

                # Deadlock cycle detected
                if holds_B and holds_C and len(waits_for_A) > 1:
                    cycle_count = len(waits_for_A)

                    if cycle_count > 0:
                        self.deadlock_cycles_detected += 1
                        self.circular_waits_detected += 1

                        # Record cycle
                        cycles.append(
                            {
                                "cycle": cycle_count,
                                "holder": service_j,
                                "victim": service_j,
                                "operations": waits_for_A,
                                "detected_at": datetime.utcnow().isoformat(),
                            }
                        )

                        logger.warning(
                            f"⚠️  DEADLOCK CYCLE DETECTED: #{cycle_count} - "
                            f"{service_j} holds {resource_j} while {service_c} waits for {operation_j}"
                        )

                        # Reset for next cycle
                        holds_B = False
                        holds_C = False
                        waits_for_A = []

                        # Statistics
                        stats = {
                            "cycles_detected": cycle_count,
                            "circular_waits": self.circular_waits_detected,
                        }

                        return stats

        return {
            "cycles_detected": self.deadlock_cycles_detected,
            "statistics": stats,
        }


@router.get("/tracing/stream", summary="Real-time deadlock event streaming")
async def stream_tracing_events():
    """
    Stream deadlock detection events to connected dashboard clients.

    Yields deadlock cycle detections as they occur.
    """
    logger.info("Streaming deadlock events...")

    try:
        while True:
            # Detect new deadlock cycles
            cycles = await detect_deadlock_cycles(limit=10)

            if cycles.get("cycles_detected", 0) > 0:
                # Get cycle details
                cycle = cycles["cycles"][0]

                # Stream to dashboard
                logger.info(f"🔴 DEADLOCK: {cycle['cycle']} detected")
                yield {
                    "type": "deadlock_cycle",
                    "data": cycle,
                }

                # Small delay to prevent overwhelming clients
                await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error streaming events: {e}")
        await asyncio.sleep(1)


# Global instance
tracer = DistributedTracer()
