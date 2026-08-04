"""
A/B Testing and Ground Truth Validation Framework

Provides tools for:
- A/B testing between Bayesian and ML models
- Ground truth validation against actual outcomes
- Statistical significance testing
- Model performance monitoring
- Calibration analysis

Author: PsychSync Engineering Team
Version: 2.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available model types for comparison"""

    BAYESIAN = "bayesian"
    ML_ENSEMBLE = "ml_ensemble"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LINEAR_REGRESSION = "linear_regression"


@dataclass
class PredictionRecord:
    """Single prediction record for A/B testing"""

    user_id: str
    group: str  # 'control' or 'treatment'
    model_type: ModelType
    prediction_date: datetime

    # Prediction values
    predicted_brs: float
    predicted_probability: float
    predicted_risk_level: str

    # Ground truth (filled in later)
    actual_brs: Optional[float] = None
    actual_outcome: Optional[str] = None  # 'burnout', 'at_risk', 'healthy'
    is_burnout_event: Optional[bool] = None

    # Additional metadata
    confidence_interval: Optional[Tuple[float, float]] = None
    features: Optional[Dict[str, Any]] = None


@dataclass
class ABTestConfig:
    """
    A/B test configuration

    Test Design:
    - Random assignment: 50% control, 50% treatment
    - Duration: Minimum 4 weeks
    - Sample size: Power analysis for 80% power at 5% significance
    """

    name: str
    control_model: ModelType
    treatment_model: ModelType
    start_date: datetime
    end_date: datetime
    sample_size_per_group: int
    metrics: List[str] = field(default_factory=lambda: ["mae", "calibration"])
    significance_level: float = 0.05
    min_effect_size: float = 0.2  # Cohen's d


@dataclass
class ABTestResult:
    """Results from A/B test analysis"""

    test_name: str
    control_model: ModelType
    treatment_model: ModelType

    # Statistical results
    metric_results: Dict[str, Dict[str, Any]]
    overall_winner: str  # 'control', 'treatment', 'tie'
    confidence_level: float
    recommendation: str

    # Sample info
    control_sample_size: int
    treatment_sample_size: int
    test_duration_days: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "test_name": self.test_name,
            "control_model": self.control_model.value,
            "treatment_model": self.treatment_model.value,
            "metric_results": self.metric_results,
            "overall_winner": self.overall_winner,
            "confidence_level": f"{self.confidence_level * 100:.0f}%",
            "recommendation": self.recommendation,
            "control_sample_size": self.control_sample_size,
            "treatment_sample_size": self.treatment_sample_size,
            "test_duration_days": self.test_duration_days,
        }


class ABTestAnalyzer:
    """
    Analyze A/B test results with statistical significance testing

    Methods:
    - Independent t-test for metric comparison
    - Cohen's d for effect size
    - Power analysis for sample size determination
    """

    def __init__(self, config: ABTestConfig):
        self.config = config
        self.control_data: List[PredictionRecord] = []
        self.treatment_data: List[PredictionRecord] = []

    def add_prediction_result(self, record: PredictionRecord):
        """
        Add a prediction result to the appropriate group

        Args:
            record: PredictionRecord with group='control' or 'treatment'
        """
        if record.group == "control":
            self.control_data.append(record)
        elif record.group == "treatment":
            self.treatment_data.append(record)
        else:
            raise ValueError(f"Invalid group: {record.group}")

    def analyze(self) -> ABTestResult:
        """
        Perform statistical analysis on collected data

        Returns:
            ABTestResult with statistical analysis
        """
        if not self.control_data or not self.treatment_data:
            raise ValueError("Both control and treatment groups must have data")

        # Extract errors for MAE analysis
        control_errors = self._extract_errors(self.control_data)
        treatment_errors = self._extract_errors(self.treatment_data)

        # MAE comparison
        control_mae = np.mean(control_errors)
        treatment_mae = np.mean(treatment_errors)

        # Independent t-test
        t_stat, p_value = stats.ttest_ind(control_errors, treatment_errors)

        # Effect size (Cohen's d)
        pooled_std = self._calculate_pooled_std(control_errors, treatment_errors)
        cohens_d = (control_mae - treatment_mae) / pooled_std

        # Determine significance
        significant = p_value < self.config.significance_level

        # Winner determination
        if significant and treatment_mae < control_mae:
            winner = "treatment"
            recommendation = f"Adopt {self.config.treatment_model.value} model - shows {abs((treatment_mae - control_mae) / control_mae * 100):.1f}% improvement"
        elif significant and control_mae < treatment_mae:
            winner = "control"
            recommendation = (
                f"Keep {self.config.control_model.value} model - outperforms treatment"
            )
        else:
            winner = "tie"
            recommendation = "No significant difference - consider other factors (interpretability, computational cost)"

        metric_results = {
            "mae": {
                "control": float(control_mae),
                "treatment": float(treatment_mae),
                "improvement_pct": float(
                    (control_mae - treatment_mae) / control_mae * 100
                ),
                "p_value": float(p_value),
                "significant": significant,
                "cohens_d": float(cohens_d),
                "t_statistic": float(t_stat),
            }
        }

        return ABTestResult(
            test_name=self.config.name,
            control_model=self.config.control_model,
            treatment_model=self.config.treatment_model,
            metric_results=metric_results,
            overall_winner=winner,
            confidence_level=1 - self.config.significance_level,
            recommendation=recommendation,
            control_sample_size=len(self.control_data),
            treatment_sample_size=len(self.treatment_data),
            test_duration_days=(self.config.end_date - self.config.start_date).days,
        )

    def _extract_errors(self, records: List[PredictionRecord]) -> np.ndarray:
        """Extract prediction errors from records"""
        errors = []
        for record in records:
            if record.actual_brs is not None:
                errors.append(abs(record.predicted_brs - record.actual_brs))
        return np.array(errors)

    def _calculate_pooled_std(
        self, control: np.ndarray, treatment: np.ndarray
    ) -> float:
        """Calculate pooled standard deviation for Cohen's d"""
        n1, n2 = len(control), len(treatment)
        var1, var2 = np.var(control, ddof=1), np.var(treatment, ddof=1)

        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        return np.sqrt(pooled_var)

    def calculate_sample_size(self, effect_size: float, power: float = 0.8) -> int:
        """
        Calculate required sample size per group using power analysis

        Args:
            effect_size: Cohen's d (small=0.2, medium=0.5, large=0.8)
            power: Statistical power (1 - β)

        Returns:
            Required sample size per group
        """
        from statsmodels.stats.power import ttest_ind_power

        analysis = ttest_ind_power()
        sample_size = analysis.solve_power(
            effect_size=effect_size,
            power=power,
            alpha=self.config.significance_level,
            ratio=1.0,
        )

        return int(np.ceil(sample_size))


@dataclass
class GroundTruthOutcome:
    """Ground truth outcome for validation"""

    user_id: str
    prediction_id: str
    prediction_date: datetime
    outcome_date: datetime
    horizon_days: int

    # Outcome flags
    is_burnout_event: bool
    is_medical_leave: bool
    is_turnover: bool
    is_performance_decline: bool

    # Details
    medical_leave_days: int = 0
    sick_leave_days: int = 0
    performance_rating_before: Optional[float] = None
    performance_rating_after: Optional[float] = None

    # Classification
    overall_outcome: str = "healthy"  # 'burnout', 'at_risk', 'healthy'


@dataclass
class ValidationMetrics:
    """Validation metrics for model performance"""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float]
    brier_score: float
    calibration_error: float

    total_predictions: int
    actual_burnouts: int
    true_positives: int
    false_positives: int
    false_negatives: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "accuracy": round(self.accuracy, 3),
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1_score": round(self.f1_score, 3),
            "roc_auc": round(self.roc_auc, 3) if self.roc_auc else None,
            "brier_score": round(self.brier_score, 3),
            "calibration_error": round(self.calibration_error, 3),
            "total_predictions": self.total_predictions,
            "actual_burnouts": self.actual_burnouts,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
        }


@dataclass
class CalibrationResult:
    """Results from calibration analysis"""

    bin_data: List[Dict[str, Any]]
    mean_calibration_error: float
    is_well_calibrated: bool
    reliability_diagram_data: Optional[List[Dict]] = None


class GroundTruthValidator:
    """
    Validate predictions against actual outcomes

    Ground truth sources:
    - Actual burnout events (medical leave, diagnosis)
    - Voluntary turnover
    - Performance decline
    - Sick leave patterns
    """

    def __init__(self):
        self.predictions: List[PredictionRecord] = []
        self.outcomes: List[GroundTruthOutcome] = []

    def add_prediction(self, prediction: PredictionRecord):
        """Add a prediction for later validation"""
        self.predictions.append(prediction)

    def add_outcome(self, outcome: GroundTruthOutcome):
        """Add a ground truth outcome"""
        self.outcomes.append(outcome)

    def validate_predictions(self, horizon_days: int = 14) -> Dict[str, Any]:
        """
        Validate predictions against ground truth

        Args:
            horizon_days: Prediction horizon to validate (default 14 days)

        Returns:
            Dictionary with metrics, calibration, and recommendations
        """
        # Match predictions with outcomes
        matched_records = self._match_predictions_to_outcomes(horizon_days)

        if not matched_records:
            logger.warning("No matched prediction-outcome pairs found")
            return {
                "metrics": None,
                "calibration": None,
                "recommendations": ["No ground truth data available for validation"],
            }

        # Extract arrays for sklearn metrics
        y_true = np.array([1 if r["is_burnout"] else 0 for r in matched_records])
        y_pred_proba = np.array([r["probability"] for r in matched_records])
        y_pred_class = np.array(
            [
                1 if r["risk_level"] in ["high", "critical"] else 0
                for r in matched_records
            ]
        )

        # Calculate metrics
        metrics = self._calculate_metrics(y_true, y_pred_class, y_pred_proba)

        # Calibration analysis
        calibration = self._analyze_calibration(matched_records)

        # Generate recommendations
        recommendations = self._generate_validation_recommendations(
            metrics, calibration
        )

        return {
            "metrics": metrics.to_dict(),
            "calibration": {
                "bin_data": calibration.bin_data,
                "mean_calibration_error": calibration.mean_calibration_error,
                "is_well_calibrated": calibration.is_well_calibrated,
            },
            "recommendations": recommendations,
        }

    def _match_predictions_to_outcomes(self, horizon_days: int) -> List[Dict]:
        """Match predictions with ground truth outcomes"""
        matched = []

        for pred in self.predictions:
            # Find matching outcome
            for outcome in self.outcomes:
                if (
                    pred.user_id == outcome.user_id
                    and outcome.prediction_date == pred.prediction_date
                    and outcome.horizon_days == horizon_days
                ):

                    matched.append(
                        {
                            "user_id": pred.user_id,
                            "predicted_brs": pred.predicted_brs,
                            "predicted_probability": pred.predicted_probability,
                            "predicted_risk_level": pred.predicted_risk_level,
                            "is_burnout": outcome.is_burnout_event
                            or outcome.overall_outcome == "burnout",
                            "probability": pred.predicted_probability,
                            "risk_level": pred.predicted_risk_level,
                            "actual_outcome": outcome.overall_outcome,
                        }
                    )
                    break

        return matched

    def _calculate_metrics(
        self, y_true: np.ndarray, y_pred_class: np.ndarray, y_pred_proba: np.ndarray
    ) -> ValidationMetrics:
        """Calculate validation metrics using sklearn"""
        # Handle edge cases
        if len(np.unique(y_true)) < 2:
            logger.warning("Only one class present in y_true - ROC AUC will be None")

        metrics = ValidationMetrics(
            accuracy=accuracy_score(y_true, y_pred_class),
            precision=precision_score(y_true, y_pred_class, zero_division=0),
            recall=recall_score(y_true, y_pred_class, zero_division=0),
            f1_score=f1_score(y_true, y_pred_class, zero_division=0),
            roc_auc=(
                roc_auc_score(y_true, y_pred_proba)
                if len(np.unique(y_true)) > 1
                else None
            ),
            brier_score=brier_score_loss(y_true, y_pred_proba),
            calibration_error=0.0,  # Will be calculated separately
            total_predictions=len(y_true),
            actual_burnouts=int(sum(y_true)),
            true_positives=int(np.sum((y_pred_class == 1) & (y_true == 1))),
            false_positives=int(np.sum((y_pred_class == 1) & (y_true == 0))),
            false_negatives=int(np.sum((y_pred_class == 0) & (y_true == 1))),
        )

        return metrics

    def _analyze_calibration(self, records: List[Dict]) -> CalibrationResult:
        """
        Analyze calibration: do predicted probabilities match observed frequencies?

        Creates probability bins and compares predicted vs actual frequencies
        """
        # Create bins
        bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        calibration_data = []

        for bin_low, bin_high in bins:
            bin_records = [r for r in records if bin_low <= r["probability"] < bin_high]

            if bin_records:
                avg_predicted_prob = np.mean([r["probability"] for r in bin_records])
                actual_frequency = np.mean(
                    [1 if r["is_burnout"] else 0 for r in bin_records]
                )

                calibration_data.append(
                    {
                        "bin": f"{bin_low:.1f}-{bin_high:.1f}",
                        "predicted_probability": float(avg_predicted_prob),
                        "actual_frequency": float(actual_frequency),
                        "sample_size": len(bin_records),
                        "calibration_error": abs(avg_predicted_prob - actual_frequency),
                    }
                )

        # Overall calibration metrics
        if calibration_data:
            calibration_errors = [d["calibration_error"] for d in calibration_data]
            mean_calibration_error = np.mean(calibration_errors)
            is_well_calibrated = mean_calibration_error < 0.1
        else:
            mean_calibration_error = 0.0
            is_well_calibrated = True

        return CalibrationResult(
            bin_data=calibration_data,
            mean_calibration_error=float(mean_calibration_error),
            is_well_calibrated=is_well_calibrated,
        )

    def _generate_validation_recommendations(
        self, metrics: ValidationMetrics, calibration: CalibrationResult
    ) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if metrics.accuracy < 0.7:
            recommendations.append(
                "Accuracy below 70% - consider model retraining with more data"
            )

        if metrics.precision < 0.6:
            recommendations.append(
                "Low precision - model may be over-predicting burnout (false positives)"
            )

        if metrics.recall < 0.6:
            recommendations.append(
                "Low recall - model may be missing actual burnout cases (false negatives)"
            )

        if not calibration.is_well_calibrated:
            recommendations.append(
                "Poor calibration - predicted probabilities don't match observed frequencies"
            )

        if metrics.roc_auc and metrics.roc_auc < 0.75:
            recommendations.append(
                "ROC AUC below 0.75 - model discrimination needs improvement"
            )

        if metrics.false_negatives > 0:
            recommendations.append(
                f"Missed {metrics.false_negatives} burnout cases - critical for safety"
            )

        if len(recommendations) == 0:
            recommendations.append(
                "Model performance is acceptable - continue monitoring"
            )

        return recommendations


class ModelPerformanceMonitor:
    """
    Continuous monitoring of model performance over time

    Tracks:
    - Prediction accuracy over time
    - Calibration drift
    - Performance degradation
    - Data distribution changes
    """

    def __init__(self):
        self.performance_history: List[Dict] = []

    def record_performance(
        self, model_type: ModelType, metrics: ValidationMetrics, timestamp: datetime
    ):
        """Record performance metrics for a model"""
        self.performance_history.append(
            {
                "model_type": model_type.value,
                "timestamp": timestamp.isoformat(),
                "metrics": metrics.to_dict(),
            }
        )

    def get_performance_trend(
        self, model_type: ModelType, days: int = 30
    ) -> List[Dict]:
        """
        Get performance trend for a model over recent days

        Args:
            model_type: Model to query
            days: Number of days to look back

        Returns:
            List of performance metrics over time
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        trend = [
            record
            for record in self.performance_history
            if record["model_type"] == model_type.value
            and datetime.fromisoformat(record["timestamp"]) >= cutoff_date
        ]

        return trend

    def detect_performance_degradation(
        self, model_type: ModelType, threshold_pct: float = 10.0
    ) -> bool:
        """
        Detect if model performance has degraded

        Args:
            model_type: Model to check
            threshold_pct: Percentage degradation threshold

        Returns:
            True if performance degraded beyond threshold
        """
        trend = self.get_performance_trend(model_type, days=7)

        if len(trend) < 2:
            return False

        # Compare latest to earliest
        latest_accuracy = trend[-1]["metrics"]["accuracy"]
        earliest_accuracy = trend[0]["metrics"]["accuracy"]

        degradation = (earliest_accuracy - latest_accuracy) / earliest_accuracy * 100

        return degradation > threshold_pct


# Convenience functions
def create_ab_test(
    name: str,
    control_model: ModelType,
    treatment_model: ModelType,
    duration_days: int = 28,
) -> ABTestAnalyzer:
    """
    Create an A/B test with standard configuration

    Args:
        name: Test name
        control_model: Control model type
        treatment_model: Treatment model type
        duration_days: Test duration in days

    Returns:
        Configured ABTestAnalyzer
    """
    config = ABTestConfig(
        name=name,
        control_model=control_model,
        treatment_model=treatment_model,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=duration_days),
        sample_size_per_group=100,  # Default, can be adjusted
    )

    return ABTestAnalyzer(config)
