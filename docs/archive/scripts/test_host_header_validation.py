#!/usr/bin/env python3
"""
Host Header Validation Test Script
Tests the HostValidationMiddleware for security vulnerabilities

Author: Security Team
Version: 1.0.0
"""

import sys
from typing import Any, Dict, List

import requests


class HostHeaderValidator:
    """Test Host header validation"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "findings": [],
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all host header validation tests"""
        print("=" * 70)
        print("HOST HEADER VALIDATION SECURITY TEST")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print()

        # Test categories
        test_suites = [
            ("Valid Host Headers", self.test_valid_hosts),
            ("Invalid Host Headers", self.test_invalid_hosts),
            ("Suspicious Patterns", self.test_suspicious_patterns),
            ("DNS Rebinding Attempts", self.test_dns_rebinding),
            ("Cache Poisoning Attempts", self.test_cache_poisoning),
            ("XSS Attempts", self.test_xss_attempts),
            ("Subdomain Validation", self.test_subdomains),
        ]

        for suite_name, test_func in test_suites:
            print(f"\n🧪 Testing: {suite_name}")
            print("-" * 70)
            test_func()
            print()

        # Print summary
        self.print_summary()

        return self.results

    def test_valid_hosts(self) -> None:
        """Test that valid hosts are accepted"""

        valid_hosts = [
            "localhost:8000",
            "127.0.0.1:8000",
            "example.com",
            "api.example.com",
            "www.example.com",
        ]

        for host in valid_hosts:
            result = self._test_host(host, should_succeed=True)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host}")

            if not result["passed"]:
                self.results["findings"].append(
                    {
                        "severity": "HIGH",
                        "issue": f"Valid host rejected: {host}",
                        "details": result.get("error", "Unknown error"),
                    }
                )

    def test_invalid_hosts(self) -> None:
        """Test that invalid hosts are rejected"""

        invalid_hosts = [
            "evil.com",
            "attacker.com",
            "malicious-site.com",
            "totally-legit-domain.com",
        ]

        for host in invalid_hosts:
            result = self._test_host(host, should_succeed=False)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host}")

            if not result["passed"]:
                self.results["findings"].append(
                    {
                        "severity": "HIGH",
                        "issue": f"Invalid host accepted: {host}",
                        "details": "Security vulnerability: Host validation not working",
                    }
                )

    def test_suspicious_patterns(self) -> None:
        """Test hosts with suspicious/malicious patterns"""

        suspicious_hosts = [
            "evil.com",
            "attacker.net",
            "payload.evil.com",
            "xss.example.com",
            "<script>.com",
            "javascript:void(0).com",
            "data:text/html.com",
            "../../etc/passwd",
            "localhost.evil.com",
        ]

        for host in suspicious_hosts:
            result = self._test_host(host, should_succeed=False)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host}")

            if not result["passed"]:
                self.results["findings"].append(
                    {
                        "severity": "CRITICAL",
                        "issue": f"Suspicious host accepted: {host}",
                        "details": "Malicious pattern not detected in host header",
                    }
                )

    def test_dns_rebinding(self) -> None:
        """Test DNS rebinding attack scenarios"""

        rebinding_attempts = [
            "127.0.0.1.evil.com",
            "localhost.attacker.com",
            "2130706433",  # 127.0.0.1 as decimal
            "0x7f000001",  # 127.0.0.1 as hex
            "0177.0000.0000.0001",  # 127.0.0.1 as octal
            "3232235521",  # 192.168.0.1 as decimal
        ]

        for host in rebinding_attempts:
            result = self._test_host(host, should_succeed=False)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host}")

            if not result["passed"]:
                self.results["findings"].append(
                    {
                        "severity": "HIGH",
                        "issue": f"DNS rebinding attempt not blocked: {host}",
                        "details": "DNS rebinding attack vulnerability",
                    }
                )

    def test_cache_poisoning(self) -> None:
        """Test cache poisoning via Host header"""

        cache_poisoning_attempts = [
            "evil.com",
            "poisoned-cache.com",
            "attacker.net",
            ".canonical.com",  # Leading dot
            "evil.com\canonical.com",  # Null byte attempt
        ]

        for host in cache_poisoning_attempts:
            result = self._test_host(host, should_succeed=False)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host}")

            if not result["passed"]:
                self.results["findings"].append(
                    {
                        "severity": "HIGH",
                        "issue": f"Cache poisoning attempt not blocked: {host}",
                        "details": "Potential cache poisoning vulnerability",
                    }
                )

    def test_xss_attempts(self) -> None:
        """Test XSS attempts via Host header"""

        xss_attempts = [
            "<script>alert(1)</script>.com",
            "javascript:alert(1).com",
            "data:text/html,<script>alert(1)</script>.com",
            "onload=alert(1).com",
            "';alert(1);//.com",
            '"><script>alert(1)</script>.com',
        ]

        for host in xss_attempts:
            result = self._test_host(host, should_succeed=False)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host}")

            if not result["passed"]:
                self.results["findings"].append(
                    {
                        "severity": "CRITICAL",
                        "issue": f"XSS attempt not blocked: {host}",
                        "details": "Cross-site scripting vulnerability via Host header",
                    }
                )

    def test_subdomains(self) -> None:
        """Test subdomain validation with wildcard patterns"""

        subdomain_tests = [
            # (host, should_succeed, description)
            ("api.example.com", True, "Valid subdomain"),
            ("admin.example.com", True, "Valid admin subdomain"),
            ("evil.example.com", True, "Potentially evil subdomain"),
            ("sub.sub.example.com", True, "Nested subdomain"),
            ("notexample.com", False, "Different domain"),
            ("example.org", False, "Different TLD"),
            ("examplecom", False, "Missing dot"),
        ]

        for host, should_succeed, description in subdomain_tests:
            result = self._test_host(host, should_succeed)
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"  {status}: {host} ({description})")

            if not result["passed"]:
                severity = "HIGH" if not should_succeed else "MEDIUM"
                self.results["findings"].append(
                    {
                        "severity": severity,
                        "issue": f"Subdomain validation failed: {host}",
                        "details": description,
                    }
                )

    def _test_host(self, host: str, should_succeed: bool) -> Dict[str, Any]:
        """
        Test a specific host header

        Args:
            host: Host header value to test
            should_succeed: Whether the request should succeed

        Returns:
            Dictionary with test results
        """
        self.results["tests_run"] += 1

        try:
            # Make request with custom Host header
            url = f"{self.base_url}/health"
            headers = {"Host": host}

            response = requests.get(url, headers=headers, timeout=5)

            # Check if result matches expectation
            passed = (response.status_code == 200) == should_succeed

            if passed:
                self.results["tests_passed"] += 1
            else:
                self.results["tests_failed"] += 1

            return {
                "passed": passed,
                "status_code": response.status_code,
                "expected_success": should_succeed,
                "actual_success": response.status_code == 200,
            }

        except requests.exceptions.RequestException as e:
            # Connection errors count as blocked (good for invalid hosts)
            if not should_succeed:
                self.results["tests_passed"] += 1
                return {
                    "passed": True,
                    "status_code": None,
                    "expected_success": should_succeed,
                    "actual_success": False,
                    "error": str(e),
                }
            else:
                self.results["tests_failed"] += 1
                return {
                    "passed": False,
                    "status_code": None,
                    "expected_success": should_succeed,
                    "actual_success": False,
                    "error": str(e),
                }

    def print_summary(self) -> None:
        """Print test summary"""
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        print(f"Tests Run:    {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print()

        if self.results["findings"]:
            print("SECURITY FINDINGS:")
            print()

            # Sort by severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            self.results["findings"].sort(
                key=lambda f: severity_order.get(f.get("severity", "LOW"), 3)
            )

            for finding in self.results["findings"]:
                severity = finding.get("severity", "LOW")
                icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🔵",
                }.get(severity, "⚪")

                print(f"{icon} [{severity}] {finding.get('issue', 'Unknown Issue')}")
                print(f"   Details: {finding.get('details', 'No details')}")
                print()
        else:
            print("✅ No security findings detected!")
            print()

        # Overall result
        if self.results["tests_failed"] == 0:
            print("✅ Overall Result: PASSED")
        elif self.results["tests_failed"] <= self.results["tests_run"] * 0.1:
            print("⚠️  Overall Result: MOSTLY PASSED")
        else:
            print("❌ Overall Result: FAILED")

        print("=" * 70)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Host header validation security")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the application to test",
    )

    args = parser.parse_args()

    # Run tests
    validator = HostHeaderValidator(args.url)
    results = validator.run_all_tests()

    # Return exit code
    if results["tests_failed"] == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
