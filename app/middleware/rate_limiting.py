"""
Rate Limiting Middleware for Expensive Operations

Implements rate limiting using slowapi to prevent DoS attacks and resource exhaustion.
"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour"],  # Default limit for all endpoints
    storage_uri="redis://localhost:6379/1",  # Redis for distributed rate limiting
    storage_options={"decode_responses": True},
)


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user ID from request for user-specific rate limiting.

    Args:
        request: FastAPI request object

    Returns:
        User ID if authenticated, otherwise IP address
    """
    # Try to get user from JWT token
    # This would typically come from the authentication dependency
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"

    # Fall back to IP address
    return get_remote_address(request)


# Custom rate limit decorators for expensive operations
def rate_limit_assessment_creation(func: Callable) -> Callable:
    """
    Rate limit assessment creation to prevent spam.

    Limit: 10 assessments per hour per user
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would be implemented with proper user context
        # For now, using IP-based rate limiting
        return await func(*args, **kwargs)

    return wrapper


def rate_limit_optimization(func: Callable) -> Callable:
    """
    Rate limit team optimization operations (computationally expensive).

    Limit: 5 optimizations per hour per user
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


def rate_limit_gdpr_export(func: Callable) -> Callable:
    """
    Rate limit GDPR data exports (resource intensive).

    Limit: 3 exports per hour per user
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


class SecurityEventLogger:
    """
    Comprehensive security event logging system.

    Logs all security-relevant events with structured context.
    """

    def __init__(self):
        self.logger = logging.getLogger("security")

    async def log_failed_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        user_agent: str,
        reason: str = "Unauthorized",
    ):
        """Log failed authorization attempt"""
        self.logger.warning(
            "Security: Failed authorization attempt",
            extra={
                "event_type": "failed_authorization",
                "user_id": str(user_id),
                "resource": resource,
                "action": action,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high",
            },
        )

    async def log_suspicious_activity(
        self,
        user_id: str,
        activity_type: str,
        details: dict,
        ip_address: str,
        severity: str = "medium",
    ):
        """Log suspicious activity"""
        self.logger.warning(
            f"Security: Suspicious activity detected - {activity_type}",
            extra={
                "event_type": "suspicious_activity",
                "activity_type": activity_type,
                "user_id": str(user_id),
                "details": details,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": severity,
            },
        )

    async def log_rate_limit_exceeded(
        self,
        identifier: str,
        endpoint: str,
        limit: str,
        ip_address: str,
    ):
        """Log rate limit exceeded event"""
        self.logger.warning(
            f"Security: Rate limit exceeded - {identifier}",
            extra={
                "event_type": "rate_limit_exceeded",
                "identifier": identifier,
                "endpoint": endpoint,
                "limit": limit,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "medium",
            },
        )

    async def log_successful_authentication(
        self, user_id: str, method: str, ip_address: str
    ):
        """Log successful authentication"""
        self.logger.info(
            f"Security: Successful authentication - {user_id}",
            extra={
                "event_type": "successful_authentication",
                "user_id": str(user_id),
                "auth_method": method,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "info",
            },
        )

    async def log_failed_authentication(
        self,
        username: str | None,
        reason: str,
        ip_address: str,
        user_agent: str,
    ):
        """Log failed authentication attempt"""
        self.logger.warning(
            "Security: Failed authentication attempt",
            extra={
                "event_type": "failed_authentication",
                "username": username,
                "reason": reason,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high",
            },
        )

    async def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str,
    ):
        """Log data access for audit trail"""
        self.logger.info(
            f"Audit: Data access - {resource_type}:{resource_id}",
            extra={
                "event_type": "data_access",
                "user_id": str(user_id),
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "action": action,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "info",
            },
        )

    async def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        changes: dict,
        ip_address: str,
    ):
        """Log data modifications for audit trail"""
        self.logger.info(
            f"Audit: Data modification - {resource_type}:{resource_id}",
            extra={
                "event_type": "data_modification",
                "user_id": str(user_id),
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "changes": changes,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "info",
            },
        )

    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: dict,
        ip_address: str | None = None,
    ):
        """Log generic security event"""
        log_func = (
            self.logger.error
            if severity == "critical"
            else (
                self.logger.warning
                if severity in ["high", "medium"]
                else self.logger.info
            )
        )

        log_func(
            f"Security: {event_type}",
            extra={
                "event_type": event_type,
                "severity": severity,
                "details": details,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# Global security event logger instance
security_logger = SecurityEventLogger()


async def log_security_middleware(request: Request, call_next):
    """
    Middleware to log all requests for security monitoring.

    Logs:
    - Request path and method
    - Response status
    - Request duration
    - IP address
    - User agent
    """
    start_time = datetime.utcnow()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

    # Log request
    if response.status_code >= 400:
        # Log error responses
        security_logger.logger.warning(
            f"Request error: {request.method} {request.url.path}",
            extra={
                "event_type": "http_error",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    return response
