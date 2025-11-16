# app/core/exceptions.py
"""
Comprehensive exception handling system for PsychSync
Provides structured error responses and proper error codes
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# ERROR CODE ENUMS
# =============================================================================

class ErrorCode(str, Enum):
    """Standardized error codes for the application"""

    # Authentication & Authorization (1000-1099)
    UNAUTHORIZED = "AUTH_1000"
    FORBIDDEN = "AUTH_1001"
    INVALID_CREDENTIALS = "AUTH_1002"
    TOKEN_EXPIRED = "AUTH_1003"
    TOKEN_INVALID = "AUTH_1004"
    USER_NOT_FOUND = "AUTH_1005"
    USER_ALREADY_EXISTS = "AUTH_1006"
    USER_INACTIVE = "AUTH_1007"
    EMAIL_NOT_VERIFIED = "AUTH_1008"
    PASSWORD_RESET_EXPIRED = "AUTH_1009"
    INVALID_PERMISSIONS = "AUTH_1010"

    # Validation (2000-2099)
    VALIDATION_ERROR = "VAL_2000"
    INVALID_INPUT = "VAL_2001"
    MISSING_REQUIRED_FIELD = "VAL_2002"
    INVALID_EMAIL = "VAL_2003"
    INVALID_PASSWORD = "VAL_2004"
    INVALID_UUID = "VAL_2005"
    INVALID_DATE_FORMAT = "VAL_2006"
    FILE_TOO_LARGE = "VAL_2007"
    INVALID_FILE_TYPE = "VAL_2008"

    # Database (3000-3099)
    DATABASE_ERROR = "DB_3000"
    RECORD_NOT_FOUND = "DB_3001"
    DUPLICATE_RECORD = "DB_3002"
    FOREIGN_KEY_VIOLATION = "DB_3003"
    CONSTRAINT_VIOLATION = "DB_3004"
    CONNECTION_ERROR = "DB_3005"
    MIGRATION_ERROR = "DB_3006"

    # Business Logic (4000-4099)
    BUSINESS_RULE_VIOLATION = "BIZ_4000"
    RESOURCE_LIMIT_EXCEEDED = "BIZ_4001"
    QUOTA_EXCEEDED = "BIZ_4002"
    SUBSCRIPTION_EXPIRED = "BIZ_4003"
    FEATURE_NOT_AVAILABLE = "BIZ_4004"
    INVALID_OPERATION = "BIZ_4005"
    ASSESSMENT_NOT_AVAILABLE = "BIZ_4006"
    TEMPLATE_NOT_FOUND = "BIZ_4007"

    # External Services (5000-5099)
    EMAIL_SERVICE_ERROR = "EXT_5000"
    PAYMENT_SERVICE_ERROR = "EXT_5001"
    SMS_SERVICE_ERROR = "EXT_5002"
    THIRD_PARTY_API_ERROR = "EXT_5003"
    NETWORK_ERROR = "EXT_5004"

    # System (6000-6099)
    INTERNAL_SERVER_ERROR = "SYS_6000"
    SERVICE_UNAVAILABLE = "SYS_6001"
    RATE_LIMIT_EXCEEDED = "SYS_6002"
    MAINTENANCE_MODE = "SYS_6003"
    CACHE_ERROR = "SYS_6004"
    CONFIGURATION_ERROR = "SYS_6005"

    # AI/ML Processing (7000-7099)
    AI_PROCESSING_ERROR = "AI_7000"
    MODEL_NOT_FOUND = "AI_7001"
    PROCESSING_TIMEOUT = "AI_7002"
    INVALID_FRAMEWORK = "AI_7003"
    INSUFFICIENT_DATA = "AI_7004"

# =============================================================================
# BASE EXCEPTION CLASSES
# =============================================================================

class PsychSyncException(Exception):
    """
    Base exception class for all PsychSync exceptions
    Provides structured error information and logging
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": True,
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "status_code": self.status_code
        }

    def log(self, level: str = "error"):
        """Log the exception with structured information"""
        log_data = {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat()
        }

        if self.cause:
            log_data["cause"] = str(self.cause)

        getattr(logger, level)(f"PsychSyncException: {self.message}", extra=log_data)

# =============================================================================
# AUTHENTICATION EXCEPTIONS
# =============================================================================

class AuthenticationError(PsychSyncException):
    """Base class for authentication errors"""

    def __init__(self, message: str, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, status_code=401, details=details)


class UnauthorizedError(AuthenticationError):
    """User is not authenticated"""

    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.UNAUTHORIZED, details)


class ForbiddenError(AuthenticationError):
    """User does not have permission"""

    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.FORBIDDEN, status_code=403, details=details)


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password"""

    def __init__(self, message: str = "Invalid email or password", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_CREDENTIALS, details=details)


class UserNotFoundError(AuthenticationError):
    """User not found"""

    def __init__(self, identifier: str, details: Optional[Dict[str, Any]] = None):
        message = f"User not found: {identifier}"
        if details is None:
            details = {"identifier": identifier}
        super().__init__(message, ErrorCode.USER_NOT_FOUND, details=details)


class UserAlreadyExistsError(AuthenticationError):
    """User already exists"""

    def __init__(self, field: str, value: str, details: Optional[Dict[str, Any]] = None):
        message = f"User with {field} '{value}' already exists"
        if details is None:
            details = {"field": field, "value": value}
        super().__init__(message, ErrorCode.USER_ALREADY_EXISTS, details=details)


class UserInactiveError(AuthenticationError):
    """User account is inactive"""

    def __init__(self, message: str = "User account is inactive", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.USER_INACTIVE, details=details)


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================

class ValidationError(PsychSyncException):
    """Base class for validation errors"""

    def __init__(self, message: str, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, status_code=422, details=details)


class InvalidInputError(ValidationError):
    """Invalid input data"""

    def __init__(self, message: str = "Invalid input data", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_INPUT, details=details)


class MissingFieldError(ValidationError):
    """Required field is missing"""

    def __init__(self, field: str, details: Optional[Dict[str, Any]] = None):
        message = f"Required field '{field}' is missing"
        if details is None:
            details = {"field": field}
        super().__init__(message, ErrorCode.MISSING_REQUIRED_FIELD, details=details)


class InvalidEmailError(ValidationError):
    """Invalid email format"""

    def __init__(self, email: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid email format: {email}"
        if details is None:
            details = {"email": email}
        super().__init__(message, ErrorCode.INVALID_EMAIL, details=details)


class InvalidPasswordError(ValidationError):
    """Invalid password"""

    def __init__(self, message: str = "Password does not meet requirements", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_PASSWORD, details=details)


# =============================================================================
# DATABASE EXCEPTIONS
# =============================================================================

class DatabaseError(PsychSyncException):
    """Base class for database errors"""

    def __init__(self, message: str, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message, error_code, status_code=500, details=details, cause=cause)


class RecordNotFoundError(DatabaseError):
    """Record not found in database"""

    def __init__(self, resource: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found: {identifier}"
        if details is None:
            details = {"resource": resource, "identifier": identifier}
        super().__init__(message, ErrorCode.RECORD_NOT_FOUND, details=details, status_code=404)


class DuplicateRecordError(DatabaseError):
    """Duplicate record in database"""

    def __init__(self, resource: str, field: str, value: str, details: Optional[Dict[str, Any]] = None):
        message = f"Duplicate {resource} with {field} '{value}'"
        if details is None:
            details = {"resource": resource, "field": field, "value": value}
        super().__init__(message, ErrorCode.DUPLICATE_RECORD, details=details, status_code=409)


# =============================================================================
# BUSINESS LOGIC EXCEPTIONS
# =============================================================================

class BusinessLogicError(PsychSyncException):
    """Base class for business logic errors"""

    def __init__(self, message: str, error_code: ErrorCode, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, status_code=status_code, details=details)


class ResourceLimitExceededError(BusinessLogicError):
    """Resource limit exceeded"""

    def __init__(self, resource: str, limit: int, details: Optional[Dict[str, Any]] = None):
        message = f"Resource limit exceeded for {resource}: {limit}"
        if details is None:
            details = {"resource": resource, "limit": limit}
        super().__init__(message, ErrorCode.RESOURCE_LIMIT_EXCEEDED, details=details)


class InvalidOperationError(BusinessLogicError):
    """Invalid operation"""

    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid operation: {operation}. {reason}"
        if details is None:
            details = {"operation": operation, "reason": reason}
        super().__init__(message, ErrorCode.INVALID_OPERATION, details=details)


# =============================================================================
# AI/ML PROCESSING EXCEPTIONS
# =============================================================================

class AIProcessingError(PsychSyncException):
    """Base class for AI processing errors"""

    def __init__(self, message: str, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message, error_code, status_code=500, details=details, cause=cause)


class ModelNotFoundError(AIProcessingError):
    """AI model not found"""

    def __init__(self, model_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"AI model not found: {model_name}"
        if details is None:
            details = {"model_name": model_name}
        super().__init__(message, ErrorCode.MODEL_NOT_FOUND, details=details)


class ProcessingTimeoutError(AIProcessingError):
    """AI processing timeout"""

    def __init__(self, operation: str, timeout_seconds: int, details: Optional[Dict[str, Any]] = None):
        message = f"AI processing timeout for {operation}: {timeout_seconds}s"
        if details is None:
            details = {"operation": operation, "timeout_seconds": timeout_seconds}
        super().__init__(message, ErrorCode.PROCESSING_TIMEOUT, details=details)


# =============================================================================
# ERROR UTILITY FUNCTIONS
# =============================================================================

def handle_database_error(error: Exception, operation: str, resource: str = None) -> PsychSyncException:
    """
    Convert database errors to structured exceptions

    Args:
        error: Original database exception
        operation: Operation being performed
        resource: Resource type (optional)

    Returns:
        Structured PsychSyncException
    """
    error_str = str(error).lower()

    if "duplicate" in error_str or "unique" in error_str:
        return DuplicateRecordError(
            resource=resource or "record",
            field="unknown",
            value="duplicate",
            details={"original_error": str(error), "operation": operation}
        )
    elif "foreign key" in error_str:
        return BusinessLogicError(
            message="Referenced resource does not exist",
            error_code=ErrorCode.FOREIGN_KEY_VIOLATION,
            details={"original_error": str(error), "operation": operation}
        )
    elif "connection" in error_str:
        return DatabaseError(
            message="Database connection error",
            error_code=ErrorCode.CONNECTION_ERROR,
            details={"original_error": str(error), "operation": operation},
            cause=error
        )
    else:
        return DatabaseError(
            message=f"Database error during {operation}",
            error_code=ErrorCode.DATABASE_ERROR,
            details={"original_error": str(error), "operation": operation},
            cause=error
        )


def log_exception(exception: PsychSyncException, user_id: Optional[str] = None, request_id: Optional[str] = None):
    """
    Log exception with additional context

    Args:
        exception: Exception to log
        user_id: User ID (optional)
        request_id: Request ID (optional)
    """
    log_data = {
        "error_code": exception.error_code.value,
        "message": exception.message,
        "details": exception.details,
        "status_code": exception.status_code,
        "timestamp": exception.timestamp.isoformat()
    }

    if user_id:
        log_data["user_id"] = user_id
    if request_id:
        log_data["request_id"] = request_id
    if exception.cause:
        log_data["cause"] = str(exception.cause)

    logger.error(f"PsychSyncException: {exception.message}", extra=log_data)


def create_error_response(exception: PsychSyncException) -> Dict[str, Any]:
    """
    Create standardized error response for API

    Args:
        exception: Exception to convert

    Returns:
        Standardized error response dictionary
    """
    response = exception.to_dict()

    # Add helpful information for development
    if logger.level <= logging.DEBUG:
        response["debug"] = {
            "exception_type": exception.__class__.__name__,
            "cause": str(exception.cause) if exception.cause else None
        }

    # Ensure datetime is properly serialized as ISO format
    if "timestamp" in response:
        response["timestamp"] = exception.timestamp.isoformat()

    return response