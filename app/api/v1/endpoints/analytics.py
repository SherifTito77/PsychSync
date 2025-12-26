# app/api/v1/endpoints/analytics.py

from typing import Optional, List, Dict, Any

from app.middleware.rate_limiter import check_rate_limit
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import (
    get_db,
    get_current_active_user,
    get_current_admin_user
)
from app.db.models.user import User

# --- CORRECTED IMPORTS ---
# from app.services.Analytics_service import analytics_service as AnalyticsService
from app.services import assessment_service as AssessmentService
from app.services import team_service as TeamService
from app.services.analytics_dashboard import AnalyticsDashboard, TimePeriod
from app.core.api_utils import cache_response
# --- END CORRECTED IMPORTS ---

router = APIRouter()



@check_rate_limit(identifier="public", endpoint_type="public")
@router.get("/assessments/{assessment_id}")
def get_assessment_analytics(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for a specific assessment.
    Requires assessment creator or team admin permission.
    """
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check permission
    if assessment.created_by_id != current_user.id:
        if assessment.team_id:
            if not TeamService.is_admin_or_owner(db, team_id=assessment.team_id, user_id=current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view these analytics"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view these analytics"
            )
    
    analytics = AnalyticsService.get_assessment_an
@check_rate_limit(identifier="public", endpoint_type="public")
alytics(db, assessment_id=assessment_id)
    return analytics


@router.get("/users/me")
def get_my_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics fo
@check_rate_limit(identifier="public", endpoint_type="public")
r current user.
    """
    analytics = AnalyticsService.get_user_analytics(db, user_id=current_user.id)
    return analytics


@router.get("/users/{user_id}")
def get_user_analytics(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for a specific user.
    User can only view their own analytics unless they're an admin.
    """
    if user_id != current_user.id:
        # This import is already correct, which is great!
        import app.services.user_service as user_service
        if not user_service.is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own analytics"
            )
    
    analytics = AnalyticsService.get_user_analytics(db, user_id=user_id)
    return analytics


@router.get("/teams/{team_id}")
def get_team_analytics(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for a team.
    Requires team membership.
    """
    if not TeamService.is_member(db, team_id=team_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a team member to view analytics"
        )
    
    analytics = AnalyticsService.get_team_analytics(db, team_id=team_id)
    return analytics


@router.get("/system")
def get_system_analytics(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get system-wide analytics.
    Admin only.
    """
    analytics = AnalyticsService.get_system_analytics(db)
    return analytics


# Pydantic models for comprehensive dashboard analytics
class DashboardOverviewResponse(BaseModel):
    """Response model for dashboard overview."""
    period: str
    generated_at: str
    user_metrics: Dict[str, Any]
    assessment_metrics: Dict[str, Any]
    team_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]
    business_metrics: Dict[str, Any]
    summary: Dict[str, Any]

class TimeSeriesRequest(BaseModel):
    """Request model for time series data."""
    metric: str = Field(..., description="Metric name to retrieve")
    time_period: TimePeriod = Field(TimePeriod.LAST_30_DAYS, description="Time period for data")
    granularity: str = Field("day", description="Data granularity: hour, day, week, month")

class TimeSeriesResponse(BaseModel):
    """Response model for time series data."""
    metric: str
    period: str
    granularity: str
    data_points: List[Dict[str, Any]]
    summary: Dict[str, float]

class InsightsResponse(BaseModel):
    """Response model for analytics insights."""
    user_insights: List[Dict[str, Any]]
    assessment_insights: List[Dict[str, Any]]
    team_insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    predictions: Dict[str, Any]

@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
@cache_response(expire_seconds=300, key_prefix="dashboard_overview", vary_on=["time_period", "organization_id", "team_id"])
async def get_dashboard_overview(
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period for data"),
    organization_id: Optional[str] = Query(None, description="Organization ID filter"),
    team_id: Optional[str] = Query(None, description="Team ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive dashboard overview with key metrics across all categories.

    - **time_period**: Time period for the analytics data
    - **organization_id**: Filter by specific organization (admin only)
    - **team_id**: Filter by specific team

    Returns aggregated metrics for users, assessments, teams, system performance, and business KPIs.
    """
    try:
        # Check permissions for organization/team filtering
        if organization_id and not current_user.is_admin:
            if current_user.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this organization's analytics"
                )

        if team_id and not current_user.is_admin:
            # Verify user belongs to the team
            user_teams = [str(team.id) for team in current_user.teams]
            if team_id not in user_teams:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this team's analytics"
                )

        # Initialize analytics service
        dashboard_service = AnalyticsDashboard(db)

        # Get dashboard overview
        overview = await dashboard_service.get_dashboard_overview(
            time_period=time_period,
            organization_id=organization_id,
            team_id=team_id
        )

        return DashboardOverviewResponse(**overview)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard overview: {str(e)}"
        )

@router.post("/dashboard/timeseries", response_model=TimeSeriesResponse)
async def get_time_series_data(
    request: TimeSeriesRequest,
    organization_id: Optional[str] = Query(None, description="Organization ID filter"),
    team_id: Optional[str] = Query(None, description="Team ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get time series data for a specific metric.

    - **metric**: Name of the metric to retrieve
    - **time_period**: Time period for the data
    - **granularity**: Data aggregation level (hour, day, week, month)

    Returns time series data with trend analysis and summary statistics.
    """
    try:
        # Validate metric name
        valid_metrics = [
            'active_users', 'completed_assessments', 'api_requests', 'revenue_mrr',
            'user_retention_rate', 'assessment_completion_rate', 'team_collaboration_score',
            'system_uptime', 'response_time_avg', 'error_rate'
        ]

        if request.metric not in valid_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric. Valid metrics: {', '.join(valid_metrics)}"
            )

        # Check permissions
        if organization_id and not current_user.is_admin:
            if current_user.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this organization's analytics"
                )

        # Initialize analytics service
        dashboard_service = AnalyticsDashboard(db)

        # Get time series data
        time_series = await dashboard_service.get_time_series_data(
            metric=request.metric,
            time_period=request.time_period,
            granularity=request.granularity,
            organization_id=organization_id,
            team_id=team_id
        )

        return TimeSeriesResponse(**time_series)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating time series data: {str(e)}"
        )

@router.get("/dashboard/insights", response_model=InsightsResponse)
async def get_analytics_insights(
    time_period: TimePeriod = Query(TimePeriod.LAST_30_DAYS, description="Time period for insights"),
    organization_id: Optional[str] = Query(None, description="Organization ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered insights and recommendations from analytics data.

    - **time_period**: Time period for analysis
    - **organization_id**: Organization filter (admin only)

    Returns insights, recommendations, anomalies, and predictions based on data analysis.
    """
    try:
        # Check permissions
        if organization_id and not current_user.is_admin:
            if current_user.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this organization's insights"
                )

        # Initialize analytics service
        dashboard_service = AnalyticsDashboard(db)

        # Get insights
        insights = await dashboard_service.get_analytics_insights(
            time_period=time_period,
            organization_id=organization_id
        )

        return InsightsResponse(**insights)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analytics insights: {str(e)}"
        )

@router.get("/metrics/available")
async def get_available_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all available metrics for analytics queries.

    Returns categorized list of metrics that can be queried through the API.
    """
    try:
        available_metrics = {
            "user_metrics": {
                "total_users": "Total number of registered users",
                "active_users": "Users with activity in the period",
                "new_users": "New user registrations in the period",
                "user_retention_rate": "Percentage of users retained from previous period",
                "user_engagement_score": "Average engagement score (1-10)",
                "average_session_duration": "Average session duration in minutes",
                "user_growth_rate": "User growth rate percentage"
            },
            "assessment_metrics": {
                "total_assessments": "Total number of assessments created",
                "completed_assessments": "Number of completed assessments",
                "assessment_completion_rate": "Percentage of assessments completed",
                "average_assessment_score": "Average score across completed assessments",
                "assessment_completion_time": "Average time to complete assessments",
                "popular_assessments": "Most frequently used assessments"
            },
            "team_metrics": {
                "total_teams": "Total number of teams",
                "active_teams": "Teams with recent activity",
                "average_team_size": "Average number of members per team",
                "team_collaboration_score": "Average collaboration score (1-10)",
                "team_performance_index": "Overall team performance index",
                "cross_team_collaboration": "Cross-team collaboration rate"
            },
            "system_metrics": {
                "api_requests": "Total API requests in the period",
                "response_time_avg": "Average API response time in milliseconds",
                "error_rate": "Percentage of requests resulting in errors",
                "uptime_percentage": "System uptime percentage",
                "database_connections": "Average active database connections",
                "cache_hit_rate": "Cache hit rate percentage",
                "storage_usage": "Storage utilization percentage"
            },
            "business_metrics": {
                "revenue_mrr": "Monthly recurring revenue",
                "conversion_rate": "User conversion rate percentage",
                "churn_rate": "Customer churn rate percentage",
                "customer_acquisition_cost": "Average cost to acquire a customer",
                "lifetime_value": "Customer lifetime value",
                "monthly_growth_rate": "Monthly growth rate percentage",
                "feature_adoption_rate": "Feature adoption rate percentage",
                "customer_satisfaction": "Customer satisfaction score (1-10)"
            }
        }

        return {
            "categories": available_metrics,
            "time_periods": [period.value for period in TimePeriod],
            "granularities": ["hour", "day", "week", "month"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving available metrics: {str(e)}"
        )