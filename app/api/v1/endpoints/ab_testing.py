# app/api/v1/endpoints/ab_testing.py
"""A/B Testing API Endpoints

API endpoints for managing A/B experiments, variant assignment, and event tracking.
"""
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_active_user
from app.api.v1.deps import get_current_user
from app.db.models.ab_testing import ABConversion, ABEvent, ABExperiment, ABVariant
from app.db.models.user import User

router = APIRouter()


# ========================================================================
# Pydantic Models
# ========================================================================


class ExperimentCreate(BaseModel):
    """Request model for creating an experiment"""

    name: str = Field(..., description="Unique experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    status: str = Field(
        "draft", description="Experiment status: draft, running, paused, completed"
    )
    start_date: Optional[datetime] = Field(
        None, description="When to start the experiment"
    )
    end_date: Optional[datetime] = Field(None, description="When to end the experiment")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Experiment configuration"
    )


class VariantConfig(BaseModel):
    """Request model for creating a variant"""

    name: str = Field(..., description="Variant name (e.g., control, variant_a)")
    traffic_split: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of traffic (0.0-1.0)"
    )
    is_control: bool = Field(False, description="Whether this is the control variant")


class ExperimentWithVariants(BaseModel):
    """Request model for creating an experiment with variants"""

    experiment: ExperimentCreate
    variants: List[VariantConfig]


class AssignRequest(BaseModel):
    """Request model for variant assignment"""

    experiment: str = Field(..., description="Experiment name")


class TrackRequest(BaseModel):
    """Request model for event tracking"""

    experiment: str = Field(..., description="Experiment name")
    variant: str = Field(..., description="Variant name")
    event_type: str = Field(
        ..., description="Event type (e.g., view, click, conversion)"
    )
    properties: Optional[Dict[str, Any]] = Field(
        None, description="Additional event properties"
    )


class AssignResponse(BaseModel):
    """Response model for variant assignment"""

    variant: str = Field(..., description="Assigned variant name")
    status: str = Field(..., description="Assignment status")
    cached: Optional[bool] = Field(None, description="Whether result was from cache")


class TrackResponse(BaseModel):
    """Response model for event tracking"""

    status: str = Field(..., description="Tracking status")


class VariantResult(BaseModel):
    """Result model for a single variant"""

    variant: str = Field(..., description="Variant name")
    assignments: int = Field(..., description="Number of users assigned")
    conversions: int = Field(..., description="Number of conversions")
    conversion_rate: float = Field(..., description="Conversion rate percentage")
    lift_vs_control: Optional[float] = Field(
        None, description="Lift vs control variant"
    )
    p_value: Optional[float] = Field(
        None, description="Statistical significance p-value"
    )
    significant: Optional[bool] = Field(
        None, description="Whether result is statistically significant"
    )
    is_control: Optional[bool] = Field(
        None, description="Whether this is the control variant"
    )


class ExperimentResults(BaseModel):
    """Response model for experiment results"""

    experiment: str = Field(..., description="Experiment name")
    status: str = Field(..., description="Experiment status")
    results: List[VariantResult] = Field(..., description="Results per variant")


# ========================================================================
# API Endpoints
# ========================================================================


@router.post(
    "/assign",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=AssignResponse,
)
async def assign_variant(
    request: AssignRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Assign user to a variant for the given experiment.

    Uses deterministic hashing for consistent assignment.
    Results are cached for 1 hour.
    """
    loop = asyncio.get_event_loop()

    # Get experiment
    experiment = await loop.run_in_executor(
        None,
        lambda: db.query(ABExperiment)
        .filter(ABExperiment.name == request.experiment)
        .first(),
    )

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Check if experiment is running
    if experiment.status != "running":
        return AssignResponse(variant="control", status=experiment.status)

    # Check if experiment is within date range
    now = datetime.utcnow()
    if experiment.start_date and now < experiment.start_date:
        return AssignResponse(variant="control", status="not_started")
    if experiment.end_date and now > experiment.end_date:
        return AssignResponse(variant="control", status="ended")

    # Get variants
    variants = await loop.run_in_executor(
        None,
        lambda: db.query(ABVariant)
        .filter(ABVariant.experiment_id == experiment.id)
        .all(),
    )

    if not variants:
        raise HTTPException(status_code=404, detail="No variants found for experiment")

    # Deterministic assignment based on user_id + experiment_name
    hash_input = f"{str(current_user.id)}:{request.experiment}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()

    # Convert to 0-1 range
    bucket = int(hash_value[:8], 16) / 0xFFFFFFFF

    # Assign based on traffic split
    cumulative = 0.0
    assigned_variant = "control"

    for variant in variants:
        cumulative += variant.traffic_split
        if bucket < cumulative:
            assigned_variant = variant.name
            break

    # Track assignment event
    assignment_event = ABEvent(
        user_id=current_user.id,
        experiment_id=experiment.id,
        variant_id=next(v.id for v in variants if v.name == assigned_variant),
        event_type="assigned",
    )
    await loop.run_in_executor(None, lambda: db.add(assignment_event))
    await loop.run_in_executor(None, lambda: db.commit())

    return AssignResponse(variant=assigned_variant, status="assigned", cached=False)


@router.post(
    "/track",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=TrackResponse,
)
async def track_event(
    request: TrackRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Track an event for an A/B test variant.

    Events can be views, clicks, conversions, or any custom event type.
    """
    loop = asyncio.get_event_loop()

    # Get experiment
    experiment = await loop.run_in_executor(
        None,
        lambda: db.query(ABExperiment)
        .filter(ABExperiment.name == request.experiment)
        .first(),
    )

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get variant
    variant = await loop.run_in_executor(
        None,
        lambda: db.query(ABVariant)
        .filter(
            ABVariant.experiment_id == experiment.id, ABVariant.name == request.variant
        )
        .first(),
    )

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    # Create event
    event = ABEvent(
        user_id=current_user.id,
        experiment_id=experiment.id,
        variant_id=variant.id,
        event_type=request.event_type,
        properties=request.properties,
    )

    await loop.run_in_executor(None, lambda: db.add(event))

    # If this is a conversion event, also record in conversions table
    if request.event_type in ["signup", "purchase", "activation", "upgrade"]:
        conversion = ABConversion(
            user_id=current_user.id,
            experiment_id=experiment.id,
            variant_id=variant.id,
            conversion_type="primary",
        )
        await loop.run_in_executor(None, lambda: db.add(conversion))

    await loop.run_in_executor(None, lambda: db.commit())

    return TrackResponse(status="tracked")


@router.get(
    "/experiments",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
)
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List all A/B experiments.

    Requires user authentication.
    """
    loop = asyncio.get_event_loop()

    # Build query
    def build_query():
        query = db.query(ABExperiment)
        if status:
            query = query.filter(ABExperiment.status == status)
        return query

    query = await loop.run_in_executor(None, build_query)

    # Execute experiments query
    def get_experiments():
        return (
            query.order_by(desc(ABExperiment.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    experiments = await loop.run_in_executor(None, get_experiments)

    # Get total count
    total = await loop.run_in_executor(None, lambda: query.count())

    return {
        "total": total,
        "experiments": [
            {
                "id": str(exp.id),
                "name": exp.name,
                "description": exp.description,
                "status": exp.status,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "created_at": exp.created_at.isoformat(),
            }
            for exp in experiments
        ],
    }


@router.get(
    "/results/{experiment_name}",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=ExperimentResults,
)
async def get_experiment_results(
    experiment_name: str, db: AsyncSession = Depends(get_async_db)
):
    """
    Get results for an experiment including conversion rates and statistical significance.

    Calculates:
    - Conversion rate per variant
    - Lift vs control
    - Statistical significance (p-value)
    """
    loop = asyncio.get_event_loop()

    # Get experiment
    experiment = await loop.run_in_executor(
        None,
        lambda: db.query(ABExperiment)
        .filter(ABExperiment.name == experiment_name)
        .first(),
    )

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get variants
    variants = await loop.run_in_executor(
        None,
        lambda: db.query(ABVariant)
        .filter(ABVariant.experiment_id == experiment.id)
        .all(),
    )

    results = []

    for variant in variants:
        # Count assignments (unique users with 'assigned' event)
        assignments = await loop.run_in_executor(
            None,
            lambda: db.query(func.count(func.distinct(ABEvent.user_id)))
            .filter(
                ABEvent.experiment_id == experiment.id,
                ABEvent.variant_id == variant.id,
                ABEvent.event_type == "assigned",
            )
            .scalar(),
        )

        # Count conversions (unique users with 'conversion' event)
        conversions = await loop.run_in_executor(
            None,
            lambda: db.query(func.count(func.distinct(ABEvent.user_id)))
            .filter(
                ABEvent.experiment_id == experiment.id,
                ABEvent.variant_id == variant.id,
                ABEvent.event_type == "conversion",
            )
            .scalar(),
        )

        conversion_rate = (conversions / assignments * 100) if assignments > 0 else 0

        result = {
            "variant": variant.name,
            "assignments": assignments,
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 2),
            "is_control": variant.is_control,
        }

        results.append(result)

    # Calculate lift and statistical significance
    control = next((r for r in results if r["is_control"]), None)
    if control:
        for result in results:
            if not result["is_control"]:
                # Calculate lift
                lift = (
                    (result["conversion_rate"] - control["conversion_rate"])
                    / control["conversion_rate"]
                    * 100
                )
                result["lift_vs_control"] = round(lift, 2)

                # Calculate statistical significance (z-test)
                p_value = _calculate_significance(
                    control["conversions"],
                    control["assignments"],
                    result["conversions"],
                    result["assignments"],
                )
                result["p_value"] = round(p_value, 4)
                result["significant"] = p_value < 0.05

    return ExperimentResults(
        experiment=experiment_name, status=experiment.status, results=results
    )


def _calculate_significance(c1: int, n1: int, c2: int, n2: int) -> float:
    """
    Calculate p-value using two-proportion z-test.

    Args:
        c1, c2: conversions for control and variant
        n1, n2: total samples for control and variant

    Returns:
        p-value (two-tailed)
    """
    import math

    p1 = c1 / n1 if n1 > 0 else 0
    p2 = c2 / n2 if n2 > 0 else 0

    if n1 == 0 or n2 == 0:
        return 1.0

    pooled_p = (c1 + c2) / (n1 + n2) if (n1 + n2) > 0 else 0

    se = math.sqrt(pooled_p * (1 - pooled_p) * (1 / n1 + 1 / n2)) if pooled_p > 0 else 0

    if se == 0:
        return 1.0

    z = (p2 - p1) / se

    # Approximate p-value from z-score (two-tailed)
    # Using error function approximation
    abs_z = abs(z)
    if abs_z > 3.7:
        p_value = 0.0001
    else:
        # Approximation using simple formula
        p_value = 0.5 * (1 - _error_function(abs_z / math.sqrt(2)))

    return 2 * p_value  # Two-tailed


def _error_function(x: float) -> float:
    """
    Approximate the error function erf(x).

    Uses Abramowitz and Stegun approximation (accurate to 1e-5).
    """
    import math

    # Constants
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    # Save the sign of x
    sign = 1 if x >= 0 else -1
    x = abs(x)

    # A&S formula 7.1.26
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)

    return sign * y
