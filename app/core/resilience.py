"""
Comprehensive Resilience and Error Handling

This module provides enterprise-grade resilience patterns including:
- Circuit breakers with configurable thresholds
- Retry policies with exponential backoff
- Rate limiting with adaptive algorithms
- Bulkhead isolation for resource protection
- Timeout management with graceful degradation
- Comprehensive error classification and handling
"""

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from functools import wraps
import logging
import statistics
import time
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")


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


class BulkheadState(Enum):
    """Bulkhead isolation states"""

    HEALTHY = "healthy"  # Operating normally
    ISOLATED = "isolated"  # Isolated to prevent failure spread
    RECOVERING = "recovering"  # In recovery process


@dataclass
class ErrorInfo:
    """Structured error information for analysis"""

    error_type: ErrorType
    error_message: str
    timestamp: datetime
    context: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    original_exception: Exception | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "error_type": self.error_type.name,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "retry_count": self.retry_count,
            "original_exception": str(self.original_exception) if self.original_exception else None,
        }


class ErrorClassifier:
    """Classifies errors into types for appropriate handling"""

    @staticmethod
    def classify_error(error: Exception, context: dict[str, Any] = None) -> ErrorInfo:
        """Classify an exception into an error type"""
        context = context or {}

        # Network-related errors
        if isinstance(error, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
            return ErrorInfo(
                error_type=ErrorType.NETWORK,
                error_message=str(error),
                timestamp=datetime.now(),
                context=context,
                original_exception=error,
            )

        # Timeout errors
        if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
            return ErrorInfo(
                error_type=ErrorType.TIMEOUT,
                error_message=str(error),
                timestamp=datetime.now(),
                context=context,
                original_exception=error,
            )

        # HTTP status code based classification (if available)
        if hasattr(error, "status_code"):
            status_code = error.status_code
            if status_code == 429:
                return ErrorInfo(
                    error_type=ErrorType.RATE_LIMIT,
                    error_message=str(error),
                    timestamp=datetime.now(),
                    context=context,
                    original_exception=error,
                )
            if status_code in (401, 403):
                return ErrorInfo(
                    error_type=ErrorType.AUTHENTICATION,
                    error_message=str(error),
                    timestamp=datetime.now(),
                    context=context,
                    original_exception=error,
                )
            if status_code >= 500:
                return ErrorInfo(
                    error_type=ErrorType.DEPENDENCY,
                    error_message=str(error),
                    timestamp=datetime.now(),
                    context=context,
                    original_exception=error,
                )

        # Database errors
        if "database" in str(type(error)).lower() or "sql" in str(type(error)).lower():
            return ErrorInfo(
                error_type=ErrorType.DEPENDENCY,
                error_message=str(error),
                timestamp=datetime.now(),
                context=context,
                original_exception=error,
            )

        # Default classification
        return ErrorInfo(
            error_type=ErrorType.UNKNOWN,
            error_message=str(error),
            timestamp=datetime.now(),
            context=context,
            original_exception=error,
        )


class CircuitBreaker:
    """Advanced circuit breaker with adaptive thresholds"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        success_threshold: int = 3,
        timeout: float = 30.0,
        half_open_max_calls: int = 5,
        monitoring_window: int = 100,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.monitoring_window = monitoring_window

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.last_state_change = datetime.now()

        # Metrics for adaptive behavior
        self.call_history = deque(maxlen=monitoring_window)
        self.failure_history = deque(maxlen=monitoring_window)
        self.response_times = deque(maxlen=50)

        # Half-open state tracking
        self.half_open_calls = 0

        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        start_time = time.time()

        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                self.logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        if (
            self.state == CircuitState.HALF_OPEN
            and self.half_open_calls >= self.half_open_max_calls
        ):
            raise CircuitBreakerOpenError(f"Circuit breaker {self.name} HALF_OPEN limit reached")

        try:
            # Execute with timeout
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)

            # Record successful call
            execution_time = time.time() - start_time
            self._on_success(execution_time)

            return result

        except self.expected_exception as e:
            execution_time = time.time() - start_time
            error_info = ErrorClassifier.classify_error(e, {"circuit_breaker": self.name})
            self._on_failure(error_info, execution_time)
            raise

        except Exception as e:
            execution_time = time.time() - start_time
            error_info = ErrorClassifier.classify_error(e, {"circuit_breaker": self.name})
            self._on_failure(error_info, execution_time)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return True

        time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout

    def _on_success(self, execution_time: float):
        """Handle successful call"""
        self.call_history.append(True)
        self.response_times.append(execution_time)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.half_open_calls += 1

            if self.success_count >= self.success_threshold:
                self._reset_circuit()

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, error_info: ErrorInfo, execution_time: float):
        """Handle failed call"""
        self.call_history.append(False)
        self.failure_history.append(error_info)
        self.response_times.append(execution_time)
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failed in half-open, return to open
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.logger.warning(
                f"Circuit breaker {self.name} returned to OPEN after HALF_OPEN failure"
            )

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning(
                    f"Circuit breaker {self.name} opened after {self.failure_count} failures"
                )

        self.last_state_change = datetime.now()

    def _reset_circuit(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_state_change = datetime.now()
        self.logger.info(f"Circuit breaker {self.name} reset to CLOSED")

    def get_metrics(self) -> dict[str, Any]:
        """Get circuit breaker metrics"""
        recent_calls = list(self.call_history)[-20:] if self.call_history else []
        recent_failures = [
            f for f in self.failure_history if (datetime.now() - f.timestamp).seconds < 300
        ]

        success_rate = sum(recent_calls) / len(recent_calls) if recent_calls else 1.0
        avg_response_time = statistics.mean(self.response_times) if self.response_times else 0

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "success_rate": round(success_rate * 100, 2),
            "avg_response_time": round(avg_response_time * 1000, 2),  # ms
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "last_state_change": self.last_state_change.isoformat(),
            "recent_failures_count": len(recent_failures),
            "total_calls": len(self.call_history),
            "monitoring_window": self.monitoring_window,
        }


class RetryPolicy:
    """Advanced retry policy with exponential backoff and jitter"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: list[ErrorType] = None,
        stop_on: list[ErrorType] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or [ErrorType.NETWORK, ErrorType.TIMEOUT, ErrorType.DEPENDENCY]
        self.stop_on = stop_on or [ErrorType.VALIDATION, ErrorType.AUTHENTICATION]

    def should_retry(self, error_info: ErrorInfo, attempt: int) -> bool:
        """Determine if operation should be retried"""
        if attempt >= self.max_attempts:
            return False

        # Don't retry on non-retryable errors
        if error_info.error_type in self.stop_on:
            return False

        # Retry on specified error types
        return error_info.error_type in self.retry_on

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt"""
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base**attempt)

        # Apply maximum delay limit
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        if self.jitter:
            delay *= 0.5 + secrets.SystemRandom().random() * 0.5

        return delay


class RateLimiter:
    """Adaptive rate limiter with multiple algorithms"""

    def __init__(
        self,
        name: str,
        algorithm: str = "sliding_window",
        limit: int = 100,
        window: float = 60.0,
        burst_limit: int = None,
    ):
        self.name = name
        self.algorithm = algorithm
        self.limit = limit
        self.window = window
        self.burst_limit = burst_limit or limit * 2

        # Sliding window state
        self.requests = deque()
        self.adaptive_limit = limit

        # Token bucket state
        self.tokens = limit
        self.last_refill = time.time()
        self.refill_rate = limit / window

        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire rate limit permit"""
        if self.algorithm == "sliding_window":
            return await self._sliding_window_acquire(tokens)
        if self.algorithm == "token_bucket":
            return await self._token_bucket_acquire(tokens)
        raise ValueError(f"Unknown rate limiting algorithm: {self.algorithm}")

    async def _sliding_window_acquire(self, tokens: int = 1) -> bool:
        """Sliding window rate limiting"""
        now = time.time()

        # Clean old requests
        while self.requests and self.requests[0] <= now - self.window:
            self.requests.popleft()

        # Check if we can accommodate this request
        if len(self.requests) + tokens <= self.adaptive_limit:
            for _ in range(tokens):
                self.requests.append(now)
            return True

        return False

    async def _token_bucket_acquire(self, tokens: int = 1) -> bool:
        """Token bucket rate limiting"""
        now = time.time()

        # Refill tokens
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.tokens + tokens_to_add, self.burst_limit)
        self.last_refill = now

        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_metrics(self) -> dict[str, Any]:
        """Get rate limiter metrics"""
        if self.algorithm == "sliding_window":
            now = time.time()
            recent_requests = [r for r in self.requests if r > now - self.window]
            utilization = len(recent_requests) / self.adaptive_limit * 100

            return {
                "algorithm": self.algorithm,
                "current_requests": len(recent_requests),
                "limit": self.adaptive_limit,
                "utilization_percent": round(utilization, 2),
                "window": self.window,
            }

        # token_bucket
        utilization = (self.burst_limit - self.tokens) / self.burst_limit * 100
        return {
            "algorithm": self.algorithm,
            "tokens_available": round(self.tokens, 2),
            "burst_limit": self.burst_limit,
            "utilization_percent": round(utilization, 2),
            "refill_rate": round(self.refill_rate, 2),
        }


class Bulkhead:
    """Bulkhead pattern for resource isolation"""

    def __init__(
        self,
        name: str,
        max_concurrent_calls: int = 10,
        max_queue_size: int = 50,
        timeout: float = 30.0,
    ):
        self.name = name
        self.max_concurrent_calls = max_concurrent_calls
        self.max_queue_size = max_queue_size
        self.timeout = timeout

        # State tracking
        self.concurrent_calls = 0
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.state = BulkheadState.HEALTHY
        self.total_calls = 0
        self.rejected_calls = 0
        self.timeouts = 0

        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead isolation"""
        self.total_calls += 1

        # Check if we can accept the call
        if self.concurrent_calls >= self.max_concurrent_calls:
            if self.queue.full():
                self.rejected_calls += 1
                raise BulkheadFullError(f"Bulkhead {self.name} is full")

        # Try to queue the call
        try:
            await asyncio.wait_for(self.queue.put(None), timeout=1.0)
        except TimeoutError:
            self.rejected_calls += 1
            raise BulkheadFullError(f"Bulkhead {self.name} queue timeout") from e

        self.concurrent_calls += 1

        try:
            # Execute the function
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
            return result

        except TimeoutError:
            self.timeouts += 1
            raise

        finally:
            self.concurrent_calls -= 1
            # Remove from queue
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                pass

    def get_metrics(self) -> dict[str, Any]:
        """Get bulkhead metrics"""
        rejection_rate = (
            (self.rejected_calls / self.total_calls * 100) if self.total_calls > 0 else 0
        )
        timeout_rate = (self.timeouts / self.total_calls * 100) if self.total_calls > 0 else 0

        return {
            "name": self.name,
            "state": self.state.value,
            "concurrent_calls": self.concurrent_calls,
            "max_concurrent_calls": self.max_concurrent_calls,
            "queue_size": self.queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "total_calls": self.total_calls,
            "rejected_calls": self.rejected_calls,
            "timeouts": self.timeouts,
            "rejection_rate_percent": round(rejection_rate, 2),
            "timeout_rate_percent": round(timeout_rate, 2),
        }


class ResilienceManager:
    """Central resilience manager coordinating all patterns"""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.rate_limiters: dict[str, RateLimiter] = {}
        self.bulkheads: dict[str, Bulkhead] = {}
        self.retry_policies: dict[str, RetryPolicy] = {}

    def create_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Create and register a circuit breaker"""
        cb = CircuitBreaker(name, **kwargs)
        self.circuit_breakers[name] = cb
        return cb

    def create_rate_limiter(self, name: str, **kwargs) -> RateLimiter:
        """Create and register a rate limiter"""
        rl = RateLimiter(name, **kwargs)
        self.rate_limiters[name] = rl
        return rl

    def create_bulkhead(self, name: str, **kwargs) -> Bulkhead:
        """Create and register a bulkhead"""
        bh = Bulkhead(name, **kwargs)
        self.bulkheads[name] = bh
        return bh

    def create_retry_policy(self, name: str, **kwargs) -> RetryPolicy:
        """Create and register a retry policy"""
        rp = RetryPolicy(**kwargs)
        self.retry_policies[name] = rp
        return rp

    def get_all_metrics(self) -> dict[str, Any]:
        """Get metrics from all resilience components"""
        return {
            "circuit_breakers": {
                name: cb.get_metrics() for name, cb in self.circuit_breakers.items()
            },
            "rate_limiters": {name: rl.get_metrics() for name, rl in self.rate_limiters.items()},
            "bulkheads": {name: bh.get_metrics() for name, bh in self.bulkheads.items()},
            "retry_policies": list(self.retry_policies.keys()),
        }


# Custom exception classes
class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""


class BulkheadFullError(Exception):
    """Raised when bulkhead is full"""


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded"""


# Decorators for easy application of resilience patterns
def resilient(
    circuit_breaker: str = None,
    rate_limiter: str = None,
    bulkhead: str = None,
    retry_policy: str = None,
    timeout: float = None,
):
    """Decorator for applying resilience patterns"""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_resilience_manager()

            # Get resilience components
            cb = manager.circuit_breakers.get(circuit_breaker) if circuit_breaker else None
            rl = manager.rate_limiters.get(rate_limiter) if rate_limiter else None
            bh = manager.bulkheads.get(bulkhead) if bulkhead else None
            rp = manager.retry_policies.get(retry_policy) if retry_policy else None

            # Apply rate limiting
            if rl:
                if not await rl.acquire():
                    raise RateLimitExceededError(f"Rate limit exceeded for {rate_limiter}")

            # Apply bulkhead
            if bh:
                return await bh.execute(
                    _execute_with_circuit_breaker_and_retry, func, cb, rp, *args, **kwargs
                )
            return await _execute_with_circuit_breaker_and_retry(func, cb, rp, *args, **kwargs)

        return wrapper

    return decorator


async def _execute_with_circuit_breaker_and_retry(
    func: Callable,
    circuit_breaker: CircuitBreaker | None,
    retry_policy: RetryPolicy | None,
    *args,
    **kwargs,
):
    """Execute function with circuit breaker and retry logic"""
    if circuit_breaker:
        if retry_policy:
            return await _execute_with_retry(
                circuit_breaker.call, func, retry_policy, *args, **kwargs
            )
        return await circuit_breaker.call(func, *args, **kwargs)
    if retry_policy:
        return await _execute_with_retry(func, func, retry_policy, *args, **kwargs)
    return await func(*args, **kwargs)


async def _execute_with_retry(
    func: Callable, target_func: Callable, retry_policy: RetryPolicy, *args, **kwargs
):
    """Execute function with retry logic"""
    last_error = None

    for attempt in range(retry_policy.max_attempts):
        try:
            return await target_func(*args, **kwargs)
        except Exception as e:
            last_error = e
            error_info = ErrorClassifier.classify_error(e)

            if not retry_policy.should_retry(error_info, attempt):
                raise

            if attempt < retry_policy.max_attempts - 1:
                delay = retry_policy.get_delay(attempt)
                await asyncio.sleep(delay)

    raise last_error


# Global resilience manager instance
_resilience_manager: ResilienceManager | None = None


def get_resilience_manager() -> ResilienceManager:
    """Get or create global resilience manager"""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = ResilienceManager()
    return _resilience_manager


# Convenience functions for common patterns
def with_circuit_breaker(name: str, **kwargs):
    """Decorator for circuit breaker only"""
    return resilient(circuit_breaker=name, **kwargs)


def with_rate_limiter(name: str, **kwargs):
    """Decorator for rate limiter only"""
    return resilient(rate_limiter=name, **kwargs)


def with_bulkhead(name: str, **kwargs):
    """Decorator for bulkhead only"""
    return resilient(bulkhead=name, **kwargs)


def with_retry(**kwargs):
    """Decorator for retry policy only"""
    rp_name = kwargs.get("name", "default")
    manager = get_resilience_manager()
    if rp_name not in manager.retry_policies:
        manager.create_retry_policy(rp_name, **{k: v for k, v in kwargs.items() if k != "name"})
    return resilient(retry_policy=rp_name)
