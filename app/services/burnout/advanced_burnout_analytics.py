"""
Advanced Burnout Analytics - Enterprise-Safe Behavioral Scoring

Implements sophisticated behavioral metrics for burnout prediction:
- Baseline Normalization (personal Z-scores)
- Cognitive Load Score (mental strain)
- Emotional Stress Score (behavioral NLP)
- Fatigue Accumulation Score (sports science)
- Psychological Risk Index (main product score)
- Team Friction Index (system toxicity)
- Self-Report Calibration (optional)

Enterprise-safe features:
- No medical data
- No body measurements
- No psychological labeling
- Only risk signals from behavior
- Probabilistic, not diagnostic

Author: PsychSync Engineering Team
Version: 3.0
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BaselineMetrics:
    """User's 30-day baseline statistics"""

    mean: float
    std: float
    count: int


@dataclass
class CognitiveLoadInput:
    """Inputs for Cognitive Load Score calculation"""

    task_velocity_z: float  # Z-score of task completion rate
    context_switch_z: float  # Z-score of context switches
    meeting_density_z: float  # Z-score of meeting hours


@dataclass
class EmotionalStressInput:
    """Inputs for Emotional Stress Score calculation"""

    sentiment_shift_z: float  # Z-score of negative sentiment shift
    escalation_z: float  # Z-score of message escalation/ sharpness
    rework_z: float  # Z-score of error rework frequency


@dataclass
class FatigueInput:
    """Inputs for Fatigue Accumulation Score calculation"""

    acute_load_7d: float  # Weighted load (last 7 days)
    chronic_load_28d: float  # Weighted load (last 28 days)


@dataclass
class PsychologicalRiskResult:
    """Output of Psychological Risk Index calculation"""

    pri_score: float  # 0-100 Psychological Risk Index
    cls_score: float  # 0-100 Cognitive Load Score
    ess_score: float  # 0-100 Emotional Stress Score
    fas_score: float  # 0-100 Fatigue Accumulation Score
    risk_level: str  # safe, watch, intervention, high_risk
    confidence: str  # low, medium, high


@dataclass
class TeamFrictionResult:
    """Output of Team Friction Index calculation"""

    tfi_score: float  # 0-100 Team Friction Index
    tfi_smoothed: float  # 14-day EMA smoothed
    trend: str  # improving, stable, worsening
    severity: str  # low, medium, high, critical


class AdvancedBurnoutAnalyzer:
    """
    Advanced burnout prediction using behavioral analytics

    Uses baseline-normalized Z-scores to remove bias between
    fast/slow workers. All scores are probabilistic, not diagnostic.
    """

    # Weights for Cognitive Load Score
    CLS_WEIGHTS = {"velocity": 0.4, "context": 0.35, "meetings": 0.25}

    # Weights for Emotional Stress Score
    ESS_WEIGHTS = {"sentiment": 0.4, "escalation": 0.35, "rework": 0.25}

    # Weights for Psychological Risk Index
    PRI_WEIGHTS = {"cls": 0.35, "ess": 0.35, "fas": 0.30}

    def __init__(self):
        self.baselines: Dict[str, BaselineMetrics] = {}

    def calculate_z_score(
        self, value_today: float, mean_30d: float, std_30d: float
    ) -> float:
        """
        Calculate Z-score relative to personal 30-day baseline

        Formula: Z = (x_today - μ_30d) / σ_30d

        This removes bias between fast/slow workers by measuring
        everything relative to the person's own normal.

        Args:
            value_today: Today's metric value
            mean_30d: Personal 30-day mean
            std_30d: Personal 30-day standard deviation

        Returns:
            Z-score (number of standard deviations from baseline)
        """
        if std_30d == 0 or std_30d < 0.001:
            return 0.0  # No variation, no deviation

        z_score = (value_today - mean_30d) / std_30d
        return z_score

    def calculate_cognitive_load_score(self, input_data: CognitiveLoadInput) -> float:
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

        Args:
            input_data: Cognitive load metrics (Z-scores)

        Returns:
            CLS score (0-100)
        """
        # Weighted combination of Z-scores
        cls_raw = (
            self.CLS_WEIGHTS["velocity"] * (-input_data.task_velocity_z)
            + self.CLS_WEIGHTS["context"]  # Negative: slower is bad
            * input_data.context_switch_z
            + self.CLS_WEIGHTS["meetings"] * input_data.meeting_density_z
        )

        # Normalize to 0-100
        cls_norm = np.clip(50 + 15 * cls_raw, 0, 100)

        return float(cls_norm)

    def calculate_emotional_stress_score(
        self, input_data: EmotionalStressInput
    ) -> float:
        """
        Calculate Emotional Stress Score (ESS)

        Derived from behavioral NLP, not feelings:
        - Negative sentiment shift (positive Z = more negative = bad)
        - Message escalation/sharpness (positive Z = sharper = bad)
        - Error rework frequency (positive Z = more rework = bad)

        Formula: ESS = w1*Z_sentiment + w2*Z_escalation + w3*Z_rework
        Normalized: ESS_norm = clip(50 + 20*ESS, 0, 100)

        Note: Sudden spikes matter more than absolute values.

        Args:
            input_data: Emotional stress metrics (Z-scores)

        Returns:
            ESS score (0-100)
        """
        # Weighted combination of Z-scores
        ess_raw = (
            self.ESS_WEIGHTS["sentiment"] * input_data.sentiment_shift_z
            + self.ESS_WEIGHTS["escalation"] * input_data.escalation_z
            + self.ESS_WEIGHTS["rework"] * input_data.rework_z
        )

        # Normalize to 0-100
        ess_norm = np.clip(50 + 20 * ess_raw, 0, 100)

        return float(ess_norm)

    def calculate_fatigue_accumulation_score(self, input_data: FatigueInput) -> float:
        """
        Calculate Fatigue Accumulation Score (FAS)

        Directly borrowed from sports science (acute/chronic workload ratio).

        Formula: FAS = Acute Load (7d) / Chronic Load (28d)

        Where load = weighted sum of:
        - Work hours
        - Task difficulty
        - Deadline pressure

        Interpretation:
        - < 0.8: Underloaded
        - 0.8-1.3: Optimal
        - 1.3: Fatigue risk
        - 1.6: Burnout zone

        Args:
            input_data: Fatigue metrics

        Returns:
            FAS score (0-100)
        """
        if input_data.chronic_load_28d == 0:
            return 0.0

        # Calculate acute/chronic ratio
        ac_ratio = input_data.acute_load_7d / input_data.chronic_load_28d

        # Convert ratio to 0-100 score
        # < 0.8 = underloaded (score decreases)
        # 0.8-1.3 = optimal (low score)
        # 1.3+ = risk zone (score increases rapidly)

        if ac_ratio < 0.8:
            # Underloaded - very low score
            fas_score = 20
        elif ac_ratio <= 1.3:
            # Optimal zone - low score
            fas_score = 25 + ((ac_ratio - 0.8) / 0.5) * 15
        else:
            # Risk zone - score increases rapidly
            excess = ac_ratio - 1.3
            fas_score = 40 + (excess / 0.3) * 30

        return float(np.clip(fas_score, 0, 100))

    def calculate_psychological_risk_index(
        self, cls_score: float, ess_score: float, fas_score: float
    ) -> PsychologicalRiskResult:
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

        Args:
            cls_score: Cognitive Load Score (0-100)
            ess_score: Emotional Stress Score (0-100)
            fas_score: Fatigue Accumulation Score (0-100)

        Returns:
            Psychological risk result with level and confidence
        """
        # Weighted combination
        pri_score = (
            self.PRI_WEIGHTS["cls"] * cls_score
            + self.PRI_WEIGHTS["ess"] * ess_score
            + self.PRI_WEIGHTS["fas"] * fas_score
        )

        # Determine risk level
        if pri_score < 40:
            risk_level = "safe"
            confidence = "high"
        elif pri_score < 60:
            risk_level = "watch"
            confidence = "medium"
        elif pri_score < 75:
            risk_level = "intervention"
            confidence = "medium"
        else:
            risk_level = "high_risk"
            confidence = "high"

        return PsychologicalRiskResult(
            pri_score=float(pri_score),
            cls_score=cls_score,
            ess_score=ess_score,
            fas_score=fas_score,
            risk_level=risk_level,
            confidence=confidence,
        )

    def calculate_team_friction_index(
        self,
        conflict_signals: int,
        escalations: int,
        coordination_failures: int,
        team_interactions: int,
        historical_tfi: Optional[List[float]] = None,
    ) -> TeamFrictionResult:
        """
        Calculate Team Friction Index (TFI)

        Measures system toxicity, not individuals.

        Formula: TFI = (Conflicts + Escalations + Failures) / Interactions
        Smoothed: TFI_smoothed = EMA_14d(TFI)

        Note: Rising TFI = culture issue, not "bad people".

        Args:
            conflict_signals: Number of conflict indicators
            escalations: Number of escalated messages
            coordination_failures: Number of failed handoffs/coordination issues
            team_interactions: Total team interactions
            historical_tfi: Historical TFI values for EMA smoothing

        Returns:
            Team friction result with trend and severity
        """
        if team_interactions == 0:
            tfi_raw = 0.0
        else:
            # Calculate raw TFI (0-1 range)
            tfi_raw = (
                conflict_signals + escalations + coordination_failures
            ) / team_interactions

        # Convert to 0-100 score
        tfi_score = tfi_raw * 100

        # Apply 14-day EMA smoothing if historical data available
        if historical_tfi and len(historical_tfi) > 0:
            alpha = 2 / (14 + 1)  # EMA smoothing factor for 14-day period
            tfi_smoothed = alpha * tfi_score + (1 - alpha) * historical_tfi[-1]
        else:
            tfi_smoothed = tfi_score

        # Determine trend
        if historical_tfi and len(historical_tfi) >= 7:
            recent_avg = np.mean(historical_tfi[-7:])
            if tfi_smoothed < recent_avg - 10:
                trend = "improving"
            elif tfi_smoothed > recent_avg + 10:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Determine severity
        if tfi_smoothed < 20:
            severity = "low"
        elif tfi_smoothed < 40:
            severity = "medium"
        elif tfi_smoothed < 60:
            severity = "high"
        else:
            severity = "critical"

        return TeamFrictionResult(
            tfi_score=float(np.clip(tfi_score, 0, 100)),
            tfi_smoothed=float(np.clip(tfi_smoothed, 0, 100)),
            trend=trend,
            severity=severity,
        )

    def calibrate_with_self_report(
        self,
        model_score: float,
        self_report_score: float,
        model_weight: float = 0.8,
        self_report_weight: float = 0.2,
    ) -> float:
        """
        Optional calibration with self-reports

        Like RPE (Rate of Perceived Exertion) in football:
        Adjusted Score = 0.8 * Model + 0.2 * Self Report

        This improves accuracy without depending on honesty.

        Args:
            model_score: Score from behavioral model
            self_report_score: User's self-reported score (0-100)
            model_weight: Weight for model score (default 0.8)
            self_report_weight: Weight for self-report (default 0.2)

        Returns:
            Calibrated score (0-100)
        """
        calibrated = model_weight * model_score + self_report_weight * self_report_score

        return float(np.clip(calibrated, 0, 100))


class BaselineManager:
    """
    Manages 30-day baseline statistics for users

    Tracks rolling means and standard deviations for
    personalized Z-score calculation.
    """

    def __init__(self):
        self.user_baselines: Dict[str, Dict[str, List[float]]] = {}

    def add_observation(
        self, user_id: str, metric_name: str, value: float, max_days: int = 30
    ) -> None:
        """
        Add a daily observation for baseline calculation

        Args:
            user_id: User identifier
            metric_name: Metric name (e.g., 'task_velocity', 'meeting_hours')
            value: Observed value
            max_days: Maximum days to keep (default 30)
        """
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = {}

        if metric_name not in self.user_baselines[user_id]:
            self.user_baselines[user_id][metric_name] = []

        # Add new observation
        self.user_baselines[user_id][metric_name].append(value)

        # Keep only last N days
        if len(self.user_baselines[user_id][metric_name]) > max_days:
            self.user_baselines[user_id][metric_name] = self.user_baselines[user_id][
                metric_name
            ][-max_days:]

    def get_baseline(self, user_id: str, metric_name: str) -> Optional[BaselineMetrics]:
        """
        Get baseline statistics for a user's metric

        Args:
            user_id: User identifier
            metric_name: Metric name

        Returns:
            Baseline metrics (mean, std, count) or None if insufficient data
        """
        if user_id not in self.user_baselines:
            return None

        if metric_name not in self.user_baselines[user_id]:
            return None

        values = self.user_baselines[user_id][metric_name]

        if len(values) < 5:  # Need minimum data points
            return None

        return BaselineMetrics(
            mean=float(np.mean(values)), std=float(np.std(values)), count=len(values)
        )

    def calculate_z_score(
        self, user_id: str, metric_name: str, value_today: float
    ) -> Optional[float]:
        """
        Calculate Z-score for today's value

        Args:
            user_id: User identifier
            metric_name: Metric name
            value_today: Today's metric value

        Returns:
            Z-score or None if baseline not available
        """
        baseline = self.get_baseline(user_id, metric_name)

        if baseline is None or baseline.std == 0:
            return None

        analyzer = AdvancedBurnoutAnalyzer()
        return analyzer.calculate_z_score(value_today, baseline.mean, baseline.std)
