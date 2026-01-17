#!/usr/bin/env python3
"""
Simplified Network Routing Leak Analysis Security Tester
Tests for network routing misconfigurations and information leaks
"""

import json
import re
import subprocess
import socket
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import urllib.parse

class SimplifiedNetworkRoutingLeakTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []

    def test_basic_network_exposure(self) -> Dict[str, Any]:
        """Test for basic network service exposure"""
        print("🔍 Testing basic network service exposure...")

        result = {
            "test_name": "Basic Network Service Exposure Test",
            "test_timestamp": datetime.now().isoformat(),
            "open_ports": [],
            "vulnerabilities": []
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
            (5174, "Vite Dev Alt")
        ]

        for port, service_name in test_ports:
            port_result = {
                "port": port,
                "service": service_name,
                "open": False,
                "security_issues": []
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
                        port_result["security_issues"].append(f"Insecure service exposed: {service_name}")

                    if port in [21, 23] and port_result["open"]:
                        port_result["security_issues"].append(f"Cleartext protocol exposed: {service_name}")

                sock.close()

            except Exception:
                # Port is closed - this is good
                pass

            result["open_ports"].append(port_result)

        # Analyze open ports for security issues
        vulnerable_services = [p for p in result["open_ports"] if p["security_issues"]]
        result["vulnerabilities"] = vulnerable_services

        # Check for development services in production-like environment
        dev_ports = [8000, 5173, 5174]
        dev_exposed = [p for p in result["open_ports"] if p["port"] in dev_ports and p["open"]]
        if dev_exposed:
            result["vulnerabilities"].append("Development services exposed to network")

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = "HIGH" if len(result["vulnerabilities"]) > 2 else "MEDIUM"

        return result

    def test_routing_configuration_files(self) -> Dict[str, Any]:
        """Test routing configuration files for security issues"""
        print("🔍 Testing routing configuration files...")

        result = {
            "test_name": "Routing Configuration Files Test",
            "test_timestamp": datetime.now().isoformat(),
            "config_files_found": [],
            "security_issues": []
        }

        # Look for routing configuration files
        routing_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "nginx.conf",
            ".env.dev",
            ".env.prod"
        ]

        for routing_file in routing_files:
            file_path = self.base_path / routing_file
            if file_path.exists():
                result["config_files_found"].append(routing_file)

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Check for security issues
                    if "proxy_pass" in content and "proxy_set_header" not in content:
                        result["security_issues"].append(f"Proxy pass without security headers in {routing_file}")

                    if "--net=host" in content:
                        result["security_issues"].append(f"Host networking mode used in {routing_file}")

                    if "bridge" in content and "isolated" not in content:
                        result["security_issues"].append(f"Default bridge network used in {routing_file}")

                    # Check for exposed ports in Docker configs
                    if '"8000:8000"' in content or '"5173:5173"' in content:
                        result["security_issues"].append(f"Development ports exposed in {routing_file}")

                    # Check for localhost references
                    if "localhost" in content and routing_file.endswith((".yml", ".yaml")):
                        result["security_issues"].append(f"Localhost references in {routing_file}")

                except Exception as e:
                    result["security_issues"].append(f"Error analyzing {routing_file}: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "HIGH" if len(result["security_issues"]) > 2 else "MEDIUM"

        return result

    def test_application_routing_leaks(self) -> Dict[str, Any]:
        """Test application code for routing information leaks"""
        print("🔍 Testing application routing information leaks...")

        result = {
            "test_name": "Application Routing Leak Test",
            "test_timestamp": datetime.now().isoformat(),
            "files_analyzed": [],
            "leak_vulnerabilities": []
        }

        # Check application files for routing leaks
        app_files = [
            "app/main.py",
            "app/core/config.py",
            "frontend/src/services/api.ts"
        ]

        for app_file in app_files:
            file_path = self.base_path / app_file
            if file_path.exists():
                result["files_analyzed"].append(app_file)

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Check for debug or development routing that might expose information
                    leak_patterns = [
                        (r'print\(.*request\.', 'Debug routing exposes request information'),
                        (r'logging\.debug.*request', 'Debug logging exposes requests'),
                        (r'traceback.*=.*True', 'Tracebacks expose application internals'),
                        (r'app\.debug\s*=\s*True', 'Debug mode enabled in production'),
                        (r'localhost.*8000', 'Localhost development URL exposed'),
                        (r'127\.0\.0\.1.*8000', 'Localhost IP exposed in routing')
                    ]

                    for pattern, description in leak_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            result["leak_vulnerabilities"].append(f"Information leak in {app_file}: {description}")

                except Exception as e:
                    result["leak_vulnerabilities"].append(f"Error analyzing {app_file}: {e}")

        result["vulnerable"] = len(result["leak_vulnerabilities"]) > 0
        result["risk_level"] = "HIGH" if len(result["leak_vulnerabilities"]) > 2 else "MEDIUM"

        return result

    def run_simplified_routing_test(self) -> Dict[str, Any]:
        """Run simplified network routing security test"""
        print("🔐 STARTING SIMPLIFIED NETWORK ROUTING SECURITY TEST")
        print("=" * 60)

        results = []

        # Test 1: Basic network service exposure
        results.append(self.test_basic_network_exposure())

        # Test 2: Routing configuration files
        results.append(self.test_routing_configuration_files())

        # Test 3: Application routing leaks
        results.append(self.test_application_routing_leaks())

        # Generate recommendations
        recommendations = []

        for result in results:
            if result.get("vulnerable", False):
                if "Network Service Exposure" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Network Security",
                        "issue": "Network services exposed unnecessarily",
                        "recommendation": "Restrict access to network services and use firewalls"
                    })
                elif "Routing Configuration" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Routing Security",
                        "issue": "Routing configuration vulnerabilities detected",
                        "recommendation": "Secure routing rules and implement proper access controls"
                    })
                elif "Application Routing Leak" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "Information Security",
                        "issue": "Application routing exposes sensitive information",
                        "recommendation": "Remove debug information from production routing configs"
                    })

        # Add general network security recommendations
        recommendations.extend([
            {
                "priority": "HIGH",
                "category": "Network Security",
                "issue": "Network segmentation required",
                "recommendation": "Implement network segmentation with proper access controls between zones"
            },
            {
                "priority": "MEDIUM",
                "category": "Network Monitoring",
                "issue": "Network security monitoring needed",
                "recommendation": "Implement network traffic monitoring and intrusion detection"
            }
        ])

        results.append({"recommendations": recommendations})

        # Generate summary
        total_tests = len(results) - 1  # Excluding recommendations
        vulnerable_tests = len([r for r in results if r.get("vulnerable", False)])

        summary = {
            "total_tests": total_tests,
            "vulnerable_tests": vulnerable_tests,
            "recommendations_count": len(recommendations),
            "overall_routing_security_score": max(0, 100 - (vulnerable_tests * 20))
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary
        }

def main():
    """Main execution function"""
    tester = SimplifiedNetworkRoutingLeakTester()

    try:
        results = tester.run_simplified_routing_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 NETWORK ROUTING SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(f"🎯 Overall Routing Security Score: {summary['overall_routing_security_score']}/100")

        # Show test results
        for i, test_result in enumerate(results["test_results"][:-1], 1):  # Exclude recommendations
            print(f"\n{i}. {test_result['test_name']}:")
            if test_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {test_result.get('risk_level', 'HIGH')}")
                if "security_issues" in test_result:
                    for issue in test_result["security_issues"]:
                        print(f"      • {issue}")
                if "leak_vulnerabilities" in test_result:
                    for vuln in test_result["leak_vulnerabilities"]:
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
        with open("/Users/sheriftito/Downloads/psychsync/network_routing_security_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: network_routing_security_report.json")

    except Exception as e:
        print(f"❌ Error running network routing security test: {e}")

if __name__ == "__main__":
    main()
