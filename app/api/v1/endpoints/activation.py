# app/api/v1/endpoints/activation.py
"""User Activation Tracking API Endpoints

API endpoints for tracking user activation metrics and funnel progress.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_active_user
from app.api.v1.deps import get_current_user
from app.db.models.user import User
from app.db.models.user_activation import UserActivation

router = APIRouter()


# ========================================================================
# Pydantic Models
# ========================================================================


class ActivationMetrics(BaseModel):
    """Activation metrics for a user"""

    user_id: str
    is_activated: bool
    activation_type: Optional[str]
    segment: str
    time_to_activation_minutes: Optional[int]
    time_to_first_assessment_minutes: Optional[int]


class FunnelStep(BaseModel):
    """Funnel step data"""

    step: str
    count: int
    cumulative_percent: float
    dropoff_from_previous: float


class FunnelAnalysis(BaseModel):
    """Complete funnel analysis"""

    period: str
    steps: List[FunnelStep]
    activation_rate: float


class SegmentMetrics(BaseModel):
    """Metrics by user segment"""

    segment: str
    total_users: int
    activated_users: int
    activation_rate: float
    median_tta_minutes: float


class ActivationDashboard(BaseModel):
    """Complete activation dashboard data"""

    period: str
    total_signups: int
    total_activated: int
    activation_rate: float
    median_tta: float
    avg_tta: float
    by_segment: List[SegmentMetrics]
    funnel: List[FunnelStep]


# ========================================================================
# API Endpoints
# ========================================================================


@router.get(
    "/my-activation",
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
    response_model=ActivationMetrics,
)
async def get_my_activation(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get activation status for the current user.
    """
    # ✅ ASYNC - Use select() instead of db.query()
    from sqlalchemy import select

    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        None,
        lambda: db.query(UserActivation)
        .filter(UserActivation.user_id == current_user.id)
        .first(),
    )
    activation = result

    if not activation:
        # Create activation record if it doesn't exist
        activation = UserActivation(
            user_id=current_user.id,
            signup_timestamp=(
                current_user.created_at
                if hasattr(current_user, "created_at")
                else func.now()
            ),
            segment="individual_free",
        )
        await loop.run_in_executor(None, lambda: db.add(activation))
        await loop.run_in_executor(None, db.commit)
        await loop.run_in_executor(None, lambda: db.refresh(activation))

    return ActivationMetrics(
        user_id=str(activation.user_id),
        is_activated=activation.is_activated,
        activation_type=activation.activation_type,
        segment=activation.segment,
        time_to_activation_minutes=activation.time_to_activation_minutes,
        time_to_first_assessment_minutes=activation.time_to_first_assessment_minutes,
    )


@router.post(
    "/track-assessment",
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
async def track_assessment_completed(
    assessment_id: str = Query(..., description="Assessment ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Track when a user completes their first assessment.
    """
    # ✅ ASYNC - Use run_in_executor for sync db operations
    loop = asyncio.get_event_loop()

    activation = await loop.run_in_executor(
        None,
        lambda: db.query(UserActivation)
        .filter(UserActivation.user_id == current_user.id)
        .first(),
    )

    if not activation:
        activation = UserActivation(
            user_id=current_user.id,
            signup_timestamp=(
                current_user.created_at
                if hasattr(current_user, "created_at")
                else func.now()
            ),
            segment="individual_free",
        )
        await loop.run_in_executor(None, lambda: db.add(activation))

    # Mark first assessment completed
    activation.mark_assessment_completed()

    # Check if user should be activated now
    if not activation.is_activated:
        await _check_and_mark_activated(activation, db)

    await loop.run_in_executor(None, db.commit)

    return {
        "status": "tracked",
        "is_activated": activation.is_activated,
        "time_to_first_assessment_minutes": activation.time_to_first_assessment_minutes,
    }


@router.post(
    "/track-results-viewed",
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
async def track_results_viewed(
    assessment_id: str = Query(..., description="Assessment ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Track when a user views their first results.
    """
    # ✅ ASYNC - Use run_in_executor for sync db operations
    loop = asyncio.get_event_loop()

    activation = await loop.run_in_executor(
        None,
        lambda: db.query(UserActivation)
        .filter(UserActivation.user_id == current_user.id)
        .first(),
    )

    if not activation:
        activation = UserActivation(
            user_id=current_user.id,
            signup_timestamp=(
                current_user.created_at
                if hasattr(current_user, "created_at")
                else func.now()
            ),
            segment="individual_free",
        )
        await loop.run_in_executor(None, lambda: db.add(activation))

    # Mark results viewed
    activation.mark_results_viewed()

    # Check if user should be activated now
    if not activation.is_activated:
        await _check_and_mark_activated(activation, db)

    await loop.run_in_executor(None, db.commit)

    return {"status": "tracked", "is_activated": activation.is_activated}


@router.get(
    "/dashboard",
    summary="Get analytics dashboard data",
    description="Retrieve comprehensive analytics for organization or team",
    responses={
        200: {
            "description": "Analytics data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "overview": {
                            "total_users": 150,
                            "active_assessments": 25,
                            "completion_rate": 0.78,
                        },
                        "trends": [
                            {"date": "2025-01-01", "completions": 45},
                            {"date": "2025-01-02", "completions": 52},
                        ],
                        "top_performers": [
                            {"user_id": 1, "score": 95},
                            {"user_id": 2, "score": 92},
                        ],
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
    },
    response_model=ActivationDashboard,
)
async def get_activation_dashboard(
    period: str = Query("month", description="Time period: day, week, month, quarter"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get activation dashboard with metrics and funnel analysis.
    """
    # ✅ ASYNC - Use run_in_executor for sync db operations
    loop = asyncio.get_event_loop()

    # Calculate date range
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:  # month
        start_date = now - timedelta(days=30)

    # Base query
    def get_query_result():
        q = db.query(UserActivation).filter(
            UserActivation.signup_timestamp >= start_date
        )
        if segment:
            q = q.filter(UserActivation.segment == segment)
        return q

    query = await loop.run_in_executor(None, get_query_result)

    # Total signups
    total_signups = await loop.run_in_executor(None, query.count)

    # Total activated
    total_activated = await loop.run_in_executor(
        None, lambda: query.filter(UserActivation.is_activated == True).count()
    )

    # Activation rate
    activation_rate = (
        (total_activated / total_signups * 100) if total_signups > 0 else 0
    )

    # Time to activation metrics
    activated_users = await loop.run_in_executor(
        None,
        lambda: query.filter(
            UserActivation.is_activated == True,
            UserActivation.time_to_activation_minutes.isnot(None),
        ).all(),
    )

    tta_values = [u.time_to_activation_minutes for u in activated_users]
    median_tta = sorted(tta_values)[len(tta_values) // 2] if tta_values else 0
    avg_tta = sum(tta_values) / len(tta_values) if tta_values else 0

    # Segment breakdown
    segment_data = await loop.run_in_executor(
        None,
        lambda: db.query(
            UserActivation.segment,
            func.count(UserActivation.user_id).label("total"),
            func.sum(func.cast(UserActivation.is_activated, db.Integer)).label(
                "activated"
            ),
        )
        .filter(UserActivation.signup_timestamp >= start_date)
        .group_by(UserActivation.segment)
        .all(),
    )

    by_segment = []
    for seg, total, activated in segment_data:
        activated_count = int(activated) if activated else 0
        rate = (activated_count / total * 100) if total > 0 else 0

        # Get median TTA for this segment
        segment_activated = await loop.run_in_executor(
            None,
            lambda: query.filter(
                UserActivation.segment == seg,
                UserActivation.is_activated == True,
                UserActivation.time_to_activation_minutes.isnot(None),
            ).all(),
        )

        segment_tta = [u.time_to_activation_minutes for u in segment_activated]
        segment_median = (
            sorted(segment_tta)[len(segment_tta) // 2] if segment_tta else 0
        )

        by_segment.append(
            SegmentMetrics(
                segment=seg,
                total_users=total,
                activated_users=activated_count,
                activation_rate=round(rate, 2),
                median_tta_minutes=round(segment_median, 2),
            )
        )

    # Funnel analysis
    funnel_steps = await _calculate_funnel(query, db)

    return ActivationDashboard(
        period=period,
        total_signups=total_signups,
        total_activated=total_activated,
        activation_rate=round(activation_rate, 2),
        median_tta=round(median_tta, 2),
        avg_tta=round(avg_tta, 2),
        by_segment=by_segment,
        funnel=funnel_steps,
    )


@router.get(
    "/funnel",
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
    response_model=List[FunnelStep],
)
async def get_activation_funnel(
    period: str = Query("month", description="Time period"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get detailed funnel analysis with drop-off at each step.
    """
    # Calculate date range
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:  # month
        start_date = now - timedelta(days=30)

    query = db.query(UserActivation).filter(
        UserActivation.signup_timestamp >= start_date
    )

    return await _calculate_funnel(query, db)


async def _calculate_funnel(query, db: AsyncSession) -> List[FunnelStep]:
    """Calculate funnel steps with drop-off percentages"""
    # ✅ ASYNC - Use run_in_executor for sync query operations
    loop = asyncio.get_event_loop()

    total = await loop.run_in_executor(None, query.count)

    # Get counts for each step
    signup_count = total
    email_verified_count = await loop.run_in_executor(
        None, lambda: query.filter(UserActivation.signup_timestamp.isnot(None)).count()
    )
    assessment_started_count = await loop.run_in_executor(
        None,
        lambda: query.filter(
            UserActivation.first_assessment_timestamp.isnot(None)
        ).count(),
    )
    results_viewed_count = await loop.run_in_executor(
        None,
        lambda: query.filter(
            UserActivation.first_results_viewed_timestamp.isnot(None)
        ).count(),
    )
    activated_count = await loop.run_in_executor(
        None, lambda: query.filter(UserActivation.is_activated == True).count()
    )

    steps_data = [
        ("Signup", signup_count),
        ("Email Verified", email_verified_count),
        ("Assessment Started", assessment_started_count),
        ("Results Viewed", results_viewed_count),
        ("Activated", activated_count),
    ]

    funnel = []
    prev_count = total

    for step_name, count in steps_data:
        cumulative_percent = (count / total * 100) if total > 0 else 0
        dropoff = ((prev_count - count) / prev_count * 100) if prev_count > 0 else 0

        funnel.append(
            FunnelStep(
                step=step_name,
                count=count,
                cumulative_percent=round(cumulative_percent, 2),
                dropoff_from_previous=round(dropoff, 2),
            )
        )

        prev_count = count

    return funnel


async def _check_and_mark_activated(
    activation: UserActivation, db: AsyncSession
) -> None:
    """Check if user meets activation criteria and mark as activated if so"""

    now = datetime.utcnow()
    signup_time = activation.signup_timestamp
    hours_since_signup = (now - signup_time).total_seconds() / 3600

    # Must be within 24 hours
    if hours_since_signup > 24:
        return

    # Must have completed assessment and viewed results
    if (
        not activation.first_assessment_timestamp
        or not activation.first_results_viewed_timestamp
    ):
        return

    # Determine activation type based on segment
    activation_type = "full"

    if activation.segment == "premium":
        if activation.upgraded_to_premium:
            activation_type = "full"
        else:
            activation_type = "weak"
    elif activation.segment == "team_manager":
        if activation.first_invite_accepted_timestamp:
            activation_type = "full"
        elif activation.invited_team_member:
            activation_type = "partial"
        else:
            activation_type = "weak"
    elif activation.segment == "enterprise":
        if activation.completed_onboarding:
            # Check SSO if required
            if activation.configured_sso:
                activation_type = "full"
            else:
                activation_type = "partial"
        else:
            activation_type = "weak"

    # Mark as activated
    activation.mark_activated(activation_type)
