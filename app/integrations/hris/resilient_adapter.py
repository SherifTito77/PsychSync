"""
Resilient Adapter for HRIS Connectors

This module provides network resilience patterns for HRIS integrations:
- Automatic retry with exponential backoff and jitter
- Circuit breaker pattern per HRIS instance
- Timeout configuration for all operations
- Comprehensive metrics tracking
- Error classification and handling

Usage:
    class MyHRISConnector(ResilientHRISAdapter):
        def __init__(self, config: dict):
            super().__init__(
                config,
                connector_name="my_hris",
                timeout=30.0,
                max_retries=3
            )

        async def fetch_employees(self):
            return await self.execute_with_resilience(
                self._fetch_employees_impl
            )

        async def _fetch_employees_impl(self):
            # Actual implementation here
            pass
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

# Default resilience configuration
HRIS_MAX_RETRIES = 3
HRIS_BASE_DELAY = 1.0  # seconds
HRIS_MAX_DELAY = 10.0  # seconds
HRIS_DEFAULT_TIMEOUT = 30.0  # seconds
HRIS_CIRCUIT_FAILURE_THRESHOLD = 5
HRIS_CIRCUIT_RECOVERY_TIMEOUT = 60.0  # seconds


class ErrorType(Enum):
    """Classification of error types for appropriate handling"""

    NETWORK = auto()  # Network connectivity issues
    TIMEOUT = auto()  # Operation timeout
    RATE_LIMIT = auto()  # Rate limiting exceeded
    AUTHENTICATION = auto()  # Authentication/authorization failures
    VALIDATION = auto()  # Input validation errors
    BUSINESS = auto()  # Business logic errors
    SYSTEM = auto()  # System-level errors
    DEPENDENCY = auto()  # External dependency failures
    UNKNOWN = auto()  # Unclassified errors


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class HRISMetrics:
    """Metrics for HRIS operations"""

    connector_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    retried_calls: int = 0
    circuit_breaker_opens: int = 0
    last_failure: datetime | None = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    timeout_errors: int = 0
    network_errors: int = 0
    authentication_errors: int = 0

    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_calls == 0:
            return 100.0
        return (self.successful_calls / self.total_calls) * 100

    def avg_response_time_ms(self) -> float:
        """Calculate average response time in milliseconds"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)


class HRISCircuitBreaker:
    """
    Circuit breaker for HRIS operations to prevent cascading failures
    """

    def __init__(
        self,
        connector_name: str,
        failure_threshold: int = HRIS_CIRCUIT_FAILURE_THRESHOLD,
        recovery_timeout: float = HRIS_CIRCUIT_RECOVERY_TIMEOUT,
    ):
        self.connector_name = connector_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.half_open_attempts = 0
        self.max_half_open_attempts = 3
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(f"{__name__}.{connector_name}")

    async def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state != CircuitState.OPEN:
            return False

        # Check if we should attempt recovery
        if self.last_failure_time:
            time_since_failure = (
                datetime.now() - self.last_failure_time
            ).total_seconds()
            if time_since_failure >= self.recovery_timeout:
                async with self._lock:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                    self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                return False

        return True

    async def record_success(self):
        """Record successful operation"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_attempts += 1
                if self.half_open_attempts >= self.max_half_open_attempts:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.logger.info("Circuit breaker reset to CLOSED")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    async def record_failure(self):
        """Record failed operation"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.logger.warning(
                    "Circuit breaker returned to OPEN after HALF_OPEN failure"
                )
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.logger.warning(
                        f"Circuit breaker opened after {self.failure_count} failures"
                    )


T = TypeVar("T")


class ResilientHRISAdapter(ABC):
    """
    Base class for resilient HRIS connectors

    Provides:
    - Automatic retry with exponential backoff
    - Circuit breaker protection
    - Timeout handling
    - Metrics tracking
    - Error classification

    Subclasses must implement the _get_configured_client() method and
    use execute_with_resilience() for all external API calls.
    """

    def __init__(
        self,
        config: dict,
        connector_name: str,
        timeout: float = HRIS_DEFAULT_TIMEOUT,
        max_retries: int = HRIS_MAX_RETRIES,
    ):
        """
        Initialize resilient HRIS adapter

        Args:
            config: Connector configuration dictionary
            connector_name: Unique name for this connector instance
            timeout: Default timeout for operations in seconds
            max_retries: Maximum number of retry attempts
        """
        self.config = config
        self.connector_name = connector_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize circuit breaker
        self.circuit_breaker = HRISCircuitBreaker(
            connector_name=connector_name,
            failure_threshold=config.get(
                "circuit_failure_threshold", HRIS_CIRCUIT_FAILURE_THRESHOLD
            ),
            recovery_timeout=config.get(
                "circuit_recovery_timeout", HRIS_CIRCUIT_RECOVERY_TIMEOUT
            ),
        )

        # Initialize metrics
        self.metrics = HRISMetrics(connector_name=connector_name)

        self.logger = logging.getLogger(f"{__name__}.{connector_name}")

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to HRIS service"""
        pass

    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff with jitter to prevent thundering herd

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds with jitter applied
        """
        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = HRIS_BASE_DELAY * (2**attempt)
        delay = min(delay, HRIS_MAX_DELAY)

        # Add jitter: ±25% randomization to prevent thundering herd
        jitter = delay * 0.25 * (random.random() * 2 - 1)
        delay += jitter

        return max(0, delay)  # Ensure non-negative

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error for appropriate handling

        Args:
            error: Exception to classify

        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        error_type_str = str(type(error).__name__).lower()

        # Network-related errors
        if any(
            name in error_type_str
            for name in ["connection", "network", "tcp", "socket"]
        ):
            return ErrorType.NETWORK

        # Timeout errors
        if any(name in error_type_str + error_str for name in ["timeout", "timed out"]):
            return ErrorType.TIMEOUT

        # Authentication errors
        if any(
            name in error_str
            for name in ["unauthorized", "authentication", "401", "403"]
        ):
            return ErrorType.AUTHENTICATION

        # Rate limiting
        if any(name in error_str for name in ["rate limit", "429", "throttle"]):
            return ErrorType.RATE_LIMIT

        # Validation errors
        if any(name in error_str for name in ["validation", "invalid", "malformed"]):
            return ErrorType.VALIDATION

        # Default to unknown
        return ErrorType.UNKNOWN

    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """
        Determine if operation should be retried based on error type

        Args:
            error_type: Classified error type
            attempt: Current attempt number

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        # Don't retry authentication or validation errors
        if error_type in [ErrorType.AUTHENTICATION, ErrorType.VALIDATION]:
            return False

        # Retry on network, timeout, and dependency errors
        return error_type in [
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
            ErrorType.DEPENDENCY,
        ]

    async def execute_with_resilience(
        self, operation: Callable[..., T], *args, timeout: float | None = None, **kwargs
    ) -> T:
        """
        Execute operation with resilience patterns

        This method wraps any external API call with:
        - Circuit breaker check
        - Retry with exponential backoff
        - Timeout handling
        - Metrics tracking

        Args:
            operation: Async callable to execute
            *args: Positional arguments for operation
            timeout: Override default timeout (None to use default)
            **kwargs: Keyword arguments for operation

        Returns:
            Result of operation

        Raises:
            RuntimeError: If circuit breaker is open
            TimeoutError: If operation times out
            Exception: Original exception if all retries exhausted
        """
        # Check circuit breaker
        if await self.circuit_breaker.is_open():
            self.logger.warning(f"Circuit breaker is OPEN, rejecting request")
            self.metrics.total_calls += 1
            self.metrics.failed_calls += 1
            raise RuntimeError(
                f"Circuit breaker is open for {self.connector_name}. "
                "Too many recent failures."
            )

        self.metrics.total_calls += 1
        start_time = time.time()
        last_error = None
        operation_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(self.max_retries):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    operation(*args, **kwargs), timeout=operation_timeout
                )

                # Record success
                await self.circuit_breaker.record_success()
                response_time = (time.time() - start_time) * 1000  # ms
                self.metrics.response_times.append(response_time)
                self.metrics.successful_calls += 1

                if attempt > 0:
                    self.metrics.retried_calls += 1
                    self.logger.info(f"Operation succeeded after {attempt} retries")

                return result

            except (asyncio.TimeoutError, TimeoutError) as e:
                last_error = e
                error_type = ErrorType.TIMEOUT
                self.metrics.timeout_errors += 1
                self.metrics.retried_calls += 1

                if attempt < self.max_retries - 1:
                    backoff = self.calculate_backoff(attempt)
                    self.logger.warning(
                        f"Operation timed out (attempt {attempt + 1}/{self.max_retries}). "
                        f"Retrying in {backoff:.2f}s..."
                    )
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(
                        f"Operation timed out after {self.max_retries} attempts"
                    )

            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)

                # Track error types
                if error_type == ErrorType.NETWORK:
                    self.metrics.network_errors += 1
                elif error_type == ErrorType.AUTHENTICATION:
                    self.metrics.authentication_errors += 1

                self.metrics.retried_calls += 1

                # Check if we should retry
                if self.should_retry(error_type, attempt):
                    if attempt < self.max_retries - 1:
                        backoff = self.calculate_backoff(attempt)
                        self.logger.warning(
                            f"Operation failed ({error_type.name}, "
                            f"attempt {attempt + 1}/{self.max_retries}): {e}. "
                            f"Retrying in {backoff:.2f}s..."
                        )
                        await asyncio.sleep(backoff)
                    else:
                        self.logger.error(
                            f"Operation failed after {self.max_retries} attempts: {e}"
                        )
                else:
                    # Don't retry this error type
                    self.logger.error(
                        f"Operation failed with non-retryable error ({error_type.name}): {e}"
                    )
                    break

        # All retries exhausted
        await self.circuit_breaker.record_failure()
        self.metrics.failed_calls += 1
        self.metrics.last_failure = datetime.now()

        if last_error:
            raise RuntimeError(
                f"Operation failed after {self.max_retries} attempts: {last_error}"
            ) from last_error
        else:
            raise RuntimeError("Operation failed: Unknown error")

    def get_metrics(self) -> dict:
        """
        Get connector metrics for monitoring

        Returns:
            Dictionary with current metrics
        """
        return {
            "connector_name": self.metrics.connector_name,
            "total_calls": self.metrics.total_calls,
            "successful_calls": self.metrics.successful_calls,
            "failed_calls": self.metrics.failed_calls,
            "retried_calls": self.metrics.retried_calls,
            "success_rate": self.metrics.success_rate(),
            "avg_response_time_ms": self.metrics.avg_response_time_ms(),
            "timeout_errors": self.metrics.timeout_errors,
            "network_errors": self.metrics.network_errors,
            "authentication_errors": self.metrics.authentication_errors,
            "circuit_breaker_opens": self.metrics.circuit_breaker_opens,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failure_count": self.circuit_breaker.failure_count,
            "last_failure": (
                self.metrics.last_failure.isoformat()
                if self.metrics.last_failure
                else None
            ),
        }


# Global registry of HRIS connectors for metrics aggregation
_hris_connectors: dict[str, ResilientHRISAdapter] = {}


def register_hris_connector(connector: ResilientHRISAdapter):
    """Register an HRIS connector for metrics tracking"""
    _hris_connectors[connector.connector_name] = connector
    logger.info(f"Registered HRIS connector: {connector.connector_name}")


def get_all_hris_metrics() -> dict:
    """Get metrics from all registered HRIS connectors"""
    return {
        name: connector.get_metrics() for name, connector in _hris_connectors.items()
    }


class ResilientXMLRPCWrapper:
    """
    Wrapper for synchronous XML-RPC calls with resilience patterns

    This class wraps synchronous XML-RPC clients (like xmlrpc.client.ServerProxy)
    and provides:
    - Automatic retry with exponential backoff
    - Circuit breaker protection
    - Timeout handling (using thread pool executor)
    - Metrics tracking

    Usage:
        wrapper = ResilientXMLRPCWrapper("odoo", config)

        # Instead of: result = server_proxy.execute_kw(...)
        result = await wrapper.call(server_proxy.execute_kw, args, kwargs)
    """

    def __init__(
        self,
        connector_name: str,
        config: dict,
    ):
        """
        Initialize resilient XML-RPC wrapper

        Args:
            connector_name: Unique name for this connector
            config: Configuration dict with optional timeout, max_retries
        """
        self.connector_name = connector_name
        self.timeout = config.get("timeout", HRIS_DEFAULT_TIMEOUT)
        self.max_retries = config.get("max_retries", HRIS_MAX_RETRIES)

        # Initialize circuit breaker
        self.circuit_breaker = HRISCircuitBreaker(
            connector_name=connector_name,
            failure_threshold=config.get(
                "circuit_failure_threshold", HRIS_CIRCUIT_FAILURE_THRESHOLD
            ),
            recovery_timeout=config.get(
                "circuit_recovery_timeout", HRIS_CIRCUIT_RECOVERY_TIMEOUT
            ),
        )

        # Initialize metrics
        self.metrics = HRISMetrics(connector_name=connector_name)

        self.logger = logging.getLogger(f"{__name__}.{connector_name}")

    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        delay = HRIS_BASE_DELAY * (2**attempt)
        delay = min(delay, HRIS_MAX_DELAY)
        jitter = delay * 0.25 * (random.random() * 2 - 1)
        delay += jitter
        return max(0, delay)

    async def call(
        self, func: Callable, *args, timeout: float | None = None, **kwargs
    ) -> Any:
        """
        Execute synchronous XML-RPC call with resilience patterns

        Args:
            func: Synchronous function to call (e.g., xmlrpc_client.execute_kw)
            *args: Positional arguments for the function
            timeout: Override default timeout
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            RuntimeError: If circuit breaker is open or all retries exhausted
        """
        # Check circuit breaker
        if await self.circuit_breaker.is_open():
            self.logger.warning(f"Circuit breaker is OPEN, rejecting request")
            self.metrics.total_calls += 1
            self.metrics.failed_calls += 1
            raise RuntimeError(f"Circuit breaker is open for {self.connector_name}")

        self.metrics.total_calls += 1
        start_time = time.time()
        last_error = None
        call_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(self.max_retries):
            try:
                # Run synchronous function in thread pool with timeout
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: func(*args, **kwargs)),
                    timeout=call_timeout,
                )

                # Record success
                await self.circuit_breaker.record_success()
                response_time = (time.time() - start_time) * 1000  # ms
                self.metrics.response_times.append(response_time)
                self.metrics.successful_calls += 1

                if attempt > 0:
                    self.metrics.retried_calls += 1
                    self.logger.info(f"XML-RPC call succeeded after {attempt} retries")

                return result

            except (asyncio.TimeoutError, TimeoutError) as e:
                last_error = e
                self.metrics.timeout_errors += 1
                self.metrics.retried_calls += 1

                if attempt < self.max_retries - 1:
                    backoff = self.calculate_backoff(attempt)
                    self.logger.warning(
                        f"XML-RPC call timed out (attempt {attempt + 1}/{self.max_retries}). "
                        f"Retrying in {backoff:.2f}s..."
                    )
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(
                        f"XML-RPC call timed out after {self.max_retries} attempts"
                    )

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                error_type_str = str(type(e).__name__).lower()

                # Track error types
                if any(name in error_type_str for name in ["connection", "network"]):
                    self.metrics.network_errors += 1
                    should_retry = True
                elif any(
                    name in error_str for name in ["unauthorized", "authentication"]
                ):
                    self.metrics.authentication_errors += 1
                    should_retry = False  # Don't retry auth errors
                else:
                    should_retry = True  # Retry other errors

                self.metrics.retried_calls += 1

                if should_retry and attempt < self.max_retries - 1:
                    backoff = self.calculate_backoff(attempt)
                    self.logger.warning(
                        f"XML-RPC call failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {backoff:.2f}s..."
                    )
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(
                        f"XML-RPC call failed after {self.max_retries} attempts: {e}"
                    )
                    break

        # All retries exhausted
        await self.circuit_breaker.record_failure()
        self.metrics.failed_calls += 1
        self.metrics.last_failure = datetime.now()

        if last_error:
            raise RuntimeError(
                f"XML-RPC call failed after {self.max_retries} attempts: {last_error}"
            ) from last_error
        else:
            raise RuntimeError("XML-RPC call failed: Unknown error")

    def get_metrics(self) -> dict:
        """Get wrapper metrics for monitoring"""
        return {
            "connector_name": self.metrics.connector_name,
            "total_calls": self.metrics.total_calls,
            "successful_calls": self.metrics.successful_calls,
            "failed_calls": self.metrics.failed_calls,
            "retried_calls": self.metrics.retried_calls,
            "success_rate": self.metrics.success_rate(),
            "avg_response_time_ms": self.metrics.avg_response_time_ms(),
            "timeout_errors": self.metrics.timeout_errors,
            "network_errors": self.metrics.network_errors,
            "authentication_errors": self.metrics.authentication_errors,
            "circuit_breaker_opens": self.metrics.circuit_breaker_opens,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failure_count": self.circuit_breaker.failure_count,
            "last_failure": (
                self.metrics.last_failure.isoformat()
                if self.metrics.last_failure
                else None
            ),
        }
