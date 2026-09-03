# app/schemas/code_quality.py

"""
CODE QUALITY SCHEMAS
Request and response schemas for code quality monitoring

Author: Product Operations Team
Version: 1.0
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CodeQualityIssueBase(BaseModel):
    """Base schema for code quality issues"""

    issue_type: str = Field(
        ..., description="Type of issue: bug, vulnerability, code_smell, duplication"
    )
    severity: str = Field(
        ..., description="Severity level: critical, major, minor, info"
    )
    category: Optional[str] = Field(
        None,
        description="Category: security, performance, maintainability, reliability",
    )
    file_path: str = Field(..., description="File where issue was found")
    line_number: Optional[int] = Field(None, description="Line number")
    function_name: Optional[str] = Field(None, description="Function name")
    title: str = Field(..., description="Issue title")
    description: Optional[str] = Field(None, description="Detailed description")
    rule_id: Optional[str] = Field(None, description="Rule identifier")
    effort: Optional[str] = Field(None, description="Estimated fix time")


class CodeQualityIssueCreate(CodeQualityIssueBase):
    """Schema for creating a code quality issue"""

    metric_id: str = Field(..., description="Parent metric ID")


class CodeQualityIssue(CodeQualityIssueBase):
    """Schema for code quality issue response"""

    id: str
    metric_id: str
    remediation_cost: Optional[float] = None
    status: str = "open"
    false_positive: float = 0.0
    ai_suggestion: Optional[str] = None
    ai_confidence: Optional[float] = None
    auto_fixable: float = 0.0
    first_detected: datetime
    last_detected: datetime
    occurrence_count: int

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class CodeQualityMetricBase(BaseModel):
    """Base schema for code quality metrics"""

    scan_date: datetime
    module_name: Optional[str] = Field(
        None, description="Module name, null for overall codebase"
    )
    cyclomatic_complexity: float = Field(
        ..., ge=0, description="Average cyclomatic complexity"
    )
    cognitive_complexity: float = Field(
        ..., ge=0, description="Average cognitive complexity"
    )
    maintainability_index: float = Field(
        ..., le=100, description="Maintainability index (0-100)"
    )
    duplication_percentage: float = Field(
        ..., ge=0, le=100, description="Code duplication percentage"
    )
    test_coverage_percentage: Optional[float] = Field(None, ge=0, le=100)
    technical_debt_ratio: float = Field(..., ge=0, description="Technical debt ratio")
    file_count: int = Field(..., ge=0)
    code_lines: int = Field(..., ge=0)
    comment_lines: int = Field(..., ge=0)


class CodeQualityMetricCreate(CodeQualityMetricBase):
    """Schema for creating code quality metrics"""

    duplicated_lines: int
    total_lines: int
    test_count: Optional[int] = None
    code_violations_count: int
    security_hotspots_count: int
    bugs_count: int
    estimated_remediation_cost: Optional[float] = None
    blank_lines: int
    language_metrics: Optional[dict[str, int]] = None
    scan_duration_seconds: Optional[float] = None
    scanner_version: Optional[str] = None


class CodeQualityMetric(CodeQualityMetricBase):
    """Schema for code quality metric response"""

    id: str
    duplicated_lines: int
    total_lines: int
    test_count: Optional[int]
    code_violations_count: int
    security_hotspots_count: int
    bugs_count: int
    estimated_remediation_cost: Optional[float]
    blank_lines: int
    language_metrics: Optional[dict[str, int]]
    complexity_trend: Optional[str]
    coverage_trend: Optional[str]
    debt_trend: Optional[str]
    quality_score: float
    quality_grade: str
    scan_duration_seconds: Optional[float]
    scanner_version: Optional[str]
    created_at: datetime

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class CodeQualityMetricWithIssues(CodeQualityMetric):
    """Schema for code quality metric with issues"""

    quality_issues: list[CodeQualityIssue] = []


class PullRequestQualityBase(BaseModel):
    """Base schema for pull request quality"""

    pr_number: int
    pr_title: str
    source_branch: str
    target_branch: str
    author_name: str
    created_at: datetime
    files_changed: int
    lines_added: int
    lines_deleted: int
    commits_count: int


class PullRequestQualityCreate(PullRequestQualityBase):
    """Schema for creating pull request quality record"""

    author_id: Optional[str] = None
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    overall_score: float = Field(..., ge=0, le=100)
    code_quality_score: float = Field(..., ge=0, le=100)
    test_coverage_score: Optional[float] = Field(None, ge=0, le=100)
    documentation_score: float = Field(..., ge=0, le=100)
    risk_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    complexity_increase: Optional[float] = None
    new_debt_added: Optional[float] = None
    duplication_added: Optional[int] = None
    review_count: int = 0
    review_time_hours: Optional[float] = None
    approval_count: int = 0
    request_changes_count: int = 0
    tests_added: int = 0
    coverage_delta: Optional[float] = None
    critical_issues_count: int = 0
    major_issues_count: int = 0
    minor_issues_count: int = 0
    repository: Optional[str] = None
    is_merged: bool = False


class PullRequestQuality(PullRequestQualityBase):
    """Schema for pull request quality response"""

    id: str
    author_id: Optional[str]
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    analyzed_at: datetime
    overall_score: float
    code_quality_score: float
    test_coverage_score: Optional[float]
    documentation_score: float
    risk_level: str
    risk_factors: Optional[list[str]]
    complexity_increase: Optional[float]
    new_debt_added: Optional[float]
    duplication_added: Optional[int]
    review_count: int
    review_time_hours: Optional[float]
    approval_count: int
    request_changes_count: int
    tests_added: int
    coverage_delta: Optional[float]
    critical_issues_count: int
    major_issues_count: int
    minor_issues_count: int
    ai_recommendations: Optional[list[dict[str, Any]]]
    merge_confidence: Optional[float]
    repository: Optional[str]
    is_merged: bool

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class CodeQualityTrend(BaseModel):
    """Schema for code quality trend data"""

    date: datetime
    quality_score: float
    complexity_trend: str
    coverage_trend: Optional[str]
    debt_trend: str
    critical_issues: int
    major_issues: int


class CodeQualitySummary(BaseModel):
    """Schema for code quality summary"""

    current_score: float
    current_grade: str
    trend: str  # "improving", "declining", "stable"
    trend_percentage: float  # percentage change from last period
    total_issues: int
    critical_issues: int
    major_issues: int
    test_coverage: float
    technical_debt_hours: float
    files_scanned: int
    last_scan_date: datetime


class PullRequestQualitySummary(BaseModel):
    """Schema for pull request quality summary"""

    avg_quality_score: float
    avg_review_time_hours: float
    total_prs_analyzed: int
    high_risk_prs: int
    medium_risk_prs: int
    low_risk_prs: int
    avg_files_changed: float
    avg_lines_added: float
    total_tests_added: int
    merge_rate: float
