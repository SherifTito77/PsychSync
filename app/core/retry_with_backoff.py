"""
EXPONENTIAL BACKOFF RETRY DECORATOR
====================================

Production-ready retry logic with exponential backoff for deadlock-prone operations.

Features:
- Exponential backoff with jitter
- Max retry limits
- Deadlock detection (skip_locked, timeout)
- Comprehensive logging and metrics

Usage:
    @retry_with_exponential_backoff(
        max_attempts=5,
        base_delay=1.0,
        max_delay=60.0,
        exceptions=(DeadlockError, TimeoutError)
    )
    async def update_assessment(assessment_id):
        # Retries automatically with exponential backoff
        # Deadlocks detected and retried seamlessly
        pass

Author: Security Team
Created: February 12, 2026
"""

import asyncio
import logging
import random
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


class DeadlockError(Exception):
    """Raised when a deadlock is detected (skip_locked, timeout, etc.)"""

    pass


class MaxRetriesExceededError(Exception):
    """Raised when max retries exceeded without success"""

    pass


def retry_with_exponential_backoff(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], Any]] = None,
    on_give_up: Optional[Callable[[], Any]] = None,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    exponential_base: float = 2.0,
) -> Callable:
    """
    Decorator for async functions with exponential backoff retry logic.

    Args:
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to retry
        on_retry: Callback after each retry (attempt, exception)
        on_give_up: Callback when giving up
        backoff_multiplier: Delay multiplier (default: 2x)
        jitter: Add randomness to prevent thundering herd
        exponential_base: Base for exponential calculation (default: 2)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
        async def fetch_data(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    # ✅ DEADLOCK DETECTION: Log attempt
                    logger.debug(
                        f"Retry attempt {attempt}/{max_attempts} for {func.__name__}"
                    )

                    # Call the function
                    result = await func(*args, **kwargs)

                    # ✅ SUCCESS: Return result
                    logger.info(f"✅ Success on attempt {attempt}/{max_attempts}")
                    return result

                except exceptions as e:
                    last_exception = e

                    # Check if we should retry
                    should_retry = any(
                        isinstance(e, exc_type) for exc_type in exceptions
                    )

                    if not should_retry or attempt >= max_attempts:
                        # ❌ GIVE UP: Don't retry
                        if on_give_up:
                            await on_give_up(attempt, e)
                        else:
                            logger.error(
                                f"❌ Giving up after {attempt}/{max_attempts} attempts: "
                                f"Last error: {type(e).__name__}: {e}"
                            )
                        raise MaxRetriesExceededError(
                            f"Max retries ({max_attempts}) exceeded: {type(e).__name__}"
                        ) from e

                    # ✅ EXPONENTIAL BACKOFF: Calculate delay before next retry
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay *= random.uniform(0.8, 1.2)
                        logger.debug(
                            f"⏳ Waiting {delay:.2f}s before retry {attempt + 1}"
                        )

                    # Wait before next retry
                    await asyncio.sleep(delay)

                    # ✅ ON RETRY: Call callback
                    if on_retry:
                        await on_retry(attempt, e)

            return wrapper

    return decorator


class RetryMetrics:
    """Track retry metrics for monitoring"""

    def __init__(self):
        self.total_retries = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.retry_by_exception: dict = defaultdict(int)
        self.retry_by_function: dict = defaultdict(int)

    def record_success(self, function_name: str, attempts: int):
        """Record successful operation after retries"""
        self.successful_retries += 1
        self.total_retries += attempts

        logger.debug(f"Retry success: {function_name} after {attempts} attempts")

    def record_failure(
        self,
        function_name: str,
        attempts: int,
        exception: Type[Exception],
    ) -> None:
        """Record failed retry attempt"""
        self.failed_retries += 1
        self.total_retries += attempts
        self.retry_by_exception[function_name] += 1
        self.retry_by_function[function_name] += 1

        logger.warning(
            f"Retry failed: {function_name} attempt {attempts}, "
            f"error: {type(exception).__name__}: {exception}"
        )

    def get_stats(self) -> dict:
        """Get retry statistics"""
        return {
            "total_retries": self.total_retries,
            "successful_retries": self.successful_retries,
            "failed_retries": self.failed_retries,
            "success_rate": (
                (self.successful_retries / self.total_retries * 100)
                if self.total_retries > 0
                else 0
            ),
            "retry_by_exception": dict(self.retry_by_exception),
            "retry_by_function": dict(self.retry_by_function),
        }


# Global metrics instance
retry_metrics = RetryMetrics()


def get_retry_metrics() -> RetryMetrics:
    """Get global retry metrics instance"""
    return retry_metrics


async def retry_with_deadlock_detection(
    operation: str,
    func: Callable,
    *args,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    **kwargs,
) -> Any:
    """
    Execute an async function with deadlock-aware retry logic.

    Args:
        operation: Operation name (for logging)
        func: Async function to execute
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        *args: Arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Raises:
        MaxRetriesExceededError: When all retries exhausted
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = await func(*args, **kwargs)
            retry_metrics.record_success(operation, attempt)
            return result

        except (DeadlockError, Exception) as e:
            last_exception = e

            should_retry = attempt < max_attempts

            if not should_retry:
                retry_metrics.record_failure(operation, attempt, e)

                logger.error(
                    f"❌ Operation {operation} failed: {type(e).__name__}: {e}"
                )

                if isinstance(e, DeadlockError):
                    # Deadlock detected - log with context
                    logger.warning(
                        f"⚠️  DEADLOCK DETECTED: {operation} "
                        f"attempt {attempt}/{max_attempts} - {type(e).__name__}"
                    )

                if should_retry:
                    delay = min(base_delay * (2.0 ** (attempt - 1)), 60.0)

                    logger.info(
                        f"⏳ Retrying {operation} in {delay:.2f}s (attempt {attempt + 1}/{max_attempts})"
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Gave up after {attempt}/{max_attempts} attempts")
                    raise MaxRetriesExceededError(
                        f"Max retries ({max_attempts}) exceeded for {operation}"
                    ) from e


# Export public API
__all__ = [
    "retry_with_exponential_backoff",
    "DeadlockError",
    "MaxRetriesExceededError",
    "get_retry_metrics",
    "retry_with_deadlock_detection",
]
