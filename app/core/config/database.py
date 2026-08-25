# app/core/config/database.py

"""
ENTERPRISE-GRADE DATABASE CONFIGURATION
Comprehensive database connection and security settings

SECURITY FEATURES:
- Connection pool optimization
- SSL/TLS enforcement
- Performance monitoring
- Security validation
- Multi-environment support

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging

from pydantic import Field, validator

# Initialize database configuration logger
db_config_logger = logging.getLogger("app.config.database")


class DatabaseConfig:
    """
    Enterprise-grade database configuration with comprehensive security
    """

    # Database connection settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/psychsync",
        env="DATABASE_URL",
    )
    # Pool defaults safe for Supabase free tier (60 pooled connections).
    # With 2 workers: 2 * (10 + 5) = 30 connections max, well under limit.
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=5, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")

    # Database security settings
    DB_SSL_MODE: str = Field(default="prefer", env="DB_SSL_MODE")
    DB_SSL_CERT: str | None = Field(default=None, env="DB_SSL_CERT")
    DB_SSL_KEY: str | None = Field(default=None, env="DB_SSL_KEY")
    DB_SSL_CA: str | None = Field(default=None, env="DB_SSL_CA")

    # Database performance settings
    DB_ECHO: bool = Field(default=False, env="DB_ECHO")
    DB_POOL_PRE_PING: bool = Field(default=True, env="DB_POOL_PRE_PING")
    DB_STATEMENT_TIMEOUT: int = Field(
        default=300000,  # 5 minutes in milliseconds
        env="DB_STATEMENT_TIMEOUT",
    )

    # Database backup and recovery
    DB_BACKUP_ENABLED: bool = Field(default=True, env="DB_BACKUP_ENABLED")
    DB_BACKUP_SCHEDULE: str = Field(
        default="0 2 * * *",  # Daily at 2 AM
        env="DB_BACKUP_SCHEDULE",
    )
    DB_BACKUP_RETENTION_DAYS: int = Field(default=30, env="DB_BACKUP_RETENTION_DAYS")

    @validator("DATABASE_URL")
    def validate_database_url(cls, v, values):
        """Validate database URL format and security"""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")

        environment = values.get("ENVIRONMENT", "development")
        testing = values.get("TESTING", False)

        # Allow SQLite in testing environment
        if testing or environment == "testing" or environment == "test":
            if "sqlite" in v or "memory" in v or "aiosqlite" in v:
                db_config_logger.info(f"Using SQLite database for testing: {v[:50]}...")
                return v

        # Allow SQLite for development flexibility
        if environment == "development" and (
            "sqlite" in v or "memory" in v or "aiosqlite" in v
        ):
            db_config_logger.info(f"Using SQLite database for development: {v[:50]}...")
            return v

        # Check for secure connection in production
        if "postgresql://" in v and "ssl=" not in v:
            db_config_logger.warning(
                "Database URL should include SSL settings for production"
            )

        # Validate URL format for non-testing environments
        allowed_drivers = [
            "postgresql+asyncpg://",
            "postgresql://",
            "sqlite://",
            "sqlite+aiosqlite://",
        ]
        if not any(driver in v for driver in allowed_drivers):
            raise ValueError("DATABASE_URL must use PostgreSQL or SQLite driver")

        return v

    @validator("DATABASE_POOL_SIZE", "DATABASE_MAX_OVERFLOW")
    def validate_pool_sizes(cls, v):
        """Validate database pool sizes"""
        if v <= 0:
            raise ValueError("Pool sizes must be positive integers")
        if v > 1000:
            db_config_logger.warning(f"Large pool size {v} may cause resource issues")
        return v

    @validator("DB_STATEMENT_TIMEOUT")
    def validate_statement_timeout(cls, v):
        """Validate statement timeout"""
        if v <= 0:
            raise ValueError("Statement timeout must be positive")
        if v > 3600000:  # 1 hour
            db_config_logger.warning(
                "Very long statement timeout may allow runaway queries"
            )
        return v

    def get_connection_args(self) -> dict:
        """
        Get database connection arguments with security settings

        Returns:
            Dictionary of connection arguments
        """
        connection_args = {
            "command_timeout": self.DB_STATEMENT_TIMEOUT / 1000,  # Convert to seconds
            # Note: Removed server_settings to avoid temp_file_limit permission errors
            # Only include minimal connection args that don't require superuser privileges
        }

        # Add SSL configuration
        if self.DB_SSL_MODE != "disable":
            connection_args["ssl"] = {
                "sslmode": self.DB_SSL_MODE,
                "sslcert": self.DB_SSL_CERT,
                "sslkey": self.DB_SSL_KEY,
                "sslrootcert": self.DB_SSL_CA,
            }

        return connection_args

    def get_pool_config(self) -> dict:
        """
        Get database pool configuration

        Returns:
            Dictionary of pool configuration
        """
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "pool_recycle": self.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
            "pool_reset_on_return": "commit",  # Security: always reset connection state
        }

    def validate_database_security(self) -> None:
        """
        Validate database security settings

        Raises:
            RuntimeError: If security settings are invalid
        """
        # Check for production security requirements
        if "production" in getattr(self, "ENVIRONMENT", "development"):
            if self.DB_SSL_MODE == "disable":
                raise RuntimeError(
                    "SSL must be enabled for production database connections"
                )

            if not self.DB_SSL_CA:
                db_config_logger.warning(
                    "Production database should use SSL certificate authority"
                )

        # Validate pool sizes
        total_connections = self.DATABASE_POOL_SIZE + self.DATABASE_MAX_OVERFLOW
        if total_connections > 1000:
            db_config_logger.warning(
                f"High database connection pool size: {total_connections}. "
                "Monitor for resource exhaustion."
            )

    def get_database_url_for_env(
        self, async_driver: bool = True, test_mode: bool = False
    ) -> str:
        """
        Get database URL for specific environment and mode

        Args:
            async_driver: Whether to use async driver
            test_mode: Whether to use test database

        Returns:
            Database URL string
        """
        url = self.DATABASE_URL

        # Switch to async driver if needed
        if async_driver and "postgresql://" in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        # Switch to sync driver if needed (convert from asyncpg back to postgresql)
        elif not async_driver and "postgresql+asyncpg://" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://")

        # Switch to test database if needed
        if test_mode:
            # Replace database name with test database
            if "/psychsync" in url:
                url = url.replace("/psychsync", "/psychsync_test")
            else:
                # Append test database name
                url += "/psychsync_test"

        # Add SSL parameters if not present (but not for asyncpg drivers)
        # asyncpg handles SSL configuration through connect_args, not URL parameters
        if (
            self.DB_SSL_MODE != "disable"
            and "?ssl=" not in url
            and "asyncpg" not in url
        ):
            separator = "&" if "?" in url else "?"
            url += f"{separator}sslmode={self.DB_SSL_MODE}"

        return url

    def __init__(self, **data):
        """Initialize database configuration with validation"""
        super().__init__(**data)
        self.validate_database_security()

        db_config_logger.info(
            "Database configuration initialized",
            extra={
                "pool_size": self.DATABASE_POOL_SIZE,
                "max_overflow": self.DATABASE_MAX_OVERFLOW,
                "ssl_mode": self.DB_SSL_MODE,
                "echo": self.DB_ECHO,
            },
        )
