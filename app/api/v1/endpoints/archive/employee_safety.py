"""
Employee Safety API Endpoints
REST API for safety incident reporting, wellness monitoring, and safety management
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.api.v1.endpoints.health_monitoring_ws import manager as ws_manager
from app.core.database import get_sync_db
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

router = APIRouter()


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


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/incidents", response_model=Dict[str, Any])
def report_incident(
    incident_data: IncidentReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Report a new safety incident

    - **incident_type**: Type of safety incident
    - **severity**: Severity level (low, medium, high, critical)
    - **title**: Brief description of the incident
    - **description**: Detailed description of what happened
    - **location**: Where the incident occurred
    - **date_occurred**: When the incident happened
    - **witnesses**: List of witness information
    - **evidence_files**: References to evidence files
    - **immediate_actions**: Actions taken immediately after incident
    - **affected_user_id**: User who was affected (if different from reporter)
    """
    try:
        safety_service = EmployeeSafetyService(db)

        # Convert request to dataclass
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

        result = safety_service.report_incident(
            incident_data=incident_report_data,
            reporter_id=current_user.id,
            organization_id=None,  # User model doesn't have organization_id
            team_id=None,  # User model doesn't have team_id
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "incident_id": str(result["incident_id"]),
                "severity": result["severity"],
                "status": result["status"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report incident: {str(e)}",
        ) from e


@router.get("/incidents", response_model=Dict[str, Any])
def get_incidents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
    limit: int = 50,
    offset: int = 0,
    severity: Optional[IncidentSeverity] = None,
    status: Optional[IncidentStatus] = None,
    incident_type: Optional[SafetyIncidentType] = None,
    team_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Get list of safety incidents with filtering options

    - **limit**: Maximum number of incidents to return
    - **offset**: Number of incidents to skip
    - **severity**: Filter by severity level
    - **status**: Filter by incident status
    - **incident_type**: Filter by incident type
    - **team_id**: Filter by team
    - **start_date**: Filter incidents after this date
    - **end_date**: Filter incidents before this date
    """
    try:
        safety_service = EmployeeSafetyService(db)

        # Convert team_id string to uuid.UUID if provided
        team_id_uuid = None
        if team_id:
            try:
                team_id_uuid = uuid.UUID(team_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid team_id format: {team_id}",
                )

        # Get date range
        date_range = None
        if start_date or end_date:
            date_range = (
                start_date or datetime.utcnow() - timedelta(days=30),
                end_date or datetime.utcnow(),
            )

        dashboard_data = safety_service.get_incidents_dashboard(
            organization_id=None,  # User model doesn't have organization_id
            team_id=team_id_uuid,
            date_range=date_range,
        )

        if "error" in dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=dashboard_data["error"]
            )

        incidents = dashboard_data.get("incidents", [])

        # Apply additional filters
        if severity:
            incidents = [inc for inc in incidents if inc["severity"] == severity.value]
        if status:
            incidents = [inc for inc in incidents if inc["status"] == status.value]
        if incident_type:
            incidents = [
                inc for inc in incidents if inc["incident_type"] == incident_type.value
            ]

        # Apply pagination
        total_count = len(incidents)
        paginated_incidents = incidents[offset : offset + limit]

        return {
            "incidents": paginated_incidents,
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "statistics": {
                "total_incidents": dashboard_data.get("total_incidents", 0),
                "recent_incidents": dashboard_data.get("recent_incidents", 0),
                "critical_incidents": dashboard_data.get("critical_incidents", 0),
                "severity_breakdown": dashboard_data.get("severity_breakdown", {}),
                "type_breakdown": dashboard_data.get("type_breakdown", {}),
                "status_breakdown": dashboard_data.get("status_breakdown", {}),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incidents: {str(e)}",
        ) from e


@router.put("/incidents/{incident_id}", response_model=Dict[str, Any])
def update_incident(
    incident_id: uuid.UUID,
    update_data: IncidentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Update incident status and investigation details

    - **incident_id**: uuid.UUID of the incident to update
    - **status**: New incident status
    - **investigation_notes**: Notes from investigation
    - **root_cause**: Identified root cause
    - **prevention_measures**: Measures to prevent recurrence
    - **resolution_details**: Details of resolution
    - **lessons_learned**: Key lessons learned
    """
    try:
        safety_service = EmployeeSafetyService(db)

        result = safety_service.update_incident_status(
            incident_id=incident_id,
            new_status=update_data.status,
            investigator_id=current_user.id,
            notes=update_data.investigation_notes,
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "status": result["status"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident: {str(e)}",
        ) from e


@router.get("/incidents/dashboard", response_model=Dict[str, Any])
def get_incidents_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
    team_id: Optional[str] = None,
    days: int = 30,
):
    """
    Get safety incidents dashboard with statistics and trends

    - **team_id**: Filter by specific team
    - **days**: Number of days to include in analysis
    """
    try:
        safety_service = EmployeeSafetyService(db)

        # Convert team_id string to uuid.UUID if provided
        team_id_uuid = None
        if team_id:
            try:
                team_id_uuid = uuid.UUID(team_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid team_id format: {team_id}",
                )

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        date_range = (start_date, end_date)

        dashboard_data = safety_service.get_incidents_dashboard(
            organization_id=None,  # User model doesn't have organization_id
            team_id=team_id_uuid,
            date_range=date_range,
        )

        if "error" in dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=dashboard_data["error"]
            )

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incidents dashboard: {str(e)}",
        ) from e


@router.get("/incidents/{incident_id}", response_model=Dict[str, Any])
def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Get details of a specific safety incident

    - **incident_id**: uuid.UUID of the incident
    """
    try:
        safety_service = EmployeeSafetyService(db)

        incident = safety_service.get_incident(incident_id, current_user.id)

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found or access denied",
            )

        return incident

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incident: {str(e)}",
        ) from e


@router.post("/wellness/assessments", response_model=Dict[str, Any])
def create_wellness_assessment(
    assessment_data: WellnessAssessmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Create a new wellness assessment

    - **user_id**: User being assessed (must be self or admin)
    - **team_id**: User's team (optional)
    - **assessment_type**: Type of assessment (scheduled, incident_triggered, self_reported)
    - **stress_level**: Current stress level (1-10)
    - **burnout_risk**: Burnout risk probability (0-1)
    - **work_life_balance**: Work-life balance score (1-10)
    - **mental_health_score**: Mental health score (1-10)
    - **physical_wellness**: Physical wellness score (1-10)
    - **sleep_quality**: Sleep quality score (1-10)
    - **social_connection**: Social connection score (1-10)
    - **job_satisfaction**: Job satisfaction score (1-10)
    - **engagement_level**: Engagement level score (1-10)
    - **work_hours_per_week**: Average weekly work hours
    - **overtime_hours**: Average overtime hours per week
    """
    try:
        # Validate permissions - can only assess self or admin can assess others
        if assessment_data.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assess this user",
            )

        safety_service = EmployeeSafetyService(db)

        wellness_data = WellnessAssessmentData(
            user_id=assessment_data.user_id,
            organization_id=None,  # User model doesn't have organization_id
            team_id=assessment_data.team_id,
            assessment_type=assessment_data.assessment_type,
            stress_level=assessment_data.stress_level,
            burnout_risk=assessment_data.burnout_risk,
            work_life_balance=assessment_data.work_life_balance,
            mental_health_score=assessment_data.mental_health_score,
            physical_wellness=assessment_data.physical_wellness,
            sleep_quality=assessment_data.sleep_quality,
            social_connection=assessment_data.social_connection,
            job_satisfaction=assessment_data.job_satisfaction,
            engagement_level=assessment_data.engagement_level,
            work_hours_per_week=assessment_data.work_hours_per_week,
            overtime_hours=assessment_data.overtime_hours,
        )

        result = safety_service.create_wellness_assessment(wellness_data)

        if result["success"]:
            return {
                "success": True,
                "message": "Wellness assessment created successfully",
                "assessment_id": str(result["assessment_id"]),
                "overall_score": result["overall_score"],
                "alert_level": result["alert_level"],
                "risk_factors_count": result["risk_factors_count"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wellness assessment: {str(e)}",
        ) from e


@router.get("/wellness/dashboard", response_model=Dict[str, Any])
def get_wellness_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
    team_id: Optional[str] = None,
    days: int = 30,
):
    """
    Get wellness dashboard with organizational/team metrics

    - **team_id**: Filter by specific team (admin only)
    - **days**: Number of days to include in analysis
    """
    try:
        safety_service = EmployeeSafetyService(db)

        # Convert team_id string to uuid.UUID if provided
        team_id_uuid = None
        if team_id:
            try:
                team_id_uuid = uuid.UUID(team_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid team_id format: {team_id}",
                )

        dashboard_data = safety_service.get_wellness_dashboard(
            organization_id=None,  # User model doesn't have organization_id
            team_id=team_id_uuid,
        )

        if "error" in dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=dashboard_data["error"]
            )

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wellness dashboard: {str(e)}",
        ) from e


@router.get("/wellness/assessments/{user_id}", response_model=List[Dict[str, Any]])
def get_employee_wellness_history(
    user_id: uuid.UUID,
    days: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Get wellness assessment history for a specific employee

    - **user_id**: User ID to get history for
    - **days**: Number of days of history to retrieve
    """
    try:
        # Validate permissions - can only view own history or admin can view others
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's wellness data",
            )

        safety_service = EmployeeSafetyService(db)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        date_range = (start_date, end_date)

        history = safety_service.get_employee_wellness_history(
            user_id=user_id, date_range=date_range
        )

        return history

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wellness history: {str(e)}",
        ) from e


# Safety Resources Endpoints


@router.post("/resources", response_model=Dict[str, Any])
def create_safety_resource(
    resource_data: SafetyResourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Create a new safety resource

    - **title**: Resource title
    - **description**: Resource description
    - **resource_type**: Type of resource (policy, guide, training, contact, emergency)
    - **category**: Resource category
    - **content**: Text content of the resource
    - **file_url**: URL to file resource
    - **is_public**: Whether resource is publicly accessible
    - **required_roles**: Roles that can access this resource
    - **targeted_teams**: Teams this resource targets
    - **tags**: Resource tags for categorization
    """
    try:
        # Only admins can create safety resources
        if not current_user.is_superuser:  # User model doesn't have is_admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create safety resources",
            )

        safety_service = EmployeeSafetyService(db)

        result = safety_service.create_safety_resource(
            organization_id=None,  # User model doesn't have organization_id
            title=resource_data.title,
            description=resource_data.description,
            resource_type=resource_data.resource_type,
            content=resource_data.content,
            file_url=resource_data.file_url,
            category=resource_data.category,
            is_public=resource_data.is_public,
            tags=resource_data.tags,
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "resource_id": str(result["resource_id"]),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create safety resource: {str(e)}",
        ) from e


@router.get("/resources", response_model=List[Dict[str, Any]])
def get_safety_resources(
    resource_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Get safety resources with filtering options

    - **resource_type**: Filter by resource type
    - **category**: Filter by category
    - **search**: Search in title and description
    """
    try:
        safety_service = EmployeeSafetyService(db)

        resources = safety_service.get_safety_resources(
            organization_id=None,  # User model doesn't have organization_id
            resource_type=resource_type,
            category=category,
            user_role=None,  # User model doesn't have role
        )

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            resources = [
                r
                for r in resources
                if search_lower in r["title"].lower()
                or search_lower in r["description"].lower()
            ]

        return resources

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get safety resources: {str(e)}",
        ) from e


# File Upload Endpoint for Evidence


@router.post("/incidents/{incident_id}/evidence")
def upload_evidence(
    incident_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db),
):
    """
    Upload evidence files for a safety incident

    - **incident_id**: uuid.UUID of the incident
    - **files**: List of files to upload as evidence
    """
    try:
        # Validate incident access
        safety_service = EmployeeSafetyService(db)
        incident = safety_service.get_incident(incident_id, current_user.id)

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found or access denied",
            )

        # Implementation would include file upload logic
        # For now, return a placeholder response
        uploaded_files = []
        for file in files:
            # TODO: Implement actual file upload to secure storage
            uploaded_files.append(
                {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": file.size,
                    "url": f"/api/v1/safety/evidence/{incident_id}/{file.filename}",
                }
            )

        return {
            "success": True,
            "message": f"Uploaded {len(uploaded_files)} evidence files",
            "files": uploaded_files,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload evidence: {str(e)}",
        ) from e


# Health Check Endpoint


@router.get("/health")
def health_check():
    """Health check endpoint for safety service"""
    return {
        "status": "healthy",
        "service": "employee_safety",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
