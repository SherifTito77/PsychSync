"""
Retry Monitoring and Management API Endpoints

Provides endpoints for:
- Viewing retry metrics (Prometheus format)
- Inspecting Dead Letter Queue
- Replaying failed operations
- Component-specific retry configuration

Author: Infrastructure Team
Version: 1.0
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.core.monitoring.retry_metrics import retry_tracker
from app.core.monitoring.retry_prometheus import generate_retry_metrics
from app.core.retry_config import RetryConfigManager
from app.core.retry_wrapper import get_dlq

router = APIRouter(prefix="/api/v1/admin/retry", tags=["retry-monitoring"])
logger = logging.getLogger(__name__)


@router.get("/metrics")
async def get_retry_metrics_prometheus():
    """
    Get retry metrics in Prometheus format for scraping.

    Returns:
        Prometheus-formatted metrics text
    """
    try:
        metrics = await generate_retry_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to generate retry metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_retry_summary(
    hours: int = Query(1, ge=1, le=24, description="Hours to look back")
):
    """
    Get retry metrics summary across all components.

    Args:
        hours: Number of hours to look back (1-24)

    Returns:
        Summary dictionary with key metrics
    """
    try:
        return retry_tracker.get_summary(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get retry summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{component}")
async def get_component_metrics(
    component: str, hours: int = Query(1, ge=1, le=24, description="Hours to look back")
):
    """
    Get retry metrics for a specific component.

    Args:
        component: Component name (database, webhook, email_smtp, etc.)
        hours: Number of hours to look back

    Returns:
        RetryMetrics for the component
    """
    try:
        metrics = retry_tracker.get_metrics(component, hours)
        return {
            "component": component,
            "period_hours": hours,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"Failed to get component metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dlq")
async def get_dlq_entries(
    component: str = Query(None, description="Filter by component"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
):
    """
    Get Dead Letter Queue entries.

    Args:
        component: Optional component filter
        limit: Maximum entries to return

    Returns:
        List of DLQ entries
    """
    try:
        dlq = get_dlq()
        entries = await dlq.get_all(component)

        # Apply limit
        entries = entries[-limit:]

        return {
            "total_count": len(entries),
            "returned": len(entries),
            "component_filter": component,
            "entries": entries,
        }
    except Exception as e:
        logger.error(f"Failed to get DLQ entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dlq/stats")
async def get_dlq_stats():
    """
    Get Dead Letter Queue statistics.

    Returns:
        DLQ statistics dictionary
    """
    try:
        dlq = get_dlq()
        stats = await dlq.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get DLQ stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dlq/clear")
async def clear_dlq(
    component: str = Query(None, description="Clear only entries for this component")
):
    """
    Clear Dead Letter Queue entries.

    ⚠️ DANGER: This permanently removes DLQ entries!

    Args:
        component: Optional component filter (clears all if None)

    Returns:
        Confirmation of cleared entries
    """
    try:
        dlq = get_dlq()

        if component:
            # Filter and rebuild queue without entries for this component
            async with dlq._lock:
                original_count = len(dlq._queue)
                dlq._queue = [e for e in dlq._queue if e["component"] != component]
                cleared_count = original_count - len(dlq._queue)

            logger.info(
                f"Cleared {cleared_count} DLQ entries for component: {component}"
            )
        else:
            # Clear all
            async with dlq._lock:
                cleared_count = len(dlq._queue)
                dlq._queue.clear()

            logger.warning(f"Cleared ALL {cleared_count} DLQ entries")

        return {
            "success": True,
            "cleared_count": cleared_count,
            "component_filter": component,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to clear DLQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_retry_configurations():
    """
    Get all retry configurations.

    Returns:
        Dictionary of component configurations
    """
    try:
        return RetryConfigManager.get_all_configs()
    except Exception as e:
        logger.error(f"Failed to get retry configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{component}")
async def get_component_configuration(component: str):
    """
    Get retry configuration for a specific component.

    Args:
        component: Component name

    Returns:
        RetryConfig for the component
    """
    try:
        config = RetryConfigManager.get_config(component)
        return {
            "component": component,
            "config": config,
        }
    except Exception as e:
        logger.error(f"Failed to get component configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_retry_alerts():
    """
    Check for abnormal retry patterns and return alerts.

    Returns:
        List of alert messages
    """
    try:
        alerts = await retry_tracker.check_and_alert()
        return {
            "alert_count": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to check retry alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_retry_health():
    """
    Get overall retry system health status.

    Returns:
        Health status with metrics and alerts
    """
    try:
        summary = retry_tracker.get_summary(hours=1)
        alerts = await retry_tracker.check_and_alert()
        dlq_stats = await (await get_dlq()).get_stats()

        # Determine overall health
        is_healthy = (
            summary["overall_retry_rate"] < 30.0
            and summary["overall_failure_rate"] < 10.0
            and len(alerts) == 0
        )

        return {
            "healthy": is_healthy,
            "summary": summary,
            "alert_count": len(alerts),
            "dlq_size": dlq_stats["total_entries"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get retry health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/high-retry-rate")
async def get_high_retry_components(
    threshold: float = Query(
        20.0, ge=0.0, le=100.0, description="Retry rate threshold"
    ),
    hours: int = Query(1, ge=1, le=24, description="Hours to look back"),
):
    """
    Get components with retry rates above threshold.

    Args:
        threshold: Retry rate percentage threshold
        hours: Number of hours to look back

    Returns:
        List of components exceeding threshold
    """
    try:
        high_retry = retry_tracker.get_high_retry_integrations(threshold, hours)

        return {
            "threshold": f"{threshold}%",
            "period_hours": hours,
            "count": len(high_retry),
            "components": [
                {
                    "integration": m.integration,
                    "retry_rate": f"{m.retry_rate:.2f}%",
                    "failure_rate": f"{m.failure_rate:.2f}%",
                    "total_attempts": m.total_attempts,
                }
                for m in high_retry
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get high retry components: {e}")
        raise HTTPException(status_code=500, detail=str(e))
