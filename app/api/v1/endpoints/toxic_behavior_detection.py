"""
Toxic Behavior Detection API Endpoints
REST API for detecting, analyzing, and preventing toxic workplace behaviors
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_active_user, get_current_user, get_db
from app.core.logging_config import logger
from app.db.models.toxicity_detection import (
    BehavioralIntervention,
    PsychologicalSafetyMetrics,
    ToxicityLevel,
    ToxicityPattern,
    ToxicityType,
)
from app.db.models.user import User
from app.services.toxicity_detection_service import toxicity_detection_service

router = APIRouter()


# ============================================
# Pydantic Models
# ============================================


class ToxicityDetectionRequest(BaseModel):
    """Request model for toxicity detection analysis"""

    organization_id: UUID
    team_id: Optional[UUID] = None
    period_days: int = Field(default=30, ge=1, le=90)


class ToxicityIndicator(BaseModel):
    """Individual toxicity indicator"""

    indicator_type: str
    description: str
    severity: float
    confidence: float
    evidence: List[str]


class ToxicPattern(BaseModel):
    """Detected toxic pattern"""

    type: str
    frequency: int
    severity_score: float
    detection_confidence: float


class ToxicityAnalysisResponse(BaseModel):
    """Response model for toxicity analysis"""

    toxicity_level: str
    risk_score: float
    patterns_detected: List[ToxicPattern]
    behavioral_indicators: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    data_insufficient: bool
    analysis_period_days: int
    communications_analyzed: int


class AnonymousReportRequest(BaseModel):
    """Request model for anonymous toxic behavior report"""

    report_type: ToxicityType
    description: str = Field(..., min_length=20, max_length=2000)
    perpetrator_hint: Optional[str] = Field(None, max_length=500)
    evidence_metadata: Optional[Dict[str, Any]] = None
    organization_id: UUID


class AnonymousReportResponse(BaseModel):
    """Response model for anonymous report submission"""

    tracking_id: str
    status: str
    message: str
    submitted_at: datetime


class InterventionRequest(BaseModel):
    """Request model for creating intervention"""

    toxicity_pattern_id: UUID
    intervention_type: str = Field(..., max_length=100)
    intervention_method: str = Field(..., max_length=100)
    priority_level: str = Field(
        default="medium", pattern="^(low|medium|high|critical)$"
    )
    intervention_description: str = Field(..., min_length=10, max_length=2000)
    behavioral_goals: List[str]
    target_group_type: str = Field(..., pattern="^(individual|team|organization)$")


class InterventionResponse(BaseModel):
    """Response model for intervention"""

    intervention_id: UUID
    status: str
    scheduled_date: Optional[datetime]
    message: str


# ============================================
# Endpoints
# ============================================


@router.post("/detect", response_model=ToxicityAnalysisResponse)
async def detect_toxic_behavior(
    request: ToxicityDetectionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze team/organization for toxic behavior patterns

    Uses AI to detect:
    - Bullying and harassment patterns
    - Micromanagement behaviors
    - Power abuse (Gapjil)
    - Public humiliation
    - Exclusion tactics
    - Passive-aggressive behavior
    """
    try:
        # Verify user has access to this organization
        if current_user.organization_id != request.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this organization",
            )

        # Run toxicity detection
        analysis = await toxicity_detection_service.analyze_team_toxicity(
            db=db,
            organization_id=str(request.organization_id),
            team_id=str(request.team_id) if request.team_id else None,
            period_days=request.period_days,
        )

        return ToxicityAnalysisResponse(**analysis)

    except Exception as e:
        logger.error(f"Toxicity detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze toxicity: {str(e)}",
        )


@router.get("/patterns")
async def get_toxicity_patterns(
    organization_id: UUID,
    team_id: Optional[UUID] = None,
    severity: Optional[ToxicityLevel] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detected toxicity patterns for organization/team

    Returns paginated list of toxicity patterns with filtering options
    """
    try:
        loop = asyncio.get_event_loop()

        # Build query
        def build_query():
            query = db.query(ToxicityPattern).filter(
                ToxicityPattern.organization_id == organization_id
            )

            if team_id:
                query = query.filter(ToxicityPattern.team_id == team_id)

            if severity:
                query = query.filter(ToxicityPattern.severity_level == severity.value)

            if status:
                query = query.filter(ToxicityPattern.status == status)

            # Order by detection date (most recent first)
            query = query.order_by(ToxicityPattern.detection_date.desc())

            return query

        query = await loop.run_in_executor(None, build_query)

        # Paginate
        total = await loop.run_in_executor(None, query.count)
        patterns = await loop.run_in_executor(
            None, lambda: query.offset(offset).limit(limit).all()
        )

        return {
            "patterns": [
                {
                    "id": str(pattern.id),
                    "pattern_type": pattern.pattern_type,
                    "severity_level": pattern.severity_level,
                    "confidence_score": float(pattern.confidence_score),
                    "detection_date": pattern.detection_date.isoformat(),
                    "frequency_score": (
                        float(pattern.frequency_score)
                        if pattern.frequency_score
                        else None
                    ),
                    "impact_score": (
                        float(pattern.impact_score) if pattern.impact_score else None
                    ),
                    "intervention_required": pattern.intervention_required,
                    "intervention_priority": pattern.intervention_priority,
                    "status": pattern.status,
                    "behavioral_indicators": pattern.behavioral_indicators,
                    "evidence_summary": pattern.evidence_summary,
                    "risk_score": pattern.calculate_overall_risk_score(),
                }
                for pattern in patterns
            ],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"Failed to fetch toxicity patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patterns: {str(e)}",
        )


@router.get("/trends")
async def get_toxicity_trends(
    organization_id: UUID,
    team_id: Optional[UUID] = None,
    days_back: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get toxicity trends over time

    Returns trend data showing how toxicity patterns have changed
    """
    try:
        trends = toxicity_detection_service.get_toxicity_trends(
            db=db,
            organization_id=str(organization_id),
            team_id=str(team_id) if team_id else None,
            days_back=days_back,
        )

        return trends

    except Exception as e:
        logger.error(f"Failed to fetch toxicity trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}",
        )


@router.post("/anonymous-report", response_model=AnonymousReportResponse)
async def submit_anonymous_report(
    request: AnonymousReportRequest, db: AsyncSession = Depends(get_async_db)
):
    """
    Submit anonymous toxic behavior report

    Allows employees to report toxic behaviors without revealing their identity.
    Returns a tracking ID for follow-up.
    """
    try:
        import secrets

        # Generate tracking ID
        tracking_id = f"TOXIC-{secrets.token_hex(8).upper()}"

        # Create toxicity pattern from report
        pattern = ToxicityPattern(
            organization_id=request.organization_id,
            team_id=None,  # Anonymous, no team info
            pattern_type=request.report_type.value,
            severity_level=ToxicityLevel.HIGH,  # Reports are treated seriously
            confidence_score=0.8,  # Self-reported, moderate confidence
            behavioral_indicators=["anonymous_report"],
            communication_patterns={
                "report_source": "anonymous_submission",
                "tracking_id": tracking_id,
            },
            involved_anonymous_ids={
                "reporter": "anonymous",
                "perpetrator_hint": request.perpetrator_hint,
            },
            detection_date=datetime.utcnow().date(),
            frequency_score=1.0,
            impact_score=8.0,
            intervention_required=True,
            intervention_priority="high",
            status="reported",
            evidence_summary=request.description,
            related_incidents=request.evidence_metadata,
        )

        db.add(pattern)
        db.commit()

        logger.info(f"Anonymous toxic behavior report submitted: {tracking_id}")

        return AnonymousReportResponse(
            tracking_id=tracking_id,
            status="submitted",
            message="Your report has been submitted anonymously. HR will review it within 24-48 hours. You can check status using your tracking ID.",
            submitted_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to submit anonymous report: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit report: {str(e)}",
        )


@router.get("/anonymous-report/{tracking_id}")
async def check_anonymous_report_status(
    tracking_id: str, db: AsyncSession = Depends(get_async_db)
):
    """
    Check status of anonymous report using tracking ID

    Allows reporters to check on their report status without revealing identity
    """
    try:
        loop = asyncio.get_event_loop()
        pattern = await loop.run_in_executor(
            None,
            lambda: db.query(ToxicityPattern)
            .filter(ToxicityPattern.evidence_summary.ilike(f"%{tracking_id}%"))
            .first(),
        )

        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found. Check your tracking ID.",
            )

        return {
            "tracking_id": tracking_id,
            "status": pattern.status,
            "pattern_type": pattern.pattern_type,
            "severity_level": pattern.severity_level,
            "intervention_required": pattern.intervention_required,
            "last_updated": pattern.updated_at,
            "message": "Your report is being reviewed. Thank you for speaking up.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check report status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check status: {str(e)}",
        )


@router.post("/interventions", response_model=InterventionResponse)
async def create_intervention(
    request: InterventionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create behavioral intervention for toxicity pattern

    Creates an intervention plan to address detected toxic behavior
    """
    try:
        loop = asyncio.get_event_loop()

        # Get toxicity pattern
        pattern = await loop.run_in_executor(
            None,
            lambda: db.query(ToxicityPattern)
            .filter(ToxicityPattern.id == request.toxicity_pattern_id)
            .first(),
        )

        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Toxicity pattern not found",
            )

        # Create intervention
        intervention = BehavioralIntervention(
            toxicity_pattern_id=request.toxicity_pattern_id,
            intervention_type=request.intervention_type,
            intervention_method=request.intervention_method,
            priority_level=request.priority_level,
            target_group_type=request.target_group_type,
            intervention_description=request.intervention_description,
            behavioral_goals=request.behavioral_goals,
            success_metrics=["reduction_in_toxicity_patterns"],
            assigned_to=current_user.id,
            status="planned",
            monitoring_period_days=30,
        )

        db.add(intervention)

        # Update pattern status
        pattern.status = "intervention_planned"

        db.commit()

        logger.info(f"Intervention created for pattern {request.toxicity_pattern_id}")

        return InterventionResponse(
            intervention_id=intervention.id,
            status=intervention.status,
            scheduled_date=intervention.scheduled_date,
            message="Intervention created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create intervention: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create intervention: {str(e)}",
        )


@router.get("/interventions")
async def get_interventions(
    organization_id: UUID,
    team_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get behavioral interventions for organization/team

    Returns list of interventions with their status and details
    """
    try:
        loop = asyncio.get_event_loop()

        # Get all pattern IDs for this org
        def build_pattern_query():
            pattern_query = db.query(ToxicityPattern.id).filter(
                ToxicityPattern.organization_id == organization_id
            )

            if team_id:
                pattern_query = pattern_query.filter(ToxicityPattern.team_id == team_id)

            return pattern_query

        pattern_query = await loop.run_in_executor(None, build_pattern_query)
        pattern_ids = [
            p[0] for p in await loop.run_in_executor(None, pattern_query.all)
        ]

        # Get interventions
        def build_intervention_query():
            query = db.query(BehavioralIntervention).filter(
                BehavioralIntervention.toxicity_pattern_id.in_(pattern_ids)
            )

            if status:
                query = query.filter(BehavioralIntervention.status == status)

            return query.order_by(BehavioralIntervention.created_at.desc()).limit(limit)

        interventions = await loop.run_in_executor(
            None, lambda: build_intervention_query().all()
        )

        return {
            "interventions": [
                {
                    "id": str(intervention.id),
                    "toxicity_pattern_id": str(intervention.toxicity_pattern_id),
                    "intervention_type": intervention.intervention_type,
                    "intervention_method": intervention.intervention_method,
                    "priority_level": intervention.priority_level,
                    "intervention_description": intervention.intervention_description,
                    "behavioral_goals": intervention.behavioral_goals,
                    "status": intervention.status,
                    "scheduled_date": (
                        intervention.scheduled_date.isoformat()
                        if intervention.scheduled_date
                        else None
                    ),
                    "completed_date": (
                        intervention.completed_date.isoformat()
                        if intervention.completed_date
                        else None
                    ),
                    "effectiveness_rating": (
                        float(intervention.effectiveness_rating)
                        if intervention.effectiveness_rating
                        else None
                    ),
                    "created_at": intervention.created_at.isoformat(),
                }
                for intervention in interventions
            ],
            "total": len(interventions),
        }

    except Exception as e:
        logger.error(f"Failed to fetch interventions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interventions: {str(e)}",
        )


@router.get("/psychological-safety")
async def get_psychological_safety_metrics(
    organization_id: UUID,
    team_id: Optional[UUID] = None,
    days_back: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get psychological safety metrics for team/organization

    Returns comprehensive psychological safety assessment including:
    - Speak-up safety
    - Mistake tolerance
    - Inclusion safety
    - Learning safety
    - Challenge safety
    """
    try:
        loop = asyncio.get_event_loop()
        cutoff_date = datetime.utcnow().date() - timedelta(days=days_back)

        def build_query():
            query = db.query(PsychologicalSafetyMetrics).filter(
                and_(
                    PsychologicalSafetyMetrics.organization_id == organization_id,
                    PsychologicalSafetyMetrics.measurement_date >= cutoff_date,
                )
            )

            if team_id:
                query = query.filter(PsychologicalSafetyMetrics.team_id == team_id)

            return query.order_by(PsychologicalSafetyMetrics.measurement_date.desc())

        metrics = await loop.run_in_executor(None, lambda: build_query().all())

        if not metrics:
            return {
                "metrics": [],
                "current_score": None,
                "trend_direction": "insufficient_data",
                "risk_level": "unknown",
                "message": "No psychological safety data available for this period",
            }

        # Get most recent metric
        current = metrics[0]

        # Calculate trend
        if len(metrics) >= 2:
            recent_avg = sum(
                m.calculate_overall_score() or 0
                for m in metrics[: min(7, len(metrics))]
            ) / min(7, len(metrics))
            earlier_avg = sum(
                m.calculate_overall_score() or 0
                for m in metrics[7:14]
                if len(metrics) > 7
            ) / max(1, len(metrics) - 7)

            if recent_avg > earlier_avg * 1.1:
                trend = "improving"
            elif recent_avg < earlier_avg * 0.9:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "metrics": [
                {
                    "id": str(m.id),
                    "measurement_date": m.measurement_date.isoformat(),
                    "psychological_safety_score": float(m.calculate_overall_score()),
                    "speak_up_safety": (
                        float(m.speak_up_safety) if m.speak_up_safety else None
                    ),
                    "mistake_tolerance": (
                        float(m.mistake_tolerance) if m.mistake_tolerance else None
                    ),
                    "inclusion_safety": (
                        float(m.inclusion_safety) if m.inclusion_safety else None
                    ),
                    "learning_safety": (
                        float(m.learning_safety) if m.learning_safety else None
                    ),
                    "challenge_safety": (
                        float(m.challenge_safety) if m.challenge_safety else None
                    ),
                    "trust_level": float(m.trust_level) if m.trust_level else None,
                    "respect_score": (
                        float(m.respect_score) if m.respect_level else None
                    ),
                    "collaboration_quality": (
                        float(m.collaboration_quality)
                        if m.collaboration_quality
                        else None
                    ),
                    "toxicity_indicators": m.toxicity_indicators,
                    "conflict_level": (
                        float(m.conflict_level) if m.conflict_level else None
                    ),
                    "stress_level": float(m.stress_level) if m.stress_level else None,
                    "risk_factors": m.risk_factors,
                    "strengths": m.strengths,
                    "improvement_recommendations": m.improvement_recommendations,
                }
                for m in metrics
            ],
            "current_score": current.calculate_overall_score(),
            "trend_direction": trend,
            "risk_level": current.get_risk_level(),
            "total_measurements": len(metrics),
        }

    except Exception as e:
        logger.error(f"Failed to fetch psychological safety metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}",
        )


@router.get("/dashboard")
async def get_toxicity_dashboard(
    organization_id: UUID,
    team_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive dashboard data for toxic behavior detection

    Returns summary statistics and key metrics for dashboard view
    """
    try:
        loop = asyncio.get_event_loop()
        cutoff_date = datetime.utcnow().date() - timedelta(days=30)

        # Get recent patterns
        def build_pattern_query():
            pattern_query = db.query(ToxicityPattern).filter(
                and_(
                    ToxicityPattern.organization_id == organization_id,
                    ToxicityPattern.detection_date >= cutoff_date,
                )
            )

            if team_id:
                pattern_query = pattern_query.filter(ToxicityPattern.team_id == team_id)

            return pattern_query

        recent_patterns = await loop.run_in_executor(
            None, lambda: build_pattern_query().all()
        )

        # Calculate statistics
        total_patterns = len(recent_patterns)
        critical_patterns = len(
            [p for p in recent_patterns if p.severity_level == ToxicityLevel.CRITICAL]
        )
        high_patterns = len(
            [p for p in recent_patterns if p.severity_level == ToxicityLevel.HIGH]
        )
        intervention_required = len(
            [p for p in recent_patterns if p.intervention_required]
        )

        # Pattern type breakdown
        pattern_types = {}
        for pattern in recent_patterns:
            pattern_types[pattern.pattern_type] = (
                pattern_types.get(pattern.pattern_type, 0) + 1
            )

        # Get active interventions
        pattern_ids = [p.id for p in recent_patterns]
        active_interventions = await loop.run_in_executor(
            None,
            lambda: db.query(BehavioralIntervention)
            .filter(
                and_(
                    BehavioralIntervention.toxicity_pattern_id.in_(pattern_ids),
                    BehavioralIntervention.status.in_(["planned", "in_progress"]),
                )
            )
            .count(),
        )

        # Get latest psychological safety score
        latest_ps = await loop.run_in_executor(
            None,
            lambda: db.query(PsychologicalSafetyMetrics)
            .filter(PsychologicalSafetyMetrics.organization_id == organization_id)
            .order_by(PsychologicalSafetyMetrics.measurement_date.desc())
            .first(),
        )

        ps_score = float(latest_ps.calculate_overall_score()) if latest_ps else None
        ps_risk_level = latest_ps.get_risk_level() if latest_ps else None

        return {
            "summary": {
                "total_patterns": total_patterns,
                "critical_patterns": critical_patterns,
                "high_patterns": high_patterns,
                "intervention_required": intervention_required,
                "active_interventions": active_interventions,
                "psychological_safety_score": ps_score,
                "psychological_safety_risk_level": ps_risk_level,
            },
            "pattern_breakdown": pattern_types,
            "recent_activity": [
                {
                    "date": p.detection_date.isoformat(),
                    "type": p.pattern_type,
                    "severity": p.severity_level,
                    "status": p.status,
                }
                for p in sorted(
                    recent_patterns, key=lambda x: x.detection_date, reverse=True
                )[:10]
            ],
        }

    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}",
        )
