"""
Integration Monitoring API Endpoints

This module provides API endpoints for monitoring external integration points:
- Database connectivity and performance
- Redis cache health
- HRIS connector status
- Email service availability
- Circuit breaker states

All endpoints return metrics for observability and health checks.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.core.rate_limiter_unified import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(tags=["integration-monitoring"])


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    timestamp: str
    checks: dict[str, str]


@router.get("/integration-health")
@rate_limit(limit=60, window=60)
async def get_integration_health() -> HealthResponse:
    """
    Get health status of all integration points (Database, Redis, HRIS, Email)

    Returns simplified health status for quick checks - no authentication required
    for use with load balancers and monitoring systems.

    Returns:
        JSON with overall status and individual component checks
    """
    try:
        from app.monitoring.integration_metrics import get_health_status

        result = await get_health_status()
        return HealthResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get integration health: {e}")
        return HealthResponse(
            status="unknown",
            timestamp=datetime.utcnow().isoformat(),
            checks={"error": str(e)},
        )


@router.get("/integration-metrics")
@rate_limit(limit=30, window=60)
async def get_integration_metrics() -> dict:
    """
    Get detailed metrics from all integration points

    Includes:
    - Database: success rate, response times, circuit breaker state
    - Redis: success rate, response times, circuit breaker state
    - HRIS: per-connector metrics
    - Email: provider status
    - Overall health summary
    """
    try:
        from app.monitoring.integration_metrics import get_all_integration_metrics

        return await get_all_integration_metrics()
    except Exception as e:
        logger.error(f"Failed to get integration metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve integration metrics: {str(e)}"
        ) from e


@router.get("/integration-metrics/prometheus", response_class=Response)
@rate_limit(limit=30, window=60)
async def get_integration_prometheus_metrics() -> Response:
    """
    Export integration metrics in Prometheus text format

    Returns metrics in Prometheus-compatible text format for scraping.
    Includes all integration metrics with proper labels and types.
    """
    try:
        from app.monitoring.integration_metrics import (
            format_metrics_for_prometheus,
            get_all_integration_metrics,
        )

        metrics = await get_all_integration_metrics()
        prometheus_text = format_metrics_for_prometheus(metrics)

        return Response(
            content=prometheus_text,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except Exception as e:
        logger.error(f"Failed to generate integration metrics: {e}")
        error_metrics = """# Integration metrics unavailable
psychsync_integration_metrics_up 0
"""
        return Response(content=error_metrics, media_type="text/plain", status_code=503)


@router.get("/integration-dashboard", response_class=Response)
@rate_limit(limit=30, window=60)
async def get_integration_dashboard() -> Response:
    """
    HTML Dashboard for Integration Metrics

    Returns a self-contained HTML dashboard with auto-refresh.
    Displays all integration metrics in a human-friendly format.
    No authentication required for easy access.
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PsychSync Integration Health</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            color: #667eea;
            font-size: 28px;
            margin-bottom: 10px;
        }

        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 16px;
        }

        .status-healthy {
            background: #d4edda;
            color: #155724;
        }

        .status-degraded {
            background: #fff3cd;
            color: #856404;
        }

        .status-unhealthy {
            background: #f8d7da;
            color: #721c24;
        }

        .last-update {
            color: #6c757d;
            font-size: 14px;
            margin-top: 10px;
        }

        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .summary-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .summary-card h3 {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 10px;
        }

        .summary-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }

        .section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .section h2 {
            color: #333;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .metric {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }

        .metric-label {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 5px;
        }

        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }

        .metric-value.good {
            color: #28a745;
        }

        .metric-value.warning {
            color: #ffc107;
        }

        .metric-value.bad {
            color: #dc3545;
        }

        .circuit-breaker {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .circuit-closed {
            background: #d4edda;
            color: #155724;
        }

        .circuit-open {
            background: #f8d7da;
            color: #721c24;
        }

        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 18px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p>Loading integration metrics...</p>
        </div>

        <div id="content" style="display: none;">
            <div class="header">
                <h1>🔌 Integration Health Dashboard</h1>
                <div>
                    <span id="overall-status" class="status-badge">Checking...</span>
                </div>
                <p class="last-update">Last updated: <span id="last-update">-</span></p>
                <p style="margin-top: 15px; color: #6c757d; font-size: 13px;">
                    Auto-refreshes every 30 seconds
                </p>
            </div>

            <div class="summary">
                <div class="summary-card">
                    <h3>Total Integrations</h3>
                    <div class="value" id="total-count">-</div>
                </div>
                <div class="summary-card">
                    <h3>Healthy</h3>
                    <div class="value" id="healthy-count" style="color: #28a745;">-</div>
                </div>
                <div class="summary-card">
                    <h3>Degraded</h3>
                    <div class="value" id="degraded-count" style="color: #ffc107;">-</div>
                </div>
                <div class="summary-card">
                    <h3>Failed</h3>
                    <div class="value" id="failed-count" style="color: #dc3545;">-</div>
                </div>
            </div>

            <div class="section">
                <h2>🗄️ Database</h2>
                <div id="database-metrics" class="metric-grid">
                    <p>Loading...</p>
                </div>
            </div>

            <div class="section">
                <h2>⚡ Redis Cache</h2>
                <div id="redis-metrics" class="metric-grid">
                    <p>Loading...</p>
                </div>
            </div>

            <div class="section">
                <h2>🏢 HRIS Connectors</h2>
                <div id="hris-metrics">
                    <p>Loading...</p>
                </div>
            </div>

            <div class="section">
                <h2>📧 Email Service</h2>
                <div id="email-metrics" class="metric-grid">
                    <p>Loading...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function formatNumber(num) {
            if (typeof num !== 'number') return '-';
            return num.toLocaleString();
        }

        function formatPercent(num) {
            if (typeof num !== 'number') return '-';
            return num.toFixed(1) + '%';
        }

        function getStatusClass(status) {
            switch(status) {
                case 'ok': return 'good';
                case 'degraded': return 'warning';
                case 'down': return 'bad';
                default: return '';
            }
        }

        function getCircuitBreakerClass(state) {
            switch(state) {
                case 'closed': return 'circuit-closed';
                case 'open': return 'circuit-open';
                default: return '';
            }
        }

        function getOverallStatusClass(status) {
            switch(status) {
                case 'healthy': return 'status-healthy';
                case 'degraded': return 'status-degraded';
                case 'unhealthy': return 'status-unhealthy';
                default: return '';
            }
        }

        function renderMetric(label, value, unit = '', statusClass = '') {
            return `
                <div class="metric">
                    <div class="metric-label">${label}</div>
                    <div class="metric-value ${statusClass}">${formatNumber(value)}${unit}</div>
                </div>
            `;
        }

        function renderDatabaseMetrics(db) {
            if (!db || db.error) {
                return `<p style="color: #dc3545;">Database metrics unavailable: ${db?.error || 'Unknown error'}</p>`;
            }

            return `
                ${renderMetric('Total Calls', db.total_calls)}
                ${renderMetric('Success Rate', db.success_rate, '%', getStatusClass(db.success_rate > 95 ? 'ok' : db.success_rate > 85 ? 'degraded' : 'down'))}
                ${renderMetric('Avg Response', db.avg_response_time_ms, 'ms', db.avg_response_time_ms < 100 ? 'good' : db.avg_response_time_ms < 500 ? 'warning' : 'bad')}
                <div class="metric">
                    <div class="metric-label">Circuit Breaker</div>
                    <div><span class="circuit-breaker ${getCircuitBreakerClass(db.circuit_breaker_state)}">${db.circuit_breaker_state?.toUpperCase() || 'UNKNOWN'}</span></div>
                </div>
                ${renderMetric('Failed Calls', db.failed_calls)}
            `;
        }

        function renderRedisMetrics(redis) {
            if (!redis || redis.error) {
                return `<p style="color: #dc3545;">Redis metrics unavailable: ${redis?.error || 'Unknown error'}</p>`;
            }

            return `
                ${renderMetric('Total Calls', redis.total_calls)}
                ${renderMetric('Success Rate', redis.success_rate, '%', getStatusClass(redis.success_rate > 90 ? 'ok' : redis.success_rate > 75 ? 'degraded' : 'down'))}
                ${renderMetric('Avg Response', redis.avg_response_time_ms, 'ms', redis.avg_response_time_ms < 50 ? 'good' : redis.avg_response_time_ms < 100 ? 'warning' : 'bad')}
                <div class="metric">
                    <div class="metric-label">Circuit Breaker</div>
                    <div><span class="circuit-breaker ${getCircuitBreakerClass(redis.circuit_breaker_state)}">${redis.circuit_breaker_state?.toUpperCase() || 'UNKNOWN'}</span></div>
                </div>
                ${renderMetric('Failed Calls', redis.failed_calls)}
            `;
        }

        function renderHRISMetrics(hris) {
            if (!hris || Object.keys(hris).length === 0) {
                return `<p style="color: #6c757d;">No HRIS connectors configured</p>`;
            }

            let html = '';
            for (const [name, metrics] of Object.entries(hris)) {
                if (metrics.error) {
                    html += `<div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <strong>${name}</strong>: ${metrics.error}
                    </div>`;
                    continue;
                }

                html += `
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <h4 style="margin-bottom: 10px; color: #333;">${name}</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 14px;">
                            <div><strong>Status:</strong> <span class="circuit-breaker ${getCircuitBreakerClass(metrics.circuit_breaker_state)}">${metrics.circuit_breaker_state?.toUpperCase()}</span></div>
                            <div><strong>Success Rate:</strong> ${formatPercent(metrics.success_rate)}</div>
                            <div><strong>Avg Time:</strong> ${formatNumber(metrics.avg_response_time_ms)}ms</div>
                            <div><strong>Total Calls:</strong> ${formatNumber(metrics.total_calls)}</div>
                            <div><strong>Failed:</strong> ${formatNumber(metrics.failed_calls)}</div>
                        </div>
                    </div>
                `;
            }
            return html;
        }

        function renderEmailMetrics(email) {
            if (!email || email.status === 'not_available' || email.error) {
                return `<p style="color: #6c757d;">Email service metrics not available</p>`;
            }

            return `
                <div class="metric">
                    <div class="metric-label">Status</div>
                    <div class="metric-value ${email.status === 'available' ? 'good' : 'warning'}">${email.status}</div>
                </div>
            `;
        }

        async function loadMetrics() {
            try {
                const response = await fetch('/api/v1/integration-metrics');
                const data = await response.json();

                // Hide loading, show content
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';

                // Update header
                const summary = data.summary || {};
                document.getElementById('overall-status').textContent = (summary.overall_status || 'unknown').toUpperCase();
                document.getElementById('overall-status').className = 'status-badge ' + getOverallStatusClass(summary.overall_status);
                document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleString();

                // Update summary cards
                document.getElementById('total-count').textContent = formatNumber(summary.total_integrations || 0);
                document.getElementById('healthy-count').textContent = formatNumber(summary.healthy_integrations || 0);
                document.getElementById('degraded-count').textContent = formatNumber(summary.degraded_integrations || 0);
                document.getElementById('failed-count').textContent = formatNumber(summary.failed_integrations || 0);

                // Update sections
                document.getElementById('database-metrics').innerHTML = renderDatabaseMetrics(data.database);
                document.getElementById('redis-metrics').innerHTML = renderRedisMetrics(data.redis);
                document.getElementById('hris-metrics').innerHTML = renderHRISMetrics(data.hris);
                document.getElementById('email-metrics').innerHTML = renderEmailMetrics(data.email);

            } catch (error) {
                document.getElementById('loading').innerHTML = `
                    <div class="error-message">
                        <h3>⚠️ Failed to load metrics</h3>
                        <p>${error.message}</p>
                        <button onclick="location.reload()" style="margin-top: 15px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">
                            Retry
                        </button>
                    </div>
                `;
            }
        }

        // Initial load
        loadMetrics();

        // Auto-refresh every 30 seconds
        setInterval(loadMetrics, 30000);
    </script>
</body>
</html>
    """

    return Response(content=html_content, media_type="text/html")
