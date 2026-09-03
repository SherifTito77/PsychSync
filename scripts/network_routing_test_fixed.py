#!/usr/bin/env python3
"""
Network Routing Rules Leak Analysis Security Tester - FIXED VERSION
Tests for network routing misconfigurations and information leaks
"""

import json
import re
import socket
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class NetworkRoutingLeakTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []
        self.vulnerabilities = []

    def analyze_firewall_rules(self) -> Dict[str, Any]:
        """Analyze firewall and network routing rules"""
        print("🔍 Analyzing firewall rules and network routing...")

        result = {
            "test_name": "Firewall Rules Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "firewall_active": False,
            "rules_found": [],
            "security_issues": [],
        }

        # Check for iptables rules
        try:
            # Check if iptables is available and has rules
            iptables_check = subprocess.run(
                ["sudo", "iptables", "-L", "-n"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if iptables_check.returncode == 0:
                result["firewall_active"] = True
                result["rules_found"].append("iptables rules found")

                # Parse iptables output for security issues
                iptables_output = iptables_check.stdout

                # Check for overly permissive rules
                if "ACCEPT 0.0.0.0/0" in iptables_output:
                    result["security_issues"].append(
                        "Firewall allows all traffic from any source"
                    )

                # Check for default policy
                if "policy ACCEPT" in iptables_output.lower():
                    result["security_issues"].append(
                        "Default firewall policy is ACCEPT (should be DROP)"
                    )

            else:
                result["security_issues"].append(
                    "iptables command failed or no rules configured"
                )

        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            result["security_issues"].append(
                "Cannot access iptables (insufficient permissions or not available)"
            )

        except Exception as e:
            result["security_issues"].append(f"Error analyzing firewall rules: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["security_issues"]) > 3 else "MEDIUM"
        )

        return result

    def test_network_service_exposure(self) -> Dict[str, Any]:
        """Test for exposed network services"""
        print("🔍 Testing network service exposure...")

        result = {
            "test_name": "Network Service Exposure Test",
            "test_timestamp": datetime.now().isoformat(),
            "open_ports": [],
            "vulnerabilities": [],
        }

        # Common ports to check
        test_ports = [
            (21, "FTP"),
            (22, "SSH"),
            (23, "Telnet"),
            (25, "SMTP"),
            (53, "DNS"),
            (80, "HTTP"),
            (110, "POP3"),
            (143, "IMAP"),
            (443, "HTTPS"),
            (3306, "MySQL"),
            (5432, "PostgreSQL"),
            (6379, "Redis"),
            (8000, "HTTP-Alt"),
            (5173, "Vite Dev"),
            (5174, "Vite Dev Alt"),
        ]

        for port, service_name in test_ports:
            port_result = {
                "port": port,
                "service": service_name,
                "open": False,
                "banner": None,
                "security_issues": [],
            }

            try:
                # Test if port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)

                result_code = sock.connect_ex(("localhost", port))
                if result_code == 0:
                    port_result["open"] = True

                    # Check for security issues
                    if service_name in ["Telnet", "FTP"] and port_result["open"]:
                        port_result["security_issues"].append(
                            f"Insecure service exposed: {service_name}"
                        )

                    if port in [21, 23] and port_result["open"]:
                        port_result["security_issues"].append(
                            f"Cleartext protocol exposed: {service_name}"
                        )

                sock.close()

            except Exception:
                # Port is closed - this is good
                pass

            result["open_ports"].append(port_result)

        # Analyze open ports for security issues
        vulnerable_services = [p for p in result["open_ports"] if p["security_issues"]]
        result["vulnerabilities"] = vulnerable_services

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 2 else "MEDIUM"
        )

        return result

    def analyze_routing_information_leaks(self) -> Dict[str, Any]:
        """Analyze routing for potential information leaks"""
        print("🔍 Analyzing routing information leaks...")

        result = {
            "test_name": "Routing Information Leak Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "leak_sources": [],
            "vulnerabilities": [],
        }

        # Check for information leaks in routing configurations
        leak_patterns = [
            (r"server_name.*localhost", "Internal hostname exposed"),
            (r"server_name.*127\.0\.0\.1", "Loopback address exposed"),
            (r"location.*admin.*http", "Admin endpoint exposed"),
            (r"proxy_pass.*admin", "Admin backend exposed"),
        ]

        config_files = [
            "nginx.conf",
            "apache2.conf",
            "httpd.conf",
            "docker-compose.yml",
        ]

        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    file_leaks = []
                    for pattern, description in leak_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            file_leaks.append(
                                {
                                    "pattern": pattern,
                                    "match": match.strip(),
                                    "description": description,
                                }
                            )

                    if file_leaks:
                        result["leak_sources"].append(
                            {"file": config_file, "leaks": file_leaks}
                        )

                        for leak in file_leaks:
                            result["vulnerabilities"].append(
                                f"Information leak in {config_file}: {leak['description']} - {leak['match']}"
                            )

                except Exception as e:
                    result["vulnerabilities"].append(
                        f"Error analyzing {config_file}: {e}"
                    )

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 3 else "MEDIUM"
        )

        return result

    def generate_routing_security_recommendations(
        self, test_results: List[Dict]
    ) -> List[Dict]:
        """Generate network routing security recommendations"""
        recommendations = []

        for result in test_results:
            if result.get("vulnerable", False):
                if "Firewall Rules Analysis" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "Network Security",
                            "issue": "Firewall configuration vulnerabilities detected",
                            "recommendation": "Configure proper firewall rules with default deny policy and restricted access",
                        }
                    )
                elif "Network Service Exposure" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "Network Security",
                            "issue": "Network services exposed unnecessarily",
                            "recommendation": "Restrict access to network services and use firewalls",
                        }
                    )
                elif "Routing Information Leak" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "Information Security",
                            "issue": "Routing configuration exposes sensitive information",
                            "recommendation": "Remove debug information from production routing configs",
                        }
                    )

        # Add general network security recommendations
        recommendations.extend(
            [
                {
                    "priority": "HIGH",
                    "category": "Network Security",
                    "issue": "Comprehensive network segmentation required",
                    "recommendation": "Implement network segmentation with proper access controls between zones",
                },
                {
                    "priority": "HIGH",
                    "category": "Network Monitoring",
                    "issue": "Network security monitoring not implemented",
                    "recommendation": "Implement network traffic monitoring and intrusion detection",
                },
            ]
        )

        return recommendations

    def run_comprehensive_routing_test(self) -> Dict[str, Any]:
        """Run comprehensive network routing security test"""
        print("🔐 STARTING COMPREHENSIVE NETWORK ROUTING SECURITY TEST")
        print("=" * 60)

        results = []

        # Test 1: Firewall rules analysis
        results.append(self.analyze_firewall_rules())

        # Test 2: Network service exposure
        results.append(self.test_network_service_exposure())

        # Test 3: Routing information leaks
        results.append(self.analyze_routing_information_leaks())

        # Generate recommendations
        recommendations = self.generate_routing_security_recommendations(results)
        results.append({"recommendations": recommendations})

        # Generate summary
        total_tests = len(results) - 1  # Excluding recommendations
        vulnerable_tests = len([r for r in results if r.get("vulnerable", False)])

        summary = {
            "total_tests": total_tests,
            "vulnerable_tests": vulnerable_tests,
            "recommendations_count": len(recommendations),
            "overall_routing_security_score": max(0, 100 - (vulnerable_tests * 20)),
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary,
        }


def main():
    """Main execution function"""
    tester = NetworkRoutingLeakTester()

    try:
        results = tester.run_comprehensive_routing_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 NETWORK ROUTING SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(
            f"🎯 Overall Routing Security Score: {summary['overall_routing_security_score']}/100"
        )

        # Show test results
        for i, test_result in enumerate(
            results["test_results"][:-1], 1
        ):  # Exclude recommendations
            print(f"\n{i}. {test_result['test_name']}:")
            if test_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {test_result.get('risk_level', 'HIGH')}")
                if "security_issues" in test_result:
                    for issue in test_result["security_issues"]:
                        print(f"      • {issue}")
                if "vulnerabilities" in test_result:
                    for vuln in test_result["vulnerabilities"]:
                        print(f"      • {vuln}")
            else:
                print(f"   ✅ SECURE: {test_result.get('risk_level', 'LOW')}")

        # Show recommendations
        print(f"\n💡 NETWORK ROUTING SECURITY RECOMMENDATIONS:")
        recommendations = results["test_results"][-1]["recommendations"]
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open(
            "/Users/sheriftito/Downloads/psychsync/network_routing_security_report.json",
            "w",
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: network_routing_security_report.json")

    except Exception as e:
        print(f"❌ Error running network routing security test: {e}")


if __name__ == "__main__":
    main()
