#!/usr/bin/env python3
"""
Security Analytics Dashboard API

Provides comprehensive security analytics and metrics:
- Real-time security metrics
- Threat detection and indicators
- Audit log querying
- Security trends and analytics
- Alert management

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import User
from app.monitoring.security_analytics import (
    security_analyzer,
    SecurityEvent,
    ThreatLevel
)
from app.monitoring.audit_logger import (
    audit_logger,
    AuditQuery,
    AuditEventType,
    AuditSeverity
)

router = APIRouter()


# ==================== Security Metrics Endpoints ====================

@router.get("/metrics/overview")
async def get_security_metrics_overview(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get real-time security metrics overview.

    Returns aggregate security metrics for dashboard display.
    Requires admin authentication.
    """
    # Check admin permissions
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get metrics from analyzer
    metrics = security_analyzer.get_security_metrics()

    # Add additional context
    metrics.update({
        "timestamp": datetime.utcnow().isoformat(),
        "threat_indicators_active": len([
            e for e in security_analyzer.event_history
            if e.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]),
        "users_with_recent_activity": metrics.get("active_users", 0),
        "ips_with_recent_activity": metrics.get("active_ips", 0)
    })

    return metrics


@router.get("/metrics/threats")
async def get_active_threats(
    hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get active threat indicators.

    Args:
        hours: Lookback period in hours (1-168)
        severity: Filter by severity level (optional)

    Returns list of detected threat indicators.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Analyze recent events for threats
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    threats = []

    # Re-analyze events in lookback window
    for event in security_analyzer.event_history:
        if event.timestamp >= cutoff_time:
            indicators = await security_analyzer.analyze_event(event)

            # Filter by severity if specified
            if severity:
                indicators = [
                    i for i in indicators
                    if i.severity.value == severity
                ]

            threats.extend([
                {
                    "indicator_type": ind.indicator_type,
                    "severity": ind.severity.value,
                    "confidence": ind.confidence,
                    "description": ind.description,
                    "affected_entities": ind.affected_entities,
                    "mitigation_suggestions": ind.mitigation_suggestions,
                    "timestamp": event.timestamp.isoformat()
                }
                for ind in indicators
            ])

    return threats


@router.get("/metrics/events")
async def get_security_events(
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get security events with filtering.

    Args:
        event_type: Filter by event type
        severity: Filter by severity
        hours: Lookback period
        limit: Max events to return

    Returns filtered security events.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    # Filter events
    events = []
    for event in security_analyzer.event_history:
        if event.timestamp < cutoff_time:
            continue

        if event_type and event.event_type != event_type:
            continue

        if severity and event.severity != severity:
            continue

        events.append({
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "session_id": event.session_id,
            "ip_address": event.ip_address,
            "severity": event.severity,
            "details": event.details
        })

        if len(events) >= limit:
            break

    # Sort by timestamp descending
    events.sort(key=lambda e: e["timestamp"], reverse=True)

    return events


@router.get("/metrics/timeline")
async def get_security_timeline(
    hours: int = Query(default=24, ge=1, le=168),
    interval: str = Query(default="hour", enum=["hour", "day"]),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get security events timeline for trend analysis.

    Args:
        hours: Lookback period
        interval: Time bucket size (hour or day)

    Returns timeline data with event counts per interval.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    # Determine bucket size
    if interval == "hour":
        bucket_delta = timedelta(hours=1)
    else:
        bucket_delta = timedelta(days=1)

    # Create buckets
    buckets = {}
    current = cutoff_time
    while current <= datetime.utcnow():
        bucket_key = current.strftime("%Y-%m-%d %H:00" if interval == "hour" else "%Y-%m-%d")
        buckets[bucket_key] = 0
        current += bucket_delta

    # Fill buckets
    for event in security_analyzer.event_history:
        if event.timestamp < cutoff_time:
            continue

        bucket_key = event.timestamp.strftime(
            "%Y-%m-%d %H:00" if interval == "hour" else "%Y-%m-%d"
        )
        if bucket_key in buckets:
            buckets[bucket_key] += 1

    return {
        "interval": interval,
        "hours": hours,
        "data": buckets
    }


# ==================== Audit Log Endpoints ====================

@router.get("/audit/logs")
async def get_audit_logs(
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Query audit logs with filtering.

    Args:
        event_type: Filter by event type
        severity: Filter by severity
        user_id: Filter by user
        hours: Lookback period
        limit: Max records to return

    Returns filtered audit log entries.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Build query
    query = AuditQuery()

    if event_type:
        query = query.filter_by_event_type(event_type)

    if severity:
        query = query.filter_by_severity(severity)

    if user_id:
        query = query.filter_by_user(user_id)

    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter_after_date(cutoff)

    query = query.limit(limit)

    # Execute query (would need actual backend implementation)
    # For now, return empty list
    return []


@router.get("/audit/summary")
async def get_audit_summary(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get audit log summary statistics.

    Args:
        hours: Lookback period

    Returns summary metrics by event type and severity.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Would query actual audit logs
    # For now, return placeholder
    return {
        "hours": hours,
        "total_events": 0,
        "by_type": {},
        "by_severity": {},
        "unique_users": 0,
        "unique_ips": 0
    }


# ==================== Alert Endpoints ====================

@router.get("/alerts/active")
async def get_active_alerts(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get active security alerts.

    Args:
        hours: Lookback period

    Returns list of active alerts requiring attention.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get recent high/critical severity events
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    alerts = []
    for event in security_analyzer.event_history:
        if event.timestamp < cutoff_time:
            continue

        if event.severity in ["high", "critical"]:
            alerts.append({
                "event_type": event.event_type,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "details": event.details
            })

    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Acknowledge a security alert.

    Args:
        alert_id: Alert identifier

    Returns acknowledgment confirmation.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Log acknowledgment
    await audit_logger.log_security_event(
        event_type="alert_acknowledged",
        severity="low",
        user_id=current_user.id,
        details={"alert_id": alert_id}
    )

    return {"status": "acknowledged", "alert_id": alert_id}


# ==================== User Risk Assessment ====================

@router.get("/risk/users/{user_id}")
async def get_user_risk_profile(
    user_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get risk profile for specific user.

    Args:
        user_id: User to analyze
        hours: Lookback period

    Returns user risk assessment.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get user's recent events
    if user_id not in security_analyzer.user_history:
        return {
            "user_id": user_id,
            "risk_level": "unknown",
            "message": "No security events found for user"
        }

    user_events = list(security_analyzer.user_history[user_id])
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_events = [e for e in user_events if e.timestamp > cutoff_time]

    # Analyze for threats
    threat_count = 0
    high_severity_count = 0

    for event in recent_events:
        indicators = await security_analyzer.analyze_event(event)
        threat_count += len(indicators)
        high_severity_count += sum(1 for i in indicators if i.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL])

    # Calculate risk level
    if high_severity_count > 0:
        risk_level = "critical"
    elif threat_count > 5:
        risk_level = "high"
    elif threat_count > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "user_id": user_id,
        "risk_level": risk_level,
        "analysis_period_hours": hours,
        "total_events": len(recent_events),
        "threat_indicators_detected": threat_count,
        "high_severity_threats": high_severity_count,
        "last_activity": recent_events[-1].timestamp.isoformat() if recent_events else None
    }


# ==================== System Security Status ====================

@router.get("/status/overview")
async def get_system_security_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get overall system security status.

    Returns comprehensive security status summary.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    metrics = security_analyzer.get_security_metrics()

    # Calculate security score
    total_events = metrics["total_events"]
    high_severity_events = metrics["events_by_severity"].get("high", 0)
    critical_events = metrics["events_by_severity"].get("critical", 0)

    # Simple scoring algorithm
    security_score = max(0, 100 - (critical_events * 20) - (high_severity_events * 5))

    # Determine status
    if critical_events > 0:
        status = "critical"
    elif high_severity_events > 5:
        status = "warning"
    else:
        status = "healthy"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "security_score": security_score,
        "total_events": total_events,
        "active_users": metrics["active_users"],
        "active_ips": metrics["active_ips"],
        "events_by_severity": metrics["events_by_severity"],
        "events_by_type": metrics["events_last_hour"]
    }
