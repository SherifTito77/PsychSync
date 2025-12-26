# app/core/api_rate_limiter.py
"""
Advanced API Rate Limiting System for PsychSync
Intelligent, multi-tiered rate limiting with different strategies for different endpoints
"""

import time
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.cache import cache_get, cache_set
from app.core.config import settings
from app.core.structured_logging import get_logger

logger = get_logger(__name__)

class RateLimitTier(Enum):
    """Rate limit tiers for different user types"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

class RateLimitType(Enum):
    """Types of rate limiting strategies"""
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"

@dataclass
class RateLimitRule:
    """Configuration for a rate limit rule"""
    requests_per_window: int
    window_seconds: int
    tier: RateLimitTier
    limit_type: RateLimitType
    burst_allowance: int = 0  # Extra requests allowed for bursts
    penalty_seconds: int = 0  # Cooldown period after limit exceeded

@dataclass
class RateLimitMetrics:
    """Metrics for rate limiting"""
    total_requests: int = 0
    blocked_requests: int = 0
    limit_exceeded_events: int = 0
    average_request_rate: float = 0.0
    peak_request_rate: float = 0.0
    window_start_time: Optional[datetime] = None

class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple strategies and user tier support
    """

    def __init__(self):
        self.rules = self._initialize_rules()
        self.sliding_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.token_buckets: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.metrics: Dict[str, RateLimitMetrics] = defaultdict(RateLimitMetrics)
        self._lock = asyncio.Lock()

    def _initialize_rules(self) -> Dict[RateLimitTier, List[RateLimitRule]]:
        """Initialize rate limit rules for different tiers"""
        return {
            RateLimitTier.FREE: [
                RateLimitRule(100, 60, RateLimitTier.FREE, RateLimitType.SLIDING_WINDOW, 10),
                RateLimitRule(1000, 3600, RateLimitTier.FREE, RateLimitType.FIXED_WINDOW, 50),
            ],
            RateLimitTier.BASIC: [
                RateLimitRule(500, 60, RateLimitTier.BASIC, RateLimitType.SLIDING_WINDOW, 50),
                RateLimitRule(5000, 3600, RateLimitTier.BASIC, RateLimitType.FIXED_WINDOW, 200),
            ],
            RateLimitTier.PREMIUM: [
                RateLimitRule(2000, 60, RateLimitTier.PREMIUM, RateLimitType.SLIDING_WINDOW, 200),
                RateLimitRule(20000, 3600, RateLimitTier.PREMIUM, RateLimitType.FIXED_WINDOW, 1000),
            ],
            RateLimitTier.ENTERPRISE: [
                RateLimitRule(10000, 60, RateLimitTier.ENTERPRISE, RateLimitType.SLIDING_WINDOW, 1000),
                RateLimitRule(100000, 3600, RateLimitTier.ENTERPRISE, RateLimitType.FIXED_WINDOW, 5000),
            ],
            RateLimitTier.ADMIN: [
                RateLimitRule(50000, 60, RateLimitTier.ADMIN, RateLimitType.TOKEN_BUCKET, 5000),
                RateLimitRule(500000, 3600, RateLimitTier.ADMIN, RateLimitType.TOKEN_BUCKET, 25000),
            ],
        }

    async def get_user_tier(self, user_id: int) -> RateLimitTier:
        """Get user's rate limit tier"""
        # TODO(human): Implement user tier detection from database or configuration
        # This should check the user's subscription level and return appropriate tier
        #
        # Context: Need to determine which rate limit tier applies to a specific user
        # Your task is to implement the logic to fetch user subscription information
        #
        # Guidance:
        # 1. Check user.subscription_level or similar field in database
        # 2. Map subscription level to RateLimitTier enum
        # 3. Cache the result to avoid repeated database queries
        # 4. Handle edge cases like trial users, suspended accounts
        # 5. Consider admin status override
        #
        # Return RateLimitTier.FREE for now as default

        cache_key = f"user_tier:{user_id}"
        cached_tier = await cache_get(cache_key)
        if cached_tier:
            return RateLimitTier(cached_tier)

        # Default tier - implement actual logic based on your user model
        tier = RateLimitTier.FREE

        # Cache for 5 minutes
        await cache_set(cache_key, tier.value, expire_seconds=300)
        return tier

    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[int] = None,
        endpoint_name: Optional[str] = None
    ) -> Tuple[bool, Optional[RateLimitRule]]:
        """
        Check if request is allowed based on rate limits
        Returns (is_allowed, rule_that_limited)
        """
        if not user_id:
            # IP-based limiting for unauthenticated requests
            return await self._check_ip_rate_limit(request)

        user_tier = await self.get_user_tier(user_id)
        rules = self.rules.get(user_tier, [])

        # Check each rule in order
        for rule in rules:
            if await self._check_rule(rule, user_id, endpoint_name):
                continue  # Rule passed
            else:
                return False, rule  # Rule failed

        return True, None  # All rules passed

    async def _check_ip_rate_limit(self, request: Request) -> Tuple[bool, Optional[RateLimitRule]]:
        """Check IP-based rate limiting for unauthenticated requests"""
        client_ip = get_remote_address(request)

        # Development-friendly limits for unauthenticated requests
        if settings.DEBUG:
            # More permissive for development: 100 requests per minute
            ip_rule = RateLimitRule(100, 60, RateLimitTier.FREE, RateLimitType.SLIDING_WINDOW, 20)
        else:
            # Strict limits for production
            ip_rule = RateLimitRule(10, 60, RateLimitTier.FREE, RateLimitType.SLIDING_WINDOW, 2)

        if await self._check_sliding_window(ip_rule, f"ip:{client_ip}"):
            return True, None
        else:
            return False, ip_rule

    async def _check_rule(
        self,
        rule: RateLimitRule,
        user_id: int,
        endpoint_name: Optional[str] = None
    ) -> bool:
        """Check a specific rate limit rule"""
        key = f"user:{user_id}:rule:{rule.window_seconds}:tier:{rule.tier.value}"

        if rule.limit_type == RateLimitType.SLIDING_WINDOW:
            return await self._check_sliding_window(rule, key)
        elif rule.limit_type == RateLimitType.FIXED_WINDOW:
            return await self._check_fixed_window(rule, key)
        elif rule.limit_type == RateLimitType.TOKEN_BUCKET:
            return await self._check_token_bucket(rule, key)
        elif rule.limit_type == RateLimitType.LEAKY_BUCKET:
            return await self._check_leaky_bucket(rule, key)
        elif rule.limit_type == RateLimitType.ADAPTIVE:
            return await self._check_adaptive_limit(rule, key, user_id, endpoint_name)
        else:
            return True  # Unknown type, allow by default

    async def _check_sliding_window(self, rule: RateLimitRule, key: str) -> bool:
        """Check sliding window rate limit"""
        now = time.time()
        window_start = now - rule.window_seconds

        window = self.sliding_windows[key]

        # Remove old entries
        while window and window[0] < window_start:
            window.popleft()

        # Count requests in window
        requests_in_window = len(window)

        # Allow if under limit (including burst allowance)
        if requests_in_window < rule.requests_per_window + rule.burst_allowance:
            window.append(now)
            return True
        else:
            # Check if we're past the penalty period
            if requests_in_window >= rule.requests_per_window and rule.penalty_seconds > 0:
                # Check if penalty period has passed
                last_request = window[-1] if window else 0
                if now - last_request > rule.penalty_seconds:
                    # Penalty passed, reset and allow
                    window.clear()
                    window.append(now)
                    return True

            return False

    async def _check_fixed_window(self, rule: RateLimitRule, key: str) -> bool:
        """Check fixed window rate limit"""
        now = time.time()
        window_start = int(now // rule.window_seconds) * rule.window_seconds
        window_key = f"{key}:window:{window_start}"

        request_count = await cache_get(window_key) or 0

        if request_count < rule.requests_per_window:
            await cache_set(window_key, request_count + 1, expire_seconds=rule.window_seconds)
            return True
        else:
            return False

    async def _check_token_bucket(self, rule: RateLimitRule, key: str) -> bool:
        """Check token bucket rate limit"""
        now = time.time()
        bucket = self.token_buckets[key]

        # Initialize bucket if needed
        if 'tokens' not in bucket:
            bucket['tokens'] = rule.requests_per_window
            bucket['last_refill'] = now

        # Refill tokens based on time elapsed
        time_elapsed = now - bucket['last_refill']
        tokens_to_add = time_elapsed * (rule.requests_per_window / rule.window_seconds)
        bucket['tokens'] = min(rule.requests_per_window, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now

        # Check if we have tokens
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        else:
            return False

    async def _check_leaky_bucket(self, rule: RateLimitRule, key: str) -> bool:
        """Check leaky bucket rate limit"""
        # Simplified leaky bucket implementation
        now = time.time()
        bucket = self.token_buckets[key]

        if 'last_leak' not in bucket:
            bucket['last_leak'] = now

        # Calculate leak rate
        leak_rate = rule.requests_per_window / rule.window_seconds
        time_elapsed = now - bucket['last_leak']
        leaked_tokens = int(time_elapsed * leak_rate)

        bucket['last_leak'] = now

        # If bucket is empty, allow request
        if leaked_tokens >= 1:
            bucket['tokens'] = max(0, bucket.get('tokens', 0) - leaked_tokens)
            return True

        return False

    async def _check_adaptive_limit(
        self,
        rule: RateLimitRule,
        key: str,
        user_id: int,
        endpoint_name: Optional[str]
    ) -> bool:
        """Check adaptive rate limit based on user behavior"""
        # Get user's recent request patterns
        user_metrics_key = f"user_metrics:{user_id}"
        metrics = self.metrics.get(user_metrics_key)

        if metrics and metrics.average_request_rate > 0:
            # Adjust limit based on user's average request rate
            adjustment_factor = min(2.0, 1.0 + (metrics.average_request_rate / 100))
            adjusted_limit = int(rule.requests_per_window * adjustment_factor)

            # Use sliding window with adjusted limit
            adjusted_rule = RateLimitRule(
                adjusted_limit,
                rule.window_seconds,
                rule.tier,
                RateLimitType.SLIDING_WINDOW,
                rule.burst_allowance,
                rule.penalty_seconds
            )

            return await self._check_sliding_window(adjusted_rule, f"adaptive:{key}")
        else:
            return await self._check_sliding_window(rule, key)

    async def record_request(self, user_id: Optional[int], endpoint_name: str, success: bool = True):
        """Record request for metrics and adaptive limiting"""
        if not user_id:
            return

        user_metrics_key = f"user_metrics:{user_id}"
        metrics = self.metrics[user_metrics_key]

        if not metrics.window_start_time:
            metrics.window_start_time = datetime.utcnow()

        metrics.total_requests += 1

        if not success:
            metrics.blocked_requests += 1

        # Calculate request rate
        time_elapsed = (datetime.utcnow() - metrics.window_start_time).total_seconds()
        if time_elapsed > 0:
            metrics.average_request_rate = metrics.total_requests / time_elapsed

        # Reset metrics window if needed
        if time_elapsed > 3600:  # Reset every hour
            self.metrics[user_metrics_key] = RateLimitMetrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        return {
            "active_sliding_windows": len(self.sliding_windows),
            "active_token_buckets": len(self.token_buckets),
            "tracked_users": len(self.metrics),
            "configured_rules": {
                tier.value: [{"limit": rule.requests_per_window, "window": rule.window_seconds}
                 for rule in rules]
                for tier, rules in self.rules.items()
            }
        }

# Global rate limiter instance
advanced_rate_limiter = AdvancedRateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for advanced rate limiting
    """

    def __init__(self, app, rate_limiter: AdvancedRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and documentation
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/metrics"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Get user ID from request (implementation depends on your auth system)
        user_id = await self._extract_user_id(request)
        endpoint_name = self._get_endpoint_name(request)

        # Check rate limit
        is_allowed, limiting_rule = await self.rate_limiter.check_rate_limit(
            request, user_id, endpoint_name
        )

        # Record request
        await self.rate_limiter.record_request(user_id, endpoint_name, is_allowed)

        if not is_allowed:
            return self._create_rate_limit_response(limiting_rule)

        # Process the request
        response = await call_next(request)

        # Add comprehensive rate limit headers
        await self._add_rate_limit_headers(response, user_id, limiting_rule, request)

        return response

    async def _add_rate_limit_headers(
        self,
        response,
        user_id: Optional[int],
        limiting_rule: Optional[RateLimitRule],
        request: Request
    ) -> None:
        """Add comprehensive rate limit information headers to response"""
        import time

        try:
            if not user_id:
                # IP-based limiting for unauthenticated requests
                client_ip = get_remote_address(request)
                window_key = f"ip:{client_ip}"

                # Get IP rate limit info (development-friendly)
                if settings.DEBUG:
                    ip_rule = RateLimitRule(100, 60, RateLimitTier.FREE, RateLimitType.SLIDING_WINDOW, 20)
                    policy_description = "IP-based: 100 requests per 60 seconds (development)"
                else:
                    ip_rule = RateLimitRule(10, 60, RateLimitTier.FREE, RateLimitType.SLIDING_WINDOW, 2)
                    policy_description = "IP-based: 10 requests per 60 seconds (production)"

                current_requests = len(self.rate_limiter.sliding_windows.get(window_key, []))

                response.headers["X-RateLimit-Limit"] = str(ip_rule.requests_per_window)
                response.headers["X-RateLimit-Window"] = str(ip_rule.window_seconds)
                response.headers["X-RateLimit-Remaining"] = str(max(0, ip_rule.requests_per_window - current_requests))
                response.headers["X-RateLimit-Reset"] = str(int(time.time() + ip_rule.window_seconds))
                response.headers["X-RateLimit-Policy"] = policy_description
                return

            # User-based limiting
            user_tier = await self.rate_limiter.get_user_tier(user_id)
            rules = self.rate_limiter.rules.get(user_tier, [])

            if rules:
                # Use the primary rule for header information
                primary_rule = rules[0]
                window_key = f"user:{user_id}:rule:{primary_rule.window_seconds}:tier:{user_tier.value}"
                current_requests = len(self.rate_limiter.sliding_windows.get(window_key, []))
                remaining = max(0, primary_rule.requests_per_window - current_requests)
                reset_time = int(time.time() + primary_rule.window_seconds)

                # Add comprehensive rate limit headers
                response.headers["X-RateLimit-Limit"] = str(primary_rule.requests_per_window)
                response.headers["X-RateLimit-Window"] = str(primary_rule.window_seconds)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(reset_time)
                response.headers["X-RateLimit-Tier"] = user_tier.value
                response.headers["X-RateLimit-Policy"] = f"{primary_rule.requests_per_window} per {primary_rule.window_seconds}s"

                # Add burst information if applicable
                if primary_rule.burst_allowance > 0:
                    response.headers["X-RateLimit-Burst"] = str(primary_rule.burst_allowance)
                    burst_remaining = max(0, primary_rule.burst_allowance + primary_rule.requests_per_window - current_requests)
                    response.headers["X-RateLimit-Burst-Remaining"] = str(burst_remaining)

                # Add secondary limit info if available
                if len(rules) > 1:
                    secondary_rule = rules[1]
                    response.headers["X-RateLimit-Hourly-Limit"] = str(secondary_rule.requests_per_window)
                    response.headers["X-RateLimit-Hourly-Window"] = str(secondary_rule.window_seconds)

            # If rate was limited, add retry information
            if limiting_rule:
                response.headers["X-RateLimit-Retry-After"] = str(limiting_rule.penalty_seconds or limiting_rule.window_seconds)
                response.headers["Retry-After"] = str(limiting_rule.penalty_seconds or limiting_rule.window_seconds)

        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")
            # Don't fail the request if header addition fails

    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from request based on JWT token"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header[7:]  # Remove "Bearer "

            # Decode token to get user ID
            from app.core.config import settings
            from jose import jwt, JWTError

            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                user_id = payload.get("sub")
                return int(user_id) if user_id and user_id.isdigit() else None
            except (JWTError, ValueError):
                return None

        except Exception as e:
            logger.error(f"Error extracting user ID from request: {e}")
            return None

    def _get_endpoint_name(self, request: Request) -> str:
        """Get endpoint name from request"""
        return f"{request.method}:{request.url.path}"

    def _create_rate_limit_response(self, limiting_rule: RateLimitRule):
        """Create rate limit exceeded response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "status": "rate_limited",
                "message": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "data": {
                    "retry_after": limiting_rule.penalty_seconds,
                    "window_seconds": limiting_rule.window_seconds,
                    "max_requests": limiting_rule.requests_per_window
                }
            },
            headers={"Retry-After": str(limiting_rule.penalty_seconds)}
        )