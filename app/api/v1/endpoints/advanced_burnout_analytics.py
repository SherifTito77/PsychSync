"""
Advanced Burnout Analytics API Endpoints

Enterprise-safe behavioral burnout prediction using:
- Baseline Normalization (personal Z-scores)
- Cognitive Load Score (mental strain)
- Emotional Stress Score (behavioral NLP)
- Fatigue Accumulation Score (sports science)
- Psychological Risk Index (main product score)
- Team Friction Index (system toxicity)
- Self-Report Calibration (optional)

Features:
- No medical data
- No body measurements
- No psychological labeling
- Only risk signals from behavior
- Probabilistic, not diagnostic

Author: PsychSync Engineering Team
Version: 3.0
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.burnout.advanced_burnout_analytics import (
    AdvancedBurnoutAnalyzer,
    BaselineManager,
    CognitiveLoadInput,
    EmotionalStressInput,
    FatigueInput,
    PsychologicalRiskResult,
    TeamFrictionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Schemas
# =============================================================================


class BaselineNormalizationRequest(BaseModel):
    """Request for baseline Z-score calculation"""

    user_id: str = Field(..., description="User ID")
    metric_name: str = Field(
        ..., description="Metric name (e.g., task_velocity, meeting_hours)"
    )
    value_today: float = Field(..., description="Today's metric value")
    historical_values: Optional[List[float]] = Field(
        None, description="Last 30 days of values (if not using stored baseline)"
    )


class ZScoreResponse(BaseModel):
    """Response for Z-score calculation"""

    user_id: str
    metric_name: str
    z_score: float
    interpretation: str  # "above_baseline", "below_baseline", "at_baseline"
    deviation_level: str  # "minimal", "moderate", "significant"


class CognitiveLoadRequest(BaseModel):
    """Request for Cognitive Load Score calculation"""

    user_id: str
    task_velocity_z: float = Field(..., description="Z-score of task completion rate")
    context_switch_z: float = Field(..., description="Z-score of context switches")
    meeting_density_z: float = Field(..., description="Z-score of meeting hours")


class EmotionalStressRequest(BaseModel):
    """Request for Emotional Stress Score calculation"""

    user_id: str
    sentiment_shift_z: float = Field(
        ..., description="Z-score of negative sentiment shift"
    )
    escalation_z: float = Field(
        ..., description="Z-score of message escalation/sharpness"
    )
    rework_z: float = Field(..., description="Z-score of error rework frequency")


class FatigueAccumulationRequest(BaseModel):
    """Request for Fatigue Accumulation Score calculation"""

    user_id: str
    acute_load_7d: float = Field(..., description="Weighted load (last 7 days)")
    chronic_load_28d: float = Field(..., description="Weighted load (last 28 days)")


class PsychologicalRiskRequest(BaseModel):
    """Request for Psychological Risk Index calculation"""

    user_id: str
    cls_score: float = Field(
        ..., ge=0, le=100, description="Cognitive Load Score (0-100)"
    )
    ess_score: float = Field(
        ..., ge=0, le=100, description="Emotional Stress Score (0-100)"
    )
    fas_score: float = Field(
        ..., ge=0, le=100, description="Fatigue Accumulation Score (0-100)"
    )


class TeamFrictionRequest(BaseModel):
    """Request for Team Friction Index calculation"""

    team_id: str
    conflict_signals: int = Field(
        ..., ge=0, description="Number of conflict indicators"
    )
    escalations: int = Field(..., ge=0, description="Number of escalated messages")
    coordination_failures: int = Field(
        ..., ge=0, description="Number of failed handoffs"
    )
    team_interactions: int = Field(..., ge=0, description="Total team interactions")
    historical_tfi: Optional[List[float]] = Field(
        None, description="Historical TFI values for EMA smoothing"
    )


class SelfReportCalibrationRequest(BaseModel):
    """Request for self-report calibration"""

    user_id: str
    model_score: float = Field(
        ..., ge=0, le=100, description="Score from behavioral model"
    )
    self_report_score: float = Field(
        ..., ge=0, le=100, description="User's self-reported score"
    )
    model_weight: float = Field(0.8, ge=0, le=1, description="Weight for model score")
    self_report_weight: float = Field(
        0.2, ge=0, le=1, description="Weight for self-report"
    )


class FullBurnoutAnalysisRequest(BaseModel):
    """Complete burnout analysis with all metrics"""

    user_id: str

    # Cognitive Load inputs
    task_velocity_z: float
    context_switch_z: float
    meeting_density_z: float

    # Emotional Stress inputs
    sentiment_shift_z: float
    escalation_z: float
    rework_z: float

    # Fatigue inputs
    acute_load_7d: float
    chronic_load_28d: float

    # Optional self-report
    self_report_score: Optional[float] = Field(None, ge=0, le=100)

    # Optional team context
    team_id: Optional[str] = None
    team_conflicts: Optional[int] = None
    team_escalations: Optional[int] = None
    team_failures: Optional[int] = None
    team_interactions: Optional[int] = None


class FullBurnoutAnalysisResponse(BaseModel):
    """Complete burnout analysis response"""

    user_id: str
    analysis_date: str

    # Component scores
    cognitive_load_score: float
    emotional_stress_score: float
    fatigue_accumulation_score: float

    # Main score
    psychological_risk_index: float
    risk_level: str
    confidence: str

    # Team context (if available)
    team_friction_index: Optional[float] = None
    team_friction_trend: Optional[str] = None
    team_friction_severity: Optional[str] = None

    # Calibration (if self-report provided)
    calibrated_pri: Optional[float] = None

    # Recommendations
    recommendations: List[str]


# =============================================================================
# Global Analyzer Instance
# =============================================================================

_analyzer = AdvancedBurnoutAnalyzer()
_baseline_manager = BaselineManager()


def get_analyzer() -> AdvancedBurnoutAnalyzer:
    """Get the global analyzer instance"""
    return _analyzer


def get_baseline_manager() -> BaselineManager:
    """Get the global baseline manager"""
    return _baseline_manager


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/analytics/burnout/baseline/z-score", response_model=ZScoreResponse)
async def calculate_baseline_z_score(request: BaselineNormalizationRequest):
    """
    Calculate Z-score relative to personal 30-day baseline

    Everything is measured relative to the person's own normal, not others.

    Formula: Z = (x_today - μ_30d) / σ_30d

    This removes bias between fast/slow workers.

    Returns:
        Z-score with interpretation and deviation level
    """
    try:
        if request.historical_values and len(request.historical_values) >= 5:
            # Use provided historical values
            mean_30d = sum(request.historical_values) / len(request.historical_values)
            variance = sum(
                (x - mean_30d) ** 2 for x in request.historical_values
            ) / len(request.historical_values)
            std_30d = variance**0.5
        else:
            # Would use stored baseline (not implemented in this example)
            raise HTTPException(
                status_code=400,
                detail="Insufficient baseline data. Need at least 5 historical values.",
            )

        # Calculate Z-score
        z_score = _analyzer.calculate_z_score(request.value_today, mean_30d, std_30d)

        # Interpret Z-score
        if abs(z_score) < 1:
            interpretation = "at_baseline"
            deviation_level = "minimal"
        elif abs(z_score) < 2:
            interpretation = "above_baseline" if z_score > 0 else "below_baseline"
            deviation_level = "moderate"
        else:
            interpretation = "above_baseline" if z_score > 0 else "below_baseline"
            deviation_level = "significant"

        return ZScoreResponse(
            user_id=request.user_id,
            metric_name=request.metric_name,
            z_score=round(z_score, 2),
            interpretation=interpretation,
            deviation_level=deviation_level,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating Z-score: {e}")
        raise HTTPException(
            status_code=500, detail=f"Z-score calculation failed: {str(e)}"
        )


@router.post("/analytics/burnout/cognitive-load", response_model=Dict[str, Any])
async def calculate_cognitive_load(request: CognitiveLoadRequest):
    """
    Calculate Cognitive Load Score (CLS)

    Measures mental strain from:
    - Task velocity drop (negative Z = slower = bad)
    - Context switching (positive Z = more switching = bad)
    - Meeting density (positive Z = more meetings = bad)

    Formula: CLS = w1*(-Z_velocity) + w2*Z_context + w3*Z_meetings
    Normalized: CLS_norm = clip(50 + 15*CLS, 0, 100)

    Interpretation:
    - 0-30: Relaxed
    - 30-60: Healthy load
    - 60-80: Overloaded
    - 80+: Cognitive fatigue
    """
    try:
        input_data = CognitiveLoadInput(
            task_velocity_z=request.task_velocity_z,
            context_switch_z=request.context_switch_z,
            meeting_density_z=request.meeting_density_z,
        )

        cls_score = _analyzer.calculate_cognitive_load_score(input_data)

        # Determine interpretation
        if cls_score < 30:
            interpretation = "relaxed"
        elif cls_score < 60:
            interpretation = "healthy_load"
        elif cls_score < 80:
            interpretation = "overloaded"
        else:
            interpretation = "cognitive_fatigue"

        return {
            "user_id": request.user_id,
            "cognitive_load_score": round(cls_score, 1),
            "interpretation": interpretation,
            "component_weights": AdvancedBurnoutAnalyzer.CLS_WEIGHTS,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating CLS: {e}")
        raise HTTPException(status_code=500, detail=f"CLS calculation failed: {str(e)}")


@router.post("/analytics/burnout/emotional-stress", response_model=Dict[str, Any])
async def calculate_emotional_stress(request: EmotionalStressRequest):
    """
    Calculate Emotional Stress Score (ESS)

    Derived from behavioral NLP, not feelings:
    - Negative sentiment shift (positive Z = more negative = bad)
    - Message escalation/sharpness (positive Z = sharper = bad)
    - Error rework frequency (positive Z = more rework = bad)

    Formula: ESS = w1*Z_sentiment + w2*Z_escalation + w3*Z_rework
    Normalized: ESS_norm = clip(50 + 20*ESS, 0, 100)

    Note: Sudden spikes matter more than absolute values.
    """
    try:
        input_data = EmotionalStressInput(
            sentiment_shift_z=request.sentiment_shift_z,
            escalation_z=request.escalation_z,
            rework_z=request.rework_z,
        )

        ess_score = _analyzer.calculate_emotional_stress_score(input_data)

        # Determine interpretation
        if ess_score < 30:
            interpretation = "calm"
        elif ess_score < 50:
            interpretation = "normal_stress"
        elif ess_score < 70:
            interpretation = "elevated_stress"
        else:
            interpretation = "critical_stress"

        return {
            "user_id": request.user_id,
            "emotional_stress_score": round(ess_score, 1),
            "interpretation": interpretation,
            "component_weights": AdvancedBurnoutAnalyzer.ESS_WEIGHTS,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating ESS: {e}")
        raise HTTPException(status_code=500, detail=f"ESS calculation failed: {str(e)}")


@router.post("/analytics/burnout/fatigue-accumulation", response_model=Dict[str, Any])
async def calculate_fatigue_accumulation(request: FatigueAccumulationRequest):
    """
    Calculate Fatigue Accumulation Score (FAS)

    Directly borrowed from sports science (acute/chronic workload ratio).

    Formula: FAS = Acute Load (7d) / Chronic Load (28d)

    Where load = weighted sum of work hours, task difficulty, deadline pressure

    Interpretation:
    - < 0.8: Underloaded
    - 0.8-1.3: Optimal
    - 1.3: Fatigue risk
    - 1.6: Burnout zone
    """
    try:
        input_data = FatigueInput(
            acute_load_7d=request.acute_load_7d,
            chronic_load_28d=request.chronic_load_28d,
        )

        fas_score = _analyzer.calculate_fatigue_accumulation_score(input_data)

        # Calculate AC ratio for interpretation
        ac_ratio = (
            request.acute_load_7d / request.chronic_load_28d
            if request.chronic_load_28d > 0
            else 0
        )

        # Determine interpretation
        if ac_ratio < 0.8:
            interpretation = "underloaded"
        elif ac_ratio <= 1.3:
            interpretation = "optimal"
        elif ac_ratio <= 1.6:
            interpretation = "fatigue_risk"
        else:
            interpretation = "burnout_zone"

        return {
            "user_id": request.user_id,
            "fatigue_accumulation_score": round(fas_score, 1),
            "acute_chronic_ratio": round(ac_ratio, 2),
            "interpretation": interpretation,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating FAS: {e}")
        raise HTTPException(status_code=500, detail=f"FAS calculation failed: {str(e)}")


@router.post(
    "/analytics/burnout/psychological-risk", response_model=PsychologicalRiskResult
)
async def calculate_psychological_risk(request: PsychologicalRiskRequest):
    """
    Calculate Psychological Risk Index (PRI)

    This is the main product score combining:
    - Cognitive Load Score (35%)
    - Emotional Stress Score (35%)
    - Fatigue Accumulation Score (30%)

    Formula: PRI = 0.35*CLS + 0.35*ESS + 0.30*FAS

    Output: 0-100 risk probability
    - 0-40: Safe
    - 40-60: Watch
    - 60-75: Intervention recommended
    - 75+: High risk
    """
    try:
        result = _analyzer.calculate_psychological_risk_index(
            cls_score=request.cls_score,
            ess_score=request.ess_score,
            fas_score=request.fas_score,
        )

        return result

    except Exception as e:
        logger.error(f"Error calculating PRI: {e}")
        raise HTTPException(status_code=500, detail=f"PRI calculation failed: {str(e)}")


@router.post("/analytics/burnout/team-friction", response_model=TeamFrictionResult)
async def calculate_team_friction(request: TeamFrictionRequest):
    """
    Calculate Team Friction Index (TFI)

    Measures system toxicity, not individuals.

    Formula: TFI = (Conflicts + Escalations + Failures) / Interactions
    Smoothed: TFI_smoothed = EMA_14d(TFI)

    Note: Rising TFI = culture issue, not "bad people".
    """
    try:
        result = _analyzer.calculate_team_friction_index(
            conflict_signals=request.conflict_signals,
            escalations=request.escalations,
            coordination_failures=request.coordination_failures,
            team_interactions=request.team_interactions,
            historical_tfi=request.historical_tfi,
        )

        return result

    except Exception as e:
        logger.error(f"Error calculating TFI: {e}")
        raise HTTPException(status_code=500, detail=f"TFI calculation failed: {str(e)}")


@router.post("/analytics/burnout/calibrate-self-report", response_model=Dict[str, Any])
async def calibrate_with_self_report(request: SelfReportCalibrationRequest):
    """
    Optional calibration with self-reports

    Like RPE (Rate of Perceived Exertion) in football:
    Adjusted Score = 0.8 * Model + 0.2 * Self Report

    This improves accuracy without depending on honesty.
    """
    try:
        calibrated_score = _analyzer.calibrate_with_self_report(
            model_score=request.model_score,
            self_report_score=request.self_report_score,
            model_weight=request.model_weight,
            self_report_weight=request.self_report_weight,
        )

        return {
            "user_id": request.user_id,
            "original_model_score": round(request.model_score, 1),
            "self_report_score": round(request.self_report_score, 1),
            "calibrated_score": round(calibrated_score, 1),
            "adjustment": round(calibrated_score - request.model_score, 1),
            "weights": {
                "model": request.model_weight,
                "self_report": request.self_report_weight,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calibrating with self-report: {e}")
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")


@router.post(
    "/analytics/burnout/full-analysis", response_model=FullBurnoutAnalysisResponse
)
async def full_burnout_analysis(request: FullBurnoutAnalysisRequest):
    """
    Complete burnout analysis with all advanced metrics

    This is the main endpoint for the advanced burnout prediction system.
    It combines:
    - Cognitive Load Score (CLS)
    - Emotional Stress Score (ESS)
    - Fatigue Accumulation Score (FAS)
    - Psychological Risk Index (PRI) - main score
    - Team Friction Index (TFI) - optional
    - Self-report calibration - optional

    All metrics use baseline-normalized Z-scores to remove bias between
    fast/slow workers. Scores are probabilistic, not diagnostic.
    """
    try:
        # Calculate component scores
        cls_input = CognitiveLoadInput(
            task_velocity_z=request.task_velocity_z,
            context_switch_z=request.context_switch_z,
            meeting_density_z=request.meeting_density_z,
        )
        cls_score = _analyzer.calculate_cognitive_load_score(cls_input)

        ess_input = EmotionalStressInput(
            sentiment_shift_z=request.sentiment_shift_z,
            escalation_z=request.escalation_z,
            rework_z=request.rework_z,
        )
        ess_score = _analyzer.calculate_emotional_stress_score(ess_input)

        fas_input = FatigueInput(
            acute_load_7d=request.acute_load_7d,
            chronic_load_28d=request.chronic_load_28d,
        )
        fas_score = _analyzer.calculate_fatigue_accumulation_score(fas_input)

        # Calculate main PRI score
        pri_result = _analyzer.calculate_psychological_risk_index(
            cls_score=cls_score, ess_score=ess_score, fas_score=fas_score
        )

        # Team friction (if provided)
        team_fri = None
        team_trend = None
        team_severity = None

        if all(
            [
                request.team_id,
                request.team_conflicts is not None,
                request.team_escalations is not None,
                request.team_failures is not None,
                request.team_interactions is not None,
            ]
        ):
            tfi_result = _analyzer.calculate_team_friction_index(
                conflict_signals=request.team_conflicts,
                escalations=request.team_escalations,
                coordination_failures=request.team_failures,
                team_interactions=request.team_interactions,
            )
            team_fri = tfi_result.tfi_smoothed
            team_trend = tfi_result.trend
            team_severity = tfi_result.severity

        # Self-report calibration (if provided)
        calibrated_pri = None
        if request.self_report_score is not None:
            calibrated_pri = _analyzer.calibrate_with_self_report(
                model_score=pri_result.pri_score,
                self_report_score=request.self_report_score,
            )

        # Generate recommendations
        recommendations = _generate_recommendations(
            cls_score=cls_score,
            ess_score=ess_score,
            fas_score=fas_score,
            pri_score=pri_result.pri_score,
            team_fri=team_fri,
        )

        return FullBurnoutAnalysisResponse(
            user_id=request.user_id,
            analysis_date=datetime.utcnow().isoformat(),
            cognitive_load_score=round(cls_score, 1),
            emotional_stress_score=round(ess_score, 1),
            fatigue_accumulation_score=round(fas_score, 1),
            psychological_risk_index=round(pri_result.pri_score, 1),
            risk_level=pri_result.risk_level,
            confidence=pri_result.confidence,
            team_friction_index=round(team_fri, 1) if team_fri is not None else None,
            team_friction_trend=team_trend,
            team_friction_severity=team_severity,
            calibrated_pri=(
                round(calibrated_pri, 1) if calibrated_pri is not None else None
            ),
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Error in full burnout analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def _generate_recommendations(
    cls_score: float,
    ess_score: float,
    fas_score: float,
    pri_score: float,
    team_fri: Optional[float] = None,
) -> List[str]:
    """Generate personalized recommendations based on scores"""

    recommendations = []

    # Cognitive Load recommendations
    if cls_score > 70:
        recommendations.append(
            "🔴 CRITICAL: Immediate cognitive overload detected. Consider urgent workload redistribution."
        )
    elif cls_score > 50:
        recommendations.append(
            "🟡 WARNING: High cognitive load. Reduce meeting density and context switching."
        )

    # Emotional Stress recommendations
    if ess_score > 70:
        recommendations.append(
            "🔴 CRITICAL: Severe emotional stress detected. Consider immediate HR intervention."
        )
    elif ess_score > 50:
        recommendations.append(
            "🟡 WARNING: Elevated stress levels. Monitor communication patterns for escalation."
        )

    # Fatigue recommendations
    if fas_score > 60:
        recommendations.append(
            "🔴 CRITICAL: Fatigue accumulation in burnout zone. Mandatory rest required."
        )
    elif fas_score > 40:
        recommendations.append(
            "🟡 WARNING: Fatigue risk approaching. Encourage time off and recovery."
        )

    # Team recommendations
    if team_fri and team_fri > 50:
        recommendations.append(
            f"🔴 TEAM ALERT: High team friction detected (TFI: {team_fri:.1f}). Address cultural issues."
        )

    # Overall PRI recommendations
    if pri_score > 75:
        recommendations.append(
            "🚨 HIGH RISK: Immediate intervention recommended. Comprehensive burnout prevention plan required."
        )
    elif pri_score > 60:
        recommendations.append(
            "⚠️ INTERVENTION RECOMMENDED: Proactive measures needed to prevent escalation."
        )
    elif pri_score < 40:
        recommendations.append(
            "✅ HEALTHY: All indicators within normal range. Continue monitoring."
        )

    return recommendations


# =============================================================================
# Public Test Endpoint (No Authentication)
# =============================================================================


@router.post("/analytics/burnout/test")
async def test_advanced_analytics():
    """
    Test endpoint for advanced burnout analytics

    Returns sample analysis with realistic data.
    No authentication required for testing.
    """

    # Sample inputs for high-risk scenario
    cls_input = CognitiveLoadInput(
        task_velocity_z=-1.8,  # Much slower than usual
        context_switch_z=2.0,  # Excessive context switching
        meeting_density_z=1.5,  # Too many meetings
    )

    ess_input = EmotionalStressInput(
        sentiment_shift_z=2.2,  # Much more negative
        escalation_z=1.8,  # More escalated messages
        rework_z=1.5,  # More errors/rework
    )

    fas_input = FatigueInput(
        acute_load_7d=85,  # High acute load
        chronic_load_28d=55,  # Moderate chronic load (ratio = 1.55)
    )

    # Calculate scores
    cls_score = _analyzer.calculate_cognitive_load_score(cls_input)
    ess_score = _analyzer.calculate_emotional_stress_score(ess_input)
    fas_score = _analyzer.calculate_fatigue_accumulation_score(fas_input)
    pri_result = _analyzer.calculate_psychological_risk_index(
        cls_score, ess_score, fas_score
    )

    return {
        "test_scenario": "high_risk_burnout",
        "scores": {
            "cognitive_load_score": round(cls_score, 1),
            "emotional_stress_score": round(ess_score, 1),
            "fatigue_accumulation_score": round(fas_score, 1),
            "psychological_risk_index": round(pri_result.pri_score, 1),
        },
        "interpretation": {
            "cls": "cognitive_fatigue" if cls_score > 80 else "overloaded",
            "ess": "critical_stress" if ess_score > 70 else "elevated_stress",
            "fas": "burnout_zone" if fas_score > 60 else "fatigue_risk",
            "pri": pri_result.risk_level,
        },
        "recommendations": _generate_recommendations(
            cls_score, ess_score, fas_score, pri_result.pri_score
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }
