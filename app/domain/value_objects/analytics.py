"""
Domain Value Objects for Analytics

These objects represent pure domain concepts with no infrastructure concerns.
They are used to pass data between layers without exposing internal structures.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ResponseSummary:
    """Summary of a user's assessment responses"""

    response_id: UUID
    assessment_id: UUID
    assessment_title: str
    submitted_at: datetime | None
    score: float | None
    time_taken: int | None


@dataclass(frozen=True)
class UserAnalytics:
    """
    Analytics data for a specific user.

    This is a domain object that contains calculated analytics.
    It has no knowledge of how data was fetched or cached.
    """

    user_id: UUID
    total_responses: int
    completed_responses: int
    in_progress_responses: int
    average_score: float | None
    response_history: list[ResponseSummary]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization (presentation concern)"""
        return {
            "user_id": str(self.user_id),
            "total_responses": self.total_responses,
            "completed_responses": self.completed_responses,
            "in_progress_responses": self.in_progress_responses,
            "average_score": self.average_score,
            "response_history": [
                {
                    "response_id": str(r.response_id),
                    "assessment_id": str(r.assessment_id),
                    "assessment_title": r.assessment_title,
                    "submitted_at": (
                        r.submitted_at.isoformat() if r.submitted_at else None
                    ),
                    "score": r.score,
                    "time_taken": r.time_taken,
                }
                for r in self.response_history
            ],
        }


@dataclass(frozen=True)
class ScoreDistribution:
    """Distribution of scores across ranges"""

    range_label: str
    count: int


@dataclass(frozen=True)
class AssessmentAnalytics:
    """
    Analytics data for a specific assessment.

    Domain object containing calculated statistics for an assessment.
    """

    assessment_id: UUID
    assessment_title: str
    total_responses: int
    total_assignments: int
    average_score: float | None
    average_time: float | None
    completion_rate: float
    score_distribution: list[ScoreDistribution]
    recent_responses: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization"""
        return {
            "assessment_id": str(self.assessment_id),
            "assessment_title": self.assessment_title,
            "total_responses": self.total_responses,
            "total_assignments": self.total_assignments,
            "average_score": self.average_score,
            "average_time": self.average_time,
            "completion_rate": self.completion_rate,
            "score_distribution": [
                {"range": sd.range_label, "count": sd.count}
                for sd in self.score_distribution
            ],
            "recent_responses": self.recent_responses,
        }


@dataclass(frozen=True)
class MemberPerformance:
    """Performance metrics for a team member"""

    user_id: UUID
    user_name: str
    completed_assessments: int
    average_score: float | None


@dataclass(frozen=True)
class TeamAnalytics:
    """
    Analytics data for a specific team.

    Domain object containing team-level statistics and member performance.
    """

    team_id: int
    total_members: int
    total_assessments: int
    total_responses: int
    completed_responses: int
    average_score: float | None
    member_performance: list[MemberPerformance]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization"""
        return {
            "team_id": self.team_id,
            "total_members": self.total_members,
            "total_assessments": self.total_assessments,
            "total_responses": self.total_responses,
            "completed_responses": self.completed_responses,
            "average_score": self.average_score,
            "member_performance": [
                {
                    "user_id": str(mp.user_id),
                    "user_name": mp.user_name,
                    "completed_assessments": mp.completed_assessments,
                    "average_score": mp.average_score,
                }
                for mp in self.member_performance
            ],
        }


@dataclass(frozen=True)
class PopularAssessment:
    """Represents a popular assessment with response count"""

    id: UUID
    title: str
    response_count: int


@dataclass(frozen=True)
class SystemAnalytics:
    """
    System-wide analytics data.

    Domain object containing platform-level statistics.
    """

    total_users: int
    total_assessments: int
    total_responses: int
    completed_responses: int
    completion_rate: float
    recent_activity_30d: int
    popular_assessments: list[PopularAssessment]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization"""
        return {
            "total_users": self.total_users,
            "total_assessments": self.total_assessments,
            "total_responses": self.total_responses,
            "completed_responses": self.completed_responses,
            "completion_rate": self.completion_rate,
            "recent_activity_30d": self.recent_activity_30d,
            "popular_assessments": [
                {
                    "id": str(pa.id),
                    "title": pa.title,
                    "response_count": pa.response_count,
                }
                for pa in self.popular_assessments
            ],
        }
