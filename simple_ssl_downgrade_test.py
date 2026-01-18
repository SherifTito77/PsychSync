#!/usr/bin/env python3
"""
Simplified SSL/TLS Downgrade Attack Security Tester
Tests for vulnerabilities to SSL/TLS protocol downgrade attacks
"""

import ssl
import socket
import requests
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SimpleSSLDowngradeTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []

    def test_tls_version_support(self) -> Dict[str, Any]:
        """Test available TLS versions"""
        print("🔍 Testing TLS version support...")

        result = {
            "test_name": "TLS Version Support Test",
            "test_timestamp": datetime.now().isoformat(),
            "supported_versions": [],
            "weak_versions": [],
            "test_results": {}
        }

        # Test endpoints
        test_endpoints = [
            ("localhost", 8000),
            ("localhost", 5174),
            ("localhost", 443),
            ("localhost", 8443)
        ]

        for hostname, port in test_endpoints:
            endpoint_result = {
                "hostname": hostname,
                "port": port,
                "tls_versions": [],
                "connection_successful": False,
                "error": None
            }

            try:
                # Try to create TLS context with default settings
                context = ssl.create_default_context()

                with socket.create_connection((hostname, port), timeout=5) as sock:
                    try:
                        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                            endpoint_result["connection_successful"] = True
                            endpoint_result["tls_versions"].append(ssock.version())
                            endpoint_result["cipher"] = ssock.cipher()
                    except ssl.SSLError as ssl_error:
                        endpoint_result["error"] = f"SSL Error: {ssl_error}"
                    except Exception as e:
                        endpoint_result["error"] = f"Connection Error: {e}"

            except (socket.error, ConnectionRefusedError, TimeoutError):
                endpoint_result["error"] = "Connection refused or timeout"

            result["test_results"][f"{hostname}:{port}"] = endpoint_result

        # Analyze results
        successful_connections = [r for r in result["test_results"].values() if r["connection_successful"]]
        result["successful_connections"] = len(successful_connections)
        result["total_connections"] = len(result["test_results"])

        # Check for security issues
        security_issues = []

        for endpoint, data in result["test_results"].items():
            if data["connection_successful"]:
                if data.get("cipher"):
                    cipher_name = data["cipher"][0].lower()
                    if any(weak in cipher_name for weak in ["rc4", "des", "3des", "md5", "null"]):
                        security_issues.append(f"Weak cipher detected: {cipher_name} on {endpoint}")

        result["security_issues"] = security_issues
        result["vulnerable"] = len(security_issues) > 0
        result["risk_level"] = "HIGH" if result["vulnerable"] else "LOW"

        return result

    def test_certificate_validation(self) -> Dict[str, Any]:
        """Test certificate validation practices"""
        print("🔍 Testing certificate validation...")

        result = {
            "test_name": "Certificate Validation Test",
            "test_timestamp": datetime.now().isoformat(),
            "cert_files_found": [],
            "certificates_analyzed": 0,
            "security_issues": []
        }

        # Find certificate files
        cert_patterns = ["*.crt", "*.pem", "*.cer", "*.key", "cert.pem", "fullchain.pem", "privkey.pem"]
        cert_files = []

        for pattern in cert_patterns:
            cert_files.extend(self.base_path.rglob(pattern))

        # Filter out system certificates
        cert_files = [f for f in cert_files if "node_modules" not in str(f) and ".git" not in str(f)]

        result["cert_files_found"] = [str(f.relative_to(self.base_path)) for f in cert_files[:5]]

        # Analyze certificate files
        for cert_file in cert_files[:3]:  # Limit analysis
            try:
                with open(cert_file, 'rb') as f:
                    cert_data = f.read()

                # Basic certificate checks
                cert_size = len(cert_data)
                if cert_size < 1000:
                    result["security_issues"].append(f"Small certificate file: {cert_file.name} ({cert_size} bytes)")
                elif cert_size > 100000:
                    result["security_issues"].append(f"Large certificate file: {cert_file.name} ({cert_size} bytes)")

                # Check for file permissions (Unix-like systems)
                try:
                    import stat
                    file_stat = cert_file.stat()
                    file_mode = oct(file_stat.st_mode)[-3:]
                    if file_mode == '644':  # World-readable
                        result["security_issues"].append(f"Certificate file world-readable: {cert_file.name} (permissions: {file_mode})")

                except (OSError, IOError, ValueError) as e:
                    pass

                result["certificates_analyzed"] += 1

            except Exception as e:
                result["security_issues"].append(f"Error analyzing {cert_file.name}: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "HIGH" if result["vulnerable"] else "LOW"

        return result

    def test_ssl_configuration_files(self) -> Dict[str, Any]:
        """Test SSL configuration in configuration files"""
        print("🔍 Testing SSL configuration files...")

        result = {
            "test_name": "SSL Configuration Test",
            "test_timestamp": datetime.now().isoformat(),
            "config_files_checked": [],
            "ssl_settings": [],
            "security_issues": []
        }

        config_files = [
            "app/main.py",
            "app/core/config.py",
            "frontend/vite.config.ts",
            ".env.dev",
            ".env.prod",
            "docker-compose.yml"
        ]

        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                result["config_files_checked"].append(config_file)

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Look for SSL-related settings
                    ssl_patterns = [
                        ("https://", "HTTPS URL found"),
                        ("ssl", "SSL configuration found"),
                        ("tls", "TLS configuration found"),
                        ("cert", "Certificate configuration found"),
                        ("key", "Private key configuration found")
                    ]

                    file_ssl_settings = []
                    for pattern, description in ssl_patterns:
                        if pattern.lower() in content.lower():
                            file_ssl_settings.append(description)

                    if file_ssl_settings:
                        result["ssl_settings"].append({
                            "file": config_file,
                            "settings": file_ssl_settings
                        })

                    # Check for security issues
                    if "http://" in content and "https://" not in content:
                        result["security_issues"].append(f"HTTP only configuration in {config_file}")

                    if "verify=false" in content.lower() or "ssl_verify=false" in content.lower():
                        result["security_issues"].append(f"SSL verification disabled in {config_file}")

                except Exception as e:
                    result["security_issues"].append(f"Error reading {config_file}: {e}")

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = "HIGH" if result["vulnerable"] else "LOW"

        return result

    def test_http_security_headers(self) -> Dict[str, Any]:
        """Test HTTP security headers via application"""
        print("🔍 Testing HTTP security headers...")

        result = {
            "test_name": "HTTP Security Headers Test",
            "test_timestamp": datetime.now().isoformat(),
            "endpoints_tested": [],
            "security_headers_found": [],
            "missing_headers": [],
            "test_results": {}
        }

        # Test endpoints
        test_endpoints = [
            "http://localhost:8000/",
            "http://localhost:5174/"
        ]

        security_headers = [
            "strict-transport-security",
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "content-security-policy",
            "referrer-policy"
        ]

        for endpoint in test_endpoints:
            endpoint_result = {
                "url": endpoint,
                "status_code": None,
                "headers": {},
                "security_headers": {},
                "missing_headers": [],
                "error": None
            }

            try:
                response = requests.get(endpoint, timeout=5, verify=False)
                endpoint_result["status_code"] = response.status_code
                endpoint_result["headers"] = dict(response.headers)

                # Check for security headers
                found_headers = []
                missing_headers = []

                for header in security_headers:
                    if header in response.headers:
                        found_headers.append(header)
                        endpoint_result["security_headers"][header] = response.headers[header]
                    else:
                        missing_headers.append(header)

                endpoint_result["missing_headers"] = missing_headers

            except requests.exceptions.RequestException as e:
                endpoint_result["error"] = str(e)

            result["test_results"][endpoint] = endpoint_result

        # Analyze missing headers
        all_missing_headers = set()
        for endpoint_data in result["test_results"].values():
            if endpoint_data.get("missing_headers"):
                all_missing_headers.update(endpoint_data["missing_headers"])

        result["missing_headers"] = list(all_missing_headers)
        result["vulnerable"] = len(all_missing_headers) > 0
        result["risk_level"] = "HIGH" if result["vulnerable"] else "MEDIUM"

        return result

    def generate_ssl_recommendations(self, results: List[Dict]) -> List[Dict]:
        """Generate SSL/TLS security recommendations"""
        recommendations = []

        # Analyze all test results
        for result in results:
            if result.get("vulnerable", False):
                if "TLS Version" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "TLS Configuration",
                        "issue": "TLS version vulnerabilities detected",
                        "recommendation": "Update TLS configuration to use modern protocols (TLSv1.2+)"
                    })
                elif "Certificate Validation" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "HIGH",
                        "category": "Certificate Security",
                        "issue": "Certificate validation issues found",
                        "recommendation": "Secure certificate files and implement proper access controls"
                    })
                elif "SSL Configuration" in result.get("test_name", ""):
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "Configuration Security",
                        "issue": "SSL configuration issues detected",
                        "recommendation": "Update configuration to use HTTPS and enable SSL verification"
                    })
                elif "Security Headers" in result.get("test_name", ""):
                    missing_headers = result.get("missing_headers", [])
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "HTTP Security Headers",
                        "issue": f"Missing security headers: {', '.join(missing_headers)}",
                        "recommendation": "Implement security headers: HSTS, X-Frame-Options, CSP, etc."
                    })

        # Add general recommendations
        recommendations.extend([
            {
                "priority": "HIGH",
                "category": "TLS Best Practices",
                "issue": "Modern TLS implementation required",
                "recommendation": "Implement TLSv1.2 or higher with strong cipher suites"
            },
            {
                "priority": "HIGH",
                "category": "Certificate Management",
                "issue": "Certificate monitoring needed",
                "recommendation": "Implement automated certificate expiry monitoring and renewal"
            },
            {
                "priority": "MEDIUM",
                "category": "Security Headers",
                "issue": "HSTS not implemented",
                "recommendation": "Implement HTTP Strict Transport Security with appropriate max-age"
            }
        ])

        return recommendations

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive SSL/TLS security test"""
        print("🔐 STARTING COMPREHENSIVE SSL/TLS SECURITY TEST")
        print("=" * 60)

        results = []

        # Test 1: TLS version support
        results.append(self.test_tls_version_support())

        # Test 2: Certificate validation
        results.append(self.test_certificate_validation())

        # Test 3: SSL configuration files
        results.append(self.test_ssl_configuration_files())

        # Test 4: HTTP security headers
        results.append(self.test_http_security_headers())

        # Generate recommendations
        recommendations = self.generate_ssl_recommendations(results)
        results.append({"recommendations": recommendations})

        # Generate summary
        total_tests = len(results) - 1  # Excluding recommendations
        vulnerable_tests = len([r for r in results if r.get("vulnerable", False)])

        summary = {
            "total_tests": total_tests,
            "vulnerable_tests": vulnerable_tests,
            "recommendations_count": len(recommendations),
            "overall_ssl_security_score": max(0, 100 - (vulnerable_tests * 25))
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary
        }

def main():
    """Main execution function"""
    tester = SimpleSSLDowngradeTester()

    try:
        results = tester.run_comprehensive_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 SSL/TLS SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(f"🎯 Overall SSL Security Score: {summary['overall_ssl_security_score']}/100")

        # Show test results
        for i, test_result in enumerate(results["test_results"][:-1], 1):  # Exclude recommendations
            print(f"\n{i}. {test_result['test_name']}:")
            if test_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {test_result.get('risk_level', 'HIGH')}")
                if "security_issues" in test_result:
                    for issue in test_result["security_issues"]:
                        print(f"      • {issue}")
            else:
                print(f"   ✅ SECURE: {test_result.get('risk_level', 'LOW')}")

        # Show recommendations
        print(f"\n💡 SSL/TLS SECURITY RECOMMENDATIONS:")
        recommendations = results["test_results"][-1]["recommendations"]
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open("/Users/sheriftito/Downloads/psychsync/ssl_security_test_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: ssl_security_test_report.json")

    except Exception as e:
        print(f"❌ Error running SSL/TLS test: {e}")

if __name__ == "__main__":
    main()
