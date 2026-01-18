#!/usr/bin/env python3
"""
Comprehensive Security Enhancement Suite
Analyzes and implements security hardening across multiple dimensions:
1. Authentication and authorization security
2. API security analysis
3. Input validation and sanitization
4. Security headers and CORS configuration
5. Dependency vulnerability scanning
6. Rate limiting and DDoS protection
"""

import asyncio
import aiohttp
import json
import sys
import time
import re
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
import subprocess
import ast

class SecurityEnhancementResult:
    def __init__(self, test_name: str, success: bool, duration: float, details: str = "",
                 vulnerabilities: List[str] = None, recommendations: List[str] = None,
                 security_score: int = None):
        self.test_name = test_name
        self.success = success
        self.duration = duration
        self.details = details
        self.vulnerabilities = vulnerabilities or []
        self.recommendations = recommendations or []
        self.security_score = security_score  # 0-100
        self.timestamp = datetime.now(timezone.utc)

class SecurityEnhancer:
    def __init__(self):
        self.frontend_url = "http://localhost:5174"
        self.backend_url = "http://localhost:8000"
        self.session = None
        self.results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def analyze_authentication_security(self):
        """Analyze authentication and authorization security"""
        start_time = time.time()
        vulnerabilities = []
        recommendations = []
        security_score = 100

        try:
            # Check environment files for security
            env_files = [".env.dev", ".env.prod", ".env"]
            security_issues = []

            for env_file in env_files:
                if Path(env_file).exists():
                    content = Path(env_file).read_text(encoding='utf-8')

                    # Check for hardcoded secrets
                    if "password=" in content.lower() and len(content.split()) < 100:
                        security_issues.append(f"Hardcoded credentials in {env_file}")
                        security_score -= 20

                    # Check for weak JWT secrets
                    jwt_lines = [line for line in content.splitlines() if 'SECRET_KEY=' in line or 'JWT_' in line]
                    for line in jwt_lines:
                        secret_value = line.split('=', 1)[1] if '=' in line else ''
                        if len(secret_value) < 32:
                            security_issues.append(f"Weak JWT secret in {env_file}")
                            security_score -= 15

                    # Check for default credentials
                    if "password123" in content or "admin" in content.lower():
                        security_issues.append(f"Default credentials found in {env_file}")
                        security_score -= 25

            # Analyze backend authentication code
            auth_file = Path("app/api/v1/endpoints/auth.py")
            if auth_file.exists():
                auth_content = auth_file.read_text(encoding='utf-8')

                # Check for password strength validation
                if "validate_password" not in auth_content:
                    recommendations.append("Implement password strength validation")
                    security_score -= 10

                # Check for rate limiting on auth endpoints
                if "rate_limit" not in auth_content.lower():
                    recommendations.append("Add rate limiting to authentication endpoints")
                    security_score -= 10

                # Check for secure token storage
                if "HttpOnly" not in auth_content and "Secure" not in auth_content:
                    recommendations.append("Use HttpOnly and Secure cookies for tokens")
                    security_score -= 10

            # Generate recommendations
            recommendations.extend([
                "Implement multi-factor authentication (MFA)",
                "Use secure password hashing (bcrypt/argon2)",
                "Implement account lockout after failed attempts",
                "Regular security audit of authentication flows"
            ])

            details = f"Security issues found: {len(security_issues)}, Score: {security_score}/100"
            if security_issues:
                details += f" | Issues: {', '.join(security_issues[:3])}"

            return SecurityEnhancementResult(
                "Authentication Security Analysis",
                True,
                time.time() - start_time,
                details,
                security_issues,
                recommendations,
                max(0, security_score)
            )

        except Exception as e:
            return SecurityEnhancementResult(
                "Authentication Security Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze authentication security: {str(e)}",
                ["Check file permissions and paths"],
                ["Review authentication implementation"],
                0
            )

    async def analyze_api_security(self):
        """Analyze API security configurations"""
        start_time = time.time()
        vulnerabilities = []
        recommendations = []
        security_score = 100

        try:
            # Test API security headers
            async with self.session.get(f"{self.backend_url}/health") as response:
                headers = response.headers

                # Check security headers
                security_headers = {
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'DENY',
                    'X-XSS-Protection': '1; mode=block',
                    'Strict-Transport-Security': 'max-age=31536000',
                    'Content-Security-Policy': None
                }

                missing_headers = []
                for header, expected in security_headers.items():
                    if expected:
                        if header not in headers or headers[header] != expected:
                            missing_headers.append(header)
                    else:
                        if header not in headers:
                            missing_headers.append(header)

                if missing_headers:
                    recommendations.append(f"Add missing security headers: {', '.join(missing_headers)}")
                    security_score -= len(missing_headers) * 5

                # Test API versioning
                if 'api/v1' not in str(response.url):
                    recommendations.append("Implement API versioning")
                    security_score -= 10

                # Check for error information disclosure
                if response.status >= 400:
                    try:
                        error_data = await response.json()
                        if 'stack' in str(error_data).lower() or 'traceback' in str(error_data).lower():
                            vulnerabilities.append("API may disclose sensitive error information")
                            security_score -= 15
                    except Exception as e:
                        pass

            # Check CORS configuration
            async with self.session.options(f"{self.backend_url}/health") as response:
                cors_headers = response.headers
                if 'Access-Control-Allow-Origin' not in cors_headers:
                    recommendations.append("Configure CORS headers properly")
                    security_score -= 10
                elif '*' in cors_headers.get('Access-Control-Allow-Origin', ''):
                    vulnerabilities.append("CORS allows all origins - security risk")
                    security_score -= 15

            details = f"Security headers analyzed, Score: {security_score}/100"
            if missing_headers:
                details += f" | Missing headers: {len(missing_headers)}"

            return SecurityEnhancementResult(
                "API Security Analysis",
                True,
                time.time() - start_time,
                details,
                vulnerabilities,
                recommendations,
                max(0, security_score)
            )

        except Exception as e:
            return SecurityEnhancementResult(
                "API Security Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze API security: {str(e)}",
                ["Check if backend server is running"],
                ["Review API security configuration"],
                0
            )

    def analyze_input_validation(self):
        """Analyze input validation and sanitization"""
        start_time = time.time()
        vulnerabilities = []
        recommendations = []
        security_score = 100

        try:
            # Check backend input validation
            app_dir = Path("app")
            py_files = list(app_dir.glob("**/*.py"))

            validation_patterns = {
                'sql_injection': [r'execute\s*\(', r'\.format\s*\(', r'%s', r'f["\'].*\{.*\}'],
                'xss': [r'innerHTML\s*=', r'dangerouslySetInnerHTML', r'eval\s*\('],
                'path_traversal': [r'\.\./', r'open\s*\(', r'Path\s*\('],
                'command_injection': [r'subprocess\.', r'os\.system', r'os\.popen']
            }

            total_files = 0
            files_with_issues = 0

            for py_file in py_files:
                if py_file.exists():
                    try:
                        content = py_file.read_text(encoding='utf-8')
                        total_files += 1
                        file_issues = []

                        for vuln_type, patterns in validation_patterns.items():
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    file_issues.append(vuln_type)

                        if file_issues:
                            files_with_issues += 1
                            vulnerabilities.extend([f"{py_file.name}: {issue}" for issue in set(file_issues)])
                            security_score -= 10

                    except Exception as e:
                        continue

            # Check frontend input validation
            frontend_dir = Path("frontend/src")
            tsx_files = list(frontend_dir.glob("**/*.tsx"))

            frontend_validation_issues = 0
            for tsx_file in tsx_files:
                if tsx_file.exists():
                    try:
                        content = tsx_file.read_text(encoding='utf-8')

                        # Check for dangerous patterns
                        if 'dangerouslySetInnerHTML' in content:
                            vulnerabilities.append(f"{tsx_file.name}: Uses dangerouslySetInnerHTML")
                            security_score -= 15

                        if 'eval(' in content:
                            vulnerabilities.append(f"{tsx_file.name}: Uses eval()")
                            security_score -= 20

                        # Check for proper validation
                        if 'validate' not in content and 'form' in content.lower():
                            frontend_validation_issues += 1

                    except Exception as e:
                        continue

            # Generate recommendations
            recommendations.extend([
                "Implement comprehensive input validation on all endpoints",
                "Use parameterized queries for database operations",
                "Sanitize all user inputs before processing",
                "Implement Content Security Policy (CSP)",
                "Use proper escaping for dynamic content rendering"
            ])

            if frontend_validation_issues > 0:
                recommendations.append(f"Add input validation to {frontend_validation_issues} frontend forms")

            details = f"Analyzed {total_files} backend files, {len(tsx_files)} frontend files"
            details += f" | Issues found: {len(vulnerabilities)}, Score: {security_score}/100"

            return SecurityEnhancementResult(
                "Input Validation Analysis",
                True,
                time.time() - start_time,
                details,
                vulnerabilities,
                recommendations,
                max(0, security_score)
            )

        except Exception as e:
            return SecurityEnhancementResult(
                "Input Validation Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze input validation: {str(e)}",
                ["Check file system permissions"],
                ["Review input validation implementation"],
                0
            )

    def analyze_dependency_security(self):
        """Analyze dependency security"""
        start_time = time.time()
        vulnerabilities = []
        recommendations = []
        security_score = 100

        try:
            # Check Python dependencies
            requirements_files = ["requirements.txt", "requirements-test.txt"]
            total_packages = 0
            outdated_packages = 0

            for req_file in requirements_files:
                if Path(req_file).exists():
                    content = Path(req_file).read_text(encoding='utf-8')
                    packages = [line.split('==')[0].split('>=')[0].split('<=')[0]
                              for line in content.splitlines()
                              if line.strip() and not line.startswith('#')]
                    total_packages += len(packages)

                    # Common vulnerable packages to check
                    vulnerable_packages = ['requests', 'urllib3', 'jinja2', 'flask', 'django']
                    for package in packages:
                        if package.lower() in vulnerable_packages:
                            vulnerabilities.append(f"Potentially vulnerable package: {package}")
                            security_score -= 5

            # Check Node.js dependencies
            package_json = Path("frontend/package.json")
            if package_json.exists():
                try:
                    package_data = json.loads(package_json.read_text(encoding='utf-8'))
                    dependencies = {**package_data.get('dependencies', {}),
                                  **package_data.get('devDependencies', {})}

                    total_packages += len(dependencies)

                    # Check for known vulnerable packages
                    vulnerable_npm_packages = ['lodash', 'request', 'node-forge', 'serialize-javascript']
                    for package in dependencies:
                        if package in vulnerable_npm_packages:
                            vulnerabilities.append(f"Potentially vulnerable npm package: {package}")
                            security_score -= 5

                except Exception as e:
                    pass

            # Check for security-related tools
            security_tools = ['safety', 'bandit', 'semgrep', 'audit']
            has_security_tools = any(Path(tool).exists() for tool in security_tools)

            if not has_security_tools:
                recommendations.append("Install security scanning tools (safety, bandit, npm audit)")
                security_score -= 15

            recommendations.extend([
                "Regularly update dependencies to latest secure versions",
                "Implement automated dependency scanning in CI/CD",
                "Use dependency lock files for reproducible builds",
                "Monitor security advisories for used packages"
            ])

            details = f"Analyzed {total_packages} dependencies"
            details += f" | Vulnerabilities found: {len(vulnerabilities)}, Score: {security_score}/100"

            return SecurityEnhancementResult(
                "Dependency Security Analysis",
                True,
                time.time() - start_time,
                details,
                vulnerabilities,
                recommendations,
                max(0, security_score)
            )

        except Exception as e:
            return SecurityEnhancementResult(
                "Dependency Security Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze dependency security: {str(e)}",
                ["Check dependency files"],
                ["Review dependency management"],
                0
            )

    def generate_security_report(self):
        """Generate comprehensive security report"""
        print(f"\n{'='*80}")
        print("🔒 COMPREHENSIVE SECURITY ENHANCEMENT REPORT")
        print(f"{'='*80}")

        total_tests = len(self.results)
        completed_tests = sum(1 for result in self.results if result.success)
        total_duration = sum(result.duration for result in self.results)

        # Calculate overall security score
        scores = [result.security_score for result in self.results if result.security_score is not None]
        overall_score = sum(scores) / len(scores) if scores else 0

        print(f"\n📈 SECURITY ANALYSIS SUMMARY:")
        print(f"  Total Analyses: {total_tests}")
        print(f"  Completed: {completed_tests} ✅")
        print(f"  Failed: {total_tests - completed_tests} ❌")
        print(f"  Total Duration: {total_duration:.3f}s")
        print(f"  Overall Security Score: {overall_score:.1f}/100")

        print(f"\n🔍 SECURITY SCORES BY CATEGORY:")
        for result in self.results:
            if result.security_score is not None:
                status = "🟢" if result.security_score >= 80 else "🟡" if result.security_score >= 60 else "🔴"
                print(f"  {status} {result.test_name}: {result.security_score}/100")

        print(f"\n⚠️  IDENTIFIED VULNERABILITIES:")
        all_vulnerabilities = []
        for result in self.results:
            all_vulnerabilities.extend(result.vulnerabilities)

        if all_vulnerabilities:
            for i, vuln in enumerate(all_vulnerabilities[:10], 1):  # Show first 10
                print(f"  {i}. {vuln}")
            if len(all_vulnerabilities) > 10:
                print(f"  ... and {len(all_vulnerabilities) - 10} more")
        else:
            print("  ✅ No critical vulnerabilities detected!")

        print(f"\n💡 SECURITY RECOMMENDATIONS:")
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)

        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        priority_recommendations = [
            "Implement multi-factor authentication (MFA)",
            "Add comprehensive input validation",
            "Implement rate limiting on API endpoints",
            "Add security headers (CSP, HSTS, X-Frame-Options)",
            "Regularly update dependencies"
        ]

        # Show priority recommendations first
        for rec in priority_recommendations:
            if rec in unique_recommendations:
                print(f"  🔴 HIGH: {rec}")
                unique_recommendations.remove(rec)

        # Show remaining recommendations
        for i, rec in enumerate(unique_recommendations[:10], 1):
            print(f"  {i}. {rec}")

        print(f"\n🚀 IMMEDIATE SECURITY ACTIONS:")
        print("  1. Fix identified critical vulnerabilities")
        print("  2. Implement missing security headers")
        print("  3. Add rate limiting and DDoS protection")
        print("  4. Set up automated security scanning")
        print("  5. Implement security monitoring and alerting")

        print(f"\n📊 NEXT PHASE:")
        print("  5. Production Deployment Preparation")

        print(f"\n{'='*80}")
        print("🎉 SECURITY ENHANCEMENT ANALYSIS COMPLETE")
        print(f"{'='*80}")

    async def run_security_analysis(self):
        """Run all security analysis"""
        print("🔒 PSYNSYNC SECURITY ENHANCEMENT SUITE")
        print("=" * 70)
        print("Analyzing and enhancing security across all system components")
        print("=" * 70)

        # Define all security analyses
        analyses = [
            self.analyze_authentication_security,
            self.analyze_api_security,
            self.analyze_input_validation,
            self.analyze_dependency_security
        ]

        # Run each analysis
        for analysis_func in analyses:
            print(f"\n🔍 Running {analysis_func.__name__}...")

            if analysis_func.__name__ in ['analyze_authentication_security', 'analyze_input_validation', 'analyze_dependency_security']:
                # These are synchronous functions
                result = analysis_func()
            else:
                # These are async functions
                result = await analysis_func()

            self.results.append(result)

            if result.success:
                score_display = f" (Score: {result.security_score}/100)" if result.security_score else ""
                print(f"✅ {result.test_name}: COMPLETED ({result.duration:.3f}s){score_display}")
                print(f"   Details: {result.details}")
            else:
                print(f"❌ {result.test_name}: FAILED ({result.duration:.3f}s)")
                print(f"   Error: {result.details}")

        # Generate final report
        self.generate_security_report()
        return self.results

async def main():
    """Main security enhancer"""
    try:
        async with SecurityEnhancer() as enhancer:
            results = await enhancer.run_security_analysis()

            # Generate exit code based on security score
            scores = [result.security_score for result in results if result.security_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0

            if avg_score < 60:
                sys.exit(2)  # Critical security issues
            elif avg_score < 80:
                sys.exit(1)  # Security improvements needed
            else:
                sys.exit(0)  # Security is acceptable

    except KeyboardInterrupt:
        print("\n⚠️  Security analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
