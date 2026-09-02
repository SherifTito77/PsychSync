"""
Computer Usage Metadata Analysis API Endpoints

Activity levels only — no screen capture, no keystroke content.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/computer-usage-metadata", tags=["Computer Usage Metadata"])


def _get_analyzer():
    from app.services.computer_usage_metadata_service import ComputerUsageAnalyzer

    return ComputerUsageAnalyzer()


def _get_registry():
    from app.services.computer_usage_metadata_service import computer_usage_registry

    return computer_usage_registry


@router.get("/signals/{org_id}")
async def get_computer_usage_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Full computer usage behavioral signals."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_buckets = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_buckets.extend(
                    await connector.fetch_buckets(current_user.email, start, end)
                )
            except Exception as e:
                logger.warning(
                    "Computer usage connector %s failed: %s", info["name"], e
                )

    signals = analyzer.analyze(all_buckets, days=days)
    return {"success": True, "org_id": org_id, "days": days, "signals": asdict(signals)}


@router.get("/burnout/{org_id}")
async def get_computer_burnout_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk from computer usage metadata."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_buckets = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_buckets.extend(
                    await connector.fetch_buckets(current_user.email, start, end)
                )
            except Exception:
                pass

    signals = analyzer.analyze(all_buckets, days=days)
    return {
        "success": True,
        "burnout": {
            "risk_score": signals.burnout_risk_score,
            "risk_label": signals.risk_label,
            "work_intensity": signals.work_intensity_score,
            "break_deficit": signals.break_deficit_score,
            "boundary_erosion": signals.boundary_erosion_score,
            "context_switching": signals.context_switching_score,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_computer_usage_status(current_user: User = Depends(get_current_user)):
    registry = _get_registry()
    return {
        "success": True,
        "connectors": registry.list_connectors(),
        "available": len(registry.list_connectors()) > 0,
        "privacy_note": "Activity levels only. No screen capture, keystroke content, or app names.",
    }
