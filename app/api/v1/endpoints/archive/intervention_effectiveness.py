"""
Intervention Effectiveness API Endpoints

REST API endpoints for intervention tracking, analysis, and effectiveness evaluation.
Provides comprehensive endpoints for managing interventions and analyzing their impact.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.intervention_effectiveness import (
    Intervention,
    InterventionEffectiveness,
    InterventionParticipant,
    PostInterventionMeasurement,
    PreInterventionMeasurement,
)
from app.db.models.user import User
from app.services.intervention_analysis import InterventionAnalyzer
from app.services.statistical_significance import StatisticalSignificanceTester

router = APIRouter(
    prefix="/intervention-effectiveness", tags=["intervention-effectiveness"]
)


# Request/Response Models
class InterventionCreateRequest(BaseModel):
    """Request model for creating interventions"""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    intervention_type: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    target_metrics: Optional[List[str]] = None
    expected_outcomes: Optional[List[str]] = None
    success_criteria: Optional[Dict[str, Any]] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[int] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    budget: Optional[float] = Field(None, ge=0)
    participants_target: Optional[int] = Field(None, ge=1)
    implementation_details: Optional[Dict[str, Any]] = None
    external_references: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    team_id: Optional[str] = None


class InterventionUpdateRequest(BaseModel):
    """Request model for updating interventions"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(
        None, pattern="^(planned|active|completed|cancelled)$"
    )

    end_date: Optional[datetime] = None
    actual_participants: Optional[int] = Field(None, ge=0)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    budget: Optional[float] = Field(None, ge=0)


class ParticipantEnrollmentRequest(BaseModel):
    """Request model for enrolling participants"""

    user_ids: List[str] = Field(..., min_items=1)
    participant_role: str = Field(
        default="participant", pattern="^(participant|facilitator|observer)$"
    )
    enrollment_notes: Optional[str] = None


class MeasurementRequest(BaseModel):
    """Request model for adding measurements"""

    user_id: str
    metric_name: str = Field(..., min_length=1, max_length=100)
    metric_value: float
    metric_type: str = Field(..., min_length=1, max_length=50)
    measurement_date: datetime
    measurement_method: Optional[str] = None
    data_source: Optional[str] = None
    confidence_level: Optional[float] = Field(None, ge=0, le=1)
    sample_size: Optional[int] = Field(None, ge=1)
    qualitative_notes: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request model for intervention analysis"""

    intervention_id: str
    metrics: Optional[List[str]] = None
    control_group_id: Optional[str] = None
    follow_up_days: Optional[int] = Field(None, ge=0)
    significance_level: float = Field(default=0.05, ge=0.001, le=0.1)
    power_threshold: float = Field(default=0.8, ge=0.5, le=0.99)


class InterventionResponse(BaseModel):
    """Response model for intervention data"""

    id: str
    organization_id: Optional[str]
    team_id: Optional[str]
    created_by: str
    title: str
    description: Optional[str]
    intervention_type: str
    category: str
    target_metrics: Optional[List[str]]
    expected_outcomes: Optional[List[str]]
    success_criteria: Optional[Dict[str, Any]]
    start_date: datetime
    end_date: Optional[datetime]
    duration_days: Optional[int]
    status: str
    priority: str
    budget: Optional[float]
    participants_target: Optional[int]
    actual_participants: Optional[int]
    completion_rate: Optional[float]
    implementation_details: Optional[Dict[str, Any]]
    external_references: Optional[List[str]]
    tags: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MeasurementResponse(BaseModel):
    """Response model for measurement data"""

    id: str
    intervention_id: str
    user_id: str
    metric_name: str
    metric_value: float
    metric_type: str
    measurement_date: datetime
    measurement_method: Optional[str]
    data_source: Optional[str]
    confidence_level: Optional[float]
    sample_size: Optional[int]
    qualitative_notes: Optional[str]
    created_at: datetime


class EffectivenessResponse(BaseModel):
    """Response model for effectiveness analysis"""

    intervention_id: str
    metric_name: str
    effect_size: float
    confidence_interval: Optional[List[float]]
    p_value: Optional[float]
    statistical_significance: Optional[bool]
    test_type: str
    sample_size_pre: Optional[int]
    sample_size_post: Optional[int]
    pre_intervention_mean: Optional[float]
    post_intervention_mean: Optional[float]
    percent_improvement: Optional[float]
    clinical_significance: Optional[str]
    practical_significance: Optional[bool]
    effect_category: str
    recommendations: Optional[str]
    created_at: datetime


class AnalysisSummaryResponse(BaseModel):
    """Response model for analysis summary"""

    intervention_id: str
    analysis_date: datetime
    total_metrics: int
    significant_metrics: int
    average_effect_size: float
    statistical_power: float
    bayesian_evidence: Dict[str, int]
    overall_recommendation: str
    confidence_score: float
    limitations: List[str]


# Core Endpoints


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/interventions", response_model=InterventionResponse)
async def create_intervention(
    request: InterventionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new intervention"""
    try:
        # ✅ Run sync db operations in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        intervention = Intervention(
            organization_id=current_user.organization_id,
            team_id=request.team_id,
            created_by=current_user.id,
            title=request.title,
            description=request.description,
            intervention_type=request.intervention_type,
            category=request.category,
            target_metrics=request.target_metrics,
            expected_outcomes=request.expected_outcomes,
            success_criteria=request.success_criteria,
            start_date=request.start_date,
            end_date=request.end_date,
            duration_days=request.duration_days,
            status="planned",
            priority=request.priority,
            budget=request.budget,
            participants_target=request.participants_target,
            implementation_details=request.implementation_details,
            external_references=request.external_references,
            tags=request.tags,
        )

        await loop.run_in_executor(None, lambda: db.add(intervention))
        await loop.run_in_executor(None, db.commit)
        await loop.run_in_executor(None, lambda: db.refresh(intervention))

        return InterventionResponse.from_orm(intervention)

    except Exception as e:
        logger.error(f"Unexpected error: {e!s}", exc_info=True)
        await loop.run_in_executor(None, db.rollback)
        raise HTTPException(
            status_code=500, detail=f"Failed to create intervention: {str(e)}"
        )


@router.get("/interventions", response_model=List[InterventionResponse])
async def list_interventions(
    status: Optional[str] = Query(
        None, pattern="^(planned|active|completed|cancelled|paused)$"
    ),
    intervention_type: Optional[str] = None,
    category: Optional[str] = None,
    team_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List interventions with filtering"""
    try:
        # ✅ Run sync db operations in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        def query_db():
            query = db.query(Intervention).filter(
                Intervention.organization_id == current_user.organization_id,
                Intervention.is_active == True,
            )

            if status:
                query = query.filter(Intervention.status == status)
            if intervention_type:
                query = query.filter(
                    Intervention.intervention_type == intervention_type
                )
            if category:
                query = query.filter(Intervention.category == category)
            if team_id:
                query = query.filter(Intervention.team_id == team_id)

            interventions = (
                query.order_by(Intervention.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return interventions

        interventions = await loop.run_in_executor(None, query_db)

        return [
            InterventionResponse.from_orm(intervention)
            for intervention in interventions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list interventions: {str(e)}"
        )


@router.get("/interventions/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific intervention details"""
    try:
        # ✅ Run sync db operations in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        intervention = await loop.run_in_executor(
            None,
            lambda: db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
                Intervention.is_active == True,
            )
            .first(),
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        return InterventionResponse.from_orm(intervention)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get intervention: {str(e)}"
        )


@router.put("/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: str,
    request: InterventionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update intervention details"""
    try:
        # ✅ Run sync db operations in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        intervention = await loop.run_in_executor(
            None,
            lambda: db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first(),
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(intervention, field, value)

        intervention.updated_at = datetime.utcnow()
        await loop.run_in_executor(None, db.commit)
        await loop.run_in_executor(None, lambda: db.refresh(intervention))

        return InterventionResponse.from_orm(intervention)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e!s}", exc_info=True)
        await loop.run_in_executor(None, db.rollback)
        raise HTTPException(
            status_code=500, detail=f"Failed to update intervention: {str(e)}"
        )


# Participant Management
@router.post("/interventions/{intervention_id}/participants")
async def enroll_participants(
    intervention_id: str,
    request: ParticipantEnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Enroll participants in intervention"""
    try:
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        enrolled_count = 0
        for user_id in request.user_ids:
            # Check if already enrolled
            existing = (
                db.query(InterventionParticipant)
                .filter(
                    InterventionParticipant.intervention_id == intervention_id,
                    InterventionParticipant.user_id == user_id,
                )
                .first()
            )

            if existing:
                continue

            participant = InterventionParticipant(
                intervention_id=intervention_id,
                user_id=user_id,
                participant_role=request.participant_role,
                notes=request.enrollment_notes,
            )

            db.add(participant)
            enrolled_count += 1

        # Update actual participants count
        total_participants = (
            db.query(InterventionParticipant)
            .filter(InterventionParticipant.intervention_id == intervention_id)
            .count()
        )
        intervention.actual_participants = total_participants

        db.commit()

        return {
            "enrolled_count": enrolled_count,
            "total_participants": total_participants,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to enroll participants: {str(e)}"
        )


@router.get("/interventions/{intervention_id}/participants")
async def list_participants(
    intervention_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List intervention participants"""
    try:
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        participants = (
            db.query(InterventionParticipant)
            .filter(InterventionParticipant.intervention_id == intervention_id)
            .all()
        )

        return [
            {
                "id": participant.id,
                "user_id": participant.user_id,
                "participant_role": participant.participant_role,
                "enrollment_date": participant.enrollment_date,
                "completion_status": participant.completion_status,
                "engagement_score": participant.engagement_score,
                "attendance_rate": participant.attendance_rate,
            }
            for participant in participants
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list participants: {str(e)}"
        )


# Measurement Management
@router.post(
    "/interventions/{intervention_id}/measurements/pre",
    response_model=MeasurementResponse,
)
async def add_pre_measurement(
    intervention_id: str,
    request: MeasurementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add pre-intervention measurement"""
    try:
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        measurement = PreInterventionMeasurement(
            intervention_id=intervention_id,
            user_id=request.user_id,
            metric_name=request.metric_name,
            metric_value=request.metric_value,
            metric_type=request.metric_type,
            measurement_date=request.measurement_date,
            measurement_method=request.measurement_method,
            data_source=request.data_source,
            confidence_level=request.confidence_level,
            sample_size=request.sample_size,
            qualitative_notes=request.qualitative_notes,
        )

        db.add(measurement)
        db.commit()
        db.refresh(measurement)

        return MeasurementResponse.from_orm(measurement)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to add pre-measurement: {str(e)}"
        )


@router.post(
    "/interventions/{intervention_id}/measurements/post",
    response_model=MeasurementResponse,
)
async def add_post_measurement(
    intervention_id: str,
    request: MeasurementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add post-intervention measurement"""
    try:
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        measurement = PostInterventionMeasurement(
            intervention_id=intervention_id,
            user_id=request.user_id,
            metric_name=request.metric_name,
            metric_value=request.metric_value,
            metric_type=request.metric_type,
            measurement_date=request.measurement_date,
            measurement_method=request.measurement_method,
            data_source=request.data_source,
            confidence_level=request.confidence_level,
            sample_size=request.sample_size,
            qualitative_notes=request.qualitative_notes,
        )

        db.add(measurement)
        db.commit()
        db.refresh(measurement)

        return MeasurementResponse.from_orm(measurement)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to add post-measurement: {str(e)}"
        )


@router.get("/interventions/{intervention_id}/measurements")
async def list_measurements(
    intervention_id: str,
    measurement_type: str = Query(..., pattern="^(pre|post)$"),
    metric_name: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List intervention measurements"""
    try:
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        if measurement_type == "pre":
            query = db.query(PreInterventionMeasurement).filter(
                PreInterventionMeasurement.intervention_id == intervention_id
            )
        else:
            query = db.query(PostInterventionMeasurement).filter(
                PostInterventionMeasurement.intervention_id == intervention_id
            )

        if metric_name:
            query = query.filter(
                getattr(query.column_descriptions[0]["type"], "metric_name")
                == metric_name
            )
        if user_id:
            query = query.filter(
                getattr(query.column_descriptions[0]["type"], "user_id") == user_id
            )

        measurements = query.order_by(
            getattr(query.column_descriptions[0]["type"], "measurement_date")
        ).all()

        return [
            {
                "id": measurement.id,
                "user_id": measurement.user_id,
                "metric_name": measurement.metric_name,
                "metric_value": float(measurement.metric_value),
                "metric_type": measurement.metric_type,
                "measurement_date": measurement.measurement_date,
                "measurement_method": measurement.measurement_method,
                "confidence_level": measurement.confidence_level,
                "qualitative_notes": measurement.qualitative_notes,
            }
            for measurement in measurements
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list measurements: {str(e)}"
        )


# Analysis Endpoints
@router.post("/analyze", response_model=AnalysisSummaryResponse)
async def analyze_intervention_effectiveness(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Analyze intervention effectiveness"""
    try:
        # Verify intervention exists and user has access
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == request.intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        # Initialize analyzers
        intervention_analyzer = InterventionAnalyzer(
            db, significance_level=request.significance_level
        )
        significance_tester = StatisticalSignificanceTester(
            db, alpha=request.significance_level, power=request.power_threshold
        )

        # Perform comprehensive analysis
        analysis_results = (
            await intervention_analyzer.analyze_intervention_effectiveness(
                request.intervention_id,
                request.metrics,
                request.control_group_id,
                request.follow_up_days,
            )
        )

        if not analysis_results:
            raise HTTPException(
                status_code=400, detail="Insufficient data for analysis"
            )

        # Calculate summary statistics
        total_metrics = len(analysis_results)
        significant_metrics = sum(
            1
            for result in analysis_results
            if any(
                test.p_value < request.significance_level
                for test in result.statistical_tests
                if test.p_value
            )
        )
        average_effect_size = (
            sum(
                max([abs(es.effect_size) for es in result.effect_sizes] + [0])
                for result in analysis_results
            )
            / total_metrics
        )

        # Generate overall recommendation
        significant_ratio = significant_metrics / total_metrics
        avg_power = (
            sum(
                result.power_analysis.power
                for result in analysis_results
                if result.power_analysis.power
            )
            / total_metrics
        )

        if significant_ratio >= 0.7 and avg_power >= 0.8:
            overall_recommendation = "Strongly recommended - highly effective"
            confidence_score = 0.9
        elif significant_ratio >= 0.5 and avg_power >= 0.6:
            overall_recommendation = "Recommended - moderately effective"
            confidence_score = 0.7
        elif significant_ratio >= 0.3:
            overall_recommendation = "Consider with modifications"
            confidence_score = 0.5
        else:
            overall_recommendation = "Not recommended - insufficient evidence"
            confidence_score = 0.3

        # Aggregate limitations
        all_limitations = []
        for result in analysis_results:
            all_limitations.extend(result.limitations)

        # Schedule background task to save results
        background_tasks.add_task(
            save_analysis_results,
            request.intervention_id,
            analysis_results,
            current_user.id,
        )

        return AnalysisSummaryResponse(
            intervention_id=request.intervention_id,
            analysis_date=datetime.utcnow(),
            total_metrics=total_metrics,
            significant_metrics=significant_metrics,
            average_effect_size=average_effect_size,
            statistical_power=avg_power,
            bayesian_evidence={
                "strong": 0,
                "moderate": 0,
                "weak": 0,
            },  # Simplified for now
            overall_recommendation=overall_recommendation,
            confidence_score=confidence_score,
            limitations=list(set(all_limitations)),  # Remove duplicates
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/interventions/{intervention_id}/effectiveness",
    response_model=List[EffectivenessResponse],
)
async def get_effectiveness_results(
    intervention_id: str,
    metric_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get saved effectiveness analysis results"""
    try:
        intervention = (
            db.query(Intervention)
            .filter(
                Intervention.id == intervention_id,
                Intervention.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        query = db.query(InterventionEffectiveness).filter(
            InterventionEffectiveness.intervention_id == intervention_id
        )

        if metric_name:
            query = query.filter(InterventionEffectiveness.metric_name == metric_name)

        results = query.order_by(InterventionEffectiveness.created_at.desc()).all()

        return [EffectivenessResponse.from_orm(result) for result in results]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get effectiveness results: {str(e)}"
        )


# Helper Functions
async def save_analysis_results(
    intervention_id: str,
    analysis_results: List[Any],
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Save analysis results to database"""
    try:
        for result in analysis_results:
            for test_result in result.statistical_tests:
                # Save effectiveness analysis
                effectiveness = InterventionEffectiveness(
                    intervention_id=intervention_id,
                    metric_name=result.metric_name,
                    effect_size=max(
                        [abs(es.effect_size) for es in result.effect_sizes] + [0]
                    ),
                    p_value=test_result.p_value,
                    statistical_significance=test_result.p_value < 0.05,
                    test_type=test_result.test_name,
                    sample_size_pre=result.sample_size,
                    sample_size_post=result.sample_size,
                    pre_intervention_mean=float(
                        np.mean(result.pre_post_data.pre_values)
                    ),
                    post_intervention_mean=float(
                        np.mean(result.pre_post_data.post_values)
                    ),
                    effect_category=(
                        "positive"
                        if float(np.mean(result.pre_post_data.post_values))
                        > float(np.mean(result.pre_post_data.pre_values))
                        else "negative"
                    ),
                )

                db.add(effectiveness)

        db.commit()

    except Exception as e:
        logger.error(f"Unexpected error: {e!s}", exc_info=True)
        db.rollback()
        # Log error but don't fail the main request
        print(f"Failed to save analysis results: {e}")
