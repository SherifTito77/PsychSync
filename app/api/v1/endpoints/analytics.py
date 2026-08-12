"""
Analytics API Endpoints

Queries Response, Assessment, User, and Team tables for real analytics.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/assessments/{assessment_id}")
async def get_assessment_analytics(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Analytics for a specific assessment."""
    # Assessment info
    assess_result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = assess_result.scalar_one_or_none()
    title = assessment.title if assessment else ""

    # Response stats
    result = await db.execute(
        select(
            func.count(Response.id),
            func.avg(Response.answer_value),
            func.avg(Response.response_time_ms),
            func.count(func.distinct(Response.user_id)),
        ).where(Response.assessment_id == assessment_id)
    )
    row = result.one_or_none()
    total = row[0] or 0 if row else 0
    avg_score = round(float(row[1] or 0), 2) if row else 0
    avg_time = round(float(row[2] or 0), 1) if row else 0
    unique_users = row[3] or 0 if row else 0

    # Score distribution (1-5 scale)
    dist_result = await db.execute(
        select(Response.answer_value, func.count(Response.id))
        .where(
            and_(
                Response.assessment_id == assessment_id,
                Response.answer_value.isnot(None),
            )
        )
        .group_by(Response.answer_value)
        .order_by(Response.answer_value)
    )
    score_distribution = [{"score": r[0], "count": r[1]} for r in dist_result.all()]

    # Recent responses
    recent_result = await db.execute(
        select(Response.user_id, Response.answer_value, Response.created_at)
        .where(Response.assessment_id == assessment_id)
        .order_by(Response.created_at.desc())
        .limit(10)
    )
    recent = [
        {
            "user_id": str(r[0]),
            "score": r[1],
            "date": r[2].isoformat() if r[2] else None,
        }
        for r in recent_result.all()
    ]

    return {
        "assessment_id": assessment_id,
        "assessment_title": title,
        "total_responses": total,
        "total_assignments": unique_users,
        "average_score": avg_score,
        "average_time": avg_time,
        "completion_rate": round(total / max(unique_users, 1) * 100, 1),
        "score_distribution": score_distribution,
        "recent_responses": recent,
    }


@router.get("/users/me")
async def get_my_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Current user's analytics."""
    return await _user_analytics(db, str(current_user.id))


@router.get("/users/{user_id}")
async def get_user_analytics(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _user_analytics(db, user_id)


async def _user_analytics(db: AsyncSession, user_id: str) -> dict[str, Any]:
    result = await db.execute(
        select(
            func.count(Response.id),
            func.avg(Response.answer_value),
            func.count(func.distinct(Response.assessment_id)),
        ).where(Response.user_id == user_id)
    )
    row = result.one_or_none()
    total = row[0] or 0 if row else 0
    avg_score = round(float(row[1] or 0), 2) if row else 0
    assessments = row[2] or 0 if row else 0

    # Response history (last 20)
    history_result = await db.execute(
        select(Response.assessment_id, Response.answer_value, Response.created_at)
        .where(Response.user_id == user_id)
        .order_by(Response.created_at.desc())
        .limit(20)
    )
    history = [
        {
            "assessment_id": str(r[0]),
            "score": r[1],
            "date": r[2].isoformat() if r[2] else None,
        }
        for r in history_result.all()
    ]

    return {
        "user_id": user_id,
        "total_responses": total,
        "completed_responses": total,
        "in_progress_responses": 0,
        "average_score": avg_score,
        "unique_assessments": assessments,
        "response_history": history,
    }


@router.get("/teams/{team_id}")
async def get_team_analytics(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Team-level analytics."""
    # Get team members
    members_result = await db.execute(
        select(TeamMember.user_id).where(TeamMember.team_id == team_id)
    )
    member_ids = [str(r[0]) for r in members_result.all()]

    if not member_ids:
        return {
            "team_id": team_id,
            "total_members": 0,
            "total_assessments": 0,
            "total_responses": 0,
            "completed_responses": 0,
            "average_score": 0,
            "member_performance": [],
        }

    # Team response stats
    result = await db.execute(
        select(
            func.count(Response.id),
            func.avg(Response.answer_value),
            func.count(func.distinct(Response.assessment_id)),
        ).where(Response.user_id.in_(member_ids))
    )
    row = result.one_or_none()
    total = row[0] or 0 if row else 0
    avg_score = round(float(row[1] or 0), 2) if row else 0
    assessments = row[2] or 0 if row else 0

    # Per-member performance
    perf_result = await db.execute(
        select(
            Response.user_id,
            func.count(Response.id),
            func.avg(Response.answer_value),
        )
        .where(Response.user_id.in_(member_ids))
        .group_by(Response.user_id)
    )
    member_perf = [
        {
            "user_id": str(r[0]),
            "response_count": r[1],
            "avg_score": round(float(r[2] or 0), 2),
        }
        for r in perf_result.all()
    ]

    return {
        "team_id": team_id,
        "total_members": len(member_ids),
        "total_assessments": assessments,
        "total_responses": total,
        "completed_responses": total,
        "average_score": avg_score,
        "member_performance": member_perf,
    }


@router.get("/system")
async def get_system_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """System-wide analytics."""
    since_30d = datetime.utcnow() - timedelta(days=30)

    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0

    assessments_result = await db.execute(select(func.count(Assessment.id)))
    total_assessments = assessments_result.scalar() or 0

    responses_result = await db.execute(select(func.count(Response.id)))
    total_responses = responses_result.scalar() or 0

    recent_result = await db.execute(
        select(func.count(Response.id)).where(Response.created_at >= since_30d)
    )
    recent_activity = recent_result.scalar() or 0

    # Popular assessments
    popular_result = await db.execute(
        select(Response.assessment_id, func.count(Response.id).label("cnt"))
        .group_by(Response.assessment_id)
        .order_by(func.count(Response.id).desc())
        .limit(5)
    )
    popular = []
    for r in popular_result.all():
        a_result = await db.execute(
            select(Assessment.title).where(Assessment.id == r[0])
        )
        title = a_result.scalar() or "Unknown"
        popular.append(
            {"assessment_id": str(r[0]), "title": title, "response_count": r[1]}
        )

    return {
        "total_users": total_users,
        "total_assessments": total_assessments,
        "total_responses": total_responses,
        "completed_responses": total_responses,
        "completion_rate": 100.0 if total_responses > 0 else 0.0,
        "recent_activity_30d": recent_activity,
        "popular_assessments": popular,
    }


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Dashboard overview aggregating all key metrics."""
    since = datetime.utcnow() - timedelta(days=30)

    # User metrics
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (
        await db.execute(
            select(func.count(func.distinct(Response.user_id))).where(
                Response.created_at >= since
            )
        )
    ).scalar() or 0

    # Assessment metrics
    total_assessments = (
        await db.execute(select(func.count(Assessment.id)))
    ).scalar() or 0

    # Response metrics
    total_responses = (await db.execute(select(func.count(Response.id)))).scalar() or 0
    recent_responses = (
        await db.execute(
            select(func.count(Response.id)).where(Response.created_at >= since)
        )
    ).scalar() or 0

    avg_score = (
        await db.execute(
            select(func.avg(Response.answer_value)).where(
                Response.answer_value.isnot(None)
            )
        )
    ).scalar()

    # Team metrics
    total_teams = (await db.execute(select(func.count(Team.id)))).scalar() or 0

    return {
        "period": "last_30_days",
        "generated_at": datetime.utcnow().isoformat(),
        "user_metrics": {
            "total": total_users,
            "active_30d": active_users,
            "engagement_rate": round(active_users / max(total_users, 1) * 100, 1),
        },
        "assessment_metrics": {
            "total": total_assessments,
        },
        "team_metrics": {
            "total_teams": total_teams,
        },
        "system_metrics": {
            "total_responses": total_responses,
            "recent_responses_30d": recent_responses,
            "avg_score": round(float(avg_score or 0), 2),
        },
    }


@router.get("/dashboard/insights")
async def get_analytics_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate insights from analytics data."""
    since = datetime.utcnow() - timedelta(days=30)
    prev_since = since - timedelta(days=30)

    insights = []

    # Activity trend
    current_count = (
        await db.execute(
            select(func.count(Response.id)).where(Response.created_at >= since)
        )
    ).scalar() or 0
    prev_count = (
        await db.execute(
            select(func.count(Response.id)).where(
                Response.created_at.between(prev_since, since)
            )
        )
    ).scalar() or 0

    if current_count > prev_count * 1.2:
        insights.append(
            {
                "type": "positive",
                "message": f"Assessment activity up {round((current_count - prev_count) / max(prev_count, 1) * 100)}% vs previous period",
            }
        )
    elif current_count < prev_count * 0.8 and prev_count > 0:
        insights.append(
            {
                "type": "warning",
                "message": f"Assessment activity down {round((prev_count - current_count) / max(prev_count, 1) * 100)}% vs previous period",
            }
        )

    # Score trends
    avg_result = await db.execute(
        select(func.avg(Response.answer_value)).where(
            and_(Response.created_at >= since, Response.answer_value.isnot(None))
        )
    )
    avg_val = float(avg_result.scalar() or 3.0)
    if avg_val < 2.5:
        insights.append(
            {
                "type": "warning",
                "message": f"Average response score is low ({avg_val:.1f}/5) — investigate potential issues",
            }
        )
    elif avg_val > 4.0:
        insights.append(
            {
                "type": "positive",
                "message": f"Average response score is strong ({avg_val:.1f}/5)",
            }
        )

    return {
        "user_insights": [],
        "assessment_insights": insights,
        "team_insights": [],
        "recommendations": [],
        "anomalies": [],
    }


@router.get("/metrics/available")
async def get_available_metrics(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "categories": {
            "engagement": ["response_count", "completion_rate", "active_users"],
            "scores": ["average_score", "score_distribution", "score_trends"],
            "performance": ["response_time", "assessment_duration"],
            "team": ["member_count", "team_score", "participation_rate"],
        },
        "time_periods": ["7d", "30d", "90d", "180d", "365d"],
        "granularities": ["hour", "day", "week", "month"],
    }
