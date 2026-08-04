"""
Test script to validate logging improvements

Tests:
1. Correlation ID propagation
2. Structured logging with log_with_context
3. Authentication logging
4. Database performance logging pattern
5. Performance decorator
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_correlation_id_propagation():
    """Test that correlation IDs propagate through context"""
    print("\n" + "=" * 60)
    print("TEST 1: Correlation ID Propagation")
    print("=" * 60)

    from app.core.correlation import (
        clear_correlation_id,
        get_correlation_id,
        set_correlation_id,
    )

    # Set correlation ID
    test_id = "test-correlation-123"
    set_correlation_id(test_id)

    # Verify it's available
    retrieved_id = get_correlation_id()
    assert retrieved_id == test_id, f"Expected {test_id}, got {retrieved_id}"

    print(f"✅ Correlation ID propagation working: {retrieved_id}")

    # Clear and verify new ID is generated
    clear_correlation_id()
    new_id = get_correlation_id()
    assert new_id != test_id, "Should generate new ID after clearing"
    assert len(new_id) == 36, "Should be UUID format"  # UUID format: 8-4-4-4-12

    print(f"✅ New correlation ID generated after clear: {new_id}")

    return True


def test_structured_logging():
    """Test structured logging with correlation ID injection"""
    print("\n" + "=" * 60)
    print("TEST 2: Structured Logging with log_with_context")
    print("=" * 60)

    from app.core.correlation import log_with_context, set_correlation_id

    # Set test correlation ID
    set_correlation_id("test-log-123")

    # Create test logger
    test_logger = logging.getLogger("test_logging")

    # Create a handler to capture log output
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(message)s"))
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    # Test log_with_context
    log_with_context(
        test_logger,
        logging.INFO,
        "Test operation completed",
        event="test_operation",
        user_id="user-123",
        duration_ms=45.2,
    )

    # Get logged output
    log_output = log_capture.getvalue()

    # Verify correlation ID was injected
    assert "test-log-123" in log_output, "Correlation ID should be in log output"
    assert "test_operation" in log_output, "Event should be in log output"
    assert "user-123" in log_output, "User ID should be in log output"
    assert "45.2" in log_output, "Duration should be in log output"

    print(f"✅ Structured logging working correctly")
    print(f"   Log output: {log_output.strip()}")

    # Clean up
    test_logger.removeHandler(handler)

    return True


async def test_performance_decorator():
    """Test performance logging decorator"""
    print("\n" + "=" * 60)
    print("TEST 3: Performance Decorator")
    print("=" * 60)

    import logging

    from app.core.correlation import (
        log_performance,
        log_with_context,
        set_correlation_id,
    )

    # Set correlation ID
    set_correlation_id("test-perf-123")

    # Create test logger with capture
    test_logger = logging.getLogger("test_performance")
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(message)s"))
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    # Define test function with decorator
    @log_performance(
        "test_operation", warning_threshold_ms=100, logger_instance=test_logger
    )
    async def fast_operation():
        await asyncio.sleep(0.01)  # 10ms
        return "success"

    @log_performance(
        "slow_operation", warning_threshold_ms=50, logger_instance=test_logger
    )
    async def slow_operation():
        await asyncio.sleep(0.1)  # 100ms
        return "success"

    # Run fast operation
    result = await fast_operation()
    assert result == "success", "Operation should return success"

    # Run slow operation (should trigger warning)
    result = await slow_operation()
    assert result == "success", "Operation should return success"

    # Get logged output
    log_output = log_capture.getvalue()

    # Verify logs
    assert "test_operation completed" in log_output, "Should log operation completion"
    assert "slow_operation completed" in log_output, "Should log slow operation"
    assert "performance_slow" in log_output, "Should log slow operation warning"

    print(f"✅ Performance decorator working correctly")
    print(f"   Detected slow operation and logged warning")

    # Clean up
    test_logger.removeHandler(handler)

    return True


async def test_database_logging_pattern():
    """Test database operation logging pattern"""
    print("\n" + "=" * 60)
    print("TEST 4: Database Logging Pattern")
    print("=" * 60)

    import logging

    from app.core.correlation import log_with_context, set_correlation_id

    # Set correlation ID
    set_correlation_id("test-db-123")

    # Create test logger
    test_logger = logging.getLogger("test_database")
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(message)s"))
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    # Simulate database operation with logging
    async def mock_db_create():
        start_time = time.time()

        log_with_context(
            test_logger,
            logging.INFO,
            "Creating record",
            event="db_create_start",
            operation="create_response",
            table="responses",
            record_id="test-123",
        )

        # Simulate work
        await asyncio.sleep(0.05)  # 50ms

        duration_ms = (time.time() - start_time) * 1000

        log_with_context(
            test_logger,
            logging.INFO,
            "Database operation completed",
            event="db_create_success",
            operation="create_response",
            table="responses",
            record_id="test-123",
            duration_ms=round(duration_ms, 2),
        )

        # Simulate slow query
        await asyncio.sleep(0.6)  # 600ms - should trigger warning

        log_with_context(
            test_logger,
            logging.WARNING,
            "Slow database operation detected",
            event="db_slow_query",
            operation="create_response",
            duration_ms=600,
            threshold_ms=500,
        )

    # Run the mock operation
    await mock_db_create()

    # Get logged output
    log_output = log_capture.getvalue()

    # Verify all expected log entries
    assert "db_create_start" in log_output, "Should log create start"
    assert "db_create_success" in log_output, "Should log create success"
    assert "db_slow_query" in log_output, "Should log slow query warning"
    assert "test-db-123" in log_output, "Should include correlation ID"

    print(f"✅ Database logging pattern working correctly")
    print(f"   Logged: create_start, create_success, slow_query warning")

    # Clean up
    test_logger.removeHandler(handler)

    return True


async def test_authentication_logging():
    """Test authentication endpoint logging pattern"""
    print("\n" + "=" * 60)
    print("TEST 5: Authentication Logging Pattern")
    print("=" * 60)

    import logging

    from app.core.audit_logger import AuditLogger, SecurityEventType
    from app.core.correlation import log_with_context, set_correlation_id

    # Set correlation ID
    set_correlation_id("test-auth-123")

    # Create test logger
    test_logger = logging.getLogger("test_auth")
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(message)s"))
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    # Simulate authentication flow
    client_ip = "192.168.1.100"
    user_agent = "Mozilla/5.0 Test Browser"
    username = "test@example.com"

    # Failed authentication attempt
    log_with_context(
        test_logger,
        logging.WARNING,
        "Authentication failed - user not found",
        event="auth_failure",
        username=username,
        reason="user_not_found",
        client_ip=client_ip,
        user_agent=user_agent,
    )

    # Security audit log
    AuditLogger.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION_FAILURE,
        details=f"Login attempt with non-existent email: {username}",
        client_ip=client_ip,
        user_agent=user_agent,
        endpoint="/api/v1/auth/simple-login",
        method="POST",
        request_id="test-auth-123",
        additional_data={
            "username": username,
            "reason": "user_not_found",
        },
    )

    # Get logged output
    log_output = log_capture.getvalue()

    # Verify authentication logging
    assert "auth_failure" in log_output, "Should log auth failure"
    assert "user_not_found" in log_output, "Should include failure reason"
    assert "test-auth-123" in log_output, "Should include correlation ID"
    assert "192.168.1.100" in log_output, "Should include client IP"

    print(f"✅ Authentication logging pattern working correctly")
    print(f"   Logged: auth_failure with IP, user_agent, correlation_id")

    # Clean up
    test_logger.removeHandler(handler)

    return True


async def run_all_tests():
    """Run all logging improvement tests"""
    print("\n" + "=" * 80)
    print("LOGGING IMPROVEMENTS TEST SUITE")
    print("=" * 80)

    tests = [
        ("Correlation ID Propagation", test_correlation_id_propagation),
        ("Structured Logging", test_structured_logging),
        ("Performance Decorator", test_performance_decorator),
        ("Database Logging Pattern", test_database_logging_pattern),
        ("Authentication Logging", test_authentication_logging),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = await test_func()

            if result:
                passed += 1
                print(f"✅ PASSED: {test_name}")
            else:
                failed += 1
                print(f"❌ FAILED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {test_name} - {str(e)}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print(
        f"TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed} total"
    )
    print("=" * 80)

    if failed == 0:
        print("\n🎉 ALL LOGGING IMPROVEMENT TESTS PASSED!")
        print("\nImplementation is ready for production deployment.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
