"""
Growth Trajectory Modeling Service

Advanced mathematical modeling for predicting individual and organizational growth
patterns using multiple curve fitting approaches and machine learning techniques.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.db.models.growth_trajectories import (
    GrowthPotentialAnalysis,
    GrowthTrajectory,
    TrajectoryPrediction,
)

logger = logging.getLogger(__name__)


class GrowthModelType(Enum):
    """Types of growth curve models"""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGISTIC = "logistic"
    POWER_LAW = "power_law"
    POLYNOMIAL = "polynomial"
    SIGMOIDAL = "sigmoidal"
    GOMPERTZ = "gompertz"
    RICHARDS = "richards"


class GrowthStage(Enum):
    """Stages of growth development"""

    FOUNDATION = "foundation"  # Initial learning phase
    ACCELERATION = "acceleration"  # Rapid growth phase
    MATURATION = "maturation"  # Slowing growth phase
    MASTERY = "mastery"  # Expert level achieved
    INNOVATION = "innovation"  # Creating new knowledge


class PotentialCategory(Enum):
    """Categories of growth potential"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXCEPTIONAL = "exceptional"


@dataclass
class TrajectoryPoint:
    """Data point for trajectory analysis"""

    timestamp: datetime
    value: float
    metric_type: str
    context: dict[str, Any] = None


@dataclass
class ModelParameters:
    """Parameters for fitted growth models"""

    model_type: GrowthModelType
    parameters: dict[str, float]
    r_squared: float
    aic: float
    bic: float
    rmse: float
    confidence_intervals: dict[str, tuple[float, float]] = None


@dataclass
class GrowthPrediction:
    """Growth trajectory prediction"""

    prediction_date: datetime
    predicted_value: float
    confidence_interval: tuple[float, float]
    probability_density: float
    growth_rate: float
    acceleration: float


@dataclass
class MilestonePrediction:
    """Prediction for milestone achievement"""

    milestone_name: str
    target_value: float
    achievement_probability: float
    expected_date: datetime
    confidence_interval: tuple[datetime, datetime]
    risk_factors: list[str]


class GrowthTrajectoryModeler:
    """Advanced growth trajectory modeling service"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.scaler = StandardScaler()

    async def build_growth_trajectory(
        self,
        user_id: str,
        competency_domain: str,
        trajectory_data: list[TrajectoryPoint],
        model_types: list[GrowthModelType] | None = None,
    ) -> GrowthTrajectory:
        """Build comprehensive growth trajectory with multiple models"""

        if not model_types:
            model_types = [
                GrowthModelType.LINEAR,
                GrowthModelType.EXPONENTIAL,
                GrowthModelType.LOGISTIC,
                GrowthModelType.SIGMOIDAL,
            ]

        self.logger.info(
            f"Building growth trajectory for user {user_id}, domain {competency_domain}"
        )

        # Prepare data
        df = self._prepare_trajectory_data(trajectory_data)

        if len(df) < 5:
            raise ValueError(
                "Insufficient data points for trajectory modeling (minimum 5 required)"
            )

        # Fit multiple models
        fitted_models = []
        for model_type in model_types:
            try:
                model_params = await self._fit_growth_model(df, model_type)
                if model_params.r_squared > 0.3:  # Minimum fit quality
                    fitted_models.append(model_params)
            except Exception as e:
                self.logger.warning(f"Failed to fit {model_type.value} model: {e}")
                continue

        if not fitted_models:
            raise ValueError("No suitable models could be fitted to the data") from e

        # Select best model based on AIC/BIC
        best_model = self._select_best_model(fitted_models)

        # Analyze growth characteristics
        growth_velocity = await self._calculate_growth_velocity(df, best_model)
        acceleration_rate = await self._calculate_acceleration(df, best_model)
        asymptotic_potential = await self._estimate_asymptotic_potential(best_model)
        growth_stage = await self._determine_growth_stage(df, best_model)

        # Create trajectory record
        trajectory = GrowthTrajectory(
            user_id=user_id,
            competency_domain=competency_domain,
            trajectory_type="individual",
            model_type=best_model.model_type.value,
            model_parameters=best_model.parameters,
            training_data_points=len(df),
            training_start_date=df["timestamp"].min(),
            training_end_date=df["timestamp"].max(),
            model_accuracy=best_model.r_squared,
            confidence_level=0.95,
            prediction_horizon_days=365,  # 1 year predictions
            growth_velocity=growth_velocity,
            acceleration_rate=acceleration_rate,
            asymptotic_potential=asymptotic_potential,
            growth_stage=growth_stage.value,
            plateau_probability=await self._estimate_plateau_probability(best_model),
            inflection_point_date=await self._estimate_inflection_point(best_model),
        )

        self.db.add(trajectory)
        self.db.commit()
        self.db.refresh(trajectory)

        # Generate initial predictions
        await self._generate_initial_predictions(trajectory, df, best_model)

        return trajectory

    async def predict_future_trajectory(
        self, trajectory_id: str, prediction_horizon_days: int = 365, confidence_level: float = 0.95
    ) -> list[GrowthPrediction]:
        """Generate predictions for future growth trajectory"""

        trajectory = (
            self.db.query(GrowthTrajectory).filter(GrowthTrajectory.id == trajectory_id).first()
        )

        if not trajectory:
            raise ValueError(f"Trajectory {trajectory_id} not found")

        # Extract model parameters
        model_type = GrowthModelType(trajectory.model_type)
        params = trajectory.model_parameters

        # Generate prediction dates
        start_date = trajectory.training_end_date
        end_date = start_date + timedelta(days=prediction_horizon_days)

        predictions = []
        current_date = start_date

        # Generate predictions at regular intervals
        while current_date <= end_date:
            days_elapsed = (current_date - start_date).days

            try:
                # Calculate prediction using model
                predicted_value, confidence_interval = await self._predict_with_model(
                    model_type, params, days_elapsed, confidence_level
                )

                # Calculate growth rate and acceleration
                growth_rate = await self._calculate_instantaneous_growth_rate(
                    model_type, params, days_elapsed
                )
                acceleration = await self._calculate_instantaneous_acceleration(
                    model_type, params, days_elapsed
                )

                prediction = GrowthPrediction(
                    prediction_date=current_date,
                    predicted_value=predicted_value,
                    confidence_interval=confidence_interval,
                    probability_density=1.0,  # Will be calculated later
                    growth_rate=growth_rate,
                    acceleration=acceleration,
                )

                predictions.append(prediction)

            except Exception as e:
                self.logger.warning(f"Failed to generate prediction for {current_date}: {e}")

            # Move to next prediction point
            current_date += timedelta(days=7)  # Weekly predictions

        # Save predictions to database
        await self._save_predictions(trajectory_id, predictions)

        return predictions

    async def analyze_growth_potential(
        self, user_id: str, competency_domains: list[str] | None = None
    ) -> GrowthPotentialAnalysis:
        """Comprehensive analysis of individual growth potential"""

        if not competency_domains:
            # Get all domains for user
            competency_domains = (
                self.db.query(GrowthTrajectory.competency_domain)
                .filter(GrowthTrajectory.user_id == user_id)
                .distinct()
                .all()
            )
            competency_domains = [domain[0] for domain in competency_domains]

        # Collect trajectory data
        trajectories = (
            self.db.query(GrowthTrajectory)
            .filter(
                GrowthTrajectory.user_id == user_id,
                GrowthTrajectory.competency_domain.in_(competency_domains),
            )
            .all()
        )

        if not trajectories:
            raise ValueError("No trajectories found for potential analysis")

        # Calculate core metrics
        potential_score = await self._calculate_overall_potential_score(trajectories)
        potential_category = self._categorize_potential(potential_score)
        growth_readiness = await self._assess_growth_readiness(trajectories)
        learning_agility = await self._assess_learning_agility(trajectories)
        adaptability_score = await self._assess_adaptability(trajectories)

        # Performance projections
        time_to_mastery = await self._estimate_time_to_mastery(trajectories)
        ceiling_estimate = await self._estimate_performance_ceiling(trajectories)
        growth_velocity_percentile = await self._calculate_velocity_percentile(
            user_id, trajectories
        )

        # Generate development insights
        key_drivers = await self._identify_key_growth_drivers(trajectories)
        limiting_factors = await self._identify_limiting_factors(trajectories)
        development_focus_areas = await self._recommend_development_focus(trajectories)
        optimal_development_path = await self._design_optimal_path(trajectories)

        # Career alignment analysis
        career_alignment = await self._assess_career_trajectory_alignment(user_id, trajectories)
        success_probability = await self._calculate_success_probability(trajectories)
        roi_estimate = await self._estimate_development_roi(trajectories)

        # Create analysis record
        analysis = GrowthPotentialAnalysis(
            user_id=user_id,
            potential_score=potential_score,
            potential_category=potential_category.value,
            growth_readiness=growth_readiness,
            learning_agility=learning_agility,
            adaptability_score=adaptability_score,
            time_to_mastery=time_to_mastery,
            ceiling_estimate=ceiling_estimate,
            growth_velocity_percentile=growth_velocity_percentile,
            key_drivers=key_drivers,
            limiting_factors=limiting_factors,
            development_focus_areas=development_focus_areas,
            optimal_development_path=optimal_development_path,
            career_trajectory_alignment=career_alignment,
            success_probability=success_probability,
            roi_estimate=roi_estimate,
            next_review_date=datetime.utcnow() + timedelta(days=90),
            analysis_methodology={
                "models_used": [t.model_type for t in trajectories],
                "data_points": sum(t.training_data_points for t in trajectories),
                "confidence_level": 0.95,
                "analysis_date": datetime.utcnow().isoformat(),
            },
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return analysis

    async def simulate_intervention_impact(
        self, trajectory_id: str, intervention_scenario: dict[str, Any], simulation_days: int = 365
    ) -> dict[str, Any]:
        """Simulate impact of interventions on growth trajectory"""

        trajectory = (
            self.db.query(GrowthTrajectory).filter(GrowthTrajectory.id == trajectory_id).first()
        )

        if not trajectory:
            raise ValueError(f"Trajectory {trajectory_id} not found")

        # Extract baseline model
        model_type = GrowthModelType(trajectory.model_type)
        baseline_params = trajectory.model_parameters.copy()

        # Apply intervention modifications
        modified_params = await self._apply_intervention_modifications(
            baseline_params, intervention_scenario
        )

        # Generate baseline predictions
        baseline_predictions = await self.predict_future_trajectory(trajectory_id, simulation_days)

        # Generate intervention predictions
        intervention_predictions = []
        start_date = trajectory.training_end_date

        for days_elapsed in range(0, simulation_days, 7):
            current_date = start_date + timedelta(days=days_elapsed)

            try:
                # Predict with modified parameters
                predicted_value, ci = await self._predict_with_model(
                    model_type, modified_params, days_elapsed, 0.95
                )

                intervention_predictions.append(
                    {"date": current_date, "value": predicted_value, "confidence_interval": ci}
                )

            except Exception as e:
                self.logger.warning(f"Intervention prediction failed for day {days_elapsed}: {e}")

        # Calculate impact metrics
        impact_analysis = await self._calculate_intervention_impact(
            baseline_predictions, intervention_predictions
        )

        return {
            "intervention_scenario": intervention_scenario,
            "baseline_predictions": baseline_predictions,
            "intervention_predictions": intervention_predictions,
            "impact_analysis": impact_analysis,
            "recommendations": await self._generate_intervention_recommendations(impact_analysis),
        }

    # Private methods for model fitting and calculations
    def _prepare_trajectory_data(self, trajectory_points: list[TrajectoryPoint]) -> pd.DataFrame:
        """Prepare trajectory data for modeling"""
        data = []
        for point in trajectory_points:
            data.append(
                {
                    "timestamp": point.timestamp,
                    "days_elapsed": 0,  # Will be calculated
                    "value": point.value,
                    "metric_type": point.metric_type,
                    "context": point.context or {},
                }
            )

        df = pd.DataFrame(data)
        df = df.sort_values("timestamp")

        # Calculate days elapsed from first point
        start_time = df["timestamp"].min()
        df["days_elapsed"] = (df["timestamp"] - start_time).dt.days

        return df

    async def _fit_growth_model(
        self, df: pd.DataFrame, model_type: GrowthModelType
    ) -> ModelParameters:
        """Fit specific growth model to trajectory data"""

        x = df["days_elapsed"].values
        y = df["value"].values

        try:
            if model_type == GrowthModelType.LINEAR:
                return await self._fit_linear_model(x, y)
            if model_type == GrowthModelType.EXPONENTIAL:
                return await self._fit_exponential_model(x, y)
            if model_type == GrowthModelType.LOGISTIC:
                return await self._fit_logistic_model(x, y)
            if model_type == GrowthModelType.SIGMOIDAL:
                return await self._fit_sigmoidal_model(x, y)
            if model_type == GrowthModelType.POWER_LAW:
                return await self._fit_power_law_model(x, y)
            if model_type == GrowthModelType.POLYNOMIAL:
                return await self._fit_polynomial_model(x, y)
            raise ValueError(f"Unsupported model type: {model_type}")

        except Exception as e:
            self.logger.error(f"Failed to fit {model_type.value} model: {e}")
            raise

    async def _fit_linear_model(self, x: np.ndarray, y: np.ndarray) -> ModelParameters:
        """Fit linear growth model: y = ax + b"""

        def linear_func(x, a, b):
            return a * x + b

        try:
            popt, pcov = curve_fit(linear_func, x, y, p0=[0.001, y[0]])
            a, b = popt

            # Calculate goodness of fit
            y_pred = linear_func(x, a, b)
            r_squared = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            # Calculate AIC and BIC
            n = len(y)
            k = 2  # Number of parameters
            aic = n * np.log(mean_squared_error(y, y_pred)) + 2 * k
            bic = n * np.log(mean_squared_error(y, y_pred)) + k * np.log(n)

            # Confidence intervals
            confidence_intervals = {}
            for i, param_name in enumerate(["a", "b"]):
                std_error = np.sqrt(np.diag(pcov))[i]
                confidence_intervals[param_name] = (
                    popt[i] - 1.96 * std_error,
                    popt[i] + 1.96 * std_error,
                )

            return ModelParameters(
                model_type=GrowthModelType.LINEAR,
                parameters={"a": float(a), "b": float(b)},
                r_squared=float(r_squared),
                aic=float(aic),
                bic=float(bic),
                rmse=float(rmse),
                confidence_intervals=confidence_intervals,
            )

        except Exception as e:
            raise ValueError(f"Linear model fitting failed: {e}") from e

    async def _fit_exponential_model(self, x: np.ndarray, y: np.ndarray) -> ModelParameters:
        """Fit exponential growth model: y = a * exp(b * x) + c"""

        def exponential_func(x, a, b, c):
            return a * np.exp(b * x) + c

        try:
            # Initial parameter guesses
            a_init = max(y) - min(y)
            b_init = 0.001
            c_init = min(y)

            popt, pcov = curve_fit(
                exponential_func, x, y, p0=[a_init, b_init, c_init], maxfev=10000
            )
            a, b, c = popt

            # Calculate goodness of fit
            y_pred = exponential_func(x, a, b, c)
            r_squared = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            # Calculate AIC and BIC
            n = len(y)
            k = 3
            aic = n * np.log(mean_squared_error(y, y_pred)) + 2 * k
            bic = n * np.log(mean_squared_error(y, y_pred)) + k * np.log(n)

            # Confidence intervals
            confidence_intervals = {}
            for i, param_name in enumerate(["a", "b", "c"]):
                std_error = np.sqrt(np.diag(pcov))[i]
                confidence_intervals[param_name] = (
                    popt[i] - 1.96 * std_error,
                    popt[i] + 1.96 * std_error,
                )

            return ModelParameters(
                model_type=GrowthModelType.EXPONENTIAL,
                parameters={"a": float(a), "b": float(b), "c": float(c)},
                r_squared=float(r_squared),
                aic=float(aic),
                bic=float(bic),
                rmse=float(rmse),
                confidence_intervals=confidence_intervals,
            )

        except Exception as e:
            raise ValueError(f"Exponential model fitting failed: {e}") from e

    async def _fit_logistic_model(self, x: np.ndarray, y: np.ndarray) -> ModelParameters:
        """Fit logistic growth model: y = L / (1 + exp(-k*(x - x0)))"""

        def logistic_func(x, L, k, x0):
            return L / (1 + np.exp(-k * (x - x0)))

        try:
            # Initial parameter guesses
            L_init = max(y) * 1.1  # Carrying capacity
            k_init = 0.01  # Growth rate
            x0_init = x[len(x) // 2]  # Inflection point

            popt, pcov = curve_fit(
                logistic_func,
                x,
                y,
                p0=[L_init, k_init, x0_init],
                maxfev=10000,
                bounds=([0, -np.inf, -np.inf], [np.inf, np.inf, np.inf]),
            )
            L, k, x0 = popt

            # Calculate goodness of fit
            y_pred = logistic_func(x, L, k, x0)
            r_squared = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            # Calculate AIC and BIC
            n = len(y)
            k_param = 3
            aic = n * np.log(mean_squared_error(y, y_pred)) + 2 * k_param
            bic = n * np.log(mean_squared_error(y, y_pred)) + k_param * np.log(n)

            # Confidence intervals
            confidence_intervals = {}
            for i, param_name in enumerate(["L", "k", "x0"]):
                std_error = np.sqrt(np.diag(pcov))[i]
                confidence_intervals[param_name] = (
                    popt[i] - 1.96 * std_error,
                    popt[i] + 1.96 * std_error,
                )

            return ModelParameters(
                model_type=GrowthModelType.LOGISTIC,
                parameters={"L": float(L), "k": float(k), "x0": float(x0)},
                r_squared=float(r_squared),
                aic=float(aic),
                bic=float(bic),
                rmse=float(rmse),
                confidence_intervals=confidence_intervals,
            )

        except Exception as e:
            raise ValueError(f"Logistic model fitting failed: {e}") from e

    async def _fit_sigmoidal_model(self, x: np.ndarray, y: np.ndarray) -> ModelParameters:
        """Fit sigmoidal model: y = L / (1 + exp(-k*(x - x0))) + y0"""

        def sigmoidal_func(x, L, k, x0, y0):
            return L / (1 + np.exp(-k * (x - x0))) + y0

        try:
            # Initial parameter guesses
            L_init = max(y) - min(y)  # Amplitude
            k_init = 0.01  # Steepness
            x0_init = x[len(x) // 2]  # Center
            y0_init = min(y)  # Offset

            popt, pcov = curve_fit(
                sigmoidal_func, x, y, p0=[L_init, k_init, x0_init, y0_init], maxfev=10000
            )
            L, k, x0, y0 = popt

            # Calculate goodness of fit
            y_pred = sigmoidal_func(x, L, k, x0, y0)
            r_squared = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            # Calculate AIC and BIC
            n = len(y)
            k_param = 4
            aic = n * np.log(mean_squared_error(y, y_pred)) + 2 * k_param
            bic = n * np.log(mean_squared_error(y, y_pred)) + k_param * np.log(n)

            # Confidence intervals
            confidence_intervals = {}
            for i, param_name in enumerate(["L", "k", "x0", "y0"]):
                std_error = np.sqrt(np.diag(pcov))[i]
                confidence_intervals[param_name] = (
                    popt[i] - 1.96 * std_error,
                    popt[i] + 1.96 * std_error,
                )

            return ModelParameters(
                model_type=GrowthModelType.SIGMOIDAL,
                parameters={"L": float(L), "k": float(k), "x0": float(x0), "y0": float(y0)},
                r_squared=float(r_squared),
                aic=float(aic),
                bic=float(bic),
                rmse=float(rmse),
                confidence_intervals=confidence_intervals,
            )

        except Exception as e:
            raise ValueError(f"Sigmoidal model fitting failed: {e}") from e

    async def _fit_power_law_model(self, x: np.ndarray, y: np.ndarray) -> ModelParameters:
        """Fit power law model: y = a * x^b + c"""

        def power_law_func(x, a, b, c):
            return a * np.power(x + 1, b) + c  # +1 to avoid x=0 issues

        try:
            # Initial parameter guesses
            a_init = 1.0
            b_init = 1.0
            c_init = min(y)

            popt, pcov = curve_fit(power_law_func, x, y, p0=[a_init, b_init, c_init], maxfev=10000)
            a, b, c = popt

            # Calculate goodness of fit
            y_pred = power_law_func(x, a, b, c)
            r_squared = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            # Calculate AIC and BIC
            n = len(y)
            k = 3
            aic = n * np.log(mean_squared_error(y, y_pred)) + 2 * k
            bic = n * np.log(mean_squared_error(y, y_pred)) + k * np.log(n)

            # Confidence intervals
            confidence_intervals = {}
            for i, param_name in enumerate(["a", "b", "c"]):
                std_error = np.sqrt(np.diag(pcov))[i]
                confidence_intervals[param_name] = (
                    popt[i] - 1.96 * std_error,
                    popt[i] + 1.96 * std_error,
                )

            return ModelParameters(
                model_type=GrowthModelType.POWER_LAW,
                parameters={"a": float(a), "b": float(b), "c": float(c)},
                r_squared=float(r_squared),
                aic=float(aic),
                bic=float(bic),
                rmse=float(rmse),
                confidence_intervals=confidence_intervals,
            )

        except Exception as e:
            raise ValueError(f"Power law model fitting failed: {e}") from e

    async def _fit_polynomial_model(self, x: np.ndarray, y: np.ndarray) -> ModelParameters:
        """Fit polynomial model (quadratic): y = ax^2 + bx + c"""

        def polynomial_func(x, a, b, c):
            return a * x**2 + b * x + c

        try:
            popt, pcov = curve_fit(polynomial_func, x, y)
            a, b, c = popt

            # Calculate goodness of fit
            y_pred = polynomial_func(x, a, b, c)
            r_squared = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            # Calculate AIC and BIC
            n = len(y)
            k = 3
            aic = n * np.log(mean_squared_error(y, y_pred)) + 2 * k
            bic = n * np.log(mean_squared_error(y, y_pred)) + k * np.log(n)

            # Confidence intervals
            confidence_intervals = {}
            for i, param_name in enumerate(["a", "b", "c"]):
                std_error = np.sqrt(np.diag(pcov))[i]
                confidence_intervals[param_name] = (
                    popt[i] - 1.96 * std_error,
                    popt[i] + 1.96 * std_error,
                )

            return ModelParameters(
                model_type=GrowthModelType.POLYNOMIAL,
                parameters={"a": float(a), "b": float(b), "c": float(c)},
                r_squared=float(r_squared),
                aic=float(aic),
                bic=float(bic),
                rmse=float(rmse),
                confidence_intervals=confidence_intervals,
            )

        except Exception as e:
            raise ValueError(f"Polynomial model fitting failed: {e}") from e

    # Additional helper methods for growth analysis
    def _select_best_model(self, models: list[ModelParameters]) -> ModelParameters:
        """Select best model based on AIC/BIC and R-squared"""
        # Use weighted scoring: 0.4*R² + 0.3*(1/normalized_AIC) + 0.3*(1/normalized_BIC)
        scores = []

        aic_values = [m.aic for m in models]
        bic_values = [m.bic for m in models]
        r2_values = [m.r_squared for m in models]

        # Normalize values
        aic_norm = [
            (aic - min(aic_values)) / (max(aic_values) - min(aic_values)) for aic in aic_values
        ]
        bic_norm = [
            (bic - min(bic_values)) / (max(bic_values) - min(bic_values)) for bic in bic_values
        ]

        for i, model in enumerate(models):
            # Lower AIC/BIC is better, higher R² is better
            score = 0.4 * r2_values[i] + 0.3 * (1 - aic_norm[i]) + 0.3 * (1 - bic_norm[i])
            scores.append(score)

        best_idx = np.argmax(scores)
        return models[best_idx]

    async def _generate_initial_predictions(
        self, trajectory: GrowthTrajectory, df: pd.DataFrame, model_params: ModelParameters
    ):
        """Generate initial predictions for the trajectory"""
        # This would generate predictions for the next few months
        # Implementation details would depend on specific business requirements

    async def _save_predictions(self, trajectory_id: str, predictions: list[GrowthPrediction]):
        """Save predictions to database"""
        for pred in predictions:
            db_pred = TrajectoryPrediction(
                trajectory_id=trajectory_id,
                prediction_date=pred.prediction_date,
                predicted_value=pred.predicted_value,
                confidence_interval_lower=pred.confidence_interval[0],
                confidence_interval_upper=pred.confidence_interval[1],
                growth_rate=pred.growth_rate,
                # Additional fields would be populated
            )
            self.db.add(db_pred)

        self.db.commit()

    # Placeholder methods for comprehensive functionality
    async def _calculate_growth_velocity(self, df: pd.DataFrame, model: ModelParameters) -> float:
        """Calculate current growth velocity"""
        # Implementation depends on model type
        return 0.01  # Placeholder

    async def _calculate_acceleration(self, df: pd.DataFrame, model: ModelParameters) -> float:
        """Calculate growth acceleration"""
        return 0.001  # Placeholder

    async def _estimate_asymptotic_potential(self, model: ModelParameters) -> float:
        """Estimate maximum potential value"""
        if model.model_type == GrowthModelType.LOGISTIC:
            return model.parameters.get("L", 0)
        if model.model_type == GrowthModelType.SIGMOIDAL:
            return model.parameters.get("L", 0) + model.parameters.get("y0", 0)
        return float("inf")  # No asymptote for linear/exponential

    async def _determine_growth_stage(
        self, df: pd.DataFrame, model: ModelParameters
    ) -> GrowthStage:
        """Determine current growth stage"""
        current_value = df["value"].iloc[-1]
        max_value = df["value"].max()

        if current_value < 0.3 * max_value:
            return GrowthStage.FOUNDATION
        if current_value < 0.6 * max_value:
            return GrowthStage.ACCELERATION
        if current_value < 0.8 * max_value:
            return GrowthStage.MATURATION
        if current_value < 0.95 * max_value:
            return GrowthStage.MASTERY
        return GrowthStage.INNOVATION

    async def _estimate_plateau_probability(self, model: ModelParameters) -> float:
        """Estimate probability of growth plateau"""
        # Implementation would analyze model characteristics
        return 0.2  # Placeholder

    async def _estimate_inflection_point(self, model: ModelParameters) -> datetime | None:
        """Estimate when growth inflection occurs"""
        if model.model_type == GrowthModelType.LOGISTIC:
            x0 = model.parameters.get("x0")
            if x0:
                # Convert days to date relative to some baseline
                return datetime.utcnow() + timedelta(days=int(x0))
        return None

    # Placeholder implementations for potential analysis methods
    async def _calculate_overall_potential_score(
        self, trajectories: list[GrowthTrajectory]
    ) -> float:
        """Calculate overall growth potential score"""
        # Implementation would analyze multiple trajectories
        return 0.75  # Placeholder

    def _categorize_potential(self, score: float) -> PotentialCategory:
        """Categorize potential score"""
        if score >= 0.9:
            return PotentialCategory.EXCEPTIONAL
        if score >= 0.75:
            return PotentialCategory.VERY_HIGH
        if score >= 0.6:
            return PotentialCategory.HIGH
        if score >= 0.4:
            return PotentialCategory.MEDIUM
        return PotentialCategory.LOW

    # Additional placeholder methods would be implemented here
    async def _predict_with_model(
        self,
        model_type: GrowthModelType,
        params: dict[str, float],
        days_elapsed: int,
        confidence_level: float,
    ) -> tuple[float, tuple[float, float]]:
        """Make prediction using fitted model"""
        # Implementation would use model parameters to predict
        return 0.0, (0.0, 0.0)  # Placeholder

    async def _calculate_instantaneous_growth_rate(
        self, model_type: GrowthModelType, params: dict[str, float], days_elapsed: int
    ) -> float:
        """Calculate instantaneous growth rate"""
        return 0.01  # Placeholder

    async def _calculate_instantaneous_acceleration(
        self, model_type: GrowthModelType, params: dict[str, float], days_elapsed: int
    ) -> float:
        """Calculate instantaneous acceleration"""
        return 0.001  # Placeholder

    # Placeholder methods for comprehensive analysis
    async def _assess_growth_readiness(self, trajectories: list[GrowthTrajectory]) -> float:
        return 0.8

    async def _assess_learning_agility(self, trajectories: list[GrowthTrajectory]) -> float:
        return 0.7

    async def _assess_adaptability(self, trajectories: list[GrowthTrajectory]) -> float:
        return 0.75

    async def _estimate_time_to_mastery(self, trajectories: list[GrowthTrajectory]) -> int:
        return 730  # 2 years

    async def _estimate_performance_ceiling(self, trajectories: list[GrowthTrajectory]) -> float:
        return 4.5

    async def _calculate_velocity_percentile(
        self, user_id: str, trajectories: list[GrowthTrajectory]
    ) -> float:
        return 0.80

    async def _identify_key_growth_drivers(self, trajectories: list[GrowthTrajectory]) -> list[str]:
        return ["consistent_practice", "mentorship", "challenge_appropriate"]

    async def _identify_limiting_factors(self, trajectories: list[GrowthTrajectory]) -> list[str]:
        return ["time_constraints", "resource_limitations"]

    async def _recommend_development_focus(self, trajectories: list[GrowthTrajectory]) -> list[str]:
        return ["technical_skills", "leadership_capabilities"]

    async def _design_optimal_path(self, trajectories: list[GrowthTrajectory]) -> list[str]:
        return ["skill_development", "experience_building", "network_expansion"]

    async def _assess_career_trajectory_alignment(
        self, user_id: str, trajectories: list[GrowthTrajectory]
    ) -> float:
        return 0.85

    async def _calculate_success_probability(self, trajectories: list[GrowthTrajectory]) -> float:
        return 0.78

    async def _estimate_development_roi(self, trajectories: list[GrowthTrajectory]) -> float:
        return 3.2

    async def _apply_intervention_modifications(
        self, baseline_params: dict[str, float], intervention_scenario: dict[str, Any]
    ) -> dict[str, float]:
        """Apply intervention modifications to model parameters"""
        modified_params = baseline_params.copy()

        # Example modifications based on intervention type
        if intervention_scenario.get("intensity") == "high":
            # Increase growth rate parameters
            for key in modified_params:
                if key in ["k", "b", "a"]:
                    modified_params[key] *= 1.3

        return modified_params

    async def _calculate_intervention_impact(
        self,
        baseline_predictions: list[GrowthPrediction],
        intervention_predictions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate impact metrics for intervention"""
        return {
            "improvement_percentage": 15.5,
            "time_to_goal_reduction_days": 60,
            "roi_estimate": 2.8,
            "confidence_level": 0.85,
        }

    async def _generate_intervention_recommendations(
        self, impact_analysis: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations based on impact analysis"""
        return [
            "Continue current intervention approach",
            "Consider increasing intensity for faster results",
            "Monitor progress quarterly",
        ]
