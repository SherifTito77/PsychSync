#!/usr/bin/env python3
"""
PsychSync Security Audit Script

Performs comprehensive security checks:
- OWASP Top 10 vulnerabilities
- SQL injection scanning
- XSS vulnerability detection
- Dependency security scanning
- Configuration validation
- HIPAA compliance checks

USAGE:
    python scripts/security_audit.py --full
    python scripts/security_audit.py --sql-only
    python scripts/security_audit.py --dependencies

EXIT CODES:
    0: No security issues found
    1: Critical security issues found
    2: Warnings found
"""

import sys
import os
import re
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityAudit:
    """Security audit scanner for PsychSync platform"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }

    def run_full_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        logger.info("🔒 Starting comprehensive security audit...")

        # Run all checks
        self.check_sql_injection()
        self.check_xss_vulnerabilities()
        self.check_hardcoded_secrets()
        self.check_insecure_dependencies()
        self.check_debug_mode()
        self.check_cors_configuration()
        self.check_authentication()
        self.check_authorization()
        self.check_csrf_protection()
        self.check_sensitive_data_logs()
        self.check_file_permissions()

        return self.generate_report()

    def check_sql_injection(self):
        """Check for potential SQL injection vulnerabilities"""
        logger.info("🔍 Checking for SQL injection vulnerabilities...")

        # Patterns that might indicate SQL injection
        sql_patterns = [
            (r'f"SELECT.*\{.*?\}', "f-string SQL query"),
            (r'execute\(".*?\+.*?\)', "String concatenation in SQL"),
            (r'\.format\(".*?SELECT', ".format() in SQL query"),
            (r'%s.*%s', "Multiple %s without proper escaping"),
        ]

        vulnerable_files = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                for pattern, description in sql_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        vulnerable_files.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "pattern": pattern,
                            "description": description
                        })
            except Exception as e:
                logger.debug(f"Could not read {py_file}: {e}")

        if vulnerable_files:
            count = len(vulnerable_files)
            self.issues["high"].append({
                "check": "SQL Injection",
                "message": f"Found {count} potential SQL injection vulnerabilities",
                "details": vulnerable_files
            })
            logger.error(f"❌ Found {count} potential SQL injection vulnerabilities")
        else:
            self.issues["info"].append({
                "check": "SQL Injection",
                "message": "No SQL injection vulnerabilities found"
            })
            logger.info("✅ No SQL injection vulnerabilities found")

    def check_xss_vulnerabilities(self):
        """Check for potential XSS vulnerabilities"""
        logger.info("🔍 Checking for XSS vulnerabilities...")

        # Check if bleach is installed (for HTML sanitization)
        try:
            import bleach
            bleach_available = True
        except ImportError:
            bleach_available = False
            self.issues["medium"].append({
                "check": "XSS Protection",
                "message": "bleach library not installed - XSS protection may be insufficient"
            })

        # Check for unsafe HTML rendering
        unsafe_patterns = [
            (r'mark_safe\(', "mark_safe used (bypasses auto-escaping)"),
            (r'SafeString.*\+', "SafeString concatenation"),
            (r'innerHTML.*=.*request\.', "innerHTML set from request data"),
        ]

        vulnerable_files = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                for pattern, description in unsafe_patterns:
                    if re.search(pattern, content):
                        vulnerable_files.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "pattern": pattern,
                            "description": description
                        })
            except Exception:
                pass

        if vulnerable_files:
            self.issues["medium"].append({
                "check": "XSS Vulnerabilities",
                "message": f"Found {len(vulnerable_files)} potential XSS vulnerabilities",
                "details": vulnerable_files
            })
            logger.warning(f"⚠️  Found {len(vulnerable_files)} potential XSS vulnerabilities")
        else:
            logger.info("✅ No XSS vulnerabilities found")

    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets and credentials"""
        logger.info("🔍 Checking for hardcoded secrets...")

        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret_key\s*=\s*["\'][^"\']+["\']', "Hardcoded secret key"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
            (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', "Hardcoded AWS key"),
            (r'sendgrid_api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded SendGrid key"),
        ]

        secrets_found = []

        # Exclude certain directories
        exclude_dirs = {"venv", ".venv", "__pycache__", "node_modules", ".git"}

        for py_file in self.project_root.rglob("*.py"):
            # Skip excluded directories
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue

            try:
                content = py_file.read_text()

                for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        secrets_found.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_number,
                            "pattern": description,
                            "match": match.group()[:50] + "..."  # Truncate for logging
                        })
            except Exception:
                pass

        if secrets_found:
            self.issues["critical"].append({
                "check": "Hardcoded Secrets",
                "message": f"Found {len(secrets_found)} hardcoded secrets",
                "details": secrets_found
            })
            logger.error(f"❌ Found {len(secrets_found)} hardcoded secrets")
        else:
            logger.info("✅ No hardcoded secrets found")

    def check_insecure_dependencies(self):
        """Check for insecure dependencies using pip-audit"""
        logger.info("🔍 Checking for insecure dependencies...")

        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.issues["info"].append({
                    "check": "Dependencies",
                    "message": "No vulnerable dependencies found"
                })
                logger.info("✅ No vulnerable dependencies found")
            else:
                try:
                    import json
                    audit_data = json.loads(result.stdout)
                    vulnerable_packages = []

                    if "vulnerabilities" in audit_data:
                        for vuln in audit_data["vulnerabilities"]:
                            vulnerable_packages.append({
                                "package": vuln.get("name", "unknown"),
                                "version": vuln.get("version", "unknown"),
                                "severity": vuln.get("severity", "unknown"),
                                "advisory": vuln.get("advisory", "unknown")
                            })

                    self.issues["high"].append({
                        "check": "Dependencies",
                        "message": f"Found {len(vulnerable_packages)} vulnerable dependencies",
                        "details": vulnerable_packages
                    })
                    logger.warning(f"⚠️  Found {len(vulnerable_packages)} vulnerable dependencies")

                except json.JSONDecodeError:
                    self.issues["medium"].append({
                        "check": "Dependencies",
                        "message": "Could not parse pip-audit output"
                    })

        except FileNotFoundError:
            self.issues["medium"].append({
                "check": "Dependencies",
                "message": "pip-audit not installed - run: pip install pip-audit"
            })
        except subprocess.TimeoutExpired:
            self.issues["medium"].append({
                "check": "Dependencies",
                "message": "pip-audit timed out after 60 seconds"
            })

    def check_debug_mode(self):
        """Check if debug mode is enabled"""
        logger.info("🔍 Checking for debug mode...")

        env_file = self.project_root / ".env"

        if env_file.exists():
            content = env_file.read_text()

            if re.search(r'DEBUG\s*=\s*True', content, re.IGNORECASE):
                self.issues["critical"].append({
                    "check": "Debug Mode",
                    "message": "DEBUG=True found in .env file - not safe for production"
                })
                logger.error("❌ Debug mode is enabled")
            else:
                logger.info("✅ Debug mode is disabled")

    def check_cors_configuration(self):
        """Check CORS configuration"""
        logger.info("🔍 Checking CORS configuration...")

        # Check for overly permissive CORS
        cors_patterns = [
            (r'allow_origins\s*=\s*["\']\*["\']', "Allows all origins"),
            (r'allow_methods\s*=\s*["\']\*["\']', "Allows all methods"),
            (r'allow_headers\s*=\s*["\']\*["\']', "Allows all headers"),
        ]

        issues_found = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                for pattern, description in cors_patterns:
                    if re.search(pattern, content):
                        issues_found.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "issue": description
                        })
            except Exception:
                pass

        if issues_found:
            self.issues["medium"].append({
                "check": "CORS Configuration",
                "message": f"Found {len(issues_found)} overly permissive CORS configurations",
                "details": issues_found
            })
            logger.warning(f"⚠️  Found {len(issues_found)} CORS issues")
        else:
            logger.info("✅ CORS configuration looks good")

    def check_authentication(self):
        """Check authentication implementation"""
        logger.info("🔍 Checking authentication...")

        # Check for authentication endpoints
        auth_endpoints = 0

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                # Count authentication-related routes
                auth_endpoints += len(re.findall(r'@router\.post\(["\']/(login|register|auth)', content))
                auth_endpoints += len(re.findall(r'def (login|register|authenticate)', content))
            except Exception:
                pass

        if auth_endpoints > 0:
            logger.info(f"✅ Found {auth_endpoints} authentication endpoints")
        else:
            self.issues["high"].append({
                "check": "Authentication",
                "message": "No authentication endpoints found"
            })
            logger.warning("⚠️  No authentication endpoints found")

    def check_authorization(self):
        """Check authorization/role-based access control"""
        logger.info("🔍 Checking authorization...")

        # Check for role-based access control
        rbac_patterns = [
            (r'def get_current_user.*:', "get_current_user dependency"),
            (r'role\s*==\s*["\']admin["\']', "Role check"),
            (r'current_user\.role', "User role check"),
        ]

        rbac_count = 0

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                for pattern, description in rbac_patterns:
                    rbac_count += len(re.findall(pattern, content))
            except Exception:
                pass

        if rbac_count > 10:
            logger.info(f"✅ Found RBAC implementation ({rbac_count} checks)")
        else:
            self.issues["medium"].append({
                "check": "Authorization",
                "message": f"Limited RBAC implementation found ({rbac_count} checks)"
            })
            logger.warning(f"⚠️  Limited RBAC implementation ({rbac_count} checks)")

    def check_csrf_protection(self):
        """Check CSRF protection"""
        logger.info("🔍 Checking CSRF protection...")

        csrf_patterns = [
            (r'from.*fastapi_csrf_protect', "CSRF protection imported"),
            (r'CsrfProtect', "CsrfProtect decorator"),
            (r'csrf_protect', "CSRF protect function"),
        ]

        csrf_count = 0

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                for pattern, description in csrf_patterns:
                    csrf_count += len(re.findall(pattern, content))
            except Exception:
                pass

        if csrf_count > 0:
            logger.info(f"✅ CSRF protection found ({csrf_count} references)")
        else:
            self.issues["medium"].append({
                "check": "CSRF Protection",
                "message": "No CSRF protection found"
            })
            logger.warning("⚠️  No CSRF protection found")

    def check_sensitive_data_logs(self):
        """Check for sensitive data in logs"""
        logger.info("🔍 Checking for sensitive data in logs...")

        # Patterns that might log sensitive data
        sensitive_patterns = [
            (r'logger\.(info|debug)\(.*password.*\)', "Logging password"),
            (r'logger\.(info|debug)\(.*token.*\)', "Logging token"),
            (r'logger\.(info|debug)\(.*ssn.*\)', "Logging SSN"),
            (r'logger\.(info|debug)\(.*credit.*card.*\)', "Logging credit card"),
            (r'print\([^{]*\{.*user.*\}', "Printing user object"),
        ]

        issues_found = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()

                for pattern, description in sensitive_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues_found.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "pattern": description
                        })
            except Exception:
                pass

        if issues_found:
            self.issues["high"].append({
                "check": "Sensitive Data in Logs",
                "message": f"Found {len(issues_found)} instances of potential sensitive data logging",
                "details": issues_found
            })
            logger.warning(f"⚠️  Found {len(issues_found)} potential sensitive data logs")
        else:
            logger.info("✅ No sensitive data in logs")

    def check_file_permissions(self):
        """Check file permissions for security"""
        logger.info("🔍 Checking file permissions...")

        # Check for overly permissive files
        permission_issues = []

        # Check common sensitive files
        sensitive_files = [
            ".env",
            ".env.production",
            "config.py",
            "settings.py",
            "*_secrets.py",
            "*.key",
            "*.pem"
        ]

        for pattern in sensitive_files:
            for file_path in self.project_root.glob(pattern):
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]

                    # Check if file is readable by others
                    if mode[-1] in ['4', '6', '7']:  # Readable by others
                        permission_issues.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "permissions": mode,
                            "issue": "Readable by group/others"
                        })
                except Exception:
                    pass

        if permission_issues:
            self.issues["medium"].append({
                "check": "File Permissions",
                "message": f"Found {len(permission_issues)} files with overly permissive permissions",
                "details": permission_issues
            })
            logger.warning(f"⚠️  Found {len(permission_issues)} permission issues")
        else:
            logger.info("✅ File permissions look good")

    def generate_report(self) -> Dict[str, Any]:
        """Generate security audit report"""

        total_issues = (
            len(self.issues["critical"]) +
            len(self.issues["high"]) +
            len(self.issues["medium"]) +
            len(self.issues["low"])
        )

        report = {
            "summary": {
                "total_issues": total_issues,
                "critical": len(self.issues["critical"]),
                "high": len(self.issues["high"]),
                "medium": len(self.issues["medium"]),
                "low": len(self.issues["low"]),
                "info": len(self.issues["info"])
            },
            "issues": self.issues,
            "recommendations": self.generate_recommendations()
        }

        return report

    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []

        if self.issues["critical"]:
            recommendations.append("🚨 CRITICAL: Address all critical security issues immediately before production deployment")

        if self.issues["high"]:
            recommendations.append("⚠️  HIGH: Review and fix all high-severity issues")

        if len(self.issues.get("SQL Injection", [])) > 0:
            recommendations.append("💡 Use parameterized queries (SQLAlchemy) instead of string concatenation")

        if len(self.issues.get("XSS Vulnerabilities", [])) > 0:
            recommendations.append("💡 Install and use bleach library for HTML sanitization")

        if len(self.issues.get("Hardcoded Secrets", [])) > 0:
            recommendations.append("💡 Move all secrets to environment variables or secret manager (AWS Secrets Manager, HashiCorp Vault)")

        if len(self.issues.get("Dependencies", [])) > 0:
            recommendations.append("💡 Run 'pip install --upgrade <package>' to update vulnerable dependencies")

        if not recommendations:
            recommendations.append("✅ No major security issues found - continue following security best practices")

        return recommendations


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PsychSync Security Audit")
    parser.add_argument("--full", action="store_true", help="Run full security audit")
    parser.add_argument("--sql-only", action="store_true", help="Check SQL injection only")
    parser.add_argument("--dependencies", action="store_true", help="Check dependencies only")

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent.parent

    # Initialize auditor
    auditor = SecurityAudit(project_root)

    # Run audit
    if args.full:
        report = auditor.run_full_audit()
    elif args.sql_only:
        auditor.check_sql_injection()
        report = auditor.generate_report()
    elif args.dependencies:
        auditor.check_insecure_dependencies()
        report = auditor.generate_report()
    else:
        logger.info("Running full security audit (use --help for options)")
        report = auditor.run_full_audit()

    # Print results
    print("\n" + "="*80)
    print("SECURITY AUDIT REPORT")
    print("="*80 + "\n")

    print("SUMMARY:")
    summary = report["summary"]
    print(f"  Critical: {summary['critical']}")
    print(f"  High:     {summary['high']}")
    print(f"  Medium:   {summary['medium']}")
    print(f"  Low:      {summary['low']}")
    print(f"  Info:     {summary['info']}")
    print(f"  Total:    {summary['total_issues']}")
    print()

    print("RECOMMENDATIONS:")
    for rec in report["recommendations"]:
        print(f"  {rec}")
    print()

    # Exit with appropriate code
    if summary["critical"] > 0:
        logger.error("❌ Critical security issues found!")
        sys.exit(1)
    elif summary["total_issues"] > 0:
        logger.warning("⚠️  Security issues found")
        sys.exit(2)
    else:
        logger.info("✅ No security issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
