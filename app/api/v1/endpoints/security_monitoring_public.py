"""
Security Monitoring Dashboard API
Provides real-time security metrics and event tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from app.core.database import get_async_db
from app.api.v1.deps import get_current_active_user
from app.db.models.user import User

router = APIRouter()


@router.get("/dashboard/metrics")
async def get_security_metrics(
    hours: int = 24,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get security metrics for the monitoring dashboard.

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        Security metrics including failed logins, CSRF attempts, etc.
    """
    # Check if user is admin
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Calculate time range
    since = datetime.utcnow() - timedelta(hours=hours)

    # In a real implementation, these would query actual logs/audit tables
    # For now, returning mock data structure
    metrics = {
        "time_range": {
            "hours": hours,
            "since": since.isoformat(),
            "until": datetime.utcnow().isoformat()
        },
        "authentication": {
            "total_login_attempts": 1523,
            "successful_logins": 1487,
            "failed_logins": 36,
            "unique_users_affected": 12,
            "blocked_by_rate_limit": 8
        },
        "authorization": {
            "total_requests": 8542,
            "authorized_requests": 8398,
            "unauthorized_requests": 144,
            "idor_attempts_prevented": 3,
            "ownership_checks_failed": 141
        },
        "csrf": {
            "csrf_tokens_issued": 1487,
            "csrf_validations": 6521,
            "csrf_violations": 15,
            "blocked_requests": 15
        },
        "suspicious_activity": {
            "multiple_failed_logins": 5,
            "unusual_access_patterns": 2,
            "rapid_requests": 12,
            "blocked_ips": 7
        },
        "top_blocked_ips": [
            {"ip": "192.168.1.100", "attempts": 45, "reason": "Rate limit exceeded"},
            {"ip": "10.0.0.55", "attempts": 23, "reason": "Failed authentication"},
            {"ip": "172.16.0.42", "attempts": 18, "reason": "CSRF violation"}
        ],
        "recent_events": await get_recent_security_events(db, limit=10)
    }

    return metrics


@router.get("/dashboard/events")
async def get_security_events(
    limit: int = 50,
    event_type: str = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get recent security events with optional filtering.

    Args:
        limit: Maximum number of events to return
        event_type: Filter by event type (e.g., "failed_login", "csrf_violation")
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    events = await get_recent_security_events(db, limit, event_type)

    return {
        "total_events": len(events),
        "events": events,
        "summary": generate_event_summary(events)
    }


@router.get("/dashboard/stats/timeline")
async def get_security_timeline(
    hours: int = 24,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get security events aggregated by time period.
    Useful for visualizing trends in the dashboard.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Generate hourly buckets for the time range
    timeline = []
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    for i in range(hours):
        hour_start = current_hour - timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)

        timeline.append({
            "hour": hour_start.isoformat(),
            "failed_logins": 1 + (i % 5),  # Mock data
            "csrf_violations": (i % 7) == 0 and 1 or 0,
            "auth_failures": 2 + (i % 3),
            "total_requests": 300 + (i * 10)
        })

    return {
        "time_range_hours": hours,
        "timeline": list(reversed(timeline))
    }


@router.post("/dashboard/test-alert")
async def send_test_alert(
    alert_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a test security alert (for dashboard testing).
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Log the test alert
    print(f"🚨 TEST ALERT [{alert_type}] sent by {current_user.email}")

    return {
        "message": "Test alert sent",
        "alert_type": alert_type,
        "timestamp": datetime.utcnow().isoformat()
    }


# Helper functions
async def get_recent_security_events(db: AsyncSession, limit: int = 10, event_type: str = None) -> List[Dict[str, Any]]:
    """
    Get recent security events from the audit log.

    In production, this would query an actual audit_logs table.
    For now, returning mock data that demonstrates the structure.
    """
    # Mock data showing various security events
    mock_events = [
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "event_type": "failed_login",
            "severity": "medium",
            "ip": "192.168.1.100",
            "user": "unknown@test.com",
            "details": "Invalid password",
            "outcome": "blocked"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
            "event_type": "csrf_violation",
            "severity": "high",
            "ip": "10.0.0.55",
            "user": None,
            "details": "Missing X-CSRF-Token header",
            "outcome": "blocked"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=32)).isoformat(),
            "event_type": "authorization_failed",
            "severity": "medium",
            "ip": "172.16.0.42",
            "user": "user@example.com",
            "details": "Attempted to access another user's data",
            "outcome": "blocked"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
            "event_type": "rate_limit_exceeded",
            "severity": "low",
            "ip": "192.168.1.200",
            "user": "attacker@evil.com",
            "details": "5 login attempts in 1 minute",
            "outcome": "blocked"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "event_type": "successful_login",
            "severity": "info",
            "ip": "10.0.0.1",
            "user": "admin@psychsync.com",
            "details": "Login successful",
            "outcome": "allowed"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "event_type": "idor_attempt_prevented",
            "severity": "high",
            "ip": "172.16.0.50",
            "user": "user@example.com",
            "details": "Attempted to delete assessment owned by another user",
            "outcome": "blocked"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
            "event_type": "token_refresh",
            "severity": "info",
            "ip": "192.168.1.10",
            "user": "user@example.com",
            "details": "Access token refreshed",
            "outcome": "allowed"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "event_type": "multiple_failed_logins",
            "severity": "high",
            "ip": "10.0.0.100",
            "user": "unknown@test.com",
            "details": "10 failed login attempts from same IP",
            "outcome": "blocked"
        }
    ]

    # Filter by event type if specified
    if event_type:
        mock_events = [e for e in mock_events if e["event_type"] == event_type]

    return mock_events[:limit]


def generate_event_summary(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Generate summary statistics from events list."""
    summary = defaultdict(int)

    for event in events:
        summary[event["event_type"]] += 1
        summary[f"severity_{event['severity']}"] += 1

    return dict(summary)
