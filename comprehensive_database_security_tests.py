#!/usr/bin/env python3
"""
Comprehensive Database Security Testing Suite
Tests for NoSQL injection, credential rotation, backup encryption,
privilege escalation, and log security
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
import base64

class ComprehensiveDatabaseSecurityTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []
        self.vulnerabilities = []

    # ============================================================================
    # TEST 1: NoSQL Injection Testing
    # ============================================================================

    async def test_nosql_injection(self) -> Dict[str, Any]:
        """Test for NoSQL injection vulnerabilities"""
        print("🔍 TEST 1: Testing for NoSQL Injection...")

        result = {
            "test_name": "NoSQL Injection Security Test",
            "test_timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "tested_files": 0,
            "injection_attempts": 0,
            "successful_injections": 0
        }

        # NoSQL injection payloads to test
        nosql_payloads = [
            {"$ne": None},  # Not equal operator
            {"$gt": ""},    # Greater than operator
            {"$regex": ".*"}, # Regex injection
            {"$where": "true"}, # Where clause injection
            {"$or": [{"admin": True}]}, # OR operator injection
            {"$in": ["admin", "root"]}, # IN operator injection
            {"$nin": []}, # NOT IN operator injection
            {"$exists": True}, # Exists operator injection
            {"$expr": {"$eq": ["$user", "admin"]}}, # Expression injection
            {"$jsonSchema": {"type": "object"}}, # Schema injection
        ]

        # Python files using MongoDB/document databases
        python_files = list(self.base_path.rglob("*.py"))

        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    result["tested_files"] += 1

                # Check for MongoDB/document database usage
                db_patterns = [
                    r'mongodb://',
                    r'from pymongo',
                    r'import pymongo',
                    r'mongoengine',
                    r'MongoClient',
                    r'\.find\(',
                    r'\.find_one\(',
                    r'\.update\(',
                    r'\.insert\(',
                ]

                uses_db = any(re.search(pattern, content, re.IGNORECASE) for pattern in db_patterns)

                if uses_db:
                    # Check for unsafe query construction
                    unsafe_patterns = [
                        (r'dict\s*\(\s*\*\*user_input', 'Dictionary unpacking with user input'),
                        (r'\.find\s*\(\s*\{[^}]*\+\s*\w+', 'String concatenation in queries'),
                        (r'\.update\s*\(\s*\{[^}]*\$\w+', 'Direct use of MongoDB operators with user input'),
                        (r'eval\s*\(', 'Using eval() with data - potential injection'),
                        (r'exec\s*\(', 'Using exec() with data - potential injection'),
                        (r'__import__\s*\(', 'Dynamic imports with user data'),
                    ]

                    file_vulnerabilities = []
                    for pattern, description in unsafe_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()

                            file_vulnerabilities.append({
                                "line": line_num,
                                "pattern": pattern,
                                "description": description,
                                "code": line_content[:150],
                                "severity": "HIGH"
                            })

                            result["injection_attempts"] += 1
                            result["successful_injections"] += 1

                    if file_vulnerabilities:
                        result["vulnerabilities"].append({
                            "file": str(py_file.relative_to(self.base_path)),
                            "vulnerabilities": file_vulnerabilities
                        })

            except Exception as e:
                print(f"   Error scanning {py_file}: {e}")

        # Check for NoSQL injection in configuration files
        config_files = list(self.base_path.rglob("*.json")) + list(self.base_path.rglob("*.yml"))
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Look for MongoDB connection strings
                if 'mongodb://' in content.lower():
                    # Check for insecure connection strings
                    if 'mongodb://localhost' in content and 'auth' not in content:
                        result["vulnerabilities"].append({
                            "file": str(config_file.relative_to(self.base_path)),
                            "vulnerabilities": [{
                                "line": 0,
                                "pattern": "mongodb://localhost without auth",
                                "description": "MongoDB connection without authentication",
                                "code": "MongoDB connection string lacks authentication",
                                "severity": "CRITICAL"
                            }]
                        })
                        result["successful_injections"] += 1

            except Exception:
                pass

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = "CRITICAL" if result["successful_injections"] > 5 else "HIGH" if result["successful_injections"] > 0 else "LOW"

        print(f"   📊 Files tested: {result['tested_files']}")
        print(f"   ⚠️  Vulnerabilities found: {len(result['vulnerabilities'])}")

        return result

    # ============================================================================
    # TEST 2: Database Credential Rotation
    # ============================================================================

    async def test_credential_rotation(self) -> Dict[str, Any]:
        """Check database credential rotation policies and implementation"""
        print("🔍 TEST 2: Checking Database Credential Rotation...")

        result = {
            "test_name": "Database Credential Rotation Test",
            "test_timestamp": datetime.now().isoformat(),
            "rotation_policies": [],
            "credential_issues": [],
            "age_analysis": [],
            "recommendations": []
        }

        # Check for credential rotation in configuration files
        config_files = [
            ".env.dev",
            ".env.prod",
            "app/core/config.py",
            "docker-compose.yml"
        ]

        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Check for hardcoded credentials
                    credential_patterns = [
                        (r'database_url\s*=\s*["\'][^"\']*password[^"\']*["\']', "Database URL with password"),
                        (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
                        (r'secret_key\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded secret key"),
                        (r'api_key\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded API key"),
                    ]

                    file_issues = []
                    for pattern, description in credential_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            file_issues.append({
                                "issue": description,
                                "severity": "HIGH",
                                "description": "Credential found in configuration file - may not be rotated"
                            })

                    if file_issues:
                        result["credential_issues"].append({
                            "file": config_file,
                            "issues": file_issues
                        })

                except Exception as e:
                    print(f"   Error checking {config_file}: {e}")

        # Check for credential rotation mechanism in code
        rotation_checks = {
            "has_rotation_function": False,
            "has_rotation_scheduler": False,
            "has_rotation_logging": False,
            "has_rotation_alerts": False
        }

        python_files = list(self.base_path.rglob("*.py"))
        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check for rotation-related functions
                if re.search(r'rotate.*credential|credential.*rotation', content, re.IGNORECASE):
                    rotation_checks["has_rotation_function"] = True

                # Check for automated rotation scheduling
                if re.search(r'cron|schedule|periodic.*rotation', content, re.IGNORECASE):
                    rotation_checks["has_rotation_scheduler"] = True

                # Check for rotation logging
                if re.search(r'log.*rotation|rotation.*log', content, re.IGNORECASE):
                    rotation_checks["has_rotation_logging"] = True

                # Check for rotation alerts
                if re.search(r'alert.*rotation|rotation.*alert|notify.*credential', content, re.IGNORECASE):
                    rotation_checks["has_rotation_alerts"] = True

            except Exception:
                pass

        result["rotation_policies"] = rotation_checks

        # Check file modification times for potential stale credentials
        stale_credentials = []
        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (datetime.now() - mtime).days

                if age_days > 90:  # 3 months
                    stale_credentials.append({
                        "file": config_file,
                        "age_days": age_days,
                        "last_modified": mtime.isoformat(),
                        "severity": "MEDIUM",
                        "description": f"Configuration file not modified in {age_days} days - credentials may be stale"
                    })

        result["age_analysis"] = stale_credentials

        # Generate recommendations
        if not rotation_checks["has_rotation_function"]:
            result["recommendations"].append({
                "priority": "HIGH",
                "issue": "No credential rotation mechanism found",
                "solution": "Implement automated database credential rotation"
            })

        if not rotation_checks["has_rotation_scheduler"]:
            result["recommendations"].append({
                "priority": "HIGH",
                "issue": "No scheduled credential rotation",
                "solution": "Set up periodic credential rotation (recommended: 90 days)"
            })

        if stale_credentials:
            result["recommendations"].append({
                "priority": "MEDIUM",
                "issue": f"{len(stale_credentials)} potentially stale credential files",
                "solution": "Review and rotate credentials in unchanged configuration files"
            })

        result["vulnerable"] = len(result["credential_issues"]) > 0 or len(stale_credentials) > 0
        result["risk_level"] = "HIGH" if result["vulnerable"] else "MEDIUM"

        print(f"   📊 Rotation policies found: {sum(rotation_checks.values())}/4")
        print(f"   ⚠️  Stale credential files: {len(stale_credentials)}")

        return result

    # ============================================================================
    # TEST 3: Database Backup Encryption
    # ============================================================================

    async def test_backup_encryption(self) -> Dict[str, Any]:
        """Test database backup files for encryption"""
        print("🔍 TEST 3: Testing Database Backup Encryption...")

        result = {
            "test_name": "Database Backup Encryption Test",
            "test_timestamp": datetime.now().isoformat(),
            "backups_found": [],
            "encrypted_backups": 0,
            "unencrypted_backups": 0,
            "security_issues": [],
            "recommendations": []
        }

        # Look for backup files
        backup_extensions = ['.sql', '.dump', '.backup', '.bak', '.sql.gz', '.tar.gz']
        backup_files = []

        for ext in backup_extensions:
            backup_files.extend(list(self.base_path.rglob(f"*{ext}")))

        # Check specific backup directories
        backup_dirs = ['backups', 'db_backups', 'database_backups', 'sql_backups']
        for backup_dir in backup_dirs:
            dir_path = self.base_path / backup_dir
            if dir_path.exists() and dir_path.is_dir():
                backup_files.extend(list(dir_path.rglob('*')))

        # Test each backup file
        for backup_file in backup_files:
            if backup_file.is_file() and backup_file.stat().st_size > 0:
                try:
                    backup_info = {
                        "file": str(backup_file.relative_to(self.base_path)),
                        "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                        "encrypted": False,
                        "encryption_type": None,
                        "issues": []
                    }

                    # Read first 1KB to check for encryption
                    with open(backup_file, 'rb') as f:
                        header = f.read(1024)

                    # Check for encryption indicators
                    is_encrypted = False
                    encryption_type = None

                    # Check for GPG encryption
                    if header[:3] == b'-----' or b'PGP' in header[:100]:
                        is_encrypted = True
                        encryption_type = "GPG"
                    # Check for AES encryption indicators
                    elif b'Salted__' in header[:20]:
                        is_encrypted = True
                        encryption_type = "AES"
                    # Check for plaintext SQL indicators
                    elif b'CREATE TABLE' in header or b'INSERT INTO' in header or b'--' in header[:100]:
                        is_encrypted = False
                        backup_info["issues"].append("Plain text SQL backup - readable by anyone")
                    # Check for base64 encoding (weak)
                    else:
                        try:
                            decoded = base64.b64decode(header)
                            if b'CREATE TABLE' in decoded or b'INSERT INTO' in decoded:
                                is_encrypted = False
                                backup_info["issues"].append("Base64 encoded backup - not true encryption")
                        except (binascii.Error, ValueError):
                            # Not valid base64 - continue checking
                            pass

                    backup_info["encrypted"] = is_encrypted
                    backup_info["encryption_type"] = encryption_type

                    if is_encrypted:
                        result["encrypted_backups"] += 1
                    else:
                        result["unencrypted_backups"] += 1

                    result["backups_found"].append(backup_info)

                    if not is_encrypted:
                        result["security_issues"].append(f"Unencrypted backup: {backup_info['file']}")

                except Exception as e:
                    print(f"   Error analyzing backup file {backup_file}: {e}")

        # Check for backup encryption configuration
        backup_scripts = list(self.base_path.rglob("*backup*.py")) + list(self.base_path.rglob("*backup*.sh"))
        encryption_in_script = False

        for script in backup_scripts:
            try:
                with open(script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check for encryption in backup scripts
                if re.search(r'encrypt|gpg|aes|cipher', content, re.IGNORECASE):
                    encryption_in_script = True
                    break
            except Exception:
                pass

        if not encryption_in_script:
            result["security_issues"].append("No encryption mechanism found in backup scripts")

        # Generate recommendations
        if result["unencrypted_backups"] > 0:
            result["recommendations"].append({
                "priority": "CRITICAL",
                "issue": f"{result['unencrypted_backups']} unencrypted database backups found",
                "solution": "Encrypt all backups using GPG or AES-256 encryption"
            })

        if not encryption_in_script:
            result["recommendations"].append({
                "priority": "HIGH",
                "issue": "Backup process lacks encryption",
                "solution": "Implement automatic encryption in backup scripts"
            })

        result["vulnerable"] = result["unencrypted_backups"] > 0
        result["risk_level"] = "CRITICAL" if result["unencrypted_backups"] > 0 else "MEDIUM"

        print(f"   📊 Backups found: {len(result['backups_found'])}")
        print(f"   🔒 Encrypted: {result['encrypted_backups']}")
        print(f"   ⚠️  Unencrypted: {result['unencrypted_backups']}")

        return result

    # ============================================================================
    # TEST 4: Database Privilege Escalation
    # ============================================================================

    async def test_privilege_escalation(self) -> Dict[str, Any]:
        """Attempt database privilege escalation and test access controls"""
        print("🔍 TEST 4: Testing Database Privilege Escalation...")

        result = {
            "test_name": "Database Privilege Escalation Test",
            "test_timestamp": datetime.now().isoformat(),
            "escalation_attempts": [],
            "vulnerabilities": [],
            "risk_level": "HIGH"
        }

        # Check for privilege escalation patterns in code
        escalation_patterns = [
            (r'SUPERUSER\s*=\s*True', 'Superuser privilege granted'),
            (r'CREATEDB\s*=\s*True', 'Database creation privilege'),
            (r'CREATEROLE\s*=\s*True', 'Role creation privilege'),
            (r'REPLICATION\s*=\s*True', 'Replication privilege'),
            (r'BYPASSRLS\s*=\s*True', 'Row Level Security bypass'),
            (r'GRANT\s+ALL\s+PRIVILEGES', 'All privileges granted'),
            (r'GRANT\s+.*\s+WITH\s+GRANT\s+OPTION', 'Grant option enabled'),
            (r'ALTER\s+ROLE.*WITH\s+SUPERUSER', 'Superuser elevation'),
            (r'DROP\s+ROLE.*CASCADE', 'Cascading role deletion'),
            (r'TRUNCATE.*WITH.*CASCADE', 'Cascading truncate'),
        ]

        python_files = list(self.base_path.rglob("*.py"))
        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                file_vulnerabilities = []
                for pattern, description in escalation_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = content.split('\n')[line_num - 1].strip()

                        file_vulnerabilities.append({
                            "line": line_num,
                            "pattern": pattern,
                            "description": description,
                            "code": line_content[:150],
                            "severity": "HIGH"
                        })

                        result["escalation_attempts"].append({
                            "file": str(py_file.relative_to(self.base_path)),
                            "line": line_num,
                            "description": description
                        })

                if file_vulnerabilities:
                    result["vulnerabilities"].append({
                        "file": str(py_file.relative_to(self.base_path)),
                        "vulnerabilities": file_vulnerabilities
                    })

            except Exception as e:
                print(f"   Error checking {py_file}: {e}")

        # Check SQL migration files for privilege escalation
        migration_files = list(self.base_path.rglob("alembic/versions/*.py"))
        for migration_file in migration_files:
            try:
                with open(migration_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Look for GRANT statements
                grants = re.findall(r'GRANT\s+([^;]+);', content, re.IGNORECASE)
                for grant in grants:
                    if 'ALL' in grant.upper() or 'SUPERUSER' in grant.upper():
                        result["escalation_attempts"].append({
                            "file": str(migration_file.relative_to(self.base_path)),
                            "description": f"Privileged grant: {grant}",
                            "severity": "MEDIUM"
                        })

            except Exception:
                pass

        # Check for role escalation patterns
        role_patterns = [
            (r'ALTER\s+USER.*WITH\s+SUPERUSER', 'User elevated to superuser'),
            (r'ALTER\s+ROLE.*WITH\s+SUPERUSER', 'Role elevated to superuser'),
            (r'CREATE\s+ROLE.*SUPERUSER', 'Superuser role created'),
            (r'SET\s+ROLE\s+.*', 'Role switching'),
            (r'SET\s+SESSION\s+AUTHORIZATION', 'Session authorization change'),
        ]

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern, description in role_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        result["escalation_attempts"].append({
                            "file": str(py_file.relative_to(self.base_path)),
                            "description": description,
                            "severity": "HIGH"
                        })

            except Exception:
                pass

        result["vulnerable"] = len(result["escalation_attempts"]) > 0
        result["risk_level"] = "CRITICAL" if len(result["escalation_attempts"]) > 5 else "HIGH"

        print(f"   📊 Escalation attempts found: {len(result['escalation_attempts'])}")

        return result

    # ============================================================================
    # TEST 5: Log File Security Analysis
    # ============================================================================

    async def test_log_security(self) -> Dict[str, Any]:
        """Check if logs expose sensitive data"""
        print("🔍 TEST 5: Analyzing Logs for Sensitive Data Exposure...")

        result = {
            "test_name": "Log Security Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "logs_analyzed": 0,
            "sensitive_data_found": [],
            "security_issues": [],
            "recommendations": []
        }

        # Patterns for sensitive data in logs
        sensitive_patterns = {
            "password": [
                r'password\s*[=:]\s*[^\s,}]{4,}',
                r'pwd\s*[=:]\s*[^\s,}]{4,}',
                r'pass\s*[=:]\s*[^\s,}]{4,}',
            ],
            "api_key": [
                r'api[_-]?key\s*[=:]\s*[^\s,}]{16,}',
                r'apikey\s*[=:]\s*[^\s,}]{16,}',
                r'secret[_-]?key\s*[=:]\s*[^\s,}]{16,}',
            ],
            "token": [
                r'token\s*[=:]\s*[^\s,}]{20,}',
                r'jwt\s*[=:]\s*[^\s,}]{20,}',
                r'auth[_-]?token\s*[=:]\s*[^\s,}]{20,}',
            ],
            "credit_card": [
                r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
                r'\d{16}',
            ],
            "email": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            "ssn": [
                r'\d{3}[-\s]?\d{2}[-\s]?\d{4}',
            ],
            "ip_address": [
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            ],
            "pii": [
                r'(?:first|last|full)[_-]?name\s*[=:]\s*[^\s,}]{2,}',
                r'(?:address|phone|mobile)\s*[=:]\s*[^\s,}]{5,}',
            ]
        }

        # Find log files
        log_extensions = ['.log', '.txt', '.out', '.err']
        log_files = []

        # Look in common log directories
        log_dirs = ['logs', 'log', 'var/log', 'tmp']
        for log_dir in log_dirs:
            dir_path = self.base_path / log_dir
            if dir_path.exists() and dir_path.is_dir():
                for ext in log_extensions:
                    log_files.extend(list(dir_path.rglob(f"*{ext}")))

        # Also check root directory for log files
        for ext in log_extensions:
            log_files.extend(list(self.base_path.glob(f"*{ext}")))

        # Analyze each log file
        for log_file in log_files:
            if log_file.is_file() and log_file.stat().st_size > 0:
                try:
                    result["logs_analyzed"] += 1

                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    file_findings = {
                        "file": str(log_file.relative_to(self.base_path)),
                        "size_kb": round(log_file.stat().st_size / 1024, 2),
                        "sensitive_data": []
                    }

                    # Check for each type of sensitive data
                    for data_type, patterns in sensitive_patterns.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                line_content = content.split('\n')[line_num - 1].strip()

                                # Mask the sensitive data in output
                                masked_line = re.sub(r'[^\s]{4,}', '***', line_content)

                                file_findings["sensitive_data"].append({
                                    "type": data_type,
                                    "line": line_num,
                                    "masked_content": masked_line[:200]
                                })

                    if file_findings["sensitive_data"]:
                        result["sensitive_data_found"].append(file_findings)
                        result["security_issues"].append(f"Sensitive data in {log_file.name}")

                except Exception as e:
                    print(f"   Error analyzing log file {log_file}: {e}")

        # Check for debug logging with sensitive data
        python_files = list(self.base_path.rglob("*.py"))
        debug_logging_issues = []

        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    # Check for debug logging with sensitive data
                    if re.search(r'logger\.debug.*password|logger\.debug.*token|logger\.debug.*key', line, re.IGNORECASE):
                        debug_logging_issues.append({
                            "file": str(py_file.relative_to(self.base_path)),
                            "line": i,
                            "code": line.strip()
                        })

                    # Check for print statements with sensitive data
                    if re.search(r'print\s*\(.*(password|token|secret|key)', line, re.IGNORECASE):
                        debug_logging_issues.append({
                            "file": str(py_file.relative_to(self.base_path)),
                            "line": i,
                            "code": line.strip(),
                            "severity": "HIGH"
                        })

            except Exception:
                pass

        if debug_logging_issues:
            result["security_issues"].append(f"{len(debug_logging_issues)} instances of debug logging with sensitive data")

        # Generate recommendations
        if result["sensitive_data_found"]:
            result["recommendations"].append({
                "priority": "CRITICAL",
                "issue": f"Sensitive data found in {len(result['sensitive_data_found'])} log files",
                "solution": "Implement log sanitization and remove sensitive data from logs"
            })

        if debug_logging_issues:
            result["recommendations"].append({
                "priority": "HIGH",
                "issue": f"{len(debug_logging_issues)} instances of debug logging with sensitive data",
                "solution": "Remove sensitive data from debug logging and use proper logging levels"
            })

        result["vulnerable"] = len(result["sensitive_data_found"]) > 0 or len(debug_logging_issues) > 0
        result["risk_level"] = "CRITICAL" if result["vulnerable"] else "MEDIUM"

        print(f"   📊 Logs analyzed: {result['logs_analyzed']}")
        print(f"   ⚠️  Sensitive data findings: {len(result['sensitive_data_found'])}")

        return result

    # ============================================================================
    # Main Test Runner
    # ============================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all 5 database security tests"""
        print("🔐 STARTING COMPREHENSIVE DATABASE SECURITY TEST SUITE")
        print("=" * 70)
        print()

        results = []

        # Test 1: NoSQL Injection
        results.append(await self.test_nosql_injection())
        print()

        # Test 2: Credential Rotation
        results.append(await self.test_credential_rotation())
        print()

        # Test 3: Backup Encryption
        results.append(await self.test_backup_encryption())
        print()

        # Test 4: Privilege Escalation
        results.append(await self.test_privilege_escalation())
        print()

        # Test 5: Log Security
        results.append(await self.test_log_security())
        print()

        # Generate summary
        vulnerable_tests = len([r for r in results if r.get("vulnerable", False)])
        total_issues = sum(len(r.get("security_issues", []) + r.get("vulnerabilities", [])) for r in results)

        summary = {
            "total_tests": len(results),
            "vulnerable_tests": vulnerable_tests,
            "total_issues": total_issues,
            "database_security_score": max(0, 100 - (vulnerable_tests * 15) - (total_issues * 2))
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary
        }


async def main():
    """Main execution function"""
    tester = ComprehensiveDatabaseSecurityTester()

    try:
        results = await tester.run_all_tests()

        # Display results
        print("\n" + "=" * 70)
        print("🔐 DATABASE SECURITY TEST SUITE RESULTS")
        print("=" * 70)

        summary = results["summary"]
        print(f"\n📊 Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"   Total Issues: {summary['total_issues']}")
        print(f"   Database Security Score: {summary['database_security_score']}/100")

        # Show individual test results
        for i, test_result in enumerate(results["test_results"], 1):
            print(f"\n{i}. {test_result['test_name']}:")
            if test_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {test_result.get('risk_level', 'HIGH')}")

                # Show key metrics
                if "injection_attempts" in test_result:
                    print(f"      Injection attempts: {test_result['injection_attempts']}")
                if "backups_found" in test_result:
                    print(f"      Unencrypted backups: {test_result['unencrypted_backups']}")
                if "escalation_attempts" in test_result:
                    print(f"      Escalation attempts: {len(test_result['escalation_attempts'])}")
                if "logs_analyzed" in test_result:
                    print(f"      Logs with sensitive data: {len(test_result['sensitive_data_found'])}")

                # Show first few vulnerabilities
                if "vulnerabilities" in test_result and test_result["vulnerabilities"]:
                    for vuln in test_result["vulnerabilities"][:2]:
                        print(f"      📁 {vuln['file']}: {len(vuln['vulnerabilities'])} issues")

                if "recommendations" in test_result and test_result["recommendations"]:
                    for rec in test_result["recommendations"][:2]:
                        print(f"      💡 [{rec['priority']}] {rec['issue']}")
            else:
                print(f"   ✅ SECURE: No significant vulnerabilities found")

        # Save detailed report
        with open("/Users/sheriftito/Downloads/psychsync/database_security_test_suite_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: database_security_test_suite_report.json")

    except Exception as e:
        print(f"❌ Error during database security testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
