#!/usr/bin/env python3
"""
Database Credentials Security Audit
Tests credential rotation, storage, and management practices
"""

import os
import json
import re
import time
import sqlite3
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class DBCredentialsAuditor:
    def __init__(self):
        self.findings = []
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")

    def check_environment_variables(self):
        """Check for hardcoded database credentials in environment files"""
        print("🔍 Checking environment files for database credentials...")

        env_files = [
            ".env.dev",
            ".env.prod",
            ".env",
            ".env.example"
        ]

        credential_patterns = [
            r'password\s*=\s*["\']?([^"\']+)["\']?',
            r'db_password\s*=\s*["\']?([^"\']+)["\']?',
            r'database_url\s*=\s*["\']?([^"\']+)["\']?',
            r'postgresql://([^:]+):([^@]+)@',
            r'mongodb://([^:]+):([^@]+)@',
            r'secret\s*=\s*["\']?([^"\']+)["\']?',
            r'key\s*=\s*["\']?([^"\']+)["\']?',
        ]

        findings = []

        for env_file in env_files:
            file_path = self.base_path / env_file
            if file_path.exists():
                print(f"  📁 Checking {env_file}...")

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in credential_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            findings.append({
                                "file": env_file,
                                "pattern": pattern,
                                "matches": matches,
                                "risk_level": "HIGH" if "password" in pattern else "MEDIUM"
                            })
                            print(f"    ⚠️  Found potential credentials in {env_file}")

                except Exception as e:
                    print(f"    ❌ Error reading {env_file}: {e}")

        return findings

    def check_config_files(self):
        """Check configuration files for hardcoded credentials"""
        print("🔍 Checking configuration files for database credentials...")

        config_patterns = [
            r'["\']password["\']?\s*:\s*["\']([^"\']+)["\']',
            r'["\']database_url["\']?\s*:\s*["\']([^"\']+)["\']',
            r'["\']db_password["\']?\s*:\s*["\']([^"\']+)["\']',
            r'["\']secret["\']?\s*:\s*["\']([^"\']+)["\']',
            r'["\']api_key["\']?\s*:\s*["\']([^"\']+)["\']',
        ]

        config_files = list(self.base_path.rglob("*.py")) + \
                      list(self.base_path.rglob("*.json")) + \
                      list(self.base_path.rglob("*.yaml")) + \
                      list(self.base_path.rglob("*.yml")) + \
                      list(self.base_path.rglob("*.toml"))

        findings = []

        for config_file in config_files[:20]:  # Limit to first 20 files
            if "node_modules" in str(config_file) or ".git" in str(config_file):
                continue

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in config_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Filter out common false positives
                        filtered_matches = [m for m in matches if not self.is_false_positive(m)]

                        if filtered_matches:
                            findings.append({
                                "file": str(config_file.relative_to(self.base_path)),
                                "pattern": pattern,
                                "matches": filtered_matches,
                                "risk_level": "HIGH"
                            })
                            print(f"    ⚠️  Found credentials in {config_file.relative_to(self.base_path)}")

            except Exception as e:
                print(f"    ❌ Error reading {config_file}: {e}")

        return findings

    def is_false_positive(self, match):
        """Filter out common false positive patterns"""
        false_positives = [
            "password", "username", "secret", "key", "token", "YOUR_",
            "REPLACE_", "example", "test", "demo", "changeme",
            "localhost", "127.0.0.1", "0.0.0.0"
        ]

        match_lower = match.lower()
        return any(fp in match_lower for fp in false_positives)

    def check_database_connections(self):
        """Test database connection security"""
        print("🔍 Testing database connection security...")

        findings = []

        # Check PostgreSQL connection if available
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="psychsync",
                user="postgres",
                password="postgres",  # Default dev password
                connect_timeout=5
            )

            cursor = conn.cursor()

            # Check for default/weak credentials
            cursor.execute("SELECT current_user, current_database();")
            result = cursor.fetchone()

            findings.append({
                "type": "database_connection",
                "user": result[0],
                "database": result[1],
                "security_issue": "Using default/weak credentials",
                "risk_level": "HIGH"
            })

            cursor.close()
            conn.close()

        except Exception as e:
            findings.append({
                "type": "database_connection",
                "status": "connection_failed",
                "error": str(e),
                "security_note": "Database not accessible with default credentials"
            })

        return findings

    def check_credential_rotation(self):
        """Check for evidence of credential rotation practices"""
        print("🔍 Checking credential rotation evidence...")

        findings = []

        # Check for rotation scripts or documentation
        rotation_indicators = [
            "rotation", "rotate", "change", "update", "renew",
            "expire", "lifecycle", "schedule", "policy"
        ]

        files_to_check = []
        for ext in ['.py', '.md', '.sh', '.yml', '.yaml']:
            files_to_check.extend(list(self.base_path.rglob(f"*{ext}")))

        rotation_evidence = False

        for file_path in files_to_check[:30]:  # Limit search
            if "node_modules" in str(file_path) or ".git" in str(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()

                for indicator in rotation_indicators:
                    if indicator in content:
                        # Check if it's related to credentials
                        credential_contexts = ["password", "secret", "key", "token", "credential"]
                        if any(ctx in content for ctx in credential_contexts):
                            rotation_evidence = True
                            findings.append({
                                "type": "credential_rotation",
                                "file": str(file_path.relative_to(self.base_path)),
                                "indicator": indicator,
                                "context": "credential_related"
                            })
                            print(f"    ✓ Found rotation evidence in {file_path.relative_to(self.base_path)}")
                            break

            except Exception as e:
                pass

        if not rotation_evidence:
            findings.append({
                "type": "credential_rotation",
                "status": "no_evidence",
                "risk_level": "HIGH",
                "recommendation": "Implement credential rotation policy and procedures"
            })

        return findings

    def check_backup_security(self):
        """Check backup file security"""
        print("🔍 Checking backup file security...")

        findings = []

        # Look for backup files
        backup_patterns = [
            "*.backup", "*.bak", "*.sql", "*.dump", "*.pg_dump"
        ]

        backup_files = []
        for pattern in backup_patterns:
            backup_files.extend(list(self.base_path.rglob(pattern)))

        for backup_file in backup_files:
            file_info = backup_file.stat()

            findings.append({
                "type": "backup_file",
                "file": str(backup_file.relative_to(self.base_path)),
                "size": file_info.st_size,
                "modified": datetime.fromtimestamp(file_info.st_mtime).isoformat(),
                "risk_level": "MEDIUM",
                "security_note": "Ensure backup files are encrypted and access-controlled"
            })

        return findings

    def generate_recommendations(self, findings):
        """Generate security recommendations based on findings"""
        recommendations = []

        # Analyze findings and generate specific recommendations
        hardcoded_creds = [f for f in findings if "file" in f and f.get("risk_level") == "HIGH"]

        if hardcoded_creds:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": "Hardcoded database credentials found",
                "recommendation": "Remove hardcoded credentials and use environment variables or secret management",
                "affected_files": [f["file"] for f in hardcoded_creds]
            })

        weak_connections = [f for f in findings if f.get("type") == "database_connection" and f.get("security_issue")]
        if weak_connections:
            recommendations.append({
                "priority": "HIGH",
                "issue": "Database using default/weak credentials",
                "recommendation": "Change default database passwords and use strong authentication"
            })

        no_rotation = [f for f in findings if f.get("status") == "no_evidence"]
        if no_rotation:
            recommendations.append({
                "priority": "HIGH",
                "issue": "No evidence of credential rotation",
                "recommendation": "Implement regular credential rotation policy (every 90 days recommended)"
            })

        backup_files = [f for f in findings if f.get("type") == "backup_file"]
        if backup_files:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": "Backup files present",
                "recommendation": "Ensure backups are encrypted and access-controlled"
            })

        return recommendations

    def run_audit(self):
        """Run complete database credentials security audit"""
        print("🔐 STARTING DATABASE CREDENTIALS SECURITY AUDIT")
        print("=" * 60)

        all_findings = []

        # Run all checks
        all_findings.extend(self.check_environment_variables())
        all_findings.extend(self.check_config_files())
        all_findings.extend(self.check_database_connections())
        all_findings.extend(self.check_credential_rotation())
        all_findings.extend(self.check_backup_security())

        # Generate recommendations
        recommendations = self.generate_recommendations(all_findings)

        # Generate report
        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(all_findings),
                "high_risk_findings": len([f for f in all_findings if f.get("risk_level") == "HIGH"]),
                "medium_risk_findings": len([f for f in all_findings if f.get("risk_level") == "MEDIUM"]),
                "recommendations_count": len(recommendations)
            },
            "findings": all_findings,
            "recommendations": recommendations
        }

        return report

def main():
    """Main execution function"""
    auditor = DBCredentialsAuditor()

    try:
        report = auditor.run_audit()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 DATABASE CREDENTIALS SECURITY AUDIT REPORT")
        print("=" * 60)

        summary = report["summary"]
        print(f"📊 Total Findings: {summary['total_findings']}")
        print(f"🚨 High Risk: {summary['high_risk_findings']}")
        print(f"⚠️  Medium Risk: {summary['medium_risk_findings']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")

        if summary["high_risk_findings"] > 0:
            print(f"\n🚨 HIGH RISK FINDINGS:")
            high_risk = [f for f in report["findings"] if f.get("risk_level") == "HIGH"]
            for finding in high_risk:
                print(f"  ❌ {finding}")

        print(f"\n💡 SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save report
        with open("/Users/sheriftito/Downloads/psychsync/db_credentials_audit_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: db_credentials_audit_report.json")

    except Exception as e:
        print(f"❌ Error running audit: {e}")

if __name__ == "__main__":
    main()
