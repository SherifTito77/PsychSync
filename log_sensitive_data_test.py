#!/usr/bin/env python3
"""
Log Sensitive Data Exposure Security Tester
Tests for sensitive data exposure in application and database logs
"""

import os
import json
import re
import gzip
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class LogSecurityTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.sensitive_patterns = []
        self.setup_sensitive_patterns()

    def setup_sensitive_patterns(self):
        """Setup patterns for detecting sensitive data in logs"""
        self.sensitive_patterns = [
            # Authentication tokens and passwords
            (r'password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', "Password in logs"),
            (r'token["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', "Authentication token in logs"),
            (r'api[_-]?key["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', "API key in logs"),
            (r'secret["\']?\s*[:=]\s*["\']([^"\']{16,})["\']', "Secret in logs"),
            (r'jwt["\']?\s*[:=]\s*["\']([^"\']{50,})["\']', "JWT token in logs"),

            # Personal information
            (r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', "SSN/PII pattern"),
            (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', "Credit card pattern"),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email address"),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "Phone number pattern"),

            # Database connection strings
            (r'(mongodb|mysql|postgresql)://[^:]+:[^@]+@', "Database credentials in connection string"),
            (r'database_url["\']?\s*[:=]\s*["\']([^"\']*password[^"\']*)["\']', "Database URL with password"),

            # Session and authentication data
            (r'session[_-]?id["\']?\s*[:=]\s*["\']([^"\']{16,})["\']', "Session ID in logs"),
            (r'auth[_-]?token["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', "Auth token in logs"),
            (r'cookie["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', "Cookie data in logs"),

            # Health and assessment data (PHI)
            (r'(diagnosis|medical|health|assessment)["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', "PHI data in logs"),
            (r'(blood_pressure|heart_rate|weight|height)["\']?\s*[:=]\s*["\']([^"\']{3,})["\']', "Health metrics in logs"),

            # SQL queries with sensitive data
            (r'SELECT.*WHERE.*password', "Password query in logs"),
            (r'SELECT.*WHERE.*ssn', "SSN query in logs"),
            (r'INSERT.*VALUES.*password', "Password insertion in logs"),
        ]

    def scan_log_files(self) -> List[Dict]:
        """Scan for log files in the project"""
        print("🔍 Scanning for log files...")

        log_extensions = ['.log', '.txt', '.out', '.err']
        log_file_names = ['app.log', 'error.log', 'access.log', 'debug.log', 'sql.log']

        log_files = []

        # Scan for log files
        for ext in log_extensions:
            log_files.extend(self.base_path.rglob(f"*{ext}"))

        for log_name in log_file_names:
            log_files.extend(self.base_path.rglob(log_name))

        # Remove duplicates and common non-log files
        unique_files = []
        seen = set()

        for file_path in log_files:
            # Skip common non-log files
            skip_patterns = ['node_modules', '.git', 'dist', '__pycache__', '.DS_Store']
            if any(skip in str(file_path) for skip in skip_patterns):
                continue

            # Get relative path
            rel_path = str(file_path.relative_to(self.base_path))

            if rel_path not in seen:
                seen.add(rel_path)
                unique_files.append(file_path)

        print(f"    📁 Found {len(unique_files)} potential log files")
        return unique_files

    def analyze_log_file(self, file_path: Path) -> Dict:
        """Analyze a single log file for sensitive data"""
        result = {
            "file": str(file_path.relative_to(self.base_path)),
            "size": file_path.stat().st_size,
            "sensitive_findings": [],
            "security_issues": [],
            "risk_level": "LOW"
        }

        try:
            # Determine if file is compressed
            if file_path.suffix == '.gz':
                content = gzip.open(file_path, 'rt').read()
            else:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Analyze each line for sensitive patterns
            lines = content.split('\n')
            sensitive_count = 0

            for line_num, line in enumerate(lines, 1):
                for pattern, description in self.sensitive_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)

                    for match in matches:
                        # Mask sensitive data in the finding
                        masked_match = self.mask_sensitive_data(match)

                        finding = {
                            "line_number": line_num,
                            "pattern_type": description,
                            "pattern": pattern,
                            "matched_data": masked_match,
                            "raw_line": line.strip()[:200] + ("..." if len(line) > 200 else ""),
                            "severity": self.determine_severity(description, match)
                        }

                        result["sensitive_findings"].append(finding)
                        sensitive_count += 1

            # Check for additional security issues
            self.check_additional_issues(result, content)

            # Determine overall risk level
            if sensitive_count > 10:
                result["risk_level"] = "HIGH"
            elif sensitive_count > 0:
                result["risk_level"] = "MEDIUM"

            # Add summary
            result["summary"] = {
                "total_lines": len(lines),
                "sensitive_findings": sensitive_count,
                "unique_pattern_types": len(set(f["pattern_type"] for f in result["sensitive_findings"]))
            }

        except Exception as e:
            result["error"] = str(e)
            result["risk_level"] = "MEDIUM"

        return result

    def mask_sensitive_data(self, data: str, mask_char: str = "*", show_last: int = 4) -> str:
        """Mask sensitive data for reporting"""
        if len(data) <= show_last:
            return mask_char * len(data)

        return mask_char * (len(data) - show_last) + data[-show_last:]

    def determine_severity(self, pattern_type: str, match: str) -> str:
        """Determine severity of a finding"""
        high_severity_patterns = [
            "Password in logs", "Authentication token in logs",
            "API key in logs", "JWT token in logs", "Database credentials"
        ]

        medium_severity_patterns = [
            "Secret in logs", "Session ID in logs", "Auth token in logs",
            "SSN/PII pattern", "Credit card pattern"
        ]

        if pattern_type in high_severity_patterns:
            return "HIGH"
        elif pattern_type in medium_severity_patterns:
            return "MEDIUM"
        else:
            return "LOW"

    def check_additional_issues(self, result: Dict, content: str):
        """Check for additional security issues in logs"""
        issues = []

        # Check for stack traces with sensitive data
        if re.search(r'(traceback|stack trace)', content, re.IGNORECASE):
            if re.search(r'(password|token|secret|key)', content, re.IGNORECASE):
                issues.append("Stack trace contains potentially sensitive data")

        # Check for SQL statements with user input
        if re.search(r'SELECT.*WHERE.*\'.*\'', content, re.IGNORECASE):
            issues.append("SQL query with literal values found in logs")

        # Check for verbose logging
        lines = content.split('\n')
        debug_lines = [line for line in lines if 'debug' in line.lower() or 'trace' in line.lower()]

        if len(debug_lines) > len(lines) * 0.3:  # More than 30% debug lines
            issues.append("Excessive debug logging detected")

        # Check for full request/response logging
        if re.search(r'(request|response).*(body|payload|data)', content, re.IGNORECASE):
            issues.append("Full request/response logging detected")

        result["security_issues"] = issues

    def check_database_logs(self) -> List[Dict]:
        """Check database logs for sensitive data"""
        print("🔍 Checking database logs...")

        db_log_results = []

        # Look for PostgreSQL logs
        pg_log_paths = [
            "/var/log/postgresql/",
            "/usr/local/var/log/postgres/",
            "/tmp/postgres.log"
        ]

        for log_path in pg_log_paths:
            if Path(log_path).exists():
                log_files = list(Path(log_path).rglob("*.log"))

                for log_file in log_files:
                    try:
                        result = self.analyze_log_file(log_file)
                        result["log_type"] = "PostgreSQL"
                        db_log_results.append(result)
                    except Exception as e:
                        db_log_results.append({
                            "file": str(log_file),
                            "error": str(e),
                            "log_type": "PostgreSQL"
                        })

        # Check for SQLite database files that might contain logs
        sqlite_files = list(self.base_path.rglob("*.db")) + list(self.base_path.rglob("*.sqlite"))

        for sqlite_file in sqlite_files:
            try:
                result = self.analyze_sqlite_database(sqlite_file)
                if result:
                    db_log_results.append(result)
            except Exception as e:
                pass

        return db_log_results

    def analyze_sqlite_database(self, db_path: Path) -> Optional[Dict]:
        """Analyze SQLite database for sensitive data"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            sensitive_findings = []

            for table_name, in tables:
                try:
                    # Check if table might contain sensitive data
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]

                    if row_count > 0:
                        # Get sample data
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        sample_data = cursor.fetchall()

                        # Get column names
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]

                        # Check for sensitive columns
                        sensitive_columns = [col for col in columns
                                          if any(keyword in col.lower()
                                                for keyword in ['password', 'token', 'secret', 'key', 'ssn', 'email'])]

                        if sensitive_columns:
                            sensitive_findings.append({
                                "table": table_name,
                                "sensitive_columns": sensitive_columns,
                                "row_count": row_count,
                                "sample_data": str(sample_data)[:200]
                            })

                except sqlite3.Error:
                    continue

            conn.close()

            if sensitive_findings:
                return {
                    "file": str(db_path.relative_to(self.base_path)),
                    "log_type": "SQLite Database",
                    "sensitive_findings": sensitive_findings,
                    "risk_level": "HIGH"
                }

        except Exception:
            pass

        return None

    def check_application_logs(self) -> List[Dict]:
        """Check application-specific logs"""
        print("🔍 Checking application logs...")

        app_log_paths = [
            "logs/",
            "var/log/",
            "/tmp/",
            "."
        ]

        app_log_results = []

        for log_path in app_log_paths:
            full_path = self.base_path / log_path
            if full_path.exists():
                log_files = list(full_path.rglob("*.log")) + list(full_path.rglob("*.out"))

                for log_file in log_files:
                    try:
                        result = self.analyze_log_file(log_file)
                        result["log_type"] = "Application"
                        app_log_results.append(result)
                    except Exception as e:
                        app_log_results.append({
                            "file": str(log_file.relative_to(self.base_path)),
                            "error": str(e),
                            "log_type": "Application"
                        })

        return app_log_results

    def generate_log_security_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Generate security recommendations based on log analysis"""
        recommendations = []

        # Analyze findings by severity
        high_risk_files = [r for r in analysis_results.get("log_file_analysis", [])
                          if r.get("risk_level") == "HIGH"]
        medium_risk_files = [r for r in analysis_results.get("log_file_analysis", [])
                            if r.get("risk_level") == "MEDIUM"]

        total_sensitive_findings = sum(
            len(r.get("sensitive_findings", [])) for r in analysis_results.get("log_file_analysis", [])
        )

        if total_sensitive_findings > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"{total_sensitive_findings} instances of sensitive data found in logs",
                "recommendation": "Implement log sanitization and remove sensitive data from logging"
            })

        if high_risk_files:
            recommendations.append({
                "priority": "HIGH",
                "issue": f"{len(high_risk_files)} log files contain high-risk sensitive data",
                "recommendation": "Review and clean up high-risk log files immediately"
            })

        if medium_risk_files:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": f"{len(medium_risk_files)} log files contain medium-risk sensitive data",
                "recommendation": "Implement proper log filtering and data masking"
            })

        # Check for specific patterns
        all_findings = []
        for result in analysis_results.get("log_file_analysis", []):
            all_findings.extend(result.get("sensitive_findings", []))

        password_findings = [f for f in all_findings if "password" in f["pattern_type"].lower()]
        if password_findings:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"{len(password_findings)} passwords found in logs",
                "recommendation": "Immediately remove passwords from logs and implement secure password handling"
            })

        token_findings = [f for f in all_findings if "token" in f["pattern_type"].lower()]
        if token_findings:
            recommendations.append({
                "priority": "HIGH",
                "issue": f"{len(token_findings)} authentication tokens found in logs",
                "recommendation": "Remove tokens from logs and implement secure session management"
            })

        return recommendations

    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive log security analysis"""
        print("🔐 STARTING LOG SENSITIVE DATA EXPOSURE SECURITY TEST")
        print("=" * 60)

        results = {}

        # Test 1: Scan and analyze log files
        print("1️⃣ Scanning log files...")
        log_files = self.scan_log_files()

        log_file_analysis = []
        for log_file in log_files[:20]:  # Limit to first 20 files for testing
            result = self.analyze_log_file(log_file)
            log_file_analysis.append(result)

        results["log_file_analysis"] = log_file_analysis

        # Test 2: Check database logs
        print("2️⃣ Checking database logs...")
        results["database_logs"] = self.check_database_logs()

        # Test 3: Check application logs
        print("3️⃣ Checking application logs...")
        results["application_logs"] = self.check_application_logs()

        # Generate recommendations
        recommendations = self.generate_log_security_recommendations(results)
        results["recommendations"] = recommendations

        # Generate summary
        total_log_files = len(log_file_analysis) + len(results["database_logs"]) + len(results["application_logs"])
        high_risk_files = len([r for r in log_file_analysis if r.get("risk_level") == "HIGH"])
        total_sensitive_findings = sum(
            len(r.get("sensitive_findings", [])) for r in log_file_analysis
        )

        results["summary"] = {
            "total_log_files_analyzed": total_log_files,
            "high_risk_files": high_risk_files,
            "total_sensitive_findings": total_sensitive_findings,
            "unique_pattern_types": len(set(
                f["pattern_type"] for r in log_file_analysis
                for f in r.get("sensitive_findings", [])
            )),
            "recommendations_count": len(recommendations),
            "overall_security_score": max(0, 100 - (total_sensitive_findings * 2))
        }

        return results

def main():
    """Main execution function"""
    tester = LogSecurityTester()

    try:
        results = tester.run_comprehensive_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 LOG SENSITIVE DATA EXPOSURE SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Log Files Analyzed: {summary['total_log_files_analyzed']}")
        print(f"🚨 High Risk Files: {summary['high_risk_files']}")
        print(f"🔍 Total Sensitive Findings: {summary['total_sensitive_findings']}")
        print(f"📋 Unique Pattern Types: {summary['unique_pattern_types']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(f"🎯 Overall Security Score: {summary['overall_security_score']}/100")

        # Show high-risk files
        high_risk_files = [r for r in results["log_file_analysis"]
                          if r.get("risk_level") == "HIGH"]

        if high_risk_files:
            print(f"\n🚨 HIGH-RISK LOG FILES:")
            for file_result in high_risk_files[:5]:  # Show first 5
                print(f"  ❌ {file_result['file']}")
                print(f"     → {file_result.get('summary', {}).get('sensitive_findings', 0)} sensitive findings")

        # Show common sensitive patterns
        all_findings = []
        for result in results["log_file_analysis"]:
            all_findings.extend(result.get("sensitive_findings", []))

        if all_findings:
            pattern_counts = {}
            for finding in all_findings:
                pattern_type = finding["pattern_type"]
                pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1

            print(f"\n📊 MOST COMMON SENSITIVE PATTERNS:")
            sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for pattern, count in sorted_patterns:
                print(f"  ⚠️  {pattern}: {count} occurrences")

        # Show recommendations
        print(f"\n💡 SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open("/Users/sheriftito/Downloads/psychsync/log_sensitive_data_security_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: log_sensitive_data_security_report.json")

    except Exception as e:
        print(f"❌ Error running log security test: {e}")

if __name__ == "__main__":
    main()