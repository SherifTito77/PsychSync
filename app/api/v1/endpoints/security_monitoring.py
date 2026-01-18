"""
Security Monitoring API Endpoints
Provides access to security monitoring data, alerts, and analytics
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.deps import get_current_active_user, get_current_admin_user
from app.core.responses import APIResponse, get_request_id
from app.core.security_monitoring import AlertSeverity, AnomalyType, RiskLevel, security_monitor
from app.core.structured_logging import EventType, get_logger
from app.db.models.user import User
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy

router = APIRouter()
logger = get_logger(__name__)


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/security/dashboard", summary="Security Dashboard")
async def get_security_dashboard(
    request: Request,
    hours: int = Query(24, description="Hours of data to include"),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get comprehensive security monitoring dashboard
    Requires admin privileges
    """
    try:
        # Get security alerts for dashboard
        alerts = await security_monitor.get_security_alerts(hours=hours)

        # Calculate metrics
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        high_alerts = [a for a in alerts if a.severity == AlertSeverity.HIGH]
        medium_alerts = [a for a in alerts if a.severity == AlertSeverity.MEDIUM]
        low_alerts = [a for a in alerts if a.severity == AlertSeverity.LOW]

        # Recent events summary
        recent_events = []
        for alert in alerts[:10]:  # Last 10 alerts
            recent_events.append(
                {
                    "id": alert.id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "user_id": alert.user_id,
                    "risk_score": alert.risk_score,
                }
            )

        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "time_period_hours": hours,
            "total_alerts": len(alerts),
            "alert_breakdown": {
                "critical": len(critical_alerts),
                "high": len(high_alerts),
                "medium": len(medium_alerts),
                "low": len(low_alerts),
            },
            "security_score": max(
                0,
                100
                - (len(critical_alerts) * 20)
                - (len(high_alerts) * 10)
                - (len(medium_alerts) * 5),
            ),
            "recent_events": recent_events,
            "active_threats": len(
                [
                    a
                    for a in alerts
                    if not a.resolved and a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
                ]
            ),
            "resolved_alerts": len([a for a in alerts if a.resolved]),
        }

        logger.info(
            EventType.SECURITY_EVENT,
            "Security dashboard accessed",
            operation_name="get_security_dashboard",
            user_id=str(current_user.id),
            total_alerts=len(alerts),
            critical_alerts=len(critical_alerts),
        )

        return APIResponse.success(
            data=dashboard_data,
            message="Security dashboard data retrieved successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(e, operation="get_security_dashboard", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to retrieve security dashboard data", request_id=get_request_id(request)
        )


@router.get("/security/alerts", summary="Security Alerts")
async def get_security_alerts(
    request: Request,
    user_id: str | None = Query(None, description="Filter by user ID"),
    severity: str | None = Query(None, description="Filter by severity level"),
    anomaly_type: str | None = Query(None, description="Filter by anomaly type"),
    hours: int = Query(24, description="Hours of alerts to retrieve"),
    include_resolved: bool = Query(False, description="Include resolved alerts"),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get security alerts with filtering options
    Requires admin privileges
    """
    try:
        # Parse severity and anomaly type if provided
        severity_enum = None
        if severity:
            try:
                severity_enum = AlertSeverity(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity level: {severity}") from e


        anomaly_type_enum = None
        if anomaly_type:
            try:
                anomaly_type_enum = AnomalyType(anomaly_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid anomaly type: {anomaly_type}") from e


        # Get alerts
        alerts = await security_monitor.get_security_alerts(
            user_id=user_id,
            severity=severity_enum,
            anomaly_type=anomaly_type_enum,
            hours=hours,
            include_resolved=include_resolved,
        )

        # Format alerts for response
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append(
                {
                    "id": alert.id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "user_id": alert.user_id,
                    "description": alert.description,
                    "details": alert.details,
                    "timestamp": alert.timestamp.isoformat(),
                    "risk_score": alert.risk_score,
                    "action_taken": alert.action_taken,
                    "resolved": alert.resolved,
                    "metadata": alert.metadata,
                }
            )

        logger.info(
            EventType.SECURITY_EVENT,
            "Security alerts retrieved",
            operation_name="get_security_alerts",
            user_id=str(current_user.id),
            alert_count=len(formatted_alerts),
            filters={
                "user_id": user_id,
                "severity": severity,
                "anomaly_type": anomaly_type,
                "hours": hours,
            },
        )

        return APIResponse.success(
            data={
                "alerts": formatted_alerts,
                "count": len(formatted_alerts),
                "filters_applied": {
                    "user_id": user_id,
                    "severity": severity,
                    "anomaly_type": anomaly_type,
                    "hours": hours,
                    "include_resolved": include_resolved,
                },
            },
            message=f"Retrieved {len(formatted_alerts)} security alerts",
            request_id=get_request_id(request),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(e, operation="get_security_alerts", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to retrieve security alerts", request_id=get_request_id(request)
        )


@router.post("/security/alerts/{alert_id}/resolve", summary="Resolve Security Alert")
async def resolve_security_alert(
    alert_id: str,
    request: Request,
    resolution_note: str | None = Query(None, description="Note about resolution"),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Mark a security alert as resolved
    Requires admin privileges
    """
    try:
        success = await security_monitor.resolve_alert(alert_id, resolution_note)

        if not success:
            raise HTTPException(status_code=404, detail=f"Security alert not found: {alert_id}") from e


        logger.info(
            EventType.SECURITY_EVENT,
            "Security alert resolved",
            operation_name="resolve_security_alert",
            user_id=str(current_user.id),
            alert_id=alert_id,
            resolution_note=resolution_note,
        )

        return APIResponse.success(
            data={
                "alert_id": alert_id,
                "resolved": True,
                "resolution_note": resolution_note,
                "resolved_by": str(current_user.id),
                "resolved_at": datetime.utcnow().isoformat(),
            },
            message="Security alert resolved successfully",
            request_id=get_request_id(request),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(e, operation="resolve_security_alert", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to resolve security alert", request_id=get_request_id(request)
        )


@router.get("/security/user-risk/{user_id}", summary="User Risk Assessment")
async def get_user_risk_assessment(
    user_id: str, request: Request, current_user: User = Depends(get_current_admin_user)
):
    """
    Get risk assessment and security profile for a specific user
    Requires admin privileges
    """
    try:
        # Get user risk level and factors
        risk_level, risk_factors = await security_monitor.get_user_risk_level(user_id)

        # Get user's recent security alerts
        user_alerts = await security_monitor.get_security_alerts(
            user_id=user_id,
            hours=168,  # Last 7 days
            include_resolved=False,
        )

        # Format alerts
        formatted_alerts = []
        for alert in user_alerts:
            formatted_alerts.append(
                {
                    "id": alert.id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "risk_score": alert.risk_score,
                }
            )

        # Get user behavior profile
        user_profile = await security_monitor._get_user_profile(user_id)

        profile_data = {
            "user_id": user_profile.user_id,
            "total_logins": user_profile.total_logins,
            "failed_login_attempts": user_profile.failed_login_attempts,
            "successful_logins": user_profile.successful_logins,
            "unique_locations": len(user_profile.unique_locations),
            "last_activity": user_profile.last_activity.isoformat(),
            "risk_level": user_profile.risk_level.value,
            "typical_ip_count": len(user_profile.typical_ip_addresses),
            "typical_user_agent_count": len(user_profile.typical_user_agents),
        }

        assessment_data = {
            "user_id": user_id,
            "current_risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "recent_alerts": formatted_alerts,
            "user_profile": profile_data,
            "assessment_timestamp": datetime.utcnow().isoformat(),
            "security_recommendations": self._generate_security_recommendations(
                risk_level, user_alerts
            ),
        }

        logger.info(
            EventType.SECURITY_EVENT,
            "User risk assessment retrieved",
            operation_name="get_user_risk_assessment",
            user_id=str(current_user.id),
            target_user_id=user_id,
            risk_level=risk_level.value,
        )

        return APIResponse.success(
            data=assessment_data,
            message="User risk assessment retrieved successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(e, operation="get_user_risk_assessment", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to retrieve user risk assessment", request_id=get_request_id(request)
        )


@router.get("/security/threat-intelligence", summary="Threat Intelligence Summary")
async def get_threat_intelligence_summary(
    request: Request,
    hours: int = Query(24, description="Hours of data to analyze"),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get threat intelligence summary and security metrics
    Requires admin privileges
    """
    try:
        # Get recent security alerts for analysis
        alerts = await security_monitor.get_security_alerts(hours=hours)

        # Analyze threat patterns
        threat_patterns = {
            "top_anomaly_types": {},
            "severity_distribution": {},
            "risk_score_distribution": {},
            "temporal_patterns": {},
            "geographic_distribution": {},
            "attack_sources": {},
        }

        # Analyze anomaly types
        for alert in alerts:
            anomaly_type = alert.anomaly_type.value
            threat_patterns["top_anomaly_types"][anomaly_type] = (
                threat_patterns["top_anomaly_types"].get(anomaly_type, 0) + 1
            )

        # Analyze severity distribution
        for alert in alerts:
            severity = alert.severity.value
            threat_patterns["severity_distribution"][severity] = (
                threat_patterns["severity_distribution"].get(severity, 0) + 1
            )

        # Analyze risk scores
        risk_buckets = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for alert in alerts:
            if alert.risk_score < 30:
                risk_buckets["low"] += 1
            elif alert.risk_score < 50:
                risk_buckets["medium"] += 1
            elif alert.risk_score < 70:
                risk_buckets["high"] += 1
            else:
                risk_buckets["critical"] += 1

        threat_patterns["risk_score_distribution"] = risk_buckets

        # Get system-wide metrics
        metrics = {
            "total_alerts": len(alerts),
            "unresolved_alerts": len([a for a in alerts if not a.resolved]),
            "critical_alerts": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            "high_risk_alerts": len([a for a in alerts if a.risk_score >= 70]),
            "unique_users_affected": len(set(a.user_id for a in alerts if a.user_id)),
            "time_period_hours": hours,
            "average_risk_score": sum(a.risk_score for a in alerts) / len(alerts) if alerts else 0,
            "security_status": "healthy"
            if len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]) == 0
            else "critical",
        }

        # Combine all data
        intelligence_summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_hours": hours,
            "metrics": metrics,
            "threat_patterns": threat_patterns,
            "security_recommendations": self._generate_system_recommendations(alerts, metrics),
        }

        logger.info(
            EventType.SECURITY_EVENT,
            "Threat intelligence summary retrieved",
            operation_name="get_threat_intelligence_summary",
            user_id=str(current_user.id),
            total_alerts=len(alerts),
            security_status=metrics["security_status"],
        )

        return APIResponse.success(
            data=intelligence_summary,
            message="Threat intelligence summary retrieved successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(
            e, operation="get_threat_intelligence_summary", user_id=str(current_user.id)
        )
        return APIResponse.server_error(
            message="Failed to retrieve threat intelligence summary",
            request_id=get_request_id(request),
        )


@router.post("/security/record-event", summary="Record Security Event")
async def record_security_event(
    event_data: dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """
    Record a security event for monitoring and analysis
    """
    try:
        # Extract event data
        event_type = event_data.get("event_type", "unknown")
        ip_address = event_data.get(
            "ip_address", request.client.host if request.client else "unknown"
        )
        user_agent = event_data.get("user_agent", request.headers.get("user-agent", "unknown"))
        success = event_data.get("success", True)
        endpoint = event_data.get("endpoint", str(request.url.path))
        metadata = event_data.get("metadata", {})

        # Record the security event
        alert = await security_monitor.record_security_event(
            user_id=str(current_user.id),
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            endpoint=endpoint,
            metadata=metadata,
        )

        response_data = {
            "event_recorded": True,
            "event_type": event_type,
            "alert_generated": alert is not None,
            "user_id": str(current_user.id),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if alert:
            response_data.update(
                {
                    "alert_id": alert.id,
                    "alert_severity": alert.severity.value,
                    "alert_description": alert.description,
                    "risk_score": alert.risk_score,
                }
            )

        logger.info(
            EventType.SECURITY_EVENT,
            "Security event recorded",
            operation_name="record_security_event",
            user_id=str(current_user.id),
            event_type=event_type,
            alert_generated=alert is not None,
        )

        return APIResponse.success(
            data=response_data,
            message="Security event recorded successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(e, operation="record_security_event", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to record security event", request_id=get_request_id(request)
        )


def _generate_security_recommendations(risk_level: RiskLevel, user_alerts: list) -> list[str]:
    """Generate security recommendations based on user risk level and alerts"""
    recommendations = []

    if risk_level in [RiskLevel.HIGH, RiskLevel.SEVERE]:
        recommendations.extend(
            [
                "Implement multi-factor authentication immediately",
                "Review recent login activity for unauthorized access",
                "Consider temporary account lock pending investigation",
                "Enable enhanced monitoring for this user",
            ]
        )

    # Specific recommendations based on alert types
    anomaly_types = set(alert.anomaly_type for alert in user_alerts)

    if "impossible_travel" in anomaly_types:
        recommendations.append("Verify user identity and recent login locations")

    if "brute_force_pattern" in anomaly_types:
        recommendations.append("Force password reset and review account security")

    if "multiple_concurrent_sessions" in anomaly_types:
        recommendations.append("Implement session management and limit concurrent access")

    if not recommendations:
        recommendations.append("Continue monitoring user activity for anomalies")

    return recommendations


def _generate_system_recommendations(alerts: list, metrics: dict[str, Any]) -> list[str]:
    """Generate system-wide security recommendations"""
    recommendations = []

    critical_alerts = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])

    if critical_alerts > 0:
        recommendations.append(
            f"IMMEDIATE ACTION REQUIRED: {critical_alerts} critical security alerts detected"
        )

    if metrics["average_risk_score"] > 60:
        recommendations.append(
            "Review overall security posture and implement additional protections"
        )

    if metrics["unique_users_affected"] > 10:
        recommendations.append(
            "Investigate potential widespread security issue affecting multiple users"
        )

    if len([a for a in alerts if a.anomaly_type.value == "brute_force_pattern"]) > 5:
        recommendations.append("Strengthen authentication mechanisms and implement rate limiting")

    if len([a for a in alerts if a.anomaly_type.value == "impossible_travel"]) > 3:
        recommendations.append("Review authentication flows and implement additional verification")

    if not recommendations:
        recommendations.append("Security posture is stable - continue routine monitoring")

    return recommendations
