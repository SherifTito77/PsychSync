#!/usr/bin/env python3
"""
SSL/TLS Downgrade Attack Security Tester
Tests for vulnerabilities to SSL/TLS protocol downgrade attacks
"""

import json
import re
import socket
import ssl
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class SSLDowngradeAttackTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []
        self.vulnerabilities = []

    def test_ssl_v2_v3_support(
        self, hostname: str = "localhost", port: int = 443
    ) -> Dict[str, Any]:
        """Test if server supports outdated SSLv2/SSLv3 protocols"""
        print(f"🔍 Testing SSLv2/SSLv3 support on {hostname}:{port}")

        test_result = {
            "test_name": "SSLv2/SSLv3 Protocol Support",
            "hostname": hostname,
            "port": port,
            "vulnerable_protocols": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        # Test SSLv2 (if available)
        test_result["sslv2_supported"] = False
        test_result["sslv3_supported"] = False

        # Note: SSLv2 and SSLv3 support was removed in modern Python versions
        # We'll document this limitation
        try:
            # Try to import SSLv2/SSLv3 constants (may not be available)
            if hasattr(ssl, "PROTOCOL_SSLv2"):
                context = ssl.SSLContext(ssl.PROTOCOL_SSLv2)
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        test_result["vulnerable_protocols"].append("SSLv2")
                        test_result["sslv2_supported"] = True
        except (AttributeError, ssl.SSLError, socket.error, ConnectionRefusedError):
            test_result["sslv2_supported"] = False

        try:
            if hasattr(ssl, "PROTOCOL_SSLv3"):
                context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        test_result["vulnerable_protocols"].append("SSLv3")
                        test_result["sslv3_supported"] = True
        except (AttributeError, ssl.SSLError, socket.error, ConnectionRefusedError):
            test_result["sslv3_supported"] = False

        # Determine vulnerability status
        if test_result["sslv2_supported"] or test_result["sslv3_supported"]:
            test_result["vulnerable"] = True
            test_result["risk_level"] = "CRITICAL"
            test_result["recommendation"] = (
                "Disable SSLv2 and SSLv3 protocols immediately"
            )
        else:
            test_result["vulnerable"] = False
            test_result["risk_level"] = "LOW"

        return test_result

    def test_tls_version_downgrade(
        self, hostname: str = "localhost", port: int = 443
    ) -> Dict[str, Any]:
        """Test for TLS version downgrade vulnerabilities"""
        print(f"🔍 Testing TLS version downgrade attacks on {hostname}:{port}")

        test_result = {
            "test_name": "TLS Version Downgrade Attack",
            "hostname": hostname,
            "port": port,
            "supported_tls_versions": [],
            "weak_versions": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        tls_versions = []

        # Check available TLS versions in current Python version
        # Use modern TLS versions
        try:
            tls_versions.append((ssl.TLSVersion.TLSv1, "TLSv1.0"))
        except AttributeError:
            pass

        try:
            tls_versions.append((ssl.TLSVersion.TLSv1_1, "TLSv1.1"))
        except AttributeError:
            pass

        try:
            tls_versions.append((ssl.TLSVersion.TLSv1_2, "TLSv1.2"))
        except AttributeError:
            pass

        try:
            tls_versions.append((ssl.TLSVersion.TLSv1_3, "TLSv1.3"))
        except AttributeError:
            pass

        for protocol, version_name in tls_versions:
            try:
                context = ssl.SSLContext(protocol)
                # Try to accept all cipher suites to test version support
                context.set_ciphers("ALL:@SECLEVEL=0")

                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        test_result["supported_tls_versions"].append(
                            {
                                "version": version_name,
                                "actual_version": ssock.version(),
                                "cipher": ssock.cipher(),
                            }
                        )

            except (ssl.SSLError, socket.error, ConnectionRefusedError):
                continue

        # Check for weak versions
        weak_versions = ["TLSv1.0", "TLSv1.1"]
        for version_info in test_result["supported_tls_versions"]:
            if version_info["version"] in weak_versions:
                test_result["weak_versions"].append(version_info["version"])

        if test_result["weak_versions"]:
            test_result["vulnerable"] = True
            test_result["risk_level"] = "HIGH"
            test_result["recommendation"] = (
                "Disable TLSv1.0 and TLSv1.1, enforce TLSv1.2+"
            )
        else:
            test_result["vulnerable"] = False
            test_result["risk_level"] = "LOW"

        return test_result

    def test_cipher_suite_downgrade(
        self, hostname: str = "localhost", port: int = 443
    ) -> Dict[str, Any]:
        """Test for weak cipher suite vulnerabilities"""
        print(f"🔍 Testing cipher suite downgrade attacks on {hostname}:{port}")

        test_result = {
            "test_name": "Cipher Suite Downgrade Attack",
            "hostname": hostname,
            "port": port,
            "supported_ciphers": [],
            "weak_ciphers": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        # Define weak cipher suites that should be disabled
        weak_cipher_patterns = [
            "RC4",
            "DES",
            "MD5",
            "NULL",
            "EXPORT",
            "ADH",
            "AECDH",
            "3DES",
        ]

        try:
            context = ssl.create_default_context()
            context.set_ciphers("ALL:@SECLEVEL=0")  # Allow all ciphers for testing

            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get cipher information
                    cipher_info = ssock.cipher()
                    if cipher_info:
                        cipher_name = cipher_info[0]
                        test_result["supported_ciphers"].append(
                            {
                                "name": cipher_name,
                                "version": cipher_info[1],
                                "bits": cipher_info[2],
                            }
                        )

                        # Check if cipher is weak
                        cipher_lower = cipher_name.lower()
                        is_weak = any(
                            pattern.lower() in cipher_lower
                            for pattern in weak_cipher_patterns
                        )

                        if is_weak:
                            test_result["weak_ciphers"].append(cipher_name)

        except Exception as e:
            test_result["error"] = str(e)
            test_result["connection_failed"] = True

        if test_result.get("weak_ciphers"):
            test_result["vulnerable"] = True
            test_result["risk_level"] = "HIGH"
            test_result["recommendation"] = (
                "Disable weak cipher suites and use only strong ciphers"
            )
        elif test_result.get("connection_failed"):
            test_result["vulnerable"] = True
            test_result["risk_level"] = "MEDIUM"
            test_result["recommendation"] = (
                "Server connection failed - investigate TLS configuration"
            )
        else:
            test_result["vulnerable"] = False
            test_result["risk_level"] = "LOW"

        return test_result

    def test_certificate_validation_bypass(
        self, hostname: str = "localhost", port: int = 443
    ) -> Dict[str, Any]:
        """Test for certificate validation bypass vulnerabilities"""
        print(f"🔍 Testing certificate validation bypass on {hostname}:{port}")

        test_result = {
            "test_name": "Certificate Validation Bypass",
            "hostname": hostname,
            "port": port,
            "validation_tests": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        validation_tests = [
            {
                "name": "Self-signed certificate acceptance",
                "context": ssl.create_default_context(),
                "verify_mode": ssl.CERT_NONE,
                "description": "Testing if self-signed certificates are accepted",
            },
            {
                "name": "Hostname verification disabled",
                "context": ssl.create_default_context(),
                "check_hostname": False,
                "description": "Testing if hostname verification can be bypassed",
            },
            {
                "name": "Certificate chain validation disabled",
                "context": ssl.create_default_context(),
                "verify_mode": ssl.CERT_NONE,
                "description": "Testing if certificate chain validation can be bypassed",
            },
        ]

        for test_case in validation_tests:
            test_case_result = {
                "name": test_case["name"],
                "description": test_case["description"],
                "bypass_possible": False,
                "error": None,
            }

            try:
                # Create custom SSL context
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

                if "verify_mode" in test_case:
                    context.verify_mode = test_case["verify_mode"]

                if "check_hostname" in test_case:
                    context.check_hostname = test_case["check_hostname"]

                # Try to connect with bypassed validation
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        test_case_result["bypass_possible"] = True
                        test_case_result["peer_certificate"] = (
                            ssock.getpeercert() is not None
                        )

            except Exception as e:
                test_case_result["error"] = str(e)

            test_result["validation_tests"].append(test_case_result)

        # Determine vulnerability
        bypass_tests = [
            t
            for t in test_result["validation_tests"]
            if t.get("bypass_possible", False)
        ]

        if bypass_tests:
            test_result["vulnerable"] = True
            test_result["risk_level"] = "HIGH"
            test_result["bypass_methods"] = [t["name"] for t in bypass_tests]
            test_result["recommendation"] = (
                "Enforce strict certificate validation and hostname verification"
            )
        else:
            test_result["vulnerable"] = False
            test_result["risk_level"] = "LOW"

        return test_result

    def test_application_ssl_downgrade(
        self, base_url: str = "http://localhost:8000"
    ) -> Dict[str, Any]:
        """Test application-level SSL downgrade attacks"""
        print(f"🔍 Testing application SSL downgrade attacks on {base_url}")

        test_result = {
            "test_name": "Application SSL Downgrade Attack",
            "base_url": base_url,
            "downgrade_tests": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        downgrade_scenarios = [
            {
                "name": "HTTPS to HTTP redirection",
                "url": base_url.replace("https://", "http://"),
                "method": "GET",
                "expected_redirect": True,
                "description": "Test if application redirects HTTPS to HTTP",
            },
            {
                "name": "Protocol switching attack",
                "url": base_url,
                "headers": {"X-Forwarded-Proto": "http"},
                "method": "GET",
                "expected_redirect": False,
                "description": "Test if X-Forwarded-Proto header can force HTTP",
            },
            {
                "name": "SSL stripping attempt",
                "url": base_url,
                "headers": {"X-Forwarded-SSL": "off"},
                "method": "GET",
                "expected_redirect": False,
                "description": "Test if SSL stripping headers affect response",
            },
            {
                "name": "Connection downgrade",
                "url": base_url,
                "headers": {"Connection": "close"},
                "method": "GET",
                "expected_redirect": False,
                "description": "Test if connection headers cause protocol issues",
            },
        ]

        for scenario in downgrade_scenarios:
            scenario_result = {
                "name": scenario["name"],
                "description": scenario["description"],
                "url": scenario["url"],
                "status_code": None,
                "response_headers": {},
                "downgrade_successful": False,
                "error": None,
            }

            try:
                response = requests.request(
                    scenario["method"],
                    scenario["url"],
                    headers=scenario["headers"],
                    timeout=5,
                    verify=False,  # Don't verify SSL for testing
                    allow_redirects=False,
                )

                scenario_result["status_code"] = response.status_code
                scenario_result["response_headers"] = dict(response.headers)

                # Check if downgrade was successful
                if scenario["expected_redirect"]:
                    if response.status_code in [301, 302, 307, 308]:
                        location = response.headers.get("Location", "")
                        if location.startswith("http://"):
                            scenario_result["downgrade_successful"] = True

                # Check for protocol information in response
                if "http://" in scenario_result["url"] and response.ok:
                    scenario_result["downgrade_successful"] = True

            except requests.exceptions.RequestException as e:
                scenario_result["error"] = str(e)

            test_result["downgrade_tests"].append(scenario_result)

        # Determine vulnerability
        successful_downgrades = [
            t
            for t in test_result["downgrade_tests"]
            if t.get("downgrade_successful", False)
        ]

        if successful_downgrades:
            test_result["vulnerable"] = True
            test_result["risk_level"] = "CRITICAL"
            test_result["downgrade_methods"] = [
                t["name"] for t in successful_downgrades
            ]
            test_result["recommendation"] = (
                "Implement HSTS, HTTPS-only enforcement, and secure redirects"
            )
        else:
            test_result["vulnerable"] = False
            test_result["risk_level"] = "LOW"

        return test_result

    def test_implementation_vulnerabilities(self) -> Dict[str, Any]:
        """Test for implementation-specific SSL/TLS vulnerabilities"""
        print("🔍 Testing implementation-specific SSL/TLS vulnerabilities")

        test_result = {
            "test_name": "SSL/TLS Implementation Vulnerabilities",
            "implementation_tests": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        # Test Heartbleed vulnerability (simplified check)
        heartbleed_test = {
            "name": "Heartbleed Vulnerability (OpenSSL)",
            "description": "Test for OpenSSL Heartbleed vulnerability (CVE-2014-0160)",
            "vulnerable": False,
            "details": "",
        }

        try:
            # Check OpenSSL version (simplified)
            result = subprocess.run(
                ["openssl", "version"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                version = result.stdout
                # Check for vulnerable OpenSSL versions
                vulnerable_patterns = ["1.0.1", "1.0.2-alpha", "1.0.2-beta", "1.0.2-rc"]

                for pattern in vulnerable_patterns:
                    if pattern in version:
                        heartbleed_test["vulnerable"] = True
                        heartbleed_test["details"] = (
                            f"Vulnerable OpenSSL version detected: {version.strip()}"
                        )
                        break
                else:
                    heartbleed_test["details"] = (
                        f"OpenSSL version appears safe: {version.strip()}"
                    )
            else:
                heartbleed_test["details"] = "Unable to determine OpenSSL version"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            heartbleed_test["details"] = "OpenSSL not available for testing"

        test_result["implementation_tests"].append(heartbleed_test)

        # Test for POODLE vulnerability
        poodle_test = {
            "name": "POODLE Vulnerability (SSLv3)",
            "description": "Test for POODLE vulnerability (CVE-2014-3566)",
            "vulnerable": False,
            "details": "",
        }

        # This is a simplified test - actual POODLE testing is more complex
        poodle_test["details"] = "Simplified POODLE test - requires manual verification"

        test_result["implementation_tests"].append(poodle_test)

        # Determine overall vulnerability
        vulnerable_tests = [
            t for t in test_result["implementation_tests"] if t.get("vulnerable", False)
        ]

        if vulnerable_tests:
            test_result["vulnerable"] = True
            test_result["risk_level"] = "CRITICAL"
            test_result["vulnerabilities"] = [t["name"] for t in vulnerable_tests]
            test_result["recommendation"] = (
                "Update OpenSSL and libraries to latest versions"
            )
        else:
            test_result["vulnerable"] = False
            test_result["risk_level"] = "LOW"

        return test_result

    def generate_downgrade_protection_recommendations(
        self, test_results: Dict
    ) -> List[Dict]:
        """Generate SSL downgrade protection recommendations"""
        recommendations = []

        # SSLv2/SSLv3 recommendations
        sslv_tests = [
            r
            for r in test_results.get("protocol_tests", [])
            if r.get("name") == "SSLv2/SSLv3 Protocol Support"
        ]
        if any(t.get("vulnerable", False) for t in sslv_tests):
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "Protocol Security",
                    "issue": "SSLv2/SSLv3 protocols are enabled",
                    "recommendation": "Disable SSLv2 and SSLv3 in server configuration and enforce TLSv1.2+ only",
                }
            )

        # TLS version recommendations
        tls_tests = [
            r
            for r in test_results.get("protocol_tests", [])
            if r.get("name") == "TLS Version Downgrade Attack"
        ]
        if any(t.get("vulnerable", False) for t in tls_tests):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Protocol Security",
                    "issue": "Weak TLS versions (1.0/1.1) are supported",
                    "recommendation": "Disable TLSv1.0 and TLSv1.1, enforce TLSv1.2 or higher",
                }
            )

        # Cipher suite recommendations
        cipher_tests = [
            r
            for r in test_results.get("protocol_tests", [])
            if r.get("name") == "Cipher Suite Downgrade Attack"
        ]
        if any(t.get("vulnerable", False) for t in cipher_tests):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Cipher Security",
                    "issue": "Weak cipher suites are supported",
                    "recommendation": "Disable weak ciphers (RC4, DES, 3DES) and use only strong modern ciphers",
                }
            )

        # Certificate validation recommendations
        cert_tests = [
            r
            for r in test_results.get("protocol_tests", [])
            if r.get("name") == "Certificate Validation Bypass"
        ]
        if any(t.get("vulnerable", False) for t in cert_tests):
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "Certificate Security",
                    "issue": "Certificate validation can be bypassed",
                    "recommendation": "Enforce strict certificate validation and hostname verification",
                }
            )

        # Application-level recommendations
        app_tests = test_results.get("application_tests")
        if app_tests and app_tests.get("vulnerable", False):
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "Application Security",
                    "issue": "Application allows SSL downgrade",
                    "recommendation": "Implement HSTS header, HTTPS-only enforcement, and secure redirect handling",
                }
            )

        # General best practices
        recommendations.extend(
            [
                {
                    "priority": "MEDIUM",
                    "category": "Best Practices",
                    "issue": "HSTS not implemented",
                    "recommendation": "Implement HTTP Strict Transport Security with max-age=31536000; includeSubDomains",
                },
                {
                    "priority": "MEDIUM",
                    "category": "Best Practices",
                    "issue": "Certificate pinning not implemented",
                    "recommendation": "Implement HPKP (HTTP Public Key Pinning) for additional security",
                },
                {
                    "priority": "LOW",
                    "category": "Monitoring",
                    "issue": "SSL/TLS monitoring not in place",
                    "recommendation": "Implement continuous SSL/TLS configuration monitoring and alerting",
                },
            ]
        )

        return recommendations

    def run_comprehensive_downgrade_test(self) -> Dict[str, Any]:
        """Run comprehensive SSL/TLS downgrade attack tests"""
        print("🔐 STARTING COMPREHENSIVE SSL/TLS DOWNGRADE ATTACK TEST")
        print("=" * 60)

        results = {}

        # Test 1: SSLv2/SSLv3 support
        print("1️⃣ Testing SSLv2/SSLv3 protocol support...")
        sslv_tests = []
        for port in [443, 8443, 8000, 5174]:
            test_result = self.test_ssl_v2_v3_support("localhost", port)
            sslv_tests.append(test_result)
        results["sslv2_v3_tests"] = sslv_tests

        # Test 2: TLS version downgrade
        print("2️⃣ Testing TLS version downgrade attacks...")
        tls_tests = []
        for port in [443, 8443, 8000, 5174]:
            test_result = self.test_tls_version_downgrade("localhost", port)
            tls_tests.append(test_result)
        results["tls_downgrade_tests"] = tls_tests

        # Test 3: Cipher suite downgrade
        print("3️⃣ Testing cipher suite downgrade attacks...")
        cipher_tests = []
        for port in [443, 8443, 8000, 5174]:
            test_result = self.test_cipher_suite_downgrade("localhost", port)
            cipher_tests.append(test_result)
        results["cipher_downgrade_tests"] = cipher_tests

        # Test 4: Certificate validation bypass
        print("4️⃣ Testing certificate validation bypass...")
        cert_tests = []
        for port in [443, 8443, 8000, 5174]:
            test_result = self.test_certificate_validation_bypass("localhost", port)
            cert_tests.append(test_result)
        results["cert_validation_tests"] = cert_tests

        # Test 5: Application-level SSL downgrade
        print("5️⃣ Testing application-level SSL downgrade...")
        app_tests = self.test_application_ssl_downgrade("http://localhost:8000")
        results["application_tests"] = app_tests

        # Test 6: Implementation vulnerabilities
        print("6️⃣ Testing implementation-specific vulnerabilities...")
        impl_tests = self.test_implementation_vulnerabilities()
        results["implementation_tests"] = impl_tests

        # Combine protocol tests for easier analysis
        all_protocol_tests = sslv_tests + tls_tests + cipher_tests + cert_tests
        results["protocol_tests"] = all_protocol_tests

        # Generate recommendations
        recommendations = self.generate_downgrade_protection_recommendations(results)
        results["recommendations"] = recommendations

        # Generate summary
        total_tests = len(all_protocol_tests) + 2  # +2 for app and impl tests
        vulnerable_tests = len(
            [t for t in all_protocol_tests if t.get("vulnerable", False)]
        )

        results["summary"] = {
            "total_tests": total_tests,
            "vulnerable_tests": vulnerable_tests,
            "application_vulnerable": app_tests.get("vulnerable", False),
            "implementation_vulnerable": impl_tests.get("vulnerable", False),
            "recommendations_count": len(recommendations),
            "overall_downgrade_security_score": self.calculate_downgrade_security_score(
                results
            ),
        }

        return results

    def calculate_downgrade_security_score(self, results: Dict) -> int:
        """Calculate overall SSL downgrade security score"""
        score = 100

        # Deduct points for vulnerable protocol tests
        protocol_tests = results.get("protocol_tests", [])
        vulnerable_protocols = len(
            [t for t in protocol_tests if t.get("vulnerable", False)]
        )
        score -= min(vulnerable_protocols * 20, 60)

        # Deduct points for application vulnerabilities
        app_tests = results.get("application_tests", {})
        if app_tests.get("vulnerable", False):
            score -= 30

        # Deduct points for implementation vulnerabilities
        impl_tests = results.get("implementation_tests", {})
        if impl_tests.get("vulnerable", False):
            score -= 25

        # Deduct points for recommendations (more recommendations = more issues)
        recommendations_count = len(results.get("recommendations", []))
        score -= min(recommendations_count * 3, 20)

        return max(0, min(100, score))


def main():
    """Main execution function"""
    tester = SSLDowngradeAttackTester()

    try:
        results = tester.run_comprehensive_downgrade_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 SSL/TLS DOWNGRADE ATTACK SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"🌐 Application Vulnerable: {summary['application_vulnerable']}")
        print(f"⚙️ Implementation Vulnerable: {summary['implementation_vulnerable']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(
            f"🎯 Overall Downgrade Security Score: {summary['overall_downgrade_security_score']}/100"
        )

        # Show vulnerable protocol tests
        vulnerable_protocols = [
            t for t in results.get("protocol_tests", []) if t.get("vulnerable", False)
        ]
        if vulnerable_protocols:
            print(f"\n🚨 PROTOCOL DOWNGRADE VULNERABILITIES:")
            for test in vulnerable_protocols:
                print(
                    f"  ❌ {test['test_name']} ({test['hostname']}:{test['port']}): {test.get('recommendation', 'Unknown issue')}"
                )

        # Show application vulnerability
        if summary["application_vulnerable"]:
            app_test = results.get("application_tests", {})
            print(f"\n🌐 APPLICATION DOWNGRADE VULNERABILITY:")
            print(
                f"  ❌ Application allows SSL downgrade: {app_test.get('recommendation', 'Unknown issue')}"
            )

        # Show implementation vulnerability
        if summary["implementation_vulnerable"]:
            impl_test = results.get("implementation_tests", {})
            print(f"\n⚙️ IMPLEMENTATION VULNERABILITY:")
            vulnerabilities = impl_test.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                print(
                    f"  ❌ {vuln}: {impl_test.get('recommendation', 'Unknown issue')}"
                )

        # Show recommendations
        print(f"\n💡 SSL DOWNGRADE PROTECTION RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open(
            "/Users/sheriftito/Downloads/psychsync/ssl_downgrade_attack_report.json",
            "w",
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: ssl_downgrade_attack_report.json")

    except Exception as e:
        print(f"❌ Error running SSL downgrade attack test: {e}")


if __name__ == "__main__":
    main()
