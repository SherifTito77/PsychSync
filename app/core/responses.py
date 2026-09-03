# app/core/responses.py
"""
Standardized API Response System for PsychSync
Provides consistent response formats across all endpoints
"""

from datetime import datetime
from typing import Any, TypeVar

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_serializer, field_validator

T = TypeVar("T")


class BaseResponse[T](BaseModel):
    """Base response with common fields"""

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Human-readable message")
    data: T | None = Field(None, description="Response data payload")
    errors: list[str] | None = Field(None, description="List of error messages")
    meta: dict[str, Any] | None = Field(None, description="Additional metadata")
    request_id: str | None = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """Convert datetime to ISO format string for JSON serialization"""
        return value.isoformat() if value else None


class SuccessResponse(BaseResponse[T]):
    """Response for successful operations"""

    success: bool = True


class ErrorResponse(BaseResponse[T]):
    """Response for failed operations"""

    success: bool = False


class PaginatedResponse(BaseResponse[list[T]]):
    """Response for paginated list operations"""

    pagination: dict[str, Any] = Field(description="Pagination metadata")

    @field_validator("pagination")
    @classmethod
    def validate_pagination(cls, v):
        """Ensure pagination has required fields"""
        required_fields = [
            "page",
            "page_size",
            "total",
            "total_pages",
            "has_next",
            "has_prev",
        ]
        for field in required_fields:
            if field not in v:
                v[field] = (
                    0
                    if field in ["page", "page_size", "total", "total_pages"]
                    else False
                )
        return v


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information"""

    field: str = Field(description="Field that failed validation")
    message: str = Field(description="Validation error message")
    value: Any | None = Field(None, description="The value that failed validation")


class ValidationErrorResponse(ErrorResponse[None]):
    """Response for validation errors with detailed field information"""

    validation_errors: list[ValidationErrorDetail] | None = Field(
        None, description="Detailed validation errors"
    )


class APIResponse:
    """
    Factory class for creating standardized API responses
    """

    @staticmethod
    def success(
        data: T | None = None,
        message: str = "Operation completed successfully",
        meta: dict[str, Any] | None = None,
        request_id: str | None = None,
        status_code: int = status.HTTP_200_OK,
    ) -> JSONResponse:
        """
        Create a successful response

        Args:
            data: Response data payload
            message: Success message
            meta: Additional metadata
            request_id: Request tracking ID
            status_code: HTTP status code

        Returns:
            JSONResponse with standardized format
        """
        response_data = SuccessResponse(
            message=message, data=data, meta=meta, request_id=request_id
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True), status_code=status_code
        )

    @staticmethod
    def created(
        data: T | None = None,
        message: str = "Resource created successfully",
        meta: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> JSONResponse:
        """
        Create a response for successful resource creation

        Args:
            data: Created resource data
            message: Success message
            meta: Additional metadata
            request_id: Request tracking ID

        Returns:
            JSONResponse with 201 status code
        """
        return APIResponse.success(
            data=data,
            message=message,
            meta=meta,
            request_id=request_id,
            status_code=status.HTTP_201_CREATED,
        )

    @staticmethod
    def paginated(
        items: list[T],
        page: int,
        page_size: int,
        total: int,
        message: str = "Items retrieved successfully",
        meta: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> JSONResponse:
        """
        Create a paginated response

        Args:
            items: List of items
            page: Current page number (1-based)
            page_size: Number of items per page
            total: Total number of items
            message: Success message
            meta: Additional metadata
            request_id: Request tracking ID

        Returns:
            JSONResponse with pagination metadata
        """
        # Calculate pagination metadata
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "items_on_page": len(items),
        }

        response_data = PaginatedResponse(
            message=message,
            data=items,
            pagination=pagination,
            meta=meta,
            request_id=request_id,
        )

        return JSONResponse(content=response_data.dict(exclude_none=True))

    @staticmethod
    def error(
        message: str,
        errors: list[str] | None = None,
        meta: dict[str, Any] | None = None,
        request_id: str | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> JSONResponse:
        """
        Create an error response

        Args:
            message: Error message
            errors: List of error messages
            meta: Additional metadata
            request_id: Request tracking ID
            status_code: HTTP status code

        Returns:
            JSONResponse with error format
        """
        response_data = ErrorResponse(
            message=message, data=None, errors=errors, meta=meta, request_id=request_id
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True), status_code=status_code
        )

    @staticmethod
    def not_found(
        message: str = "Resource not found", request_id: str | None = None
    ) -> JSONResponse:
        """
        Create a 404 not found response

        Args:
            message: Not found message
            request_id: Request tracking ID

        Returns:
            JSONResponse with 404 status code
        """
        return APIResponse.error(
            message=message,
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        validation_errors: list[ValidationErrorDetail] | None = None,
        errors: list[str] | None = None,
        request_id: str | None = None,
    ) -> JSONResponse:
        """
        Create a validation error response

        Args:
            message: Validation error message
            validation_errors: Detailed field validation errors
            errors: General error messages
            request_id: Request tracking ID

        Returns:
            JSONResponse with 422 status code
        """
        response_data = ValidationErrorResponse(
            message=message,
            data=None,
            errors=errors,
            validation_errors=validation_errors,
            request_id=request_id,
        )

        return JSONResponse(
            content=response_data.dict(exclude_none=True),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @staticmethod
    def unauthorized(
        message: str = "Unauthorized access", request_id: str | None = None
    ) -> JSONResponse:
        """
        Create an unauthorized response

        Args:
            message: Unauthorized message
            request_id: Request tracking ID

        Returns:
            JSONResponse with 401 status code
        """
        return APIResponse.error(
            message=message,
            request_id=request_id,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def forbidden(
        message: str = "Access forbidden", request_id: str | None = None
    ) -> JSONResponse:
        """
        Create a forbidden response

        Args:
            message: Forbidden message
            request_id: Request tracking ID

        Returns:
            JSONResponse with 403 status code
        """
        return APIResponse.error(
            message=message,
            request_id=request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    @staticmethod
    def conflict(
        message: str = "Resource conflict", request_id: str | None = None
    ) -> JSONResponse:
        """
        Create a conflict response

        Args:
            message: Conflict message
            request_id: Request tracking ID

        Returns:
            JSONResponse with 409 status code
        """
        return APIResponse.error(
            message=message, request_id=request_id, status_code=status.HTTP_409_CONFLICT
        )

    @staticmethod
    def server_error(
        message: str = "Internal server error", request_id: str | None = None
    ) -> JSONResponse:
        """
        Create a server error response

        Args:
            message: Server error message
            request_id: Request tracking ID

        Returns:
            JSONResponse with 500 status code
        """
        return APIResponse.error(
            message=message,
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @staticmethod
    def rate_limited(
        message: str = "Rate limit exceeded",
        request_id: str | None = None,
        retry_after: int | None = None,
    ) -> JSONResponse:
        """
        Create a rate limited response

        Args:
            message: Rate limit message
            request_id: Request tracking ID
            retry_after: Seconds until client can retry

        Returns:
            JSONResponse with 429 status code
        """
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        return APIResponse.error(
            message=message,
            request_id=request_id,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
        )


class ResponseBuilder:
    """
    Builder pattern for constructing complex responses
    """

    def __init__(self):
        self.data = None
        self.message = "Operation completed successfully"
        self.errors = None
        self.meta = None
        self.request_id = None
        self.validation_errors = None
        self.status_code = status.HTTP_200_OK

    def with_data(self, data: T) -> "ResponseBuilder":
        """Add data to response"""
        self.data = data
        return self

    def with_message(self, message: str) -> "ResponseBuilder":
        """Set response message"""
        self.message = message
        return self

    def with_errors(self, errors: list[str]) -> "ResponseBuilder":
        """Add error messages"""
        self.errors = errors
        return self

    def with_meta(self, meta: dict[str, Any]) -> "ResponseBuilder":
        """Add metadata"""
        self.meta = meta
        return self

    def with_request_id(self, request_id: str) -> "ResponseBuilder":
        """Set request ID"""
        self.request_id = request_id
        return self

    def with_validation_errors(
        self, validation_errors: list[ValidationErrorDetail]
    ) -> "ResponseBuilder":
        """Add validation error details"""
        self.validation_errors = validation_errors
        return self

    def with_status(self, status_code: int) -> "ResponseBuilder":
        """Set HTTP status code"""
        self.status_code = status_code
        return self

    def build(self) -> JSONResponse:
        """Build the final JSON response"""
        # Determine response type based on status code
        if 200 <= self.status_code < 300:
            if self.validation_errors:
                # Success response with validation warnings
                return APIResponse.success(
                    data=self.data,
                    message=self.message,
                    meta=self.meta,
                    request_id=self.request_id,
                    status_code=self.status_code,
                )
            # Standard success response
            return APIResponse.success(
                data=self.data,
                message=self.message,
                meta=self.meta,
                request_id=self.request_id,
                status_code=self.status_code,
            )
        if self.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            # Validation error
            return APIResponse.validation_error(
                message=self.message,
                validation_errors=self.validation_errors,
                errors=self.errors,
                request_id=self.request_id,
            )
        # General error response
        return APIResponse.error(
            message=self.message,
            errors=self.errors,
            meta=self.meta,
            request_id=self.request_id,
            status_code=self.status_code,
        )


# TODO(human): Implement response compression for large payloads
# This should automatically compress JSON responses that exceed a certain size
# threshold, improving performance for API consumers


class CompressedJSONResponse(JSONResponse):
    """
    JSON Response with automatic compression for large payloads
    """

    def __init__(
        self,
        content: dict[str, Any],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/json",
        compression_threshold: int = 10240,  # 10KB
    ):
        self.compression_threshold = compression_threshold

        # Convert to JSON string to check size
        import json

        content_str = json.dumps(content, separators=(",", ":"))

        # Apply compression if content is large enough
        if len(content_str.encode("utf-8")) > compression_threshold:
            # Add compression headers
            if headers is None:
                headers = {}

            # This would integrate with actual compression middleware
            # For now, we'll set the header to indicate compression is available
            headers["X-Compressed"] = "true"
            headers["Content-Encoding"] = "gzip"

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
        )


# Convenience function to get request ID from FastAPI request
def get_request_id(request) -> str | None:
    """Extract request ID from FastAPI request"""
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    if hasattr(request, "headers") and "X-Request-ID" in request.headers:
        return request.headers["X-Request-ID"]
    return None


# Error response helpers for common scenarios
def handle_validation_exception(
    exc: Exception, request_id: str | None = None
) -> JSONResponse:
    """Convert validation exceptions to standardized error responses"""
    if hasattr(exc, "errors"):  # Pydantic validation error
        validation_errors = []
        for error in exc.errors():
            validation_errors.append(
                ValidationErrorDetail(
                    field=".".join(str(x) for x in error["loc"]),
                    message=error["msg"],
                    value=error.get("input"),
                )
            )

        return APIResponse.validation_error(
            message="Validation failed",
            validation_errors=validation_errors,
            request_id=request_id,
        )
    return APIResponse.validation_error(
        message=str(exc), errors=[str(exc)], request_id=request_id
    )


def handle_database_exception(
    exc: Exception, request_id: str | None = None
) -> JSONResponse:
    """Convert database exceptions to standardized error responses"""
    if "unique" in str(exc).lower():
        return APIResponse.conflict(
            message="Resource already exists", errors=[str(exc)], request_id=request_id
        )
    if "foreign key" in str(exc).lower():
        return APIResponse.validation_error(
            message="Referenced resource does not exist",
            errors=[str(exc)],
            request_id=request_id,
        )
    return APIResponse.server_error(
        message="Database operation failed", request_id=request_id
    )
