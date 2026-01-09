# app/core/cors.py

"""
ENTERPRISE-GRADE CORS CONFIGURATION
Centralized CORS management for PsychSync application

SECURITY FEATURES:
- Environment-aware CORS configuration
- Origin validation and security checks
- Production safety mechanisms
- Development convenience features

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Initialize CORS logger
cors_logger = logging.getLogger("app.security.cors")


class EnterpriseCORSManager:
    """
    Enterprise-grade CORS management with comprehensive security controls
    """

    def __init__(self):
        self._origins: list[str] | None = None
        self._initialized = False

    def _validate_origins(self, origins: list[str]) -> list[str]:
        """
        Validate and filter CORS origins based on security policies

        Args:
            origins: List of origin URLs to validate

        Returns:
            List of validated origins

        Raises:
            RuntimeError: If invalid origins are detected in production
        """
        validated_origins = []

        for origin in origins:
            origin = origin.strip()

            # Basic format validation
            if not origin.startswith(("http://", "https://")):
                if settings.ENVIRONMENT == "production":
                    cors_logger.critical(f"CRITICAL: Invalid CORS origin format: {origin}")
                    raise RuntimeError(f"CORS origin must start with http:// or https://: {origin}")
                cors_logger.warning(f"Invalid CORS origin format in development: {origin}")
                continue

            # Production security checks
            if settings.ENVIRONMENT == "production":
                # Prevent wildcard origins in production
                if origin == "*" or "*." in origin:
                    cors_logger.critical("CRITICAL: Wildcard CORS origins detected in production")
                    raise RuntimeError(
                        "CRITICAL SECURITY ERROR: Wildcard CORS origins not allowed in production. "
                        "Please specify exact origins for security."
                    )

                # Prevent localhost in production
                if "localhost" in origin.lower() or "127.0.0.1" in origin:
                    cors_logger.critical(f"CRITICAL: Localhost CORS origin in production: {origin}")
                    raise RuntimeError(
                        "CRITICAL SECURITY ERROR: Localhost origins not allowed in production CORS configuration."
                    )

            validated_origins.append(origin)
            cors_logger.debug(f"CORS origin validated: {origin}")

        if not validated_origins and settings.ENVIRONMENT == "production":
            cors_logger.critical("No valid CORS origins configured for production")
            raise RuntimeError("Production requires valid CORS origins")

        cors_logger.info(f"CORS origins validated - {len(validated_origins)} origins configured")
        return validated_origins

    def _get_origins(self) -> list[str]:
        """
        Get CORS origins from configuration with validation

        Returns:
            List of validated CORS origins
        """
        if self._origins is not None:
            return self._origins

        # Get origins from settings
        origins = settings.CORS_ORIGINS

        # Validate origins
        self._origins = self._validate_origins(origins)
        self._initialized = True

        return self._origins

    def get_cors_middleware_config(self) -> dict:
        """
        Get complete CORS middleware configuration

        Returns:
            Dictionary with all CORS middleware parameters
        """
        origins = self._get_origins()

        # Base configuration
        config = {
            "allow_origins": origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": [
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-CSRF-Token",
                "X-Device-Fingerprint",
                "X-Session-ID",
                "API-Key",
                "User-Agent",
                "Cache-Control",
                "Pragma",
            ],
            "expose_headers": [
                "X-Total-Count",
                "X-Page-Count",
                "X-Rate-Limit-Remaining",
                "X-Rate-Limit-Reset",
                "X-Request-ID",
                "X-Response-Time",
            ],
        }

        # Environment-specific adjustments
        if settings.ENVIRONMENT == "development":
            # More permissive for development
            config["allow_origins"] = ["*"] if not origins else origins
            config["max_age"] = 3600  # 1 hour for development
        else:
            # Stricter for production
            config["max_age"] = 86400  # 24 hours for production

        return config

    def configure_cors(self, app: FastAPI) -> None:
        """
        Configure CORS middleware for FastAPI application

        Args:
            app: FastAPI application instance
        """
        try:
            config = self.get_cors_middleware_config()

            # Add CORS middleware
            app.add_middleware(CORSMiddleware, **config)

            cors_logger.info(
                "CORS middleware configured successfully",
                extra={
                    "allowed_origins_count": len(config["allow_origins"]),
                    "allow_credentials": config["allow_credentials"],
                    "max_age": config["max_age"],
                    "environment": settings.ENVIRONMENT,
                },
            )

        except Exception as e:
            cors_logger.error(f"Failed to configure CORS: {e}")
            raise

    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if a specific origin is allowed by CORS policy

        Args:
            origin: Origin URL to check

        Returns:
            True if origin is allowed, False otherwise
        """
        if not self._initialized:
            self._get_origins()

        if "*" in self._origins:
            return True

        return origin in self._origins

    def get_allowed_origins(self) -> list[str]:
        """
        Get list of allowed origins (for debugging/logging)

        Returns:
            List of allowed origins
        """
        if not self._initialized:
            self._get_origins()

        return self._origins.copy()


# Global CORS manager instance
cors_manager = EnterpriseCORSManager()


def configure_cors(app: FastAPI) -> None:
    """
    Convenience function to configure CORS for FastAPI app

    Args:
        app: FastAPI application instance
    """
    cors_manager.configure_cors(app)


def is_origin_allowed(origin: str) -> bool:
    """
    Convenience function to check if origin is allowed

    Args:
        origin: Origin URL to check

    Returns:
        True if origin is allowed, False otherwise
    """
    return cors_manager.is_origin_allowed(origin)


def get_allowed_origins() -> list[str]:
    """
    Convenience function to get allowed origins

    Returns:
        List of allowed origins
    """
    return cors_manager.get_allowed_origins()
