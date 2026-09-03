# app/schemas/breaking_changes.py
"""
Pydantic schemas for Breaking Changes Detection
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BreakingChangeBase(BaseModel):
    """Base schema for breaking change"""

    change_type: str = Field(
        ...,
        description="Type: api_breaking, schema_change, contract_change, dependency_break",
    )
    affected_component: str = Field(
        ..., description="API endpoint, database table, or service name"
    )
    description: str = Field(..., description="Description of the breaking change")
    severity: str = Field(..., description="Severity: critical, high, medium, low")


class BreakingChangeCreate(BreakingChangeBase):
    """Schema for creating breaking change"""

    source_branch: str = Field(..., description="Git branch introducing the change")
    commit_hash: str = Field(..., description="Git commit SHA")
    file_path: str = Field(..., description="File where change was detected")
    line_number: int = Field(..., description="Line number of change")
    backwards_compatible: bool = Field(
        default=False, description="Whether change is backwards compatible"
    )
    migration_required: bool = Field(
        default=False, description="Whether data migration is required"
    )
    affected_endpoints: Optional[list[str]] = Field(
        None, description="Affected API endpoints"
    )
    affected_models: Optional[list[str]] = Field(
        None, description="Affected database models"
    )


class BreakingChangeUpdate(BaseModel):
    """Schema for updating breaking change"""

    description: Optional[str] = Field(
        None, description="Description of the breaking change"
    )
    severity: Optional[str] = Field(
        None, description="Severity: critical, high, medium, low"
    )
    ai_risk_assessment: Optional[str] = Field(
        None, description="AI-generated risk assessment"
    )
    ai_mitigation_suggestion: Optional[str] = Field(
        None, description="AI mitigation suggestion"
    )
    is_approved: Optional[bool] = Field(None, description="Whether change is approved")
    approved_by: Optional[str] = Field(None, description="Who approved the change")


class BreakingChange(BreakingChangeBase):
    """Schema for breaking change response"""

    id: UUID
    source_branch: str
    commit_hash: str
    file_path: str
    line_number: int
    backwards_compatible: bool
    migration_required: bool
    affected_endpoints: Optional[list[str]]
    affected_models: Optional[list[str]]
    ai_risk_assessment: Optional[str]
    ai_mitigation_suggestion: Optional[str]
    is_approved: bool
    approved_by: Optional[str]
    created_at: datetime

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class MigrationGuideBase(BaseModel):
    """Base schema for migration guide"""

    breaking_change_id: UUID = Field(..., description="Link to breaking change")
    guide_type: str = Field(
        ..., description="Type: code_update, data_migration, config_change"
    )


class MigrationGuideCreate(MigrationGuideBase):
    """Schema for creating migration guide"""

    steps: list[str] = Field(..., description="Step-by-step migration instructions")
    estimated_effort_hours: float
    required_downtime_minutes: int = Field(
        default=0, description="Required downtime for migration"
    )


class MigrationGuide(MigrationGuideBase):
    """Schema for migration guide response"""

    id: UUID
    steps: list[str]
    estimated_effort_hours: float
    required_downtime_minutes: int
    is_automated: bool
    created_at: datetime

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class BreakingChangeReportBase(BaseModel):
    """Base schema for breaking change report"""

    report_date: datetime = Field(..., description="When report was generated")
    period_start: datetime = Field(..., description="Start of analysis period")
    period_end: datetime = Field(..., description="End of analysis period")


class BreakingChangeReportCreate(BreakingChangeReportBase):
    """Schema for creating breaking change report"""

    total_changes_detected: int
    critical_changes: int
    high_priority_changes: int
    medium_priority_changes: int
    low_priority_changes: int
    backwards_compatible_changes: int
    breaking_changes: int
    changes_by_type: dict[str, int]
    most_affected_components: dict[str, int]
    ai_summary: str
    ai_insights: dict[str, Any]
    recommendations: list[str]


class BreakingChangeReport(BreakingChangeReportBase):
    """Schema for breaking change report response"""

    id: UUID
    total_changes_detected: int
    critical_changes: int
    high_priority_changes: int
    medium_priority_changes: int
    low_priority_changes: int
    backwards_compatible_changes: int
    breaking_changes: int
    changes_by_type: dict[str, int]
    most_affected_components: dict[str, int]
    risk_score: float
    ai_summary: str
    ai_insights: dict[str, Any]
    recommendations: list[str]

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class BreakingChangesSummary(BaseModel):
    """Summary of breaking changes"""

    total_changes: int
    unresolved_changes: int
    critical_changes: int
    high_priority_changes: int
    overall_risk_score: float
    risk_grade: str
    backwards_compatible_count: int
    breaking_changes_count: int
    most_common_change_type: str
    most_affected_component: str
