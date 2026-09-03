"""
Behavioral Analysis Schemas
Pydantic models for behavioral analysis endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection"""

    entity_id: str = Field(..., description="ID of the entity (user, team, etc.)")
    entity_type: str = Field(
        ..., description="Type of entity (user, team, organization)"
    )
    metric_name: str = Field(..., description="Name of the metric to analyze")
    time_period_days: int = Field(default=30, ge=1, le=365)
    threshold_std_dev: float = Field(default=2.5, ge=1.0, le=5.0)


class AnomalyDetectionResponse(BaseModel):
    """Response model for anomaly detection"""

    has_anomaly: bool
    anomaly_score: float
    anomaly_description: Optional[str]
    baseline_value: float
    current_value: float
    deviation_percentage: float
    confidence: float
    recommended_actions: List[str]


class BehavioralPatternRequest(BaseModel):
    """Request model for behavioral pattern analysis"""

    analysis_scope: str = Field(..., description="Scope: 'individual' or 'team'")
    user_id: Optional[str] = Field(
        None, description="User ID (for individual analysis)"
    )
    team_id: Optional[int] = Field(None, description="Team ID (for team analysis)")
    time_period: str = Field(default="30d", description="Time period for analysis")
    behavioral_categories: List[str] = Field(
        default_factory=lambda: ["temporal", "sequential", "social"],
        description="Categories of behaviors to analyze",
    )
    analysis_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional analysis options"
    )


class BehavioralPatternResponse(BaseModel):
    """Response model for behavioral pattern analysis"""

    success: bool
    analysis_scope: str
    time_period: str
    behavioral_categories: List[str]
    patterns: Dict[str, Any]
    confidence_scores: Dict[str, float]
    recommendations: List[str]
    analyzed_at: datetime


class BehavioralTrendRequest(BaseModel):
    """Request model for behavioral trend analysis"""

    entity_id: str = Field(..., description="ID of the entity")
    entity_type: str = Field(..., description="Type of entity")
    metric_names: List[str] = Field(..., description="Metrics to analyze")
    time_period_days: int = Field(default=90, ge=1, le=365)


class BehavioralTrendResponse(BaseModel):
    """Response model for behavioral trend analysis"""

    trends: Dict[str, Any]
    slope_direction: str
    trend_significance: float
    predictions: Optional[Dict[str, Any]]
    confidence_interval: List[float]


class TeamBehavioralInsightsRequest(BaseModel):
    """Request model for team behavioral insights"""

    team_id: UUID = Field(..., description="Team ID")
    time_period: int = Field(
        default=30, ge=1, le=365, description="Time period in days"
    )
    insight_categories: List[str] = Field(
        default_factory=list, description="Categories of insights to generate"
    )


class TeamBehavioralInsightsResponse(BaseModel):
    """Response model for team behavioral insights"""

    team_id: UUID
    insights: Dict[str, Any]
    behavioral_metrics: Dict[str, float]
    collaboration_score: float
    productivity_score: float
    recommendations: List[str]
    analysis_period_days: int
    generated_at: datetime


class OrganizationalBehavioralReport(BaseModel):
    """Request model for organizational behavioral report"""

    organization_id: UUID = Field(..., description="Organization ID")
    time_period_days: int = Field(default=90, ge=1, le=365)
    include_teams: bool = True
    include_benchmarks: bool = True
