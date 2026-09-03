"""
Bayesian Burnout Prediction Engine

Implements hierarchical Bayesian models for burnout risk prediction with
uncertainty quantification using PyMC.

Key Features:
- Hierarchical modeling with organization-level random effects
- Uncertainty quantification with credible intervals
- 14-day trajectory prediction using Gaussian Processes
- MCMC inference with NUTS sampler

Author: PsychSync Engineering Team
Version: 2.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import arviz as az
import numpy as np
import pymc as pm

logger = logging.getLogger(__name__)


@dataclass
class BurnoutFeatures:
    """Input features for burnout prediction"""

    # Workload features
    weekly_hours: float
    continuous_days: int
    after_hours_percentage: float
    late_night_work_days: int
    early_morning_work_days: int
    weekend_work_days: int

    # Recovery features
    pto_days_used: int
    pto_days_available: int
    avg_daily_break_hours: float
    sleep_hours_avg: float

    # Sentiment features
    negative_sentiment_avg: float
    sentiment_volatility: float
    conflict_indicators: int

    # Communication features
    communication_volume_decline: float
    meeting_participation_decline: float
    response_time_avg_minutes: float

    # Biometric features (optional)
    resting_hr: Optional[float] = None
    hrv: Optional[float] = None
    blood_pressure_systolic: Optional[float] = None
    steps_per_day: Optional[float] = None

    def to_feature_vector(self) -> np.ndarray:
        """Convert to numpy array for model input"""
        return np.array(
            [
                self.weekly_hours,
                float(self.continuous_days),
                self.after_hours_percentage,
                self.pto_days_used,
                self.avg_daily_break_hours,
                self.sleep_hours_avg,
                abs(self.negative_sentiment_avg),
                self.sentiment_volatility,
                float(self.conflict_indicators),
                self.communication_volume_decline,
                self.meeting_participation_decline,
                min(self.response_time_avg_minutes / 60.0, 2.0),  # Cap at 2 hours
            ]
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BurnoutFeatures":
        """Create from dictionary"""
        return cls(
            weekly_hours=data.get("weekly_hours", 40),
            continuous_days=data.get("continuous_days", 0),
            after_hours_percentage=data.get("after_hours_percentage", 0.0),
            late_night_work_days=data.get("late_night_work_days", 0),
            early_morning_work_days=data.get("early_morning_work_days", 0),
            weekend_work_days=data.get("weekend_work_days", 0),
            pto_days_used=data.get("pto_days_used", 0),
            pto_days_available=data.get("pto_days_available", 15),
            avg_daily_break_hours=data.get("avg_daily_break_hours", 0.5),
            sleep_hours_avg=data.get("sleep_hours_avg", 7.0),
            negative_sentiment_avg=data.get("negative_sentiment_avg", 0.0),
            sentiment_volatility=data.get("sentiment_volatility", 0.0),
            conflict_indicators=data.get("conflict_indicators", 0),
            communication_volume_decline=data.get("communication_volume_decline", 0.0),
            meeting_participation_decline=data.get(
                "meeting_participation_decline", 0.0
            ),
            response_time_avg_minutes=data.get("response_time_avg_minutes", 60),
            resting_hr=data.get("resting_hr"),
            hrv=data.get("hrv"),
            blood_pressure_systolic=data.get("blood_pressure_systolic"),
            steps_per_day=data.get("steps_per_day"),
        )


@dataclass
class PredictionResult:
    """Result from Bayesian prediction"""

    user_id: str
    prediction_date: datetime
    model_type: str = "bayesian"

    # BRS predictions
    brs_mean: float = 0.0
    brs_median: float = 0.0
    brs_std: float = 0.0
    brs_50ci: Tuple[float, float] = (0.0, 0.0)  # 50% credible interval
    brs_89ci: Tuple[float, float] = (0.0, 0.0)  # 89% credible interval
    brs_94ci: Tuple[float, float] = (0.0, 0.0)  # 94% credible interval
    brs_95ci: Tuple[float, float] = (0.0, 0.0)  # 95% credible interval

    # Probability predictions
    probability_mean: float = 0.0
    probability_50ci: Tuple[float, float] = (0.0, 0.0)
    probability_89ci: Tuple[float, float] = (0.0, 0.0)
    probability_95ci: Tuple[float, float] = (0.0, 0.0)

    # Risk classification
    risk_level: str = "minimal"
    confidence: str = "moderate"

    # Metadata
    feature_vector: Optional[np.ndarray] = None
    posterior_samples: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "prediction_date": self.prediction_date.isoformat(),
            "model_type": self.model_type,
            "brs_mean": round(self.brs_mean, 2),
            "brs_median": round(self.brs_median, 2),
            "brs_std": round(self.brs_std, 2),
            "brs_50ci": [round(v, 2) for v in self.brs_50ci],
            "brs_89ci": [round(v, 2) for v in self.brs_89ci],
            "brs_94ci": [round(v, 2) for v in self.brs_94ci],
            "brs_95ci": [round(v, 2) for v in self.brs_95ci],
            "probability_mean": round(self.probability_mean * 100, 1),
            "probability_50ci": [round(v * 100, 1) for v in self.probability_50ci],
            "probability_89ci": [round(v * 100, 1) for v in self.probability_89ci],
            "probability_95ci": [round(v * 100, 1) for v in self.probability_95ci],
            "risk_level": self.risk_level,
            "confidence": self.confidence,
        }


@dataclass
class TrajectoryResult:
    """14-day trajectory prediction result"""

    user_id: str
    prediction_date: datetime
    days: List[int] = field(default_factory=list)

    # BRS trajectory
    brs_mean: List[float] = field(default_factory=list)
    brs_lower_89ci: List[float] = field(default_factory=list)
    brs_upper_89ci: List[float] = field(default_factory=list)
    brs_lower_95ci: List[float] = field(default_factory=list)
    brs_upper_95ci: List[float] = field(default_factory=list)

    # Probability trajectory
    probability_mean: List[float] = field(default_factory=list)
    probability_lower_89ci: List[float] = field(default_factory=list)
    probability_upper_89ci: List[float] = field(default_factory=list)

    # Warning zones
    warning_zones: List[Dict[str, Any]] = field(default_factory=list)
    intervention_points: List[Dict[str, Any]] = field(default_factory=list)
    risk_trajectory: str = "stable"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "prediction_date": self.prediction_date.isoformat(),
            "days": self.days,
            "brs_mean": [round(v, 2) for v in self.brs_mean],
            "brs_lower_89ci": [round(v, 2) for v in self.brs_lower_89ci],
            "brs_upper_89ci": [round(v, 2) for v in self.brs_upper_89ci],
            "brs_lower_95ci": [round(v, 2) for v in self.brs_lower_95ci],
            "brs_upper_95ci": [round(v, 2) for v in self.brs_upper_95ci],
            "probability_mean": [round(v * 100, 1) for v in self.probability_mean],
            "probability_lower_89ci": [
                round(v * 100, 1) for v in self.probability_lower_89ci
            ],
            "probability_upper_89ci": [
                round(v * 100, 1) for v in self.probability_upper_89ci
            ],
            "warning_zones": self.warning_zones,
            "intervention_points": self.intervention_points,
            "risk_trajectory": self.risk_trajectory,
        }


class BayesianBurnoutPredictor:
    """
    Hierarchical Bayesian model for burnout prediction

    Model Specification:
    BRS_i ~ Normal(μ_i, σ²)
    μ_i = α + β₁·Workload_i + β₂·Recovery_i + ... + u_org[org_i]

    Priors:
    α ~ Normal(50, 20)
    β₁...βₙ ~ Normal(0, 10)
    σ ~ HalfNormal(15)
    u_org ~ Normal(0, τ²)
    τ ~ HalfNormal(10)
    """

    def __init__(self, n_features: int = 12, n_organizations: int = 100):
        self.n_features = n_features
        self.n_organizations = n_organizations
        self.model = None
        self.trace = None
        self.is_fitted = False

        # Feature names for interpretability
        self.feature_names = [
            "weekly_hours",
            "continuous_days",
            "after_hours_pct",
            "pto_days_used",
            "daily_break_hours",
            "sleep_hours",
            "neg_sentiment",
            "sentiment_volatility",
            "conflict_indicators",
            "comm_volume_decline",
            "meeting_decline",
            "response_time_hours",
        ]

    def build_model(self, X: np.ndarray, y: np.ndarray, org_ids: np.ndarray):
        """
        Build hierarchical Bayesian model

        Args:
            X: Feature matrix (n_samples, n_features)
            y: BRS scores (n_samples,)
            org_ids: Organization IDs for random effects (n_samples,)
        """
        logger.info(
            f"Building Bayesian model with {X.shape[0]} samples, {X.shape[1]} features"
        )

        with pm.Model() as self.model:
            # Data containers (for future predictions)
            X_data = pm.Data("X", X)
            y_data = pm.Data("y", y)
            org_data = pm.Data("org", org_ids)

            # Hyperpriors
            α = pm.Normal("α", mu=50, sigma=20)  # Intercept
            β = pm.Normal("β", mu=0, sigma=10, shape=self.n_features)  # Coefficients
            σ = pm.HalfNormal("σ", sigma=15)  # Observation noise

            # Organization-level random effects
            τ = pm.HalfNormal("τ", sigma=10)  # Between-org variation
            u_org = pm.Normal("u_org", mu=0, sigma=τ, shape=self.n_organizations)

            # Linear predictor
            μ = α + pm.math.dot(X_data, β) + u_org[org_data]

            # Likelihood
            likelihood = pm.Normal("y_obs", mu=μ, sigma=σ, observed=y_data)

        logger.info("Bayesian model built successfully")
        return self.model

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        org_ids: np.ndarray,
        samples: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        target_accept: float = 0.95,
        cores: int = 4,
    ):
        """
        Fit model using MCMC sampling (NUTS)

        Args:
            X: Feature matrix
            y: BRS scores
            org_ids: Organization IDs
            samples: Number of posterior samples per chain
            tune: Number of tuning steps
            chains: Number of MCMC chains
            target_accept: Target acceptance rate
            cores: Number of CPU cores to use

        Returns:
            InferenceData object with posterior samples
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        logger.info(
            f"Fitting Bayesian model with {samples} samples per chain, {chains} chains"
        )

        with self.model:
            # Sample from posterior
            self.trace = pm.sample(
                draws=samples,
                tune=tune,
                chains=chains,
                target_accept=target_accept,
                return_inferencedata=True,
                cores=cores,
                progressbar=True,
            )

        self.is_fitted = True

        # Diagnostics
        summary = az.summary(self.trace, hdi_prob=0.94)
        rhat_values = summary["r_hat"]
        max_rhat = rhat_values.max()

        if max_rhat > 1.05:
            logger.warning(
                f"Some parameters have R-hat > 1.05 (max: {max_rhat:.3f}). "
                "Model may not have converged."
            )
        else:
            logger.info(f"Model converged successfully (max R-hat: {max_rhat:.3f})")

        return self.trace

    def predict(self, X_new: np.ndarray, org_id: int) -> PredictionResult:
        """
        Predict BRS with uncertainty quantification

        Args:
            X_new: Feature vector (1, n_features) or (n_features,)
            org_id: Organization ID

        Returns:
            PredictionResult with mean, std, and credible intervals
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # Ensure 2D array
        if X_new.ndim == 1:
            X_new = X_new.reshape(1, -1)

        # Get posterior predictive samples
        posterior_samples = self._get_posterior_predictive(X_new, org_id)

        # Calculate statistics
        brs_mean = float(np.mean(posterior_samples))
        brs_median = float(np.median(posterior_samples))
        brs_std = float(np.std(posterior_samples))

        # Credible intervals
        brs_50ci = (
            float(np.percentile(posterior_samples, 25)),
            float(np.percentile(posterior_samples, 75)),
        )
        brs_89ci = (
            float(np.percentile(posterior_samples, 5.5)),
            float(np.percentile(posterior_samples, 94.5)),
        )
        brs_94ci = (
            float(np.percentile(posterior_samples, 3)),
            float(np.percentile(posterior_samples, 97)),
        )
        brs_95ci = (
            float(np.percentile(posterior_samples, 2.5)),
            float(np.percentile(posterior_samples, 97.5)),
        )

        # Convert to probability
        def brs_to_prob(brs_samples):
            return 1 / (1 + np.exp(-(-8.5 + 0.12 * brs_samples)))

        prob_samples = brs_to_prob(posterior_samples)
        prob_mean = float(np.mean(prob_samples))
        prob_50ci = (
            float(np.percentile(prob_samples, 25)),
            float(np.percentile(prob_samples, 75)),
        )
        prob_89ci = (
            float(np.percentile(prob_samples, 5.5)),
            float(np.percentile(prob_samples, 94.5)),
        )
        prob_95ci = (
            float(np.percentile(prob_samples, 2.5)),
            float(np.percentile(prob_samples, 97.5)),
        )

        # Risk classification
        risk_level = self._classify_risk(brs_mean)
        confidence = self._assess_confidence(brs_95ci)

        result = PredictionResult(
            user_id="",  # Set by caller
            prediction_date=datetime.utcnow(),
            brs_mean=brs_mean,
            brs_median=brs_median,
            brs_std=brs_std,
            brs_50ci=brs_50ci,
            brs_89ci=brs_89ci,
            brs_94ci=brs_94ci,
            brs_95ci=brs_95ci,
            probability_mean=prob_mean,
            probability_50ci=prob_50ci,
            probability_89ci=prob_89ci,
            probability_95ci=prob_95ci,
            risk_level=risk_level,
            confidence=confidence,
            feature_vector=X_new.flatten(),
            posterior_samples=posterior_samples,
        )

        return result

    def _get_posterior_predictive(
        self, X_new: np.ndarray, org_id: int, samples: int = 2000
    ) -> np.ndarray:
        """Get posterior predictive samples"""
        if self.trace is None:
            raise ValueError("No trace available. Model must be fitted first.")

        with self.model:
            # Update data for prediction
            pm.set_data(
                {
                    "X": X_new,
                    "y": np.zeros(X_new.shape[0]),  # Dummy
                    "org": np.full(X_new.shape[0], org_id, dtype=int),
                }
            )

            # Sample posterior predictive
            ppc = pm.sample_posterior_predictive(
                self.trace, var_names=["y_obs"], samples=samples
            )

        return ppc.posterior_predictive["y_obs"].values.flatten()

    def _classify_risk(self, brs: float) -> str:
        """Classify risk level from BRS"""
        if brs >= 80:
            return "critical"
        elif brs >= 65:
            return "high"
        elif brs >= 45:
            return "moderate"
        elif brs >= 25:
            return "low"
        else:
            return "minimal"

    def _assess_confidence(self, ci_95: Tuple[float, float]) -> str:
        """Assess prediction confidence based on CI width"""
        width = ci_95[1] - ci_95[0]
        if width < 10:
            return "high"
        elif width < 20:
            return "moderate"
        else:
            return "low"

    def predict_14_day_trajectory(
        self, features: BurnoutFeatures, org_id: int
    ) -> TrajectoryResult:
        """
        Predict 14-day burnout trajectory using Gaussian Process

        This is a simplified version - full GP implementation would require
        time-series data. Here we use the hierarchical model with assumed
        trajectory based on current risk level.

        Args:
            features: Current burnout features
            org_id: Organization ID

        Returns:
            TrajectoryResult with 14-day predictions
        """
        # Get current prediction
        X = features.to_feature_vector()
        current_pred = self.predict(X, org_id)

        # Simulate trajectory (in production, use GP on historical data)
        days = list(range(1, 15))
        brs_mean = []
        brs_lower_89ci = []
        brs_upper_89ci = []
        brs_lower_95ci = []
        brs_upper_95ci = []
        prob_mean = []
        prob_lower_89ci = []
        prob_upper_89ci = []

        # Simple trajectory model based on current trend
        # In production, this would use Gaussian Process regression
        current_brs = current_pred.brs_mean
        current_prob = current_pred.probability_mean

        # Assume slight worsening if high risk, improvement if low risk
        # (in production, this would be learned from data)
        trend_factor = 0.5 if current_brs > 50 else -0.3

        for day in days:
            # Daily change
            daily_change = trend_factor * day * 0.5
            day_brs = current_brs + daily_change

            # Add uncertainty that increases with time
            uncertainty = 2 + day * 0.8

            brs_mean.append(max(0, min(100, day_brs)))
            brs_lower_95ci.append(max(0, day_brs - 1.96 * uncertainty))
            brs_upper_95ci.append(min(100, day_brs + 1.96 * uncertainty))
            brs_lower_89ci.append(max(0, day_brs - 1.55 * uncertainty))
            brs_upper_89ci.append(min(100, day_brs + 1.55 * uncertainty))

            # Convert to probability
            def brs_to_prob(brs):
                return 1 / (1 + np.exp(-(-8.5 + 0.12 * brs)))

            prob_mean.append(brs_to_prob(day_brs))
            prob_lower_89ci.append(brs_to_prob(day_brs - 1.55 * uncertainty))
            prob_upper_89ci.append(brs_to_prob(day_brs + 1.55 * uncertainty))

        # Classify warning zones
        warning_zones = []
        for day, prob in zip(days, prob_mean):
            if prob >= 0.8:
                zone = "critical"
            elif prob >= 0.6:
                zone = "high"
            elif prob >= 0.3:
                zone = "moderate"
            elif prob >= 0.1:
                zone = "elevated"
            else:
                zone = "normal"

            warning_zones.append(
                {"day": day, "zone": zone, "probability": round(prob * 100, 1)}
            )

        # Find intervention points
        intervention_points = self._find_intervention_points(warning_zones)

        # Determine trajectory direction
        if prob_mean[-1] < prob_mean[0] - 0.1:
            risk_trajectory = "improving"
        elif prob_mean[-1] > prob_mean[0] + 0.1:
            risk_trajectory = "worsening"
        else:
            risk_trajectory = "stable"

        return TrajectoryResult(
            user_id="",  # Set by caller
            prediction_date=datetime.utcnow(),
            days=days,
            brs_mean=brs_mean,
            brs_lower_89ci=brs_lower_89ci,
            brs_upper_89ci=brs_upper_89ci,
            brs_lower_95ci=brs_lower_95ci,
            brs_upper_95ci=brs_upper_95ci,
            probability_mean=prob_mean,
            probability_lower_89ci=prob_lower_89ci,
            probability_upper_89ci=prob_upper_89ci,
            warning_zones=warning_zones,
            intervention_points=intervention_points,
            risk_trajectory=risk_trajectory,
        )

    def _find_intervention_points(self, warning_zones: List[Dict]) -> List[Dict]:
        """Find optimal intervention points based on warning zones"""
        interventions = []
        entered_high_zone = False

        for zone_data in warning_zones:
            day = zone_data["day"]
            zone = zone_data["zone"]
            prob = zone_data["probability"]

            # First time entering high/critical zone
            if zone in ["high", "critical"] and not entered_high_zone:
                interventions.append(
                    {
                        "day": day,
                        "type": "immediate",
                        "priority": "urgent",
                        "reason": f"Entered {zone} zone",
                        "recommended_action": "Same-day manager check-in",
                    }
                )
                entered_high_zone = True

            # Day 7 checkpoint
            elif day == 7 and zone in ["elevated", "moderate"]:
                interventions.append(
                    {
                        "day": day,
                        "type": "scheduled",
                        "priority": "high",
                        "reason": f"Still in {zone} zone at day 7",
                        "recommended_action": "Schedule intervention within 48 hours",
                    }
                )

            # Day 10 checkpoint - approaching critical
            elif day == 10 and prob > 50:
                interventions.append(
                    {
                        "day": day,
                        "type": "preventive",
                        "priority": "critical",
                        "reason": "Approaching high-risk threshold",
                        "recommended_action": "Execute crisis prevention plan",
                    }
                )

        return sorted(interventions, key=lambda x: x["day"])

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from posterior coefficient distributions

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        # Extract coefficient posterior samples
        β_samples = self.trace.posterior["β"].values

        # Calculate absolute mean as importance
        importance = np.mean(np.abs(β_samples), axis=(0, 1))

        return dict(zip(self.feature_names, importance.tolist()))


# Convenience functions
def create_bayesian_predictor(n_organizations: int = 100) -> BayesianBurnoutPredictor:
    """
    Factory function to create Bayesian predictor

    Args:
        n_organizations: Estimated number of unique organizations

    Returns:
        Initialized BayesianBurnoutPredictor
    """
    return BayesianBurnoutPredictor(n_features=12, n_organizations=n_organizations)


def load_pretrained_model(model_path: str) -> BayesianBurnoutPredictor:
    """
    Load a pre-trained Bayesian model from disk

    Args:
        model_path: Path to saved model (InferenceData object)

    Returns:
        Loaded BayesianBurnoutPredictor
    """
    predictor = BayesianBurnoutPredictor()
    predictor.trace = az.from_netcdf(model_path)
    predictor.is_fitted = True

    return predictor
