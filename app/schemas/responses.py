# app/schemas/responses.py
"""
Standardized response schemas for PsychSync API
Provides consistent API response format across all endpoints
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

# =============================================================================
# TYPE VARIABLES
# =============================================================================

T = TypeVar('T')

# =============================================================================
# BASE RESPONSE MODELS
# =============================================================================

class BaseResponse(GenericModel, Generic[T]):
    """
    Base response model for all API responses
    Provides consistent structure for success and error responses
    """

    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[T] = Field(None, description="Response data payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class SuccessResponse(BaseResponse[T]):
    """
    Success response model
    Used for successful API responses
    """

    success: bool = Field(True, description="Request was successful")
    error_code: Optional[str] = Field(None, description="Error code (null for success)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")


class ErrorResponse(BaseResponse[None]):
    """
    Error response model
    Used for error API responses
    """

    success: bool = Field(False, description="Request failed")
    error_code: str = Field(..., description="Standardized error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    stack_trace: Optional[str] = Field(None, description="Stack trace (development only)")


# =============================================================================
# PAGINATION MODELS
# =============================================================================

class PaginationInfo(BaseModel):
    """Pagination information for list responses"""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class PaginatedResponse(BaseResponse[List[T]]):
    """
    Paginated response model
    Used for list responses with pagination
    """

    success: bool = Field(True, description="Request was successful")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    error_code: Optional[str] = Field(None, description="Error code (null for success)")


# =============================================================================
# SPECIFIC RESPONSE MODELS
# =============================================================================

class TokenResponse(BaseModel):
    """Authentication token response"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")


class AuthResponse(SuccessResponse[TokenResponse]):
    """Authentication response with user info"""

    user: Optional[Dict[str, Any]] = Field(None, description="User information")


class HealthCheckResponse(BaseModel):
    """Health check response data"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""

    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    value: Any = Field(None, description="Invalid value")
    code: Optional[str] = Field(None, description="Error code")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-level details"""

    validation_errors: List[ValidationErrorDetail] = Field(
        default_factory=list,
        description="List of validation errors"
    )


# =============================================================================
# RESPONSE FACTORY FUNCTIONS
# =============================================================================

def create_success_response(
    data: Optional[T] = None,
    message: str = "Success",
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponse[T]:
    """
    Create a standardized success response

    Args:
        data: Response data payload
        message: Success message
        request_id: Request identifier
        metadata: Additional metadata

    Returns:
        SuccessResponse instance
    """
    return SuccessResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id,
        metadata=metadata
    )


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    stack_trace: Optional[str] = None
) -> ErrorResponse:
    """
    Create a standardized error response

    Args:
        error_code: Standardized error code
        message: Error message
        details: Additional error details
        request_id: Request identifier
        stack_trace: Stack trace (development only)

    Returns:
        ErrorResponse instance
    """
    return ErrorResponse(
        success=False,
        message=message,
        data=None,
        error_code=error_code,
        details=details,
        request_id=request_id,
        stack_trace=stack_trace
    )


def create_paginated_response(
    data: List[T],
    page: int,
    page_size: int,
    total_items: int,
    message: str = "Success",
    request_id: Optional[str] = None
) -> PaginatedResponse[T]:
    """
    Create a standardized paginated response

    Args:
        data: List of items
        page: Current page number
        page_size: Items per page
        total_items: Total number of items
        message: Success message
        request_id: Request identifier

    Returns:
        PaginatedResponse instance
    """
    total_pages = (total_items + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1

    pagination = PaginationInfo(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        timestamp=datetime.utcnow(),
        request_id=request_id,
        pagination=pagination,
        error_code=None
    )


def create_validation_error_response(
    validation_errors: List[ValidationErrorDetail],
    message: str = "Validation failed",
    request_id: Optional[str] = None
) -> ValidationErrorResponse:
    """
    Create a validation error response

    Args:
        validation_errors: List of validation errors
        message: Error message
        request_id: Request identifier

    Returns:
        ValidationErrorResponse instance
    """
    return ValidationErrorResponse(
        success=False,
        message=message,
        data=None,
        error_code="VALIDATION_ERROR",
        validation_errors=validation_errors,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )


# =============================================================================
# COMMON RESPONSE TEMPLATES
# =============================================================================

class CommonResponses:
    """Common response templates"""

    @staticmethod
    def created(data: Optional[T] = None, message: str = "Resource created successfully") -> SuccessResponse[T]:
        """Created resource response"""
        return create_success_response(data=data, message=message)

    @staticmethod
    def updated(data: Optional[T] = None, message: str = "Resource updated successfully") -> SuccessResponse[T]:
        """Updated resource response"""
        return create_success_response(data=data, message=message)

    @staticmethod
    def deleted(message: str = "Resource deleted successfully") -> SuccessResponse[None]:
        """Deleted resource response"""
        return create_success_response(data=None, message=message)

    @staticmethod
    def not_found(resource: str = "Resource") -> ErrorResponse:
        """Not found error response"""
        return create_error_response(
            error_code="NOT_FOUND",
            message=f"{resource} not found",
            details={"resource_type": resource}
        )

    @staticmethod
    def unauthorized(message: str = "Authentication required") -> ErrorResponse:
        """Unauthorized error response"""
        return create_error_response(
            error_code="UNAUTHORIZED",
            message=message
        )

    @staticmethod
    def forbidden(message: str = "Access denied") -> ErrorResponse:
        """Forbidden error response"""
        return create_error_response(
            error_code="FORBIDDEN",
            message=message
        )

    @staticmethod
    def validation_failed(validation_errors: List[ValidationErrorDetail]) -> ValidationErrorResponse:
        """Validation failed response"""
        return create_validation_error_response(
            validation_errors=validation_errors,
            message="Validation failed"
        )

    @staticmethod
    def internal_error(message: str = "Internal server error") -> ErrorResponse:
        """Internal server error response"""
        return create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message=message
        )

    @staticmethod
    def rate_limited(message: str = "Rate limit exceeded") -> ErrorResponse:
        """Rate limited response"""
        return create_error_response(
            error_code="RATE_LIMIT_EXCEEDED",
            message=message
        )


# =============================================================================
# RESPONSE TYPE ALIASES
# =============================================================================

# Common response types
UserResponse = SuccessResponse[Dict[str, Any]]
UsersListResponse = PaginatedResponse[Dict[str, Any]]
TemplateResponse = SuccessResponse[Dict[str, Any]]
TemplatesListResponse = PaginatedResponse[Dict[str, Any]]
AuthSuccessResponse = AuthResponse
HealthResponse = SuccessResponse[HealthCheckResponse]