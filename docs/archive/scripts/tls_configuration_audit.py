#!/usr/bin/env python3
"""
TLS/SSL Configuration Security Audit Tool
Comprehensive analysis of TLS configuration security
"""

import json
import re
import socket
import ssl
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import certifi
import requests


class TLSConfigurationAuditor:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.results = []
        self.tls_vulnerabilities = []
        self.certificate_analysis = []

    def scan_tls_configurations(self) -> List[Dict]:
        """Scan for TLS configuration files and settings"""
        print("🔍 Scanning for TLS configuration files...")

        config_files = []
        tls_config_patterns = [
            "*nginx*.conf",
            "*apache*.conf",
            "*ssl*.conf",
            "*tls*.conf",
            "*.pem",
            "*.crt",
            "*.key",
            "cert.pem",
            "fullchain.pem",
            "privkey.pem",
        ]

        for pattern in tls_config_patterns:
            config_files.extend(self.base_path.rglob(pattern))

        # Filter out node_modules and git directories
        config_files = [
            f
            for f in config_files
            if "node_modules" not in str(f) and ".git" not in str(f)
        ]

        print(f"    📁 Found {len(config_files)} TLS-related files")

        return config_files

    def analyze_ssl_certificate(self, cert_path: Path) -> Dict[str, Any]:
        """Analyze SSL certificate for security issues"""
        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()

            cert = ssl.PEM_cert_to_DER_cert(cert_data)
            cert_obj = ssl.DER_cert_to_PEM_cert(cert)
            x509 = ssl.PEM_cert_to_DER_cert(cert_obj)

            # For Python 3.9+, use cryptography library for proper cert analysis
            try:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend

                cert_obj = x509.load_pem_x509_certificate(cert_data, default_backend())

                analysis = {
                    "file": str(cert_path.relative_to(self.base_path)),
                    "subject": cert_obj.subject.rfc4514_string(),
                    "issuer": cert_obj.issuer.rfc4514_string(),
                    "not_valid_before": cert_obj.not_valid_before.isoformat(),
                    "not_valid_after": cert_obj.not_valid_after.isoformat(),
                    "is_expired": cert_obj.not_valid_after < datetime.now(),
                    "days_until_expiry": (
                        cert_obj.not_valid_after - datetime.now()
                    ).days,
                    "serial_number": str(cert_obj.serial_number),
                    "version": cert_obj.version.name,
                    "signature_algorithm": cert_obj.signature_algorithm_oid._name,
                    "public_key_size": cert_obj.public_key().key_size,
                    "extensions": [],
                }

                # Analyze certificate extensions
                for ext in cert_obj.extensions:
                    if ext.critical:
                        analysis["extensions"].append(
                            {
                                "name": ext.oid._name,
                                "critical": True,
                                "value": str(ext.value),
                            }
                        )

                # Check for common certificate issues
                issues = []
                if cert_obj.not_valid_after < datetime.now():
                    issues.append("Certificate has expired")
                elif (cert_obj.not_valid_after - datetime.now()).days < 30:
                    issues.append("Certificate expires within 30 days")

                if cert_obj.public_key().key_size < 2048:
                    issues.append(
                        f"Weak key size: {cert_obj.public_key().key_size} bits"
                    )

                if cert_obj.issuer == cert_obj.subject:
                    issues.append("Self-signed certificate detected")

                analysis["security_issues"] = issues
                analysis["risk_level"] = "HIGH" if issues else "LOW"

                return analysis

            except ImportError:
                # Fallback analysis without cryptography library
                return {
                    "file": str(cert_path.relative_to(self.base_path)),
                    "error": "cryptography library not available for detailed analysis",
                    "risk_level": "MEDIUM",
                }

        except Exception as e:
            return {
                "file": str(cert_path.relative_to(self.base_path)),
                "error": str(e),
                "risk_level": "HIGH",
            }

    def analyze_application_tls_config(self) -> Dict[str, Any]:
        """Analyze application TLS configuration"""
        print("🔧 Analyzing application TLS configuration...")

        config_files = [
            "app/main.py",
            "app/core/config.py",
            "frontend/vite.config.ts",
            "frontend/package.json",
            ".env.dev",
            ".env.prod",
        ]

        analysis = {
            "tls_enabled": False,
            "http_configured": False,
            "https_configured": False,
            "certificate_files": [],
            "tls_versions": [],
            "cipher_suites": [],
            "security_issues": [],
        }

        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for TLS configuration
                    if re.search(r"https?://", content, re.IGNORECASE):
                        analysis["http_configured"] = True

                    if re.search(r"https://", content, re.IGNORECASE):
                        analysis["https_configured"] = True
                        analysis["tls_enabled"] = True

                    # Look for certificate paths
                    cert_matches = re.findall(
                        r'(cert|certificate|ssl_cert|tls_cert)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        content,
                        re.IGNORECASE,
                    )
                    for match in cert_matches:
                        analysis["certificate_files"].append(match[1])

                    # Look for TLS version configuration
                    tls_version_matches = re.findall(
                        r'(tls_version|ssl_version|proto)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        content,
                        re.IGNORECASE,
                    )
                    for match in tls_version_matches:
                        analysis["tls_versions"].append(match[1])

                    # Check for security issues
                    if "http://" in content:
                        analysis["security_issues"].append(
                            "Plain HTTP configuration detected"
                        )

                    if (
                        "ssl_verify=False" in content.lower()
                        or "verify_ssl=False" in content.lower()
                    ):
                        analysis["security_issues"].append("SSL verification disabled")

                    if "allow_weak_ssl=True" in content.lower():
                        analysis["security_issues"].append("Weak SSL allowed")

                except Exception as e:
                    analysis["security_issues"].append(
                        f"Error analyzing {config_file}: {e}"
                    )

        # Determine risk level
        if not analysis["tls_enabled"]:
            analysis["risk_level"] = "CRITICAL"
            analysis["security_issues"].append("TLS not configured")
        elif len(analysis["security_issues"]) > 0:
            analysis["risk_level"] = "HIGH"
        else:
            analysis["risk_level"] = "LOW"

        return analysis

    def test_server_tls_configuration(
        self, hostname: str = "localhost", port: int = 8000
    ) -> Dict[str, Any]:
        """Test TLS configuration on a running server"""
        print(f"🌐 Testing TLS configuration on {hostname}:{port}")

        results = {
            "hostname": hostname,
            "port": port,
            "tls_supported": False,
            "certificate_info": None,
            "tls_versions": [],
            "cipher_suites": [],
            "security_issues": [],
            "test_timestamp": datetime.now().isoformat(),
        }

        try:
            # Test TLS connection
            context = ssl.create_default_context()

            # Set a timeout
            socket.setdefaulttimeout(10)

            with socket.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    results["tls_supported"] = True

                    # Get certificate information
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_pem = ssock.getpeercert()

                    results["certificate_info"] = {
                        "subject": dict(cert_pem["subject"]),
                        "issuer": dict(cert_pem["issuer"]),
                        "not_valid_before": cert_pem["notBefore"],
                        "not_valid_after": cert_pem["notAfter"],
                        "serial_number": cert_pem.get("serialNumber"),
                        "version": cert_pem.get("version"),
                    }

                    # Check certificate expiry
                    expiry_date = datetime.strptime(
                        cert_pem["notAfter"], "%b %d %H:%M:%S %Y %Z"
                    )
                    if expiry_date < datetime.now():
                        results["security_issues"].append("Certificate has expired")
                    elif (expiry_date - datetime.now()).days < 30:
                        results["security_issues"].append(
                            "Certificate expires within 30 days"
                        )

                    # Get TLS version
                    results["tls_versions"].append(ssock.version())

                    # Get cipher suite
                    results["cipher_suites"].append(ssock.cipher())

        except ssl.SSLError as e:
            results["security_issues"].append(f"SSL/TLS Error: {e}")
            results["tls_supported"] = False
        except socket.timeout:
            results["security_issues"].append("Connection timeout")
            results["tls_supported"] = False
        except ConnectionRefusedError:
            results["security_issues"].append("Connection refused")
            results["tls_supported"] = False
        except Exception as e:
            results["security_issues"].append(f"Connection error: {e}")
            results["tls_supported"] = False

        # Determine risk level
        if not results["tls_supported"]:
            results["risk_level"] = "HIGH"
        elif len(results["security_issues"]) > 0:
            results["risk_level"] = "MEDIUM"
        else:
            results["risk_level"] = "LOW"

        return results

    def check_docker_tls_configuration(self) -> Dict[str, Any]:
        """Check TLS configuration in Docker containers"""
        print("🐳 Checking Docker TLS configuration...")

        docker_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "Dockerfile",
            "deployment/Dockerfile",
        ]

        analysis = {
            "docker_tls_configured": False,
            "https_ports": [],
            "certificate_volumes": [],
            "security_issues": [],
        }

        for docker_file in docker_files:
            file_path = self.base_path / docker_file
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for HTTPS port mappings
                    https_port_matches = re.findall(r'- "(\d+):\d+"', content)
                    for match in https_port_matches:
                        if match in ["443", "8443", "9443"]:
                            analysis["https_ports"].append(match)
                            analysis["docker_tls_configured"] = True

                    # Check for certificate volume mounts
                    cert_volume_matches = re.findall(
                        r"- ([^:]+/[^:]+\.crt|[^:]+/[^:]+\.pem|[^:]+/[^:]+\.key):([^:]+)",
                        content,
                    )
                    for match in cert_volume_matches:
                        analysis["certificate_volumes"].append(match[0])

                    # Check for TLS environment variables
                    tls_env_matches = re.findall(
                        r"(TLS_|SSL_|CERT_|KEY_)[^=]*=[^s]+", content, re.IGNORECASE
                    )
                    if tls_env_matches:
                        analysis["docker_tls_configured"] = True

                    # Security checks
                    if "ports:" in content and "443" not in content:
                        analysis["security_issues"].append(
                            "Docker container exposes HTTP without HTTPS"
                        )

                    if (
                        "restart: always" not in content
                        and "restart: unless-stopped" not in content
                    ):
                        analysis["security_issues"].append(
                            "Docker container lacks proper restart policy"
                        )

                except Exception as e:
                    analysis["security_issues"].append(
                        f"Error analyzing {docker_file}: {e}"
                    )

        # Determine risk level
        if not analysis["docker_tls_configured"]:
            analysis["risk_level"] = "HIGH"
        elif len(analysis["security_issues"]) > 0:
            analysis["risk_level"] = "MEDIUM"
        else:
            analysis["risk_level"] = "LOW"

        return analysis

    def check_nginx_ssl_configuration(self) -> Dict[str, Any]:
        """Check nginx SSL configuration"""
        print("🌐 Checking nginx SSL configuration...")

        nginx_files = list(self.base_path.rglob("*nginx*.conf"))

        analysis = {
            "nginx_configured": len(nginx_files) > 0,
            "ssl_directives": [],
            "certificate_files": [],
            "security_issues": [],
        }

        ssl_directives = {
            "ssl_protocols": "TLSv1.2 TLSv1.3",
            "ssl_ciphers": "HIGH:!aNULL:!MD5",
            "ssl_prefer_server_ciphers": "on",
            "ssl_session_cache": "shared:SSL:10m",
            "ssl_session_timeout": "10m",
        }

        for nginx_file in nginx_files:
            try:
                with open(nginx_file, "r") as f:
                    content = f.read()

                # Check for SSL directives
                for directive, recommended_value in ssl_directives.items():
                    if directive in content:
                        analysis["ssl_directives"].append(directive)

                # Check for certificate files
                cert_matches = re.findall(
                    r'(ssl_certificate|ssl_certificate_key)["\']?\s*([^;]+);', content
                )
                for match in cert_matches:
                    analysis["certificate_files"].append(match[1])

                # Security checks
                if "ssl_protocols TLSv1 TLSv1.1" in content:
                    analysis["security_issues"].append(
                        "Insecure TLS protocols (TLSv1.0, TLSv1.1) enabled"
                    )

                if "ssl_ciphers LOW:!aNULL:!MD5" in content:
                    analysis["security_issues"].append("Weak cipher suites enabled")

                if "listen 80;" in content and "listen 443 ssl;" not in content:
                    analysis["security_issues"].append(
                        "HTTP port 80 enabled without HTTPS redirect"
                    )

                if "add_header Strict-Transport-Security" not in content:
                    analysis["security_issues"].append("HSTS header not configured")

            except Exception as e:
                analysis["security_issues"].append(f"Error analyzing {nginx_file}: {e}")

        # Determine risk level
        if len(analysis["security_issues"]) > 0:
            analysis["risk_level"] = "HIGH"
        elif not analysis["nginx_configured"]:
            analysis["risk_level"] = "MEDIUM"
        else:
            analysis["risk_level"] = "LOW"

        return analysis

    def generate_tls_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Generate TLS security recommendations"""
        recommendations = []

        # Certificate recommendations
        certs_with_issues = [
            cert
            for cert in analysis_results.get("certificates", [])
            if cert.get("risk_level") in ["HIGH", "MEDIUM"]
        ]

        if certs_with_issues:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Certificate Security",
                    "issue": f"{len(certs_with_issues)} certificates have security issues",
                    "recommendation": "Update or replace vulnerable certificates, ensure proper key sizes (2048+ bits), and monitor expiry dates",
                }
            )

        # Application TLS recommendations
        app_tls = analysis_results.get("application_tls", {})
        if app_tls.get("risk_level") in ["HIGH", "MEDIUM"]:
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "Application TLS",
                    "issue": app_tls.get("risk_level", "")
                    + " risk in application TLS configuration",
                    "recommendation": "Enable HTTPS, disable SSL verification bypass, and configure secure TLS settings",
                }
            )

        # Docker TLS recommendations
        docker_tls = analysis_results.get("docker_tls", {})
        if docker_tls.get("risk_level") in ["HIGH", "MEDIUM"]:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Docker Security",
                    "issue": "Docker containers lack proper TLS configuration",
                    "recommendation": "Configure HTTPS ports, mount certificates properly, and implement security policies",
                }
            )

        # Server testing recommendations
        server_tests = analysis_results.get("server_tests", [])
        failed_tests = [
            test for test in server_tests if not test.get("tls_supported", True)
        ]
        if failed_tests:
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "Server TLS",
                    "issue": f"{len(failed_tests)} servers have TLS issues",
                    "recommendation": "Configure TLS properly on all servers, ensure valid certificates, and disable insecure protocols",
                }
            )

        # General TLS best practices
        recommendations.extend(
            [
                {
                    "priority": "MEDIUM",
                    "category": "TLS Best Practices",
                    "issue": "HSTS not configured",
                    "recommendation": "Implement HTTP Strict Transport Security header with appropriate max-age",
                },
                {
                    "priority": "MEDIUM",
                    "category": "TLS Best Practices",
                    "issue": "TLS 1.2/1.3 not enforced",
                    "recommendation": "Disable TLS 1.0/1.1 and enforce TLS 1.2 or higher",
                },
                {
                    "priority": "LOW",
                    "category": "Certificate Management",
                    "issue": "Certificate monitoring needed",
                    "recommendation": "Implement automated certificate expiry monitoring and renewal process",
                },
            ]
        )

        return recommendations

    def run_comprehensive_tls_audit(self) -> Dict[str, Any]:
        """Run comprehensive TLS configuration security audit"""
        print("🔐 STARTING COMPREHENSIVE TLS/SSL SECURITY AUDIT")
        print("=" * 60)

        results = {}

        # Test 1: Scan TLS configuration files
        print("1️⃣ Scanning TLS configuration files...")
        config_files = self.scan_tls_configurations()
        results["config_files_found"] = len(config_files)
        results["config_files"] = [
            str(f.relative_to(self.base_path)) for f in config_files[:10]
        ]  # Limit to first 10

        # Test 2: Analyze certificates
        print("2️⃣ Analyzing SSL certificates...")
        certificates = []
        for config_file in config_files:
            if config_file.suffix in [".pem", ".crt", ".cer"]:
                cert_analysis = self.analyze_ssl_certificate(config_file)
                certificates.append(cert_analysis)

        results["certificates"] = certificates
        results["certificates_with_issues"] = len(
            [c for c in certificates if c.get("risk_level") in ["HIGH", "MEDIUM"]]
        )

        # Test 3: Analyze application TLS configuration
        print("3️⃣ Analyzing application TLS configuration...")
        results["application_tls"] = self.analyze_application_tls_config()

        # Test 4: Test server TLS configuration
        print("4️⃣ Testing server TLS configuration...")
        server_tests = []
        test_endpoints = [
            ("localhost", 8000),
            ("localhost", 5174),
            ("localhost", 443),
            ("localhost", 8443),
        ]

        for hostname, port in test_endpoints:
            try:
                test_result = self.test_server_tls_configuration(hostname, port)
                server_tests.append(test_result)
            except Exception as e:
                server_tests.append(
                    {
                        "hostname": hostname,
                        "port": port,
                        "error": str(e),
                        "tls_supported": False,
                        "risk_level": "HIGH",
                    }
                )

        results["server_tests"] = server_tests
        results["servers_with_tls_issues"] = len(
            [t for t in server_tests if not t.get("tls_supported", True)]
        )

        # Test 5: Check Docker TLS configuration
        print("5️⃣ Checking Docker TLS configuration...")
        results["docker_tls"] = self.check_docker_tls_configuration()

        # Test 6: Check nginx SSL configuration
        print("6️⃣ Checking nginx SSL configuration...")
        results["nginx_ssl"] = self.check_nginx_ssl_configuration()

        # Generate recommendations
        recommendations = self.generate_tls_recommendations(results)
        results["recommendations"] = recommendations

        # Generate summary
        results["summary"] = {
            "total_config_files": len(config_files),
            "certificates_analyzed": len(certificates),
            "certificates_with_issues": len(
                [c for c in certificates if c.get("risk_level") in ["HIGH", "MEDIUM"]]
            ),
            "servers_tested": len(server_tests),
            "servers_with_tls_issues": len(
                [t for t in server_tests if not t.get("tls_supported", True)]
            ),
            "recommendations_count": len(recommendations),
            "overall_tls_security_score": self.calculate_tls_security_score(results),
        }

        return results

    def calculate_tls_security_score(self, results: Dict) -> int:
        """Calculate overall TLS security score"""
        score = 100

        # Deduct points for certificates with issues
        cert_issues = len(
            [
                c
                for c in results.get("certificates", [])
                if c.get("risk_level") in ["HIGH", "MEDIUM"]
            ]
        )
        score -= min(cert_issues * 15, 30)

        # Deduct points for application TLS issues
        app_tls = results.get("application_tls", {})
        if app_tls.get("risk_level") == "CRITICAL":
            score -= 40
        elif app_tls.get("risk_level") == "HIGH":
            score -= 25
        elif app_tls.get("risk_level") == "MEDIUM":
            score -= 15

        # Deduct points for server TLS issues
        server_issues = len(
            [
                t
                for t in results.get("server_tests", [])
                if not t.get("tls_supported", True)
            ]
        )
        score -= min(server_issues * 20, 40)

        # Deduct points for Docker TLS issues
        docker_tls = results.get("docker_tls", {})
        if docker_tls.get("risk_level") == "HIGH":
            score -= 15
        elif docker_tls.get("risk_level") == "MEDIUM":
            score -= 10

        # Deduct points for nginx SSL issues
        nginx_ssl = results.get("nginx_ssl", {})
        if nginx_ssl.get("risk_level") == "HIGH":
            score -= 15
        elif nginx_ssl.get("risk_level") == "MEDIUM":
            score -= 10

        return max(0, min(100, score))


def main():
    """Main execution function"""
    auditor = TLSConfigurationAuditor()

    try:
        results = auditor.run_comprehensive_tls_audit()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 TLS/SSL CONFIGURATION SECURITY AUDIT REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 TLS Configuration Files: {summary['total_config_files']}")
        print(f"🔒 Certificates Analyzed: {summary['certificates_analyzed']}")
        print(f"⚠️ Certificates with Issues: {summary['certificates_with_issues']}")
        print(f"🌐 Servers Tested: {summary['servers_tested']}")
        print(f"❌ Servers with TLS Issues: {summary['servers_with_tls_issues']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(
            f"🎯 Overall TLS Security Score: {summary['overall_tls_security_score']}/100"
        )

        # Show certificate issues
        cert_issues = [
            c
            for c in results.get("certificates", [])
            if c.get("risk_level") in ["HIGH", "MEDIUM"]
        ]
        if cert_issues:
            print(f"\n🔒 CERTIFICATE SECURITY ISSUES:")
            for cert in cert_issues:
                print(
                    f"  ❌ {cert['file']}: {', '.join(cert.get('security_issues', []))}"
                )

        # Show server TLS issues
        server_issues = [
            t
            for t in results.get("server_tests", [])
            if not t.get("tls_supported", True)
        ]
        if server_issues:
            print(f"\n🌐 SERVER TLS ISSUES:")
            for test in server_issues:
                print(
                    f"  ❌ {test['hostname']}:{test['port']}: {', '.join(test.get('security_issues', []))}"
                )

        # Show recommendations
        print(f"\n💡 TLS SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open(
            "/Users/sheriftito/Downloads/psychsync/tls_configuration_security_report.json",
            "w",
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: tls_configuration_security_report.json")

    except Exception as e:
        print(f"❌ Error running TLS audit: {e}")


if __name__ == "__main__":
    main()
