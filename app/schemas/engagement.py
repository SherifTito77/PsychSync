"""
Engagement Schemas
Schemas for employee engagement analysis and scoring
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IndividualEngagementScore(BaseModel):
    """Individual engagement score for an employee"""

    employee_id: str
    employee_name: str
    department: str
    overall_score: float
    job_satisfaction: float
    work_life_balance: float
    management_support: float
    career_growth: float
    compensation_satisfaction: float
    team_collaboration: float
    survey_date: str


class EngagementAnalytics(BaseModel):
    """Engagement analytics for a team or organization"""

    scores: List[IndividualEngagementScore]
    summary: Dict[str, float]
    participation_rate: float
    last_updated: datetime


class EngagementSurveyCreate(BaseModel):
    """Schema for creating an engagement survey template"""

    title: str = "Annual Employee Engagement Survey"
    description: Optional[str] = (
        "Survey to measure employee satisfaction and workplace sentiment"
    )
    organization_id: UUID
