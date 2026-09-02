# app/api/v1/endpoints/external_benchmarks.py
"""External Benchmarking API — Opt-in, contribute, and compare."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.external_benchmark_service import external_benchmark_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/external-benchmarks",
    tags=["External Benchmarks"],
)


@router.post("/{organization_id}/opt-in")
async def opt_in(
    organization_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Opt into external benchmarking. Requires industry and company_size."""
    opt = await external_benchmark_service.opt_in(
        db,
        organization_id=UUID(organization_id),
        industry=payload["industry"],
        company_size=payload["company_size"],
        maturity_stage=payload.get("maturity_stage"),
    )
    await db.commit()
    return {
        "opted_in": True,
        "industry": opt.industry,
        "company_size": opt.company_size,
    }


@router.post("/{organization_id}/opt-out")
async def opt_out(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Opt out of external benchmarking. All future contributions stop."""
    success = await external_benchmark_service.opt_out(db, UUID(organization_id))
    await db.commit()
    return {"opted_in": False, "success": success}


@router.get("/{organization_id}/status")
async def opt_in_status(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Check opt-in status."""
    opt = await external_benchmark_service.get_opt_in_status(db, UUID(organization_id))
    if not opt:
        return {"opted_in": False}
    return {
        "opted_in": opt.opted_in,
        "industry": opt.industry,
        "company_size": opt.company_size,
        "maturity_stage": opt.maturity_stage,
    }


@router.post("/{organization_id}/contribute")
async def contribute(
    organization_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Contribute anonymized org-level scores to the benchmark pool."""
    contribution = await external_benchmark_service.contribute(
        db,
        organization_id=UUID(organization_id),
        org_scores=payload["scores"],
        team_count=payload.get("team_count", 0),
        employee_count=payload.get("employee_count", 0),
    )
    await db.commit()
    if not contribution:
        return {"contributed": False, "reason": "not_opted_in_or_already_contributed"}
    return {"contributed": True, "period": contribution.contribution_period}


@router.get("/{organization_id}/compare")
async def compare(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get benchmark comparison with peer organizations (with DP noise)."""
    from app.services.behavioral_intelligence_service import (
        BehavioralIntelligenceService,
    )

    bi = BehavioralIntelligenceService()
    dashboard = await bi.get_organization_dashboard(db, organization_id)
    org_scores = dashboard.get("scores", {})

    return await external_benchmark_service.get_benchmarks(
        db, UUID(organization_id), org_scores
    )
