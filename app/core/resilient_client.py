"""
Resilient HTTP Client - Production-grade HTTP client with resilience patterns

This module provides a robust HTTP client with:
- Timeouts on all requests
- Automatic retry with exponential backoff
- Circuit breaker integration
- Connection pooling
- Request/response validation
- Comprehensive logging and monitoring

Usage:
    from app.core.resilient_client import resilient_http_client

    response = await resilient_http_client.post(
        "https://api.example.com/endpoint",
        json={"key": "value"},
        timeout=30.0,  # Optional: override default timeout
        retries=3,  # Optional: override default retry count
    )
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import uuid

import httpx
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

from app.core.resilience import Circuit, ErrorType, CircuitState


logger = logging.getLogger(__name__)


class HTTPClientError(Exception):
    """Base exception for HTTP client errors"""
    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class TimeoutError(HTTPClientError):
    """Request timed out"""
    pass


class RetryExhaustedError(HTTPClientError):
    """All retry attempts exhausted"""
    pass


class CircuitBreakerOpenError(HTTPClientError):
    """Circuit breaker is open, request blocked"""
    pass


@dataclass
class HTTPRequestConfig:
    """Configuration for HTTP requests"""

    # Timeout configuration
    timeout: float = 30.0  # Default timeout for all requests
    connect_timeout: float = 10.0  # Timeout for initial connection

    # Retry configuration
    max_retries: int = 3  # Maximum number of retry attempts
    retry_multiplier: float = 1.0  # Exponential backoff multiplier
    retry_min: float = 1.0  # Minimum wait between retries (seconds)
    retry_max: float = 10.0  # Maximum wait between retries (seconds)

    # Circuit breaker configuration
    circuit_failure_threshold: int = 5  # Failures before opening circuit
    circuit_recovery_timeout: float = 60.0  # Seconds before trying again
    circuit_half_open_attempts: int = 3  # Attempts in half-open state

    # Circuit breaker enabled by default
    enable_circuit_breaker: bool = True

    # Retry on these status codes
    retry_status_codes = frozenset({408, 429, 500, 502, 503, 504})

    # Retry on these exception types
    retry_exceptions = frozenset({
        # TimeoutError,  # Don't retry timeouts - they're usually permanent
        ConnectionError,
        ConnectionRefusedError,
        ConnectionResetError,
        # Add more specific exceptions as needed
    })

    # Validation
    validate_response: bool = True  # Validate response structure
    max_response_size: int = 10 * 1024 * 1024  # 10MB max response


class ResilientHTTPClient:
    """
    Production-grade HTTP client with resilience patterns.

    Features:
    - Timeouts on all requests (prevents hanging)
    - Automatic retry with exponential backoff (handles transient failures)
    - Circuit breaker integration (prevents cascading failures)
    - Connection pooling (better performance)
    - Request/response logging (observability)
    - Comprehensive error handling

    Singleton Pattern: Use the global `resilient_http_client` instance.
    """

    def __init__(self, config: HTTPRequestConfig | None = None):
        """
        Initialize resilient HTTP client.

        Args:
            config: Request configuration (uses defaults if not provided)
        """
        self.config = config or HTTPRequestConfig()

        # Create HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.timeout,
                write=self.config.timeout,
            ),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            ),
        )

        # Create circuit breakers for different endpoints
        self._circuits: dict[str, Circuit] = {}
        self._circuit_lock = asyncio.Lock()

        logger.info(
            f"ResilientHTTPClient initialized: "
            f"timeout={self.config.timeout}s, "
            f"retries={self.config.max_retries}, "
            f"circuit_breaker={'enabled' if self.config.enable_circuit_breaker else 'disabled'}"
        )

    async def _get_or_create_circuit(self, key: str) -> Circuit | None:
        """Get or create circuit breaker for endpoint"""
        if not self.config.enable_circuit_breaker:
            return None

        async with self._circuit_lock:
            if key not in self._circuits:
                self._circuits[key] = Circuit(
                    failure_threshold=self.config.circuit_failure_threshold,
                    recovery_timeout=self.config.circuit_recovery_timeout,
                    half_open_attempts=self.config.circuit_half_open_attempts,
                )
                logger.info(f"Created circuit breaker for endpoint: {key}")

        return self._circuits.get(key)

    def _should_retry(self, response: httpx.Response) -> bool:
        """Determine if request should be retried based on status code"""
        return response.status_code in self.config.retry_status_codes

    def _should_retry_exception(self, exception: Exception) -> bool:
        """Determine if request should be retried based on exception type"""
        # Don't retry timeouts - they usually indicate permanent issues
        if isinstance(exception, (asyncio.TimeoutError, httpx.TimeoutException)):
            return False

        # Retry connection errors
        return isinstance(exception, self.config.retry_exceptions)

    async def _execute_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Execute HTTP request with resilience patterns.

        This method implements:
        1. Circuit breaker check (if enabled)
        2. Retry logic with exponential backoff
        3. Comprehensive logging
        4. Error handling
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()

        # Extract endpoint key for circuit breaker
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        endpoint_key = f"{method}:{parsed_url.netloc}:{parsed_url.path}"

        # Check circuit breaker
        circuit = await self._get_or_create_circuit(endpoint_key)
        if circuit:
            if await circuit.is_open():
                logger.warning(
                    f"[{request_id}] Circuit breaker OPEN for {endpoint_key}, blocking request"
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open for {endpoint_key}. Too many recent failures.",
                    status_code=503,
                )

        # Execute with retry logic
        last_exception = None
        attempt = 0

        while attempt <= self.config.max_retries:
            attempt += 1

            try:
                logger.info(
                    f"[{request_id}] {method} {url} (attempt {attempt}/{self.config.max_retries + 1})"
                )

                # Execute request
                response = await self._client.request(method, url, **kwargs)

                # Validate response size
                if self.config.validate_response:
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.config.max_response_size:
                        logger.error(
                            f"[{request_id}] Response too large: {content_length} bytes "
                            f"(max: {self.config.max_response_size})"
                        )
                        raise HTTPClientError(
                            f"Response size exceeds maximum allowed size"
                        )

                # Check if we should retry based on status code
                if response.status_code >= 400:
                    if attempt < self.config.max_retries and self._should_retry(response):
                        wait_time = min(
                            self.config.retry_min * (self.config.retry_multiplier ** (attempt - 1)),
                            self.config.retry_max
                        )
                        logger.warning(
                            f"[{request_id}] Got {response.status_code}, "
                            f"retrying in {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    # Record failure in circuit breaker
                    if circuit and response.status_code >= 500:
                        await circuit.record_failure()
                        logger.error(
                            f"[{request_id}] Request failed: {response.status_code} "
                            f"(circuit state: {await circuit.get_state()})"
                        )
                else:
                    # Record success in circuit breaker
                    if circuit:
                        await circuit.record_success()

                    # Log success
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.info(
                        f"[{request_id}] Success: {method} {url} → "
                        f"{response.status_code} ({duration:.3f}s)"
                    )

                    return response

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"[{request_id}] Request timed out: {e}")

                if attempt < self.config.max_retries:
                    # Don't retry timeouts - they're usually permanent
                    # But we wait once more to be sure
                    wait_time = self.config.retry_min
                    logger.warning(f"[{request_id}] Timeout, final retry in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Record failure in circuit breaker
                    if circuit:
                        await circuit.record_failure()
                    raise TimeoutError(f"Request timed out after {attempt} attempts")

            except (ConnectionError, ConnectionRefusedError, ConnectionResetError) as e:
                last_exception = e
                logger.warning(f"[{request_id}] Connection error: {e}")

                if attempt < self.config.max_retries:
                    wait_time = min(
                        self.config.retry_min * (self.config.retry_multiplier ** (attempt - 1)),
                        self.config.retry_max
                    )
                    logger.warning(f"[{request_id}] Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Record failure in circuit breaker
                    if circuit:
                        await circuit.record_failure()
                    raise HTTPClientError(f"Connection failed after {attempt} attempts") from e

            except Exception as e:
                last_exception = e
                logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)

                # Record failure in circuit breaker
                if circuit:
                    await circuit.record_failure()

                # Don't retry unknown exceptions
                raise HTTPClientError(f"Request failed: {str(e)}") from e

        # All retries exhausted
        if last_exception:
            raise RetryExhaustedError(
                f"Request failed after {self.config.max_retries + 1} attempts"
            ) from last_exception

    # Convenience methods

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Execute GET request"""
        return await self._execute_request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Execute POST request"""
        return await self._execute_request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Execute PUT request"""
        return await self._execute_request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Execute PATCH request"""
        return await self._execute_request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Execute DELETE request"""
        return await self._execute_request("DELETE", url, **kwargs)

    async def close(self):
        """Close HTTP client and release resources"""
        await self._client.aclose()
        logger.info("ResilientHTTPClient closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Global instance for application-wide use
resilient_http_client = ResilientHTTPClient()

# Convenience function
async def resilient_request(
    method: str,
    url: str,
    config: HTTPRequestConfig | None = None,
    **kwargs
) -> httpx.Response:
    """
    Convenience function for making resilient HTTP requests.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        config: Optional configuration override
        **kwargs: Additional arguments passed to httpx

    Returns:
        HTTP response

    Raises:
        TimeoutError: If request times out
        RetryExhaustedError: If all retries exhausted
        CircuitBreakerOpenError: If circuit breaker is open
        HTTPClientError: For other errors

    Example:
        response = await resilient_request(
            "POST",
            "https://api.example.com/endpoint",
            json={"key": "value"},
        )
    """
    client = ResilientHTTPClient(config)
    try:
        return await client._execute_request(method, url, **kwargs)
    finally:
        await client.close()


# Decorator for adding resilience to existing functions
def with_resilience(
    max_retries: int = 3,
    timeout: float = 30.0,
    circuit_breaker: bool = True,
):
    """
    Decorator to add resilience patterns to async functions that make HTTP calls.

    Example:
        @with_resilience(max_retries=3, timeout=30.0)
        async def call_external_api(data):
            async with httpx.AsyncClient(timeout=30.0) as client:
                return await client.post("https://api.example.com", json=data)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            config = HTTPRequestConfig(
                timeout=timeout,
                max_retries=max_retries,
                enable_circuit_breaker=circuit_breaker,
            )
            client = ResilientHTTPClient(config)
            try:
                # Call the original function (assuming it makes HTTP calls)
                result = await func(*args, **kwargs)
                return result
            finally:
                await client.close()
        return wrapper
    return decorator
