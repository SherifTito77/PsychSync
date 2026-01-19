"""
Retry Metrics and Monitoring Service

Tracks retry behavior across all external integrations to identify:
- Services with high retry rates (indicates instability)
- Services with consistently failing retries (indicates service degradation)
- Timeout patterns and circuit breaker activations
- Overall external service health

Features:
- Track retry counts per integration
- Calculate retry rates
- Alert on abnormal retry patterns
- Export metrics for monitoring systems (Prometheus, etc.)

Author: Security Team
Version: 1.0
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class RetryStatus(str, Enum):
    """Retry attempt status"""
    SUCCESS = "success"
    RETRY = "retry"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class RetryAttempt:
    """Individual retry attempt record"""
    integration: str
    endpoint: str
    attempt_number: int
    status: RetryStatus
    timestamp: datetime
    error_type: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class RetryMetrics:
    """Aggregated retry metrics for an integration"""
    integration: str
    total_attempts: int = 0
    successful_attempts: int = 0
    retry_attempts: int = 0
    failed_attempts: int = 0
    timeout_attempts: int = 0
    circuit_breaker_opens: int = 0
    avg_duration_ms: float = 0.0
    retry_rate: float = 0.0  # Percentage
    failure_rate: float = 0.0  # Percentage
    last_updated: datetime = field(default_factory=datetime.utcnow)


class RetryMetricsTracker:
    """
    Tracks and analyzes retry metrics across all external integrations.

    Usage:
        tracker = RetryMetricsTracker.get_instance()

        # Record a retry attempt
        await tracker.record_attempt(
            integration="openai",
            endpoint="https://api.openai.com/v1/chat/completions",
            attempt_number=2,
            status=RetryStatus.SUCCESS,
            duration_ms=1500.0
        )

        # Get metrics for an integration
        metrics = tracker.get_metrics("openai")

        # Get all integrations with high retry rates
        high_retry = tracker.get_high_retry_integrations(threshold=20.0)
    """

    _instance: Optional["RetryMetricsTracker"] = None

    def __init__(self):
        self.attempts: List[RetryAttempt] = []
        self.metrics_cache: Dict[str, RetryMetrics] = {}
        self._lock = asyncio.Lock()
        self._max_records = 10000  # Keep last 10k attempts
        self._retention_hours = 24  # Keep data for 24 hours

    @classmethod
    def get_instance(cls) -> "RetryMetricsTracker":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def record_attempt(
        self,
        integration: str,
        endpoint: str,
        attempt_number: int,
        status: RetryStatus,
        error_type: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """
        Record a retry attempt.

        Args:
            integration: Integration name (e.g., "openai", "fcm", "s3")
            endpoint: API endpoint being called
            attempt_number: Attempt number (1 = first attempt)
            status: Status of this attempt
            error_type: Type of error if failed
            duration_ms: Request duration in milliseconds
        """
        async with self._lock:
            attempt = RetryAttempt(
                integration=integration,
                endpoint=endpoint,
                attempt_number=attempt_number,
                status=status,
                timestamp=datetime.utcnow(),
                error_type=error_type,
                duration_ms=duration_ms,
            )

            self.attempts.append(attempt)

            # Cleanup old records
            await self._cleanup_old_records()

            # Invalidate cache for this integration
            if integration in self.metrics_cache:
                del self.metrics_cache[integration]

            logger.debug(
                f"Recorded retry attempt: {integration} attempt {attempt_number} - {status.value}"
            )

    async def _cleanup_old_records(self) -> None:
        """Remove records older than retention period"""
        cutoff = datetime.utcnow() - timedelta(hours=self._retention_hours)

        # Filter old records
        self.attempts = [a for a in self.attempts if a.timestamp > cutoff]

        # Trim if exceeding max records
        if len(self.attempts) > self._max_records:
            self.attempts = self.attempts[-self._max_records:]

    def get_metrics(self, integration: str, hours: int = 1) -> RetryMetrics:
        """
        Get retry metrics for a specific integration.

        Args:
            integration: Integration name
            hours: Number of hours to look back (default: 1)

        Returns:
            RetryMetrics for the integration
        """
        # Check cache
        if integration in self.metrics_cache:
            cached = self.metrics_cache[integration]
            if (datetime.utcnow() - cached.last_updated).seconds < 60:
                return cached

        # Calculate metrics from scratch
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        integration_attempts = [
            a for a in self.attempts
            if a.integration == integration and a.timestamp > cutoff
        ]

        if not integration_attempts:
            return RetryMetrics(integration=integration)

        total = len(integration_attempts)
        successful = len([a for a in integration_attempts if a.status == RetryStatus.SUCCESS])
        retries = len([a for a in integration_attempts if a.attempt_number > 1])
        failed = len([a for a in integration_attempts if a.status == RetryStatus.FAILURE])
        timeouts = len([a for a in integration_attempts if a.status == RetryStatus.TIMEOUT])
        circuit_opens = len([a for a in integration_attempts if a.status == RetryStatus.CIRCUIT_OPEN])

        avg_duration = sum(a.duration_ms for a in integration_attempts) / total if total > 0 else 0.0

        metrics = RetryMetrics(
            integration=integration,
            total_attempts=total,
            successful_attempts=successful,
            retry_attempts=retries,
            failed_attempts=failed,
            timeout_attempts=timeouts,
            circuit_breaker_opens=circuit_opens,
            avg_duration_ms=avg_duration,
            retry_rate=(retries / total * 100) if total > 0 else 0.0,
            failure_rate=(failed / total * 100) if total > 0 else 0.0,
            last_updated=datetime.utcnow(),
        )

        # Cache the result
        self.metrics_cache[integration] = metrics

        return metrics

    def get_all_metrics(self, hours: int = 1) -> Dict[str, RetryMetrics]:
        """
        Get metrics for all integrations.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary mapping integration names to metrics
        """
        integrations = set(a.integration for a in self.attempts)

        return {
            integration: self.get_metrics(integration, hours)
            for integration in integrations
        }

    def get_high_retry_integrations(self, threshold: float = 20.0, hours: int = 1) -> List[RetryMetrics]:
        """
        Get integrations with retry rates above threshold.

        Args:
            threshold: Retry rate percentage threshold (default: 20%)
            hours: Number of hours to look back

        Returns:
            List of RetryMetrics for integrations exceeding threshold
        """
        all_metrics = self.get_all_metrics(hours)

        return [
            metrics for metrics in all_metrics.values()
            if metrics.retry_rate > threshold
        ]

    def get_summary(self, hours: int = 1) -> Dict[str, any]:
        """
        Get summary of retry metrics across all integrations.

        Args:
            hours: Number of hours to look back

        Returns:
            Summary dictionary with key metrics
        """
        all_metrics = self.get_all_metrics(hours)

        total_attempts = sum(m.total_attempts for m in all_metrics.values())
        total_retries = sum(m.retry_attempts for m in all_metrics.values())
        total_failures = sum(m.failed_attempts for m in all_metrics.values())

        high_retry = self.get_high_retry_integrations(threshold=20.0, hours=hours)

        return {
            "total_integrations": len(all_metrics),
            "total_attempts": total_attempts,
            "total_retries": total_retries,
            "total_failures": total_failures,
            "overall_retry_rate": (total_retries / total_attempts * 100) if total_attempts > 0 else 0.0,
            "overall_failure_rate": (total_failures / total_attempts * 100) if total_attempts > 0 else 0.0,
            "integrations_with_high_retry_rate": len(high_retry),
            "high_retry_integrations": [
                {
                    "integration": m.integration,
                    "retry_rate": f"{m.retry_rate:.2f}%",
                    "failure_rate": f"{m.failure_rate:.2f}%",
                }
                for m in high_retry
            ],
            "period_hours": hours,
        }

    def export_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-compatible metrics text
        """
        all_metrics = self.get_all_metrics(hours=1)

        lines = [
            "# HELP external_integration_retry_attempts_total Total retry attempts per integration",
            "# TYPE external_integration_retry_attempts_total counter",
            "",
            "# HELP external_integration_retry_rate Retry rate percentage per integration",
            "# TYPE external_integration_retry_rate gauge",
            "",
            "# HELP external_integration_failure_rate Failure rate percentage per integration",
            "# TYPE external_integration_failure_rate gauge",
            "",
            "# HELP external_integration_avg_duration_ms Average request duration in milliseconds",
            "# TYPE external_integration_avg_duration_ms gauge",
            "",
        ]

        for integration, metrics in all_metrics.items():
            # Total attempts
            lines.append(
                f'external_integration_retry_attempts_total{{integration="{integration}"}} '
                f'{metrics.total_attempts}'
            )

            # Retry rate
            lines.append(
                f'external_integration_retry_rate{{integration="{integration}"}} '
                f'{metrics.retry_rate:.2f}'
            )

            # Failure rate
            lines.append(
                f'external_integration_failure_rate{{integration="{integration}"}} '
                f'{metrics.failure_rate:.2f}'
            )

            # Average duration
            lines.append(
                f'external_integration_avg_duration_ms{{integration="{integration}"}} '
                f'{metrics.avg_duration_ms:.2f}'
            )

            lines.append("")

        return "\n".join(lines)

    async def check_and_alert(self) -> List[str]:
        """
        Check for abnormal retry patterns and return alert messages.

        Returns:
            List of alert messages
        """
        alerts = []
        summary = self.get_summary(hours=1)

        # Alert 1: High overall retry rate
        if summary["overall_retry_rate"] > 30.0:
            alerts.append(
                f"⚠️ HIGH OVERALL RETRY RATE: {summary['overall_retry_rate']:.2f}% "
                f"of external API calls are being retried. This indicates widespread service instability."
            )

        # Alert 2: High overall failure rate
        if summary["overall_failure_rate"] > 10.0:
            alerts.append(
                f"🚨 HIGH FAILURE RATE: {summary['overall_failure_rate']:.2f}% "
                f"of external API calls are failing even after retries. Immediate attention required."
            )

        # Alert 3: Individual integrations with high retry rates
        high_retry = self.get_high_retry_integrations(threshold=30.0, hours=1)
        for metrics in high_retry:
            alerts.append(
                f"⚠️ {metrics.integration.upper()} RETRY RATE: {metrics.retry_rate:.2f}% - "
                f"This integration is experiencing high retry rates. Consider investigation."
            )

        # Alert 4: Circuit breaker activations
        for metrics in self.get_all_metrics(hours=1).values():
            if metrics.circuit_breaker_opens > 5:
                alerts.append(
                    f"🔌 {metrics.integration.upper()} CIRCUIT BREAKER: "
                    f"Opened {metrics.circuit_breaker_opens} times in the last hour. "
                    f"This integration may be down."
                )

        # Alert 5: High timeout rates
        for metrics in self.get_all_metrics(hours=1).values():
            if metrics.total_attempts > 10:
                timeout_rate = (metrics.timeout_attempts / metrics.total_attempts) * 100
                if timeout_rate > 20.0:
                    alerts.append(
                        f"⏱️ {metrics.integration.upper()} TIMEOUT RATE: {timeout_rate:.2f}% - "
                        f"This integration is experiencing frequent timeouts. "
                        f"Consider increasing timeout or investigating network issues."
                    )

        return alerts


# Global instance
retry_tracker = RetryMetricsTracker.get_instance()


# Convenience functions for recording metrics
async def record_retry_attempt(
    integration: str,
    endpoint: str,
    attempt_number: int,
    status: RetryStatus,
    error_type: Optional[str] = None,
    duration_ms: float = 0.0,
) -> None:
    """Convenience function to record a retry attempt"""
    await retry_tracker.record_attempt(
        integration=integration,
        endpoint=endpoint,
        attempt_number=attempt_number,
        status=status,
        error_type=error_type,
        duration_ms=duration_ms,
    )


def get_retry_metrics(integration: str, hours: int = 1) -> RetryMetrics:
    """Convenience function to get metrics for an integration"""
    return retry_tracker.get_metrics(integration, hours)


def get_retry_summary(hours: int = 1) -> Dict[str, any]:
    """Convenience function to get retry metrics summary"""
    return retry_tracker.get_summary(hours)
