"""
Early-Warning Engine - 14-Day Horizon Burnout Prediction

Implements sophisticated early-warning detection:
- Trend slope analysis (7-day momentum)
- Volatility acceleration (σ7d / σ30d)
- Early Warning Score (EW = 0.6×Slope + 0.4×Volatility)
- Trigger conditions: EW↑ AND PRI > 55 for ≥3 days

Fires 10-14 days before visible burnout

Framing: "System problem, not human blame"
Alert: "Sustained cognitive load trend detected. Recommend load redistribution."

Author: PsychSync Engineering Team
Version: 3.1
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EarlyWarningSignal:
    """Early warning signal result"""

    early_warning_score: float  # 0-100
    trend_slope: float  # 7-day slope
    volatility_ratio: float  # σ7d / σ30d
    is_triggered: bool  # Warning condition met
    trigger_reason: str  # Human-readable explanation
    days_above_threshold: int  # Consecutive days above threshold
    predicted_horizon_days: int  # Days until potential burnout
    recommended_actions: List[str]


@dataclass
class FeatureVector:
    """Derived features for ML/Bayesian models"""

    # Velocity features
    velocity_drop_pct: float  # % change vs baseline
    velocity_z_score: float

    # Variance features
    variance_spike: float  # σ7d / σ30d
    variance_z_score: float

    # Load features
    load_ratio: float  # acute7d / chronic28d
    load_z_score: float

    # Recovery features
    recovery_failure: bool  # no rebound after low-load day
    recovery_score: float

    # Escalation features
    escalation_density: float  # conflicts / interactions
    escalation_z_score: float

    # Trend features
    trend_7d: float  # 7-day slope
    trend_14d: float  # 14-day slope
    trend_30d: float  # 30-day slope

    # Composite scores
    cls_score: float  # Cognitive Load Score
    ess_score: float  # Emotional Stress Score
    fas_score: float  # Fatigue Accumulation Score
    pri_score: float  # Psychological Risk Index


class EarlyWarningEngine:
    """
    Early-Warning Engine for 14-day horizon burnout prediction

    Detects sustained adverse trends 10-14 days before visible burnout.

    Trigger Condition:
        EW↑ AND PRI > 55 for ≥3 consecutive days

    Alert Framing:
        "Sustained cognitive load trend detected.
         Recommend load redistribution."

    System problem, not human blame.
    """

    def __init__(self):
        self.historical_data: Dict[str, List[float]] = {}

    def calculate_trend_slope(
        self, score_history: List[float], window_days: int = 7
    ) -> float:
        """
        Calculate trend slope over N days

        Formula: Slope_7d = (S_today - S_7d_ago) / 7

        Positive = increasing risk
        Negative = decreasing risk

        Args:
            score_history: Historical scores (most recent last)
            window_days: Window size (default 7)

        Returns:
            Slope value (score change per day)
        """
        if len(score_history) < window_days:
            return 0.0

        today_score = score_history[-1]
        past_score = score_history[-window_days]

        slope = (today_score - past_score) / window_days
        return slope

    def calculate_volatility_ratio(
        self, score_history: List[float], short_window: int = 7, long_window: int = 30
    ) -> float:
        """
        Calculate volatility acceleration ratio

        Formula: Vol_ratio = σ_short / σ_long

        > 1.0 = Recent volatility higher than normal
        = 1.0 = Stable volatility
        < 1.0 = Volatility decreasing

        Args:
            score_history: Historical scores
            short_window: Short-term window (default 7 days)
            long_window: Long-term window (default 30 days)

        Returns:
            Volatility ratio
        """
        if len(score_history) < long_window:
            return 1.0

        short_scores = score_history[-short_window:]
        long_scores = score_history[-long_window:]

        short_std = np.std(short_scores) if len(short_scores) > 1 else 0
        long_std = np.std(long_scores) if len(long_scores) > 1 else 0.001

        if long_std == 0:
            return 1.0

        vol_ratio = short_std / long_std
        return vol_ratio

    def calculate_early_warning_score(
        self, trend_slope: float, volatility_ratio: float
    ) -> float:
        """
        Calculate Early Warning Score

        Formula: EW = 0.6×Slope_7d + 0.4×Vol_ratio

        Weights:
        - 60% trend slope (sustained direction matters most)
        - 40% volatility (instability warning)

        Args:
            trend_slope: 7-day trend slope
            volatility_ratio: σ7d / σ30d

        Returns:
            Early Warning Score (0-100)
        """
        # Normalize slope to 0-100 range
        # Assume slope of +2 per day = 100 (very bad)
        # Assume slope of -2 per day = 0 (very good)
        slope_normalized = np.clip((trend_slope + 2) / 4 * 100, 0, 100)

        # Normalize volatility ratio to 0-100
        # Assume ratio of 2.0 = 100 (very unstable)
        # Assume ratio of 0.5 = 0 (very stable)
        vol_normalized = np.clip((volatility_ratio - 0.5) / 1.5 * 100, 0, 100)

        # Weighted combination
        ew_score = 0.6 * slope_normalized + 0.4 * vol_normalized

        return float(ew_score)

    def check_trigger_conditions(
        self,
        pri_score: float,
        early_warning_score: float,
        consecutive_days: int,
        pri_threshold: float = 55.0,
        ew_threshold: float = 60.0,
    ) -> Tuple[bool, str]:
        """
        Check if early warning trigger conditions are met

        Trigger Condition:
            EW↑ (above threshold) AND
            PRI > 55 for ≥3 consecutive days

        This combination detects sustained risk, not temporary spikes.

        Args:
            pri_score: Current Psychological Risk Index
            early_warning_score: Current Early Warning Score
            consecutive_days: Days above threshold
            pri_threshold: PRI threshold (default 55)
            ew_threshold: EW threshold (default 60)

        Returns:
            (is_triggered, trigger_reason)
        """
        ew_above = early_warning_score > ew_threshold
        pri_above = pri_score > pri_threshold
        sustained = consecutive_days >= 3

        if ew_above and pri_above and sustained:
            return True, (
                f"Sustained risk detected: EW={early_warning_score:.1f} "
                f"(threshold {ew_threshold}), PRI={pri_score:.1f} "
                f"(threshold {pri_threshold}) for {consecutive_days} days"
            )

        if ew_above and pri_above:
            return False, (
                f"Elevated risk (EW={early_warning_score:.1f}, "
                f"PRI={pri_score:.1f}) but not yet sustained "
                f"({consecutive_days}/3 days)"
            )

        return False, "Risk levels within normal range"

    def generate_early_warning(
        self,
        user_id: str,
        pri_history: List[float],
        cls_history: Optional[List[float]] = None,
        ess_history: Optional[List[float]] = None,
        fas_history: Optional[List[float]] = None,
    ) -> EarlyWarningSignal:
        """
        Generate complete early warning signal

        Detects 10-14 days before visible burnout by analyzing:
        1. Trend slope (sustained direction)
        2. Volatility acceleration (instability)
        3. Sustained elevation (consecutive days)

        Args:
            user_id: User identifier
            pri_history: PRI scores (most recent last)
            cls_history: Optional CLS scores
            ess_history: Optional ESS scores
            fas_history: Optional FAS scores

        Returns:
            Early warning signal with actions
        """
        # Calculate trend slope
        trend_slope = self.calculate_trend_slope(pri_history, window_days=7)

        # Calculate volatility ratio
        vol_ratio = self.calculate_volatility_ratio(pri_history)

        # Calculate Early Warning Score
        ew_score = self.calculate_early_warning_score(trend_slope, vol_ratio)

        # Count consecutive days above threshold
        pri_threshold = 55.0
        consecutive_days = 0
        for score in reversed(pri_history):
            if score > pri_threshold:
                consecutive_days += 1
            else:
                break

        # Check trigger conditions
        is_triggered, trigger_reason = self.check_trigger_conditions(
            pri_score=pri_history[-1],
            early_warning_score=ew_score,
            consecutive_days=consecutive_days,
        )

        # Predict days until potential burnout
        if trend_slope > 0.5:
            # Slope of 0.5 per day = 14 days until score increases by 7 points
            predicted_horizon = int((100 - pri_history[-1]) / trend_slope)
            predicted_horizon = max(7, min(predicted_horizon, 30))
        else:
            predicted_horizon = 999  # Not on burnout trajectory

        # Generate recommended actions
        recommended_actions = self._generate_actions(
            is_triggered=is_triggered,
            trend_slope=trend_slope,
            vol_ratio=vol_ratio,
            pri_score=pri_history[-1],
            cls_history=cls_history,
            ess_history=ess_history,
            fas_history=fas_history,
        )

        return EarlyWarningSignal(
            early_warning_score=round(ew_score, 1),
            trend_slope=round(trend_slope, 2),
            volatility_ratio=round(vol_ratio, 2),
            is_triggered=is_triggered,
            trigger_reason=trigger_reason,
            days_above_threshold=consecutive_days,
            predicted_horizon_days=predicted_horizon,
            recommended_actions=recommended_actions,
        )

    def _generate_actions(
        self,
        is_triggered: bool,
        trend_slope: float,
        vol_ratio: float,
        pri_score: float,
        cls_history: Optional[List[float]] = None,
        ess_history: Optional[List[float]] = None,
        fas_history: Optional[List[float]] = None,
    ) -> List[str]:
        """
        Generate recommended actions

        Framing: "System problem, not human blame"
        Focus: Workload redistribution, not person fixing
        """
        actions = []

        if not is_triggered:
            actions.append("✅ All indicators stable. Continue current monitoring.")
            return actions

        # Primary alert (system-focused, not person-focused)
        if trend_slope > 0.3:
            actions.append(
                "⚠️ SUSTAINED COGNITIVE LOAD TREND DETECTED. "
                "Recommend: Review workload distribution and project timelines."
            )

        if vol_ratio > 1.3:
            actions.append(
                "⚠️ ELEVATED VOLATILITY DETECTED. "
                "Recommend: Stabilize work patterns and reduce context switching."
            )

        # Component-specific actions
        if cls_history and cls_history[-1] > 70:
            actions.append(
                "🟡 COGNITIVE LOAD: Reduce meeting density and task fragmentation. "
                "Consider focus blocks."
            )

        if ess_history and ess_history[-1] > 70:
            actions.append(
                "🟡 EMOTIONAL STRESS: Monitor team communication patterns. "
                "Review escalation frequency and conflict resolution."
            )

        if fas_history and fas_history[-1] > 60:
            actions.append(
                "🔴 FATIGUE ACCUMULATION: Recovery required. "
                "Mandatory time off or reduced workload recommended."
            )

        # Organizational actions (not individual)
        actions.append(
            "📊 MANAGER ACTION: Review team capacity and project deadlines. "
            "Consider workload redistribution across team."
        )

        actions.append(
            "🎯 HR ACTION: Check in on team dynamics and culture. "
            "Address systemic issues, not individual performance."
        )

        return actions


class FeatureEngineeringLayer:
    """
    Feature Engineering Layer for ML/Bayesian Models

    Creates derived features from raw metrics:
    - Velocity Drop: % change vs baseline
    - Variance Spike: σ7d / σ30d
    - Load Ratio: acute7d / chronic28d
    - Recovery Failure: no rebound after low-load day
    - Escalation Density: conflicts / interactions
    """

    def create_feature_vector(
        self,
        user_id: str,
        raw_metrics: Dict[str, float],
        historical_metrics: Dict[str, List[float]],
        baseline_stats: Dict[str, Dict[str, float]],  # {metric: {mean, std}}
    ) -> FeatureVector:
        """
        Create complete feature vector for ML/Bayesian inference

        Args:
            user_id: User identifier
            raw_metrics: Today's raw metric values
            historical_metrics: Historical values (last 30-90 days)
            baseline_stats: Personal baseline statistics

        Returns:
            FeatureVector with all derived features
        """
        # Extract histories
        pri_history = historical_metrics.get("pri", [])
        cls_history = historical_metrics.get("cls", [])
        ess_history = historical_metrics.get("ess", [])
        fas_history = historical_metrics.get("fas", [])

        # Calculate Z-scores using baseline normalization
        velocity_z = self._calculate_z_score(
            raw_metrics.get("task_velocity", 0), baseline_stats.get("task_velocity", {})
        )

        variance_spike = self._calculate_variance_spike(
            historical_metrics.get("task_velocity", [])
        )

        load_ratio = self._calculate_load_ratio(
            raw_metrics.get("acute_load_7d", 0), raw_metrics.get("chronic_load_28d", 1)
        )

        escalation_density = self._calculate_escalation_density(
            raw_metrics.get("conflicts", 0), raw_metrics.get("interactions", 1)
        )

        recovery_failure = self._check_recovery_failure(
            historical_metrics.get("work_hours", [])
        )

        # Calculate trends
        engine = EarlyWarningEngine()
        trend_7d = engine.calculate_trend_slope(pri_history, 7)
        trend_14d = engine.calculate_trend_slope(pri_history, 14)
        trend_30d = engine.calculate_trend_slope(pri_history, 30)

        return FeatureVector(
            # Velocity features
            velocity_drop_pct=raw_metrics.get("velocity_drop_pct", 0),
            velocity_z_score=velocity_z,
            # Variance features
            variance_spike=variance_spike,
            variance_z_score=0.0,  # Would need baseline variance
            # Load features
            load_ratio=load_ratio,
            load_z_score=self._calculate_z_score(
                load_ratio, baseline_stats.get("load_ratio", {})
            ),
            # Recovery features
            recovery_failure=recovery_failure,
            recovery_score=raw_metrics.get("recovery_score", 50),
            # Escalation features
            escalation_density=escalation_density,
            escalation_z_score=0.0,  # Would need baseline
            # Trend features
            trend_7d=trend_7d,
            trend_14d=trend_14d,
            trend_30d=trend_30d,
            # Composite scores
            cls_score=cls_history[-1] if cls_history else 0,
            ess_score=ess_history[-1] if ess_history else 0,
            fas_score=fas_history[-1] if fas_history else 0,
            pri_score=pri_history[-1] if pri_history else 0,
        )

    def _calculate_z_score(self, value: float, baseline: Dict[str, float]) -> float:
        """Calculate Z-score using baseline mean and std"""
        if "mean" not in baseline or "std" not in baseline:
            return 0.0

        mean = baseline["mean"]
        std = baseline.get("std", 1.0)

        if std == 0:
            return 0.0

        return (value - mean) / std

    def _calculate_variance_spike(
        self, history: List[float], short_window: int = 7, long_window: int = 30
    ) -> float:
        """Calculate variance spike ratio"""
        if len(history) < long_window:
            return 1.0

        short_std = np.std(history[-short_window:])
        long_std = np.std(history[-long_window:])

        if long_std == 0:
            return 1.0

        return short_std / long_std

    def _calculate_load_ratio(self, acute_load: float, chronic_load: float) -> float:
        """Calculate acute/chronic load ratio"""
        if chronic_load == 0:
            return 0.0
        return acute_load / chronic_load

    def _calculate_escalation_density(self, conflicts: int, interactions: int) -> float:
        """Calculate escalation density (conflicts per interaction)"""
        if interactions == 0:
            return 0.0
        return conflicts / interactions

    def _check_recovery_failure(self, work_hours_history: List[float]) -> bool:
        """
        Check for recovery failure (no rebound after low-load day)

        Pattern: Low-load day followed by high-load day without recovery
        """
        if len(work_hours_history) < 3:
            return False

        # Look for low-load day (< 40 hours)
        for i in range(len(work_hours_history) - 2):
            if work_hours_history[i] < 40:
                # Check next days for rebound
                next_day = work_hours_history[i + 1]
                if next_day > 50:  # High load without recovery
                    return True

        return False
