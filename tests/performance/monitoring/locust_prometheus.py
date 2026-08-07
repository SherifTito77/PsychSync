"""
Locust Prometheus Exporter

Exports Locust metrics to Prometheus for monitoring and alerting.
Provides real-time visibility into load test performance.

Metrics Exported:
- locust_requests_total: Total request count (by endpoint, method, status)
- locust_request_duration_seconds: Request duration histogram
- locust_users: Current number of users
- locust_failures: Total failure count (by endpoint, error)
- locust_rps: Requests per second
- locust_response_time_percentiles: p50, p95, p99 response times

Usage:
    # Start Prometheus exporter alongside Locust
    python locust_prometheus.py --port 9090

    # Or integrate with locust command
    locust -f baseline_scenarios.py --prometheus-port 9090

Prometheus Configuration:
    scrape_configs:
      - job_name: 'locust'
        static_configs:
          - targets: ['localhost:9090']

Grafana Dashboard:
    Import dashboard from: grafana_dashboard.json
"""

import logging
import time
from typing import Optional

from locust import events
from locust.runners import MasterRunner
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, start_http_server
from prometheus_client.exposition import generate_latest

logger = logging.getLogger(__name__)


# Prometheus metrics
REQUEST_COUNT = Counter(
    "locust_requests_total",
    "Total number of requests",
    ["endpoint", "method", "status"],
)

REQUEST_DURATION = Histogram(
    "locust_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint", "method"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

USER_COUNT = Gauge("locust_users", "Current number of users")

FAILURE_COUNT = Counter(
    "locust_failures_total", "Total number of failures", ["endpoint", "error"]
)

RPS = Gauge("locust_rps", "Current requests per second")

RESPONSE_TIME_P50 = Gauge(
    "locust_response_time_p50_seconds", "Median response time in seconds", ["endpoint"]
)

RESPONSE_TIME_P95 = Gauge(
    "locust_response_time_p95_seconds",
    "95th percentile response time in seconds",
    ["endpoint"],
)

RESPONSE_TIME_P99 = Gauge(
    "locust_response_time_p99_seconds",
    "99th percentile response time in seconds",
    ["endpoint"],
)

AVG_RESPONSE_TIME = Gauge(
    "locust_response_time_avg_seconds", "Average response time in seconds", ["endpoint"]
)


class LocustPrometheusExporter:
    """Exports Locust metrics to Prometheus"""

    def __init__(self, port: int = 9090):
        """
        Initialize Prometheus exporter.

        Args:
            port: Port to run Prometheus exporter on
        """
        self.port = port
        self.start_time = time.time()
        self.last_request_count = 0
        self.last_update_time = time.time()

        logger.info(f"Starting Prometheus exporter on port {port}")

    def start(self):
        """Start Prometheus HTTP server"""
        try:
            start_http_server(self.port)
            logger.info(
                f"✅ Prometheus exporter started on http://localhost:{self.port}"
            )
            logger.info(
                "Metrics available at: http://localhost:{}/metrics".format(self.port)
            )
        except Exception as e:
            logger.error(f"Failed to start Prometheus exporter: {e}")
            raise

    def register_handlers(self):
        """Register Locust event handlers"""
        events.request.add_listener(self.on_request)
        events.test_stop.add_listener(self.on_test_stop)

        logger.info("✅ Prometheus event handlers registered")

    def on_request(
        self, request_type, name, response_time, response_length, exception, **kwargs
    ):
        """
        Handle request event and update Prometheus metrics.

        Args:
            request_type: HTTP method (GET, POST, etc.)
            name: Request name
            response_time: Response time in milliseconds
            response_length: Response size in bytes
            exception: Exception if request failed
        """
        # Convert response time from milliseconds to seconds
        duration_seconds = response_time / 1000.0 if response_time else 0

        # Update request count
        status = "success" if exception is None else "failure"
        REQUEST_COUNT.labels(endpoint=name, method=request_type, status=status).inc()

        # Update request duration histogram
        REQUEST_DURATION.labels(endpoint=name, method=request_type).observe(
            duration_seconds
        )

    def on_test_stop(self, environment, **kwargs):
        """
        Handle test stop event and export final metrics.

        Args:
            environment: Locust environment
        """
        logger.info("Test stopped - exporting final metrics to Prometheus")

        stats = environment.stats

        # Export per-endpoint percentiles
        for entry in stats.entries.values():
            if entry.num_requests > 0:
                endpoint = entry.name

                # Response time percentiles (convert to seconds)
                p50 = entry.median_response_time / 1000.0
                p95 = entry.get_response_time_percentile(0.95) / 1000.0
                p99 = entry.get_response_time_percentile(0.99) / 1000.0
                avg = entry.avg_response_time / 1000.0

                RESPONSE_TIME_P50.labels(endpoint=endpoint).set(p50)
                RESPONSE_TIME_P95.labels(endpoint=endpoint).set(p95)
                RESPONSE_TIME_P99.labels(endpoint=endpoint).set(p99)
                AVG_RESPONSE_TIME.labels(endpoint=endpoint).set(avg)

        # Export aggregate stats
        if stats.total.num_requests > 0:
            total_p50 = stats.total.median_response_time / 1000.0
            total_p95 = stats.total.get_response_time_percentile(0.95) / 1000.0
            total_p99 = stats.total.get_response_time_percentile(0.99) / 1000.0

            RESPONSE_TIME_P50.labels(endpoint="TOTAL").set(total_p50)
            RESPONSE_TIME_P95.labels(endpoint="TOTAL").set(total_p95)
            RESPONSE_TIME_P99.labels(endpoint="TOTAL").set(total_p99)


def update_user_count(environment):
    """Update user count metric"""
    if hasattr(environment, "runner") and environment.runner:
        user_count = environment.runner.user_count
        USER_COUNT.set(user_count)


def update_rps(environment):
    """Update requests per second metric"""
    if hasattr(environment, "stats"):
        rps = environment.stats.total.total_rps
        RPS.set(rps)


def start_background_metrics_update(environment, interval: int = 5):
    """
    Start background task to update gauge metrics.

    Args:
        environment: Locust environment
        interval: Update interval in seconds
    """
    import threading

    def update_metrics():
        while True:
            try:
                update_user_count(environment)
                update_rps(environment)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                time.sleep(interval)

    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()

    logger.info(f"Started background metrics update (interval: {interval}s)")


# Initialize exporter
_exporter: Optional[LocustPrometheusExporter] = None


def init_prometheus_exporter(port: int = 9090, environment=None):
    """
    Initialize Prometheus exporter for Locust.

    Args:
        port: Port to run exporter on
        environment: Locust environment

    Usage in locustfile:
        from locust_prometheus import init_prometheus_exporter

        @events.test_start.add_listener
        def on_test_start(environment, **kwargs):
            init_prometheus_exporter(port=9090, environment=environment)
    """
    global _exporter

    if _exporter is None:
        _exporter = LocustPrometheusExporter(port)
        _exporter.start()
        _exporter.register_handlers()

        if environment:
            start_background_metrics_update(environment)

        logger.info("✅ Prometheus exporter initialized")
    else:
        logger.warning("Prometheus exporter already initialized")


if __name__ == "__main__":
    import sys

    # Standalone Prometheus exporter (for testing)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090

    print(
        f"""
╔══════════════════════════════════════════════════════════════════════╗
║              Locust Prometheus Exporter                               ║
╚══════════════════════════════════════════════════════════════════════╝

Starting Prometheus metrics exporter on port {port}...

Metrics will be available at:
  http://localhost:{port}/metrics

Prometheus Configuration:
  Add to prometheus.yml:

  scrape_configs:
    - job_name: 'locust'
      static_configs:
        - targets: ['localhost:{port}']
      scrape_interval: 5s

Grafana Dashboard:
  Import the dashboard from grafana_dashboard.json

Press Ctrl+C to stop

    """
    )

    try:
        start_http_server(port)
        logger.info(f"Prometheus exporter running on port {port}")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Prometheus exporter stopped")
