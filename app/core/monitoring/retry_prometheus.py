"""
Prometheus Retry Metrics Exporter

Exports retry metrics in Prometheus format with Counter and Gauge metrics.

Metrics:
- retry_attempts_total: Counter of total retry attempts
-_retry_success_total: Counter of successful operations after retry
-_retry_failure_total: Counter of failed operations after all retries
-_retry_duration_seconds: Histogram of operation duration
- retry_queue_size: Gauge of DLQ size

Usage:
    GET /metrics/retry - Prometheus metrics endpoint

Author: Observability Team
Version: 1.0
"""

import logging
from typing import Dict

from app.core.monitoring.retry_metrics import RetryStatus, retry_tracker
from app.core.retry_wrapper import get_dlq

logger = logging.getLogger(__name__)


class RetryMetricsExporter:
    """Export retry metrics in Prometheus format"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def generate_metrics(self) -> str:
        """
        Generate all retry metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics text
        """
        try:
            # Get retry metrics summary
            summary = retry_tracker.get_summary(hours=1)
            all_metrics = retry_tracker.get_all_metrics(hours=1)

            # Get DLQ stats
            dlq = get_dlq()
            dlq_stats = await dlq.get_stats()

            lines = []

            # HELP and TYPE for retry attempts counter
            lines.extend(
                [
                    "# HELP retry_attempts_total Total number of retry attempts per component",
                    "# TYPE retry_attempts_total counter",
                    "",
                ]
            )

            # Component-specific attempt counters
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_attempts_total{{component="{integration}"}} {metrics.total_attempts}'
                )

            lines.extend(
                [
                    "",
                    "# HELP retry_success_total Total successful operations after retry",
                    "# TYPE retry_success_total counter",
                    "",
                ]
            )

            # Success counters
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_success_total{{component="{integration}"}} {metrics.successful_attempts}'
                )

            lines.extend(
                [
                    "",
                    "# HELP retry_failure_total Total failed operations after all retries",
                    "# TYPE retry_failure_total counter",
                    "",
                ]
            )

            # Failure counters
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_failure_total{{component="{integration}"}} {metrics.failed_attempts}'
                )

            lines.extend(
                [
                    "",
                    "# HELP retry_rate_percentage Retry rate percentage per component",
                    "# TYPE retry_rate_percentage gauge",
                    "",
                ]
            )

            # Retry rate gauges
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_rate_percentage{{component="{integration}"}} {metrics.retry_rate:.2f}'
                )

            lines.extend(
                [
                    "",
                    "# HELP retry_failure_rate_percentage Failure rate percentage per component",
                    "# TYPE retry_failure_rate_percentage gauge",
                    "",
                ]
            )

            # Failure rate gauges
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_failure_rate_percentage{{component="{integration}"}} {metrics.failure_rate:.2f}'
                )

            lines.extend(
                [
                    "",
                    "# HELP retry_avg_duration_ms Average operation duration in milliseconds",
                    "# TYPE retry_avg_duration_ms gauge",
                    "",
                ]
            )

            # Average duration gauges
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_avg_duration_ms{{component="{integration}"}} {metrics.avg_duration_ms:.2f}'
                )

            lines.extend(
                [
                    "",
                    "# HELP retry_circuit_breaker_opens_total Circuit breaker open count per component",
                    "# TYPE retry_circuit_breaker_opens_total counter",
                    "",
                ]
            )

            # Circuit breaker metrics
            for integration, metrics in all_metrics.items():
                lines.append(
                    f'retry_circuit_breaker_opens_total{{component="{integration}"}} {metrics.circuit_breaker_opens}'
                )

            # DLQ metrics
            lines.extend(
                [
                    "",
                    "# HELP retry_dlq_size Current dead letter queue size",
                    "# TYPE retry_dlq_size gauge",
                    "",
                    f"retry_dlq_size {dlq_stats['total_entries']}",
                    "",
                    "# HELP retry_dlq_size_by_component Dead letter queue size per component",
                    "# TYPE retry_dlq_size_by_component gauge",
                    "",
                ]
            )

            for component, count in dlq_stats.get("by_component", {}).items():
                lines.append(
                    f'retry_dlq_size_by_component{{component="{component}"}} {count}'
                )

            # Overall summary metrics
            lines.extend(
                [
                    "",
                    "# HELP retry_overall_rate Overall system retry rate percentage",
                    "# TYPE retry_overall_rate gauge",
                    f"retry_overall_rate {summary['overall_retry_rate']:.2f}",
                    "",
                    "# HELP retry_overall_failure_rate Overall system failure rate percentage",
                    "# TYPE retry_overall_failure_rate gauge",
                    f"retry_overall_failure_rate {summary['overall_failure_rate']:.2f}",
                    "",
                    "# HELP retry_total_integrations Total number of tracked integrations",
                    "# TYPE retry_total_integrations gauge",
                    f"retry_total_integrations {summary['total_integrations']}",
                    "",
                ]
            )

            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Failed to generate retry metrics: {e}")
            # Return minimal metrics on error
            return (
                "# ERROR: Failed to generate metrics\n" f"retry_generation_errors 1\n"
            )


# Global exporter instance
metrics_exporter = RetryMetricsExporter()


async def generate_retry_metrics() -> str:
    """Generate retry metrics in Prometheus format"""
    return await metrics_exporter.generate_metrics()
