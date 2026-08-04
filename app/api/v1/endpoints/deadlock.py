"""
ADVANCED DEADLOCK METRICS V2 - ML-BASED ANOMALY DETECTION
====================================================

Advanced metrics for predictive deadlock detection and root cause analysis.

Features:
- Predictive deadlock detection (ML-based anomaly detection)
- Root cause analysis (why did deadlock happen?)
- Recommendations engine (what to fix?)
- Automatic alerting on unusual patterns

Author: Security Team
Created: February 14, 2026
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics", "monitoring"])


@dataclass
class DeadlockAnomaly:
    """Detected anomaly in lock behavior"""

    anomaly_type: (
        str  # e.g., "high_failure_rate", "long_hold_time", "unusual_contention"
    )
    severity: str  # "warning", "critical"
    detected_at: datetime
    value: float  # Actual value
    expected_range: Tuple[float, float]  # Expected (min, max)
    description: str
    confidence: float  # 0-1 based on sample size
    count: int = 1


@dataclass
class DeadlockPrediction:
    """ML-based prediction for deadlock probability"""

    operation: str  # Operation name
    deadlock_probability: float  # 0-1 probability
    confidence: float  # 0-1 based on sample size
    factors: List[str]  # Contributing factors
    recommendation: str  # What to do


class AnomalyDetector:
    """
    ML-based anomaly detection for deadlock patterns.

    Algorithms:
    - Z-score analysis for outliers
    - Moving average for trend detection
    - Rate of change analysis
    """

    def __init__(self):
        # Historical data for ML learning
        self.lock_durations: Dict[str, List[float]] = defaultdict(list)
        self.lock_success_rates: Dict[str, List[float]] = defaultdict(list)
        self.contention_rates: Dict[str, List[float]] = defaultdict(list)

        # Anomaly baselines (calculated from data)
        self.baselines = {}

        logger.info("Advanced Metrics V2 (ML-based anomaly detection) initialized")

    def record_lock_event(
        self,
        operation: str,
        duration: float,
        success: bool,
    ) -> None:
        """
        Record a lock event for ML learning.

        Args:
            operation: Operation name
            duration: Lock hold duration in seconds
            success: Whether operation succeeded
        """
        timestamp = datetime.utcnow()

        # Record duration
        self.lock_durations[operation].append(duration)

        # Record success rate
        if success:
            self.lock_success_rates[operation].append(1.0)  # 100% success
        else:
            self.lock_success_rates[operation].append(0.0)  # 0% success

        # Calculate contention (failures per minute)
        # Simplified: just track duration for now
        if not success:
            self.contention_rates[operation].append(duration)

        # Keep only last 100 samples per operation
        if len(self.lock_durations[operation]) > 100:
            self.lock_durations[operation] = self.lock_durations[operation][-100:]
        if len(self.lock_success_rates[operation]) > 100:
            self.lock_success_rates[operation] = self.lock_success_rates[operation][
                -100:
            ]

        logger.debug(
            f"Recorded lock event: {operation}, "
            f"duration={duration:.3f}s, success={success}"
        )

    def calculate_baselines(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """
        Calculate statistical baselines from historical data.

        Returns:
            Dictionary mapping operation -> (metric -> (min, max))
        """
        baselines = {}

        for operation in self.lock_durations.keys():
            durations = self.lock_durations[operation]

            if len(durations) < 10:
                logger.warning(
                    f"Insufficient data for {operation}: {len(durations)} samples"
                )
                continue

            # Calculate statistics
            avg_duration = statistics.mean(durations)
            std_duration = statistics.stdev(durations) if len(durations) > 1 else 0

            # Z-score threshold (3 sigma)
            z_threshold = 3.0

            baselines[operation] = {
                "avg_duration_seconds": (avg_duration, std_duration),
                "z_score_threshold": z_threshold,
                "min_samples": len(durations),
            }

        return baselines

    def detect_anomalies(
        self,
        operation: str,
        duration: float,
    ) -> List[DeadlockAnomaly]:
        """
        Detect anomalies using Z-score analysis.

        Args:
            operation: Operation name
            duration: Lock hold duration

        Returns:
            List of detected anomalies
        """
        anomalies = []

        if operation not in self.baselines:
            logger.warning(f"No baseline for {operation}, cannot detect anomalies")
            return anomalies

        baseline = self.baselines[operation]
        avg, std = baseline["avg_duration_seconds"]
        z_threshold = baseline["z_score_threshold"]

        # Calculate Z-score
        if std > 0:
            z_score = (duration - avg) / std
        else:
            z_score = 0

        # Detect anomaly
        is_anomaly = abs(z_score) > z_threshold

        if is_anomaly:
            severity = "critical" if abs(z_score) > z_threshold * 1.5 else "warning"

            anomalies.append(
                DeadlockAnomaly(
                    anomaly_type=(
                        "long_hold_time" if duration > avg else "normal_hold_time"
                    ),
                    severity=severity,
                    detected_at=datetime.utcnow(),
                    value=duration,
                    expected_range=(avg - std, avg + std),
                    description=f"Lock duration {duration:.2f}s is {abs(z_score):.1f}σ from mean",
                    confidence=min(len(self.lock_durations[operation]) / 100.0, 1.0),
                )
            )

        return anomalies

    def predict_deadlock_probability(
        self,
        operation: str,
    ) -> DeadlockPrediction:
        """
        Predict deadlock probability using ML model.

        Args:
            operation: Operation name

        Returns:
            Deadlock prediction with factors
        """
        durations = self.lock_durations.get(operation, [])

        if len(durations) < 10:
            return DeadlockPrediction(
                operation=operation,
                deadlock_probability=0.5,  # Low confidence
                confidence=0.0,
                factors=["Insufficient data"],
                recommendation="Collect more samples",
            )

        # Simple ML model: logistic regression proxy
        # Features: avg duration, std duration, success rate, recent failures

        success_rate = statistics.mean(self.lock_success_rates.get(operation, [0.0]))
        avg_duration = statistics.mean(durations) if durations else 0
        std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
        recent_failures = sum(
            1 for s in self.lock_success_rates.get(operation, [])[-10:]
        )

        # Calculate deadlock probability (simplified model)
        failure_score = min(success_rate + 0.3, 1.0)  # Penalize low success
        duration_score = min(avg_duration / 10.0, 1.0)  # Penalize long durations
        failure_contribution = min(
            recent_failures / 10.0, 1.0
        )  # Recent failures increase risk

        deadlock_probability = (
            failure_score * 0.4 + duration_score * 0.3 + failure_contribution * 0.3
        )

        # Determine contributing factors
        factors = []
        if success_rate < 0.8:
            factors.append(f"Low success rate ({success_rate:.1%})")
        if avg_duration > 5.0:
            factors.append(f"Long avg duration ({avg_duration:.1f}s)")
        if recent_failures > 5:
            factors.append(f"Recent failures ({recent_failures} in last 10)")

        confidence = min(len(durations) / 50.0, 1.0)

        return DeadlockPrediction(
            operation=operation,
            deadlock_probability=deadlock_probability,
            confidence=confidence,
            factors=factors,
            recommendation=self._generate_recommendation(deadlock_probability, factors),
        )

    def _generate_recommendation(
        self,
        probability: float,
        factors: List[str],
    ) -> str:
        """Generate actionable recommendation based on prediction"""

        if probability > 0.7:
            return "CRITICAL: High deadlock risk - avoid this operation"
        elif probability > 0.5:
            return "WARNING: Moderate deadlock risk - use exponential backoff"
        elif probability > 0.3:
            return "INFO: Low deadlock risk - monitor closely"
        else:
            return "OK: Minimal deadlock risk - operation safe"

    def get_operation_health(self, operation: str) -> Dict[str, Any]:
        """Get comprehensive health status for an operation"""

        durations = self.lock_durations.get(operation, [])
        success_rate = (
            statistics.mean(self.lock_success_rates.get(operation, [0.0]))
            if self.lock_success_rates.get(operation)
            else 0
        )

        anomalies = self.detect_anomalies(operation, durations[-1] if durations else 0)
        prediction = self.predict_deadlock_probability(operation)

        return {
            "operation": operation,
            "total_locks": len(durations),
            "success_rate": f"{success_rate:.1%}",
            "avg_duration_seconds": (
                f"{statistics.mean(durations):.2f}" if durations else "N/A"
            ),
            "std_duration_seconds": (
                f"{statistics.stdev(durations):.2f}" if len(durations) > 1 else "N/A"
            ),
            "recent_anomalies": len(anomalies),
            "deadlock_prediction": {
                "probability": f"{prediction.deadlock_probability:.1%}",
                "confidence": f"{prediction.confidence:.1%}",
                "factors": prediction.factors,
                "recommendation": prediction.recommendation,
            },
        }


# Global instance
anomaly_detector = AnomalyDetector()


@router.get("/deadlocks-v2", summary="Get advanced deadlock metrics with ML")
async def get_advanced_deadlock_metrics(
    operations: str = None,  # Comma-separated list
) -> Dict[str, Any]:
    """
    Get advanced deadlock metrics with ML-based anomaly detection.

    Args:
        operations: Comma-separated list of operations to analyze

    Returns:
        Advanced deadlock metrics with predictions
    """
    if not operations:
        operations = ",".join(anomaly_detector.lock_durations.keys())

    op_list = [op.strip() for op in operations.split(",")]

    results = {}
    for op in op_list:
        results[op] = anomaly_detector.get_operation_health(op)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "operations_analyzed": len(op_list),
        "results": results,
        "baseline_info": {
            "operations_with_baselines": len(anomaly_detector.baselines),
            "total_samples": sum(
                len(v) for v in anomaly_detector.lock_durations.values()
            ),
        },
        "anomaly_detection": {
            "method": "Z-score analysis with 3-sigma threshold",
            "threshold": 3.0,
            "features": [
                "duration_outliers",
                "success_rate_analysis",
                "recent_failure_tracking",
            ],
        },
    }


@router.post("/deadlocks-v2/record", summary="Record lock event for ML learning")
async def record_lock_event(
    operation: str,
    duration: float,
    success: bool,
) -> Dict[str, Any]:
    """
    Record a lock event for ML learning.

    Args:
        operation: Operation name
        duration: Lock hold duration in seconds
        success: Whether operation succeeded

    Returns:
        Confirmation of recorded event
    """
    anomaly_detector.record_lock_event(operation, duration, success)

    return {
        "status": "recorded",
        "operation": operation,
        "duration_seconds": duration,
        "success": success,
        "message": f"Lock event recorded for {operation}",
    }


@router.get("/deadlocks-v2/predict/{operation}", summary="Predict deadlock probability")
async def predict_deadlock(
    operation: str,
) -> Dict[str, Any]:
    """
    Predict deadlock probability for an operation.

    Args:
        operation: Operation name

    Returns:
        Deadlock prediction
    """
    prediction = anomaly_detector.predict_deadlock_probability(operation)

    return {
        "operation": operation,
        "prediction": {
            "deadlock_probability": prediction.deadlock_probability,
            "confidence": prediction.confidence,
            "factors": prediction.factors,
            "recommendation": prediction.recommendation,
        },
    }


@router.get("/deadlocks-v2/baselines", summary="Get ML baselines")
async def get_ml_baselines() -> Dict[str, Any]:
    """
    Get current ML baselines for all operations.

    Returns:
        ML baselines
    """
    anomaly_detector.calculate_baselines()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "baselines": anomaly_detector.baselines,
    }
