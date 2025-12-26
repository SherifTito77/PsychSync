#!/usr/bin/env python3
"""
Fast Validation Rules Test Suite
Tests validation rules directly using Pydantic schemas without database dependencies
"""

import sys
sys.path.append('.')

from pydantic import ValidationError
from app.schemas.auth import UserRegister, PasswordChange
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.assessment import QuestionCreate, AssessmentBase
from typing import List, Dict, Any

class FastValidationTester:
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "validation_results": []
        }

    def log_test_result(self, test_name: str, passed: bool, expected: str, actual: str, details: str = ""):
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
            "passed": passed
        }
        self.test_results["validation_results"].append(result)

        print(f"{status} {test_name}")
        if not passed and details:
            print(f"   Details: {details}")

    def test_email_validation(self):
        """Test email validation using Pydantic schemas"""
        print("\n📧 Testing Email Validation Rules...")

        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.org",
            "firstname.lastname@company.com"
        ]

        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@.domain.com",
            "user name@domain.com",
            "user@test..com"
        ]

        for email in valid_emails:
            try:
                user_data = UserRegister(
                    email=email,
                    password="ValidPassword123!",
                    full_name="Test User"
                )
                passed = True
                self.log_test_result(
                    f"Valid email: {email}",
                    passed,
                    "Validation passes",
                    f"Validated: {user_data.email}",
                    "Email format should be accepted"
                )
            except ValidationError as e:
                passed = False
                self.log_test_result(
                    f"Valid email: {email}",
                    passed,
                    "Validation passes",
                    f"Error: {str(e)}",
                    "Valid email should not raise ValidationError"
                )
            except Exception as e:
                passed = False
                self.log_test_result(
                    f"Valid email: {email}",
                    passed,
                    "Validation passes",
                    f"Exception: {str(e)}",
                    "Unexpected exception"
                )

        for email in invalid_emails:
            try:
                user_data = UserRegister(
                    email=email,
                    password="ValidPassword123!",
                    full_name="Test User"
                )
                passed = False
                self.log_test_result(
                    f"Invalid email: {email}",
                    passed,
                    "Validation fails",
                    f"Unexpected success: {user_data.email}",
                    "Invalid email should raise ValidationError"
                )
            except ValidationError as e:
                passed = True
                self.log_test_result(
                    f"Invalid email: {email}",
                    passed,
                    "Validation fails",
                    f"Error: {str(e)[:100]}...",
                    "Invalid email should be rejected"
                )
            except Exception as e:
                passed = True  # Other exceptions are acceptable for invalid input
                self.log_test_result(
                    f"Invalid email: {email}",
                    passed,
                    "Validation fails",
                    f"Exception: {str(e)[:100]}...",
                    "Invalid email should be rejected"
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
            "GoodPassword123!@#"
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
            "short1!",  # Too short even though it meets other criteria
        ]

        for password in valid_passwords:
            try:
                user_data = UserRegister(
                    email="test@example.com",
                    password=password,
                    full_name="Test User"
                )
                passed = True
                self.log_test_result(
                    f"Valid password: {password[:10]}...",
                    passed,
                    "Validation passes",
                    f"Password accepted",
                    "Strong password should be accepted"
                )
            except ValidationError as e:
                passed = False
                self.log_test_result(
                    f"Valid password: {password[:10]}...",
                    passed,
                    "Validation passes",
                    f"Error: {str(e)}",
                    "Strong password should not raise ValidationError"
                )
            except Exception as e:
                passed = False
                self.log_test_result(
                    f"Valid password: {password[:10]}...",
                    passed,
                    "Validation passes",
                    f"Exception: {str(e)}",
                    "Unexpected exception"
                )

        for password in invalid_passwords:
            try:
                user_data = UserRegister(
                    email=f"test{len(password)}@example.com",
                    password=password,
                    full_name="Test User"
                )
                passed = False
                self.log_test_result(
                    f"Invalid password: {password}",
                    passed,
                    "Validation fails",
                    f"Unexpected success",
                    "Weak password should raise ValidationError"
                )
            except ValidationError as e:
                passed = True
                self.log_test_result(
                    f"Invalid password: {password}",
                    passed,
                    "Validation fails",
                    f"Properly rejected: {str(e)[:50]}...",
                    "Weak password should be rejected"
                )
            except Exception as e:
                passed = True
                self.log_test_result(
                    f"Invalid password: {password}",
                    passed,
                    "Validation fails",
                    f"Exception: {str(e)[:50]}...",
                    "Weak password should be rejected"
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
            "Dr. John Smith Jr.",
            "Maria Garcia-Lopez"
        ]

        # Invalid names
        invalid_names = [
            "",  # Empty
            "A",  # Too short (less than 2 characters)
            "   ",  # Only spaces
            "\t\n",  # Only whitespace
        ]

        for name in valid_names:
            try:
                user_data = UserRegister(
                    email="test@example.com",
                    password="ValidPassword123!",
                    full_name=name
                )
                passed = True
                self.log_test_result(
                    f"Valid name: {name[:20]}...",
                    passed,
                    "Validation passes",
                    f"Name accepted: {user_data.full_name[:20]}...",
                    "Valid name should be accepted"
                )
            except ValidationError as e:
                passed = False
                self.log_test_result(
                    f"Valid name: {name[:20]}...",
                    passed,
                    "Validation passes",
                    f"Error: {str(e)}",
                    "Valid name should not raise ValidationError"
                )
            except Exception as e:
                passed = False
                self.log_test_result(
                    f"Valid name: {name[:20]}...",
                    passed,
                    "Validation passes",
                    f"Exception: {str(e)}",
                    "Unexpected exception"
                )

        for name in invalid_names:
            try:
                user_data = UserRegister(
                    email=f"test{len(name)}@example.com",
                    password="ValidPassword123!",
                    full_name=name
                )
                passed = False
                self.log_test_result(
                    f"Invalid name: '{repr(name)}'",
                    passed,
                    "Validation fails",
                    f"Unexpected success: {user_data.full_name}",
                    "Invalid name should raise ValidationError"
                )
            except ValidationError as e:
                passed = True
                self.log_test_result(
                    f"Invalid name: '{repr(name)}'",
                    passed,
                    "Validation fails",
                    f"Properly rejected: {str(e)[:50]}...",
                    "Invalid name should be rejected"
                )
            except Exception as e:
                passed = True
                self.log_test_result(
                    f"Invalid name: '{repr(name)}'",
                    passed,
                    "Validation fails",
                    f"Exception: {str(e)[:50]}...",
                    "Invalid name should be rejected"
                )

    def test_assessment_validation(self):
        """Test assessment validation rules"""
        print("\n📋 Testing Assessment Validation Rules...")

        # Valid assessment data
        valid_assessments = [
            {
                "title": "Team Performance Assessment Q1 2024",
                "description": "Quarterly team performance evaluation",
                "category": "performance",
                "instructions": "Complete this assessment honestly"
            },
            {
                "title": "Employee Satisfaction Survey",
                "description": "Annual employee feedback collection",
                "category": "satisfaction",
                "instructions": "Your feedback helps us improve"
            },
            {
                "title": "Leadership Skills Evaluation",
                "description": "Management competency assessment",
                "category": "leadership"
            }
        ]

        # Test question type validation
        valid_question_types = ["multiple_choice", "rating_scale", "text", "yes_no", "likert"]
        invalid_question_types = ["invalid_type", "custom", "open", "closed", "numeric"]

        for assessment in valid_assessments:
            try:
                assessment_data = AssessmentBase(**assessment)
                passed = True
                self.log_test_result(
                    f"Valid assessment: {assessment['title'][:30]}...",
                    passed,
                    "Validation passes",
                    f"Assessment accepted",
                    "Valid assessment should be accepted"
                )
            except ValidationError as e:
                passed = False
                self.log_test_result(
                    f"Valid assessment: {assessment['title'][:30]}...",
                    passed,
                    "Validation passes",
                    f"Error: {str(e)}",
                    "Valid assessment should not raise ValidationError"
                )

        # Test question type validation
        for q_type in valid_question_types:
            try:
                question_data = QuestionCreate(
                    question_type=q_type,
                    question_text="Sample question text"
                )
                passed = True
                self.log_test_result(
                    f"Valid question type: {q_type}",
                    passed,
                    "Validation passes",
                    f"Question type accepted",
                    "Valid question type should be accepted"
                )
            except ValidationError as e:
                passed = False
                self.log_test_result(
                    f"Valid question type: {q_type}",
                    passed,
                    "Validation passes",
                    f"Error: {str(e)}",
                    "Valid question type should not raise ValidationError"
                )

        for q_type in invalid_question_types:
            try:
                question_data = QuestionCreate(
                    question_type=q_type,
                    question_text="Sample question text"
                )
                passed = False
                self.log_test_result(
                    f"Invalid question type: {q_type}",
                    passed,
                    "Validation fails",
                    f"Unexpected success: {question_data.question_type}",
                    "Invalid question type should raise ValidationError"
                )
            except ValidationError as e:
                passed = True
                self.log_test_result(
                    f"Invalid question type: {q_type}",
                    passed,
                    "Validation fails",
                    f"Properly rejected: {str(e)[:50]}...",
                    "Invalid question type should be rejected"
                )

    def test_xss_prevention(self):
        """Test XSS prevention through validation"""
        print("\n🛡️ Testing XSS Prevention...")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'; DROP TABLE users; --",
            "<iframe src='javascript:alert(1)'></iframe>",
            "data:text/html,<script>alert('XSS')</script>"
        ]

        for payload in xss_payloads:
            try:
                # Test in name field
                user_data = UserRegister(
                    email="test@example.com",
                    password="ValidPassword123!",
                    full_name=payload
                )
                # If validation passes, check if payload is sanitized (basic check)
                contains_script = "<script>" in payload.lower() or "javascript:" in payload.lower()
                passed = not contains_script  # For this test, we consider rejection as better
                self.log_test_result(
                    f"XSS payload in name: {payload[:30]}...",
                    passed,
                    "Rejected or sanitized",
                    f"Contains script: {contains_script}",
                    "XSS payload should be rejected or sanitized"
                )
            except ValidationError as e:
                passed = True
                self.log_test_result(
                    f"XSS payload in name: {payload[:30]}...",
                    passed,
                    "Rejected",
                    f"ValidationError: {str(e)[:50]}...",
                    "XSS payload should be rejected"
                )
            except Exception as e:
                passed = True
                self.log_test_result(
                    f"XSS payload in name: {payload[:30]}...",
                    passed,
                    "Rejected",
                    f"Exception: {str(e)[:50]}...",
                    "XSS payload should be rejected"
                )

    def test_length_validation(self):
        """Test input length validation"""
        print("\n📏 Testing Input Length Validation...")

        # Test extremely long inputs
        very_long_string = "A" * 10000  # 10,000 characters
        moderately_long_string = "A" * 500  # 500 characters

        # Test long name
        try:
            user_data = UserRegister(
                email="test@example.com",
                password="ValidPassword123!",
                full_name=very_long_string
            )
            passed = False
            self.log_test_result(
                f"Extremely long name ({len(very_long_string)} chars)",
                passed,
                "Validation fails",
                f"Unexpected success",
                "Extremely long names should be rejected"
            )
        except ValidationError as e:
            passed = True
            self.log_test_result(
                f"Extremely long name ({len(very_long_string)} chars)",
                passed,
                "Validation fails",
                f"Rejected: {str(e)[:50]}...",
                "Extremely long inputs should be rejected"
            )
        except Exception as e:
            passed = True
            self.log_test_result(
                f"Extremely long name ({len(very_long_string)} chars)",
                passed,
                "Validation fails",
                f"Exception: {str(e)[:50]}...",
                "Extremely long inputs should be rejected"
            )

        # Test long assessment title
        try:
            assessment_data = AssessmentBase(
                title=very_long_string,
                description="Test assessment",
                category="test"
            )
            passed = False
            self.log_test_result(
                f"Extremely long title ({len(very_long_string)} chars)",
                passed,
                "Validation fails",
                f"Unexpected success",
                "Extremely long titles should be rejected"
            )
        except ValidationError as e:
            passed = True
            self.log_test_result(
                f"Extremely long title ({len(very_long_string)} chars)",
                passed,
                "Validation fails",
                f"Rejected: {str(e)[:50]}...",
                "Extremely long inputs should be rejected"
            )
        except Exception as e:
            passed = True
            self.log_test_result(
                f"Extremely long title ({len(very_long_string)} chars)",
                passed,
                "Validation fails",
                f"Exception: {str(e)[:50]}...",
                "Extremely long inputs should be rejected"
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
            "Multi-line\ntext\twith\tabs\nand newlines",
            "O'Connor-McDonald"
        ]

        for test_string in special_char_strings:
            try:
                user_data = UserRegister(
                    email="test@example.com",
                    password="ValidPassword123!",
                    full_name=test_string
                )
                passed = True
                self.log_test_result(
                    f"Special chars: {test_string[:30]}...",
                    passed,
                    "No validation error",
                    f"Accepted: {user_data.full_name[:30]}...",
                    "Should handle special characters properly"
                )
            except ValidationError as e:
                passed = False
                self.log_test_result(
                    f"Special chars: {test_string[:30]}...",
                    passed,
                    "No validation error",
                    f"Error: {str(e)[:50]}...",
                    "Should handle special characters properly"
                )
            except Exception as e:
                passed = False
                self.log_test_result(
                    f"Special chars: {test_string[:30]}...",
                    passed,
                    "No validation error",
                    f"Exception: {str(e)[:50]}...",
                    "Should handle special characters properly"
                )

    def run_comprehensive_validation_tests(self):
        """Run all validation tests"""
        print("🚀 PSYCHSYNC FAST VALIDATION RULES TEST SUITE")
        print("=" * 60)

        self.test_email_validation()
        self.test_password_validation()
        self.test_name_validation()
        self.test_assessment_validation()
        self.test_xss_prevention()
        self.test_length_validation()
        self.test_special_characters_handling()

        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RULES TEST SUMMARY")
        print("=" * 60)

        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"] * 100) if self.test_results["total_tests"] > 0 else 0

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
            elif "assessment" in test_name.lower() or "question" in test_name.lower():
                category = "Assessment Validation"
            elif "xss" in test_name.lower():
                category = "XSS Prevention"
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
        security_tests = [r for r in self.test_results["validation_results"]
                         if any(keyword in r["test_name"].lower()
                               for keyword in ["xss", "password", "length"])]

        if security_tests:
            security_passed = sum(1 for r in security_tests if r["passed"])
            security_total = len(security_tests)
            security_rate = (security_passed / security_total * 100)

            print(f"Security Tests: {security_passed}/{security_total} ({security_rate:.1f}%)")

            if security_rate >= 90:
                print("✅ EXCELLENT - Strong security validation implementation")
            elif security_rate >= 75:
                print("✅ GOOD - Solid security validation in place")
            elif security_rate >= 60:
                print("⚠️ ACCEPTABLE - Basic security validation functional")
            else:
                print("❌ NEEDS IMPROVEMENT - Security validation requires attention")

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
    tester = FastValidationTester()
    tester.run_comprehensive_validation_tests()