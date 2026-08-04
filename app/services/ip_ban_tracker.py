"""
Cumulative IP Ban Tracking Service

Implements IP ban tracking across all endpoints to prevent:
- Brute force attacks across multiple endpoints
- Automated attack tools
- Persistent offenders

Security Features:
- Per-endpoint failure tracking
- Cumulative failure counting
- IP reputation scoring
- Automatic IP banning
- Configurable ban thresholds
- Ban duration with automatic expiry
- Whitelist support
- Ban reason logging
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

try:
    from redis.asyncio import redis as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class BanReason(str, Enum):
    """Reason for IP ban"""

    BRUTE_FORCE = "brute_force"  # Too many failed attempts across endpoints
    AUTOMATED_ATTACK = "automated_attack"  # Pattern of automated tool usage
    CREDENTIAL_STUFFING = "credential_stuffing"  # Repeated credential stuffing
    RATE_LIMIT_VIOLATION = "rate_limit_violation"  # Exceeded rate limits repeatedly
    MALICIOUS_PATTERN = "malicious_pattern"  # Suspicious request patterns
    SYSTEM_ADMIN = "system_admin"  # Administrative action


class IPReputation:
    """Track IP reputation score"""

    def __init__(self):
        self.scores = {}  # ip -> score (0-100, higher is better)
        self.recent_failures = {}  # ip -> [(endpoint, timestamp), ...]

    def get_score(self, ip: str) -> int:
        """Get reputation score for IP"""
        if ip not in self.scores:
            return 50  # Neutral score for new IPs
        score = self.scores.get(ip, 50)

        # Check for recent failures
        failures = self.recent_failures.get(ip, [])
        if len(failures) > 5:
            # Decrease score
            score -= 10 * len(failures)
        elif len(failures) > 10:
            score -= 5 * len(failures)

        return max(0, min(100, score))


class IPBanTracker:
    """
    Track IP bans and cumulative failures across endpoints
    """

    # Ban thresholds (configurable)
    BAN_THRESHOLD_FAILURES = 100  # Cumulative failures across ALL endpoints
    BAN_THRESHOLD_BRUTE_FORCE = 50  # Brute force attempts
    BAN_THRESHOLD_RATE_LIMIT = 100  # Rate limit violations
    BAN_DURATION_MINUTES = 60  # Default ban duration
    BAN_MAX_FAILURES_PER_HOUR = 10  # Max allowed per hour even after ban

    # Whitelist IPs (administrative)
    WHITELIST = {
        "127.0.0.1",
        "::1",
        "localhost",
    }

    def __init__(self, redis_client=None):
        """
        Initialize IP ban tracker

        Args:
            redis_client: Redis client for ban tracking
        """
        self.redis_client = redis_client
        self.bans: Dict[str, Dict] = {}  # ip -> {ban_info}
        self.failure_counts: Dict[str, Dict] = {}  # ip -> endpoint -> count
        self.reputation = IPReputation()

    async def _get_redis_client(self):
        """Get or create Redis client"""
        if self.redis_client is None:
            try:
                self.redis_client = await aioredis.from_url(
                    "redis://localhost:6379",
                    decode_responses=True,
                    health_check_interval=30,
                )
                logger.info("Connected to Redis for IP ban tracking")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Fail open on error
                self.redis_client = None

        return self.redis_client

    async def record_failure(
        self,
        ip: str,
        endpoint: str,
        reason: BanReason,
        user_id: Optional[str] = None,
    ):
        """Record a failure for an IP"""
        if not self.redis_client:
            return

        await self._get_redis_client()

        client_ip = ip

        # Get current hour key
        hour_key = (
            f"banned:failures:{client_ip}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        )

        # Increment failure count for this endpoint
        endpoint_key = f"failures:{endpoint}"
        endpoint_count_key = f"{hour_key}:{endpoint_key}"

        pipe = self.redis_client.pipeline()
        pipe.incr(hour_key)
        pipe.incr(endpoint_count_key)
        pipe.expire(hour_key, 7200)  # 1 hour expiry
        pipe.incr(f"cumulative_failures:{client_ip}")
        pipe.expire(f"cumulative_failures:{client_ip}", 86400)  # 24 hours

        # Track recent failures
        recent_failures_key = f"recent_failures:{client_ip}"
        pipe.lpush(
            recent_failures_key,
            {
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason.value,
            },
        )
        pipe.ltrim(recent_failures_key, 0, 100)  # Keep last 100

        # Execute atomically
        await pipe.execute()

        logger.debug(
            f"Failure recorded: {endpoint} from {ip} - Reason: {reason.value}",
            extra={
                "client_ip": client_ip,
                "endpoint": endpoint,
                "user_id": user_id or "anonymous",
                "cumulative_failures": await self.redis_client.get(
                    f"cumulative_failures:{client_ip}"
                ),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def check_ban_status(self, ip: str) -> bool:
        """Check if IP is currently banned"""
        if not self.redis_client:
            return False

        ban_info = await self.redis_client.get(f"banned:{ip}")
        if not ban_info:
            return False

        # Parse ban info
        import json

        try:
            data = json.loads(ban_info) if isinstance(ban_info, str) else ban_info
        except:
            return False

        return data.get("banned", False)

    async def should_ban_ip(self, ip: str) -> tuple[bool, str]:
        """
        Determine if IP should be banned based on cumulative failures

        Args:
            ip: IP address

        Returns:
            (is_banned, reason)
        """
        if not self.redis_client:
            return False, "Redis not available"

        await self._get_redis_client()

        # Get cumulative failure count
        cumulative_failures = await self.redis_client.get(f"cumulative_failures:{ip}")
        failure_count = int(cumulative_failures) if cumulative_failures else 0

        # Get endpoint-specific failures
        recent_failures = await self.redis_client.lrange(f"recent_failures:{ip}", 0, 20)

        # Determine ban reason
        ban_reason = None

        if failure_count >= self.BAN_THRESHOLD_FAILURES:
            # Too many failures across all endpoints
            ban_reason = BanReason.BRUTE_FORCE
        elif failure_count >= self.BAN_THRESHOLD_BRUTE_FORCE:
            # Too many auth failures
            ban_reason = BanReason.CREDENTIAL_STUFFING
        elif failure_count >= self.BAN_THRESHOLD_RATE_LIMIT:
            # Too many rate limit violations
            ban_reason = BanReason.RATE_LIMIT_VIOLATION
        else:
            # Check for recent failures
            recent_failure_types = []
            for failure in recent_failures:
                try:
                    data = json.loads(failure)
                    if isinstance(data, dict) and "reason" in data:
                        recent_failure_types.append(data.get("reason", ""))
                except:
                    pass

            # Check for repeated brute force pattern
            brute_force_failures = sum(
                1 for r in recent_failure_types if r == BanReason.BRUTE_FORCE.value
            )
            if brute_force_failures >= 3:
                ban_reason = BanReason.BRUTE_FORCE
            # Check for rate limit violations
            rate_limit_failures = sum(
                1
                for r in recent_failure_types
                if r == BanReason.RATE_LIMIT_VIOLATION.value
            )
            if rate_limit_failures >= 5:
                if rate_limit_failures >= 3:
                    ban_reason = BanReason.RATE_LIMIT_VIOLATION
            else:
                # Check for credential stuffing
                credential_failures = sum(
                    1
                    for r in recent_failure_types
                    if r == BanReason.CREDENTIAL_STUFFING.value
                )
                if credential_failures >= 5:
                    ban_reason = BanReason.CREDENTIAL_STUFFING

        # Check reputation score
        reputation_score = self.reputation.get_score(ip)
        if reputation_score < 30:
            # Low reputation, ban aggressively
            ban_reason = BanReason.AUTOMATED_ATTACK
        elif reputation_score < 50:
            # Medium-low reputation, consider ban
            ban_reason = BanReason.MALICIOUS_PATTERN

        # Check if in whitelist
        if ip in self.WHITELIST:
            return False, "IP in whitelist"

        if ban_reason:
            return True, ban_reason.value
        return False, ""

    async def ban_ip(
        self, ip: str, ban_reason: BanReason, duration_minutes: int = None
    ):
        """Ban an IP address"""
        await self._get_redis_client()

        # Set ban info
        expiry_time = datetime.utcnow() + timedelta(
            minutes=duration_minutes or self.BAN_DURATION_MINUTES
        )

        ban_info = {
            "ip": ip,
            "reason": ban_reason.value,
            "banned_at": datetime.utcnow().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "banned_by": "system",
        }

        ban_key = f"banned:{ip}"
        await self.redis_client.setex(
            ban_key,
            int((expiry_time - datetime.utcnow()).total_seconds()),
            json.dumps(ban_info),
        )

        # Clear failure history
        await self.redis_client.delete(f"recent_failures:{ip}")
        await self.redis_client.delete(f"cumulative_failures:{ip}")

        # Track ban
        self.bans[ip] = ban_info

        logger.warning(
            f"IP banned: {ip} - Reason: {ban_reason.value}",
            extra={
                "client_ip": ip,
                "ban_reason": ban_reason.value,
                "expires_at": expiry_time.isoformat(),
                "duration_minutes": duration_minutes,
            },
        )

        return ban_info

    async def unban_ip(self, ip: str):
        """Unban an IP address"""
        if not self.redis_client:
            return

        await self.redis_client.delete(f"banned:{ip}")
        if ip in self.bans:
            del self.bans[ip]

        logger.info(f"IP unbanned: {ip}")

    async def get_ip_status(self, ip: str) -> Dict[str, Any]:
        """Get comprehensive IP status"""
        status = {
            "is_banned": await self.check_ban_status(ip),
            "failure_count": (
                int(await self.redis_client.get(f"cumulative_failures:{ip}") or 0)
                if self.redis_client
                else 0
            ),
            "reputation_score": self.reputation.get_score(ip),
            "recent_failures": await self.redis_client.lrange(
                f"recent_failures:{ip}", 0, 10
            ),
            "whitelisted": ip in self.WHITELIST,
            "ban_info": self.bans.get(ip) if ip in self.bans else None,
            "endpoint_failures": {} if self.redis_client else {},
        }

        # Get endpoint-specific failure counts
        endpoints_to_track = [
            "/login",
            "/register",
            "/login/mfa/verify",
            "/password/reset",
            "/auth/token",
        ]
        for endpoint in endpoints_to_track:
            try:
                endpoint_failures = await self.redis_client.lrange(
                    f"failures:{endpoint}:{ip}", 0, 10
                )
                endpoint_failures_count = (
                    int(endpoint_failures[0])
                    if endpoint_failures
                    else endpoint_failures.count()
                )
                status["endpoint_failures"][endpoint] = endpoint_failures_count
            except Exception:
                status["endpoint_failures"][endpoint] = 0

        return status

    async def clean_old_data(self, days_to_keep: int = 7):
        """Clean old failure data (keeps recent N days)"""
        if not self.redis_client:
            return

        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_time.strftime("%Y-%m-%d")

        # Clean recent failures
        await self.redis_client.delete(f"recent_failures:*:{cutoff_str}")

        # Clean cumulative failures
        await self.redis_client.delete(f"cumulative_failures:*:{cutoff_str}")

        # Clean old bans
        old_bans_pattern = f"banned:*"
        keys = await self.redis_client.keys(old_bans_pattern)
        for key in keys:
            ban_info = await self.redis_client.get(key)
            if ban_info:
                expiry = datetime.fromisoformat(ban_info.get("expires_at"))
                if datetime.utcnow() > datetime.fromisoformat(expiry):
                    await self.redis_client.delete(key)

        logger.info(f"Cleaned {len(keys)} old ban records")

    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of currently blocked IPs"""
        if not self.redis_client:
            return []

        pattern = "banned:*"
        keys = await self.redis_client.keys(pattern)

        blocked_ips = []
        for key in keys:
            ban_info = await self.redis_client.get(key)
            if ban_info:
                blocked_ips.append(ban_info)

        return blocked_ips


# Global instance
ip_ban_tracker = IPBanTracker()


def check_ip_banned_dependency():
    """FastAPI dependency to check if IP is banned"""

    async def check_ip_banned(request: Request) -> bool:
        """Check if client IP is banned before processing request"""
        client_ip = request.client.host if request.client else "unknown"

        is_banned, reason = await ip_ban_tracker.should_ban_ip(client_ip)

        if is_banned:
            logger.warning(f"Request from banned IP: {client_ip} - Reason: {reason}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your IP address has been temporarily blocked due to {reason.value}. Please contact support if you believe this is an error.",
                headers={"X-RateLimit-Ban-Reason": reason.value},
            )

        return False
        return True
