"""
Prometheus Security Metrics Exporter

Exports security metrics in Prometheus format for scraping by observability platforms.

Usage:
    from app.monitoring.prometheus_metrics import generate_prometheus_metrics

    metrics_text = await generate_prometheus_metrics()
    print(metrics_text)

Endpoints:
    GET /metrics - Prometheus metrics endpoint
"""

import logging
from datetime import datetime
from typing import Any

from app.monitoring.security_metrics import SecurityMetricsCollector

logger = logging.getLogger("app.security.prometheus")


class PrometheusMetrics:
    """Generate Prometheus-formatted metrics"""

    def __init__(self):
        """Initialize Prometheus metrics generator"""
        self.collector = SecurityMetricsCollector()
        self.logger = logging.getLogger("app.security.prometheus")

    async def generate_metrics(self) -> str:
        """
        Generate all security metrics in Prometheus format

        Returns:
            Prometheus-formatted metrics text
        """
        try:
            # Collect security metrics
            security_metrics = await self.collector.collect_all_metrics()
            summary = security_metrics.get_summary()
            compliance = await self.collector.get_compliance_status()
            by_tool = security_metrics.get_vulnerabilities_by_tool()

            # Build Prometheus metrics
            metrics_lines = []

            # Security score metrics
            metrics_lines.append(
                "# HELP psychsync_security_score Security score (0-100)"
            )
            metrics_lines.append("# TYPE psychsync_security_score gauge")
            metrics_lines.append(
                f"psychsync_security_score {summary['security_score']}"
            )

            metrics_lines.append(
                "\n# HELP psychsync_security_grade Security grade (A+, A, B, C, F)"
            )
            metrics_lines.append("# TYPE psychsync_security_grade gauge")
            grade_score = self._grade_to_number(summary["security_grade"])
            metrics_lines.append(
                f'psychsync_security_score {{grade="{summary["security_grade"]}"}} {grade_score}'
            )

            # Vulnerability count metrics
            metrics_lines.append(
                "\n# HELP psychsync_vulnerabilities_total Total number of vulnerabilities"
            )
            metrics_lines.append("# TYPE psychsync_vulnerabilities_total gauge")
            metrics_lines.append(
                f"psychsync_vulnerabilities_total {summary['total_findings']}"
            )

            metrics_lines.append(
                "\n# HELP psychsync_vulnerabilities_by_severity Number of vulnerabilities by severity"
            )
            metrics_lines.append("# TYPE psychsync_vulnerabilities_by_severity gauge")
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_severity{{severity="critical"}} {summary["critical_severity"]}'
            )
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_severity{{severity="high"}} {summary["high_severity"]}'
            )
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_severity{{severity="medium"}} {summary["medium_severity"]}'
            )
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_severity{{severity="low"}} {summary["low_severity"]}'
            )

            # Source metrics
            metrics_lines.append(
                "\n# HELP psychsync_vulnerabilities_by_source Number of vulnerabilities by source"
            )
            metrics_lines.append("# TYPE psychsync_vulnerabilities_by_source gauge")
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_source{{source="SAST"}} {summary["sast_findings"]}'
            )
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_source{{source="DAST"}} {summary["dast_findings"]}'
            )
            metrics_lines.append(
                f'psychsync_vulnerabilities_by_source{{source="SCA"}} {summary["sca_findings"]}'
            )

            # Tool metrics
            metrics_lines.append(
                "\n# HELP psychsync_vulnerabilities_by_tool Number of vulnerabilities by tool"
            )
            metrics_lines.append("# TYPE psychsync_vulnerabilities_by_tool gauge")
            for tool, counts in by_tool.items():
                if counts["total"] > 0:
                    metrics_lines.append(
                        f'psychsync_vulnerabilities_by_tool{{tool="{tool}"}} {counts["total"]}'
                    )
                    metrics_lines.append(
                        f'psychsync_vulnerabilities_by_tool{{tool="{tool}",severity="critical"}} {counts["critical"]}'
                    )
                    metrics_lines.append(
                        f'psychsync_vulnerabilities_by_tool{{tool="{tool}",severity="high"}} {counts["high"]}'
                    )
                    metrics_lines.append(
                        f'psychsync_vulnerabilities_by_tool{{tool="{tool}",severity="medium"}} {counts["medium"]}'
                    )
                    metrics_lines.append(
                        f'psychsync_vulnerabilities_by_tool{{tool="{tool}",severity="low"}} {counts["low"]}'
                    )

            # Compliance metrics
            metrics_lines.append(
                "\n# HELP psychsync_compliance_status Compliance status (1=compliant, 0=non-compliant)"
            )
            metrics_lines.append("# TYPE psychsync_compliance_status gauge")
            for standard, compliant in compliance.items():
                status = 1 if compliant else 0
                metrics_lines.append(
                    f'psychsync_compliance_status{{standard="{standard}"}} {status}'
                )

            # Scan timestamp
            metrics_lines.append(
                "\n# HELP psychsync_last_scan_timestamp Unix timestamp of last security scan"
            )
            metrics_lines.append("# TYPE psychsync_last_scan_timestamp gauge")
            scan_time = int(datetime.fromisoformat(summary["scan_date"]).timestamp())
            metrics_lines.append(f"psychsync_last_scan_timestamp {scan_time}")

            # Join with newlines
            return "\n".join(metrics_lines)

        except Exception as e:
            self.logger.error(f"Failed to generate Prometheus metrics: {e}")
            return self._generate_error_metrics(e)

    def _grade_to_number(self, grade: str) -> int:
        """Convert letter grade to numeric value"""
        grade_map = {"A+": 5, "A": 4, "B": 3, "C": 2, "F": 1}
        return grade_map.get(grade, 0)

    def _generate_error_metrics(self, error: Exception) -> str:
        """Generate error metrics when collection fails"""
        return f"""# HELP psychsync_metrics_up Indicates if metrics collection succeeded
# TYPE psychsync_metrics_up gauge
psychsync_metrics_up 0

# HELP psychsync_metrics_error Error message from metrics collection
# TYPE psychsync_metrics_error gauge
psychsync_metrics_error{{error="{error!s}"}} 1
"""


# ============================================================================
# Convenience Functions
# ============================================================================


async def generate_prometheus_metrics() -> str:
    """
    Generate Prometheus-formatted security metrics

    Returns:
        Prometheus metrics text
    """
    generator = PrometheusMetrics()
    return await generator.generate_metrics()


async def get_prometheus_metrics_dict() -> dict[str, Any]:
    """
    Get security metrics as dictionary for custom formatting

    Returns:
        Dictionary of metrics
    """
    collector = SecurityMetricsCollector()
    dashboard_data = await collector.generate_dashboard_data()

    return {
        "security_score": dashboard_data["overview"]["security_score"],
        "security_grade": dashboard_data["overview"]["security_grade"],
        "total_findings": dashboard_data["overview"]["total_findings"],
        "severity_breakdown": dashboard_data["severity_breakdown"],
        "by_source": dashboard_data["by_source"],
        "by_tool": dashboard_data["by_tool"],
        "compliance": dashboard_data["compliance"],
    }


# ============================================================================
# CLI Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        """CLI entry point"""
        generator = PrometheusMetrics()

        print("\n" + "=" * 60)
        print("📊 PSYCHSYNC SECURITY METRICS (PROMETHEUS FORMAT)")
        print("=" * 60 + "\n")

        metrics = await generator.generate_metrics()
        print(metrics)

        print("\n" + "=" * 60 + "\n")

    asyncio.run(main())
