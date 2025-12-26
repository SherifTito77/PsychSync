#!/usr/bin/env python3
"""
Security audit and vulnerability assessment for PsychSync
"""
import os
import sys
import re
import json
import hashlib
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class PsychSyncSecurityAuditor:
    """Comprehensive security audit class"""

    def __init__(self):
        self.security_findings = []
        self.project_root = Path(__file__).parent
        self.total_checks = 0
        self.passed_checks = 0

    def log_finding(self, category: str, severity: str, title: str, description: str, recommendation: str = ""):
        """Log security finding"""
        finding = {
            "category": category,
            "severity": severity,
            "title": title,
            "description": description,
            "recommendation": recommendation
        }
        self.security_findings.append(finding)

        severity_emoji = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "INFO": "ℹ️"
        }.get(severity, "⚪")

        print(f"{severity_emoji} {severity} - {title}")
        print(f"   {description}")
        if recommendation:
            print(f"   💡 Recommendation: {recommendation}")
        print()

    def check_secret_exposure(self):
        """Check for exposed secrets in code"""
        print("🔍 Checking for exposed secrets...")

        # Patterns for sensitive data
        secret_patterns = {
            "API Keys": {
                "patterns": [
                    r'(?i)api[_-]?key["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
                    r'(?i)secret[_-]?key["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
                    r'(?i)access[_-]?token["\']?\s*[:=]\s*["\'][^"\']{20,}["\']'
                ],
                "severity": "HIGH",
                "files": ['.py', '.yml', '.yaml', '.json', '.env*', '.md']
            },
            "Database URLs": {
                "patterns": [
                    r'(?i)password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
                    r'(?i)database[_-]?url["\']?\s*[:=]\s*["\'][^"\']{10,}["\']',
                    r'postgres://[^@]*:[^@]*@',
                    r'mysql://[^@]*:[^@]*@'
                ],
                "severity": "HIGH",
                "files": ['.py', '.yml', '.yaml', '.env*', '.conf']
            },
            "Private Keys": {
                "patterns": [
                    r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----',
                    r'-----BEGIN OPENSSH PRIVATE KEY-----'
                ],
                "severity": "CRITICAL",
                "files": ['.pem', '.key', '.ppk', '.p12']
            },
            "JWT Secrets": {
                "patterns": [
                    r'(?i)secret[_-]?key["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
                    r'(?i)jwt[_-]?secret["\']?\s*[:=]\s*["\'][^"\']{20,}["\']'
                ],
                "severity": "HIGH",
                "files": ['.py', '.env*', '.yml', '.yaml']
            }
        }

        secrets_found = 0
        for category, config in secret_patterns.items():
            print(f"  Checking {category}...")

            for pattern in config["patterns"]:
                for file_ext in config["files"]:
                    for file_path in self.project_root.rglob(f"*{file_ext}"):
                        if self._should_skip_file(file_path):
                            continue

                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            matches = re.findall(pattern, content)

                            if matches:
                                secrets_found += len(matches)
                                self.log_finding(
                                    "Secret Exposure",
                                    config["severity"],
                                    f"{category} in {file_path.relative_to(self.project_root)}",
                                    f"Found {len(matches)} potential {category.lower()}",
                                    "Remove secrets and use environment variables or secure storage"
                                )
                        except Exception as e:
                            continue

        if secrets_found == 0:
            print("  ✅ No exposed secrets found")
        else:
            print(f"  ❌ Found {secrets_found} potential secret exposures")

    def check_sql_injection_risks(self):
        """Check for potential SQL injection vulnerabilities"""
        print("🔍 Checking for SQL injection risks...")

        dangerous_patterns = [
            r'(?i)f"SELECT.*\{.*\}"',  # f-string SQL
            r'(?i)f"INSERT.*\{.*\}"',
            r'(?i)f"UPDATE.*\{.*\}"',
            r'(?i)f"DELETE.*\{.*\}"',
            r'(?i)execute\s*\(\s*["\'][^"\']*["\'].*\+',  # String concatenation in execute
            r'(?i)query\s*\(\s*["\'][^"\']*["\'].*\+'
        ]

        sql_files = list(self.project_root.rglob("*.py"))
        risks_found = 0

        for file_path in sql_files:
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                for pattern in dangerous_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        risks_found += len(matches)
                        self.log_finding(
                            "SQL Injection",
                            "HIGH",
                            f"Potential SQL injection in {file_path.relative_to(self.project_root)}",
                            f"Found {len(matches)} instances of unsafe SQL construction",
                            "Use parameterized queries or SQLAlchemy ORM instead"
                        )
            except Exception:
                continue

        if risks_found == 0:
            print("  ✅ No obvious SQL injection risks found")
        else:
            print(f"  ❌ Found {risks_found} potential SQL injection risks")

    def check_xss_risks(self):
        """Check for XSS vulnerabilities"""
        print("🔍 Checking for XSS vulnerabilities...")

        risky_patterns = [
            r'(?i)innerHTML\s*=\s*.*\+',  # Concatenation with innerHTML
            r'(?i)outerHTML\s*=\s*.*\+',
            r'(?i)document\.write\s*\(\s*.*\+',
            r'(?i)eval\s*\(\s*.*\+',
            r'render_string\s*\(\s*.*request',  # Flask/Jinja2 render_string with request data
        ]

        template_files = (
            list(self.project_root.rglob("*.html")) +
            list(self.project_root.rglob("*.jsx")) +
            list(self.project_root.rglob("*.tsx")) +
            list(self.project_root.rglob("*.js"))
        )

        risks_found = 0

        for file_path in template_files:
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                for pattern in risky_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        risks_found += len(matches)
                        self.log_finding(
                            "XSS Vulnerability",
                            "HIGH",
                            f"Potential XSS in {file_path.relative_to(self.project_root)}",
                            f"Found {len(matches)} instances of unsafe DOM manipulation",
                            "Use proper escaping and sanitized templating"
                        )
            except Exception:
                continue

        # Check Flask/Jinja2 templates
        jinja_files = list(self.project_root.rglob("*.jinja2")) + list(self.project_root.rglob("*.j2"))
        for file_path in jinja_files:
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                # Look for unsafe template rendering
                if re.search(r'\{\{\s*.*request\.\w+\s*\}\}', content):
                    risks_found += 1
                    self.log_finding(
                        "XSS Vulnerability",
                        "MEDIUM",
                        f"Unsafe template rendering in {file_path.relative_to(self.project_root)}",
                        "Template renders user input without escaping",
                        "Use |escape filter and validate input"
                    )
            except Exception:
                continue

        if risks_found == 0:
            print("  ✅ No obvious XSS vulnerabilities found")
        else:
            print(f"  ❌ Found {risks_found} potential XSS vulnerabilities")

    def check_dependency_vulnerabilities(self):
        """Check for vulnerable dependencies"""
        print("🔍 Checking for dependency vulnerabilities...")

        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            print("  ⚠️  No requirements.txt found")
            return

        try:
            requirements = requirements_file.read_text().strip().split('\n')
            vulnerable_packages = {
                'requests': '<2.20.0',  # Example vulnerability
                'urllib3': '<1.26.0',
                'cryptography': '<3.4.8',
                'pillow': '<8.2.0',
                'pyyaml': '<5.4.0'
            }

            vulnerabilities_found = 0

            for requirement in requirements:
                requirement = requirement.strip()
                if not requirement or requirement.startswith('#'):
                    continue

                package_match = re.match(r'^([a-zA-Z0-9_-]+)', requirement)
                if package_match:
                    package_name = package_match.group(1).lower()

                    if package_name in vulnerable_packages:
                        vulnerabilities_found += 1
                        self.log_finding(
                            "Vulnerable Dependency",
                            "MEDIUM",
                            f"Vulnerable package: {package_name}",
                            f"Package {package_name} may have known security vulnerabilities",
                            f"Update to latest stable version (>={vulnerable_packages[package_name]})"
                        )

            if vulnerabilities_found == 0:
                print("  ✅ No obviously vulnerable dependencies found")
            else:
                print(f"  ⚠️  Found {vulnerabilities_found} potentially vulnerable dependencies")

        except Exception as e:
            print(f"  ❌ Error checking dependencies: {e}")

    def check_file_permissions(self):
        """Check file permissions for security"""
        print("🔍 Checking file permissions...")

        permission_issues = []

        for file_path in self.project_root.rglob("*"):
            if self._should_skip_file(file_path):
                continue

            try:
                # Check world-readable files with sensitive content
                if file_path.is_file():
                    stat_info = file_path.stat()
                    mode = oct(stat_info.st_mode)[-3:]

                    # Files with sensitive patterns should not be world-readable
                    if mode[-1] in ['4', '5', '6', '7']:  # World readable
                        if file_path.suffix in ['.key', '.pem', '.p12', '.env']:
                            permission_issues.append(str(file_path.relative_to(self.project_root)))

                            self.log_finding(
                                "File Permissions",
                                "MEDIUM",
                                f"World-readable sensitive file: {file_path.name}",
                                f"File {file_path.relative_to(self.project_root)} has world-readable permissions",
                                "Restrict file permissions (chmod 600) and use proper access controls"
                            )
            except Exception:
                continue

        if not permission_issues:
            print("  ✅ No critical file permission issues found")
        else:
            print(f"  ❌ Found {len(permission_issues)} files with permission issues")

    def check_hardcoded_credentials(self):
        """Check for hardcoded credentials in environment files"""
        print("🔍 Checking for hardcoded credentials...")

        env_files = list(self.project_root.rglob(".env*")) + list(self.project_root.rglob("config*"))

        credential_patterns = [
            (r'password\s*=\s*[^#\n]+', "Password"),
            (r'secret[_-]?key\s*=\s*[^#\n]+', "Secret Key"),
            (r'api[_-]?key\s*=\s*[^#\n]+', "API Key"),
            (r'token\s*=\s*[^#\n]+', "Token"),
            (r'jwt[_-]?secret\s*=\s*[^#\n]+', "JWT Secret")
        ]

        credentials_found = 0

        for file_path in env_files:
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                for pattern, cred_type in credential_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)

                    for match in matches:
                        # Check if it's a default/placeholder value
                        if not self._is_default_value(match):
                            credentials_found += 1
                            self.log_finding(
                                "Hardcoded Credentials",
                                "HIGH",
                                f"Hardcoded {cred_type} in {file_path.relative_to(self.project_root)}",
                                "Hardcoded credentials found in environment file",
                                "Use proper secret management and avoid committing credentials"
                            )
            except Exception:
                continue

        if credentials_found == 0:
            print("  ✅ No hardcoded credentials found")
        else:
            print(f"  ❌ Found {credentials_found} hardcoded credentials")

    def check_debug_mode(self):
        """Check if debug mode is enabled in production"""
        print("🔍 Checking debug mode configuration...")

        config_files = [
            self.project_root / ".env",
            self.project_root / ".env.production",
            self.project_root / "app/core/config.py"
        ]

        debug_enabled = []

        for config_file in config_files:
            if not config_file.exists():
                continue

            try:
                content = config_file.read_text(encoding='utf-8', errors='ignore')

                # Check for debug settings
                debug_patterns = [
                    r'(?i)debug\s*=\s*true',
                    r'(?i)debug\s*=\s*1',
                    r'(?i)flask_debug\s*=\s*true'
                ]

                for pattern in debug_patterns:
                    if re.search(pattern, content):
                        debug_enabled.append(str(config_file.relative_to(self.project_root)))

                        self.log_finding(
                            "Debug Mode",
                            "MEDIUM",
                            f"Debug mode enabled in {config_file.name}",
                            "Debug mode is enabled which may expose sensitive information",
                            "Disable debug mode in production environments"
                        )
                        break
            except Exception:
                continue

        if not debug_enabled:
            print("  ✅ No debug mode configurations found")
        else:
            print(f"  ⚠️  Debug mode enabled in {len(debug_enabled)} configuration files")

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during security scan"""
        skip_patterns = [
            '.git',
            '.venv',
            '__pycache__',
            'node_modules',
            '.pytest_cache',
            '.mypy_cache',
            'dist',
            'build',
            'coverage'
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _is_default_value(self, value: str) -> bool:
        """Check if a credential value is a default/placeholder"""
        default_values = [
            'password',
            'secret',
            'key',
            'token',
            'change_me',
            'replace_this',
            'your_',
            'example.',
            'test_',
            'dev_',
            'localhost',
            '127.0.0.1',
            '0.0.0.0'
        ]

        return any(default in value.lower() for default in default_values)

    def run_comprehensive_audit(self):
        """Run all security checks"""
        print("🔒 PsychSync Security Audit & Vulnerability Assessment")
        print("=" * 60)
        print("Scanning for security vulnerabilities and compliance issues...")
        print()

        self.total_checks = 8
        checks_completed = 0

        # Run all security checks
        self.check_secret_exposure()
        checks_completed += 1

        self.check_sql_injection_risks()
        checks_completed += 1

        self.check_xss_risks()
        checks_completed += 1

        self.check_dependency_vulnerabilities()
        checks_completed += 1

        self.check_file_permissions()
        checks_completed += 1

        self.check_hardcoded_credentials()
        checks_completed += 1

        self.check_debug_mode()
        checks_completed += 1

        # Generate summary
        self.generate_security_report()

        return len(self.security_findings)

    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n" + "=" * 60)
        print("📊 SECURITY AUDIT REPORT")
        print("=" * 60)

        # Categorize findings
        findings_by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "INFO": []
        }

        for finding in self.security_findings:
            severity = finding.get("severity", "INFO")
            findings_by_severity[severity].append(finding)

        # Summary statistics
        total_findings = len(self.security_findings)
        critical_count = len(findings_by_severity["CRITICAL"])
        high_count = len(findings_by_severity["HIGH"])
        medium_count = len(findings_by_severity["MEDIUM"])
        low_count = len(findings_by_severity["LOW"])

        print(f"🔍 Total Security Findings: {total_findings}")
        print(f"🔴 Critical: {critical_count}")
        print(f"🟠 High: {high_count}")
        print(f"🟡 Medium: {medium_count}")
        print(f"🟢 Low: {low_count}")
        print()

        # Detailed findings by category
        if total_findings > 0:
            categories = set(f["category"] for f in self.security_findings)

            for category in sorted(categories):
                print(f"📂 {category.upper()}")
                print("-" * 40)

                category_findings = [f for f in self.security_findings if f["category"] == category]

                for finding in category_findings:
                    severity = finding.get("severity", "INFO")
                    title = finding.get("title", "Unknown")
                    description = finding.get("description", "No description")

                    severity_emoji = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡",
                        "LOW": "🟢",
                        "INFO": "ℹ️"
                    }.get(severity, "⚪")

                    print(f"  {severity_emoji} {title}")
                    print(f"     {description}")
                    if finding.get("recommendation"):
                        print(f"     💡 {finding['recommendation']}")
                    print()
        else:
            print("🎉 No security vulnerabilities found!")
            print("Your codebase appears to follow security best practices.")

        # Security recommendations
        print("🛡️ SECURITY RECOMMENDATIONS")
        print("-" * 40)

        if critical_count > 0 or high_count > 0:
            print("⚠️  IMMEDIATE ACTION REQUIRED:")
            print("   - Address all CRITICAL and HIGH severity findings")
            print("   - Rotate any exposed credentials")
            print("   - Implement proper input validation")
            print("   - Review access controls")
        elif medium_count > 0:
            print("📋 RECOMMENDED ACTIONS:")
            print("   - Address MEDIUM severity findings within 30 days")
            print("   - Update dependencies to secure versions")
            print("   - Review and update security policies")
        else:
            print("✅ EXCELLENT SECURITY POSTURE:")
            print("   - Continue following security best practices")
            print("   - Regular security scanning and updates")
            print("   - Security training for development team")

def main():
    """Main security audit function"""
    auditor = PsychSyncSecurityAuditor()
    total_findings = auditor.run_comprehensive_audit()

    # Exit with different codes based on findings
    if any(f.get("severity") == "CRITICAL" for f in auditor.security_findings):
        return 2  # Critical security issues
    elif any(f.get("severity") == "HIGH" for f in auditor.security_findings):
        return 1  # High severity issues
    else:
        return 0  # No critical issues

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)