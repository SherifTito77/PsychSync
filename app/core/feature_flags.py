"""
Advanced Feature Flag System

This module provides enterprise-grade feature flag management with:
- Dynamic feature toggling without deployment
- A/B testing and experimentation support
- Gradual rollout capabilities
- Environment-specific configuration
- Real-time flag updates
- Audit logging for flag changes
- Performance optimization with caching
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
from typing import Any

import aioredis

logger = logging.getLogger(__name__)


class FlagType(Enum):
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    JSON = "json"
    STRING = "string"
    NUMBER = "number"


class RolloutStrategy(Enum):
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    A_B_TEST = "ab_test"
    CANARY = "canary"
    TIME_BASED = "time_based"


@dataclass
class FeatureFlag:
    """Feature flag definition"""

    key: str
    flag_type: FlagType
    description: str
    enabled: bool = False
    value: Any = None
    rollout_strategy: RolloutStrategy = RolloutStrategy.IMMEDIATE
    rollout_percentage: float = 0.0
    conditions: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int = 1


@dataclass
class UserContext:
    """User context for flag evaluation"""

    user_id: str
    organization_id: str
    email: str
    role: str
    attributes: dict[str, Any] | None = None


@dataclass
class FlagEvaluationResult:
    """Result of feature flag evaluation"""

    flag_key: str
    enabled: bool
    value: Any
    reason: str
    rollout_percentage: float
    cache_hit: bool
    evaluation_time_ms: float
    user_id: str


class FeatureFlagCache:
    """Redis-based feature flag cache"""

    def __init__(self, redis_url: str, ttl: int = 300):
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis = None

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)

    async def get_flag(self, key: str) -> dict[str, Any] | None:
        """Get flag from cache"""
        try:
            cached = await self.redis.get(f"flag:{key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
        return None

    async def set_flag(self, key: str, flag_data: dict[str, Any]):
        """Set flag in cache"""
        try:
            await self.redis.setex(
                f"flag:{key}", self.ttl, json.dumps(flag_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")

    async def get_evaluation_result(
        self, key: str, user_id: str
    ) -> dict[str, Any] | None:
        """Get cached evaluation result"""
        try:
            cache_key = (
                f"eval:{key}:{hashlib.sha256(user_id.encode()).hexdigest()[:16]}"
            )
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Evaluation cache get error: {e}")
        return None

    async def set_evaluation_result(
        self, key: str, user_id: str, result: dict[str, Any]
    ):
        """Cache evaluation result"""
        try:
            cache_key = (
                f"eval:{key}:{hashlib.sha256(user_id.encode()).hexdigest()[:16]}"
            )
            await self.redis.setex(
                cache_key, 60, json.dumps(result, default=str)
            )  # 1 minute TTL
        except Exception as e:
            logger.warning(f"Evaluation cache set error: {e}")

    async def invalidate_flag(self, key: str):
        """Invalidate cached flag"""
        try:
            await self.redis.delete(f"flag:{key}")
        except Exception as e:
            logger.warning(f"Cache invalidation error for {key}: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()


class FeatureFlagManager:
    """Enterprise feature flag manager"""

    def __init__(self, redis_url: str):
        self.cache = FeatureFlagCache(redis_url)
        self.flags: dict[str, FeatureFlag] = {}
        self.default_flags: dict[str, FeatureFlag] = {}
        self.initialized = False

    async def initialize(self, default_flags: dict[str, FeatureFlag] = None):
        """Initialize feature flag manager"""
        await self.cache.initialize()

        if default_flags:
            self.default_flags = default_flags
            self.flags.update(default_flags)

        # Load initial flags from Redis/database
        await self.load_flags()

        self.initialized = True
        logger.info("🚀 Feature flag manager initialized")

    async def load_flags(self):
        """Load all feature flags"""
        # In production, this would load from a database
        # For now, use defaults and cache
        for key, flag in self.default_flags.items():
            cached_flag = await self.cache.get_flag(key)
            if cached_flag:
                # Update with cached data
                flag_dict = cached_flag
                flag.enabled = flag_dict.get("enabled", flag.enabled)
                flag.value = flag_dict.get("value", flag.value)
                flag.rollout_percentage = flag_dict.get(
                    "rollout_percentage", flag.rollout_percentage
                )
                flag.updated_at = datetime.fromisoformat(
                    flag_dict.get("updated_at", datetime.now().isoformat())
                )

    async def evaluate_flag(
        self, flag_key: str, user_context: UserContext, use_cache: bool = True
    ) -> FlagEvaluationResult:
        """Evaluate feature flag for user"""
        start_time = time.time()
        cache_hit = False

        if not self.initialized:
            raise RuntimeError("Feature flag manager not initialized")

        # Check cache first
        if use_cache:
            cached_result = await self.cache.get_evaluation_result(
                flag_key, user_context.user_id
            )
            if cached_result:
                return FlagEvaluationResult(**cached_result)

        # Get flag definition
        flag = self.flags.get(flag_key)
        if not flag:
            # Return default disabled result
            result = FlagEvaluationResult(
                flag_key=flag_key,
                enabled=False,
                value=None,
                reason="flag_not_found",
                rollout_percentage=0.0,
                cache_hit=cache_hit,
                evaluation_time_ms=(time.time() - start_time) * 1000,
                user_id=user_context.user_id,
            )

            # Cache result
            if use_cache:
                await self.cache.set_evaluation_result(
                    flag_key, user_context.user_id, asdict(result)
                )

            return result

        # Evaluate based on flag type and strategy
        enabled, value, reason = await self._evaluate_flag_logic(flag, user_context)

        evaluation_time = (time.time() - start_time) * 1000
        result = FlagEvaluationResult(
            flag_key=flag_key,
            enabled=enabled,
            value=value,
            reason=reason,
            rollout_percentage=flag.rollout_percentage,
            cache_hit=cache_hit,
            evaluation_time_ms=evaluation_time,
            user_id=user_context.user_id,
        )

        # Cache result
        if use_cache:
            await self.cache.set_evaluation_result(
                flag_key, user_context.user_id, asdict(result)
            )

        # Log evaluation for analytics
        await self._log_evaluation(result, user_context)

        return result

    async def _evaluate_flag_logic(
        self, flag: FeatureFlag, user_context: UserContext
    ) -> tuple:
        """Core flag evaluation logic"""

        # Check if flag is globally enabled
        if not flag.enabled:
            return False, flag.value, "disabled"

        # Evaluate conditions
        if flag.conditions:
            if not self._evaluate_conditions(flag.conditions, user_context):
                return False, flag.value, "conditions_not_met"

        # Evaluate based on rollout strategy
        if flag.rollout_strategy == RolloutStrategy.IMMEDIATE:
            return True, flag.value, "immediate"

        if flag.rollout_strategy == RolloutStrategy.PERCENTAGE:
            return self._evaluate_percentage_rollout(flag, user_context)

        if flag.rollout_strategy == RolloutStrategy.GRADUAL:
            return self._evaluate_gradual_rollout(flag, user_context)

        if flag.rollout_strategy == RolloutStrategy.A_B_TEST:
            return self._evaluate_ab_test(flag, user_context)

        if flag.rollout_strategy == RolloutStrategy.CANARY:
            return self._evaluate_canary(flag, user_context)

        if flag.rollout_strategy == RolloutStrategy.TIME_BASED:
            return self._evaluate_time_based(flag, user_context)

        return True, flag.value, "default"

    def _evaluate_conditions(
        self, conditions: dict[str, Any], user_context: UserContext
    ) -> bool:
        """Evaluate flag conditions"""

        # User-based conditions
        if "users" in conditions:
            if user_context.user_id not in conditions["users"]:
                return False

        # Organization-based conditions
        if "organizations" in conditions:
            if user_context.organization_id not in conditions["organizations"]:
                return False

        # Role-based conditions
        if "roles" in conditions:
            if user_context.role not in conditions["roles"]:
                return False

        # Attribute-based conditions
        if "attributes" in conditions:
            for attr_key, expected_value in conditions["attributes"].items():
                user_attr_value = (
                    user_context.attributes.get(attr_key)
                    if user_context.attributes
                    else None
                )
                if user_attr_value != expected_value:
                    return False

        return True

    def _evaluate_percentage_rollout(
        self, flag: FeatureFlag, user_context: UserContext
    ) -> tuple:
        """Evaluate percentage-based rollout"""
        hash_input = f"{flag.key}:{user_context.user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        user_percentage = (hash_value % 10000) / 100.0  # 0.00 to 100.00

        if user_percentage < flag.rollout_percentage:
            return True, flag.value, f"percentage_rollout_{flag.rollout_percentage}%"
        return False, flag.value, f"percentage_rollout_{flag.rollout_percentage}%"

    def _evaluate_gradual_rollout(
        self, flag: FeatureFlag, user_context: UserContext
    ) -> tuple:
        """Evaluate gradual rollout based on time"""
        if not flag.created_at:
            return False, flag.value, "no_created_date"

        hours_since_creation = (
            datetime.now(UTC) - flag.created_at
        ).total_seconds() / 3600

        # Gradual rollout over 24 hours
        max_hours = 24.0
        if hours_since_creation >= max_hours:
            return True, flag.value, "gradual_rollout_complete"

        gradual_percentage = min(100.0, (hours_since_creation / max_hours) * 100.0)

        hash_input = f"{flag.key}:{user_context.user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        user_percentage = (hash_value % 10000) / 100.0

        if user_percentage < gradual_percentage:
            return True, flag.value, f"gradual_rollout_{gradual_percentage:.1f}%"
        return False, flag.value, f"gradual_rollout_{gradual_percentage:.1f}%"

    def _evaluate_ab_test(self, flag: FeatureFlag, user_context: UserContext) -> tuple:
        """Evaluate A/B test"""
        # Assign user to variant based on hash
        hash_input = f"{flag.key}:{user_context.user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        variant = hash_value % 100

        if variant < flag.rollout_percentage:
            return True, flag.value, "ab_test_variant_a"
        return False, flag.value, "ab_test_variant_b"

    def _evaluate_canary(self, flag: FeatureFlag, user_context: UserContext) -> tuple:
        """Evaluate canary rollout (early adopters)"""
        # Check if user is an early adopter based on creation date or specific attributes
        if user_context.attributes and user_context.attributes.get("early_adopter"):
            return True, flag.value, "canary_early_adopter"

        # Hash-based canary selection
        hash_input = f"{flag.key}:canary:{user_context.user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        user_percentage = (hash_value % 10000) / 100.0

        if user_percentage < flag.rollout_percentage:
            return True, flag.value, "canary_rollout"
        return False, flag.value, "not_in_canary"

    def _evaluate_time_based(
        self, flag: FeatureFlag, user_context: UserContext
    ) -> tuple:
        """Evaluate time-based rollout"""
        if not flag.conditions or "time_window" not in flag.conditions:
            return False, flag.value, "no_time_window"

        time_window = flag.conditions["time_window"]
        now = datetime.now(UTC)

        # Check if current time is within the allowed window
        start_time = datetime.fromisoformat(time_window["start"]).replace(tzinfo=UTC)
        end_time = datetime.fromisoformat(time_window["end"]).replace(tzinfo=UTC)

        if start_time <= now <= end_time:
            return True, flag.value, "time_window_active"
        return False, flag.value, "time_window_inactive"

    async def _log_evaluation(
        self, result: FlagEvaluationResult, user_context: UserContext
    ):
        """Log flag evaluation for analytics"""
        try:
            log_data = {
                "flag_key": result.flag_key,
                "user_id": user_context.user_id,
                "organization_id": user_context.organization_id,
                "enabled": result.enabled,
                "reason": result.reason,
                "evaluation_time_ms": result.evaluation_time_ms,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # In production, send to analytics system
            logger.info(f"Flag evaluation: {json.dumps(log_data)}")

        except Exception as e:
            logger.warning(f"Failed to log flag evaluation: {e}")

    async def update_flag(self, flag_key: str, updates: dict[str, Any]) -> bool:
        """Update feature flag"""
        flag = self.flags.get(flag_key)
        if not flag:
            return False

        # Update flag properties
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)

        flag.updated_at = datetime.now(UTC)
        flag.version += 1

        # Update cache
        await self.cache.set_flag(flag_key, asdict(flag))

        # Invalidate evaluation cache for this flag
        await self.cache.invalidate_flag(flag_key)

        logger.info(f"Updated feature flag {flag_key}: {updates}")
        return True

    async def create_flag(self, flag_key: str, flag: FeatureFlag) -> bool:
        """Create new feature flag"""
        if flag_key in self.flags:
            return False

        flag.created_at = datetime.now(UTC)
        flag.updated_at = datetime.now(UTC)

        self.flags[flag_key] = flag

        # Update cache
        await self.cache.set_flag(flag_key, asdict(flag))

        logger.info(f"Created feature flag {flag_key}")
        return True

    async def delete_flag(self, flag_key: str) -> bool:
        """Delete feature flag"""
        if flag_key not in self.flags:
            return False

        del self.flags[flag_key]

        # Clear cache
        await self.cache.invalidate_flag(flag_key)

        logger.info(f"Deleted feature flag {flag_key}")
        return True

    def get_flag(self, flag_key: str) -> FeatureFlag | None:
        """Get feature flag definition"""
        return self.flags.get(flag_key)

    def get_all_flags(self) -> dict[str, FeatureFlag]:
        """Get all feature flags"""
        return self.flags.copy()

    async def close(self):
        """Close feature flag manager"""
        await self.cache.close()


# Global feature flag manager
feature_flag_manager: FeatureFlagManager | None = None


def is_enabled(flag_key: str, user_context: UserContext = None, default: bool = False):
    """Decorator to check if feature is enabled"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if feature_flag_manager and user_context:
                result = await feature_flag_manager.evaluate_flag(
                    flag_key, user_context
                )
                if result.enabled:
                    return await func(*args, **kwargs)

            # Return default behavior if feature is disabled
            if default:
                return await func(*args, **kwargs)

            # Raise exception or return None
            raise ValueError(f"Feature {flag_key} is not enabled")

        return wrapper

    return decorator


def get_flag_value(flag_key: str, default_value: Any = None):
    """Decorator to get feature flag value"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if feature_flag_manager:
                flag = feature_flag_manager.get_flag(flag_key)
                if flag and flag.enabled:
                    return flag.value

            return default_value

        return wrapper

    return decorator


# Default feature flags
DEFAULT_FEATURE_FLAGS = {
    "advanced_analytics": FeatureFlag(
        key="advanced_analytics",
        flag_type=FlagType.BOOLEAN,
        description="Enable advanced analytics dashboard",
        enabled=True,
        rollout_strategy=RolloutStrategy.IMMEDIATE,
    ),
    "beta_features": FeatureFlag(
        key="beta_features",
        flag_type=FlagType.BOOLEAN,
        description="Enable beta features for early adopters",
        enabled=True,
        rollout_strategy=RolloutStrategy.PERCENTAGE,
        rollout_percentage=20.0,
        conditions={"attributes": {"early_adopter": True}},
    ),
    "new_ui_theme": FeatureFlag(
        key="new_ui_theme",
        flag_type=FlagType.PERCENTAGE,
        description="New UI theme rollout",
        enabled=True,
        rollout_strategy=RolloutStrategy.GRADUAL,
        rollout_percentage=50.0,
        created_at=datetime.now(UTC),
    ),
    "ai_insights": FeatureFlag(
        key="ai_insights",
        flag_type=FlagType.BOOLEAN,
        description="AI-powered insights and recommendations",
        enabled=True,
        rollout_strategy=RolloutStrategy.CANARY,
        rollout_percentage=10.0,
    ),
    "enhanced_search": FeatureFlag(
        key="enhanced_search",
        flag_type=FlagType.BOOLEAN,
        description="Enhanced search with natural language processing",
        enabled=True,
        rollout_strategy=RolloutStrategy.A_B_TEST,
        rollout_percentage=50.0,
    ),
}


async def initialize_feature_flags(redis_url: str) -> FeatureFlagManager:
    """Initialize feature flag system"""
    global feature_flag_manager

    feature_flag_manager = FeatureFlagManager(redis_url)
    await feature_flag_manager.initialize(DEFAULT_FEATURE_FLAGS)

    return feature_flag_manager


async def get_feature_flag_manager() -> FeatureFlagManager:
    """Get global feature flag manager"""
    if not feature_flag_manager:
        raise RuntimeError("Feature flag manager not initialized")
    return feature_flag_manager
