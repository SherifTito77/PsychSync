"""
Email Metadata Analysis API Endpoints

Privacy-first email intelligence: analyzes ONLY metadata (timestamps,
directions, recipient counts, domains). Never reads email bodies.

Endpoints:
  GET /email-metadata/signals/{org_id}   — full behavioral signals
  GET /email-metadata/daily/{org_id}     — daily breakdown for charting
  GET /email-metadata/burnout/{org_id}   — burnout risk summary only
  GET /email-metadata/status             — connector status
"""

import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-metadata", tags=["Email Metadata Analysis"])


def _get_analyzer():
    from app.services.email_metadata_service import EmailMetadataAnalyzer

    return EmailMetadataAnalyzer()


def _get_registry():
    from app.services.email_metadata_service import email_metadata_registry

    return email_metadata_registry


# ---------------------------------------------------------------------------
# Signals — full behavioral analysis
# ---------------------------------------------------------------------------


@router.get("/signals/{org_id}")
async def get_email_metadata_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90, description="Lookback window in days"),
    current_user: User = Depends(get_current_user),
):
    """Full email metadata behavioral signals for an organization.

    Returns volume metrics, timing patterns, responsiveness indicators,
    network shape, composite scores, and recommendations.
    All derived from metadata only — zero email content accessed.
    """
    registry = _get_registry()
    analyzer = _get_analyzer()

    connectors = registry.list_connectors()
    if not connectors:
        signals = analyzer.analyze([], days=days)
        return {
            "success": True,
            "org_id": org_id,
            "days": days,
            "data_source": "no_connector",
            "signals": asdict(signals),
        }

    # Gather metadata from all registered connectors
    from app.services.email_metadata_service import EmailMetadataAnalyzer

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for connector_info in connectors:
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                records = await connector.fetch_metadata(
                    user_email=current_user.email,
                    start=start,
                    end=end,
                )
                all_records.extend(records)
            except Exception as e:
                logger.warning(
                    "Connector %s failed for %s: %s",
                    connector_info["name"],
                    org_id,
                    e,
                )

    # Compute response times before analysis
    all_records = EmailMetadataAnalyzer.compute_response_times(all_records)
    signals = analyzer.analyze(all_records, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "record_count": len(all_records),
        "data_source": "live" if all_records else "no_data",
        "signals": asdict(signals),
    }


# ---------------------------------------------------------------------------
# Daily breakdown — for charts
# ---------------------------------------------------------------------------


@router.get("/daily/{org_id}")
async def get_email_daily_breakdown(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Per-day email volume and timing breakdown for dashboard charts."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for connector_info in registry.list_connectors():
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                records = await connector.fetch_metadata(
                    user_email=current_user.email,
                    start=start,
                    end=end,
                )
                all_records.extend(records)
            except Exception:
                pass

    signals = analyzer.analyze(all_records, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "daily_breakdown": signals.daily_breakdown,
        "hourly_distribution": signals.hourly_distribution,
    }


# ---------------------------------------------------------------------------
# Burnout summary — lightweight view
# ---------------------------------------------------------------------------


@router.get("/burnout/{org_id}")
async def get_email_burnout_signals(
    org_id: str,
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk signals derived from email metadata only."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    for connector_info in registry.list_connectors():
        connector = registry.get(connector_info["name"])
        if connector:
            try:
                records = await connector.fetch_metadata(
                    user_email=current_user.email,
                    start=start,
                    end=end,
                )
                all_records.extend(records)
            except Exception:
                pass

    from app.services.email_metadata_service import EmailMetadataAnalyzer

    all_records = EmailMetadataAnalyzer.compute_response_times(all_records)
    signals = analyzer.analyze(all_records, days=days)

    return {
        "success": True,
        "org_id": org_id,
        "days": days,
        "burnout": {
            "risk_score": signals.burnout_risk_score,
            "risk_label": signals.risk_label,
            "communication_load": signals.communication_load_score,
            "boundary_erosion": signals.boundary_erosion_score,
            "after_hours_ratio": signals.after_hours_ratio,
            "weekend_ratio": signals.weekend_ratio,
            "instant_reply_ratio": signals.instant_reply_ratio,
            "avg_response_time_min": signals.avg_response_time_min,
        },
        "recommendations": signals.recommendations,
    }


# ---------------------------------------------------------------------------
# Connector status
# ---------------------------------------------------------------------------


@router.get("/status")
async def get_email_metadata_status(
    current_user: User = Depends(get_current_user),
):
    """Check which email metadata connectors are registered."""
    registry = _get_registry()
    connectors = registry.list_connectors()

    return {
        "success": True,
        "connectors": connectors,
        "available": len(connectors) > 0,
        "privacy_note": "Only email metadata is accessed. Email bodies are never read.",
    }
