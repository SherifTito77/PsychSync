# app/core/constants.py
"""
Application constants for PsychSync
Centralizes all magic numbers, strings, and configuration values
"""

from enum import Enum
from typing import Dict, Any

# =============================================================================
# APPLICATION METADATA
# =============================================================================

class AppInfo:
    """Application metadata constants"""

    NAME = "PsychSync"
    VERSION = "1.0.0"
    DESCRIPTION = "PsychSync AI - Behavioral Analytics for High-Performance Agile Teams"
    API_TITLE = "PsychSync AI API"
    CONTACT_EMAIL = "support@psychsync.com"
    DOCS_URL = "/docs"
    REDOC_URL = "/redoc"


# =============================================================================
# HTTP STATUS CODES
# =============================================================================

class HttpStatus:
    """HTTP status codes"""

    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# =============================================================================
# CACHE SETTINGS
# =============================================================================

class CacheKeys:
    """Cache key prefixes"""

    USER = "user"
    ASSESSMENT = "assessment"
    TEMPLATE = "template"
    TEAM = "team"
    ORGANIZATION = "organization"
    ANALYTICS = "analytics"
    SESSION = "session"

    @classmethod
    def get_user_key(cls, user_id: str) -> str:
        return f"{cls.USER}:{user_id}"

    @classmethod
    def get_assessment_key(cls, assessment_id: str) -> str:
        return f"{cls.ASSESSMENT}:{assessment_id}"


class CacheTTL:
    """Cache time-to-live values in seconds"""

    SHORT = 300      # 5 minutes
    MEDIUM = 1800    # 30 minutes
    LONG = 3600      # 1 hour
    EXTENDED = 7200  # 2 hours
    DAILY = 86400    # 24 hours


# =============================================================================
# AUTHENTICATION CONSTANTS
# =============================================================================

class Auth:
    """Authentication constants"""

    # Token settings
    DEFAULT_TOKEN_EXPIRE_MINUTES = 30
    DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7

    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128

    # Token types
    TOKEN_TYPE_ACCESS = "access"
    TOKEN_TYPE_REFRESH = "refresh"
    TOKEN_TYPE_PASSWORD_RESET = "password_reset"
    TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"

    # User roles
    ROLE_SUPERUSER = "superuser"
    ROLE_ADMIN = "admin"
    ROLE_USER = "user"
    ROLE_GUEST = "guest"


# =============================================================================
# ASSESSMENT CONSTANTS
# =============================================================================

class Assessment:
    """Assessment-related constants"""

    # Assessment frameworks
    BIG_FIVE = "big_five"
    MBTI = "mbti"
    ENNEAGRAM = "enneagram"
    DISC = "disc"
    PREDICTIVE_INDEX = "predictive_index"
    CLIFTON_STRENGTHS = "clifton_strengths"
    SOCIAL_STYLES = "social_styles"

    # Assessment types
    TYPE_PERSONALITY = "personality"
    TYPE_SKILLS = "skills"
    TYPE_COMPETENCY = "competency"
    TYPE_360_FEEDBACK = "360_feedback"
    TYPE_SURVEY = "survey"

    # Assessment statuses
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_ARCHIVED = "archived"

    # Response statuses
    RESPONSE_IN_PROGRESS = "in_progress"
    RESPONSE_COMPLETED = "completed"
    RESPONSE_ABANDONED = "abandoned"
    RESPONSE_EXPIRED = "expired"

    # Scoring
    MIN_SCORE = 0.0
    MAX_SCORE = 1.0
    DEFAULT_CONFIDENCE = 0.8

    # Time limits
    DEFAULT_MAX_DURATION_MINUTES = 60
    DEFAULT_IDLE_TIMEOUT_MINUTES = 30
    DEFAULT_EXPIRY_DAYS = 30


# =============================================================================
# DATABASE CONSTANTS
# =============================================================================

class Database:
    """Database constants"""

    # Pool settings
    DEFAULT_POOL_SIZE = 5
    DEFAULT_MAX_OVERFLOW = 10
    DEFAULT_POOL_RECYCLE = 300
    DEFAULT_POOL_PRE_PING = True

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1

    # Index names
    IDX_USER_EMAIL = "idx_user_email"
    IDX_USER_ORG = "idx_user_organization_id"
    IDX_TEMPLATE_TYPE = "idx_template_type"
    IDX_ASSESSMENT_STATUS = "idx_assessment_status"

    # Soft delete
    DELETED_AT_NULL = None


# =============================================================================
# RATE LIMITING CONSTANTS
# =============================================================================

class RateLimit:
    """Rate limiting constants"""

    # General limits
    DEFAULT_REQUESTS_PER_MINUTE = 60
    DEFAULT_REQUESTS_PER_HOUR = 1000
    DEFAULT_REQUESTS_PER_DAY = 10000

    # Auth endpoints
    AUTH_REQUESTS_PER_MINUTE = 5
    AUTH_REQUESTS_PER_HOUR = 20

    # Sensitive endpoints
    SENSITIVE_REQUESTS_PER_MINUTE = 10
    SENSITIVE_REQUESTS_PER_HOUR = 100

    # File uploads
    UPLOAD_REQUESTS_PER_HOUR = 50

    # Multipliers for authenticated users
    AUTHENTICATED_MULTIPLIER = 10
    PREMIUM_MULTIPLIER = 50


# =============================================================================
# FILE UPLOAD CONSTANTS
# =============================================================================

class FileUpload:
    """File upload constants"""

    # Size limits (bytes)
    MAX_AVATAR_SIZE = 5 * 1024 * 1024      # 5MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024   # 10MB
    MAX_IMAGE_SIZE = 20 * 1024 * 1024      # 20MB

    # Allowed extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    SPREADSHEET_EXTENSIONS = {'.xls', '.xlsx', '.csv'}

    # Upload directories
    AVATAR_DIR = "uploads/avatars"
    DOCUMENT_DIR = "uploads/documents"
    TEMP_DIR = "uploads/temp"


# =============================================================================
# EMAIL CONSTANTS
# =============================================================================

class Email:
    """Email constants"""

    # Template types
    TEMPLATE_WELCOME = "welcome"
    TEMPLATE_EMAIL_VERIFICATION = "email_verification"
    TEMPLATE_PASSWORD_RESET = "password_reset"
    TEMPLATE_ASSESSMENT_INVITATION = "assessment_invitation"
    TEMPLATE_ASSESSMENT_COMPLETED = "assessment_completed"
    TEMPLATE_TEAM_INVITATION = "team_invitation"

    # Timeouts (hours)
    VERIFICATION_EXPIRE_HOURS = 24
    PASSWORD_RESET_EXPIRE_HOURS = 1

    # Rate limits
    MAX_EMAILS_PER_HOUR = 100
    MAX_EMAILS_PER_DAY = 1000


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

class Validation:
    """Validation constants"""

    # String lengths
    MAX_NAME_LENGTH = 255
    MAX_EMAIL_LENGTH = 255
    MAX_TITLE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 2000
    MAX_MESSAGE_LENGTH = 10000

    # Regular expressions
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    STRONG_PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'

    # Phone number
    PHONE_PATTERN = r'^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'


# =============================================================================
# LOGGING CONSTANTS
# =============================================================================

class Logging:
    """Logging constants"""

    # Log levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    # Log formats
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    JSON_FORMAT = "json"

    # File settings
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    DEFAULT_LOG_FILE = "logs/psychsync.log"


# =============================================================================
# API CONSTANTS
# =============================================================================

class API:
    """API constants"""

    # API versions
    V1 = "/api/v1"

    # Response codes
    SUCCESS_CODE = "SUCCESS"
    ERROR_CODE = "ERROR"

    # Request headers
    HEADER_REQUEST_ID = "X-Request-ID"
    HEADER_API_VERSION = "X-API-Version"
    HEADER_USER_AGENT = "User-Agent"

    # Response headers
    HEADER_RATE_LIMIT = "X-RateLimit-Limit"
    HEADER_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
    HEADER_RATE_LIMIT_RESET = "X-RateLimit-Reset"

    # Content types
    JSON = "application/json"
    FORM_DATA = "multipart/form-data"
    URL_ENCODED = "application/x-www-form-urlencoded"


# =============================================================================
# CORS SETTINGS
# =============================================================================

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175"
]


# =============================================================================
# TEAM CONSTANTS
# =============================================================================

class Team:
    """Team constants"""

    # Team sizes
    MIN_TEAM_SIZE = 2
    MAX_TEAM_SIZE = 50
    DEFAULT_TEAM_SIZE = 10

    # Team roles
    ROLE_OWNER = "owner"
    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"
    ROLE_VIEWER = "viewer"

    # Invitation statuses
    INVITATION_PENDING = "pending"
    INVITATION_ACCEPTED = "accepted"
    INVITATION_DECLINED = "declined"
    INVITATION_EXPIRED = "expired"

    # Invitation expiration (days)
    INVITATION_EXPIRE_DAYS = 7


# =============================================================================
# ORGANIZATION CONSTANTS
# =============================================================================

class Organization:
    """Organization constants"""

    # Organization sizes
    MAX_USERS_PER_ORG = 1000
    DEFAULT_MAX_USERS = 100

    # Organization types
    TYPE_STARTUP = "startup"
    TYPE_SMALL_BUSINESS = "small_business"
    TYPE_ENTERPRISE = "enterprise"
    TYPE_NONPROFIT = "nonprofit"
    TYPE_EDUCATIONAL = "educational"

    # Subscription tiers
    TIER_FREE = "free"
    TIER_BASIC = "basic"
    TIER_PROFESSIONAL = "professional"
    TIER_ENTERPRISE = "enterprise"


# =============================================================================
# AI PROCESSING CONSTANTS
# =============================================================================

class AIProcessing:
    """AI processing constants"""

    # Processing timeouts (seconds)
    DEFAULT_TIMEOUT = 30
    LONG_PROCESSING_TIMEOUT = 300  # 5 minutes

    # Confidence thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.5
    DEFAULT_CONFIDENCE_THRESHOLD = 0.8
    HIGH_CONFIDENCE_THRESHOLD = 0.9

    # Processing queues
    QUEUE_HIGH_PRIORITY = "high"
    QUEUE_NORMAL_PRIORITY = "normal"
    QUEUE_LOW_PRIORITY = "low"

    # Retry settings
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 5


# =============================================================================
# SECURITY CONSTANTS
# =============================================================================

class Security:
    """Security constants"""

    # JWT settings
    JWT_ALGORITHM = "HS256"
    JWT_SECRET_MIN_LENGTH = 32

    # Password hashing
    BCRYPT_ROUNDS = 12

    # Session settings
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONCURRENT_SESSIONS = 5

    # Two-factor authentication
    TOTP_DIGITS = 6
    TOTP_PERIOD = 30
    BACKUP_CODES_COUNT = 10

    # Rate limiting for failed attempts
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW_MINUTES = 15
    LOCKOUT_DURATION_MINUTES = 30


# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

class EnvironmentVariables:
    """Environment variable names"""

    # Database
    DATABASE_URL = "DATABASE_URL"
    DB_HOST = "DB_HOST"
    DB_PORT = "DB_PORT"
    DB_NAME = "DB_NAME"
    DB_USER = "DB_USER"
    DB_PASSWORD = "DB_PASSWORD"

    # Redis
    REDIS_HOST = "REDIS_HOST"
    REDIS_PORT = "REDIS_PORT"
    REDIS_DB = "REDIS_DB"
    REDIS_PASSWORD = "REDIS_PASSWORD"

    # Security
    SECRET_KEY = "SECRET_KEY"
    JWT_ALGORITHM = "JWT_ALGORITHM"

    # Email
    SMTP_HOST = "SMTP_HOST"
    SMTP_PORT = "SMTP_PORT"
    SMTP_USER = "SMTP_USER"
    SMTP_PASSWORD = "SMTP_PASSWORD"

    # Application
    DEBUG = "DEBUG"
    ENVIRONMENT = "ENVIRONMENT"
    LOG_LEVEL = "LOG_LEVEL"

    # External services
    SENTRY_DSN = "SENTRY_DSN"
    OPENAI_API_KEY = "OPENAI_API_KEY"


# =============================================================================
# DEFAULT VALUES DICTIONARY
# =============================================================================

DEFAULT_VALUES: Dict[str, Any] = {
    "timezone": "UTC",
    "locale": "en-US",
    "currency": "USD",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M:%S",
    "datetime_format": "%Y-%m-%d %H:%M:%S",
    "page_size": Database.DEFAULT_PAGE_SIZE,
    "max_page_size": Database.MAX_PAGE_SIZE,
    "cache_ttl": CacheTTL.MEDIUM,
    "rate_limit": RateLimit.DEFAULT_REQUESTS_PER_MINUTE,
}


# =============================================================================
# STATUS ENUMS
# =============================================================================

class Status(str, Enum):
    """Common status values"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DRAFT = "draft"
    PUBLISHED = "published"


class Priority(str, Enum):
    """Priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"