import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.db.models.assessment import Assessment, AssessmentResponse
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.schemas.engagement import EngagementAnalytics, IndividualEngagementScore
from app.services.assessment_scoring_strategies import (
    FrameworkCode,
    get_scoring_strategy_registry,
)

router = APIRouter()


@router.get("/engagement/individual-scores", response_model=EngagementAnalytics)
async def get_engagement_analytics(
    organization_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """
    Fetch individual engagement scores for an organization.
    Calculates scores from real assessment responses.
    """
    # 1. Get all engagement assessments for this org
    assessments_query = select(Assessment).where(
        Assessment.organization_id == organization_id,
        Assessment.framework_code == "ENGAGEMENT",
    )
    assessments_result = await db.execute(assessments_query)
    assessments = assessments_result.scalars().all()

    if not assessments:
        return EngagementAnalytics(
            scores=[],
            summary={},
            participation_rate=0.0,
            last_updated=datetime.utcnow(),
        )

    assessment_ids = [a.id for a in assessments]

    # 2. Get all responses for these assessments, grouped by user
    # We want to join with User and Team (via TeamMember)
    query = (
        select(User, Team.name.label("department"), Response)
        .join(Response, Response.user_id == User.id)
        .outerjoin(TeamMember, TeamMember.user_id == User.id)
        .outerjoin(Team, Team.id == TeamMember.team_id)
        .where(Response.assessment_id.in_(assessment_ids))
        .order_by(User.id, Response.created_at.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    # Process results into individual scores
    user_responses: Dict[uuid.UUID, Dict[str, Any]] = {}

    # Registry for scoring
    registry = get_scoring_strategy_registry()
    strategy = registry.get_strategy(FrameworkCode.ENGAGEMENT.value)

    for user, dept, response in rows:
        if user.id not in user_responses:
            user_responses[user.id] = {
                "user": user,
                "dept": dept or "General",
                "responses": [],
            }
        user_responses[user.id]["responses"].append(response)

    individual_scores: List[IndividualEngagementScore] = []

    for user_id, data in user_responses.items():
        user = data["user"]
        responses = data["responses"]

        # Calculate scores using the strategy
        scoring_result = strategy.calculate(responses)
        scores = scoring_result.scores

        individual_scores.append(
            IndividualEngagementScore(
                employee_id=str(user.id)[:8].upper(),
                employee_name=user.full_name or user.email,
                department=data["dept"],
                overall_score=round(scores.get("overall_score", 0), 2),
                job_satisfaction=round(scores.get("job_satisfaction", 0), 2),
                work_life_balance=round(scores.get("work_life_balance", 0), 2),
                management_support=round(scores.get("management_support", 0), 2),
                career_growth=round(scores.get("career_growth", 0), 2),
                compensation_satisfaction=round(
                    scores.get("compensation_satisfaction", 0), 2
                ),
                team_collaboration=round(scores.get("team_collaboration", 0), 2),
                survey_date=(
                    responses[0].created_at.strftime("%Y-%m-%d")
                    if responses
                    else datetime.utcnow().strftime("%Y-%m-%d")
                ),
            )
        )

    # Calculate summary
    if not individual_scores:
        return EngagementAnalytics(
            scores=[],
            summary={},
            participation_rate=0.0,
            last_updated=datetime.utcnow(),
        )

    avg_overall = sum(s.overall_score for s in individual_scores) / len(
        individual_scores
    )

    # Participation rate (simplified: respondents / total users in org)
    total_users_query = select(func.count(User.id)).where(
        User.organization_id == organization_id
    )
    total_users_result = await db.execute(total_users_query)
    total_users_count = total_users_result.scalar() or 1

    participation_rate = (len(user_responses) / total_users_count) * 100

    return EngagementAnalytics(
        scores=individual_scores,
        summary={"avg_overall": round(avg_overall, 2)},
        participation_rate=round(participation_rate, 1),
        last_updated=datetime.utcnow(),
    )
