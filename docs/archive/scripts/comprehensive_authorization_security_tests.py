#!/usr/bin/env python3
"""
Comprehensive Authorization & Access Control Security Testing Suite
Tests for authorization, access control, and privilege escalation vulnerabilities
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuthorizationTestResult:
    """Authorization security test result"""

    category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str  # pass, fail, warning
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    location: Optional[str] = None


class AuthorizationSecurityTester:
    """Comprehensive authorization and access control scanner"""

    def __init__(
        self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")
    ):
        self.project_root = project_root
        self.results: List[AuthorizationTestResult] = []
        self.issue_count = 0
        self.pass_count = 0

    # =========================================================================
    # TEST 1: PRIVILEGE ESCALATION (HORIZONTAL/VERTICAL)
    # =========================================================================

    async def test_privilege_escalation(self) -> AuthorizationTestResult:
        """
        Test for privilege escalation vulnerabilities:
        - Horizontal escalation (user-to-user)
        - Vertical escalation (user-to-admin)
        - Role manipulation
        - Permission bypass
        - Admin panel access
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        services_dir = self.project_root / "app/services"

        # Check for role change endpoints
        for directory in [endpoints_dir, services_dir]:
            if not directory.exists():
                continue

            for file_path in directory.glob("*.py"):
                content = file_path.read_text()

                # Check for role modification
                if re.search(
                    r"(change_role|update_role|set_role|make_admin|promote)",
                    content,
                    re.IGNORECASE,
                ):
                    # Check if properly protected
                    func_context = content

                    if "get_current_user" in func_context:
                        # Check for admin verification
                        if (
                            "is_admin" in func_context
                            or "admin" in func_context.lower()
                        ):
                            findings.append(
                                f"Role change found in {file_path.name} with admin check"
                            )
                        else:
                            findings.append(
                                f"Role change in {file_path.name} may lack admin verification"
                            )
                            recommendations.append(
                                "Verify admin role before allowing role changes"
                            )
                            severity = "high"
                            status = "fail"
                    else:
                        findings.append(
                            f"Role change in {file_path.name} lacks authentication"
                        )
                        recommendations.append(
                            "Add authentication to role change operations"
                        )
                        severity = "critical"
                        status = "fail"

                # Check for permission modification
                if re.search(
                    r"(add_permission|remove_permission|grant|revoke)",
                    content,
                    re.IGNORECASE,
                ):
                    if "is_admin" not in content:
                        findings.append(
                            f"Permission modification in {file_path.name} may lack admin check"
                        )
                        recommendations.append(
                            "Require admin verification for permission changes"
                        )
                        severity = "high"
                        status = "warning"

        # Check user model for role fields
        user_model = self.project_root / "app/db/models/user.py"
        if user_model.exists():
            content = user_model.read_text()

            if "role" in content.lower() or "is_admin" in content.lower():
                findings.append("User model has role/admin fields")

                # Check if role is mutable
                if "role = Column" in content or "is_admin = Column" in content:
                    # Check for validation
                    if "validator" not in content.lower():
                        findings.append(
                            "Role field may be directly mutable without validation"
                        )
                        recommendations.append(
                            "Add validators to prevent unauthorized role changes"
                        )
                        status = "warning"

        return AuthorizationTestResult(
            category="Authorization Security",
            test_name="Privilege Escalation",
            severity=severity,
            status=status,
            description="Tests for horizontal and vertical privilege escalation",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 2: INSECURE DIRECT OBJECT REFERENCES (IDOR)
    # =========================================================================

    async def test_idor(self) -> AuthorizationTestResult:
        """
        Test for IDOR vulnerabilities:
        - Sequential ID access
        - Missing ownership checks
        - Direct object access without authorization
        - Predictable identifiers
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        endpoints_dir = self.project_root / "app/api/v1/endpoints"

        if endpoints_dir.exists():
            idor_risk_count = 0

            for endpoint_file in endpoints_dir.glob("*.py"):
                content = endpoint_file.read_text()

                # Find routes with ID parameters
                routes = re.finditer(
                    r'@router\.(get|put|delete|patch)\s*\(\s*["\']([^"\']*\{[^}]*\}[^"\']*)["\']',
                    content,
                )

                for route_match in routes:
                    route_path = route_match.group(2)
                    route_method = route_match.group(1)

                    # Check if modifying/deleting operation
                    if route_method in ["put", "delete", "patch"]:
                        # Get function context
                        route_start = route_match.start()
                        route_context = content[route_start : route_start + 1000]

                        # Check for ownership/authorization check
                        has_ownership_check = (
                            "owner" in route_context.lower()
                            or "created_by" in route_context.lower()
                            or "user_id" in route_context.lower()
                            or "organization_id" in route_context.lower()
                        )

                        has_auth_check = "get_current_user" in route_context

                        if not has_auth_check:
                            findings.append(
                                f"{route_method} {route_path} - no authentication"
                            )
                            idor_risk_count += 1
                            severity = "critical"
                            status = "fail"
                        elif not has_ownership_check and "{id}" in route_path:
                            findings.append(
                                f"{route_method} {route_path} - may lack ownership check"
                            )
                            recommendations.append(
                                "Verify user owns resource before allowing access"
                            )
                            idor_risk_count += 1
                            if severity != "critical":
                                severity = "high"
                                status = "warning"

            if idor_risk_count > 0:
                findings.append(
                    f"Found {idor_risk_count} potential IDOR vulnerabilities"
                )
            else:
                findings.append("No obvious IDOR vulnerabilities detected")

        # Check for UUID vs integer IDs
        user_model = self.project_root / "app/db/models/user.py"
        if user_model.exists():
            content = user_model.read_text()

            if "UUID" in content:
                findings.append("Using UUIDs (harder to guess than sequential IDs)")
            elif "Integer" in content or "id = Column(Integer" in content:
                findings.append("Using integer IDs (predictable, consider UUIDs)")
                recommendations.append("Use UUIDs instead of sequential integer IDs")
                status = "warning"

        return AuthorizationTestResult(
            category="Authorization Security",
            test_name="Insecure Direct Object References (IDOR)",
            severity=severity,
            status=status,
            description="Tests for IDOR vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 3: API KEY LEAKAGE
    # =========================================================================

    async def test_api_key_leakage(self) -> AuthorizationTestResult:
        """
        Test for API key leakage:
        - Keys in logs
        - Keys in error messages
        - Keys in API responses
        - Hardcoded keys in code
        - Keys in version control
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for hardcoded API keys
        project_files = []

        # Check common directories
        for directory in ["app", "frontend/src", "config", "scripts"]:
            dir_path = self.project_root / directory
            if dir_path.exists():
                project_files.extend(dir_path.rglob("*.py"))
                project_files.extend(dir_path.rglob("*.js"))
                project_files.extend(dir_path.rglob("*.ts"))
                project_files.extend(dir_path.rglob("*.tsx"))
                project_files.extend(dir_path.rglob("*.env*"))

        key_patterns = {
            r'api[_-]?key\s*=\s*["\']([a-zA-Z0-9]{20,})["\']': "Hardcoded API key",
            r'secret[_-]?key\s*=\s*["\']([a-zA-Z0-9]{20,})["\']': "Hardcoded secret key",
            r'access[_-]?token\s*=\s*["\']([a-zA-Z0-9]{20,})["\']': "Hardcoded access token",
            r'aws[_-]?key[_-]?id\s*=\s*["\']([A-Z0-9]{20})["\']': "Hardcoded AWS key",
            r'stripe[_-]?secret\s*=\s*["\']sk_(test|live)_[a-zA-Z0-9]{20,}["\']': "Hardcoded Stripe key",
        }

        keys_found = 0

        for file_path in project_files[:100]:  # Limit scan
            try:
                content = file_path.read_text()

                for pattern, description in key_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip .env.example files
                        if ".env.example" not in str(file_path):
                            findings.append(f"{description} in {file_path.name}")
                            recommendations.append(
                                "Move secrets to environment variables"
                            )
                            severity = "critical"
                            status = "fail"
                            keys_found += 1
            except Exception:
                continue

        if keys_found == 0:
            findings.append("No hardcoded API keys found")

        # Check for keys in error responses
        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        if endpoints_dir.exists():
            for endpoint_file in endpoints_dir.glob("*.py"):
                content = endpoint_file.read_text()

                # Check if exceptions include sensitive data
                if "raise HTTPException" in content or "raise Exception" in content:
                    # Check if exception includes variables
                    if re.search(r"HTTPException.*?\{.*?\}", content):
                        findings.append(
                            f"Error responses may include variable data in {endpoint_file.name}"
                        )
                        recommendations.append(
                            "Sanitize error messages to prevent data leakage"
                        )
                        status = "warning"

        # Check logging for sensitive data
        for log_file in project_files[:50]:
            if not log_file.exists():
                continue

            try:
                content = log_file.read_text()

                # Check for logging of sensitive data
                if re.search(
                    r"logger\.(info|debug|error).*?(key|token|secret|password)",
                    content,
                    re.IGNORECASE,
                ):
                    findings.append(
                        f"Potential sensitive data logging in {log_file.name}"
                    )
                    recommendations.append("Never log API keys, tokens, or secrets")
                    if severity != "critical":
                        severity = "high"
                        status = "warning"
            except Exception:
                continue

        return AuthorizationTestResult(
            category="Authorization Security",
            test_name="API Key Leakage",
            severity=severity,
            status=status,
            description="Tests for API key leakage vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 4: MISSING AUTHORIZATION CHECKS
    # =========================================================================

    async def test_missing_authorization(self) -> AuthorizationTestResult:
        """
        Test for missing authorization checks:
        - Admin operations without admin check
        - Organization-level operations without org check
        - Team operations without team membership check
        - Resource operations without ownership check
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        endpoints_dir = self.project_root / "app/api/v1/endpoints"

        if endpoints_dir.exists():
            missing_auth_count = 0

            for endpoint_file in endpoints_dir.glob("*.py"):
                content = endpoint_file.read_text()

                # Find admin/sensitive operations
                admin_routes = re.finditer(
                    r'@router\.(post|put|delete)\s*\(\s*["\'][^"\']*(admin|delete|remove|ban|promote)[^"\']*["\']',
                    content,
                    re.IGNORECASE,
                )

                for route_match in admin_routes:
                    route_start = route_match.start()
                    route_context = content[route_start : route_start + 1500]

                    has_auth = "get_current_user" in route_context
                    has_admin_check = (
                        "is_admin" in route_context or "admin" in route_context.lower()
                    )

                    if not has_auth:
                        findings.append(
                            f"Admin operation without auth in {endpoint_file.name}"
                        )
                        missing_auth_count += 1
                        severity = "critical"
                        status = "fail"
                    elif not has_admin_check:
                        findings.append(
                            f"Admin operation without admin check in {endpoint_file.name}"
                        )
                        missing_auth_count += 1
                        severity = "high"
                        status = "warning"

                # Find organization-level operations
                org_routes = re.finditer(
                    r'@router\.(get|post|put|delete)\s*\(\s*["\'][^"\']*organization[^"\']*["\']',
                    content,
                    re.IGNORECASE,
                )

                for route_match in org_routes:
                    route_start = route_match.start()
                    route_context = content[route_start : route_start + 1500]

                    # Check for organization membership verification
                    has_org_check = (
                        "organization_id" in route_context
                        or "member" in route_context.lower()
                        or "belongs_to" in route_context.lower()
                    )

                    if not has_org_check and "get_current_user" in route_context:
                        findings.append(
                            f"Organization operation may lack org check in {endpoint_file.name}"
                        )
                        recommendations.append(
                            "Verify user belongs to organization before access"
                        )
                        missing_auth_count += 1
                        if severity != "critical" and severity != "high":
                            severity = "medium"
                            status = "warning"

            if missing_auth_count > 0:
                findings.append(
                    f"Found {missing_auth_count} operations with missing authorization"
                )
            else:
                findings.append("Authorization checks appear properly implemented")

        return AuthorizationTestResult(
            category="Authorization Security",
            test_name="Missing Authorization Checks",
            severity=severity,
            status=status,
            description="Tests for missing authorization checks",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 5: ADMIN PANEL ACCESS
    # =========================================================================

    async def test_admin_panel_access(self) -> AuthorizationTestResult:
        """
        Test for admin panel access controls:
        - Admin route protection
        - Admin dashboard access
        - Admin-only operations
        - Admin session security
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for admin endpoints
        admin_endpoints = self.project_root / "app/api/v1/endpoints/admin.py"
        endpoints_dir = self.project_root / "app/api/v1/endpoints"

        admin_files = []
        if admin_endpoints.exists():
            admin_files.append(admin_endpoints)

        if endpoints_dir.exists():
            admin_files.extend(endpoints_dir.glob("*admin*"))

        if admin_files:
            for admin_file in admin_files:
                content = admin_file.read_text()

                # Check for admin verification
                routes = re.finditer(r"@router\.(get|post|put|delete)", content)
                unprotected_admin_routes = 0

                for route_match in routes:
                    route_start = route_match.start()
                    route_context = content[route_start : route_start + 1000]

                    has_auth = "get_current_user" in route_context
                    has_admin_check = (
                        "is_admin" in route_context or "admin" in route_context.lower()
                    )

                    if not has_auth:
                        unprotected_admin_routes += 1
                        severity = "critical"
                        status = "fail"
                    elif not has_admin_check:
                        unprotected_admin_routes += 1
                        if severity != "critical":
                            severity = "high"
                            status = "warning"

                if unprotected_admin_routes > 0:
                    findings.append(
                        f"Found {unprotected_admin_routes} unprotected admin routes in {admin_file.name}"
                    )
                    recommendations.append(
                        "Add admin verification to all admin endpoints"
                    )
                else:
                    findings.append(
                        f"Admin routes in {admin_file.name} appear protected"
                    )

        # Check for MFA requirement for admin
        deps_file = self.project_root / "app/api/v1/deps.py"
        if deps_file.exists():
            content = deps_file.read_text()

            if "get_admin_user_with_mfa" in content:
                findings.append("MFA enforcement for admin operations detected")
            elif "get_admin_user" in content:
                findings.append("Admin endpoint exists but may not require MFA")
                recommendations.append("Require MFA for all admin operations")
                status = "warning"

        # Check for admin audit logging
        audit_log = self.project_root / "app/core/audit_logging.py"
        if audit_log.exists():
            content = audit_log.read_text()

            if "log_impersonation" in content or "admin" in content.lower():
                findings.append("Admin action audit logging detected")
            else:
                findings.append("No admin-specific audit logging found")
                recommendations.append("Log all admin actions for security monitoring")
                status = "info"

        return AuthorizationTestResult(
            category="Authorization Security",
            test_name="Admin Panel Access",
            severity=severity,
            status=status,
            description="Tests for admin panel access controls",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST ORCHESTRATION
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all authorization security tests"""

        print("\n" + "=" * 96)
        print("🔐 AUTHORIZATION & ACCESS CONTROL SECURITY TESTING")
        print("=" * 96)
        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        test_methods = [
            ("Privilege Escalation", self.test_privilege_escalation),
            ("IDOR", self.test_idor),
            ("API Key Leakage", self.test_api_key_leakage),
            ("Missing Authorization", self.test_missing_authorization),
            ("Admin Panel Access", self.test_admin_panel_access),
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
                    AuthorizationTestResult(
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
        print("📊 AUTHORIZATION & ACCESS CONTROL SECURITY TEST SUMMARY")
        print("=" * 96)

        print(f"\n{'='*96}")
        print(f"OVERALL SECURITY SCORE: {score}/100")
        print("=" * 96)

        if score >= 80:
            print("✅ EXCELLENT - Strong authorization controls")
        elif score >= 60:
            print("⚠️  GOOD - Some authorization issues")
        elif score >= 40:
            print("🟠 FAIR - Multiple authorization vulnerabilities")
        else:
            print("🔴 POOR - Critical authorization vulnerabilities")

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
    tester = AuthorizationSecurityTester(project_root)

    report = await tester.run_all_tests()

    # Save report to JSON
    output_file = (
        project_root
        / f"authorization_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
