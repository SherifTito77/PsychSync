"""
Burnout Prediction API Endpoints

Provides REST API endpoints for:
- 14-day burnout probability prediction
- Bayesian and ML model predictions
- Prediction history
- Model comparison

Author: PsychSync Engineering Team
Version: 2.0
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import get_current_active_user
from app.db.models.user import User
from app.services.burnout.exact_scoring import (
    BurnoutRiskCalculator,
    WorkloadMetrics,
    RecoveryMetrics,
    SentimentMetrics,
    WithdrawalMetrics,
    PatternMetrics,
    BiometricMetrics,
)

logger = logging.getLogger(__name__)

# Optional Bayesian predictor (requires PyMC)
try:
    from app.services.burnout.bayesian_burnout_predictor import (
        BayesianBurnoutPredictor,
        BurnoutFeatures,
        PredictionResult,
        TrajectoryResult,
    )

    BAYESIAN_AVAILABLE = True
except ImportError:
    logger.info(
        "Bayesian predictor not available - PyMC not installed (Bayesian analysis is optional)"
    )
    BAYESIAN_AVAILABLE = False
    BayesianBurnoutPredictor = None
    BurnoutFeatures = None
    PredictionResult = None
    TrajectoryResult = None

router = APIRouter()


# =============================================================================
# Pydantic Schemas for Request/Response
# =============================================================================


class BurnoutFeaturesRequest(BaseModel):
    """Request schema for burnout prediction features"""

    # Workload features
    weekly_hours: float = Field(
        ..., ge=0, le=168, description="Average weekly work hours"
    )
    continuous_days: int = Field(
        ..., ge=0, le=365, description="Consecutive days worked without break"
    )
    after_hours_percentage: float = Field(
        ..., ge=0, le=1, description="After-hours work percentage"
    )
    late_night_work_days: int = Field(
        0, ge=0, le=30, description="Days with work after 9 PM"
    )
    early_morning_work_days: int = Field(
        0, ge=0, le=30, description="Days with work before 7 AM"
    )
    weekend_work_days: int = Field(0, ge=0, le=30, description="Days worked on weekend")

    # Recovery features
    pto_days_used: int = Field(0, ge=0, description="PTO days used in current period")
    pto_days_available: int = Field(15, ge=0, description="Total PTO days available")
    avg_daily_break_hours: float = Field(
        0.5, ge=0, le=8, description="Average daily break hours"
    )
    sleep_hours_avg: float = Field(
        7.0, ge=0, le=24, description="Average daily sleep hours"
    )

    # Sentiment features
    negative_sentiment_avg: float = Field(
        0.0, ge=-1, le=0, description="Average negative sentiment"
    )
    sentiment_volatility: float = Field(
        0.0, ge=0, description="Sentiment volatility (std)"
    )
    conflict_indicators: int = Field(
        0, ge=0, description="Number of high-conflict communications"
    )

    # Communication features
    communication_volume_decline: float = Field(
        0.0, ge=-1, le=1, description="Communication volume decline"
    )
    meeting_participation_decline: float = Field(
        0.0, ge=-1, le=1, description="Meeting participation decline"
    )
    social_interaction_score: float = Field(
        7.0, ge=1, le=10, description="Social interaction score (1-10)"
    )

    # Work pattern features
    response_time_avg_minutes: float = Field(
        60, ge=0, description="Average response time in minutes"
    )

    # Biometric features (optional)
    resting_hr: Optional[float] = Field(
        None, ge=40, le=200, description="Resting heart rate (bpm)"
    )
    hrv: Optional[float] = Field(
        None, ge=0, le=200, description="Heart rate variability (ms)"
    )
    blood_pressure_systolic: Optional[int] = Field(
        None, ge=70, le=250, description="Systolic blood pressure"
    )
    steps_per_day: Optional[float] = Field(
        None, ge=0, description="Average daily steps"
    )

    # Trend data (for 14-day prediction)
    brs_trend_slope: float = Field(0.0, description="Weekly BRS trend slope")
    recent_acceleration: float = Field(0.0, description="Recent acceleration in BRS")


class BurnoutPredictionResponse(BaseModel):
    """Response schema for burnout prediction"""

    user_id: str
    prediction_date: str
    model_type: str

    # BRS predictions
    brs_mean: float
    brs_median: float
    brs_std: float
    brs_50ci: List[float]
    brs_89ci: List[float]
    brs_95ci: List[float]

    # Probability predictions
    probability_mean: float
    probability_50ci: List[float]
    probability_89ci: List[float]
    probability_95ci: List[float]

    # Risk classification
    risk_level: str
    confidence: str


class TrajectoryResponse(BaseModel):
    """Response schema for 14-day trajectory prediction"""

    user_id: str
    prediction_date: str
    days: List[int]

    # BRS trajectory
    brs_mean: List[float]
    brs_lower_89ci: List[float]
    brs_upper_89ci: List[float]
    brs_lower_95ci: List[float]
    brs_upper_95ci: List[float]

    # Probability trajectory
    probability_mean: List[float]
    probability_lower_89ci: List[float]
    probability_upper_89ci: List[float]

    # Warning zones and interventions
    warning_zones: List[Dict[str, Any]]
    intervention_points: List[Dict[str, Any]]
    risk_trajectory: str


class PredictionHistoryResponse(BaseModel):
    """Response schema for prediction history"""

    user_id: str
    predictions: List[Dict[str, Any]]
    total_count: int


# =============================================================================
# Global Model Instance
# =============================================================================

# Global predictor instance (will be loaded on startup)
_bayesian_predictor: Optional[BayesianBurnoutPredictor] = None


def get_bayesian_predictor() -> Optional[BayesianBurnoutPredictor]:
    """Get or create the global Bayesian predictor instance"""
    if not BAYESIAN_AVAILABLE:
        return None

    global _bayesian_predictor
    if _bayesian_predictor is None:
        # Create predictor (should be loaded from trained model)
        _bayesian_predictor = BayesianBurnoutPredictor(
            n_features=12, n_organizations=100
        )
        logger.info("Created new Bayesian predictor instance")
    return _bayesian_predictor


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/predictions/burnout/14-day", response_model=Dict[str, Any])
async def predict_burnout_14_day(
    user_id: str,
    organization_id: str,
    features: BurnoutFeaturesRequest,
    model_type: str = Query(
        "bayesian", description="Model type: bayesian, ml_ensemble, or both"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate 14-day burnout prediction with uncertainty quantification

    Args:
        user_id: User to predict for
        organization_id: Organization ID
        features: Burnout feature values
        model_type: Which model(s) to use (bayesian, ml_ensemble, or both)

    Returns:
        Dictionary with prediction results, trajectory, and intervention points
    """
    try:
        logger.info(f"Generating burnout prediction for user {user_id}")

        # Check if Bayesian predictor is available
        if model_type in ["bayesian", "both"] and not BAYESIAN_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Bayesian predictor not available. PyMC not installed. Install with: pip install pymc>=5.10.0",
            )

        result = {
            "user_id": user_id,
            "organization_id": organization_id,
            "prediction_date": datetime.utcnow().isoformat(),
        }

        # Get predictor and generate predictions
        predictor = get_bayesian_predictor()

        if model_type in ["bayesian", "both"] and predictor:
            # Convert request to BurnoutFeatures (only if predictor is available)
            burnout_features = BurnoutFeatures(
                weekly_hours=features.weekly_hours,
                continuous_days=features.continuous_days,
                after_hours_percentage=features.after_hours_percentage,
                late_night_work_days=features.late_night_work_days,
                early_morning_work_days=features.early_morning_work_days,
                weekend_work_days=features.weekend_work_days,
                pto_days_used=features.pto_days_used,
                pto_days_available=features.pto_days_available,
                avg_daily_break_hours=features.avg_daily_break_hours,
                sleep_hours_avg=features.sleep_hours_avg,
                negative_sentiment_avg=features.negative_sentiment_avg,
                sentiment_volatility=features.sentiment_volatility,
                conflict_indicators=features.conflict_indicators,
                communication_volume_decline=features.communication_volume_decline,
                meeting_participation_decline=features.meeting_participation_decline,
                response_time_avg_minutes=features.response_time_avg_minutes,
                resting_hr=features.resting_hr,
                hrv=features.hrv,
                blood_pressure_systolic=features.blood_pressure_systolic,
                steps_per_day=features.steps_per_day,
            )

            # Bayesian prediction
            prediction = predictor.predict(
                burnout_features.to_feature_vector(),
                org_id=int(organization_id.replace("-", "").replace(" ", ""), 16) % 100,
            )
            prediction.user_id = user_id

            result["bayesian"] = prediction.to_dict()

            # 14-day trajectory
            trajectory = predictor.predict_14_day_trajectory(
                burnout_features,
                org_id=int(organization_id.replace("-", "").replace(" ", ""), 16) % 100,
            )
            trajectory.user_id = user_id
            result["trajectory"] = trajectory.to_dict()

        # Note: ML ensemble would be added here when implemented
        if model_type == "ml_ensemble":
            result["ml_ensemble"] = {
                "status": "not_implemented",
                "message": "ML ensemble model not yet implemented",
            }

        # Store prediction in database (optional, for later validation)
        # await _store_prediction(db, user_id, organization_id, features.dict(), result)

        logger.info(f"Burnout prediction generated successfully for user {user_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating burnout prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get(
    "/predictions/burnout/history/{user_id}", response_model=PredictionHistoryResponse
)
async def get_prediction_history(
    user_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of recent predictions"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get prediction history for a user

    Args:
        user_id: User to get history for
        limit: Maximum number of predictions to return

    Returns:
        List of historical predictions
    """
    try:
        # Query prediction history from database
        # (Implementation depends on having stored predictions)
        from app.db.models.burnout_predictions import BurnoutPrediction

        query = (
            select(BurnoutPrediction)
            .where(BurnoutPrediction.user_id == user_id)
            .order_by(BurnoutPrediction.prediction_date.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        predictions = result.scalars().all()

        return PredictionHistoryResponse(
            user_id=user_id,
            predictions=[
                {
                    "id": str(pred.id),
                    "prediction_date": pred.prediction_date.isoformat(),
                    "model_type": pred.model_type,
                    "brs_mean": pred.brs_mean,
                    "probability_mean": pred.probability_mean,
                    "risk_level": pred.risk_level,
                    "confidence_level": pred.confidence,
                }
                for pred in predictions
            ],
            total_count=len(predictions),
        )

    except Exception as e:
        logger.error(f"Error fetching prediction history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch history: {str(e)}"
        )


@router.post("/predictions/burnout/exact-score")
async def calculate_exact_brs(
    features: BurnoutFeaturesRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculate Burnout Risk Score using exact formulas

    This endpoint uses the mathematically validated exact scoring formulas
    without Bayesian inference or ML models.

    Returns:
        BRS calculation with detailed component breakdown

    Note: Authentication required for production. For testing, you can
    temporarily comment out the current_user dependency above.
    """
    try:
        calculator = BurnoutRiskCalculator()

        # Create metric objects
        workload = WorkloadMetrics(
            weekly_hours=features.weekly_hours,
            continuous_days=features.continuous_days,
            after_hours_pct=features.after_hours_percentage,
            late_night_work_days=features.late_night_work_days,
            early_morning_work_days=features.early_morning_work_days,
            weekend_work_days=features.weekend_work_days,
        )

        recovery = RecoveryMetrics(
            pto_days_used=features.pto_days_used,
            pto_days_available=features.pto_days_available,
            avg_daily_break_hours=features.avg_daily_break_hours,
            sleep_hours_avg=features.sleep_hours_avg,
            last_pto_days_ago=180,  # Default, could be calculated
        )

        sentiment = SentimentMetrics(
            negative_sentiment_avg=features.negative_sentiment_avg,
            sentiment_volatility=features.sentiment_volatility,
            conflict_indicators=features.conflict_indicators,
        )

        withdrawal = WithdrawalMetrics(
            communication_volume_decline=features.communication_volume_decline,
            meeting_participation_decline=features.meeting_participation_decline,
            social_interaction_score=features.social_interaction_score,
        )

        pattern = PatternMetrics(
            late_night_work_days=features.late_night_work_days,
            early_morning_work_days=features.early_morning_work_days,
            weekend_work_days=features.weekend_work_days,
            response_time_avg_minutes=features.response_time_avg_minutes,
        )

        biometric = None
        if any([features.resting_hr, features.hrv, features.steps_per_day]):
            biometric = BiometricMetrics(
                resting_hr=features.resting_hr,
                hrv=features.hrv,
                steps_per_day=features.steps_per_day,
            )

        # Calculate BRS
        result = calculator.calculate(
            workload=workload,
            recovery=recovery,
            sentiment=sentiment,
            withdrawal=withdrawal,
            pattern=pattern,
            biometric=biometric,
            brs_trend_slope=features.brs_trend_slope,
            recent_acceleration=features.recent_acceleration,
        )

        return result.to_dict()

    except Exception as e:
        logger.error(f"Error calculating BRS: {e}")
        raise HTTPException(status_code=500, detail=f"BRS calculation failed: {str(e)}")


@router.post("/predictions/burnout/exact-score/test")
async def calculate_exact_brs_test(features: BurnoutFeaturesRequest):
    """
    Calculate Burnout Risk Score using exact formulas (TEST ENDPOINT - NO AUTH)

    This is a public test endpoint for development and testing purposes.
    In production, use the authenticated endpoint: /predictions/burnout/exact-score

    Returns:
        BRS calculation with detailed component breakdown
    """
    try:
        calculator = BurnoutRiskCalculator()

        # Create metric objects
        workload = WorkloadMetrics(
            weekly_hours=features.weekly_hours,
            continuous_days=features.continuous_days,
            after_hours_pct=features.after_hours_percentage,
            late_night_work_days=features.late_night_work_days,
            early_morning_work_days=features.early_morning_work_days,
            weekend_work_days=features.weekend_work_days,
        )

        recovery = RecoveryMetrics(
            pto_days_used=features.pto_days_used,
            pto_days_available=features.pto_days_available,
            avg_daily_break_hours=features.avg_daily_break_hours,
            sleep_hours_avg=features.sleep_hours_avg,
            last_pto_days_ago=180,  # Default, could be calculated
        )

        sentiment = SentimentMetrics(
            negative_sentiment_avg=features.negative_sentiment_avg,
            sentiment_volatility=features.sentiment_volatility,
            conflict_indicators=features.conflict_indicators,
        )

        withdrawal = WithdrawalMetrics(
            communication_volume_decline=features.communication_volume_decline,
            meeting_participation_decline=features.meeting_participation_decline,
            social_interaction_score=features.social_interaction_score,
        )

        pattern = PatternMetrics(
            late_night_work_days=features.late_night_work_days,
            early_morning_work_days=features.early_morning_work_days,
            weekend_work_days=features.weekend_work_days,
            response_time_avg_minutes=features.response_time_avg_minutes,
        )

        biometric = None
        if any([features.resting_hr, features.hrv, features.steps_per_day]):
            biometric = BiometricMetrics(
                resting_hr=features.resting_hr,
                hrv=features.hrv,
                steps_per_day=features.steps_per_day,
            )

        # Calculate BRS
        result = calculator.calculate(
            workload=workload,
            recovery=recovery,
            sentiment=sentiment,
            withdrawal=withdrawal,
            pattern=pattern,
            biometric=biometric,
            brs_trend_slope=features.brs_trend_slope,
            recent_acceleration=features.recent_acceleration,
        )

        return result.to_dict()

    except Exception as e:
        logger.error(f"Error calculating BRS: {e}")
        raise HTTPException(status_code=500, detail=f"BRS calculation failed: {str(e)}")


# =============================================================================
# Internal Helper Functions
# =============================================================================


async def _store_prediction(
    db: AsyncSession,
    user_id: str,
    organization_id: str,
    features: Dict[str, Any],
    result: Dict[str, Any],
):
    """Store prediction result in database for later validation"""
    try:
        from app.db.models.burnout_predictions import BurnoutPrediction

        # Extract prediction data
        if "bayesian" in result:
            bayesian_pred = result["bayesian"]
            prediction = BurnoutPrediction(
                user_id=user_id,
                organization_id=organization_id,
                model_type="bayesian",
                brs_mean=bayesian_pred["brs_mean"],
                brs_lower_95ci=bayesian_pred["brs_95ci"][0],
                brs_upper_95ci=bayesian_pred["brs_95ci"][1],
                probability_mean=bayesian_pred["probability_mean"] / 100,
                probability_lower_95ci=bayesian_pred["probability_95ci"][0] / 100,
                probability_upper_95ci=bayesian_pred["probability_95ci"][1] / 100,
                risk_level=bayesian_pred["risk_level"],
                confidence_level=bayesian_pred["confidence"],
                trajectory_days=result.get("trajectory", {}).get("days"),
                trajectory_brs_mean=result.get("trajectory", {}).get("brs_mean"),
                trajectory_probability_mean=result.get("trajectory", {}).get(
                    "probability_mean"
                ),
                warning_zones=result.get("trajectory", {}).get("warning_zones"),
                intervention_points=result.get("trajectory", {}).get(
                    "intervention_points"
                ),
            )

            db.add(prediction)
            await db.commit()

            logger.info(f"Stored prediction {prediction.id} for user {user_id}")

    except Exception as e:
        logger.error(f"Error storing prediction: {e}")
        # Don't raise - prediction should still be returned to user
