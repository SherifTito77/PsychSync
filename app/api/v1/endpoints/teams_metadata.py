"""
Microsoft Teams Metadata Analysis API Endpoints

Privacy-first Teams intelligence: analyzes ONLY metadata (activity counts,
call durations, presence status). Never reads message content.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams-metadata", tags=["Teams Metadata Analysis"])


def _get_analyzer():
    from app.services.teams_metadata_service import TeamsMetadataAnalyzer

    return TeamsMetadataAnalyzer()


def _get_registry():
    from app.services.teams_metadata_service import teams_metadata_registry

    return teams_metadata_registry


@router.get("/signals/{org_id}")
async def get_teams_metadata_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Full Teams metadata behavioral signals for an organization."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_activity = []
    all_presence = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                activity = await connector.fetch_activity(
                    current_user.email, start, end
                )
                presence = await connector.fetch_presence(
                    current_user.email, start, end
                )
                all_activity.extend(activity)
                all_presence.extend(presence)
            except Exception as e:
                logger.warning("Teams connector %s failed: %s", info["name"], e)

    signals = analyzer.analyze(all_activity, all_presence, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "record_count": len(all_activity),
        "data_source": "live" if all_activity else "no_data",
        "signals": asdict(signals),
    }


@router.get("/daily/{org_id}")
async def get_teams_daily_breakdown(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Per-day Teams activity breakdown for dashboard charts."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_activity = []
    all_presence = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_activity.extend(
                    await connector.fetch_activity(current_user.email, start, end)
                )
                all_presence.extend(
                    await connector.fetch_presence(current_user.email, start, end)
                )
            except Exception:
                pass

    signals = analyzer.analyze(all_activity, all_presence, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "daily_breakdown": signals.daily_breakdown,
        "hourly_distribution": signals.hourly_distribution,
    }


@router.get("/burnout/{org_id}")
async def get_teams_burnout_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk signals derived from Teams metadata only."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_activity = []
    all_presence = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_activity.extend(
                    await connector.fetch_activity(current_user.email, start, end)
                )
                all_presence.extend(
                    await connector.fetch_presence(current_user.email, start, end)
                )
            except Exception:
                pass

    signals = analyzer.analyze(all_activity, all_presence, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "burnout": {
            "risk_score": signals.burnout_risk_score,
            "risk_label": signals.risk_label,
            "communication_load": signals.communication_load_score,
            "boundary_erosion": signals.boundary_erosion_score,
            "meeting_fatigue": signals.meeting_fatigue_score,
            "meeting_hours_per_week": signals.meeting_hours_per_week,
            "after_hours_ratio": signals.after_hours_ratio,
            "weekend_ratio": signals.weekend_ratio,
            "dnd_usage": signals.dnd_usage_ratio,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_teams_metadata_status(
    current_user: User = Depends(get_current_user),
):
    """Check which Teams metadata connectors are registered."""
    registry = _get_registry()
    return {
        "success": True,
        "connectors": registry.list_connectors(),
        "available": len(registry.list_connectors()) > 0,
        "privacy_note": "Only Graph Reports + Presence APIs used. Message content is never accessed.",
    }
