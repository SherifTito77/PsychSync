"""
Redis Connection Manager for Security Middleware

This module is SOLELY responsible for managing Redis connections
for security features (rate limiting, IP blocking, etc.).

Single Responsibility Principle: Only manage Redis connections.
"""

import logging
from typing import Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    """Custom exception for Redis connection failures"""

    pass


class RedisConnectionManager:
    """
    Manages Redis connection with graceful degradation.

    Features:
    - Automatic connection with retry
    - Graceful degradation in development
    - Strict validation in production
    - Connection health monitoring
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        require_in_production: bool = True,
    ):
        """
        Initialize Redis connection manager.

        Args:
            host: Redis host (defaults to settings.REDIS_HOST)
            port: Redis port (defaults to settings.REDIS_PORT)
            db: Redis DB number (defaults to settings.REDIS_DB)
            require_in_production: Whether Redis is required in production

        Raises:
            RedisConnectionError: If connection fails in production
        """
        self.host = host or settings.REDIS_HOST
        self.port = port or settings.REDIS_PORT
        self.db = db or settings.REDIS_DB
        self.require_in_production = require_in_production
        self.client: Optional[redis.Redis] = None
        self._is_available = False

        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """
        Initialize Redis connection with proper error handling.

        In production: Fails fast if Redis is unavailable
        In development: Logs warning and continues without Redis
        """
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # Test connection
            self.client.ping()
            self._is_available = True
            logger.info(
                f"Redis connection established: {self.host}:{self.port}/{self.db}",
                extra={"component": "RedisConnectionManager"},
            )

        except redis.ConnectionError as e:
            logger.critical(
                f"Redis connection failed: {e!s}",
                extra={
                    "error_type": "ConnectionError",
                    "host": self.host,
                    "port": self.port,
                    "db": self.db,
                    "environment": settings.ENVIRONMENT,
                },
                exc_info=True,
            )

            # Fail fast in production if required
            if settings.ENVIRONMENT == "production" and self.require_in_production:
                raise RedisConnectionError(
                    f"Redis initialization failed in production. "
                    f"Rate limiting and security monitoring disabled. Error: {e}"
                ) from e

            # Development-only: Continue with warning
            logger.warning(
                "⚠️  Running without Redis - rate limiting and security monitoring disabled. "
                "This is NOT safe for production!"
            )
            self._is_available = False
            self.client = None

        except Exception as e:
            logger.critical(
                f"Unexpected error initializing Redis: {e!s}",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "host": self.host,
                    "port": self.port,
                    "db": self.db,
                    "environment": settings.ENVIRONMENT,
                },
                exc_info=True,
            )

            if settings.ENVIRONMENT == "production" and self.require_in_production:
                raise RedisConnectionError(
                    f"Unexpected Redis initialization error in production: {e}"
                ) from e

            logger.warning("Continuing without Redis due to unexpected error")
            self._is_available = False
            self.client = None

    @property
    def is_available(self) -> bool:
        """Check if Redis client is available"""
        return self._is_available and self.client is not None

    def get_client(self) -> Optional[redis.Redis]:
        """
        Get Redis client instance.

        Returns:
            Redis client if available, None otherwise

        Note:
            Callers should always check is_available() first or
            handle None gracefully
        """
        return self.client

    def health_check(self) -> bool:
        """
        Perform health check on Redis connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.is_available:
            return False

        try:
            self.client.ping()
            return True
        except Exception:
            self._is_available = False
            return False

    def close(self) -> None:
        """Close Redis connection gracefully"""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.client = None
                self._is_available = False
