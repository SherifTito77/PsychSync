#!/usr/bin/env python3
"""
Pre-Production Security Audit Script for PsychSync
Validates all critical security measures before production deployment
"""

import asyncio
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import asyncpg
import requests


class SecurityAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        self.status = {
            'security': 'UNKNOWN',
            'database': 'UNKNOWN',
            'performance': 'UNKNOWN',
            'infrastructure': 'UNKNOWN'
        }

    def log_issue(self, severity: str, category: str, message: str, fix: str = None):
        """Log a security issue"""
        self.issues.append({
            'severity': severity,
            'category': category,
            'message': message,
            'fix': fix
        })
        print(f"❌ [{severity}] {category}: {message}")
        if fix:
            print(f"   Fix: {fix}")

    def log_warning(self, category: str, message: str, recommendation: str = None):
        """Log a warning"""
        self.warnings.append({
            'category': category,
            'message': message,
            'recommendation': recommendation
        })
        print(f"⚠️  {category}: {message}")
        if recommendation:
            print(f"   Recommendation: {recommendation}")

    def log_pass(self, category: str, message: str):
        """Log a passed check"""
        self.passed.append({
            'category': category,
            'message': message
        })
        print(f"✅ {category}: {message}")

    def check_secret_strength(self):
        """Check if SECRET_KEY is strong"""
        print("\n🔐 Checking Secret Configuration...")

        try:
            from app.core.config import settings
        except Exception as e:
            self.log_issue('CRITICAL', 'Secrets', f"Cannot load config: {e}")
            return

        # Check SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', None)
        if not secret_key:
            self.log_issue('CRITICAL', 'Secrets', 'SECRET_KEY not configured',
                           'Set SECRET_KEY in environment variables (32+ chars)')
            return

        # Check length
        if len(secret_key) < 32:
            self.log_issue('CRITICAL', 'Secrets', f'SECRET_KEY too weak: {len(secret_key)} chars',
                           'Use: python -c "import secrets; print(secrets.token_urlsafe(32))"')
            return

        # Check for default/common secrets
        weak_secrets = [
            'dev-secret-key',
            'secret', 'password', 'test',
            '123456789', 'abcd1234',
            'your-secret-key-here',
            'changeme',
            'default',
            'insecure'
        ]

        if secret_key.lower() in [s.lower() for s in weak_secrets]:
            self.log_issue('CRITICAL', 'Secrets', 'Using default/weak SECRET_KEY',
                           'Generate a strong 32+ character key')
            return

        # Check entropy (basic check)
        try:
            # Basic entropy check
            unique_chars = len(set(secret_key))
            if unique_chars < 16:
                self.log_warning('Secrets', 'SECRET_KEY has low entropy',
                               'Use more random characters')
            else:
                self.log_pass('Secrets', f'SECRET_KEY is strong ({len(secret_key)} chars)')
        except Exception as e:
            self.log_warning('Secrets', 'Could not check SECRET_KEY entropy')

        # Check token expiration
        access_token_expire = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', None)
        if not access_token_expire:
            self.log_issue('HIGH', 'Secrets', 'ACCESS_TOKEN_EXPIRE_MINUTES not configured',
                           'Set to 15-30 minutes for security')
        elif access_token_expire > 60:
            self.log_warning('Secrets', f'Access tokens expire in {access_token_expire} minutes',
                           'Consider shorter expiration (15-30 min)')
        else:
            self.log_pass('Secrets', f'Access tokens expire in {access_token_expire} minutes')

    def check_code_for_secrets(self):
        """Scan code for hardcoded secrets"""
        print("\n🔍 Scanning Code for Secrets...")

        code_dirs = ['app/', 'scripts/', 'tests/']

        secret_patterns = [
            (r'(SECRET_KEY|PASSWORD|API_KEY|TOKEN|SECRET)[\s]*[:=][\s]*["\']([^"\']+)["\']', 'Hardcoded secret'),
            (r'(SECRET_KEY|PASSWORD|API_KEY|TOKEN|SECRET)[\s]*[:=][\s]*["\']([^"\']+?)["\']', 'Hardcoded secret'),
            (r'api_key\s*[:=]\s*[\'"]([a-zA-Z0-9_-]+)[\'"]', 'API key'),
            (r'password\s*[:=]\s*[\'"]([a-zA-Z0-9_-]+)[\'"]', 'Password'),
        ]

        found_secrets = []

        for code_dir in code_dirs:
            if not os.path.exists(code_dir):
                continue

            for file_path in Path(code_dir).rglob('*.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        line_num = 0
                        for pattern, description in secret_patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                found_secrets.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'type': description,
                                    'value': match.group(1),
                                    'context': content[max(0, match.start()-50):match.end()+50]
                                })
                except Exception as e:
                    self.log_warning('Code Scan', f"Could not read {file_path}: {e}")

        if found_secrets:
            for secret in found_secrets[:10]:  # Limit to 10 results
                self.log_issue('HIGH', 'Code Security',
                            f"Hardcoded secret in {secret['file']}:{secret['line']}",
                            f"Type: {secret['type']}, Value: {secret['value']}")
        else:
            self.log_pass('Code Security', 'No hardcoded secrets found in code')

    def check_git_history_secrets(self):
        """Check git history for committed secrets"""
        print("\n📝 Checking Git History for Secrets...")

        try:
            # Check for .env files in git
            result = subprocess.run(
                ['git', 'log', '--all', '--full-history', '--', '**/.env'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                if '.env' in result.stdout:
                    self.log_issue('CRITICAL', 'Git Security',
                                '.env file found in git history',
                                'Remove .env from git history with: git filter-branch')
                else:
                    self.log_pass('Git Security', 'No .env files found in git history')
        except Exception as e:
            self.log_warning('Git Security', f"Could not check git history: {e}")

        try:
            # Check for secrets in git diff
            result = subprocess.run(
                ['git', 'grep', '-i', '-n', '--text', '(key|secret|password|token)', '.'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                self.log_issue('HIGH', 'Git Security',
                            f"Potential secrets found in git diff",
                            'Review and secure before commit')
            else:
                self.log_pass('Git Security', 'No obvious secrets in tracked files')
        except Exception as e:
            self.log_warning('Git Security', f"Could not check git diff: {e}")

    def check_database_security(self):
        """Check database security configuration"""
        print("\n🗄️ Checking Database Security...")

        try:
            from app.core.config import settings
            database_url = getattr(settings, 'DATABASE_URL', '')

            if not database_url:
                self.log_issue('CRITICAL', 'Database', 'DATABASE_URL not configured',
                               'Set database connection string in environment')
                return

            # Parse database URL to check for insecure configurations
            if 'password=' in database_url.lower():
                self.log_issue('HIGH', 'Database', 'Password in database URL (consider using .pgpass)',
                               'Use connection string without password')

            if database_url.startswith('sqlite://'):
                self.log_issue('HIGH', 'Database', 'Using SQLite in production',
                               'Use PostgreSQL with SSL for production')
            elif database_url.startswith('postgresql://'):
                if 'sslmode=disable' in database_url.lower():
                    self.log_issue('CRITICAL', 'Database', 'SSL disabled for PostgreSQL',
                                   'Enable SSL for production database')
                elif 'sslmode=allow' in database_url.lower():
                    self.log_issue('HIGH', 'Database', 'SSL allow-verify in production',
                                  'Use require or prefer')
                elif 'sslmode=' not in database_url.lower():
                    self.log_warning('Database', 'No SSL mode specified for PostgreSQL',
                                  'Add ?sslmode=require to database URL')
                else:
                    self.log_pass('Database', 'PostgreSQL SSL configured')

            # Test database connection
            self._test_database_connection()

        except Exception as e:
            self.log_issue('HIGH', 'Database', f"Cannot check database security: {e}")

    def _test_database_connection(self):
        """Test database connection with proper security settings"""
        try:
            from app.core.config import settings

            # Parse database URL to get connection details
            db_url = settings.DATABASE_URL
            if not db_url:
                return

            # Parse URL to extract connection details
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(db_url)

            # Test connection with proper SSL settings
            import asyncpg
            conn = asyncio.run(asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
                sslmode='require'  # Enforce SSL
            ))

            # Test basic query
            result = asyncio.run(conn.fetch('SELECT 1'))
            asyncio.run(conn.close())

            self.log_pass('Database', 'Database connection successful with SSL')

        except Exception as e:
            self.log_issue('HIGH', 'Database', f"Database connection test failed: {e}")

    def check_api_security(self):
        """Check API security configuration"""
        print("\n🌐 Checking API Security...")

        # Test authentication endpoints
        auth_endpoints = [
            '/api/v1/auth/token',
            '/api/v1/auth/refresh',
            '/api/v1/users/me',
        ]

        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')

        for endpoint in auth_endpoints:
            try:
                # Test without authentication (should fail)
                response = requests.get(f"{base_url}{endpoint}")
                if response.status_code != 401:
                    self.log_issue('CRITICAL', 'API Security',
                                f"Endpoint {endpoint} not protected (status: {response.status_code})",
                                "Add authentication requirement")
                else:
                    self.log_pass('API Security', f"Endpoint {endpoint} properly protected")
            except Exception as e:
                self.log_warning('API Security', f"Could not test {endpoint}: {e}")

        # Test rate limiting
        self._test_rate_limiting()

    def _test_rate_limiting(self):
        """Test rate limiting on authentication endpoints"""
        print("\n⚡ Testing Rate Limiting...")

        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')

        try:
            # Make multiple rapid login attempts
            responses = []
            for i in range(10):
                response = requests.post(
                    f"{base_url}/api/v1/auth/token",
                    data={
                        "username": "test@example.com",
                        "password": "wrongpassword"
                    }
                )
                responses.append(response)

            # Check if rate limiting kicks in
            status_codes = [r.status_code for r in responses]
            if status_codes.count(429) > 0:
                self.log_pass('API Security', f"Rate limiting active (429 responses after {status_codes.index(429)+1} attempts)")
            else:
                self.log_warning('API Security', 'No rate limiting detected on authentication endpoint',
                                     "Consider implementing rate limiting')

        except Exception as e:
            self.log_warning('API Security', f"Could not test rate limiting: {e}")

    def check_file_permissions(self):
        """Check critical file permissions"""
        print("\n🔒 Checking File Permissions...")

        critical_files = [
            '.env',
            'app/core/config.py',
            'app/core/security.py',
        ]

        for file_path in critical_files:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                mode = oct(stat_info.st_mode)[-3:]

                # Check permissions (should be 600 for sensitive files)
                if file_path == '.env':
                    if mode != '600':
                        self.log_issue('HIGH', 'File Security',
                                    f".env permissions too open: {mode}",
                                    "Run: chmod 600 .env")
                    else:
                        self.log_pass('File Security', f".env permissions correct: {mode}")
                else:
                    if mode not in ['644', '755']:
                        self.log_warning('File Security',
                                      f"{file_path} permissions: {mode}",
                                      "Consider reviewing file permissions")

    def check_ssl_certificates(self):
        """Check SSL certificate configuration"""
        print("\n🔒 Checking SSL Certificates...")

        try:
            domain = os.getenv('DOMAIN', 'localhost:8000')
            if domain.startswith('localhost'):
                self.log_warning('SSL', 'Running on localhost - SSL not applicable')
                return

            # Check certificate expiration
            import ssl
            import socket
            from datetime import datetime

            context = ssl.create_default_context()

            with socket.create_connection((domain, 443)) as sock:
                with context.wrap_socket(sock) as ssock:
                    ssock.settimeout(10)
                    cert = ssock.getpeercert(True)

                    if cert:
                        expiration_date = cert.getNotAfter()
                        days_until_expiration = (expiration_date - datetime.now()).days

                        if days_until_expiration < 30:
                            self.log_issue('HIGH', 'SSL',
                                        f"SSL certificate expires in {days_until_expiration} days",
                                        "Renew certificate before expiration")
                        elif days_until_expiration < 90:
                            self.log_warning('SSL',
                                            f"SSL certificate expires in {days_until_expiration} days",
                                            "Schedule certificate renewal")
                        else:
                            self.log_pass('SSL', f"SSL certificate valid for {days_until_expiration} days")

                        # Check certificate strength
                        cert_subject = cert.get_subject()
                        cert_issuer = cert.get_issuer()

                        print(f"   Certificate info:")
                        print(f"   Subject: {cert_subject}")
                        print(f"   Issuer: {cert_issuer}")
                        print(f"   Expires: {expiration_date}")
                    else:
                        self.log_issue('HIGH', 'SSL', 'No SSL certificate found',
                                       "Obtain valid SSL certificate')

        except Exception as e:
            self.log_issue('HIGH', 'SSL', f"Could not check SSL certificate: {e}")

    def check_dependency_vulnerabilities(self):
        """Check for known vulnerable dependencies"""
        print("\n📦 Checking Dependencies for Vulnerabilities...")

        try:
            # Check with safety
            result = subprocess.run(
                ['safety', 'check', '--file', 'requirements.txt'],
                capture_output=True,
                text=True
            )

            if 'WARNING: Unsafe dependencies found:' in result.stdout:
                self.log_issue('HIGH', 'Dependencies', 'Vulnerable dependencies found',
                               'Run: safety check --fix to auto-fix issues')

                # Parse vulnerable packages
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'WARNING:' in line or 'CRITICAL:' in line:
                        # Extract package name and CVE
                        if '->' in line:
                            package = line.split('->')[0].strip()
                            cve_info = line.split('->')[1].strip()
                            self.log_issue('HIGH', 'Dependencies',
                                        f"Vulnerable dependency: {package} - {cve_info}")
            elif result.returncode == 0:
                self.log_pass('Dependencies', 'No security vulnerabilities in dependencies')
        else:
            self.log_warning('Dependencies', 'Safety tool not installed',
                                 'Install with: pip install safety')

        except Exception as e:
            self.log_warning('Dependencies', f"Could not check dependencies: {e}")

    def check_https_redirects(self):
        """Check HTTP to HTTPS redirects"""
        print("\n🔄 Checking HTTPS Redirects...")

        try:
            domain = os.getenv('DOMAIN', 'psychsync.com')

            # Test HTTP redirect to HTTPS
            response = requests.get(f"http://{domain}", allow_redirects=False)

            if response.status_code == 301 or response.status_code == 302:
                location = response.headers.get('location', '')
                if location.startswith('https://'):
                    self.log_pass('HTTPS', f"HTTP redirects to HTTPS: {location}")
                else:
                    self.log_issue('HIGH', 'HTTPS', f"HTTP redirects to HTTP: {location}",
                                   "Ensure all redirects use HTTPS")
            else:
                self.log_issue('HIGH', 'HTTPS', f"HTTP site accessible (no redirect)",
                               "Enforce HTTPS with 301 redirect")

        except Exception as e:
            self.log_warning('HTTPS', f"Could not test HTTPS redirect: {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate final security audit report"""

        # Calculate overall status
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']

        if critical_issues:
            overall_status = 'CRITICAL - DO NOT DEPLOY'
        elif high_issues:
            overall_status = 'HIGH - FIX BEFORE DEPLOY'
        elif self.warnings:
            overall_status = 'WARNING - RECOMMENDED FIXES'
        else:
            overall_status = 'PASSED - READY FOR PRODUCTION'

        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'warnings': len(self.warnings),
                'passed_checks': len(self.passed)
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'passed_checks': self.passed,
            'status': self.status
        }

def main():
    """Main security audit execution"""
    print("🔒 PSYCHSYNC PRE-PRODUCTION SECURITY AUDIT")
    print("=" * 60)
    print("⚠️  CRITICAL: Fix all CRITICAL issues before production deployment")
    print("📋 Run this script in the project root directory")
    print("=" * 60)

    auditor = SecurityAuditor()

    # Run all security checks
    auditor.check_secret_strength()
    auditor.check_code_for_secrets()
    auditor.check_git_history_secrets()
    auditor.check_database_security()
    auditor.check_api_security()
    auditor.check_file_permissions()
    auditor.check_ssl_certificates()
    auditor.check_https_redirects()
    auditor.check_dependency_vulnerabilities()

    # Generate final report
    report = auditor.generate_report()

    print("\n" + "=" * 60)
    print("📊 SECURITY AUDIT REPORT")
    print("=" * 60)
    print(f"🚨 Overall Status: {report['overall_status']}")
    print(f"📊 Critical Issues: {report['summary']['critical_issues']}")
    print(f"⚠️ High Issues: {report['summary']['high_issues']}")
    print(f"ℹ️ Warnings: {report['summary']['warnings']}")
    print(f"✅ Passed Checks: {report['summary']['passed_checks']}")

    if report['issues']:
        print("\n🔧 ISSUES FOUND:")
        for issue in report['issues']:
            print(f"\n{issue['severity']} [{issue['category']}] {issue['message']}")
            if issue['fix']:
                print(f"   Fix: {issue['fix']}")

    if report['warnings']:
        print("\n⚠️ WARNINGS:")
        for warning in report['warnings']:
            print(f"⚠️ [{warning['category']}] {warning['message']}")
            if warning['recommendation']:
                print(f"   Recommendation: {warning['recommendation']}")

    if report['passed_checks']:
        print("\n✅ PASSED CHECKS:")
        for check in report['passed_checks']:
            print(f"✅ [{check['category']}] {check['message']}")

    # Save detailed report to file
    report_file = f"security_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📁 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    exit_code = 1 if report['issues'] else 0
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
