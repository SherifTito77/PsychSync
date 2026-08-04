"""
Resilience Monitoring API Endpoints

Provides real-time visibility into circuit breaker states, retry metrics,
and overall system boundary health.

Author: Resilience Team
Version: 1.0
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.logging_config import logger
from app.core.resilience import get_resilience_manager
from app.db.models.user import User

router = APIRouter()


@router.get("/health")
async def resilience_health_check():
    """
    Overall resilience health check.

    Returns overall system resilience status based on circuit breaker states.
    """
    manager = get_resilience_manager()
    metrics = manager.get_all_metrics()

    # Analyze circuit breaker states
    open_circuits = []
    half_open_circuits = []
    healthy_circuits = []

    for cb_name, cb_metrics in metrics["circuit_breakers"].items():
        state = cb_metrics["state"]
        if state == "open":
            open_circuits.append(cb_name)
        elif state == "half_open":
            half_open_circuits.append(cb_name)
        else:
            healthy_circuits.append(cb_name)

    # Determine overall health
    total_cbs = len(metrics["circuit_breakers"])
    if total_cbs == 0:
        overall_status = "healthy"
        status_code = 200
    elif len(open_circuits) > total_cbs * 0.5:
        # More than 50% of circuits are open
        overall_status = "degraded"
        status_code = 503  # Service Unavailable
    elif len(open_circuits) > 0:
        overall_status = "warning"
        status_code = 200  # Still functional but with issues
    else:
        overall_status = "healthy"
        status_code = 200

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_circuit_breakers": total_cbs,
            "open": len(open_circuits),
            "half_open": len(half_open_circuits),
            "closed": len(healthy_circuits),
        },
        "open_circuits": open_circuits,
        "half_open_circuits": half_open_circuits,
        "_links": {
            "details": "/api/v1/resilience/metrics",
            "circuit_breakers": "/api/v1/resilience/circuit-breakers",
        },
    }, status_code


@router.get("/resilience-metrics")
async def get_resilience_metrics(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive resilience metrics for all components.

    Requires authentication.
    """
    manager = get_resilience_manager()
    metrics = manager.get_all_metrics()

    return {
        "timestamp": datetime.now().isoformat(),
        "circuit_breakers": metrics["circuit_breakers"],
        "rate_limiters": metrics["rate_limiters"],
        "bulkheads": metrics["bulkheads"],
        "retry_policies": metrics["retry_policies"],
    }


@router.get("/circuit-breakers")
async def get_circuit_breaker_states(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed state information for all circuit breakers.

    Requires authentication.
    """
    manager = get_resilience_manager()
    all_metrics = manager.get_all_metrics()

    circuit_breakers = []
    for cb_name, cb in manager.circuit_breakers.items():
        metrics = cb.get_metrics()

        # Add health status
        state = metrics["state"]
        if state == "closed":
            health = "healthy"
        elif state == "half_open":
            health = "recovering"
        else:
            health = "unhealthy"

        # Calculate time in current state
        time_in_state = (
            datetime.now() - datetime.fromisoformat(metrics["last_state_change"])
        ).total_seconds()

        circuit_breakers.append(
            {
                "name": cb_name,
                "state": state,
                "health": health,
                "failure_count": metrics["failure_count"],
                "success_count": metrics["success_count"],
                "success_rate": metrics["success_rate"],
                "avg_response_time_ms": metrics["avg_response_time"],
                "time_in_current_state_seconds": round(time_in_state, 2),
                "last_failure_time": metrics["last_failure_time"],
                "total_calls": metrics["total_calls"],
                "recent_failures": metrics["recent_failures_count"],
            }
        )

    return {
        "timestamp": datetime.now().isoformat(),
        "circuit_breakers": circuit_breakers,
        "summary": {
            "total": len(circuit_breakers),
            "healthy": sum(1 for cb in circuit_breakers if cb["health"] == "healthy"),
            "recovering": sum(
                1 for cb in circuit_breakers if cb["health"] == "recovering"
            ),
            "unhealthy": sum(
                1 for cb in circuit_breakers if cb["health"] == "unhealthy"
            ),
        },
    }


@router.get("/circuit-breakers/{circuit_name}")
async def get_circuit_breaker_details(
    circuit_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed information about a specific circuit breaker.

    Requires authentication.
    """
    manager = get_resilience_manager()

    if circuit_name not in manager.circuit_breakers:
        raise HTTPException(
            status_code=404, detail=f"Circuit breaker '{circuit_name}' not found"
        )

    cb = manager.circuit_breakers[circuit_name]
    metrics = cb.get_metrics()

    return {
        "name": circuit_name,
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "failure_threshold": cb.failure_threshold,
            "recovery_timeout": cb.recovery_timeout,
            "success_threshold": cb.success_threshold,
            "timeout": cb.timeout,
            "half_open_max_calls": cb.half_open_max_calls,
            "monitoring_window": cb.monitoring_window,
        },
        "current_state": {
            "state": metrics["state"],
            "failure_count": metrics["failure_count"],
            "success_count": metrics["success_count"],
            "success_rate": metrics["success_rate"],
            "avg_response_time_ms": metrics["avg_response_time"],
            "last_state_change": metrics["last_state_change"],
            "last_failure_time": metrics["last_failure_time"],
        },
        "call_history": {
            "total_calls": metrics["total_calls"],
            "recent_failures": metrics["recent_failures_count"],
            "monitoring_window": metrics["monitoring_window"],
        },
        "recommendations": _get_circuit_breaker_recommendations(metrics),
    }


def _get_circuit_breaker_recommendations(metrics: dict) -> list[str]:
    """Generate recommendations based on circuit breaker state"""
    recommendations = []

    state = metrics["state"]
    success_rate = metrics["success_rate"]
    avg_response_time = metrics["avg_response_time_ms"]
    recent_failures = metrics["recent_failures_count"]

    if state == "open":
        recommendations.append("Circuit is OPEN - Check external service availability")
        recommendations.append("Review logs for root cause of failures")
        recommendations.append("Consider increasing timeout if service is slow")
    elif state == "half_open":
        recommendations.append("Circuit is recovering - Monitor for stability")
        recommendations.append("Reduced traffic allowed to test service recovery")
    elif success_rate < 80:
        recommendations.append(
            f"Low success rate ({success_rate}%) - Investigate service health"
        )
        recommendations.append("Check for increased latency or error rates")
        recommendations.append("Review external service metrics")

    if avg_response_time > 5000:
        recommendations.append(
            f"High response time ({avg_response_time}ms) - Consider optimizing queries"
        )

    if recent_failures > 10:
        recommendations.append(
            f"Multiple recent failures ({recent_failures}) - Check service dependencies"
        )

    return (
        recommendations if recommendations else ["Circuit breaker operating normally"]
    )


@router.get("/rate-limiters")
async def get_rate_limiter_states(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get state information for all rate limiters.

    Requires authentication.
    """
    manager = get_resilience_manager()
    rate_limiters = []

    for rl_name, rl in manager.rate_limiters.items():
        metrics = rl.get_metrics()

        rate_limiters.append(
            {
                "name": rl_name,
                "algorithm": metrics["algorithm"],
                "utilization_percent": metrics.get("utilization_percent", 0),
                "current_requests": metrics.get("current_requests", 0),
                "limit": metrics.get("limit", 0),
                "window": metrics.get("window", 0),
            }
        )

    return {
        "timestamp": datetime.now().isoformat(),
        "rate_limiters": rate_limiters,
    }


@router.post("/circuit-breakers/{circuit_name}/reset")
async def reset_circuit_breaker(
    circuit_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually reset a circuit breaker to CLOSED state.

    WARNING: Only use this if you've verified the external service is healthy.
    This is an administrative operation for recovery purposes.

    Requires authentication.
    """
    manager = get_resilience_manager()

    if circuit_name not in manager.circuit_breakers:
        raise HTTPException(
            status_code=404, detail=f"Circuit breaker '{circuit_name}' not found"
        )

    cb = manager.circuit_breakers[circuit_name]

    # Reset circuit breaker
    old_state = cb.state.value
    cb._reset_circuit()

    logger.info(
        f"Circuit breaker {circuit_name} manually reset from {old_state} to CLOSED "
        f"by user {current_user.id}"
    )

    return {
        "message": f"Circuit breaker '{circuit_name}' reset successfully",
        "previous_state": old_state,
        "new_state": "closed",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/history")
async def get_resilience_history(
    hours: int = 24,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical resilience metrics over time.

    Requires authentication and database access.
    """
    # This would typically query a metrics store like Prometheus, InfluxDB, or a dedicated table
    # For now, return current state with placeholder for historical data

    manager = get_resilience_manager()
    current_metrics = manager.get_all_metrics()

    return {
        "timestamp": datetime.now().isoformat(),
        "period_hours": hours,
        "message": "Historical metrics integration pending - configure Prometheus/Grafana",
        "current_metrics": current_metrics,
        "setup_instructions": {
            "prometheus": "Install prometheus-fastapi-instrumentator",
            "grafana": "Import dashboard from ./monitoring/grafana/resilience-dashboard.json",
        },
    }


@router.get("/alerts")
async def get_resilience_alerts(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current resilience alerts and warnings.

    Requires authentication.
    """
    manager = get_resilience_manager()
    metrics = manager.get_all_metrics()

    alerts = []
    warnings = []

    # Check circuit breakers
    for cb_name, cb_metrics in metrics["circuit_breakers"].items():
        if cb_metrics["state"] == "open":
            alerts.append(
                {
                    "severity": "critical",
                    "type": "circuit_breaker_open",
                    "component": cb_name,
                    "message": f"Circuit breaker '{cb_name}' is OPEN - failing fast",
                    "failure_count": cb_metrics["failure_count"],
                    "last_failure": cb_metrics["last_failure_time"],
                    "recommendation": "Investigate external service health immediately",
                }
            )
        elif cb_metrics["state"] == "half_open":
            warnings.append(
                {
                    "severity": "warning",
                    "type": "circuit_breaker_half_open",
                    "component": cb_name,
                    "message": f"Circuit breaker '{cb_name}' is HALF_OPEN - testing recovery",
                    "success_count": cb_metrics["success_count"],
                    "recommendation": "Monitor for successful recovery",
                }
            )
        elif cb_metrics["success_rate"] < 90:
            warnings.append(
                {
                    "severity": "warning",
                    "type": "low_success_rate",
                    "component": cb_name,
                    "message": f"Circuit breaker '{cb_name}' has low success rate: {cb_metrics['success_rate']}%",
                    "success_rate": cb_metrics["success_rate"],
                    "recommendation": "Investigate increased error rates",
                }
            )

    # Check rate limiters
    for rl_name, rl_metrics in metrics["rate_limiters"].items():
        utilization = rl_metrics.get("utilization_percent", 0)
        if utilization > 90:
            alerts.append(
                {
                    "severity": "critical",
                    "type": "rate_limit_high",
                    "component": rl_name,
                    "message": f"Rate limiter '{rl_name}' at {utilization}% capacity",
                    "utilization": utilization,
                    "recommendation": "Consider increasing rate limit or scaling service",
                }
            )
        elif utilization > 75:
            warnings.append(
                {
                    "severity": "warning",
                    "type": "rate_limit_elevated",
                    "component": rl_name,
                    "message": f"Rate limiter '{rl_name}' at {utilization}% capacity",
                    "utilization": utilization,
                    "recommendation": "Monitor traffic patterns",
                }
            )

    return {
        "timestamp": datetime.now().isoformat(),
        "alerts": alerts,
        "warnings": warnings,
        "summary": {
            "critical_alerts": len(alerts),
            "warnings": len(warnings),
        },
    }
