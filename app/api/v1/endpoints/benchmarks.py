# app/api/v1/endpoints/benchmarks.py
"""
Benchmarking Endpoints

Industry percentile comparison for BI metrics.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.benchmark_service import benchmark_service
from app.services.security import get_current_user

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("/{organization_id}/percentiles", response_model=dict[str, Any])
async def get_all_percentiles(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get percentile ranks for all BI metrics against the org's benchmark cohort."""
    return await benchmark_service.get_all_percentiles(db, organization_id)


@router.get("/{organization_id}/percentile/{metric}", response_model=dict[str, Any])
async def get_metric_percentile(
    organization_id: UUID,
    metric: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get percentile rank for a specific BI metric."""
    return await benchmark_service.get_percentile(db, organization_id, metric)


@router.post("/{organization_id}/enroll/{cohort_id}", response_model=dict[str, Any])
async def enroll_in_benchmark(
    organization_id: UUID,
    cohort_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Enroll an organization in a benchmark cohort."""
    return await benchmark_service.enroll_organization(db, organization_id, cohort_id)


@router.post("/cohorts/{cohort_id}/aggregate", response_model=dict[str, Any])
async def aggregate_cohort(
    cohort_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger benchmark aggregation for a cohort (admin-only in production)."""
    return await benchmark_service.aggregate_cohort(db, cohort_id)
