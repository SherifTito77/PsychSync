"""
Growth Analytics API Endpoints
Advanced analytics for conversion optimization, user behavior analysis, and growth forecasting
"""

from datetime import datetime, timedelta
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.models.user import User
from app.middleware.rate_limiter import check_rate_limit
from app.services.growth_analytics_service import (
    ConversionEvent,
    ConversionEventType,
    UserSegment,
    growth_analytics_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics/growth", tags=["Growth Analytics"])


@check_rate_limit(identifier="public", limit_name="public")
@router.post("/events/track")
async def track_conversion_event(
    user_id: str,
    event_type: ConversionEventType,
    event_data: dict[str, Any],
    funnel_stage: str | None = None,
    attribution_data: dict[str, Any] | None = None,
    revenue_impact: float = 0.0,
    current_user: User = Depends(get_current_user),
):
    """
    Track conversion event for analytics
    """
    try:
        # Verify user can track events for this user (admin or self)
        if not current_user.is_admin and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to track events for this user",
            )

        # Create conversion event
        event = ConversionEvent(
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            event_data=event_data,
            funnel_stage=funnel_stage or "unknown",
            attribution_data=attribution_data or {},
            revenue_impact=revenue_impact,
        )

        # Track event
        result = await growth_analytics_service.track_conversion_event(event)

        return {
            "success": True,
            "event_id": result["event_id"],
            "user_segment": result["user_segment"].value,
            "triggers_activated": result["triggers_activated"],
            "real_time_insights": result["real_time_insights"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track conversion event: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track conversion event: {e!s}",
        ) from e


@router.get("/behavior/analyze")
async def analyze_user_behavior(
    user_id: str | None = None,
    segment: UserSegment | None = None,
    date_range_days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze comprehensive user behavior patterns
    """
    try:
        # Verify user has analytics permissions (admin or data analyst role)
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for behavior analytics",
            )

        # Analyze behavior patterns
        analysis = await growth_analytics_service.analyze_user_behavior_patterns(
            user_id=user_id, segment=segment, date_range_days=date_range_days
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze user behavior: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze user behavior: {e!s}",
        ) from e


@router.post("/funnel/optimize")
async def optimize_conversion_funnel(
    funnel_name: str,
    optimization_goals: list[str] | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze and optimize conversion funnel performance
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for funnel optimization",
            )

        # Optimize funnel
        optimization = await growth_analytics_service.optimize_conversion_funnel(
            funnel_name=funnel_name, optimization_goals=optimization_goals
        )

        return optimization

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to optimize conversion funnel {funnel_name}: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize conversion funnel: {e!s}",
        ) from e


@router.get("/forecast/growth")
async def forecast_growth(
    forecast_period_days: int = 90,
    scenarios: list[str] | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive growth forecasts
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for growth forecasting",
            )

        # Validate forecast period
        if forecast_period_days < 7 or forecast_period_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Forecast period must be between 7 and 365 days",
            )

        # Generate growth forecast
        forecast = await growth_analytics_service.forecast_growth(
            forecast_period_days=forecast_period_days, scenarios=scenarios
        )

        return forecast

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate growth forecast: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate growth forecast: {e!s}",
        ) from e


@router.get("/clv/calculate")
async def calculate_customer_lifetime_value(
    segmentation: bool = True,
    predictive: bool = True,
    current_user: User = Depends(get_current_user),
):
    """
    Calculate comprehensive Customer Lifetime Value (CLV) metrics
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for CLV calculations",
            )

        # Calculate CLV
        clv_analysis = await growth_analytics_service.calculate_customer_lifetime_value(
            segmentation=segmentation, predictive=predictive
        )

        return clv_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate customer lifetime value: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate customer lifetime value: {e!s}",
        ) from e


@router.get("/dashboard/growth")
async def get_growth_dashboard(
    date_range_days: int = 30,
    include_forecasts: bool = True,
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive growth analytics dashboard
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for growth dashboard",
            )

        # Validate date range
        if date_range_days < 1 or date_range_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range must be between 1 and 365 days",
            )

        # Generate dashboard
        dashboard = await growth_analytics_service.generate_comprehensive_growth_dashboard(
            date_range_days=date_range_days, include_forecasts=include_forecasts
        )

        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate growth dashboard: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate growth dashboard: {e!s}",
        ) from e


@router.get("/segments/list")
async def list_user_segments(current_user: User = Depends(get_current_user)):
    """
    Get available user segments and their definitions
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for segment information",
            )

        segments = {}
        for segment_enum, segment_def in growth_analytics_service.user_segments.items():
            segments[segment_enum.value] = {
                "name": segment_enum.value,
                "criteria": segment_def["criteria"],
                "characteristics": segment_def["characteristics"],
                "recommended_strategies": segment_def["strategies"],
            }

        return {"available_segments": segments, "total_segments": len(segments)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list user segments: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user segments: {e!s}",
        ) from e


@router.get("/funnels/list")
async def list_conversion_funnels(current_user: User = Depends(get_current_user)):
    """
    Get available conversion funnels and their definitions
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for funnel information",
            )

        funnels = {}
        for funnel_name, funnel_def in growth_analytics_service.funnel_definitions.items():
            funnels[funnel_name] = {
                "name": funnel_def["name"],
                "description": funnel_def.get("description", ""),
                "stages": funnel_def["stages"],
                "success_metric": funnel_def["success_metric"],
                "target_conversion_rate": funnel_def["target_conversion_rate"],
            }

        return {"available_funnels": funnels, "total_funnels": len(funnels)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list conversion funnels: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversion funnels: {e!s}",
        ) from e


@router.get("/metrics/acquisition")
async def get_acquisition_metrics(
    date_range_days: int = 30,
    channel: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed acquisition metrics
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for acquisition metrics",
            )

        # Calculate acquisition metrics
        metrics = await growth_analytics_service._calculate_acquisition_metrics(date_range_days)

        # Filter by channel if specified
        if channel:
            metrics["channel_breakdown"] = {channel: metrics.get("channels", {}).get(channel, {})}

        return {
            "period": {
                "start": (datetime.utcnow() - timedelta(days=date_range_days)).isoformat(),
                "end": datetime.utcnow().isoformat(),
                "days": date_range_days,
            },
            "metrics": metrics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get acquisition metrics: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get acquisition metrics: {e!s}",
        ) from e


@router.get("/metrics/engagement")
async def get_engagement_metrics(
    date_range_days: int = 30,
    segment: UserSegment | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed engagement metrics
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for engagement metrics",
            )

        # Calculate engagement metrics
        metrics = await growth_analytics_service._calculate_engagement_metrics(date_range_days)

        return {
            "period": {
                "start": (datetime.utcnow() - timedelta(days=date_range_days)).isoformat(),
                "end": datetime.utcnow().isoformat(),
                "days": date_range_days,
            },
            "segment_filter": segment.value if segment else "all_users",
            "metrics": metrics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get engagement metrics: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement metrics: {e!s}",
        ) from e


@router.post("/experiments/start")
async def start_ab_test(
    test_name: str,
    hypothesis: str,
    variant_a_config: dict[str, Any],
    variant_b_config: dict[str, Any],
    traffic_split: float = 0.5,
    sample_size_target: int = 1000,
    current_user: User = Depends(get_current_user),
):
    """
    Start new A/B test for conversion optimization
    """
    try:
        # Verify user has analytics permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to start A/B tests",
            )

        # Validate inputs
        if not test_name or not hypothesis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test name and hypothesis are required",
            )

        if traffic_split <= 0 or traffic_split >= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Traffic split must be between 0 and 1 (exclusive)",
            )

        # Create A/B test
        from app.services.growth_marketing_service import growth_service

        ab_test = await growth_service.create_a_b_test(
            test_name=test_name,
            hypothesis=hypothesis,
            variant_a_config=variant_a_config,
            variant_b_config=variant_b_config,
            traffic_split=traffic_split,
        )

        # Update sample size target
        ab_test["sample_size_target"] = sample_size_target

        return {
            "success": True,
            "ab_test": ab_test,
            "monitoring_dashboard": f"/analytics/ab-tests/{ab_test['test_id']}",
            "estimated_duration": f"{sample_size_target // 10} days at 10 users/day",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start A/B test: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start A/B test: {e!s}",
        ) from e
