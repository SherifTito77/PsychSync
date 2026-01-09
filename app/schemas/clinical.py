"""
Clinical Assessment Schemas
Pydantic models for clinical assessment endpoints
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# Mental Health Screening Schemas
class MentalHealthScreeningRequest(BaseModel):
    screening_type: str
    screening_tools: list[str]
    responses: dict[str, list[Any]]
    context: dict[str, Any] = {}


class MentalHealthScreeningResponse(BaseModel):
    success: bool
    user_id: int
    screening_type: str
    screening_tools: list[str]
    screening_results: dict[str, Any]
    risk_assessment: dict[str, Any]
    overall_risk_level: str
    recommendations: list[str]
    crisis_alert: dict[str, Any] | None = None
    next_screening_date: datetime | None = None
    screened_at: datetime
    clinical_disclaimer: str


# Wellness Assessment Schemas
class WellnessAssessmentRequest(BaseModel):
    assessment_type: str
    wellness_dimensions: list[str]
    responses: dict[str, Any]
    biometric_data: dict[str, Any] | None = None
    lifestyle_data: dict[str, Any] | None = None


class WellnessAssessmentResponse(BaseModel):
    success: bool
    user_id: int
    assessment_type: str
    wellness_dimensions: list[str]
    wellness_scores: dict[str, float]
    overall_wellness_score: float
    dimension_insights: dict[str, Any]
    strengths: list[str]
    improvement_areas: list[str]
    wellness_recommendations: list[str]
    burnout_risk: dict[str, Any]
    action_plan: dict[str, Any]
    assessed_at: datetime


# Crisis Alert Schemas
class CrisisAlertRequest(BaseModel):
    alert_type: str
    severity_indicators: dict[str, Any]
    immediate_context: dict[str, Any] = {}


class CrisisAlertResponse(BaseModel):
    success: bool
    user_id: int
    alert_type: str
    crisis_assessment: dict[str, Any]
    immediate_actions: list[str]
    emergency_resources: dict[str, Any]
    safety_plan: dict[str, Any]
    professional_intervention: dict[str, Any]
    follow_up_schedule: dict[str, Any] | None = None
    crisis_hotlines: list[dict[str, str]]
    response_generated_at: datetime
    disclaimer: str


# Mental Health Trends Schemas
class MentalHealthTrendRequest(BaseModel):
    screening_types: list[str]
    start_date: datetime
    end_date: datetime
    trend_period: str = "monthly"


class MentalHealthTrendResponse(BaseModel):
    success: bool
    user_id: int
    analysis_period: dict[str, datetime]
    screening_types: list[str]
    trend_analysis: dict[str, Any]
    significant_changes: list[dict[str, Any]]
    protective_factors: list[str]
    risk_factors: list[str]
    trend_recommendations: list[str]
    trajectory_prediction: dict[str, Any]
    next_assessment_date: datetime | None = None
    analyzed_at: datetime


# Wellness Plan Schemas
class WellnessPlanRequest(BaseModel):
    focus_areas: list[str]
    user_preferences: dict[str, Any] = {}
    time_frame: str = "3_months"


class WellnessPlanResponse(BaseModel):
    success: bool
    user_id: int
    wellness_baseline: dict[str, Any]
    wellness_goals: dict[str, list[dict[str, Any]]]
    action_steps: dict[str, list[dict[str, Any]]]
    wellness_resources: dict[str, Any]
    monitoring_plan: dict[str, Any]
    milestones: list[dict[str, Any]]
    estimated_timeline: str
    success_factors: list[str]
    potential_barriers: list[str]
    plan_created_at: datetime
    next_review_date: datetime | None = None


# Clinical Resource Schemas
class ClinicalResourceRequest(BaseModel):
    resource_type: str | None = None
    condition: str | None = None
    user_location: str | None = None


class ClinicalResourceResponse(BaseModel):
    success: bool
    resource_type: str | None
    condition: str | None
    user_location: str | None
    resources: dict[str, Any]
    resource_categories: list[str]
    last_updated: datetime
    disclaimer: str
