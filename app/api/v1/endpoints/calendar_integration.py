"""
Calendar Integration API

Connect Google Calendar or Outlook to analyze meeting load,
focus time, after-hours work, and calendar fragmentation.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.db.models.user import User
from app.services.calendar_integration_service import (
    CalendarBehavioralAnalyzer,
    GoogleCalendarConnector,
    OutlookCalendarConnector,
    calendar_registry,
)
from app.services.security import get_current_user

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar Integration"],
)

_analyzer = CalendarBehavioralAnalyzer()


class CalendarConnectorConfig(BaseModel):
    type: str  # "google" or "outlook"
    name: str
    credentials_json: Optional[str] = None
    service_account_key: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


@router.get("/connectors")
async def list_connectors(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "connectors": calendar_registry.list_connectors(),
        "available_types": ["google", "outlook"],
    }


@router.post("/connectors")
async def register_connector(
    config: CalendarConnectorConfig,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if config.type == "google":
        connector = GoogleCalendarConnector(
            credentials_json=config.credentials_json,
            service_account_key=config.service_account_key,
        )
    elif config.type == "outlook":
        connector = OutlookCalendarConnector(
            tenant_id=config.tenant_id or "",
            client_id=config.client_id or "",
            client_secret=config.client_secret or "",
        )
    else:
        raise HTTPException(400, f"Unknown calendar type: {config.type}")

    test = await connector.test_connection()
    calendar_registry.register(config.name, connector)
    return {"success": True, "name": config.name, "type": config.type, "test": test}


@router.get("/connectors/{name}/events")
async def fetch_events(
    name: str,
    user_email: str = Query(...),
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    connector = calendar_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Calendar connector '{name}' not found")

    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(days=days)

    events = await connector.fetch_events(user_email, start, end)
    return {
        "connector": name,
        "user_email": user_email,
        "period_days": days,
        "total_events": len(events),
        "events": [
            {
                "title": e.title,
                "start": e.start.isoformat(),
                "end": e.end.isoformat(),
                "duration_minutes": e.duration_minutes,
                "attendees": e.attendee_count,
                "type": e.meeting_type.value,
                "recurring": e.is_recurring,
                "after_hours": e.is_after_hours,
            }
            for e in events[:200]
        ],
    }


@router.get("/connectors/{name}/health")
async def meeting_health(
    name: str,
    user_email: str = Query(...),
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Analyze meeting health from calendar data."""
    connector = calendar_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Calendar connector '{name}' not found")

    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(days=days)

    events = await connector.fetch_events(user_email, start, end)
    health = _analyzer.analyze_meeting_health(events, days)

    return {
        "connector": name,
        "user_email": user_email,
        "period_days": days,
        "score": health.score,
        "label": health.label,
        "meeting_hours_per_week": health.meeting_hours_per_week,
        "focus_hours_per_week": health.focus_hours_per_week,
        "after_hours_pct": health.after_hours_pct,
        "back_to_back_rate": health.back_to_back_rate,
        "one_on_one_ratio": health.one_on_one_ratio,
        "recurring_burden_pct": health.recurring_burden_pct,
        "fragmentation_score": health.fragmentation_score,
        "recommendations": health.recommendations,
    }


@router.get("/connectors/{name}/daily")
async def daily_breakdown(
    name: str,
    user_email: str = Query(...),
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Per-day meeting breakdown for charts."""
    connector = calendar_registry.get(name)
    if not connector:
        raise HTTPException(404, f"Calendar connector '{name}' not found")

    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(days=days)

    events = await connector.fetch_events(user_email, start, end)
    breakdown = _analyzer.daily_breakdown(events, days)

    return {
        "connector": name,
        "user_email": user_email,
        "period_days": days,
        "daily": breakdown,
    }
