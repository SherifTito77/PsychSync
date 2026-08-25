"""
Organizational Pulse API

The unified predictive intelligence endpoint that answers 7 key questions
about organizational health, turning PsychSync from an HR platform into
an Organizational Behavioral Intelligence Platform.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.data_source_aggregator import data_source_aggregator
from app.services.organizational_pulse_service import OrganizationalPulseService
from app.services.privacy_guard import PrivacyContext, PrivacyGuard
from app.services.security import get_current_user

router = APIRouter(
    prefix="/pulse",
    tags=["Organizational Pulse"],
)

_service = OrganizationalPulseService()
_privacy = PrivacyGuard()


@router.get("/{organization_id}")
async def get_organizational_pulse(
    organization_id: str,
    lookback_days: int = Query(default=45, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Full organizational pulse — answers 7 key predictive questions:

    1. Which teams are becoming isolated?
    2. Which managers are creating burnout?
    3. Which departments are collaborating effectively?
    4. Where is organizational friction increasing?
    5. Which teams are at risk of losing key talent?
    6. Which organizational changes are likely to reduce performance?
    7. What interventions should leaders take before problems become visible?

    Returns early warnings, predictions, and prioritized interventions.
    """
    # Gather enrichment from connected data sources
    enrichment = await data_source_aggregator.gather_bi_enrichment(organization_id)
    hris = await data_source_aggregator.gather_hris_analysis(organization_id)

    pulse = await _service.generate_pulse(
        db,
        organization_id,
        lookback_days,
        enrichment=enrichment or None,
        hris_signals=hris,
    )

    # Apply privacy guard to team-level details within pulse questions
    ctx = PrivacyContext(organization_id=organization_id)
    pulse = _guard_pulse_response(pulse, ctx)
    pulse["data_sources"] = data_source_aggregator.get_data_source_status()
    return pulse


@router.get("/{organization_id}/history")
async def get_pulse_history(
    organization_id: str,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Historical pulse snapshots for temporal trending.
    Returns summary-level data (scores, risk counts, trend) per day.
    """
    return await _service.get_pulse_history(db, organization_id, days)


def _guard_pulse_response(pulse: dict, ctx: PrivacyContext) -> dict:
    """Suppress team-level details in pulse questions when groups are too small."""
    questions = pulse.get("questions", {})
    for q_key, q_data in questions.items():
        if not isinstance(q_data, dict):
            continue
        details = q_data.get("details", [])
        if not isinstance(details, list):
            continue
        guarded_details = []
        for item in details:
            member_count = item.get("member_count", item.get("team_size", 0))
            if member_count and member_count < 5:
                guarded_details.append(
                    {
                        **{
                            k: v
                            for k, v in item.items()
                            if k in ("team_name", "department", "severity")
                        },
                        "suppressed": True,
                        "reason": "Group too small for privacy-safe reporting",
                    }
                )
            else:
                guarded_details.append(item)
        q_data["details"] = guarded_details
    return pulse
