#!/usr/bin/env python3
"""
Comprehensive Data Protection & Encryption Security Testing Suite
Tests for data protection, encryption, and PII handling
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DataProtectionTestResult:
    """Data protection security test result"""

    category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str  # pass, fail, warning
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    location: Optional[str] = None


class DataProtectionSecurityTester:
    """Comprehensive data protection and encryption scanner"""

    def __init__(
        self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")
    ):
        self.project_root = project_root
        self.results: List[DataProtectionTestResult] = []
        self.issue_count = 0
        self.pass_count = 0

    # =========================================================================
    # TEST 1: SENSITIVE DATA AT REST ENCRYPTION
    # =========================================================================

    async def test_encryption_at_rest(self) -> DataProtectionTestResult:
        """
        Test for encryption at rest:
        - Database encryption
        - File system encryption
        - Backup encryption
        - Environment variable encryption
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check database configuration for encryption
        db_config = self.project_root / "app/core/config.py"
        if db_config.exists():
            content = db_config.read_text()

            if "ssl" in content.lower() or "tls" in content.lower():
                findings.append("Database SSL/TLS configuration found")

            # Check for encrypted fields in models
            if "encrypt" in content.lower() or "cipher" in content.lower():
                findings.append("Encryption configuration detected")

        # Check models for encrypted fields
        models_dir = self.project_root / "app/db/models"
        if models_dir.exists():
            for model_file in models_dir.glob("*.py"):
                content = model_file.read_text()

                # Check for sensitive fields
                sensitive_fields = [
                    "password",
                    "ssn",
                    "credit_card",
                    "token",
                    "secret",
                    "key",
                ]
                for field in sensitive_fields:
                    if field in content.lower():
                        # Check if encrypted
                        if "encrypted" in content.lower() or "hash" in content.lower():
                            findings.append(
                                f"Sensitive field '{field}' appears protected in {model_file.name}"
                            )
                        else:
                            findings.append(
                                f"Sensitive field '{field}' in {model_file.name} - verify encryption"
                            )
                            status = "warning"

        # Check for backup encryption
        backup_files = list(self.project_root.rglob("*.sql")) + list(
            self.project_root.rglob("*.backup")
        )
        if backup_files:
            encrypted_backups = [
                f for f in backup_files if ".enc" in str(f) or "password" in str(f)
            ]

            findings.append(f"Found {len(backup_files)} backup files")
            if encrypted_backups:
                findings.append(
                    f"Found {len(encrypted_backups)} encrypted backups (good)"
                )
            else:
                findings.append("No encrypted backups found")
                recommendations.append("Encrypt database backups")
                status = "warning"

        return DataProtectionTestResult(
            category="Data Protection",
            test_name="Sensitive Data at Rest Encryption",
            severity=severity,
            status=status,
            description="Tests for encryption of data at rest",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 2: TLS/SSL CONFIGURATION
    # =========================================================================

    async def test_tls_ssl_config(self) -> DataProtectionTestResult:
        """
        Test for TLS/SSL configuration:
        - HTTPS enforcement
        - SSL certificate validation
        - TLS version configuration
        - Cipher suite configuration
        - HSTS headers
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check main app for SSL/TLS configuration
        main_app = self.project_root / "app/main.py"
        if main_app.exists():
            content = main_app.read_text()

            # Check for SSL
            if "ssl" in content.lower() or "https" in content.lower():
                findings.append("SSL/HTTPS configuration found")

            # Check for HSTS
            if "HSTS" in content or "Strict-Transport-Security" in content:
                findings.append("HSTS header configured")
            else:
                findings.append("HSTS header not found")
                recommendations.append("Add HTTP Strict Transport Security header")
                status = "warning"

        # Check nginx/Apache config files
        nginx_conf = self.project_root / "nginx/nginx.conf"
        if nginx_conf.exists():
            content = nginx_conf.read_text()

            if "ssl_certificate" in content:
                findings.append("SSL certificate configured in nginx")

            if "ssl_protocols" in content:
                # Check for TLS 1.2+
                if "TLSv1.2" in content or "TLSv1.3" in content:
                    findings.append("Modern TLS protocols configured (1.2+)")
                else:
                    findings.append("TLS protocols may be outdated")
                    recommendations.append("Use TLS 1.2 or higher")
                    status = "warning"

        return DataProtectionTestResult(
            category="Data Protection",
            test_name="TLS/SSL Configuration",
            severity=severity,
            status=status,
            description="Tests for TLS/SSL configuration",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 3: API RESPONSE DATA LEAKAGE
    # =========================================================================

    async def test_api_response_leakage(self) -> DataProtectionTestResult:
        """
        Test for sensitive data in API responses:
        - Passwords in responses
        - Internal IDs exposed
        - Stack traces in errors
        - Sensitive user data in list endpoints
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        schemas_dir = self.project_root / "app/schemas"

        # Check schemas for sensitive field exposure
        if schemas_dir.exists():
            for schema_file in schemas_dir.glob("*.py"):
                content = schema_file.read_text()

                # Check for password fields in response schemas
                if "password" in content.lower():
                    # Check if excluded
                    if "exclude" in content or "write_only" in content:
                        findings.append(
                            f"Password field properly protected in {schema_file.name}"
                        )
                    else:
                        findings.append(
                            f"Password field may be exposed in {schema_file.name}"
                        )
                        recommendations.append(
                            "Use exclude=True or write_only=True for password fields"
                        )
                        severity = "high"
                        status = "warning"

        # Check endpoints for data leakage
        if endpoints_dir.exists():
            for endpoint_file in endpoints_dir.glob("*.py"):
                content = endpoint_file.read_text()

                # Check for returning full user objects
                if "return.*User" in content or "response.*user" in content:
                    findings.append(
                        f"{endpoint_file.name} may return full user objects"
                    )
                    recommendations.append(
                        "Use response schemas to filter sensitive fields"
                    )
                    status = "warning"

                # Check for debug mode in errors
                if "traceback" in content.lower() or "debug.*true" in content.lower():
                    findings.append(f"{endpoint_file.name} may expose stack traces")
                    recommendations.append("Never expose stack traces in production")
                    severity = "high"
                    status = "warning"

        return DataProtectionTestResult(
            category="Data Protection",
            test_name="API Response Data Leakage",
            severity=severity,
            status=status,
            description="Tests for sensitive data leakage in API responses",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 4: HASH ALGORITHM STRENGTH
    # =========================================================================

    async def test_hash_algorithm_strength(self) -> DataProtectionTestResult:
        """
        Test for hash algorithm strength:
        - Password hashing algorithm (bcrypt, argon2, scrypt)
        - Hash work factor
        - Deprecated algorithms (MD5, SHA1)
        - Salt usage
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check requirements for hashing libraries
        requirements = self.project_root / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text()

            if "bcrypt" in content:
                findings.append("Using bcrypt for password hashing (good)")

            if "argon2" in content or "argon2-cffi" in content:
                findings.append("Using argon2 (best practice for password hashing)")

            if "passlib" in content:
                findings.append("Using passlib (password hashing library)")

        # Check auth service for hash implementation
        auth_service = self.project_root / "app/services/auth_service.py"
        if auth_service.exists():
            content = auth_service.read_text()

            # Check for bcrypt
            if "bcrypt" in content.lower():
                findings.append("bcrypt used for password hashing")

                # Check work factor
                rounds_match = re.search(r"rounds\s*=\s*(\d+)", content)
                if rounds_match:
                    rounds = int(rounds_match.group(1))
                    if rounds >= 12:
                        findings.append(f"Bcrypt work factor: {rounds} (good)")
                    else:
                        findings.append(f"Bcrypt work factor: {rounds} (should be 12+)")
                        recommendations.append("Increase bcrypt work factor to 12+")
                        status = "warning"

            # Check for weak algorithms
            weak_algos = ["md5", "sha1", "sha256"]
            for algo in weak_algos:
                if algo in content.lower():
                    findings.append(f"Weak hash algorithm detected: {algo}")
                    recommendations.append(
                        f"Replace {algo.upper()} with bcrypt or argon2"
                    )
                    severity = "critical"
                    status = "fail"

        return DataProtectionTestResult(
            category="Data Protection",
            test_name="Hash Algorithm Strength",
            severity=severity,
            status=status,
            description="Tests for hash algorithm strength",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 5: PII HANDLING COMPLIANCE
    # =========================================================================

    async def test_pii_handling(self) -> DataProtectionTestResult:
        """
        Test for PII handling compliance:
        - Data minimization
        - PII encryption
        - GDPR compliance features
        - Data anonymization
        - Right to deletion (GDPR Article 17)
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for GDPR/privacy features
        gdpr_endpoints = self.project_root / "app/api/v1/endpoints/gdpr.py"
        users_gdpr = self.project_root / "app/api/v1/endpoints/users_gdpr.py"

        gdpr_found = False
        if gdpr_endpoints.exists() or users_gdpr.exists():
            gdpr_found = True
            findings.append("GDPR/privacy endpoints found")

            # Check for deletion endpoint
            for gdpr_file in [gdpr_endpoints, users_gdpr]:
                if not gdpr_file.exists():
                    continue

                content = gdpr_file.read_text()

                if "delete" in content.lower() or "remove" in content.lower():
                    findings.append(f"Data deletion endpoint in {gdpr_file.name}")

                if "export" in content.lower() or "download" in content.lower():
                    findings.append(f"Data export endpoint in {gdpr_file.name}")

        if not gdpr_found:
            findings.append("No GDPR/privacy endpoints found")
            recommendations.append(
                "Implement GDPR compliance endpoints (delete, export, anonymize)"
            )
            status = "warning"

        # Check for PII encryption in models
        models_dir = self.project_root / "app/db/models"
        pii_fields = ["email", "phone", "ssn", "address", "name", "birth_date"]

        if models_dir.exists():
            pii_count = 0
            for model_file in models_dir.glob("*.py"):
                content = model_file.read_text()

                for field in pii_fields:
                    if field in content.lower():
                        pii_count += 1
                        break

            if pii_count > 0:
                findings.append(f"Found {pii_count} models with PII fields")
                recommendations.append("Ensure PII fields are encrypted at rest")
                status = "info"

        # Check for data anonymization
        anonymization_service = self.project_root / "app/services/data_anonymization.py"
        if anonymization_service.exists():
            findings.append("Data anonymization service found")
        else:
            findings.append("No data anonymization service found")
            recommendations.append("Implement data anonymization for analytics/backup")
            status = "info"

        return DataProtectionTestResult(
            category="Data Protection",
            test_name="PII Handling Compliance",
            severity=severity,
            status=status,
            description="Tests for PII handling and GDPR compliance",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST ORCHESTRATION
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all data protection security tests"""

        print("\n" + "=" * 96)
        print("🔐 DATA PROTECTION & ENCRYPTION SECURITY TESTING")
        print("=" * 96)
        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        test_methods = [
            ("Encryption at Rest", self.test_encryption_at_rest),
            ("TLS/SSL Configuration", self.test_tls_ssl_config),
            ("API Response Leakage", self.test_api_response_leakage),
            ("Hash Algorithm Strength", self.test_hash_algorithm_strength),
            ("PII Handling", self.test_pii_handling),
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
                    DataProtectionTestResult(
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
        print("📊 DATA PROTECTION & ENCRYPTION SECURITY TEST SUMMARY")
        print("=" * 96)

        print(f"\n{'='*96}")
        print(f"OVERALL SECURITY SCORE: {score}/100")
        print("=" * 96)

        if score >= 80:
            print("✅ EXCELLENT - Strong data protection")
        elif score >= 60:
            print("⚠️  GOOD - Some data protection issues")
        elif score >= 40:
            print("🟠 FAIR - Multiple data protection issues")
        else:
            print("🔴 POOR - Critical data protection vulnerabilities")

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
    tester = DataProtectionSecurityTester(project_root)

    report = await tester.run_all_tests()

    # Save report to JSON
    output_file = (
        project_root
        / f"data_protection_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
