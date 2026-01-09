"""
Security Metrics Collector

Aggregates security metrics from multiple sources (SAST, DAST, SCA, secret detection)
to provide a unified security dashboard.

Usage:
    from app.monitoring.security_metrics import SecurityMetricsCollector

    collector = SecurityMetricsCollector()

    # Collect all metrics
    metrics = await collector.collect_all_metrics()

    # Get summary
    summary = metrics.get_summary()
    print(f"Security Score: {summary['security_score']}")
    print(f"Total Vulnerabilities: {summary['total_vulnerabilities']}")
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger("app.security.metrics")


class SeverityLevel(Enum):
    """Vulnerability severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class VulnerabilityFinding:
    """Single vulnerability finding"""

    source: str  # SAST, DAST, SCA
    tool: str  # Semgrep, ZAP, Trivy, Snyk, etc.
    severity: SeverityLevel
    cve_id: str | None = None
    title: str = ""
    description: str = ""
    location: str = ""  # file:line or URL
    remediation: str = ""
    detected_at: datetime = None
    status: str = "open"  # open, fixed, ignored

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "tool": self.tool,
            "severity": self.severity.value,
            "cve_id": self.cve_id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "remediation": self.remediation,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "status": self.status,
        }


@dataclass
class SecurityMetrics:
    """Aggregated security metrics"""

    scan_date: datetime
    sast_findings: list[VulnerabilityFinding] = field(default_factory=list)
    dast_findings: list[VulnerabilityFinding] = field(default_factory=list)
    sca_findings: list[VulnerabilityFinding] = field(default_factory=list)

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all findings"""
        total_sast = len(self.sast_findings)
        total_dast = len(self.dast_findings)
        total_sca = len(self.sca_findings)
        total_all = total_sast + total_dast + total_sca

        # Count by severity
        critical = (
            sum(1 for f in self.sast_findings if f.severity == SeverityLevel.CRITICAL)
            + sum(1 for f in self.dast_findings if f.severity == SeverityLevel.CRITICAL)
            + sum(1 for f in self.sca_findings if f.severity == SeverityLevel.CRITICAL)
        )

        high = (
            sum(1 for f in self.sast_findings if f.severity == SeverityLevel.HIGH)
            + sum(1 for f in self.dast_findings if f.severity == SeverityLevel.HIGH)
            + sum(1 for f in self.sca_findings if f.severity == SeverityLevel.HIGH)
        )

        medium = (
            sum(1 for f in self.sast_findings if f.severity == SeverityLevel.MEDIUM)
            + sum(1 for f in self.dast_findings if f.severity == SeverityLevel.MEDIUM)
            + sum(1 for f in self.sca_findings if f.severity == SeverityLevel.MEDIUM)
        )

        low = (
            sum(1 for f in self.sast_findings if f.severity == SeverityLevel.LOW)
            + sum(1 for f in self.dast_findings if f.severity == SeverityLevel.LOW)
            + sum(1 for f in self.sca_findings if f.severity == SeverityLevel.LOW)
        )

        # Calculate security score
        security_score = self.calculate_security_score(total_all, critical, high, medium)

        return {
            "scan_date": self.scan_date.isoformat(),
            "total_findings": total_all,
            "sast_findings": total_sast,
            "dast_findings": total_dast,
            "sca_findings": total_sca,
            "critical_severity": critical,
            "high_severity": high,
            "medium_severity": medium,
            "low_severity": low,
            "security_score": security_score,
            "security_grade": self.get_grade_from_score(security_score),
        }

    def calculate_security_score(self, total: int, critical: int, high: int, medium: int) -> int:
        """
        Calculate security score (0-100)

        Formula:
        - Base score: 100
        - Subtract 50 for each critical
        - Subtract 20 for each high
        - Subtract 10 for each medium
        - Minimum score: 0
        """
        score = 100
        score -= critical * 50
        score -= high * 20
        score -= medium * 10
        return max(0, score)

    def get_grade_from_score(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A+"
        if score >= 80:
            return "A"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "F"

    def get_trend(self, historical_metrics: list["SecurityMetrics"]) -> dict[str, str]:
        """Get trend compared to historical metrics"""
        if not historical_metrics:
            return {"trend": "no_data", "change": "N/A"}

        previous = historical_metrics[-1]
        prev_summary = previous.get_summary()
        curr_summary = self.get_summary()

        prev_total = prev_summary["total_findings"]
        curr_total = curr_summary["total_findings"]

        if curr_total < prev_total:
            return {"trend": "improving", "change": f"-{prev_total - curr_total}"}
        if curr_total > prev_total:
            return {"trend": "degrading", "change": f"+{curr_total - prev_total}"}
        return {"trend": "stable", "change": "0"}

    def get_top_vulnerabilities(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top vulnerabilities by severity"""
        all_findings = self.sast_findings + self.dast_findings + self.sca_findings

        # Sort by severity (critical > high > medium > low)
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4,
        }

        sorted_findings = sorted(
            all_findings,
            key=lambda f: (severity_order.get(f.severity, 99), f.detected_at or datetime.min),
        )

        return [f.to_dict() for f in sorted_findings[:limit]]

    def get_vulnerabilities_by_tool(self) -> dict[str, dict[str, int]]:
        """Get vulnerability counts by tool"""
        summary = {
            "semgrep": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
            "zap": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
            "trivy": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
            "snyk": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
            "npm_audit": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
            "safety": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
            "gitleaks": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
        }

        # Count SAST findings
        for finding in self.sast_findings:
            if finding.tool == "semgrep":
                summary["semgrep"][finding.severity.value] += 1
                summary["semgrep"]["total"] += 1

        # Count DAST findings
        for finding in self.dast_findings:
            if finding.tool == "zap":
                summary["zap"][finding.severity.value] += 1
                summary["zap"]["total"] += 1

        # Count SCA findings
        for finding in self.sca_findings:
            if finding.tool in summary:
                summary[finding.tool][finding.severity.value] += 1
                summary[finding.tool]["total"] += 1

        return summary


class SecurityMetricsCollector:
    """
    Collects and aggregates security metrics from multiple sources
    """

    def __init__(self):
        """Initialize metrics collector"""
        self.logger = logging.getLogger("app.security.collector")

    async def collect_from_sast(
        self, scan_results_path: str = ".github/workflows/semgrep-results.json"
    ) -> list[VulnerabilityFinding]:
        """
        Collect metrics from SAST scan results (Semgrep)

        Args:
            scan_results_path: Path to Semgrep SARIF results

        Returns:
            List of vulnerability findings
        """
        findings = []

        try:
            import json

            with open(scan_results_path) as f:
                sarif = json.load(f)

            # Extract findings from SARIF
            for run in sarif.get("runs", []):
                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "")
                    level = result.get("level", "warning")

                    # Map Semgrep level to severity
                    severity_map = {
                        "error": SeverityLevel.HIGH,
                        "warning": SeverityLevel.MEDIUM,
                        "info": SeverityLevel.LOW,
                    }

                    severity = severity_map.get(level, SeverityLevel.LOW)

                    # Get location
                    locations = result.get("locations", [])
                    location_str = ""
                    if locations:
                        phys_loc = locations[0].get("physicalLocation", {})
                        artifact_loc = phys_loc.get("artifactLocation", {})
                        region = phys_loc.get("region", {})
                        location_str = (
                            f"{artifact_loc.get('uri', 'unknown')}:{region.get('startLine', '?')}"
                        )

                    finding = VulnerabilityFinding(
                        source="SAST",
                        tool="semgrep",
                        severity=severity,
                        title=result.get("message", {}).get("text", ""),
                        location=location_str,
                        detected_at=datetime.utcnow(),
                    )

                    findings.append(finding)

            self.logger.info(f"Collected {len(findings)} SAST findings")

        except FileNotFoundError:
            self.logger.warning(f"SAST results not found at {scan_results_path}")
        except Exception as e:
            self.logger.error(f"Error collecting SAST metrics: {e}")

        return findings

    async def collect_from_dast(
        self, scan_results_path: str = ".github/workflows/zap-results/zap-report.xml"
    ) -> list[VulnerabilityFinding]:
        """
        Collect metrics from DAST scan results (OWASP ZAP)

        Args:
            scan_results_path: Path to ZAP XML report

        Returns:
            List of vulnerability findings
        """
        findings = []

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(scan_results_path)
            root = tree.getroot()

            # Extract alerts from ZAP XML
            for alert in root.findall(".//alert"):
                plugin_id = alert.find("pluginid")
                riskcode = alert.find("riskcode")
                name = alert.find("name")
                desc = alert.find("desc")
                solution = alert.find("solution")

                # Map ZAP riskcode to severity
                risk_level = int(riskcode.text) if riskcode is not None else 0
                severity_map = {
                    3: SeverityLevel.HIGH,
                    2: SeverityLevel.MEDIUM,
                    1: SeverityLevel.LOW,
                    0: SeverityLevel.INFO,
                }

                severity = severity_map.get(risk_level, SeverityLevel.LOW)

                # Get location
                location_elem = alert.find("location")
                location_str = ""
                if location_elem is not None:
                    uri = location_elem.find("uri")
                    if uri is not None:
                        location_str = uri.text

                finding = VulnerabilityFinding(
                    source="DAST",
                    tool="zap",
                    severity=severity,
                    title=name.text if name is not None else "",
                    description=desc.text if desc is not None else "",
                    location=location_str,
                    remediation=solution.text if solution is not None else "",
                    detected_at=datetime.utcnow(),
                )

                findings.append(finding)

            self.logger.info(f"Collected {len(findings)} DAST findings")

        except FileNotFoundError:
            self.logger.warning(f"DAST results not found at {scan_results_path}")
        except Exception as e:
            self.logger.error(f"Error collecting DAST metrics: {e}")

        return findings

    async def collect_from_sca(
        self, scan_results_path: str = ".github/workflows/trivy-results.json"
    ) -> list[VulnerabilityFinding]:
        """
        Collect metrics from SCA scan results (Trivy)

        Args:
            scan_results_path: Path to Trivy SARIF results

        Returns:
            List of vulnerability findings
        """
        findings = []

        try:
            import json

            with open(scan_results_path) as f:
                sarif = json.load(f)

            # Extract vulnerabilities from SARIF
            for run in sarif.get("runs", []):
                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "")

                    # Parse severity from ruleId
                    # Trivy format: CVE-YYYY-XXXX (severity)
                    if "CRITICAL" in rule_id.upper():
                        severity = SeverityLevel.CRITICAL
                    elif "HIGH" in rule_id.upper():
                        severity = SeverityLevel.HIGH
                    elif "MEDIUM" in rule_id.upper():
                        severity = SeverityLevel.MEDIUM
                    else:
                        severity = SeverityLevel.LOW

                    # Extract CVE ID if present
                    cve_id = None
                    if "CVE-" in rule_id:
                        cve_id = rule_id.split("-")[0] + "-" + rule_id.split("-")[1]

                    # Get location
                    locations = result.get("locations", [])
                    location_str = ""
                    if locations:
                        phys_loc = locations[0].get("physicalLocation", {})
                        artifact_loc = phys_loc.get("artifactLocation", {})
                        location_str = artifact_loc.get("uri", "unknown")

                    finding = VulnerabilityFinding(
                        source="SCA",
                        tool="trivy",
                        severity=severity,
                        cve_id=cve_id,
                        title=result.get("message", {}).get("text", ""),
                        location=location_str,
                        detected_at=datetime.utcnow(),
                    )

                    findings.append(finding)

            self.logger.info(f"Collected {len(findings)} SCA findings")

        except FileNotFoundError:
            self.logger.warning(f"SCA results not found at {scan_results_path}")
        except Exception as e:
            self.logger.error(f"Error collecting SCA metrics: {e}")

        return findings

    async def collect_all_metrics(self) -> SecurityMetrics:
        """
        Collect security metrics from all sources

        Returns:
            Aggregated security metrics
        """
        self.logger.info("Collecting security metrics from all sources...")

        sast_findings = await self.collect_from_sast()
        dast_findings = await self.collect_from_dast()
        sca_findings = await self.collect_from_sca()

        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=sast_findings,
            dast_findings=dast_findings,
            sca_findings=sca_findings,
        )

        self.logger.info(
            f"Collected {len(sast_findings)} SAST, "
            f"{len(dast_findings)} DAST, "
            f"{len(sca_findings)} SCA findings"
        )

        return metrics

    async def get_compliance_status(self) -> dict[str, bool]:
        """
        Check compliance status against various security standards

        Returns:
            Dictionary of compliance requirements and status
        """
        metrics = await self.collect_all_metrics()
        summary = metrics.get_summary()

        compliance = {
            "owasp_asvs_1_4_1": True,  # Static analysis (SAST)
            "owasp_asvs_5_2_1": summary["dast_findings"] == 0,  # Dynamic testing (DAST)
            "owasp_asvs_7_1_1": summary["sca_findings"] == 0,  # Vulnerability scanning (SCA)
            "owasp_a08_2021": summary["critical_severity"] == 0,  # Software verification
            "nist_800_53_cm": summary["critical_severity"] == 0,  # Vulnerability management
            "soc_2_cc7_2": summary["critical_severity"] == 0,  # Monitoring
            "hipaa_security": summary["critical_severity"] == 0 and summary["high_severity"] == 0,
        }

        return compliance

    async def generate_dashboard_data(self) -> dict[str, Any]:
        """
        Generate data for security dashboard

        Returns:
            Dashboard data dictionary
        """
        metrics = await self.collect_all_metrics()
        summary = metrics.get_summary()

        dashboard_data = {
            "overview": {
                "security_score": summary["security_score"],
                "security_grade": summary["security_grade"],
                "total_findings": summary["total_findings"],
                "last_scan": summary["scan_date"],
            },
            "severity_breakdown": {
                "critical": summary["critical_severity"],
                "high": summary["high_severity"],
                "medium": summary["medium_severity"],
                "low": summary["low_severity"],
            },
            "by_source": {
                "sast": summary["sast_findings"],
                "dast": summary["dast_findings"],
                "sca": summary["sca_findings"],
            },
            "by_tool": metrics.get_vulnerabilities_by_tool(),
            "top_vulnerabilities": metrics.get_top_vulnerabilities(10),
            "compliance": await self.get_compliance_status(),
        }

        return dashboard_data


# ============================================================================
# Helper Functions
# ============================================================================


async def collect_security_metrics() -> dict[str, Any]:
    """
    Convenience function to collect all security metrics

    Returns:
        Dashboard data dictionary
    """
    collector = SecurityMetricsCollector()
    return await collector.generate_dashboard_data()


async def get_security_score() -> int:
    """
    Get current security score

    Returns:
        Security score (0-100)
    """
    metrics = await collect_security_metrics()
    return metrics["overview"]["security_score"]


async def get_security_grade() -> str:
    """
    Get current security grade

    Returns:
        Letter grade (A+, A, B, C, F)
    """
    metrics = await collect_security_metrics()
    return metrics["overview"]["security_grade"]


# ============================================================================
# CLI Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        """CLI entry point"""
        collector = SecurityMetricsCollector()

        # Collect metrics
        metrics = await collector.collect_all_metrics()

        # Print summary
        summary = metrics.get_summary()

        print("\n" + "=" * 60)
        print("🔒 PSYCHSYNC SECURITY METRICS")
        print("=" * 60)
        print(f"\n📅 Scan Date: {summary['scan_date']}")
        print(f"📊 Security Score: {summary['security_score']}/100 ({summary['security_grade']})")
        print(f"\n📈 Total Findings: {summary['total_findings']}")
        print(f"   🔴 Critical: {summary['critical_severity']}")
        print(f"   🟠 High:     {summary['high_severity']}")
        print(f"   🟡 Medium:   {summary['medium_severity']}")
        print(f"   🟢 Low:      {summary['low_severity']}")

        print("\n" + "-" * 60)
        print("Breakdown by Source:")
        print("-" * 60)
        print(f"SAST (Semgrep): {summary['sast_findings']}")
        print(f"DAST (OWASP ZAP): {summary['dast_findings']}")
        print(f"SCA (Dependencies): {summary['sca_findings']}")

        print("\n" + "-" * 60)
        print("Top 10 Vulnerabilities:")
        print("-" * 60)

        top_vulns = metrics.get_top_vulnerabilities(10)
        for i, vuln in enumerate(top_vulns, 1):
            print(f"\n{i}. {vuln['title']}")
            print(f"   Severity: {vuln['severity'].upper()}")
            print(f"   Location: {vuln['location']}")

        print("\n" + "=" * 60 + "\n")

    asyncio.run(main())
