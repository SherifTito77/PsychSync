"""
Behavioral User Dashboard API Endpoints

Derives per-user behavioral analytics from the Response table:
quick stats, period comparison, peer benchmarks, alerts, forecasts,
and mental health summaries.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User

router = APIRouter(tags=["behavioral-user-dashboard"])


def _parse_days(time_range: str) -> int:
    return int(time_range.rstrip("d")) if time_range.endswith("d") else 30


async def _user_stats(db: AsyncSession, user_id: str, days: int) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(Response.id),
            func.avg(Response.answer_value),
            func.avg(Response.response_time_ms),
            func.min(Response.answer_value),
            func.max(Response.answer_value),
        ).where(and_(Response.user_id == user_id, Response.created_at >= since))
    )
    row = result.one_or_none()
    return {
        "count": row[0] or 0 if row else 0,
        "avg_val": float(row[1] or 3.0) if row else 3.0,
        "avg_time": float(row[2] or 10000) if row else 10000,
        "min_val": row[3] or 3 if row else 3,
        "max_val": row[4] or 3 if row else 3,
    }


async def _peer_stats(db: AsyncSession, user_id: str, days: int) -> dict:
    """Average stats for peers (users in same teams)."""
    since = datetime.utcnow() - timedelta(days=days)
    # Find peer user IDs
    team_result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    team_ids = [str(r[0]) for r in team_result.all()]
    if not team_ids:
        return {"avg_val": 3.0, "count": 0}

    peer_result = await db.execute(
        select(TeamMember.user_id)
        .where(and_(TeamMember.team_id.in_(team_ids), TeamMember.user_id != user_id))
        .distinct()
    )
    peer_ids = [str(r[0]) for r in peer_result.all()]
    if not peer_ids:
        return {"avg_val": 3.0, "count": 0}

    result = await db.execute(
        select(func.avg(Response.answer_value), func.count(Response.id)).where(
            and_(Response.user_id.in_(peer_ids), Response.created_at >= since)
        )
    )
    row = result.one_or_none()
    return {
        "avg_val": float(row[0] or 3.0) if row else 3.0,
        "count": row[1] or 0 if row else 0,
    }


def _wellness_score(avg_val: float) -> int:
    """Convert 1-5 avg to 0-100 wellness score."""
    return int(min(100, max(0, (avg_val - 1) / 4 * 100)))


def _risk_count(stats: dict) -> int:
    risks = 0
    if stats["avg_val"] < 2.5:
        risks += 1
    if stats["count"] < 3:
        risks += 1
    if stats["avg_time"] < 3000 and stats["count"] > 5:
        risks += 1
    return risks


# ---------------------------------------------------------------------------
# /behavioral/* routes
# ---------------------------------------------------------------------------


@router.get("/behavioral/quick-stats/{user_id}")
async def get_quick_stats(
    user_id: str,
    time_range: str = Query(default="30d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    days = _parse_days(time_range)
    current = await _user_stats(db, user_id, days)
    previous = await _user_stats(db, user_id, days * 2)

    wellness = _wellness_score(current["avg_val"])
    prev_wellness = _wellness_score(previous["avg_val"])
    risks = _risk_count(current)
    prev_risks = _risk_count(previous)

    # Streak: count consecutive days with responses
    streak_result = await db.execute(
        select(func.date(Response.created_at))
        .where(Response.user_id == user_id)
        .group_by(func.date(Response.created_at))
        .order_by(func.date(Response.created_at).desc())
        .limit(60)
    )
    dates = [r[0] for r in streak_result.all()]
    streak = 0
    today = datetime.utcnow().date()
    for i, d in enumerate(dates):
        expected = today - timedelta(days=i)
        if d == expected:
            streak += 1
        else:
            break

    return {
        "assessmentsCompleted": current["count"],
        "assessmentsChange": current["count"] - previous["count"],
        "wellnessScore": wellness,
        "wellnessChange": wellness - prev_wellness,
        "riskFactorsDetected": risks,
        "riskFactorsChange": risks - prev_risks,
        "goalsAchieved": min(current["count"], 5),
        "goalsCompletionRate": min(100, current["count"] * 10),
        "streakDays": streak,
    }


@router.get("/behavioral/comparison/{user_id}")
async def get_comparison_data(
    user_id: str,
    time_range: str = Query(default="30d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    days = _parse_days(time_range)
    current = await _user_stats(db, user_id, days)
    previous = await _user_stats(db, user_id, days * 2)
    peers = await _peer_stats(db, user_id, days)

    cur_w = _wellness_score(current["avg_val"])
    prev_w = _wellness_score(previous["avg_val"])
    peer_w = _wellness_score(peers["avg_val"])

    engagement = min(100, current["count"] * 5)
    prev_engagement = min(100, previous["count"] * 5)
    peer_engagement = min(100, peers["count"] * 3)

    productivity = min(100, int((20000 - min(current["avg_time"], 20000)) / 200))
    prev_productivity = min(100, int((20000 - min(previous["avg_time"], 20000)) / 200))

    # Percentile ranking (simplified: compare to peer average)
    wellness_pctile = min(99, max(1, int(50 + (cur_w - peer_w))))
    engagement_pctile = min(99, max(1, int(50 + (engagement - peer_engagement))))

    return {
        "currentPeriod": {
            "wellnessScore": cur_w,
            "engagementScore": engagement,
            "productivityScore": productivity,
        },
        "previousPeriod": {
            "wellnessScore": prev_w,
            "engagementScore": prev_engagement,
            "productivityScore": prev_productivity,
        },
        "peerAverage": {
            "wellnessScore": peer_w,
            "engagementScore": peer_engagement,
            "productivityScore": 50,
        },
        "percentileRankings": {
            "wellness": wellness_pctile,
            "engagement": engagement_pctile,
            "productivity": 50,
        },
    }


@router.get("/behavioral/alerts/{user_id}")
async def get_alerts(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await _user_stats(db, user_id, 30)
    warnings = []
    achievements = []
    tips = []

    if stats["avg_val"] < 2.5:
        warnings.append(
            {
                "type": "low_scores",
                "message": "Your recent assessment scores are below average — consider reaching out to a counselor",
                "severity": "high",
            }
        )
    if stats["count"] < 3:
        warnings.append(
            {
                "type": "low_engagement",
                "message": "Low assessment participation this month — staying engaged helps track your wellbeing",
                "severity": "medium",
            }
        )
    if stats["avg_time"] < 3000 and stats["count"] > 5:
        warnings.append(
            {
                "type": "rushing",
                "message": "Response times suggest you may be rushing — take your time for more accurate results",
                "severity": "low",
            }
        )

    if stats["count"] >= 10:
        achievements.append(
            {
                "type": "consistent",
                "message": "Completed 10+ assessments this month!",
                "icon": "star",
            }
        )
    if stats["avg_val"] >= 4.0:
        achievements.append(
            {
                "type": "high_scores",
                "message": "Your scores are in the top range — keep it up!",
                "icon": "trophy",
            }
        )

    if stats["avg_val"] < 3.0:
        tips.append(
            {
                "message": "Try a brief mindfulness exercise before your next assessment",
                "category": "wellness",
            }
        )
    if stats["count"] > 0:
        tips.append(
            {
                "message": "Review your trend data to identify patterns in your wellbeing",
                "category": "insight",
            }
        )

    return {"warnings": warnings, "achievements": achievements, "tips": tips}


@router.get("/behavioral/goals/{user_id}")
async def get_goals(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await _user_stats(db, user_id, 30)
    goals = []

    # Auto-generate goals based on current stats
    if stats["count"] < 10:
        goals.append(
            {
                "id": "goal-assessments",
                "title": "Complete 10 assessments this month",
                "progress": min(100, stats["count"] * 10),
                "target": 10,
                "current": stats["count"],
                "category": "engagement",
            }
        )

    wellness = _wellness_score(stats["avg_val"])
    if wellness < 75:
        goals.append(
            {
                "id": "goal-wellness",
                "title": "Improve wellness score to 75+",
                "progress": min(100, int(wellness / 75 * 100)),
                "target": 75,
                "current": wellness,
                "category": "wellness",
            }
        )

    goals.append(
        {
            "id": "goal-consistency",
            "title": "Maintain a 7-day assessment streak",
            "progress": min(100, stats["count"] * 14),
            "target": 7,
            "current": min(7, stats["count"]),
            "category": "consistency",
        }
    )

    return {"goals": goals}


@router.get("/behavioral/forecasts/{user_id}")
async def get_forecasts(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stats_30 = await _user_stats(db, user_id, 30)
    stats_60 = await _user_stats(db, user_id, 60)

    w_current = _wellness_score(stats_30["avg_val"])
    w_prev = _wellness_score(stats_60["avg_val"])
    trend_per_day = (w_current - w_prev) / 30 if w_prev != w_current else 0

    w_7d = max(0, min(100, int(w_current + trend_per_day * 7)))
    w_30d = max(0, min(100, int(w_current + trend_per_day * 30)))
    w_90d = max(0, min(100, int(w_current + trend_per_day * 90)))

    # Burnout risk: inverse of wellness
    burnout_current = max(0, min(100, 100 - w_current))
    burnout_7d = max(0, min(100, 100 - w_7d))
    burnout_30d = max(0, min(100, 100 - w_30d))

    if trend_per_day > 0.2:
        trend = "improving"
    elif trend_per_day < -0.2:
        trend = "declining"
    else:
        trend = "stable"

    burnout_level = "low"
    if burnout_current > 60:
        burnout_level = "high"
    elif burnout_current > 30:
        burnout_level = "moderate"

    confidence = min(95, 30 + stats_30["count"] * 5)

    return {
        "wellnessForecast": {
            "current": w_current,
            "predicted7Days": w_7d,
            "predicted30Days": w_30d,
            "predicted90Days": w_90d,
            "trend": trend,
        },
        "burnoutRiskForecast": {
            "current": burnout_current,
            "predicted7Days": burnout_7d,
            "predicted30Days": burnout_30d,
            "riskLevel": burnout_level,
        },
        "confidence": confidence,
    }


@router.get("/behavioral/recommendations/{user_id}")
async def get_recommendations(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await _user_stats(db, user_id, 30)
    recs = []

    if stats["avg_val"] < 2.5:
        recs.append(
            {
                "id": "rec-counseling",
                "title": "Schedule a wellness check-in",
                "description": "Your recent scores suggest you might benefit from speaking with a counselor or manager",
                "priority": "high",
                "category": "mental_health",
            }
        )
    if stats["count"] < 5:
        recs.append(
            {
                "id": "rec-engage",
                "title": "Increase assessment frequency",
                "description": "Regular self-assessment helps identify patterns early — aim for weekly check-ins",
                "priority": "medium",
                "category": "engagement",
            }
        )
    if stats["avg_time"] < 3000 and stats["count"] > 3:
        recs.append(
            {
                "id": "rec-mindful",
                "title": "Practice mindful responding",
                "description": "Taking more time with assessments improves accuracy and self-reflection",
                "priority": "low",
                "category": "quality",
            }
        )
    if stats["avg_val"] >= 3.5:
        recs.append(
            {
                "id": "rec-mentor",
                "title": "Consider peer mentoring",
                "description": "Your strong scores suggest you could help colleagues — explore mentoring opportunities",
                "priority": "low",
                "category": "growth",
            }
        )
    if not recs:
        recs.append(
            {
                "id": "rec-maintain",
                "title": "Keep up your current routine",
                "description": "Your behavioral indicators are healthy — continue your current practices",
                "priority": "low",
                "category": "maintenance",
            }
        )

    return {"recommendations": recs}


# ---------------------------------------------------------------------------
# Mental health summary
# ---------------------------------------------------------------------------


@router.get("/assessments/user/{user_id}/mental-health-summary")
async def get_mental_health_summary(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await _user_stats(db, user_id, 30)
    prev_stats = await _user_stats(db, user_id, 60)

    avg = stats["avg_val"]

    # Risk indicators based on score ranges
    def risk_level(val: float) -> str:
        if val >= 4.0:
            return "low"
        elif val >= 3.0:
            return "moderate"
        elif val >= 2.0:
            return "high"
        return "critical"

    risk = risk_level(avg)

    # Trends
    def trend(current: float, previous: float) -> str:
        diff = current - previous
        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        return "stable"

    val_trend = trend(stats["avg_val"], prev_stats["avg_val"])

    # Recent assessments
    recent_result = await db.execute(
        select(Response.assessment_id, Response.answer_value, Response.created_at)
        .where(Response.user_id == user_id)
        .order_by(Response.created_at.desc())
        .limit(5)
    )
    recent = [
        {
            "assessment_id": str(r[0]),
            "score": r[1],
            "date": r[2].isoformat() if r[2] else None,
        }
        for r in recent_result.all()
    ]

    recs = []
    if risk in ("high", "critical"):
        recs.append("Consider scheduling a professional consultation")
    if stats["count"] < 3:
        recs.append("Increase assessment frequency for better tracking")

    return {
        "recent_assessments": recent,
        "risk_indicators": {
            "depression_risk": risk,
            "anxiety_risk": risk,
            "stress_level": risk,
            "overall_risk": risk,
        },
        "recommendations": recs,
        "wellness_trends": {
            "mood_trend": val_trend,
            "energy_levels": val_trend,
            "sleep_quality": "stable",
            "social_engagement": "improving" if stats["count"] > 5 else "stable",
        },
    }
