"""
PTO Patterns Analysis API Endpoints

Leave booking/cancellation metadata only — no leave reasons or medical details.
"""

import logging
from dataclasses import asdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pto-patterns", tags=["PTO Patterns Analysis"])


def _get_analyzer():
    from app.services.pto_patterns_metadata_service import PTOPatternsAnalyzer

    return PTOPatternsAnalyzer()


def _get_registry():
    from app.services.pto_patterns_metadata_service import pto_registry

    return pto_registry


@router.get("/signals/{org_id}")
async def get_pto_signals(
    org_id: str,
    lookback_days: int = Query(365, ge=30, le=730),
    current_user: User = Depends(get_current_user),
):
    """Full PTO behavioral signals — vacation avoidance, sick patterns, recovery deficit."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    balance = None
    end = date.today()
    start = end - timedelta(days=lookback_days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                records = await connector.fetch_leave_records(
                    current_user.email, start, end
                )
                all_records.extend(records)
                if balance is None:
                    balance = await connector.fetch_balance(current_user.email)
            except Exception as e:
                logger.warning("PTO connector %s failed: %s", info["name"], e)

    signals = analyzer.analyze(all_records, balance, lookback_days)
    return {
        "success": True,
        "org_id": org_id,
        "lookback_days": lookback_days,
        "signals": asdict(signals),
    }


@router.get("/burnout/{org_id}")
async def get_pto_burnout_signals(
    org_id: str,
    lookback_days: int = Query(365, ge=30, le=730),
    current_user: User = Depends(get_current_user),
):
    """Burnout risk from PTO patterns."""
    registry = _get_registry()
    analyzer = _get_analyzer()

    all_records = []
    balance = None
    end = date.today()
    start = end - timedelta(days=lookback_days)

    for info in registry.list_connectors():
        connector = registry.get(info["name"])
        if connector:
            try:
                all_records.extend(
                    await connector.fetch_leave_records(current_user.email, start, end)
                )
                if balance is None:
                    balance = await connector.fetch_balance(current_user.email)
            except Exception:
                pass

    signals = analyzer.analyze(all_records, balance, lookback_days)
    return {
        "success": True,
        "burnout": {
            "risk_score": signals.burnout_risk_score,
            "risk_label": signals.risk_label,
            "vacation_avoidance": signals.vacation_avoidance_score,
            "recovery_deficit": signals.recovery_deficit_score,
            "sick_pattern": signals.sick_pattern_score,
            "days_since_last_vacation": signals.days_since_last_vacation,
            "cancellation_rate": signals.cancellation_rate,
            "utilization_gap": signals.utilization_gap,
        },
        "recommendations": signals.recommendations,
    }


@router.get("/status")
async def get_pto_status(current_user: User = Depends(get_current_user)):
    registry = _get_registry()
    return {
        "success": True,
        "connectors": registry.list_connectors(),
        "available": len(registry.list_connectors()) > 0,
        "privacy_note": "Leave dates and status only. No leave reasons or medical details.",
    }
