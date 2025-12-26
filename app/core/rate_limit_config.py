"""
Comprehensive Rate Limiting Configuration for FastAPI
Implements tiered rate limiting based on endpoint sensitivity
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RateLimitTier(str, Enum):
    """Rate limiting tiers based on endpoint sensitivity."""
    STRICT = "strict"  # Authentication endpoints
    HIGH = "high"  # API endpoints
    MEDIUM = "medium"  # General endpoints
    LOW = "low"  # Public endpoints
    CUSTOM = "custom"  # Custom limits


class RateLimitConfig(BaseModel):
    """Rate limit configuration for an endpoint tier."""

    # Request limits
    requests_per_minute: int = Field(..., description="Requests allowed per minute")
    requests_per_hour: int = Field(..., description="Requests allowed per hour")
    requests_per_day: int = Field(..., description="Requests allowed per day")

    # Burst protection
    burst_size: int = Field(default=10, description="Maximum burst size")

    # Enabled flag
    enabled: bool = Field(default=True, description="Whether rate limiting is enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "burst_size": 10,
                "enabled": True
            }
        }


# Predefined rate limit configurations for different endpoint types
RATE_LIMIT_TIERS: Dict[RateLimitTier, RateLimitConfig] = {
    # STRICT: Authentication endpoints (login, register, password reset)
    RateLimitTier.STRICT: RateLimitConfig(
        requests_per_minute=5,  # 5 login attempts per minute
        requests_per_hour=20,  # 20 per hour
        requests_per_day=50,  # 50 per day
        burst_size=3,  # Small burst to prevent brute force
        enabled=True
    ),

    # HIGH: Sensitive API endpoints (user management, data export)
    RateLimitTier.HIGH: RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=5000,
        burst_size=10,
        enabled=True
    ),

    # MEDIUM: General API endpoints (assessments, responses)
    RateLimitTier.MEDIUM: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        burst_size=20,
        enabled=True
    ),

    # LOW: Public endpoints (health check, public pages)
    RateLimitTier.LOW: RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=2000,
        requests_per_day=20000,
        burst_size=50,
        enabled=True
    ),

    # CUSTOM: For endpoints with specific requirements
    RateLimitTier.CUSTOM: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        burst_size=10,
        enabled=True
    )
}


# Endpoint path to tier mapping
ENDPOINT_RATE_LIMITS: Dict[str, RateLimitTier] = {
    # Authentication endpoints - STRICT
    "/api/v1/auth/login": RateLimitTier.STRICT,
    "/api/v1/auth/register": RateLimitTier.STRICT,
    "/api/v1/auth/forgot-password": RateLimitTier.STRICT,
    "/api/v1/auth/reset-password": RateLimitTier.STRICT,
    "/api/v1/auth/verify-email": RateLimitTier.STRICT,

    # User management - HIGH
    "/api/v1/users/": RateLimitTier.HIGH,
    "/api/v1/users/me": RateLimitTier.HIGH,
    "/api/v1/users/change-password": RateLimitTier.HIGH,
    "/api/v1/users/delete-account": RateLimitTier.HIGH,

    # Admin endpoints - HIGH
    "/api/v1/admin/": RateLimitTier.HIGH,

    # Assessment endpoints - MEDIUM
    "/api/v1/assessments/": RateLimitTier.MEDIUM,
    "/api/v1/responses/": RateLimitTier.MEDIUM,

    # Clinical endpoints - HIGH (sensitive data)
    "/api/v1/clinical/": RateLimitTier.HIGH,

    # Analytics - MEDIUM
    "/api/v1/analytics/": RateLimitTier.MEDIUM,

    # Public endpoints - LOW
    "/api/v1/health": RateLimitTier.LOW,
    "/api/v1/docs": RateLimitTier.LOW,
    "/api/v1/openapi.json": RateLimitTier.LOW,
}


def get_rate_limit_for_path(path: str) -> RateLimitConfig:
    """
    Get rate limit configuration for a given path.

    Args:
        path: URL path to get rate limit for

    Returns:
        RateLimitConfig for the path
    """
    # Exact match first
    if path in ENDPOINT_RATE_LIMITS:
        tier = ENDPOINT_RATE_LIMITS[path]
        return RATE_LIMIT_TIERS[tier]

    # Prefix match for nested paths
    for endpoint_path, tier in sorted(
        ENDPOINT_RATE_LIMITS.items(),
        key=lambda x: len(x[0]),
        reverse=True  # Check longest paths first
    ):
        if path.startswith(endpoint_path):
            return RATE_LIMIT_TIERS[tier]

    # Default to MEDIUM tier
    return RATE_LIMIT_TIERS[RateLimitTier.MEDIUM]


def get_rate_limit_tier(path: str) -> RateLimitTier:
    """
    Get the rate limit tier for a given path.

    Args:
        path: URL path to get tier for

    Returns:
        RateLimitTier for the path
    """
    # Exact match first
    if path in ENDPOINT_RATE_LIMITS:
        return ENDPOINT_RATE_LIMITS[path]

    # Prefix match for nested paths
    for endpoint_path, tier in sorted(
        ENDPOINT_RATE_LIMITS.items(),
        key=lambda x: len(x[0]),
        reverse=True  # Check longest paths first
    ):
        if path.startswith(endpoint_path):
            return tier

    # Default to MEDIUM tier
    return RateLimitTier.MEDIUM


# IP-based rate limiting for abuse prevention
IP_BLOCKLIST = set()  # Dynamically blocked IPs
IP_TRUSTLIST = set()  # Trusted IPs (e.g., monitoring services)

# Rate limit by user tier (free, pro, enterprise)
USER_TIER_LIMITS = {
    "free": RATE_LIMIT_TIERS[RateLimitTier.MEDIUM],
    "pro": RATE_LIMIT_TIERS[RateLimitTier.HIGH],
    "enterprise": RATE_LIMIT_TIERS[RateLimitTier.LOW],  # Higher limits for enterprise
}


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int, limit_type: str = "requests"):
        self.retry_after = retry_after
        self.limit_type = limit_type
        super().__init__(
            f"Rate limit exceeded for {limit_type}. Retry after {retry_after} seconds."
        )


def configure_rate_limits(
    path: str,
    requests_per_minute: Optional[int] = None,
    requests_per_hour: Optional[int] = None,
    requests_per_day: Optional[int] = None,
    burst_size: Optional[int] = None,
) -> RateLimitConfig:
    """
    Configure custom rate limits for an endpoint.

    Args:
        path: Endpoint path
        requests_per_minute: Requests per minute
        requests_per_hour: Requests per hour
        requests_per_day: Requests per day
        burst_size: Burst size

    Returns:
        RateLimitConfig
    """
    # Get base config
    config = get_rate_limit_for_path(path)

    # Override with custom values
    if requests_per_minute is not None:
        config.requests_per_minute = requests_per_minute
    if requests_per_hour is not None:
        config.requests_per_hour = requests_per_hour
    if requests_per_day is not None:
        config.requests_per_day = requests_per_day
    if burst_size is not None:
        config.burst_size = burst_size

    return config
