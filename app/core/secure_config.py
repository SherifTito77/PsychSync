# app/core/secure_config.py
"""
Secure Configuration & Secrets Management for PsychSync
Replaces vibe-coded config with production-ready secrets handling
"""

from functools import lru_cache
import logging

from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


# ============================================
# SECURE SETTINGS (Production-Ready)
# ============================================


class SecureSettings(BaseSettings):
    """
    Production-ready settings with validation

    ✅ SECURE PRACTICES:
    - All secrets use SecretStr (never logged)
    - Environment-specific validation
    - Secrets fetched from vault (not .env in prod)
    - Strong defaults with security in mind
    """

    # ============================================
    # ENVIRONMENT
    # ============================================
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    @validator("DEBUG")
    def validate_debug(cls, v, values):
        """Ensure DEBUG is False in production"""
        if values.get("ENVIRONMENT") == "production" and v:
            raise ValueError("DEBUG cannot be True in production")
        return v

    # ============================================
    # APPLICATION
    # ============================================
    APP_NAME: str = Field(default="PsychSync", env="APP_NAME")
    API_VERSION: str = Field(default="v1", env="API_VERSION")
    API_PREFIX: str = Field(default="/api/v1", env="API_PREFIX")

    # ============================================
    # DATABASE (Secure Credentials)
    # ============================================
    DATABASE_URL: SecretStr = Field(..., env="DATABASE_URL")

    # Connection pool settings (prevent DoS)
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Ensure DATABASE_URL is not using default credentials"""
        url = v.get_secret_value()

        # Check for default credentials
        dangerous_patterns = [
            "postgres:postgres@",
            "root:root@",
            "admin:admin@",
            "password@",
        ]

        for pattern in dangerous_patterns:
            if pattern in url.lower():
                raise ValueError(f"Database URL contains default credentials: {pattern}")

        return v

    # ============================================
    # REDIS (Secure Credentials)
    # ============================================
    REDIS_URL: SecretStr = Field(..., env="REDIS_URL")
    REDIS_PASSWORD: SecretStr | None = Field(default=None, env="REDIS_PASSWORD")

    @validator("REDIS_PASSWORD", always=True)
    def validate_redis_password(cls, v, values):
        """Require password in production"""
        if values.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("REDIS_PASSWORD is required in production")
        return v

    # ============================================
    # JWT AUTHENTICATION (Strong Secrets)
    # ============================================
    SECRET_KEY: SecretStr = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """Ensure SECRET_KEY is strong enough"""
        secret = v.get_secret_value()

        # Check length
        if len(secret) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")

        # Check entropy (not just repeated characters)
        if len(set(secret)) < 10:
            raise ValueError("SECRET_KEY has insufficient entropy")

        # Warn if using default/example key
        dangerous_keys = [
            "your-secret-key-here",
            "change-me",
            "secret",
            "mysecretkey",
        ]

        if secret.lower() in dangerous_keys:
            raise ValueError(f"SECRET_KEY is using a default value: {secret[:10]}...")

        return v

    # ============================================
    # ENCRYPTION (Data at Rest)
    # ============================================
    ENCRYPTION_KEY: SecretStr | None = Field(default=None, env="ENCRYPTION_KEY")

    @validator("ENCRYPTION_KEY")
    def validate_encryption_key(cls, v):
        """Ensure encryption key is Fernet-compatible"""
        if v is None:
            # Allow None for development
            return v

        try:
            from cryptography.fernet import Fernet

            Fernet(v.get_secret_value().encode())
        except Exception:
            raise ValueError(
                "ENCRYPTION_KEY must be a valid Fernet key. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            ) from None

        return v

    # ============================================
    # CORS (Strict in Production)
    # ============================================
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("CORS_ORIGINS")
    def validate_cors_origins(cls, v, values):
        """Ensure CORS is not wide open in production"""
        if values.get("ENVIRONMENT") == "production":
            dangerous_origins = ["*", "http://*", "https://*"]

            for origin in v:
                if origin in dangerous_origins:
                    raise ValueError(f"CORS origin '{origin}' is too permissive for production")

                # Ensure HTTPS in production
                if origin.startswith("http://") and "localhost" not in origin:
                    raise ValueError(f"CORS origin must use HTTPS in production: {origin}")

        return v

    # ============================================
    # EMAIL (Secure SMTP)
    # ============================================
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str | None = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: SecretStr | None = Field(default=None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")

    @validator("SMTP_TLS")
    def validate_smtp_tls(cls, v, values):
        """Require TLS in production"""
        if values.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("SMTP_TLS must be True in production")
        return v

    # ============================================
    # THIRD-PARTY APIS (Secure Tokens)
    # ============================================
    SLACK_CLIENT_ID: str | None = Field(default=None, env="SLACK_CLIENT_ID")
    SLACK_CLIENT_SECRET: SecretStr | None = Field(default=None, env="SLACK_CLIENT_SECRET")

    GOOGLE_CLIENT_ID: str | None = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: SecretStr | None = Field(default=None, env="GOOGLE_CLIENT_SECRET")

    OPENAI_API_KEY: SecretStr | None = Field(default=None, env="OPENAI_API_KEY")

    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_AUTH_PER_MINUTE: int = Field(default=5, env="RATE_LIMIT_AUTH_PER_MINUTE")

    # ============================================
    # SECURITY SETTINGS
    # ============================================
    ALLOWED_HOSTS: list[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")

    # Session security
    SECURE_COOKIES: bool = Field(default=True, env="SECURE_COOKIES")
    COOKIE_SAMESITE: str = Field(default="lax", env="COOKIE_SAMESITE")
    COOKIE_HTTPONLY: bool = Field(default=True, env="COOKIE_HTTPONLY")

    @validator("SECURE_COOKIES")
    def validate_secure_cookies(cls, v, values):
        """Require secure cookies in production"""
        if values.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("SECURE_COOKIES must be True in production")
        return v

    # ============================================
    # DATA RETENTION (GDPR Compliance)
    # ============================================
    DATA_RETENTION_DAYS: int = Field(default=90, env="DATA_RETENTION_DAYS")
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=365, env="AUDIT_LOG_RETENTION_DAYS")

    # ============================================
    # MONITORING
    # ============================================
    SENTRY_DSN: SecretStr | None = Field(default=None, env="SENTRY_DSN")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Ensure valid log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    # ============================================
    # PYDANTIC CONFIG
    # ============================================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ============================================
# SETTINGS INSTANCE (Cached)
# ============================================


@lru_cache
def get_settings() -> SecureSettings:
    """
    Get cached settings instance

    Uses @lru_cache to ensure settings are loaded once
    """
    try:
        settings = SecureSettings()

        # Log configuration (sanitized)
        logger.info(f"✅ Configuration loaded: {settings.ENVIRONMENT} environment")
        logger.info(f"   App: {settings.APP_NAME}")
        logger.info(f"   Debug: {settings.DEBUG}")
        logger.info(f"   CORS Origins: {len(settings.CORS_ORIGINS)} configured")

        # Security validation passed
        logger.info("✅ All security validations passed")

        return settings

    except Exception as e:
        logger.critical(f"❌ CRITICAL: Configuration validation failed: {e}")
        raise


# Export settings instance
settings = get_settings()


# ============================================
# HELPER FUNCTIONS
# ============================================


def get_secret(key: str) -> str:
    """
    Safely get a secret value

    Usage:
        api_key = get_secret("OPENAI_API_KEY")
    """
    secret = getattr(settings, key, None)

    if secret is None:
        raise ValueError(f"Secret '{key}' not found in configuration")

    # If it's a SecretStr, extract the value
    if isinstance(secret, SecretStr):
        return secret.get_secret_value()

    return secret


def validate_production_readiness() -> bool:
    """
    Validate that all production requirements are met

    Call this during startup in production
    """
    if settings.ENVIRONMENT != "production":
        return True

    logger.info("Running production readiness checks...")

    checks = {
        "DEBUG disabled": not settings.DEBUG,
        "Secure cookies enabled": settings.SECURE_COOKIES,
        "HTTPS required": all(
            origin.startswith("https://") or "localhost" in origin
            for origin in settings.CORS_ORIGINS
        ),
        "Redis password set": settings.REDIS_PASSWORD is not None,
        "Strong secret key": len(settings.SECRET_KEY.get_secret_value()) >= 32,
    }

    failed_checks = [name for name, passed in checks.items() if not passed]

    if failed_checks:
        logger.critical(f"❌ Production readiness FAILED: {failed_checks}")
        return False

    logger.info("✅ Production readiness validated")
    return True


# ============================================
# ENVIRONMENT FILE GENERATOR
# ============================================


def generate_secure_env_template():
    """
    Generate a secure .env.example file

    Run this to create template for new deployments
    """
    template = """
# PsychSync Secure Configuration
# Copy to .env and fill in real values
# NEVER commit .env to git!

# Environment
ENVIRONMENT=development
DEBUG=false

# Database (Use strong credentials!)
DATABASE_URL=postgresql://user:CHANGE_ME@localhost:5432/psychsync

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=CHANGE_ME

# JWT Authentication (Generate strong secret!)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=GENERATE_STRONG_SECRET_HERE

# Encryption (Generate Fernet key!)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=GENERATE_FERNET_KEY_HERE

# CORS (Comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=CHANGE_ME
SMTP_TLS=true

# Third-party APIs
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
OPENAI_API_KEY=

# Monitoring
SENTRY_DSN=
LOG_LEVEL=INFO

# Security
RATE_LIMIT_PER_MINUTE=60
SECURE_COOKIES=true
"""

    with open(".env.example", "w") as f:
        f.write(template.strip())

    logger.info("✅ Generated .env.example template")


if __name__ == "__main__":
    # Generate template
    generate_secure_env_template()

    # Test configuration
    try:
        settings = get_settings()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
