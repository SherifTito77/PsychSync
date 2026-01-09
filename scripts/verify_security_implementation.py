#!/usr/bin/env python3
"""
Security Implementation Verification Script

Verifies that the LLM Security Framework is properly integrated
and all components are functioning correctly.

Usage:
    python scripts/verify_security_implementation.py

Author: Security Team
Version: 1.0
Date: 2025-12-27
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80 + "\n")


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def verify_imports():
    """Verify all security modules can be imported"""
    print_header("1. Verifying Security Module Imports")

    try:
        from app.middleware.spotlighting import (
            SpotlightingEngine,
            ToolAllowList,
            ApprovalManager,
            SpotlightingMiddleware,
            ContentSource,
            TrustLevel,
            SpotlightingMode,
        )
        print_success("All spotlighting modules imported successfully")

        # Check key classes
        assert SpotlightingEngine is not None
        assert ToolAllowList is not None
        assert ApprovalManager is not None
        assert SpotlightingMiddleware is not None
        print_success("All core classes available")

        return True

    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def verify_spotlighting_engine():
    """Verify spotlighting engine functionality"""
    print_header("2. Verifying SpotlightingEngine")

    try:
        from app.middleware.spotlighting import SpotlightingEngine, SpotlightingMode, ContentSource

        # Test initialization
        engine = SpotlightingEngine(mode=SpotlightingMode.STRICT)
        print_success("SpotlightingEngine initialized in STRICT mode")

        # Test content spotlighting
        test_content = "Test content for spotlighting"
        spotlighted = engine.spotlight_content(
            content=test_content,
            source=ContentSource.USER
        )
        assert spotlighted.content == test_content
        assert spotlighted.content_hash is not None
        print_success("Content spotlighting functional")

        # Test wrapping/unwrapping
        wrapped = engine.wrap_content(test_content, spotlighted)
        unwrapped = engine.unwrap_content(wrapped)
        assert unwrapped == test_content
        print_success("Content wrapping/unwrapping functional")

        # Test output validation
        safe_output = "This is safe output"
        is_valid, issues = engine.validate_llm_output(safe_output)
        assert is_valid is True
        assert len(issues) == 0
        print_success("Output validation functional (safe content)")

        # Test dangerous pattern detection
        dangerous_output = "<script>alert('XSS')</script>"
        is_valid, issues = engine.validate_llm_output(dangerous_output)
        assert is_valid is False
        assert len(issues) > 0
        print_success("Output validation functional (dangerous content detected)")

        return True

    except Exception as e:
        print_error(f"SpotlightingEngine verification failed: {e}")
        return False


def verify_tool_allowlist():
    """Verify tool allow-list functionality"""
    print_header("3. Verifying ToolAllowList")

    try:
        from app.middleware.spotlighting import ToolAllowList

        # Test initialization
        allowlist = ToolAllowList()
        print_success("ToolAllowList initialized")

        # Test allowed tools
        allowed_tool = "get_user_profile"
        is_allowed, reason = allowlist.is_tool_allowed(allowed_tool)
        assert is_allowed is True
        print_success(f"Allowed tool check: {allowed_tool}")

        # Test blocked tools
        blocked_tool = "execute_arbitrary_code"
        is_allowed, reason = allowlist.is_tool_allowed(blocked_tool)
        assert is_allowed is False
        print_success(f"Blocked tool check: {blocked_tool}")

        # Test approval-required tools
        approval_tool = "delete_user"
        is_allowed, reason = allowlist.is_tool_allowed(approval_tool)
        assert is_allowed is False
        assert "approval" in reason.lower()
        print_success(f"Approval-required tool check: {approval_tool}")

        # Test unknown tools (default-deny)
        unknown_tool = "unknown_tool_xyz"
        is_allowed, reason = allowlist.is_tool_allowed(unknown_tool)
        assert is_allowed is False
        print_success(f"Default-deny check: {unknown_tool}")

        return True

    except Exception as e:
        print_error(f"ToolAllowList verification failed: {e}")
        return False


def verify_approval_manager():
    """Verify approval manager functionality"""
    print_header("4. Verifying ApprovalManager")

    try:
        from app.middleware.spotlighting import ApprovalManager

        # Test initialization
        manager = ApprovalManager(approval_timeout=300)
        print_success("ApprovalManager initialized")

        # Test approval request
        approval_id = manager.request_approval(
            operation="test_operation",
            context={"test": "data"},
            user_id="user_123"
        )
        assert approval_id is not None
        assert approval_id in manager.pending_approvals
        print_success("Approval request created")

        # Test approval
        success = manager.approve_operation(approval_id, "admin")
        assert success is True
        print_success("Operation approved")

        # Test status check
        is_approved, message = manager.check_approval(approval_id)
        assert is_approved is True
        print_success("Approval status check functional")

        # Test duplicate prevention
        success2 = manager.approve_operation(approval_id, "another_admin")
        assert success2 is False
        print_success("Duplicate approval prevention functional")

        return True

    except Exception as e:
        print_error(f"ApprovalManager verification failed: {e}")
        return False


def verify_middleware_integration():
    """Verify middleware is integrated in main.py"""
    print_header("5. Verifying Middleware Integration")

    try:
        # Check if main.py exists and contains spotlighting
        main_py_path = os.path.join(project_root, "app", "main.py")

        if not os.path.exists(main_py_path):
            print_error("app/main.py not found")
            return False

        with open(main_py_path, 'r') as f:
            main_content = f.read()

        # Check for spotlighting imports
        if "from app.middleware.spotlighting import" in main_content:
            print_success("Spotlighting imports found in main.py")
        else:
            print_error("Spotlighting imports not found in main.py")
            return False

        # Check for middleware initialization
        if "SpotlightingMiddleware" in main_content:
            print_success("SpotlightingMiddleware found in main.py")
        else:
            print_error("SpotlightingMiddleware not found in main.py")
            return False

        # Check for middleware registration
        if "app.add_middleware" in main_content and "SpotlightingMiddleware" in main_content:
            print_success("Middleware registration found in main.py")
        else:
            print_error("Middleware registration not found in main.py")
            return False

        return True

    except Exception as e:
        print_error(f"Middleware integration verification failed: {e}")
        return False


def verify_tests():
    """Verify tests are present and can run"""
    print_header("6. Verifying Test Suite")

    try:
        test_file = os.path.join(project_root, "tests/unit/test_spotlighting_middleware.py")

        if not os.path.exists(test_file):
            print_error("Test file not found")
            return False

        print_success("Test file exists")

        # Try to import test module
        import tests.unit.test_spotlighting_middleware as test_module
        print_success("Test module can be imported")

        # Check for test classes
        assert hasattr(test_module, 'TestSpotlightingEngine')
        assert hasattr(test_module, 'TestToolAllowList')
        assert hasattr(test_module, 'TestApprovalManager')
        print_success("All test classes present")

        return True

    except Exception as e:
        print_error(f"Test verification failed: {e}")
        return False


def verify_documentation():
    """Verify documentation files exist"""
    print_header("7. Verifying Documentation")

    try:
        docs_to_check = [
            ("docs/LLM_SECURITY_POLICY.md", "Security Policy"),
            ("docs/LLM_SECURITY_INTEGRATION_GUIDE.md", "Integration Guide"),
            ("docs/LLM_SECURITY_IMPLEMENTATION_SUMMARY.md", "Implementation Summary"),
        ]

        all_exist = True
        for doc_path, doc_name in docs_to_check:
            full_path = os.path.join(project_root, doc_path)
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                print_success(f"{doc_name}: {file_size} bytes")
            else:
                print_error(f"{doc_name}: not found")
                all_exist = False

        return all_exist

    except Exception as e:
        print_error(f"Documentation verification failed: {e}")
        return False


def verify_example_endpoints():
    """Verify example secure AI endpoints exist"""
    print_header("8. Verifying Example Endpoints")

    try:
        endpoints_file = os.path.join(project_root, "app/api/v1/endpoints/ai_secure.py")

        if not os.path.exists(endpoints_file):
            print_warning("Example endpoints file not found (optional)")
            return True

        print_success("Example secure endpoints file exists")

        # Check file size
        file_size = os.path.getsize(endpoints_file)
        print_success(f"Endpoints file size: {file_size} bytes")

        return True

    except Exception as e:
        print_error(f"Example endpoints verification failed: {e}")
        return False


def generate_summary(results: dict):
    """Generate verification summary"""
    print_header("📊 VERIFICATION SUMMARY")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()

    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check}")

    print("\n" + "="*80)

    if failed == 0:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\nThe LLM Security Framework is fully integrated and functional.")
        print("\nNext steps:")
        print("1. Run the demo: python scripts/demo_llm_security.py")
        print("2. Run the tests: pytest tests/unit/test_spotlighting_middleware.py -v")
        print("3. Review the docs: docs/LLM_SECURITY_*.md")
        print("4. Start using in your endpoints!")
        return 0
    else:
        print(f"\n⚠️  {failed} VERIFICATION(S) FAILED")
        print("\nPlease review the errors above and fix any issues.")
        return 1


def main():
    """Run all verifications"""
    print_header("🔐 LLM Security Framework - Implementation Verification")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: 1.0")

    results = {}

    # Run all verifications
    results["Module Imports"] = verify_imports()
    results["SpotlightingEngine"] = verify_spotlighting_engine()
    results["ToolAllowList"] = verify_tool_allowlist()
    results["ApprovalManager"] = verify_approval_manager()
    results["Middleware Integration"] = verify_middleware_integration()
    results["Test Suite"] = verify_tests()
    results["Documentation"] = verify_documentation()
    results["Example Endpoints"] = verify_example_endpoints()

    # Generate summary
    return generate_summary(results)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


# ==================== Usage Instructions ====================

"""
USAGE:

    python scripts/verify_security_implementation.py

EXPECTED OUTPUT:

    - All checks should pass with ✅
    - Summary showing 8/8 verifications passed
    - Next steps for using the framework

VERIFICATION CHECKS:

    1. Module Imports - All security modules can be imported
    2. SpotlightingEngine - Content marking and validation works
    3. ToolAllowList - Tool authorization functional
    4. ApprovalManager - Approval workflow operational
    5. Middleware Integration - Integrated into app/main.py
    6. Test Suite - Tests present and importable
    7. Documentation - All docs exist
    8. Example Endpoints - Example code available

TROUBLESHOOTING:

    If any checks fail:
    1. Check the error message for details
    2. Verify files are in correct locations
    3. Check imports are working
    4. Review main.py integration
    5. Run: python -m pytest tests/unit/test_spotlighting_middleware.py -v
"""
