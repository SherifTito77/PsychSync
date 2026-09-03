"""
SLO/SLI Tracking Implementation

Service Level Objectives (SLOs) and Service Level Indicators (SLIs) are critical for:
1. Measuring reliability
2. Setting expectations with users
3. Driving engineering priorities
4. Calculating error budgets

This module provides SLO/SLI tracking for the PsychSync API.

CRITICAL: Without SLO tracking, you're flying blind - you don't know if
you're meeting your reliability targets or how much "error budget" you have.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


# ============================================================================
# SLO DEFINITIONS
# ============================================================================


class SLO(Enum):
    """
    Service Level Objectives for PsychSync API

    These are the reliability commitments we make to users.
    """

    # API Availability (uptime)
    API_AVAILABILITY = 0.999  # 99.9% = 8.76 hours downtime/year
    API_AVAILABILITY_FREE = 0.99  # 99% = 3.65 days downtime/year

    # API Performance (latency)
    API_P50_LATENCY = 0.1  # 100ms
    API_P95_LATENCY = 0.5  # 500ms
    API_P99_LATENCY = 1.0  # 1000ms

    # Error Rate
    ERROR_RATE = 0.01  # 1% error rate
    ERROR_RATE_CRITICAL = 0.001  # 0.1% for critical endpoints

    # Data Durability
    DATA_DURABILITY = 0.999999999  # 11 nines (industry standard)

    # Data Freshness
    DATA_FRESHNESS = 60  # 60 seconds max staleness


# ============================================================================
# SLI TRACKING
# ============================================================================


class SLITracker:
    """
    Service Level Indicator tracker

    Tracks SLIs over rolling windows to calculate SLO compliance.
    """

    def __init__(
        self,
        slo: SLO,
        window_minutes: int = 30,
        granular_minutes: int = 1,
    ):
        """
        Initialize SLI tracker

        Args:
            slo: Service Level Objective to track
            window_minutes: Rolling window size (default: 30 minutes)
            granular_minutes: Granularity of measurements (default: 1 minute)
        """
        self.slo = slo
        self.window_minutes = window_minutes
        self.granular_minutes = granular_minutes
        self.measurements: list[tuple[datetime, bool]] = []

        # Prometheus metrics
        from prometheus_client import REGISTRY

        self.sli_compliance = None
        try:
            self.sli_compliance = Gauge(
                "slo_compliance",
                f"SLO compliance for {slo.name}",
                ["slo_name"],
                namespace="psychsync",
            )
        except ValueError:
            self.sli_compliance = REGISTRY._names_to_collectors[
                "psychsync_slo_compliance"
            ]

        self.sli_measurement_count = None
        try:
            self.sli_measurement_count = Counter(
                "sli_measurement_count",
                "Total SLI measurements",
                ["slo_name", "result"],
                namespace="psychsync",
            )
        except ValueError:
            self.sli_measurement_count = REGISTRY._names_to_collectors[
                "psychsync_sli_measurement_count"
            ]

        logger.info(
            f"✅ SLI tracker initialized for {slo.name} "
            f"(window: {window_minutes}m, granularity: {granular_minutes}m)"
        )

    def record(self, success: bool, timestamp: datetime | None = None) -> None:
        """
        Record an SLI measurement

        Args:
            success: Whether the measurement met the SLO
            timestamp: When the measurement occurred (default: now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        self.measurements.append((timestamp, success))

        # Clean old measurements outside window
        self._cleanup_old_measurements()

        # Update compliance metrics
        self._update_compliance()

        # Track measurement count
        result_str = "success" if success else "failure"
        self.sli_measurement_count.labels(
            slo_name=self.slo.name, result=result_str
        ).inc()

    def _cleanup_old_measurements(self) -> None:
        """Remove measurements outside the rolling window"""
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        self.measurements = [
            (ts, success) for ts, success in self.measurements if ts > cutoff
        ]

    def _update_compliance(self) -> None:
        """Calculate and update SLO compliance"""
        if not self.measurements:
            return

        # Calculate success rate
        successful = sum(1 for _, success in self.measurements if success)
        total = len(self.measurements)
        compliance_rate = successful / total if total > 0 else 0

        # Update gauge
        self.sli_compliance.labels(slo_name=self.slo.name).set(compliance_rate)

    def get_compliance(self) -> float:
        """
        Get current SLO compliance rate

        Returns:
            Compliance rate (0.0 to 1.0)
        """
        if not self.measurements:
            return 1.0  # No data = assume compliant

        successful = sum(1 for _, success in self.measurements if success)
        total = len(self.measurements)
        return successful / total if total > 0 else 0

    def get_error_budget_remaining(self) -> float:
        """
        Calculate remaining error budget

        Error budget = 1 - (actual failure rate / allowed failure rate)

        Returns:
            Error budget remaining (0.0 to 1.0, negative = over budget)
        """
        compliance = self.get_compliance()

        # Get SLO target
        target = self.slo.value

        # Calculate error budget
        if compliance >= target:
            # Under error budget (good!)
            error_rate = 1 - compliance
            allowed_error_rate = 1 - target
            budget_remaining = 1 - (error_rate / allowed_error_rate)
            return budget_remaining
        else:
            # Over error budget (bad!)
            error_rate = 1 - compliance
            allowed_error_rate = 1 - target
            budget_remaining = 1 - (error_rate / allowed_error_rate)
            return budget_remaining

    def is_met(self) -> bool:
        """
        Check if SLO is currently being met

        Returns:
            True if SLO is met, False otherwise
        """
        return self.get_compliance() >= self.slo.value


# ============================================================================
# PRECONFIGURED TRACKERS
# ============================================================================

# API Availability tracker
api_availability_tracker = SLITracker(
    slo=SLO.API_AVAILABILITY,
    window_minutes=30,
)

# API Latency trackers
api_p50_latency_tracker = SLITracker(
    slo=SLO.API_P50_LATENCY,
    window_minutes=30,
)

api_p95_latency_tracker = SLITracker(
    slo=SLO.API_P95_LATENCY,
    window_minutes=30,
)

api_p99_latency_tracker = SLITracker(
    slo=SLO.API_P99_LATENCY,
    window_minutes=30,
)

# Error rate tracker
error_rate_tracker = SLITracker(
    slo=SLO.ERROR_RATE,
    window_minutes=30,
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def track_api_request(
    status_code: int,
    duration_ms: float,
    is_critical: bool = False,
) -> None:
    """
    Track API request against SLOs

    Args:
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        is_critical: Whether this is a critical endpoint
    """
    # Track availability (2xx, 3xx = success)
    success_availability = 200 <= status_code < 400
    api_availability_tracker.record(success_availability)

    # Track latency
    success_p50 = duration_ms <= SLO.API_P50_LATENCY.value * 1000
    success_p95 = duration_ms <= SLO.API_P95_LATENCY.value * 1000
    success_p99 = duration_ms <= SLO.API_P99_LATENCY.value * 1000

    api_p50_latency_tracker.record(success_p50)
    api_p95_latency_tracker.record(success_p95)
    api_p99_latency_tracker.record(success_p99)

    # Track error rate
    target_error_rate = (
        SLO.ERROR_RATE_CRITICAL.value if is_critical else SLO.ERROR_RATE.value
    )
    actual_error = status_code >= 500
    success_error = not actual_error

    error_rate_tracker.record(success_error)


def get_slo_status() -> dict[str, Any]:
    """
    Get current SLO status for all trackers

    Returns:
        Dictionary with SLO status information
    """
    return {
        "api_availability": {
            "slo_target": SLO.API_AVAILABILITY.value,
            "current_compliance": api_availability_tracker.get_compliance(),
            "error_budget_remaining": api_availability_tracker.get_error_budget_remaining(),
            "is_met": api_availability_tracker.is_met(),
        },
        "api_latency_p50": {
            "slo_target_ms": SLO.API_P50_LATENCY.value * 1000,
            "current_compliance": api_p50_latency_tracker.get_compliance(),
            "is_met": api_p50_latency_tracker.is_met(),
        },
        "api_latency_p95": {
            "slo_target_ms": SLO.API_P95_LATENCY.value * 1000,
            "current_compliance": api_p95_latency_tracker.get_compliance(),
            "is_met": api_p95_latency_tracker.is_met(),
        },
        "api_latency_p99": {
            "slo_target_ms": SLO.API_P99_LATENCY.value * 1000,
            "current_compliance": api_p99_latency_tracker.get_compliance(),
            "is_met": api_p99_latency_tracker.is_met(),
        },
        "error_rate": {
            "slo_target": SLO.ERROR_RATE.value,
            "current_compliance": error_rate_tracker.get_compliance(),
            "error_budget_remaining": error_rate_tracker.get_error_budget_remaining(),
            "is_met": error_rate_tracker.is_met(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# ALERTING ON SLO VIOLATIONS
# ============================================================================


class SLOAlertManager:
    """
    Manages SLO violation alerts

    Provides burn rate calculations and alerts when error budget is being consumed too quickly.
    """

    def __init__(self, burn_rate_threshold: float = 2.0):
        """
        Initialize alert manager

        Args:
            burn_rate_threshold: Alert if burn rate exceeds this (default: 2x)
        """
        self.burn_rate_threshold = burn_rate_threshold
        self.logger = logging.getLogger(__name__)

    def check_burn_rate(self, tracker: SLITracker) -> float:
        """
        Calculate current burn rate

        Burn rate = (actual error rate) / (allowed error rate)
        Burn rate of 1.0 = exactly consuming error budget as expected
        Burn rate > 1.0 = consuming error budget too fast

        Args:
            tracker: SLI tracker to check

        Returns:
            Current burn rate
        """
        compliance = tracker.get_compliance()
        target = tracker.slo.value

        if compliance >= target:
            return 0.0  # Not burning error budget

        actual_error_rate = 1 - compliance
        allowed_error_rate = 1 - target

        if allowed_error_rate == 0:
            return float("inf")  # Division by zero = infinite burn rate

        burn_rate = actual_error_rate / allowed_error_rate
        return burn_rate

    def check_alert_conditions(self) -> list[str]:
        """
        Check all SLO trackers for alert conditions

        Returns:
            List of alert messages
        """
        alerts = []

        # Check availability
        if not api_availability_tracker.is_met():
            burn_rate = self.check_burn_rate(api_availability_tracker)
            if burn_rate > self.burn_rate_threshold:
                alerts.append(
                    f"🚨 CRITICAL: API availability SLO violated! "
                    f"Current: {api_availability_tracker.get_compliance():.3%}, "
                    f"Burn rate: {burn_rate:.2f}x"
                )

        # Check latency
        if not api_p95_latency_tracker.is_met():
            alerts.append(
                f"⚠️  WARNING: API P95 latency SLO violated! "
                f"Current: {api_p95_latency_tracker.get_compliance():.3%}"
            )

        # Check error rate
        if not error_rate_tracker.is_met():
            burn_rate = self.check_burn_rate(error_rate_tracker)
            if burn_rate > self.burn_rate_threshold:
                alerts.append(
                    f"🚨 CRITICAL: Error rate SLO violated! "
                    f"Current: {error_rate_tracker.get_compliance():.3%}, "
                    f"Burn rate: {burn_rate:.2f}x"
                )

        return alerts


# ============================================================================
# DECORATOR FOR TRACKING
# ============================================================================


def track_slo(
    slo_tracker: SLITracker,
    success_criteria: Callable[[Any], bool] = lambda x: True,
):
    """
    Decorator to automatically track function calls against SLO

    Usage:

    ```python
    @track_slo(api_availability_tracker)
    async def my_api_function():
        # If this raises an exception, it's recorded as failure
        # If it returns normally, it's recorded as success
        pass
    ```

    Args:
        slo_tracker: SLI tracker to use
        success_criteria: Function to determine success (default: no exception = success)
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                slo_tracker.record(True)
                return result
            except Exception:
                slo_tracker.record(False)
                raise

        return wrapper

    return decorator


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SLO",
    "SLITracker",
    "api_availability_tracker",
    "api_p50_latency_tracker",
    "api_p95_latency_tracker",
    "api_p99_latency_tracker",
    "error_rate_tracker",
    "track_api_request",
    "get_slo_status",
    "SLOAlertManager",
    "track_slo",
]
