#!/usr/bin/env python3
"""
Database Backup Security Testing Suite
Tests for backup encryption, credential rotation, and secure backup practices
"""

import os
import sys
import json
import re
import base64
import hashlib
import subprocess
import asyncio
import aiohttp
import gzip
import tarfile
import zipfile
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class BackupType(Enum):
    SQL_DUMP = "sql_dump"
    MONGODB_DUMP = "mongodb_dump"
    FILE_SYSTEM = "file_system"
    CLOUD_BACKUP = "cloud_backup"
    ENCRYPTED_ARCHIVE = "encrypted_archive"
    DATABASE_SNAPSHOT = "database_snapshot"

class EncryptionStandard(Enum):
    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    TLS_1_3 = "TLS-1.3"
    PGP_RSA = "PGP-RSA-4096"
    UNKNOWN = "UNKNOWN"

@dataclass
class BackupFinding:
    backup_path: str
    backup_type: BackupType
    issue_type: str
    severity: str
    description: str
    evidence: str
    recommendation: str
    encryption_detected: Optional[EncryptionStandard] = None
    file_size: Optional[int] = None
    created_date: Optional[datetime] = None

class BackupSecurityTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.findings: List[BackupFinding] = []
        self.logger = self.setup_logging()
        self.backup_directories = config.get('backup_directories', [
            './backups', '/var/backups', '/tmp/backups',
            './db_backups', './sql_dumps', './mongodumps'
        ])

    def setup_logging(self):
        """Setup detailed logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backup_security_test.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('BackupSecurityTester')

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all backup security tests"""
        self.logger.info("🔍 Starting comprehensive backup security testing...")

        # Test backup file encryption
        await self.test_backup_encryption()

        # Test backup processes
        await self.test_backup_processes()

        # Test cloud backup security
        await self.test_cloud_backup_security()

        # Test backup retention and deletion
        await self.test_backup_retention()

        # Test backup integrity
        await self.test_backup_integrity()

        # Generate report
        return await self.generate_report()

    async def test_backup_encryption(self):
        """Test backup files for encryption"""
        self.logger.info("🔍 Testing backup file encryption...")

        for backup_dir in self.backup_directories:
            if os.path.exists(backup_dir):
                await self.scan_directory_for_backups(backup_dir)

    async def scan_directory_for_backups(self, directory: str):
        """Scan directory for backup files and test encryption"""
        backup_extensions = [
            '.sql', '.dump', '.backup', '.bak', '.gz',
            '.zip', '.tar', '.tar.gz', '.tgz', '.bz2',
            '.enc', '.pgp', '.gpg', '.aes'
        ]

        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext.lower()) for ext in backup_extensions):
                    file_path = os.path.join(root, file)
                    await self.analyze_backup_file(file_path)

    async def analyze_backup_file(self, file_path: str):
        """Analyze a backup file for security issues"""
        try:
            file_size = os.path.getsize(file_path)
            created_date = datetime.fromtimestamp(os.path.getctime(file_path))

            # Determine backup type
            backup_type = self.detect_backup_type(file_path)

            # Test for encryption
            encryption_result = await self.test_file_encryption(file_path)

            # Scan for sensitive data if not encrypted
            if not encryption_result['is_encrypted']:
                await self.scan_for_sensitive_data(file_path)

            # Check file permissions
            await self.check_file_permissions(file_path)

            # Create finding based on results
            if not encryption_result['is_encrypted']:
                finding = BackupFinding(
                    backup_path=file_path,
                    backup_type=backup_type,
                    issue_type="Unencrypted Backup",
                    severity="HIGH",
                    description="Backup file is not encrypted",
                    evidence=f"File size: {file_size} bytes, Created: {created_date}",
                    recommendation="Encrypt backup files using AES-256 or stronger",
                    encryption_detected=EncryptionStandard.UNKNOWN,
                    file_size=file_size,
                    created_date=created_date
                )
                self.findings.append(finding)
                self.logger.warning(f"⚠️  Unencrypted backup found: {file_path}")
            else:
                self.logger.info(f"✅ Encrypted backup detected: {file_path} ({encryption_result['encryption_type']})")

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {str(e)}")

    def detect_backup_type(self, file_path: str) -> BackupType:
        """Detect the type of backup file"""
        filename = os.path.basename(file_path).lower()
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.sql', '.dump']:
            return BackupType.SQL_DUMP
        elif 'mongodb' in filename or file_extension in ['.bson']:
            return BackupType.MONGODB_DUMP
        elif file_extension in ['.enc', '.pgp', '.gpg', '.aes']:
            return BackupType.ENCRYPTED_ARCHIVE
        elif any(ext in filename for ext in ['snapshot', 'snap']):
            return BackupType.DATABASE_SNAPSHOT
        else:
            return BackupType.FILE_SYSTEM

    async def test_file_encryption(self, file_path: str) -> Dict[str, Any]:
        """Test if a file is encrypted and identify encryption type"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)  # Read first 1KB

            # Check for encryption signatures
            encryption_signatures = {
                EncryptionStandard.AES_256_GCM: [b'\x00\x00\x00\x01\x67'],  # GCM IV
                EncryptionStandard.AES_256_CBC: [b'Salted__'],  # OpenSSL salted format
                EncryptionStandard.PGP_RSA: [b'-----BEGIN PGP'],  # PGP format
                EncryptionStandard.UNKNOWN: [
                    b'PK\x03\x04',  # ZIP (encrypted)
                    b'\x1f\x8b\x08',  # GZIP
                    b'BZh',  # BZIP2
                ]
            }

            # Check for plaintext indicators
            plaintext_patterns = [
                b'CREATE TABLE',
                b'INSERT INTO',
                b'-- MySQL dump',
                b'-- PostgreSQL dump',
                b'MongoDB dump',
                b'{ "_id":',  # MongoDB JSON
                b'\x7b\x22\x5f\x69\x64\x22\x3a',  # Minified MongoDB JSON
                b'pg_dump',
                b'mysqldump',
                b'Database dump',
            ]

            # Check for high entropy (indicates encryption)
            def calculate_entropy(data: bytes) -> float:
                if len(data) == 0:
                    return 0
                byte_counts = [0] * 256
                for byte in data:
                    byte_counts[byte] += 1
                entropy = 0
                for count in byte_counts:
                    if count > 0:
                        probability = count / len(data)
                        entropy -= probability * (probability.bit_length() - 1)
                return entropy / 8  # Normalize to 0-1

            entropy = calculate_entropy(header)

            # Determine encryption status
            is_encrypted = False
            encryption_type = EncryptionStandard.UNKNOWN

            # Check signatures
            for enc_type, signatures in encryption_signatures.items():
                for sig in signatures:
                    if sig in header:
                        is_encrypted = True
                        encryption_type = enc_type
                        break
                if is_encrypted:
                    break

            # Check for plaintext
            if not is_encrypted:
                for pattern in plaintext_patterns:
                    if pattern in header:
                        return {
                            'is_encrypted': False,
                            'encryption_type': None,
                            'entropy': entropy,
                            'confidence': 'high'
                        }

            # Use entropy as additional indicator
            if not is_encrypted and entropy > 0.95:
                is_encrypted = True

            return {
                'is_encrypted': is_encrypted,
                'encryption_type': encryption_type if is_encrypted else None,
                'entropy': entropy,
                'confidence': 'high' if is_encrypted or entropy < 0.5 else 'medium'
            }

        except Exception as e:
            self.logger.error(f"Error testing encryption for {file_path}: {str(e)}")
            return {
                'is_encrypted': False,
                'encryption_type': None,
                'entropy': 0,
                'confidence': 'low'
            }

    async def scan_for_sensitive_data(self, file_path: str):
        """Scan backup file for sensitive data patterns"""
        sensitive_patterns = {
            'Email Addresses': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'Phone Numbers': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
            'Credit Cards': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'API Keys': r'["\']?[A-Za-z0-9]{20,}["\']?',
            'Passwords': r'password["\']?\s*[:=]\s*["\'][^"\']{6,}["\']',
            'Database URLs': r'(mongodb|mysql|postgres)://[^@]+:[^@]+@',
            'JWT Tokens': r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
        }

        try:
            # Handle different file types
            if file_path.endswith('.gz'):
                content = await self.read_gzip_file(file_path)
            elif file_path.endswith('.zip'):
                content = await self.read_zip_file(file_path)
            else:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read(1024 * 1024)  # Read first 1MB

            # Scan for sensitive data
            for pattern_name, pattern in sensitive_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                match_count = 0
                sample_matches = []

                for match in matches:
                    match_count += 1
                    if len(sample_matches) < 3:  # Keep first 3 samples
                        # Mask sensitive data in samples
                        matched_text = match.group()
                        if len(matched_text) > 10:
                            masked = matched_text[:5] + "*" * (len(matched_text) - 10) + matched_text[-5:]
                        else:
                            masked = "*" * len(matched_text)
                        sample_matches.append(masked)

                if match_count > 0:
                    finding = BackupFinding(
                        backup_path=file_path,
                        backup_type=self.detect_backup_type(file_path),
                        issue_type="Sensitive Data Exposure",
                        severity="CRITICAL",
                        description=f"Backup contains {pattern_name}",
                        evidence=f"Found {match_count} instances. Samples: {sample_matches}",
                        recommendation="Remove sensitive data from backups or encrypt them"
                    )
                    self.findings.append(finding)
                    self.logger.critical(f"🚨 Sensitive data in {file_path}: {pattern_name} ({match_count} instances)")

        except Exception as e:
            self.logger.error(f"Error scanning for sensitive data in {file_path}: {str(e)}")

    async def read_gzip_file(self, file_path: str) -> str:
        """Read and decompress gzipped file"""
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                return f.read(1024 * 1024)  # Read first 1MB
        except:
            # If text decompression fails, try binary
            with gzip.open(file_path, 'rb') as f:
                binary_data = f.read(1024 * 1024)
                return binary_data.decode('utf-8', errors='ignore')

    async def read_zip_file(self, file_path: str) -> str:
        """Read zip file contents"""
        content = ""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                for file_info in zip_file.filelist[:5]:  # Check first 5 files
                    if not file_info.is_dir():
                        with zip_file.open(file_info) as file:
                            content += file.read(1024 * 512).decode('utf-8', errors='ignore')
        except:
            pass
        return content

    async def check_file_permissions(self, file_path: str):
        """Check file permissions for security issues"""
        try:
            stat_info = os.stat(file_path)
            mode = oct(stat_info.st_mode)[-3:]

            # Check for world-readable files
            if mode[2] in ['4', '5', '6', '7']:  # Others have read permission
                finding = BackupFinding(
                    backup_path=file_path,
                    backup_type=self.detect_backup_type(file_path),
                    issue_type="Insecure File Permissions",
                    severity="MEDIUM",
                    description="Backup file is readable by all users",
                    evidence=f"File permissions: {mode}",
                    recommendation="Restrict backup file permissions (chmod 600)"
                )
                self.findings.append(finding)
                self.logger.warning(f"⚠️  Insecure permissions for {file_path}: {mode}")

        except Exception as e:
            self.logger.error(f"Error checking permissions for {file_path}: {str(e)}")

    async def test_backup_processes(self):
        """Test running backup processes for security issues"""
        self.logger.info("🔍 Testing backup processes...")

        backup_processes = [
            'pg_dump', 'mysqldump', 'mongodump', 'sqlite3',
            'pg_basebackup', 'rsync', 'tar', 'cp', 'dd'
        ]

        try:
            # Check running processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.lower()

            for process in backup_processes:
                if process in processes:
                    # Check for encryption flags
                    encryption_flags = ['-e', '--encrypt', '--cipher', '-k', '--password']
                    has_encryption = any(flag in processes for flag in encryption_flags)

                    if not has_encryption:
                        finding = BackupFinding(
                            backup_path="Running Process",
                            backup_type=BackupType.DATABASE_SNAPSHOT,
                            issue_type="Unencrypted Backup Process",
                            severity="MEDIUM",
                            description=f"Backup process {process} running without encryption",
                            evidence="Process found in ps aux without encryption flags",
                            recommendation="Add encryption flags to backup commands"
                        )
                        self.findings.append(finding)
                        self.logger.warning(f"⚠️  Unencrypted backup process: {process}")

        except Exception as e:
            self.logger.error(f"Error testing backup processes: {str(e)}")

    async def test_cloud_backup_security(self):
        """Test cloud backup configurations"""
        self.logger.info("🔍 Testing cloud backup security...")

        # Test AWS S3 backup security
        await self.test_s3_backup_security()

        # Test Azure Blob backup security
        await self.test_azure_backup_security()

        # Test Google Cloud Storage backup security
        await self.test_gcs_backup_security()

    async def test_s3_backup_security(self):
        """Test AWS S3 backup security"""
        try:
            # Check for AWS credentials in environment
            aws_creds = {
                'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
                'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'AWS_SESSION_TOKEN': os.getenv('AWS_SESSION_TOKEN')
            }

            if all(aws_creds.values()):
                s3 = boto3.client('s3')

                # List S3 buckets
                buckets = s3.list_buckets()
                for bucket in buckets['Buckets']:
                    bucket_name = bucket['Name']

                    # Check bucket encryption
                    try:
                        encryption = s3.get_bucket_encryption(Bucket=bucket_name)
                        self.logger.info(f"✅ S3 bucket {bucket_name} has encryption enabled")
                    except s3.exceptions.ClientError as e:
                        if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
                            finding = BackupFinding(
                                backup_path=f"s3://{bucket_name}",
                                backup_type=BackupType.CLOUD_BACKUP,
                                issue_type="Unencrypted Cloud Storage",
                                severity="HIGH",
                                description=f"S3 bucket {bucket_name} lacks encryption",
                                evidence="GetBucketEncryption operation failed",
                                recommendation="Enable S3 bucket encryption (SSE-S3 or SSE-KMS)"
                            )
                            self.findings.append(finding)
                            self.logger.warning(f"⚠️  S3 bucket {bucket_name} not encrypted")

                    # Check bucket policy for public access
                    try:
                        policy = s3.get_bucket_policy(Bucket=bucket_name)
                        policy_str = json.dumps(policy['Policy'])
                        if '"Effect": "Allow"' in policy_str and '"Principal": "*"' in policy_str:
                            finding = BackupFinding(
                                backup_path=f"s3://{bucket_name}",
                                backup_type=BackupType.CLOUD_BACKUP,
                                issue_type="Public Bucket Access",
                                severity="CRITICAL",
                                description=f"S3 bucket {bucket_name} has public access policy",
                                evidence="Policy allows public access",
                                recommendation="Restrict bucket access and remove public policies"
                            )
                            self.findings.append(finding)
                            self.logger.critical(f"🚨 S3 bucket {bucket_name} is publicly accessible!")

                    except s3.exceptions.NoSuchBucketPolicy:
                        # No policy is better than public policy
                        pass

        except (NoCredentialsError, ClientError):
            self.logger.info("ℹ️  AWS credentials not available for S3 testing")
        except Exception as e:
            self.logger.error(f"Error testing S3 backup security: {str(e)}")

    async def test_azure_backup_security(self):
        """Test Azure Blob storage backup security"""
        # Azure testing would require azure-storage-blob library and credentials
        self.logger.info("ℹ️  Azure backup security testing requires Azure SDK and credentials")

    async def test_gcs_backup_security(self):
        """Test Google Cloud Storage backup security"""
        # GCS testing would require google-cloud-storage library and credentials
        self.logger.info("ℹ️  GCS backup security testing requires Google Cloud SDK and credentials")

    async def test_backup_retention(self):
        """Test backup retention policies"""
        self.logger.info("🔍 Testing backup retention policies...")

        # Check for very old backup files
        cutoff_date = datetime.now() - timedelta(days=365)  # 1 year

        old_backups = []
        for finding in self.findings:
            if finding.created_date and finding.created_date < cutoff_date:
                old_backups.append(finding)

        if old_backups:
            finding = BackupFinding(
                backup_path="Multiple Files",
                backup_type=BackupType.FILE_SYSTEM,
                issue_type="Excessive Backup Retention",
                severity="MEDIUM",
                description=f"Found {len(old_backups)} backup files older than 1 year",
                evidence=f"Oldest backup from {min(f.created_date for f in old_backups)}",
                recommendation="Implement backup retention policy and securely delete old backups"
            )
            self.findings.append(finding)
            self.logger.warning(f"⚠️  Found {len(old_backups)} backup files older than 1 year")

    async def test_backup_integrity(self):
        """Test backup file integrity"""
        self.logger.info("🔍 Testing backup integrity...")

        # Check for corrupted or incomplete backup files
        for finding in self.findings:
            if finding.backup_type in [BackupType.SQL_DUMP, BackupType.MONGODB_DUMP]:
                try:
                    # Test SQL file integrity
                    if finding.backup_path.endswith('.sql'):
                        await self.test_sql_file_integrity(finding.backup_path)

                    # Test MongoDB dump integrity
                    elif 'bson' in finding.backup_path:
                        await self.test_mongodb_dump_integrity(finding.backup_path)

                except Exception as e:
                    self.logger.error(f"Error testing integrity for {finding.backup_path}: {str(e)}")

    async def test_sql_file_integrity(self, file_path: str):
        """Test SQL dump file integrity"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Read first 1KB

            # Check for SQL dump indicators
            sql_indicators = [
                '-- MySQL dump',
                '-- PostgreSQL dump',
                'CREATE TABLE',
                'INSERT INTO',
                '-- Dump completed'
            ]

            if not any(indicator in content for indicator in sql_indicators):
                finding = BackupFinding(
                    backup_path=file_path,
                    backup_type=BackupType.SQL_DUMP,
                    issue_type="Corrupted Backup",
                    severity="HIGH",
                    description="SQL dump file appears corrupted or incomplete",
                    evidence="No valid SQL dump headers found",
                    recommendation="Verify backup process and file integrity"
                )
                self.findings.append(finding)
                self.logger.warning(f"⚠️  Corrupted SQL dump detected: {file_path}")

        except Exception as e:
            self.logger.error(f"Error testing SQL file integrity {file_path}: {str(e)}")

    async def test_mongodb_dump_integrity(self, file_path: str):
        """Test MongoDB dump file integrity"""
        # MongoDB BSON files would require specific libraries to validate
        self.logger.info(f"ℹ️  MongoDB dump integrity testing requires BSON library for {file_path}")

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive backup security report"""
        self.logger.info("📋 Generating backup security report...")

        report = {
            "scan_date": datetime.utcnow().isoformat(),
            "total_backups_scanned": len(set(f.backup_path for f in self.findings)),
            "findings": [],
            "summary": {},
            "recommendations": []
        }

        # Convert findings to dictionaries
        for finding in self.findings:
            finding_dict = {
                "backup_path": finding.backup_path,
                "backup_type": finding.backup_type.value,
                "issue_type": finding.issue_type,
                "severity": finding.severity,
                "description": finding.description,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
                "file_size": finding.file_size,
                "created_date": finding.created_date.isoformat() if finding.created_date else None
            }
            report["findings"].append(finding_dict)

        # Generate summary statistics
        severity_count = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }

        issue_type_count = {}

        for finding in self.findings:
            severity = finding.severity
            severity_count[severity] = severity_count.get(severity, 0) + 1

            issue_type = finding.issue_type
            issue_type_count[issue_type] = issue_type_count.get(issue_type, 0) + 1

        report["summary"] = {
            "total_findings": len(self.findings),
            "by_severity": severity_count,
            "by_issue_type": issue_type_count,
            "encryption_status": {
                "encrypted": len([f for f in self.findings if f.encryption_detected != EncryptionStandard.UNKNOWN]),
                "unencrypted": len([f for f in self.findings if f.issue_type == "Unencrypted Backup"])
            }
        }

        # Generate recommendations
        if severity_count["CRITICAL"] > 0:
            report["recommendations"].append({
                "priority": "IMMEDIATE",
                "issue": "Critical backup security vulnerabilities",
                "action": "Address all critical findings immediately",
                "affected_files": len([f for f in self.findings if f.severity == "CRITICAL"])
            })

        if severity_count["HIGH"] > 0:
            report["recommendations"].append({
                "priority": "URGENT",
                "issue": "High-risk backup security issues",
                "action": "Address high-risk findings within 48 hours",
                "affected_files": len([f for f in self.findings if f.severity == "HIGH"])
            })

        report["recommendations"].extend([
            {
                "priority": "STANDARD",
                "issue": "Backup encryption",
                "action": "Encrypt all backup files using AES-256-GCM or stronger"
            },
            {
                "priority": "STANDARD",
                "issue": "Access control",
                "action": "Implement strict access controls for backup files (chmod 600)"
            },
            {
                "priority": "STANDARD",
                "issue": "Cloud storage security",
                "action": "Enable encryption and restrict public access for cloud backups"
            },
            {
                "priority": "STANDARD",
                "issue": "Retention policy",
                "action": "Define and implement backup retention policies"
            }
        ])

        # Save report
        report_file = f"backup_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"✅ Backup security report saved to: {report_file}")
        return report

async def main():
    """Main execution function"""
    config = {
        "backup_directories": [
            "./backups", "/var/backups", "/tmp/backups",
            "./db_backups", "./sql_dumps", "./mongodumps"
        ],
        "cloud_config": {
            "aws": {
                "check_s3": True,
                "regions": ["us-east-1", "us-west-2"]
            }
        }
    }

    tester = BackupSecurityTester(config)

    try:
        report = await tester.run_all_tests()

        print(f"\n🔍 Backup Security Test Complete")
        print(f"📊 Total Backups Scanned: {report['total_backups_scanned']}")
        print(f"🚨 Critical Findings: {report['summary']['by_severity'].get('CRITICAL', 0)}")
        print(f"⚠️  High Findings: {report['summary']['by_severity'].get('HIGH', 0)}")
        print(f"⚡ Medium Findings: {report['summary']['by_severity'].get('MEDIUM', 0)}")
        print(f"ℹ️  Low Findings: {report['summary']['by_severity'].get('LOW', 0)}")
        print(f"🔒 Encrypted: {report['summary']['encryption_status']['encrypted']}")
        print(f"🔓 Unencrypted: {report['summary']['encryption_status']['unencrypted']}")

        # Show critical findings
        critical_findings = [f for f in tester.findings if f.severity == 'CRITICAL']
        if critical_findings:
            print(f"\n🚨 CRITICAL FINDINGS:")
            for finding in critical_findings[:5]:
                print(f"• {finding.issue_type}: {finding.description}")

    except Exception as e:
        print(f"❌ Error during backup security testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())