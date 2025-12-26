#!/usr/bin/env python3
"""
COMPREHENSIVE ENCRYPTION SECURITY TEST SUITE
Tests all cryptographic implementations in the PsychSync platform

Tests:
1. Password hashing algorithm (bcrypt/Argon2)
2. Database field encryption
3. Secure random token generation
4. Weak cipher detection
5. Encryption key rotation

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import os
import sys
import re
import json
import hashlib
import secrets
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class TestResult:
    """Result of a security test"""
    test_name: str
    status: str  # PASS, FAIL, WARN, INFO
    score: int  # 0-100
    findings: List[str]
    recommendations: List[str]
    details: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


class EncryptionSecurityTester:
    """Comprehensive encryption security testing suite"""

    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        self.results: List[TestResult] = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all encryption security tests"""
        print("=" * 80)
        print("🔐 COMPREHENSIVE ENCRYPTION SECURITY TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print()

        # Test 1: Password hashing algorithm
        print("🔍 TEST 1: Verifying password hashing algorithm...")
        result1 = self.test_password_hashing()
        self.results.append(result1)
        self.print_test_result(result1)

        # Test 2: Database field encryption
        print("\n🔍 TEST 2: Checking database field encryption...")
        result2 = self.test_database_field_encryption()
        self.results.append(result2)
        self.print_test_result(result2)

        # Test 3: Secure random token generation
        print("\n🔍 TEST 3: Testing secure random token generation...")
        result3 = self.test_secure_token_generation()
        self.results.append(result3)
        self.print_test_result(result3)

        # Test 4: Weak cipher detection
        print("\n🔍 TEST 4: Testing for weak ciphers...")
        result4 = self.test_weak_ciphers()
        self.results.append(result4)
        self.print_test_result(result4)

        # Test 5: Encryption key rotation
        print("\n🔍 TEST 5: Checking encryption key rotation...")
        result5 = self.test_encryption_key_rotation()
        self.results.append(result5)
        self.print_test_result(result5)

        # Generate summary report
        return self.generate_summary_report()

    def test_password_hashing(self) -> TestResult:
        """Test 1: Verify passwords use salted bcrypt or Argon2"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check security.py for password hashing configuration
            security_file = self.project_root / "app" / "core" / "security.py"

            if not security_file.exists():
                findings.append("❌ security.py not found")
                return TestResult(
                    test_name="Password Hashing Algorithm",
                    status="FAIL",
                    score=0,
                    findings=findings,
                    recommendations=["Implement bcrypt or Argon2 password hashing"],
                    details={}
                )

            content = security_file.read_text()

            # Check for bcrypt
            bcrypt_found = "bcrypt" in content.lower()
            argon2_found = "argon2" in content.lower()
            passlib_found = "passlib" in content.lower()

            # Check for CryptContext configuration
            pwd_context_match = re.search(
                r'pwd_context\s*=\s*CryptContext\s*\(\s*schemes\s*=\s*\[(.*?)\]',
                content,
                re.DOTALL
            )

            if pwd_context_match:
                schemes = pwd_context_match.group(1)
                details["schemes"] = schemes.strip()

                if "bcrypt" in schemes.lower():
                    findings.append("✅ Using bcrypt for password hashing")
                    score += 40

                    # Check bcrypt rounds
                    rounds_match = re.search(r'bcrypt__rounds\s*=\s*(\d+)', content)
                    if rounds_match:
                        rounds = int(rounds_match.group(1))
                        details["bcrypt_rounds"] = rounds

                        if rounds >= 12:
                            findings.append(f"✅ bcrypt rounds: {rounds} (secure)")
                            score += 20
                        elif rounds >= 10:
                            findings.append(f"⚠️  bcrypt rounds: {rounds} (adequate, recommend 12+)")
                            score += 15
                        else:
                            findings.append(f"⚠️  bcrypt rounds: {rounds} (weak, recommend 12+)")
                            score += 10
                            recommendations.append("Increase bcrypt rounds to at least 12")

                else:
                    findings.append(f"⚠️  CryptContext configured but not using bcrypt: {schemes}")
                    recommendations.append("Configure bcrypt as the default password hashing algorithm")

            # Check for salt
            if "salt" in content.lower() or bcrypt_found:
                findings.append("✅ Password hashing includes salt (bcrypt auto-generates salt)")
                score += 20

            # Check for deprecated algorithms
            weak_algorithms = ["md5", "sha1", "crypt"]
            weak_found = []
            for algo in weak_algorithms:
                if algo in content.lower() and f"hash.{algo}" in content.lower():
                    weak_found.append(algo)

            if weak_found:
                findings.append(f"❌ Weak algorithms found: {', '.join(weak_found)}")
                recommendations.append("Remove all MD5, SHA1, and crypt usage")
                score -= 30
            else:
                findings.append("✅ No weak algorithms (MD5, SHA1, crypt) detected")
                score += 20

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            if not recommendations:
                recommendations.append("Continue monitoring for best practices in password hashing")

            return TestResult(
                test_name="Password Hashing Algorithm",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Password Hashing Algorithm",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_database_field_encryption(self) -> TestResult:
        """Test 2: Check DB fields that should be encrypted"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check for encrypted field patterns in models
            models_dir = self.project_root / "app" / "db" / "models"

            if not models_dir.exists():
                findings.append("❌ Models directory not found")
                return TestResult(
                    test_name="Database Field Encryption",
                    status="ERROR",
                    score=0,
                    findings=findings,
                    recommendations=["Check database models directory structure"],
                    details={}
                )

            # Sensitive fields that should be encrypted
            sensitive_fields = [
                "ssn", "social_security", "credit_card", "password", "secret",
                "token", "api_key", "full_name", "phone", "address", "email",
                "date_of_birth", "dob", "mfa", "backup_code"
            ]

            encrypted_fields_found = []
            unencrypted_sensitive_fields = []

            # Scan all model files
            for model_file in models_dir.glob("*.py"):
                content = model_file.read_text()

                # Find encrypted columns
                encrypted_matches = re.findall(
                    r'(\w+)\s*=\s*Column\s*\([^)]*encrypted[^)]*\)',
                    content,
                    re.IGNORECASE
                )
                encrypted_fields_found.extend(encrypted_matches)

                # Check for sensitive fields without encryption
                for sensitive in sensitive_fields:
                    # Look for column definitions with sensitive names
                    # but NOT marked as encrypted
                    pattern = rf'{sensitive}\w*\s*=\s*Column\s*\((?!.*encrypted.*?)(?!.*hash.*?)'
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's a hash (which is acceptable for passwords)
                        if "hash" not in content.lower() or sensitive not in ["password", "pass"]:
                            unencrypted_sensitive_fields.append({
                                "file": model_file.name,
                                "field": sensitive
                            })

            details["encrypted_fields_count"] = len(encrypted_fields_found)
            details["encrypted_fields"] = list(set(encrypted_fields_found))[:20]  # First 20
            details["unencrypted_sensitive_fields"] = unencrypted_sensitive_fields[:10]

            # Score based on findings
            if len(encrypted_fields_found) > 0:
                findings.append(f"✅ Found {len(encrypted_fields_found)} encrypted field(s)")
                score += 40

            # Check for Fernet or other encryption usage
            fernet_found = False
            for model_file in models_dir.glob("*.py"):
                if "Fernet" in model_file.read_text():
                    fernet_found = True
                    break

            if fernet_found:
                findings.append("✅ Using Fernet encryption (AES-128)")
                score += 30
            else:
                findings.append("⚠️  Fernet encryption not found in models")
                recommendations.append("Use Fernet (AES-128) or stronger for field encryption")
                score += 10

            # Check for unencrypted sensitive fields
            if len(unencrypted_sensitive_fields) == 0:
                findings.append("✅ No unencrypted sensitive fields detected")
                score += 30
            else:
                findings.append(f"⚠️  Found {len(unencrypted_sensitive_fields)} potentially unencrypted sensitive field(s)")
                for field in unencrypted_sensitive_fields[:5]:
                    findings.append(f"   - {field['file']}: {field['field']}")
                recommendations.append("Encrypt all sensitive PII fields at rest")
                score -= 20

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Database Field Encryption",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Database Field Encryption",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_secure_token_generation(self) ->TestResult:
        """Test 3: Test secure random token generation"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check for insecure random usage
            insecure_patterns = [
                (r'random\.random\(\)', "random.random() - not cryptographically secure"),
                (r'random\.randint\(', "random.randint() - not cryptographically secure"),
                (r'random\.choice\(', "random.choice() - not cryptographically secure"),
            ]

            secure_patterns = [
                (r'secrets\.token_[a-z]+\(', "secrets.token_*() - cryptographically secure"),
                (r'secrets\.choice\(', "secrets.choice() - cryptographically secure"),
                (r'secrets\.randbelow\(', "secrets.randbelow() - cryptographically secure"),
                (r'os\.urandom\(', "os.urandom() - cryptographically secure"),
            ]

            insecure_usage = []
            secure_usage = []

            # Scan Python files
            for py_file in self.project_root.rglob("*.py"):
                # Skip test files and virtual environments
                if "test" in str(py_file) or "venv" in str(py_file) or ".venv" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()

                    # Check for insecure patterns
                    for pattern, desc in insecure_patterns:
                        if re.search(pattern, content):
                            insecure_usage.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "pattern": desc
                            })

                    # Check for secure patterns
                    for pattern, desc in secure_patterns:
                        if re.search(pattern, content):
                            secure_usage.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "pattern": desc
                            })
                except Exception:
                    continue

            details["secure_usage_count"] = len(secure_usage)
            details["insecure_usage_count"] = len(insecure_usage)

            # Score findings
            if len(secure_usage) > 0:
                findings.append(f"✅ Found {len(secure_usage)} secure token generation usage(s)")
                score += 50

            if len(insecure_usage) == 0:
                findings.append("✅ No insecure random number generation detected")
                score += 50
            else:
                findings.append(f"❌ Found {len(insecure_usage)} insecure random usage(s)")
                for usage in insecure_usage[:5]:
                    findings.append(f"   - {usage['file']}: {usage['pattern']}")
                recommendations.append("Replace all 'random' module usage with 'secrets' module")
                score -= 30

            # Test token generation quality
            print("\n   🧪 Testing token generation quality...")
            test_tokens = []
            for _ in range(10):
                token = secrets.token_urlsafe(32)
                test_tokens.append(token)

            # Check for randomness (basic check for duplicates)
            unique_tokens = len(set(test_tokens))
            if unique_tokens == 10:
                findings.append("✅ Token generation test: all tokens unique")
                score += 10
            else:
                findings.append(f"❌ Token generation test: found duplicate tokens")
                score -= 20

            # Check token entropy
            token_length = len(test_tokens[0])
            details["test_token_length"] = token_length
            details["test_token_bytes"] = token_length * 3 // 4  # base64 encoding

            if token_length >= 32:
                findings.append(f"✅ Token length: {token_length} chars (secure)")
                score += 10
            else:
                findings.append(f"⚠️  Token length: {token_length} chars (recommend 32+)")
                score += 5

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Secure Random Token Generation",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Secure Random Token Generation",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_weak_ciphers(self) -> TestResult:
        """Test 4: Test for weak ciphers"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Known weak ciphers and algorithms
            weak_crypto = [
                ("DES", "Data Encryption Standard - 56-bit key, broken"),
                ("RC4", "Rivest Cipher 4 - broken, prohibited"),
                ("MD5", "Message Digest 5 - broken, collisions possible"),
                ("SHA1", "Secure Hash Algorithm 1 - deprecated, broken"),
                ("ECB", "Electronic Codebook mode - not semantically secure"),
                ("blowfish", "Blowfish - has weak keys, deprecated"),
            ]

            weak_crypto_found = []

            # Scan Python files for weak crypto
            for py_file in self.project_root.rglob("*.py"):
                if "test" in str(py_file) or "venv" in str(py_file) or ".venv" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()

                    for cipher, desc in weak_crypto:
                        # Check for cipher usage
                        if re.search(rf'\b{cipher}\b', content, re.IGNORECASE):
                            weak_crypto_found.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "cipher": cipher,
                                "description": desc
                            })
                except Exception:
                    continue

            details["weak_crypto_found"] = weak_crypto_found[:10]

            # Score findings
            if len(weak_crypto_found) == 0:
                findings.append("✅ No weak ciphers detected")
                score += 50
            else:
                findings.append(f"❌ Found {len(weak_crypto_found)} weak cipher usage(s)")
                for crypto in weak_crypto_found[:5]:
                    findings.append(f"   - {crypto['file']}: {crypto['cipher']} ({crypto['description']})")
                recommendations.append("Remove all weak cipher usage")
                score -= 40

            # Check for strong crypto
            strong_crypto = []

            for py_file in self.project_root.rglob("*.py"):
                if "test" in str(py_file) or "venv" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()

                    if "AES" in content or "Fernet" in content:
                        strong_crypto.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "algorithm": "AES/Fernet"
                        })

                    if "SHA256" in content or "SHA512" in content:
                        strong_crypto.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "algorithm": "SHA256/SHA512"
                        })
                except Exception:
                    continue

            if len(strong_crypto) > 0:
                findings.append(f"✅ Found {len(set(c['file'] for c in strong_crypto))} files using strong crypto")
                score += 40

            # Check JWT algorithm
            settings_file = self.project_root / "app" / "core" / "config" / "settings.py"
            if settings_file.exists():
                content = settings_file.read_text()
                jwt_match = re.search(r'JWT_ALGORITHM[^=]*=\s*[\""]([^\"\']+)[\""]', content)
                if jwt_match:
                    jwt_algo = jwt_match.group(1)
                    details["jwt_algorithm"] = jwt_algo

                    if jwt_algo in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]:
                        findings.append(f"✅ JWT algorithm: {jwt_algo} (secure)")
                        score += 10
                    elif jwt_algo in ["none", "None", "NONE"]:
                        findings.append(f"❌ JWT algorithm: {jwt_algo} (CRITICAL - no signature!)")
                        recommendations.append("Immediately change JWT algorithm to HS256 or RS256")
                        score -= 50
                    else:
                        findings.append(f"⚠️  JWT algorithm: {jwt_algo} (verify security)")
                        score += 5

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Weak Cipher Detection",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Weak Cipher Detection",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_encryption_key_rotation(self) -> TestResult:
        """Test 5: Check if encryption keys are rotated"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check for credential rotation module
            rotation_file = self.project_root / "app" / "core" / "credential_rotation.py"

            if rotation_file.exists():
                findings.append("✅ Credential rotation module exists")
                score += 30

                content = rotation_file.read_text()

                # Check for rotation interval
                interval_match = re.search(r'rotation.*interval.*(\d+)\s*(day|week|month|hour)', content, re.IGNORECASE)
                if interval_match:
                    interval = interval_match.group(0)
                    findings.append(f"✅ Key rotation interval configured: {interval}")
                    score += 30
                    details["rotation_interval"] = interval
                else:
                    findings.append("⚠️  Rotation interval not clearly defined")
                    score += 15

                # Check for automated rotation
                if "cron" in content.lower() or "schedule" in content.lower():
                    findings.append("✅ Automated rotation scheduling available")
                    score += 20
                else:
                    findings.append("⚠️  Automated scheduling not found")
                    recommendations.append("Implement automated key rotation scheduling")
                    score += 10

            else:
                findings.append("❌ Credential rotation module not found")
                recommendations.append("Implement encryption key rotation mechanism")
                score += 0

            # Check for key generation patterns
            key_generation_found = False
            for py_file in self.project_root.rglob("*.py"):
                if "test" in str(py_file) or "venv" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()

                    # Check for secure key generation
                    if re.search(r'secrets\.(token_[a-z]+|choice|randbelow)', content):
                        key_generation_found = True
                        break

                    if re.search(r'os\.urandom', content):
                        key_generation_found = True
                        break
                except Exception:
                    continue

            if key_generation_found:
                findings.append("✅ Secure key generation patterns found")
                score += 20
            else:
                findings.append("⚠️  Secure key generation not clearly found")
                score += 10

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            if not recommendations:
                recommendations.append("Consider implementing automated key rotation")

            return TestResult(
                test_name="Encryption Key Rotation",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Encryption Key Rotation",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def print_test_result(self, result: TestResult):
        """Print formatted test result"""
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️ ",
            "INFO": "ℹ️ ",
            "ERROR": "🔥"
        }

        emoji = status_emoji.get(result.status, "❓")

        for finding in result.findings:
            print(f"   {finding}")

        if result.recommendations:
            print(f"\n   💡 Recommendations:")
            for rec in result.recommendations:
                print(f"      - {rec}")

        print(f"\n   📊 Score: {result.score}/100")

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report"""
        print("\n" + "=" * 80)
        print("📋 SUMMARY REPORT")
        print("=" * 80)

        total_score = sum(r.score for r in self.results)
        avg_score = total_score / len(self.results) if self.results else 0

        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARN")
        failed = sum(1 for r in self.results if r.status in ["FAIL", "ERROR"])

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Passed: {passed} ✅")
        print(f"Warnings: {warned} ⚠️")
        print(f"Failed: {failed} ❌")
        print(f"\nOverall Security Score: {avg_score:.1f}/100")

        # Determine overall status
        if avg_score >= 80:
            overall_status = "SECURE ✅"
            color = "🟢"
        elif avg_score >= 60:
            overall_status = "ADEQUATE ⚠️"
            color = "🟡"
        else:
            overall_status = "AT RISK ❌"
            color = "🔴"

        print(f"Overall Status: {color} {overall_status}")
        print(f"\nCompleted at: {datetime.now().isoformat()}")

        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(avg_score, 2),
            "overall_status": overall_status,
            "test_results": [r.to_dict() for r in self.results],
            "summary": {
                "total_tests": len(self.results),
                "passed": passed,
                "warnings": warned,
                "failed": failed
            }
        }

        report_file = self.project_root / "encryption_security_test_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file.name}")

        return report


def main():
    """Main entry point"""
    tester = EncryptionSecurityTester()
    report = tester.run_all_tests()

    # Exit with appropriate code
    avg_score = report["overall_score"]
    if avg_score < 60:
        sys.exit(1)  # Exit with error if security is poor
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
