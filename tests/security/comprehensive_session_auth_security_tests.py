#!/usr/bin/env python3
"""
Comprehensive Session & Authentication Security Testing Suite
Tests for session management and authentication security vulnerabilities
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionAuthTestResult:
    """Session & authentication security test result"""

    category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str  # pass, fail, warning
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    location: Optional[str] = None


class SessionAuthSecurityTester:
    """Comprehensive session and authentication security scanner"""

    def __init__(
        self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")
    ):
        self.project_root = project_root
        self.results: List[SessionAuthTestResult] = []
        self.issue_count = 0
        self.pass_count = 0

    # =========================================================================
    # TEST 1: JWT TOKEN SECURITY
    # =========================================================================

    async def test_jwt_token_security(self) -> SessionAuthTestResult:
        """
        Test for JWT token security:
        - Secret strength and randomness
        - Algorithm configuration (HS256 vs RS256)
        - Token expiration settings
        - Refresh token implementation
        - Token blacklisting/revocation
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check JWT configuration
        config = self.project_root / "app/core/config.py"
        security = self.project_root / "app/core/security.py"
        auth_deps = self.project_root / "app/api/v1/deps.py"

        jwt_secret_found = False
        jwt_weak_secret = False

        for config_file in [config, security, auth_deps]:
            if not config_file.exists():
                continue

            content = config_file.read_text()

            # Check for JWT secret
            if (
                "SECRET_KEY" in content
                or "JWT_SECRET" in content
                or "secret" in content.lower()
            ):
                jwt_secret_found = True

                # Check for weak/obvious secrets
                weak_patterns = [
                    (r'secret\s*=\s*["\']secret["\']', "Default secret 'secret'"),
                    (r'secret\s*=\s*["\']test["\']', "Test secret"),
                    (r'secret\s*=\s*["\']password["\']', "Password as secret"),
                    (r'secret\s*=\s*["\']changeme["\']', "Placeholder secret"),
                    (r'secret\s*=\s*["\'][a-z]{1,10}["\']', "Short/lowercase secret"),
                ]

                for pattern, description in weak_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append(f"Weak JWT secret detected: {description}")
                        recommendations.append(
                            "Use cryptographically secure random secret (32+ bytes)"
                        )
                        jwt_weak_secret = True
                        severity = "critical"
                        status = "fail"
                        break

                # Check for environment variable loading
                if "os.getenv" in content or "os.environ" in content:
                    findings.append(
                        "JWT secret loaded from environment (good practice)"
                    )

                # Check secret length
                secret_match = re.search(
                    r'secret\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE
                )
                if secret_match and not jwt_weak_secret:
                    secret_value = secret_match.group(1)
                    if len(secret_value) < 32:
                        findings.append(
                            f"JWT secret too short: {len(secret_value)} characters (minimum 32 recommended)"
                        )
                        recommendations.append(
                            "Use longer JWT secret (32+ bytes/characters)"
                        )
                        severity = "high"
                        status = "fail"

            # Check JWT algorithm
            if "JWT_ALGORITHM" in content or "algorithm" in content.lower():
                algo_match = re.search(
                    r'JWT_ALGORITHM\s*=\s*["\']([^"\']+)["\']', content
                )
                if algo_match:
                    algorithm = algo_match.group(1)
                    if algorithm == "HS256":
                        findings.append(
                            f"JWT algorithm: {algorithm} (HMAC with SHA-256)"
                        )
                    elif algorithm == "RS256":
                        findings.append(
                            f"JWT algorithm: {algorithm} (RSA with SHA-256 - more secure)"
                        )
                        recommendations.append(
                            "RS256 provides better security but requires key management"
                        )
                    else:
                        findings.append(f"JWT algorithm: {algorithm}")
                        if algorithm in ["none", "None", "NONE"]:
                            findings.append(
                                "CRITICAL: 'none' algorithm allows token bypass!"
                            )
                            severity = "critical"
                            status = "fail"

        # Check token expiration
        if config.exists():
            content = config.read_text()

            if "ACCESS_TOKEN_EXPIRE" in content or "TOKEN_EXPIRATION" in content:
                expire_match = re.search(
                    r"(ACCESS_TOKEN_EXPIRE|TOKEN_EXPIRATION).*?(\d+)", content
                )
                if expire_match:
                    expire_value = int(expire_match.group(2))

                    # Determine if it's minutes or seconds
                    if "minute" in content.lower() or "MINUTE" in content:
                        expire_minutes = expire_value
                    else:
                        # Assume seconds
                        expire_minutes = (
                            expire_value // 60 if expire_value > 3600 else expire_value
                        )

                    if expire_minutes > 1440:  # More than 24 hours
                        findings.append(
                            f"Access token expiration too long: {expire_minutes} minutes"
                        )
                        recommendations.append(
                            "Reduce access token expiration to 15-30 minutes"
                        )
                        severity = "high"
                        status = "warning"
                    elif expire_minutes > 60:
                        findings.append(
                            f"Access token expiration: {expire_minutes} minutes"
                        )
                        status = "info"
                    else:
                        findings.append(
                            f"Access token expiration: {expire_minutes} minutes (good)"
                        )
            else:
                findings.append("No token expiration configuration found")
                recommendations.append(
                    "Set access token expiration (15-30 minutes recommended)"
                )
                status = "warning"

        # Check for refresh token implementation
        auth_service = self.project_root / "app/services/auth_service.py"
        if auth_service.exists():
            content = auth_service.read_text()

            if "refresh_token" in content.lower() or "refresh_token" in content.lower():
                findings.append("Refresh token implementation detected")

                # Check if refresh tokens are stored securely
                if "hash" in content.lower() or "bcrypt" in content.lower():
                    findings.append("Refresh tokens are hashed (good practice)")
            else:
                findings.append("No refresh token implementation found")
                recommendations.append(
                    "Implement refresh token mechanism for better security"
                )
                status = "warning"

        # Check for token blacklisting/revocation
        if auth_service.exists():
            content = auth_service.read_text()

            if (
                "blacklist" in content.lower()
                or "revoke" in content.lower()
                or "invalidate" in content.lower()
            ):
                findings.append("Token revocation mechanism detected")
            else:
                findings.append("No token blacklisting/revocation found")
                recommendations.append(
                    "Implement token blacklisting for logout scenarios"
                )
                status = "info"

        if not findings:
            findings.append("JWT configuration not found")
            status = "fail"

        return SessionAuthTestResult(
            category="Session & Auth Security",
            test_name="JWT Token Security",
            severity=severity,
            status=status,
            description="Tests for JWT token configuration and security",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 2: SESSION FIXATION VULNERABILITIES
    # =========================================================================

    async def test_session_fixation(self) -> SessionAuthTestResult:
        """
        Test for session fixation vulnerabilities:
        - Session regeneration after login
        - Session ID entropy/randomness
        - Session timeout configuration
        - Concurrent session limits
        - Session invalidation on password change
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check session management
        auth_service = self.project_root / "app/services/auth_service.py"
        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"

        session_files = [f for f in [auth_service, auth_endpoints] if f.exists()]

        if not session_files:
            findings.append("No authentication service found")
            return SessionAuthTestResult(
                category="Session & Auth Security",
                test_name="Session Fixation Vulnerabilities",
                severity="high",
                status="fail",
                description="Tests for session fixation vulnerabilities",
                evidence=findings,
                recommendations=["Implement proper session management"],
            )

        for session_file in session_files:
            content = session_file.read_text()

            # Check for session regeneration after login
            if "login" in content.lower():
                if "regenerate" in content.lower() or "new_session" in content.lower():
                    findings.append("Session regeneration after login detected")
                else:
                    findings.append("Sessions may not be regenerated after login")
                    recommendations.append(
                        "Implement session regeneration after authentication"
                    )
                    status = "warning"

            # Check for session timeout
            if (
                "expire" in content.lower()
                or "timeout" in content.lower()
                or "ttl" in content.lower()
            ):
                findings.append("Session expiration/timeout configured")
            else:
                findings.append("No session timeout configuration found")
                recommendations.append(
                    "Set session timeout (15-30 minutes for inactivity)"
                )
                status = "warning"

            # Check for concurrent session limits
            if "concurrent" in content.lower() or "max_sessions" in content.lower():
                findings.append("Concurrent session limit detected")
            else:
                findings.append("No concurrent session limits found")
                recommendations.append(
                    "Consider implementing concurrent session limits"
                )
                status = "info"

        # Check if using JWT (stateless) vs sessions
        if auth_service.exists():
            content = auth_service.read_text()

            if "jwt" in content.lower() or "token" in content.lower():
                findings.append("Using JWT tokens (stateless authentication)")
                findings.append("Session fixation less applicable with JWT (stateless)")

                # Check for proper token generation
                if "secrets.token_urlsafe" in content or "uuid" in content.lower():
                    findings.append(
                        "Token generation uses cryptographically secure random"
                    )
                else:
                    findings.append("Token generation may use weak randomness")
                    recommendations.append(
                        "Use secrets.token_urlsafe() for token generation"
                    )
                    status = "warning"

        return SessionAuthTestResult(
            category="Session & Auth Security",
            test_name="Session Fixation Vulnerabilities",
            severity=severity,
            status=status,
            description="Tests for session fixation vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 3: COOKIE SECURITY FLAGS
    # =========================================================================

    async def test_cookie_security(self) -> SessionAuthTestResult:
        """
        Test for cookie security:
        - HttpOnly flag
        - Secure flag (HTTPS only)
        - SameSite attribute
        - Cookie domain/path configuration
        - Cookie expiration
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        main_app = self.project_root / "app/main.py"
        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"

        cookie_config_found = False

        for config_file in [main_app, auth_endpoints]:
            if not config_file.exists():
                continue

            content = config_file.read_text()

            # Check for cookie configuration
            if "cookie" in content.lower() or "Cookie" in content:
                cookie_config_found = True

                # Check for HttpOnly
                if "httponly" in content.lower() or "HttpOnly" in content:
                    findings.append("HttpOnly cookie flag found (prevents XSS)")
                else:
                    findings.append("HttpOnly flag may not be set on cookies")
                    recommendations.append(
                        "Set HttpOnly flag on all authentication cookies"
                    )
                    severity = "high"
                    status = "fail"

                # Check for Secure flag
                if "secure" in content.lower() and "cookie" in content.lower():
                    findings.append("Secure cookie flag found (HTTPS only)")
                else:
                    findings.append("Secure flag may not be set on cookies")
                    recommendations.append(
                        "Set Secure flag on all authentication cookies (HTTPS only)"
                    )
                    status = "warning"

                # Check for SameSite
                if "samesite" in content.lower() or "SameSite" in content:
                    samesite_match = re.search(
                        r'SameSite\s*=\s*["\']?(\w+)["\']?', content
                    )
                    if samesite_match:
                        samesite_value = samesite_match.group(1)
                        findings.append(f"SameSite attribute: {samesite_value}")

                        if samesite_value.upper() == "NONE":
                            findings.append("SameSite=None requires Secure flag")
                            if "secure" not in content.lower():
                                recommendations.append(
                                    "Add Secure flag when using SameSite=None"
                                )
                                severity = "high"
                                status = "fail"
                else:
                    findings.append("SameSite attribute not found on cookies")
                    recommendations.append(
                        "Set SameSite=Lax or SameSite=Strict on cookies"
                    )
                    status = "warning"

                # Check for cookie domain/path
                if (
                    "cookie_domain" in content.lower()
                    or "cookie_path" in content.lower()
                ):
                    findings.append("Cookie domain/path configured")

        # Check if using JWT in Authorization header (more secure than cookies)
        if auth_endpoints.exists():
            content = auth_endpoints.read_text()

            if "Authorization" in content or "authorization" in content:
                findings.append(
                    "Using Authorization header for tokens (recommended over cookies)"
                )

        if not cookie_config_found:
            findings.append("No explicit cookie configuration found")
            findings.append("JWT tokens likely used (Authorization header)")
            status = "pass"

        return SessionAuthTestResult(
            category="Session & Auth Security",
            test_name="Cookie Security Flags",
            severity=severity,
            status=status,
            description="Tests for cookie security configuration",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 4: PASSWORD STRENGTH VALIDATION
    # =========================================================================

    async def test_password_strength(self) -> SessionAuthTestResult:
        """
        Test for password strength validation:
        - Minimum length requirements
        - Complexity requirements (uppercase, lowercase, numbers, symbols)
        - Password strength meter/checker
        - Common password detection
        - Password history/reuse prevention
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check schemas for password validation
        user_schema = self.project_root / "app/schemas/user.py"
        auth_schema = self.project_root / "app/schemas/auth.py"
        schemas_dir = self.project_root / "app/schemas"

        schema_files = []
        if user_schema.exists():
            schema_files.append(user_schema)
        if auth_schema.exists():
            schema_files.append(auth_schema)

        if not schema_files and schemas_dir.exists():
            schema_files = list(schemas_dir.glob("*.py"))

        password_validation_found = False

        for schema_file in schema_files:
            content = schema_file.read_text()

            # Look for password validation
            if "password" in content.lower():
                password_validation_found = True

                # Check for Field validators
                if "Field(" in content and "min_length" in content:
                    min_length_match = re.search(r"min_length\s*=\s*(\d+)", content)
                    if min_length_match:
                        min_length = int(min_length_match.group(1))

                        if min_length < 8:
                            findings.append(
                                f"Password minimum length too short: {min_length} characters"
                            )
                            recommendations.append(
                                "Set minimum password length to 8+ characters"
                            )
                            severity = "high"
                            status = "fail"
                        else:
                            findings.append(
                                f"Password minimum length: {min_length} characters (good)"
                            )

                # Check for regex validation
                if re.search(r"regex.*?password", content, re.IGNORECASE):
                    findings.append("Password complexity validation found (regex)")

                    # Check what's required
                    if re.search(r"[A-Z]", content):
                        findings.append("Requires uppercase letters")
                    if re.search(r"[a-z]", content):
                        findings.append("Requires lowercase letters")
                    if re.search(r"\d", content):
                        findings.append("Requires numbers")
                    if re.search(r"[!@#$%^&*]", content):
                        findings.append("Requires special characters")
                else:
                    findings.append("No password complexity requirements found")
                    recommendations.append(
                        "Add password complexity validation (uppercase, lowercase, numbers, symbols)"
                    )
                    status = "warning"

                # Check for strength validator
                if (
                    "strength" in content.lower()
                    or "validate_password" in content.lower()
                ):
                    findings.append("Password strength validation detected")

        # Check auth service for password policies
        auth_service = self.project_root / "app/services/auth_service.py"
        if auth_service.exists():
            content = auth_service.read_text()

            # Check for password hashing
            if "hash" in content.lower() or "bcrypt" in content.lower():
                findings.append("Password hashing implemented (bcrypt)")

                # Check work factor
                bcrypt_rounds = re.search(r"rounds\s*=\s*(\d+)", content)
                if bcrypt_rounds:
                    rounds = int(bcrypt_rounds.group(1))
                    if rounds >= 12:
                        findings.append(f"Bcrypt rounds: {rounds} (good)")
                    elif rounds >= 10:
                        findings.append(f"Bcrypt rounds: {rounds} (acceptable)")
                    else:
                        findings.append(
                            f"Bcrypt rounds: {rounds} (too low, recommend 12+)"
                        )
                        recommendations.append("Increase bcrypt work factor to 12+")
                        status = "warning"

            # Check for common password detection
            if (
                "common_password" in content.lower()
                or "haveibeenpwned" in content.lower()
            ):
                findings.append("Common password detection implemented")

        if not password_validation_found:
            findings.append("No password validation found")
            recommendations.append("Implement password strength validation")
            status = "fail"

        return SessionAuthTestResult(
            category="Session & Auth Security",
            test_name="Password Strength Validation",
            severity=severity,
            status=status,
            description="Tests for password strength validation",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 5: BRUTE FORCE PROTECTION
    # =========================================================================

    async def test_brute_force_protection(self) -> SessionAuthTestResult:
        """
        Test for brute force protection:
        - Account lockout after failed attempts
        - Progressive delays
        - CAPTCHA integration
        - IP-based blocking
        - Logging of failed attempts
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"
        auth_service = self.project_root / "app/services/auth_service.py"

        brute_force_protection = False

        for auth_file in [auth_endpoints, auth_service]:
            if not auth_file.exists():
                continue

            content = auth_file.read_text()

            # Check for account lockout
            if "lockout" in content.lower() or "account_lock" in content.lower():
                findings.append("Account lockout mechanism detected")
                brute_force_protection = True

            # Check for failed attempt tracking
            if "failed_attempt" in content.lower() or "failed_login" in content.lower():
                findings.append("Failed login attempt tracking detected")
                brute_force_protection = True

            # Check for rate limiting (already covered in API security)
            if "rate_limit" in content.lower() or "limiter" in content.lower():
                findings.append(
                    "Rate limiting on authentication endpoints (helps prevent brute force)"
                )
                brute_force_protection = True

            # Check for progressive delays
            if "delay" in content.lower() or "exponential_backoff" in content.lower():
                findings.append("Progressive delay mechanism detected")
                brute_force_protection = True

            # Check for CAPTCHA
            if "captcha" in content.lower():
                findings.append("CAPTCHA integration detected")
                brute_force_protection = True

            # Check for IP-based blocking
            if "ip_block" in content.lower() or "block_ip" in content.lower():
                findings.append("IP-based blocking detected")
                brute_force_protection = True

            # Check for logging of failed attempts
            if "log.*fail" in content.lower() or "audit.*fail" in content.lower():
                findings.append("Failed attempt logging detected")

        if not brute_force_protection:
            findings.append("No explicit brute force protection found")
            recommendations.append(
                "Implement account lockout after 5-10 failed attempts"
            )
            recommendations.append("Add progressive delays between attempts")
            recommendations.append("Log all failed authentication attempts")
            status = "warning"

        return SessionAuthTestResult(
            category="Session & Auth Security",
            test_name="Brute Force Protection",
            severity=severity,
            status=status,
            description="Tests for brute force protection mechanisms",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST ORCHESTRATION
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all session & authentication security tests"""

        print("\n" + "=" * 96)
        print("🔐 SESSION & AUTHENTICATION SECURITY TESTING")
        print("=" * 96)
        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        test_methods = [
            ("JWT Token Security", self.test_jwt_token_security),
            ("Session Fixation", self.test_session_fixation),
            ("Cookie Security", self.test_cookie_security),
            ("Password Strength", self.test_password_strength),
            ("Brute Force Protection", self.test_brute_force_protection),
        ]

        for test_name, test_method in test_methods:
            print(f"\n{'='*96}")
            print(f"Testing: {test_name}")
            print("=" * 96)

            try:
                result = await test_method()
                self.results.append(result)

                # Print test results
                status_icon = (
                    "✅"
                    if result.status == "pass"
                    else "⚠️" if result.status == "warning" else "❌"
                )
                severity_icon = (
                    "🔴"
                    if result.severity == "critical"
                    else "🟠" if result.severity == "high" else "🟡"
                )

                print(f"\n{severity_icon} Severity: {result.severity.upper()}")
                print(f"{status_icon} Status: {result.status.upper()}")
                print(f"\n📋 Description: {result.description}")

                if result.evidence:
                    print(f"\n🔍 Evidence:")
                    for evidence in result.evidence[:5]:
                        print(f"   • {evidence}")
                    if len(result.evidence) > 5:
                        print(f"   ... and {len(result.evidence) - 5} more")

                if result.recommendations:
                    print(f"\n💡 Recommendations:")
                    for rec in result.recommendations[:3]:
                        print(f"   • {rec}")

                # Count issues
                if result.status in ["fail", "warning"]:
                    self.issue_count += 1
                else:
                    self.pass_count += 1

            except Exception as e:
                print(f"\n❌ Error running test: {e}")
                self.results.append(
                    SessionAuthTestResult(
                        category=test_name,
                        test_name=test_name,
                        severity="error",
                        status="error",
                        description=f"Test failed with error: {str(e)}",
                    )
                )
                self.issue_count += 1

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""

        # Calculate score
        critical_count = sum(1 for r in self.results if r.severity == "critical")
        high_count = sum(1 for r in self.results if r.severity == "high")
        medium_count = sum(1 for r in self.results if r.severity == "medium")

        # Base score starts at 100, deduct based on severity
        score = 100
        score -= critical_count * 25
        score -= high_count * 15
        score -= medium_count * 5
        score = max(score, 0)

        # Compile report
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "overall_score": score,
            "total_tests": len(self.results),
            "passed": self.pass_count,
            "failed": self.issue_count,
            "severity_breakdown": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": sum(1 for r in self.results if r.severity == "low"),
                "info": sum(1 for r in self.results if r.severity == "info"),
            },
            "test_results": [
                {
                    "category": r.category,
                    "test_name": r.test_name,
                    "severity": r.severity,
                    "status": r.status,
                    "description": r.description,
                    "evidence": r.evidence,
                    "recommendations": r.recommendations,
                    "location": r.location,
                }
                for r in self.results
            ],
        }

        # Print summary
        print("\n" + "=" * 96)
        print("📊 SESSION & AUTHENTICATION SECURITY TEST SUMMARY")
        print("=" * 96)

        print(f"\n{'='*96}")
        print(f"OVERALL SECURITY SCORE: {score}/100")
        print("=" * 96)

        if score >= 80:
            print("✅ EXCELLENT - Strong session & authentication security")
        elif score >= 60:
            print("⚠️  GOOD - Some vulnerabilities detected")
        elif score >= 40:
            print("🟠 FAIR - Multiple authentication security issues")
        else:
            print("🔴 POOR - Critical authentication vulnerabilities")

        print(f"\n📈 Test Results:")
        print(f"   ✅ Passed: {self.pass_count}")
        print(f"   ❌ Failed/Warning: {self.issue_count}")

        print(f"\n🚨 Severity Breakdown:")
        print(f"   🔴 Critical: {critical_count}")
        print(f"   🟠 High: {high_count}")
        print(f"   🟡 Medium: {medium_count}")
        print(f"   🟢 Low: {sum(1 for r in self.results if r.severity == 'low')}")
        print(f"   ℹ️  Info: {sum(1 for r in self.results if r.severity == 'info')}")

        print(f"\n{'='*96}")
        print("CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION")
        print("=" * 96)

        critical_results = [r for r in self.results if r.severity == "critical"]
        if not critical_results:
            print("\n✅ No critical issues detected!")
        else:
            for result in critical_results:
                print(f"\n🔴 {result.category}: {result.test_name}")
                for evidence in result.evidence:
                    print(f"   • {evidence}")

        print(f"\n{'='*96}")
        print(f"Completed: {datetime.now().isoformat()}")
        print("=" * 96)

        return report


async def main():
    """Main entry point"""
    project_root = Path("/Users/sheriftito/Downloads/psychsync")
    tester = SessionAuthSecurityTester(project_root)

    report = await tester.run_all_tests()

    # Save report to JSON
    output_file = (
        project_root
        / f"session_auth_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
