# app/schemas/build_analysis.py
"""
Pydantic schemas for Build Failure Analysis
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BuildFailureBase(BaseModel):
    """Base schema for build failure"""
    build_id: str = Field(..., description="Build identifier")
    project_name: str = Field(..., description="Project/repository name")
    branch_name: str = Field(..., description="Git branch")
    commit_hash: str = Field(..., description="Git commit SHA")
    failure_type: str = Field(..., description="Type of failure: test_failure, compilation_error, lint_issue, deployment_failure")
    failure_stage: str = Field(..., description="Stage where failure occurred: build, test, deploy, integration")
    error_message: str = Field(..., description="Primary error message")
    stack_trace: Optional[str] = Field(None, description="Full stack trace")
    failed_tests: Optional[list[str]] = Field(None, description="List of failed test names")
    changed_files: Optional[list[str]] = Field(None, description="Files changed in this build")
    developer_name: str = Field(..., description="Developer who triggered build")


class BuildFailureCreate(BuildFailureBase):
    """Schema for creating build failure"""
    root_cause_category: str = Field(..., description="Category: code_bug, dependency_issue, environment_problem, test_flake, infrastructure_issue")
    suspected_culprit_file: Optional[str] = Field(None, description="File likely causing the failure")
    ai_suggested_fix: Optional[str] = Field(None, description="AI-generated fix suggestion")
    priority: str = Field(default="medium", description="Priority: critical, high, medium, low")


class BuildFailureUpdate(BaseModel):
    """Schema for updating build failure"""
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None
    actual_root_cause: Optional[str] = None
    fix_commit_hash: Optional[str] = None
    resolution_time_minutes: Optional[int] = None


class BuildFailure(BuildFailureBase):
    """Schema for build failure response"""
    id: UUID
    root_cause_category: str
    suspected_culprit_file: Optional[str]
    ai_suggested_fix: Optional[str]
    priority: str
    is_resolved: bool
    resolution_notes: Optional[str]
    actual_root_cause: Optional[str]
    fix_commit_hash: Optional[str]
    resolution_time_minutes: Optional[int]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class RootCauseAnalysisBase(BaseModel):
    """Base schema for root cause analysis"""
    failure_id: UUID = Field(..., description="Link to build failure")
    analysis_depth: str = Field(..., description="Depth: shallow, medium, deep")


class RootCauseAnalysisCreate(RootCauseAnalysisBase):
    """Schema for creating root cause analysis"""
    contributing_factors: list[str] = Field(..., description="List of contributing factors")
    affected_components: list[str] = Field(default_factory=list, description="Components affected")
    similar_failures: list[UUID] = Field(default_factory=list, description="Links to similar past failures")


class RootCauseAnalysis(RootCauseAnalysisBase):
    """Schema for root cause analysis response"""
    id: UUID
    contributing_factors: list[str]
    affected_components: list[str]
    similar_failures: list[UUID]
    confidence_score: float
    analysis_result: str
    created_at: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class BuildPatternBase(BaseModel):
    """Base schema for build patterns"""
    pattern_type: str = Field(..., description="Pattern type: flaky_test, slow_build, frequent_failure, dependency_conflict")
    pattern_name: str = Field(..., description="Human-readable pattern name")


class BuildPatternCreate(BuildPatternBase):
    """Schema for creating build pattern"""
    occurrence_count: int = Field(..., description="Number of times this pattern occurred")
    affected_branches: list[str] = Field(..., description="Branches where pattern appears")
    affected_developers: list[str] = Field(default_factory=list, description="Developers typically affected")
    remediation_priority: str = Field(default="medium", description="Priority for addressing pattern")
    ai_remediation_suggestion: Optional[str] = Field(None, description="AI-suggested fix")


class BuildPattern(BuildPatternBase):
    """Schema for build pattern response"""
    id: UUID
    occurrence_count: int
    affected_branches: list[str]
    affected_developers: list[str]
    remediation_priority: str
    ai_remediation_suggestion: Optional[str]
    last_seen: datetime
    is_resolved: bool

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class BuildAnalysisReportBase(BaseModel):
    """Base schema for build analysis report"""
    report_date: datetime = Field(..., description="When report was generated")
    period_start: datetime = Field(..., description="Start of analysis period")
    period_end: datetime = Field(..., description="End of analysis period")


class BuildAnalysisReportCreate(BuildAnalysisReportBase):
    """Schema for creating build analysis report"""
    total_builds: int
    successful_builds: int
    failed_builds: int
    flaky_builds: int
    average_build_time_minutes: float
    average_recovery_time_minutes: float
    top_failure_types: dict[str, int]
    top_failing_branches: dict[str, int]
    top_failing_developers: dict[str, int]
    ai_summary: str
    ai_insights: dict[str, Any]
    recommendations: list[str]


class BuildAnalysisReport(BuildAnalysisReportBase):
    """Schema for build analysis report response"""
    id: UUID
    total_builds: int
    successful_builds: int
    failed_builds: int
    flaky_builds: int
    average_build_time_minutes: float
    average_recovery_time_minutes: float
    success_rate: float
    top_failure_types: dict[str, int]
    top_failing_branches: dict[str, int]
    top_failing_developers: dict[str, int]
    ai_summary: str
    ai_insights: dict[str, Any]
    recommendations: list[str]

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class BuildFailureSummary(BaseModel):
    """Summary of build failures"""
    total_failures: int
    unresolved_failures: int
    critical_failures: int
    high_priority_failures: int
    overall_health_grade: str
    average_resolution_time_minutes: float
    most_common_failure_type: str
    flaky_test_count: int
    top_contributing_factor: str
