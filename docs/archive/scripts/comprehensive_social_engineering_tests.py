#!/usr/bin/env python3
"""
Comprehensive Social Engineering Security Testing Suite
Tests for social engineering vulnerabilities and human-exploitable weaknesses
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
class SocialEngTestResult:
    """Social engineering test result"""

    category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str  # pass, fail, warning
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    location: Optional[str] = None


class SocialEngineeringSecurityTester:
    """Comprehensive social engineering vulnerability scanner"""

    def __init__(
        self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")
    ):
        self.project_root = project_root
        self.results: List[SocialEngTestResult] = []
        self.issue_count = 0
        self.pass_count = 0

    # =========================================================================
    # TEST 1: PHISHING SCENARIOS
    # =========================================================================

    async def test_phishing_scenarios(self) -> SocialEngTestResult:
        """
        Test for phishing vulnerabilities:
        - Email verification flow weaknesses
        - Password reset link exploitation
        - Lack of email link expiration
        - Missing sender verification
        - Universal cross-site scripting (UXSS) opportunities
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check email service implementations
        email_service = self.project_root / "app/services/email_service.py"
        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"

        if email_service.exists():
            content = email_service.read_text()

            # Check for link expiration
            if not re.search(
                r"expires?\s*(at|in|before|within)", content, re.IGNORECASE
            ):
                findings.append("Email links may not have expiration times")
                recommendations.append(
                    "Add expiration time to all email verification/reset links"
                )
                status = "fail"
                severity = "high"

            # Check for token uniqueness
            if re.search(r'token\s*=\s*["\']\w+["\']', content) or re.search(
                r"uuid\.\w*\(\)", content
            ):
                pass  # Good: using UUID or tokens
            else:
                findings.append("Email tokens may not be sufficiently unique")
                recommendations.append(
                    "Use cryptographically secure random tokens (UUID4, secrets.token_urlsafe)"
                )
                status = "fail"

            # Check for HTML email vulnerabilities
            if "html" in content.lower() and "Content-Type" not in content:
                findings.append("HTML emails sent without Content-Type headers")
                recommendations.append(
                    "Always set Content-Type headers for HTML emails"
                )
                status = "warning"

        # Check auth endpoints for email-based flows
        if auth_endpoints.exists():
            content = auth_endpoints.read_text()

            # Check for rate limiting on password reset
            reset_func = re.search(
                r"def\s+(?:forgot_password|reset_password|send_reset_email)", content
            )
            if reset_func:
                # Look for rate limiting decorators or middleware
                func_context = content[reset_func.start() : reset_func.start() + 500]
                if (
                    "rate_limit" not in func_context.lower()
                    and "limiter" not in func_context.lower()
                ):
                    findings.append("Password reset endpoint lacks rate limiting")
                    recommendations.append(
                        "Add rate limiting to prevent email bombing/spam"
                    )
                    status = "fail"
                    severity = "critical"

            # Check for link expiration in reset flow
            if "reset_password" in content.lower():
                if not re.search(r"(expires|exp|max_age|ttl)", content, re.IGNORECASE):
                    findings.append("Password reset links may not expire")
                    recommendations.append(
                        "Set short expiration (15-60 minutes) for reset links"
                    )
                    status = "fail"

        # Check email templates for phishing indicators
        templates_dir = self.project_root / "app/templates/emails"
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.html"):
                content = template_file.read_text()

                # Check for generic branding
                if (
                    "click here" in content.lower()
                    and "psychsync" not in content.lower()
                ):
                    findings.append(
                        f"Template {template_file.name} uses generic 'click here' links"
                    )
                    recommendations.append(
                        "Use specific, branded language in email CTAs"
                    )

                # Check for HTTP links
                if "http://" in content and "https://" not in content:
                    findings.append(
                        f"Template {template_file.name} contains insecure HTTP links"
                    )
                    recommendations.append("Always use HTTPS links in emails")
                    status = "fail"
                    severity = "high"

                # Check for missing domain verification
                if "href=" in content and "psychsync" not in content.lower():
                    findings.append(
                        f"Template {template_file.name} may link to external domains"
                    )
                    recommendations.append(
                        "Verify all email links point to official domains"
                    )

        if not findings:
            findings.append("No critical phishing vulnerabilities detected")
            recommendations.append(
                "Implement DMARC, SPF, and DKIM for email authentication"
            )
            recommendations.append("Add email link expiration and rate limiting")

        return SocialEngTestResult(
            category="Phishing",
            test_name="Phishing Scenario Testing",
            severity=severity,
            status=status,
            description="Tests for email-based phishing vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 2: FORGOTTEN PASSWORD SOCIAL MANIPULATION
    # =========================================================================

    async def test_forgotten_password_manipulation(self) -> SocialEngTestResult:
        """
        Test for social engineering in password reset flows:
        - Information disclosure (valid vs invalid email)
        - Reset without proper verification
        - Missing rate limiting allows email enumeration
        - Weak security questions
        - Multiple reset requests
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"

        if auth_endpoints.exists():
            content = auth_endpoints.read_text()

            # Check for information disclosure in reset flow
            reset_endpoints = re.finditer(
                r'@router\.(post|put)\s*\(\s*["\']/(?:forgot|reset|lost)[/_]?password',
                content,
            )

            for match in reset_endpoints:
                endpoint_content = content[match.start() : match.end() + 2000]

                # Look for different responses based on email existence
                if (
                    "if.*email.*exists" in endpoint_content.lower()
                    or "if.*user" in endpoint_content.lower()
                ):
                    findings.append(
                        "Password reset may leak information about email existence"
                    )
                    recommendations.append(
                        "Always return same response regardless of email existence"
                    )
                    status = "fail"
                    severity = "high"

                # Check for immediate vs delayed responses
                if (
                    "asyncio.sleep" in endpoint_content
                    or "time.sleep" in endpoint_content
                ):
                    pass  # Good: timing attack protection
                else:
                    findings.append(
                        "Password reset may be vulnerable to timing attacks"
                    )
                    recommendations.append(
                        "Use constant-time responses to prevent email enumeration"
                    )
                    status = "warning"

            # Check for security questions (generally bad practice)
            if (
                "security_question" in content.lower()
                or "mother_maiden" in content.lower()
            ):
                findings.append(
                    "Security questions detected (weak authentication method)"
                )
                recommendations.append("Remove security questions - use 2FA instead")
                status = "fail"
                severity = "critical"

            # Check for old password requirement in reset
            if "old_password" in content.lower() and "reset" in content.lower():
                findings.append("Password reset requires old password (self-service)")
                recommendations.append(
                    "Ensure old password verification is properly implemented"
                )
                status = "warning"

        # Check user service for reset logic
        user_service = self.project_root / "app/services/user_service.py"
        if user_service.exists():
            content = user_service.read_text()

            # Check for reset token storage
            if "reset_token" in content.lower() or "reset_token" in content.lower():
                # Check if token is hashed
                if "hash" in content.lower() or "bcrypt" in content.lower():
                    pass  # Good: tokens are hashed
                else:
                    findings.append("Password reset tokens may be stored in plain text")
                    recommendations.append("Always hash reset tokens before storage")
                    status = "fail"
                    severity = "high"

            # Check for token expiration
            if "reset_token" in content.lower():
                if not re.search(r"(expires|exp|ttl|max_age)", content, re.IGNORECASE):
                    findings.append("Reset tokens may not expire")
                    recommendations.append(
                        "Set short expiration (15-60 minutes) for reset tokens"
                    )
                    status = "fail"

        # Check for multiple reset request handling
        models = self.project_root / "app/db/models/user.py"
        if models.exists():
            content = models.read_text()

            # Check if multiple reset tokens can exist
            if "reset_token" in content.lower():
                if "Column" in content and "reset_token" in content:
                    findings.append("User model has reset token field")
                    recommendations.append(
                        "Ensure only one valid reset token exists at a time"
                    )
                    status = "info"

        if not findings:
            findings.append("Password reset flow appears properly implemented")
            recommendations.append(
                "Implement universal response: 'If email exists, reset link sent'"
            )
            recommendations.append(
                "Add rate limiting to prevent email enumeration attacks"
            )

        return SocialEngTestResult(
            category="Social Manipulation",
            test_name="Forgotten Password Social Manipulation Testing",
            severity=severity,
            status=status,
            description="Tests for social engineering vulnerabilities in password reset flows",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 3: IMPERSONATION VIA HELPDESK
    # =========================================================================

    async def test_helpdesk_impersonation(self) -> SocialEngTestResult:
        """
        Test for helpdesk impersonation vulnerabilities:
        - Weak admin authentication
        - Missing action logging
        - Privilege escalation opportunities
        - User impersonation features
        - Password change by support
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for admin/impersonation endpoints
        api_endpoints = self.project_root / "app/api/v1/endpoints"
        if api_endpoints.exists():
            for endpoint_file in api_endpoints.glob("*.py"):
                content = endpoint_file.read_text()

                # Check for impersonation functions
                if re.search(
                    r"impersonat|login_as|become_user|sudo", content, re.IGNORECASE
                ):
                    findings.append(
                        f"User impersonation feature in {endpoint_file.name}"
                    )
                    recommendations.append(
                        "Ensure impersonation requires MFA and detailed audit logging"
                    )
                    status = "fail"
                    severity = "critical"

                # Check for admin password reset
                if re.search(
                    r"admin.*reset.*password|force.*reset|set_password",
                    content,
                    re.IGNORECASE,
                ):
                    findings.append(f"Admin password reset in {endpoint_file.name}")
                    recommendations.append(
                        "Require user confirmation for admin-initiated password changes"
                    )
                    status = "warning"

                # Check for user role modification
                if re.search(
                    r"(change_role|update_role|set_role|make_admin)",
                    content,
                    re.IGNORECASE,
                ):
                    if not re.search(r"audit|log|track", content, re.IGNORECASE):
                        findings.append(
                            f"Role changes in {endpoint_file.name} may not be audited"
                        )
                        recommendations.append(
                            "Log all role/permission changes with admin identity"
                        )
                        status = "fail"
                        severity = "high"

        # Check for admin authentication
        admin_endpoints = self.project_root / "app/api/v1/endpoints/users.py"
        if admin_endpoints.exists():
            content = admin_endpoints.read_text()

            # Check for admin-only routes
            admin_routes = re.finditer(r"@router\.(get|post|put|delete)", content)
            for route in admin_routes:
                route_context = content[route.start() : route.end() + 300]

                if "admin" in route_context.lower():
                    # Check for proper admin check
                    if (
                        "current_user" not in route_context
                        or "is_admin" not in route_context.lower()
                    ):
                        findings.append(
                            "Admin route may lack proper authorization check"
                        )
                        recommendations.append(
                            "Always verify admin role with get_current_user dependency"
                        )
                        status = "fail"
                        severity = "critical"

        # Check audit logging
        audit_log = self.project_root / "app/core/audit_logging.py"
        if not audit_log.exists():
            findings.append("No dedicated audit logging module found")
            recommendations.append(
                "Implement comprehensive audit logging for admin actions"
            )
            status = "warning"
        else:
            content = audit_log.read_text()
            has_impersonation_logging = "log_impersonation" in content
            has_role_change_logging = "log_role_change" in content
            has_password_reset_logging = "log_password_reset" in content

            if has_impersonation_logging and has_role_change_logging:
                findings.append(
                    "Comprehensive audit logging for admin operations detected"
                )
            elif (
                "impersonat" not in content.lower()
                and "role_change" not in content.lower()
            ):
                findings.append(
                    "Audit logging may not cover impersonation/role changes"
                )
                recommendations.append(
                    "Add audit events for sensitive admin operations"
                )
                status = "warning"

        # Check for MFA requirement
        security_config = self.project_root / "app/core/security.py"
        if security_config.exists():
            content = security_config.read_text()

            if "mfa" not in content.lower() and "two_factor" not in content.lower():
                findings.append("No MFA enforcement for admin operations detected")
                recommendations.append(
                    "Require MFA for all admin actions and impersonation"
                )
                status = "warning"

        if not findings:
            findings.append("No critical impersonation vulnerabilities detected")
            recommendations.append("Implement MFA for all admin operations")
            recommendations.append(
                "Log all admin actions with timestamp, admin ID, and affected user"
            )

        return SocialEngTestResult(
            category="Impersonation",
            test_name="Helpdesk Impersonation Testing",
            severity=severity,
            status=status,
            description="Tests for helpdesk/admin impersonation vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 4: RECOVERY FLOWS IDENTITY VERIFICATION
    # =========================================================================

    async def test_recovery_flows_identity_verification(self) -> SocialEngTestResult:
        """
        Test for identity verification weaknesses in account recovery:
        - Weak KBA (knowledge-based authentication)
        - Bypass via alternate recovery methods
        - Insufficient verification before account changes
        - Recovery code reuse
        - Missing recovery attempt logging
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"
        two_fa_service = self.project_root / "app/services/two_factor_service.py"
        two_fa_endpoints = self.project_root / "app/api/v1/endpoints/two_factor_auth.py"

        # Check for 2FA system (new modular approach)
        has_2fa_service = two_fa_service.exists()
        has_2fa_endpoints = two_fa_endpoints.exists()

        # Check for 2FA in auth.py (legacy approach)
        auth_has_2fa = False
        if auth_endpoints.exists():
            content = auth_endpoints.read_text()
            auth_has_2fa = (
                "2fa" in content.lower()
                or "two_factor" in content.lower()
                or "mfa" in content.lower()
            )

            # Check for KBA endpoints
            if re.search(
                r"security_question|mother_maiden|pet_name|favorite_",
                content,
                re.IGNORECASE,
            ):
                findings.append("Knowledge-based authentication questions detected")
                recommendations.append("Remove KBA - use 2FA or recovery codes instead")
                status = "fail"
                severity = "critical"

        # Determine if 2FA system exists
        has_2fa = has_2fa_service or has_2fa_endpoints or auth_has_2fa

        if has_2fa:
            findings.append("2FA system detected")
            # Check if recovery codes are implemented
            if has_2fa_service:
                service_content = two_fa_service.read_text()
                if (
                    "recovery_code" in service_content.lower()
                    and "single" in service_content.lower()
                ):
                    findings.append(
                        "2FA includes single-use recovery codes (best practice)"
                    )
                elif "recovery_code" in service_content.lower():
                    findings.append("2FA includes recovery codes")
                else:
                    findings.append("2FA detected but no recovery code system")
                    recommendations.append("Implement recovery codes for 2FA backup")
                    status = "warning"

            # Check if 2FA is enforced for admin
            deps_file = self.project_root / "app/api/v1/deps.py"
            if deps_file.exists():
                deps_content = deps_file.read_text()
                if (
                    "get_admin_user_with_mfa" in deps_content
                    or "get_current_user_with_mfa" in deps_content
                ):
                    findings.append("MFA enforcement for admin operations detected")
                else:
                    findings.append("2FA exists but not enforced for admin operations")
                    recommendations.append("Require 2FA for all admin actions")
                    status = "warning"
        else:
            findings.append("No 2FA system detected")
            recommendations.append("Implement TOTP-based 2FA with recovery codes")
            status = "fail"
            severity = "high"

        # Check for account recovery without verification (only if auth.py exists)
        if auth_endpoints.exists():
            recovery_func = re.search(
                r"def\s+(?:recover_account|restore_account|verify_recovery)", content
            )
            if recovery_func:
                func_context = content[
                    recovery_func.start() : recovery_func.start() + 1000
                ]

                # Check verification steps
                verification_count = len(
                    re.findall(
                        r"verif|confirm|validate|check", func_context, re.IGNORECASE
                    )
                )
                if verification_count < 2:
                    findings.append(
                        "Account recovery may have insufficient verification"
                    )
                    recommendations.append(
                        "Require multiple verification factors (email + 2FA)"
                    )
                    status = "fail"

        # Check user model for recovery fields
        user_model = self.project_root / "app/db/models/user.py"
        if user_model.exists():
            content = user_model.read_text()

            # Check for recovery code storage
            if "recovery_code" in content.lower() or "backup_code" in content.lower():
                # Check if codes are hashed
                if "hash" not in content.lower() and "bcrypt" not in content.lower():
                    findings.append("Recovery codes may be stored in plain text")
                    recommendations.append("Always hash recovery codes before storage")
                    status = "fail"
                    severity = "high"

        # Check for account change verification
        users_service = self.project_root / "app/services/user_service.py"
        if users_service.exists():
            content = users_service.read_text()

            # Check email change verification
            if "change_email" in content.lower() or "update_email" in content.lower():
                if not re.search(
                    r"verif|confirm.*token|send.*email", content, re.IGNORECASE
                ):
                    findings.append("Email changes may not require verification")
                    recommendations.append(
                        "Always require email verification for email changes"
                    )
                    status = "fail"
                    severity = "high"

            # Check password change verification
            if "change_password" in content.lower():
                if not re.search(
                    r"old_password|current_password|verify_password",
                    content,
                    re.IGNORECASE,
                ):
                    findings.append("Password changes may not require current password")
                    recommendations.append(
                        "Always require current password for password changes"
                    )
                    status = "fail"
                    severity = "high"

        # Check for recovery attempt rate limiting
        auth_service = self.project_root / "app/services/auth_service.py"
        if auth_service.exists():
            content = auth_service.read_text()

            if "recover" in content.lower() or "reset" in content.lower():
                if not re.search(
                    r"rate.?limit|throttle|attempt.*limit", content, re.IGNORECASE
                ):
                    findings.append("Account recovery may lack rate limiting")
                    recommendations.append(
                        "Limit recovery attempts to prevent brute force"
                    )
                    status = "warning"

        if not findings:
            findings.append(
                "No critical identity verification vulnerabilities detected"
            )
            recommendations.append("Implement 2FA with single-use recovery codes")
            recommendations.append(
                "Require multiple verification factors for account recovery"
            )
            recommendations.append("Log all recovery attempts with IP and timestamp")

        return SocialEngTestResult(
            category="Identity Verification",
            test_name="Recovery Flow Identity Verification Testing",
            severity=severity,
            status=status,
            description="Tests for identity verification weaknesses in account recovery",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 5: BYPASSING PHONE VERIFICATION
    # =========================================================================

    async def test_phone_verification_bypass(self) -> SocialEngTestResult:
        """
        Test for phone/SMS verification bypass vulnerabilities:
        - SMS interception opportunities
        - Code reuse/replay attacks
        - Weak SMS codes (predictable)
        - Missing rate limiting
        - VoIP number acceptance
        - SS7 vulnerabilities
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for phone verification implementation
        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"
        auth_service = self.project_root / "app/services/auth_service.py"

        phone_verification_found = False

        for file_path in [auth_endpoints, auth_service]:
            if file_path and file_path.exists():
                content = file_path.read_text()

                # Check for SMS/phone verification
                if re.search(
                    r"sms|phone|verify.?phone|send.?code|otp", content, re.IGNORECASE
                ):
                    phone_verification_found = True

                    # Check SMS code generation
                    if re.search(r"code\s*=\s*\d{4,6}|pin\s*=\s*\d+", content):
                        findings.append(
                            "SMS codes may be predictable (sequential/static)"
                        )
                        recommendations.append(
                            "Use cryptographically secure random codes (secrets module)"
                        )
                        status = "fail"
                        severity = "high"

                    # Check code expiration
                    if not re.search(
                        r"expires?|ttl|max_age|valid_for", content, re.IGNORECASE
                    ):
                        findings.append("SMS codes may not expire")
                        recommendations.append(
                            "Set short expiration (5-10 minutes) for SMS codes"
                        )
                        status = "fail"

                    # Check code length
                    code_length_match = re.search(r"code.*?(\d{4,6})", content)
                    if code_length_match:
                        code_length = int(code_length_match.group(1))
                        if code_length < 6:
                            findings.append(
                                f"SMS codes are only {code_length} digits (weak)"
                            )
                            recommendations.append(
                                "Use at least 6-digit codes for SMS verification"
                            )
                            status = "warning"

                    # Check for rate limiting
                    if not re.search(
                        r"rate.?limit|throttle|attempt.*limit", content, re.IGNORECASE
                    ):
                        findings.append("SMS verification may lack rate limiting")
                        recommendations.append(
                            "Limit SMS attempts to prevent SMS bombing and cost attacks"
                        )
                        status = "fail"
                        severity = "high"

                    # Check for code storage/hashing
                    if "store" in content.lower() or "save" in content.lower():
                        if (
                            "hash" not in content.lower()
                            and "bcrypt" not in content.lower()
                        ):
                            findings.append("SMS codes may be stored in plain text")
                            recommendations.append("Hash SMS codes before storage")
                            status = "fail"
                            severity = "high"

                    # Check for VoIP number filtering
                    if "twilio" in content.lower() or "nexmo" in content.lower():
                        if (
                            "voip" not in content.lower()
                            and "type" not in content.lower()
                        ):
                            findings.append("SMS service may not filter VoIP numbers")
                            recommendations.append(
                                "Filter VoIP numbers which are easier to compromise"
                            )
                            status = "warning"

        if not phone_verification_found:
            findings.append("No phone/SMS verification system detected")
            recommendations.append(
                "Consider implementing SMS verification as 2FA factor"
            )
            recommendations.append(
                "If using SMS, be aware of SS7 vulnerabilities and SIM swapping risks"
            )
            status = "info"
            severity = "info"

        # Check for 2FA alternatives to SMS
        security_config = self.project_root / "app/core/security.py"
        if security_config.exists():
            content = security_config.read_text()

            if "totp" not in content.lower() and "authenticator" not in content.lower():
                findings.append("No TOTP authenticator app option (only SMS?)")
                recommendations.append(
                    "Implement TOTP (Google Authenticator) as more secure 2FA alternative"
                )
                status = "warning"

        # Check for replay attack protection
        if phone_verification_found:
            for file_path in [auth_endpoints, auth_service]:
                if file_path and file_path.exists():
                    content = file_path.read_text()

                    if "verify" in content.lower() and "code" in content.lower():
                        # Check if code is marked as used
                        if not re.search(
                            r"use|consum|redeem|invalidate", content, re.IGNORECASE
                        ):
                            findings.append(
                                "SMS codes may not be invalidated after use (replay attack risk)"
                            )
                            recommendations.append(
                                "Mark codes as used after successful verification"
                            )
                            status = "fail"
                            severity = "high"
                        break

        if not findings or status == "info":
            findings = [
                "No phone verification bypass vulnerabilities detected (or no SMS system)"
            ]
            recommendations = [
                "If implementing SMS verification:",
                "- Use 6+ digit codes with random generation",
                "- Set 5-10 minute expiration",
                "- Implement rate limiting (attempts and number of SMS)",
                "- Hash codes before storage",
                "- Mark codes as used after verification",
                "- Prefer TOTP authenticator apps over SMS",
            ]

        return SocialEngTestResult(
            category="Phone Verification",
            test_name="Phone Verification Bypass Testing",
            severity=severity,
            status=status,
            description="Tests for SMS/phone verification bypass vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST ORCHESTRATION
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all social engineering security tests"""

        print("\n" + "=" * 96)
        print("🔐 SOCIAL ENGINEERING SECURITY TESTING")
        print("=" * 96)
        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        test_methods = [
            ("Phishing Scenarios", self.test_phishing_scenarios),
            ("Password Manipulation", self.test_forgotten_password_manipulation),
            ("Helpdesk Impersonation", self.test_helpdesk_impersonation),
            ("Recovery Flows", self.test_recovery_flows_identity_verification),
            ("Phone Verification Bypass", self.test_phone_verification_bypass),
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
                    SocialEngTestResult(
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
        print("📊 SOCIAL ENGINEERING SECURITY TEST SUMMARY")
        print("=" * 96)

        print(f"\n{'='*96}")
        print(f"OVERALL SECURITY SCORE: {score}/100")
        print("=" * 96)

        if score >= 80:
            print("✅ GOOD - Strong social engineering defenses")
        elif score >= 60:
            print("⚠️  FAIR - Some vulnerabilities detected")
        elif score >= 40:
            print("🟠 MODERATE RISK - Multiple vulnerabilities")
        else:
            print("🔴 HIGH RISK - Critical social engineering vulnerabilities")

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
    tester = SocialEngineeringSecurityTester(project_root)

    report = await tester.run_all_tests()

    # Save report to JSON
    output_file = (
        project_root
        / f"social_engineering_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
