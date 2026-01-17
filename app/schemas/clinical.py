"""
Clinical Assessment Schemas
Pydantic models for clinical assessment endpoints and screening tools
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


# ============================================================================
# SPECIFIC SCREENING TOOL SCHEMAS
# ============================================================================

class PHQ9Request(BaseModel):
    """
    Patient Health Questionnaire-9 (Depression)
    9 items, 0-3 scale
    """
    q1_interest: int = Field(..., ge=0, le=3)
    q2_depressed: int = Field(..., ge=0, le=3)
    q3_sleep: int = Field(..., ge=0, le=3)
    q4_energy: int = Field(..., ge=0, le=3)
    q5_appetite: int = Field(..., ge=0, le=3)
    q6_self_worth: int = Field(..., ge=0, le=3)
    q7_concentration: int = Field(..., ge=0, le=3)
    q8_motor: int = Field(..., ge=0, le=3)
    q9_suicide: int = Field(..., ge=0, le=3)


class GAD7Request(BaseModel):
    """
    Generalized Anxiety Disorder-7
    7 items, 0-3 scale
    """
    q1_nervous: int = Field(..., ge=0, le=3)
    q2_control_worry: int = Field(..., ge=0, le=3)
    q3_worry_too_much: int = Field(..., ge=0, le=3)
    q4_trouble_relaxing: int = Field(..., ge=0, le=3)
    q5_restless: int = Field(..., ge=0, le=3)
    q6_irritable: int = Field(..., ge=0, le=3)
    q7_afraid: int = Field(..., ge=0, le=3)


class CSSRSRequest(BaseModel):
    """
    Columbia-Suicide Severity Rating Scale
    CRITICAL: Any positive triggers crisis protocol
    """
    q1_wish_dead: bool
    q2_nonspecific_thoughts: bool
    q3_active_ideation: bool
    q4_intent: bool
    q5_plan: bool
    q11_actual_attempt: bool
    q12_preparatory_acts: bool
    q13_aborted_attempt: bool


class ASRSRequest(BaseModel):
    """
    Adult ADHD Self-Report Scale v1.1
    18 items, 0-4 scale (Never to Very Often)
    Part A: Inattention (Questions 1-9)
    Part B: Hyperactivity-Impulsivity (Questions 10-18)
    """
    # Part A: Inattention Symptoms (1-9)
    q1: int = Field(..., ge=0, le=4, description="Trouble wrapping up final details")
    q2: int = Field(..., ge=0, le=4, description="Difficulty getting things in order")
    q3: int = Field(..., ge=0, le=4, description="Problems remembering appointments")
    q4: int = Field(..., ge=0, le=4, description="Avoid/delay starting complex tasks")
    q5: int = Field(..., ge=0, le=4, description="Fidget or squirm when sitting")
    q6: int = Field(..., ge=0, le=4, description="Feel overly active/driven by motor")
    q7: int = Field(..., ge=0, le=4, description="Make careless mistakes")
    q8: int = Field(..., ge=0, le=4, description="Difficulty keeping attention on boring work")
    q9: int = Field(..., ge=0, le=4, description="Difficulty concentrating when spoken to")

    # Part B: Hyperactivity-Impulsivity (10-18)
    q10: int = Field(..., ge=0, le=4, description="Leave seat when expected to remain")
    q11: int = Field(..., ge=0, le=4, description="Feel restless/fidgety")
    q12: int = Field(..., ge=0, le=4, description="Difficulty unwinding/relaxing")
    q13: int = Field(..., ge=0, le=4, description="Talk too much in social situations")
    q14: int = Field(..., ge=0, le=4, description="Finish others' sentences")
    q15: int = Field(..., ge=0, le=4, description="Difficulty waiting turn")
    q16: int = Field(..., ge=0, le=4, description="Interrupt others")
    q17: int = Field(..., ge=0, le=4, description="Difficulty focusing with distractions")
    q18: int = Field(..., ge=0, le=4, description="Misplace or lose things")


class ISIRequest(BaseModel):
    """
    Insomnia Severity Index
    7 items, 0-4 scale (No problem to Very severe problem)
    Assesses insomnia severity and daytime impairment over past 2 weeks
    """
    q1: int = Field(..., ge=0, le=4, description="Difficulty falling asleep")
    q2: int = Field(..., ge=0, le=4, description="Difficulty staying asleep")
    q3: int = Field(..., ge=0, le=4, description="Problems waking up too early")
    q4: int = Field(..., ge=0, le=4, description="Satisfaction with sleep pattern")
    q5: int = Field(..., ge=0, le=4, description="Noticeability to others")
    q6: int = Field(..., ge=0, le=4, description="Worried/distressed about sleep")
    q7: int = Field(..., ge=0, le=4, description="Interference with daily functioning")


class ScreeningResponse(BaseModel):
    """
    Standard response for all screening tools
    Includes scoring, risk assessment, and crisis alerts
    """
    id: UUID
    screening_type: str
    total_score: Optional[float] = None
    severity_level: str
    risk_level: str
    interpretation: str
    recommendations: List[str]
    crisis_alert: bool
    risk_flags: List[str]
    completed_at: datetime


# ============================================================================
# BASE CLINICAL SCHEMAS (from original file)
# ============================================================================


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


# ============================================================================
# ADVANCED CLINICAL ASSESSMENT SCHEMAS
# ============================================================================

from typing import Dict, Optional
from pydantic import Field


class LSASItemRequest(BaseModel):
    """Individual LSAS item with fear and avoidance ratings"""
    fear: int = Field(..., ge=0, le=3, description="Fear level: 0=None, 1=Mild, 2=Moderate, 3=Severe")
    avoidance: int = Field(..., ge=0, le=3, description="Avoidance level: 0=Never, 1=Occasionally, 2=Often, 3=Usually")


class LSASRequest(BaseModel):
    """
    Liebowitz Social Anxiety Scale Request
    24 items, each with fear and avoidance ratings
    """
    item_1: LSASItemRequest
    item_2: LSASItemRequest
    item_3: LSASItemRequest
    item_4: LSASItemRequest
    item_5: LSASItemRequest
    item_6: LSASItemRequest
    item_7: LSASItemRequest
    item_8: LSASItemRequest
    item_9: LSASItemRequest
    item_10: LSASItemRequest
    item_11: LSASItemRequest
    item_12: LSASItemRequest
    item_13: LSASItemRequest
    item_14: LSASItemRequest
    item_15: LSASItemRequest
    item_16: LSASItemRequest
    item_17: LSASItemRequest
    item_18: LSASItemRequest
    item_19: LSASItemRequest
    item_20: LSASItemRequest
    item_21: LSASItemRequest
    item_22: LSASItemRequest
    item_23: LSASItemRequest
    item_24: LSASItemRequest


class EAT26BehavioralQuestions(BaseModel):
    """EAT-26 Behavioral questions for referral determination"""
    weight_loss_6months: bool = Field(False, description="Lost 20+ lbs in past 6 months")
    binge_eating: str = Field("never", description="Binge eating frequency")
    vomiting: str = Field("never", description="Self-induced vomiting frequency")
    laxatives: str = Field("never", description="Laxative use frequency")
    exercise: str = Field("never", description="Excessive exercise frequency")
    bmi_concern: bool = Field(False, description="Concern about BMI or weight")


class EAT26Request(BaseModel):
    """
    Eating Attitudes Test-26 Request
    26 items, 6-point scale (Always to Never)
    """
    responses: Dict[int, int] = Field(..., description="Item responses 1-26, scale 0-5")
    behavioral_questions: Optional[EAT26BehavioralQuestions] = None


class YBOCSRequest(BaseModel):
    """
    Yale-Brown Obsessive Compulsive Scale Request
    10 items (5 obsessions, 5 compulsions), 0-4 scale each
    """
    item_1_time_obsessions: int = Field(..., ge=0, le=4)
    item_2_interference_obsessions: int = Field(..., ge=0, le=4)
    item_3_distress_obsessions: int = Field(..., ge=0, le=4)
    item_4_resistance_obsessions: int = Field(..., ge=0, le=4)
    item_5_control_obsessions: int = Field(..., ge=0, le=4)
    item_6_time_compulsions: int = Field(..., ge=0, le=4)
    item_7_interference_compulsions: int = Field(..., ge=0, le=4)
    item_8_distress_compulsions: int = Field(..., ge=0, le=4)
    item_9_resistance_compulsions: int = Field(..., ge=0, le=4)
    item_10_control_compulsions: int = Field(..., ge=0, le=4)


# ============================================================================
# NOTIFICATION SYSTEM SCHEMAS
# ============================================================================

class NotificationPreferenceCreate(BaseModel):
    """Create or update notification preferences"""
    email_enabled: bool = True
    push_enabled: bool = False
    sms_enabled: bool = False
    in_app_enabled: bool = True
    notify_on_crisis_alert: bool = True
    notify_on_high_risk: bool = True
    notify_on_moderate_risk: bool = False
    notify_on_pending_review: bool = True
    notify_on_weekly_summary: bool = False
    min_severity_for_notification: str = "moderate"  # low, moderate, high, critical
    quiet_hours_enabled: bool = True
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    timezone: str = "America/New_York"
    bypass_quiet_hours_for_critical: bool = True

    @validator('min_severity_for_notification')
    def validate_severity(cls, v):
        valid_levels = ['low', 'moderate', 'high', 'critical']
        if v not in valid_levels:
            raise ValueError(f'must be one of {valid_levels}')
        return v


class NotificationPreferenceResponse(BaseModel):
    """Notification preferences response"""
    id: UUID
    user_id: UUID
    email_enabled: bool
    push_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    notify_on_crisis_alert: bool
    notify_on_high_risk: bool
    notify_on_moderate_risk: bool
    notify_on_pending_review: bool
    notify_on_weekly_summary: bool
    min_severity_for_notification: str
    quiet_hours_enabled: bool
    quiet_hours_start: time
    quiet_hours_end: time
    timezone: str
    bypass_quiet_hours_for_critical: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Notification response"""
    id: UUID
    recipient_id: UUID
    notification_type: str
    entity_type: str
    entity_id: Optional[UUID]
    title: str
    message: str
    priority: str
    channel: str
    sent_at: Optional[datetime]
    delivery_status: str
    read: bool
    read_at: Optional[datetime]
    action_taken: Optional[str]
    action_taken_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    total_sent: int
    total_delivered: int
    total_failed: int
    unread_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
