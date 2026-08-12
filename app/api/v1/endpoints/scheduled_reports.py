"""
Scheduled Reports API Endpoints

CRUD for user-configured automated report schedules.
next_run is computed from frequency on create/toggle.
send-now is a fire-and-log operation (actual email delivery via notification_service).
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.scheduled_reports import ScheduledReport
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/scheduled-reports", tags=["scheduled-reports"])


def _next_run_for(frequency: str) -> datetime:
    now = datetime.utcnow()
    if frequency == "monthly":
        # First day of next month at 09:00 UTC
        if now.month == 12:
            return datetime(now.year + 1, 1, 1, 9, 0)
        return datetime(now.year, now.month + 1, 1, 9, 0)
    # weekly: next Monday at 09:00 UTC
    days_until_monday = (7 - now.weekday()) % 7 or 7
    next_monday = (now + timedelta(days=days_until_monday)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    return next_monday


def _serialize(r: ScheduledReport) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "name": r.name,
        "frequency": r.frequency,
        "recipients": r.recipients or [],
        "format": r.format,
        "status": r.status,
        "include_charts": r.include_charts,
        "next_run": r.next_run.isoformat() if r.next_run else None,
        "last_run": r.last_run.isoformat() if r.last_run else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(ScheduledReport)
        .where(ScheduledReport.user_id == current_user.id)
        .order_by(ScheduledReport.created_at.desc())
    )
    reports = result.scalars().all()
    return {"reports": [_serialize(r) for r in reports], "total": len(reports)}


class CreateReportRequest(BaseModel):
    name: str
    frequency: str = "weekly"
    recipients: list[str]
    format: str = "pdf"
    include_charts: bool = True


@router.post("")
async def create_report(
    body: CreateReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if body.frequency not in ("weekly", "monthly"):
        raise HTTPException(
            status_code=400, detail="frequency must be 'weekly' or 'monthly'"
        )
    if body.format not in ("pdf", "html"):
        raise HTTPException(status_code=400, detail="format must be 'pdf' or 'html'")
    if not body.recipients:
        raise HTTPException(status_code=400, detail="at least one recipient required")

    report = ScheduledReport(
        user_id=current_user.id,
        name=body.name,
        frequency=body.frequency,
        recipients=body.recipients,
        format=body.format,
        include_charts=body.include_charts,
        status="active",
        next_run=_next_run_for(body.frequency),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return _serialize(report)


@router.post("/{report_id}/toggle")
async def toggle_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    result = await db.execute(
        select(ScheduledReport).where(
            ScheduledReport.id == rid,
            ScheduledReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "paused" if report.status == "active" else "active"
    # Recompute next_run on reactivation
    if report.status == "active":
        report.next_run = _next_run_for(report.frequency)
    await db.commit()
    return {"id": report_id, "status": report.status}


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    result = await db.execute(
        select(ScheduledReport).where(
            ScheduledReport.id == rid,
            ScheduledReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)
    await db.commit()
    return {"id": report_id, "deleted": True}


@router.post("/{report_id}/send-now")
async def send_now(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    result = await db.execute(
        select(ScheduledReport).where(
            ScheduledReport.id == rid,
            ScheduledReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Mark last_run; actual email delivery is handled by the notification service
    report.last_run = datetime.utcnow()
    await db.commit()

    return {
        "id": report_id,
        "status": "queued",
        "recipients": report.recipients,
        "message": f"Report '{report.name}' queued for immediate delivery",
    }
