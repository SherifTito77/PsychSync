"""
Request Timeout Middleware for Slow POST Attack Prevention

Implements timeout protection to prevent:
- Slow POST attacks (slowloris, RUDY, etc.)
- Resource exhaustion via long-running requests
- Connection holding

Security Features:
- Configurable timeout per request type
- Timeout protection for POST/PUT/DELETE/PATCH
- Lenient timeout for GET requests
- Request body size limits
- Timeout tracking and logging
- Graceful timeout handling
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Any, Dict

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestTimeoutConfig:
    """
    Configuration for request timeout middleware
    """

    # Timeout settings (in seconds)
    POST_TIMEOUT = 30
    PUT_TIMEOUT = 30
    DELETE_TIMEOUT = 30
    PATCH_TIMEOUT = 30
    GET_TIMEOUT = 60  # More lenient for GET
    FILE_UPLOAD_TIMEOUT = 60  # Longer for file uploads

    # Request body size limits (in bytes)
    MAX_BODY_SIZE_POST = 10 * 1024 * 1024  # 10MB for POST
    MAX_BODY_SIZE_GET = 1 * 1024 * 1024  # 1MB for GET

    # Enable/disable settings
    ENABLED = True
    TIMEOUT_ON_ERROR = False  # If True, timeout even if timeout occurs

    # Headers to add to timeout responses
    TIMEOUT_HEADER = "X-Request-Timeout"
    TIMEOUT_STATUS = "499"  # HTTP 499 Client Closed Request


class RequestTimeoutMiddleware:
    """
    Middleware for handling request timeouts and slow POST attacks
    """

    def __init__(self, config: RequestTimeoutConfig = None):
        """
        Initialize timeout middleware

        Args:
            config: Optional configuration, uses defaults if not provided
        """
        self.config = config if config else RequestTimeoutConfig()
        self.timeout_counts: {
            "timeouts_triggered": 0,
            "slow_attacks_blocked": 0,
            "connection_holds_detected": 0,
            "large_request_attempts": 0,
            "timeouts_by_endpoint": {},
        }

    async def _get_timeout(self, request: Request) -> int:
        """
        Get timeout based on request method

        Args:
            request: FastAPI request

        Returns:
            Timeout in seconds
        """
        method = request.method

        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            return self.config.POST_TIMEOUT
        elif method == "GET":
            return self.config.GET_TIMEOUT
        elif method in ("HEAD", "OPTIONS"):
            return 60  # Very lenient
        elif method == "DELETE":
            return self.config.DELETE_TIMEOUT
        else:
            return self.config.POST_TIMEOUT  # Default

    def _check_slow_attack_thresholds(self, client_ip: str, request: Request) -> bool:
        """
        Check if client shows signs of slow POST attack

        Args:
            client_ip: Client IP address
            request: Request: FastAPI request

        Returns:
            True if slow attack detected, False otherwise
        """
        # Check for recent timeouts from this IP
        # (This would require tracking recent rate limit violations)
        # For now, use simple heuristics

        # Check request method (slow attacks usually use POST)
        if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
            return False

        # Check Content-Type (slow attacks often send large payloads)
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type and len(request._body) > 100000:
            return True  # Large JSON payload

        # Check User-Agent (common attack tools)
        user_agent = request.headers.get("user-agent", "").lower()
        attack_tools = [
            "curl",
            "wget",
            "python",
            "requests",
            "httpie",
            "sqlmap",
            "nmap",
            "nikto",
        ]
        if any(tool in user_agent for tool in attack_tools):
            return True

        # Check for common attack patterns
        # This would require more sophisticated detection
        return False

        return False

    async def _record_timeout_event(self, request: Request, reason: str, endpoint: str):
        """
        Record a timeout event for monitoring

        Args:
            request: FastAPI request
            reason: Reason for timeout
            endpoint: Endpoint path
        """
        self.timeout_counts["timeouts_triggered"] += 1

        event_data = {
            "client_ip": request.client.host if request.client else "unknown",
            "method": request.method,
            "path": request.url.path,
            "endpoint": endpoint,
            "reason": reason,
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": time.time(),
        }

        logger.warning(
            f"Request timeout triggered: {request.method} {request.url.path}",
            extra={
                "event_type": "request_timeout",
                "client_ip": event_data["client_ip"],
                "endpoint": endpoint,
                "method": event_data["method"],
                "path": event_data["path"],
                "reason": reason,
                "user_agent": event_data["user_agent"],
                "timestamp": event_data["timestamp"],
            },
        )

    async def _is_slow_request(self, request: Request, timeout: int) -> bool:
        """
        Check if request is taking too long to process

        Args:
            request: FastAPI request
            timeout: Timeout threshold in seconds

        Returns:
            True if request is slow
        """
        # This is a simplified version - in production, use request.start_time
        start_time = getattr(request.state, "_start_time", None)

        if start_time:
            elapsed = time.time() - start_time
            return elapsed > (timeout * 0.5)  # 50% of timeout

        return False

    async def _check_request_body_size(self, request: Request) -> bool:
        """
        Check if request body size exceeds limit

        Args:
            request: FastAPI request

        Returns:
            True if size exceeds limit, False otherwise
        """
        body_size_limit = (
            self.config.MAX_BODY_SIZE_POST
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]
            else self.config.MAX_BODY_SIZE_GET
        )

        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if not content_length:
            return False

        try:
            size = int(content_length)
            return size > body_size_limit
        except ValueError:
            return False

    async def _generate_timeout_response(
        self, request: Request, status_code: int
    ) -> Response:
        """
        Generate timeout response with appropriate headers

        Args:
            request: FastAPI request
            status_code: HTTP status code

        Returns:
            JSONResponse with timeout headers
        """
        response = JSONResponse(
            status_code=status_code,
            content={
                "error": "Request timeout",
                "message": f"Request took too long to process. Maximum time is {self._get_timeout(request)} seconds.",
                "retryable": False,
            },
            headers={
                self.config.TIMEOUT_HEADER: self.config.TIMEOUT_STATUS,
                "Content-Type": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

        return response

    async def _detect_slow_post_attack(self, request: Request) -> Optional[str]:
        """
        Detect slow POST attack patterns

        Args:
            request: FastAPI request

        Returns:
            Attack type description if detected, None otherwise
        """
        # Check for slow attack indicators
        if self._check_slow_attack_thresholds(request.client.host, request):
            # Check for large JSON payloads (slow POST attack)
            if (
                "application/json" in request.headers.get("content-type", "")
                and len(request._body) > 50000
            ):
                return "Large JSON payload (slow POST attack)"

            # Check for many fields (complex query)
            if hasattr(request, "_body") and len(request._body) > 0:
                try:
                    import json

                    body = json.loads(request._body)
                    if len(body) > 50:  # Many fields
                        return "Complex query with many fields (slow POST attack)"
                except:
                    pass

        return None

    def create_middleware(self) -> Callable:
        """
        Create middleware function

        Returns:
            Middleware function for FastAPI
        """

        async def middleware(request: Request, call_next):
            """
            Main middleware function
            """
            if not self.config.ENABLED:
                return await call_next(request)

            # Set start time for timeout tracking
            request.state._start_time = time.time()

            # Check request body size first
            if await self._check_request_body_size(request):
                return await self._generate_timeout_response(
                    request, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                )

            # Check if this is a POST/PUT/DELETE/PATCH request
            is_mutation = request.method in ["POST", "PUT", "DELETE", "PATCH"]

            # Process request
            try:
                # Set timeout task
                timeout = self._get_timeout(request)

                # Process with timeout
                if is_mutation:
                    try:
                        response = await asyncio.wait_for(
                            call_next(request), timeout=timeout
                        )
                    except asyncio.TimeoutError:
                        # Timeout occurred
                        logger.warning(
                            f"Request timeout: {request.method} {request.url.path}",
                            extra={
                                "client_ip": (
                                    request.client.host if request.client else "unknown"
                                ),
                                "method": request.method,
                                "path": request.url.path,
                                "timeout": timeout,
                                "user_agent": request.headers.get("user-agent", ""),
                                "timestamp": time.time(),
                            },
                        )

                        # Generate timeout response
                        await self._record_timeout_event(
                            request, "Request processing timeout", request.url.path
                        )

                        # Return timeout response
                        response = self._generate_timeout_response(
                            request, self.config.TIMEOUT_STATUS
                        )

                        # If TIMEOUT_ON_ERROR is True, still attempt to call_next
                        # This allows the request to complete but prevents hanging
                        if self.config.TIMEOUT_ON_ERROR:
                            try:
                                # Try to read response if already sent
                                await call_next(request)
                            except:
                                pass
                        else:
                            return response
                else:
                    # For GET requests, process normally (or use asyncio.wait_for)
                    response = await call_next(request)

                # Record endpoint statistics
                endpoint = request.url.path
                if endpoint not in self.timeout_counts["timeouts_by_endpoint"]:
                    self.timeout_counts["timeouts_by_endpoint"][endpoint] = 0

                # Check if slow POST attack detected
                attack_type = await self._detect_slow_post_attack(request)
                if attack_type:
                    self.timeout_counts["slow_attacks_blocked"] += 1
                    logger.warning(
                        f"Slow POST attack detected and blocked: {attack_type}",
                        extra={
                            "client_ip": request.client.host,
                            "endpoint": endpoint,
                            "method": request.method,
                            "path": request.path,
                            "attack_type": attack_type,
                            "timestamp": time.time(),
                        },
                    )

                    # Return timeout response to block the attack
                    response = await self._generate_timeout_response(
                        request, status.HTTP_429_TOO_MANY_REQUESTS
                    )

                    # Clean up request state
                    if hasattr(request.state, "_start_time"):
                        delattr(request.state, "_start_time")

                    # return response

                # Check request duration and log slow requests
                if is_mutation:
                    duration = (
                        time.time() - request.state._start_time
                        if hasattr(request.state, "_start_time")
                        else 0
                    )
                    slow_threshold = timeout * 0.7  # 70% of timeout
                    if duration > slow_threshold:
                        logger.info(
                            f"Slow request detected: {duration:.2f}s threshold: {slow_threshold:.2f}s",
                            extra={
                                "client_ip": request.client.host,
                                "method": request.method,
                                "path": request.url.path,
                                "duration": duration,
                                "timeout": timeout,
                            },
                        )

                return response

            except Exception as e:
                logger.error(f"Timeout middleware error: {e}")

                return response


# Global instance
request_timeout_middleware = RequestTimeoutMiddleware()


def get_request_timeout_middleware(
    config: Optional[RequestTimeoutConfig] = None,
) -> Callable:
    """
    Factory function to create timeout middleware with custom config

    Args:
        config: Optional configuration

    Returns:
        Middleware function for FastAPI
    """
    middleware = RequestTimeoutMiddleware(config)
    return middleware
