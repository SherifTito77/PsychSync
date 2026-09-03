"""
Trajectory Prediction Service

Advanced prediction system for forecasting future growth trajectories using
machine learning, ensemble methods, and uncertainty quantification.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.growth_trajectories import (
    GrowthMilestone,
    GrowthTrajectory,
    TrajectoryPrediction,
)
from app.services.growth_trajectory_modeling import (
    GrowthModelType,
    GrowthTrajectoryModeler,
)

logger = logging.getLogger(__name__)


class PredictionMethod(Enum):
    """Methods for trajectory prediction"""

    PARAMETRIC_MODEL = "parametric_model"
    ENSEMBLE_ML = "ensemble_ml"
    GAUSSIAN_PROCESS = "gaussian_process"
    BAYESIAN_FORECAST = "bayesian_forecast"
    SIMULATION_BASED = "simulation_based"
    HYBRID_APPROACH = "hybrid_approach"


class UncertaintyLevel(Enum):
    """Levels of prediction uncertainty"""

    VERY_LOW = "very_low"  # < 5% uncertainty
    LOW = "low"  # 5-15% uncertainty
    MODERATE = "moderate"  # 15-30% uncertainty
    HIGH = "high"  # 30-50% uncertainty
    VERY_HIGH = "very_high"  # > 50% uncertainty


@dataclass
class PredictionFeatures:
    """Features for trajectory prediction"""

    days_elapsed: float
    current_value: float
    historical_velocity: list[float]
    acceleration_trend: float
    seasonality_factors: dict[str, float]
    external_factors: dict[str, float]
    learning_history: dict[str, Any]
    intervention_history: list[dict[str, Any]]


@dataclass
class PredictionResult:
    """Single trajectory prediction result"""

    prediction_date: datetime
    predicted_value: float
    confidence_interval: tuple[float, float]
    prediction_method: PredictionMethod
    uncertainty_level: UncertaintyLevel
    probability_distribution: dict[str, float] | None
    feature_importance: dict[str, float] | None
    model_confidence: float
    data_quality_score: float


@dataclass
class MilestoneForecast:
    """Forecast for milestone achievement"""

    milestone_id: str
    milestone_name: str
    target_value: float
    achievement_probability: float
    expected_date: datetime
    confidence_interval: tuple[datetime, datetime]
    risk_factors: list[str]
    success_factors: list[str]
    optimal_intervention_timing: datetime | None


@dataclass
class TrajectoryForecast:
    """Complete trajectory forecast"""

    trajectory_id: str
    forecast_horizon_days: int
    predictions: list[PredictionResult]
    milestone_forecasts: list[MilestoneForecast]
    overall_confidence: float
    data_quality_assessment: dict[str, Any]
    forecast_metadata: dict[str, Any]


class TrajectoryPredictor:
    """Advanced trajectory prediction service"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.modeler = GrowthTrajectoryModeler(db_session)
        self.scalers = {}
        self.ml_models = {}
        self.gp_models = {}

    async def generate_comprehensive_forecast(
        self,
        trajectory_id: str,
        forecast_horizon_days: int = 365,
        prediction_methods: list[PredictionMethod] | None = None,
        include_milestones: bool = True,
    ) -> TrajectoryForecast:
        """Generate comprehensive trajectory forecast using multiple methods"""

        if not prediction_methods:
            prediction_methods = [
                PredictionMethod.PARAMETRIC_MODEL,
                PredictionMethod.ENSEMBLE_ML,
                PredictionMethod.GAUSSIAN_PROCESS,
            ]

        self.logger.info(
            f"Generating comprehensive forecast for trajectory {trajectory_id}"
        )

        # Get trajectory data
        trajectory = (
            self.db.query(GrowthTrajectory)
            .filter(GrowthTrajectory.id == trajectory_id)
            .first()
        )

        if not trajectory:
            raise ValueError(f"Trajectory {trajectory_id} not found")

        # Prepare historical data
        historical_data = await self._prepare_historical_data(trajectory)
        prediction_features = await self._extract_prediction_features(historical_data)

        # Generate predictions using multiple methods
        method_predictions = {}
        for method in prediction_methods:
            try:
                predictions = await self._predict_with_method(
                    trajectory, method, forecast_horizon_days, prediction_features
                )
                method_predictions[method] = predictions
            except Exception as e:
                self.logger.warning(f"Prediction method {method.value} failed: {e}")

        if not method_predictions:
            raise ValueError("No prediction methods succeeded")

        # Combine predictions using ensemble approach
        combined_predictions = await self._combine_predictions(method_predictions)

        # Generate milestone forecasts if requested
        milestone_forecasts = []
        if include_milestones:
            milestone_forecasts = await self._forecast_milestones(
                trajectory, combined_predictions, forecast_horizon_days
            )

        # Assess overall confidence
        overall_confidence = await self._calculate_overall_confidence(
            method_predictions, combined_predictions
        )

        # Data quality assessment
        data_quality = await self._assess_data_quality(historical_data)

        forecast = TrajectoryForecast(
            trajectory_id=trajectory_id,
            forecast_horizon_days=forecast_horizon_days,
            predictions=combined_predictions,
            milestone_forecasts=milestone_forecasts,
            overall_confidence=overall_confidence,
            data_quality_assessment=data_quality,
            forecast_metadata={
                "methods_used": [m.value for m in method_predictions],
                "generation_date": datetime.utcnow().isoformat(),
                "data_points": len(historical_data),
                "feature_engineering": True,
            },
        )

        # Save forecast to database
        await self._save_forecast_to_database(forecast)

        return forecast

    async def predict_milestone_achievement(
        self,
        trajectory_id: str,
        milestone_target: float,
        confidence_threshold: float = 0.8,
    ) -> MilestoneForecast:
        """Predict when a specific milestone will be achieved"""

        trajectory = (
            self.db.query(GrowthTrajectory)
            .filter(GrowthTrajectory.id == trajectory_id)
            .first()
        )

        if not trajectory:
            raise ValueError(f"Trajectory {trajectory_id} not found")

        # Generate extended forecast
        forecast = await self.generate_comprehensive_forecast(
            trajectory_id,
            forecast_horizon_days=1095,  # 3 years
        )

        # Find when milestone is achieved
        achievement_date = None
        achievement_probability = 0
        confidence_interval = (None, None)

        for prediction in forecast.predictions:
            if prediction.predicted_value >= milestone_target:
                achievement_date = prediction.prediction_date
                # Calculate probability based on confidence interval
                if prediction.confidence_interval[0] >= milestone_target:
                    achievement_probability = 0.95
                elif prediction.confidence_interval[1] >= milestone_target:
                    # Linear interpolation within confidence interval
                    range_size = (
                        prediction.confidence_interval[1]
                        - prediction.confidence_interval[0]
                    )
                    if range_size > 0:
                        achievement_probability = max(
                            0.5,
                            min(
                                0.95,
                                (
                                    prediction.predicted_value
                                    - prediction.confidence_interval[0]
                                )
                                / range_size
                                * 0.45
                                + 0.5,
                            ),
                        )
                break

        if not achievement_date:
            # Milestone not achieved within forecast horizon
            achievement_date = forecast.predictions[-1].prediction_date
            achievement_probability = 0.1

        # Analyze risk and success factors
        risk_factors = await self._identify_milestone_risks(
            trajectory, milestone_target
        )
        success_factors = await self._identify_milestone_success_factors(
            trajectory, milestone_target
        )

        # Determine optimal intervention timing
        optimal_timing = await self._calculate_optimal_intervention_timing(
            trajectory, milestone_target, achievement_date
        )

        return MilestoneForecast(
            milestone_id="",  # Would be populated with actual milestone ID
            milestone_name=f"Milestone: {milestone_target}",
            target_value=milestone_target,
            achievement_probability=achievement_probability,
            expected_date=achievement_date,
            confidence_interval=confidence_interval,
            risk_factors=risk_factors,
            success_factors=success_factors,
            optimal_intervention_timing=optimal_timing,
        )

    async def simulate_intervention_scenarios(
        self,
        trajectory_id: str,
        intervention_scenarios: list[dict[str, Any]],
        forecast_horizon_days: int = 365,
    ) -> dict[str, TrajectoryForecast]:
        """Simulate multiple intervention scenarios"""

        baseline_forecast = await self.generate_comprehensive_forecast(
            trajectory_id, forecast_horizon_days
        )

        scenario_results = {"baseline": baseline_forecast}

        for i, scenario in enumerate(intervention_scenarios):
            try:
                # Create modified trajectory for scenario
                scenario_trajectory = await self._create_scenario_trajectory(
                    trajectory_id, scenario
                )

                # Generate forecast for scenario
                scenario_forecast = await self.generate_comprehensive_forecast(
                    scenario_trajectory.id, forecast_horizon_days
                )

                scenario_results[f"scenario_{i + 1}"] = scenario_forecast

            except Exception as e:
                self.logger.warning(f"Scenario {i + 1} simulation failed: {e}")

        return scenario_results

    async def update_predictions_with_actuals(
        self, trajectory_id: str, new_actual_data: list[tuple[datetime, float]]
    ) -> dict[str, Any]:
        """Update predictions with new actual measurements"""

        trajectory = (
            self.db.query(GrowthTrajectory)
            .filter(GrowthTrajectory.id == trajectory_id)
            .first()
        )

        if not trajectory:
            raise ValueError(f"Trajectory {trajectory_id} not found")

        # Compare actuals with predictions
        prediction_comparisons = []
        for actual_date, actual_value in new_actual_data:
            # Find corresponding prediction
            prediction = (
                self.db.query(TrajectoryPrediction)
                .filter(
                    TrajectoryPrediction.trajectory_id == trajectory_id,
                    func.date(TrajectoryPrediction.prediction_date)
                    == actual_date.date(),
                )
                .first()
            )

            if prediction:
                prediction_accuracy = (
                    1
                    - abs(actual_value - float(prediction.predicted_value))
                    / actual_value
                )
                prediction_comparisons.append(
                    {
                        "date": actual_date,
                        "predicted": float(prediction.predicted_value),
                        "actual": actual_value,
                        "accuracy": prediction_accuracy,
                        "error": actual_value - float(prediction.predicted_value),
                    }
                )

        # Calculate model performance metrics
        if prediction_comparisons:
            mae = np.mean([abs(comp["error"]) for comp in prediction_comparisons])
            mape = (
                np.mean(
                    [
                        abs(comp["error"]) / comp["actual"]
                        for comp in prediction_comparisons
                    ]
                )
                * 100
            )
            bias = np.mean([comp["error"] for comp in prediction_comparisons])
        else:
            mae = mape = bias = None

        # Determine if model retraining is needed
        retraining_needed = await self._assess_retraining_need(
            prediction_comparisons, trajectory
        )

        if retraining_needed:
            # Retrain model with new data
            await self._retrain_trajectory_model(trajectory_id, new_actual_data)

        return {
            "prediction_comparisons": prediction_comparisons,
            "performance_metrics": {"mae": mae, "mape": mape, "bias": bias},
            "retraining_needed": retraining_needed,
            "updated_at": datetime.utcnow(),
        }

    # Private methods for prediction implementation
    async def _prepare_historical_data(
        self, trajectory: GrowthTrajectory
    ) -> pd.DataFrame:
        """Prepare historical data for prediction"""

        # Get historical predictions and actual measurements
        historical_predictions = (
            self.db.query(TrajectoryPrediction)
            .filter(TrajectoryPrediction.trajectory_id == trajectory.id)
            .order_by(TrajectoryPrediction.prediction_date)
            .all()
        )

        # Convert to DataFrame
        data = []
        for pred in historical_predictions:
            data.append(
                {
                    "date": pred.prediction_date,
                    "predicted_value": float(pred.predicted_value),
                    "confidence_interval_lower": (
                        float(pred.confidence_interval_lower)
                        if pred.confidence_interval_lower
                        else None
                    ),
                    "confidence_interval_upper": (
                        float(pred.confidence_interval_upper)
                        if pred.confidence_interval_upper
                        else None
                    ),
                    "growth_rate": (
                        float(pred.growth_rate) if pred.growth_rate else None
                    ),
                }
            )

        return pd.DataFrame(data)

    async def _extract_prediction_features(
        self, historical_data: pd.DataFrame
    ) -> PredictionFeatures:
        """Extract features for prediction modeling"""

        if historical_data.empty:
            return PredictionFeatures(
                days_elapsed=0,
                current_value=0,
                historical_velocity=[],
                acceleration_trend=0,
                seasonality_factors={},
                external_factors={},
                learning_history={},
                intervention_history=[],
            )

        # Calculate basic features
        current_value = (
            historical_data["predicted_value"].iloc[-1]
            if not historical_data.empty
            else 0
        )

        # Calculate historical velocities
        if len(historical_data) > 1:
            velocities = []
            for i in range(1, len(historical_data)):
                days_diff = (
                    historical_data.iloc[i]["date"]
                    - historical_data.iloc[i - 1]["date"]
                ).days
                if days_diff > 0:
                    value_diff = (
                        historical_data.iloc[i]["predicted_value"]
                        - historical_data.iloc[i - 1]["predicted_value"]
                    )
                    velocity = value_diff / days_diff
                    velocities.append(velocity)
        else:
            velocities = []

        # Calculate acceleration trend
        acceleration_trend = 0
        if len(velocities) > 1:
            recent_velocities = velocities[-5:]  # Last 5 velocities
            if len(recent_velocities) > 1:
                acceleration_trend = np.mean(np.diff(recent_velocities))

        return PredictionFeatures(
            days_elapsed=0,  # Would be calculated based on trajectory start
            current_value=current_value,
            historical_velocity=velocities,
            acceleration_trend=acceleration_trend,
            seasonality_factors={},  # Would be calculated if seasonal data available
            external_factors={},  # Would be populated from external data sources
            learning_history={},  # Would be populated from learning records
            intervention_history=[],  # Would be populated from intervention records
        )

    async def _predict_with_method(
        self,
        trajectory: GrowthTrajectory,
        method: PredictionMethod,
        forecast_horizon_days: int,
        features: PredictionFeatures,
    ) -> list[PredictionResult]:
        """Generate predictions using specific method"""

        if method == PredictionMethod.PARAMETRIC_MODEL:
            return await self._predict_with_parametric_model(
                trajectory, forecast_horizon_days
            )
        if method == PredictionMethod.ENSEMBLE_ML:
            return await self._predict_with_ensemble_ml(
                trajectory, forecast_horizon_days, features
            )
        if method == PredictionMethod.GAUSSIAN_PROCESS:
            return await self._predict_with_gaussian_process(
                trajectory, forecast_horizon_days, features
            )
        if method == PredictionMethod.BAYESIAN_FORECAST:
            return await self._predict_with_bayesian_forecast(
                trajectory, forecast_horizon_days
            )
        raise ValueError(f"Unsupported prediction method: {method}")

    async def _predict_with_parametric_model(
        self, trajectory: GrowthTrajectory, forecast_horizon_days: int
    ) -> list[PredictionResult]:
        """Predict using fitted parametric model"""

        model_type = GrowthModelType(trajectory.model_type)
        params = trajectory.model_parameters

        predictions = []
        start_date = trajectory.training_end_date

        for days_ahead in range(7, forecast_horizon_days + 1, 7):  # Weekly predictions
            prediction_date = start_date + timedelta(days=days_ahead)

            try:
                # Use the modeler to predict
                predicted_value, confidence_interval = (
                    await self.modeler._predict_with_model(
                        model_type, params, days_ahead, 0.95
                    )
                )

                # Calculate uncertainty level based on confidence interval width
                ci_width = confidence_interval[1] - confidence_interval[0]
                relative_uncertainty = ci_width / max(predicted_value, 0.1)

                if relative_uncertainty < 0.1:
                    uncertainty_level = UncertaintyLevel.VERY_LOW
                elif relative_uncertainty < 0.2:
                    uncertainty_level = UncertaintyLevel.LOW
                elif relative_uncertainty < 0.4:
                    uncertainty_level = UncertaintyLevel.MODERATE
                elif relative_uncertainty < 0.6:
                    uncertainty_level = UncertaintyLevel.HIGH
                else:
                    uncertainty_level = UncertaintyLevel.VERY_HIGH

                prediction = PredictionResult(
                    prediction_date=prediction_date,
                    predicted_value=predicted_value,
                    confidence_interval=confidence_interval,
                    prediction_method=PredictionMethod.PARAMETRIC_MODEL,
                    uncertainty_level=uncertainty_level,
                    probability_distribution=None,
                    feature_importance=None,
                    model_confidence=float(trajectory.model_accuracy or 0.5),
                    data_quality_score=0.9,  # High quality for parametric model
                )

                predictions.append(prediction)

            except Exception as e:
                self.logger.warning(
                    f"Parametric prediction failed for day {days_ahead}: {e}"
                )

        return predictions

    async def _predict_with_ensemble_ml(
        self,
        trajectory: GrowthTrajectory,
        forecast_horizon_days: int,
        features: PredictionFeatures,
    ) -> list[PredictionResult]:
        """Predict using ensemble machine learning models"""

        # This is a simplified implementation
        # In practice, you would train ML models on historical data

        predictions = []
        start_date = trajectory.training_end_date
        current_value = features.current_value

        # Simple trend-based prediction with ML-like uncertainty
        for days_ahead in range(7, forecast_horizon_days + 1, 7):
            prediction_date = start_date + timedelta(days=days_ahead)

            # Use growth velocity from trajectory if available
            growth_rate = float(trajectory.growth_velocity or 0.01)

            # Apply acceleration if available
            acceleration = float(trajectory.acceleration_rate or 0)
            predicted_value = (
                current_value
                + (growth_rate * days_ahead)
                + (0.5 * acceleration * days_ahead**2)
            )

            # Add ensemble uncertainty
            uncertainty = 0.1 + (days_ahead / forecast_horizon_days) * 0.3
            confidence_interval = (
                max(0, predicted_value * (1 - uncertainty)),
                predicted_value * (1 + uncertainty),
            )

            prediction = PredictionResult(
                prediction_date=prediction_date,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                prediction_method=PredictionMethod.ENSEMBLE_ML,
                uncertainty_level=UncertaintyLevel.MODERATE,
                probability_distribution=None,
                feature_importance={
                    "growth_velocity": 0.4,
                    "acceleration": 0.3,
                    "historical_trend": 0.3,
                },
                model_confidence=0.75,
                data_quality_score=0.8,
            )

            predictions.append(prediction)

        return predictions

    async def _predict_with_gaussian_process(
        self,
        trajectory: GrowthTrajectory,
        forecast_horizon_days: int,
        features: PredictionFeatures,
    ) -> list[PredictionResult]:
        """Predict using Gaussian Process regression"""

        # This is a simplified implementation
        # In practice, you would train GP models on historical data

        predictions = []
        start_date = trajectory.training_end_date
        current_value = features.current_value

        for days_ahead in range(7, forecast_horizon_days + 1, 7):
            prediction_date = start_date + timedelta(days=days_ahead)

            # Simple GP-like prediction with uncertainty that grows with distance
            mean_growth = float(trajectory.growth_velocity or 0.01)
            predicted_value = current_value + mean_growth * days_ahead

            # GP uncertainty increases with prediction horizon
            uncertainty = 0.05 * np.sqrt(
                days_ahead / 30
            )  # Uncertainty grows with sqrt of time
            confidence_interval = (
                max(0, predicted_value - uncertainty),
                predicted_value + uncertainty,
            )

            prediction = PredictionResult(
                prediction_date=prediction_date,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                prediction_method=PredictionMethod.GAUSSIAN_PROCESS,
                uncertainty_level=(
                    UncertaintyLevel.LOW
                    if days_ahead < 180
                    else UncertaintyLevel.MODERATE
                ),
                probability_distribution=None,
                feature_importance={"time_horizon": 0.6, "historical_pattern": 0.4},
                model_confidence=0.8,
                data_quality_score=0.85,
            )

            predictions.append(prediction)

        return predictions

    async def _predict_with_bayesian_forecast(
        self, trajectory: GrowthTrajectory, forecast_horizon_days: int
    ) -> list[PredictionResult]:
        """Predict using Bayesian forecasting methods"""

        # Simplified Bayesian forecasting
        predictions = []
        start_date = trajectory.training_end_date
        current_value = features.current_value

        for days_ahead in range(7, forecast_horizon_days + 1, 7):
            prediction_date = start_date + timedelta(days=days_ahead)

            # Bayesian combination of parametric and trend-based predictions
            parametric_pred = (
                current_value + float(trajectory.growth_velocity or 0.01) * days_ahead
            )
            trend_pred = current_value * (1 + 0.01) ** (
                days_ahead / 30
            )  # Monthly growth

            # Bayesian weighted average
            weight_parametric = 0.6
            weight_trend = 0.4
            predicted_value = (
                weight_parametric * parametric_pred + weight_trend * trend_pred
            )

            # Bayesian uncertainty combining model and parameter uncertainty
            model_uncertainty = 0.1
            param_uncertainty = 0.05
            total_uncertainty = np.sqrt(
                model_uncertainty**2 + param_uncertainty**2
            ) * (1 + days_ahead / 365)

            confidence_interval = (
                max(0, predicted_value - total_uncertainty),
                predicted_value + total_uncertainty,
            )

            prediction = PredictionResult(
                prediction_date=prediction_date,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                prediction_method=PredictionMethod.BAYESIAN_FORECAST,
                uncertainty_level=UncertaintyLevel.MODERATE,
                probability_distribution={
                    "mean": predicted_value,
                    "std": total_uncertainty,
                },
                feature_importance={
                    "parametric_model": weight_parametric,
                    "trend_model": weight_trend,
                },
                model_confidence=0.82,
                data_quality_score=0.88,
            )

            predictions.append(prediction)

        return predictions

    async def _combine_predictions(
        self, method_predictions: dict[PredictionMethod, list[PredictionResult]]
    ) -> list[PredictionResult]:
        """Combine predictions from multiple methods using weighted ensemble"""

        if not method_predictions:
            return []

        # Get all unique prediction dates
        all_dates = set()
        for predictions in method_predictions.values():
            for pred in predictions:
                all_dates.add(pred.prediction_date)

        combined_predictions = []

        for date in sorted(all_dates):
            # Collect predictions for this date from all methods
            date_predictions = []
            method_weights = {}

            for method, predictions in method_predictions.items():
                for pred in predictions:
                    if pred.prediction_date == date:
                        date_predictions.append(pred)
                        # Assign weights based on method confidence
                        if method == PredictionMethod.PARAMETRIC_MODEL:
                            method_weights[method] = pred.model_confidence * 0.4
                        elif (
                            method == PredictionMethod.ENSEMBLE_ML
                            or method == PredictionMethod.GAUSSIAN_PROCESS
                        ):
                            method_weights[method] = pred.model_confidence * 0.3
                        break

            if date_predictions:
                # Weighted average of predictions
                total_weight = sum(method_weights.values())
                if total_weight > 0:
                    weighted_prediction = (
                        sum(
                            pred.predicted_value * method_weights.get(method, 0)
                            for method, pred in zip(
                                method_weights.keys(), date_predictions
                            )
                        )
                        / total_weight
                    )

                    # Combine confidence intervals (weighted)
                    lower_bounds = [
                        pred.confidence_interval[0]
                        for pred in date_predictions
                        if pred.confidence_interval[0]
                    ]
                    upper_bounds = [
                        pred.confidence_interval[1]
                        for pred in date_predictions
                        if pred.confidence_interval[1]
                    ]

                    if lower_bounds and upper_bounds:
                        combined_lower = (
                            sum(
                                lb * method_weights.get(method, 0)
                                for method, lb in zip(
                                    method_weights.keys(), lower_bounds
                                )
                            )
                            / total_weight
                        )
                        combined_upper = (
                            sum(
                                ub * method_weights.get(method, 0)
                                for method, ub in zip(
                                    method_weights.keys(), upper_bounds
                                )
                            )
                            / total_weight
                        )
                    else:
                        # Default confidence interval if none available
                        margin = weighted_prediction * 0.2
                        combined_lower = max(0, weighted_prediction - margin)
                        combined_upper = weighted_prediction + margin

                    # Overall confidence is weighted average
                    overall_confidence = (
                        sum(
                            pred.model_confidence * method_weights.get(method, 0)
                            for method, pred in zip(
                                method_weights.keys(), date_predictions
                            )
                        )
                        / total_weight
                    )

                    combined_prediction = PredictionResult(
                        prediction_date=date,
                        predicted_value=weighted_prediction,
                        confidence_interval=(combined_lower, combined_upper),
                        prediction_method=PredictionMethod.HYBRID_APPROACH,
                        uncertainty_level=UncertaintyLevel.MODERATE,  # Default
                        probability_distribution=None,
                        feature_importance={
                            method.value: weight / total_weight
                            for method, weight in method_weights.items()
                        },
                        model_confidence=overall_confidence,
                        data_quality_score=np.mean(
                            [pred.data_quality_score for pred in date_predictions]
                        ),
                    )

                    combined_predictions.append(combined_prediction)

        return combined_predictions

    async def _forecast_milestones(
        self,
        trajectory: GrowthTrajectory,
        predictions: list[PredictionResult],
        forecast_horizon_days: int,
    ) -> list[MilestoneForecast]:
        """Forecast achievement of growth milestones"""

        # Get milestones for this trajectory
        milestones = (
            self.db.query(GrowthMilestone)
            .filter(GrowthMilestone.trajectory_id == trajectory.id)
            .all()
        )

        milestone_forecasts = []

        for milestone in milestones:
            try:
                forecast = await self.predict_milestone_achievement(
                    trajectory.id, milestone.target_value
                )
                forecast.milestone_id = str(milestone.id)
                forecast.milestone_name = milestone.milestone_name
                milestone_forecasts.append(forecast)
            except Exception as e:
                self.logger.warning(
                    f"Milestone forecast failed for {milestone.id}: {e}"
                )

        return milestone_forecasts

    # Placeholder implementations for remaining methods
    async def _calculate_overall_confidence(
        self,
        method_predictions: dict[PredictionMethod, list[PredictionResult]],
        combined_predictions: list[PredictionResult],
    ) -> float:
        """Calculate overall forecast confidence"""
        if not combined_predictions:
            return 0.5

        # Average confidence across all combined predictions
        return np.mean([pred.model_confidence for pred in combined_predictions])

    async def _assess_data_quality(
        self, historical_data: pd.DataFrame
    ) -> dict[str, Any]:
        """Assess quality of historical data"""
        if historical_data.empty:
            return {"score": 0.0, "issues": ["No historical data"]}

        score = 1.0
        issues = []

        # Check for missing values
        missing_ratio = (
            historical_data.isnull().sum().sum()
            / len(historical_data)
            / len(historical_data.columns)
        )
        if missing_ratio > 0.1:
            score -= missing_ratio
            issues.append(f"High missing data ratio: {missing_ratio:.2%}")

        # Check data consistency
        if len(historical_data) < 10:
            score -= 0.3
            issues.append("Limited historical data points")

        return {
            "score": max(0, score),
            "issues": issues,
            "data_points": len(historical_data),
        }

    async def _save_forecast_to_database(self, forecast: TrajectoryForecast):
        """Save forecast predictions to database"""
        for prediction in forecast.predictions:
            db_prediction = TrajectoryPrediction(
                trajectory_id=forecast.trajectory_id,
                prediction_date=prediction.prediction_date,
                predicted_value=prediction.predicted_value,
                confidence_interval_lower=prediction.confidence_interval[0],
                confidence_interval_upper=prediction.confidence_interval[1],
                prediction_accuracy=prediction.model_confidence,
                growth_rate=0,  # Would be calculated
                prediction_metadata={
                    "method": prediction.prediction_method.value,
                    "uncertainty_level": prediction.uncertainty_level.value,
                    "feature_importance": prediction.feature_importance,
                },
            )
            self.db.add(db_prediction)

        self.db.commit()

    # Additional placeholder methods
    async def _identify_milestone_risks(
        self, trajectory: GrowthTrajectory, target: float
    ) -> list[str]:
        return ["plateau_risk", "external_factors", "motivation_decline"]

    async def _identify_milestone_success_factors(
        self, trajectory: GrowthTrajectory, target: float
    ) -> list[str]:
        return ["consistent_practice", "mentor_support", "resource_availability"]

    async def _calculate_optimal_intervention_timing(
        self, trajectory: GrowthTrajectory, target: float, expected_date: datetime
    ) -> datetime | None:
        # Calculate optimal timing (e.g., 30 days before expected achievement)
        return expected_date - timedelta(days=30)

    async def _create_scenario_trajectory(
        self, trajectory_id: str, scenario: dict[str, Any]
    ) -> GrowthTrajectory:
        """Create modified trajectory for scenario simulation"""
        # This would create a copy of the trajectory with modified parameters
        # Placeholder implementation
        original = (
            self.db.query(GrowthTrajectory)
            .filter(GrowthTrajectory.id == trajectory_id)
            .first()
        )
        return original  # Simplified

    async def _assess_retraining_need(
        self, prediction_comparisons: list[dict[str, Any]], trajectory: GrowthTrajectory
    ) -> bool:
        """Assess if model retraining is needed"""
        if not prediction_comparisons:
            return False

        # Check if average accuracy is below threshold
        avg_accuracy = np.mean([comp["accuracy"] for comp in prediction_comparisons])
        return avg_accuracy < 0.8

    async def _retrain_trajectory_model(
        self, trajectory_id: str, new_data: list[tuple[datetime, float]]
    ):
        """Retrain trajectory model with new data"""
        # This would trigger model retraining with the new data
        self.logger.info(
            f"Retraining model for trajectory {trajectory_id} with {len(new_data)} new data points"
        )
