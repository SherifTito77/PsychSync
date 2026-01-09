# app/api/v1/endpoints/onboarding.py
# FastAPI endpoints for value-first onboarding experience
from datetime import datetime
import json
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_current_user_optional
from app.core.database import get_async_db as get_db
from app.core.input_validation import validate_input
from app.core.rate_limiter import RateLimiter
from app.db.models.user import User
from app.schemas.onboarding import (
    OnboardingAnalyticsEvent,
    QuickAssessmentRequest,
    QuickAssessmentResponse,
    TeamInsightRequest,
    TeamInsightResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.onboarding_service import OnboardingService

router = APIRouter()
onboarding_service = OnboardingService()
analytics_service = AnalyticsService()


@router.post("/quick-assessment", response_model=QuickAssessmentResponse)
@RateLimiter(limit=20, window_seconds=60)  # 20 requests per minute
async def quick_assessment(
    request: QuickAssessmentRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Generate instant team insights from role and challenge (no auth required).
    This is the core of the value-first onboarding experience.
    """
    try:
        # Input validation and sanitization
        validate_input(request.dict())

        # Get client IP for rate limiting and analytics
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        # Track analytics event (async, non-blocking)
        await analytics_service.track_onboarding_event(
            event_type="quick_assessment_started",
            user_id=current_user.id if current_user else None,
            session_id=request.session_id or str(uuid.uuid4()),
            data={
                "role": request.role.value if hasattr(request.role, "value") else str(request.role),
                "challenge": request.challenge.value
                if hasattr(request.challenge, "value")
                else str(request.challenge),
                "team_size": request.team_size,
                "client_ip": client_ip,
                "user_agent": user_agent[:200],  # Truncate for security
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Generate instant insights
        insights = await onboarding_service.generate_quick_insights(
            role=request.role,
            challenge=request.challenge,
            team_size=request.team_size,
            industry=request.industry,
            user_id=current_user.id if current_user else None,
        )

        # Track completion event
        await analytics_service.track_onboarding_event(
            event_type="quick_assessment_completed",
            user_id=current_user.id if current_user else None,
            session_id=request.session_id or str(uuid.uuid4()),
            data={
                "role": request.role,
                "challenge": request.challenge,
                "insights_generated": len(insights.recommendations),
                "conversion_probability": insights.conversion_probability,
            },
        )

        return QuickAssessmentResponse(
            success=True,
            insights=insights,
            next_steps=[
                "Create your account to save these insights",
                "Set up your team for detailed analysis",
                "Take the full personality assessment",
            ],
            value_proposition=f"As a {request.role}, you can potentially {insights.primary_benefit}",
            estimated_time_to_value=insights.estimated_time_to_value,
        )

    except Exception as e:
        await analytics_service.track_onboarding_event(
            event_type="quick_assessment_error",
            user_id=current_user.id if current_user else None,
            session_id=request.session_id or str(uuid.uuid4()),
            data={"error": str(e), "role": request.role, "challenge": request.challenge},
        )
        raise HTTPException(status_code=500, detail=f"Assessment generation failed: {e!s}")


@router.post("/team-insights", response_model=TeamInsightResponse)
@RateLimiter(limit=30, window_seconds=60)  # 30 requests per minute for authenticated users
async def get_team_insights(
    request: TeamInsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    ),  # Require authentication for team insights
):
    """
    Generate deeper team insights for registered users.
    This follows the quick assessment with more detailed analysis.
    """
    try:
        # Input validation
        if request.team_id:
            validate_input({"team_id": request.team_id})

        # Validate team composition data size to prevent DoS
        if request.team_composition and len(json.dumps(request.team_composition)) > 10000:
            raise HTTPException(status_code=400, detail="Team composition data too large")
        insights = await onboarding_service.generate_detailed_team_insights(
            user_id=current_user.id,
            team_id=request.team_id,
            assessment_data=request.assessment_data,
            team_composition=request.team_composition,
        )

        await analytics_service.track_onboarding_event(
            event_type="team_insights_generated",
            user_id=current_user.id,
            session_id=request.session_id,
            data={
                "team_id": request.team_id,
                "insights_count": len(insights.detailed_insights),
                "recommendations_count": len(insights.action_items),
            },
        )

        return TeamInsightResponse(
            success=True,
            team_profile=insights.team_profile,
            detailed_insights=insights.detailed_insights,
            action_items=insights.action_items,
            predicted_outcomes=insights.predicted_outcomes,
            implementation_roadmap=insights.implementation_roadmap,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Team insights generation failed: {e!s}")


@router.post("/track-conversion")
@RateLimiter(limit=100, window_seconds=60)  # Higher limit for analytics
async def track_conversion_event(
    event: OnboardingAnalyticsEvent,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Track onboarding conversion events for analytics and optimization.
    """
    try:
        # Input validation and size limits
        if len(event.event_type) > 100:
            raise HTTPException(status_code=400, detail="Event type too long")

        if event.data and len(json.dumps(event.data)) > 5000:
            raise HTTPException(status_code=400, detail="Event data too large")

        # Get client info for analytics
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")[:200]
        await analytics_service.track_onboarding_event(
            event_type=event.event_type,
            user_id=current_user.id if current_user else None,
            session_id=event.session_id,
            data={**(event.data or {}), "client_ip": client_ip, "user_agent": user_agent},
        )

        return {"success": True, "message": "Event tracked successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics tracking failed: {e!s}")


@router.get("/onboarding-status")
@RateLimiter(limit=60, window_seconds=60)
async def get_onboarding_status(
    http_request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's onboarding progress and recommended next steps.
    """
    if not current_user:
        return {
            "is_authenticated": False,
            "onboarding_complete": False,
            "recommended_actions": [
                "Try the quick assessment to see instant value",
                "Create an account to save your insights",
            ],
        }

    try:
        status = await onboarding_service.get_onboarding_status(current_user.id)
        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get onboarding status: {e!s}")


@router.post("/setup-wizard")
@RateLimiter(limit=20, window_seconds=60)
async def setup_wizard_step(
    step_data: dict[str, Any],
    http_request: Request,
    current_user: User = Depends(get_current_active_user),  # Require authentication
    db: AsyncSession = Depends(get_db),
):
    """
    Handle progressive setup wizard steps.
    """
    try:
        # Input validation and size limits
        if not isinstance(step_data, dict):
            raise HTTPException(status_code=400, detail="Step data must be a JSON object")

        if len(json.dumps(step_data)) > 8000:
            raise HTTPException(status_code=400, detail="Step data too large")

        step = step_data.get("step")
        if step and len(str(step)) > 50:
            raise HTTPException(status_code=400, detail="Step name too long")

        data = step_data.get("data", {})

        result = await onboarding_service.process_setup_step(
            user_id=current_user.id, step=step, data=data
        )

        await analytics_service.track_onboarding_event(
            event_type="setup_step_completed",
            user_id=current_user.id,
            session_id=step_data.get("session_id"),
            data={"step": step, "success": result.get("success", False)},
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup wizard step failed: {e!s}")


@router.get("/value-metrics")
@RateLimiter(limit=30, window_seconds=60)
async def get_value_metrics(
    http_request: Request,
    current_user: User = Depends(get_current_active_user),  # Require authentication
    db: AsyncSession = Depends(get_db),
):
    """
    Get real-time value metrics for the user's team (post-onboarding).
    """
    try:
        metrics = await onboarding_service.calculate_value_metrics(current_user.id)
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate value metrics: {e!s}")
