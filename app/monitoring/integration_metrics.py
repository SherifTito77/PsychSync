"""
Unified Integration Metrics Monitoring System

This module provides centralized metrics collection for all integration points:
- Database operations metrics
- Redis operations metrics
- HRIS connector metrics
- Email service metrics
- HTTP client metrics

All metrics include:
- Success/failure rates
- Response times (p50, p95, p99)
- Circuit breaker states
- Error classification
- Health status

Usage:
    from app.monitoring.integration_metrics import get_all_integration_metrics

    metrics = await get_all_integration_metrics()
    # Returns dictionary with all integration metrics
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def get_all_integration_metrics() -> dict[str, Any]:
    """
    Get metrics from all integration points for monitoring

    Returns:
        Dictionary with metrics from all integrations:
        {
            "timestamp": "2026-02-11T12:00:00Z",
            "database": {...},
            "redis": {...},
            "hris": {...},
            "email": {...},
            "http_client": {...},
            "summary": {...}
        }
    """
    metrics = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Database metrics
    try:
        # Import the function from its actual location and get async session
        from app.api.v1.endpoints.health import (
            get_database_metrics as get_db_metrics_from_health,
        )
        from app.core.database import get_async_db

        async for db_session in get_async_db():
            # Call the async function with the obtained session
            metrics["database"] = await get_db_metrics_from_health(db=db_session)
            break  # Exit after getting session and metrics
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        metrics["database"] = {"error": str(e)}

    # Redis metrics
    try:
        from app.core.redis_client import get_redis_metrics

        metrics["redis"] = get_redis_metrics()
    except Exception as e:
        logger.error(f"Failed to get Redis metrics: {e}")
        metrics["redis"] = {"error": str(e)}

    # HRIS metrics
    try:
        from app.integrations.hris.resilient_adapter import get_all_hris_metrics

        metrics["hris"] = get_all_hris_metrics()
    except Exception as e:
        logger.error(f"Failed to get HRIS metrics: {e}")
        metrics["hris"] = {"error": str(e)}

    # Email service metrics (if available)
    try:
        from app.services.email_providers import get_email_service

        email_service = get_email_service()
        if hasattr(email_service, "get_metrics"):
            metrics["email"] = email_service.get_metrics()
        else:
            metrics["email"] = {"status": "not_available"}
    except Exception as e:
        logger.error(f"Failed to get email metrics: {e}")
        metrics["email"] = {"error": str(e)}

    # HTTP client metrics (if available)
    try:
        from app.core.resilient_client import resilient_http_client

        if hasattr(resilient_http_client, "get_metrics"):
            metrics["http_client"] = resilient_http_client.get_metrics()
        else:
            metrics["http_client"] = {"status": "not_available"}
    except Exception as e:
        logger.error(f"Failed to get HTTP client metrics: {e}")
        metrics["http_client"] = {"error": str(e)}

    # Calculate overall summary
    metrics["summary"] = _calculate_summary(metrics)

    return metrics


def _calculate_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate overall health summary from all integration metrics

    Args:
        metrics: Dictionary with all integration metrics

    Returns:
        Summary dictionary with overall health status
    """
    summary = {
        "total_integrations": 0,
        "healthy_integrations": 0,
        "degraded_integrations": 0,
        "failed_integrations": 0,
        "overall_status": "unknown",
    }

    # Check database health
    if "database" in metrics and "error" not in metrics["database"]:
        summary["total_integrations"] += 1
        db_state = metrics["database"].get("circuit_breaker_state", "closed")
        if db_state == "closed":
            summary["healthy_integrations"] += 1
        else:
            summary["degraded_integrations"] += 1

    # Check Redis health
    if "redis" in metrics and "error" not in metrics["redis"]:
        summary["total_integrations"] += 1
        redis_state = metrics["redis"].get("circuit_breaker_state", "closed")
        if redis_state == "closed":
            summary["healthy_integrations"] += 1
        else:
            summary["degraded_integrations"] += 1

    # Check HRIS connectors
    if "hris" in metrics and "error" not in metrics["hris"]:
        for connector_name, connector_metrics in metrics["hris"].items():
            summary["total_integrations"] += 1
            state = connector_metrics.get("circuit_breaker_state", "closed")
            if state == "closed":
                summary["healthy_integrations"] += 1
            else:
                summary["degraded_integrations"] += 1

    # Check email service
    if "email" in metrics and "error" not in metrics["email"]:
        summary["total_integrations"] += 1
        if metrics["email"].get("status") != "not_available":
            summary["healthy_integrations"] += 1

    # Determine overall status
    if summary["total_integrations"] > 0:
        health_ratio = summary["healthy_integrations"] / summary["total_integrations"]
        if health_ratio >= 0.9:
            summary["overall_status"] = "healthy"
        elif health_ratio >= 0.5:
            summary["overall_status"] = "degraded"
        else:
            summary["overall_status"] = "unhealthy"

    return summary


async def get_health_status() -> dict[str, Any]:
    """
    Get simplified health status for quick health checks

    Returns:
        Simplified health status dictionary:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "timestamp": "2026-02-11T12:00:00Z",
            "checks": {
                "database": "ok" | "degraded" | "down",
                "redis": "ok" | "degraded" | "down",
                "hris": {...},
                "email": "ok" | "degraded" | "down",
            }
        }
    """
    full_metrics = await get_all_integration_metrics()
    summary = full_metrics.get("summary", {})

    checks = {}

    # Database check
    if "database" in full_metrics:
        db_state = full_metrics["database"].get("circuit_breaker_state", "closed")
        checks["database"] = "ok" if db_state == "closed" else "degraded"
    else:
        checks["database"] = "down"

    # Redis check
    if "redis" in full_metrics:
        redis_state = full_metrics["redis"].get("circuit_breaker_state", "closed")
        checks["redis"] = "ok" if redis_state == "closed" else "degraded"
    else:
        checks["redis"] = "down"

    # HRIS check
    if "hris" in full_metrics:
        hris_checks = {}
        for name, metrics in full_metrics["hris"].items():
            state = metrics.get("circuit_breaker_state", "closed")
            hris_checks[name] = "ok" if state == "closed" else "degraded"
        checks["hris"] = hris_checks
    else:
        checks["hris"] = "down"

    # Email check
    if "email" in full_metrics:
        checks["email"] = (
            "ok"
            if full_metrics["email"].get("status") != "not_available"
            else "unknown"
        )
    else:
        checks["email"] = "down"

    return {
        "status": summary.get("overall_status", "unknown"),
        "timestamp": full_metrics.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "checks": checks,
    }


def format_metrics_for_prometheus(metrics: dict[str, Any]) -> str:
    """
    Format metrics for Prometheus scraping

    Args:
        metrics: Dictionary with all integration metrics

    Returns:
        Prometheus-compatible text format metrics
    """
    lines = []

    # Helper to format metric
    def format_metric(name: str, value: float | int, labels: dict[str, str] = None):
        label_str = ""
        if labels:
            label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"
        return f"psychsync_{name}{label_str} {value}"

    # Database metrics
    if "database" in metrics and "error" not in metrics["database"]:
        db = metrics["database"]
        lines.append(format_metric("db_total_calls", db.get("total_calls", 0)))
        lines.append(
            format_metric("db_successful_calls", db.get("successful_calls", 0))
        )
        lines.append(format_metric("db_failed_calls", db.get("failed_calls", 0)))
        lines.append(format_metric("db_success_rate", db.get("success_rate", 0)))
        lines.append(
            format_metric("db_avg_response_time_ms", db.get("avg_response_time_ms", 0))
        )
        lines.append(
            format_metric(
                "db_circuit_breaker_open",
                1 if db.get("circuit_breaker_state") == "open" else 0,
            )
        )

    # Redis metrics
    if "redis" in metrics and "error" not in metrics["redis"]:
        redis = metrics["redis"]
        lines.append(format_metric("redis_total_calls", redis.get("total_calls", 0)))
        lines.append(
            format_metric("redis_successful_calls", redis.get("successful_calls", 0))
        )
        lines.append(format_metric("redis_failed_calls", redis.get("failed_calls", 0)))
        lines.append(format_metric("redis_success_rate", redis.get("success_rate", 0)))
        lines.append(
            format_metric(
                "redis_avg_response_time_ms", redis.get("avg_response_time_ms", 0)
            )
        )
        lines.append(
            format_metric(
                "redis_circuit_breaker_open",
                1 if redis.get("circuit_breaker_state") == "open" else 0,
            )
        )

    # HRIS metrics
    if "hris" in metrics and "error" not in metrics["hris"]:
        for name, hris in metrics["hris"].items():
            labels = {"connector": name}
            lines.append(
                format_metric("hris_total_calls", hris.get("total_calls", 0), labels)
            )
            lines.append(
                format_metric(
                    "hris_successful_calls", hris.get("successful_calls", 0), labels
                )
            )
            lines.append(
                format_metric("hris_failed_calls", hris.get("failed_calls", 0), labels)
            )
            lines.append(
                format_metric("hris_success_rate", hris.get("success_rate", 0), labels)
            )
            lines.append(
                format_metric(
                    "hris_avg_response_time_ms",
                    hris.get("avg_response_time_ms", 0),
                    labels,
                )
            )
            lines.append(
                format_metric(
                    "hris_circuit_breaker_open",
                    1 if hris.get("circuit_breaker_state") == "open" else 0,
                    labels,
                )
            )

    # Summary metrics
    if "summary" in metrics:
        summary = metrics["summary"]
        lines.append(
            format_metric(
                "integration_total_count", summary.get("total_integrations", 0)
            )
        )
        lines.append(
            format_metric(
                "integration_healthy_count", summary.get("healthy_integrations", 0)
            )
        )
        lines.append(
            format_metric(
                "integration_degraded_count", summary.get("degraded_integrations", 0)
            )
        )
        lines.append(
            format_metric(
                "integration_failed_count", summary.get("failed_integrations", 0)
            )
        )

    return "\n".join(lines) + "\n"
