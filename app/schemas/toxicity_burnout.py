# app/schemas/toxicity_burnout.py
"""
Pydantic schemas for Toxicity & Burnout Intelligence API.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SignalBreakdown(BaseModel):
    """Individual signal score with label."""

    name: str
    score: float = Field(ge=0, le=100)
    weight: float


class ToxicityBurnoutCompositeResponse(BaseModel):
    """Full composite risk response."""

    burnout_score: float = Field(ge=0, le=100)
    toxicity_score: float = Field(ge=0, le=100)
    combined_risk: float = Field(ge=0, le=100)
    cross_contamination_multiplier: float = Field(ge=1.0)

    burnout_label: str
    toxicity_label: str
    combined_label: str

    burnout_signals: dict[str, float]
    toxicity_signals: dict[str, float]
    active_burnout_sources: int
    active_toxicity_sources: int

    overlap_patterns: list[str]
    recommendations: list[str]


class ToxicitySignalsResponse(BaseModel):
    """Toxicity-only signals breakdown."""

    toxicity_score: float = Field(ge=0, le=100)
    toxicity_label: str
    signals: dict[str, float]
    active_sources: int


class BurnoutPassiveResponse(BaseModel):
    """Passive burnout signals from infrastructure metadata."""

    burnout_score: float = Field(ge=0, le=100)
    burnout_label: str
    signals: dict[str, float]
    active_sources: int


class DataSourceStatus(BaseModel):
    """Availability status of a single data source."""

    name: str
    available: bool
    category: str = Field(description="toxicity | burnout")


class DataSourcesResponse(BaseModel):
    """All data source connector statuses."""

    sources: list[DataSourceStatus]
    total_available: int
    total_configured: int


class ToxicityBurnoutSnapshotResponse(BaseModel):
    """Persisted snapshot for trend display."""

    id: UUID
    snapshot_date: date
    scope: str
    burnout_score: float
    toxicity_score: float
    combined_risk: float
    cross_contamination_multiplier: float
    burnout_label: str
    toxicity_label: str
    combined_label: str
    active_burnout_sources: int
    active_toxicity_sources: int
    created_at: datetime


class ToxicityBurnoutTrendResponse(BaseModel):
    """Trend over time."""

    snapshots: list[ToxicityBurnoutSnapshotResponse]
    trend_direction: str = Field(
        description="improving | stable | declining | critical"
    )
    period_days: int


class AlertResponse(BaseModel):
    """Single alert from overlap detection."""

    id: UUID
    severity: str
    alert_type: str
    description: str
    burnout_score_at_alert: float | None
    toxicity_score_at_alert: float | None
    combined_risk_at_alert: float | None
    is_resolved: bool
    created_at: datetime


class AlertsListResponse(BaseModel):
    """List of active alerts."""

    alerts: list[AlertResponse]
    total: int
    unresolved: int
