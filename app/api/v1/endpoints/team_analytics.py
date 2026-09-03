"""
Team Analytics API Endpoints
Provides aggregate email analytics for teams and organizations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.team_analytics_service import team_analytics_service
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.get("/team/{team_id}")
async def get_team_analytics(
    team_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive analytics for a specific team

    Args:
        team_id: Team ID to analyze
        days: Number of days to look back (default: 30)
        current_user: Authenticated user
        db: Database session

    Returns:
        Team analytics with member breakdown and aggregate metrics
    """
    try:
        analytics = await team_analytics_service.get_team_analytics(
            db=db, team_id=team_id, days=days
        )

        return {"success": True, "analytics": analytics}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch team analytics: {str(e)}"
        )


@router.post("/compare-teams")
async def compare_teams(
    team_ids: List[int],
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare analytics across multiple teams

    Args:
        team_ids: List of team IDs to compare
        days: Number of days to analyze
        current_user: Authenticated user
        db: Database session

    Returns:
        Team comparison with rankings and insights
    """
    if not team_ids or len(team_ids) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 teams required for comparison"
        )

    if len(team_ids) > 10:
        raise HTTPException(
            status_code=400, detail="Maximum 10 teams can be compared at once"
        )

    try:
        comparison = await team_analytics_service.compare_teams(
            db=db, team_ids=team_ids, days=days
        )

        return {"success": True, "comparison": comparison}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compare teams: {str(e)}"
        )


@router.get("/organization/{organization_id}")
async def get_organization_analytics(
    organization_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics for entire organization

    Args:
        organization_id: Organization ID to analyze
        days: Number of days to analyze
        current_user: Authenticated user
        db: Database session

    Returns:
        Organization analytics with team breakdown
    """
    try:
        analytics = await team_analytics_service.get_organization_analytics(
            db=db, organization_id=organization_id, days=days
        )

        return {"success": True, "analytics": analytics}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch organization analytics: {str(e)}"
        )


@router.get("/my-teams")
async def get_my_teams_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics for all teams the current user belongs to

    Args:
        days: Number of days to analyze
        current_user: Authenticated user
        db: Database session

    Returns:
        Analytics for user's teams
    """
    try:
        # TODO: Get user's actual teams from database
        # For now, return mock data
        user_teams = [1, 2, 3]  # Mock team IDs

        team_analyses = []
        for team_id in user_teams:
            analytics = await team_analytics_service.get_team_analytics(
                db=db, team_id=team_id, days=days
            )
            team_analyses.append(analytics)

        return {
            "success": True,
            "user_teams": team_analyses,
            "total_teams": len(user_teams),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch team analytics: {str(e)}"
        )


@router.get("/team/{team_id}/top-performers")
async def get_team_top_performers(
    team_id: int,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top performers in a team

    Args:
        team_id: Team ID
        days: Number of days to analyze
        limit: Number of top performers to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of top performing team members
    """
    try:
        analytics = await team_analytics_service.get_team_analytics(
            db=db, team_id=team_id, days=days
        )

        top_performers = analytics["team_metrics"]["top_performers"][:limit]

        return {"success": True, "team_id": team_id, "top_performers": top_performers}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch top performers: {str(e)}"
        )


@router.get("/team/{team_id}/trends")
async def get_team_trends(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get productivity and sentiment trends for a team over time

    Args:
        team_id: Team ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Trend data over multiple periods
    """
    # TODO: Implement actual trend calculation from historical data

    return {
        "success": True,
        "team_id": team_id,
        "trends": {
            "productivity": {
                "current": 78,
                "last_week": 75,
                "last_month": 72,
                "trend": "improving",
            },
            "sentiment": {
                "current_positive": 65,
                "last_week_positive": 60,
                "last_month_positive": 55,
                "trend": "improving",
            },
            "stress": {
                "current_high_stress": 1,
                "last_week_high_stress": 2,
                "last_month_high_stress": 3,
                "trend": "improving",
            },
        },
        "note": "Trend analysis requires historical data storage",
    }


@router.get("/organization/{organization_id}/leaderboard")
async def get_organization_leaderboard(
    organization_id: int,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get leaderboard of top performers across organization

    Args:
        organization_id: Organization ID
        days: Number of days to analyze
        limit: Number of performers to return
        current_user: Authenticated user
        db: Database session

    Returns:
        Leaderboard of top performers
    """
    try:
        analytics = await team_analytics_service.get_organization_analytics(
            db=db, organization_id=organization_id, days=days
        )

        # Aggregate all members from all teams
        all_members = []
        for team_data in analytics["team_analytics"]:
            for member in team_data["analytics"]["member_analytics"]:
                all_members.append(
                    {
                        "name": member["member_name"],
                        "team": team_data["team_name"],
                        "productivity_score": member["analytics"]["productivity_score"],
                        "total_emails": member["analytics"]["total_emails"],
                    }
                )

        # Sort by productivity score
        leaderboard = sorted(
            all_members, key=lambda x: x["productivity_score"], reverse=True
        )[:limit]

        return {
            "success": True,
            "organization_id": organization_id,
            "leaderboard": leaderboard,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch leaderboard: {str(e)}"
        )
