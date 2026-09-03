"""Intelligence Loop API — the core product cycle endpoint."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(prefix="/intelligence", tags=["Intelligence Loop"])


@router.get("/{org_id}/cycle")
async def run_intelligence_cycle(org_id: str, db: AsyncSession = Depends(get_db)):
    """Run a full intelligence cycle and return results."""
    from dataclasses import asdict

    from app.services.intelligence_loop import intelligence_loop

    result = await intelligence_loop.run_cycle(db, org_id)
    return asdict(result)


@router.get("/{org_id}/risks")
async def get_active_risks(
    org_id: str,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get current risk cards, optionally filtered by severity."""
    from dataclasses import asdict

    from app.services.intelligence_loop import intelligence_loop

    result = await intelligence_loop.run_cycle(db, org_id)
    risks = [asdict(r) for r in result.risks]
    if severity:
        risks = [r for r in risks if r["severity"] == severity]
    return {"org_id": org_id, "risks": risks, "total": len(risks)}


@router.get("/{org_id}/health")
async def get_org_health(org_id: str, db: AsyncSession = Depends(get_db)):
    """Get overall organizational health score with breakdown."""
    from dataclasses import asdict

    from app.services.intelligence_loop import intelligence_loop

    result = await intelligence_loop.run_cycle(db, org_id)
    return {
        "org_id": org_id,
        "overall_health_score": result.overall_health_score,
        "network_health": result.network_health,
        "signal_summary": result.signal_summary,
        "risk_summary": result.risk_summary,
        "active_interventions": result.active_interventions,
        "data_sources": [asdict(ds) for ds in result.data_sources],
    }


@router.get("/{org_id}/improvements")
async def get_improvements(org_id: str, db: AsyncSession = Depends(get_db)):
    """Get improvement metrics for active interventions."""
    from dataclasses import asdict

    from app.services.intelligence_loop import intelligence_loop

    result = await intelligence_loop.run_cycle(db, org_id)
    return {
        "org_id": org_id,
        "improvements": [asdict(m) for m in result.improvement_metrics],
        "active_interventions": result.active_interventions,
        "narrative_summary": result.narrative_summary,
    }
