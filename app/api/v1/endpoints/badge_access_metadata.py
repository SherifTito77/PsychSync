"""
Badge Access Metadata Analysis API Endpoints

Building entry/exit timestamps only — no room-level tracking.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/badge-access-metadata", tags=["Badge Access Metadata"])


def _get_analyzer():
    from app.services.badge_access_metadata_service import BadgeAccessAnalyzer

    return BadgeAccessAnalyzer()


def _get_registry():
    from app.services.badge_access_metadata_service import badge_access_registry

    return badge_access_registry


@router.get("/signals/{org_id}")
async def get_badge_access_signals(
    org_id: str,
    days: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
):
    """Full badge access behavioral signals."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_swipes = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_swipes.extend(
                    await connector.fetch_swipes(current_user.email, start, end)
                )
            except Exception as e:
                logger.warning("Badge connector %s failed: %s", info["name"], e)

    signals = analyzer.analyze(all_swipes, days=days)
    return {"success": True, "org_id": org_id, "days": days, "signals": asdict(signals)}


@router.get("/burnout/{org_id}")
async def get_badge_burnout_signals(
    org_id: str,
    days: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk from badge access metadata."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_swipes = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_swipes.extend(
                    await connector.fetch_swipes(current_user.email, start, end)
                )
            except Exception:
                pass

    signals = analyzer.analyze(all_swipes, days=days)
    return {
        "success": True,
        "burnout": {
            "risk_score": signals.burnout_risk_score,
            "risk_label": signals.risk_label,
            "overwork": signals.overwork_score,
            "boundary_erosion": signals.boundary_erosion_score,
            "hours_trend": signals.hours_trend,
            "recent_vs_baseline": signals.recent_vs_baseline_hours,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_badge_access_status(current_user: User = Depends(get_current_user)):
    registry = _get_registry()
    return {
        "success": True,
        "connectors": registry.list_connectors(),
        "available": len(registry.list_connectors()) > 0,
        "privacy_note": "Building entry/exit only. No room-level or movement tracking.",
    }
