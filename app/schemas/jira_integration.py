# app/schemas/jira_integration.py

"""
JIRA INTEGRATION SCHEMAS
Request and response schemas for Jira integration

Author: Product Operations Team
Version: 1.0
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JiraIssueBase(BaseModel):
    """Base schema for Jira issues"""
    issue_key: str = Field(..., description="Jira issue key (e.g., PROJ-123)")
    issue_type: str = Field(..., description="Issue type: Bug, Story, Task, Epic")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(None, description="Issue description")
    status: str = Field(..., description="Issue status")
    priority: str = Field(..., description="Issue priority")
    is_bug: bool = Field(default=False)
    severity: Optional[str] = Field(None, description="Bug severity: critical, major, minor")
    category: Optional[str] = Field(None, description="Bug category")
    reporter_id: Optional[str] = None
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    time_estimate: Optional[int] = None
    time_spent: Optional[int] = None
    time_remaining: Optional[int] = None
    sprint_id: Optional[str] = None
    sprint_name: Optional[str] = None
    project_key: str
    project_name: str
    labels: Optional[list[str]] = None
    components: Optional[list[str]] = None
    attachment_count: int = 0
    comment_count: int = 0


class JiraIssueCreate(JiraIssueBase):
    """Schema for creating a Jira issue"""
    pass


class JiraIssue(JiraIssueBase):
    """Schema for Jira issue response"""
    id: str
    last_synced_at: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class JiraBugSummaryBase(BaseModel):
    """Base schema for bug summaries"""
    summary_date: datetime
    project_key: str
    sprint_id: Optional[str] = None
    total_bugs: int
    new_bugs: int
    resolved_bugs: int
    reopened_bugs: int
    critical_bugs: int
    major_bugs: int
    minor_bugs: int


class JiraBugSummaryCreate(JiraBugSummaryBase):
    """Schema for creating bug summary"""
    avg_bug_age_hours: Optional[float] = None
    oldest_bug_age_hours: Optional[float] = None
    bugs_over_sla: int = 0
    bugs_by_category: Optional[dict[str, int]] = None
    top_bugs: Optional[list[dict[str, Any]]] = None
    ai_summary: Optional[str] = None
    ai_insights: Optional[list[str]] = None
    ai_recommendations: Optional[list[str]] = None
    trend_new_bugs: Optional[str] = None
    trend_resolution_rate: Optional[str] = None
    assignee_workload: Optional[dict[str, int]] = None
    resolution_time_avg_hours: Optional[float] = None
    generated_by: str = "ai_agent"
    issue_ids: Optional[list[str]] = None


class JiraBugSummary(JiraBugSummaryBase):
    """Schema for bug summary response"""
    id: str
    avg_bug_age_hours: Optional[float]
    oldest_bug_age_hours: Optional[float]
    bugs_over_sla: int
    bugs_by_category: Optional[dict[str, int]]
    top_bugs: Optional[list[dict[str, Any]]]
    ai_summary: Optional[str]
    ai_insights: Optional[list[str]]
    ai_recommendations: Optional[list[str]]
    trend_new_bugs: Optional[str]
    trend_resolution_rate: Optional[str]
    assignee_workload: Optional[dict[str, int]]
    resolution_time_avg_hours: Optional[float]
    created_at: datetime
    generated_by: str
    issue_ids: Optional[list[str]]

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class JiraSprintMetricsBase(BaseModel):
    """Base schema for sprint metrics"""
    sprint_id: str
    sprint_name: str
    project_key: str
    start_date: datetime
    end_date: datetime
    completed_at: Optional[datetime] = None
    state: str
    committed_points: Optional[int] = None
    completed_points: Optional[int] = None
    total_issues: int
    completed_issues: int
    in_progress_issues: int
    todo_issues: int
    bugs_found: int
    bugs_fixed: int
    bugs_carried_over: int
    sprint_goal: Optional[str] = None


class JiraSprintMetricsCreate(JiraSprintMetricsBase):
    """Schema for creating sprint metrics"""
    completion_rate: Optional[float] = None
    team_velocity: Optional[int] = None
    velocity_change: Optional[float] = None
    ai_retrospective: Optional[str] = None
    ai_improvements: Optional[list[str]] = None
    goal_achieved: Optional[float] = None


class JiraSprintMetrics(JiraSprintMetricsBase):
    """Schema for sprint metrics response"""
    id: str
    completion_rate: Optional[float]
    team_velocity: Optional[int]
    velocity_change: Optional[float]
    ai_retrospective: Optional[str]
    ai_improvements: Optional[list[str]]
    goal_achieved: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class BugTrendData(BaseModel):
    """Schema for bug trend data"""
    date: datetime
    new_bugs: int
    resolved_bugs: int
    total_bugs: int
    critical_bugs: int
    resolution_rate: float


class EngineeringPerformanceReport(BaseModel):
    """Schema for engineering performance report"""
    period_start: datetime
    period_end: datetime
    project_key: str

    # Bug metrics
    total_bugs_created: int
    total_bugs_resolved: int
    bugs_by_severity: dict[str, int]
    avg_resolution_time_hours: float

    # Sprint metrics
    sprints_completed: int
    avg_velocity: int
    completion_rate: float

    # PR metrics (if integrated)
    pull_requests_merged: Optional[int] = None
    avg_review_time_hours: Optional[float] = None

    # Quality metrics
    code_quality_score: Optional[float] = None

    # Team performance
    top_contributors: list[dict[str, Any]]
    team_workload: dict[str, int]

    # AI insights
    ai_summary: str
    ai_highlights: list[str]
    ai_concerns: list[str]
    ai_recommendations: list[str]
