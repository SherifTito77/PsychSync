#!/usr/bin/env python3
"""
Validation Fixes Verification Script
Tests the fixed validation schemas to ensure they work correctly

Author: Security Team
Version: 1.0
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from pydantic import ValidationError
from app.schemas.auth import UserRegister, PasswordChange, PasswordResetConfirm
from app.services.security import validate_password

def test_password_validation_fixes():
    """Test that password validation now works correctly after schema fixes"""
    print("🔧 TESTING PASSWORD VALIDATION FIXES")
    print("=" * 50)

    test_cases = [
        # (password, should_be_valid, description)
        ("SecurePassword123!", True, "Strong password with all requirements"),
        ("weakpass", False, "Too short and missing requirements"),
        ("nopunctuation123", False, "Missing special character"),
        ("NOlowercase123!", False, "Missing lowercase letter"),
        ("nouppercase123!", False, "Missing uppercase letter"),
        ("NoDigits!", False, "Missing digits"),
        ("password123!", False, "Contains common pattern 'password'"),
        ("SecurePassword123!", False, "Contains common pattern 'password' even with uppercase"),
    ]

    results = []

    print("\n1. TESTING CORE VALIDATION FUNCTION:")
    print("-" * 30)

    for password, expected_valid, description in test_cases:
        try:
            # Test the core validation function
            result = validate_password(password)
            actual_valid = result['valid']

            status = "✅" if actual_valid == expected_valid else "❌"
            print(f"{status} {description}")
            print(f"   Password: '{password}'")
            print(f"   Expected: {expected_valid}, Got: {actual_valid}")
            if result['errors']:
                print(f"   Errors: {result['errors']}")
            if result['warnings']:
                print(f"   Warnings: {result['warnings']}")
            print()

            results.append({
                'test': description,
                'password': password,
                'expected': expected_valid,
                'actual': actual_valid,
                'valid': actual_valid == expected_valid
            })

        except Exception as e:
            print(f"❌ {description}")
            print(f"   Password: '{password}'")
            print(f"   Error: {str(e)}")
            results.append({
                'test': description,
                'password': password,
                'expected': expected_valid,
                'actual': False,
                'valid': False,
                'error': str(e)
            })

    print("\n2. TESTING USER REGISTER SCHEMA:")
    print("-" * 30)

    schema_test_cases = [
        ("SecurePassword123!", "test@example.com", "John Doe", True),
        ("weakpass", "test@example.com", "John Doe", False),
        ("SecurePassword123!", "invalid-email", "John Doe", False),
        ("SecurePassword123!", "test@example.com", "A", False),  # Name too short
    ]

    for password, email, name, should_be_valid in schema_test_cases:
        try:
            user_data = {
                "email": email,
                "full_name": name,
                "password": password
            }
            user = UserRegister(**user_data)

            status = "✅" if should_be_valid else "❌"
            print(f"{status} User Register Schema")
            print(f"   Email: {email}, Name: {name}")
            print(f"   Password: '{password}'")
            print(f"   Expected valid: {should_be_valid}, Got: Valid schema")

        except ValidationError as e:
            status = "✅" if not should_be_valid else "❌"
            print(f"{status} User Register Schema")
            print(f"   Email: {email}, Name: {name}")
            print(f"   Password: '{password}'")
            print(f"   Expected valid: {should_be_valid}, Got: ValidationError")
            print(f"   Error: {e.errors()[0]['msg']}")

        except Exception as e:
            print(f"❌ User Register Schema - Unexpected error: {str(e)}")
        print()

    print("\n3. TESTING PASSWORD CHANGE SCHEMA:")
    print("-" * 30)

    try:
        password_change_data = {
            "current_password": "OldPassword123!",
            "new_password": "SecurePassword123!"
        }
        password_change = PasswordChange(**password_change_data)
        print("✅ Password Change Schema - Valid data accepted")

    except ValidationError as e:
        print(f"❌ Password Change Schema - Unexpected validation error: {e.errors()[0]['msg']}")
    except Exception as e:
        print(f"❌ Password Change Schema - Unexpected error: {str(e)}")

    try:
        password_change_data = {
            "current_password": "OldPassword123!",
            "new_password": "weak"
        }
        password_change = PasswordChange(**password_change_data)
        print("❌ Password Change Schema - Weak password incorrectly accepted")

    except ValidationError as e:
        print("✅ Password Change Schema - Weak password correctly rejected")
        print(f"   Error: {e.errors()[0]['msg']}")
    except Exception as e:
        print(f"❌ Password Change Schema - Unexpected error: {str(e)}")

    print("\n" + "=" * 50)
    print("VALIDATION FIXES VERIFICATION COMPLETE")
    print("=" * 50)

    # Calculate success rate
    successful_tests = sum(1 for r in results if r['valid'])
    total_tests = len(results)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0

    print(f"Core Validation Tests: {successful_tests}/{total_tests} passed ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 VALIDATION FIXES: SUCCESS")
        print("✅ Password validation schema is now working correctly")
    else:
        print("⚠️  VALIDATION FIXES: NEED MORE WORK")
        print("❌ Some validation tests are still failing")

    return success_rate >= 90

if __name__ == "__main__":
    success = test_password_validation_fixes()
    sys.exit(0 if success else 1)
