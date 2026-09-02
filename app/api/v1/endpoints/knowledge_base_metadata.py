"""
Knowledge Base / Wiki Analytics API Endpoints

Activity metadata only — no page content, no titles, no attachments.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.services.security import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-base-metadata", tags=["Knowledge Base Analytics"])


def _get_analyzer():
    from app.services.knowledge_base_metadata_service import KBAnalyticsAnalyzer

    return KBAnalyticsAnalyzer()


def _get_registry():
    from app.services.knowledge_base_metadata_service import kb_analytics_registry

    return kb_analytics_registry


@router.get("/signals/{org_id}")
async def get_kb_signals(
    org_id: str,
    days: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
):
    """Full knowledge base behavioral signals."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_records.extend(await connector.fetch_activity(org_id, start, end))
            except Exception as e:
                logger.warning("KB connector %s failed: %s", info["name"], e)

    signals = analyzer.analyze(all_records, days=days)
    return {"success": True, "org_id": org_id, "days": days, "signals": asdict(signals)}


@router.get("/burnout/{org_id}")
async def get_kb_burnout(
    org_id: str,
    days: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
):
    """Burnout/disengagement risk from knowledge base activity patterns."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_records.extend(await connector.fetch_activity(org_id, start, end))
            except Exception:
                pass

    signals = analyzer.analyze(all_records, days=days)
    return {
        "success": True,
        "burnout": {
            "risk_score": signals.burnout_risk,
            "risk_label": signals.risk_label,
            "contribution_trend": signals.contribution_trend,
            "creation_trend": signals.creation_trend,
            "stale_content_ratio": signals.stale_content_ratio,
        },
        "engagement": {
            "knowledge_sharing_score": signals.knowledge_sharing_score,
            "engagement_score": signals.engagement_score,
            "contributor_concentration": signals.contributor_concentration,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_kb_status(current_user: User = Depends(get_current_user)):
    """Check connected knowledge base data sources."""
    registry = _get_registry()
    return {
        "success": True,
        "connectors": registry.list_connectors(),
        "available": len(registry.list_connectors()) > 0,
        "privacy_note": "Activity event metadata only. No page content, titles, or attachments.",
    }
