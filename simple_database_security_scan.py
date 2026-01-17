#!/usr/bin/env python3
"""
Simple Database Security Scanner - Bypassing syntax errors in main file
Performs essential database vulnerability checks
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SimpleDatabaseSecurityScanner:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.vulnerabilities = []

    def scan_code_for_sql_injection(self) -> Dict[str, Any]:
        """Scan codebase for SQL injection vulnerabilities"""
        print("🔍 Scanning for SQL injection vulnerabilities...")

        result = {
            "scan_name": "SQL Injection Code Analysis",
            "scan_timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "files_scanned": 0
        }

        # SQL injection patterns to search for
        dangerous_patterns = [
            (r'\.execute\s*\(\s*["\'].*?\%.*?["\']', "String formatting in SQL queries"),
            (r'\.execute\s*\(\s*f["\'].*?\{.*?\}.*?["\']', "F-string SQL injection"),
            (r'\.execute\s*\(\s*["\'].*?\+.*?["\']', "String concatenation in SQL"),
            (r'cursor\.execute\s*\([^)]*\%[^)]*\)', "Unsafe parameter formatting"),
            (r'SELECT.*FROM.*\+.*WHERE', "Dynamic SQL construction"),
            (r'INSERT.*VALUES.*\+', "INSERT statement with concatenation"),
            (r'UPDATE.*SET.*\+', "UPDATE statement with concatenation"),
            (r'DELETE.*FROM.*\+', "DELETE statement with concatenation")
        ]

        # Python files to scan
        python_files = list(self.base_path.rglob("*.py"))

        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    result["files_scanned"] += 1

                # Check for dangerous patterns
                file_vulnerabilities = []
                for pattern, description in dangerous_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = content.split('\n')[line_num - 1].strip()

                        file_vulnerabilities.append({
                            "line": line_num,
                            "pattern": pattern,
                            "description": description,
                            "code": line_content[:100] + "..." if len(line_content) > 100 else line_content
                        })

                if file_vulnerabilities:
                    result["vulnerabilities"].append({
                        "file": str(py_file.relative_to(self.base_path)),
                        "vulnerabilities": file_vulnerabilities
                    })

            except Exception as e:
                print(f"   Error scanning {py_file}: {e}")

        result["total_vulnerabilities"] = sum(len(v["vulnerabilities"]) for v in result["vulnerabilities"])
        result["vulnerable"] = result["total_vulnerabilities"] > 0
        result["risk_level"] = "HIGH" if result["total_vulnerabilities"] > 5 else "MEDIUM"

        return result

    def check_hardcoded_credentials(self) -> Dict[str, Any]:
        """Check for hardcoded credentials in codebase"""
        print("🔍 Scanning for hardcoded credentials...")

        result = {
            "scan_name": "Hardcoded Credentials Scan",
            "scan_timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "files_scanned": 0
        }

        # Credential patterns
        credential_patterns = [
            (r'password\s*=\s*["\'][^"\']{3,}["\']', "Hardcoded password"),
            (r'secret_key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret key"),
            (r'api_key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
            (r'database_url\s*=\s*["\'][^"\']*password[^"\']*["\']', "Database URL with password"),
            (r'connection_string\s*=\s*["\'][^"\']*password[^"\']*["\']', "Connection string with password"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded token"),
            (r'private_key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded private key")
        ]

        # Files to scan
        config_extensions = ['.py', '.env', '.yml', '.yaml', '.json', '.conf']
        config_files = []
        for ext in config_extensions:
            config_files.extend(self.base_path.rglob(f"*{ext}"))

        for config_file in config_files:
            if "test" in str(config_file) or "__pycache__" in str(config_file):
                continue

            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    result["files_scanned"] += 1

                # Check for credential patterns
                file_vulnerabilities = []
                for pattern, description in credential_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's a placeholder or example
                        match_text = match.group().lower()
                        if any(skip in match_text for skip in ['example', 'placeholder', 'your_', 'xxx', 'localhost']):
                            continue

                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = content.split('\n')[line_num - 1].strip()

                        # Mask the actual credential in the output
                        masked_line = re.sub(r'["\'][^"\']{3,}["\']', "'***MASKED***'", line_content)

                        file_vulnerabilities.append({
                            "line": line_num,
                            "pattern": pattern,
                            "description": description,
                            "code": masked_line
                        })

                if file_vulnerabilities:
                    result["vulnerabilities"].append({
                        "file": str(config_file.relative_to(self.base_path)),
                        "vulnerabilities": file_vulnerabilities
                    })

            except Exception as e:
                print(f"   Error scanning {config_file}: {e}")

        result["total_vulnerabilities"] = sum(len(v["vulnerabilities"]) for v in result["vulnerabilities"])
        result["vulnerable"] = result["total_vulnerabilities"] > 0
        result["risk_level"] = "CRITICAL" if result["total_vulnerabilities"] > 3 else "HIGH"

        return result

    def analyze_database_config_security(self) -> Dict[str, Any]:
        """Analyze database configuration for security issues"""
        print("🔍 Analyzing database configuration security...")

        result = {
            "scan_name": "Database Configuration Analysis",
            "scan_timestamp": datetime.now().isoformat(),
            "config_issues": [],
            "files_analyzed": 0
        }

        # Config files to check
        config_files = [
            "app/core/config.py",
            ".env.dev",
            ".env.prod",
            "docker-compose.yml",
            "alembic.ini"
        ]

        for config_file in config_files:
            file_path = self.base_path / config_file
            if file_path.exists():
                result["files_analyzed"] += 1
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()

                    file_issues = []

                    # Check for insecure database settings
                    if "ssl=false" in content or "sslmode=disable" in content:
                        file_issues.append("Database SSL disabled")

                    if "password=" in content and "encrypt" not in content:
                        file_issues.append("Database password without encryption")

                    if "localhost" in content and "production" in content:
                        file_issues.append("Production database pointing to localhost")

                    if "port=5432" in content and "firewall" not in content:
                        file_issues.append("Default database port exposed without firewall mention")

                    if "connection_timeout" not in content:
                        file_issues.append("Missing database connection timeout")

                    if "max_connections" not in content or "1000" in content:
                        file_issues.append("Potentially unsafe connection limits")

                    if file_issues:
                        result["config_issues"].append({
                            "file": config_file,
                            "issues": file_issues
                        })

                except Exception as e:
                    result["config_issues"].append({
                        "file": config_file,
                        "issues": [f"Error analyzing file: {e}"]
                    })

        result["total_issues"] = sum(len(issues["issues"]) for issues in result["config_issues"])
        result["vulnerable"] = result["total_issues"] > 0
        result["risk_level"] = "HIGH" if result["total_issues"] > 5 else "MEDIUM"

        return result

    def run_comprehensive_database_scan(self) -> Dict[str, Any]:
        """Run comprehensive database security scan"""
        print("🔐 STARTING COMPREHENSIVE DATABASE SECURITY SCAN")
        print("=" * 60)

        results = []

        # Scan 1: SQL Injection vulnerabilities
        results.append(self.scan_code_for_sql_injection())

        # Scan 2: Hardcoded credentials
        results.append(self.check_hardcoded_credentials())

        # Scan 3: Database configuration security
        results.append(self.analyze_database_config_security())

        # Generate summary
        total_vulnerabilities = sum(r.get("total_vulnerabilities", r.get("total_issues", 0)) for r in results)
        vulnerable_scans = len([r for r in results if r.get("vulnerable", False)])

        summary = {
            "total_scans": len(results),
            "vulnerable_scans": vulnerable_scans,
            "total_vulnerabilities": total_vulnerabilities,
            "database_security_score": max(0, 100 - (total_vulnerabilities * 5))
        }

        return {
            "scan_timestamp": datetime.now().isoformat(),
            "scan_results": results,
            "summary": summary
        }

def main():
    """Main execution function"""
    scanner = SimpleDatabaseSecurityScanner()

    try:
        results = scanner.run_comprehensive_database_scan()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 DATABASE SECURITY SCAN REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Scans: {summary['total_scans']}")
        print(f"🚨 Vulnerable Scans: {summary['vulnerable_scans']}")
        print(f"⚠️ Total Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"🎯 Database Security Score: {summary['database_security_score']}/100")

        # Show individual scan results
        for i, scan_result in enumerate(results["scan_results"], 1):
            print(f"\n{i}. {scan_result['scan_name']}:")
            if scan_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {scan_result.get('risk_level', 'HIGH')}")

                vuln_count = scan_result.get("total_vulnerabilities", scan_result.get("total_issues", 0))
                print(f"   📊 Issues Found: {vuln_count}")

                if "vulnerabilities" in scan_result:
                    for vuln in scan_result["vulnerabilities"][:3]:  # Show first 3
                        print(f"      📁 {vuln['file']}: {len(vuln['vulnerabilities'])} issues")
                        for issue in vuln["vulnerabilities"][:2]:  # Show first 2
                            print(f"         • Line {issue['line']}: {issue['description']}")

                if "config_issues" in scan_result:
                    for issue in scan_result["config_issues"][:3]:  # Show first 3
                        print(f"      📁 {issue['file']}: {', '.join(issue['issues'])}")
            else:
                print(f"   ✅ SECURE: No vulnerabilities found")

        # Save detailed report
        import json
        with open("/Users/sheriftito/Downloads/psychsync/database_security_scan_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: database_security_scan_report.json")

    except Exception as e:
        print(f"❌ Error during database security scan: {e}")

if __name__ == "__main__":
    main()
