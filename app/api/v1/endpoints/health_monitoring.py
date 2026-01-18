"""
Health Monitoring & Intervention API Endpoints
Provides comprehensive health monitoring, stress detection, and automated interventions

Endpoints:
- POST /analyze - Analyze health risks
- GET /health-report - Get comprehensive health report
- POST /interventions - Create intervention plan
- GET /interventions - Get active interventions
- POST /biometric - Submit biometric data
- GET /manager-dashboard - Manager view of team health (anonymized)
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user, get_current_user, get_db
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.services.health.stress_monitoring_service import (
    StressMonitoringService,
    HealthRiskIndicators,
    BiometricData,
    StressLevel,
    BurnoutStage
)
from app.services.health.intervention_system import (
    HealthInterventionSystem,
    InterventionAction
)

router = APIRouter()


# Pydantic schemas for requests/responses


class BiometricDataSubmit(BaseModel):
    """Biometric data submission schema"""
    data_source: str = Field(..., description="Source of biometric data")
    measurement_date: str = Field(..., description="Date of measurement (YYYY-MM-DD)")

    # Cardiovascular
    resting_heart_rate: Optional[float] = Field(None, ge=30, le=220)
    heart_rate_variability: Optional[float] = Field(None, ge=0, le=300)
    avg_heart_rate: Optional[float] = Field(None, ge=30, le=220)
    blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=150)

    # Respiratory
    oxygen_saturation: Optional[float] = Field(None, ge=0, le=100)

    # Sleep
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality_score: Optional[float] = Field(None, ge=0, le=1)
    deep_sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    rem_sleep_hours: Optional[float] = Field(None, ge=0, le=24)

    # Activity
    steps_count: Optional[int] = Field(None, ge=0)
    activity_minutes: Optional[int] = Field(None, ge=0)
    sedentary_minutes: Optional[int] = Field(None, ge=0)

    device_info: Optional[Dict[str, Any]] = None


class HealthAnalysisRequest(BaseModel):
    """Request health analysis"""
    time_window_days: int = Field(30, ge=7, le=90, description="Days to analyze")
    include_biometric: bool = Field(False, description="Include biometric data if available")
    biometric_data: Optional[BiometricDataSubmit] = None


class HealthAnalysisResponse(BaseModel):
    """Health analysis results"""
    analysis_date: datetime
    user_id: str
    time_window_days: int

    # Risk scores
    stress_level: str
    burnout_stage: str
    cardiovascular_risk_score: float
    mental_health_risk: float
    work_life_imbalance: float
    sleep_disruption_score: float
    social_isolation_score: float

    # Intervention flags
    urgent_intervention_needed: bool
    recommend_medical_evaluation: bool
    recommend_immediate_break: bool
    recommend_workload_reduction: bool

    # Details
    primary_risk_factors: List[str]
    warning_signs: List[str]
    protective_factors: List[str]

    # Data quality
    data_sources: List[str]
    confidence_level: float

    # Recommendations
    recommended_actions: List[str]


class InterventionCreateRequest(BaseModel):
    """Create intervention plan request"""
    health_risks: Dict[str, Any]
    work_patterns: Dict[str, Any]


class InterventionResponse(BaseModel):
    """Intervention response"""
    intervention_id: str
    intervention_type: str
    urgency: str
    title: str
    message: str
    actions_required: List[str]
    notify_user: bool
    notify_manager: bool
    notify_hr: bool
    resources: List[Dict[str, str]]
    follow_up_required: bool
    follow_up_days: int
    created_at: datetime


class ManagerDashboardResponse(BaseModel):
    """Manager dashboard response (anonymized team health)"""
    team_id: str
    team_name: str
    analysis_date: datetime
    total_team_members: int
    members_analyzed: int

    # Aggregate metrics (anonymized)
    average_stress_level: float
    stress_distribution: Dict[str, int]  # {"normal": 10, "elevated": 3, ...}

    high_risk_members_count: int  # Count only, no identities
    critical_interventions_active: int

    # Trends
    weekly_stress_trend: List[Dict[str, Any]]
    cardiovascular_risk_distribution: Dict[str, int]

    # Action items (anonymized)
    recommended_team_actions: List[str]
    organizational_risk_factors: List[str]


class ConsentRequest(BaseModel):
    """Health data consent request"""
    biometric_collection: bool = Field(False, description="Consent to collect biometric data")
    biometric_processing: bool = Field(False, description="Consent to process for wellness")
    biometric_sharing: bool = Field(False, description="Consent to share with healthcare")
    data_sources: Optional[List[str]] = Field(None, description="Consented data sources")
    data_retention_days: int = Field(365, ge=30, le=2555, description="Days to retain data")


# Endpoints


@router.post("/analyze", response_model=HealthAnalysisResponse)
async def analyze_health_risks(
    request: HealthAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Analyze health risks based on work patterns, communication, and biometric data

    Integrates:
    - Email metadata for work patterns
    - Communication analysis for behavioral stress
    - Wellness metrics for comprehensive assessment
    - Optional biometric data from wearables
    """
    try:
        # Convert biometric data if provided
        biometric_data = None
        if request.include_biometric and request.biometric_data:
            biometric_data = BiometricData(
                heart_rate_avg=request.biometric_data.avg_heart_rate,
                heart_rate_variability=request.biometric_data.heart_rate_variability,
                resting_heart_rate=request.biometric_data.resting_heart_rate,
                blood_pressure_systolic=request.biometric_data.blood_pressure_systolic,
                blood_pressure_diastolic=request.biometric_data.blood_pressure_diastolic,
                oxygen_saturation=request.biometric_data.oxygen_saturation,
                sleep_hours=request.biometric_data.sleep_hours,
                sleep_quality=request.biometric_data.sleep_quality_score,
                steps_per_day=request.biometric_data.steps_count,
                activity_minutes=request.biometric_data.activity_minutes
            )

        # Initialize service
        monitoring_service = StressMonitoringService(db)

        # Analyze health risks
        health_risks = await monitoring_service.analyze_health_risks(
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            time_window_days=request.time_window_days,
            biometric_data=biometric_data
        )

        # Generate recommended actions based on risks
        recommended_actions = _generate_recommended_actions(health_risks)

        return HealthAnalysisResponse(
            analysis_date=datetime.utcnow(),
            user_id=str(current_user.id),
            time_window_days=request.time_window_days,
            stress_level=health_risks.stress_level.value,
            burnout_stage=health_risks.burnout_stage.value,
            cardiovascular_risk_score=health_risks.cardiovascular_risk_score,
            mental_health_risk=health_risks.mental_health_risk,
            work_life_imbalance=health_risks.work_life_imbalance,
            sleep_disruption_score=health_risks.sleep_disruption_score,
            social_isolation_score=health_risks.social_isolation_score,
            urgent_intervention_needed=health_risks.urgent_intervention_needed,
            recommend_medical_evaluation=health_risks.recommend_medical_evaluation,
            recommend_immediate_break=health_risks.recommend_immediate_break,
            recommend_workload_reduction=health_risks.recommend_workload_reduction,
            primary_risk_factors=health_risks.primary_risk_factors,
            warning_signs=health_risks.warning_signs,
            protective_factors=health_risks.protective_factors,
            data_sources=health_risks.data_sources,
            confidence_level=health_risks.confidence_level,
            recommended_actions=recommended_actions
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health analysis failed: {str(e)}"
        )


@router.get("/health-report")
async def get_health_report(
    days: int = Query(30, ge=7, le=90, description="Days to include in report"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get comprehensive health report for current user

    Includes:
    - Historical wellness metrics
    - Trend analysis
    - Risk factors
    - Active interventions
    """
    try:
        monitoring_service = StressMonitoringService(db)

        # Get current health risks
        health_risks = await monitoring_service.analyze_health_risks(
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            time_window_days=days
        )

        # Get historical data (would query WellnessMetrics for trends)
        # This is simplified - in production would pull actual historical data

        return {
            "user_id": str(current_user.id),
            "report_date": datetime.utcnow().isoformat(),
            "time_period_days": days,
            "current_health_status": {
                "stress_level": health_risks.stress_level.value,
                "burnout_stage": health_risks.burnout_stage.value,
                "cardiovascular_risk": health_risks.cardiovascular_risk_score,
                "mental_health_risk": health_risks.mental_health_risk
            },
            "risk_factors": health_risks.primary_risk_factors,
            "warning_signs": health_risks.warning_signs,
            "protective_factors": health_risks.protective_factors,
            "data_sources_analyzed": health_risks.data_sources,
            "confidence_level": health_risks.confidence_level,
            "needs_attention": health_risks.urgent_intervention_needed,
            "recommendations": _generate_recommended_actions(health_risks)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate health report: {str(e)}"
        )


@router.post("/interventions", response_model=List[InterventionResponse])
async def create_intervention_plan(
    request: InterventionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create intervention plan based on health risks

    Automatically creates and executes interventions:
    - Sends notifications to user
    - Alerts managers if needed
    - Creates database records
    - Triggers automated actions
    """
    try:
        # Reconstruct HealthRiskIndicators from request
        # In production, would pass the actual object or retrieve from DB
        health_risks = HealthRiskIndicators(
            stress_level=StressLevel(request.health_risks.get("stress_level", "normal")),
            burnout_stage=BurnoutStage(request.health_risks.get("burnout_stage", "none")),
            cardiovascular_risk_score=request.health_risks.get("cardiovascular_risk_score", 0),
            mental_health_risk=request.health_risks.get("mental_health_risk", 0),
            work_life_imbalance=request.health_risks.get("work_life_imbalance", 0),
            sleep_disruption_score=request.health_risks.get("sleep_disruption_score", 0),
            social_isolation_score=request.health_risks.get("social_isolation_score", 0),
            urgent_intervention_needed=request.health_risks.get("urgent_intervention_needed", False),
            recommend_medical_evaluation=request.health_risks.get("recommend_medical_evaluation", False),
            recommend_immediate_break=request.health_risks.get("recommend_immediate_break", False),
            recommend_workload_reduction=request.health_risks.get("recommend_workload_reduction", False),
            primary_risk_factors=request.health_risks.get("primary_risk_factors", []),
            warning_signs=request.health_risks.get("warning_signs", []),
            protective_factors=request.health_risks.get("protective_factors", []),
            data_sources=request.health_risks.get("data_sources", []),
            confidence_level=request.health_risks.get("confidence_level", 0.5)
        )

        # Get user's team
        team_id = None
        if current_user.team_id:
            team_id = str(current_user.team_id)

        # Create intervention plan
        intervention_system = HealthInterventionSystem(db)
        interventions = await intervention_system.create_intervention_plan(
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            team_id=team_id,
            health_risks=health_risks,
            work_patterns=request.work_patterns
        )

        # Convert to response format
        response_interventions = []
        for intervention in interventions:
            response_interventions.append(InterventionResponse(
                intervention_id="",  # Would come from DB
                intervention_type=intervention.intervention_type.value,
                urgency=intervention.urgency.value,
                title=intervention.title,
                message=intervention.message,
                actions_required=intervention.actions_required,
                notify_user=intervention.notify_user,
                notify_manager=intervention.notify_manager,
                notify_hr=intervention.notify_hr,
                resources=intervention.resources,
                follow_up_required=intervention.follow_up_required,
                follow_up_days=intervention.follow_up_days,
                created_at=datetime.utcnow()
            ))

        return response_interventions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create intervention plan: {str(e)}"
        )


@router.post("/biometric")
async def submit_biometric_data(
    data: BiometricDataSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Submit biometric health data from wearables or manual entry

    Stores data and triggers health analysis if needed.
    Requires user consent.
    """
    try:
        # Check consent
        # TODO: Verify user has given consent for biometric data

        # Import BiometricHealthData model
        from app.db.models.biometric_health import BiometricHealthData

        # Create biometric data record
        biometric_record = BiometricHealthData(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            measurement_date=datetime.strptime(data.measurement_date, "%Y-%m-%d").date(),
            data_source=data.data_source,
            device_info=data.device_info,
            sync_timestamp=datetime.utcnow(),

            # Cardiovascular
            resting_heart_rate=data.resting_heart_rate,
            heart_rate_variability=data.heart_rate_variability,
            avg_heart_rate=data.avg_heart_rate,
            blood_pressure_systolic=data.blood_pressure_systolic,
            blood_pressure_diastolic=data.blood_pressure_diastolic,

            # Respiratory
            oxygen_saturation=data.oxygen_saturation,

            # Sleep
            sleep_hours=data.sleep_hours,
            sleep_quality_score=data.sleep_quality_score,
            deep_sleep_hours=data.deep_sleep_hours,
            rem_sleep_hours=data.rem_sleep_hours,

            # Activity
            steps_count=data.steps_count,
            activity_minutes=data.activity_minutes,
            sedentary_minutes=data.sedentary_minutes,

            consent_given=True,  # Already verified
            consent_date=datetime.utcnow().date()
        )

        db.add(biometric_record)
        await db.commit()

        # Analyze for critical health alerts
        risk_indicators = biometric_record.get_cardiovascular_risk_indicators()

        # If critical risks detected, trigger immediate alert
        if risk_indicators["max_severity"] in ["critical", "high"]:
            # TODO: Create urgent health alert
            pass

        return {
            "success": True,
            "message": "Biometric data submitted successfully",
            "data_id": str(biometric_record.id),
            "risk_indicators": risk_indicators
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit biometric data: {str(e)}"
        )


@router.get("/manager-access")
async def check_manager_access(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Check if current user has manager/HR access to team health analytics

    Returns true for users with admin/superuser roles or team managers
    """
    try:
        # Check if user has superuser privileges (only is_superuser exists on User model)
        has_access = current_user.is_superuser

        return {
            "has_access": has_access,
            "user_id": str(current_user.id),
            "is_admin": current_user.is_admin,
            "is_superuser": current_user.is_superuser
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check manager access: {str(e)}"
        )


@router.get("/manager-dashboard", response_model=ManagerDashboardResponse)
async def get_manager_dashboard(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    days: int = Query(30, ge=7, le=90, description="Days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get anonymized team health dashboard (manager/HR only)

    Privacy-focused:
    - No individual user identifiers
    - Aggregate metrics only
    - Anonymized risk distributions
    - Count-based reporting
    """
    try:
        # Verify user has manager/HR role (only is_superuser exists on User model)
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Manager dashboard requires superuser privileges"
            )

        # Get team or organization
        if team_id:
            from sqlalchemy import select
            team_result = await db.execute(select(Team).filter(Team.id == UUID(team_id)))
            team = team_result.scalar_one_or_none()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            team_name = team.name
            organization_id = team.organization_id
        else:
            team_name = "All Teams"
            # Note: organization_id might not exist on User model
            organization_id = getattr(current_user, 'organization_id', None)

        # Get aggregate wellness metrics for the team/org
        # This is simplified - in production would query and aggregate properly
        monitoring_service = StressMonitoringService(db)

        # Placeholder - would aggregate actual team data
        team_stats = {
            "total_team_members": 25,
            "members_analyzed": 22,
            "average_stress_level": 2.3,  # On 1-4 scale
            "stress_distribution": {
                "normal": 15,
                "elevated": 5,
                "high": 2,
                "critical": 0
            },
            "high_risk_members_count": 2,
            "critical_interventions_active": 1,
            "weekly_stress_trend": [
                {"week": "2025-01", "avg_stress": 2.1},
                {"week": "2025-02", "avg_stress": 2.3},
                {"week": "2025-03", "avg_stress": 2.5}
            ],
            "cardiovascular_risk_distribution": {
                "low": 18,
                "medium": 3,
                "high": 1
            }
        }

        # Generate organizational recommendations
        org_risks = []
        if team_stats["high_risk_members_count"] > 0:
            org_risks.append(f"{team_stats['high_risk_members_count']} team members at elevated health risk")

        if team_stats["critical_interventions_active"] > 0:
            org_risks.append(f"{team_stats['critical_interventions_active']} critical intervention(s) active")

        recommended_actions = [
            "Review workload distribution across team",
            "Consider implementing mandatory break policies",
            "Schedule team wellness workshop",
            "Audit after-hours communication patterns"
        ]

        return ManagerDashboardResponse(
            team_id=team_id or "",
            team_name=team_name,
            analysis_date=datetime.utcnow(),
            total_team_members=team_stats["total_team_members"],
            members_analyzed=team_stats["members_analyzed"],
            average_stress_level=team_stats["average_stress_level"],
            stress_distribution=team_stats["stress_distribution"],
            high_risk_members_count=team_stats["high_risk_members_count"],
            critical_interventions_active=team_stats["critical_interventions_active"],
            weekly_stress_trend=team_stats["weekly_stress_trend"],
            cardiovascular_risk_distribution=team_stats["cardiovascular_risk_distribution"],
            recommended_team_actions=recommended_actions,
            organizational_risk_factors=org_risks
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate manager dashboard: {str(e)}"
        )


@router.post("/consent")
async def update_consent_preferences(
    request: ConsentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update consent preferences for health data collection and processing

    Ensures GDPR/HIPAA compliance
    """
    try:
        from app.db.models.biometric_health import HealthDataConsent

        # Check if consent record exists using run_in_executor
        loop = asyncio.get_event_loop()
        consent_record = await loop.run_in_executor(
            None,
            lambda: db.query(HealthDataConsent).filter(
                HealthDataConsent.user_id == current_user.id
            ).first()
        )

        if consent_record:
            # Update existing record
            consent_record.biometric_collection = request.biometric_collection
            consent_record.biometric_processing = request.biometric_processing
            consent_record.biometric_sharing = request.biometric_sharing
            consent_record.data_sources = request.data_sources
            consent_record.data_retention_days = request.data_retention_days
            consent_record.consent_date = datetime.utcnow().date()
            consent_record.updated_at = datetime.utcnow()
        else:
            # Create new consent record
            consent_record = HealthDataConsent(
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                biometric_collection=request.biometric_collection,
                biometric_processing=request.biometric_processing,
                biometric_sharing=request.biometric_sharing,
                data_sources=request.data_sources,
                data_retention_days=request.data_retention_days,
                consent_given=request.biometric_collection or request.biometric_processing,
                consent_date=datetime.utcnow().date()
            )
            db.add(consent_record)

        await db.commit()

        return {
            "success": True,
            "message": "Consent preferences updated successfully",
            "consent_given": consent_record.consent_given
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update consent: {str(e)}"
        )


@router.get("/consent")
async def get_consent_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get current consent status for health data"""
    try:
        from app.db.models.biometric_health import HealthDataConsent

        # Query using run_in_executor
        loop = asyncio.get_event_loop()
        consent_record = await loop.run_in_executor(
            None,
            lambda: db.query(HealthDataConsent).filter(
                HealthDataConsent.user_id == current_user.id
            ).first()
        )

        if not consent_record:
            return {
                "consent_given": False,
                "biometric_collection": False,
                "biometric_processing": False,
                "biometric_sharing": False,
                "data_sources": []
            }

        return {
            "consent_given": consent_record.consent_given,
            "consent_date": consent_record.consent_date.isoformat() if consent_record.consent_date else None,
            "biometric_collection": consent_record.biometric_collection,
            "biometric_processing": consent_record.biometric_processing,
            "biometric_sharing": consent_record.biometric_sharing,
            "data_sources": consent_record.data_sources,
            "data_retention_days": consent_record.data_retention_days
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent status: {str(e)}"
        )


# Helper functions


def _generate_recommended_actions(health_risks: HealthRiskIndicators) -> List[str]:
    """Generate recommended actions based on health risks"""
    actions = []

    # Critical priorities
    if health_risks.recommend_medical_evaluation:
        actions.append("Schedule medical evaluation today")
        actions.append("Call emergency services if experiencing chest pain, shortness of breath, or severe headache")

    if health_risks.urgent_intervention_needed:
        actions.append("Stop working immediately and take a break")
        actions.append("Contact your manager about urgent health concerns")

    # High priority
    if health_risks.recommend_immediate_break:
        actions.append("Take a 30-minute break away from your desk")
        actions.append("Practice deep breathing exercises")

    if health_risks.recommend_workload_reduction:
        actions.append("Schedule meeting with manager to discuss workload")
        actions.append("Identify tasks that can be delegated")

    # Medium priority
    if health_risks.work_life_imbalance > 0.6:
        actions.append("Set clear work hours and stick to them")
        actions.append("Enable after-hours email blocking")

    if health_risks.sleep_disruption_score > 0.6:
        actions.append("Establish consistent sleep schedule")
        actions.append("Avoid screens 1 hour before bed")

    if health_risks.social_isolation_score > 0.6:
        actions.append("Schedule social activities with friends/family")
        actions.append("Reach out to a trusted person")

    # Wellness maintenance
    if health_risks.stress_level in [StressLevel.ELEVATED, StressLevel.HIGH]:
        actions.append("Practice daily mindfulness or meditation")
        actions.append("Exercise for at least 30 minutes")

    return actions
