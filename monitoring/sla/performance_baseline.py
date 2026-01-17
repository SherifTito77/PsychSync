#!/usr/bin/env python3
"""
PsychSync Performance Baselining and SLA Monitoring
Automated performance monitoring with SLA compliance tracking
"""

import asyncio
import aiohttp
import time
import json
import logging
import statistics
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse

import prometheus_client
from prometheus_client import start_http_server, Gauge, Histogram, Counter, Info

# Configuration
PROMETHEUS_URL = "http://prometheus:9090"
SLA_CONFIG_FILE = "/etc/sla/config.json"
BASELINE_CONFIG_FILE = "/etc/baseline/config.json"
REPORT_OUTPUT_DIR = "/tmp/sla_reports"
METRICS_PORT = 8083

# SLA Metrics
SLA_COMPLIANCE = Gauge('psychsync_sla_compliance_percentage', 'SLA compliance percentage', ['sla_type'])
PERFORMANCE_BASELINE = Gauge('psychsync_performance_baseline_ms', 'Performance baseline value', ['metric_name'])
PERFORMANCE_CURRENT = Gauge('psychsync_performance_current_ms', 'Current performance value', ['metric_name'])
SLA_VIOLATIONS = Counter('psychsync_sla_violations_total', 'SLA violations', ['sla_type', 'severity'])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SLAConfig:
    """SLA configuration definition"""
    name: str
    metric: str
    query: str
    threshold: float
    comparison: str  # 'lt', 'gt', 'lte', 'gte'
    window: str  # Prometheus time window
    description: str
    business_impact: str
    weight: float = 1.0  # Weight for overall SLA calculation


@dataclass
class PerformanceBaseline:
    """Performance baseline definition"""
    name: str
    metric: str
    query: str
    baseline_period: str  # e.g., '7d', '30d'
    aggregation: str  # 'avg', 'p50', 'p95', 'p99'
    description: str


@dataclass
class SLAViolation:
    """SLA violation record"""
    timestamp: datetime
    sla_type: str
    current_value: float
    threshold: float
    severity: str
    duration: Optional[float] = None


class PerformanceMonitor:
    """Performance monitoring and SLA compliance tracking"""

    def __init__(self):
        self.session = None
        self.sla_configs = []
        self.performance_baselines = []
        self.violations = []
        self.compliance_history = []

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def load_configurations(self):
        """Load SLA and baseline configurations"""
        # Load SLA configurations
        try:
            with open(SLA_CONFIG_FILE, 'r') as f:
                sla_data = json.load(f)
                self.sla_configs = [SLAConfig(**config) for config in sla_data.get('slas', [])]
            logger.info(f"Loaded {len(self.sla_configs)} SLA configurations")
        except FileNotFoundError:
            logger.warning(f"SLA config file not found: {SLA_CONFIG_FILE}")
            self.sla_configs = self._get_default_sla_configs()

        # Load baseline configurations
        try:
            with open(BASELINE_CONFIG_FILE, 'r') as f:
                baseline_data = json.load(f)
                self.performance_baselines = [PerformanceBaseline(**config)
                                           for config in baseline_data.get('baselines', [])]
            logger.info(f"Loaded {len(self.performance_baselines)} baseline configurations")
        except FileNotFoundError:
            logger.warning(f"Baseline config file not found: {BASELINE_CONFIG_FILE}")
            self.performance_baselines = self._get_default_baselines()

    def _get_default_sla_configs(self) -> List[SLAConfig]:
        """Get default SLA configurations"""
        return [
            SLAConfig(
                name="api_response_time_p95",
                metric="response_time_p95",
                query="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                threshold=1.0,
                comparison="lt",
                window="5m",
                description="P95 API response time",
                business_impact="User experience and satisfaction",
                weight=0.3
            ),
            SLAConfig(
                name="api_error_rate",
                metric="error_rate",
                query="rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
                threshold=0.01,
                comparison="lt",
                window="5m",
                description="API error rate",
                business_impact="Service reliability",
                weight=0.25
            ),
            SLAConfig(
                name="api_availability",
                metric="availability",
                query="up{job=\"psychsync-api\"}",
                threshold=0.999,
                comparison="gt",
                window="5m",
                description="API availability",
                business_impact="Service accessibility",
                weight=0.25
            ),
            SLAConfig(
                name="database_query_time",
                metric="db_query_time",
                query="rate(pg_stat_statements_total_time_seconds[5m]) / rate(pg_stat_statements_calls[5m])",
                threshold=0.5,
                comparison="lt",
                window="5m",
                description="Database query time",
                business_impact="Application performance",
                weight=0.1
            ),
            SLAConfig(
                name="frontend_load_time",
                metric="frontend_load_time",
                query="histogram_quantile(0.95, rate(frontend_page_load_time_seconds_bucket[5m]))",
                threshold=3.0,
                comparison="lt",
                window="5m",
                description="Frontend page load time",
                business_impact="User experience",
                weight=0.1
            )
        ]

    def _get_default_baselines(self) -> List[PerformanceBaseline]:
        """Get default performance baselines"""
        return [
            PerformanceBaseline(
                name="api_response_time",
                metric="http_request_duration_seconds",
                query="rate(http_request_duration_seconds_sum[1h]) / rate(http_request_duration_seconds_count[1h])",
                baseline_period="7d",
                aggregation="avg",
                description="Average API response time"
            ),
            PerformanceBaseline(
                name="api_response_time_p95",
                metric="http_request_duration_seconds",
                query="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1h]))",
                baseline_period="7d",
                aggregation="p95",
                description="P95 API response time"
            ),
            PerformanceBaseline(
                name="database_connection_utilization",
                metric="pg_stat_activity_count",
                query="pg_stat_activity_count / pg_settings_max_connections",
                baseline_period="7d",
                aggregation="avg",
                description="Database connection utilization"
            ),
            PerformanceBaseline(
                name="memory_usage",
                metric="process_resident_memory_bytes",
                query="process_resident_memory_bytes",
                baseline_period="7d",
                aggregation="avg",
                description="Application memory usage"
            )
        ]

    async def query_prometheus(self, query: str) -> Optional[float]:
        """Query Prometheus and return scalar value"""
        try:
            url = f"{PROMETHEUS_URL}/api/v1/query"
            params = {"query": query}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "success" and data["data"]["result"]:
                        value = float(data["data"]["result"][0]["value"][1])
                        return value
                else:
                    logger.error(f"Prometheus query failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None

    async def calculate_performance_baselines(self) -> Dict[str, float]:
        """Calculate current performance baselines"""
        baselines = {}

        for baseline in self.performance_baselines:
            try:
                # Query for baseline period
                baseline_query = f"avg_over_time({baseline.query}, {baseline.baseline_period})"
                baseline_value = await self.query_prometheus(baseline_query)

                if baseline_value is not None:
                    baselines[baseline.name] = baseline_value
                    PERFORMANCE_BASELINE.labels(metric_name=baseline.name).set(baseline_value * 1000)  # Convert to ms
                    logger.info(f"Baseline for {baseline.name}: {baseline_value:.3f}")
                else:
                    logger.warning(f"Could not calculate baseline for {baseline.name}")

            except Exception as e:
                logger.error(f"Error calculating baseline for {baseline.name}: {e}")

        return baselines

    async def check_sla_compliance(self) -> Dict[str, Dict[str, Any]]:
        """Check SLA compliance for all configured SLAs"""
        compliance_results = {}

        for sla in self.sla_configs:
            try:
                current_value = await self.query_prometheus(sla.query)

                if current_value is not None:
                    # Check compliance
                    compliant = self._check_threshold(current_value, sla.threshold, sla.comparison)
                    severity = "critical" if not compliant else "ok"

                    # Update metrics
                    compliance_percentage = 100.0 if compliant else 0.0
                    SLA_COMPLIANCE.labels(sla_type=sla.name).set(compliance_percentage)
                    PERFORMANCE_CURRENT.labels(metric_name=sla.metric).set(current_value * 1000)

                    if not compliant:
                        SLA_VIOLATIONS.labels(sla_type=sla.name, severity=severity).inc()
                        violation = SLAViolation(
                            timestamp=datetime.now(),
                            sla_type=sla.name,
                            current_value=current_value,
                            threshold=sla.threshold,
                            severity=severity
                        )
                        self.violations.append(violation)
                        logger.warning(f"SLA violation: {sla.name} = {current_value:.3f} (threshold: {sla.threshold})")

                    compliance_results[sla.name] = {
                        "current_value": current_value,
                        "threshold": sla.threshold,
                        "compliant": compliant,
                        "severity": severity,
                        "description": sla.description,
                        "business_impact": sla.business_impact,
                        "weight": sla.weight
                    }
                else:
                    logger.warning(f"Could not get value for SLA: {sla.name}")

            except Exception as e:
                logger.error(f"Error checking SLA {sla.name}: {e}")

        return compliance_results

    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Check if value complies with threshold based on comparison operator"""
        if comparison == "lt":
            return value < threshold
        elif comparison == "lte":
            return value <= threshold
        elif comparison == "gt":
            return value > threshold
        elif comparison == "gte":
            return value >= threshold
        else:
            raise ValueError(f"Unknown comparison operator: {comparison}")

    def calculate_overall_sla_compliance(self, compliance_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall SLA compliance weighted by SLA importance"""
        total_weight = 0.0
        compliant_weight = 0.0

        for sla_name, result in compliance_results.items():
            weight = result.get("weight", 1.0)
            total_weight += weight

            if result.get("compliant", False):
                compliant_weight += weight

        if total_weight > 0:
            return (compliant_weight / total_weight) * 100.0
        else:
            return 0.0

    async def generate_sla_report(self, compliance_results: Dict[str, Dict[str, Any]], baselines: Dict[str, float]) -> Dict[str, Any]:
        """Generate comprehensive SLA compliance report"""
        overall_compliance = self.calculate_overall_sla_compliance(compliance_results)

        # Count violations by severity
        critical_violations = len([v for v in self.violations if v.severity == "critical"])
        total_violations = len(self.violations)

        # Calculate compliance trend (last 24 hours)
        trend = await self.calculate_compliance_trend()

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_sla_compliance": overall_compliance,
            "total_slas_checked": len(self.sla_configs),
            "compliant_slas": len([r for r in compliance_results.values() if r.get("compliant", False)]),
            "critical_violations": critical_violations,
            "total_violations": total_violations,
            "compliance_trend": trend,
            "performance_baselines": baselines,
            "detailed_results": compliance_results,
            "recent_violations": [asdict(v) for v in self.violations[-10:]],  # Last 10 violations
            "sla_health": self._calculate_sla_health(overall_compliance)
        }

        return report

    async def calculate_compliance_trend(self) -> Dict[str, float]:
        """Calculate compliance trend over different time periods"""
        trends = {}
        periods = ["1h", "6h", "24h", "7d"]

        for period in periods:
            try:
                # Query average compliance over period
                compliant_count = 0
                for sla in self.sla_configs:
                    value = await self.query_prometheus(sla.query.replace("5m", period))
                    if value is not None and self._check_threshold(value, sla.threshold, sla.comparison):
                        compliant_count += 1

                if len(self.sla_configs) > 0:
                    trend = (compliant_count / len(self.sla_configs)) * 100.0
                    trends[period] = trend

            except Exception as e:
                logger.error(f"Error calculating trend for period {period}: {e}")
                trends[period] = 0.0

        return trends

    def _calculate_sla_health(self, compliance_percentage: float) -> str:
        """Calculate overall SLA health status"""
        if compliance_percentage >= 95:
            return "excellent"
        elif compliance_percentage >= 90:
            return "good"
        elif compliance_percentage >= 80:
            return "warning"
        else:
            return "critical"

    def save_report(self, report: Dict[str, Any]):
        """Save SLA report to file"""
        output_dir = Path(REPORT_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"sla_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"SLA report saved to {report_file}")
        return report_file

    async def send_sla_alerts(self, report: Dict[str, Any]):
        """Send alerts for SLA violations"""
        if report["critical_violations"] > 0:
            message = f"""
🚨 **CRITICAL SLA VIOLATIONS DETECTED**

**Overall Compliance**: {report['overall_sla_compliance']:.1f}%
**Critical Violations**: {report['critical_violations']}
**Total Violations**: {report['total_violations']}
**SLA Health**: {report['sla_health']}

**Violating SLAs:**
"""
            for sla_name, result in report["detailed_results"].items():
                if not result.get("compliant", False):
                    message += f"- {sla_name}: {result['current_value']:.3f} (threshold: {result['threshold']})\n"

            # Send to Slack (implementation depends on your webhook setup)
            # await self.send_slack_alert(message)

    async def monitor_continuously(self, interval: int = 300):
        """Monitor SLAs continuously"""
        logger.info("Starting continuous SLA monitoring")

        while True:
            try:
                # Load latest configurations
                await self.load_configurations()

                # Calculate performance baselines
                baselines = await self.calculate_performance_baselines()

                # Check SLA compliance
                compliance_results = await self.check_sla_compliance()

                # Generate report
                report = await self.generate_sla_report(compliance_results, baselines)

                # Save report
                self.save_report(report)

                # Send alerts if needed
                await self.send_sla_alerts(report)

                logger.info(f"SLA monitoring cycle completed. Overall compliance: {report['overall_sla_compliance']:.1f}%")

                # Wait for next cycle
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in SLA monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait before retrying


async def main():
    """Main function to run SLA monitoring"""
    parser = argparse.ArgumentParser(description="PsychSync SLA Monitoring")
    parser.add_argument("--interval", type=int, default=300, help="Monitoring interval in seconds")
    parser.add_argument("--port", type=int, default=METRICS_PORT, help="Metrics server port")
    parser.add_argument("--one-shot", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    logger.info("Starting PsychSync SLA Monitoring")

    # Start metrics server
    start_http_server(args.port)
    logger.info(f"Metrics server started on port {args.port}")

    try:
        async with PerformanceMonitor() as monitor:
            if args.one_shot:
                # Run once
                await monitor.load_configurations()
                baselines = await monitor.calculate_performance_baselines()
                compliance_results = await monitor.check_sla_compliance()
                report = await monitor.generate_sla_report(compliance_results, baselines)
                monitor.save_report(report)
                print(json.dumps(report, indent=2, default=str))
            else:
                # Run continuously
                await monitor.monitor_continuously(args.interval)

    except KeyboardInterrupt:
        logger.info("Shutting down SLA monitoring")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
