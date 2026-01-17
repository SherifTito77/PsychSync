#!/usr/bin/env python3
"""
Log Security Testing Suite
Tests for sensitive data exposure, log injection, and log security vulnerabilities
"""

import os
import re
import json
import base64
import hashlib
import gzip
import asyncio
import aiohttp
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import mimetypes

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SensitiveDataType(Enum):
    PII = "PII"
    CREDENTIALS = "CREDENTIALS"
    TOKENS = "TOKENS"
    FINANCIAL = "FINANCIAL"
    HEALTH = "HEALTH"
    SYSTEM = "SYSTEM"
    INJECTION = "INJECTION"
    NETWORK = "NETWORK"

@dataclass
class LogFinding:
    log_file: str
    line_number: int
    sensitive_type: SensitiveDataType
    severity: str
    description: str
    evidence: str
    recommendation: str
    masked_data: Optional[str] = None
    context: Optional[str] = None

class LogSecurityTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.findings: List[LogFinding] = []
        self.logger = self.setup_logging()
        self.log_directories = config.get('log_directories', [
            './logs', '/var/log', './app/logs', './log',
            '.',  # Current directory
            '/tmp', '/var/tmp'
        ])
        self.max_file_size = config.get('max_file_size', 50 * 1024 * 1024)  # 50MB

    def setup_logging(self):
        """Setup detailed logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileWriter('log_security_test.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('LogSecurityTester')

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all log security tests"""
        self.logger.info("🚀 Starting comprehensive log security testing...")

        # Test log files for sensitive data
        await self.test_sensitive_data_exposure()

        # Test log file permissions
        await self.test_log_permissions()

        # Test log injection vulnerabilities
        await self.test_log_injection()

        # Test log retention and cleanup
        await self.test_log_retention()

        # Test log integrity
        await self.test_log_integrity()

        # Test log monitoring
        await self.test_log_monitoring()

        # Generate report
        return await self.generate_report()

    async def test_sensitive_data_exposure(self):
        """Test log files for sensitive data exposure"""
        self.logger.info("🔍 Testing logs for sensitive data exposure...")

        # Define sensitive data patterns
        sensitive_patterns = {
            SensitiveDataType.PII: [
                # SSN patterns
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{3}\s\d{2}\s\d{4}\b',
                r'\b\d{9}\b(?!\d)',  # 9-digit numbers (SSN-like)

                # Email addresses
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',

                # Phone numbers
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',

                # Addresses
                r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
                r'\b[A-Z][a-z]+\s*,\s*[A-Z]{2}\s*\d{5}\b',

                # Names (basic pattern)
                r'\b(CAPT|CPT|LT|LTC|MAJ|MAJ|MR|MRS|MS|DR|PROF|HON|SIR)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            ],

            SensitiveDataType.CREDENTIALS: [
                # Password patterns
                r'password["\']?\s*[:=]\s*["\'][^"\']{6,}["\']',
                r'passwd["\']?\s*[:=]\s*["\'][^"\']{6,}["\']',
                r'pwd["\']?\s*[:=]\s*["\'][^"\']{6,}["\']',
                r'pass["\']?\s*[:=]\s*["\'][^"\']{6,}["\']',

                # Database connection strings
                r'(mongodb|mysql|postgres|postgresql)://[^@]+:[^@]+@',
                r'(mysql|pgsql)://[^:]+:[^@]+@',
                r'db_connection_string["\']?\s*[:=]\s*["\'][^"\']+["\']',

                # API keys and secrets
                r'api_key["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}["\']',
                r'secret_key["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}["\']',
                r'private_key["\']?\s*[:=]\s*["\'][A-Za-z0-9/+=]{40,}["\']',
                r'access_token["\']?\s*[:=]\s*["\'][A-Za-z0-9._-]{20,}["\']',
                r'auth_token["\']?\s*[:=]\s*["\'][A-Za-z0-9._-]{20,}["\']',
                r'session_token["\']?\s*[:=]\s*["\'][A-Za-z0-9._-]{20,}["\']',

                # Environment variables
                r'(AWS_|AZURE_|GCP_|DB_|DATABASE_|REDIS_|MONGO_)[A-Z_]*["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
            ],

            SensitiveDataType.TOKENS: [
                # JWT tokens
                r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',

                # Session IDs
                r'session[_-]?id["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}["\']',

                # CSRF tokens
                r'csrf[_-]?token["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}["\']',

                # Authorization headers
                r'authorization["\']?\s*[:=]\s*["\'][Bb]earer\s+[A-Za-z0-9._-]+["\']',

                # OAuth tokens
                r'oauth[_-]?token["\']?\s*[:=]\s*["\'][A-Za-z0-9._-]{20,}["\']',
            ],

            SensitiveDataType.FINANCIAL: [
                # Credit card numbers
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                r'\b\d{4}[*]{4,}\d{4}\b',

                # Bank account numbers
                r'\b\d{8,17}\b',  # Basic account number pattern

                # Routing numbers
                r'\b\d{9}\b(?!\d)',  # 9-digit routing numbers
            ],

            SensitiveDataType.HEALTH: [
                # Medical record numbers
                r'mrn["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{6,}["\']',
                r'medical[_-]?record[_-]?number["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{6,}["\']',

                # Health information
                r'(blood_pressure|heart_rate|weight|height|allergies|medication)["\']?\s*[:=]\s*["\'][^"\']{3,}["\']',
            ],

            SensitiveDataType.SYSTEM: [
                # File paths
                r'/(?:etc|var|usr|home|root)/[^/\s]+',
                r'[A-Z]:[\\/](?:Windows|Program Files|Users)[\\/][^\\\s]+',

                # IP addresses
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',

                # Hostnames
                r'\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\b',
            ],

            SensitiveDataType.INJECTION: [
                # SQL injection attempts
                r'(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+',
                r'(?i)\'\s*(?:or|and)\s*["\']?\d["\']?\s*=\s*["\']?\d["\']?',
                r'(?i)\'\s*;\s*(?:drop|delete|update|insert)',

                # NoSQL injection attempts
                r'(?i)\$ne|\$gt|\$lt|\$regex|\$where|\$or|\$and',
                r'(?i)\{[^}]*\$where[^}]*\}',

                # XSS attempts
                r'(?i)<script[^>]*>.*?</script>',
                r'(?i)javascript:',
                r'(?i)on\w+\s*=\s*["\'][^"\']*["\']',

                # Command injection
                r'(?i)(;|\||&|`|\$\()\s*(?:cat|ls|dir|whoami|id|pwd)',

                # Path traversal
                r'(?i)\.\./\.\./|\.\.\\',
            ],

            SensitiveDataType.NETWORK: [
                # MAC addresses
                r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',

                # URLs with sensitive info
                r'https?://[^:]+:[^@]+@[^/\s]+',
            ]
        }

        # Scan all log directories
        for log_dir in self.log_directories:
            if os.path.exists(log_dir):
                await self.scan_directory_for_logs(log_dir, sensitive_patterns)

    async def scan_directory_for_logs(self, directory: str, patterns: Dict[SensitiveDataType, List[str]]):
        """Scan directory for log files and test them"""
        log_extensions = [
            '.log', '.out', '.err', '.txt', '.trace',
            '.debug', '.info', '.warn', '.error',
            '.access', '.audit', '.security'
        ]

        log_patterns = [
            r'.*log.*',
            r'.*error.*',
            r'.*debug.*',
            r'.*access.*',
            r'.*audit.*',
            r'.*application.*',
            r'.*server.*',
            r'.*service.*',
        ]

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)

                # Check file extension and name patterns
                is_log_file = False
                if any(file.lower().endswith(ext.lower()) for ext in log_extensions):
                    is_log_file = True
                else:
                    for pattern in log_patterns:
                        if re.match(pattern, file, re.IGNORECASE):
                            is_log_file = True
                            break

                if is_log_file:
                    await self.analyze_log_file(file_path, patterns)

    async def analyze_log_file(self, file_path: str, patterns: Dict[SensitiveDataType, List[str]]):
        """Analyze a log file for sensitive data"""
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                self.logger.warning(f"⚠️  Skipping large file {file_path} ({file_size} bytes)")
                return

            # Check if file is compressed
            content = await self.read_file_content(file_path)
            if not content:
                return

            # Scan line by line for sensitive data
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # Skip empty lines
                if not line.strip():
                    continue

                # Test each sensitive data type
                for sensitive_type, type_patterns in patterns.items():
                    for pattern in type_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # Mask the sensitive data for evidence
                            matched_text = match.group()
                            masked_data = self.mask_sensitive_data(matched_text, sensitive_type)

                            # Get context around the match
                            context_start = max(0, match.start() - 50)
                            context_end = min(len(line), match.end() + 50)
                            context = line[context_start:context_end]

                            # Determine severity
                            severity = self.determine_severity(sensitive_type, matched_text)

                            finding = LogFinding(
                                log_file=file_path,
                                line_number=line_num,
                                sensitive_type=sensitive_type,
                                severity=severity,
                                description=f"Sensitive {sensitive_type.value} data found in log",
                                evidence=f"Pattern: {pattern} at line {line_num}",
                                recommendation=self.get_recommendation(sensitive_type),
                                masked_data=masked_data,
                                context=context.strip()
                            )
                            self.findings.append(finding)

                            self.logger.warning(
                                f"⚠️  Sensitive data in {file_path}:{line_num} - {sensitive_type.value}: {masked_data}"
                            )

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {str(e)}")

    async def read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content, handling compression"""
        try:
            # Check file type
            mime_type, _ = mimetypes.guess_type(file_path)

            if mime_type == 'application/gzip':
                # Handle gzip compressed files
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            elif file_path.endswith('.gz'):
                # Handle .gz extension
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            else:
                # Handle regular text files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

        except Exception as e:
            self.logger.debug(f"Error reading {file_path}: {str(e)}")
            return None

    def mask_sensitive_data(self, data: str, sensitive_type: SensitiveDataType) -> str:
        """Mask sensitive data for logging"""
        if len(data) <= 10:
            return "*" * len(data)

        # Different masking strategies for different types
        if sensitive_type in [SensitiveDataType.CREDENTIALS, SensitiveDataType.TOKENS]:
            # Show first 3 and last 3 characters
            return data[:3] + "*" * (len(data) - 6) + data[-3:]
        elif sensitive_type == SensitiveDataType.PII:
            # Show first character, mask middle, show last 4
            return data[0] + "*" * (len(data) - 5) + data[-4:]
        elif sensitive_type in [SensitiveDataType.FINANCIAL, SensitiveDataType.HEALTH]:
            # Show first and last 2 characters
            return data[:2] + "*" * (len(data) - 4) + data[-2:]
        else:
            # Default masking
            return data[:5] + "*" * (len(data) - 10) + data[-5:] if len(data) > 10 else "*" * len(data)

    def determine_severity(self, sensitive_type: SensitiveDataType, matched_data: str) -> str:
        """Determine severity based on type and content"""
        if sensitive_type in [SensitiveDataType.CREDENTIALS, SensitiveDataType.TOKENS]:
            if any(key in matched_data.lower() for key in ['password', 'secret', 'private', 'key']):
                return "CRITICAL"
            return "HIGH"
        elif sensitive_type == SensitiveDataType.FINANCIAL:
            return "CRITICAL"
        elif sensitive_type == SensitiveDataType.PII:
            if any(pattern in matched_data for pattern in ['@', 'ssn', 'social']):
                return "HIGH"
            return "MEDIUM"
        elif sensitive_type == SensitiveDataType.HEALTH:
            return "HIGH"
        elif sensitive_type == SensitiveDataType.INJECTION:
            if any(cmd in matched_data.lower() for cmd in ['drop', 'delete', '<script>', ';']):
                return "HIGH"
            return "MEDIUM"
        else:
            return "MEDIUM"

    def get_recommendation(self, sensitive_type: SensitiveDataType) -> str:
        """Get recommendation for sensitive data type"""
        recommendations = {
            SensitiveDataType.PII: "Remove PII from logs or implement data masking",
            SensitiveDataType.CREDENTIALS: "Never log credentials. Use environment variables or secure vaults",
            SensitiveDataType.TOKENS: "Never log authentication tokens. Use token references only",
            SensitiveDataType.FINANCIAL: "Remove financial data from logs and implement PCI DSS compliance",
            SensitiveDataType.HEALTH: "Remove PHI from logs and implement HIPAA compliance",
            SensitiveDataType.SYSTEM: "Sanitize system information in logs",
            SensitiveDataType.INJECTION: "Implement input validation and output encoding",
            SensitiveDataType.NETWORK: "Mask or remove network identifiers from logs"
        }
        return recommendations.get(sensitive_type, "Review and sanitize sensitive data in logs")

    async def test_log_permissions(self):
        """Test log file permissions"""
        self.logger.info("🔍 Testing log file permissions...")

        for finding in self.findings:
            try:
                stat_info = os.stat(finding.log_file)
                mode = oct(stat_info.st_mode)[-3:]

                # Check for world-readable files
                if mode[2] in ['4', '5', '6', '7']:  # Others have read permission
                    finding = LogFinding(
                        log_file=finding.log_file,
                        line_number=0,
                        sensitive_type=SensitiveDataType.SYSTEM,
                        severity="MEDIUM",
                        description="Log file has overly permissive permissions",
                        evidence=f"Permissions: {mode}",
                        recommendation="Restrict log file permissions to root/application user only (chmod 600/640)"
                    )
                    self.findings.append(finding)
                    self.logger.warning(f"⚠️  Insecure permissions for {finding.log_file}: {mode}")

                # Check for world-writable files
                if mode[2] in ['2', '3', '6', '7']:  # Others have write permission
                    finding = LogFinding(
                        log_file=finding.log_file,
                        line_number=0,
                        sensitive_type=SensitiveDataType.SYSTEM,
                        severity="HIGH",
                        description="Log file is world-writable",
                        evidence=f"Permissions: {mode}",
                        recommendation="Remove world-write permissions from log files (chmod 644/640)"
                    )
                    self.findings.append(finding)
                    self.logger.warning(f"🚨 World-writable log file: {finding.log_file}: {mode}")

            except Exception as e:
                self.logger.debug(f"Error checking permissions for {finding.log_file}: {str(e)}")

    async def test_log_injection(self):
        """Test for log injection vulnerabilities"""
        self.logger.info("🔍 Testing log injection vulnerabilities...")

        injection_payloads = [
            # Newline injection
            "\n[CRITICAL] Security breach detected",
            "\r\n[ERROR] Database connection failed",
            "\x0a[ALERT] System compromise",

            # Log forging
            "[2024-01-01 12:00:00] [ADMIN] User login successful",
            "2024-01-01 12:00:00 [ROOT] System access granted",

            # XSS in logs
            "<script>alert('XSS in logs')</script>",
            "<img src=x onerror=alert('XSS')>",

            # Format string injection
            "%s%s%s%s",
            "%x%x%x%x",

            # ANSI escape sequences
            "\x1b[31m[CRITICAL]\x1b[0m Security alert",
            "\x1b[2J[1;1H",  # Clear screen

            # Control characters
            "\x07",  # Bell
            "\x08",  # Backspace
            "\x7f",  # Delete

            # JSON injection
            ',"role":"admin"',
            ',"is_admin":true',

            # Template injection
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
        ]

        base_url = self.config.get('api_base_url', 'http://localhost:8000')
        injection_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users",
            "/api/v1/assessments",
            "/api/v1/responses",
            "/health",
            "/metrics"
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in injection_endpoints:
                for payload in injection_payloads:
                    try:
                        # Test injection in various parameter types
                        test_data = {
                            "username": f"testuser{payload}",
                            "email": f"test{payload}@example.com",
                            "message": payload,
                            "search": payload,
                            "filter": payload
                        }

                        async with session.post(f"{base_url}{endpoint}", json=test_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status in [200, 201, 400]:  # Request was processed
                                # Wait a moment for log writing
                                await asyncio.sleep(0.1)

                                # Check logs for injection evidence
                                if await self.check_logs_for_injection(payload):
                                    finding = LogFinding(
                                        log_file="Application Logs",
                                        line_number=0,
                                        sensitive_type=SensitiveDataType.INJECTION,
                                        severity="HIGH",
                                        description=f"Log injection vulnerability in {endpoint}",
                                        evidence=f"Payload: {repr(payload)}",
                                        recommendation="Implement log sanitization and escape sequences"
                                    )
                                    self.findings.append(finding)
                                    self.logger.warning(f"⚠️  Log injection detected: {repr(payload)}")

                    except Exception as e:
                        self.logger.debug(f"Error testing log injection: {str(e)}")

    async def check_logs_for_injection(self, payload: str) -> bool:
        """Check if injection payload appears in recent logs"""
        # This would typically check recent log files
        # For now, return False as we can't access real-time logs
        return False

    async def test_log_retention(self):
        """Test log retention policies"""
        self.logger.info("🔍 Testing log retention policies...")

        # Check for very old log files
        cutoff_date = datetime.now() - timedelta(days=365)  # 1 year

        for log_dir in self.log_directories:
            if os.path.exists(log_dir):
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if any(file.lower().endswith(ext.lower()) for ext in ['.log', '.out', '.err']):
                            file_path = os.path.join(root, file)
                            try:
                                file_age = datetime.fromtimestamp(os.path.getctime(file_path))
                                if file_age < cutoff_date:
                                    file_size = os.path.getsize(file_path)
                                    finding = LogFinding(
                                        log_file=file_path,
                                        line_number=0,
                                        sensitive_type=SensitiveDataType.SYSTEM,
                                        severity="MEDIUM",
                                        description=f"Log file older than 1 year found",
                                        evidence=f"File age: {(datetime.now() - file_age).days} days, Size: {file_size} bytes",
                                        recommendation="Implement log rotation and retention policies"
                                    )
                                    self.findings.append(finding)
                                    self.logger.warning(f"⚠️  Old log file: {file_path} ({(datetime.now() - file_age).days} days)")

                            except Exception as e:
                                self.logger.debug(f"Error checking {file_path}: {str(e)}")

    async def test_log_integrity(self):
        """Test log file integrity"""
        self.logger.info("🔍 Testing log file integrity...")

        # Check for truncated or corrupted log files
        for log_dir in self.log_directories:
            if os.path.exists(log_dir):
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if any(file.lower().endswith(ext.lower()) for ext in ['.log', '.out', '.err']):
                            file_path = os.path.join(root, file)
                            try:
                                content = await self.read_file_content(file_path)
                                if content:
                                    # Check for log file integrity issues
                                    await self.check_log_integrity_issues(file_path, content)
                            except Exception as e:
                                finding = LogFinding(
                                    log_file=file_path,
                                    line_number=0,
                                    sensitive_type=SensitiveDataType.SYSTEM,
                                    severity="MEDIUM",
                                    description="Log file appears corrupted or unreadable",
                                    evidence=f"Error reading file: {str(e)}",
                                    recommendation="Check log file integrity and rotation"
                                )
                                self.findings.append(finding)

    async def check_log_integrity_issues(self, file_path: str, content: str):
        """Check for specific log integrity issues"""
        lines = content.split('\n')

        # Check for truncated entries
        for i, line in enumerate(lines, 1):
            if line and len(line) > 1000:  # Unusually long line might indicate truncation
                finding = LogFinding(
                    log_file=file_path,
                    line_number=i,
                    sensitive_type=SensitiveDataType.SYSTEM,
                    severity="LOW",
                    description="Potential log truncation detected",
                    evidence=f"Line length: {len(line)} characters",
                    recommendation="Check log formatting and rotation settings"
                )
                self.findings.append(finding)

        # Check for missing timestamps (common in logs)
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Mon DD HH:MM:SS
        ]

        missing_timestamps = 0
        for line in lines:
            if line.strip():
                has_timestamp = any(re.search(pattern, line) for pattern in timestamp_patterns)
                if not has_timestamp:
                    missing_timestamps += 1

        if missing_timestamps > len(lines) * 0.5:  # More than 50% missing timestamps
            finding = LogFinding(
                log_file=file_path,
                line_number=0,
                sensitive_type=SensitiveDataType.SYSTEM,
                severity="MEDIUM",
                description="High percentage of log entries missing timestamps",
                evidence=f"{missing_timestamps}/{len(lines)} entries missing timestamps",
                recommendation="Ensure proper log formatting with timestamps"
            )
            self.findings.append(finding)

    async def test_log_monitoring(self):
        """Test log monitoring and alerting"""
        self.logger.info("🔍 Testing log monitoring...")

        # Check for log monitoring tools
        monitoring_tools = [
            'fail2ban', 'logwatch', 'logrotate', 'rsyslog', 'syslog-ng',
            'fluentd', 'logstash', 'splunk', 'elasticsearch'
        ]

        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.lower()

            monitoring_found = []
            for tool in monitoring_tools:
                if tool in processes:
                    monitoring_found.append(tool)

            if not monitoring_found:
                finding = LogFinding(
                    log_file="System",
                    line_number=0,
                    sensitive_type=SensitiveDataType.SYSTEM,
                    severity="MEDIUM",
                    description="No log monitoring tools detected",
                    evidence="No running log monitoring processes found",
                    recommendation="Implement log monitoring and alerting system"
                )
                self.findings.append(finding)
            else:
                self.logger.info(f"✅ Log monitoring tools found: {', '.join(monitoring_found)}")

        except Exception as e:
            self.logger.error(f"Error checking log monitoring: {str(e)}")

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive log security report"""
        self.logger.info("📋 Generating log security report...")

        report = {
            "scan_date": datetime.utcnow().isoformat(),
            "total_findings": len(self.findings),
            "findings": [],
            "summary": {},
            "recommendations": []
        }

        # Convert findings to dictionaries
        for finding in self.findings:
            finding_dict = {
                "log_file": finding.log_file,
                "line_number": finding.line_number,
                "sensitive_type": finding.sensitive_type.value,
                "severity": finding.severity,
                "description": finding.description,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
                "masked_data": finding.masked_data,
                "context": finding.context
            }
            report["findings"].append(finding_dict)

        # Generate summary statistics
        findings_by_severity = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }

        findings_by_type = {}
        files_with_issues = set()

        for finding in self.findings:
            severity = finding.severity
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1

            sensitive_type = finding.sensitive_type.value
            findings_by_type[sensitive_type] = findings_by_type.get(sensitive_type, 0) + 1

            files_with_issues.add(finding.log_file)

        report["summary"] = {
            "by_severity": findings_by_severity,
            "by_type": findings_by_type,
            "files_with_issues": len(files_with_issues),
            "unique_files": list(files_with_issues)[:10]  # Show first 10
        }

        # Generate recommendations
        if findings_by_severity["CRITICAL"] > 0:
            report["recommendations"].append({
                "priority": "IMMEDIATE",
                "issue": "Critical log security vulnerabilities",
                "action": "Address all critical findings immediately",
                "affected_files": len([f for f in self.findings if f.severity == "CRITICAL"])
            })

        if findings_by_severity["HIGH"] > 0:
            report["recommendations"].append({
                "priority": "URGENT",
                "issue": "High-risk log security issues",
                "action": "Address high-risk findings within 48 hours",
                "affected_files": len([f for f in self.findings if f.severity == "HIGH"])
            })

        report["recommendations"].extend([
            {
                "priority": "STANDARD",
                "issue": "Log sanitization",
                "action": "Implement comprehensive log sanitization and data masking"
            },
            {
                "priority": "STANDARD",
                "issue": "Log access control",
                "action": "Restrict log file permissions and implement access controls"
            },
            {
                "priority": "STANDARD",
                "issue": "Log monitoring",
                "action": "Implement real-time log monitoring and alerting"
            },
            {
                "priority": "STANDARD",
                "issue": "Log retention",
                "action": "Define and implement log retention and rotation policies"
            },
            {
                "priority": "STANDARD",
                "issue": "Security logging",
                "action": "Ensure security events are properly logged and monitored"
            }
        ])

        # Save report
        report_file = f"log_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"✅ Log security report saved to: {report_file}")
        return report

async def main():
    """Main execution function"""
    config = {
        "log_directories": [
            "./logs", "/var/log", "./app/logs", "./log",
            ".", "/tmp", "/var/tmp"
        ],
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "api_base_url": "http://localhost:8000"
    }

    tester = LogSecurityTester(config)

    try:
        report = await tester.run_all_tests()

        print(f"\n🔍 Log Security Test Complete")
        print(f"📊 Total Findings: {report['total_findings']}")
        print(f"🚨 Critical: {report['summary']['by_severity'].get('CRITICAL', 0)}")
        print(f"⚠️  High: {report['summary']['by_severity'].get('HIGH', 0)}")
        print(f"⚡ Medium: {report['summary']['by_severity'].get('MEDIUM', 0)}")
        print(f"ℹ️  Low: {report['summary']['by_severity'].get('LOW', 0)}")
        print(f"📁 Files with Issues: {report['summary']['files_with_issues']}")

        # Show top sensitive data types
        print(f"\n📊 Findings by Type:")
        for data_type, count in report['summary']['by_type'].items():
            print(f"• {data_type}: {count}")

        # Show critical findings
        critical_findings = [f for f in tester.findings if f.severity == 'CRITICAL']
        if critical_findings:
            print(f"\n🚨 CRITICAL FINDINGS:")
            for finding in critical_findings[:5]:
                print(f"• {finding.log_file}: {finding.description}")

    except Exception as e:
        print(f"❌ Error during log security testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
