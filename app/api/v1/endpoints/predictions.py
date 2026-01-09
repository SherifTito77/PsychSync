"""
Predictive Analytics API Endpoints

REST API endpoints for machine learning prediction capabilities including:
- Model training and management
- Team performance predictions
- User outcome predictions
- Model evaluation and comparison
- Batch prediction operations
"""

from datetime import datetime, timedelta

from app.api.v1.deps import get_current_user

from app.middleware.rate_limiter import check_rate_limit
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import asyncio
import logging

from app.core.database import get_db
from app.services.prediction_service import (
    PredictionService, ModelType, TargetType,
    ModelComparisonResult
)
from app.services.prediction_data_service import PredictionDataCollectionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response schemas

class PredictionType(str, Enum):
    """Types of predictions supported by the service."""
    TEAM_PERFORMANCE = "team_performance"
    USER_OUTCOME = "user_outcome"
    ASSESSMENT_COMPLETION = "assessment_completion"
    TEAM_DYNAMICS = "team_dynamics"
    PERFORMANCE_TREND = "performance_trend"
    RETENTION_RISK = "retention_risk"
    LEADERSHIP_POTENTIAL = "leadership_potential"
    TEAM_COHESION = "team_cohesion"

class PredictionResult(BaseModel):
    """Single prediction result with confidence."""
    prediction: Union[float, int, str]
    confidence: float
    prediction_interval: Optional[Tuple[float, float]] = None
    probabilities: Optional[Dict[str, float]] = None
    feature_contributions: Optional[Dict[str, float]] = None
    model_id: Optional[str] = None
    prediction_type: Optional[PredictionType] = None
    timestamp: Optional[datetime] = None

class TrainingRequest(BaseModel):
    """Request model for training prediction models."""
    prediction_type: PredictionType = Field(..., description="Type of prediction to train for")
    target_variable: str = Field(..., description="Target variable to predict")
    team_ids: Optional[List[int]] = Field(None, description="Specific team IDs to include")
    user_ids: Optional[List[str]] = Field(None, description="Specific user IDs to include")
    model_types: Optional[List[ModelType]] = Field(None, description="Model types to train")
    test_size: float = Field(0.2, ge=0.1, le=0.5, description="Test set proportion")
    cv_folds: int = Field(5, ge=2, le=10, description="Cross-validation folds")
    hyperparameter_tuning: bool = Field(True, description="Enable hyperparameter tuning")
    feature_selection: bool = Field(True, description="Enable feature selection")
    min_data_quality: float = Field(0.7, ge=0.0, le=1.0, description="Minimum data quality score")

class PredictionRequest(BaseModel):
    """Request model for making predictions."""
    prediction_type: PredictionType = Field(..., description="Type of prediction")
    entity_ids: List[Union[int, str]] = Field(..., description="Team IDs or user IDs")
    model_id: Optional[str] = Field(None, description="Specific model to use")
    include_confidence: bool = Field(True, description="Include confidence intervals")
    include_feature_importance: bool = Field(True, description="Include feature contributions")
    batch_size: Optional[int] = Field(50, ge=1, le=1000, description="Batch size for processing")

class ModelEvaluationRequest(BaseModel):
    """Request model for model evaluation."""
    model_id: str = Field(..., description="Model ID to evaluate")
    cv_folds: int = Field(5, ge=2, le=10, description="Cross-validation folds")

class BatchTrainingRequest(BaseModel):
    """Request model for batch training multiple models."""
    training_configs: List[TrainingRequest] = Field(..., description="List of training configurations")
    parallel_execution: bool = Field(True, description="Execute training in parallel")

# Response models

class ModelPerformance(BaseModel):
    """Model performance metrics."""
    model_name: str
    accuracy: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    training_time: Optional[float] = None
    prediction_time: Optional[float] = None

class ModelComparisonResult(BaseModel):
    """Model comparison results."""
    model_performances: Dict[str, ModelPerformance]
    best_model_name: str
    comparison_metrics: Dict[str, float]
    recommendation: str

class TrainingResponse(BaseModel):
    """Response model for training results."""
    success: bool
    model_comparison: Optional[ModelComparisonResult] = None
    best_model_id: Optional[str] = None
    training_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    training_metadata: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    """Response model for prediction results."""
    success: bool
    predictions: List[PredictionResult] = []
    prediction_time_seconds: Optional[float] = None
    model_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    success: bool
    model_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ModelsListResponse(BaseModel):
    """Response model for listing trained models."""
    success: bool
    models: List[Dict[str, Any]] = []
    total_count: int = 0
    error_message: Optional[str] = None

# Initialize services
prediction_service = PredictionService()
data_service = PredictionDataCollectionService()


@check_rate_limit(identifier="public", limit_name="public")
@router.post("/train", response_model=TrainingResponse, dependencies=[Depends(get_current_user)])
async def train_prediction_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Train a new prediction model.

    This endpoint trains ML models for the specified prediction type and target variable.
    It supports multiple model types, hyperparameter tuning, and comprehensive evaluation.
    """
    try:
        start_time = datetime.now()

        logger.info(f"Starting model training for {request.prediction_type.value} "
                   f"with target: {request.target_variable}")

        # Route to appropriate training method
        if request.prediction_type == PredictionType.TEAM_PERFORMANCE:
            result = await prediction_service.train_team_performance_model(
                db=db,
                team_ids=request.team_ids,
                target_variable=request.target_variable,
                model_types=request.model_types,
                test_size=request.test_size,
                cv_folds=request.cv_folds,
                hyperparameter_tuning=request.hyperparameter_tuning,
                feature_selection=request.feature_selection
            )
        elif request.prediction_type == PredictionType.USER_OUTCOME:
            result = await prediction_service.train_user_outcome_model(
                db=db,
                outcome_variable=request.target_variable,
                user_ids=request.user_ids,
                model_types=request.model_types
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Training not implemented for {request.prediction_type.value}"
            )

        training_time = (datetime.now() - start_time).total_seconds()

        # Get the best model ID
        best_model_id = None
        if hasattr(result, 'best_model_name') and result.model_performances:
            best_model_id = f"{result.best_model_name}_{request.prediction_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return TrainingResponse(
            success=True,
            model_comparison=result,
            best_model_id=best_model_id,
            training_time_seconds=training_time,
            training_metadata={
                "prediction_type": request.prediction_type.value,
                "target_variable": request.target_variable,
                "data_sources": getattr(result, 'data_sources', []),
                "feature_count": getattr(result, 'feature_count', 0)
            }
        )

    except Exception as e:
        logger.error(f"Error in model training: {str(e)}")
        return TrainingResponse(

@check_rate_limit(identifier="public", limit_name="public")
     success=False,
            error_message=str(e)
        )

@router.post("/predict", response_model=PredictionResponse)
async def make_predictions(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """
    Make predictions for specified entities.

    This endpoint uses trained models to make predictions for teams or users.
    Supports both single and batch predictions with confidence intervals.
    """
    try:
        start_time = datetime.now()

        logger.info(f"Making {request.prediction_type.value} predictions for "
                   f"{len(request.entity_ids)} entities")

        # Route to appropriate prediction method
        if request.prediction_type == PredictionType.TEAM_PERFORMANCE:
            # Batch prediction for team performance
            results = await prediction_service.batch_predict(
                db=db,
                prediction_type=request.prediction_type,
                entity_ids=request.entity_ids,  # These are team IDs
                model_id=request.model_id
            )

            prediction_time = (datetime.now() - start_time).total_seconds()

            # Get model metadata if model_id specified
            model_metadata = None
            if request.model_id:
                model_metadata = await prediction_service.get_model_info(request.model_id)

            return PredictionResponse(
                success=True,
                predictions=results,
                prediction_time_seconds=prediction_time,
                model_metadata=model_metadata
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Prediction not implemented for {request.prediction_type.value}"
            )

    except Exception as e:
        logger.error(f"Error in p rediction: {str(e)}")
        return PredictionResponse(
            success=False,
            error_message=str(e)
        )

@router.post("/predict/team/{team_id}", response_model=PredictionResponse)
async def predict_team_performance(
    team_id: int,
    model_id: Optional[str] = Query(None, description="Specific model to use"),
    include_confidence: bool = Query(True, description="Include confidence intervals"),
    include_feature_importance: bool = Query(True, description="Include feature contributions"),
    db: Session = Depends(get_db)
):
    """
    Predict performance for a specific team.

    This endpoint provides detailed prediction for a single team including
    confidence intervals and feature contributions.
    """
    try:
        start_time = datetime.now()

        logger.info(f"Predicting performance for team {team_id}")

        result = await prediction_service.predict_team_performance(
            db=db,
            team_id=team_id,
            model_id=model_id,
            include_confidence=include_confidence,
            include_feature_importance=include_feature_importance
        )

        prediction_time = (datetime.now() - start_time).total_seconds()

        # Get model metadata
        model_metadata = None
        if result.model_id:
            model_metadata = await prediction_service.get_model_info(result.model_id)

        return PredictionResponse(
            success=True,
            predictions=[result],
            prediction_time_seconds=prediction_time,
            model_metadata=model_metadata
        )

    except Exception as e:
        logger.error(f"Error in team prediction: {str(e)}")
        return PredictionResponse(
            success=False,
            error_message=str(e)
        )

@router.get("/models", response_model=ModelsListResponse)
async def list_models(
    prediction_type: Optional[PredictionType] = Query(None, description="Filter by prediction type"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of models to return")
):
    """
    List all trained prediction models.

    This endpoint returns information about all trained models with optional
    filtering by prediction type.
    """
    try:
        models = await prediction_service.list_trained_models(
            prediction_type=prediction_type
        )

        # Limit results
        if limit and len(models) > limit:
            models = models[:limit]

        return ModelsListResponse(
            success=True,
            models=models,
            total_count=len(models)
        )

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return ModelsListResponse(
            success=False,
            error_message=str(e),
            total_count=0
        )

@router.get("/models/{model_id}", response_model=ModelInfoResponse)
async def get_model_info(model_id: str):
    """
    Get detailed information about a specific model.

    This endpoint returns comprehensive metadata about a trained model
    including performance metrics and hyperparameters.
    """
    try:
        model_info = await prediction_service.get_model_info(model_id)

        if model_info is None:
            return ModelInfoResponse(
                success=False,
                error_message=f"Model {model_id} not found"
            )

        return ModelInfoResponse(
            success=True,
            model_info=model_info
        )

    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return ModelInfoResponse(
            success=False,
            error_message=str(e, dependencies=[Depends(get_current_user)])
        )

@router.post("/models/{model_id}/evaluate", response_model=Dict[str, Any])
async def evaluate_model(
    model_id: str,
    request: ModelEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate a trained model's performance.

    This endpoint performs comprehensive evaluation of a trained model
    using cross-validation and various performance metrics.
    """
    try:
        performance = await prediction_service.evaluate_model_performance(
            model_id=model_id,
            cv_folds=request.cv_folds
        )

        return {
            "success": True,
            "model_id": model_id,
            "performance": {
                "mse": performance.mse,
                "mae": performance.mae,
                "rmse": performance.rmse,
                "r2": performance.r2,
                "accuracy": performance.accuracy,
                "precision": performance.precision,
                "recall": performance.recall,
                "f1": performance.f1,
                "auc": performance.auc,
                "cv_scores": performance.cv_scores,
                "feature_importance": performance.feature_importance
            },
            "evaluation_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error evaluating model: {str(e)}")
        return {
            "success": False,
            "error_message": str(e, dependencies=[Depends(get_current_user)])
        }

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """
    Delete a trained model.

    This endpoint removes a trained model from the system.
    """
    try:
        success = await prediction_service.delete_model(model_id)

        if not success:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error_message": f"Model {model_id} not found"
                }
            )

        return {
            "success": True,
            "message": f"Model {model_id} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting model: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_message": str(e, dependencies=[Depends(get_current_user)])
            }
        )

@router.post("/train/batch", response_model=Dict[str, Any], dependencies=[Depends(get_current_user)])
async def batch_train_models(
    request: BatchTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Train multiple models in batch.

    This endpoint supports training multiple prediction models simultaneously
    with different configurations.
    """
    try:
        start_time = datetime.now()

        logger.info(f"Starting batch training for {len(request.training_configs)} models")

        results = []

        if request.parallel_execution:
            # Execute training tasks in parallel
            tasks = []
            for config in request.training_configs:
                task = asyncio.create_task(
                    _train_single_model(config, db)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "config_index": i,
                        "success": False,
                        "error_message": str(result)
                    })
                else:
                    results.append(result)

        else:
            # Execute training tasks sequentially
            for i, config in enumerate(request.training_configs):
                result = await _train_single_model(config, db)
                results.append(result)

        total_time = (datetime.now() - start_time).total_seconds()

        successful_trainings = [r for r in results if r.get("success", False)]
        failed_trainings = [r for r in results if not r.get("success", False)]

        return {
            "success": True,
            "total_models": len(request.training_configs),
            "successful_trainings": len(successful_trainings),
            "failed_trainings": len(failed_trainings),
            "total_time_seconds": total_time,
            "results": results,
            "summary": {
                "success_rate": len(successful_trainings) / len(request.training_configs),
                "average_training_time": total_time / len(request.training_configs)
            }
        }

    except Exception as e:
        logger.error(f"Error in batch training: {str(e)}")
        return {
            "success": False,
            "error_message": str(e)
        }

@router.get("/data/quality")
async def assess_data_quality(
    db: Session = Depends(get_db),
    team_ids: Optional[List[int]] = Query(None, description="Team IDs to assess"),
    user_ids: Optional[List[str]] = Query(None, description="User IDs to assess")
):
    """
    Assess data quality for model training.

    This endpoint evaluates the quality and completeness of available data
    for training prediction models.
    """
    try:
        # Collect training data assessment
        data_result = await data_service.collect_training_data(
            db=db,
            include_assessment_responses=True,
            include_team_performance=True,
            include_demographics=True,
            include_response_patterns=True,
            team_ids=team_ids,
            user_ids=user_ids,
            min_data_quality=0.0  # Collect all data for assessment
        )

        if not data_result["success"]:
            return {
                "success": False,
                "error_message": data_result.get("error", "Data collection failed")
            }

        df = data_result["data"]

        # Calculate quality metrics
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0

        # Feature statistics
        numeric_features = len(df.select_dtypes(include=['number']).columns)
        categorical_features = len(df.select_dtypes(include=['object', 'category']).columns)

        # Data volume assessment
        rows = len(df)
        columns = len(df.columns)

        # Quality assessment
        quality_score = min(1.0, completeness * 0.6 + (rows / 1000) * 0.4)  # Weighted score

        return {
            "success": True,
            "data_quality": {
                "overall_score": quality_score,
                "completeness": completeness,
                "total_rows": rows,
                "total_features": columns,
                "numeric_features": numeric_features,
                "categorical_features": categorical_features,
                "missing_values": int(missing_cells),
                "data_sources": data_result.get("data_sources", []),
                "assessment_time": datetime.now().isoformat()
            },
            "recommendations": _generate_data_quality_recommendations(quality_score, rows, completeness)
        }

    except Exception as e:
        logger.error(f"Error assessing data quality: {str(e)}")
        return {
            "success": False,
            "error_message": str(e)
        }

# Helper functions

async def _train_single_model(config: TrainingRequest, db: Session) -> Dict[str, Any]:
    """Helper function to train a single model."""
    try:
        start_time = datetime.now()

        if config.prediction_type == PredictionType.TEAM_PERFORMANCE:
            result = await prediction_service.train_team_performance_model(
                db=db,
                team_ids=config.team_ids,
                target_variable=config.target_variable,
                model_types=config.model_types,
                test_size=config.test_size,
                cv_folds=config.cv_folds,
                hyperparameter_tuning=config.hyperparameter_tuning,
                feature_selection=config.feature_selection
            )
        else:
            raise ValueError(f"Unsupported prediction type: {config.prediction_type.value}")

        training_time = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "prediction_type": config.prediction_type.value,
            "target_variable": config.target_variable,
            "best_model": result.best_model_name,
            "training_time_seconds": training_time,
            "performance_metrics": result.comparison_metrics
        }

    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return {
            "success": False,
            "error_message": str(e)
        }

def _generate_data_quality_recommendations(quality_score: float, rows: int, completeness: float) -> List[str]:
    """Generate data quality recommendations."""
    recommendations = []

    if quality_score < 0.3:
        recommendations.append("Data quality is poor. Consider data collection improvements before training models.")
    elif quality_score < 0.6:
        recommendations.append("Data quality is fair. Some feature engineering may improve model performance.")

    if completeness < 0.8:
        recommendations.append("Consider data imputation strategies for missing values.")

    if rows < 100:
        recommendations.append("Limited data volume. Models may not generalize well.")
    elif rows < 500:
        recommendations.append("Moderate data volume. Consider cross-validation for robust evaluation.")

    if quality_score >= 0.8 and rows >= 500:
        recommendations.append("Good data quality for model training.")

    return recommendations
