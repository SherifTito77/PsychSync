#!/usr/bin/env python3
"""
Network Routing Rules Leak Analysis Security Tester
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
            "security_issues": []
        }

        # Check for iptables rules
        try:
            # Check if iptables is available and has rules
            iptables_check = subprocess.run(
                ["sudo", "iptables", "-L", "-n"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if iptables_check.returncode == 0:
                result["firewall_active"] = True
                result["rules_found"].append("iptables rules found")

                # Parse iptables output for security issues
                iptables_output = iptables_check.stdout

                # Check for overly permissive rules
                if "ACCEPT 0.0.0.0/0" in iptables_output:
                    result["security_issues"].append("Firewall allows all traffic from any source")

                # Check for default policy
                if "policy ACCEPT" in iptables_output.lower():
                    result["security_issues"].append("Default firewall policy is ACCEPT (should be DROP)")

                # Check for unnecessary open ports
                open_ports = re.findall(r'ACCEPT.*:(\d+)', iptables_output)
                for port in open_ports:
                    port_num = int(port[0])
                    if port_num in [22, 23, 25, 53, 135, 139, 443, 445, 993, 995]:
                        # These are standard ports, check if they're properly restricted
                        pass
                    else:
                        result["security_issues"].append(f"Firewall allows traffic on port {port_num[0]} without restrictions")

            else:
                result["security_issues"].append("iptables command failed or no rules configured")

        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            result["security_issues"].append("Cannot access iptables (insufficient permissions or not available)")

        except Exception as e:
            result["security_issues"].append(f"Error analyzing firewall rules: {e}")

        # Check UFW (Uncomplicated Firewall) if available
        try:
            ufw_check = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if ufw_check.returncode == 0:
                result["rules_found"].append("UFW firewall active")

                # Parse UFW output
                ufw_output = ufw_check.stdout
                if "Status: active" in ufw_output:
                    result["firewall_active"] = True

                # Get UFW rules
                ufw_rules = subprocess.run(
                    ["ufw", "status", "verbose"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if ufw_rules.returncode == 0:
                    # Parse rules for security issues
                    rules_text = ufw_rules.stdout
                    if "ALLOW Anywhere" in rules_text:
                        result["security_issues"].append("UFW allows traffic from anywhere")

                    open_ports = re.findall(r'(\d+/\w+)', rules_text)
                    for port in open_ports:
                        if "ALLOW" in port:
                            port_parts = port.split('/')
                            port_num = port_parts[0]
                            if port_num not in ["22", "80", "443", "8000", "5174"]:
                                result["security_issues"].append(f"UFW allows port {port_num} globally")

        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            result["security_issues"].append("Cannot access UFW (insufficient permissions or not available)")

        except Exception as e:
            result["security_issues"].append(f"Error analyzing UFW: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "HIGH" if len(result["security_issues"]) > 3 else "MEDIUM"

        return result

    def analyze_routing_configuration(self) -> Dict[str, Any]:
        """Analyze routing configuration files"""
        print("🔍 Analyzing routing configuration...")

        result = {
            "test_name": "Routing Configuration Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "routing_files": [],
            "routing_rules": [],
            "security_issues": []
        }

        # Look for routing configuration files
        routing_files = [
            "nginx.conf",
            "apache2.conf",
            "httpd.conf",
            "docker-compose.yml",
            "kubernetes/"
        ]

        for routing_file in routing_files:
            file_path = self.base_path / routing_file
            if file_path.exists() or (routing_file.endswith("/") and file_path.is_dir()):
                result["routing_files"].append(routing_file)

                # Recursively search for routing configs
                config_files = []
                if file_path.is_dir():
                    config_files.extend(list(file_path.rglob("*.conf")))
                else:
                    config_files.append(file_path)

                for config_file in config_files[:3]:  # Limit to avoid too many files
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()

                        # Look for routing patterns
                        routing_patterns = [
                            (r'server_name\s+([^;]+)', "Server name configuration"),
                            (r'location\s+([^;{]+)', "Location directive"),
                            (r'proxy_pass\s+([^;]+)', "Proxy pass configuration"),
                            (r'upstream\s+([^;{]+)', "Upstream configuration"),
                            (r'gateway\s+([^;{]+)', "Gateway configuration"),
                            (r'route\s+([^;{]+)', "Route configuration"),
                            (r'path\s+([^;{]+)', "Path configuration")
                        ]

                        file_rules = []
                        for pattern, description in routing_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                if match not in [r["match"] for r in file_rules]:
                                    file_rules.append({
                                        "pattern": pattern,
                                        "match": match.strip(),
                                        "description": description
                                    })

                        if file_rules:
                            result["routing_rules"].append({
                                "file": str(config_file.relative_to(self.base_path)),
                                "rules": file_rules
                            })

                        # Check for security issues
                        if "proxy_pass" in content and "proxy_set_header" not in content:
                            result["security_issues"].append(f"Proxy pass without security headers in {config_file}")

                        if "location /" in content and "return 404" not in content:
                            result["security_issues"].append(f"Root location without proper restrictions in {config_file}")

                        if "add_header X-Forwarded-For" in content and "proxy_set_header X-Forwarded-Proto" not in content:
                            result["security_issues"].append(f"Forwarded headers not properly sanitized in {config_file}")

                    except Exception as e:
                        result["security_issues"].append(f"Error analyzing {config_file}: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "HIGH" if len(result["security_issues"]) > 2 else "MEDIUM"

        return result

    def test_network_service_exposure(self) -> Dict[str, Any]:
        """Test for exposed network services"""
        print("🔍 Testing network service exposure...")

        result = {
            "test_name": "Network Service Exposure Test",
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
                "banner": None,
                "security_issues": []
            }

            try:
                # Test if port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)

                result_code = sock.connect_ex(("localhost", port))
                if result_code == 0:
                    port_result["open"] = True

                    # Try to get service banner
                    try:
                        sock.send(b"GET / HTTP/1.1\r\n\r\n")
                        banner = sock.recv(1024)
                        port_result["banner"] = banner.decode('utf-8', errors='ignore')[:200]
                    except:
                        pass

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

    def test_container_network_isolation(self) -> Dict[str, Any]:
        """Test Docker container network isolation"""
        print("🐳 Testing container network isolation...")

        result = {
            "test_name": "Container Network Isolation Test",
            "test_timestamp": datetime.now().isoformat(),
            "containers_found": [],
            "network_configs": [],
            "vulnerabilities": []
        }

        # Check Docker containers and their network configuration
        try:
            # Get running containers
            containers_check = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if containers_check.returncode == 0:
                for line in containers_check.stdout.split('\n')[1:]:  # Skip header
                    if line.strip():
                        container_info = line.split('\t')
                        if len(container_info) >= 2:
                            container_id = container_info[0]
                            container_name = container_info[1]
                            container_status = container_info[2] if len(container_info) > 2 else "Unknown"

                            result["containers_found"].append({
                                "id": container_id[:12],  # Truncate for readability
                                "name": container_name,
                                "status": container_status
                            })

                            # Check container network configuration
                            try:
                                inspect_result = subprocess.run(
                                    ["docker", "inspect", container_id, "--format", "{{.NetworkSettings}}"],
                                    capture_output=True,
                                    text=True,
                                        timeout=5
                                    )

                                if inspect_result.returncode == 0:
                                    network_config = inspect_result.stdout
                                    result["network_configs"].append({
                                        "container": container_name,
                                        "config": network_config
                                    })

                            except:
                                pass

            else:
                result["vulnerabilities"].append("Cannot access Docker containers")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            result["vulnerabilities"].append("Docker not available or timeout")

        except Exception as e:
            result["vulnerabilities"].append(f"Error checking Docker containers: {e}")

        # Check Docker network configuration files
        docker_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml"
        ]

        for docker_file in docker_files:
            file_path = self.base_path / docker_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Check network configurations
                    network_patterns = [
                        (r'networks:\s*([^"\n\r]+)', "Docker networks defined"),
                        (r'ports:\s*["\']([^"\']+)["\']', "Port mappings'),
                        (r'links:\s*["\']([^"\']+)["\']', "Container links')
                    ]

                    file_networks = []
                    for pattern, description in network_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match not in [n["match"] for n in file_networks]:
                                file_networks.append({
                                    "pattern": pattern,
                                    "match": match.strip().strip('"').strip("'"),
                                    "description": description
                                })

                    if file_networks:
                        result["network_configs"].append({
                            "file": docker_file,
                            "networks": file_networks
                        })

                    # Check for security issues
                    if "bridge" in content and "isolated" not in content:
                        result["vulnerabilities"].append(f"Default bridge network used in {docker_file}")

                    if "--net=host" in content:
                        result["vulnerabilities"].append(f"Host networking mode used in {docker_file}")

                except Exception as e:
                    result["vulnerabilities"].append(f"Error analyzing {docker_file}: {e}")

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = "MEDIUM" if result["vulnerable"] else "LOW"

        return result

    def analyze_routing_information_leaks(self) -> Dict[str, Any]:
        """Analyze routing for potential information leaks"""
        print("🔍 Analyzing routing information leaks...")

        result = {
            "test_name": "Routing Information Leak Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "leak_sources": [],
            "vulnerabilities": []
        }

        # Check for information leaks in routing configurations
        leak_patterns = [
            (r'server_name.*localhost', "Internal hostname exposed"),
            (r'server_name.*127\.0\.0\.1', "Loopback address exposed"),
            (r'location.*admin.*http', "Admin endpoint exposed"),
            (r'proxy_pass.*admin', "Admin backend exposed"),
            (r'add_header.*X-Real-IP.*\\$remote_addr', "Real IP header exposes source information"),
            (r'add_header.*X-Forwarded-For.*\\$proxy_add_x_forwarded_for', "Forwarded header chain")
        ]

        config_files = [
            "nginx.conf",
            "apache2.conf",
            "httpd.conf",
            "docker-compose.yml"
        ]

        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    file_leaks = []
                    for pattern, description in leak_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            file_leaks.append({
                                "pattern": pattern,
                                "match": match.strip(),
                                "description": description
                            })

                    if file_leaks:
                        result["leak_sources"].append({
                            "file": config_file,
                            "leaks": file_leaks
                        })

                        for leak in file_leaks:
                            result["vulnerabilities"].append(f"Information leak in {config_file}: {leak['description']} - {leak['match']}")

                except Exception as e:
                    result["vulnerabilities"].append(f"Error analyzing {config_file}: {e}")

        # Check application code for routing leaks
        app_files = [
            "app/main.py",
            "app/core/config.py"
        ]

        for app_file in app_files:
            file_path = self.base_path / app_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    app_leaks = []
                    # Check for debug or development routing that might expose information
                    app_patterns = [
                        (r'print\(.*request\.', 'Debug routing exposes request information'),
                        (r'logging\.debug.*request', 'Debug logging exposes requests'),
                        (r'traceback.*=True', 'Tracebacks expose application internals'),
                        (r'app\.debug\s*=\s*True', 'Debug mode enabled in production')
                    ]

                    for pattern, description in app_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            app_leaks.append({
                                "pattern": pattern,
                                "description": description
                            })

                    if app_leaks:
                        result["leak_sources"].append({
                            "file": app_file,
                            "leaks": app_leaks
                        })

                        for leak in app_leaks:
                            result["vulnerabilities"].append(f"Information leak in {app_file}: {leak['description']}")

                except Exception as e:
                    result["vulnerabilities"].append(f"Error analyzing {app_file}: {e}")

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = "HIGH" if len(result["vulnerabilities"]) > 3 else "MEDIUM"

        return result

    def generate_routing_security_recommendations(self, test_results: List[Dict]) -> List[Dict]:
        """Generate network routing security recommendations"""
        recommendations = []

        for result in test_results:
            if result.get("vulnerable", False):
                if "Firewall Rules Analysis" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Network Security",
                        "issue": "Firewall configuration vulnerabilities detected",
                        "recommendation": "Configure proper firewall rules with default deny policy and restricted access"
                    })
                elif "Routing Configuration" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Routing Security",
                        "issue": "Routing configuration vulnerabilities detected",
                        "recommendation": "Secure routing rules and implement proper access controls"
                    })
                elif "Network Service Exposure" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Network Security",
                        "issue": "Network services exposed unnecessarily",
                        "recommendation": "Restrict access to network services and use firewalls"
                    })
                elif "Container Network Isolation" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "Container Security",
                        "issue": "Container network isolation issues detected",
                        "recommendation": "Implement proper Docker network segmentation and isolation"
                    })
                elif "Routing Information Leak" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Information Security",
                        "issue": "Routing configuration exposes sensitive information",
                        "recommendation": "Remove debug information from production routing configs"
                    })

        # Add general network security recommendations
        recommendations.extend([
            {
                "priority": "HIGH",
                "category": "Network Security",
                "issue": "Comprehensive network segmentation required",
                "recommendation": "Implement network segmentation with proper access controls between zones"
            },
            {
                "priority": "HIGH",
                "category": "Network Monitoring",
                "issue": "Network security monitoring not implemented",
                "recommendation": "Implement network traffic monitoring and intrusion detection"
            },
            {
                "priority": "MEDIUM",
                "category": "Network Security",
                "issue": "Network vulnerability scanning not implemented",
                "recommendation": "Implement regular network vulnerability scanning and penetration testing"
            }
        ])

        return recommendations

    def run_comprehensive_routing_test(self) -> Dict[str, Any]:
        """Run comprehensive network routing security test"""
        print("🔐 STARTING COMPREHENSIVE NETWORK ROUTING SECURITY TEST")
        print("=" * 60)

        results = []

        # Test 1: Firewall rules analysis
        results.append(self.analyze_firewall_rules())

        # Test 2: Routing configuration analysis
        results.append(self.analyze_routing_configuration())

        # Test 3: Network service exposure
        results.append(self.test_network_service_exposure())

        # Test 4: Container network isolation
        results.append(self.test_container_network_isolation())

        # Test 5: Routing information leaks
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
            "overall_routing_security_score": max(0, 100 - (vulnerable_tests * 15))
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary
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
        print(f"🎯 Overall Routing Security Score: {summary['overall_routing_security_score']}/100")

        # Show test results
        for i, test_result in enumerate(results["test_results"][:-1], 1):  # Exclude recommendations
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
        with open("/Users/sheriftito/Downloads/psychsync/network_routing_security_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: network_routing_security_report.json")

    except Exception as e:
        print(f"❌ Error running network routing security test: {e}")

if __name__ == "__main__":
    main()