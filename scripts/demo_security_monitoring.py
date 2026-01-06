#!/usr/bin/env python3
"""
Security Monitoring System Demo

This script demonstrates the complete security monitoring workflow:
1. Creates mock scan results (SAST, DAST, SCA)
2. Collects and aggregates metrics
3. Calculates security score
4. Checks compliance status
5. Generates dashboard data
6. Exports Prometheus metrics

Usage:
    python scripts/demo_security_monitoring.py
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.monitoring.security_metrics import (
    SecurityMetricsCollector,
    SecurityMetrics,
    VulnerabilityFinding,
    SeverityLevel
)
from app.monitoring.prometheus_metrics import generate_prometheus_metrics


def create_mock_sast_results():
    """Create mock Semgrep SARIF results"""
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
                            "text": "Possible SQL injection through string concatenation"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "app/services/user_service.py"
                                    },
                                    "region": {
                                        "startLine": 127,
                                        "endLine": 127
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "ruleId": "python.assert",
                        "level": "warning",
                        "message": {
                            "text": "Assert statements should not be used for control flow"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "app/main.py"
                                    },
                                    "region": {
                                        "startLine": 45,
                                        "endLine": 45
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "ruleId": "python.best-practice",
                        "level": "info",
                        "message": {
                            "text": "Consider using enum for constants"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "app/core/config.py"
                                    },
                                    "region": {
                                        "startLine": 12,
                                        "endLine": 12
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }


def create_mock_dast_results():
    """Create mock OWASP ZAP XML results"""
    return '''<?xml version="1.0"?>
<OWASPZAPReport>
    <site name="http://staging.psychsync.com">
        <alerts>
            <alert>
                <pluginid>10021</pluginid>
                <riskcode>3</riskcode>
                <name>X-Content-Type-Options Header Missing</name>
                <desc>The X-Content-Type-Options header is not set. This allows some browsers to perform MIME-sniffing on the response body.</desc>
                <solution>Add the X-Content-Type-Options header with value 'nosniff' to the response.</solution>
                <location>
                    <uri>http://staging.psychsync.com/api/v1/auth/login</uri>
                </location>
            </alert>
            <alert>
                <pluginid>10061</pluginid>
                <riskcode>2</riskcode>
                <name>Information Disclosure - Debug Error Messages</name>
                <desc>The web server disclosed debug information in error messages.</desc>
                <solution>Configure server to hide debug information in production.</solution>
                <location>
                    <uri>http://staging.psychsync.com/api/v1/health</uri>
                </location>
            </alert>
            <alert>
                <pluginid>10098</pluginid>
                <riskcode>1</riskcode>
                <name>Timestamp Disclosure</name>
                <desc>A timestamp was disclosed by the application.</desc>
                <solution>Consider removing or masking timestamps in responses.</solution>
                <location>
                    <uri>http://staging.psychsync.com/api/v1/users</uri>
                </location>
            </alert>
        </alerts>
    </site>
</OWASPZAPReport>'''


def create_mock_sca_results():
    """Create mock Trivy SARIF results"""
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
                        "ruleId": "CVE-2023-38501 (HIGH)",
                        "level": "error",
                        "message": {
                            "text": "High severity vulnerability in requests>=2.31.0"
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
                        "ruleId": "CVE-2023-45857 (MEDIUM)",
                        "level": "warning",
                        "message": {
                            "text": "Medium severity vulnerability in pyyaml>=6.0"
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
                        "ruleId": "CVE-2023-39117 (MEDIUM)",
                        "level": "warning",
                        "message": {
                            "text": "Medium severity vulnerability in flask-cors>=4.0.0"
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
                        "ruleId": "CVE-2023-44487 (LOW)",
                        "level": "note",
                        "message": {
                            "text": "Low severity vulnerability in werkzeug>=3.0.0"
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
                    }
                ]
            }
        ]
    }


async def demo_complete_workflow():
    """Demonstrate the complete security monitoring workflow"""

    print("\n" + "="*70)
    print("🔒 PSYCHSYNC SECURITY MONITORING SYSTEM DEMO")
    print("="*70 + "\n")

    # Step 1: Create mock scan results
    print("📝 Step 1: Creating mock scan results...")
    print("   ├── SAST (Semgrep) - Static code analysis")
    print("   ├── DAST (OWASP ZAP) - Dynamic application testing")
    print("   └── SCA (Trivy) - Software composition analysis\n")

    # Create temporary files
    sast_data = create_mock_sast_results()
    dast_data = create_mock_dast_results()
    sca_data = create_mock_sca_results()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sast_data, f)
        sast_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(dast_data)
        dast_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sca_data, f)
        sca_path = f.name

    try:
        # Step 2: Collect metrics
        print("🔍 Step 2: Collecting security metrics...")
        collector = SecurityMetricsCollector()

        sast_findings = await collector.collect_from_sast(sast_path)
        dast_findings = await collector.collect_from_dast(dast_path)
        sca_findings = await collector.collect_from_sca(sca_path)

        print(f"   ✓ Collected {len(sast_findings)} SAST findings")
        print(f"   ✓ Collected {len(dast_findings)} DAST findings")
        print(f"   ✓ Collected {len(sca_findings)} SCA findings\n")

        # Step 3: Aggregate metrics
        print("📊 Step 3: Aggregating metrics...")
        metrics = SecurityMetrics(
            scan_date=datetime.utcnow(),
            sast_findings=sast_findings,
            dast_findings=dast_findings,
            sca_findings=sca_findings
        )

        summary = metrics.get_summary()
        print(f"   ✓ Total findings: {summary['total_findings']}")
        print(f"   ✓ Critical: {summary['critical_severity']}")
        print(f"   ✓ High: {summary['high_severity']}")
        print(f"   ✓ Medium: {summary['medium_severity']}")
        print(f"   ✓ Low: {summary['low_severity']}\n")

        # Step 4: Calculate security score
        print("📈 Step 4: Calculating security score...")
        score = summary['security_score']
        grade = summary['security_grade']

        print(f"   ✓ Security Score: {score}/100")
        print(f"   ✓ Security Grade: {grade}\n")

        # Step 5: Check compliance
        print("✅ Step 5: Checking compliance status...")
        compliance = await collector.get_compliance_status()

        compliant_count = sum(1 for v in compliance.values() if v)
        total_count = len(compliance)
        print(f"   ✓ Compliance: {compliant_count}/{total_count} standards met")

        for standard, status in compliance.items():
            icon = "✅" if status else "❌"
            print(f"      {icon} {standard}")
        print()

        # Step 6: Get top vulnerabilities
        print("⚠️  Step 6: Top vulnerabilities...")
        top_vulns = metrics.get_top_vulnerabilities(limit=5)

        for i, vuln in enumerate(top_vulns, 1):
            severity_icon = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(vuln['severity'], '⚪')

            print(f"   {i}. {severity_icon} {vuln['title']}")
            print(f"      Severity: {vuln['severity'].upper()}")
            print(f"      Source: {vuln['source']} ({vuln['tool']})")
            print(f"      Location: {vuln['location']}")
            print()

        # Step 7: Generate Prometheus metrics
        print("📊 Step 7: Generating Prometheus metrics...")
        prometheus_text = await generate_prometheus_metrics()

        # Show a snippet of Prometheus metrics
        print("   ✓ Sample Prometheus metrics:")
        print("─" * 70)
        lines = prometheus_text.split('\n')
        for line in lines[:20]:  # Show first 20 lines
            print(f"   {line}")
        if len(lines) > 20:
            print(f"   ... ({len(lines) - 20} more lines)")
        print("─" * 70 + "\n")

        # Step 8: Generate dashboard data
        print("🎨 Step 8: Generating dashboard data...")
        dashboard_data = await collector.generate_dashboard_data()

        print("   ✓ Dashboard data structure:")
        print(f"      ├── Overview: {len(dashboard_data.get('overview', {}))} fields")
        print(f"      ├── Severity breakdown: {len(dashboard_data.get('severity_breakdown', {}))} levels")
        print(f"      ├── By source: {len(dashboard_data.get('by_source', {}))} sources")
        print(f"      ├── By tool: {len(dashboard_data.get('by_tool', {}))} tools")
        print(f"      ├── Top vulnerabilities: {len(dashboard_data.get('top_vulnerabilities', []))} items")
        print(f"      └── Compliance: {len(dashboard_data.get('compliance', {}))} standards\n")

        # Final summary
        print("="*70)
        print("📋 DEMO SUMMARY")
        print("="*70)
        print(f"\n🔒 Security Score: {score}/100 ({grade})")
        print(f"📊 Total Findings: {summary['total_findings']}")
        print(f"   🔴 Critical: {summary['critical_severity']}")
        print(f"   🟠 High:     {summary['high_severity']}")
        print(f"   🟡 Medium:   {summary['medium_severity']}")
        print(f"   🟢 Low:      {summary['low_severity']}")
        print(f"\n✅ Compliance: {compliant_count}/{total_count} standards met")
        print(f"\n🔍 Top Vulnerability:")
        if top_vulns:
            v = top_vulns[0]
            print(f"   {v['title']}")
            print(f"   Severity: {v['severity'].upper()}")
            print(f"   Location: {v['location']}")

        print("\n" + "="*70)
        print("✅ Demo completed successfully!")
        print("="*70 + "\n")

        print("💡 Next Steps:")
        print("   1. Review the findings in the GitHub Security tab")
        print("   2. Address high-severity vulnerabilities immediately")
        print("   3. View the Grafana dashboard for visualizations")
        print("   4. Monitor Prometheus alerts for real-time notifications")
        print()

    finally:
        # Clean up temporary files
        os.unlink(sast_path)
        os.unlink(dast_path)
        os.unlink(sca_path)


if __name__ == "__main__":
    asyncio.run(demo_complete_workflow())
