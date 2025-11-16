# app/core/config.py

"""
File Path: app/core/config.py
Complete Application Configuration Settings
Backward compatible with existing PsychSync .env variables
"""

import os
import json
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, EmailStr


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    PROJECT_NAME: str = Field(default="PsychSync AI", env="PROJECT_NAME")
    APP_NAME: str = Field(default="PsychSync", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")

    @property
    def api_prefix(self) -> str:
        """Get API prefix"""
        return self.API_V1_PREFIX
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production-min-32-chars",
        env="SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret"""
        return self.SECRET_KEY
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, env="PASSWORD_REQUIRE_LOWERCASE")
    PASSWORD_REQUIRE_DIGITS: bool = Field(default=True, env="PASSWORD_REQUIRE_DIGITS")
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(default=24, env="EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS")
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    DATABASE_URL: str = Field(
        default="postgresql://psychsync_user:password@localhost:5432/psychsync_db",
        env="DATABASE_URL"
    )
    DB_USER: str = Field(default="psychsync_user", env="DB_USER")
    DB_PASSWORD: str = Field(default="password", env="DB_PASSWORD")
    DB_NAME: str = Field(default="psychsync_db", env="DB_NAME")
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_POOL_SIZE: int = Field(default=5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    DB_POOL_RECYCLE: int = Field(default=300, env="DB_POOL_RECYCLE")
    DB_POOL_PRE_PING: bool = Field(default=True, env="DB_POOL_PRE_PING")
    DB_ECHO: bool = Field(default=False, env="DB_ECHO")
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # =============================================================================
    # CACHE CONFIGURATION
    # =============================================================================
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_DEFAULT_EXPIRE: int = Field(default=3600, env="CACHE_DEFAULT_EXPIRE")
    CACHE_USER_EXPIRE: int = Field(default=1800, env="CACHE_USER_EXPIRE")
    CACHE_ASSESSMENT_EXPIRE: int = Field(default=3600, env="CACHE_ASSESSMENT_EXPIRE")
    CACHE_TEAM_EXPIRE: int = Field(default=1800, env="CACHE_TEAM_EXPIRE")
    CACHE_ORG_EXPIRE: int = Field(default=7200, env="CACHE_ORG_EXPIRE")
    
    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175",
        env="ALLOWED_ORIGINS"
    )
    BACKEND_CORS_ORIGINS: str = Field(
        default='["http://localhost:3000","http://localhost:5173","http://localhost:5174","http://localhost:5175"]',
        env="BACKEND_CORS_ORIGINS"
    )
    ALLOWED_METHODS: str = Field(
        default="GET,POST,PUT,DELETE,PATCH,OPTIONS",
        env="ALLOWED_METHODS"
    )
    ALLOWED_HEADERS: str = Field(default="*", env="ALLOWED_HEADERS")
    ALLOW_CREDENTIALS: bool = Field(default=True, env="ALLOW_CREDENTIALS")

    # =============================================================================
    # EMAIL CONNECTOR SETTINGS
    # =============================================================================

    # Gmail OAuth Settings
    GMAIL_CLIENT_ID: Optional[str] = Field(default=None, env="GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: Optional[str] = Field(default=None, env="GMAIL_CLIENT_SECRET")

    # Outlook/Office 365 OAuth Settings
    OUTLOOK_CLIENT_ID: Optional[str] = Field(default=None, env="OUTLOOK_CLIENT_ID")
    OUTLOOK_CLIENT_SECRET: Optional[str] = Field(default=None, env="OUTLOOK_CLIENT_SECRET")

    # Email Processing Settings
    EMAIL_CALLBACK_URL: str = Field(
        default="http://localhost:8000/api/v1/email/callback",
        env="EMAIL_CALLBACK_URL"
    )
    EMAIL_SYNC_BATCH_SIZE: int = Field(default=1000, env="EMAIL_SYNC_BATCH_SIZE")
    EMAIL_SYNC_MAX_DAYS_BACK: int = Field(default=30, env="EMAIL_SYNC_MAX_DAYS_BACK")
    EMAIL_MIN_SYNC_INTERVAL_HOURS: int = Field(default=6, env="EMAIL_MIN_SYNC_INTERVAL_HOURS")

    # Email Analysis Settings
    EMAIL_ANALYSIS_ENABLED: bool = Field(default=False, env="EMAIL_ANALYSIS_ENABLED")
    EMAIL_ANALYZE_INTERNAL_ONLY: bool = Field(default=True, env="EMAIL_ANALYZE_INTERNAL_ONLY")
    EMAIL_EXCLUDE_SENSITIVE_SUBJECTS: bool = Field(default=True, env="EMAIL_EXCLUDE_SENSITIVE_SUBJECTS")
    EMAIL_ENCRYPTION_KEY: Optional[str] = Field(default=None, env="EMAIL_ENCRYPTION_KEY")

    # Rate limiting for email APIs
    EMAIL_RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=10000, env="EMAIL_RATE_LIMIT_REQUESTS_PER_HOUR")
    EMAIL_RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, env="EMAIL_RATE_LIMIT_REQUESTS_PER_MINUTE")

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS to list"""
        if self.ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        if self.BACKEND_CORS_ORIGINS:
            try:
                origins = json.loads(self.BACKEND_CORS_ORIGINS.strip())
                return origins if isinstance(origins, list) else []
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"]
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Alias for backward compatibility"""
        return self.allowed_origins_list
    
    @property
    def allowed_methods_list(self) -> List[str]:
        """Convert ALLOWED_METHODS string to list"""
        return [method.strip() for method in self.ALLOWED_METHODS.split(",")]
    
    # =============================================================================
    # EMAIL CONFIGURATION
    # =============================================================================
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # Mail settings (alternative naming)
    MAIL_USERNAME: str = Field(default="your-email@gmail.com", env="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(default="your-gmail-app-password", env="MAIL_PASSWORD")
    MAIL_FROM: str = Field(default="your-email@gmail.com", env="MAIL_FROM")
    MAIL_PORT: int = Field(default=587, env="MAIL_PORT")
    MAIL_SERVER: str = Field(default="smtp.gmail.com", env="MAIL_SERVER")
    MAIL_FROM_NAME: str = Field(default="PsychSync", env="MAIL_FROM_NAME")
    MAIL_STARTTLS: bool = Field(default=True, env="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = Field(default=False, env="MAIL_SSL_TLS")
    MAIL_USE_CREDENTIALS: bool = Field(default=True, env="MAIL_USE_CREDENTIALS")
    MAIL_USE_TLS: bool = Field(default=True, env="MAIL_USE_TLS")
    MAIL_USE_SSL: bool = Field(default=False, env="MAIL_USE_SSL")
    MAIL_VALIDATE_CERTS: bool = Field(default=False, env="MAIL_VALIDATE_CERTS")
    
    EMAIL_FROM: Optional[str] = Field(default=None, env="EMAIL_FROM")
    EMAIL_FROM_NAME: str = Field(default="PsychSync", env="EMAIL_FROM_NAME")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_SSL: bool = Field(default=False, env="SMTP_SSL")
    EMAIL_TEMPLATES_DIR: str = Field(default="templates/email", env="EMAIL_TEMPLATES_DIR")
    
    @property
    def emails_enabled(self) -> bool:
        """Check if email is properly configured"""
        return bool(
            (self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD) or
            (self.MAIL_SERVER and self.MAIL_USERNAME and self.MAIL_PASSWORD)
        )
    
    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    RATE_LIMIT_PER_DAY: int = Field(default=10000, env="RATE_LIMIT_PER_DAY")
    RATE_LIMIT_AUTHENTICATED_MULTIPLIER: int = Field(default=10, env="RATE_LIMIT_AUTHENTICATED_MULTIPLIER")
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/psychsync.log", env="LOG_FILE")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_MAX_BYTES: int = Field(default=10485760, env="LOG_MAX_BYTES")
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # =============================================================================
    # FILE UPLOAD SETTINGS
    # =============================================================================
    MAX_UPLOAD_SIZE: int = Field(default=10485760, env="MAX_UPLOAD_SIZE")
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    ALLOWED_UPLOAD_EXTENSIONS: str = Field(
        default=".jpg,.jpeg,.png,.pdf,.doc,.docx",
        env="ALLOWED_UPLOAD_EXTENSIONS"
    )
    
    @property
    def allowed_upload_extensions_list(self) -> List[str]:
        """Convert allowed extensions string to list"""
        return [ext.strip() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")]
    
    # =============================================================================
    # ASSESSMENT CONFIGURATION
    # =============================================================================
    ASSESSMENT_FRAMEWORKS: str = Field(
        default="MBTI,BIG_FIVE,ENNEAGRAM,DISC,PREDICTIVE_INDEX,CLIFTON_STRENGTHS,SOCIAL_STYLES",
        env="ASSESSMENT_FRAMEWORKS"
    )
    ASSESSMENT_MAX_DURATION: int = Field(default=60, env="ASSESSMENT_MAX_DURATION")
    ASSESSMENT_IDLE_TIMEOUT: int = Field(default=30, env="ASSESSMENT_IDLE_TIMEOUT")
    ASSESSMENT_EXPIRY_DAYS: int = Field(default=30, env="ASSESSMENT_EXPIRY_DAYS")
    
    @property
    def assessment_frameworks_list(self) -> List[str]:
        """Convert assessment frameworks string to list"""
        return [fw.strip() for fw in self.ASSESSMENT_FRAMEWORKS.split(",")]
    
    # =============================================================================
    # AI/ML SETTINGS
    # =============================================================================
    AI_ENABLED: bool = Field(default=False, env="AI_ENABLED")
    AI_MODEL_PATH: str = Field(default="", env="AI_MODEL_PATH")
    AI_API_KEY: str = Field(default="", env="AI_API_KEY")
    AI_API_URL: str = Field(default="", env="AI_API_URL")
    AI_MAX_TOKENS: int = Field(default=1000, env="AI_MAX_TOKENS")
    AI_TEMPERATURE: float = Field(default=0.7, env="AI_TEMPERATURE")
    
    # =============================================================================
    # TEAM SETTINGS
    # =============================================================================
    MAX_TEAM_SIZE: int = Field(default=50, env="MAX_TEAM_SIZE")
    MIN_TEAM_SIZE: int = Field(default=2, env="MIN_TEAM_SIZE")
    TEAM_INVITE_EXPIRY_DAYS: int = Field(default=7, env="TEAM_INVITE_EXPIRY_DAYS")
    
    # =============================================================================
    # ORGANIZATION SETTINGS
    # =============================================================================
    MAX_USERS_PER_ORG: int = Field(default=1000, env="MAX_USERS_PER_ORG")
    ORG_INVITE_EXPIRY_DAYS: int = Field(default=7, env="ORG_INVITE_EXPIRY_DAYS")
    
    # =============================================================================
    # PAGINATION SETTINGS
    # =============================================================================
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # =============================================================================
    # FRONTEND SETTINGS
    # =============================================================================
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    FRONTEND_PASSWORD_RESET_URL: str = Field(
        default="http://localhost:3000/reset-password",
        env="FRONTEND_PASSWORD_RESET_URL"
    )
    FRONTEND_EMAIL_VERIFY_URL: str = Field(
        default="http://localhost:3000/verify-email",
        env="FRONTEND_EMAIL_VERIFY_URL"
    )
    
    # =============================================================================
    # CELERY CONFIGURATION
    # =============================================================================
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # =============================================================================
    # MONITORING & ANALYTICS
    # =============================================================================
    SENTRY_DSN: str = Field(default="", env="SENTRY_DSN")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # =============================================================================
    # TESTING SETTINGS
    # =============================================================================
    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: str = Field(
        default="postgresql+asyncpg://psychsync_user:password@localhost:5432/psychsync_test",
        env="TEST_DATABASE_URL"
    )
    
    # =============================================================================
    # VALIDATORS
    # =============================================================================
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            return 'INFO'
        return v.upper()
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment"""
        allowed_envs = ['development', 'staging', 'production', 'test']
        if v.lower() not in allowed_envs:
            return 'development'
        return v.lower()
    
    # =============================================================================
    # PYDANTIC CONFIGURATION
    # =============================================================================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# =============================================================================
# CREATE GLOBAL SETTINGS INSTANCE
# =============================================================================
settings = Settings()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_database_url(async_driver: bool = False) -> str:
    """
    Get database URL with optional async driver
    Handles both asyncpg and psycopg2 formats
    """
    db_url = settings.DATABASE_URL

    # Debug logging to understand what URL is being used
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"DEBUG: Original DATABASE_URL = {db_url}")
    logger.warning(f"DEBUG: DB_USER from settings = {settings.DB_USER}")

    if async_driver:
        if 'postgresql://' in db_url and 'asyncpg' not in db_url:
            result = db_url.replace('postgresql://', 'postgresql+asyncpg://')
            logger.warning(f"DEBUG: Final async URL = {result}")
            return result
        logger.warning(f"DEBUG: Final async URL (unchanged) = {db_url}")
        return db_url
    else:
        result = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        logger.warning(f"DEBUG: Final sync URL = {result}")
        return result


def is_production() -> bool:
    """Check if running in production"""
    return settings.ENVIRONMENT == 'production'


def is_development() -> bool:
    """Check if running in development"""
    return settings.ENVIRONMENT == 'development'


def is_testing() -> bool:
    """Check if running tests"""
    return settings.TESTING or settings.ENVIRONMENT == 'test'