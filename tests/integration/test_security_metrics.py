"""
Integration Tests for Security Metrics System

Tests the complete security monitoring system including:
- SecurityMetricsCollector
- PrometheusMetricsExporter
- API endpoints
- Metrics aggregation
- Compliance checking
- Score calculation
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.monitoring.security_metrics import (
    SecurityMetricsCollector,
    SecurityMetrics,
    VulnerabilityFinding,
    SeverityLevel,
    collect_security_metrics,
    get_security_score,
    get_security_grade
)
from app.monitoring.prometheus_metrics import (
    PrometheusMetrics,
    generate_prometheus_metrics
)


@pytest.fixture
def mock_sast_results():
    """Mock Semgrep SARIF results"""
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Semgrep",
                        "version": "1.0.0"
                    }
                },
                "results": [
                    {
                        "ruleId": "python.sql-injection",
                        "level": "error",
                        "message": {
                            "text": "Possible SQL injection"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "app/services/user_service.py"
                                    },
                                    "region": {
                                        "startLine": 127
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "ruleId": "python.best-practice",
                        "level": "warning",
                        "message": {
                            "text": "Use of assert detected"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "app/main.py"
                                    },
                                    "region": {
                                        "startLine": 45
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_dast_results():
    """Mock OWASP ZAP XML results"""
    return '''<?xml version="1.0"?>
<OWASPZAPReport>
    <site name="http://staging.psychsync.com">
        <alerts>
            <alert>
                <pluginid>10021</pluginid>
                <riskcode>3</riskcode>
                <name>X-Content-Type-Options Header Missing</name>
                <desc>The X-Content-Type-Options header is not set</desc>
                <solution>Add X-Content-Type-Options: nosniff header</solution>
                <location>
                    <uri>http://staging.psychsync.com/api/v1/auth/login</uri>
                </location>
            </alert>
            <alert>
                <pluginid>10061</pluginid>
                <riskcode>2</riskcode>
                <name>Information Disclosure</name>
                <desc>Server version disclosed</desc>
                <solution>Configure server to hide version</solution>
                <location>
                    <uri>http://staging.psychsync.com/api/v1/health</uri>
                </location>
            </alert>
        </alerts>
    </site>
</OWASPZAPReport>'''


@pytest.fixture
def mock_sca_results():
    """Mock Trivy SARIF results"""
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Trivy",
                        "version": "0.40.0"
                    }
                },
                "results": [
                    {
                        "ruleId": "CVE-2023-1234 (HIGH)",
                        "level": "error",
                        "message": {
                            "text": "High severity vulnerability in package"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "requirements.txt"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "ruleId": "CVE-2023-5678 (MEDIUM)",
                        "level": "warning",
                        "message": {
                            "text": "Medium severity vulnerability in package"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "package.json"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }


class TestSecurityMetricsCollector:
    """Test SecurityMetricsCollector"""

    @pytest.mark.asyncio
    async def test_collect_from_sast(self, mock_sast_results):
        """Test collecting SAST metrics from Semgrep SARIF"""
        # Create temporary file with mock results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_sast_results, f)
            temp_path = f.name

        try:
            collector = SecurityMetricsCollector()
            findings = await collector.collect_from_sast(scan_results_path=temp_path)

            assert len(findings) == 2
            assert findings[0].source == "SAST"
            assert findings[0].tool == "semgrep"
            assert findings[0].severity == SeverityLevel.HIGH
            assert findings[0].location == "app/services/user_service.py:127"
            assert findings[1].severity == SeverityLevel.MEDIUM
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_collect_from_dast(self, mock_dast_results):
        """Test collecting DAST metrics from ZAP XML"""
        # Create temporary file with mock results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_dast_results)
            temp_path = f.name

        try:
            collector = SecurityMetricsCollector()
            findings = await collector.collect_from_dast(scan_results_path=temp_path)

            assert len(findings) == 2
            assert findings[0].source == "DAST"
            assert findings[0].tool == "zap"
            assert findings[0].severity == SeverityLevel.HIGH
            assert findings[0].title == "X-Content-Type-Options Header Missing"
            assert findings[1].severity == SeverityLevel.MEDIUM
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_collect_from_sca(self, mock_sca_results):
        """Test collecting SCA metrics from Trivy SARIF"""
        # Create temporary file with mock results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_sca_results, f)
            temp_path = f.name

        try:
            collector = SecurityMetricsCollector()
            findings = await collector.collect_from_sca(scan_results_path=temp_path)

            assert len(findings) == 2
            assert findings[0].source == "SCA"
            assert findings[0].tool == "trivy"
            assert findings[0].severity == SeverityLevel.HIGH
            assert findings[0].cve_id is not None
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_collect_all_metrics(self, mock_sast_results, mock_dast_results, mock_sca_results):
        """Test collecting all security metrics"""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_sast_results, f)
            sast_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(mock_dast_results)
            dast_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_sca_results, f)
            sca_path = f.name

        try:
            # Mock the file paths
            collector = SecurityMetricsCollector()

            # Manually collect from each source
            sast_findings = await collector.collect_from_sast(sast_path)
            dast_findings = await collector.collect_from_dast(dast_path)
            sca_findings = await collector.collect_from_sca(sca_path)

            metrics = SecurityMetrics(
                scan_date=datetime.utcnow(),
                sast_findings=sast_findings,
                dast_findings=dast_findings,
                sca_findings=sca_findings
            )

            summary = metrics.get_summary()

            assert summary['sast_findings'] == 2
            assert summary['dast_findings'] == 2
            assert summary['sca_findings'] == 2
            assert summary['total_findings'] == 6

        finally:
            os.unlink(sast_path)
            os.unlink(dast_path)
            os.unlink(sca_path)


class TestSecurityMetrics:
    """Test SecurityMetrics calculations"""

    def test_calculate_security_score_perfect(self):
        """Test score calculation with no vulnerabilities"""
        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=[],
            dast_findings=[],
            sca_findings=[]
        )

        summary = metrics.get_summary()
        assert summary['security_score'] == 100
        assert summary['security_grade'] == 'A+'

    def test_calculate_security_score_with_critical(self):
        """Test score calculation with critical vulnerabilities"""
        # Create a critical finding
        finding = VulnerabilityFinding(
            source="SCA",
            tool="trivy",
            severity=SeverityLevel.CRITICAL,
            title="Critical vulnerability",
            location="requirements.txt"
        )

        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=[finding],
            dast_findings=[],
            sca_findings=[]
        )

        summary = metrics.get_summary()
        # Score = 100 - (1 * 50) = 50
        assert summary['security_score'] == 50
        assert summary['security_grade'] == 'F'

    def test_calculate_security_score_with_multiple(self):
        """Test score calculation with mixed vulnerabilities"""
        findings = [
            VulnerabilityFinding(source="SAST", tool="semgrep", severity=SeverityLevel.HIGH),
            VulnerabilityFinding(source="SAST", tool="semgrep", severity=SeverityLevel.HIGH),
            VulnerabilityFinding(source="DAST", tool="zap", severity=SeverityLevel.MEDIUM),
        ]

        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=findings,
            dast_findings=[],
            sca_findings=[]
        )

        summary = metrics.get_summary()
        # Score = 100 - (2 * 20) - (1 * 10) = 50
        assert summary['security_score'] == 50
        assert summary['security_grade'] == 'F'

    def test_get_top_vulnerabilities(self):
        """Test getting top vulnerabilities sorted by severity"""
        findings = [
            VulnerabilityFinding(
                source="SCA",
                tool="trivy",
                severity=SeverityLevel.LOW,
                title="Low severity issue"
            ),
            VulnerabilityFinding(
                source="SAST",
                tool="semgrep",
                severity=SeverityLevel.CRITICAL,
                title="Critical issue"
            ),
            VulnerabilityFinding(
                source="DAST",
                tool="zap",
                severity=SeverityLevel.HIGH,
                title="High severity issue"
            ),
        ]

        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=findings,
            dast_findings=[],
            sca_findings=[]
        )

        top = metrics.get_top_vulnerabilities(limit=10)

        # Critical should be first, then High, then Low
        assert top[0]['severity'] == 'critical'
        assert top[1]['severity'] == 'high'
        assert top[2]['severity'] == 'low'

    def test_get_vulnerabilities_by_tool(self):
        """Test getting vulnerability breakdown by tool"""
        findings = [
            VulnerabilityFinding(source="SAST", tool="semgrep", severity=SeverityLevel.HIGH),
            VulnerabilityFinding(source="SAST", tool="semgrep", severity=SeverityLevel.MEDIUM),
            VulnerabilityFinding(source="DAST", tool="zap", severity=SeverityLevel.HIGH),
            VulnerabilityFinding(source="SCA", tool="trivy", severity=SeverityLevel.CRITICAL),
        ]

        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=findings[:2],
            dast_findings=[findings[2]],
            sca_findings=[findings[3]]
        )

        by_tool = metrics.get_vulnerabilities_by_tool()

        assert by_tool['semgrep']['total'] == 2
        assert by_tool['semgrep']['high'] == 1
        assert by_tool['semgrep']['medium'] == 1

        assert by_tool['zap']['total'] == 1
        assert by_tool['zap']['high'] == 1

        assert by_tool['trivy']['total'] == 1
        assert by_tool['trivy']['critical'] == 1


class TestComplianceChecking:
    """Test compliance status checking"""

    @pytest.mark.asyncio
    async def test_compliance_with_no_vulnerabilities(self):
        """Test compliance when no vulnerabilities"""
        # TODO(human): Implement this test to verify that get_compliance_status()
        # returns all True values when there are no vulnerabilities.
        #
        # Requirements:
        # 1. Create a SecurityMetricsCollector instance
        # 2. Mock the collect_all_metrics() method to return metrics with zero findings
        # 3. Call get_compliance_status() and verify all standards return True
        # 4. Expected standards to check: owasp_asvs_1_4_1, owasp_asvs_5_2_1,
        #    owasp_asvs_7_1_1, owasp_a08_2021, nist_800_53_cm, soc_2_cc7_2,
        #    hipaa_security
        pass

    @pytest.mark.asyncio
    async def test_compliance_with_critical_vulnerabilities(self):
        """Test compliance fails with critical vulnerabilities"""
        # TODO(human): Implement this test to verify that get_compliance_status()
        # returns False for standards that require zero critical vulnerabilities.
        #
        # Requirements:
        # 1. Create mock metrics with at least one critical vulnerability
        # 2. Call get_compliance_status() on the collector
        # 3. Verify that owasp_a08_2021, nist_800_53_cm, soc_2_cc7_2, and
        #    hipaa_security all return False
        # 4. SAST compliance (owasp_asvs_1_4_1) should still return True
        pass


class TestPrometheusMetrics:
    """Test Prometheus metrics exporter"""

    @pytest.mark.asyncio
    async def test_generate_metrics_format(self):
        """Test that Prometheus metrics are in correct format"""
        # Create a mock metrics collector
        metrics_text = await generate_prometheus_metrics()

        # Verify it's a string
        assert isinstance(metrics_text, str)

        # Check for required Prometheus elements
        assert '# HELP' in metrics_text or '# TYPE' in metrics_text
        assert 'psychsync_security_score' in metrics_text or 'psychsync_metrics_up' in metrics_text

    @pytest.mark.asyncio
    async def test_generate_metrics_contains_all_metrics(self):
        """Test that all expected metrics are generated"""
        # TODO(human): Implement this test to verify all expected metrics
        # are present in the Prometheus output.
        #
        # Requirements:
        # 1. Call generate_prometheus_metrics()
        # 2. Verify the output contains these metric names:
        #    - psychsync_security_score
        #    - psychsync_vulnerabilities_total
        #    - psychsync_vulnerabilities_by_severity
        #    - psychsync_vulnerabilities_by_source
        #    - psychsync_compliance_status
        # 3. Verify HELP and TYPE comments exist for each metric
        # 4. Use 'in' operator to check substring presence
        pass


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.mark.asyncio
    async def test_collect_security_metrics(self):
        """Test the collect_security_metrics convenience function"""
        # This function calls generate_dashboard_data()
        # We can test that it returns a dict with expected structure
        dashboard_data = await collect_security_metrics()

        assert isinstance(dashboard_data, dict)
        assert 'overview' in dashboard_data or 'security_score' in dashboard_data

    @pytest.mark.asyncio
    async def test_get_security_score(self):
        """Test the get_security_score convenience function"""
        score = await get_security_score()
        assert isinstance(score, int)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_get_security_grade(self):
        """Test the get_security_grade convenience function"""
        grade = await get_security_grade()
        assert isinstance(grade, str)
        assert grade in ['A+', 'A', 'B', 'C', 'F']


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end security monitoring workflow"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_sast_results, mock_sca_results):
        """Test the complete workflow from scan results to dashboard"""
        # This test simulates the complete flow:
        # 1. GitHub Actions workflow runs and produces SARIF results
        # 2. SecurityMetricsCollector reads and aggregates results
        # 3. Security score is calculated
        # 4. Compliance status is checked
        # 5. Dashboard data is generated
        # 6. Prometheus metrics are exported

        # TODO(human): Implement the complete end-to-end test.
        #
        # Requirements:
        # 1. Create temporary files with mock scan results (SAST, DAST, SCA)
        # 2. Use SecurityMetricsCollector to collect from all sources
        # 3. Verify SecurityMetrics contains all findings
        # 4. Verify security score is calculated correctly
        # 5. Verify compliance status reflects findings
        # 6. Generate Prometheus metrics and verify format
        # 7. Clean up temporary files
        #
        # This should test the ENTIRE pipeline from scan to display.
        pass
