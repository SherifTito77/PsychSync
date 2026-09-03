"""
Clinical ML Prediction API Endpoints

Provides endpoints for machine learning-based clinical predictions:
- Depression risk prediction
- Anxiety risk prediction
- Crisis risk prediction
- Treatment response prediction
- Relapse risk prediction
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.db.models.user import User
from app.services.clinical.risk_prediction_service import RiskPredictionService

router = APIRouter(prefix="/clinical/ml-predictions", tags=["clinical-ml"])


# =============================================================================
# Request/Response Models
# =============================================================================


class RiskPredictionResponse(BaseModel):
    """Response model for risk predictions"""

    user_id: str
    prediction_type: str
    risk_level: str
    confidence: float
    predicted_value: Optional[float] = None
    factors: Dict[str, Any] = {}
    recommendations: list[str] = []
    timestamp: str

    class Config:
        from_attributes = True


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions"""

    user_ids: list[str]
    prediction_type: str  # depression_risk, anxiety_risk, crisis_risk, etc.


class BatchPredictionResponse(BaseModel):
    """Response for batch predictions"""

    predictions: list[RiskPredictionResponse]
    summary: Dict[str, Any]


# =============================================================================
# Depression Risk Prediction Endpoints
# =============================================================================


@router.post("/depression-risk/{user_id}", response_model=RiskPredictionResponse)
async def predict_depression_risk(
    user_id: str,
    prediction_days: int = Query(30, ge=7, le=90, description="Days to predict ahead"),
    min_assessments: int = Query(
        3, ge=2, le=10, description="Minimum assessments required"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict depression risk based on BDI-II trajectory

    Analyzes:
    - Historical BDI-II scores
    - Rate of change (improving/worsening)
    - Score volatility
    - Current severity level

    Risk Levels:
    - critical: Immediate intervention needed
    - high: Clinical assessment within 1 week
    - moderate: Regular monitoring recommended
    - low: Continue current plan

    Requires at least 3 BDI-II assessments.
    """
    try:
        # Verify authorization (users can only access their own data, clinicians can access any)
        if (
            current_user.role not in ["clinician", "admin"]
            and current_user.id != user_id
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this user's data"
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate prediction
        result = await prediction_service.predict_depression_risk(
            user_id=user_id,
            prediction_days=prediction_days,
            min_assessments=min_assessments,
        )

        logger.info(
            f"Depression risk prediction generated for user {user_id}: "
            f"risk_level={result.risk_level}, confidence={result.confidence}"
        )

        return RiskPredictionResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Error in depression risk prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/depression-risk/{user_id}", response_model=RiskPredictionResponse)
async def get_depression_risk(
    user_id: str,
    prediction_days: int = Query(30, ge=7, le=90),
    min_assessments: int = Query(3, ge=2, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GET method for depression risk prediction (same as POST)"""
    return await predict_depression_risk(
        user_id=user_id,
        prediction_days=prediction_days,
        min_assessments=min_assessments,
        current_user=current_user,
        db=db,
    )


# =============================================================================
# Anxiety Risk Prediction Endpoints
# =============================================================================


@router.post("/anxiety-risk/{user_id}", response_model=RiskPredictionResponse)
async def predict_anxiety_risk(
    user_id: str,
    prediction_days: int = Query(30, ge=7, le=90, description="Days to predict ahead"),
    min_assessments: int = Query(
        3, ge=2, le=10, description="Minimum assessments required"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict anxiety risk based on BAI trajectory

    Analyzes:
    - Historical BAI scores
    - Rate of change
    - Score volatility
    - Panic symptom patterns

    Risk Levels:
    - critical: Immediate intervention needed
    - high: Clinical assessment within 1 week
    - moderate: Regular monitoring recommended
    - low: Continue current plan

    Requires at least 3 BAI assessments.
    """
    try:
        # Verify authorization
        if (
            current_user.role not in ["clinician", "admin"]
            and current_user.id != user_id
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this user's data"
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate prediction
        result = await prediction_service.predict_anxiety_risk(
            user_id=user_id,
            prediction_days=prediction_days,
            min_assessments=min_assessments,
        )

        logger.info(
            f"Anxiety risk prediction generated for user {user_id}: "
            f"risk_level={result.risk_level}, confidence={result.confidence}"
        )

        return RiskPredictionResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Error in anxiety risk prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anxiety-risk/{user_id}", response_model=RiskPredictionResponse)
async def get_anxiety_risk(
    user_id: str,
    prediction_days: int = Query(30, ge=7, le=90),
    min_assessments: int = Query(3, ge=2, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GET method for anxiety risk prediction"""
    return await predict_anxiety_risk(
        user_id=user_id,
        prediction_days=prediction_days,
        min_assessments=min_assessments,
        current_user=current_user,
        db=db,
    )


# =============================================================================
# Crisis Risk Prediction Endpoints
# =============================================================================


@router.post("/crisis-risk/{user_id}", response_model=RiskPredictionResponse)
async def predict_crisis_risk(
    user_id: str,
    lookback_days: int = Query(90, ge=30, le=180, description="Days to look back"),
    min_assessments: int = Query(
        2, ge=1, le=5, description="Minimum assessments required"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict crisis risk (suicidal ideation, self-harm, severe deterioration)

    CRITICAL: This endpoint analyzes multiple crisis indicators:
    - Recent crisis alerts
    - Rapid score increases
    - Suicidal ideation flags
    - High severity patterns

    Risk Levels:
    - critical: Immediate action required - contact crisis team
    - high: Urgent assessment needed - implement safety plan
    - moderate: Schedule assessment within 48 hours
    - low: Continue current monitoring

    Requires at least 2 assessments within lookback period.
    """
    try:
        # Verify authorization (crisis risk should be accessible to clinicians)
        if (
            current_user.role not in ["clinician", "admin"]
            and current_user.id != user_id
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this user's data"
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate prediction
        result = await prediction_service.predict_crisis_risk(
            user_id=user_id,
            lookback_days=lookback_days,
            min_assessments=min_assessments,
        )

        # Log critical/high risks
        if result.risk_level in ["critical", "high"]:
            logger.warning(
                f"⚠️ CRISIS RISK DETECTED for user {user_id}: "
                f"risk_level={result.risk_level}, factors={result.factors}"
            )

        return RiskPredictionResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Error in crisis risk prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Treatment Response Prediction Endpoints
# =============================================================================


@router.post("/treatment-response/{user_id}", response_model=RiskPredictionResponse)
async def predict_treatment_response(
    user_id: str,
    assessment_type: str = Query("BDI2", description="Assessment type to analyze"),
    treatment_start_days: int = Query(
        60, ge=30, le=180, description="Days since treatment start"
    ),
    min_assessments: int = Query(
        4, ge=3, le=10, description="Minimum assessments required"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict treatment response based on score trajectory

    Classifies response as:
    - full_response: Significant improvement (>50% reduction)
    - partial_response: Moderate improvement (25-50% reduction)
    - non_response: Little to no improvement (<25% reduction)
    - deterioration: Worsening symptoms

    Analyzes:
    - Score reduction percentage
    - Trend direction and strength
    - Rate of improvement

    Requires at least 4 assessments over treatment period.
    """
    try:
        # Verify authorization
        if (
            current_user.role not in ["clinician", "admin"]
            and current_user.id != user_id
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this user's data"
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate prediction
        result = await prediction_service.predict_treatment_response(
            user_id=user_id,
            assessment_type=assessment_type,
            treatment_start_days=treatment_start_days,
            min_assessments=min_assessments,
        )

        logger.info(
            f"Treatment response prediction for user {user_id}: "
            f"risk_level={result.risk_level}, predicted_value={result.predicted_value}"
        )

        return RiskPredictionResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Error in treatment response prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Relapse Risk Prediction Endpoints
# =============================================================================


@router.post("/relapse-risk/{user_id}", response_model=RiskPredictionResponse)
async def predict_relapse_risk(
    user_id: str,
    assessment_type: str = Query("BDI2", description="Assessment type to analyze"),
    remission_threshold: int = Query(
        12, ge=5, le=20, description="Score threshold for remission"
    ),
    lookback_days: int = Query(90, ge=30, le=180, description="Days to look back"),
    min_assessments: int = Query(
        4, ge=3, le=10, description="Minimum assessments required"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict relapse risk for users in remission

    Analyzes:
    - Time in remission
    - Recent score trajectory
    - Score volatility
    - Assessment compliance

    Risk Levels:
    - high: Significant risk of relapse - proactive intervention needed
    - moderate: Moderate risk - increased monitoring recommended
    - low: Low risk - continue current plan
    - not_in_remission: User not currently in remission

    Requires at least 4 assessments.
    """
    try:
        # Verify authorization
        if (
            current_user.role not in ["clinician", "admin"]
            and current_user.id != user_id
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this user's data"
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate prediction
        result = await prediction_service.predict_relapse_risk(
            user_id=user_id,
            assessment_type=assessment_type,
            remission_threshold=remission_threshold,
            lookback_days=lookback_days,
            min_assessments=min_assessments,
        )

        logger.info(
            f"Relapse risk prediction for user {user_id}: "
            f"risk_level={result.risk_level}, confidence={result.confidence}"
        )

        return RiskPredictionResponse(**result.to_dict())

    except Exception as e:
        logger.error(f"Error in relapse risk prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Comprehensive Risk Assessment
# =============================================================================


@router.get("/comprehensive-risk/{user_id}")
async def get_comprehensive_risk_assessment(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive risk assessment across all prediction types

    Returns predictions for:
    - Depression risk
    - Anxiety risk
    - Crisis risk
    - Treatment response (if applicable)
    - Relapse risk (if in remission)

    Provides holistic view of user's clinical risk profile.
    """
    try:
        # Verify authorization
        if (
            current_user.role not in ["clinician", "admin"]
            and current_user.id != user_id
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this user's data"
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate all predictions
        predictions = {}

        # Depression risk
        depression_result = await prediction_service.predict_depression_risk(
            user_id=user_id, prediction_days=30, min_assessments=3
        )
        predictions["depression_risk"] = depression_result.to_dict()

        # Anxiety risk
        anxiety_result = await prediction_service.predict_anxiety_risk(
            user_id=user_id, prediction_days=30, min_assessments=3
        )
        predictions["anxiety_risk"] = anxiety_result.to_dict()

        # Crisis risk (most critical)
        crisis_result = await prediction_service.predict_crisis_risk(
            user_id=user_id, lookback_days=90, min_assessments=2
        )
        predictions["crisis_risk"] = crisis_result.to_dict()

        # Treatment response
        treatment_result = await prediction_service.predict_treatment_response(
            user_id=user_id,
            assessment_type="BDI2",
            treatment_start_days=60,
            min_assessments=4,
        )
        predictions["treatment_response"] = treatment_result.to_dict()

        # Relapse risk
        relapse_result = await prediction_service.predict_relapse_risk(
            user_id=user_id,
            assessment_type="BDI2",
            remission_threshold=12,
            lookback_days=90,
            min_assessments=4,
        )
        predictions["relapse_risk"] = relapse_result.to_dict()

        # Calculate overall risk summary
        summary = _calculate_overall_risk_summary(predictions)

        logger.info(f"Comprehensive risk assessment generated for user {user_id}")

        return {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": predictions,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error in comprehensive risk assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_overall_risk_summary(predictions: Dict) -> Dict[str, Any]:
    """Calculate overall risk summary from all predictions"""

    # Count high-risk predictions
    critical_count = sum(
        1
        for p in predictions.values()
        if p.get("risk_level") in ["critical", "high"]
        and p.get("risk_level") != "insufficient_data"
    )

    moderate_count = sum(
        1 for p in predictions.values() if p.get("risk_level") == "moderate"
    )

    # Determine overall risk level
    if critical_count >= 2:
        overall_risk = "critical"
        priority = "immediate"
    elif critical_count == 1:
        overall_risk = "high"
        priority = "urgent"
    elif moderate_count >= 2:
        overall_risk = "moderate"
        priority = "monitoring"
    else:
        overall_risk = "low"
        priority = "routine"

    # Extract key recommendations
    all_recommendations = []
    for pred_type, pred_data in predictions.items():
        if pred_data.get("recommendations"):
            all_recommendations.extend(pred_data["recommendations"])

    return {
        "overall_risk_level": overall_risk,
        "priority_level": priority,
        "critical_risk_count": critical_count,
        "moderate_risk_count": moderate_count,
        "total_recommendations": len(all_recommendations),
        "key_recommendations": all_recommendations[:5],  # Top 5
    }


# =============================================================================
# Batch Prediction Endpoints (for clinicians/admins)
# =============================================================================


@router.post("/batch/depression-risk", response_model=BatchPredictionResponse)
async def batch_predict_depression_risk(
    request: BatchPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch depression risk prediction for multiple users

    Clinicians and admins only.
    Useful for population health monitoring and identifying at-risk users.
    """
    try:
        # Verify authorization (clinicians/admins only)
        if current_user.role not in ["clinician", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Batch predictions require clinician or admin role",
            )

        # Initialize service
        prediction_service = RiskPredictionService(db)

        # Generate predictions for all users
        predictions = []
        for user_id in request.user_ids:
            try:
                result = await prediction_service.predict_depression_risk(
                    user_id=user_id, prediction_days=30, min_assessments=3
                )
                predictions.append(RiskPredictionResponse(**result.to_dict()))
            except Exception as e:
                logger.error(f"Error predicting for user {user_id}: {e}")
                # Continue with other users

        # Calculate summary statistics
        risk_counts = {}
        for pred in predictions:
            risk_counts[pred.risk_level] = risk_counts.get(pred.risk_level, 0) + 1

        summary = {
            "total_users": len(request.user_ids),
            "successful_predictions": len(predictions),
            "risk_distribution": risk_counts,
        }

        logger.info(
            f"Batch depression risk prediction completed: {len(predictions)} predictions"
        )

        return BatchPredictionResponse(predictions=predictions, summary=summary)

    except Exception as e:
        logger.error(f"Error in batch depression risk prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Model Information Endpoint
# =============================================================================


@router.get("/model-info")
async def get_model_info():
    """
    Get information about the ML models used for predictions

    Returns details about:
    - Model types used
    - Feature engineering
    - Training methodology
    - Limitations and considerations
    """
    return {
        "models": {
            "depression_risk": {
                "type": "Linear Regression + Risk Classification",
                "features": [
                    "Historical BDI-II scores",
                    "Rate of change (slope)",
                    "Score volatility",
                    "Current severity level",
                    "Recent score changes",
                ],
                "accuracy": "Validated on clinical datasets",
                "limitations": [
                    "Requires minimum 3 assessments",
                    "Accuracy improves with more data points",
                    "Predicts trajectory, not diagnosis",
                ],
            },
            "anxiety_risk": {
                "type": "Linear Regression + Risk Classification",
                "features": [
                    "Historical BAI scores",
                    "Rate of change",
                    "Score volatility",
                    "Panic symptom patterns",
                    "Current severity",
                ],
                "accuracy": "Validated on clinical datasets",
                "limitations": [
                    "Requires minimum 3 assessments",
                    "Anxiety can be more volatile than depression",
                    "External stressors may not be captured",
                ],
            },
            "crisis_risk": {
                "type": "Rule-based Risk Classification",
                "features": [
                    "Recent crisis alerts",
                    "High severity patterns",
                    "Rapid score increases",
                    "Suicidal ideation flags",
                    "Max recent scores",
                ],
                "accuracy": "High sensitivity for crisis detection",
                "limitations": [
                    "Cannot predict sudden onset crises",
                    "Requires regular assessments",
                    "Clinical judgment essential",
                ],
            },
            "treatment_response": {
                "type": "Trend Analysis + Classification",
                "features": [
                    "Score reduction percentage",
                    "Trend direction and strength",
                    "Rate of improvement",
                    "Time since treatment start",
                ],
                "accuracy": "Validated for common treatments",
                "limitations": [
                    "Individual variation significant",
                    "Treatment changes not captured",
                    "External factors not considered",
                ],
            },
            "relapse_risk": {
                "type": "Multi-factor Risk Assessment",
                "features": [
                    "Recent score trajectory",
                    "Score volatility",
                    "Assessment compliance",
                    "Proximity to remission threshold",
                    "Time in remission",
                ],
                "accuracy": "Best for users with regular assessments",
                "limitations": [
                    "Only for users in remission",
                    "Requires consistent monitoring",
                    "Life events may impact accuracy",
                ],
            },
        },
        "general_limitations": [
            "Predictions are probabilistic, not deterministic",
            "Should supplement, not replace, clinical judgment",
            "Requires adequate historical data",
            "Models trained on aggregated clinical data",
            "Individual variation may not be captured",
            "Regular retraining recommended for optimal performance",
        ],
        "best_practices": [
            "Use predictions as one factor in clinical decision-making",
            "Combine with clinical interviews and observations",
            "Monitor prediction accuracy over time",
            "Update models regularly with new data",
            "Consider individual patient history and context",
        ],
        "version": "1.0.0",
        "last_updated": "2026-01-16",
    }
