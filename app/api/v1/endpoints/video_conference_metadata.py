"""
Video Conferencing Metadata Analysis API Endpoints

Call lifecycle metadata only — no recordings, no transcripts, no screen content.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.services.security import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/video-conference-metadata", tags=["Video Conferencing Metadata"]
)


def _get_analyzer():
    from app.services.video_conference_metadata_service import VideoConferenceAnalyzer

    return VideoConferenceAnalyzer()


def _get_registry():
    from app.services.video_conference_metadata_service import video_conference_registry

    return video_conference_registry


@router.get("/signals/{org_id}")
async def get_video_conference_signals(
    org_id: str,
    days: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
):
    """Full video conferencing behavioral signals."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_records.extend(await connector.fetch_meetings(org_id, start, end))
            except Exception as e:
                logger.warning(
                    "Video conference connector %s failed: %s", info["name"], e
                )

    signals = analyzer.analyze(all_records, days=days)
    return {"success": True, "org_id": org_id, "days": days, "signals": asdict(signals)}


@router.get("/burnout/{org_id}")
async def get_video_conference_burnout(
    org_id: str,
    days: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk from video conferencing patterns."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_records.extend(await connector.fetch_meetings(org_id, start, end))
            except Exception:
                pass

    signals = analyzer.analyze(all_records, days=days)
    return {
        "success": True,
        "burnout": {
            "risk_score": signals.burnout_risk,
            "risk_label": signals.risk_label,
            "meeting_fatigue": signals.meeting_fatigue_score,
            "overload": signals.overload_score,
            "back_to_back_rate": signals.back_to_back_rate,
            "after_hours_rate": signals.after_hours_meeting_rate,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_video_conference_status(current_user: User = Depends(get_current_user)):
    """Check connected video conferencing data sources."""
    registry = _get_registry()
    return {
        "success": True,
        "connectors": registry.list_connectors(),
        "available": len(registry.list_connectors()) > 0,
        "privacy_note": "Call lifecycle metadata only. No recordings, transcripts, or screen content.",
    }
