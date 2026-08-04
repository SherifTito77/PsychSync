#!/usr/bin/env python3
"""
Threat Detection Metrics Aggregator

Aggregates and exposes Prometheus metrics for all threat detection components:
- Jailbreak detector metrics
- Behavioral analyzer metrics
- Real-time threat monitor metrics
- Automated response metrics

Integrates with Prometheus for scraping and Grafana for visualization.

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import logging
from collections import Counter
from typing import Any

# Prometheus client library
try:
    from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create dummy classes for type hints
    class Counter:
        pass

    class Gauge:
        pass

    class Histogram:
        pass

    class Info:
        pass


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ThreatDetectionMetrics:
    """
    Prometheus metrics aggregator for threat detection system.

    Exposes metrics at /metrics endpoint for Prometheus scraping.
    """

    def __init__(self, port: int = 8001):
        """
        Initialize metrics aggregator.

        Args:
            port: Port for metrics endpoint
        """
        self.port = port

        if PROMETHEUS_AVAILABLE:
            # Jailbreak Detection Metrics
            self.jailbreak_attempts_total = Counter(
                "psychsync_jailbreak_attempts_total",
                "Total number of jailbreak attempts detected",
                ["jailbreak_type"],
            )

            self.jailbreak_by_severity = Counter(
                "psychsync_jailbreak_by_severity",
                "Jailbreak attempts by severity level",
                ["severity"],
            )

            self.jailbreak_patterns_matched = Counter(
                "psychsync_jailbreak_patterns_matched",
                "Number of jailbreak patterns matched",
                ["pattern"],
            )

            self.jailbreak_confidence = Histogram(
                "psychsync_jailbreak_confidence",
                "Jailbreak detection confidence scores",
                buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            )

            # Behavioral Analysis Metrics
            self.behavioral_anomalies = Counter(
                "psychsync_behavioral_anomalies",
                "Behavioral anomalies detected",
                ["category", "threat_type"],
            )

            self.behavioral_baseline_users = Gauge(
                "psychsync_users_with_baselines",
                "Number of users with established behavioral baselines",
            )

            self.behavioral_total_users = Gauge(
                "psychsync_total_users_tracked",
                "Total number of users tracked by behavioral analyzer",
            )

            self.user_risk_score = Gauge(
                "psychsync_user_risk_score",
                "Behavioral risk score by user",
                ["user_id"],
            )

            # Unified Threat Monitoring Metrics
            self.threat_signals = Counter(
                "psychsync_threat_signals",
                "Threat signals from unified monitoring",
                ["source", "severity", "threat_type"],
            )

            self.threat_level = Gauge(
                "psychsync_threat_level",
                "Current threat level by session",
                ["session_id", "level"],
            )

            self.avg_risk_score = Gauge(
                "psychsync_avg_risk_score", "Average risk score across all assessments"
            )

            self.active_sessions = Gauge(
                "psychsync_active_sessions", "Number of active monitoring sessions"
            )

            # Automated Response Metrics
            self.response_actions_executed = Counter(
                "psychsync_response_actions_executed_total",
                "Response actions executed",
                ["action", "status"],
            )

            self.response_actions_failed = Counter(
                "psychsync_response_actions_failed",
                "Response actions that failed",
                ["action"],
            )

            self.response_duration = Histogram(
                "psychsync_response_duration_seconds",
                "Response action execution duration",
                ["action"],
                buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            )

            self.response_success_rate = Gauge(
                "psychsync_response_success_rate", "Response action success rate (0-1)"
            )

            self.auto_response_enabled = Gauge(
                "psychsync_auto_response_enabled",
                "Whether automated response is enabled (1 or 0)",
            )

            # Request Metrics
            self.requests_blocked_total = Counter(
                "psychsync_requests_blocked_total",
                "Total requests blocked by threat detection",
            )

            self.requests_analyzed_total = Counter(
                "psychsync_requests_analyzed_total",
                "Total requests analyzed for threats",
            )

            # System Health Metrics
            self.system_health = Gauge(
                "psychsync_threat_detection_health",
                "Health status of threat detection system (1=healthy, 0=unhealthy)",
            )

            # System Info
            self.metrics_info = Info(
                "psychsync_threat_detection",
                "Information about the threat detection system",
                {
                    "version": "1.0.0",
                    "components": [
                        "jailbreak_detector",
                        "behavioral_analyzer",
                        "realtime_monitor",
                        "auto_responder",
                    ],
                },
            )

            # Set initial values
            self.auto_response_enabled.set(1)
            self.system_health.set(1)

            logger.info(f"Prometheus metrics initialized on port {port}")
        else:
            logger.warning("Prometheus client not available - metrics disabled")

    def record_jailbreak_attempt(
        self,
        jailbreak_type: str,
        severity: str,
        patterns_matched: list[str],
        confidence: float,
    ):
        """Record jailbreak attempt metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.jailbreak_attempts_total.labels(jailbreak_type=jailbreak_type).inc()
        self.jailbreak_by_severity.labels(severity=severity).inc()

        for pattern in patterns_matched:
            self.jailbreak_patterns_matched.labels(pattern=pattern).inc()

        self.jailbreak_confidence.observe(confidence)

    def record_behavioral_anomaly(
        self, user_id: str, category: str, threat_type: str, risk_score: float
    ):
        """Record behavioral anomaly metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.behavioral_anomalies.labels(
            category=category, threat_type=threat_type
        ).inc()

        self.user_risk_score.labels(user_id=user_id).set(risk_score)

    def update_baseline_stats(self, users_with_baselines: int, total_users: int):
        """Update behavioral baseline statistics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.behavioral_baseline_users.set(users_with_baselines)
        self.behavioral_total_users.set(total_users)

    def record_threat_signal(
        self,
        source: str,
        severity: str,
        threat_type: str,
        session_id: str | None = None,
    ):
        """Record unified threat signal"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.threat_signals.labels(
            source=source, severity=severity, threat_type=threat_type
        ).inc()

    def record_threat_assessment(
        self, session_id: str, threat_level: str, risk_score: float
    ):
        """Record threat assessment metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        # Update threat level (as gauge: 1 if current level, 0 otherwise)
        for level in ["safe", "low", "medium", "high", "critical"]:
            value = 1.0 if level == threat_level else 0.0
            self.threat_level.labels(session_id=session_id, level=level).set(value)

    def update_avg_risk_score(self, avg_score: float):
        """Update average risk score"""
        if PROMETHEUS_AVAILABLE:
            self.avg_risk_score.set(avg_score)

    def update_active_sessions(self, count: int):
        """Update active sessions count"""
        if PROMETHEUS_AVAILABLE:
            self.active_sessions.set(count)

    def record_response_action(
        self, action: str, status: str, duration_seconds: float, success: bool
    ):
        """Record response action metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.response_actions_executed.labels(action=action, status=status).inc()
        self.response_duration.labels(action=action).observe(duration_seconds)

        if not success:
            self.response_actions_failed.labels(action=action).inc()

    def update_response_success_rate(self, success_rate: float):
        """Update response success rate"""
        if PROMETHEUS_AVAILABLE:
            self.response_success_rate.set(success_rate)

    def record_request_analyzed(self, blocked: bool = False):
        """Record request analysis"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.requests_analyzed_total.inc()
        if blocked:
            self.requests_blocked_total.inc()

    def start_metrics_server(self):
        """Start Prometheus metrics HTTP server"""
        if PROMETHEUS_AVAILABLE:
            logger.info(f"Starting Prometheus metrics server on port {self.port}")
            start_http_server(self.port)
        else:
            logger.error(
                "Cannot start metrics server - prometheus_client not installed"
            )


# Global metrics instance
threat_metrics = ThreatDetectionMetrics()


def get_metrics() -> ThreatDetectionMetrics:
    """Get the global metrics instance"""
    return threat_metrics


def record_jailbreak(
    jailbreak_type: str, severity: str, patterns_matched: list[str], confidence: float
):
    """
    Convenience function to record jailbreak attempt.

    Usage:
        from app.monitoring.threat_metrics import record_jailbreak

        record_jailbreak(
            jailbreak_type='direct_injection',
            severity='high',
            patterns_matched=['ignore.*instructions'],
            confidence=0.85
        )
    """
    threat_metrics.record_jailbreak_attempt(
        jailbreak_type=jailbreak_type,
        severity=severity,
        patterns_matched=patterns_matched,
        confidence=confidence,
    )


def record_behavioral_anomaly(
    user_id: str, category: str, threat_type: str, risk_score: float
):
    """Convenience function to record behavioral anomaly"""
    threat_metrics.record_behavioral_anomaly(
        user_id=user_id,
        category=category,
        threat_type=threat_type,
        risk_score=risk_score,
    )


def record_threat_assessment(
    session_id: str, threat_level: str, risk_score: float, signals: list[dict[str, Any]]
):
    """Convenience function to record threat assessment"""
    # Update threat level
    threat_metrics.record_threat_assessment(
        session_id=session_id, threat_level=threat_level, risk_score=risk_score
    )

    # Record each signal
    for signal in signals:
        threat_metrics.record_threat_signal(
            source=signal.get("source", "unknown"),
            severity=signal.get("severity", "unknown"),
            threat_type=signal.get("threat_type", "unknown"),
            session_id=session_id,
        )

    # Update average risk score
    threat_metrics.update_avg_risk_score(risk_score)


def record_response(action: str, status: str, duration_seconds: float, success: bool):
    """Convenience function to record response action"""
    threat_metrics.record_response_action(
        action=action, status=status, duration_seconds=duration_seconds, success=success
    )


# CLI interface
def main():
    """CLI interface for metrics aggregator"""
    import argparse

    parser = argparse.ArgumentParser(description="Threat Detection Metrics Aggregator")
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for metrics endpoint (default: 8001)",
    )
    parser.add_argument("--test", action="store_true", help="Generate test metrics")

    args = parser.parse_args()

    # Initialize metrics
    metrics = ThreatDetectionMetrics(port=args.port)

    if args.test:
        # Generate test metrics
        logger.info("Generating test metrics...")

        metrics.record_jailbreak_attempt(
            jailbreak_type="direct_injection",
            severity="high",
            patterns_matched=["ignore.*instructions"],
            confidence=0.85,
        )

        metrics.record_behavioral_anomaly(
            user_id="test_user_123",
            category="bot_automation",
            threat_type="bot_automation",
            risk_score=0.75,
        )

        metrics.record_threat_assessment(
            session_id="test_session",
            threat_level="high",
            risk_score=0.7,
            signals=[
                {
                    "source": "jailbreak",
                    "severity": "high",
                    "threat_type": "direct_injection",
                },
                {
                    "source": "behavioral",
                    "severity": "medium",
                    "threat_type": "anomaly",
                },
            ],
        )

        metrics.record_response_action(
            action="Block Session",
            status="executed",
            duration_seconds=0.5,
            success=True,
        )

        logger.info("Test metrics generated")
        logger.info(f"View metrics at: http://localhost:{args.port}/metrics")

    # Start metrics server
    logger.info(f"\nStarting metrics server on port {args.port}...")
    logger.info("Metrics available at: http://localhost:{args.port}/metrics")
    metrics.start_metrics_server()


if __name__ == "__main__":
    main()
