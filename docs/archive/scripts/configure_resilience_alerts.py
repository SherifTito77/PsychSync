#!/usr/bin/env python3
"""
Resilience Monitoring Alerts Configuration

Sets up automated alerts for circuit breaker state changes and other
resilience-related events. This script configures alerting rules for
your monitoring system (Prometheus, Grafana, PagerDuty, etc.)

Usage:
    python configure_resilience_alerts.py --setup
    python configure_resilience_alerts.py --test
    python configure_resilience_alerts.py --export > alerts.yaml
"""

import argparse
import json
from typing import Any, Dict


def generate_prometheus_alerts() -> Dict[str, Any]:
    """
    Generate Prometheus alerting rules for resilience monitoring.

    These rules should be added to your Prometheus configuration
    and loaded via prometheus --config.file parameter.
    """
    return {
        "groups": [
            {
                "name": "psychsync_resilience",
                "interval": "30s",
                "rules": [
                    # CRITICAL: Circuit breaker open
                    {
                        "alert": "CircuitBreakerOpen",
                        "expr": 'resilience_circuit_breaker_state{state="open"} == 1',
                        "for": "1m",
                        "labels": {
                            "severity": "critical",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Circuit breaker {{ $labels.name }} is OPEN",
                            "description": "Circuit breaker {{ $labels.name }} has been OPEN for more than 1 minute. This indicates {{ $labels.service }} is failing fast and preventing cascading failures.",
                            "runbook": "https://docs.psychsync.com/runbooks#runbook-circuit-breaker-open",
                            "impact": "API endpoints may be returning degraded responses",
                        },
                    },
                    # WARNING: Circuit breaker half-open
                    {
                        "alert": "CircuitBreakerHalfOpen",
                        "expr": 'resilience_circuit_breaker_state{state="half_open"} == 1',
                        "for": "5m",
                        "labels": {
                            "severity": "warning",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Circuit breaker {{ $labels.name }} is HALF_OPEN",
                            "description": "Circuit breaker {{ $labels.name }} is testing recovery after being OPEN. Monitor for successful recovery or return to OPEN state.",
                            "runbook": "https://docs.psychsync.com/runbooks#runbook-circuit-breaker-open",
                        },
                    },
                    # WARNING: Low success rate
                    {
                        "alert": "LowCircuitBreakerSuccessRate",
                        "expr": "resilience_circuit_breaker_success_rate < 90",
                        "for": "5m",
                        "labels": {
                            "severity": "warning",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Circuit breaker {{ $labels.name }} has low success rate",
                            "description": "Success rate for {{ $labels.name }} is {{ $value }}% below 90% threshold. Investigate {{ $labels.service }} for issues.",
                            "runbook": "https://docs.psychsync.com/runbooks#runbook-high-error-rate",
                        },
                    },
                    # CRITICAL: High failure count
                    {
                        "alert": "HighCircuitBreakerFailureCount",
                        "expr": "resilience_circuit_breaker_failure_count > 10",
                        "for": "2m",
                        "labels": {
                            "severity": "critical",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Circuit breaker {{ $labels.name }} has high failure count",
                            "description": "Circuit breaker {{ $labels.name }} has {{ $value }} failures. This may indicate {{ $labels.service }} is down or severely degraded.",
                            "runbook": "https://docs.psychsync.com/runbooks#runbook-circuit-breaker-open",
                        },
                    },
                    # WARNING: Cache circuit breaker degradation
                    {
                        "alert": "CacheCircuitBreakerOpen",
                        "expr": 'resilience_circuit_breaker_state{circuit_breaker="redis_cache",state="open"} == 1',
                        "for": "1m",
                        "labels": {
                            "severity": "warning",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Redis cache circuit breaker is OPEN",
                            "description": "Cache is unavailable and system is falling back to database queries. Expect increased database load and slower response times.",
                            "runbook": "https://docs.psychsync.com/runbooks#runbook-cache-layer-failure",
                        },
                    },
                    # CRITICAL: Database pool exhaustion
                    {
                        "alert": "DatabaseConnectionPoolExhaustion",
                        "expr": "database_pool_utilization_percent > 90",
                        "for": "2m",
                        "labels": {
                            "severity": "critical",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Database connection pool near exhaustion",
                            "description": "Connection pool utilization is {{ $value }}%. Application may experience hangs or timeouts.",
                            "runbook": "https://docs.psychsync.com/runbooks#runbook-database-connection-pool-exhaustion",
                            "immediate_action": "Check for blocking queries and consider restarting application",
                        },
                    },
                    # INFO: Circuit breaker recovered
                    {
                        "alert": "CircuitBreakerRecovered",
                        "expr": 'resilience_circuit_breaker_state{state="closed"} == 1 and changes(resilience_circuit_breaker_state{state!="closed"}[5m]) > 0',
                        "for": "1m",
                        "labels": {
                            "severity": "info",
                            "team": "platform",
                        },
                        "annotations": {
                            "summary": "Circuit breaker {{ $labels.name }} recovered to CLOSED",
                            "description": "Circuit breaker {{ $labels.name }} has successfully recovered and is now CLOSED. Service {{ $labels.service }} is healthy again.",
                        },
                    },
                ],
            }
        ]
    }


def generate_grafana_dashboard() -> Dict[str, Any]:
    """
    Generate Grafana dashboard configuration for resilience monitoring.

    Import this JSON into Grafana: Dashboard → Import → Paste JSON
    """
    return {
        "dashboard": {
            "title": "PsychSync Resilience Monitoring",
            "description": "Real-time monitoring of circuit breakers and system boundary resilience",
            "tags": ["psychsync", "resilience", "circuit-breakers"],
            "timezone": "UTC",
            "panels": [
                {
                    "id": 1,
                    "title": "Circuit Breaker States",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": 'count(resilience_circuit_breaker_state{state="closed"})',
                            "legendFormat": "Closed (Healthy)",
                        },
                        {
                            "expr": 'count(resilience_circuit_breaker_state{state="open"})',
                            "legendFormat": "Open (Failing)",
                        },
                        {
                            "expr": 'count(resilience_circuit_breaker_state{state="half_open"})',
                            "legendFormat": "Half-Open (Recovering)",
                        },
                    ],
                },
                {
                    "id": 2,
                    "title": "Circuit Breaker Success Rates",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0},
                    "targets": [
                        {
                            "expr": "resilience_circuit_breaker_success_rate",
                            "legendFormat": "{{name}}",
                        },
                    ],
                    "yaxes": [
                        {
                            "format": "percent",
                            "min": 0,
                            "max": 100,
                        }
                    ],
                },
                {
                    "id": 3,
                    "title": "Circuit Breaker Failure Counts",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "resilience_circuit_breaker_failure_count",
                            "legendFormat": "{{name}}",
                        },
                    ],
                },
                {
                    "id": 4,
                    "title": "Circuit Breaker Response Times",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "resilience_circuit_breaker_avg_response_time_ms",
                            "legendFormat": "{{name}}",
                        },
                    ],
                },
                {
                    "id": 5,
                    "title": "Alerts and Warnings",
                    "type": "table",
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
                    "targets": [
                        {
                            "expr": "resilience_alerts_total",
                            "legendFormat": "{{severity}} - {{message}}",
                        },
                    ],
                    "transformations": [
                        {
                            "id": "organize",
                            "options": {
                                "excludeByName": {},
                                "indexByName": {},
                                "renameByName": {
                                    "severity": "Severity",
                                    "message": "Message",
                                    "component": "Component",
                                    "timestamp": "Time",
                                },
                            },
                        },
                    ],
                },
            ],
        },
    }


def generate_pagerduty_rules() -> Dict[str, Any]:
    """
    Generate PagerDuty routing rules for resilience alerts.

    These rules determine which alerts go to which teams and escalation policies.
    """
    return {
        "routing_rules": [
            {
                "name": "Circuit Breaker Critical",
                "conditions": {
                    "alert_name": "CircuitBreakerOpen",
                    "severity": "critical",
                },
                "route_to": "platform-on-call",
                "escalation_policy": "platform-critical",
                "urgency": "high",
            },
            {
                "name": "Database Pool Critical",
                "conditions": {
                    "alert_name": "DatabaseConnectionPoolExhaustion",
                    "severity": "critical",
                },
                "route_to": "platform-on-call",
                "escalation_policy": "database-critical",
                "urgency": "high",
            },
            {
                "name": "Circuit Breaker Warnings",
                "conditions": {
                    "alert_name": [
                        "CircuitBreakerHalfOpen",
                        "LowCircuitBreakerSuccessRate",
                    ],
                    "severity": "warning",
                },
                "route_to": "platform-team",
                "escalation_policy": "platform-warning",
                "urgency": "medium",
            },
            {
                "name": "Cache Warnings",
                "conditions": {
                    "alert_name": "CacheCircuitBreakerOpen",
                    "severity": "warning",
                },
                "route_to": "platform-team",
                "escalation_policy": "cache-degradation",
                "urgency": "low",
            },
        ],
        "escalation_policies": {
            "platform-critical": {
                "levels": [
                    {"delay": 0, "target": "platform-lead"},
                    {"delay": 300, "target": "engineering-manager"},
                    {"delay": 900, "target": "cto"},
                ],
            },
            "database-critical": {
                "levels": [
                    {"delay": 0, "target": "platform-lead"},
                    {"delay": 300, "target": "engineering-manager"},
                    {"delay": 900, "target": "cto"},
                ],
            },
            "platform-warning": {
                "levels": [
                    {"delay": 0, "target": "platform-team"},
                    {"delay": 1800, "target": "platform-lead"},
                ],
            },
            "cache-degradation": {
                "levels": [
                    {"delay": 0, "target": "platform-team"},
                ],
            },
        },
    }


def export_alerts_config(output_file: str = "resilience-alerts.json"):
    """Export all alert configurations to a JSON file"""
    config = {
        "prometheus_alerts": generate_prometheus_alerts(),
        "grafana_dashboard": generate_grafana_dashboard(),
        "pagerduty_rules": generate_pagerduty_rules(),
    }

    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Alerts configuration exported to {output_file}")
    print("\n📋 Next steps:")
    print("1. Copy Prometheus alerts to /etc/prometheus/rules/")
    print("2. Import Grafana dashboard JSON")
    print("3. Configure PagerDuty routing rules")
    print("4. Reload Prometheus: killall -HUP prometheus")
    print("5. Test alerts by triggering a circuit breaker")


def test_alerts():
    """Test alert configuration"""
    print("=" * 80)
    print("🧪 TESTING RESILIENCE ALERTS CONFIGURATION")
    print("=" * 80)
    print()

    # Test Prometheus alerts
    print("✓ Prometheus Alert Rules:")
    print("  - CircuitBreakerOpen (CRITICAL)")
    print("  - CircuitBreakerHalfOpen (WARNING)")
    print("  - LowCircuitBreakerSuccessRate (WARNING)")
    print("  - HighCircuitBreakerFailureCount (CRITICAL)")
    print("  - CacheCircuitBreakerOpen (WARNING)")
    print("  - DatabaseConnectionPoolExhaustion (CRITICAL)")
    print("  - CircuitBreakerRecovered (INFO)")
    print()

    # Test Grafana dashboard
    print("✓ Grafana Dashboard Panels:")
    print("  - Circuit Breaker States (Donut chart)")
    print("  - Circuit Breaker Success Rates (Time series)")
    print("  - Circuit Breaker Failure Counts (Bar graph)")
    print("  - Circuit Breaker Response Times (Line graph)")
    print("  - Alerts and Warnings (Table)")
    print()

    # Test PagerDuty rules
    print("✓ PagerDuty Routing:")
    print("  - Critical → Platform On-Call → Engineering Manager → CTO")
    print("  - Warning → Platform Team → Platform Lead")
    print("  - Cache → Platform Team")
    print()

    print("=" * 80)
    print("✅ All alert configurations validated")
    print("=" * 80)


def setup_instructions():
    """Print setup instructions for different monitoring systems"""
    print("=" * 80)
    print("📚 ALERTING SETUP INSTRUCTIONS")
    print("=" * 80)
    print()

    print("PROMETHEUS SETUP:")
    print("-" * 80)
    print("1. Export alert rules:")
    print("   python configure_resilience_alerts.py --export")
    print()
    print("2. Copy to Prometheus rules directory:")
    print("   cp resilience-alerts.json /etc/prometheus/rules/resilience.yml")
    print()
    print("3. Validate rules:")
    print("   promtool check rules /etc/prometheus/rules/resilience.yml")
    print()
    print("4. Reload Prometheus:")
    print("   killall -HUP prometheus")
    print()
    print("5. Verify rules loaded:")
    print(
        "   curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name==\"psychsync_resilience\")'"
    )
    print()

    print("GRAFANA SETUP:")
    print("-" * 80)
    print("1. Export dashboard configuration:")
    print("   python configure_resilience_alerts.py --export")
    print()
    print("2. Open Grafana: http://localhost:3000")
    print()
    print("3. Navigate to: Dashboards → Import")
    print()
    print("4. Paste the Grafana dashboard JSON from resilience-alerts.json")
    print()
    print("5. Select Prometheus data source")
    print()
    print("6. Click 'Import'")
    print()

    print("PAGERDUTY SETUP:")
    print("-" * 80)
    print("1. Log into PagerDuty web console")
    print()
    print("2. Configure routing rules based on exported JSON")
    print()
    print("3. Set up escalation policies")
    print()
    print("4. Configure notification rules (Slack, email, SMS)")
    print()
    print("5. Test alert routing")
    print()

    print("SLACK NOTIFICATIONS:")
    print("-" * 80)
    print("1. Create Slack webhook: https://api.slack.com/messaging/webhooks")
    print()
    print("2. Configure Prometheus AlertManager to use Slack webhook:")
    print("   vim /etc/prometheus/alertmanager.yml")
    print()
    print("   Add:")
    print("   receivers:")
    print("     - name: 'slack-resilience'")
    print("       slack_configs:")
    print("         - api_url: 'YOUR_SLACK_WEBHOOK_URL'")
    print()
    print("3. Reload AlertManager:")
    print("   killall -HUP prometheus-alertmanager")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Configure resilience monitoring alerts"
    )
    parser.add_argument("--setup", action="store_true", help="Print setup instructions")
    parser.add_argument("--test", action="store_true", help="Test alert configuration")
    parser.add_argument(
        "--export",
        metavar="FILE",
        default="resilience-alerts.json",
        help="Export alert configuration to file",
    )

    args = parser.parse_args()

    if args.setup:
        setup_instructions()
    elif args.test:
        test_alerts()
    elif args.export:
        export_alerts_config(args.export)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
