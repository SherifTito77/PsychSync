"""
Employee Safety API Endpoints
REST API for safety incident reporting, wellness monitoring, and safety management
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Use async session for compatibility with modern codebase
from app.api.v1.deps import get_current_active_user, get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.employee_safety import (
    IncidentSeverity,
    IncidentStatus,
    SafetyIncidentType,
)
from app.db.models.user import User
from app.services.employee_safety_service import (
    EmployeeSafetyService,
    IncidentReportData,
    WellnessAssessmentData,
)

router = APIRouter(prefix="/safety", tags=["employee-safety"])


# Pydantic Models for API


class IncidentReportRequest(BaseModel):
    """Request model for incident reporting"""

    incident_type: SafetyIncidentType
    severity: IncidentSeverity
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    location: Optional[str] = None
    date_occurred: Optional[datetime] = None
    witnesses: Optional[List[Dict[str, Any]]] = None
    evidence_files: Optional[List[str]] = None
    immediate_actions: Optional[List[str]] = None
    affected_user_id: Optional[uuid.UUID] = None

    @validator("date_occurred")
    def validate_date_occurred(cls, v):
        if v and v > datetime.utcnow():
            raise ValueError("Date occurred cannot be in the future")
        return v


class IncidentUpdateRequest(BaseModel):
    """Request model for incident updates"""

    status: IncidentStatus
    investigation_notes: Optional[str] = None
    root_cause: Optional[str] = None
    prevention_measures: Optional[List[str]] = None
    resolution_details: Optional[str] = None
    lessons_learned: Optional[str] = None


class WellnessAssessmentRequest(BaseModel):
    """Request model for wellness assessment"""

    user_id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
    assessment_type: str = Field(
        default="scheduled", pattern="^(scheduled|incident_triggered|self_reported)$"
    )
    stress_level: Optional[float] = Field(None, ge=1, le=10)
    burnout_risk: Optional[float] = Field(None, ge=0, le=1)
    work_life_balance: Optional[float] = Field(None, ge=1, le=10)
    mental_health_score: Optional[float] = Field(None, ge=1, le=10)
    physical_wellness: Optional[float] = Field(None, ge=1, le=10)
    sleep_quality: Optional[float] = Field(None, ge=1, le=10)
    social_connection: Optional[float] = Field(None, ge=1, le=10)
    job_satisfaction: Optional[float] = Field(None, ge=1, le=10)
    engagement_level: Optional[float] = Field(None, ge=1, le=10)
    work_hours_per_week: Optional[float] = Field(None, ge=0)
    overtime_hours: Optional[float] = Field(None, ge=0)


class SafetyResourceRequest(BaseModel):
    """Request model for safety resources"""

    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    resource_type: str = Field(
        ..., pattern="^(policy|guide|training|contact|emergency)$"
    )
    category: Optional[str] = None
    content: Optional[str] = None
    file_url: Optional[str] = None
    is_public: bool = False
    required_roles: Optional[List[str]] = None
    targeted_teams: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# Incident Reporting Endpoints


@router.post("/incidents", response_model=Dict[str, Any])
async def report_incident(
    incident_data: IncidentReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a new safety incident"""
    try:
        safety_service = EmployeeSafetyService(db)

        incident_report_data = IncidentReportData(
            incident_type=incident_data.incident_type,
            severity=incident_data.severity,
            title=incident_data.title,
            description=incident_data.description,
            location=incident_data.location,
            date_occurred=incident_data.date_occurred,
            witnesses=incident_data.witnesses,
            evidence_files=incident_data.evidence_files,
            immediate_actions=incident_data.immediate_actions,
            affected_user_id=incident_data.affected_user_id,
        )

        # Note: Depending on service implementation, this might need to be await
        result = safety_service.report_incident(
            incident_data=incident_report_data,
            reporter_id=current_user.id,
            organization_id=None,
            team_id=None,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report incident: {str(e)}",
        )


@router.get("/incidents", response_model=Dict[str, Any])
async def get_incidents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get list of safety incidents"""
    try:
        safety_service = EmployeeSafetyService(db)

        # Dashboard data often includes statistics
        dashboard_data = safety_service.get_incidents_dashboard(
            organization_id=None,
            team_id=None,
            date_range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()),
        )

        return {
            "incidents": dashboard_data.get("incidents", []),
            "total_count": len(dashboard_data.get("incidents", [])),
            "statistics": dashboard_data.get("statistics", {}),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incidents: {str(e)}",
        )


@router.get("/incidents/dashboard", response_model=Dict[str, Any])
async def get_incidents_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    team_id: Optional[str] = None,
    days: int = 30,
):
    """Get safety incidents dashboard"""
    try:
        safety_service = EmployeeSafetyService(db)

        # Date range for safety service
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        dashboard_data = safety_service.get_incidents_dashboard(
            organization_id=None,
            team_id=uuid.UUID(team_id) if team_id else None,
            date_range=(start_date, end_date),
        )

        return dashboard_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incidents dashboard: {str(e)}",
        )


@router.get("/wellness/dashboard", response_model=Dict[str, Any])
async def get_wellness_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    team_id: Optional[str] = None,
):
    """Get wellness dashboard"""
    try:
        safety_service = EmployeeSafetyService(db)
        dashboard_data = safety_service.get_wellness_dashboard(
            organization_id=None, team_id=uuid.UUID(team_id) if team_id else None
        )
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wellness dashboard: {str(e)}",
        )
