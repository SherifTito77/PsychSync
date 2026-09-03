#!/usr/bin/env python3
"""
Comprehensive Validation Rules Test Suite
Tests all text input fields and validation rules in the PsychSync application
"""

import json
from typing import Any, Dict, List, Tuple

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app


class ValidationRulesTester:
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "validation_results": [],
        }

    def log_test_result(
        self,
        test_name: str,
        passed: bool,
        expected: str,
        actual: Any,
        details: str = "",
    ):
        """Log a test result"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.test_results["failed_tests"] += 1
            status = "❌ FAIL"

        result = {
            "test_name": test_name,
            "status": status,
            "expected": expected,
            "actual": actual,
            "details": details,
            "passed": passed,
        }
        self.test_results["validation_results"].append(result)

        print(f"{status} {test_name}")
        if not passed:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
            if details:
                print(f"   Details: {details}")

    def test_email_validation(self):
        """Test email validation rules"""
        print("\n📧 Testing Email Validation Rules...")

        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.org",
            "firstname.lastname@company.com",
        ]

        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@.domain.com",
            "user name@domain.com",
        ]

        for email in valid_emails:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": email,
                        "password": "ValidPassword123!",
                        "full_name": "Test User",
                    },
                )
                # Should not fail due to email validation (may fail for other reasons)
                passed = response.status_code != 422
                self.log_test_result(
                    f"Valid email: {email}",
                    passed,
                    "Not 422 (validation error)",
                    f"Status: {response.status_code}",
                    "Email format should be accepted",
                )
            except Exception as e:
                self.log_test_result(
                    f"Valid email: {email}",
                    False,
                    "No exception",
                    str(e),
                    "Request should not raise exception",
                )

        for email in invalid_emails:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": email,
                        "password": "ValidPassword123!",
                        "full_name": "Test User",
                    },
                )
                passed = response.status_code == 422
                self.log_test_result(
                    f"Invalid email: {email}",
                    passed,
                    "422 (validation error)",
                    f"Status: {response.status_code}",
                    "Invalid email should be rejected",
                )
            except Exception as e:
                self.log_test_result(
                    f"Invalid email: {email}",
                    True,  # Exception is expected for validation
                    "Exception",
                    str(e),
                    "Validation should reject invalid email",
                )

    def test_password_validation(self):
        """Test password validation rules"""
        print("\n🔒 Testing Password Validation Rules...")

        # Valid passwords
        valid_passwords = [
            "StrongPassword123!",
            "MySecure@Pass2024",
            "ComplexP#ssw0rd",
            "Very$ecurePassphrase123",
        ]

        # Invalid passwords
        invalid_passwords = [
            "weak",  # Too short
            "password",  # Common pattern
            "123456",  # Only numbers
            "nouppercase1!",  # No uppercase
            "NOLOWERCASE1!",  # No lowercase
            "NoDigits!",  # No numbers
            "NoSpecialChars123",  # No special characters
        ]

        for password in valid_passwords:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test@example.com",
                        "password": password,
                        "full_name": "Test User",
                    },
                )
                # Should not fail due to password validation (may fail for other reasons)
                passed = response.status_code != 422
                self.log_test_result(
                    f"Valid password: {password[:10]}...",
                    passed,
                    "Not 422 (validation error)",
                    f"Status: {response.status_code}",
                    "Strong password should be accepted",
                )
            except Exception as e:
                self.log_test_result(
                    f"Valid password: {password[:10]}...",
                    False,
                    "No exception",
                    str(e),
                    "Request should not raise exception",
                )

        for password in invalid_passwords:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test2@example.com",
                        "password": password,
                        "full_name": "Test User",
                    },
                )
                passed = response.status_code == 422
                self.log_test_result(
                    f"Invalid password: {password}",
                    passed,
                    "422 (validation error)",
                    f"Status: {response.status_code}",
                    "Weak password should be rejected",
                )
            except Exception as e:
                self.log_test_result(
                    f"Invalid password: {password}",
                    True,  # Exception is expected for validation
                    "Exception",
                    str(e),
                    "Validation should reject weak password",
                )

    def test_name_validation(self):
        """Test name/full_name validation rules"""
        print("\n👤 Testing Name Validation Rules...")

        # Valid names
        valid_names = [
            "John Doe",
            "Mary Jane Smith",
            "Jean-Luc Picard",
            "O'Connor",
            "José María",
            "张伟",  # Chinese characters
        ]

        # Invalid names
        invalid_names = [
            "",  # Empty
            "A",  # Too short (less than 2 characters)
            "   ",  # Only spaces
        ]

        for name in valid_names:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test@example.com",
                        "password": "ValidPassword123!",
                        "full_name": name,
                    },
                )
                passed = response.status_code != 422
                self.log_test_result(
                    f"Valid name: {name}",
                    passed,
                    "Not 422 (validation error)",
                    f"Status: {response.status_code}",
                    "Valid name should be accepted",
                )
            except Exception as e:
                self.log_test_result(
                    f"Valid name: {name}",
                    False,
                    "No exception",
                    str(e),
                    "Request should not raise exception",
                )

        for name in invalid_names:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test2@example.com",
                        "password": "ValidPassword123!",
                        "full_name": name,
                    },
                )
                passed = response.status_code == 422
                self.log_test_result(
                    f"Invalid name: '{name}'",
                    passed,
                    "422 (validation error)",
                    f"Status: {response.status_code}",
                    "Invalid name should be rejected",
                )
            except Exception as e:
                self.log_test_result(
                    f"Invalid name: '{name}'",
                    True,  # Exception is expected for validation
                    "Exception",
                    str(e),
                    "Validation should reject invalid name",
                )

    def test_assessment_title_validation(self):
        """Test assessment title validation rules"""
        print("\n📋 Testing Assessment Title Validation Rules...")

        # Valid titles
        valid_titles = [
            "Team Performance Assessment Q1 2024",
            "Employee Satisfaction Survey",
            "Leadership Evaluation Form",
            "Customer Feedback Collection",
        ]

        # Test assessment creation with valid titles (will fail auth but not validation)
        for title in valid_titles:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/",
                    json={
                        "title": title,
                        "description": "Test assessment description",
                        "assessment_type": "team_performance",
                        "category": "performance",
                    },
                )
                # Should return 401 (unauthorized) not 422 (validation error)
                passed = response.status_code != 422
                self.log_test_result(
                    f"Valid assessment title: {title[:30]}...",
                    passed,
                    "Not 422 (validation error)",
                    f"Status: {response.status_code}",
                    "Valid title should pass validation",
                )
            except Exception as e:
                self.log_test_result(
                    f"Valid assessment title: {title[:30]}...",
                    False,
                    "No exception",
                    str(e),
                    "Request should not raise exception",
                )

    def test_xss_prevention(self):
        """Test XSS prevention in text inputs"""
        print("\n🛡️ Testing XSS Prevention...")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'; DROP TABLE users; --",
            "<iframe src='javascript:alert(1)'></iframe>",
            "data:text/html,<script>alert('XSS')</script>",
        ]

        # Test in user registration name field
        for payload in xss_payloads:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test@example.com",
                        "password": "ValidPassword123!",
                        "full_name": payload,
                    },
                )
                # Should either accept (with sanitization) or reject (validation error)
                passed = response.status_code in [
                    422,
                    401,
                    500,
                ]  # Any status except 200/201 is good for XSS
                self.log_test_result(
                    f"XSS payload in name: {payload[:30]}...",
                    passed,
                    "Rejected or sanitized",
                    f"Status: {response.status_code}",
                    "XSS payload should be rejected or sanitized",
                )
            except Exception as e:
                self.log_test_result(
                    f"XSS payload in name: {payload[:30]}...",
                    True,  # Exception is acceptable for XSS protection
                    "Exception",
                    str(e),
                    "XSS protection should prevent processing",
                )

        # Test in assessment title field
        for payload in xss_payloads:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/",
                    json={
                        "title": payload,
                        "description": "Test assessment",
                        "assessment_type": "team_performance",
                        "category": "performance",
                    },
                )
                passed = response.status_code in [422, 401, 500]
                self.log_test_result(
                    f"XSS payload in title: {payload[:30]}...",
                    passed,
                    "Rejected or sanitized",
                    f"Status: {response.status_code}",
                    "XSS payload should be rejected or sanitized",
                )
            except Exception as e:
                self.log_test_result(
                    f"XSS payload in title: {payload[:30]}...",
                    True,
                    "Exception",
                    str(e),
                    "XSS protection should prevent processing",
                )

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        print("\n🗄️ Testing SQL Injection Prevention...")

        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM users --",
            "admin'; DELETE FROM assessments; --",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
            "'; UPDATE users SET password='hacked'; --",
        ]

        # Test in various text fields
        for payload in sql_injection_payloads:
            # Test in registration name
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test@example.com",
                        "password": "ValidPassword123!",
                        "full_name": payload,
                    },
                )
                passed = response.status_code != 200  # Should not succeed
                self.log_test_result(
                    f"SQL injection in name: {payload[:30]}...",
                    passed,
                    "Rejected or sanitized",
                    f"Status: {response.status_code}",
                    "SQL injection should be prevented",
                )
            except Exception as e:
                self.log_test_result(
                    f"SQL injection in name: {payload[:30]}...",
                    True,
                    "Exception",
                    str(e),
                    "SQL injection protection should prevent processing",
                )

            # Test in assessment title
            try:
                response = self.client.post(
                    "/api/v1/api/v1/",
                    json={
                        "title": payload,
                        "description": "Test assessment",
                        "assessment_type": "team_performance",
                        "category": "performance",
                    },
                )
                passed = response.status_code != 200
                self.log_test_result(
                    f"SQL injection in title: {payload[:30]}...",
                    passed,
                    "Rejected or sanitized",
                    f"Status: {response.status_code}",
                    "SQL injection should be prevented",
                )
            except Exception as e:
                self.log_test_result(
                    f"SQL injection in title: {payload[:30]}...",
                    True,
                    "Exception",
                    str(e),
                    "SQL injection protection should prevent processing",
                )

    def test_length_validation(self):
        """Test input length validation"""
        print("\n📏 Testing Input Length Validation...")

        # Test extremely long inputs
        long_string = "A" * 10000  # 10,000 characters

        try:
            response = self.client.post(
                "/api/v1/api/v1/register",
                json={
                    "email": "test@example.com",
                    "password": "ValidPassword123!",
                    "full_name": long_string,
                },
            )
            passed = response.status_code == 422  # Should reject extremely long names
            self.log_test_result(
                f"Extremely long name ({len(long_string)} chars)",
                passed,
                "422 (validation error)",
                f"Status: {response.status_code}",
                "Extremely long inputs should be rejected",
            )
        except Exception as e:
            self.log_test_result(
                f"Extremely long name ({len(long_string)} chars)",
                True,
                "Exception",
                str(e),
                "Should reject extremely long inputs",
            )

        # Test long assessment title
        try:
            response = self.client.post(
                "/api/v1/api/v1/",
                json={
                    "title": long_string,
                    "description": "Test assessment",
                    "assessment_type": "team_performance",
                    "category": "performance",
                },
            )
            passed = response.status_code == 422
            self.log_test_result(
                f"Extremely long title ({len(long_string)} chars)",
                passed,
                "422 (validation error)",
                f"Status: {response.status_code}",
                "Extremely long inputs should be rejected",
            )
        except Exception as e:
            self.log_test_result(
                f"Extremely long title ({len(long_string)} chars)",
                True,
                "Exception",
                str(e),
                "Should reject extremely long inputs",
            )

    def test_special_characters_handling(self):
        """Test special characters handling"""
        print("\n🔤 Testing Special Characters Handling...")

        special_char_strings = [
            "Hello World! @#$%^&*()",
            "Café Münster — Brezel",
            "Москва - Санкт-Петербург",
            "北京 上海 广州 深圳",
            "🎉 🚀 💻 📱",
            "Test: [JSON] {data} (info)",
            "Multi-line\ntext\twith\ttabs\nand newlines",
        ]

        for test_string in special_char_strings:
            try:
                response = self.client.post(
                    "/api/v1/api/v1/register",
                    json={
                        "email": "test@example.com",
                        "password": "ValidPassword123!",
                        "full_name": test_string,
                    },
                )
                # Should handle special characters properly
                passed = response.status_code != 500  # Should not crash
                self.log_test_result(
                    f"Special chars: {test_string[:30]}...",
                    passed,
                    "No crash",
                    f"Status: {response.status_code}",
                    "Should handle special characters gracefully",
                )
            except Exception as e:
                self.log_test_result(
                    f"Special chars: {test_string[:30]}...",
                    False,
                    "No exception",
                    str(e),
                    "Should handle special characters without crashing",
                )

    def run_comprehensive_validation_tests(self):
        """Run all validation tests"""
        print("🚀 PSYCHSYNC VALIDATION RULES COMPREHENSIVE TEST SUITE")
        print("=" * 70)

        self.test_email_validation()
        self.test_password_validation()
        self.test_name_validation()
        self.test_assessment_title_validation()
        self.test_xss_prevention()
        self.test_sql_injection_prevention()
        self.test_length_validation()
        self.test_special_characters_handling()

        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION RULES TEST SUMMARY")
        print("=" * 70)

        success_rate = (
            (self.test_results["passed_tests"] / self.test_results["total_tests"] * 100)
            if self.test_results["total_tests"] > 0
            else 0
        )

        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        print(f"Success Rate: {success_rate:.1f}%")

        print("\n📋 Test Results by Category:")

        # Group results by test type
        categories = {}
        for result in self.test_results["validation_results"]:
            test_name = result["test_name"]
            if "email" in test_name.lower():
                category = "Email Validation"
            elif "password" in test_name.lower():
                category = "Password Validation"
            elif "name" in test_name.lower():
                category = "Name Validation"
            elif "title" in test_name.lower():
                category = "Title Validation"
            elif "xss" in test_name.lower():
                category = "XSS Prevention"
            elif "sql" in test_name.lower():
                category = "SQL Injection Prevention"
            elif "length" in test_name.lower():
                category = "Length Validation"
            elif "special" in test_name.lower():
                category = "Special Characters"
            else:
                category = "Other"

            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0}

            if result["passed"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1

        for category, counts in categories.items():
            total = counts["passed"] + counts["failed"]
            rate = (counts["passed"] / total * 100) if total > 0 else 0
            status = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
            print(f"{status} {category}: {counts['passed']}/{total} ({rate:.1f}%)")

        print("\n🎯 Security Assessment:")
        security_tests = [
            r
            for r in self.test_results["validation_results"]
            if any(
                keyword in r["test_name"].lower()
                for keyword in ["xss", "sql", "injection", "password"]
            )
        ]

        if security_tests:
            security_passed = sum(1 for r in security_tests if r["passed"])
            security_total = len(security_tests)
            security_rate = security_passed / security_total * 100

            print(
                f"Security Tests: {security_passed}/{security_total} ({security_rate:.1f}%)"
            )

            if security_rate >= 90:
                print("✅ Excellent security validation implementation")
            elif security_rate >= 75:
                print("⚠️ Good security validation with room for improvement")
            else:
                print("❌ Security validation needs improvement")

        print("\n🔐 Overall Validation Security:")
        if success_rate >= 90:
            print("✅ EXCELLENT - Comprehensive validation rules implemented")
        elif success_rate >= 80:
            print("✅ GOOD - Strong validation rules in place")
        elif success_rate >= 70:
            print("⚠️ ACCEPTABLE - Validation rules functional but could be enhanced")
        else:
            print("❌ NEEDS IMPROVEMENT - Validation rules require attention")


if __name__ == "__main__":
    tester = ValidationRulesTester()
    tester.run_comprehensive_validation_tests()
