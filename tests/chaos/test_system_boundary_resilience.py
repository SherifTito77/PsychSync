"""
Chaos Testing for System Boundary Interactions

This module tests the resilience of system boundary interactions by simulating
various failure scenarios including:
- Network failures
- Timeout scenarios
- Service unavailability
- Partial degradation
- Circuit breaker behavior

Author: Resilience Team
Version: 1.0
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.core.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    ErrorClassifier,
    ErrorType,
    RateLimiter,
    RetryPolicy,
    get_resilience_manager,
)

# ============================================================================
# TEST: Circuit Breaker Behavior
# ============================================================================


class TestCircuitBreakerResilience:
    """Test circuit breaker behavior under various failure scenarios"""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing"""
        cb = CircuitBreaker(
            name="test_cb",
            failure_threshold=3,
            recovery_timeout=5.0,
            success_threshold=2,
            timeout=1.0,
        )
        yield cb
        # Reset after test
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        cb.success_count = 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test that circuit breaker opens after threshold failures"""
        failing_function = AsyncMock(side_effect=Exception("Service unavailable"))

        # Trigger failures up to threshold
        for i in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(failing_function)
            except Exception:
                pass

        # Circuit should be OPEN
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.failure_count >= circuit_breaker.failure_threshold

    @pytest.mark.asyncio
    async def test_circuit_breaker_fails_fast_when_open(self, circuit_breaker):
        """Test that circuit breaker fails fast when OPEN"""
        failing_function = AsyncMock(side_effect=Exception("Service unavailable"))

        # Open the circuit
        for _ in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(failing_function)
            except Exception:
                pass

        assert circuit_breaker.state == CircuitState.OPEN

        # Should raise CircuitBreakerOpenError immediately
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(AsyncMock())

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers_after_timeout(self, circuit_breaker):
        """Test that circuit breaker transitions to HALF_OPEN after timeout"""
        circuit_breaker.recovery_timeout = 0.1  # Short timeout for testing

        failing_function = AsyncMock(side_effect=Exception("Service unavailable"))

        # Open the circuit
        for _ in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(failing_function)
            except Exception:
                pass

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(circuit_breaker.recovery_timeout + 0.1)

        # Try a call - should transition to HALF_OPEN
        working_function = AsyncMock(return_value="success")
        result = await circuit_breaker.call(working_function)

        assert circuit_breaker.state == CircuitState.HALF_OPEN
        assert result == "success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_success_threshold(
        self, circuit_breaker
    ):
        """Test that circuit breaker closes after success threshold in HALF_OPEN"""
        # Open and wait for recovery
        circuit_breaker.recovery_timeout = 0.1
        failing_function = AsyncMock(side_effect=Exception("Service unavailable"))

        for _ in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(failing_function)
            except Exception:
                pass

        await asyncio.sleep(0.2)

        # Get to HALF_OPEN
        working_function = AsyncMock(return_value="success")
        await circuit_breaker.call(working_function)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Achieve success threshold
        for _ in range(circuit_breaker.success_threshold):
            await circuit_breaker.call(working_function)

        assert circuit_breaker.state == CircuitState.CLOSED


# ============================================================================
# TEST: Retry Policy Behavior
# ============================================================================


class TestRetryPolicyResilience:
    """Test retry policy behavior for transient failures"""

    @pytest.mark.asyncio
    async def test_retry_on_transient_errors(self):
        """Test that retry policy retries on transient errors"""
        retry_policy = RetryPolicy(
            max_attempts=3,
            base_delay=0.01,  # Very short for testing
            retry_on=[ErrorType.NETWORK, ErrorType.TIMEOUT],
        )

        # Simulate transient error then success
        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"

        # Should retry and succeed
        from app.core.resilience import _execute_with_retry

        result = await _execute_with_retry(flaky_function, flaky_function, retry_policy)

        assert result == "success"
        assert call_count == 2  # Failed once, succeeded on retry

    @pytest.mark.asyncio
    async def test_no_retry_on_authentication_errors(self):
        """Test that authentication errors are not retried"""
        retry_policy = RetryPolicy(
            max_attempts=3,
            base_delay=0.01,
            stop_on=[ErrorType.AUTHENTICATION],
        )

        call_count = 0

        async def auth_failing_function():
            nonlocal call_count
            call_count += 1
            # Create an error that looks like authentication error
            error = Exception("Unauthorized")
            setattr(error, "status_code", 401)
            raise error

        from app.core.resilience import _execute_with_retry

        # Should NOT retry authentication errors
        with pytest.raises(Exception):
            await _execute_with_retry(
                auth_failing_function, auth_failing_function, retry_policy
            )

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test that retry delay increases exponentially"""
        retry_policy = RetryPolicy(
            max_attempts=5,
            base_delay=0.01,
            exponential_base=2.0,
            jitter=False,  # Disable jitter for predictable testing
        )

        delays = []
        for attempt in range(4):
            delay = retry_policy.get_delay(attempt)
            delays.append(delay)

        # Verify exponential growth
        assert delays[0] == 0.01
        assert delays[1] == 0.02
        assert delays[2] == 0.04
        assert delays[3] == 0.08


# ============================================================================
# TEST: Error Classification
# ============================================================================


class TestErrorClassification:
    """Test error classification for appropriate handling"""

    def test_classify_network_errors(self):
        """Test that network errors are classified correctly"""
        error = ConnectionError("Connection refused")
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.error_type == ErrorType.NETWORK
        assert error_info.original_exception == error

    def test_classify_timeout_errors(self):
        """Test that timeout errors are classified correctly"""
        error = asyncio.TimeoutError("Operation timed out")
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.error_type == ErrorType.TIMEOUT

    def test_classify_rate_limit_errors(self):
        """Test that rate limit errors are classified correctly"""
        error = Exception("Too many requests")
        setattr(error, "status_code", 429)
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.error_type == ErrorType.RATE_LIMIT

    def test_classify_auth_errors(self):
        """Test that authentication errors are classified correctly"""
        error = Exception("Unauthorized")
        setattr(error, "status_code", 401)
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.error_type == ErrorType.AUTHENTICATION


# ============================================================================
# TEST: Rate Limiter Behavior
# ============================================================================


class TestRateLimiterResilience:
    """Test rate limiter behavior"""

    @pytest.mark.asyncio
    async def test_sliding_window_rate_limiting(self):
        """Test sliding window rate limiting"""
        rate_limiter = RateLimiter(
            name="test_rl", algorithm="sliding_window", limit=5, window=1.0
        )

        # Should allow requests up to limit
        for _ in range(rate_limiter.limit):
            assert await rate_limiter.acquire() is True

        # Next request should be denied
        assert await rate_limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_rate_limit_window_slides(self):
        """Test that rate limit window slides correctly"""
        rate_limiter = RateLimiter(
            name="test_rl", algorithm="sliding_window", limit=3, window=0.2
        )

        # Use up limit
        for _ in range(rate_limiter.limit):
            await rate_limiter.acquire()

        # Should be denied
        assert await rate_limiter.acquire() is False

        # Wait for window to slide
        await asyncio.sleep(rate_limiter.window + 0.1)

        # Should be allowed again
        assert await rate_limiter.acquire() is True


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================


class TestBoundaryResilienceIntegration:
    """Test integration scenarios combining multiple resilience patterns"""

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self):
        """Test that circuit breaker prevents cascading failures"""
        # This test simulates a scenario where a failing external service
        # could cause cascading failures throughout the system

        circuit_breaker = CircuitBreaker(
            name="integration_cb",
            failure_threshold=2,
            recovery_timeout=1.0,
            timeout=0.5,
        )

        failing_service = AsyncMock(side_effect=ConnectionError("Service down"))

        # Simulate multiple calls to failing service
        start_time = time.time()

        for _ in range(10):
            try:
                await circuit_breaker.call(failing_service)
            except Exception:
                pass

        elapsed = time.time() - start_time

        # Should fail fast after circuit opens (< 1 second for 10 calls)
        assert elapsed < 2.0, "Circuit breaker should fail fast"

        # Circuit should be open
        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_timeout_protection(self):
        """Test that timeout prevents hanging on slow services"""
        circuit_breaker = CircuitBreaker(
            name="timeout_cb",
            failure_threshold=3,
            timeout=0.1,  # Very short timeout
        )

        async def slow_function():
            await asyncio.sleep(5.0)  # Takes too long
            return "success"

        # Should timeout quickly
        start_time = time.time()
        try:
            await circuit_breaker.call(slow_function)
        except (asyncio.TimeoutError, Exception):
            pass

        elapsed = time.time() - start_time

        # Should timeout in < 0.5 seconds (circuit breaker timeout + overhead)
        assert (
            elapsed < 0.5
        ), f"Timeout should protect against slow calls (took {elapsed}s)"

    @pytest.mark.asyncio
    async def test_recovery_after_service_restoration(self):
        """Test system recovery after service is restored"""
        circuit_breaker = CircuitBreaker(
            name="recovery_cb",
            failure_threshold=2,
            recovery_timeout=0.2,
            success_threshold=2,
        )

        call_count = 0

        async def recovering_service():
            nonlocal call_count
            call_count += 1
            # Fail only for first 2 calls
            if call_count <= 2:
                raise ConnectionError("Service unavailable")
            return "success"

        # Trigger circuit to open (2 failures)
        for _ in range(2):
            try:
                await circuit_breaker.call(recovering_service)
            except Exception:
                pass

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.3)

        # Try recovery - should succeed
        result = await circuit_breaker.call(recovering_service)
        assert result == "success"


# ============================================================================
# TEST: Real-World Scenarios
# ============================================================================


class TestRealWorldFailureScenarios:
    """Test realistic failure scenarios"""

    @pytest.mark.asyncio
    async def test_partial_service_degradation(self):
        """Test handling of partial service degradation (some endpoints fail, others work)"""
        # Create separate circuit breakers for different endpoints
        users_cb = CircuitBreaker(name="users_api", failure_threshold=3)
        orders_cb = CircuitBreaker(name="orders_api", failure_threshold=3)

        # Users endpoint is failing
        async def get_users():
            raise ConnectionError("Users service down")

        # Orders endpoint is working
        async def get_orders():
            return ["order1", "order2"]

        # Trigger users circuit to open (3 failures)
        for _ in range(3):
            try:
                await users_cb.call(get_users)
            except Exception:
                pass

        # Orders endpoint works normally
        orders_result = await orders_cb.call(get_orders)

        # Verify degradation handling
        assert orders_result == ["order1", "order2"]
        assert users_cb.state == CircuitState.OPEN  # Users circuit opened
        assert orders_cb.state == CircuitState.CLOSED  # Orders still working

    @pytest.mark.asyncio
    async def test_network_instability(self):
        """Test handling of unstable network (intermittent failures)"""
        circuit_breaker = CircuitBreaker(
            name="unstable_network",
            failure_threshold=5,  # Higher threshold for unstable networks
            recovery_timeout=0.5,
        )

        call_count = 0
        success_count = 0

        async def unstable_service():
            nonlocal call_count, success_count
            call_count += 1
            # Succeed 60% of the time
            if call_count % 5 < 3:
                success_count += 1
                return "success"
            raise ConnectionError("Network unstable")

        # Make multiple calls to unstable service
        for _ in range(20):
            try:
                await circuit_breaker.call(unstable_service)
            except Exception:
                pass

        # Should have some successes despite instability
        assert success_count > 0

        # Circuit may or may not be open depending on failure pattern
        # The important thing is that we handle it gracefully

    @pytest.mark.asyncio
    async def test_slow_service_with_timeouts(self):
        """Test handling of service that responds very slowly"""
        circuit_breaker = CircuitBreaker(
            name="slow_service",
            failure_threshold=3,
            timeout=0.2,  # Short timeout
        )

        async def slow_service():
            await asyncio.sleep(1.0)  # Too slow
            return "success"

        # Multiple timeout attempts should open circuit
        for _ in range(4):
            try:
                await circuit_breaker.call(slow_service)
            except (asyncio.TimeoutError, Exception):
                pass

        # Circuit should be open after repeated timeouts
        assert circuit_breaker.state == CircuitState.OPEN


# ============================================================================
# Helper Functions
# ============================================================================


async def run_chaos_test(test_name: str, test_func) -> dict[str, Any]:
    """
    Run a chaos test and collect metrics

    Args:
        test_name: Name of the test
        test_func: Async test function to run

    Returns:
        Dictionary with test results and metrics
    """
    start_time = time.time()
    result = {"test_name": test_name, "start_time": datetime.now().isoformat()}

    try:
        await test_func()
        result["status"] = "PASSED"
        result["message"] = "Test completed successfully"
    except Exception as e:
        result["status"] = "FAILED"
        result["message"] = str(e)
        result["error_type"] = type(e).__name__

    result["duration_seconds"] = time.time() - start_time
    result["end_time"] = datetime.now().isoformat()

    return result


# ============================================================================
# Test Runner
# ============================================================================


if __name__ == "__main__":
    print("=" * 80)
    print("CHAOS TESTING: System Boundary Resilience")
    print("=" * 80)
    print()

    # Run all chaos tests
    tests = [
        (
            "Circuit Breaker Opens on Failures",
            TestCircuitBreakerResilience().test_circuit_breaker_opens_on_failures,
        ),
        (
            "Circuit Breaker Fails Fast",
            TestCircuitBreakerResilience().test_circuit_breaker_fails_fast_when_open,
        ),
        (
            "Circuit Breaker Recovery",
            TestCircuitBreakerResilience().test_circuit_breaker_recovers_after_timeout,
        ),
        (
            "Retry on Transient Errors",
            TestRetryPolicyResilience().test_retry_on_transient_errors,
        ),
        (
            "No Retry on Auth Errors",
            TestRetryPolicyResilience().test_no_retry_on_authentication_errors,
        ),
        (
            "Rate Limiting",
            TestRateLimiterResilience().test_sliding_window_rate_limiting,
        ),
        (
            "Cascading Failure Prevention",
            TestBoundaryResilienceIntegration().test_cascading_failure_prevention,
        ),
        (
            "Timeout Protection",
            TestBoundaryResilienceIntegration().test_timeout_protection,
        ),
        (
            "Service Recovery",
            TestBoundaryResilienceIntegration().test_recovery_after_service_restoration,
        ),
    ]

    async def run_all_tests():
        results = []
        for test_name, test_func in tests:
            result = await run_chaos_test(test_name, test_func)
            results.append(result)

            print(
                f"{'✓' if result['status'] == 'PASSED' else '✗'} {test_name}: {result['status']}"
            )
            if result["status"] == "FAILED":
                print(f"  Error: {result.get('message', 'Unknown error')}")

        return results

    results = asyncio.run(run_all_tests())

    print()
    print("=" * 80)
    print("CHAOS TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")

    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed / len(results) * 100:.1f}%")
