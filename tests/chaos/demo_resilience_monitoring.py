#!/usr/bin/env python3
"""
Resilience Monitoring Demo Script

Demonstrates the resilience monitoring capabilities without requiring
the full API server to be running.
"""

import asyncio
import json
from datetime import datetime

from app.core.resilience import (
    CircuitBreaker,
    CircuitState,
    ErrorType,
    RateLimiter,
    get_resilience_manager,
)


async def monitor_resilience():
    """Demonstrate resilience monitoring capabilities"""

    print("=" * 80)
    print("🔍 PSYCHSYNC RESILIENCE MONITORING DASHBOARD")
    print("=" * 80)
    print()

    manager = get_resilience_manager()

    # Create example circuit breakers (these would normally be created by your services)
    print("📊 Initializing Circuit Breakers...")
    print("-" * 80)

    # HRIS circuit breaker
    hris_cb = manager.create_circuit_breaker(
        name="hris_bamboohr",
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=3,
        timeout=30.0,
    )
    print("  ✓ HRIS BambooHR circuit breaker initialized")

    # Email OAuth circuit breaker
    email_cb = manager.create_circuit_breaker(
        name="email_oauth",
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=15.0,
    )
    print("  ✓ Email OAuth circuit breaker initialized")

    # Cache circuit breaker
    cache_cb = manager.create_circuit_breaker(
        name="redis_cache",
        failure_threshold=10,
        recovery_timeout=30.0,
        success_threshold=3,
        timeout=5.0,
    )
    print("  ✓ Redis Cache circuit breaker initialized")

    print()

    # Simulate some activity
    print("🔄 Simulating Service Activity...")
    print("-" * 80)

    async def mock_hris_call():
        """Mock HRIS API call"""
        await asyncio.sleep(0.01)
        return {"employees": 100}

    async def mock_oauth_call():
        """Mock OAuth token refresh"""
        await asyncio.sleep(0.01)
        return {"access_token": "xyz789"}

    # Make some successful calls
    for i in range(3):
        await hris_cb.call(mock_hris_call)
        await email_cb.call(mock_oauth_call)

    print("  ✓ 3 successful calls to each service")
    print()

    # Display overall health
    print("🏥 RESILIENCE HEALTH CHECK")
    print("-" * 80)

    all_metrics = manager.get_all_metrics()

    # Analyze circuit states
    open_circuits = []
    half_open_circuits = []
    healthy_circuits = []

    for cb_name, cb_metrics in all_metrics["circuit_breakers"].items():
        state = cb_metrics["state"]
        if state == "open":
            open_circuits.append(cb_name)
        elif state == "half_open":
            half_open_circuits.append(cb_name)
        else:
            healthy_circuits.append(cb_name)

    total_cbs = len(all_metrics["circuit_breakers"])

    # Determine overall health
    if len(open_circuits) > total_cbs * 0.5:
        overall_status = "DEGRADED"
        status_emoji = "🔴"
    elif len(open_circuits) > 0:
        overall_status = "WARNING"
        status_emoji = "🟡"
    else:
        overall_status = "HEALTHY"
        status_emoji = "🟢"

    print(f"  Overall Status: {status_emoji} {overall_status}")
    print(f"  Total Circuit Breakers: {total_cbs}")
    print(f"  Open (Failing Fast): {len(open_circuits)}")
    print(f"  Half-Open (Recovering): {len(half_open_circuits)}")
    print(f"  Closed (Healthy): {len(healthy_circuits)}")
    print()

    # Display detailed circuit breaker states
    print("📈 CIRCUIT BREAKER DETAILS")
    print("-" * 80)

    for cb_name, cb in manager.circuit_breakers.items():
        metrics = cb.get_metrics()

        # Calculate health status
        state = metrics["state"]
        if state == "closed":
            health = "🟢 Healthy"
        elif state == "half_open":
            health = "🟡 Recovering"
        else:
            health = "🔴 Unhealthy"

        print(f"\n  [{cb_name}]")
        print(f"    State: {state.upper()} {health}")
        print(f"    Success Rate: {metrics['success_rate']}%")
        print(f"    Avg Response: {metrics['avg_response_time']:.2f}ms")
        print(f"    Failures: {metrics['failure_count']}")
        print(f"    Total Calls: {metrics['total_calls']}")

        # Add recommendations based on state
        if state == "closed" and metrics["success_rate"] < 90:
            print(f"    ⚠️  Warning: Low success rate - investigate service health")
        elif state == "open":
            print(f"    🚨 Action: Check external service availability immediately")

    print()

    # Display alerts and warnings
    print("🚨 ALERTS AND WARNINGS")
    print("-" * 80)

    alerts = []
    warnings = []

    for cb_name, cb_metrics in all_metrics["circuit_breakers"].items():
        if cb_metrics["state"] == "open":
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "component": cb_name,
                    "message": f"Circuit breaker '{cb_name}' is OPEN - failing fast",
                }
            )
        elif cb_metrics["success_rate"] < 90:
            warnings.append(
                {
                    "severity": "WARNING",
                    "component": cb_name,
                    "message": f"Low success rate ({cb_metrics['success_rate']}%) on {cb_name}",
                }
            )

    if not alerts and not warnings:
        print("  ✅ No alerts or warnings - all systems operating normally")
    else:
        if alerts:
            print(f"\n  Alerts ({len(alerts)}):")
            for alert in alerts:
                print(f"    🔴 {alert['severity']}: {alert['message']}")

        if warnings:
            print(f"\n  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"    🟡 {warning['severity']}: {warning['message']}")

    print()
    print("=" * 80)
    print("💡 NEXT STEPS")
    print("-" * 80)
    print("1. Monitor circuit breaker states regularly")
    print("2. Set up alerts for state changes")
    print("3. Review runbooks for incident response")
    print("4. Run chaos tests to validate resilience")
    print()
    print("📚 Documentation:")
    print("  - SYSTEM_BOUNDARY_RESILIENCE_REPORT.md - Technical details")
    print("  - OPERATIONAL_RUNBOOKS.md - Incident procedures")
    print("  - IMPLEMENTATION_SUMMARY_RESILIENCE.md - Executive summary")
    print()
    print(f"✅ Monitoring complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(monitor_resilience())
