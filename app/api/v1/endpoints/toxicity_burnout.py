"""
Toxicity & Burnout Intelligence API

Endpoints for the passive signal-based toxicity and burnout detection
system. All data comes from infrastructure metadata — zero human input
required. Detects toxic interpersonal patterns and burnout trajectories
from SSO, VPN, endpoint, calendar, code review, ticket, and
communication metadata.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.toxicity_burnout import (
    ToxicityBurnoutAlert,
    ToxicityBurnoutSnapshot,
)
from app.db.models.user import User
from app.services.data_source_aggregator import data_source_aggregator
from app.services.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/toxicity-burnout",
    tags=["Toxicity & Burnout Intelligence"],
)


async def _persist_snapshot(
    db: AsyncSession,
    organization_id: str,
    result: dict[str, Any],
) -> ToxicityBurnoutSnapshot:
    """Save composite result as a snapshot and generate alerts."""
    snapshot = ToxicityBurnoutSnapshot(
        organization_id=organization_id,
        snapshot_date=date.today(),
        scope="organization",
        burnout_score=result.get("burnout_score", 0),
        toxicity_score=result.get("toxicity_score", 0),
        combined_risk=result.get("combined_risk", 0),
        cross_contamination_multiplier=result.get(
            "cross_contamination_multiplier", 1.0
        ),
        burnout_label=result.get("burnout_label", "No Data"),
        toxicity_label=result.get("toxicity_label", "No Data"),
        combined_label=result.get("combined_label", "No Data"),
        burnout_signals=result.get("burnout_signals"),
        toxicity_signals=result.get("toxicity_signals"),
        active_burnout_sources=result.get("active_burnout_sources", 0),
        active_toxicity_sources=result.get("active_toxicity_sources", 0),
        overlap_patterns=result.get("overlap_patterns"),
        recommendations=result.get("recommendations"),
    )
    db.add(snapshot)

    # Generate alerts from overlap patterns
    overlap_patterns = result.get("overlap_patterns", [])
    combined_risk = result.get("combined_risk", 0)

    alert_type_map = {
        "Overwork + Exclusion": "overwork_exclusion",
        "High output + No recognition": "high_output_no_recognition",
        "Manager 1:1 drought": "manager_drought",
        "Review hostility + PTO": "review_hostility_pto",
        "Meeting domination + team attrition": "meeting_domination_attrition",
    }

    severity = (
        "critical"
        if combined_risk >= 70
        else (
            "high"
            if combined_risk >= 45
            else "medium" if combined_risk >= 25 else "low"
        )
    )

    for pattern in overlap_patterns:
        alert_type = "overlap_detected"
        for prefix, mapped_type in alert_type_map.items():
            if pattern.startswith(prefix):
                alert_type = mapped_type
                break

        alert = ToxicityBurnoutAlert(
            organization_id=organization_id,
            severity=severity,
            alert_type=alert_type,
            description=pattern,
            burnout_score_at_alert=result.get("burnout_score"),
            toxicity_score_at_alert=result.get("toxicity_score"),
            combined_risk_at_alert=combined_risk,
        )
        db.add(alert)

    await db.commit()
    await db.refresh(snapshot)
    return snapshot


@router.get("/{organization_id}/composite")
async def get_composite_risk(
    organization_id: str,
    days: int = Query(default=30, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Full toxicity + burnout composite with cross-contamination multiplier."""
    result = await data_source_aggregator.gather_toxicity_burnout_composite(
        organization_id=organization_id,
        days=days,
    )

    # Persist snapshot
    try:
        snapshot = await _persist_snapshot(db, organization_id, result)
        result["snapshot_id"] = str(snapshot.id)
    except Exception as exc:
        logger.warning("Failed to persist toxicity snapshot: %s", exc)

    return result


@router.get("/{organization_id}/toxicity")
async def get_toxicity_signals(
    organization_id: str,
    days: int = Query(default=30, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Toxicity signals from all passive collectors."""
    return await data_source_aggregator.gather_toxicity_signals(
        organization_id=organization_id,
        days=days,
    )


@router.get("/{organization_id}/burnout-passive")
async def get_passive_burnout_signals(
    organization_id: str,
    user_email: Optional[str] = Query(default=None),
    days: int = Query(default=14, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Passive burnout signals from infrastructure metadata."""
    return await data_source_aggregator.gather_passive_burnout_signals(
        organization_id=organization_id,
        user_email=user_email,
        days=days,
    )


@router.get("/{organization_id}/data-sources")
async def get_data_source_status(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Report which toxicity/burnout data sources are connected."""
    return data_source_aggregator.get_data_source_status()


@router.get("/{organization_id}/trend")
async def get_trend(
    organization_id: str,
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Historical trend of toxicity/burnout scores."""
    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(ToxicityBurnoutSnapshot)
        .where(ToxicityBurnoutSnapshot.organization_id == organization_id)
        .where(ToxicityBurnoutSnapshot.snapshot_date >= start_date)
        .order_by(ToxicityBurnoutSnapshot.snapshot_date)
    )
    snapshots = result.scalars().all()

    points = [
        {
            "date": str(s.snapshot_date),
            "burnout_score": s.burnout_score,
            "toxicity_score": s.toxicity_score,
            "combined_risk": s.combined_risk,
            "cross_contamination_multiplier": s.cross_contamination_multiplier,
            "burnout_label": s.burnout_label,
            "toxicity_label": s.toxicity_label,
            "combined_label": s.combined_label,
        }
        for s in snapshots
    ]

    # Determine trend direction
    if len(points) >= 2:
        recent = points[-1]["combined_risk"]
        older = points[0]["combined_risk"]
        diff = recent - older
        direction = "improving" if diff < -5 else "declining" if diff > 5 else "stable"
    else:
        direction = "stable"

    return {
        "snapshots": points,
        "trend_direction": direction,
        "period_days": days,
    }


@router.get("/{organization_id}/alerts")
async def get_alerts(
    organization_id: str,
    resolved: Optional[bool] = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Active toxicity/burnout alerts from overlap detection."""
    query = select(ToxicityBurnoutAlert).where(
        ToxicityBurnoutAlert.organization_id == organization_id
    )
    if resolved is not None:
        query = query.where(ToxicityBurnoutAlert.is_resolved == resolved)
    query = query.order_by(desc(ToxicityBurnoutAlert.created_at)).limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "alerts": [
            {
                "id": str(a.id),
                "severity": a.severity,
                "alert_type": a.alert_type,
                "description": a.description,
                "burnout_score_at_alert": a.burnout_score_at_alert,
                "toxicity_score_at_alert": a.toxicity_score_at_alert,
                "combined_risk_at_alert": a.combined_risk_at_alert,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "total": len(alerts),
        "unresolved": sum(1 for a in alerts if not a.is_resolved),
    }
