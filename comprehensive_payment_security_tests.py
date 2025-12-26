#!/usr/bin/env python3
"""
COMPREHENSIVE PAYMENT SECURITY TESTING SUITE
Tests payment processing security for business logic vulnerabilities

Author: Security Team
Version: 1.0
Date: December 23, 2024

Tests:
1. Double-charging on rapid click
2. Refund race conditions
3. PCI compliance essentials
4. Card data leakage
5. Subscription cancellation behavior
"""

import os
import sys
import re
import json
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import ast

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

project_root = Path(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class SecurityIssue:
    """Represents a security issue found during testing"""
    category: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    location: str
    evidence: str = ""
    remediation: str = ""
    cvss_score: float = 0.0


@dataclass
class TestResult:
    """Represents the result of a security test"""
    test_name: str
    passed: bool
    score: float  # 0-100
    issues: List[SecurityIssue] = field(default_factory=list)
    details: str = ""


class PaymentSecurityTester:
    """Comprehensive payment security testing suite"""

    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.test_results: List[TestResult] = []
        self.start_time = datetime.now()

    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}{title}{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}\n")

    def print_test_header(self, test_name: str):
        """Print test section header"""
        print(f"\n{MAGENTA}🔍 {test_name}{RESET}")
        print(f"{MAGENTA}{'-' * 80}{RESET}")

    # =========================================================================
    # TEST 1: Double-Charging on Rapid Click
    # =========================================================================

    async def test_double_charging(self) -> TestResult:
        """Test for double-charging vulnerability on rapid clicks"""
        self.print_test_header("TEST 1: Double-Charging on Rapid Click")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning for idempotency protection mechanisms...{RESET}")

        # Check for idempotency keys in billing code
        billing_files = [
            "app/api/v1/endpoints/billing.py",
            "app/services/billing.py"
        ]

        idempotency_found = False
        idempotency_patterns = [
            r"idempotency_key",
            r"idempotency-key",
            r"Idempotency",
            r"unique.*request.*id",
            r"request.*id.*unique"
        ]

        for file_path_str in billing_files:
            file_path = project_root / file_path_str
            if file_path.exists():
                content = file_path.read_text()

                for pattern in idempotency_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        idempotency_found = True
                        details.append(f"✅ Found idempotency pattern: {pattern} in {file_path_str}")
                        break

        if not idempotency_found:
            score -= 40
            issues.append(SecurityIssue(
                category="double_charging",
                severity="critical",
                title="Missing Idempotency Protection",
                description="Payment endpoints lack idempotency keys, allowing potential double-charging on rapid clicks",
                location="app/api/v1/endpoints/billing.py",
                remediation="Add idempotency_key to all payment mutations:\n"
                          "- Generate unique UUID for each payment request\n"
                          "- Store idempotency keys in Redis with TTL\n"
                          "- Check key exists before processing payment\n"
                          "- Example: idempotency_key = request.headers.get('Idempotency-Key')",
                cvss_score=7.5
            ))
            details.append(f"{RED}❌ CRITICAL: No idempotency protection found{RESET}")
        else:
            details.append(f"{GREEN}✅ Idempotency protection detected{RESET}")

        # Check for duplicate request prevention
        print(f"\n{BLUE}Checking for duplicate request prevention...{RESET}")

        duplicate_prevention = False
        duplicate_patterns = [
            r"seen.*request",
            r"request.*cache",
            r"deduplicate",
            r"already.*processed"
        ]

        for file_path_str in billing_files:
            file_path = project_root / file_path_str
            if file_path.exists():
                content = file_path.read_text()
                for pattern in duplicate_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        duplicate_prevention = True
                        details.append(f"✅ Found duplicate prevention: {pattern}")
                        break

        if not duplicate_prevention:
            score -= 30
            issues.append(SecurityIssue(
                category="double_charging",
                severity="high",
                title="No Duplicate Request Prevention",
                description="System lacks duplicate request detection mechanism",
                location="app/api/v1/endpoints/billing.py",
                remediation="Implement request deduplication:\n"
                          "- Cache recent payment requests (Redis)\n"
                          "- Check customer + amount + timestamp combinations\n"
                          "- Use exponential backoff for retries",
                cvss_score=6.5
            ))
            details.append(f"{YELLOW}⚠️  WARNING: No explicit duplicate prevention found{RESET}")

        # Check for rate limiting on payment endpoints
        print(f"\n{BLUE}Checking for rate limiting on payment endpoints...{RESET}")

        rate_limit_found = False
        rate_limit_files = [
            "app/core/rate_limiter.py",
            "app/core/api_rate_limiter.py",
            "app/middleware/rate_limiter.py"
        ]

        for file_path_str in rate_limit_files:
            file_path = project_root / file_path_str
            if file_path.exists():
                content = file_path.read_text()
                if "billing" in content.lower() or "payment" in content.lower():
                    rate_limit_found = True
                    details.append(f"✅ Rate limiting mentions payment/billing")
                    break

        if not rate_limit_found:
            score -= 20
            issues.append(SecurityIssue(
                category="double_charging",
                severity="medium",
                title="Missing Rate Limiting on Payment Endpoints",
                description="Payment endpoints may not have strict rate limiting",
                location="app/api/v1/endpoints/billing.py",
                remediation="Add aggressive rate limiting:\n"
                          "- 10 requests per minute per IP for payment endpoints\n"
                          "- 3 requests per second per customer for charges\n"
                          "- Use Redis-based rate limiting",
                cvss_score=5.5
            ))
            details.append(f"{YELLOW}⚠️  WARNING: Payment rate limiting not confirmed{RESET}")
        else:
            details.append(f"{GREEN}✅ Rate limiting detected{RESET}")

        # Check for client-side debounce in frontend
        print(f"\n{BLUE}Checking frontend for click debouncing...{RESET}")

        frontend_files = list((project_root / "frontend/src").rglob("*.tsx"))
        frontend_files.extend(list((project_root / "frontend/src").rglob("*.ts")))

        debounce_found = False
        debounce_patterns = [
            r"debounce",
            r"throttle",
            r"disabled.*\{.*loading",
            r"isSubmitting.*true",
            r"preventDefault"
        ]

        for file_path in frontend_files[:50]:  # Check first 50 files
            try:
                if "billing" in file_path.name.lower() or "payment" in file_path.name.lower():
                    content = file_path.read_text()
                    for pattern in debounce_patterns:
                        if re.search(pattern, content):
                            debounce_found = True
                            details.append(f"✅ Found {pattern} in {file_path.name}")
                            break
            except Exception:
                pass

        if not debounce_found:
            score -= 10
            details.append(f"{YELLOW}⚠️  INFO: Frontend click protection not confirmed{RESET}")
        else:
            details.append(f"{GREEN}✅ Frontend protection detected{RESET}")

        # Output results
        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details:
            print(f"   {detail}")

        print(f"\n{CYAN}Score: {score}/100{RESET}")

        return TestResult(
            test_name="Double-Charging Prevention",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # TEST 2: Refund Race Conditions
    # =========================================================================

    async def test_refund_race_conditions(self) -> TestResult:
        """Test for race condition vulnerabilities in refund processing"""
        self.print_test_header("TEST 2: Refund Race Conditions")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning for race condition protection in refund logic...{RESET}")

        # Check for atomic operations or transactions
        billing_service = project_root / "app/services/billing.py"
        if billing_service.exists():
            content = billing_service.read_text()

            # Look for refund-related functions
            refund_section = re.search(r'def.*refund.*\(|async def.*refund.*\(', content, re.IGNORECASE)
            if refund_section:
                details.append("✅ Refund function found")
            else:
                details.append(f"{YELLOW}⚠️  No dedicated refund function found{RESET}")

            # Check for database transaction usage
            transaction_patterns = [
                r"begin\(\)",
                r"commit\(\)",
                r"rollback\(\)",
                r"with.*transaction",
                r"@transactional",
                r"async with.*transaction"
            ]

            transaction_found = False
            for pattern in transaction_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    transaction_found = True
                    details.append(f"✅ Found transaction pattern: {pattern}")
                    break

            if not transaction_found:
                score -= 35
                issues.append(SecurityIssue(
                    category="race_condition",
                    severity="critical",
                    title="Refund Lacks Transaction Protection",
                    description="Refund operations not wrapped in atomic transactions",
                    location="app/services/billing.py",
                    remediation="Use database transactions for refunds:\n"
                              "- BEGIN TRANSACTION before refund\n"
                              "- Lock payment record\n"
                              "- Check refund status\n"
                              "- Process refund if not already refunded\n"
                              "- COMMIT or ROLLBACK on error",
                    cvss_score=8.2
                ))
                details.append(f"{RED}❌ CRITICAL: No transaction protection found{RESET}")

            # Check for refund state checks
            state_check_patterns = [
                r"if.*refund.*status",
                r"check.*refund.*state",
                r"refund.*already.*processed",
                r"status.*==.*refund"
            ]

            state_check_found = False
            for pattern in state_check_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    state_check_found = True
                    details.append(f"✅ Found state check pattern")
                    break

            if not state_check_found:
                score -= 25
                issues.append(SecurityIssue(
                    category="race_condition",
                    severity="high",
                    title="Missing Refund State Validation",
                    description="Refund doesn't check if payment was already refunded",
                    location="app/services/billing.py",
                    remediation="Add state validation before refund:\n"
                              "- Check payment.refund_status\n"
                              "- Use enum: PENDING, REFUNDED, PARTIALLY_REFUNDED\n"
                              "- Store refund_id after processing\n"
                              "- Atomic check-and-set operation",
                    cvss_score=7.0
                ))
                details.append(f"{RED}❌ HIGH: No refund state validation found{RESET}")

            # Check for idempotency in refunds
            refund_idempotency = False
            if "idempotency" in content.lower():
                refund_idempotency = True
                details.append("✅ Idempotency mentioned in billing service")

            if not refund_idempotency:
                score -= 20
                issues.append(SecurityIssue(
                    category="race_condition",
                    severity="high",
                    title="Refund Not Idempotent",
                    description="Multiple refund requests could process multiple times",
                    location="app/services/billing.py",
                    remediation="Make refunds idempotent:\n"
                              "- Generate unique refund_idempotency_key\n"
                              "- Store in database before Stripe call\n"
                              "- Check key exists before refunding\n"
                              "- Return cached result on duplicate",
                    cvss_score=7.5
                ))
                details.append(f"{YELLOW}⚠️  WARNING: Refund idempotency not confirmed{RESET}")

            # Check for webhook handling for refunds
            webhook_patterns = [
                r"charge\.refunded",
                r"refund\.updated",
                r"refund\.created",
                r"webhook.*refund"
            ]

            webhook_found = False
            for pattern in webhook_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    webhook_found = True
                    details.append(f"✅ Found webhook handling: {pattern}")
                    break

            if not webhook_found:
                score -= 20
                details.append(f"{YELLOW}⚠️  INFO: Refund webhook handling not confirmed{RESET}")

        # Output results
        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details:
            print(f"   {detail}")

        print(f"\n{CYAN}Score: {score}/100{RESET}")

        return TestResult(
            test_name="Refund Race Condition Protection",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # TEST 3: PCI Compliance Essentials
    # =========================================================================

    async def test_pci_compliance(self) -> TestResult:
        """Check for PCI DSS compliance essentials"""
        self.print_test_header("TEST 3: PCI Compliance Essentials")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Checking PCI DSS compliance requirements...{RESET}")

        # Check 1: Never store full card data
        print(f"\n{BLUE}✓ Requirement: Never store full card number, CVV, or PIN data{RESET}")

        card_data_patterns = [
            r"card_number.*=",
            r"cvv.*=",
            r"cvv2.*=",
            r"cvc.*=",
            r"pin.*=",
            r"track.*data",
            r"magnetic.*stripe"
        ]

        card_storage_found = False
        for py_file in project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in card_data_patterns:
                    # Exclude test files and migrations
                    if "test" not in str(py_file).lower() and "migration" not in str(py_file).lower():
                        if re.search(pattern, content, re.IGNORECASE):
                            # Check if it's just a variable assignment (could be legitimate)
                            if "=" in content:
                                card_storage_found = True
                                issues.append(SecurityIssue(
                                    category="pci_compliance",
                                    severity="critical",
                                    title="Potential Card Data Storage",
                                    description=f"Found potential card data storage pattern",
                                    location=str(py_file.relative_to(project_root)),
                                    remediation="NEVER store card data:\n"
                                              "- Use Stripe Elements / Stripe.js\n"
                                              "- Card data goes directly to Stripe\n"
                                              "- Only store payment_method_id (pm_xxx)\n"
                                              "- Use Stripe tokens for single-use",
                                    cvss_score=9.0
                                ))
                                details.append(f"{RED}❌ CRITICAL: {pattern} in {py_file.name}{RESET}")
                                break
            except Exception:
                pass

        if not card_storage_found:
            details.append(f"{GREEN}✅ No card data storage detected{RESET}")
        else:
            score -= 30

        # Check 2: Use HTTPS/TLS for all payment data
        print(f"\n{BLUE}✓ Requirement: HTTPS/TLS for payment data transmission{RESET}")

        tls_configured = False
        config_files = [
            "app/core/config.py",
            "app/core/config/settings.py",
            ".env",
            "nginx.conf"
        ]

        for config_file in config_files:
            file_path = project_root / config_file
            if file_path.exists():
                content = file_path.read_text()
                if re.search(r"https?://.*stripe", content, re.IGNORECASE):
                    tls_configured = True
                    details.append(f"✅ HTTPS configured in {config_file}")
                    break

                if "SSL" in content or "TLS" in content or "HTTPS" in content:
                    tls_configured = True
                    details.append(f"✅ SSL/TLS found in {config_file}")
                    break

        if not tls_configured:
            score -= 15
            details.append(f"{YELLOW}⚠️  WARNING: HTTPS/TLS configuration not confirmed{RESET}")

        # Check 3: Stripe integration (PCI SAQ A eligible)
        print(f"\n{BLUE}✓ Requirement: Use PCI-compliant payment processor (Stripe){RESET}")

        stripe_found = False
        stripe_patterns = [
            r"import stripe",
            r"from stripe",
            r"stripe\.api_key",
            r"stripe\.Customer",
            r"stripe\.PaymentIntent"
        ]

        for py_file in project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in stripe_patterns:
                    if re.search(pattern, content):
                        stripe_found = True
                        details.append(f"✅ Stripe integration found in {py_file.name}")
                        break
            except Exception:
                pass

        if stripe_found:
            details.append(f"{GREEN}✅ Using Stripe (PCI SAQ A eligible){RESET}")
        else:
            score -= 20
            details.append(f"{RED}❌ ERROR: No Stripe integration found{RESET}")

        # Check 4: No logging of sensitive card data
        print(f"\n{BLUE}✓ Requirement: Never log full card numbers or sensitive data{RESET}")

        logging_safe = True
        log_patterns = [
            r"logger\.(info|debug|warning|error).*card",
            r"print\(.*card",
            r"log\.(info|debug).*card"
        ]

        for py_file in project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in log_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's just a generic mention (like "card updated")
                        line_matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in line_matches:
                            line_content = content[max(0, match.start()-50):match.end()+50]
                            # Look for actual card number patterns
                            if re.search(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', line_content):
                                logging_safe = False
                                issues.append(SecurityIssue(
                                    category="pci_compliance",
                                    severity="critical",
                                    title="Potential Card Data in Logs",
                                    description="May be logging card numbers",
                                    location=str(py_file.relative_to(project_root)),
                                    remediation="Never log card data:\n"
                                              "- Mask card numbers: ****-****-****-1234\n"
                                              "- Never log CVV/CVC/PIN\n"
                                              "- Use Stripe's test mode for development",
                                    cvss_score=8.5
                                ))
                                details.append(f"{RED}❌ CRITICAL: Possible card logging in {py_file.name}{RESET}")
            except Exception:
                pass

        if logging_safe:
            details.append(f"{GREEN}✅ No card data logging detected{RESET}")
        else:
            score -= 25

        # Check 5: Webhook signature verification
        print(f"\n{BLUE}✓ Requirement: Verify webhook signatures{RESET}")

        webhook_verified = False
        webhook_patterns = [
            r"stripe\.Webhook\.construct_event",
            r"verify_webhook_signature",
            r"stripe-signature",
            r"webhook.*secret"
        ]

        for py_file in project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in webhook_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        webhook_verified = True
                        details.append(f"✅ Webhook verification in {py_file.name}")
                        break
            except Exception:
                pass

        if not webhook_verified:
            score -= 10
            details.append(f"{YELLOW}⚠️  WARNING: Webhook signature verification not confirmed{RESET}")

        # Output results
        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details:
            print(f"   {detail}")

        print(f"\n{CYAN}Score: {score}/100{RESET}")
        print(f"\n{BLUE}PCI DSS Compliance Level:{RESET}")
        if score >= 90:
            print(f"   {GREEN}✅ PCI SAQ A eligible (Stripe integration){RESET}")
        elif score >= 70:
            print(f"   {YELLOW}⚠️  PCI SAQ A-EP may be required{RESET}")
        else:
            print(f"   {RED}❌ PCI compliance gaps detected{RESET}")

        return TestResult(
            test_name="PCI Compliance Essentials",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # TEST 4: Card Data Leakage
    # =========================================================================

    async def test_card_data_leakage(self) -> TestResult:
        """Test for card data leakage in responses, logs, and storage"""
        self.print_test_header("TEST 4: Card Data Leakage")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning for potential card data leakage...{RESET}")

        # Check API responses for card data exposure
        print(f"\n{BLUE}Checking API response serialization...{RESET}")

        billing_endpoints = project_root / "app/api/v1/endpoints/billing.py"
        if billing_endpoints.exists():
            content = billing_endpoints.read_text()

            # Look for return statements that might include card data
            risky_returns = []
            return_patterns = [
                r"return\s*\{[^}]*customer[^}]*\}",
                r"return\s*\{[^}]*payment_method[^}]*\}",
                r"return\s*\{[^}]*card[^}]*\}"
            ]

            for pattern in return_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    return_statement = match.group(0)
                    # Check if it includes sensitive fields
                    if any(field in return_statement.lower() for field in
                           ['number', 'cvv', 'cvc', 'exp_month', 'exp_year', 'brand']):
                        risky_returns.append(return_statement[:100])

            if risky_returns:
                score -= 30
                issues.append(SecurityIssue(
                    category="data_leakage",
                    severity="high",
                    title="Card Data in API Responses",
                    description="API responses may include card details",
                    location="app/api/v1/endpoints/billing.py",
                    remediation="Never return card data in API:\n"
                              "- Only return payment_method_id\n"
                              "- Return last4 and brand only\n"
                              "- Mask all other data: ****-****-****-1234",
                    cvss_score=7.0
                ))
                details.append(f"{RED}❌ HIGH: Potential card data in responses{RESET}")
            else:
                details.append(f"{GREEN}✅ No obvious card data in responses{RESET}")

        # Check Pydantic schemas for card data fields
        print(f"\n{BLUE}Checking schemas for card data exposure...{RESET}")

        schema_files = list((project_root / "app/schemas").rglob("*.py"))
        card_exposure = False

        for schema_file in schema_files:
            try:
                content = schema_file.read_text()
                # Look for card-related fields
                if re.search(r"(card_number|cvv|cvc|pin|expiry)", content, re.IGNORECASE):
                    # Check if it's a legitimate model or just a field definition
                    if "class" in content or "BaseModel" in content:
                        card_exposure = True
                        details.append(f"{YELLOW}⚠️  Card fields in {schema_file.name}{RESET}")
            except Exception:
                pass

        if not card_exposure:
            details.append(f"{GREEN}✅ No card data schemas found{RESET}")

        # Check frontend for card data storage
        print(f"\n{BLUE}Checking frontend for card data handling...{RESET}")

        frontend_src = project_root / "frontend/src"
        risky_storage = []

        # Check localStorage/sessionStorage usage
        for ts_file in frontend_src.rglob("*.ts"):
            for tsx_file in frontend_src.rglob("*.tsx"):
                for js_file in frontend_src.rglob("*.js"):
                    for file in [ts_file, tsx_file, js_file]:
                        try:
                            content = file.read_text()
                            # Check for storage of payment-related data
                            if re.search(
                                r"(localStorage|sessionStorage)\.(setItem|setItem)\(.*[\"'].*(card|payment|stripe)",
                                content,
                                re.IGNORECASE
                            ):
                                risky_storage.append(file.name)
                        except Exception:
                            pass

        if risky_storage:
            score -= 25
            issues.append(SecurityIssue(
                category="data_leakage",
                severity="critical",
                title="Card Data in Browser Storage",
                description="Frontend may store card data in localStorage/sessionStorage",
                location="frontend/src",
                remediation="Never store card data in browser:\n"
                          "- Use Stripe Elements (tokenization)\n"
                          "- Only store payment_method_id temporarily\n"
                          "- Clear card data immediately after use\n"
                          "- Never store CVV/CVC under any circumstance",
                cvss_score=8.5
            ))
            details.append(f"{RED}❌ CRITICAL: Possible card data storage in frontend{RESET}")
        else:
            details.append(f"{GREEN}✅ No card storage in frontend detected{RESET}")

        # Check for card data in URLs
        print(f"\n{BLUE}Checking for card data in URL parameters...{RESET}")

        url_card_data = False
        frontend_files = list(frontend_src.rglob("*.tsx")) + list(frontend_src.rglob("*.ts"))

        for file in frontend_files[:100]:
            try:
                content = file.read_text()
                # Check if card data is passed in URLs
                if re.search(r"\?.*card\s*=", content, re.IGNORECASE):
                    url_card_data = True
                    details.append(f"{YELLOW}⚠️  Card data may be in URL: {file.name}{RESET}")
            except Exception:
                pass

        if url_card_data:
            score -= 20
            issues.append(SecurityIssue(
                category="data_leakage",
                severity="high",
                title="Card Data in URL Parameters",
                description="Card data may be passed in URL parameters",
                location="frontend/src",
                remediation="Never pass card data in URLs:\n"
                          "- URLs are logged in server logs\n"
                          "- URLs appear in browser history\n"
                          "- Use POST body with HTTPS\n"
                          "- Use Stripe Elements for tokenization",
                cvss_score=7.5
            ))
        else:
            details.append(f"{GREEN}✅ No card data in URLs detected{RESET}")

        # Check logs for card data patterns
        print(f"\n{BLUE}Checking log files for card data patterns...{RESET}")

        log_files = list(project_root.glob("*.log"))
        card_in_logs = False

        for log_file in log_files:
            try:
                content = log_file.read_text()[:10000]  # Check first 10KB
                # Look for potential card number patterns
                if re.search(r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", content):
                    card_in_logs = True
                    details.append(f"{RED}❌ CRITICAL: Card-like numbers in {log_file.name}{RESET}")
                    break
            except Exception:
                pass

        if not card_in_logs:
            details.append(f"{GREEN}✅ No card data in logs detected{RESET}")

        # Check environment files
        print(f"\n{BLUE}Checking environment files for card data...{RESET}")

        env_files = list(project_root.glob(".env*"))
        card_in_env = False

        for env_file in env_files:
            try:
                content = env_file.read_text()
                # Check for test card numbers (common in development)
                if re.search(r"4242.*4242.*4242.*4242", content):
                    card_in_env = True
                    details.append(f"{YELLOW}⚠️  Test card numbers in {env_file.name} (development){RESET}")
            except Exception:
                pass

        if not card_in_env:
            details.append(f"{GREEN}✅ No card data in environment files{RESET}")

        # Output results
        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details:
            print(f"   {detail}")

        print(f"\n{CYAN}Score: {score}/100{RESET}")

        return TestResult(
            test_name="Card Data Leakage Prevention",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # TEST 5: Subscription Cancellation Behavior
    # =========================================================================

    async def test_subscription_cancellation(self) -> TestResult:
        """Test subscription cancellation for proper behavior and security"""
        self.print_test_header("TEST 5: Subscription Cancellation Behavior")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Testing subscription cancellation logic...{RESET}")

        billing_service = project_root / "app/services/billing.py"
        billing_endpoints = project_root / "app/api/v1/endpoints/billing.py"

        if billing_service.exists():
            service_content = billing_service.read_text()

            # Check for cancellation function
            cancel_function = re.search(
                r'async def cancel_subscription\(|def cancel_subscription\(',
                service_content,
                re.IGNORECASE
            )

            if cancel_function:
                details.append("✅ Cancellation function found")
            else:
                score -= 20
                details.append(f"{RED}❌ ERROR: No cancellation function found{RESET}")

            # Check for ownership verification
            print(f"\n{BLUE}✓ Requirement: Verify user owns subscription before cancellation{RESET}")

            ownership_check = False
            ownership_patterns = [
                r"verify.*ownership",
                r"check.*subscription.*owner",
                r"user.*subscription.*id",
                r"customer_id.*=="
            ]

            for pattern in ownership_patterns:
                if re.search(pattern, service_content, re.IGNORECASE):
                    ownership_check = True
                    details.append(f"✅ Ownership verification pattern found")
                    break

            if billing_endpoints.exists():
                endpoint_content = billing_endpoints.read_text()
                if "current_user" in endpoint_content and "subscription_id" in endpoint_content:
                    ownership_check = True
                    details.append("✅ User authentication required for cancellation")

            if not ownership_check:
                score -= 25
                issues.append(SecurityIssue(
                    category="subscription_security",
                    severity="critical",
                    title="Missing Subscription Ownership Verification",
                    description="Cancellation doesn't verify user owns the subscription",
                    location="app/api/v1/endpoints/billing.py:cancel_subscription",
                    remediation="Add ownership verification:\n"
                              "- Query subscription by ID\n"
                              "- Verify customer_id == current_user.stripe_customer_id\n"
                              "- Or verify user.organization owns subscription\n"
                              "- Return 403 if ownership fails",
                    cvss_score=8.0
                ))
                details.append(f"{RED}❌ CRITICAL: No ownership verification found{RESET}")

            # Check for immediate vs period-end cancellation
            print(f"\n{BLUE}✓ Requirement: Support immediate and period-end cancellation{RESET}")

            immediate_cancel = False
            period_end_cancel = False

            if "cancel_at_period_end" in service_content:
                period_end_cancel = True
                details.append("✅ Period-end cancellation supported")

            if "immediate" in service_content.lower() and "cancel" in service_content.lower():
                immediate_cancel = True
                details.append("✅ Immediate cancellation option found")

            if not (immediate_cancel and period_end_cancel):
                score -= 15
                details.append(f"{YELLOW}⚠️  WARNING: Cancellation options incomplete{RESET}")

            # Check for refund policy on cancellation
            print(f"\n{BLUE}✓ Requirement: Clear refund policy on cancellation{RESET}")

            refund_policy = False
            refund_patterns = [
                r"refund.*policy",
                r"proration",
                r"refund.*remaining"
            ]

            for pattern in refund_patterns:
                if re.search(pattern, service_content, re.IGNORECASE):
                    refund_policy = True
                    details.append(f"✅ Refund policy handling found")
                    break

            if not refund_policy:
                score -= 15
                issues.append(SecurityIssue(
                    category="subscription_security",
                    severity="medium",
                    title="Unclear Refund Policy on Cancellation",
                    description="Cancellation behavior regarding refunds unclear",
                    location="app/services/billing.py:cancel_subscription",
                    remediation="Document and implement refund policy:\n"
                              "- Immediate cancellation: prorated refund?\n"
                              "- Period-end: no refund, access until period end\n"
                              "- Store refund_policy in subscription metadata\n"
                              "- Communicate policy to user before cancellation",
                    cvss_score=5.0
                ))
                details.append(f"{YELLOW}⚠️  WARNING: Refund policy not explicit{RESET}")

            # Check for audit logging
            print(f"\n{BLUE}✓ Requirement: Log all cancellation events{RESET}")

            audit_logging = False
            audit_patterns = [
                r"logger\.(info|warning)\.cancel",
                r"audit.*log",
                r"log.*cancellation"
            ]

            for pattern in audit_patterns:
                if re.search(pattern, service_content, re.IGNORECASE):
                    audit_logging = True
                    details.append(f"✅ Cancellation logging found")
                    break

            if not audit_logging:
                score -= 10
                details.append(f"{YELLOW}⚠️  INFO: Cancellation audit logging not confirmed{RESET}")

            # Check for webhook notification handling
            print(f"\n{BLUE}✓ Requirement: Handle cancellation webhooks from Stripe{RESET}")

            webhook_cancellation = False
            webhook_patterns = [
                r"customer\.subscription\.deleted",
                r"subscription\.canceled",
                r"webhook.*cancel"
            ]

            for pattern in webhook_patterns:
                if re.search(pattern, service_content, re.IGNORECASE):
                    webhook_cancellation = True
                    details.append(f"✅ Cancellation webhook handling found")
                    break

            if not webhook_cancellation:
                score -= 10
                details.append(f"{YELLOW}⚠️  INFO: Webhook cancellation handling not confirmed{RESET}")

        # Check for proper access revocation
        print(f"\n{BLUE}✓ Requirement: Revoke access on cancellation{RESET}")

        access_revocation = False
        access_patterns = [
            r"revoke.*access",
            r"downgrade.*plan",
            r"update.*subscription.*status",
            r"set.*tier.*free"
        ]

        if billing_service.exists():
            content = billing_service.read_text()
            for pattern in access_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    access_revocation = True
                    details.append(f"✅ Access revocation logic found")
                    break

        if not access_revocation:
            score -= 15
            issues.append(SecurityIssue(
                category="subscription_security",
                severity="high",
                title="Access Not Revoked After Cancellation",
                description="User features may not be disabled after cancellation",
                location="app/services/billing.py",
                remediation="Implement access revocation:\n"
                          "- Listen for subscription.deleted webhook\n"
                          "- Update user tier to 'free'\n"
                          "- Revoke premium features immediately\n"
                          "- Clear feature flags\n"
                          "- Send confirmation email",
                cvss_score=6.5
            ))
            details.append(f"{YELLOW}⚠️  WARNING: Access revocation not confirmed{RESET}")

        # Output results
        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details:
            print(f"   {detail}")

        print(f"\n{CYAN}Score: {score}/100{RESET}")

        return TestResult(
            test_name="Subscription Cancellation Security",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # Main Execution
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all payment security tests"""
        self.print_header("🔒 PAYMENT SECURITY TESTING SUITE")

        print(f"{BLUE}Started: {self.start_time.isoformat()}{RESET}")
        print(f"{BLUE}Project: {project_root}{RESET}\n")

        print(f"{YELLOW}Tests to run:{RESET}")
        print(f"   1. Double-Charging on Rapid Click")
        print(f"   2. Refund Race Conditions")
        print(f"   3. PCI Compliance Essentials")
        print(f"   4. Card Data Leakage")
        print(f"   5. Subscription Cancellation Behavior")

        # Run tests
        try:
            result1 = await self.test_double_charging()
            self.test_results.append(result1)

            result2 = await self.test_refund_race_conditions()
            self.test_results.append(result2)

            result3 = await self.test_pci_compliance()
            self.test_results.append(result3)

            result4 = await self.test_card_data_leakage()
            self.test_results.append(result4)

            result5 = await self.test_subscription_cancellation()
            self.test_results.append(result5)

        except Exception as e:
            print(f"{RED}Error running tests: {e}{RESET}")
            import traceback
            traceback.print_exc()

        # Generate summary
        self.print_summary()

        # Save detailed report
        self.save_report()

        return {
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r.passed),
            "failed": sum(1 for r in self.test_results if not r.passed),
            "average_score": sum(r.score for r in self.test_results) / len(self.test_results) if self.test_results else 0,
            "issues_found": sum(len(r.issues) for r in self.test_results),
            "critical_issues": sum(
                1 for r in self.test_results
                for i in r.issues
                if i.severity == "critical"
            )
        }

    def print_summary(self):
        """Print test summary"""
        self.print_header("📊 PAYMENT SECURITY SUMMARY")

        if not self.test_results:
            print(f"{RED}No test results available{RESET}")
            return

        # Calculate overall score
        total_score = sum(r.score for r in self.test_results) / len(self.test_results)

        print(f"\n{CYAN}Overall Security Score: {total_score:.1f}/100{RESET}\n")

        # Print individual test results
        for result in self.test_results:
            status = f"{GREEN}✅ PASS{RESET}" if result.passed else f"{RED}❌ FAIL{RESET}"
            print(f"{status} {result.test_name}: {result.score:.1f}/100")

            if result.issues:
                for issue in result.issues:
                    severity_color = {
                        "critical": RED,
                        "high": YELLOW,
                        "medium": YELLOW,
                        "low": BLUE
                    }.get(issue.severity, RESET)

                    print(f"   {severity_color}● {issue.severity.upper()}: {issue.title}{RESET}")

        # Print issue count
        total_issues = sum(len(r.issues) for r in self.test_results)
        critical_issues = sum(
            1 for r in self.test_results
            for i in r.issues
            if i.severity == "critical"
        )

        print(f"\n{YELLOW}Total Issues Found: {total_issues}{RESET}")
        if critical_issues > 0:
            print(f"{RED}Critical Issues: {critical_issues}{RESET}")

        # Print status
        if total_score >= 90:
            print(f"\n{GREEN}✅ EXCELLENT: Payment security is strong{RESET}")
        elif total_score >= 70:
            print(f"\n{YELLOW}⚠️  GOOD: Some improvements recommended{RESET}")
        else:
            print(f"\n{RED}❌ POOR: Critical payment security issues detected{RESET}")

        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{BLUE}Completed: {datetime.now().isoformat()}{RESET}")
        print(f"{BLUE}Duration: {elapsed:.2f} seconds{RESET}")

    def save_report(self):
        """Save detailed report to JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(project_root),
            "overall_score": sum(r.score for r in self.test_results) / len(self.test_results) if self.test_results else 0,
            "tests": [
                {
                    "name": r.test_name,
                    "passed": r.passed,
                    "score": r.score,
                    "issues": [
                        {
                            "category": i.category,
                            "severity": i.severity,
                            "title": i.title,
                            "description": i.description,
                            "location": i.location,
                            "remediation": i.remediation,
                            "cvss_score": i.cvss_score
                        }
                        for i in r.issues
                    ],
                    "details": r.details
                }
                for r in self.test_results
            ]
        }

        report_file = project_root / "payment_security_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n{BLUE}Detailed report saved to: {report_file}{RESET}")


async def main():
    """Main entry point"""
    tester = PaymentSecurityTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
