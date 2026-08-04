"""
Centralized Retry Configuration System

Provides dynamic, environment-configurable retry settings for all system components.

Features:
- Environment-based configuration
- Component-specific override capabilities
- Runtime parameter adjustment
- Integration with monitoring/metrics

Author: Infrastructure Team
Version: 1.0
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    # Basic retry settings
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds

    # Jitter settings
    jitter_enabled: bool = True
    jitter_percentage: float = 0.25  # ±25%

    # Retryable error patterns
    retryable_errors: tuple = ()

    # Circuit breaker integration
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: float = 60.0  # seconds before half-open

    # Metrics integration
    enable_metrics: bool = True
    metrics_integration: str = "prometheus"  # prometheus, statsd, or none


class RetryConfigManager:
    """
    Manages retry configuration across the system with environment variable support.

    Environment Variables:
        RETRY_MAX_RETRIES: Default maximum retry attempts (default: 3)
        RETRY_BASE_DELAY: Base delay in seconds (default: 1.0)
        RETRY_MAX_DELAY: Maximum delay in seconds (default: 30.0)
        RETRY_JITTER_ENABLED: Enable jitter (default: true)
        RETRY_JITTER_PERCENTAGE: Jitter percentage (default: 0.25)
        RETRY_CIRCUIT_BREAKER_ENABLED: Enable circuit breaker (default: true)
        RETRY_METRICS_ENABLED: Enable metrics collection (default: true)
        RETRY_METRICS_TYPE: Metrics backend (default: prometheus)

    Component-Specific Environment Variables:
        {COMPONENT}_RETRY_MAX_RETRIES: Override max retries for component
        {COMPONENT}_RETRY_BASE_DELAY: Override base delay for component

    Examples:
        # Database retry config
        DATABASE_RETRY_MAX_RETRIES=5
        DATABASE_RETRY_BASE_DELAY=0.5

        # Webhook retry config
        WEBHOOK_RETRY_MAX_RETRIES=3
        WEBHOOK_RETRY_BASE_DELAY=2.0
    """

    # Predefined component configurations
    COMPONENT_CONFIGS = {
        "database": RetryConfig(
            max_retries=3,
            base_delay=0.5,
            max_delay=5.0,
            retryable_errors=(
                "could not serialize access",
                "deadlock",
                "connection reset",
                "server closed the connection",
                "timeout",
                "could not acquire lock",
            ),
        ),
        "webhook": RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_errors=("5xx", "timeout", "connection"),
        ),
        "email_smtp": RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_errors=(
                "timeout",
                "connection",
                "network",
                "421",
                "450",
                "451",
                "452",
                "454",
            ),
        ),
        "email_imap": RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_errors=("timeout", "connection", "network", "temporary"),
        ),
        "hris_api": RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_errors=("timeout", "connection", "network", "5xx", "429"),
        ),
        "hris_db": RetryConfig(
            max_retries=3,
            base_delay=0.5,
            max_delay=5.0,
            retryable_errors=("deadlock", "lock", "timeout", "connection"),
        ),
        "default": RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
        ),
    }

    @classmethod
    def get_config(cls, component: str = "default") -> RetryConfig:
        """
        Get retry configuration for a component with environment variable overrides.

        Args:
            component: Component name (database, webhook, email_smtp, etc.)

        Returns:
            RetryConfig with environment overrides applied
        """
        # Get base configuration
        base_config = cls.COMPONENT_CONFIGS.get(
            component, cls.COMPONENT_CONFIGS["default"]
        )

        # Apply environment variable overrides
        config = RetryConfig(
            max_retries=cls._get_env_int(
                f"{component.upper()}_RETRY_MAX_RETRIES",
                base_config.max_retries,
            ),
            base_delay=cls._get_env_float(
                f"{component.upper()}_RETRY_BASE_DELAY",
                base_config.base_delay,
            ),
            max_delay=cls._get_env_float(
                f"{component.upper()}_RETRY_MAX_DELAY",
                base_config.max_delay,
            ),
            jitter_enabled=cls._get_env_bool(
                f"{component.upper()}_RETRY_JITTER_ENABLED",
                base_config.jitter_enabled,
            ),
            jitter_percentage=cls._get_env_float(
                f"{component.upper()}_RETRY_JITTER_PERCENTAGE",
                base_config.jitter_percentage,
            ),
            retryable_errors=base_config.retryable_errors,
            enable_circuit_breaker=cls._get_env_bool(
                f"{component.upper()}_RETRY_CIRCUIT_BREAKER_ENABLED",
                base_config.enable_circuit_breaker,
            ),
            circuit_breaker_threshold=cls._get_env_int(
                f"{component.upper()}_RETRY_CIRCUIT_BREAKER_THRESHOLD",
                base_config.circuit_breaker_threshold,
            ),
            circuit_breaker_timeout=cls._get_env_float(
                f"{component.upper()}_RETRY_CIRCUIT_BREAKER_TIMEOUT",
                base_config.circuit_breaker_timeout,
            ),
            enable_metrics=cls._get_env_bool(
                f"{component.upper()}_RETRY_METRICS_ENABLED",
                base_config.enable_metrics,
            ),
            metrics_integration=cls._get_env_str(
                f"{component.upper()}_RETRY_METRICS_TYPE",
                base_config.metrics_integration,
            ),
        )

        return config

    @staticmethod
    def _get_env_int(key: str, default: int) -> int:
        """Get integer environment variable with fallback"""
        value = os.getenv(key)
        if value is None:
            # Check global default
            global_key = key.split("_", 1)[1] if "_" in key else key
            global_value = os.getenv(f"RETRY_{global_key}")
            if global_value is not None:
                try:
                    return int(global_value)
                except ValueError:
                    pass
            return default
        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    def _get_env_float(key: str, default: float) -> float:
        """Get float environment variable with fallback"""
        value = os.getenv(key)
        if value is None:
            # Check global default
            global_key = key.split("_", 1)[1] if "_" in key else key
            global_value = os.getenv(f"RETRY_{global_key}")
            if global_value is not None:
                try:
                    return float(global_value)
                except ValueError:
                    pass
            return default
        try:
            return float(value)
        except ValueError:
            return default

    @staticmethod
    def _get_env_bool(key: str, default: bool) -> bool:
        """Get boolean environment variable with fallback"""
        value = os.getenv(key)
        if value is None:
            # Check global default
            global_key = key.split("_", 1)[1] if "_" in key else key
            global_value = os.getenv(f"RETRY_{global_key}")
            if global_value is not None:
                return global_value.lower() in ("true", "1", "yes", "on")
            return default
        return value.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def _get_env_str(key: str, default: str) -> str:
        """Get string environment variable with fallback"""
        value = os.getenv(key)
        if value is None:
            # Check global default
            global_key = key.split("_", 1)[1] if "_" in key else key
            global_value = os.getenv(f"RETRY_{global_key}")
            if global_value is not None:
                return global_value
            return default
        return value

    @classmethod
    def get_all_configs(cls) -> dict:
        """Get all component configurations"""
        return {
            component: cls.get_config(component)
            for component in cls.COMPONENT_CONFIGS.keys()
        }


# Global convenience functions
def get_retry_config(component: str = "default") -> RetryConfig:
    """Get retry configuration for a component"""
    return RetryConfigManager.get_config(component)
