"""
Clinical Assessment Schemas
Pydantic models for clinical assessment endpoints
"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

# Mental Health Screening Schemas
class MentalHealthScreeningRequest(BaseModel):
    screening_type: str
    screening_tools: List[str]
    responses: Dict[str, List[Any]]
    context: Dict[str, Any] = {}

class MentalHealthScreeningResponse(BaseModel):
    success: bool
    user_id: int
    screening_type: str
    screening_tools: List[str]
    screening_results: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    overall_risk_level: str
    recommendations: List[str]
    crisis_alert: Optional[Dict[str, Any]] = None
    next_screening_date: Optional[datetime] = None
    screened_at: datetime
    clinical_disclaimer: str

# Wellness Assessment Schemas
class WellnessAssessmentRequest(BaseModel):
    assessment_type: str
    wellness_dimensions: List[str]
    responses: Dict[str, Any]
    biometric_data: Optional[Dict[str, Any]] = None
    lifestyle_data: Optional[Dict[str, Any]] = None

class WellnessAssessmentResponse(BaseModel):
    success: bool
    user_id: int
    assessment_type: str
    wellness_dimensions: List[str]
    wellness_scores: Dict[str, float]
    overall_wellness_score: float
    dimension_insights: Dict[str, Any]
    strengths: List[str]
    improvement_areas: List[str]
    wellness_recommendations: List[str]
    burnout_risk: Dict[str, Any]
    action_plan: Dict[str, Any]
    assessed_at: datetime

# Crisis Alert Schemas
class CrisisAlertRequest(BaseModel):
    alert_type: str
    severity_indicators: Dict[str, Any]
    immediate_context: Dict[str, Any] = {}

class CrisisAlertResponse(BaseModel):
    success: bool
    user_id: int
    alert_type: str
    crisis_assessment: Dict[str, Any]
    immediate_actions: List[str]
    emergency_resources: Dict[str, Any]
    safety_plan: Dict[str, Any]
    professional_intervention: Dict[str, Any]
    follow_up_schedule: Optional[Dict[str, Any]] = None
    crisis_hotlines: List[Dict[str, str]]
    response_generated_at: datetime
    disclaimer: str

# Mental Health Trends Schemas
class MentalHealthTrendRequest(BaseModel):
    screening_types: List[str]
    start_date: datetime
    end_date: datetime
    trend_period: str = "monthly"

class MentalHealthTrendResponse(BaseModel):
    success: bool
    user_id: int
    analysis_period: Dict[str, datetime]
    screening_types: List[str]
    trend_analysis: Dict[str, Any]
    significant_changes: List[Dict[str, Any]]
    protective_factors: List[str]
    risk_factors: List[str]
    trend_recommendations: List[str]
    trajectory_prediction: Dict[str, Any]
    next_assessment_date: Optional[datetime] = None
    analyzed_at: datetime

# Wellness Plan Schemas
class WellnessPlanRequest(BaseModel):
    focus_areas: List[str]
    user_preferences: Dict[str, Any] = {}
    time_frame: str = "3_months"

class WellnessPlanResponse(BaseModel):
    success: bool
    user_id: int
    wellness_baseline: Dict[str, Any]
    wellness_goals: Dict[str, List[Dict[str, Any]]]
    action_steps: Dict[str, List[Dict[str, Any]]]
    wellness_resources: Dict[str, Any]
    monitoring_plan: Dict[str, Any]
    milestones: List[Dict[str, Any]]
    estimated_timeline: str
    success_factors: List[str]
    potential_barriers: List[str]
    plan_created_at: datetime
    next_review_date: Optional[datetime] = None

# Clinical Resource Schemas
class ClinicalResourceRequest(BaseModel):
    resource_type: Optional[str] = None
    condition: Optional[str] = None
    user_location: Optional[str] = None

class ClinicalResourceResponse(BaseModel):
    success: bool
    resource_type: Optional[str]
    condition: Optional[str]
    user_location: Optional[str]
    resources: Dict[str, Any]
    resource_categories: List[str]
    last_updated: datetime
    disclaimer: str