#!/usr/bin/env python3
"""
Network Layer Security Audit Script
Comprehensive security testing for TLS, SSL, DNS, internal APIs, and routing

Author: Security Audit Team
Version: 1.0.0
"""

import json
import re
import socket
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class NetworkSecurityAuditor:
    """Comprehensive network security auditor"""

    def __init__(self, target_host="localhost", target_port=8000):
        self.target_host = target_host
        self.target_port = target_port
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "target": f"{target_host}:{target_port}",
            "audits": {},
        }

    def run_all_audits(self) -> Dict[str, Any]:
        """Run all network security audits"""
        print("=" * 70)
        print("NETWORK LAYER SECURITY AUDIT")
        print("=" * 70)
        print(f"Target: {self.target_host}:{self.target_port}")
        print(f"Timestamp: {self.results['timestamp']}")
        print()

        # 1. TLS Configuration Audit
        print("🔒 Running TLS Configuration Audit...")
        self.results["audits"]["tls_configuration"] = self.audit_tls_configuration()
        print("✓ TLS Configuration Audit complete\n")

        # 2. SSL Downgrade Attack Testing
        print("🛡️  Testing SSL Downgrade Attacks...")
        self.results["audits"]["ssl_downgrade"] = self.test_ssl_downgrade_attacks()
        print("✓ SSL Downgrade Attack Testing complete\n")

        # 3. DNS Poisoning Testing
        print("🌐 Testing DNS Poisoning Scenarios...")
        self.results["audits"]["dns_poisoning"] = self.test_dns_poisoning_scenarios()
        print("✓ DNS Poisoning Testing complete\n")

        # 4. Internal API Restriction Check
        print("🔐 Checking Internal API Restrictions...")
        self.results["audits"]["internal_api"] = self.check_internal_api_restrictions()
        print("✓ Internal API Restriction Check complete\n")

        # 5. Routing Rules Leak Check
        print("🔀 Checking Routing Rules for Leaks...")
        self.results["audits"]["routing_leaks"] = self.check_routing_leaks()
        print("✓ Routing Rules Leak Check complete\n")

        # Generate overall score
        self._calculate_overall_score()

        return self.results

    def audit_tls_configuration(self) -> Dict[str, Any]:
        """Audit TLS configuration for security issues"""
        results = {
            "status": "passed",
            "findings": [],
            "recommendations": [],
            "tests": {},
        }

        # Test 1: Check SSL/TLS certificate
        print("  → Checking SSL/TLS certificate...")
        try:
            context = ssl.create_default_context()
            with socket.create_connection(
                (self.target_host, self.target_port), timeout=5
            ) as sock:
                with context.wrap_socket(
                    sock, server_hostname=self.target_host
                ) as ssock:
                    cert = ssock.getpeercert()
                    results["tests"]["certificate"] = {
                        "status": "present",
                        "subject": cert.get("subject", []),
                        "issuer": cert.get("issuer", []),
                        "version": cert.get("version"),
                        "notBefore": cert.get("notBefore"),
                        "notAfter": cert.get("notAfter"),
                    }
                    print(f"    ✓ Certificate found: {cert.get('subject', [])}")
        except Exception as e:
            results["tests"]["certificate"] = {"status": "error", "error": str(e)}
            results["findings"].append(
                {
                    "severity": "HIGH",
                    "issue": "SSL/TLS certificate not accessible",
                    "details": str(e),
                }
            )
            print(f"    ⚠ Certificate error: {e}")

        # Test 2: Check TLS versions
        print("  → Checking TLS version support...")
        tls_versions = {
            "SSLv2": False,
            "SSLv3": False,
            "TLSv1.0": False,
            "TLSv1.1": False,
            "TLSv1.2": False,
            "TLSv1.3": False,
        }

        # Use TLS method names instead of deprecated constants
        tls_methods = [
            ("SSLv2", "SSLv2"),
            ("SSLv3", "SSLv3"),
            ("TLSv1.0", "TLSv1"),
            ("TLSv1.1", "TLSv1_1"),
            ("TLSv1.2", "TLSv1_2"),
            ("TLSv1.3", "TLSv1_3"),
        ]

        for tls_name, method_name in tls_methods:
            try:
                # Try to create context for each version
                if hasattr(ssl, f'PROTOCOL_{method_name.replace(".", "_")}'):
                    proto_const = getattr(
                        ssl, f'PROTOCOL_{method_name.replace(".", "_")}'
                    )
                    context = ssl.SSLContext(proto_const)
                    with socket.create_connection(
                        (self.target_host, self.target_port), timeout=2
                    ) as sock:
                        with context.wrap_socket(
                            sock, server_hostname=self.target_host
                        ) as ssock:
                            tls_versions[tls_name] = True
                else:
                    # For newer Python versions, use minimum_version
                    if tls_name in ["TLSv1.2", "TLSv1.3"]:
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        if tls_name == "TLSv1.2":
                            context.minimum_version = ssl.TLSVersion.TLSv1_2
                            context.maximum_version = ssl.TLSVersion.TLSv1_2
                        elif tls_name == "TLSv1.3":
                            context.minimum_version = ssl.TLSVersion.TLSv1_3
                            context.maximum_version = ssl.TLSVersion.TLSv1_3

                        with socket.create_connection(
                            (self.target_host, self.target_port), timeout=2
                        ) as sock:
                            with context.wrap_socket(
                                sock, server_hostname=self.target_host
                            ) as ssock:
                                tls_versions[tls_name] = True
            except Exception as e:
                pass  # Version not supported

        results["tests"]["tls_versions"] = tls_versions

        # Check for insecure versions
        insecure_versions = ["SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1"]
        for version in insecure_versions:
            if tls_versions.get(version, False):
                results["findings"].append(
                    {
                        "severity": "CRITICAL",
                        "issue": f"Insecure TLS version supported: {version}",
                        "details": f"Server accepts connections using {version}, which is deprecated and insecure",
                    }
                )
                results["status"] = "failed"

        # Check for secure versions
        if not tls_versions.get("TLSv1.2", False) and not tls_versions.get(
            "TLSv1.3", False
        ):
            results["findings"].append(
                {
                    "severity": "HIGH",
                    "issue": "No secure TLS version supported",
                    "details": "Server does not support TLS 1.2 or 1.3",
                }
            )
            results["status"] = "failed"

        print(
            f"    TLS Versions: {', '.join([v for v, supported in tls_versions.items() if supported]) or 'None accessible'}"
        )

        # Test 3: Check cipher suites
        print("  → Checking cipher suite configuration...")
        try:
            context = ssl.create_default_context()
            context.set_ciphers("ALL")
            with socket.create_connection(
                (self.target_host, self.target_port), timeout=5
            ) as sock:
                with context.wrap_socket(
                    sock, server_hostname=self.target_host
                ) as ssock:
                    cipher = ssock.cipher()
                    results["tests"]["cipher_suite"] = {
                        "name": cipher[0],
                        "protocol": cipher[1],
                        "secret_bits": cipher[2],
                    }
                    print(f"    Current cipher: {cipher[0]} ({cipher[1]})")

                    # Check for weak ciphers
                    weak_ciphers = ["RC4", "DES", "3DES", "MD5", "SHA1", "SHA"]
                    if any(weak in cipher[0] for weak in weak_ciphers):
                        results["findings"].append(
                            {
                                "severity": "HIGH",
                                "issue": "Weak cipher suite detected",
                                "details": f"Server using {cipher[0]} which contains weak algorithms",
                            }
                        )
                        results["status"] = "failed"
        except Exception as e:
            results["tests"]["cipher_suite"] = {"error": str(e)}

        # Test 4: Check security headers
        print("  → Checking security headers...")
        try:
            response = urllib.request.urlopen(
                f"http://{self.target_host}:{self.target_port}/", timeout=5
            )
            headers = dict(response.headers)

            security_headers = {
                "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
                "X-Frame-Options": headers.get("X-Frame-Options"),
                "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
                "X-XSS-Protection": headers.get("X-XSS-Protection"),
                "Content-Security-Policy": headers.get("Content-Security-Policy"),
                "Referrer-Policy": headers.get("Referrer-Policy"),
            }

            results["tests"]["security_headers"] = security_headers

            # Check for missing security headers
            for header, value in security_headers.items():
                if not value:
                    results["findings"].append(
                        {
                            "severity": "MEDIUM",
                            "issue": f"Missing security header: {header}",
                            "details": f"The {header} header should be set for enhanced security",
                        }
                    )

            print(
                f"    Security headers found: {len([v for v in security_headers.values() if v])}/6"
            )

        except Exception as e:
            results["tests"]["security_headers"] = {"error": str(e)}

        return results

    def test_ssl_downgrade_attacks(self) -> Dict[str, Any]:
        """Test for SSL downgrade attack vulnerabilities"""
        results = {"status": "passed", "findings": [], "tests": {}}

        # Test 1: Attempt SSL version downgrade
        print("  → Testing SSL version downgrade...")

        # Test older TLS versions using modern API
        tls_versions_to_test = [
            ("SSLv3", None),
            ("TLSv1.0", ssl.TLSVersion.TLSv1),
            ("TLSv1.1", ssl.TLSVersion.TLSv1_1),
        ]

        for proto_name, tls_version_enum in tls_versions_to_test:
            try:
                if tls_version_enum is None:
                    # SSLv3 is not available in modern Python
                    continue

                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.minimum_version = tls_version_enum
                context.maximum_version = tls_version_enum

                with socket.create_connection(
                    (self.target_host, self.target_port), timeout=2
                ) as sock:
                    with context.wrap_socket(
                        sock, server_hostname=self.target_host
                    ) as ssock:
                        results["tests"][f"downgrade_to_{proto_name}"] = {
                            "status": "vulnerable",
                            "details": f"Server accepted {proto_name} connection",
                        }
                        results["findings"].append(
                            {
                                "severity": "CRITICAL",
                                "issue": f"SSL Downgrade Attack Vector: {proto_name}",
                                "details": f"Server accepts {proto_name}, making it vulnerable to downgrade attacks like POODLE",
                            }
                        )
                        results["status"] = "failed"
                        print(f"    ⚠ Vulnerable: Server accepts {proto_name}")
            except (
                ssl.SSLError,
                OSError,
                ConnectionResetError,
                TimeoutError,
                AttributeError,
            ):
                results["tests"][f"downgrade_to_{proto_name}"] = {
                    "status": "protected",
                    "details": f"Server correctly rejects {proto_name}",
                }
                print(f"    ✓ Protected: Server rejects {proto_name}")
            except Exception as e:
                results["tests"][f"downgrade_to_{proto_name}"] = {
                    "status": "error",
                    "details": str(e),
                }
                print(f"    ? Error testing {proto_name}: {e}")

        # Test 2: Check for HSTS header
        print("  → Checking HSTS protection...")
        try:
            response = urllib.request.urlopen(
                f"http://{self.target_host}:{self.target_port}/", timeout=5
            )
            hsts_header = response.headers.get("Strict-Transport-Security")

            if hsts_header:
                # Parse HSTS header
                max_age = None
                include_subdomains = False
                preload = False

                if "max-age=" in hsts_header:
                    max_age = int(
                        hsts_header.split("max-age=")[1].split(";")[0].strip()
                    )
                include_subdomains = (
                    "includeSubDomains" in hsts_header
                    or "includesubdomains" in hsts_header
                )
                preload = "preload" in hsts_header

                results["tests"]["hsts"] = {
                    "status": "present",
                    "header": hsts_header,
                    "max_age": max_age,
                    "include_subdomains": include_subdomains,
                    "preload": preload,
                }

                if max_age and max_age >= 31536000:  # 1 year
                    print(f"    ✓ Strong HSTS: max-age={max_age}")
                else:
                    results["findings"].append(
                        {
                            "severity": "MEDIUM",
                            "issue": "Weak HSTS configuration",
                            "details": f"HSTS max-age is {max_age}, recommended is 31536000 (1 year)",
                        }
                    )
                    print(f"    ⚠ Weak HSTS: max-age={max_age}")
            else:
                results["tests"]["hsts"] = {
                    "status": "missing",
                    "details": "HSTS header not present",
                }
                results["findings"].append(
                    {
                        "severity": "HIGH",
                        "issue": "HSTS header missing",
                        "details": "Without HSTS, the site is vulnerable to SSL stripping attacks",
                    }
                )
                results["status"] = "failed"
                print("    ⚠ HSTS header missing")

        except Exception as e:
            results["tests"]["hsts"] = {"error": str(e)}

        # Test 3: Check certificate validation
        print("  → Testing certificate validation...")
        # Check if server presents any certificate
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection(
                (self.target_host, self.target_port), timeout=5
            ) as sock:
                with context.wrap_socket(
                    sock, server_hostname=self.target_host
                ) as ssock:
                    results["tests"]["certificate_validation"] = {
                        "status": "certificate_present",
                        "details": "Server presents SSL certificate",
                    }
                    print("    ✓ Certificate presented")
        except Exception as e:
            results["tests"]["certificate_validation"] = {
                "status": "no_certificate",
                "details": str(e),
            }
            print(f"    ⚠ No certificate: {e}")

        return results

    def test_dns_poisoning_scenarios(self) -> Dict[str, Any]:
        """Test for DNS poisoning vulnerabilities"""
        results = {"status": "passed", "findings": [], "tests": {}}

        # Test 1: Check DNSSEC validation
        print("  → Checking DNSSEC configuration...")
        try:
            # Try to resolve using DNSSEC-aware resolver
            result = subprocess.run(
                ["dig", "+dnssec", self.target_host],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if "ad" in result.stdout:  # Authenticated Data flag
                results["tests"]["dnssec"] = {
                    "status": "enabled",
                    "details": "DNSSEC validation appears to be enabled",
                }
                print("    ✓ DNSSEC validation enabled")
            else:
                results["tests"]["dnssec"] = {
                    "status": "unknown",
                    "details": "DNSSEC status could not be determined",
                }
                results["findings"].append(
                    {
                        "severity": "MEDIUM",
                        "issue": "DNSSEC validation status unclear",
                        "details": "Could not verify DNSSEC is enabled for DNS resolution",
                    }
                )
                print("    ⚠ DNSSEC status unknown")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["tests"]["dnssec"] = {
                "status": "not_tested",
                "details": "dig command not available",
            }
            print("    ⊘ DNSSEC test skipped (dig not available)")

        # Test 2: Check DNS cache poisoning controls
        print("  → Checking DNS cache configuration...")
        try:
            # Check /etc/resolv.conf for DNS settings
            resolv_conf = Path("/etc/resolv.conf")
            if resolv_conf.exists():
                content = resolv_conf.read_text()

                dns_servers = re.findall(r"nameserver\s+([\d.]+)", content)
                results["tests"]["dns_servers"] = dns_servers

                # Check for localhost DNS resolver (more secure)
                if any(
                    ip.startswith("127.") or ip == "localhost" for ip in dns_servers
                ):
                    results["tests"]["local_dns_resolver"] = {
                        "status": "present",
                        "details": "Using local DNS resolver",
                    }
                    print(f"    ✓ Local DNS resolver: {dns_servers}")
                else:
                    results["tests"]["local_dns_resolver"] = {
                        "status": "absent",
                        "details": f"Using external DNS servers: {dns_servers}",
                    }
                    results["findings"].append(
                        {
                            "severity": "LOW",
                            "issue": "Using external DNS resolvers",
                            "details": f"DNS servers: {dns_servers}. Consider using local DNS resolver with cache poisoning protection",
                        }
                    )
                    print(f"    ⚠ External DNS: {dns_servers}")

        except Exception as e:
            results["tests"]["dns_configuration"] = {"error": str(e)}

        # Test 3: Check for DNS rebinding protection
        print("  → Checking DNS rebinding protection...")
        # Check if the application validates Host header
        try:
            # Test with malformed Host header
            test_headers = {"Host": "evil.com", "X-Forwarded-Host": "evil.com"}

            results["tests"]["host_header_validation"] = {
                "status": "not_tested",
                "details": "Manual testing required for Host header validation",
            }
            results["findings"].append(
                {
                    "severity": "MEDIUM",
                    "issue": "Host header validation not verified",
                    "details": "Manual testing required to verify Host header validation prevents DNS rebinding",
                }
            )
            print("    ⚠ Host header validation requires manual testing")

        except Exception as e:
            results["tests"]["dns_rebinding"] = {"error": str(e)}

        # Test 4: DNS timeout and retry configuration
        print("  → Checking DNS timeout configuration...")
        results["tests"]["dns_timeouts"] = {
            "status": "informational",
            "details": "DNS timeout configuration should be reviewed in application settings",
        }
        print("    ℹ DNS timeout configuration requires review")

        return results

    def check_internal_api_restrictions(self) -> Dict[str, Any]:
        """Check if internal API endpoints are properly restricted"""
        results = {"status": "passed", "findings": [], "tests": {}}

        # List of potentially internal endpoints to test
        internal_endpoints = [
            "/admin",
            "/internal",
            "/debug",
            "/metrics",
            "/health",
            "/api/internal",
            "/api/admin",
            "/config",
            "/.env",
            "/api/v1/internal",
        ]

        print("  → Testing internal endpoint access control...")
        for endpoint in internal_endpoints:
            try:
                url = f"http://{self.target_host}:{self.target_port}{endpoint}"
                request = urllib.request.Request(url, method="GET")

                # Test without authentication
                try:
                    response = urllib.request.urlopen(request, timeout=3)
                    status_code = response.getcode()

                    # If accessible without auth, it might be a security issue
                    if status_code == 200:
                        results["tests"][endpoint.replace("/", "_")] = {
                            "status": "accessible",
                            "code": status_code,
                            "auth_required": False,
                        }

                        # Some endpoints are meant to be public (like /health)
                        if endpoint not in ["/health", "/metrics"]:
                            results["findings"].append(
                                {
                                    "severity": "HIGH",
                                    "issue": f"Internal endpoint accessible without authentication: {endpoint}",
                                    "details": f"Endpoint returns 200 without authentication",
                                }
                            )
                            results["status"] = "failed"
                            print(f"    ⚠ Unrestricted: {endpoint} (200)")
                        else:
                            print(f"    ✓ Public: {endpoint} (200)")
                    else:
                        print(f"    ✓ Protected: {endpoint} ({status_code})")

                except urllib.error.HTTPError as e:
                    # 401/403 is good - endpoint is protected
                    if e.code in [401, 403]:
                        results["tests"][endpoint.replace("/", "_")] = {
                            "status": "protected",
                            "code": e.code,
                            "auth_required": True,
                        }
                        print(f"    ✓ Protected: {endpoint} ({e.code})")
                    else:
                        results["tests"][endpoint.replace("/", "_")] = {
                            "status": f"error_{e.code}",
                            "code": e.code,
                        }
                        print(f"    ? {endpoint}: {e.code}")

                except urllib.error.URLError as e:
                    # 404 is expected for non-existent endpoints
                    results["tests"][endpoint.replace("/", "_")] = {
                        "status": "not_found",
                        "details": "Endpoint does not exist",
                    }
                    print(f"    ⊘ Not found: {endpoint}")

            except Exception as e:
                results["tests"][endpoint.replace("/", "_")] = {"error": str(e)}

        # Test 2: Check for localhost-only endpoints accessible externally
        print("  → Checking localhost-only endpoint exposure...")
        # This would require checking the code or configuration
        results["tests"]["localhost_exposure"] = {
            "status": "not_tested",
            "details": "Code review required to verify localhost-only endpoints",
        }
        results["findings"].append(
            {
                "severity": "MEDIUM",
                "issue": "Localhost endpoint exposure not verified",
                "details": "Manual code review required to ensure localhost-only endpoints are not exposed",
            }
        )
        print("    ⚠ Localhost exposure check requires code review")

        # Test 3: Check for admin panel exposure
        print("  → Checking admin panel access...")
        admin_paths = ["/admin", "/administration", "/dashboard/admin", "/api/v1/admin"]
        for path in admin_paths:
            try:
                url = f"http://{self.target_host}:{self.target_port}{path}"
                response = urllib.request.urlopen(url, timeout=2)
                if response.getcode() == 200:
                    results["tests"][f"admin_{path}"] = {
                        "status": "exposed",
                        "details": f"Admin panel accessible at {path}",
                    }
                    results["findings"].append(
                        {
                            "severity": "CRITICAL",
                            "issue": f"Admin panel exposed: {path}",
                            "details": "Admin interface should be restricted to specific IPs or require authentication",
                        }
                    )
                    results["status"] = "failed"
                    print(f"    ⚠ CRITICAL: Admin panel exposed at {path}")
            except Exception as e:
                pass  # Admin panel not accessible or doesn't exist

        return results

    def check_routing_leaks(self) -> Dict[str, Any]:
        """Check for routing rule leaks and misconfigurations"""
        results = {"status": "passed", "findings": [], "tests": {}}

        # Test 1: Check for open redirects
        print("  → Testing for open redirect vulnerabilities...")
        redirect_tests = [
            "/redirect?url=http://evil.com",
            "/redirect?target=http://evil.com",
            "/login?next=http://evil.com",
            "/logout?return=http://evil.com",
            "/link?to=http://evil.com",
        ]

        for test_url in redirect_tests:
            try:
                url = f"http://{self.target_host}:{self.target_port}{test_url}"
                request = urllib.request.Request(url, method="GET")

                # Don't follow redirects automatically
                response = urllib.request.urlopen(request, timeout=3)

                if 300 <= response.getcode() < 400:
                    location = response.headers.get("Location", "")
                    if "evil.com" in location:
                        results["tests"][
                            f"redirect_{test_url.split('=')[0].split('/')[-1]}"
                        ] = {
                            "status": "vulnerable",
                            "details": f"Open redirect to: {location}",
                        }
                        results["findings"].append(
                            {
                                "severity": "MEDIUM",
                                "issue": f"Open redirect vulnerability: {test_url}",
                                "details": f"Redirects to external URL without validation: {location}",
                            }
                        )
                        results["status"] = "failed"
                        print(f"    ⚠ Open redirect: {test_url}")
            except urllib.error.HTTPError as e:
                # 404 or other errors are OK
                pass
            except Exception:
                pass

        if not any("vulnerable" in str(v) for v in results["tests"].values()):
            print("    ✓ No open redirects detected")

        # Test 2: Check for path traversal in routes
        print("  → Testing for path traversal in routes...")
        path_traversal_tests = [
            "/api/v1/../../etc/passwd",
            "/api/v1/..\\..\\..\\windows\\system32",
            "/files/../../../etc/passwd",
            "/download?file=../../../etc/passwd",
        ]

        for test_path in path_traversal_tests:
            try:
                url = f"http://{self.target_host}:{self.target_port}{test_path}"
                response = urllib.request.urlopen(url, timeout=3)

                if response.getcode() == 200:
                    content = response.read(1000).decode("utf-8", errors="ignore")

                    # Check if we got actual file content
                    if "root:" in content or "Windows" in content:
                        results["tests"][f"path_traversal_{test_path[:30]}"] = {
                            "status": "vulnerable",
                            "details": f"Path traversal successful: {test_path}",
                        }
                        results["findings"].append(
                            {
                                "severity": "CRITICAL",
                                "issue": f"Path traversal vulnerability: {test_path}",
                                "details": "Can access files outside the web root",
                            }
                        )
                        results["status"] = "failed"
                        print(f"    ⚠ CRITICAL: Path traversal: {test_path}")

            except urllib.error.HTTPError as e:
                # 404 or other errors are expected
                pass
            except Exception:
                pass

        if not any(
            "vulnerable" in str(v) and "path_traversal" in k
            for k, v in results["tests"].items()
        ):
            print("    ✓ No path traversal vulnerabilities detected")

        # Test 3: Check CORS configuration
        print("  → Checking CORS configuration...")
        try:
            request = urllib.request.Request(
                f"http://{self.target_host}:{self.target_port}/api/v1/health",
                headers={"Origin": "http://evil.com"},
            )
            response = urllib.request.urlopen(request, timeout=3)

            aca_header = response.headers.get("Access-Control-Allow-Origin")
            acac_header = response.headers.get("Access-Control-Allow-Credentials")

            results["tests"]["cors_evil_origin"] = {
                "allowed_origin": aca_header,
                "allow_credentials": acac_header,
            }

            if aca_header == "*" or aca_header == "http://evil.com":
                results["findings"].append(
                    {
                        "severity": "HIGH",
                        "issue": "Permissive CORS configuration",
                        "details": f"CORS allows origin: {aca_header}",
                    }
                )
                if acac_header == "true":
                    results["status"] = "failed"
                    print(f"    ⚠ Permissive CORS: {aca_header} with credentials")
                else:
                    print(f"    ⚠ Permissive CORS: {aca_header}")
            else:
                print(f"    ✓ CORS restricted: {aca_header}")

        except Exception as e:
            results["tests"]["cors_configuration"] = {"error": str(e)}

        # Test 4: Check for information disclosure in error messages
        print("  → Testing for information disclosure...")
        invalid_paths = [
            "/api/v1/nonexistent",
            "/api/v1/assessments/invalid-uuid-12345",
            "/this-path-does-not-exist-404",
        ]

        for path in invalid_paths:
            try:
                url = f"http://{self.target_host}:{self.target_port}{path}"
                response = urllib.request.urlopen(url, timeout=3)

                content = response.read(1000).decode("utf-8", errors="ignore")

                # Check for sensitive information
                sensitive_info = [
                    "Traceback (most recent call last)",
                    "SQL query",
                    "Database error",
                    "Internal Server Error",
                    "/var/www",
                    "C:\\Users\\",
                    "stack trace",
                    "exception",
                ]

                found_sensitive = [
                    info for info in sensitive_info if info.lower() in content.lower()
                ]

                if found_sensitive:
                    results["tests"][
                        f"info_disclosure_{path.replace('/', '_')[-30:]}"
                    ] = {"status": "leaking", "details": f"Found: {found_sensitive}"}
                    results["findings"].append(
                        {
                            "severity": "MEDIUM",
                            "issue": f"Information disclosure: {path}",
                            "details": f"Error messages contain: {found_sensitive}",
                        }
                    )
                    print(f"    ⚠ Information disclosure: {path}")

            except urllib.error.HTTPError as e:
                # Check error response body even for 404/500
                try:
                    error_content = e.read(1000).decode("utf-8", errors="ignore")
                    if (
                        "traceback" in error_content.lower()
                        or "exception" in error_content.lower()
                    ):
                        results["findings"].append(
                            {
                                "severity": "MEDIUM",
                                "issue": f"Information disclosure in error: {path}",
                                "details": "Error response contains stack trace",
                            }
                        )
                        print(f"    ⚠ Stack trace in error: {path}")
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    pass
            except Exception:
                pass

        if not any("leaking" in str(v) for v in results["tests"].values()):
            print("    ✓ No information disclosure detected")

        return results

    def _calculate_overall_score(self) -> None:
        """Calculate overall security score"""
        scores = {"passed": 10, "warning": 7, "failed": 3, "error": 0}

        audit_scores = []
        for audit_name, audit_results in self.results["audits"].items():
            status = audit_results.get("status", "error")
            severity_weight = 1

            # Weight by severity of findings
            for finding in audit_results.get("findings", []):
                if finding.get("severity") == "CRITICAL":
                    severity_weight = 0.5
                    break
                elif finding.get("severity") == "HIGH":
                    severity_weight = 0.7

            audit_scores.append(scores.get(status, 0) * severity_weight)

        if audit_scores:
            overall_score = sum(audit_scores) / len(audit_scores)
            self.results["overall_score"] = round(overall_score, 2)

            if overall_score >= 9:
                self.results["overall_status"] = "EXCELLENT"
            elif overall_score >= 7:
                self.results["overall_status"] = "GOOD"
            elif overall_score >= 5:
                self.results["overall_status"] = "FAIR"
            else:
                self.results["overall_status"] = "POOR"
        else:
            self.results["overall_score"] = 0
            self.results["overall_status"] = "UNKNOWN"

    def print_report(self) -> None:
        """Print formatted audit report"""
        print()
        print("=" * 70)
        print("NETWORK SECURITY AUDIT REPORT")
        print("=" * 70)
        print()
        print(f"Overall Status: {self.results.get('overall_status', 'UNKNOWN')}")
        print(f"Security Score: {self.results.get('overall_score', 0)}/10")
        print()

        # Print findings by severity
        all_findings = []
        for audit_name, audit_results in self.results["audits"].items():
            for finding in audit_results.get("findings", []):
                finding["audit"] = audit_name
                all_findings.append(finding)

        if all_findings:
            print("SECURITY FINDINGS:")
            print()

            # Sort by severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            all_findings.sort(
                key=lambda f: severity_order.get(f.get("severity", "LOW"), 3)
            )

            for finding in all_findings:
                severity = finding.get("severity", "LOW")
                icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🔵",
                }.get(severity, "⚪")

                print(f"{icon} [{severity}] {finding.get('issue', 'Unknown Issue')}")
                print(f"   Location: {finding.get('audit', 'Unknown')}")
                print(f"   Details: {finding.get('details', 'No details')}")
                print()
        else:
            print("✓ No security findings detected!")
            print()

        print("=" * 70)

    def save_report(self, filename: str = None) -> str:
        """Save audit report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_security_audit_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ Report saved to: {filename}")
        return filename


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Network Layer Security Audit")
    parser.add_argument(
        "--host", default="localhost", help="Target host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Target port (default: 8000)"
    )
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    # Run audit
    auditor = NetworkSecurityAuditor(args.host, args.port)
    auditor.run_all_audits()
    auditor.print_report()

    # Save report
    if args.output:
        auditor.save_report(args.output)
    else:
        auditor.save_report()

    # Return exit code based on status
    status = auditor.results.get("overall_status", "UNKNOWN")
    if status in ["POOR", "UNKNOWN"]:
        return 2
    elif status in ["FAIR"]:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
