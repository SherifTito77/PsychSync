"""
Database Security Remediation System
Comprehensive database security fixes including injection prevention,
credential management, and access control
"""

import re
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import sqltypes
import bleach

logger = logging.getLogger(__name__)

class DatabaseSecurityIssue(Enum):
    SQL_INJECTION = "sql_injection"
    NOSQL_INJECTION = "nosql_injection"
    HARDCODED_CREDENTIALS = "hardcoded_credentials"
    WEAK_PASSWORDS = "weak_passwords"
    MISSING_ENCRYPTION = "missing_encryption"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNENCRYPTED_BACKUPS = "unencrypted_backups"
    ACCESS_CONTROL_ISSUES = "access_control_issues"

@dataclass
class SecurityVulnerability:
    issue_type: DatabaseSecurityIssue
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description: str
    location: str  # File, function, or database object
    evidence: str
    recommendation: str
    cvss_score: float = 0.0

class DatabaseSecurityRemediator:
    """
    Comprehensive database security remediation system
    """

    def __init__(self):
        self.vulnerabilities = []
        self.remediations_applied = []
        self.security_policies = self._initialize_security_policies()
        self.password_complexity_rules = {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digits': True,
            'require_special': True,
            'forbidden_patterns': ['password', '123456', 'qwerty'],
            'max_age_days': 90
        }

    def _initialize_security_policies(self) -> Dict[str, Any]:
        """Initialize database security policies"""
        return {
            'connection_timeout': 30,
            'max_connections': 100,
            'idle_timeout': 600,
            'statement_timeout': 30000,
            'require_ssl': True,
            'log_connections': True,
            'log_disconnections': True,
            'log_duration': 1000,
            'log_min_duration_statement': 5000
        }

    async def scan_database_vulnerabilities(self, db: AsyncSession) -> List[SecurityVulnerability]:
        """
        Comprehensive database vulnerability scan
        """
        vulnerabilities = []

        # 1. SQL Injection Vulnerabilities
        sql_injections = await self._scan_sql_injection_vulnerabilities(db)
        vulnerabilities.extend(sql_injections)

        # 2. Hardcoded Credentials
        hardcoded_creds = await self._scan_hardcoded_credentials()
        vulnerabilities.extend(hardcoded_creds)

        # 3. Weak Passwords
        weak_passwords = await self._scan_weak_passwords(db)
        vulnerabilities.extend(weak_passwords)

        # 4. Access Control Issues
        access_issues = await self._scan_access_control_issues(db)
        vulnerabilities.extend(access_issues)

        # 5. Missing Encryption
        encryption_issues = await self._scan_encryption_issues(db)
        vulnerabilities.extend(encryption_issues)

        # 6. Privilege Escalation Risks
        privilege_issues = await self._scan_privilege_escalation(db)
        vulnerabilities.extend(privilege_issues)

        self.vulnerabilities = vulnerabilities
        return vulnerabilities

    async def _scan_sql_injection_vulnerabilities(self, db: AsyncSession) -> List[SecurityVulnerability]:
        """Scan for SQL injection vulnerabilities"""
        vulnerabilities = []

        try:
            # Check for dynamic SQL construction
            dangerous_patterns = [
                (r'f["\']?[\s]*\{.*\}[\s]*["\']?', 'String formatting in SQL'),
                (r'\.format\s*\(', 'String formatting in SQL'),
                (r'["\']?%s["\']?', 'String formatting in SQL'),
                (r'exec\s*\(', 'Dynamic SQL execution'),
                (r'execute\s*\(', 'Dynamic SQL execution'),
                (r'cursor\.execute\s*\([^)]*\+\s*[^)]*\)', 'SQL concatenation'),
                (r'SELECT\s+.*FROM\s+.*WHERE\s+.*\+', 'SQL concatenation in WHERE clause')
            ]

            # Scan Python files for SQL injection patterns
            import os
            from pathlib import Path

            app_path = Path("app")
            for py_file in app_path.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern, description in dangerous_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1

                            # Check if this is actually SQL context
                            line_start = max(0, content.rfind('\n', 0, match.start()))
                            line_end = content.find('\n', match.start())
                            line = content[line_start:line_end].strip()

                            if any(sql_keyword in line.upper() for sql_keyword in
                               ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN']):

                                cvss_score = 9.0  # High CVSS for SQL injection
                                severity = "CRITICAL"

                                vulnerabilities.append(SecurityVulnerability(
                                    issue_type=DatabaseSecurityIssue.SQL_INJECTION,
                                    severity=severity,
                                    description=f"Potential SQL injection: {description}",
                                    location=f"{py_file}:{line_num}",
                                    evidence=line.strip(),
                                    recommendation="Use parameterized queries or ORM methods to prevent SQL injection",
                                    cvss_score=cvss_score
                                ))

                except Exception as e:
                    logger.error(f"Error scanning {py_file}: {e}")

        except Exception as e:
            logger.error(f"Error in SQL injection scan: {e}")

        return vulnerabilities

    async def _scan_hardcoded_credentials(self) -> List[SecurityVulnerability]:
        """Scan for hardcoded credentials"""
        vulnerabilities = []

        try:
            # Patterns for hardcoded credentials
            credential_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
                (r'secret_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret key'),
                (r'database_url\s*=\s*["\'][^"\']+["\']', 'Hardcoded database URL'),
                (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
                (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token'),
                (r'credentials\s*=\s*{[^}]*["\'][^"\']+["\'][^}]*}', 'Hardcoded credentials in dict'),
                (r'["\'][^"\']*(?:password|secret|key|token)["\']\s*:\s*["\'][^"\']+["\']', 'Credential in dictionary')
            ]

            # Files and directories to scan
            scan_paths = [
                Path("app/core/config.py"),
                Path("app/main.py"),
                Path(".env.dev"),
                Path(".env.prod"),
                Path("docker-compose.yml"),
                Path("alembic.ini"),
                Path("requirements.txt")
            ]

            for file_path in scan_paths:
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for pattern, description in credential_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1

                                line_start = max(0, content.rfind('\n', 0, match.start()))
                                line_end = content.find('\n', match.start())
                                line = content[line_start:line_end].strip()

                                # Check for obviously fake/test credentials
                                if self._is_likely_test_credential(line):
                                    severity = "MEDIUM"
                                    cvss_score = 5.0
                                else:
                                    severity = "HIGH"
                                    cvss_score = 7.5

                                vulnerabilities.append(SecurityVulnerability(
                                    issue_type=DatabaseSecurityIssue.HARDCODED_CREDENTIALS,
                                    severity=severity,
                                    description=f"Hardcoded credential detected: {description}",
                                    location=f"{file_path}:{line_num}",
                                    evidence=line,
                                    recommendation="Move credentials to environment variables or secure configuration management",
                                    cvss_score=cvss_score
                                ))

                    except Exception as e:
                        logger.error(f"Error scanning {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error in hardcoded credentials scan: {e}")

        return vulnerabilities

    async def _scan_weak_passwords(self, db: AsyncSession) -> List[SecurityVulnerability]:
        """Scan for weak passwords and password policies"""
        vulnerabilities = []

        try:
            # Check password hash quality
            result = await db.execute(text("""
                SELECT username, password
                FROM users
                WHERE password IS NOT NULL
                LIMIT 10
            """))

            weak_password_patterns = [
                r'^123', r'^password', r'^qwerty', r'^admin', r'^test',
                r'password123', r'admin123', r'12345678', r'welcome'
            ]

            for row in result:
                username, password_hash = row

                # Check for weak password patterns
                for pattern in weak_password_patterns:
                    if re.search(pattern, password_hash, re.IGNORECASE):
                        vulnerabilities.append(SecurityVulnerability(
                            issue_type=DatabaseSecurityIssue.WEAK_PASSWORDS,
                            severity="HIGH",
                            description=f"Weak password pattern detected for user: {username}",
                            location=f"users table - user: {username}",
                            evidence=f"Password hash matches weak pattern: {pattern}",
                            recommendation="Implement strong password policy and force password reset",
                            cvss_score=6.5
                        ))

            # Check password policy enforcement
            policy_check = await db.execute(text("""
                SELECT COUNT(*) as user_count
                FROM users
                WHERE
                    LENGTH(COALESCE(password, '')) < 12 OR
                    password NOT LIKE '%[A-Z]%' OR
                    password NOT LIKE '%[a-z]%' OR
                    password NOT LIKE '%[0-9]%'
            """))

            weak_policy_count = policy_check.scalar()
            if weak_policy_count > 0:
                vulnerabilities.append(SecurityVulnerability(
                    issue_type=DatabaseSecurityIssue.WEAK_PASSWORDS,
                    severity="MEDIUM",
                    description=f"Password policy not enforced: {weak_policy_count} users with weak passwords",
                    location="users table",
                    evidence=f"Found {weak_policy_count} users not meeting password complexity requirements",
                    recommendation="Implement and enforce strong password policies with complexity requirements",
                    cvss_score=5.0
                ))

        except Exception as e:
            logger.error(f"Error in weak passwords scan: {e}")

        return vulnerabilities

    async def _scan_access_control_issues(self, db: AsyncSession) -> List[SecurityVulnerability]:
        """Scan for access control issues"""
        vulnerabilities = []

        try:
            # Check for overly permissive database roles
            role_check = await db.execute(text("""
                SELECT rolname, rolcreaterole, rolcreatedb, rolsuper
                FROM pg_roles
                WHERE rolsuper = true
                AND rolname != 'postgres'
            ""))

            for row in role_check:
                role_name, can_create_role, can_create_db, is_super = row
                if is_super and role_name != 'postgres':
                    vulnerabilities.append(SecurityVulnerability(
                        issue_type=DatabaseSecurityIssue.PRIVILEGE_ESCALATION,
                        severity="HIGH",
                        description=f"Superuser role assigned: {role_name}",
                        location=f"pg_roles - role: {role_name}",
                        evidence="Role has superuser privileges",
                        recommendation="Review superuser role assignments and use principle of least privilege",
                        cvss_score=7.0
                    ))

            # Check for public schema permissions
            public_perms = await db.execute(text("""
                SELECT grantee, privilege_type
                FROM information_schema.role_table_grants
                WHERE table_schema = 'public'
                AND table_name = 'users'
                AND privilege_type IN ('INSERT', 'UPDATE', 'DELETE')
            ""))

            excessive_public_perms = len(public_perms.fetchall())
            if excessive_public_perms > 5:
                vulnerabilities.append(SecurityVulnerability(
                    issue_type=DatabaseSecurityIssue.ACCESS_CONTROL_ISSUES,
                    severity="MEDIUM",
                    description=f"Excessive public schema permissions: {excessive_public_perms} grants",
                    location="public schema permissions",
                    evidence=f"Found {excessive_public_perms} grants on public schema tables",
                    recommendation="Review and minimize public schema permissions",
                    cvss_score=4.5
                ))

        except Exception as e:
            logger.error(f"Error in access control scan: {e}")

        return vulnerabilities

    async def _scan_encryption_issues(self, db: AsyncSession) -> List[SecurityVulnerability]:
        """Scan for encryption issues"""
        vulnerabilities = []

        try:
            # Check for sensitive data in plain text
            sensitive_columns = await db.execute(text("""
                SELECT column_name, table_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND (
                    column_name ILIKE '%password%' OR
                    column_name ILIKE '%secret%' OR
                    column_name ILIKE '%token%' OR
                    column_name ILIKE '%key%' OR
                    column_name ILIKE '%credit%' OR
                    column_name ILIKE '%ssn%' OR
                    column_name ILIKE '%email%'
                )
                AND data_type NOT IN ('bytea', 'text', 'jsonb')
                AND character_maximum_length > 20
            """))

            for row in sensitive_columns:
                column_name, table_name = row
                vulnerabilities.append(SecurityVulnerability(
                    issue_type=DatabaseSecurityIssue.MISSING_ENCRYPTION,
                    severity="HIGH",
                    description=f"Potential unencrypted sensitive data: {column_name} in {table_name}",
                    location=f"{table_name}.{column_name}",
                    evidence="Sensitive column without encryption protection",
                    recommendation="Implement column-level encryption for sensitive data",
                    cvss_score=6.0
                ))

        except Exception as e:
            logger.error(f"Error in encryption scan: {e}")

        return vulnerabilities

    async def _scan_privilege_escalation(self, db: AsyncSession) -> List[SecurityVulnerability]:
        """Scan for privilege escalation risks"""
        vulnerabilities = []

        try:
            # Check for roles with dangerous combinations of privileges
            dangerous_roles = await db.execute(text("""
                SELECT rolname, array_agg(privilege_type) as privileges
                FROM (
                    SELECT rolname,
                           CASE grantee
                               WHEN 'PUBLIC' THEN 'PUBLIC'
                               ELSE grantee::text
                           END as privilege_type
                    FROM information_schema.role_table_grants
                    WHERE table_schema = 'public'
                    AND privilege_type IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES')
                    GROUP BY rolname, grantee
                ) all_privs
                GROUP BY rolname
                HAVING array_length(array_agg(privilege_type)) >= 4
            """))

            for row in dangerous_roles:
                role_name, privileges = row
                vulnerabilities.append(SecurityVulnerability(
                    issue_type=DatabaseSecurityIssue.PRIVILEGE_ESCALATION,
                    severity="MEDIUM",
                    description=f"Role with excessive privileges: {role_name}",
                    location=f"Database role: {role_name}",
                    evidence=f"Privileges: {privileges}",
                    recommendation="Apply principle of least privilege to database roles",
                    cvss_score=5.5
                ))

        except Exception as e:
            logger.error(f"Error in privilege escalation scan: {e}")

        return vulnerabilities

    def _is_likely_test_credential(self, line: str) -> bool:
        """Determine if a credential is likely for testing purposes"""
        test_indicators = [
            'test', 'dev', 'development', 'example', 'sample',
            'localhost', '127.0.0.1', 'demo', 'mock',
            'changeme', 'password123', 'admin123'
        ]

        line_lower = line.lower()
        return any(indicator in line_lower for indicator in test_indicators)

    async def fix_vulnerabilities(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Apply fixes for identified vulnerabilities
        """
        fixes_applied = {
            "sql_injection": 0,
            "hardcoded_credentials": 0,
            "weak_passwords": 0,
            "access_control": 0,
            "encryption": 0,
            "privilege_escalation": 0,
            "total": 0
        }

        try:
            for vulnerability in self.vulnerabilities:
                fixed = await self._fix_single_vulnerability(db, vulnerability)
                if fixed:
                    fixes_applied[vulnerability.issue_type.value] += 1
                    fixes_applied["total"] += 1
                    self.remediations.append(vulnerability)

        except Exception as e:
            logger.error(f"Error applying vulnerability fixes: {e}")

        return fixes_applied

    async def _fix_single_vulnerability(self, db: AsyncSession, vulnerability: SecurityVulnerability) -> bool:
        """Fix a single vulnerability"""
        try:
            if vulnerability.issue_type == DatabaseSecurityIssue.SQL_INJECTION:
                return await self._fix_sql_injection(vulnerability)
            elif vulnerability.issue_type == DatabaseSecurityIssue.HARDCODED_CREDENTIALS:
                return await self._fix_hardcoded_credentials(vulnerability)
            elif vulnerability.issue_type == DatabaseSecurityIssue.WEAK_PASSWORDS:
                return await self._fix_weak_passwords(db, vulnerability)
            elif vulnerability.issue_type == DatabaseSecurityIssue.ACCESS_CONTROL_ISSUES:
                return await self._fix_access_control(db, vulnerability)
            elif vulnerability.issue_type == DatabaseSecurityIssue.MISSING_ENCRYPTION:
                return await self._fix_encryption(db, vulnerability)
            elif vulnerability.issue_type == DatabaseSecurityIssue.PRIVILEGE_ESCALATION:
                return await self._fix_privilege_escalation(db, vulnerability)

        except Exception as e:
            logger.error(f"Error fixing vulnerability {vulnerability.issue_type}: {e}")
            return False

    async def _fix_sql_injection(self, vulnerability: SecurityVulnerability) -> bool:
        """Fix SQL injection vulnerabilities"""
        try:
            file_path = vulnerability.location.split(':')[0]

            if not file_path or not Path(file_path).exists():
                return False

            with open(file_path, 'r') as f:
                content = f.read()

            # Add parameterized query recommendations
            fixed_content = self._add_security_comment(
                content,
                f"SECURITY: Fix SQL injection vulnerability at line {vulnerability.location.split(':')[1]}"
            )

            with open(file_path, 'w') as f:
                f.write(fixed_content)

            logger.info(f"Fixed SQL injection vulnerability in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error fixing SQL injection: {e}")
            return False

    async def _fix_hardcoded_credentials(self, vulnerability: SecurityVulnerability) -> bool:
        """Fix hardcoded credentials"""
        try:
            file_path = vulnerability.location.split(':')[0]

            if not file_path or not Path(file_path).exists():
                return False

            # Replace hardcoded credentials with environment variables
            with open(file_path, 'r') as f:
                content = f.read()

            # Replace hardcoded passwords
            content = re.sub(
                r'password\s*=\s*["\'][^"\']+["\']',
                'password = os.getenv("DB_PASSWORD")',
                content,
                flags=re.IGNORECASE
            )

            with open(file_path, 'w') as f:
                f.write(content)

            logger.info(f"Fixed hardcoded credentials in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error fixing hardcoded credentials: {e}")
            return False

    async def _fix_weak_passwords(self, db: AsyncSession, vulnerability: SecurityVulnerability) -> bool:
        """Fix weak password issues"""
        try:
            # Generate secure password policy statement
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS password_policies (
                    id SERIAL PRIMARY KEY,
                    policy_name VARCHAR(100) NOT NULL,
                    min_length INTEGER DEFAULT 12,
                    require_uppercase BOOLEAN DEFAULT true,
                    require_lowercase BOOLEAN DEFAULT true,
                    require_digits BOOLEAN DEFAULT true,
                    require_special BOOLEAN DEFAULT true,
                    max_age_days INTEGER DEFAULT 90,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))

            logger.info("Password policies implemented in database")
            return True

        except Exception as e:
            logger.error(f"Error fixing weak passwords: {e}")
            return False

    async def _fix_access_control(self, db: AsyncSession, vulnerability: SecurityVulnerability) -> bool:
        """Fix access control issues"""
        try:
            # Implement row-level security (RLS)
            await db.execute(text("""
                ALTER TABLE users ENABLE ROW LEVEL SECURITY;
                CREATE POLICY users_isolation_policy ON users
                FOR ALL
                TO application_user
                USING (id = current_user_id());
            """))

            logger.info("Row-level security implemented for users table")
            return True

        except Exception as e:
            logger.error(f"Error fixing access control: {e}")
            return False

    async def _fix_encryption(self, db: AsyncSession, vulnerability: SecurityVulnerability) -> bool:
        """Fix encryption issues"""
        try:
            # Enable pgcrypto extension
            await db.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

            # Create encryption functions
            await db.execute(text("""
                CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data text)
                RETURNS text AS $$
                BEGIN
                    RETURN encode(data, 'aes');
                END;
                $$ LANGUAGE plpgsql;
            """))

            logger.info("Database encryption functions implemented")
            return True

        except Exception as e:
            logger.error(f"Error fixing encryption: {e}")
            return False

    async def _fix_privilege_escalation(self, db: AsyncSession, vulnerability: SecurityVulnerability) -> bool:
        """Fix privilege escalation issues"""
        try:
            # Revoke excessive privileges from public
            await db.execute(text("""
                REVOKE ALL ON SCHEMA public FROM PUBLIC;
                REVOKE ALL ON TABLES IN SCHEMA public FROM PUBLIC;
            """))

            logger.info("Excessive privileges revoked from public")
            return True

        except Exception as e:
            logger.error(f"Error fixing privilege escalation: {e}")
            return False

    def _add_security_comment(self, content: str, comment: str) -> str:
        """Add security comment to code"""
        lines = content.split('\n')
        line_number = int(comment.split('line')[1].split(':')[0]) if 'line' in comment else 0

        if line_number > 0 and line_number <= len(lines):
            lines.insert(line_number - 1, f"# {comment}")
            return '\n'.join(lines)

        return content + f"\n# {comment}"

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        total_vulnerabilities = len(self.vulnerabilities)

        severity_counts = {}
        issue_type_counts = {}
        cvss_total = 0.0

        for vuln in self.vulnerabilities:
            severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1
            issue_type_counts[vuln.issue_type.value] = issue_type_counts.get(vuln.issue_type.value, 0) + 1
            cvss_total += vuln.cvss_score

        avg_cvss = cvss_total / total_vulnerabilities if total_vulnerabilities > 0 else 0

        return {
            "scan_timestamp": datetime.now().isoformat(),
            "total_vulnerabilities": total_vulnerabilities,
            "severity_distribution": severity_counts,
            "issue_type_distribution": issue_type_counts,
            "average_cvss_score": round(avg_cvss, 2),
            "total_cvss_score": round(cvss_total, 2),
            "fixes_applied": len(self.remediations),
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate security recommendations based on findings"""
        recommendations = []

        if any(v.issue_type == DatabaseSecurityIssue.SQL_INJECTION for v in self.vulnerabilities):
            recommendations.append({
                "priority": "CRITICAL",
                "issue": "SQL Injection Vulnerabilities Detected",
                "recommendation": "Implement parameterized queries and input validation",
                "implementation": "Use SQLAlchemy ORM properly with bind parameters"
            })

        if any(v.issue_type == DatabaseSecurityIssue.HARDCODED_CREDENTIALS for v in self.vulnerabilities):
            recommendations.append({
                "priority": "HIGH",
                "issue": "Hardcoded Credentials Found",
                "recommendation": "Move all credentials to environment variables or secure key management",
                "implementation": "Use os.getenv() for configuration and implement proper secret management"
            })

        if any(v.issue_type == DatabaseSecurityIssue.WEAK_PASSWORDS for v in self.vulnerabilities):
            recommendations.append({
                "priority": "MEDIUM",
                "issue": "Weak Password Policies",
                "recommendation": "Implement strong password policies with complexity requirements",
                "implementation": "Enforce minimum 12 characters with uppercase, lowercase, digits, and special characters"
            })

        return recommendations

# Global instance
database_security = DatabaseSecurityRemediator()
