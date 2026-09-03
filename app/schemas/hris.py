"""
HRIS Connector Schemas
Request and response models for HRIS integration endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== Base Schemas ====================


class HRISProviderConfig(BaseModel):
    """Base configuration for any HRIS provider"""

    provider_type: str = Field(..., description="Type of HRIS provider")
    connection_params: Dict[str, Any] = Field(
        ..., description="Provider-specific connection parameters"
    )


# ==================== Connection Management ====================


class HRISConnectionRequest(BaseModel):
    """Request to setup HRIS connection"""

    provider: str = Field(
        ..., description="HRIS provider name (workday, bamboohr, etc.)"
    )
    organization_id: int = Field(..., description="Organization ID")
    connection_parameters: Dict[str, Any] = Field(
        ..., description="Connection parameters (API keys, URLs, credentials)"
    )
    data_permissions: List[str] = Field(
        default=["basic"], description="Data access permissions levels"
    )
    sync_settings: Dict[str, Any] = Field(
        default={}, description="Synchronization settings"
    )
    auto_sync_enabled: bool = Field(
        default=False, description="Enable automatic synchronization"
    )


class HRISConnectionResponse(BaseModel):
    """Response for HRIS connection setup"""

    success: bool
    provider: str
    organization_id: int
    connection_id: Optional[str] = None
    connection_status: str
    sync_enabled: Optional[bool] = None
    data_permissions: Optional[List[str]] = None
    setup_completed: bool
    setup_completed_at: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    available_endpoints: Optional[List[str]] = None
    data_schema: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# ==================== Analytics ====================


class HRISAnalyticsRequest(BaseModel):
    """Request for HRIS workforce analytics"""

    organization_id: int = Field(..., description="Organization ID")
    analytics_type: str = Field(
        ...,
        description="Type of analytics: demographics, performance, turnover, engagement, compensation, learning_development, succession_planning",
    )
    data_types: List[str] = Field(
        default=["employees"], description="Data types to analyze"
    )
    date_range: Dict[str, str] = Field(
        default={"start": "2024-01-01", "end": "2024-12-31"},
        description="Date range for analysis",
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional filters for analysis"
    )


class HRISAnalyticsResponse(BaseModel):
    """Response for HRIS analytics"""

    success: bool
    organization_id: int
    analytics_type: str
    analysis_period: Dict[str, str]
    data_types: List[str]
    total_records_analyzed: int
    analytics_results: Dict[str, Any] = Field(default={})
    workforce_insights: List[str] = Field(default=[])
    workforce_metrics: Dict[str, Any] = Field(default={})
    benchmark_comparison: Optional[Dict[str, Any]] = None
    recommendations: List[str] = Field(default=[])
    compliance_alerts: List[Dict[str, Any]] = Field(default=[])
    analyzed_at: datetime


# ==================== Employee Data ====================


class EmployeeDataRequest(BaseModel):
    """Request for employee data from HRIS"""

    organization_id: int = Field(..., description="Organization ID")
    employee_ids: Optional[List[str]] = Field(
        default=None, description="Specific employee IDs (null for all)"
    )
    data_scope: str = Field(
        default="basic", description="Data scope: basic, standard, advanced, custom"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Filters for employee data"
    )
    include_sensitive: bool = Field(
        default=False, description="Include sensitive employee data"
    )
    include_pii: bool = Field(
        default=True, description="Include personally identifiable information"
    )
    include_psychometric_data: bool = Field(
        default=False, description="Include psychometric assessment data"
    )


class EmployeeDataResponse(BaseModel):
    """Response with employee data"""

    success: bool
    organization_id: int
    data_scope: str
    total_employees: int
    employee_data: Dict[str, Any] = Field(default={})
    data_fields_included: List[str] = Field(default=[])
    privacy_level: str
    data_freshness: Optional[str] = None
    retrieved_at: datetime


# ==================== Synchronization ====================


class HRISSyncRequest(BaseModel):
    """Request to trigger manual HRIS sync"""

    organization_id: int = Field(..., description="Organization ID")
    connection_id: str = Field(..., description="HRIS connection ID")
    sync_options: Dict[str, Any] = Field(
        default={}, description="Sync options (data types, incremental, etc.)"
    )


class HRISSyncResponse(BaseModel):
    """Response for HRIS sync operation"""

    success: bool
    organization_id: int
    connection_id: str
    sync_task_id: Optional[str] = None
    sync_status: str
    sync_options: Dict[str, Any] = Field(default={})
    estimated_duration: Optional[str] = None
    sync_started_at: datetime
    last_sync: Optional[datetime] = None
    records_to_sync: int = Field(default=0)
    data_types_syncing: List[str] = Field(default=[])


# ==================== Configuration ====================


class HRISConfigurationRequest(BaseModel):
    """Request to update HRIS configuration"""

    organization_id: int = Field(..., description="Organization ID")
    connection_id: str = Field(..., description="HRIS connection ID")
    configuration_updates: Dict[str, Any] = Field(
        ..., description="Configuration parameters to update"
    )


class HRISConfigurationResponse(BaseModel):
    """Response for HRIS configuration update"""

    success: bool
    organization_id: int
    connection_id: str
    configuration_updates_applied: Dict[str, Any]
    updated_configuration: Dict[str, Any]
    configuration_updated_at: datetime
    next_effective_date: Optional[datetime] = None
    requires_reauth: bool = Field(default=False)
    impact_assessment: Optional[Dict[str, Any]] = None
