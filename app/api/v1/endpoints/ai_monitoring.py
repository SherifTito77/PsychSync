"""
AI Monitoring API Endpoints
Provides access to AI engine performance metrics, health status, and alerts
"""

from fastapi import APIRouter, HTTPException, Depends, Query

from app.middleware.rate_limiter import check_rate_limit
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.api.v1.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.services.ai_monitoring_service import AIMonitoringService, MetricType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-monitoring", tags=["ai-monitoring"])

# Global monitoring service instance
_ai_monitoring_service: Optional[AIMonitoringService] = None

def get_ai_monitoring_service(db: AsyncSession) -> AIMonitoringService:
    """Get or create AI monitoring service instance"""
    global _ai_monitoring_service
    if _ai_monitoring_service is None:
        _ai_monitoring_service = AIMonitoringService(db)
    return _ai_monitoring_service

@router.get("/health")
async def get_ai_health_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive AI engine health status

    Returns overall health score, active alerts, performance metrics, and recommendations
    """
    try:
        # Validate permissions (admin or team lead)
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="AI monitoring requires admin or team lead privileges"
            )

        monitoring_service = get_ai_monitoring_service(db)
        health_status = await monitoring_service.get_ai_health_status()

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
                        "resolution_actions": alert.resolution_actions
                    }
                    for alert in health_status.active_alerts
                ],
                "performance_metrics": health_status.performance_metrics,
                "last_check": health_status.last_check.isoformat(),
                "uptime_percentage": health_status.uptime_percentage,
                "recommendations": health_status.recommendations
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI health status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI health status: {str(e)}"
        )


@check_rate_limit(identifier="public", endpoint_type="public")
@router.get("/metrics")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours (1-168)"),
    metric_types: Optional[str] = Query(None, description="Comma-separated metric types to filter"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI engine performance metrics and trends

    - **hours**: Time period for metrics (1-168 hours)
    - **metric_types**: Filter by specific metric types (comma-separated)
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Performance metrics require admin or team lead privileges"
            )

        monitoring_service = get_ai_monitoring_service(db)

        # Parse metric types filter
        metric_type_filter = None
        if metric_types:
            try:
                type_names = [name.strip() for name in metric_types.split(',')]
                metric_type_filter = [MetricType(name) for name in type_names if name in [t.value for t in MetricType]]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric type: {str(e)}"
                )

        trends = await monitoring_service.get_performance_trends(
            hours=hours,
            metric_types=metric_type_filter
        )

        return {
            "success": True,
            "data": trends
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            d
@check_rate_limit(identifier="public", endpoint_type="public")
etail=f"Failed to get performance metrics: {str(e)}"
        )

@router.get("/alerts")
async def get_ai_alerts(
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    active_only: bool = Query(True, description="Show only active alerts"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI system alerts

    - **severity**: Filter by severity level (info, warning, error, critical)
    - **active_only**: Show only currently active alerts
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Alert viewing requires admin or team lead privileges"
            )

        monitoring_service = get_ai_monitoring_service(db)
        health_status = await monitoring_service.get_ai_health_status()

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
                        "resolution_actions": alert.resolution_actions
                    }
                    for alert in alerts
                ],
                "filter_applied": {
                    "severity": severity,
                    "active_only": active_only
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI alerts: {str(e)}"
        )

@router.post("/start-monitoring")
async def start_ai_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start AI engine monitoring (admin only)

    Begins continuous monitoring of AI performance and health metrics
    """
    try:
        # Validate admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Starting AI monitoring requires admin privileges"
            )

        monitoring_service = get_ai_monitoring_service(db)
        await monitoring_service.start_monitoring()

        return {
            "success": True,
            "message": "AI engine monitoring started successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting AI monitoring: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start AI monitoring: {str(e)}"
        )

@router.post("/stop-monitoring")
async def stop_ai_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stop AI engine monitoring (admin only)

    Stops continuous monitoring of AI performance and health metrics
    """
    try:
        # Validate admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Stopping AI monitoring requires admin privileges"
            )

        monitoring_service = get_ai_monitoring_service(db)
        await monitoring_service.stop_monitoring()

        return {
            "success": True,
            "message": "AI engine monitoring stopped successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping AI monitoring: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop AI monitoring: {str(e)}"
        )

@router.get("/dashboard")
async def get_ai_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive AI monitoring dashboard data

    Returns a complete overview of AI engine status, metrics, alerts, and trends
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="AI monitoring dashboard requires admin or team lead privileges"
            )

        monitoring_service = get_ai_monitoring_service(db)
        health_status = await monitoring_service.get_ai_health_status()
        performance_trends = await monitoring_service.get_performance_trends(hours=24)

        # Calculate alert statistics
        alert_stats = {
            "critical": len([a for a in health_status.active_alerts if a.severity.value == "critical"]),
            "error": len([a for a in health_status.active_alerts if a.severity.value == "error"]),
            "warning": len([a for a in health_status.active_alerts if a.severity.value == "warning"]),
            "info": len([a for a in health_status.active_alerts if a.severity.value == "info"])
        }

        # Get metric summaries
        metric_summaries = {}
        for metric_name, trend_data in performance_trends.get("trends", {}).items():
            metric_summaries[metric_name] = {
                "current": trend_data.get("current", 0),
                "average": trend_data.get("average", 0),
                "trend": trend_data.get("trend", "stable"),
                "status": "good" if trend_data.get("current", 0) > trend_data.get("average", 0) else "warning"
            }

        return {
            "success": True,
            "data": {
                "dashboard_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "monitoring_active": monitoring_service.monitoring_active,
                    "total_metrics_collected": len(monitoring_service.metrics_history)
                },
                "health_summary": {
                    "overall_status": health_status.overall_status,
                    "health_score": health_status.health_score,
                    "uptime_percentage": health_status.uptime_percentage,
                    "status_color": "green" if health_status.overall_status == "healthy" else "orange" if health_status.overall_status == "degraded" else "red"
                },
                "alert_summary": alert_stats,
                "active_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "description": alert.description,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in health_status.active_alerts[:5]  # Top 5 recent alerts
                ],
                "performance_summary": {
                    "total_metrics": len(performance_trends.get("trends", {})),
                    "metrics": metric_summaries
                },
                "recommendations": health_status.recommendations,
                "last_updated": health_status.last_check.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI monitoring dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI monitoring dashboard: {str(e)}"
        )

@router.get("/metric-types")
async def get_available_metric_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available AI metric types for filtering and analysis
    """
    try:
        # Validate permissions
        if not (current_user.is_admin or current_user.is_team_lead):
            raise HTTPException(
                status_code=403,
                detail="Metric type listing requires admin or team lead privileges"
            )

        metric_types = [
            {
                "value": metric_type.value,
                "label": metric_type.value.replace('_', ' ').title(),
                "description": _get_metric_description(metric_type)
            }
            for metric_type in MetricType
        ]

        return {
            "success": True,
            "data": {
                "metric_types": metric_types,
                "total_count": len(metric_types)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric types: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metric types: {str(e)}"
        )

def _get_metric_description(metric_type: MetricType) -> str:
    """Get description for a metric type"""
    descriptions = {
        MetricType.PROCESSING_TIME: "Time taken to process AI requests in milliseconds",
        MetricType.ACCURACY_SCORE: "Accuracy of AI predictions and classifications",
        MetricType.CONFIDENCE_SCORE: "Confidence level of AI-generated insights",
        MetricType.ENGAGEMENT_PREDICTION_ACCURACY: "Accuracy of user engagement predictions",
        MetricType.PERSONALIZATION_EFFECTIVENESS: "Effectiveness of AI personalization features",
        MetricType.ERROR_RATE: "Rate of errors in AI processing",
        MetricType.THROUGHPUT: "Number of AI requests processed per minute",
        MetricType.MEMORY_USAGE: "Memory usage percentage of AI engine",
        MetricType.CACHE_HIT_RATE: "Percentage of AI requests served from cache"
    }
    return descriptions.get(metric_type, "AI performance metric")