"""
Application Performance Monitoring (APM) Integration

Supports multiple APM providers:
- Sentry (Error tracking & performance)
- Datadog (Full-stack monitoring)
- New Relic (APM & infrastructure)

USAGE:
    from app.services.monitoring import init_sentry, init_datadog

    # Initialize Sentry for error tracking
    init_sentry(
        dsn="your-sentry-dsn",
        environment="production",
        traces_sample_rate=0.1
    )

    # Initialize Datadog for metrics
    init_datadog(
        service_name="psychsync-api",
        statsd_host="localhost",
        statsd_port=8125
    )
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# SENTRY INTEGRATION
# ============================================================================

def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
) -> bool:
    """
    Initialize Sentry for error tracking and performance monitoring

    DESIGN DECISIONS:
    - Sample 10% of transactions for performance monitoring
    - Enable profiling for 10% of transactions
    - Filter sensitive data (PHI, PII) from Sentry
    - Custom tags for clinical operations

    Args:
        dsn: Sentry DSN from Sentry project settings
        environment: Environment name (production, staging, development)
        traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0)

    Returns:
        True if initialized successfully, False otherwise
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        if dsn is None:
            dsn = os.getenv("SENTRY_DSN")

        if not dsn:
            logger.warning("Sentry DSN not configured, skipping Sentry initialization")
            return False

        # Configure Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration()
            ],
            # Filter sensitive data
            before_send_transaction=before_send_transaction_filter,
            before_send=before_send_filter,
            # Clinical operation tags
            release=os.getenv("APP_VERSION", "1.0.0"),
            server_name=os.getenv("SERVER_NAME", "psychsync-api"),
        )

        logger.info(f"Sentry initialized successfully (environment: {environment})")
        return True

    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {str(e)}")
        return False


def before_send_transaction_filter(event, hint):
    """Filter PHI/PII from transaction events before sending to Sentry"""

    # Remove request bodies (may contain PHI)
    if "request" in event:
        event["request"].pop("body", None)
        event["request"].pop("data", None)

    # Remove query parameters (may contain PHI in filters)
    if "request" in event and "query_string" in event["request"]:
        event["request"]["query_string"] = "[FILTERED]"

    return event


def before_send_filter(event, hint):
    """Filter PHI/PII from error events before sending to Sentry"""

    # Scrub user data
    if "user" in event:
        event["user"]["email"] = "[FILTERED]"
        event["user"]["username"] = "[FILTERED]"
        event["user"].pop("ip_address", None)

    # Scrub request data
    if "request" in event:
        event["request"].pop("body", None)
        event["request"].pop("data", None)
        event["request"].pop("query_string", None)

        # Filter headers that might contain PHI
        if "headers" in event["request"]:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                event["request"]["headers"].pop(header, None)

    # Scrub breadcrumbs (may contain PHI in URLs)
    if "breadcrumbs" in event:
        for breadcrumb in event["breadcrumbs"]:
            if "url" in breadcrumb:
                # Remove query parameters from URLs
                breadcrumb["url"] = breadcrumb["url"].split("?")[0]

    return event


def capture_clinical_error(
    error: Exception,
    screening_type: str,
    user_role: str,
    context: dict
):
    """
    Capture clinical error with context for Sentry

    DESIGN DECISION:
    - Add clinical operation tags
    - Severity levels based on clinical impact
    - Context includes operation type but excludes PHI
    """
    import sentry_sdk

    with sentry_sdk.push_scope() as scope:
        # Add clinical context
        scope.set_tag("operation", "clinical")
        scope.set_tag("screening_type", screening_type)
        scope.set_tag("user_role", user_role)
        scope.set_tag("severity", context.get("severity", "error"))

        # Add context (no PHI)
        scope.set_context("clinical", {
            "operation": context.get("operation"),
            "step": context.get("step"),
            "error_code": context.get("error_code"),
            "has_ph": context.get("has_ph", False)
        })

        # Capture exception
        sentry_sdk.capture_exception(error)


# ============================================================================
# DATADOG INTEGRATION
# ============================================================================

def init_datadog(
    service_name: str = "psychsync-api",
    statsd_host: str = "localhost",
    statsd_port: int = 8125,
    env: str = "production"
) -> bool:
    """
    Initialize Datadog for metrics and tracing

    DESIGN DECISIONS:
    - Use DogStatsD for metrics aggregation
    - Trace clinical operations (screening submissions, crisis alerts)
    - Custom metrics for clinical KPIs
    - Service mapping for distributed tracing

    Args:
        service_name: Name of the service (psychsync-api, psychsync-frontend)
        statsd_host: DogStatsD agent host
        statsd_port: DogStatsD agent port
        env: Environment name

    Returns:
        True if initialized successfully, False otherwise
    """
    try:
        from ddtrace import tracer, patch_all
        from ddtrace import config as dd_config

        # Configure Datadog
        dd_config.service = service_name
        dd_config.env = env

        # Patch all supported libraries
        patch_all()

        # Configure tracer
        tracer.configure(
            hostname=statsd_host,
            port=statsd_port,
            enabled=True,
            analytics_enabled=True,
            trace_propagation_styles=["datadog", "b3"]
        )

        logger.info(f"Datadog initialized successfully (service: {service_name})")
        return True

    except ImportError:
        logger.warning("ddtrace not installed, skipping Datadog initialization")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Datadog: {str(e)}")
        return False


# ============================================================================
# CUSTOM METRICS
# ============================================================================

class ClinicalMetrics:
    """
    Custom metrics for clinical operations

    DESIGN DECISIONS:
    - Track clinical KPIs separately from app metrics
    - No PHI in metric tags or values
    - Aggregate counts only (no individual patient data)
    """

    def __init__(self, statsd_client=None):
        """
        Initialize clinical metrics

        Args:
            statsd_client: DogStatsD client (if using Datadog)
        """
        self.statsd = statsd_client

    def increment_screening_submitted(self, screening_type: str, severity: str):
        """Increment screening submitted counter"""
        if self.statsd:
            metric_name = f"clinical.screening.submitted.{screening_type}"
            self.statsd.increment(metric_name, tags=[f"severity:{severity}"])
        logger.debug(f"Metric: {screening_type} submitted ({severity} severity)")

    def increment_screening_completed(self, screening_type: str, risk_level: str):
        """Increment screening completed counter"""
        if self.statsd:
            metric_name = f"clinical.screening.completed.{screening_type}"
            self.statsd.increment(metric_name, tags=[f"risk_level:{risk_level}"])
        logger.debug(f"Metric: {screening_type} completed ({risk_level} risk)")

    def increment_crisis_alert(self, alert_type: str, severity: str):
        """Increment crisis alert counter"""
        if self.statsd:
            metric_name = "clinical.crisis_alert.triggered"
            self.statsd.increment(metric_name, tags=[f"type:{alert_type}", f"severity:{severity}"])
        logger.warning(f"Metric: Crisis alert {alert_type} ({severity} severity)")

    def timing_screening_duration(self, screening_type: str, duration_ms: int):
        """Record screening completion time"""
        if self.statsd:
            metric_name = f"clinical.screening.duration.{screening_type}"
            self.statsd.timed(metric_name, duration_ms)
        logger.debug(f"Metric: {screening_type} completed in {duration_ms}ms")

    def increment_clinician_notification(self, notification_type: str, provider: str):
        """Increment notification sent counter"""
        if self.statsd:
            metric_name = "clinical.notification.sent"
            self.statsd.increment(metric_name, tags=[f"type:{notification_type}", f"provider:{provider}"])
        logger.debug(f"Metric: Notification sent ({notification_type} via {provider})")


# Singleton instance
_clinical_metrics: Optional[ClinicalMetrics] = None


def get_clinical_metrics() -> ClinicalMetrics:
    """Get or create singleton clinical metrics instance"""
    global _clinical_metrics
    if _clinical_metrics is None:
        # Try to initialize with Datadog
        try:
            from datadog import DogStatsd
            statsd = DogStatsd(
                host=os.getenv("DATADOG_HOST", "localhost"),
                port=int(os.getenv("DATADOG_PORT", 8125))
            )
            _clinical_metrics = ClinicalMetrics(statsd_client=statsd)
            logger.info("Clinical metrics initialized with Datadog")
        except ImportError:
            _clinical_metrics = ClinicalMetrics(statsd_client=None)
            logger.info("Clinical metrics initialized without Datadog (metrics disabled)")

    return _clinical_metrics


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

def get_monitoring_status() -> dict:
    """
    Get status of all monitoring systems

    Returns:
        Dict with status of Sentry, Datadog, and logging
    """
    status = {
        "sentry": {"configured": False, "environment": None},
        "datadog": {"configured": False, "service": None},
        "logging": {"configured": False, "level": None}
    }

    # Check Sentry
    try:
        import sentry_sdk
        status["sentry"]["configured"] = sentry_sdk.Hub.current_client is not None
        status["sentry"]["environment"] = os.getenv("ENVIRONMENT", "unknown")
    except ImportError:
        pass

    # Check Datadog
    try:
        import ddtrace
        status["datadog"]["configured"] = ddgame.tracer is not None
        status["datadog"]["service"] = os.getenv("DD_SERVICE", "psychsync-api")
    except ImportError:
        pass

    # Check logging
    import logging
    root_logger = logging.getLogger()
    status["logging"]["configured"] = len(root_logger.handlers) > 0
    status["logging"]["level"] = root_logger.level

    return status
