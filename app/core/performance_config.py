"""
Centralized Performance Configuration Management

This module provides unified configuration management for all performance-related
settings with validation, environment-specific overrides, and runtime updates.

Features:
- Environment-specific configuration (dev/staging/prod)
- Runtime configuration updates
- Validation with detailed error messages
- Configuration versioning and migration
- Performance tuning recommendations
- Configuration change tracking
"""

import hashlib
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseSettings, Field, root_validator, validator

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported environment types"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class PerformanceTier(str, Enum):
    """Performance optimization tiers"""

    BASIC = "basic"  # Essential optimizations only
    STANDARD = "standard"  # Recommended for most use cases
    AGGRESSIVE = "aggressive"  # Maximum performance
    CONSERVATIVE = "conservative"  # Minimal resource usage


class DatabaseConfig(BaseSettings):
    """Database performance configuration"""

    # Connection pool settings
    pool_size: int = Field(
        default=20, ge=1, le=100, description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Maximum number of connections beyond pool_size",
    )
    pool_recycle: int = Field(
        default=1800,
        ge=300,
        le=7200,
        description="Connection recycling time in seconds",
    )
    pool_pre_ping: bool = Field(
        default=True, description="Validate connections before use"
    )
    pool_timeout: int = Field(
        default=30, ge=5, le=300, description="Timeout for getting connection from pool"
    )

    # Query optimization
    statement_timeout: int = Field(
        default=300, ge=30, le=3600, description="Default statement timeout in seconds"
    )
    query_cache_size: int = Field(
        default=1000, ge=0, le=10000, description="Query result cache size"
    )

    @validator("max_overflow")
    def validate_pool_vs_overflow(cls, v, values):
        if "pool_size" in values and v > values["pool_size"] * 5:
            raise ValueError("max_overflow should not exceed 5x pool_size")
        return v

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class CacheConfig(BaseSettings):
    """Caching performance configuration"""

    # Redis settings
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(
        default=6379, ge=1, le=65535, description="Redis server port"
    )
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    redis_max_connections: int = Field(
        default=50, ge=1, le=200, description="Maximum Redis connections"
    )

    # Cache settings
    default_ttl: int = Field(
        default=300, ge=60, le=3600, description="Default cache TTL in seconds"
    )
    max_memory_policy: str = Field(
        default="allkeys-lru", description="Redis max memory policy"
    )
    cache_prefix: str = Field(default="psychsync", description="Cache key prefix")

    class Config:
        env_prefix = "CACHE_"
        case_sensitive = False


class FrontendConfig(BaseSettings):
    """Frontend performance configuration"""

    # Bundle optimization
    bundle_size_target_kb: int = Field(
        default=500, ge=100, le=2000, description="Target bundle size in KB"
    )
    chunk_size_target_kb: int = Field(
        default=100, ge=50, le=500, description="Target chunk size in KB"
    )
    enable_source_maps: bool = Field(
        default=False, description="Enable source maps in production"
    )
    minification_level: str = Field(
        default="terser",
        regex="^(none|basic|terser)$",
        description="Minification level",
    )

    # Performance features
    enable_lazy_loading: bool = Field(
        default=True, description="Enable lazy loading of components"
    )
    enable_virtual_scrolling: bool = Field(
        default=True, description="Enable virtual scrolling for large lists"
    )
    enable_service_worker: bool = Field(
        default=False, description="Enable service worker for caching"
    )

    class Config:
        env_prefix = "FRONTEND_"
        case_sensitive = False


class APIConfig(BaseSettings):
    """API performance configuration"""

    # Response optimization
    enable_compression: bool = Field(
        default=True, description="Enable response compression"
    )
    compression_threshold: int = Field(
        default=1024,
        ge=100,
        le=10240,
        description="Minimum response size for compression",
    )
    enable_http_caching: bool = Field(
        default=True, description="Enable HTTP caching headers"
    )
    default_cache_max_age: int = Field(
        default=300, ge=60, le=86400, description="Default cache max-age in seconds"
    )

    # Rate limiting
    enable_rate_limiting: bool = Field(
        default=True, description="Enable API rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100, ge=10, le=10000, description="Rate limit requests per window"
    )
    rate_limit_window: int = Field(
        default=60, ge=30, le=3600, description="Rate limit window in seconds"
    )

    class Config:
        env_prefix = "API_"
        case_sensitive = False


class MonitoringConfig(BaseSettings):
    """Performance monitoring configuration"""

    # Metrics collection
    enable_metrics: bool = Field(
        default=True, description="Enable performance metrics collection"
    )
    metrics_sample_rate: float = Field(
        default=1.0, ge=0.1, le=1.0, description="Metrics sampling rate"
    )
    enable_real_time_monitoring: bool = Field(
        default=True, description="Enable real-time performance monitoring"
    )

    # Alerting
    enable_alerts: bool = Field(default=True, description="Enable performance alerts")
    alert_threshold_cpu: float = Field(
        default=80.0,
        ge=50.0,
        le=100.0,
        description="CPU usage alert threshold percentage",
    )
    alert_threshold_memory: float = Field(
        default=85.0,
        ge=50.0,
        le=100.0,
        description="Memory usage alert threshold percentage",
    )
    alert_threshold_response_time: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Response time alert threshold in milliseconds",
    )

    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False


class PerformanceThresholds(BaseSettings):
    """Performance thresholds for monitoring"""

    # Database thresholds (milliseconds)
    database_query_threshold: int = Field(
        default=100, ge=10, le=1000, description="Database query threshold in ms"
    )
    database_connection_threshold: int = Field(
        default=50, ge=10, le=500, description="Database connection threshold in ms"
    )

    # API thresholds (milliseconds)
    api_response_threshold: int = Field(
        default=200, ge=50, le=2000, description="API response threshold in ms"
    )
    authentication_threshold: int = Field(
        default=50, ge=10, le=500, description="Authentication threshold in ms"
    )

    # Frontend thresholds
    frontend_load_threshold: int = Field(
        default=2000, ge=500, le=10000, description="Frontend load threshold in ms"
    )
    bundle_size_threshold_kb: int = Field(
        default=500, ge=100, le=2000, description="Bundle size threshold in KB"
    )

    class Config:
        env_prefix = "THRESHOLD_"
        case_sensitive = False


class PerformanceConfig(BaseSettings):
    """Unified performance configuration"""

    # Environment settings
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Runtime environment"
    )
    performance_tier: PerformanceTier = Field(
        default=PerformanceTier.STANDARD, description="Performance optimization tier"
    )
    debug_performance: bool = Field(
        default=False, description="Enable performance debugging"
    )

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    thresholds: PerformanceThresholds = Field(default_factory=PerformanceThresholds)

    # Version tracking
    config_version: str = Field(default="1.0.0", description="Configuration version")
    last_updated: datetime | None = Field(
        default=None, description="Last configuration update timestamp"
    )

    @validator("environment", pre=True)
    def parse_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @validator("performance_tier", pre=True)
    def parse_tier(cls, v):
        if isinstance(v, str):
            return PerformanceTier(v.lower())
        return v

    @root_validator
    def apply_environment_defaults(cls, values):
        """Apply environment-specific defaults"""
        environment = values.get("environment", Environment.DEVELOPMENT)
        tier = values.get("performance_tier", PerformanceTier.STANDARD)

        if environment == Environment.PRODUCTION:
            # Production optimizations
            if tier == PerformanceTier.AGGRESSIVE:
                values.setdefault(
                    "database", DatabaseConfig(pool_size=50, max_overflow=75)
                )
                values.setdefault("cache", CacheConfig(default_ttl=600))
                values.setdefault(
                    "frontend",
                    FrontendConfig(
                        enable_source_maps=False, minification_level="terser"
                    ),
                )
            elif tier == PerformanceTier.CONSERVATIVE:
                values.setdefault(
                    "database", DatabaseConfig(pool_size=10, max_overflow=15)
                )
                values.setdefault("cache", CacheConfig(default_ttl=1800))

        elif environment == Environment.DEVELOPMENT:
            # Development defaults
            values.setdefault("database", DatabaseConfig(pool_size=5, max_overflow=10))
            values.setdefault(
                "frontend",
                FrontendConfig(enable_source_maps=True, debug_performance=True),
            )
            values.setdefault("debug_performance", True)

        return values

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "performance_tier": self.performance_tier.value,
            "debug_performance": self.debug_performance,
            "config_version": self.config_version,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "database": self.database.dict(),
            "cache": self.cache.dict(),
            "frontend": self.frontend.dict(),
            "api": self.api.dict(),
            "monitoring": self.monitoring.dict(),
            "thresholds": self.thresholds.dict(),
        }

    def get_config_hash(self) -> str:
        """Get configuration hash for change detection"""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def update_environment(self, environment: str | Environment):
        """Update environment and apply new defaults"""
        if isinstance(environment, str):
            environment = Environment(environment.lower())

        self.environment = environment
        self.last_updated = datetime.now()

        # Reapply environment defaults
        # This would trigger the root_validator
        new_config = PerformanceConfig(
            environment=environment,
            performance_tier=self.performance_tier,
            debug_performance=self.debug_performance,
        )

        # Update sub-configurations with new environment defaults
        self.database = new_config.database
        self.cache = new_config.cache
        self.frontend = new_config.frontend
        self.api = new_config.api
        self.monitoring = new_config.monitoring

        logger.info(f"Updated environment to {environment.value}")

    def validate_performance_tier(self) -> list[str]:
        """Validate configuration against performance tier"""
        issues = []
        tier = self.performance_tier

        if tier == PerformanceTier.BASIC:
            if self.database.pool_size > 20:
                issues.append("BASIC tier recommends smaller connection pools")
            if self.frontend.bundle_size_target_kb < 800:
                issues.append("BASIC tier allows larger bundle sizes")

        elif tier == PerformanceTier.AGGRESSIVE:
            if self.database.pool_size < 30:
                issues.append("AGGRESSIVE tier recommends larger connection pools")
            if not self.frontend.enable_service_worker:
                issues.append("AGGRESSIVE tier should enable service worker")

        elif tier == PerformanceTier.CONSERVATIVE:
            if self.database.pool_size > 15:
                issues.append("CONSERVATIVE tier recommends smaller connection pools")

        return issues

    def get_optimization_recommendations(self) -> list[str]:
        """Get optimization recommendations based on current settings"""
        recommendations = []

        # Database recommendations
        if self.database.pool_size < 20 and self.environment == Environment.PRODUCTION:
            recommendations.append(
                "Consider increasing database pool size for production"
            )

        if self.database.statement_timeout > 300:
            recommendations.append("Long statement timeout may indicate slow queries")

        # Cache recommendations
        if self.cache.default_ttl < 300:
            recommendations.append(
                "Consider increasing default cache TTL for better performance"
            )

        # Frontend recommendations
        if self.frontend.bundle_size_target_kb > 800:
            recommendations.append("Consider code splitting to reduce bundle size")

        if not self.frontend.enable_lazy_loading:
            recommendations.append("Enable lazy loading to improve initial load time")

        # API recommendations
        if not self.api.enable_compression:
            recommendations.append("Enable compression to reduce response sizes")

        if not self.api.enable_http_caching:
            recommendations.append("Enable HTTP caching for better client performance")

        return recommendations

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "forbid"  # Reject extra fields


class ConfigurationManager:
    """Configuration manager with runtime updates and persistence"""

    def __init__(self, config_file: str | None = None):
        self.config_file = config_file or "performance_config.json"
        self._config: PerformanceConfig | None = None
        self._config_hash: str | None = None
        self._change_callbacks: list[callable] = []

    @property
    def config(self) -> PerformanceConfig:
        """Get current configuration (lazy loaded)"""
        if self._config is None:
            self._config = self._load_config()
            self._config_hash = self._config.get_config_hash()
        return self._config

    def _load_config(self) -> PerformanceConfig:
        """Load configuration from file or environment"""
        config_path = Path(self.config_file)

        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)

                logger.info(f"Loading performance config from {config_path}")
                return PerformanceConfig(**config_data)

            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")

        # Load from environment variables
        logger.info("Loading performance config from environment")
        return PerformanceConfig()

    def save_config(self):
        """Save current configuration to file"""
        if not self._config:
            return

        config_path = Path(self.config_file)
        config_data = self._config.to_dict()

        try:
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Saved performance config to {config_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")

    def reload_config(self):
        """Reload configuration from file"""
        old_config = self._config
        self._config = None  # Force reload
        new_config = self.config  # This will trigger reload

        # Check if configuration changed
        if old_config and old_config.get_config_hash() != new_config.get_config_hash():
            self._notify_config_change(old_config, new_config)
            logger.info("Configuration reloaded with changes")

    def update_config(self, updates: dict[str, Any]):
        """Update configuration with new values"""
        if not self._config:
            self._config = self.config  # Load if not loaded

        old_config = self._config.to_dict()

        # Update configuration
        for key, value in updates.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")

        self._config.last_updated = datetime.now()

        # Validate new configuration
        try:
            # Revalidate using Pydantic
            self._config = PerformanceConfig(**self._config.to_dict())

            # Check for changes and notify
            new_config_hash = self._config.get_config_hash()
            if self._config_hash != new_config_hash:
                self._notify_config_change(self._config, self._config)
                self._config_hash = new_config_hash

            # Save changes
            self.save_config()

        except Exception as e:
            logger.error(f"Invalid configuration update: {e}")
            # Restore old configuration
            self._config = PerformanceConfig(**old_config)
            raise

    def add_change_callback(self, callback: callable):
        """Add callback for configuration changes"""
        self._change_callbacks.append(callback)

    def _notify_config_change(
        self, old_config: PerformanceConfig, new_config: PerformanceConfig
    ):
        """Notify callbacks of configuration changes"""
        for callback in self._change_callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error(f"Configuration change callback failed: {e}")

    def get_environment_specific_config(
        self, environment: Environment
    ) -> PerformanceConfig:
        """Get configuration for specific environment"""
        config_data = self.config.to_dict()
        config_data["environment"] = environment.value

        return PerformanceConfig(**config_data)


# Global configuration instance
config_manager = ConfigurationManager()


# Convenience functions
def get_performance_config() -> PerformanceConfig:
    """Get current performance configuration"""
    return config_manager.config


def update_performance_config(updates: dict[str, Any]):
    """Update performance configuration"""
    config_manager.update_config(updates)


def reload_performance_config():
    """Reload performance configuration"""
    config_manager.reload_config()


# Environment-specific configuration getters
def get_database_config() -> DatabaseConfig:
    """Get database performance configuration"""
    return get_performance_config().database


def get_cache_config() -> CacheConfig:
    """Get cache performance configuration"""
    return get_performance_config().cache


def get_frontend_config() -> FrontendConfig:
    """Get frontend performance configuration"""
    return get_performance_config().frontend


def get_api_config() -> APIConfig:
    """Get API performance configuration"""
    return get_performance_config().api


def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring performance configuration"""
    return get_performance_config().monitoring


def get_performance_thresholds() -> PerformanceThresholds:
    """Get performance thresholds configuration"""
    return get_performance_config().thresholds
