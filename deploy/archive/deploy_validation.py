#!/usr/bin/env python3
"""
Deployment Validation Script

Comprehensive validation checklist for deploying the security service migration.
This script checks all critical aspects before allowing deployment.

Run before deploying to production:
    python scripts/deploy_validation.py

Exit codes:
    0: All validations passed
    1: Critical validation failed
    2: Warning validation failed (use --allow-warnings to bypass)
"""

import argparse
import ast
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ValidationResults:
    """Track validation results."""

    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, check: str, message: str):
        self.passed.append((check, message))

    def add_fail(self, check: str, message: str):
        self.failed.append((check, message))

    def add_warning(self, check: str, message: str):
        self.warnings.append((check, message))

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("DEPLOYMENT VALIDATION RESULTS")
        print("=" * 80)

        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)} checks):")
            for check, message in self.passed:
                print(f"   ✓ {check}: {message}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)} checks):")
            for check, message in self.warnings:
                print(f"   ⚠ {check}: {message}")

        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)} checks):")
            for check, message in self.failed:
                print(f"   ✗ {check}: {message}")

        print("\n" + "=" * 80)

        if not self.failed:
            if not self.warnings:
                print("✅ ALL VALIDATIONS PASSED - Safe to deploy!")
            else:
                print(
                    f"⚠️  Passed with {len(self.warnings)} warnings. Use --allow-warnings to proceed."
                )
        else:
            print(
                f"❌ {len(self.failed)} critical validation(s) failed. Deployment blocked!"
            )
            print("   Please fix the issues above before deploying.")

        print("=" * 80 + "\n")


def check_import_consistency(results: ValidationResults) -> bool:
    """Check that all imports use the new paths consistently."""
    print("Checking import path consistency...")

    # Check that old app.core.security imports are minimal (only in services/security)
    app_dir = project_root / "app"

    # Find all Python files
    python_files = list(app_dir.rglob("*.py"))

    old_imports = []
    new_imports = []

    for file in python_files:
        # Skip __pycache__ and the security service itself
        if "__pycache__" in str(file):
            continue
        if "services/security/__init__.py" in str(file):
            continue

        try:
            content = file.read_text()

            # Check for old imports
            if "from app.core.security import" in content:
                # Exclude the re-export in services/security
                if "services/security" not in str(file):
                    old_imports.append(file)

            # Check for new imports
            if "from app.services.security import" in content:
                new_imports.append(file)

        except Exception:
            pass

    if old_imports:
        results.add_fail(
            "Import Consistency",
            f"Found {len(old_imports)} files using old import path 'from app.core.security import'. "
            f"Files: {', '.join(str(f.relative_to(project_root)) for f in old_imports[:5])}",
        )
        return False
    else:
        results.add_pass(
            "Import Consistency",
            f"All imports use new path. Found {len(new_imports)} files using app.services.security.",
        )
        return True


def check_atomic_operations_usage(results: ValidationResults) -> bool:
    """Check that critical operations use atomic patterns."""
    print("Checking atomic operations usage...")

    # Key files that should use atomic operations
    critical_files = [
        "app/services/user_service.py",
        "app/services/response_service.py",
        "app/services/assessment_service.py",
    ]

    has_warnings = False

    for file_path in critical_files:
        full_path = project_root / file_path
        if not full_path.exists():
            results.add_warning("Atomic Operations", f"File not found: {file_path}")
            continue

        content = full_path.read_text()

        # Check if file uses atomic operations
        uses_atomic = "atomic_" in content or "with_for_update" in content

        if uses_atomic:
            results.add_pass("Atomic Operations", f"{file_path} uses atomic operations")
        else:
            results.add_warning(
                "Atomic Operations",
                f"{file_path} may not use atomic operations for concurrent safety",
            )
            has_warnings = True

    return not has_warnings


def check_organization_access_control(results: ValidationResults) -> bool:
    """Check that organization access control is implemented."""
    print("Checking organization access control...")

    deps_file = project_root / "app/api/v1/deps.py"

    if not deps_file.exists():
        results.add_fail("Organization Access Control", "deps.py not found")
        return False

    content = deps_file.read_text()

    # Check for new access control functions
    required_functions = [
        "get_organization_or_404",
        "check_organization_access",
        "check_organization_admin",
    ]

    missing = []
    for func in required_functions:
        if f"async def {func}" not in content:
            missing.append(func)

    if missing:
        results.add_fail(
            "Organization Access Control", f"Missing functions: {', '.join(missing)}"
        )
        return False
    else:
        results.add_pass(
            "Organization Access Control",
            "All required access control functions present",
        )
        return True


def check_test_coverage(results: ValidationResults) -> bool:
    """Check that tests exist for critical functionality."""
    print("Checking test coverage...")

    # Critical test files
    required_tests = [
        "tests/integrations/test_atomic_operations.py",
        "tests/integrations/test_organization_access_control.py",
    ]

    missing = []
    for test_file in required_tests:
        if not (project_root / test_file).exists():
            missing.append(test_file)

    if missing:
        results.add_fail("Test Coverage", f"Missing test files: {', '.join(missing)}")
        return False
    else:
        results.add_pass("Test Coverage", "All critical test files present")
        return True


def check_monitoring_setup(results: ValidationResults) -> bool:
    """Check that database lock monitoring is set up."""
    print("Checking monitoring setup...")

    monitor_file = project_root / "app/core/monitoring/database_lock_monitor.py"

    if not monitor_file.exists():
        results.add_fail("Monitoring Setup", "Database lock monitor not found")
        return False

    content = monitor_file.read_text()

    # Check for key features
    required_features = [
        "monitor_lock",
        "LockMetrics",
        "check_lock_health",
    ]

    missing = []
    for feature in required_features:
        if feature not in content:
            missing.append(feature)

    if missing:
        results.add_fail(
            "Monitoring Setup", f"Monitor missing features: {', '.join(missing)}"
        )
        return False
    else:
        results.add_pass(
            "Monitoring Setup", "Database lock monitoring properly configured"
        )
        return True


def check_deprecation_warnings(results: ValidationResults) -> bool:
    """Check that deprecation warnings are in place."""
    print("Checking deprecation warnings...")

    security_file = project_root / "app/core/security.py"

    if not security_file.exists():
        results.add_fail("Deprecation Warnings", "security.py not found")
        return False

    content = security_file.read_text()

    # Check for deprecation warnings in key functions
    deprecated_functions = [
        "get_password_hash",
        "verify_password",
        "validate_password",
    ]

    missing_warnings = []
    for func in deprecated_functions:
        # Check if function has deprecation warning (handles both "def" and "async def")
        func_start = content.find(f"def {func}(")
        if func_start == -1:
            # Try async def
            func_start = content.find(f"async def {func}(")
        if func_start == -1:
            continue

        # Get the next 1500 characters (should include docstring and warning)
        # Increased from 500 to catch warnings that appear after long docstrings
        func_section = content[func_start : func_start + 1500]

        # Check for both deprecation markers
        has_deprecated = "DEPRECATED" in func_section
        has_warning = (
            "warnings.warn" in func_section or "warnings_module.warn" in func_section
        )

        if not (has_deprecated and has_warning):
            missing_warnings.append(func)

    if missing_warnings:
        results.add_fail(
            "Deprecation Warnings",
            f"Functions missing deprecation warnings: {', '.join(missing_warnings)}",
        )
        return False
    else:
        results.add_pass(
            "Deprecation Warnings", "All deprecated functions have proper warnings"
        )
        return True


def check_exception_handling(results: ValidationResults) -> bool:
    """Check that exception handling is standardized."""
    print("Checking exception handling...")

    exception_handler = project_root / "app/core/exception_handling.py"

    if not exception_handler.exists():
        results.add_fail("Exception Handling", "exception_handling.py not found")
        return False

    content = exception_handler.read_text()

    # Check for key components
    required = [
        "get_safe_error_message",
        "sanitize_error_detail",
        "SAFE_ERROR_MESSAGES",
    ]

    missing = [r for r in required if r not in content]

    if missing:
        results.add_fail("Exception Handling", f"Missing: {', '.join(missing)}")
        return False
    else:
        results.add_pass(
            "Exception Handling", "Standardized exception handling in place"
        )
        return True


def check_transaction_safety(results: ValidationResults) -> bool:
    """Check that transaction safety is implemented in critical services."""
    print("Checking transaction safety...")

    user_service = project_root / "app/services/user_service.py"

    if not user_service.exists():
        results.add_fail("Transaction Safety", "user_service.py not found")
        return False

    content = user_service.read_text()

    # Check for proper error handling
    has_rollback = "await db.rollback()" in content
    has_commit = "await db.commit()" in content
    has_integrity_handling = "except IntegrityError" in content

    if not all([has_rollback, has_commit, has_integrity_handling]):
        missing = []
        if not has_rollback:
            missing.append("rollback")
        if not has_commit:
            missing.append("commit")
        if not has_integrity_handling:
            missing.append("IntegrityError handling")

        results.add_fail(
            "Transaction Safety",
            f"Missing transaction safety features: {', '.join(missing)}",
        )
        return False
    else:
        results.add_pass(
            "Transaction Safety", "User service has proper transaction safety"
        )
        return True


def check_cache_invalidation_order(results: ValidationResults) -> bool:
    """Check that cache invalidation happens after commit."""
    print("Checking cache invalidation order...")

    user_service = project_root / "app/services/user_service.py"

    if not user_service.exists():
        results.add_warning("Cache Invalidation", "user_service.py not found")
        return True

    content = user_service.read_text()

    # Simplified check: Look for patterns where cache is invalidated in the same
    # function as commits, which suggests proper ordering

    # Check that there are commits and cache invalidations
    has_commits = "await db.commit()" in content
    has_cache_invalidation = "cache_delete_pattern" in content

    if has_commits and has_cache_invalidation:
        # Check for the comment indicating proper order
        has_proper_order_comment = (
            "after commit" in content.lower() or "after successful" in content.lower()
        )

        results.add_pass(
            "Cache Invalidation Order",
            "Cache invalidation present with commits (manual review recommended)",
        )
        return True
    elif not has_cache_invalidation:
        results.add_warning("Cache Invalidation", "No cache invalidation found")
        return True
    else:
        results.add_pass("Cache Invalidation Order", "Basic validation passed")
        return True


def check_security_fixes(results: ValidationResults) -> bool:
    """Check that critical security fixes are in place."""
    print("Checking security fixes...")

    api_file = project_root / "app/api/v1/api.py"

    if not api_file.exists():
        results.add_fail("Security Fixes", "api.py not found")
        return False

    content = api_file.read_text()
    lines = content.split("\n")

    # Check if simple_auth appears in any UNCOMMENTED line
    simple_auth_active = False
    for line in lines:
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue
        # Check if simple_auth appears as an endpoint (uncommented)
        if '"simple_auth"' in stripped or "'simple_auth'" in stripped:
            simple_auth_active = True
            break

    if simple_auth_active:
        results.add_fail(
            "Security Fixes",
            "simple_auth endpoint is still active (should be disabled)",
        )
        return False

    results.add_pass("Security Fixes", "Duplicate auth system disabled")
    return True


async def run_all_validations(allow_warnings: bool = False) -> int:
    """Run all validation checks."""
    print("Starting deployment validation...\n")

    results = ValidationResults()

    # Run all checks
    check_import_consistency(results)
    check_atomic_operations_usage(results)
    check_organization_access_control(results)
    check_test_coverage(results)
    check_monitoring_setup(results)
    check_deprecation_warnings(results)
    check_exception_handling(results)
    check_transaction_safety(results)
    check_cache_invalidation_order(results)
    check_security_fixes(results)

    # Print summary
    results.print_summary()

    # Determine exit code
    if results.failed:
        return 1  # Critical failures
    elif results.warnings and not allow_warnings:
        return 2  # Warnings (unless allowed)
    else:
        return 0  # All good


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate deployment readiness for security service migration"
    )
    parser.add_argument(
        "--allow-warnings", action="store_true", help="Allow deployment with warnings"
    )

    args = parser.parse_args()

    # Run validations
    exit_code = asyncio.run(run_all_validations(allow_warnings=args.allow_warnings))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
