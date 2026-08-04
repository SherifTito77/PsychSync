"""
Heuristic Monitoring API Endpoints
Provides access to Heuristic engine performance metrics, health status, and alerts
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.user import User
from app.services.heuristic_monitoring_service import (
    HeuristicMonitoringService,
    MetricType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/heuristic-monitoring", tags=["heuristic-monitoring"])

# Global monitoring service instance
_heuristic_monitoring_service: HeuristicMonitoringService | None = None


def get_heuristic_monitoring_service(db: AsyncSession) -> HeuristicMonitoringService:
    """Get or create Heuristic monitoring service instance"""
    global _heuristic_monitoring_service
    if _heuristic_monitoring_service is None:
        _heuristic_monitoring_service = HeuristicMonitoringService(db)
    return _heuristic_monitoring_service


@router.get("/health")
async def get_heuristic_health_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive Heuristic engine health status

    Returns overall health score, active alerts, performance metrics, and recommendations
    """
    try:
        # Validate permissions (admin or team lead)
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Heuristic monitoring requires admin or team lead privileges",
            )

        monitoring_service = get_heuristic_monitoring_service(db)
        health_status = await monitoring_service.get_heuristic_health_status()

        return {
            "success": True,
            "data": {
                "overall_status": health_status.overall_status,
                "health_score": health_status.health_score,
                "active_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "description": alert.description,
                        "metric_type": alert.metric_type.value,
                        "current_value": alert.current_value,
                        "threshold_value": alert.threshold_value,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolution_actions": alert.resolution_actions,
                    }
                    for alert in health_status.active_alerts
                ],
                "performance_metrics": health_status.performance_metrics,
                "last_check": health_status.last_check.isoformat(),
                "uptime_percentage": health_status.uptime_percentage,
                "recommendations": health_status.recommendations,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Heuristic health status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Heuristic health status: {e!s}"
        ) from e


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/ai-monitoring-metrics")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours (1-168)"),
    metric_types: str | None = Query(
        None, description="Comma-separated metric types to filter"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Heuristic engine performance metrics and trends

    - **hours**: Time period for metrics (1-168 hours)
    - **metric_types**: Filter by specific metric types (comma-separated)
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Performance metrics require admin or team lead privileges",
            )

        monitoring_service = get_heuristic_monitoring_service(db)

        # Parse metric types filter
        metric_type_filter = None
        if metric_types:
            try:
                type_names = [name.strip() for name in metric_types.split(",")]
                metric_type_filter = [
                    MetricType(name)
                    for name in type_names
                    if name in [t.value for t in MetricType]
                ]
            except ValueError as err:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {err!s}"
                ) from err

        trends = await monitoring_service.get_performance_trends(
            hours=hours, metric_types=metric_type_filter
        )

        return {"success": True, "data": trends}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance metrics: {e!s}"
        ) from e


@router.get("/alerts")
async def get_heuristic_alerts(
    severity: str | None = Query(None, description="Filter by alert severity"),
    active_only: bool = Query(True, description="Show only active alerts"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Heuristic system alerts

    - **severity**: Filter by severity level (info, warning, error, critical)
    - **active_only**: Show only currently active alerts
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Alert viewing requires admin or team lead privileges",
            )

        monitoring_service = get_heuristic_monitoring_service(db)
        health_status = await monitoring_service.get_heuristic_health_status()

        alerts = health_status.active_alerts

        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.severity.value == severity]

        return {
            "success": True,
            "data": {
                "total_alerts": len(alerts),
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "description": alert.description,
                        "metric_type": alert.metric_type.value,
                        "current_value": alert.current_value,
                        "threshold_value": alert.threshold_value,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolution_actions": alert.resolution_actions,
                    }
                    for alert in alerts
                ],
                "filter_applied": {"severity": severity, "active_only": active_only},
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Heuristic alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Heuristic alerts: {e!s}"
        ) from e


@router.post("/start-monitoring")
async def start_heuristic_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start Heuristic engine monitoring (admin only)

    Begins continuous monitoring of Heuristic performance and health metrics
    """
    try:
        # Validate admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Starting Heuristic monitoring requires admin privileges",
            )

        monitoring_service = get_heuristic_monitoring_service(db)
        await monitoring_service.start_monitoring()

        return {
            "success": True,
            "message": "Heuristic engine monitoring started successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Heuristic monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start Heuristic monitoring: {e!s}"
        ) from e


@router.post("/stop-monitoring")
async def stop_heuristic_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stop Heuristic engine monitoring (admin only)

    Stops continuous monitoring of Heuristic performance and health metrics
    """
    try:
        # Validate admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Stopping Heuristic monitoring requires admin privileges",
            )

        monitoring_service = get_heuristic_monitoring_service(db)
        await monitoring_service.stop_monitoring()

        return {
            "success": True,
            "message": "Heuristic engine monitoring stopped successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping Heuristic monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop Heuristic monitoring: {e!s}"
        ) from e


@router.get("/dashboard")
async def get_heuristic_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive Heuristic monitoring dashboard data

    Returns a complete overview of Heuristic engine status, metrics, alerts, and trends
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Heuristic monitoring dashboard requires admin or team lead privileges",
            )

        monitoring_service = get_heuristic_monitoring_service(db)
        health_status = await monitoring_service.get_heuristic_health_status()
        performance_trends = await monitoring_service.get_performance_trends(hours=24)

        # Calculate alert statistics
        alert_stats = {
            "critical": len(
                [
                    a
                    for a in health_status.active_alerts
                    if a.severity.value == "critical"
                ]
            ),
            "error": len(
                [a for a in health_status.active_alerts if a.severity.value == "error"]
            ),
            "warning": len(
                [
                    a
                    for a in health_status.active_alerts
                    if a.severity.value == "warning"
                ]
            ),
            "info": len(
                [a for a in health_status.active_alerts if a.severity.value == "info"]
            ),
        }

        # Get metric summaries
        metric_summaries = {}
        for metric_name, trend_data in performance_trends.get("trends", {}).items():
            metric_summaries[metric_name] = {
                "current": trend_data.get("current", 0),
                "average": trend_data.get("average", 0),
                "trend": trend_data.get("trend", "stable"),
                "status": (
                    "good"
                    if trend_data.get("current", 0) > trend_data.get("average", 0)
                    else "warning"
                ),
            }

        return {
            "success": True,
            "data": {
                "dashboard_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "monitoring_active": monitoring_service.monitoring_active,
                    "total_metrics_collected": len(monitoring_service.metrics_history),
                },
                "health_summary": {
                    "overall_status": health_status.overall_status,
                    "health_score": health_status.health_score,
                    "uptime_percentage": health_status.uptime_percentage,
                    "status_color": (
                        "green"
                        if health_status.overall_status == "healthy"
                        else (
                            "orange"
                            if health_status.overall_status == "degraded"
                            else "red"
                        )
                    ),
                },
                "alert_summary": alert_stats,
                "active_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "description": alert.description,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in health_status.active_alerts[:5]  # Top 5 recent alerts
                ],
                "performance_summary": {
                    "total_metrics": len(performance_trends.get("trends", {})),
                    "metrics": metric_summaries,
                },
                "recommendations": health_status.recommendations,
                "last_updated": health_status.last_check.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Heuristic monitoring dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Heuristic monitoring dashboard: {e!s}",
        ) from e


@router.get("/metric-types")
async def get_available_metric_types(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of available Heuristic metric types for filtering and analysis
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Metric type listing requires admin or team lead privileges",
            )

        metric_types = [
            {
                "value": metric_type.value,
                "label": metric_type.value.replace("_", " ").title(),
                "description": _get_metric_description(metric_type),
            }
            for metric_type in MetricType
        ]

        return {
            "success": True,
            "data": {"metric_types": metric_types, "total_count": len(metric_types)},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric types: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric types: {e!s}"
        ) from e


def _get_metric_description(metric_type: MetricType) -> str:
    """Get description for a metric type"""
    descriptions = {
        MetricType.PROCESSING_TIME: "Time taken to process Heuristic requests in milliseconds",
        MetricType.ACCURACY_SCORE: "Accuracy of Heuristic predictions and classifications",
        MetricType.CONFIDENCE_SCORE: "Confidence level of Heuristic-generated insights",
        MetricType.ENGAGEMENT_PREDICTION_ACCURACY: "Accuracy of user engagement predictions",
        MetricType.PERSONALIZATION_EFFECTIVENESS: "Effectiveness of Heuristic personalization features",
        MetricType.ERROR_RATE: "Rate of errors in Heuristic processing",
        MetricType.THROUGHPUT: "Number of Heuristic requests processed per minute",
        MetricType.MEMORY_USAGE: "Memory usage percentage of Heuristic engine",
        MetricType.CACHE_HIT_RATE: "Percentage of Heuristic requests served from cache",
    }
    return descriptions.get(metric_type, "Heuristic performance metric")
