"""
Advanced Clinical Assessment API Endpoints

Provides REST endpoints for:
- LSAS (Social Anxiety)
- EAT-26 (Eating Disorders)
- Y-BOCS (OCD)
- Advanced Analytics (trends, population metrics)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from app.api.v1.dependencies.auth import get_current_active_user
from app.db.session import get_async_db
from app.db.models.user import User
from app.services.clinical.scoring_algorithms import LSASScorer, EAT26Scorer, YBOCSScorer
from app.services.clinical.advanced_analytics_service import AdvancedAnalyticsService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clinical", tags=["clinical-assessments"])


# =====================================================================
# Pydantic Schemas
# =====================================================================

class LSASRequest(BaseModel):
    """Request schema for LSAS assessment"""
    responses: Dict[str, Dict[str, int]] = Field(
        ...,
        description="Dict mapping item_1 through item_24 to {'fear': int, 'avoidance': int}"
    )


class EAT26Request(BaseModel):
    """Request schema for EAT-26 assessment"""
    responses: Dict[int, int] = Field(
        ...,
        description="Dict mapping item numbers 1-26 to response values (0-5)"
    )
    behavioral: Optional[Dict[str, any]] = Field(
        None,
        description="Behavioral questions: weight_loss_6months, binge_eating, vomiting, laxatives, exercise"
    )


class YBOCSRequest(BaseModel):
    """Request schema for Y-BOCS assessment"""
    responses: Dict[int, int] = Field(
        ...,
        description="Dict mapping item numbers 1-10 to response values (0-4)"
    )


class AssessmentResponse(BaseModel):
    """Standardized assessment response"""
    assessment_type: str
    total_score: float
    severity_level: str
    risk_level: str
    subscale_scores: Dict[str, float]
    interpretation: str
    recommendations: List[str]
    crisis_alert: bool
    risk_flags: List[str]
    completed_at: datetime


class TrendAnalysisResponse(BaseModel):
    """Trend analysis response"""
    trend_direction: str
    slope: float
    r_squared: float
    confidence: str
    interpretation: str
    change_30d: Optional[float]
    change_90d: Optional[float]


# =====================================================================
# LSAS (Social Anxiety) Endpoints
# =====================================================================

@router.post("/LSAS/submit", response_model=AssessmentResponse)
async def submit_lsas_assessment(
    request: LSASRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit LSAS (Liebowitz Social Anxiety Scale) assessment

    Scoring:
    - 24 items with dual-rating (fear + avoidance)
    - Each item: 0-3 scale (None → Severe)
    - Range: 0-144 total

    Clinical cutoffs:
    - < 30: Minimal social anxiety
    - 30-49: Mild social anxiety
    - 50-65: Moderate social anxiety
    - 66-80: Marked social anxiety
    - > 80: Severe social anxiety
    """
    try:
        # Score assessment
        result = LSASScorer.score(request.responses)

        # Store in database
        from app.db.models.clinical import ClinicalAssessmentExtended

        assessment = ClinicalAssessmentExtended(
            user_id=current_user.id,
            assessment_type="LSAS",
            responses=request.responses,
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=datetime.utcnow()
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        # Trigger crisis alert if needed
        if result.crisis_alert:
            await _trigger_crisis_alert(
                db=db,
                user_id=current_user.id,
                assessment_id=assessment.id,
                assessment_type="LSAS",
                severity=result.risk_level,
                risk_flags=result.risk_flags
            )

        return AssessmentResponse(
            assessment_type="LSAS",
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=assessment.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LSAS submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process assessment")


@router.get("/LSAS/history")
async def get_lsas_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user's LSAS assessment history"""

    from app.db.models.clinical import ClinicalAssessmentExtended

    query = select(ClinicalAssessmentExtended).where(
        and_(
            ClinicalAssessmentExtended.user_id == current_user.id,
            ClinicalAssessmentExtended.assessment_type == "LSAS",
            ClinicalAssessmentExtended.deleted_at.is_(None)
        )
    ).order_by(
        ClinicalAssessmentExtended.completed_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    assessments = result.scalars().all()

    return {
        "assessments": [
            {
                "id": str(a.id),
                "total_score": float(a.total_score),
                "severity_level": a.severity_level,
                "completed_at": a.completed_at.isoformat()
            }
            for a in assessments
        ]
    }


# =====================================================================
# EAT-26 (Eating Disorders) Endpoints
# =====================================================================

@router.post("/EAT26/submit", response_model=AssessmentResponse)
async def submit_eat26_assessment(
    request: EAT26Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit EAT-26 (Eating Attitudes Test) assessment

    Scoring:
    - 26 items: 0-5 scale (Never → Always)
    - Range: 0-78
    - Clinical cutoff: ≥20 indicates possible eating disorder

    CRITICAL: Includes behavioral risk assessment for:
    - Recent weight loss
    - Binge eating frequency
    - Self-induced vomiting
    - Laxative use
    - Exercise frequency
    """
    try:
        # Score assessment
        result = EAT26Scorer.score(
            request.responses,
            behavioral=request.behavioral
        )

        # Store in database
        from app.db.models.clinical import ClinicalAssessmentExtended

        assessment = ClinicalAssessmentExtended(
            user_id=current_user.id,
            assessment_type="EAT26",
            responses=request.responses,
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            response_metadata={
                "behavioral": request.behavioral
            } if request.behavioral else None,
            completed_at=datetime.utcnow()
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        # Trigger crisis alert for high-risk eating disorder behaviors
        if result.crisis_alert:
            await _trigger_crisis_alert(
                db=db,
                user_id=current_user.id,
                assessment_id=assessment.id,
                assessment_type="EAT26",
                severity=result.risk_level,
                risk_flags=result.risk_flags
            )

        return AssessmentResponse(
            assessment_type="EAT26",
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=assessment.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"EAT-26 submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process assessment")


# =====================================================================
# Y-BOCS (OCD) Endpoints
# =====================================================================

@router.post("/YBOCS/submit", response_model=AssessmentResponse)
async def submit_ybocs_assessment(
    request: YBOCSRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit Y-BOCS (Yale-Brown Obsessive Compulsive Scale) assessment

    Scoring:
    - 10 items: 0-4 scale (None → Extreme)
    - Range: 0-40
    - Subscales: Obsessions (items 1-5), Compulsions (items 6-10)

    Clinical cutoffs:
    - 0-7: Subclinical
    - 8-15: Mild OCD
    - 16-23: Moderate OCD
    - 24-31: Severe OCD
    - 32-40: Extreme OCD
    """
    try:
        # Score assessment
        result = YBOCSScorer.score(request.responses)

        # Store in database
        from app.db.models.clinical import ClinicalAssessmentExtended

        assessment = ClinicalAssessmentExtended(
            user_id=current_user.id,
            assessment_type="YBOCS",
            responses=request.responses,
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=datetime.utcnow()
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        # Trigger crisis alert for extreme OCD
        if result.crisis_alert:
            await _trigger_crisis_alert(
                db=db,
                user_id=current_user.id,
                assessment_id=assessment.id,
                assessment_type="YBOCS",
                severity=result.risk_level,
                risk_flags=result.risk_flags
            )

        return AssessmentResponse(
            assessment_type="YBOCS",
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=assessment.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Y-BOCS submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process assessment")


# =====================================================================
# Advanced Analytics Endpoints
# =====================================================================

@router.get("/analytics/user/trends")
async def get_user_trends(
    assessment_type: str = Query(..., description="Assessment type (PHQ9, GAD7, LSAS, EAT26, YBOCS)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get longitudinal trend analysis for user's assessments

    Returns:
    - Trend direction (improving, stable, worsening)
    - Linear regression metrics (slope, R²)
    - 30-day and 90-day change
    - Interpretation and confidence level
    """

    analytics = AdvancedAnalyticsService(db)

    try:
        trend = await analytics.calculate_user_trends(
            user_id=str(current_user.id),
            assessment_type=assessment_type,
            min_data_points=3
        )

        if not trend:
            return {
                "message": f"Insufficient data for trend analysis. Need at least 3 {assessment_type} assessments.",
                "trend": None
            }

        return TrendAnalysisResponse(
            trend_direction=trend.trend_direction,
            slope=trend.slope,
            r_squared=trend.r_squared,
            confidence=trend.confidence,
            interpretation=trend.interpretation,
            change_30d=trend.change_30d,
            change_90d=trend.change_90d
        )

    except Exception as e:
        logger.error(f"Trend analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate trends")


@router.get("/analytics/population-metrics")
async def get_population_metrics(
    assessment_type: str = Query(..., description="Assessment type"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    group_by: str = Query("week", description="Group by: all, week, month"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get population health metrics (clinicians/admins only)

    Requires: Clinician or Admin role

    Returns:
    - Total assessments
    - Unique users
    - Mean/median scores
    - Severity distribution
    - Crisis rate
    - High-risk rate
    """

    # Check authorization
    if current_user.role not in ['clinician', 'admin']:
        raise HTTPException(status_code=403, detail="Only clinicians and admins can access population metrics")

    analytics = AdvancedAnalyticsService(db)

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        metrics = await analytics.get_population_health_metrics(
            assessment_type=assessment_type,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        return {
            "assessment_type": assessment_type,
            "period_days": period_days,
            "metrics": [
                {
                    "period": m.date_range[0].isoformat(),
                    "total_assessments": m.total_assessments,
                    "unique_users": m.unique_users,
                    "mean_score": m.mean_score,
                    "median_score": m.median_score,
                    "std_dev": m.std_dev,
                    "severity_distribution": m.score_distribution,
                    "crisis_rate": m.crisis_rate,
                    "high_risk_rate": m.high_risk_rate
                }
                for m in metrics
            ]
        }

    except Exception as e:
        logger.error(f"Population metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate population metrics")


@router.get("/analytics/high-risk-users")
async def get_high_risk_users(
    assessment_type: str = Query(..., description="Assessment type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum users to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get list of high-risk or deteriorating users (clinicians/admins only)

    Returns users with:
    - Worsening trend
    - High mean scores
    - Recent high-risk episodes
    """

    # Check authorization
    if current_user.role not in ['clinician', 'admin']:
        raise HTTPException(status_code=403, detail="Only clinicians and admins can access high-risk user lists")

    analytics = AdvancedAnalyticsService(db)

    try:
        high_risk_users = await analytics.identify_high_risk_users(
            assessment_type=assessment_type,
            limit=limit
        )

        return {
            "assessment_type": assessment_type,
            "total_users": len(high_risk_users),
            "users": high_risk_users
        }

    except Exception as e:
        logger.error(f"High-risk user identification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to identify high-risk users")


@router.post("/analytics/refresh-views")
async def refresh_analytics_views(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh materialized views (clinicians/admins only)

    Updates population_health_stats materialized view with latest data
    """

    # Check authorization
    if current_user.role not in ['clinician', 'admin']:
        raise HTTPException(status_code=403, detail="Only clinicians and admins can refresh analytics")

    analytics = AdvancedAnalyticsService(db)

    try:
        await analytics.refresh_materialized_view()

        return {
            "success": True,
            "message": "Materialized views refreshed successfully"
        }

    except Exception as e:
        logger.error(f"View refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh views")


# =====================================================================
# Helper Functions
# =====================================================================

async def _trigger_crisis_alert(
    db: AsyncSession,
    user_id: str,
    assessment_id: str,
    assessment_type: str,
    severity: str,
    risk_flags: List[str]
):
    """Trigger crisis alert notification to clinicians"""

    try:
        # Import CrisisAlert model (assuming it exists)
        from app.db.models.clinical import CrisisAlert

        alert = CrisisAlert(
            user_id=user_id,
            assessment_id=assessment_id,
            alert_type=f"{assessment_type}_crisis_detection",
            severity=severity,
            risk_factors=risk_flags,
            trigger_content=f"{assessment_type} assessment triggered crisis alert",
            status='active'
        )

        db.add(alert)
        await db.commit()

        # TODO: Send notification to clinicians via notification service
        # await notification_service.notify_clinicians_of_alert(...)

        logger.warning(f"Crisis alert triggered for user {user_id}, assessment {assessment_type}, severity {severity}")

    except Exception as e:
        logger.error(f"Failed to trigger crisis alert: {str(e)}")
        # Don't raise - still want to save the assessment


# =====================================================================
# BDI-II (Beck Depression Inventory-II) Endpoints
# =====================================================================

@router.post("/BDI2/submit", response_model=AssessmentResponse)
async def submit_bdi2_assessment(
    request: Dict[str, int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit BDI-II (Beck Depression Inventory-II) assessment

    Scoring:
    - 21 items: 0-3 scale (Not present → Severe)
    - Range: 0-63

    Clinical cutoffs:
    - 0-13: Minimal depression
    - 14-19: Mild depression
    - 20-28: Moderate depression
    - 29-63: Severe depression

    Reliability: α = 0.91
    Test-retest: r = 0.93

    CRITICAL: Item 9 assesses suicidal thoughts - requires immediate attention
    """
    try:
        from app.services.clinical.scoring_algorithms import BDI2Scorer

        # Score assessment
        result = BDI2Scorer.score(request)

        # Store in database
        from app.db.models.clinical import ClinicalAssessmentExtended

        assessment = ClinicalAssessmentExtended(
            user_id=current_user.id,
            assessment_type="BDI2",
            responses=request,
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=datetime.utcnow()
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        # Trigger crisis alert for suicidal ideation or extreme scores
        if result.crisis_alert:
            await _trigger_crisis_alert(
                db=db,
                user_id=current_user.id,
                assessment_id=str(assessment.id),
                assessment_type="BDI2",
                severity=result.risk_level,
                risk_flags=result.risk_flags
            )

        return AssessmentResponse(
            assessment_type="BDI2",
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=assessment.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"BDI-II submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process assessment")


@router.get("/BDI2/history")
async def get_bdi2_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user's BDI-II assessment history"""

    from app.db.models.clinical import ClinicalAssessmentExtended

    query = select(ClinicalAssessmentExtended).where(
        and_(
            ClinicalAssessmentExtended.user_id == current_user.id,
            ClinicalAssessmentExtended.assessment_type == "BDI2",
            ClinicalAssessmentExtended.deleted_at.is_(None)
        )
    ).order_by(
        ClinicalAssessmentExtended.completed_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    assessments = result.scalars().all()

    return {
        "assessments": [
            {
                "id": str(a.id),
                "total_score": float(a.total_score),
                "severity_level": a.severity_level,
                "completed_at": a.completed_at.isoformat()
            }
            for a in assessments
        ]
    }


# =====================================================================
# BAI (Beck Anxiety Inventory) Endpoints
# =====================================================================

@router.post("/BAI/submit", response_model=AssessmentResponse)
async def submit_bai_assessment(
    request: Dict[str, int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit BAI (Beck Anxiety Inventory) assessment

    Scoring:
    - 21 items: 0-3 scale (Not at all → Severely)
    - Range: 0-63

    Clinical cutoffs:
    - 0-7: Minimal anxiety
    - 8-15: Mild anxiety
    - 16-25: Moderate anxiety
    - 26-63: Severe anxiety

    Reliability: α = 0.92
    Test-retest: r = 0.75

    Measures SEVERITY of symptoms (not frequency like GAD-7)
    """
    try:
        from app.services.clinical.scoring_algorithms import BAIScorer

        # Score assessment
        result = BAIScorer.score(request)

        # Store in database
        from app.db.models.clinical import ClinicalAssessmentExtended

        assessment = ClinicalAssessmentExtended(
            user_id=current_user.id,
            assessment_type="BAI",
            responses=request,
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=datetime.utcnow()
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        # Trigger crisis alert for severe panic or extreme anxiety
        if result.crisis_alert:
            await _trigger_crisis_alert(
                db=db,
                user_id=current_user.id,
                assessment_id=str(assessment.id),
                assessment_type="BAI",
                severity=result.risk_level,
                risk_flags=result.risk_flags
            )

        return AssessmentResponse(
            assessment_type="BAI",
            total_score=result.total_score,
            severity_level=result.severity_level,
            risk_level=result.risk_level,
            subscale_scores=result.subscale_scores,
            interpretation=result.interpretation,
            recommendations=result.recommendations,
            crisis_alert=result.crisis_alert,
            risk_flags=result.risk_flags,
            completed_at=assessment.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"BAI submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process assessment")


@router.get("/BAI/history")
async def get_bai_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user's BAI assessment history"""

    from app.db.models.clinical import ClinicalAssessmentExtended

    query = select(ClinicalAssessmentExtended).where(
        and_(
            ClinicalAssessmentExtended.user_id == current_user.id,
            ClinicalAssessmentExtended.assessment_type == "BAI",
            ClinicalAssessmentExtended.deleted_at.is_(None)
        )
    ).order_by(
        ClinicalAssessmentExtended.completed_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    assessments = result.scalars().all()

    return {
        "assessments": [
            {
                "id": str(a.id),
                "total_score": float(a.total_score),
                "severity_level": a.severity_level,
                "completed_at": a.completed_at.isoformat()
            }
            for a in assessments
        ]
    }


# =====================================================================
# GAD-7 Extended Endpoints (Enhanced Analytics)
# =====================================================================

@router.get("/GAD7/extended-analytics/{user_id}")
async def get_gad7_extended_analytics(
    user_id: str,
    days_back: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get extended GAD-7 analytics with trend analysis and prediction

    Enhanced features:
    - Longitudinal trend analysis
    - Symptom cluster identification
    - Treatment response tracking
    - Relapse risk prediction

    Requires: User, Clinician, or Admin role
    """

    # Check authorization
    if (str(current_user.id) != user_id and
        current_user.role not in ['clinician', 'admin']):
        raise HTTPException(status_code=403, detail="Not authorized to view these analytics")

    try:
        from app.services.clinical.advanced_analytics_service import AdvancedAnalyticsService
        from app.db.models.clinical_extended import ClinicalAssessmentExtended

        analytics = AdvancedAnalyticsService(db)

        # Get trend data
        trend = await analytics.calculate_user_trends(
            user_id=user_id,
            assessment_type="GAD7",
            min_data_points=2
        )

        if not trend:
            return {
                "message": "Insufficient data for extended analytics. Need at least 2 GAD-7 assessments.",
                "trend": None,
                "recommendation": "Continue regular GAD-7 assessments (every 2-4 weeks recommended) to build data for trend analysis."
            }

        # Get detailed history
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        query = select(
            ClinicalAssessmentExtended.total_score,
            ClinicalAssessmentExtended.completed_at,
            ClinicalAssessmentExtended.subscale_scores
        ).where(
            and_(
                ClinicalAssessmentExtended.user_id == user_id,
                ClinicalAssessmentExtended.assessment_type == "GAD7",
                ClinicalAssessmentExtended.completed_at >= start_date,
                ClinicalAssessmentExtended.deleted_at.is_(None)
            )
        ).order_by(
            ClinicalAssessmentExtended.completed_at.asc()
        )

        result = await db.execute(query)
        assessments = result.all()

        # Calculate symptom patterns
        if len(assessments) >= 2:
            scores = [float(a.total_score) for a in assessments]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            volatility = max(scores) - min(scores)

            # Simple prediction (linear trend extrapolation)
            if trend.get('slope') is not None:
                next_predicted_score = scores[-1] + (trend['slope'] * 30)  # 30 days from now
            else:
                next_predicted_score = None
        else:
            avg_score = max_score = min_score = volatility = next_predicted_score = None

        return {
            "assessment_type": "GAD7",
            "period_analyzed": f"{days_back} days",
            "total_assessments": len(assessments),
            "trend": trend,
            "statistics": {
                "average_score": avg_score,
                "max_score": max_score,
                "min_score": min_score,
                "volatility": volatility
            },
            "prediction": {
                "predicted_score_30days": next_predicted_score,
                "trend_direction": trend.get('trend_direction'),
                "confidence": trend.get('confidence')
            },
            "recommendations": _generate_gad7_recommendations(trend, avg_score, volatility)
        }

    except Exception as e:
        logger.error(f"Extended GAD-7 analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate extended analytics")


def _generate_gad7_recommendations(trend: Dict, avg_score: Optional[float], volatility: Optional[float]) -> List[str]:
    """Generate personalized GAD-7 recommendations based on analytics"""
    recommendations = []

    if not trend:
        return ["Complete regular GAD-7 assessments to enable personalized recommendations."]

    trend_direction = trend.get('trend_direction', 'stable')

    if trend_direction == 'worsening':
        recommendations.extend([
            "⚠️ WARNING: Anxiety symptoms are worsening over time",
            "Consider consulting with mental health professional",
            "Increase treatment frequency or adjust treatment plan",
            "Practice anxiety management techniques daily",
            "Identify and address stressors contributing to worsening"
        ])
    elif trend_direction == 'improving':
        recommendations.extend([
            "✓ Great progress! Anxiety symptoms are improving",
            "Continue current treatment plan",
            "Maintain coping strategies and self-care practices",
            "Regular check-ins to maintain progress"
        ])
    else:
        recommendations.extend([
            "Anxiety symptoms remain stable over time",
            "Continue current treatment and monitoring",
            "Discuss with clinician if symptoms persist despite treatment"
        ])

    if avg_score is not None:
        if avg_score >= 15:
            recommendations.append("Consider discussing additional treatment options with provider")
        elif avg_score <= 5:
            recommendations.append("Excellent symptom control - maintain self-care practices")

    if volatility is not None and volatility > 10:
        recommendations.append("High symptom variability detected - consider tracking triggers and patterns")

    return recommendations
