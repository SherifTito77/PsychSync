#!/usr/bin/env python3
"""
DNS Poisoning Attack Security Tester
Tests for DNS poisoning vulnerabilities and DNS security configuration
"""

import json
import re
import socket
import subprocess
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class DNSPoisoningTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []
        self.vulnerabilities = []

    def check_dns_servers_configuration(self) -> Dict[str, Any]:
        """Check DNS server configuration and security"""
        print("🔍 Checking DNS server configuration...")

        result = {
            "test_name": "DNS Server Configuration",
            "test_timestamp": datetime.now().isoformat(),
            "dns_servers": [],
            "resolv_conf": {},
            "security_issues": [],
        }

        # Read resolv.conf
        resolv_conf_path = Path("/etc/resolv.conf")
        if resolv_conf_path.exists():
            try:
                with open(resolv_conf_path, "r") as f:
                    resolv_content = f.read()

                result["resolv_conf"]["content"] = resolv_content
                result["resolv_conf"]["exists"] = True

                # Parse DNS servers
                dns_servers = []
                for line in resolv_content.split("\n"):
                    if line.startswith("nameserver"):
                        ip = line.split()[1].strip()
                        dns_servers.append(ip)

                result["dns_servers"] = dns_servers

                # Check for security issues in resolv.conf
                if len(dns_servers) == 0:
                    result["security_issues"].append("No DNS servers configured")

                if len(dns_servers) == 1:
                    result["security_issues"].append(
                        "Single DNS server configured (single point of failure)"
                    )

                # Check for localhost DNS
                if "127.0.0.1" in dns_servers:
                    result["security_issues"].append(
                        "Localhost DNS configured (may be secure if properly configured)"
                    )

            except Exception as e:
                result["security_issues"].append(f"Error reading resolv.conf: {e}")
        else:
            result["resolv_conf"]["exists"] = False
            result["security_issues"].append("resolv.conf file not found")

        # Check system DNS configuration
        try:
            # Test DNS resolution
            test_domains = ["google.com", "cloudflare.com", "localhost"]
            resolved_domains = {}

            for domain in test_domains:
                try:
                    ip_addresses = socket.gethostbyname_ex(domain)
                    resolved_domains[domain] = ip_addresses[2] if ip_addresses else []
                except socket.gaierror:
                    resolved_domains[domain] = []

            result["resolution_test"] = resolved_domains

            # Check for localhost resolution
            if "localhost" in resolved_domains and "127.0.0.1" not in str(
                resolved_domains["localhost"]
            ):
                result["security_issues"].append(
                    "localhost does not resolve to 127.0.0.1"
                )

        except Exception as e:
            result["security_issues"].append(f"DNS resolution test failed: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["security_issues"]) > 2 else "MEDIUM"
        )

        return result

    def test_dns_cache_poisoning(
        self, target_domain: str = "localhost"
    ) -> Dict[str, Any]:
        """Test for DNS cache poisoning vulnerabilities"""
        print(f"🔍 Testing DNS cache poisoning for {target_domain}...")

        result = {
            "test_name": "DNS Cache Poisoning Test",
            "target_domain": target_domain,
            "test_timestamp": datetime.now().isoformat(),
            "cache_tests": [],
            "vulnerabilities": [],
        }

        # Test 1: Normal resolution
        try:
            normal_ip = socket.gethostbyname(target_domain)
            result["normal_resolution"] = normal_ip
        except socket.gaierror:
            result["normal_resolution"] = None
            result["vulnerabilities"].append(f"Cannot resolve {target_domain}")

        # Test 2: Check if server allows recursive queries
        recursion_test = {
            "name": "Recursive Query Test",
            "description": "Test if DNS server allows recursive queries",
            "result": None,
            "vulnerable": False,
        }

        try:
            # Create a simple DNS query (simplified)
            dns_query = subprocess.run(
                ["dig", "+short", target_domain],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if dns_query.returncode == 0:
                recursion_test["result"] = dns_query.stdout.strip()
                # Check if the response is what we expect
                if (
                    result["normal_resolution"]
                    and result["normal_resolution"] in dns_query.stdout
                ):
                    recursion_test["vulnerable"] = False
                else:
                    recursion_test["vulnerable"] = True
                    result["vulnerabilities"].append(
                        "DNS response differs from system resolution"
                    )
            else:
                recursion_test["result"] = dns_query.stderr
                recursion_test["vulnerable"] = True
                result["vulnerabilities"].append("DNS query failed")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            recursion_test["vulnerable"] = True
            result["vulnerabilities"].append("dig command not available or timed out")

        result["cache_tests"].append(recursion_test)

        # Test 3: Check DNSSEC support
        dnssec_test = {
            "name": "DNSSEC Support Test",
            "description": "Test if DNSSEC is supported",
            "result": None,
            "vulnerable": False,
        }

        try:
            dnssec_query = subprocess.run(
                ["dig", "+dnssec", target_domain],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if dnssec_query.returncode == 0:
                dnssec_test["result"] = "DNSSEC query completed"
                # Check for DNSSEC validation
                if "RRSIG" in dnssec_query.stdout:
                    dnssec_test["vulnerable"] = False
                else:
                    dnssec_test["vulnerable"] = True
                    result["vulnerabilities"].append("DNSSEC not validated")
            else:
                dnssec_test["result"] = dnssec_query.stderr
                dnssec_test["vulnerable"] = True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            dnssec_test["vulnerable"] = True
            result["vulnerabilities"].append("DNSSEC test failed")

        result["cache_tests"].append(dnssec_test)

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 2 else "MEDIUM"
        )

        return result

    def analyze_application_dns_usage(self) -> Dict[str, Any]:
        """Analyze how applications use DNS"""
        print("🔍 Analyzing application DNS usage...")

        result = {
            "test_name": "Application DNS Usage Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "dns_references": [],
            "external_domains": [],
            "security_issues": [],
        }

        # Check application files for DNS references
        app_files = [
            "app/main.py",
            "app/core/config.py",
            "frontend/src/services/api.ts",
            "frontend/src/services/authService.ts",
            "frontend/package.json",
        ]

        for app_file in app_files:
            file_path = self.base_path / app_file
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Look for domain references
                    domain_patterns = [
                        r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                        r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                        r"localhost",
                        r"127\.0\.0\.1",
                        r"0\.0\.0\.0",
                    ]

                    file_domains = []
                    for pattern in domain_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match not in file_domains:
                                file_domains.append(match)

                    if file_domains:
                        result["dns_references"].append(
                            {"file": app_file, "domains": file_domains}
                        )

                    # Check for hardcoded external domains
                    external_pattern = r"https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
                    external_matches = re.findall(external_pattern, content)
                    for match in external_matches:
                        if match[1] not in result["external_domains"]:
                            result["external_domains"].append(match[1])

                except Exception as e:
                    result["security_issues"].append(f"Error analyzing {app_file}: {e}")

        # Check for security issues
        hardcoded_domains = result["external_domains"]
        if hardcoded_domains:
            result["security_issues"].append(
                f"Hardcoded external domains: {', '.join(hardcoded_domains)}"
            )

        if "localhost" in str(result["dns_references"]):
            result["security_issues"].append(
                "Localhost references found in configuration"
            )

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "MEDIUM" if result["vulnerable"] else "LOW"

        return result

    def test_dns_spoofing_vulnerability(self) -> Dict[str, Any]:
        """Test for DNS spoofing vulnerabilities"""
        print("🔍 Testing DNS spoofing vulnerabilities...")

        result = {
            "test_name": "DNS Spoofing Vulnerability Test",
            "test_timestamp": datetime.now().isoformat(),
            "spoofing_tests": [],
            "vulnerabilities": [],
        }

        # Test 1: Check hosts file entries
        hosts_test = {
            "name": "Hosts File Analysis",
            "description": "Check /etc/hosts for suspicious entries",
            "result": None,
            "vulnerable": False,
        }

        hosts_path = Path("/etc/hosts")
        if hosts_path.exists():
            try:
                with open(hosts_path, "r") as f:
                    hosts_content = f.read()

                hosts_test["result"] = hosts_content

                # Check for suspicious entries
                suspicious_patterns = [
                    r"\b(?:facebook\.com|google\.com|twitter\.com|linkedin\.com)\b",
                    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*(?:facebook\.com|google\.com)",
                    r"\blockalhost.*(?:google\.com|facebook\.com|twitter\.com)",
                ]

                for pattern in suspicious_patterns:
                    if re.search(pattern, hosts_content, re.IGNORECASE):
                        hosts_test["vulnerable"] = True
                        result["vulnerabilities"].append(
                            f"Suspicious hosts file entry: {pattern}"
                        )

            except Exception as e:
                hosts_test["error"] = str(e)
                result["vulnerabilities"].append(f"Error reading hosts file: {e}")
        else:
            hosts_test["result"] = "Hosts file not found"

        result["spoofing_tests"].append(hosts_test)

        # Test 2: Check for DNS cache pollution vectors
        cache_test = {
            "name": "DNS Cache Pollution Test",
            "description": "Test for DNS cache pollution vectors",
            "vulnerable": False,
        }

        # Check application configuration for DNS cache settings
        config_files = ["app/core/config.py", ".env.dev", ".env.prod"]

        dns_cache_settings = []
        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    if "dns" in content.lower() or "cache" in content.lower():
                        dns_cache_settings.append(config_file)

                except Exception:
                    pass

        if not dns_cache_settings:
            cache_test["vulnerable"] = False
            cache_test["result"] = "No DNS cache configuration found (potentially good)"
        else:
            cache_test["vulnerable"] = True
            cache_test["result"] = (
                f"DNS cache configuration found: {', '.join(dns_cache_settings)}"
            )
            result["vulnerabilities"].append(
                "DNS cache configuration may be vulnerable to pollution"
            )

        result["spoofing_tests"].append(cache_test)

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 1 else "MEDIUM"
        )

        return result

    def check_docker_dns_configuration(self) -> Dict[str, Any]:
        """Check Docker DNS configuration"""
        print("🐳 Checking Docker DNS configuration...")

        result = {
            "test_name": "Docker DNS Configuration",
            "test_timestamp": datetime.now().isoformat(),
            "docker_files": [],
            "dns_settings": [],
            "security_issues": [],
        }

        docker_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "Dockerfile",
        ]

        for docker_file in docker_files:
            file_path = self.base_path / docker_file
            if file_path.exists():
                result["docker_files"].append(docker_file)

                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Look for DNS-related configurations
                    dns_patterns = [
                        "dns:",
                        "DNS:",
                        "resolv:",
                        "RESOLV:",
                        "hosts:",
                        "/etc/resolv.conf",
                    ]

                    file_dns_settings = []
                    for pattern in dns_patterns:
                        if pattern in content:
                            file_dns_settings.append(pattern)

                    if file_dns_settings:
                        result["dns_settings"].append(
                            {"file": docker_file, "settings": file_dns_settings}
                        )

                    # Check for security issues
                    if "8.8.8.8" in content or "8.8.4.4" in content:
                        result["security_issues"].append(
                            "Public DNS servers used in Docker configuration"
                        )

                    if "/etc/hosts" in content and "127.0.0.1" not in content:
                        result["security_issues"].append(
                            "Custom hosts mapping without localhost entry"
                        )

                except Exception as e:
                    result["security_issues"].append(
                        f"Error analyzing {docker_file}: {e}"
                    )

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "MEDIUM" if result["vulnerable"] else "LOW"

        return result

    def generate_dns_security_recommendations(
        self, test_results: List[Dict]
    ) -> List[Dict]:
        """Generate DNS security recommendations"""
        recommendations = []

        for result in test_results:
            if result.get("vulnerable", False):
                if "DNS Server Configuration" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "DNS Infrastructure",
                            "issue": "DNS server configuration issues detected",
                            "recommendation": "Configure multiple secure DNS servers and implement DNSSEC",
                        }
                    )
                elif "DNS Cache Poisoning" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "DNS Security",
                            "issue": "DNS cache poisoning vulnerabilities detected",
                            "recommendation": "Implement DNSSEC validation and secure DNS resolvers",
                        }
                    )
                elif "Application DNS Usage" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "MEDIUM",
                            "category": "Application Security",
                            "issue": "Hardcoded DNS references in application",
                            "recommendation": "Use environment variables for DNS configuration",
                        }
                    )
                elif "DNS Spoofing" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "DNS Security",
                            "issue": "DNS spoofing vulnerabilities detected",
                            "recommendation": "Secure hosts file and implement DNSSEC validation",
                        }
                    )
                elif "Docker DNS Configuration" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "MEDIUM",
                            "category": "Container Security",
                            "issue": "Docker DNS configuration issues",
                            "recommendation": "Use secure DNS resolvers and implement proper DNSSEC validation",
                        }
                    )

        # Add general DNS security recommendations
        recommendations.extend(
            [
                {
                    "priority": "HIGH",
                    "category": "DNS Infrastructure",
                    "issue": "DNSSEC implementation required",
                    "recommendation": "Implement DNSSEC validation for all DNS queries",
                },
                {
                    "priority": "HIGH",
                    "category": "DNS Security",
                    "issue": "Secure DNS resolvers needed",
                    "recommendation": "Use secure DNS resolvers (Cloudflare 1.1.1.1, OpenDNS, etc.)",
                },
                {
                    "priority": "MEDIUM",
                    "category": "DNS Monitoring",
                    "issue": "DNS monitoring not implemented",
                    "recommendation": "Implement DNS resolution monitoring and alerting",
                },
            ]
        )

        return recommendations

    def run_comprehensive_dns_test(self) -> Dict[str, Any]:
        """Run comprehensive DNS security test"""
        print("🔐 STARTING COMPREHENSIVE DNS SECURITY TEST")
        print("=" * 60)

        results = []

        # Test 1: DNS server configuration
        results.append(self.check_dns_servers_configuration())

        # Test 2: DNS cache poisoning
        results.append(self.test_dns_cache_poisoning())

        # Test 3: Application DNS usage
        results.append(self.analyze_application_dns_usage())

        # Test 4: DNS spoofing
        results.append(self.test_dns_spoofing_vulnerability())

        # Test 5: Docker DNS configuration
        results.append(self.check_docker_dns_configuration())

        # Generate recommendations
        recommendations = self.generate_dns_security_recommendations(results)
        results.append({"recommendations": recommendations})

        # Generate summary
        total_tests = len(results) - 1  # Excluding recommendations
        vulnerable_tests = len([r for r in results if r.get("vulnerable", False)])

        summary = {
            "total_tests": total_tests,
            "vulnerable_tests": vulnerable_tests,
            "recommendations_count": len(recommendations),
            "overall_dns_security_score": max(0, 100 - (vulnerable_tests * 20)),
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary,
        }


def main():
    """Main execution function"""
    tester = DNSPoisoningTester()

    try:
        results = tester.run_comprehensive_dns_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 DNS POISONING SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(
            f"🎯 Overall DNS Security Score: {summary['overall_dns_security_score']}/100"
        )

        # Show test results
        for i, test_result in enumerate(
            results["test_results"][:-1], 1
        ):  # Exclude recommendations
            print(f"\n{i}. {test_result['test_name']}:")
            if test_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {test_result.get('risk_level', 'HIGH')}")
                if "vulnerabilities" in test_result:
                    for vuln in test_result["vulnerabilities"]:
                        print(f"      • {vuln}")
                if "security_issues" in test_result:
                    for issue in test_result["security_issues"]:
                        print(f"      • {issue}")
            else:
                print(f"   ✅ SECURE: {test_result.get('risk_level', 'LOW')}")

        # Show recommendations
        print(f"\n💡 DNS SECURITY RECOMMENDATIONS:")
        recommendations = results["test_results"][-1]["recommendations"]
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open(
            "/Users/sheriftito/Downloads/psychsync/dns_poisoning_security_report.json",
            "w",
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: dns_poisoning_security_report.json")

    except Exception as e:
        print(f"❌ Error running DNS poisoning test: {e}")


if __name__ == "__main__":
    main()
