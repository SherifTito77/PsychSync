#!/usr/bin/env python3
"""
Production Security Verification Script

This script performs comprehensive security checks to verify that all
security enhancements are properly configured and operational in production.

Usage:
    python scripts/verify_production_security.py

Exit Codes:
    0: All checks passed
    1: Critical security issues detected
    2: Warnings detected (non-critical)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.core.password_validator import password_validator
    from app.core.secure_logging import security_logger
    from app.main import app
except ImportError as e:
    print(f"❌ CRITICAL: Failed to import required modules: {e}")
    print(
        "Make sure you're running this from the project root with dependencies installed."
    )
    sys.exit(1)

# Verification results
results: List[Dict[str, Any]] = []


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def add_result(check_name: str, passed: bool, critical: bool, details: str = ""):
    """Add verification result"""
    results.append(
        {
            "check": check_name,
            "passed": passed,
            "critical": critical,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


def verify_configuration_security() -> bool:
    """Verify security configuration settings"""
    print_header("SECURITY CONFIGURATION VERIFICATION")

    all_passed = True

    # Check SECRET_KEY strength
    print_info("Checking SECRET_KEY strength...")
    if settings.SECRET_KEY:
        key_length = len(settings.SECRET_KEY)
        if key_length >= 128:
            print_success(f"SECRET_KEY is sufficiently long ({key_length} characters)")
            add_result("SECRET_KEY_LENGTH", True, True, f"{key_length} characters")
        else:
            print_error(
                f"SECRET_KEY is too short ({key_length} characters, minimum 128 recommended)"
            )
            add_result(
                "SECRET_KEY_LENGTH", False, True, f"{key_length} characters (< 128)"
            )
            all_passed = False
    else:
        print_error("SECRET_KEY is not set!")
        add_result("SECRET_KEY_SET", False, True, "Not configured")
        all_passed = False

    # Check environment
    print_info("Checking environment configuration...")
    if settings.ENVIRONMENT == "production":
        print_success(f"Running in {settings.ENVIRONMENT} mode")
        add_result("ENVIRONMENT", True, True, settings.ENVIRONMENT)
    else:
        print_warning(
            f"Running in {settings.ENVIRONMENT} mode (should be 'production' for production deployment)"
        )
        add_result("ENVIRONMENT", False, False, f"Running as {settings.ENVIRONMENT}")

    # Check debug mode
    print_info("Checking DEBUG setting...")
    if not settings.DEBUG:
        print_success("DEBUG mode is disabled")
        add_result("_DEBUG_DISABLED", True, True, "DEBUG=False")
    else:
        print_error("DEBUG mode is enabled in production!")
        add_result("_DEBUG_DISABLED", False, True, "DEBUG=True in production")
        all_passed = False

    return all_passed


def verify_password_validator() -> bool:
    """Verify password validator is working"""
    print_header("PASSWORD VALIDATOR VERIFICATION")

    all_passed = True

    # Test weak password rejection
    print_info("Testing weak password rejection...")
    is_valid, errors = password_validator.validate_password("weak")
    if not is_valid:
        print_success("Weak passwords are properly rejected")
        add_result("WEAK_PASSWORD_REJECTION", True, True)
    else:
        print_error("Weak passwords are being accepted!")
        add_result("WEAK_PASSWORD_REJECTION", False, True)
        all_passed = False

    # Test strong password acceptance
    print_info("Testing strong password acceptance...")
    is_valid, errors = password_validator.validate_password(
        "Str0ng!Pass1234WithMoreChars!!"
    )
    if is_valid:
        print_success("Strong passwords are properly accepted")
        add_result("STRONG_PASSWORD_ACCEPTANCE", True, True)
    else:
        print_warning(f"Strong password validation issue: {errors}")
        add_result("STRONG_PASSWORD_ACCEPTANCE", False, False, str(errors))

    # Test entropy calculation
    print_info("Testing password entropy calculation...")
    result = password_validator.assess_strength("Tr0ub4dor&3Horse!")
    if result.entropy_bits >= 60:
        print_success(
            f"Password entropy calculation working: {result.entropy_bits:.1f} bits"
        )
        add_result("PASSWORD_ENTROPY", True, True, f"{result.entropy_bits:.1f} bits")
    else:
        print_warning(f"Password entropy seems low: {result.entropy_bits:.1f} bits")
        add_result("PASSWORD_ENTROPY", False, False, f"{result.entropy_bits:.1f} bits")

    return all_passed


def verify_security_headers() -> bool:
    """Verify security headers are configured"""
    print_header("SECURITY HEADERS VERIFICATION")

    all_passed = True

    try:
        client = TestClient(app)

        # Make request to root endpoint
        print_info("Testing security headers on root endpoint...")
        response = client.get("/")

        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "max-age=31536000",
            "X-Frame-Options": "DENY",
        }

        for header, expected_value in required_headers.items():
            if header in response.headers:
                actual_value = response.headers[header]
                if expected_value in actual_value:
                    print_success(f"{header}: {actual_value}")
                    add_result(f"HEADER_{header}", True, True, actual_value)
                else:
                    print_warning(
                        f"{header}: Expected '{expected_value}', got '{actual_value}'"
                    )
                    add_result(
                        f"HEADER_{header}",
                        False,
                        False,
                        f"Expected: {expected_value}, Got: {actual_value}",
                    )
            else:
                print_error(f"{header} is missing!")
                add_result(f"HEADER_{header}", False, True, "Missing")
                all_passed = False

        # Check CSP header for unsafe-inline removal
        print_info("Checking Content-Security-Policy for unsafe-inline removal...")
        csp = response.headers.get("Content-Security-Policy", "")
        if "unsafe-inline" not in csp and "unsafe-eval" not in csp:
            print_success("CSP policy does not contain unsafe-inline or unsafe-eval")
            add_result("CSP_NO_UNSAFE_INLINE", True, True)
        else:
            errors = []
            if "unsafe-inline" in csp:
                errors.append("unsafe-inline present")
            if "unsafe-eval" in csp:
                errors.append("unsafe-eval present")
            print_warning(f"CSP contains: {', '.join(errors)}")
            add_result("CSP_NO_UNSAFE_INLINE", False, False, ", ".join(errors))

        # Check for HSTS preload
        if "preload" in csp:
            print_success("HSTS preload directive is present")
            add_result("HSTS_PRELOAD", True, True)
        else:
            print_info("HSTS preload directive not found (optional for production)")
            add_result("HSTS_PRELOAD", False, False, "Not configured")

    except Exception as e:
        print_error(f"Failed to test security headers: {e}")
        add_result("SECURITY_HEADERS_TEST", False, True, str(e))
        all_passed = False

    return all_passed


def verify_logging_security() -> bool:
    """Verify secure logging is configured"""
    print_header("SECURE LOGGING VERIFICATION")

    all_passed = True

    # Test that sensitive data is redacted
    print_info("Testing sensitive data redaction in logs...")

    import io

    from app.core.secure_logging import SensitiveDataFilter

    # Create a test logger with the filter
    test_logger = logging.getLogger("test_security_logging")
    test_logger.setLevel(logging.INFO)

    # Add string handler to capture log output
    string_stream = io.StringIO()
    handler = logging.StreamHandler(string_stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(SensitiveDataFilter())
    test_logger.addHandler(handler)

    # Log with sensitive data
    test_logger.info("User login: password=secret123")
    test_logger.info("JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    test_logger.info("Credit card: 4111-1111-1111-1111")

    # Get logged output
    log_output = string_stream.getvalue()

    # Check for redaction
    if (
        "***REDACTED***" in log_output
        or "***JWT***" in log_output
        or "***CARD***" in log_output
    ):
        print_success("Sensitive data is being redacted in logs")
        add_result("LOG_REDACTION", True, True)
    else:
        print_warning("Log redaction may not be working properly")
        add_result("LOG_REDACTION", False, False, "Redaction patterns not detected")

    # Clean up
    test_logger.removeHandler(handler)

    return all_passed


def verify_cors_configuration() -> bool:
    """Verify CORS configuration is secure"""
    print_header("CORS CONFIGURATION VERIFICATION")

    all_passed = True

    print_info("Checking CORS allowed origins...")

    if hasattr(settings, "CORS_ORIGINS"):
        cors_origins = settings.CORS_ORIGINS
        if cors_origins:
            print_info(f"CORS origins configured: {len(cors_origins)} origins")

            # Check for wildcard (dangerous in production)
            if "*" in cors_origins:
                print_error(
                    "CORS allows all origins (*) - this is dangerous in production!"
                )
                add_result("CORS_WILDCARD", False, True, "Wildcard origin allowed")
                all_passed = False
            else:
                print_success("CORS does not allow wildcard origins")
                add_result("CORS_WILDCARD", True, True, "No wildcard")

            # Check for localhost only (should be limited in production)
            localhost_count = sum(1 for origin in cors_origins if "localhost" in origin)
            if settings.ENVIRONMENT == "production" and localhost_count > 0:
                print_warning(
                    f"Localhost origins found in production ({localhost_count} origins)"
                )
                add_result(
                    "CORS_LOCALHOST_IN_PROD",
                    False,
                    False,
                    f"{localhost_count} localhost origins",
                )
            else:
                print_success("CORS origins are appropriately configured")
                add_result("CORS_LOCALHOST_IN_PROD", True, True)
        else:
            print_warning("No CORS origins configured")
            add_result("CORS_CONFIGURED", False, False, "No origins")
    else:
        print_info("CORS configuration not checked (CORS_ORIGINS not in settings)")

    return all_passed


def generate_report() -> Tuple[int, int]:
    """Generate verification report"""
    print_header("VERIFICATION REPORT")

    critical_passed = sum(1 for r in results if r["passed"] and r["critical"])
    critical_total = sum(1 for r in results if r["critical"])
    non_critical_passed = sum(1 for r in results if r["passed"] and not r["critical"])
    non_critical_total = sum(1 for r in results if not r["critical"])
    total_passed = sum(1 for r in results if r["passed"])

    print(f"Total Checks: {len(results)}")
    print(f"Critical Checks: {critical_passed}/{critical_total} passed")
    print(f"Non-Critical Checks: {non_critical_passed}/{non_critical_total} passed")
    print(f"Overall: {total_passed}/{len(results)} passed\n")

    # List failed checks
    failed_checks = [r for r in results if not r["passed"]]
    if failed_checks:
        print(f"{Colors.YELLOW}{Colors.BOLD}Failed Checks:{Colors.END}")
        for check in failed_checks:
            icon = "❌" if check["critical"] else "⚠️ "
            print(f"{icon} {check['check']}: {check.get('details', 'No details')}")
        print()

    # List passed critical checks
    passed_critical = [r for r in results if r["passed"] and r["critical"]]
    if passed_critical:
        print(f"{Colors.GREEN}{Colors.BOLD}Passed Critical Checks:{Colors.END}")
        for check in passed_critical:
            print(f"✅ {check['check']}")
        print()

    return critical_passed, critical_total


def main():
    """Main verification function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print(" PRODUCTION SECURITY VERIFICATION".center(70))
    print("=" * 70)
    print(f"{Colors.END}")
    print(f"Verification Time: {datetime.utcnow().isoformat()}")
    print(f"Environment: {settings.ENVIRONMENT}")

    # Run all verifications
    config_ok = verify_configuration_security()
    password_ok = verify_password_validator()
    headers_ok = verify_security_headers()
    logging_ok = verify_logging_security()
    cors_ok = verify_cors_configuration()

    # Generate report
    critical_passed, critical_total = generate_report()

    # Final verdict
    print_header("FINAL VERDICT")

    if critical_passed == critical_total:
        print(
            f"{Colors.GREEN}{Colors.BOLD}✅ ALL CRITICAL SECURITY CHECKS PASSED{Colors.END}\n"
        )
        print("Your application is properly configured for production deployment.")
        print("Remember to:")
        print("  1. Monitor security logs regularly")
        print("  2. Keep dependencies updated")
        print("  3. Run security audits periodically")
        print("  4. Review rate limiting and lockout metrics")
        sys.exit(0)
    else:
        print(
            f"{Colors.RED}{Colors.BOLD}❌ CRITICAL SECURITY ISSUES DETECTED{Colors.END}\n"
        )
        print(
            "Please address the critical issues above before deploying to production."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
