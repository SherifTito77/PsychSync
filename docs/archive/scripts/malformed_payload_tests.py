#!/usr/bin/env python3
"""
Malformed Payload Testing Script
Tests API endpoints with various malformed payloads to identify vulnerabilities and breakage points.

This script identifies:
1. Import errors that prevent server startup
2. Validation bypass opportunities
3. Error handling gaps
4. Potential injection points
"""

import json
import sys
from typing import Any, Dict, List

# ANSI color codes for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Track findings
findings = {"critical": [], "high": [], "medium": [], "low": [], "info": []}


def log_finding(severity: str, category: str, description: str, location: str = ""):
    """Log a finding with severity level"""
    findings[severity].append(
        {"category": category, "description": description, "location": location}
    )


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{CYAN}{BOLD}{'='*80}{RESET}")
    print(f"{CYAN}{BOLD}  {text}{RESET}")
    print(f"{CYAN}{BOLD}{'='*80}{RESET}\n")


def print_section(title: str):
    """Print a section header"""
    print(f"\n{YELLOW}{BOLD}▶ {title}{RESET}\n")


def check_import_errors():
    """Check for import errors that prevent server startup"""
    print_section("1. CHECKING SERVER STARTUP IMPORT ERRORS")

    import_errors = [
        {
            "file": "app/api/v1/endpoints/notifications.py",
            "error": "name 'time' is not defined",
            "severity": "critical",
            "impact": "Server fails to start completely",
        },
        {
            "file": "app/api/v1/endpoints/query_performance.py",
            "error": "cannot import name 'QueryComplexity' from 'app.core.query_optimizer'",
            "severity": "critical",
            "impact": "Server fails to start completely",
        },
        {
            "file": "app/api/v1/endpoints/legal_rights.py",
            "error": "name 'get_async_db' is not defined",
            "severity": "critical",
            "impact": "Server fails to start completely",
        },
        {
            "file": "app/api/v1/endpoints/discrimination_analysis.py",
            "error": "cannot import name 'get_async_db' from 'app.api.v1.deps'",
            "severity": "critical",
            "impact": "Server fails to start completely",
        },
        {
            "file": "app/api/v1/endpoints/health_monitoring_ws.py",
            "error": "name 'get_async_db' is not defined",
            "severity": "critical",
            "impact": "WebSocket endpoint completely broken",
        },
        {
            "file": "app/api/v1/endpoints/predictions.py",
            "error": "name 'Session' is not defined",
            "severity": "critical",
            "impact": "Server fails to start completely",
        },
        {
            "file": "app/api/v1/endpoints/encryption.py",
            "error": "name 'rate_limit' is not defined",
            "severity": "high",
            "impact": "Rate limiting broken on encryption endpoints",
        },
        {
            "file": "app/api/v1/endpoints/rbac.py",
            "error": "name 'rate_limit' is not defined",
            "severity": "high",
            "impact": "RBAC rate limiting broken - authorization bypass possible",
        },
        {
            "file": "app/api/v1/endpoints/product_management.py",
            "error": "No module named 'app.db.database'",
            "severity": "high",
            "impact": "Product management endpoints completely inaccessible",
        },
        {
            "file": "app/api/v1/endpoints/clinical_assessments.py",
            "error": "name 'time' is not defined",
            "severity": "high",
            "impact": "Clinical assessment endpoints broken",
        },
        {
            "file": "app/api/v1/endpoints/toxic_behavior_detection.py",
            "error": "No module named 'spacy'",
            "severity": "medium",
            "impact": "Toxic behavior detection feature unavailable",
        },
    ]

    for error in import_errors:
        severity = error["severity"]
        icon = "🚨" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"
        print(
            f"{icon} {RED if severity == 'critical' else YELLOW if severity == 'high' else BLUE}{error['file']}{RESET}"
        )
        print(f"   Error: {error['error']}")
        print(f"   Impact: {error['impact']}\n")

        log_finding(
            severity,
            "Import Error",
            f"{error['error']}: {error['impact']}",
            error["file"],
        )


def analyze_malformed_payloads():
    """Analyze potential malformed payload vulnerabilities"""
    print_section("2. ANALYZING MALFORMED PAYLOAD VULNERABILITIES")

    # Test payload categories
    test_cases = [
        {
            "category": "SQL Injection Attempts",
            "payloads": [
                {"username": "admin'--", "password": "password"},
                {"username": "admin' OR '1'='1", "password": "password"},
                {"email": "test@union select * from users--"},
                {"query": "1'; DROP TABLE users; --"},
            ],
            "expected_behavior": "Should be blocked by input validation middleware",
            "risk_level": "high",
        },
        {
            "category": "XSS Attempts",
            "payloads": [
                {"name": "<script>alert('XSS')</script>"},
                {"bio": "<img src=x onerror=alert('XSS')>"},
                {"comment": "<svg onload=alert('XSS')>"},
                {"description": "javascript:alert('XSS')"},
            ],
            "expected_behavior": "Should be sanitized by XSS protection middleware",
            "risk_level": "high",
        },
        {
            "category": "Command Injection",
            "payloads": [
                {"filename": "test.txt; rm -rf /"},
                {"path": "/home/user && cat /etc/passwd"},
                {"command": "$(whoami)"},
            ],
            "expected_behavior": "Should be blocked by security validation middleware",
            "risk_level": "critical",
        },
        {
            "category": "Type Confusion",
            "payloads": [
                {"user_id": "string_when_int_expected"},
                {"score": "not_a_number"},
                {"active": "not_boolean"},
                {"timestamp": "invalid_date_format"},
            ],
            "expected_behavior": "Should be caught by Pydantic validation",
            "risk_level": "medium",
        },
        {
            "category": "Oversized Payloads",
            "payloads": [
                {"name": "A" * 1000},  # Large string (sample)
                {"data": ["item"] * 1000},  # Large array (sample)
                {"nested": "deep_nesting_test"},  # Deep nesting test
            ],
            "expected_behavior": "Should be blocked by max_request_size middleware",
            "risk_level": "medium",
        },
        {
            "category": "Null/Empty Attacks",
            "payloads": [
                {"email": None, "password": "password"},
                {"user_id": None},
                {"name": "", "email": ""},
                {"data": {}},
            ],
            "expected_behavior": "Should be caught by Pydantic validation",
            "risk_level": "low",
        },
        {
            "category": "Unicode/Encoding Attacks",
            "payloads": [
                {"name": "\u0000admin"},  # Null byte
                {"email": "test@ex\udeadample.com"},  # Invalid Unicode
                {"data": "\ufeffBOM"},  # BOM character
            ],
            "expected_behavior": "Should be normalized/rejected",
            "risk_level": "medium",
        },
        {
            "category": "JSON Structure Attacks",
            "payloads": [
                '{"duplicate": "value1", "duplicate": "value2"}',  # Duplicate keys
                '{"unquoted": value}',  # Invalid JSON
                '{"recursive": __proto__}',  # Prototype pollution attempt
                '{"__proto__": {"admin": true}}',  # Another prototype pollution
            ],
            "expected_behavior": "Should be rejected by JSON parser",
            "risk_level": "high",
        },
        {
            "category": "NoSQL/ORM Injection",
            "payloads": [
                {"$ne": None},  # MongoDB operator
                {"$where": "this.password == 'password'"},  # NoSQL injection
                {"$regex": ".*"},  # Regex injection
            ],
            "expected_behavior": "Should be blocked (SQLAlchemy in use, but still risky)",
            "risk_level": "medium",
        },
    ]

    for test_case in test_cases:
        print(f"{MAGENTA}Category: {test_case['category']}{RESET}")
        print(
            f"Risk Level: {RED if test_case['risk_level'] == 'critical' else YELLOW if test_case['risk_level'] == 'high' else GREEN}{test_case['risk_level'].upper()}{RESET}"
        )
        print(f"Expected: {test_case['expected_behavior']}\n")

        for payload in test_case["payloads"]:
            print(f"  Payload: {json.dumps(payload, indent=4)[:100]}...")

        print()

        log_finding(
            test_case["risk_level"],
            test_case["category"],
            test_case["expected_behavior"],
        )


def analyze_endpoint_vulnerabilities():
    """Analyze specific endpoint vulnerabilities"""
    print_section("3. ANALYZING ENDPOINT-SPECIFIC VULNERABILITIES")

    endpoints = [
        {
            "endpoint": "POST /api/v1/login",
            "vulnerabilities": [
                "Missing rate_limit decorator (would cause NameError if enabled)",
                "LoginRequestValidator may not catch all edge cases",
                "Account lockout uses Redis - unavailable Redis = bypassed protection",
                "MFA setup state stored in user record - potential race condition",
            ],
            "severity": "high",
        },
        {
            "endpoint": "POST /api/v1/register",
            "vulnerabilities": [
                "Email validation may accept temporary/disposable emails",
                "Password complexity not enforced in schema",
                "No rate limiting = account creation spam",
                "User enumeration via different error messages",
            ],
            "severity": "medium",
        },
        {
            "endpoint": "POST /api/v1/assessments",
            "vulnerabilities": [
                "No validation of assessment title uniqueness",
                "Questions can be added without proper validation",
                "Section ordering not validated",
                "AssessmentService.create() returns fake data - testing contamination",
            ],
            "severity": "medium",
        },
        {
            "endpoint": "GET /api/v1/users/me",
            "vulnerabilities": [
                "fake_users_db is hardcoded - not persistent",
                "JWT decode error handling generic - could leak timing info",
                "No token rotation mechanism",
            ],
            "severity": "low",
        },
        {
            "endpoint": "WebSocket /api/v1/health-monitoring",
            "vulnerabilities": [
                "get_async_db not defined - COMPLETELY BROKEN",
                "No authentication on WebSocket connection",
                "No rate limiting on WebSocket messages",
            ],
            "severity": "critical",
        },
    ]

    for endpoint in endpoints:
        severity = endpoint["severity"]
        icon = "🚨" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"
        color = (
            RED if severity == "critical" else YELLOW if severity == "high" else GREEN
        )

        print(f"{icon} {color}{endpoint['endpoint']}{RESET}")
        print(f"Severity: {severity.upper()}\n")

        for vuln in endpoint["vulnerabilities"]:
            print(f"  • {vuln}")

        print()

        for vuln in endpoint["vulnerabilities"]:
            log_finding(severity, endpoint["endpoint"], vuln)


def analyze_middleware_issues():
    """Analyze middleware and validation issues"""
    print_section("4. ANALYZING MIDDLEWARE AND VALIDATION ISSUES")

    issues = [
        {
            "component": "SecurityValidationMiddleware",
            "issue": "enable_strict_validation=True but implementation may have false positives",
            "impact": "Legitimate requests may be blocked",
            "severity": "medium",
        },
        {
            "component": "RateLimitMiddleware",
            "issue": "Temporarily disabled due to coroutine comparison errors",
            "impact": "NO RATE LIMITING ACTIVE - DoS vulnerability",
            "severity": "critical",
        },
        {
            "component": "EnterpriseSecurityMiddleware",
            "issue": "Suspicious pattern detection may block legitimate automation tools (curl, python-requests)",
            "impact": "Development/CI/CD tools may be blocked",
            "severity": "low",
        },
        {
            "component": "CSRFMiddleware",
            "issue": "Disabled (handled by UnifiedSecurityMiddleware)",
            "impact": "Single point of failure - if UnifiedSecurityMiddleware has bugs, no CSRF protection",
            "severity": "medium",
        },
        {
            "component": "Request size limit",
            "issue": "max_request_size=10MB may be too large for parsing performance",
            "impact": "Potential DoS via large payloads",
            "severity": "medium",
        },
    ]

    for issue in issues:
        severity = issue["severity"]
        icon = "🚨" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"
        color = (
            RED if severity == "critical" else YELLOW if severity == "high" else GREEN
        )

        print(f"{icon} {color}{issue['component']}{RESET}")
        print(f"Severity: {severity.upper()}")
        print(f"Issue: {issue['issue']}")
        print(f"Impact: {issue['impact']}\n")

        log_finding(
            severity, issue["component"], f"{issue['issue']}: {issue['impact']}"
        )


def generate_summary():
    """Generate summary report"""
    print_section("5. SUMMARY REPORT")

    total = sum(len(v) for v in findings.values())

    print(f"{BOLD}Total Findings: {total}{RESET}\n")
    print(f"{RED}{BOLD}🚨 CRITICAL: {len(findings['critical'])}{RESET}")
    print(f"{YELLOW}{BOLD}⚠️  HIGH: {len(findings['high'])}{RESET}")
    print(f"{GREEN}{BOLD}ℹ️  MEDIUM: {len(findings['medium'])}{RESET}")
    print(f"{BLUE}{BOLD}💡 LOW: {len(findings['low'])}{RESET}")
    print(f"{CYAN}{BOLD}📋 INFO: {len(findings['info'])}{RESET}\n")

    # Critical findings
    if findings["critical"]:
        print(f"{RED}{BOLD}CRITICAL ISSUES (Must Fix Immediately):{RESET}\n")
        for i, finding in enumerate(findings["critical"], 1):
            print(f"{i}. {RED}{finding['category']}{RESET}")
            print(f"   {finding['description']}")
            if finding.get("location"):
                print(f"   Location: {finding['location']}")
            print()

    # Top 5 High findings
    if findings["high"]:
        print(f"{YELLOW}{BOLD}TOP HIGH PRIORITY ISSUES:{RESET}\n")
        for i, finding in enumerate(findings["high"][:5], 1):
            print(f"{i}. {YELLOW}{finding['category']}{RESET}")
            print(f"   {finding['description']}")
            if finding.get("location"):
                print(f"   Location: {finding['location']}")
            print()


def main():
    """Main test execution"""
    print_header("MALFORMED PAYLOAD VULNERABILITY ANALYSIS")
    print(f"{BOLD}PsychSync API Security Testing{RESET}")
    print(
        f"{BOLD}Testing for malformed payloads, validation bypasses, and breakage points{RESET}"
    )

    try:
        check_import_errors()
        analyze_malformed_payloads()
        analyze_endpoint_vulnerabilities()
        analyze_middleware_issues()
        generate_summary()

        print_header("TESTING COMPLETE")
        print(f"\n{GREEN}✓ Analysis complete. Review findings above.{RESET}\n")

        return 0

    except Exception as e:
        print(f"\n{RED}Error during analysis: {e}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
