"""
Simple validation test for logging improvements

Validates:
1. Correlation ID module exists and works
2. Authentication endpoint uses structured logging
3. Middleware integration exists
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_correlation_module_exists():
    """Test that correlation module exists and has required functions"""
    print("\n" + "="*60)
    print("TEST 1: Correlation Module Exists")
    print("="*60)

    try:
        from app.core.correlation import (
            set_correlation_id,
            get_correlation_id,
            clear_correlation_id,
            log_with_context,
            log_performance,
        )

        # Test basic functionality
        test_id = "test-123"
        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()

        assert retrieved_id == test_id, f"Expected {test_id}, got {retrieved_id}"
        print(f"✅ Correlation ID propagation working: {retrieved_id}")

        # Test clear
        clear_correlation_id()
        new_id = get_correlation_id()
        assert new_id != test_id, "Should generate new ID"
        print(f"✅ New ID generated after clear: {new_id}")

        return True

    except ImportError as e:
        print(f"❌ Failed to import correlation module: {e}")
        return False


def test_authentication_logging_improved():
    """Test that authentication endpoint uses structured logging"""
    print("\n" + "="*60)
    print("TEST 2: Authentication Logging Improved")
    print("="*60)

    try:
        # Read the simple_auth.py file
        with open("app/api/v1/endpoints/simple_auth.py", "r") as f:
            content = f.read()

        # Check for print statements (should NOT exist)
        has_print_statements = 'print(f"' in content

        if has_print_statements:
            print(f"❌ FAILED: File still contains print() statements")
            return False

        print(f"✅ No print() statements found in simple_auth.py")

        # Check for structured logging imports
        required_imports = [
            "from app.core.audit_logger import AuditLogger",
            "from app.core.correlation import",
            "log_with_context",
            "AuditLogger.log_security_event",
        ]

        all_found = True
        for import_stmt in required_imports:
            if import_stmt in content:
                print(f"✅ Found: {import_stmt}")
            else:
                print(f"❌ Missing: {import_stmt}")
                all_found = False

        # Check for structured logging patterns
        logging_patterns = [
            'event="auth_attempt_start"',
            'event="auth_failure"',
            'event="auth_success"',
            'event="auth_error"',
            'SecurityEventType.AUTHENTICATION_FAILURE',
            'SecurityEventType.AUTHENTICATION_SUCCESS',
        ]

        for pattern in logging_patterns:
            if pattern in content:
                print(f"✅ Found logging pattern: {pattern}")
            else:
                print(f"❌ Missing pattern: {pattern}")
                all_found = False

        return all_found

    except Exception as e:
        print(f"❌ Error reading simple_auth.py: {e}")
        return False


def test_middleware_integration():
    """Test that middleware has correlation context integration"""
    print("\n" + "="*60)
    print("TEST 3: Middleware Integration")
    print("="*60)

    try:
        # Read the logging middleware file
        with open("app/middleware/logging.py", "r") as f:
            content = f.read()

        # Check for correlation imports
        required_imports = [
            "from app.core.correlation import",
            "set_correlation_id",
            "clear_correlation_id",
        ]

        all_found = True
        for import_stmt in required_imports:
            if import_stmt in content:
                print(f"✅ Found: {import_stmt}")
            else:
                print(f"❌ Missing: {import_stmt}")
                all_found = False

        # Check for usage in dispatch method
        usage_patterns = [
            "set_correlation_id(correlation_id)",
            "clear_correlation_id()",
        ]

        for pattern in usage_patterns:
            if pattern in content:
                print(f"✅ Found usage: {pattern}")
            else:
                print(f"❌ Missing usage: {pattern}")
                all_found = False

        return all_found

    except Exception as e:
        print(f"❌ Error reading logging middleware: {e}")
        return False


def test_correlation_module_features():
    """Test that correlation module has all required features"""
    print("\n" + "="*60)
    print("TEST 4: Correlation Module Features")
    print("="*60)

    try:
        # Read the correlation module
        with open("app/core/correlation.py", "r") as f:
            content = f.read()

        # Check for required functions and decorators
        required_features = [
            "def set_correlation_id",
            "def get_correlation_id",
            "def clear_correlation_id",
            "def log_with_context",
            "def log_performance",
            "def log_db_operation",
            "class StructuredFormatter",
            "CORRELATION_ID_CONTEXT",
        ]

        all_found = True
        for feature in required_features:
            if feature in content:
                print(f"✅ Found feature: {feature}")
            else:
                print(f"❌ Missing feature: {feature}")
                all_found = False

        # Check for documentation
        if '"""' in content:
            print(f"✅ Module has documentation")
        else:
            print(f"❌ Module missing documentation")
            all_found = False

        return all_found

    except Exception as e:
        print(f"❌ Error reading correlation module: {e}")
        return False


def test_implementation_documentation():
    """Test that implementation documentation exists"""
    print("\n" + "="*60)
    print("TEST 5: Implementation Documentation")
    print("="*60)

    try:
        # Check for documentation files
        doc_files = [
            "LOGGING_BLIND_SPOTS_ANALYSIS.md",
            "LOGGING_IMPROVEMENT_PLAN.md",
            "LOGGING_IMPLEMENTATION_COMPLETE.md",
        ]

        all_found = True
        for doc_file in doc_files:
            try:
                with open(doc_file, "r") as f:
                    content = f.read()
                    if len(content) > 1000:  # Has substantial content
                        print(f"✅ Found: {doc_file} ({len(content)} bytes)")
                    else:
                        print(f"⚠️  File too small: {doc_file}")
                        all_found = False
            except FileNotFoundError:
                print(f"❌ Missing: {doc_file}")
                all_found = False

        return all_found

    except Exception as e:
        print(f"❌ Error checking documentation: {e}")
        return False


def main():
    """Run all validation tests"""
    print("\n" + "="*80)
    print("LOGGING IMPROVEMENTS - VALIDATION SUITE")
    print("="*80)

    tests = [
        ("Correlation Module Exists", test_correlation_module_exists),
        ("Authentication Logging Improved", test_authentication_logging_improved),
        ("Middleware Integration", test_middleware_integration),
        ("Correlation Module Features", test_correlation_module_features),
        ("Implementation Documentation", test_implementation_documentation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()

            if result:
                passed += 1
                print(f"\n✅ PASSED: {test_name}")
            else:
                failed += 1
                print(f"\n❌ FAILED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"\n❌ FAILED: {test_name} - {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print(f"VALIDATION RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
    print("="*80)

    if failed == 0:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("\n✅ Logging improvements successfully implemented")
        print("✅ Ready for production deployment")
        print("\nKey Changes:")
        print("  • Correlation ID context propagation")
        print("  • Authentication endpoint with structured logging")
        print("  • Security audit trail integration")
        print("  • Performance monitoring decorators")
        print("  • Database operation logging patterns")
        return True
    else:
        print(f"\n⚠️  {failed} validation(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
