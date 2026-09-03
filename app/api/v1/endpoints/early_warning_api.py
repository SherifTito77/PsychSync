"""
Early Warning API Endpoints

14-day horizon burnout prediction with trend analysis:
- Trend slope detection
- Volatility acceleration
- Early Warning Score (EW)
- Trigger conditions (3+ days above threshold)
- System-focused alerts (not human blame)

Author: PsychSync Engineering Team
Version: 3.1
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.burnout.early_warning_engine import (
    EarlyWarningEngine,
    EarlyWarningSignal,
    FeatureEngineeringLayer,
    FeatureVector,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
_early_warning_engine = EarlyWarningEngine()
_feature_engine = FeatureEngineeringLayer()


class EarlyWarningRequest(BaseModel):
    """Request for early warning analysis"""

    user_id: str
    pri_history: List[float] = Field(
        ..., min_items=7, description="Last 7-30 days of PRI scores"
    )
    cls_history: Optional[List[float]] = Field(None, description="Optional CLS history")
    ess_history: Optional[List[float]] = Field(None, description="Optional ESS history")
    fas_history: Optional[List[float]] = Field(None, description="Optional FAS history")


class FeatureEngineeringRequest(BaseModel):
    """Request for feature engineering"""

    user_id: str
    raw_metrics: Dict[str, float]
    historical_metrics: Dict[str, List[float]]
    baseline_stats: Dict[str, Dict[str, float]]


@router.post("/analytics/burnout/early-warning", response_model=Dict[str, Any])
async def generate_early_warning(request: EarlyWarningRequest):
    """
    Generate Early Warning Signal (14-day horizon)

    Detects 10-14 days before visible burnout by analyzing:
    1. Trend slope (sustained direction)
    2. Volatility acceleration (instability)
    3. Sustained elevation (consecutive days above threshold)

    Trigger Condition:
        EW↑ AND PRI > 55 for ≥3 consecutive days

    Alert Framing:
        "Sustained cognitive load trend detected.
         Recommend load redistribution."

    System problem, not human blame.
    """
    try:
        signal = _early_warning_engine.generate_early_warning(
            user_id=request.user_id,
            pri_history=request.pri_history,
            cls_history=request.cls_history,
            ess_history=request.ess_history,
            fas_history=request.fas_history,
        )

        return {
            "user_id": request.user_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "early_warning_score": signal.early_warning_score,
            "trend_slope": signal.trend_slope,
            "volatility_ratio": signal.volatility_ratio,
            "is_triggered": signal.is_triggered,
            "trigger_reason": signal.trigger_reason,
            "days_above_threshold": signal.days_above_threshold,
            "predicted_horizon_days": signal.predicted_horizon_days,
            "recommended_actions": signal.recommended_actions,
            "interpretation": _interpret_early_warning(signal),
        }

    except Exception as e:
        logger.error(f"Error generating early warning: {e}")
        raise HTTPException(
            status_code=500, detail=f"Early warning generation failed: {str(e)}"
        )


@router.post("/analytics/burnout/features", response_model=Dict[str, Any])
async def create_feature_vector(request: FeatureEngineeringRequest):
    """
    Create Feature Vector for ML/Bayesian Models

    Generates derived features:
    - Velocity Drop: % change vs baseline
    - Variance Spike: σ7d / σ30d
    - Load Ratio: acute7d / chronic28d
    - Recovery Failure: no rebound after low-load day
    - Escalation Density: conflicts / interactions
    - Trend slopes: 7d, 14d, 30d
    """
    try:
        feature_vector = _feature_engine.create_feature_vector(
            user_id=request.user_id,
            raw_metrics=request.raw_metrics,
            historical_metrics=request.historical_metrics,
            baseline_stats=request.baseline_stats,
        )

        return {
            "user_id": request.user_id,
            "feature_vector": {
                "velocity_features": {
                    "velocity_drop_pct": feature_vector.velocity_drop_pct,
                    "velocity_z_score": feature_vector.velocity_z_score,
                },
                "variance_features": {
                    "variance_spike": feature_vector.variance_spike,
                    "variance_z_score": feature_vector.variance_z_score,
                },
                "load_features": {
                    "load_ratio": feature_vector.load_ratio,
                    "load_z_score": feature_vector.load_z_score,
                },
                "recovery_features": {
                    "recovery_failure": feature_vector.recovery_failure,
                    "recovery_score": feature_vector.recovery_score,
                },
                "escalation_features": {
                    "escalation_density": feature_vector.escalation_density,
                    "escalation_z_score": feature_vector.escalation_z_score,
                },
                "trend_features": {
                    "trend_7d": feature_vector.trend_7d,
                    "trend_14d": feature_vector.trend_14d,
                    "trend_30d": feature_vector.trend_30d,
                },
                "composite_scores": {
                    "cls": feature_vector.cls_score,
                    "ess": feature_vector.ess_score,
                    "fas": feature_vector.fas_score,
                    "pri": feature_vector.pri_score,
                },
            },
            "created_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating feature vector: {e}")
        raise HTTPException(
            status_code=500, detail=f"Feature engineering failed: {str(e)}"
        )


@router.post("/analytics/burnout/early-warning/test")
async def test_early_warning():
    """
    Test endpoint for early warning system

    Returns sample early warning analysis with realistic data.
    No authentication required for testing.
    """
    # Simulate 30 days of PRI scores showing escalating risk
    pri_history = [
        45,
        46,
        47,
        48,  # Days 1-4: Normal
        50,
        52,
        53,
        55,  # Days 5-8: Rising
        56,
        57,
        58,
        58,  # Days 9-12: Sustained elevation
        59,
        60,
        61,
        62,  # Days 13-16: Continuing to rise
        63,
        64,
        65,
        66,  # Days 17-20: Concerning trend
        67,
        68,
        69,
        70,  # Days 21-24: High risk
        71,
        72,
        73,
        74,  # Days 25-28: Very high
        75,
        76,  # Days 29-30: Critical
    ]

    cls_history = [score * 0.95 for score in pri_history]  # CLS tracks with PRI
    ess_history = [score * 1.05 for score in pri_history]  # ESS slightly higher
    fas_history = [score * 0.8 for score in pri_history]  # FAS lower but rising

    signal = _early_warning_engine.generate_early_warning(
        user_id="test-user-escalating-risk",
        pri_history=pri_history,
        cls_history=cls_history,
        ess_history=ess_history,
        fas_history=fas_history,
    )

    return {
        "test_scenario": "escalating_risk_over_30_days",
        "early_warning_signal": {
            "early_warning_score": signal.early_warning_score,
            "trend_slope": signal.trend_slope,
            "volatility_ratio": signal.volatility_ratio,
            "is_triggered": signal.is_triggered,
            "trigger_reason": signal.trigger_reason,
            "days_above_threshold": signal.days_above_threshold,
            "predicted_horizon_days": signal.predicted_horizon_days,
            "recommended_actions": signal.recommended_actions,
        },
        "interpretation": _interpret_early_warning(signal),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _interpret_early_warning(signal: EarlyWarningSignal) -> str:
    """Generate human-readable interpretation"""
    if not signal.is_triggered:
        return "✅ All indicators stable. No immediate action required."

    if signal.predicted_horizon_days <= 14:
        urgency = "🔴 CRITICAL: Burnout risk within 14 days"
    elif signal.predicted_horizon_days <= 30:
        urgency = "🟠 URGENT: Burnout risk within 30 days"
    else:
        urgency = "🟡 ELEVATED: Burnout risk detected"

    if signal.trend_slope > 0.5:
        trend_desc = "rapidly escalating"
    elif signal.trend_slope > 0.2:
        trend_desc = "steadily increasing"
    else:
        trend_desc = "elevated but stable"

    return (
        f"{urgency}. Risk level is {trend_desc}. "
        f"System-focused intervention recommended."
    )
