# app/schemas/corporate_data_sources.py
"""
Schemas for Corporate Data Source Integration API
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class PrivacyLevel(str, Enum):
    """Privacy levels for data sources"""

    METADATA_ONLY = "metadata_only"
    ANONYMIZED = "anonymized"
    FULL = "full"


class SyncStatus(str, Enum):
    """Sync status for data sources"""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    PENDING = "pending"
    DISABLED = "disabled"


class DataSourceType(str, Enum):
    """Types of corporate data sources"""

    EMAIL_METADATA = "email_metadata"
    SLACK_MESSAGES = "slack_messages"
    TEAMS_MESSAGES = "teams_messages"
    ZOOM_TRANSCRIPTS = "zoom_transcripts"
    CALENDAR_EVENTS = "calendar_events"
    JIRA_ACTIVITY = "jira_activity"
    GITHUB_COMMITS = "github_commits"
    CONFLUENCE_EDITS = "confluence_edits"
    ASANA_TASKS = "asana_tasks"
    MONDAY_PROJECTS = "monday_projects"
    WORKDAY_DATA = "workday_data"
    BAMBOO_HR = "bamboo_hr"
    ADP_ATTENDANCE = "adp_attendance"
    TIME_TRACKING = "time_tracking"
    PTO_REQUESTS = "pto_requests"
    PERFORMANCE_REVIEWS = "performance_reviews"
    PULSE_SURVEYS = "pulse_surveys"
    ENGAGEMENT_SURVEYS = "engagement_surveys"
    EXIT_INTERVIEWS = "exit_interviews"
    ONE_ON_ONE_NOTES = "one_on_one_notes"
    WEARABLE_DATA = "wearable_data"
    WELLNESS_APP_DATA = "wellness_app_data"
    MENTAL_HEALTH_CHECKS = "mental_health_checks"
    VPN_LOGS = "vpn_logs"
    BADGE_SWIPES = "badge_swipes"
    SYSTEM_LOGIN_TIMES = "system_login_times"
    APPLICATION_USAGE = "application_usage"
    BONUS_DATA = "bonus_data"
    PROMOTION_DATA = "promotion_data"
    COMPENSATION_CHANGES = "compensation_changes"
    TRAINING_COMPLETIONS = "training_completions"
    CERTIFICATION_DATA = "certification_data"
    SKILL_ASSESSMENTS = "skill_assessments"


class BehavioralSignal(BaseModel):
    """A behavioral signal extracted from data"""

    signal_name: str = Field(..., description="Name of the behavioral signal")
    value: float = Field(..., description="Signal value (normalized 0-1)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    timestamp: datetime = Field(..., description="When the signal was detected")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class IntegrationConfig(BaseModel):
    """Configuration for a data source integration"""

    source_type: DataSourceType
    enabled: bool = True
    privacy_level: PrivacyLevel
    sync_frequency_hours: int = Field(
        ..., ge=1, le=168, description="Sync frequency (1-168 hours)"
    )
    data_retention_days: int = Field(
        ..., ge=30, le=1095, description="Data retention (30-1095 days)"
    )
    requires_consent: bool = False
    api_credentials: Optional[Dict[str, str]] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)

    @validator("sync_frequency_hours")
    def validate_sync_frequency(cls, v, values):
        """Ensure sensitive data has appropriate sync frequency"""
        if "privacy_level" in values and values["privacy_level"] == PrivacyLevel.FULL:
            if v < 24:
                raise ValueError(
                    "Full privacy data requires sync frequency >= 24 hours"
                )
        return v


class IntegrationStatus(BaseModel):
    """Status of an integration"""

    source_type: DataSourceType
    status: SyncStatus
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    records_processed: int = 0
    error_message: Optional[str] = None
    health_score: float = Field(ge=0, le=1, description="Integration health (0-1)")


class IntegrationResponse(BaseModel):
    """Response model for integration details"""

    config: IntegrationConfig
    status: IntegrationStatus
    behavioral_signals: List[str] = Field(
        description="Available signals from this source"
    )
    data_points_count: int = Field(description="Total data points collected")


class CreateIntegrationRequest(BaseModel):
    """Request to create a new integration"""

    source_type: DataSourceType
    privacy_level: PrivacyLevel
    sync_frequency_hours: int = Field(24, ge=1, le=168)
    data_retention_days: int = Field(90, ge=30, le=1095)
    api_credentials: Optional[Dict[str, str]] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class UpdateIntegrationRequest(BaseModel):
    """Request to update an existing integration"""

    enabled: Optional[bool] = None
    privacy_level: Optional[PrivacyLevel] = None
    sync_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    data_retention_days: Optional[int] = Field(None, ge=30, le=1095)
    api_credentials: Optional[Dict[str, str]] = None
    custom_settings: Optional[Dict[str, Any]] = None


class SyncIntegrationRequest(BaseModel):
    """Request to manually trigger sync"""

    force_full_sync: bool = False
    date_range: Optional[Dict[str, datetime]] = Field(
        None, description="Optional date range: {'start': datetime, 'end': datetime}"
    )


class BehavioralAnalysisRequest(BaseModel):
    """Request to analyze behavioral data"""

    source_types: List[DataSourceType] = Field(
        description="Which data sources to analyze"
    )
    date_range: Dict[str, datetime] = Field(
        ..., description="Date range: {'start': datetime, 'end': datetime}"
    )
    employee_ids: Optional[List[int]] = Field(
        None, description="Specific employees to analyze (null = all)"
    )
    analysis_type: str = Field(
        "comprehensive",
        description="Type: 'toxicity', 'burnout', 'team_health', 'comprehensive'",
    )


class BehavioralInsight(BaseModel):
    """A behavioral insight derived from data"""

    category: str = Field(
        ..., description="Category: 'burnout', 'toxicity', 'engagement', etc."
    )
    severity: str = Field(
        ..., description="Severity: 'low', 'medium', 'high', 'critical'"
    )
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    affected_employees: List[int] = Field(description="Employee IDs affected")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    recommendations: List[str] = Field(description="Actionable recommendations")
    data_sources: List[DataSourceType] = Field(
        description="Sources contributing to insight"
    )
    detected_at: datetime = Field(..., description="When insight was generated")


class OrganizationIntegrations(BaseModel):
    """All integrations for an organization"""

    organization_id: int
    integrations: List[IntegrationResponse]
    summary: Dict[str, Any] = Field(description="Summary statistics")
    recommendations: List[str] = Field(description="Setup recommendations")


class DataIngestionRecord(BaseModel):
    """Record of data ingestion"""

    id: int
    source_type: DataSourceType
    employee_id: Optional[int]
    raw_data: Dict[str, Any]
    processed_signals: List[BehavioralSignal]
    ingested_at: datetime
    processed_at: Optional[datetime]


class IntegrationHealthMetrics(BaseModel):
    """Health metrics for integrations"""

    total_integrations: int
    active_integrations: int
    error_integrations: int
    total_data_points: int
    last_24h_ingestion_count: int
    avg_sync_latency_minutes: float
    data_quality_score: float = Field(ge=0, le=1)


class ConsentRecord(BaseModel):
    """Employee consent for data collection"""

    employee_id: int
    source_types: List[DataSourceType]
    granted: bool
    granted_at: datetime
    revoked_at: Optional[datetime]
    consent_version: str = Field(description="Version of consent form")


class BulkIntegrationRequest(BaseModel):
    """Request to set up multiple integrations at once"""

    organization_size: int = Field(..., description="Number of employees")
    privacy_preference: str = Field(
        "balanced", description="Privacy level: 'minimal', 'balanced', 'comprehensive'"
    )
    auto_enable_recommended: bool = Field(
        True, description="Automatically enable recommended integrations"
    )


class IntegrationInsightsReport(BaseModel):
    """Comprehensive insights report from integrations"""

    report_id: str
    generated_at: datetime
    date_range: Dict[str, datetime]
    organization_id: int
    insights: List[BehavioralInsight]
    health_metrics: IntegrationHealthMetrics
    summary: Dict[str, Any]
    recommendations: List[str]
