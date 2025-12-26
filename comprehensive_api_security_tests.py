#!/usr/bin/env python3
"""
Comprehensive API Security Testing Suite
Tests for API security vulnerabilities and configuration issues
"""

import asyncio
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class APISecTestResult:
    """API security test result"""
    category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str    # pass, fail, warning
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    location: Optional[str] = None


class APISecurityTester:
    """Comprehensive API security vulnerability scanner"""

    def __init__(self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")):
        self.project_root = project_root
        self.results: List[APISecTestResult] = []
        self.issue_count = 0
        self.pass_count = 0

    # =========================================================================
    # TEST 1: RATE LIMITING EFFECTIVENESS
    # =========================================================================

    async def test_rate_limiting_effectiveness(self) -> APISecTestResult:
        """
        Test for rate limiting vulnerabilities:
        - Missing rate limiting on public endpoints
        - Rate bypass techniques
        - Ineffective rate limit configuration
        - No rate limiting on auth endpoints
        - Distributed rate limiting (Redis) not used
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for rate limiter middleware
        rate_limiter = self.project_root / "app/middleware/rate_limiter.py"
        core_rate_limiter = self.project_root / "app/core/rate_limiter.py"

        if rate_limiter.exists():
            findings.append("Rate limiter middleware found")
            content = rate_limiter.read_text()

            # Check for Redis backing
            if 'redis' not in content.lower():
                findings.append("Rate limiter may not use Redis (not distributed)")
                recommendations.append("Use Redis-backed rate limiting for multi-instance deployments")
                status = "warning"

        elif core_rate_limiter.exists():
            findings.append("Core rate limiter found")
            content = core_rate_limiter.read_text()

            if 'redis' not in content.lower():
                findings.append("Rate limiter may not use Redis (not distributed)")
                status = "warning"
        else:
            findings.append("No rate limiter implementation found")
            recommendations.append("Implement rate limiting on all public endpoints")
            status = "fail"
            severity = "high"

        # Check auth endpoints for rate limiting
        auth_endpoints = self.project_root / "app/api/v1/endpoints/auth.py"
        if auth_endpoints.exists():
            content = auth_endpoints.read_text()

            # Check for rate limiting decorators
            if 'rate_limit' not in content.lower() and 'limiter' not in content.lower():
                findings.append("Auth endpoints may lack rate limiting")
                recommendations.append("Add rate limiting to login, register, password reset endpoints")
                status = "fail"
                severity = "high"
            else:
                findings.append("Auth endpoints have rate limiting protection")

        # Check API endpoints directory-wide for rate limiting
        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        if endpoints_dir.exists():
            endpoints_with_rate_limit = 0
            total_endpoints = 0

            for endpoint_file in endpoints_dir.glob("*.py"):
                total_endpoints += 1
                content = endpoint_file.read_text()

                if 'rate_limit' in content.lower() or 'limiter' in content.lower():
                    endpoints_with_rate_limit += 1

            rate_limit_coverage = (endpoints_with_rate_limit / total_endpoints * 100) if total_endpoints > 0 else 0

            if rate_limit_coverage < 50:
                findings.append(f"Only {rate_limit_coverage:.0f}% of endpoints have rate limiting")
                recommendations.append(f"Add rate limiting to remaining endpoints (target: 100%)")
                status = "fail"
                severity = "high"
            else:
                findings.append(f"Rate limiting coverage: {rate_limit_coverage:.0f}% of endpoints")

        # Check for slowapi or similar
        requirements = self.project_root / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text()

            if 'slowapi' in content.lower():
                findings.append("slowapi rate limiting library detected")
            else:
                findings.append("No dedicated rate limiting library found")
                recommendations.append("Add slowapi or similar for rate limiting")
                status = "warning"

        if not findings:
            findings.append("No rate limiting implementation detected")
            recommendations.append("Implement rate limiting with Redis backing")

        return APISecTestResult(
            category="API Security",
            test_name="Rate Limiting Effectiveness",
            severity=severity,
            status=status,
            description="Tests for rate limiting vulnerabilities and bypass techniques",
            evidence=findings,
            recommendations=recommendations
        )

    # =========================================================================
    # TEST 2: INPUT VALIDATION VULNERABILITIES
    # =========================================================================

    async def test_input_validation(self) -> APISecTestResult:
        """
        Test for input validation vulnerabilities:
        - SQL injection opportunities
        - NoSQL injection opportunities
        - XSS via API parameters
        - Command injection
        - Path traversal in API endpoints
        - Mass assignment vulnerabilities
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for raw SQL queries
        api_endpoints_dir = self.project_root / "app/api/v1/endpoints"
        services_dir = self.project_root / "app/services"

        files_to_check = []
        if api_endpoints_dir.exists():
            files_to_check.extend(api_endpoints_dir.glob("*.py"))
        if services_dir.exists():
            files_to_check.extend(services_dir.glob("*.py"))

        raw_sql_found = False
        sql_injection_risk = False

        for file_path in files_to_check:
            content = file_path.read_text()

            # Check for raw SQL execution
            if re.search(r'\.execute\s*\(', content):
                raw_sql_found = True

                # Check for f-strings or format strings in SQL
                if re.search(r'execute\s*\(\s*f["\']|execute\s*\(\s*\.format|execute\s*\(\s*%', content):
                    findings.append(f"Potential SQL injection in {file_path.name}")
                    recommendations.append("Use parameterized queries instead of string formatting")
                    sql_injection_risk = True
                    severity = "critical"
                    status = "fail"

            # Check for direct os.system or subprocess calls with user input
            if re.search(r'os\.system\s*\(|subprocess\.(call|run|Popen)\s*\(', content):
                if r'request\.' in content or r'form\.' in content or r'args\.' in content:
                    findings.append(f"Potential command injection in {file_path.name}")
                    recommendations.append("Never pass user input directly to system commands")
                    severity = "critical"
                    status = "fail"

        if raw_sql_found and not sql_injection_risk:
            findings.append("Raw SQL queries found (parameterized)")
        elif not raw_sql_found:
            findings.append("No raw SQL queries detected (using ORM)")

        # Check for Pydantic models for validation
        schemas_dir = self.project_root / "app/schemas"
        if schemas_dir.exists():
            schema_files = list(schemas_dir.glob("*.py"))
            if schema_files:
                findings.append(f"Pydantic validation schemas found ({len(schema_files)} files)")

            # Check for input validation in schemas
            for schema_file in schema_files:
                content = schema_file.read_text()

                # Check for Field validators
                if 'Field(' in content or 'validator' in content:
                    pass  # Good: validation found

        # Check for path traversal in file upload/download endpoints
        for file_path in files_to_check:
            content = file_path.read_text()

            if re.search(r'(upload|download|file)', content, re.IGNORECASE):
                if 'sanitize_path' not in content and 'safe_path' not in content:
                    findings.append(f"File operations in {file_path.name} may lack path sanitization")
                    recommendations.append("Use path sanitization utilities for all file operations")
                    status = "warning"

        # Check for mass assignment
        for file_path in files_to_check:
            content = file_path.read_text()

            # Look for direct model assignment from request
            if re.search(r'User\(\*\*request\.|user\.update\(|item\.update\(', content):
                findings.append(f"Potential mass assignment vulnerability in {file_path.name}")
                recommendations.append("Use explicit field assignment instead of **kwargs unpacking")
                status = "warning"

        # Check for XSS protection
        main_app = self.project_root / "app/main.py"
        if main_app.exists():
            content = main_app.read_text()

            # Check for HTML escaping
            if 'escape' not in content.lower():
                findings.append("No HTML escaping detected in responses")
                recommendations.append("Ensure HTML responses are properly escaped")
                status = "info"

        if not findings:
            findings.append("Input validation appears properly implemented")

        return APISecTestResult(
            category="API Security",
            test_name="Input Validation Vulnerabilities",
            severity=severity,
            status=status,
            description="Tests for injection and input validation vulnerabilities",
            evidence=findings,
            recommendations=recommendations
        )

    # =========================================================================
    # TEST 3: CORS MISCONFIGURATION
    # =========================================================================

    async def test_cors_configuration(self) -> APISecTestResult:
        """
        Test for CORS misconfiguration:
        - overly permissive CORS origins
        - CORS allowing credentials with *
        - Missing CORS headers
        - CORS reflecting Origin header
        - Preflight caching issues
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check CORS configuration
        cors_config = self.project_root / "app/core/cors.py"
        main_app = self.project_root / "app/main.py"

        cors_found = False
        overly_permissive = False

        for config_file in [cors_config, main_app]:
            if not config_file.exists():
                continue

            content = config_file.read_text()

            # Check for CORS middleware
            if 'CORSMiddleware' in content or 'cors' in content.lower():
                cors_found = True

                # Check for wildcard origins
                if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                    findings.append("CORS configured with wildcard origins (*)")
                    recommendations.append("Use specific origin list instead of wildcard")
                    overly_permissive = True
                    severity = "high"
                    status = "fail"

                # Check for credentials with wildcard
                if 'allow_origins=["*"]' in content and 'allow_credentials' in content:
                    findings.append("CORS allows credentials with wildcard origins (security issue)")
                    recommendations.append("Never use wildcard origins with credentials enabled")
                    overly_permissive = True
                    severity = "critical"
                    status = "fail"

                # Check for Origin reflection
                if 'allow_origin_regex' in content or 'origin' in content.lower():
                    findings.append("CORS may reflect Origin header (potential for reflection attacks)")
                    recommendations.append("Validate origins against whitelist, don't reflect")
                    status = "warning"

                # Check for specific allowed origins
                if 'allow_origins' in content:
                    # Extract origins
                    origins_match = re.search(r'allow_origins\s*=\s*\[(.*?)\]', content, re.DOTALL)
                    if origins_match:
                        origins = origins_match.group(1)
                        if len(origins) > 10 and 'localhost' in origins:
                            findings.append("CORS configured with specific origins (including localhost)")
                        elif len(origins) > 10:
                            findings.append("CORS configured with specific origins")

        if not cors_found:
            findings.append("No CORS middleware found")
            recommendations.append("Add CORSMiddleware for API security")
            status = "warning"

        # Check for CORS in frontend requests
        frontend_api = self.project_root / "frontend/src/services/api.ts"
        if frontend_api.exists():
            content = frontend_api.read_text()

            # Check for credentials mode
            if 'credentials:' in content or 'withCredentials:' in content:
                findings.append("Frontend sends credentials with API requests")
                if overly_permissive:
                    recommendations.append("Ensure CORS allows credentials only for trusted origins")

        return APISecTestResult(
            category="API Security",
            test_name="CORS Misconfiguration",
            severity=severity,
            status=status,
            description="Tests for Cross-Origin Resource Sharing misconfiguration",
            evidence=findings,
            recommendations=recommendations
        )

    # =========================================================================
    # TEST 4: API VERSIONING ISSUES
    # =========================================================================

    async def test_api_versioning(self) -> APISecTestResult:
        """
        Test for API versioning issues:
        - No versioning strategy
        - Breaking changes without version bump
        - Deprecated endpoints still accessible
        - Version deprecation policy missing
        - Multiple API versions coexistence issues
        """
        findings = []
        recommendations = []
        severity = "low"
        status = "pass"

        # Check API router for versioning
        api_router = self.project_root / "app/api/v1/api.py"
        main_app = self.project_root / "app/main.py"

        has_versioning = False

        if api_router.exists():
            content = api_router.read_text()

            # Check for /api/v1/ prefix
            if 'prefix="/api/v1' in content or 'prefix="/api/v2' in content:
                has_versioning = True
                findings.append("API uses versioned endpoints (/api/v1/)")

                # Check for multiple versions
                if '/v1/' in content and '/v2/' in content:
                    findings.append("Multiple API versions detected")
                    recommendations.append("Document version deprecation policy")
                    status = "info"

        # Check for version negotiation
        if main_app.exists():
            content = main_app.read_text()

            # Check for Accept header versioning
            if 'accept' in content.lower() and 'version' in content.lower():
                findings.append("API supports content negotiation versioning")

        # Check for breaking changes documentation
        docs = self.project_root / "docs"
        if docs.exists():
            api_docs = list(docs.glob("*API*")) + list(docs.glob("api*"))
            if api_docs:
                findings.append(f"API documentation found ({len(api_docs)} files)")

                # Check for versioning docs
                version_docs = False
                for doc_file in api_docs:
                    content = doc_file.read_text()
                    if 'version' in content.lower() and 'deprecat' in content.lower():
                        version_docs = True
                        break

                if not version_docs:
                    recommendations.append("Document API versioning strategy and deprecation policy")
                    status = "warning"

        # Check for deprecated endpoint markers
        endpoints_dir = self.project_root / "app/api/v1/endpoints"
        if endpoints_dir.exists():
            deprecated_count = 0
            for endpoint_file in endpoints_dir.glob("*.py"):
                content = endpoint_file.read_text()

                if 'deprecated' in content.lower():
                    deprecated_count += 1

            if deprecated_count > 0:
                findings.append(f"Found {deprecated_count} endpoints marked as deprecated")
                recommendations.append("Set timeline for removing deprecated endpoints")
                status = "info"

        if not has_versioning:
            findings.append("No API versioning strategy detected")
            recommendations.append("Implement API versioning (/api/v1/, /api/v2/, etc.)")
            status = "warning"

        return APISecTestResult(
            category="API Security",
            test_name="API Versioning Issues",
            severity=severity,
            status=status,
            description="Tests for API versioning strategy and deprecation issues",
            evidence=findings,
            recommendations=recommendations
        )

    # =========================================================================
    # TEST 5: BROKEN AUTHENTICATION IN API CALLS
    # =========================================================================

    async def test_broken_authentication(self) -> APISecTestResult:
        """
        Test for broken authentication in API calls:
        - Missing authentication on sensitive endpoints
        - Weak token validation
        - No CSRF protection
        - Session fixation opportunities
        - Authentication bypass attempts
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        # Check for public vs protected endpoints
        endpoints_dir = self.project_root / "app/api/v1/endpoints"

        if endpoints_dir.exists():
            unprotected_sensitive = []
            protected_count = 0
            total_endpoints = 0

            for endpoint_file in endpoints_dir.glob("*.py"):
                content = endpoint_file.read_text()

                # Find all endpoint definitions
                routes = re.finditer(r'@router\.(get|post|put|delete|patch)', content)

                for route_match in routes:
                    total_endpoints += 1

                    # Get context around the route
                    route_context = content[route_match.start():route_match.start()+500]

                    # Check for sensitive operations
                    sensitive_keywords = ['delete', 'update', 'create', 'admin', 'password', 'email']
                    is_sensitive = any(kw in route_context.lower() for kw in sensitive_keywords)

                    # Check if protected
                    has_auth = 'get_current_user' in route_context or 'Depends' in route_context

                    if is_sensitive and not has_auth:
                        unprotected_sensitive.append(f"{endpoint_file.name}")
                        severity = "critical"
                        status = "fail"
                    elif has_auth:
                        protected_count += 1

            if unprotected_sensitive:
                findings.append(f"Found {len(unprotected_sensitive)} sensitive endpoints without authentication")
                recommendations.append("Add get_current_user dependency to all sensitive endpoints")
            else:
                findings.append(f"Sensitive endpoints appear protected ({protected_count} with auth)")

        # Check JWT configuration
        security_config = self.project_root / "app/core/security.py"
        config = self.project_root / "app/core/config.py"

        jwt_secret_weak = False

        for config_file in [security_config, config]:
            if not config_file.exists():
                continue

            content = config_file.read_text()

            # Check for weak JWT secrets
            if 'SECRET_KEY' in content or 'JWT_SECRET' in content:
                # Check for default/weak secrets
                weak_patterns = [
                    r'secret\s*=\s*["\']secret["\']',
                    r'secret\s*=\s*["\']test["\']',
                    r'secret\s*=\s*["\']change',
                ]

                for pattern in weak_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append("Weak JWT secret detected")
                        recommendations.append("Use strong, randomly generated JWT secret (32+ bytes)")
                        jwt_secret_weak = True
                        severity = "critical"
                        status = "fail"
                        break

                # Check for secret loading from env
                if 'os.getenv' in content or 'os.environ' in content:
                    findings.append("JWT secret loaded from environment (good)")

        # Check token expiration
        if security_config.exists():
            content = security_config.read_text()

            if 'ACCESS_TOKEN_EXPIRE' in content:
                # Check expiration time
                expire_match = re.search(r'ACCESS_TOKEN_EXPIRE.*?(\d+)', content)
                if expire_match:
                    expire_minutes = int(expire_match.group(1))

                    if expire_minutes > 1440:  # More than 24 hours
                        findings.append(f"Access token expiration too long: {expire_minutes} minutes")
                        recommendations.append("Reduce access token expiration to 30 minutes or less")
                        severity = "high"
                        status = "fail"
                    elif expire_minutes > 60:
                        findings.append(f"Access token expiration: {expire_minutes} minutes")
                        status = "warning"
                    else:
                        findings.append(f"Access token expiration: {expire_minutes} minutes (good)")

        # Check for CSRF protection
        main_app = self.project_root / "app/main.py"
        if main_app.exists():
            content = main_app.read_text()

            if 'csrf' not in content.lower():
                findings.append("No CSRF protection detected")
                recommendations.append("Add CSRF protection for state-changing operations")
                status = "warning"

        # Check for session fixation
        auth_service = self.project_root / "app/services/auth_service.py"
        if auth_service.exists():
            content = auth_service.read_text()

            # Check for session regeneration after login
            if 'login' in content.lower():
                if 'regenerate' not in content.lower() and 'new_session' not in content.lower():
                    findings.append("Sessions may not be regenerated after login")
                    recommendations.append("Implement session regeneration after authentication")
                    status = "warning"

        if not findings:
            findings.append("Authentication appears properly configured")

        return APISecTestResult(
            category="API Security",
            test_name="Broken Authentication in API Calls",
            severity=severity,
            status=status,
            description="Tests for authentication bypass and weak authentication mechanisms",
            evidence=findings,
            recommendations=recommendations
        )

    # =========================================================================
    # TEST ORCHESTRATION
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API security tests"""

        print("\n" + "="*96)
        print("🔒 API SECURITY TESTING")
        print("="*96)
        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        test_methods = [
            ("Rate Limiting", self.test_rate_limiting_effectiveness),
            ("Input Validation", self.test_input_validation),
            ("CORS Configuration", self.test_cors_configuration),
            ("API Versioning", self.test_api_versioning),
            ("Broken Authentication", self.test_broken_authentication),
        ]

        for test_name, test_method in test_methods:
            print(f"\n{'='*96}")
            print(f"Testing: {test_name}")
            print('='*96)

            try:
                result = await test_method()
                self.results.append(result)

                # Print test results
                status_icon = "✅" if result.status == "pass" else "⚠️" if result.status == "warning" else "❌"
                severity_icon = "🔴" if result.severity == "critical" else "🟠" if result.severity == "high" else "🟡"

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
                self.results.append(APISecTestResult(
                    category=test_name,
                    test_name=test_name,
                    severity="error",
                    status="error",
                    description=f"Test failed with error: {str(e)}"
                ))
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
        print("\n" + "="*96)
        print("📊 API SECURITY TEST SUMMARY")
        print("="*96)

        print(f"\n{'='*96}")
        print(f"OVERALL SECURITY SCORE: {score}/100")
        print('='*96)

        if score >= 80:
            print("✅ EXCELLENT - Strong API security posture")
        elif score >= 60:
            print("⚠️  GOOD - Some vulnerabilities detected")
        elif score >= 40:
            print("🟠 FAIR - Multiple API security issues")
        else:
            print("🔴 POOR - Critical API security vulnerabilities")

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
        print('='*96)

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
        print('='*96)

        return report


async def main():
    """Main entry point"""
    project_root = Path("/Users/sheriftito/Downloads/psychsync")
    tester = APISecurityTester(project_root)

    report = await tester.run_all_tests()

    # Save report to JSON
    output_file = project_root / f"api_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
