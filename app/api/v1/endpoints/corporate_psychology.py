"""
Corporate Psychology Encoding Endpoints
System-level organizational psychology for executive decision-making

All endpoints operate at ORGANIZATIONAL level - NO individual diagnostics.
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_current_user, get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.corporate_psychology import (
    CorporatePsychologyMetrics,
    InterventionCategory,
    InterventionStatus,
    RiskHorizon,
    StructuralIntervention,
    SystemSignalAlert,
)
from app.db.models.user import User
from app.services.corporate_psychology_service import (
    CorporatePsychologyService,
    InterventionRecommendation,
    SystemSignal,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/corporate-psychology", tags=["corporate-psychology"])


# ═══════════════════════════════════════════════════════════════
# Request/Response Schemas
# ═══════════════════════════════════════════════════════════════


class PsychologyMetricsResponse(BaseModel):
    """Response model for psychology metrics."""

    organization_id: str
    team_id: Optional[str]
    measurement_period_start: date
    measurement_period_end: date

    # Core encodings
    cognitive_load_index: float
    trust_stability_score: float
    emotional_volatility_score: float
    coordination_friction_score: float
    psychological_debt_score: float
    recovery_resilience_capacity: float
    recovery_resilience_score: float

    # Derived metrics
    organizational_health_index: float
    overall_risk_score: float
    risk_horizon: str

    # Trends
    health_trajectory: str

    created_at: datetime


class SystemSignalResponse(BaseModel):
    """Response model for system signals."""

    id: str
    alert_type: str
    severity: str
    risk_horizon: str
    signal_summary: str
    change_description: str
    operational_impact: str
    current_value: float
    probability_range: str
    recommended_actions: list[str]
    urgency: str
    status: str
    created_at: datetime


class InterventionRequest(BaseModel):
    """Request model for creating intervention."""

    organization_id: str
    team_id: Optional[str] = None
    intervention_title: str
    intervention_description: str
    intervention_category: str
    expected_outcomes: str
    business_rationale: str
    implementation_approach: str
    estimated_duration_weeks: int
    resource_requirements: str


class InterventionResponse(BaseModel):
    """Response model for interventions."""

    id: str
    organization_id: str
    team_id: Optional[str]
    intervention_title: str
    intervention_category: str
    expected_outcomes: str
    status: str
    progress_percentage: float
    created_at: datetime


class AnalysisRequest(BaseModel):
    """Request model for running psychology analysis."""

    organization_id: str
    team_id: Optional[str] = None
    measurement_period_days: int = 30

    # Data sources (will be fetched from existing tables)
    include_culture_metrics: bool = True
    include_wellness_metrics: bool = True
    include_behavioral_metrics: bool = True
    include_communication_metrics: bool = True


class AnalysisResponse(BaseModel):
    """Response model for psychology analysis."""

    success: bool
    message: str
    metrics_id: Optional[str] = None
    signals_generated: int = 0
    interventions_recommended: int = 0


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════


@rate_limit(limit=50, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/metrics/{organization_id}", response_model=PsychologyMetricsResponse)
async def get_psychology_metrics(
    organization_id: str,
    team_id: Optional[str] = Query(None, description="Filter by team if specified"),
    include_history: bool = Query(False, description="Include historical trend data"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PsychologyMetricsResponse:
    """
    Get current Corporate Psychology metrics for an organization

    Returns the 6 core psychology encodings:
    - Cognitive Load Index (CLI)
    - Trust Stability Curve (TSC)
    - Emotional Volatility Signal (EVS)
    - Coordination Friction Score (CFS)
    - Psychological Debt Accumulation (PDA)
    - Recovery & Resilience Capacity (RRC)

    All metrics are at ORGANIZATIONAL level, not individual.
    """
    try:
        org_uuid = uuid.UUID(organization_id)
        # Build query
        query = (
            select(CorporatePsychologyMetrics)
            .where(CorporatePsychologyMetrics.organization_id == org_uuid)
            .order_by(desc(CorporatePsychologyMetrics.measurement_period_end))
            .limit(1)
        )

        if team_id:
            query = query.where(CorporatePsychologyMetrics.team_id == team_id)

        result = await db.execute(query)
        metrics = result.scalar_one_or_none()

        if not metrics:
            logger.info(
                f"No metrics found for org {organization_id}, returning mock data for demo."
            )
            # Mock response for demo purposes
            return PsychologyMetricsResponse(
                organization_id=organization_id,
                team_id=team_id,
                measurement_period_start=date.today() - timedelta(days=30),
                measurement_period_end=date.today(),
                cognitive_load_index=45.0,
                trust_stability_score=75.0,
                emotional_volatility_score=30.0,
                coordination_friction_score=25.0,
                psychological_debt_score=20.0,
                recovery_resilience_capacity=80.0,
                recovery_resilience_score=80.0,
                organizational_health_index=85.0,
                overall_risk_score=15.0,
                risk_horizon="structural",
                health_trajectory="stable",
                created_at=datetime.now(),
            )

        return PsychologyMetricsResponse(
            organization_id=str(metrics.organization_id),
            team_id=str(metrics.team_id) if metrics.team_id else None,
            measurement_period_start=metrics.measurement_period_start,
            measurement_period_end=metrics.measurement_period_end,
            cognitive_load_index=float(metrics.cognitive_load_index),
            trust_stability_score=float(metrics.trust_stability_score),
            emotional_volatility_score=float(metrics.emotional_volatility_score),
            coordination_friction_score=float(metrics.coordination_friction_score),
            psychological_debt_score=float(metrics.psychological_debt_score),
            recovery_resilience_score=float(metrics.recovery_resilience_score),
            organizational_health_index=float(metrics.organizational_health_index),
            overall_risk_score=float(metrics.overall_risk_score),
            risk_horizon=metrics.risk_horizon or "unknown",
            health_trajectory=metrics.health_trajectory or "unknown",
            created_at=metrics.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting psychology metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve psychology metrics: {str(e)}"
        ) from e


@rate_limit(limit=20, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/analyze", response_model=AnalysisResponse)
async def run_psychology_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Run Corporate Psychology analysis for an organization

    Calculates all 6 psychology encodings based on existing data sources:
    - Culture metrics (psychological safety, trust, collaboration)
    - Wellness metrics (burnout risk, stress levels)
    - Behavioral metrics (team dynamics, patterns)
    - Communication metrics (email, collaboration patterns)

    Generates system signals and intervention recommendations as needed.
    """
    try:
        service = CorporatePsychologyService()

        # Calculate measurement period
        measurement_end = date.today()
        measurement_start = date.today() - timedelta(
            days=request.measurement_period_days
        )

        # Gather data from existing sources
        data_sources = await _gather_data_sources(
            db,
            request.organization_id,
            request.team_id,
            measurement_start,
            measurement_end,
            request.include_culture_metrics,
            request.include_wellness_metrics,
            request.include_behavioral_metrics,
            request.include_communication_metrics,
        )

        # Calculate all 6 core encodings
        cli = service.calculate_cognitive_load_index(
            request.organization_id,
            measurement_start,
            measurement_end,
            data_sources,
        )

        tsc = service.calculate_trust_stability_curve(
            request.organization_id,
            measurement_start,
            measurement_end,
            data_sources,
        )

        evs = service.calculate_emotional_volatility_signal(
            request.organization_id,
            measurement_start,
            measurement_end,
            data_sources,
        )

        cfs = service.calculate_coordination_friction_score(
            request.organization_id,
            measurement_start,
            measurement_end,
            data_sources,
        )

        pda = service.calculate_psychological_debt_accumulation(
            request.organization_id,
            measurement_start,
            measurement_end,
            data_sources,
        )

        rrc = service.calculate_recovery_resilience_capacity(
            request.organization_id,
            measurement_start,
            measurement_end,
            data_sources,
        )

        # Calculate aggregate metrics
        health_index = service.calculate_organizational_health_index(
            cli, tsc, evs, cfs, pda, rrc
        )

        encodings = {
            "cli": cli,
            "tsc": tsc,
            "evs": evs,
            "cfs": cfs,
            "pda": pda,
            "rrc": rrc,
        }

        risk_score = service.calculate_overall_risk_score(health_index, encodings)

        # Determine health trajectory
        health_trajectory = _determine_health_trajectory(encodings)

        # Determine risk horizon
        risk_horizon = _determine_risk_horizon(risk_score, encodings)

        # Create metrics record
        metrics_record = CorporatePsychologyMetrics(
            organization_id=request.organization_id,
            team_id=request.team_id,
            measurement_period_start=measurement_start,
            measurement_period_end=measurement_end,
            # Core encodings
            cognitive_load_index=cli.value,
            cli_trend=cli.trend,
            cli_slope=cli.slope,
            cli_acceleration=cli.acceleration,
            trust_stability_score=tsc.value,
            tsc_trend=tsc.trend,
            tsc_volatility=tsc.drivers.get("volatility") if tsc.drivers else None,
            emotional_volatility_score=evs.value,
            evs_trend=evs.trend,
            evs_recovery_time=evs.drivers.get("recovery_time") if evs.drivers else None,
            coordination_friction_score=cfs.value,
            cfs_bottlenecks=(
                cfs.drivers.get("bottleneck_score") if cfs.drivers else None
            ),
            psychological_debt_score=pda.value,
            pda_rate=pda.drivers.get("debt_rate") if pda.drivers else None,
            recovery_resilience_score=rrc.value,
            rrc_buffer=rrc.drivers.get("resilience_buffer") if rrc.drivers else None,
            # Aggregate metrics
            organizational_health_index=health_index,
            health_trajectory=health_trajectory,
            overall_risk_score=risk_score,
            risk_horizon=risk_horizon,
            # Data quality
            data_quality_score=data_sources.get("data_quality", 75.0),
            confidence_level=data_sources.get("confidence", 70.0),
            sample_size=data_sources.get("sample_size", 0),
        )

        db.add(metrics_record)
        await db.flush()  # Get the ID

        # Generate system signals
        signals = service.generate_system_signals(
            request.organization_id,
            encodings,
            health_index,
            risk_score,
        )

        # Create signal alerts
        for signal in signals:
            alert_record = SystemSignalAlert(
                organization_id=request.organization_id,
                team_id=request.team_id,
                alert_date=date.today(),
                alert_type=signal.alert_type,
                severity=signal.severity,
                risk_horizon=signal.risk_horizon,
                signal_summary=signal.summary,
                change_description=signal.description,
                rate_of_change=signal.rate_of_change,
                operational_impact=signal.operational_impact,
                current_value=signal.current_value,
                baseline_value=signal.baseline_value,
                probability_range=signal.probability_range,
                urgency=signal.urgency,
                status="active",
                confidence_level=75.0,  # Default confidence
            )
            db.add(alert_record)

        # Generate intervention recommendations
        interventions = service.generate_intervention_recommendations(
            signals,
            encodings,
        )

        # Create intervention records for recommendations
        for intervention in interventions:
            intervention_record = StructuralIntervention(
                organization_id=request.organization_id,
                team_id=request.team_id,
                intervention_title=intervention.title,
                intervention_description=intervention.description,
                intervention_category=intervention.category.value,
                expected_outcomes=intervention.expected_outcomes,
                business_rationale=intervention.business_rationale,
                implementation_approach=intervention.implementation_approach,
                estimated_duration_weeks=intervention.estimated_duration_weeks,
                resource_requirements=intervention.resource_requirements,
                proposed_date=date.today(),
                status="proposed",
            )
            db.add(intervention_record)

        await db.commit()

        logger.info(
            f"Psychology analysis completed for org {request.organization_id}: "
            f"health={health_index}, risk={risk_score}, "
            f"signals={len(signals)}, interventions={len(interventions)}"
        )

        return AnalysisResponse(
            success=True,
            message="Psychology analysis completed successfully",
            metrics_id=str(metrics_record.id),
            signals_generated=len(signals),
            interventions_recommended=len(interventions),
        )

    except Exception as e:
        logger.error(f"Error running psychology analysis: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to run psychology analysis: {str(e)}"
        ) from e


@rate_limit(limit=50, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/signals/{organization_id}")
async def get_system_signals(
    organization_id: str,
    team_id: Optional[str] = Query(None),
    status: Optional[str] = Query(
        None, description="Filter by status: active, acknowledged, resolved"
    ),
    severity: Optional[str] = Query(
        None, description="Filter by severity: low, medium, high, critical"
    ),
    limit: int = Query(50, description="Maximum number of signals to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SystemSignalResponse]:
    """
    Get system signals (early-warning alerts) for an organization

    Returns active and historical signals indicating:
    - What is changing in the organization
    - How fast changes are occurring
    - Why it matters operationally
    - Recommended interventions
    """
    try:
        org_uuid = uuid.UUID(organization_id)
        query = (
            select(SystemSignalAlert)
            .where(SystemSignalAlert.organization_id == org_uuid)
            .order_by(desc(SystemSignalAlert.created_at))
            .limit(limit)
        )

        if team_id:
            query = query.where(SystemSignalAlert.team_id == team_id)

        if status:
            query = query.where(SystemSignalAlert.status == status)

        if severity:
            query = query.where(SystemSignalAlert.severity == severity)

        result = await db.execute(query)
        alerts = result.scalars().all()

        return [
            SystemSignalResponse(
                id=str(alert.id),
                alert_type=alert.alert_type,
                severity=alert.severity,
                risk_horizon=alert.risk_horizon,
                signal_summary=alert.signal_summary,
                change_description=alert.change_description,
                operational_impact=alert.operational_impact,
                current_value=float(alert.current_value),
                probability_range=alert.probability_range or "unknown",
                recommended_actions=[],  # Would parse from JSON in production
                urgency=alert.urgency,
                status=alert.status,
                created_at=alert.created_at,
            )
            for alert in alerts
        ]

    except Exception as e:
        logger.error(f"Error getting system signals: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve system signals: {str(e)}"
        ) from e


@rate_limit(limit=50, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/interventions/{organization_id}")
async def get_interventions(
    organization_id: str,
    team_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[InterventionResponse]:
    """
    Get structural interventions for an organization

    Returns proposed, approved, and in-progress interventions including:
    - Process changes
    - Cadence adjustments
    - Incentive modifications
    - Structural changes
    - Communication improvements
    - Workload rebalancing
    """
    try:
        org_uuid = uuid.UUID(organization_id)
        query = (
            select(StructuralIntervention)
            .where(StructuralIntervention.organization_id == org_uuid)
            .order_by(desc(StructuralIntervention.created_at))
        )

        if team_id:
            query = query.where(StructuralIntervention.team_id == team_id)

        if status:
            query = query.where(StructuralIntervention.status == status)

        if category:
            query = query.where(
                StructuralIntervention.intervention_category == category
            )

        result = await db.execute(query)
        interventions = result.scalars().all()

        return [
            InterventionResponse(
                id=str(intervention.id),
                organization_id=str(intervention.organization_id),
                team_id=str(intervention.team_id) if intervention.team_id else None,
                intervention_title=intervention.intervention_title,
                intervention_category=intervention.intervention_category,
                expected_outcomes=intervention.expected_outcomes,
                status=intervention.status,
                progress_percentage=float(intervention.progress_percentage or 0),
                created_at=intervention.created_at,
            )
            for intervention in interventions
        ]

    except Exception as e:
        logger.error(f"Error getting interventions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve interventions: {str(e)}"
        ) from e


@rate_limit(limit=10, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/interventions")
async def create_intervention(
    request: InterventionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> InterventionResponse:
    """
    Create a new structural intervention

    Creates a proposed intervention to address organizational psychology issues.
    Interventions are structural, not individual-focused.
    """
    try:
        intervention_record = StructuralIntervention(
            organization_id=request.organization_id,
            team_id=request.team_id,
            intervention_title=request.intervention_title,
            intervention_description=request.intervention_description,
            intervention_category=request.intervention_category,
            expected_outcomes=request.expected_outcomes,
            business_rationale=request.business_rationale,
            implementation_approach=request.implementation_approach,
            estimated_duration_weeks=request.estimated_duration_weeks,
            resource_requirements=request.resource_requirements,
            proposed_date=date.today(),
            status="proposed",
            approval_status="pending",
            created_by=str(current_user.id),
        )

        db.add(intervention_record)
        await db.commit()
        await db.refresh(intervention_record)

        logger.info(
            f"Intervention created: {request.intervention_title} "
            f"for org {request.organization_id}"
        )

        return InterventionResponse(
            id=str(intervention_record.id),
            organization_id=str(intervention_record.organization_id),
            team_id=(
                str(intervention_record.team_id)
                if intervention_record.team_id
                else None
            ),
            intervention_title=intervention_record.intervention_title,
            intervention_category=intervention_record.intervention_category,
            expected_outcomes=intervention_record.expected_outcomes,
            status=intervention_record.status,
            progress_percentage=0.0,
            created_at=intervention_record.created_at,
        )

    except Exception as e:
        logger.error(f"Error creating intervention: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to create intervention"
        ) from e


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════


def _determine_health_trajectory(encodings: dict[str, Any]) -> str:
    """Determine overall health trajectory."""
    # Count improving vs declining trends
    improving = 0
    declining = 0

    # For CLI, EVS, CFS, PDA: lower is better
    for key in ["cli", "evs", "cfs", "pda"]:
        if encodings[key].slope < -5:
            improving += 1
        elif encodings[key].slope > 5:
            declining += 1

    # For TSC, RRC: higher is better
    for key in ["tsc", "rrc"]:
        if encodings[key].slope > 5:
            improving += 1
        elif encodings[key].slope < -5:
            declining += 1

    if improving > declining:
        return "improving"
    if declining > improving:
        return "declining"
    return "stable"


def _determine_risk_horizon(risk_score: float, encodings: dict[str, Any]) -> str:
    """Determine primary risk horizon."""
    # Check for immediate risks (CLI, EVS critically high)
    if (
        encodings["cli"].value > 80
        or encodings["evs"].value > 80
        or encodings["cfs"].value > 85
    ):
        return RiskHorizon.IMMEDIATE

    # Check for emerging risks (moderate elevation)
    if (
        encodings["cli"].value > 65
        or encodings["evs"].value > 65
        or encodings["cfs"].value > 65
        or encodings["tsc"].value < 40
    ):
        return RiskHorizon.EMERGING

    # Otherwise, structural risks
    return RiskHorizon.STRUCTURAL


async def _gather_data_sources(
    db: AsyncSession,
    organization_id: str,
    team_id: Optional[str],
    start_date: date,
    end_date: date,
    include_culture: bool,
    include_wellness: bool,
    include_behavioral: bool,
    include_communication: bool,
) -> dict[str, Any]:
    """
    Gather data from existing sources for psychology analysis

    In production, this would query:
    - culture_metrics table
    - wellness_metrics table
    - behavioral analytics
    - communication patterns
    - team dynamics

    For now, returns mock data structure.
    """
    # TODO: Implement actual data gathering from existing tables
    # This is a placeholder that shows the expected structure

    return {
        "culture_metrics": {
            "psychological_safety_score": 65,
            "transparency_score": 60,
            "collaboration_effectiveness": 70,
            "trust_indicators": {"honesty": 65, "information_sharing": 60},
            "conflict_level": "medium",
        },
        "wellness_metrics": {
            "average_stress_level": 55,
            "average_exhaustion": 45,
            "chronic_workload_score": 60,
            "recovery_deficit": 40,
            "wellness_deterioration_rate": 30,
        },
        "behavioral_metrics": {
            "handoff_efficiency": 65,
            "bottleneck_score": 50,
            "dependency_complexity": 55,
            "cross_team_score": 60,
        },
        "communication_metrics": {
            "daily_message_volume": 150,
            "message_complexity": 55,
            "sentiment_variance": 35,
            "response_delay_score": 45,
            "emotional_volatility": 40,
        },
        "team_metrics": {
            "adaptation_score": 55,
            "resource_availability": 60,
        },
        "baseline_cli": 55.0,
        "baseline_tsc": 60.0,
        "baseline_evs": 45.0,
        "baseline_cfs": 50.0,
        "baseline_pda": 55.0,
        "baseline_rrc": 55.0,
        "data_quality": 75.0,
        "confidence": 70.0,
        "sample_size": 85,
    }
