# app/schemas/onboarding.py
# Pydantic schemas for value-first onboarding experience
from pydantic import BaseModel, Field

import re
from typing import Optional
from pydantic import field_validator

def validate_password_strength(password: str) -> str:
    """
    Validate password strength

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Password if valid

    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one number")

    if not re.search(r'''[!@#$%^&*()_+\-=\[\]{};':"|,.<>?]''', password):
        raise ValueError("Password must contain at least one special character")

    return password

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    MANAGER = "manager"
    HR = "hr"
    LEAD = "lead"
    MEMBER = "member"
    EXECUTIVE = "executive"

class TeamChallenge(str, Enum):
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    TURNOVER = "turnover"
    COLLABORATION = "collaboration"
    CONFLICT = "conflict"

class QuickAssessmentRequest(BaseModel):
    role: UserRole = Field(..., description="User's role in the organization")
    challenge: TeamChallenge = Field(..., description="Primary team challenge")
    team_size: Optional[str] = Field(None, description="Team size (e.g., '5-10', '10-20')")
    industry: Optional[str] = Field(None, description="Industry sector")
    session_id: Optional[str] = Field(None, description="Anonymous session identifier")
    referrer: Optional[str] = Field(None, description="Traffic source")

class Insight(BaseModel):
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    impact_level: str = Field(..., description="High/Medium/Low impact")
    financial_impact: Optional[float] = Field(None, description="Estimated financial impact")
    time_to_implement: Optional[str] = Field(None, description="Time to see results")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in insight")

class Recommendation(BaseModel):
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="What to do")
    priority: str = Field(..., description="High/Medium/Low priority")
    effort: str = Field(..., description="Low/Medium/High effort")
    expected_outcome: str = Field(..., description="Expected result")

class QuickInsights(BaseModel):
    primary_benefit: str = Field(..., description="Main value proposition")
    risk_areas: List[str] = Field(default_factory=list, description="Identified risks")
    strengths: List[str] = Field(default_factory=list, description="Team strengths")
    opportunities: List[str] = Field(default_factory=list, description="Growth opportunities")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Action items")
    conversion_probability: float = Field(..., ge=0, le=1, description="Likelihood to convert")
    estimated_time_to_value: str = Field(..., description="Time to see value")

class QuickAssessmentResponse(BaseModel):
    success: bool = Field(..., description="Request successful")
    insights: QuickInsights = Field(..., description="Generated insights")
    next_steps: List[str] = Field(..., description="Recommended next actions")
    value_proposition: str = Field(..., description="Personalized value proposition")
    estimated_time_to_value: str = Field(..., description="Time to see value")

class TeamInsightRequest(BaseModel):
    team_id: Optional[str] = Field(None, description="Team identifier")
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Assessment responses")
    team_composition: Optional[List[Dict[str, Any]]] = Field(None, description="Team member profiles")
    session_id: Optional[str] = Field(None, description="Session identifier")

class TeamProfile(BaseModel):
    team_size: int = Field(..., description="Number of team members")
    avg_experience: float = Field(..., description="Average years of experience")
    personality_distribution: Dict[str, float] = Field(..., description="Personality type distribution")
    communication_style: str = Field(..., description="Primary communication style")
    work_preference: str = Field(..., description="Team work preference")
    current_performance: float = Field(..., ge=0, le=1, description="Current performance score")
    potential_performance: float = Field(..., ge=0, le=1, description="Potential performance score")

class DetailedInsight(BaseModel):
    category: str = Field(..., description="Insight category")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    impact_score: float = Field(..., ge=0, le=1, description="Impact severity")
    urgency: str = Field(..., description="Low/Medium/High urgency")

class ActionItem(BaseModel):
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="What to do")
    responsible: Optional[str] = Field(None, description="Who should do it")
    timeline: str = Field(..., description="When to do it")
    resources: List[str] = Field(default_factory=list, description="Required resources")
    success_metrics: List[str] = Field(default_factory=list, description="How to measure success")
    priority_score: float = Field(..., ge=0, le=1, description="Priority ranking")

class PredictedOutcome(BaseModel):
    metric: str = Field(..., description="Performance metric")
    current_value: float = Field(..., description="Current value")
    predicted_value: float = Field(..., description="Predicted value after changes")
    confidence_interval: List[float] = Field(..., description="Confidence range")
    timeframe: str = Field(..., description="Time to achieve")

class ImplementationRoadmap(BaseModel):
    phase: str = Field(..., description="Implementation phase")
    duration: str = Field(..., description="Phase duration")
    activities: List[str] = Field(..., description="Activities in this phase")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisites")
    expected_outcomes: List[str] = Field(..., description="Expected results")

class TeamInsightResponse(BaseModel):
    success: bool = Field(..., description="Request successful")
    team_profile: TeamProfile = Field(..., description="Team behavioral profile")
    detailed_insights: List[DetailedInsight] = Field(..., description="Detailed team insights")
    action_items: List[ActionItem] = Field(..., description="Recommended actions")
    predicted_outcomes: List[PredictedOutcome] = Field(..., description="Expected improvements")
    implementation_roadmap: List[ImplementationRoadmap] = Field(..., description="Implementation plan")

class OnboardingAnalyticsEvent(BaseModel):
    event_type: str = Field(..., description="Type of analytics event")
    session_id: Optional[str] = Field(None, description="Session identifier")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")

class OnboardingStatus(BaseModel):
    is_authenticated: bool = Field(..., description="User is logged in")
    onboarding_complete: bool = Field(..., description="Onboarding finished")
    current_step: Optional[str] = Field(None, description="Current onboarding step")
    completed_steps: List[str] = Field(default_factory=list, description="Finished steps")
    recommended_actions: List[str] = Field(..., description="Next recommended actions")
    progress_percentage: float = Field(..., ge=0, le=1, description="Completion progress")
    estimated_remaining_time: Optional[str] = Field(None, description="Time to complete")

class ValueMetrics(BaseModel):
    productivity_improvement: float = Field(..., description="Productivity increase %")
    communication_efficiency: float = Field(..., description="Communication improvement %")
    conflict_reduction: float = Field(..., description="Conflict reduction %")
    turnover_risk_reduction: float = Field(..., description="Turnover risk reduction %")
    team_satisfaction_score: float = Field(..., ge=0, le=1, description="Team satisfaction")
    roi_estimate: float = Field(..., description="Return on investment estimate")
    time_to_value: str = Field(..., description="Time to see value")
    monthly_value_created: float = Field(..., description="Value created per month")

# Streamlined registration schemas
class StreamlinedRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="User's full name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., write_only=True, min_length=8, description="Password")
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    company_name: Optional[str] = Field(None, description="Company name")
    role: UserRole = Field(..., description="User's role")
    primary_challenge: TeamChallenge = Field(..., description="Main team challenge")
    referrer: Optional[str] = Field(None, description="How they found us")
    accept_terms: bool = Field(..., description="Terms accepted")
    marketing_consent: bool = Field(False, description="Marketing consent")

# A/B testing schemas
class OnboardingVariant(BaseModel):
    variant_id: str = Field(..., description="A/B test variant ID")
    test_name: str = Field(..., description="Name of the test")
    version: str = Field(..., description="Variant version")
    features: List[str] = Field(..., description="Features enabled in this variant")

class ConversionEvent(BaseModel):
    event_type: str = Field(..., description="Type of conversion event")
    variant_id: str = Field(..., description="A/B test variant")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    step: str = Field(..., description="Onboarding step")
    success: bool = Field(..., description="Event successful")
    duration_seconds: Optional[float] = Field(None, description="Time taken")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional data")
