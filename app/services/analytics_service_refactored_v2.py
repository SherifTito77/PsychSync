"""
Refactored Analytics Service

This is the CORRECT service layer implementation.
It focuses ONLY on business logic, not data access or response formatting.

Responsibilities:
- Analytics calculation logic
- Domain knowledge about what analytics mean
- Orchestration of data retrieval

NOT responsible for:
- Database queries (that's repository layer's job)
- HTTP response formatting (that's API layer's job)
- Caching (that's infrastructure/ concern)
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.analytics import (
    AssessmentAnalytics,
    MemberPerformance,
    PopularAssessment,
    ResponseSummary,
    ScoreDistribution,
    SystemAnalytics,
    TeamAnalytics,
    UserAnalytics,
)
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.response_repository import ResponseRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics business logic service

    This service orchestrates analytics by:
    1. Using repositories for data access (NO direct database queries)
    2. Calculating analytics based on business rules
    3. Returning domain objects (NOT HTTP responses)

    It does NOT contain:
    - Database queries (delegated to repositories)
    - HTTP response formatting (API layer's job)
    - Caching logic (infrastructure concern)
    """

    def __init__(
        self,
        user_repo: UserRepository,
        assessment_repo: AssessmentRepository,
        response_repo: ResponseRepository,
        team_repo: TeamRepository,
    ):
        """
        Initialize analytics service with repository dependencies

        Args:
            user_repo: Repository for user data access
            assessment_repo: Repository for assessment data access
            response_repo: Repository for response data access
            team_repo: Repository for team data access
        """
        self._user_repo = user_repo
        self._assessment_repo = assessment_repo
        self._response_repo = response_repo
        self._team_repo = team_repo

    async def get_user_analytics(
        self, db: AsyncSession, user_id: UUID
    ) -> UserAnalytics:
        """
        Get analytics for a specific user

        BUSINESS LOGIC:
        - What constitutes user analytics?
        - How to calculate completion rates?
        - What's considered "recent" activity?

        DATA ACCESS (delegated to repositories):
        - Fetching user responses
        - Getting response details

        Returns:
            UserAnalytics domain object (not a dict for HTTP response)
        """
        try:
            # Data access: delegate to repository
            responses = await self._response_repo.get_by_user(
                db, user_id, limit=1000, include_assessment=True
            )

            # Business logic: categorize responses
            completed_responses = [r for r in responses if r.submitted_at is not None]
            in_progress_responses = [r for r in responses if r.submitted_at is None]

            # Business logic: calculate average score
            scores = [r.score for r in completed_responses if r.score is not None]
            average_score = sum(scores) / len(scores) if scores else None

            # Business logic: build response history (last 10)
            response_summaries = []
            for response in completed_responses[:10]:
                summary = ResponseSummary(
                    response_id=response.id,
                    assessment_id=response.assessment_id,
                    assessment_title=getattr(response.assessment, "title", "Unknown"),
                    submitted_at=response.submitted_at,
                    score=response.score,
                    time_taken=response.time_taken,
                )
                response_summaries.append(summary)

            # Return domain object (not dict!)
            return UserAnalytics(
                user_id=user_id,
                total_responses=len(responses),
                completed_responses=len(completed_responses),
                in_progress_responses=len(in_progress_responses),
                average_score=average_score,
                response_history=response_summaries,
            )

        except Exception as e:
            logger.error(f"Error calculating user analytics for {user_id}: {e}")
            # Return empty analytics on error
            return UserAnalytics(
                user_id=user_id,
                total_responses=0,
                completed_responses=0,
                in_progress_responses=0,
                average_score=None,
                response_history=[],
            )

    async def get_assessment_analytics(
        self, db: AsyncSession, assessment_id: UUID
    ) -> AssessmentAnalytics:
        """
        Get analytics for a specific assessment

        BUSINESS LOGIC:
        - How to calculate completion rates?
        - How to bucket score distributions?
        - What's considered "recent"?

        Returns:
            AssessmentAnalytics domain object
        """
        try:
            # Data access: delegate to repository
            assessment = await self._assessment_repo.get_by_id(db, assessment_id)
            if not assessment:
                raise ValueError(f"Assessment {assessment_id} not found")

            responses = await self._response_repo.get_by_assessment(
                db, assessment_id, limit=10000
            )

            # Business logic: categorize responses
            completed_responses = [r for r in responses if r.submitted_at is not None]

            # Business logic: calculate statistics
            scores = [r.score for r in completed_responses if r.score is not None]
            average_score = sum(scores) / len(scores) if scores else None

            times = [
                r.time_taken for r in completed_responses if r.time_taken is not None
            ]
            average_time = sum(times) / len(times) if times else None

            completion_rate = (
                len(completed_responses) / len(responses) * 100 if responses else 0
            )

            # Business logic: calculate score distribution
            score_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
            for score in scores:
                if score <= 20:
                    score_ranges["0-20"] += 1
                elif score <= 40:
                    score_ranges["21-40"] += 1
                elif score <= 60:
                    score_ranges["41-60"] += 1
                elif score <= 80:
                    score_ranges["61-80"] += 1
                else:
                    score_ranges["81-100"] += 1

            score_distributions = [
                ScoreDistribution(range_label=k, count=v)
                for k, v in score_ranges.items()
            ]

            # Business logic: build recent responses list
            recent_responses = [
                {
                    "id": str(r.id),
                    "submitted_at": (
                        r.submitted_at.isoformat() if r.submitted_at else None
                    ),
                    "score": r.score,
                }
                for r in completed_responses[:10]
            ]

            # Return domain object
            return AssessmentAnalytics(
                assessment_id=assessment_id,
                assessment_title=assessment.title,
                total_responses=len(responses),
                total_assignments=len(responses),
                average_score=average_score,
                average_time=average_time,
                completion_rate=completion_rate,
                score_distribution=score_distributions,
                recent_responses=recent_responses,
            )

        except Exception as e:
            logger.error(
                f"Error calculating assessment analytics for {assessment_id}: {e}"
            )
            raise

    async def get_team_analytics(self, db: AsyncSession, team_id: int) -> TeamAnalytics:
        """
        Get analytics for a specific team

        BUSINESS LOGIC:
        - How to aggregate team member performance?
        - What team-level metrics matter?

        Returns:
            TeamAnalytics domain object
        """
        try:
            # Data access: delegate to repositories
            team = await self._team_repo.get_with_members(team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            members = team.members if hasattr(team, "members") else []

            # Data access: get team assessments via repository
            team_assessments = await self._assessment_repo.get_by_team(
                db, team_id, limit=1000
            )

            # Data access: collect all team responses
            all_responses = []
            for assessment in team_assessments:
                assessment_responses = await self._response_repo.get_by_assessment(
                    db, assessment_id=assessment.id
                )
                all_responses.extend(assessment_responses)

            # Business logic: categorize and calculate
            completed_responses = [
                r for r in all_responses if r.submitted_at is not None
            ]

            scores = [r.score for r in completed_responses if r.score is not None]
            average_score = sum(scores) / len(scores) if scores else None

            # Business logic: calculate member performance
            member_performances = []
            for member in members:
                member_responses = [
                    r for r in all_responses if str(r.user_id) == str(member.id)
                ]
                member_completed = [
                    r for r in member_responses if r.submitted_at is not None
                ]
                member_scores = [
                    r.score for r in member_completed if r.score is not None
                ]
                member_avg = (
                    sum(member_scores) / len(member_scores) if member_scores else None
                )

                performance = MemberPerformance(
                    user_id=member.id,
                    user_name=member.full_name or member.email,
                    completed_assessments=len(member_completed),
                    average_score=member_avg,
                )
                member_performances.append(performance)

            # Return domain object
            return TeamAnalytics(
                team_id=team_id,
                total_members=len(members),
                total_assessments=len(team_assessments),
                total_responses=len(all_responses),
                completed_responses=len(completed_responses),
                average_score=average_score,
                member_performance=member_performances,
            )

        except Exception as e:
            logger.error(f"Error calculating team analytics for {team_id}: {e}")
            raise

    async def get_system_analytics(self, db: AsyncSession) -> SystemAnalytics:
        """
        Get system-wide analytics

        BUSINESS LOGIC:
        - What are the key system metrics?
        - How to identify popular assessments?
        - What time period constitutes "recent"?

        Returns:
            SystemAnalytics domain object
        """
        try:
            # Data access: delegate to repositories
            total_users = await self._user_repo.count()
            total_assessments = await self._assessment_repo.count()

            # Get all responses (note: this could be optimized with a repository method)
            # For now, we'll use statistics method
            response_stats = await self._response_repo.get_response_statistics()

            # Business logic: calculate completion rate
            total_responses = response_stats["total_responses"]
            completed_responses = response_stats["completed_responses"]
            completion_rate = (
                completed_responses / total_responses * 100
                if total_responses > 0
                else 0
            )

            # Business logic: recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            # Would need a repository method for this
            # For now, using placeholder
            recent_activity = 0

            # Business logic: identify popular assessments
            # This would require a repository method that aggregates response counts
            # For now, returning empty list
            popular_assessments = []

            # Return domain object
            return SystemAnalytics(
                total_users=total_users,
                total_assessments=total_assessments,
                total_responses=total_responses,
                completed_responses=completed_responses,
                completion_rate=completion_rate,
                recent_activity_30d=recent_activity,
                popular_assessments=popular_assessments,
            )

        except Exception as e:
            logger.error(f"Error calculating system analytics: {e}")
            raise


# Factory function to create service instance with repositories
def create_analytics_service(db: AsyncSession) -> AnalyticsService:
    """
    Factory function to create analytics service with repository dependencies

    Args:
        db: Database session

    Returns:
        AnalyticsService instance with injected repositories
    """
    return AnalyticsService(
        user_repo=UserRepository(db),
        assessment_repo=AssessmentRepository(db),
        response_repo=ResponseRepository(db),
        team_repo=TeamRepository(db),
    )
