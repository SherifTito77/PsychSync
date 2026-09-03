#!/usr/bin/env python3
"""
Quick validation script for retry logic improvements.

This script validates that:
1. All modified files exist and are syntactically correct
2. Configuration is accessible
3. Basic retry patterns are implemented

Run with: python validate_retry_improvements.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def validate_file_syntax(filepath):
    """Validate that a Python file has correct syntax"""
    try:
        with open(filepath, "r") as f:
            compile(f.read(), filepath, "exec")
        return True, "✓ Syntax valid"
    except SyntaxError as e:
        return False, f"✗ Syntax error: {e}"


def main():
    print("=" * 70)
    print("RETRY LOGIC IMPROVEMENTS VALIDATION")
    print("=" * 70)
    print()

    # Files that should be modified
    modified_files = [
        "app/services/ai_insights_service.py",
        "app/services/push_notification_service.py",
        "app/core/siem_integration.py",
        "app/services/database_backup_service.py",
        "app/core/config/settings.py",
    ]

    # Files that should be created
    created_files = [
        "tests/integrations/test_external_service_retry.py",
        "app/core/monitoring/retry_metrics.py",
        "RETRY_LOGIC_IMPROVEMENTS.md",
        "RETRY_IMPROVEMENTS_SUMMARY.md",
    ]

    print("1. VALIDATING MODIFIED FILES")
    print("-" * 70)

    all_valid = True
    for filepath in modified_files:
        full_path = Path(filepath)
        if not full_path.exists():
            print(f"✗ {filepath}: File not found")
            all_valid = False
            continue

        valid, message = validate_file_syntax(full_path)
        status = "✓" if valid else "✗"
        print(f"{status} {filepath}: {message}")
        if not valid:
            all_valid = False

    print()
    print("2. VALIDATING CREATED FILES")
    print("-" * 70)

    for filepath in created_files:
        full_path = Path(filepath)
        if not full_path.exists():
            print(f"✗ {filepath}: File not found")
            all_valid = False
            continue

        valid, message = validate_file_syntax(full_path)
        status = "✓" if valid else "✗"
        print(f"{status} {filepath}: {message}")
        if not valid:
            all_valid = False

    print()
    print("3. CHECKING KEY IMPLEMENTATIONS")
    print("-" * 70)

    # Check AI Insights Service for tenacity
    try:
        with open("app/services/ai_insights_service.py", "r") as f:
            content = f.read()
            if "@retry" in content and "tenacity" in content:
                print("✓ AI Insights Service: Tenacity retry decorator present")
            else:
                print("✗ AI Insights Service: Tenacity retry decorator missing")
                all_valid = False
    except Exception as e:
        print(f"✗ AI Insights Service: Error checking: {e}")
        all_valid = False

    # Check Push Notification Service for resilient client
    try:
        with open("app/services/push_notification_service.py", "r") as f:
            content = f.read()
            if "resilient_http_client" in content:
                print(
                    "✓ Push Notification Service: Resilient HTTP client usage present"
                )
            else:
                print("✗ Push Notification Service: Resilient HTTP client missing")
                all_valid = False

            if "self.timeout = 20.0" in content:
                print("✓ Push Notification Service: Timeout increased to 20s")
            else:
                print("⚠ Push Notification Service: Timeout may not be increased")
    except Exception as e:
        print(f"✗ Push Notification Service: Error checking: {e}")
        all_valid = False

    # Check SIEM Integration for retry logic
    try:
        with open("app/core/siem_integration.py", "r") as f:
            content = f.read()
            if "max_retries = 3" in content:
                print("✓ SIEM Integration: Retry configuration present")
            else:
                print("⚠ SIEM Integration: Retry configuration may be missing")

            if "timeout_seconds: int = 30" in content:
                print("✓ SIEM Integration: Timeout increased to 30s")
            else:
                print("⚠ SIEM Integration: Timeout may not be increased")
    except Exception as e:
        print(f"✗ SIEM Integration: Error checking: {e}")
        all_valid = False

    # Check Database Backup for boto3 config
    try:
        with open("app/services/database_backup_service.py", "r") as f:
            content = f.read()
            if "'max_attempts': 10" in content:
                print("✓ Database Backup: boto3 retry configuration present")
            else:
                print("✗ Database Backup: boto3 retry configuration missing")
                all_valid = False

            if "TransferConfig" in content:
                print("✓ Database Backup: Multipart upload configured")
            else:
                print("✗ Database Backup: Multipart upload missing")
                all_valid = False
    except Exception as e:
        print(f"✗ Database Backup: Error checking: {e}")
        all_valid = False

    # Check Settings for retry config
    try:
        with open("app/core/config/settings.py", "r") as f:
            content = f.read()
            retry_fields = [
                "RETRY_MAX_ATTEMPTS",
                "RETRY_TIMEOUT_SHORT",
                "RETRY_TIMEOUT_MEDIUM",
                "RETRY_TIMEOUT_LONG",
            ]
            found_fields = sum(1 for field in retry_fields if field in content)

            if found_fields == len(retry_fields):
                print(
                    f"✓ Settings: All retry configuration fields present ({found_fields}/{len(retry_fields)})"
                )
            else:
                print(
                    f"⚠ Settings: Some retry fields missing ({found_fields}/{len(retry_fields)})"
                )

            if "get_retry_config" in content:
                print("✓ Settings: get_retry_config() method present")
            else:
                print("✗ Settings: get_retry_config() method missing")
                all_valid = False
    except Exception as e:
        print(f"✗ Settings: Error checking: {e}")
        all_valid = False

    print()
    print("4. VALIDATING IMPORTS")
    print("-" * 70)

    # Try to import key modules
    modules_to_test = [
        ("app.core.config.settings", "Settings"),
        ("app.core.resilient_client", "ResilientHTTPClient"),
        ("app.core.monitoring.retry_metrics", "retry_tracker"),
    ]

    for module_name, class_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name}: Import successful")
        except Exception as e:
            print(f"✗ {module_name}: Import failed - {e}")
            all_valid = False

    print()
    print("=" * 70)
    if all_valid:
        print("✓ ALL VALIDATIONS PASSED")
        print()
        print("Next steps:")
        print("1. Review the changes in each modified file")
        print(
            "2. Run integration tests: pytest tests/integrations/test_external_service_retry.py -v"
        )
        print("3. Test in staging environment")
        print("4. Monitor retry metrics after deployment")
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print()
        print("Please review the errors above and fix before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
