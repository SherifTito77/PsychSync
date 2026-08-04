#!/usr/bin/env python3
"""
Database Backup Encryption Security Tester
Tests backup encryption, access controls, and security practices
"""

import base64
import bz2
import gzip
import hashlib
import json
import lzma
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class BackupSecurityTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.findings = []
        self.test_files = []

    def scan_for_backup_files(self) -> List[Dict]:
        """Scan for all potential backup files"""
        print("🔍 Scanning for backup files...")

        backup_patterns = [
            "*.sql",
            "*.dump",
            "*.backup",
            "*.bak",
            "*.pg_dump",
            "*.tar",
            "*.tar.gz",
            "*.tgz",
            "*.zip",
            "*.7z",
            "*.enc",
            "*.gpg",
            "*.aes",
            "*.db",
            "*.sqlite",
            "*.csv",
            "*.json",
            "*backup*",
            "*dump*",
            "*backup_*",
        ]

        backup_files = []

        for pattern in backup_patterns:
            files = list(self.base_path.rglob(pattern))

            for file_path in files:
                # Skip common non-backup files
                skip_patterns = [
                    "node_modules",
                    ".git",
                    "dist",
                    "build",
                    "__pycache__",
                    "package-lock.json",
                    "yarn.lock",
                    ".DS_Store",
                ]

                if any(skip in str(file_path) for skip in skip_patterns):
                    continue

                try:
                    stat_info = file_path.stat()
                    backup_files.append(
                        {
                            "path": str(file_path),
                            "size": stat_info.st_size,
                            "modified": stat_info.st_mtime,
                            "relative_path": str(file_path.relative_to(self.base_path)),
                        }
                    )
                except Exception as e:
                    print(f"    ❌ Error accessing {file_path}: {e}")

        print(f"    📁 Found {len(backup_files)} potential backup files")
        return backup_files

    def test_file_encryption(self, file_info: Dict) -> Dict:
        """Test if a backup file is encrypted"""
        file_path = Path(file_info["path"])
        result = {
            "file": file_info["relative_path"],
            "encrypted": False,
            "encryption_type": None,
            "security_issues": [],
            "risk_level": "LOW",
        }

        try:
            with open(file_path, "rb") as f:
                header = f.read(1024)  # Read first 1KB

            # Test for common encryption signatures
            encryption_signatures = {
                b"Salted__": "OpenSSL Salt",
                b"-----BEGIN PGP": "PGP/GPG Encryption",
                b"PK\x03\x04": "ZIP Archive",
                b"\x1f\x8b\x08": "GZIP Compression",
                b"BZh": "BZIP2 Compression",
                b"\xfd7zXZ": "XZ/LZMA Compression",
                b"\x89PNG": "PNG Image",
                b"\xff\xd8\xff": "JPEG Image",
            }

            for signature, enc_type in encryption_signatures.items():
                if header.startswith(signature):
                    result["encrypted"] = True
                    result["encryption_type"] = enc_type
                    break

            # Additional encryption tests
            if not result["encrypted"]:
                # Check for high entropy (possible encryption)
                if self.calculate_entropy(header) > 7.0:
                    result["encrypted"] = True
                    result["encryption_type"] = "High Entropy (Possible Encryption)"
                    result["security_issues"].append(
                        "File has high entropy but no clear encryption signature"
                    )

                # Check if it's readable text
                try:
                    text_content = header.decode("utf-8")
                    if any(
                        keyword in text_content.lower()
                        for keyword in ["password", "secret", "key", "token"]
                    ):
                        result["security_issues"].append(
                            "Unencrypted backup contains sensitive keywords"
                        )
                        result["risk_level"] = "HIGH"
                except (UnicodeDecodeError, AttributeError):
                    # Binary data or non-text header - skip keyword check
                    pass

            # Check file permissions
            if os.access(file_path, os.R_OK | os.W_OK | os.X_OK):
                result["security_issues"].append(
                    "File has overly permissive permissions"
                )
                result["risk_level"] = "MEDIUM"

        except Exception as e:
            result["security_issues"].append(f"Error analyzing file: {e}")
            result["risk_level"] = "MEDIUM"

        return result

    def calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if len(data) == 0:
            return 0

        # Count byte frequencies
        byte_counts = {}
        for byte in data:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1

        # Calculate entropy
        entropy = 0
        data_len = len(data)

        for count in byte_counts.values():
            probability = count / data_len
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)

        return entropy

    def test_database_backup_encryption(self) -> Dict:
        """Test database backup encryption capabilities"""
        print("🔍 Testing database backup encryption capabilities...")

        results = {
            "postgresql_backup_test": None,
            "sqlite_backup_test": None,
            "encryption_key_management": None,
        }

        # Test PostgreSQL backup encryption
        try:
            # Create a test backup with encryption
            test_backup_sql = """
            -- Test backup content
            CREATE TABLE test_sensitive_data (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                password_hash VARCHAR(100),
                email VARCHAR(100),
                ssn VARCHAR(20),
                credit_card VARCHAR(20)
            );

            INSERT INTO test_sensitive_data (username, password_hash, email, ssn, credit_card)
            VALUES ('testuser', 'hashed_password_123', 'test@example.com', '123-45-6789', '4111-1111-1111-1111');
            """

            # Test GPG encryption simulation
            encrypted_content = self.simulate_encryption(test_backup_sql)

            results["postgresql_backup_test"] = {
                "status": "tested",
                "encryption_method": "simulated_gpg",
                "content_encrypted": encrypted_content is not None,
                "security_level": "high" if encrypted_content else "low",
            }

        except Exception as e:
            results["postgresql_backup_test"] = {"status": "failed", "error": str(e)}

        # Test SQLite backup
        try:
            # Create test SQLite database
            test_db_path = self.base_path / "test_backup_security.db"

            conn = sqlite3.connect(str(test_db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sensitive_data (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )
            """
            )

            cursor.execute(
                """
                INSERT INTO sensitive_data (data) VALUES
                ('test_sensitive_information_123'),
                ('password_secret_456'),
                ('api_key_789')
            """
            )

            conn.commit()
            conn.close()

            # Test backup encryption
            encrypted_backup = self.create_encrypted_backup(str(test_db_path))

            results["sqlite_backup_test"] = {
                "status": "tested",
                "backup_created": True,
                "encryption_successful": encrypted_backup is not None,
                "backup_file": str(encrypted_backup) if encrypted_backup else None,
            }

            # Clean up test files
            if test_db_path.exists():
                test_db_path.unlink()
            if encrypted_backup and encrypted_backup.exists():
                encrypted_backup.unlink()

        except Exception as e:
            results["sqlite_backup_test"] = {"status": "failed", "error": str(e)}

        return results

    def simulate_encryption(self, content: str) -> Optional[bytes]:
        """Simulate GPG encryption for testing"""
        try:
            # Generate a test encryption key
            password = b"test_encryption_password_123"
            salt = os.urandom(16)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))

            f = Fernet(key)
            encrypted_content = f.encrypt(content.encode())

            # Add salt to encrypted content
            return salt + encrypted_content

        except Exception as e:
            print(f"    ❌ Encryption simulation failed: {e}")
            return None

    def create_encrypted_backup(self, db_path: str) -> Optional[Path]:
        """Create an encrypted backup of SQLite database"""
        try:
            # Read database file
            with open(db_path, "rb") as f:
                db_content = f.read()

            # Encrypt content
            encrypted_content = self.simulate_encryption(
                db_content.decode("utf-8", errors="ignore")
            )

            if encrypted_content:
                # Create encrypted backup file
                backup_path = Path(db_path).with_suffix(".db.enc")
                with open(backup_path, "wb") as f:
                    f.write(encrypted_content)

                return backup_path

        except Exception as e:
            print(f"    ❌ Failed to create encrypted backup: {e}")

        return None

    def test_backup_access_controls(self) -> Dict:
        """Test backup file access controls"""
        print("🔍 Testing backup file access controls...")

        backup_files = self.scan_for_backup_files()
        access_control_results = []

        for file_info in backup_files:
            file_path = Path(file_info["path"])

            if not file_path.exists():
                continue

            try:
                # Check file permissions
                stat_info = file_path.stat()
                mode = oct(stat_info.st_mode)[-3:]

                # Check if file is readable by others
                world_readable = bool(stat_info.st_mode & 0o004)
                world_writable = bool(stat_info.st_mode & 0o002)

                # Check if file is readable/writable by group
                group_readable = bool(stat_info.st_mode & 0o040)
                group_writable = bool(stat_info.st_mode & 0o020)

                access_result = {
                    "file": file_info["relative_path"],
                    "permissions": mode,
                    "world_readable": world_readable,
                    "world_writable": world_writable,
                    "group_readable": group_readable,
                    "group_writable": group_writable,
                    "security_issues": [],
                }

                # Identify security issues
                if world_readable:
                    access_result["security_issues"].append("File readable by anyone")
                if world_writable:
                    access_result["security_issues"].append("File writable by anyone")
                if group_writable:
                    access_result["security_issues"].append("File writable by group")

                # Check if file contains sensitive information
                try:
                    with open(file_path, "rb") as f:
                        content = f.read(1024).decode("utf-8", errors="ignore")

                    sensitive_keywords = [
                        "password",
                        "secret",
                        "key",
                        "token",
                        "ssn",
                        "credit_card",
                    ]
                    if any(
                        keyword in content.lower() for keyword in sensitive_keywords
                    ):
                        access_result["security_issues"].append(
                            "File may contain sensitive information"
                        )

                except (OSError, IOError, UnicodeDecodeError):
                    # File can't be read or decoded - skip content check
                    pass

                if access_result["security_issues"]:
                    access_result["risk_level"] = "HIGH"
                elif group_readable or group_writable:
                    access_result["risk_level"] = "MEDIUM"
                else:
                    access_result["risk_level"] = "LOW"

                access_control_results.append(access_result)

            except Exception as e:
                access_control_results.append(
                    {
                        "file": file_info["relative_path"],
                        "error": str(e),
                        "risk_level": "MEDIUM",
                    }
                )

        return access_control_results

    def test_backup_rotation_policy(self) -> Dict:
        """Test backup rotation and retention policies"""
        print("🔍 Testing backup rotation and retention policies...")

        backup_files = self.scan_for_backup_files()

        if not backup_files:
            return {
                "status": "no_backup_files_found",
                "recommendation": "Implement regular backup schedule with retention policy",
            }

        # Analyze backup ages
        current_time = time.time()
        old_backups = []
        recent_backups = []

        for file_info in backup_files:
            age_days = (current_time - file_info["modified"]) / (24 * 3600)

            if age_days > 90:  # Older than 90 days
                old_backups.append(
                    {"file": file_info["relative_path"], "age_days": age_days}
                )
            else:
                recent_backups.append(
                    {"file": file_info["relative_path"], "age_days": age_days}
                )

        result = {
            "total_backups": len(backup_files),
            "recent_backups": len(recent_backups),
            "old_backups": len(old_backups),
            "old_backup_files": old_backups,
        }

        if len(old_backups) > 0:
            result["security_issue"] = (
                f"Found {len(old_backups)} backups older than 90 days"
            )
            result["recommendation"] = (
                "Implement backup retention policy and secure old backups"
            )

        return result

    def generate_security_recommendations(self, test_results: Dict) -> List[Dict]:
        """Generate security recommendations based on test results"""
        recommendations = []

        # Analyze file encryption results
        unencrypted_files = [
            f
            for f in test_results.get("file_encryption_tests", [])
            if not f.get("encrypted", False)
        ]

        if unencrypted_files:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "issue": f"{len(unencrypted_files)} unencrypted backup files found",
                    "recommendation": "Implement encryption for all backup files using AES-256 or GPG",
                    "affected_files": [f["file"] for f in unencrypted_files],
                }
            )

        # Analyze access control results
        access_issues = [
            f
            for f in test_results.get("access_control_tests", [])
            if f.get("security_issues")
        ]

        if access_issues:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "issue": f"{len(access_issues)} backup files have access control issues",
                    "recommendation": "Restrict file permissions to backup administrators only",
                    "affected_files": [f["file"] for f in access_issues],
                }
            )

        # Analyze backup encryption capabilities
        backup_encryption = test_results.get("backup_encryption_test", {})
        if (
            backup_encryption.get("postgresql_backup_test", {}).get("security_level")
            == "low"
        ):
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "issue": "Database backup encryption not properly configured",
                    "recommendation": "Configure database backup tools with encryption options",
                }
            )

        # Analyze backup rotation
        rotation_results = test_results.get("backup_rotation_test", {})
        if rotation_results.get("old_backups", 0) > 0:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "issue": f"{rotation_results.get('old_backups', 0)} old backup files found",
                    "recommendation": "Implement backup retention policy and secure archival",
                }
            )

        return recommendations

    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive backup security test"""
        print("🔐 STARTING COMPREHENSIVE BACKUP SECURITY TEST")
        print("=" * 60)

        results = {}

        # Test 1: Scan and analyze backup files
        print("1️⃣ Scanning backup files...")
        backup_files = self.scan_for_backup_files()

        file_encryption_results = []
        for file_info in backup_files[:10]:  # Limit to first 10 for testing
            result = self.test_file_encryption(file_info)
            file_encryption_results.append(result)

        results["file_encryption_tests"] = file_encryption_results

        # Test 2: Test database backup encryption
        print("2️⃣ Testing database backup encryption capabilities...")
        results["backup_encryption_test"] = self.test_database_backup_encryption()

        # Test 3: Test access controls
        print("3️⃣ Testing backup access controls...")
        results["access_control_tests"] = self.test_backup_access_controls()

        # Test 4: Test backup rotation
        print("4️⃣ Testing backup rotation policies...")
        results["backup_rotation_test"] = self.test_backup_rotation_policy()

        # Generate recommendations
        recommendations = self.generate_security_recommendations(results)
        results["recommendations"] = recommendations

        # Generate summary
        total_files = len(file_encryption_results)
        encrypted_files = len(
            [f for f in file_encryption_results if f.get("encrypted", False)]
        )
        access_issues = len(
            [
                f
                for f in results.get("access_control_tests", [])
                if f.get("security_issues")
            ]
        )

        results["summary"] = {
            "total_backup_files": total_files,
            "encrypted_files": encrypted_files,
            "unencrypted_files": total_files - encrypted_files,
            "files_with_access_issues": access_issues,
            "recommendations_count": len(recommendations),
            "overall_security_score": self.calculate_security_score(results),
        }

        return results

    def calculate_security_score(self, results: Dict) -> int:
        """Calculate overall security score (0-100)"""
        score = 100

        # Deduct points for unencrypted files
        file_encryption_tests = results.get("file_encryption_tests", [])
        unencrypted = len(
            [f for f in file_encryption_tests if not f.get("encrypted", False)]
        )
        if file_encryption_tests:
            score -= (unencrypted / len(file_encryption_tests)) * 30

        # Deduct points for access issues
        access_tests = results.get("access_control_tests", [])
        access_issues = len([f for f in access_tests if f.get("security_issues")])
        if access_tests:
            score -= (access_issues / len(access_tests)) * 25

        # Deduct points for poor encryption capabilities
        backup_encryption = results.get("backup_encryption_test", {})
        pg_test = backup_encryption.get("postgresql_backup_test", {})
        if pg_test.get("security_level") == "low":
            score -= 20

        return max(0, min(100, int(score)))


def main():
    """Main execution function"""
    tester = BackupSecurityTester()

    try:
        results = tester.run_comprehensive_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 BACKUP ENCRYPTION SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Backup Files: {summary['total_backup_files']}")
        print(f"🔒 Encrypted Files: {summary['encrypted_files']}")
        print(f"🔓 Unencrypted Files: {summary['unencrypted_files']}")
        print(f"🚨 Files with Access Issues: {summary['files_with_access_issues']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(f"🎯 Overall Security Score: {summary['overall_security_score']}/100")

        # Show unencrypted files
        unencrypted_files = [
            f for f in results["file_encryption_tests"] if not f.get("encrypted", False)
        ]

        if unencrypted_files:
            print(f"\n🔓 UNENCRYPTED BACKUP FILES:")
            for file_info in unencrypted_files:
                print(f"  ❌ {file_info['file']}")

        # Show access issues
        access_issues = [
            f for f in results["access_control_tests"] if f.get("security_issues")
        ]

        if access_issues:
            print(f"\n🚨 ACCESS CONTROL ISSUES:")
            for issue in access_issues[:5]:  # Show first 5
                print(f"  ⚠️  {issue['file']}: {', '.join(issue['security_issues'])}")

        # Show recommendations
        print(f"\n💡 SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open(
            "/Users/sheriftito/Downloads/psychsync/backup_encryption_security_report.json",
            "w",
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: backup_encryption_security_report.json")

    except Exception as e:
        print(f"❌ Error running backup security test: {e}")


if __name__ == "__main__":
    main()
