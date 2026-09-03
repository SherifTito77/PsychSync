"""
Email Connector Schemas
Request and response schemas for email integration and analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

# ============================================================================
# Email Connection Schemas
# ============================================================================


class EmailConnectionRequest(BaseModel):
    """Request schema for setting up email connection"""

    provider: str = Field(
        ..., description="Email provider (gmail, outlook, exchange, imap)"
    )
    email_address: EmailStr = Field(..., description="Email address to connect")
    connection_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific connection parameters (OAuth tokens, IMAP credentials, etc.)",
    )
    permissions: List[str] = Field(
        default=["read"], description="Granted permissions (read, send, delete, etc.)"
    )
    sync_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Email synchronization settings (frequency, filters, etc.)",
    )
    auto_sync_enabled: bool = Field(
        default=False, description="Enable automatic email sync"
    )


class EmailConnectionResponse(BaseModel):
    """Response schema for email connection setup"""

    success: bool
    provider: str
    email_address: EmailStr
    connection_id: Optional[str] = None
    connection_status: str = Field(..., description="connected, failed, pending")
    error_message: Optional[str] = None
    sync_enabled: bool = False
    permissions_granted: List[str] = Field(default_factory=list)
    setup_completed: bool = False
    setup_completed_at: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    capabilities: Optional[Dict[str, Any]] = None


# ============================================================================
# Email Analytics Schemas
# ============================================================================


class EmailAnalyticsRequest(BaseModel):
    """Request schema for email communication analytics"""

    date_range: Dict[str, str] = Field(
        ...,
        description="Date range for analysis (start_date, end_date)",
    )
    email_filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Filters for email selection (folders, senders, subjects, etc.)",
    )
    analysis_categories: List[str] = Field(
        ...,
        description="Analysis categories to perform (communication_style, responsiveness, engagement, etc.)",
    )


class EmailAnalyticsResponse(BaseModel):
    """Response schema for email analytics"""

    success: bool
    user_id: str
    analysis_period: Dict[str, str]
    analysis_categories: List[str]
    total_emails_analyzed: int
    communication_analysis: Dict[str, Any] = Field(default_factory=dict)
    communication_insights: List[str] = Field(default_factory=list)
    communication_metrics: Dict[str, Any] = Field(default_factory=dict)
    communication_style_profile: Optional[Dict[str, Any]] = None
    behavioral_indicators: List[Dict[str, Any]] = Field(default_factory=list)
    collaboration_patterns: Dict[str, Any] = Field(default_factory=dict)
    network_insights: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime


# ============================================================================
# Email Assessment Schemas
# ============================================================================


class EmailAssessmentRequest(BaseModel):
    """Request schema for email-based behavioral assessment"""

    assessment_type: str = Field(
        ...,
        description="Type of assessment (communication_effectiveness, leadership_communication, etc.)",
    )
    time_period: Dict[str, str] = Field(
        ..., description="Time period for assessment data"
    )
    data_scope: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scope of data to include (folders, contacts, etc.)",
    )


class EmailAssessmentResponse(BaseModel):
    """Response schema for email behavioral assessment"""

    success: bool
    user_id: str
    assessment_type: str
    time_period: Dict[str, str]
    data_scope: Dict[str, Any]
    emails_analyzed: int
    assessment_results: Dict[str, Any] = Field(default_factory=dict)
    behavioral_integration: Dict[str, Any] = Field(default_factory=dict)
    assessment_scores: Dict[str, float] = Field(default_factory=dict)
    assessment_recommendations: List[str] = Field(default_factory=list)
    development_areas: List[str] = Field(default_factory=list)
    strengths_identified: List[str] = Field(default_factory=list)
    behavioral_correlations: Dict[str, Any] = Field(default_factory=dict)
    assessed_at: datetime


# ============================================================================
# Email Sync Schemas
# ============================================================================


class EmailSyncRequest(BaseModel):
    """Request schema for manual email sync"""

    connection_id: str = Field(..., description="Email connection ID to sync")
    sync_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sync options (date_range, folders, batch_size, etc.)",
    )


class EmailSyncResponse(BaseModel):
    """Response schema for email sync"""

    success: bool
    user_id: str
    connection_id: str
    sync_task_id: str
    sync_status: str = Field(..., description="started, in_progress, completed, failed")
    sync_options: Dict[str, Any] = Field(default_factory=dict)
    estimated_duration: Optional[int] = None
    sync_started_at: datetime
    last_sync: Optional[datetime] = None
    emails_to_sync: int = 0


# ============================================================================
# Email Configuration Schemas
# ============================================================================


class EmailConfigurationRequest(BaseModel):
    """Request schema for updating email configuration"""

    connection_id: str = Field(..., description="Email connection ID")
    configuration_updates: Dict[str, Any] = Field(
        ...,
        description="Configuration updates to apply (sync_settings, permissions, etc.)",
    )


class EmailConfigurationResponse(BaseModel):
    """Response schema for email configuration update"""

    success: bool
    connection_id: str
    configuration_updates_applied: Dict[str, Any]
    updated_configuration: Dict[str, Any]
    configuration_updated_at: datetime
    next_effective_date: Optional[datetime] = None
    requires_reauth: bool = False


# ============================================================================
# OAuth Flow Schemas
# ============================================================================


class OAuthUrlRequest(BaseModel):
    """Request schema for OAuth URL generation"""

    provider: str = Field(..., description="Email provider (gmail, outlook)")
    redirect_uri: Optional[str] = Field(
        None, description="Override default redirect URI"
    )
    state: Optional[str] = Field(None, description="OAuth state parameter for security")


class OAuthUrlResponse(BaseModel):
    """Response schema for OAuth URL generation"""

    success: bool
    provider: str
    auth_url: str
    state: str
    expires_at: Optional[datetime] = None


class OAuthCallbackRequest(BaseModel):
    """Request schema for OAuth callback handling"""

    provider: str = Field(..., description="Email provider")
    code: str = Field(..., description="OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter")
    redirect_uri: Optional[str] = Field(
        None, description="Redirect URI used in auth flow"
    )


class OAuthCallbackResponse(BaseModel):
    """Response schema for OAuth callback"""

    success: bool
    provider: str
    email_address: Optional[EmailStr] = None
    connection_id: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# IMAP Connection Schemas
# ============================================================================


class IMAPConnectionRequest(BaseModel):
    """Request schema for IMAP/POP3 connection"""

    email_address: EmailStr = Field(..., description="Email address")
    provider: str = Field(default="imap", description="Provider type (imap, pop3)")
    server: str = Field(..., description="IMAP/POP3 server address")
    port: int = Field(
        default=993, description="Server port (993 for IMAPS, 995 for POP3S)"
    )
    use_ssl: bool = Field(default=True, description="Use SSL/TLS connection")
    username: Optional[str] = Field(
        None, description="Username (if different from email)"
    )
    password: str = Field(..., description="Email password or app-specific password")
    sync_folder: str = Field(default="INBOX", description="Folder to sync")


class IMAPConnectionResponse(BaseModel):
    """Response schema for IMAP connection"""

    success: bool
    provider: str
    email_address: EmailStr
    connection_id: Optional[str] = None
    connection_status: str
    test_results: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
