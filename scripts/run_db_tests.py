#!/usr/bin/env python3
"""
Synchronous Database Security Tests - Real-time Output
"""

import json
import re
from datetime import datetime
from pathlib import Path


def test_nosql_injection():
    """Test 1: NoSQL Injection"""
    print("🔍 TEST 1: Testing for NoSQL Injection...")

    base_path = Path("/Users/sheriftito/Downloads/psychsync")
    vulnerabilities = []
    tested_files = 0

    # NoSQL injection patterns
    unsafe_patterns = [
        (r"dict\s*\(\s*\*\*user_input", "Dictionary unpacking with user input"),
        (r"\.find\s*\(\s*\{[^}]*\+\s*\w+", "String concatenation in queries"),
        (r"\.update\s*\(\s*\{[^}]*\$\w+", "Direct use of MongoDB operators"),
        (r"eval\s*\(", "Using eval() with data"),
        (r"exec\s*\(", "Using exec() with data"),
        (r"mongodb://", "MongoDB connection string"),
    ]

    python_files = list(base_path.rglob("*.py"))
    for py_file in python_files[:50]:  # Limit to first 50 for speed
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tested_files += 1

            for pattern, description in unsafe_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    vulnerabilities.append(
                        {
                            "file": str(py_file.relative_to(base_path)),
                            "description": description,
                        }
                    )
                    break

        except Exception:
            pass

    print(f"   📊 Files tested: {tested_files}")
    print(f"   ⚠️  Vulnerabilities: {len(vulnerabilities)}")

    return {
        "test": "NoSQL Injection",
        "vulnerable": len(vulnerabilities) > 0,
        "count": len(vulnerabilities),
        "risk": "HIGH" if vulnerabilities else "LOW",
    }


def test_credential_rotation():
    """Test 2: Credential Rotation"""
    print("🔍 TEST 2: Checking Database Credential Rotation...")

    base_path = Path("/Users/sheriftito/Downloads/psychsync")
    issues = []

    # Check config files
    config_files = [".env.dev", ".env.prod", "app/core/config.py"]
    for config_file in config_files:
        file_path = base_path / config_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Check for hardcoded credentials
                if re.search(
                    r'password\s*=\s*["\'][^"\']{8,}["\']', content, re.IGNORECASE
                ):
                    issues.append(f"Hardcoded password in {config_file}")

                # Check file age
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (datetime.now() - mtime).days
                if age_days > 90:
                    issues.append(f"Stale config ({age_days} days old): {config_file}")

            except Exception:
                pass

    # Check for rotation mechanism in code
    has_rotation = False
    python_files = list(base_path.rglob("*.py"))[:30]
    for py_file in python_files:
        if "test" in str(py_file):
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if re.search(
                r"rotate.*credential|credential.*rotation|cron.*password",
                content,
                re.IGNORECASE,
            ):
                has_rotation = True
                break
        except Exception:
            pass

    if not has_rotation:
        issues.append("No automated credential rotation mechanism found")

    print(f"   📊 Issues found: {len(issues)}")
    print(f"   🔒 Has rotation: {'✅' if has_rotation else '❌'}")

    return {
        "test": "Credential Rotation",
        "vulnerable": len(issues) > 0,
        "count": len(issues),
        "risk": "HIGH" if issues else "MEDIUM",
        "issues": issues,
    }


def test_backup_encryption():
    """Test 3: Backup Encryption"""
    print("🔍 TEST 3: Testing Database Backup Encryption...")

    base_path = Path("/Users/sheriftito/Downloads/psychsync")
    backups = []
    encrypted = 0
    unencrypted = 0

    # Look for backup files
    backup_extensions = [".sql", ".dump", ".backup", ".bak"]
    for ext in backup_extensions:
        backups.extend(list(base_path.rglob(f"*{ext}")))

    for backup in backups:
        if backup.is_file() and backup.stat().st_size > 100:
            try:
                with open(backup, "rb") as f:
                    header = f.read(1024)

                # Check if encrypted
                if b"CREATE TABLE" in header or b"INSERT INTO" in header:
                    unencrypted += 1
                    print(f"   ⚠️  Unencrypted: {backup.name}")
                else:
                    encrypted += 1

            except Exception:
                pass

    print(f"   📊 Backups found: {len(backups)}")
    print(f"   🔒 Encrypted: {encrypted}")
    print(f"   ⚠️  Unencrypted: {unencrypted}")

    return {
        "test": "Backup Encryption",
        "vulnerable": unencrypted > 0,
        "count": unencrypted,
        "risk": "CRITICAL" if unencrypted > 0 else "MEDIUM",
    }


def test_privilege_escalation():
    """Test 4: Privilege Escalation"""
    print("🔍 TEST 4: Testing Database Privilege Escalation...")

    base_path = Path("/Users/sheriftito/Downloads/psychsync")
    escalations = []

    escalation_patterns = [
        (r"SUPERUSER\s*=\s*True", "Superuser privilege"),
        (r"GRANT\s+ALL\s+PRIVILEGES", "All privileges granted"),
        (r"ALTER\s+ROLE.*WITH\s+SUPERUSER", "Superuser elevation"),
        (r"CREATEROLE\s*=\s*True", "Role creation privilege"),
    ]

    python_files = list(base_path.rglob("*.py"))[:50]
    for py_file in python_files:
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pattern, description in escalation_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    escalations.append(
                        {
                            "file": str(py_file.relative_to(base_path)),
                            "description": description,
                        }
                    )
                    break

        except Exception:
            pass

    print(f"   📊 Escalation patterns found: {len(escalations)}")

    return {
        "test": "Privilege Escalation",
        "vulnerable": len(escalations) > 0,
        "count": len(escalations),
        "risk": "HIGH" if escalations else "MEDIUM",
    }


def test_log_security():
    """Test 5: Log Security"""
    print("🔍 TEST 5: Analyzing Logs for Sensitive Data...")

    base_path = Path("/Users/sheriftito/Downloads/psychsync")
    sensitive_findings = []

    # Sensitive data patterns
    sensitive_patterns = {
        "password": r"password\s*[=:]\s*[^\s,}]{4,}",
        "api_key": r"api[_-]?key\s*[=:]\s*[^\s,}]{16,}",
        "token": r"token\s*[=:]\s*[^\s,}]{20,}",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ip": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    }

    # Find log files
    log_files = []
    log_dirs = ["logs", "log", "tmp"]
    for log_dir in log_dirs:
        dir_path = base_path / log_dir
        if dir_path.exists():
            log_files.extend(list(dir_path.rglob("*.log")))

    for log_file in log_files[:10]:  # Limit to 10 logs
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for data_type, pattern in sensitive_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    sensitive_findings.append(
                        {"file": log_file.name, "type": data_type}
                    )
                    break

        except Exception:
            pass

    # Check for debug logging issues
    python_files = list(base_path.rglob("*.py"))[:30]
    debug_issues = 0
    for py_file in python_files:
        if "test" in str(py_file):
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line in lines:
                if re.search(
                    r"logger\.debug.*(password|token|secret|key)", line, re.IGNORECASE
                ):
                    debug_issues += 1
                    break

        except Exception:
            pass

    print(f"   📊 Logs analyzed: {len(log_files)}")
    print(f"   ⚠️  Sensitive data found: {len(sensitive_findings)}")
    print(f"   ⚠️  Debug logging issues: {debug_issues}")

    return {
        "test": "Log Security",
        "vulnerable": len(sensitive_findings) > 0 or debug_issues > 0,
        "count": len(sensitive_findings) + debug_issues,
        "risk": "HIGH" if (sensitive_findings or debug_issues) else "MEDIUM",
    }


def main():
    """Run all database security tests"""
    print("🔐 COMPREHENSIVE DATABASE SECURITY TEST SUITE")
    print("=" * 60)
    print()

    results = []

    # Run all 5 tests
    results.append(test_nosql_injection())
    print()

    results.append(test_credential_rotation())
    print()

    results.append(test_backup_encryption())
    print()

    results.append(test_privilege_escalation())
    print()

    results.append(test_log_security())
    print()

    # Summary
    print("=" * 60)
    print("🔐 DATABASE SECURITY TEST RESULTS")
    print("=" * 60)

    vulnerable_tests = sum(1 for r in results if r["vulnerable"])
    total_issues = sum(r["count"] for r in results)
    security_score = max(0, 100 - (vulnerable_tests * 15) - (total_issues * 2))

    print(f"\n📊 SUMMARY:")
    print(f"   Total Tests: {len(results)}")
    print(f"   Vulnerable: {vulnerable_tests}/{len(results)}")
    print(f"   Total Issues: {total_issues}")
    print(f"   Security Score: {security_score}/100")
    print()

    # Individual results
    for i, result in enumerate(results, 1):
        status = "❌ VULNERABLE" if result["vulnerable"] else "✅ SECURE"
        print(f"{i}. {result['test']}: {status} [{result['risk']}]")
        if result["vulnerable"]:
            print(f"   Issues: {result['count']}")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_tests": len(results),
            "vulnerable_tests": vulnerable_tests,
            "total_issues": total_issues,
            "security_score": security_score,
        },
    }

    with open("database_security_test_results.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved: database_security_test_results.json")


if __name__ == "__main__":
    main()
