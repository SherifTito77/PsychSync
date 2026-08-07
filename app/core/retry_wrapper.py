"""
Enhanced Retry Wrapper with Metrics and Circuit Breaker Integration

Provides a unified retry mechanism with:
- Exponential backoff with jitter
- Prometheus metrics integration
- Circuit breaker protection
- Dead letter queue for permanently failed operations
- Component-specific configuration

Author: Infrastructure Team
Version: 1.0
"""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from app.core.monitoring.retry_metrics import RetryStatus, retry_tracker
from app.core.resilience import get_resilience_manager, CircuitBreaker
from app.core.retry_config import RetryConfig, get_retry_config

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DeadLetterQueue:
    """
    Dead Letter Queue for operations that exhausted all retries.

    Stores failed operations for manual inspection and reprocessing.
    """

    def __init__(self, max_size: int = 10000):
        self._queue = []
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def add(
        self,
        component: str,
        operation: str,
        error: Exception,
        attempts: int,
        context: dict = None,
    ) -> None:
        """Add failed operation to DLQ"""
        async with self._lock:
            entry = {
                "component": component,
                "operation": operation,
                "error": str(error),
                "error_type": type(error).__name__,
                "attempts": attempts,
                "timestamp": time.time(),
                "context": context or {},
            }

            self._queue.append(entry)

            # Trim if exceeding max size
            if len(self._queue) > self._max_size:
                self._queue = self._queue[-self._max_size :]

            logger.warning(
                f"Added to DLQ: {component}.{operation} after {attempts} attempts - {error}"
            )

    async def get_all(self, component: Optional[str] = None) -> list:
        """Get all DLQ entries, optionally filtered by component"""
        async with self._lock:
            if component:
                return [e for e in self._queue if e["component"] == component]
            return self._queue.copy()

    async def get_stats(self) -> dict:
        """Get DLQ statistics"""
        async with self._lock:
            by_component = {}
            for entry in self._queue:
                comp = entry["component"]
                by_component[comp] = by_component.get(comp, 0) + 1

            return {
                "total_entries": len(self._queue),
                "by_component": by_component,
                "max_size": self._max_size,
            }


# Global DLQ instance
_dlq = DeadLetterQueue()


def with_retry(
    component: str,
    operation: Optional[str] = None,
    config: Optional[RetryConfig] = None,
):
    """
    Decorator for automatic retry with metrics and circuit breaker integration.

    Args:
        component: Component name (database, webhook, email_smtp, etc.)
        operation: Operation name (defaults to function name)
        config: Optional custom RetryConfig (uses component defaults if None)

    Example:
        @with_retry(component="database", operation="user_create")
        async def create_user(db, user_data):
            return await db.execute(insert(user).values(**user_data))

        # Environment override:
        # DATABASE_RETRY_MAX_RETRIES=5 DATABASE_RETRY_BASE_DELAY=0.5
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Get configuration
            retry_config = config or get_retry_config(component)
            op_name = operation or func.__name__

            # Get circuit breaker if enabled
            circuit_breaker = None
            if retry_config.enable_circuit_breaker:
                try:
                    manager = get_resilience_manager()
                    cb_name = f"{component}_{op_name}"
                    circuit_breaker = manager.circuit_breakers.get(cb_name)
                    if not circuit_breaker:
                        circuit_breaker = manager.create_circuit_breaker(
                            name=cb_name,
                            failure_threshold=retry_config.circuit_breaker_threshold,
                            recovery_timeout=retry_config.circuit_breaker_timeout,
                        )
                except Exception as e:
                    logger.warning(f"Failed to setup circuit breaker: {e}")

            last_error = None
            start_time = time.time()

            for attempt in range(retry_config.max_retries):
                attempt_start = time.time()

                try:
                    # Execute through circuit breaker if available
                    if circuit_breaker:
                        result = await circuit_breaker.call(
                            lambda: func(*args, **kwargs)
                        )
                    else:
                        result = await func(*args, **kwargs)

                    # Record success metrics
                    if retry_config.enable_metrics:
                        duration_ms = (time.time() - start_time) * 1000
                        await retry_tracker.record_attempt(
                            integration=component,
                            endpoint=f"{component}.{op_name}",
                            attempt_number=attempt + 1,
                            status=RetryStatus.SUCCESS,
                            duration_ms=duration_ms,
                        )

                    # Log if we succeeded after retry
                    if attempt > 0:
                        logger.info(
                            f"{component}.{op_name} succeeded after {attempt} retries",
                            extra={
                                "component": component,
                                "operation": op_name,
                                "attempts": attempt + 1,
                                "duration_ms": (time.time() - start_time) * 1000,
                            },
                        )

                    return result

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # Check if error is retryable
                    is_retryable = any(
                        retry_err in error_str
                        for retry_err in retry_config.retryable_errors
                    )

                    # Record failure metrics
                    if retry_config.enable_metrics:
                        duration_ms = (time.time() - attempt_start) * 1000
                        status = (
                            RetryStatus.RETRY if is_retryable else RetryStatus.FAILURE
                        )
                        await retry_tracker.record_attempt(
                            integration=component,
                            endpoint=f"{component}.{op_name}",
                            attempt_number=attempt + 1,
                            status=status,
                            error_type=type(e).__name__,
                            duration_ms=duration_ms,
                        )

                    # Decide whether to retry
                    if not is_retryable or attempt >= retry_config.max_retries - 1:
                        break

                    # Calculate backoff with jitter
                    delay = retry_config.base_delay * (2**attempt)
                    delay = min(delay, retry_config.max_delay)

                    if retry_config.jitter_enabled:
                        jitter = (
                            delay
                            * retry_config.jitter_percentage
                            * (random.random() * 2 - 1)
                        )
                        delay = max(0, delay + jitter)

                    logger.warning(
                        f"{component}.{op_name} failed (attempt {attempt + 1}/{retry_config.max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s...",
                        extra={
                            "component": component,
                            "operation": op_name,
                            "attempt": attempt + 1,
                            "max_retries": retry_config.max_retries,
                            "error": str(e),
                            "backoff_s": delay,
                        },
                    )

                    await asyncio.sleep(delay)

            # All retries exhausted - add to DLQ and raise
            if retry_config.enable_metrics:
                await retry_tracker.record_attempt(
                    integration=component,
                    endpoint=f"{component}.{op_name}",
                    attempt_number=retry_config.max_retries,
                    status=RetryStatus.FAILURE,
                    error_type=type(last_error).__name__,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Add to Dead Letter Queue
            await _dlq.add(
                component=component,
                operation=op_name,
                error=last_error,
                attempts=retry_config.max_retries,
                context={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
            )

            logger.error(
                f"{component}.{op_name} failed after {retry_config.max_retries} attempts: {last_error}",
                extra={
                    "component": component,
                    "operation": op_name,
                    "attempts": retry_config.max_retries,
                    "error": str(last_error),
                },
            )

            raise last_error

        return wrapper

    return decorator


async def retry_async(
    component: str,
    operation: str,
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> Any:
    """
    Execute an async function with retry logic (non-decorator version).

    Args:
        component: Component name
        operation: Operation name for metrics
        func: Async function to execute
        *args: Arguments to pass to func
        config: Optional custom RetryConfig
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func

    Raises:
        Last exception if all retries exhausted

    Example:
        result = await retry_async(
            "database",
            "fetch_user",
            db.execute,
            select(User).where(User.id == user_id)
        )
    """
    retry_config = config or get_retry_config(component)

    @with_retry(component=component, operation=operation, config=retry_config)
    async def _wrapper():
        return await func(*args, **kwargs)

    return await _wrapper()


def get_dlq() -> DeadLetterQueue:
    """Get the global Dead Letter Queue instance"""
    return _dlq
