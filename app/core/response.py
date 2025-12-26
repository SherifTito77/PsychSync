# app/core/response.py
"""
Enhanced Standardized API response formats for consistent client experience
Includes comprehensive error handling, pagination, and metadata
"""

from typing import Any, Optional, Generic, TypeVar, List, Dict, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class ResponseStatus(str, Enum):
    """Standard response status codes"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"

class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    value: Optional[Any] = Field(None, description="Value that caused the error")

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, le=1000, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether next page exists")
    has_prev: bool = Field(description="Whether previous page exists")

    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        size = values.get('size', 10)
        return (total + size - 1) // size if size > 0 else 0

    @validator('has_next', always=True)
    def calculate_has_next(cls, v, values):
        page = values.get('page', 1)
        pages = values.get('pages', 0)
        return page < pages

    @validator('has_prev', always=True)
    def calculate_has_prev(cls, v, values):
        page = values.get('page', 1)
        return page > 1

class FilterMeta(BaseModel):
    """Filtering metadata"""
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
    available_filters: Dict[str, Any] = Field(default_factory=dict)
    sort_by: Optional[str] = Field(None, description="Current sort field")
    sort_order: Optional[str] = Field(None, description="Current sort order (asc/desc)")

class ResponseMeta(BaseModel):
    """Response metadata"""
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="v1", description="API version")
    pagination: Optional[PaginationMeta] = None
    filters: Optional[FilterMeta] = None
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")

class APIResponse(BaseModel, Generic[T]):
    """Enhanced standard API response wrapper"""
    success: bool = Field(description="Whether the request was successful")
    status: ResponseStatus = Field(description="Response status")
    message: Optional[str] = Field(None, description="Human-readable message")
    data: Optional[T] = Field(None, description="Response data payload")
    errors: List[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SuccessResponse(APIResponse[T]):
    """Successful response with automatic status"""

    def __init__(self, data: T = None, message: str = "Operation successful",
                 meta: Optional[ResponseMeta] = None, **kwargs):
        super().__init__(
            success=True,
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta or ResponseMeta(),
            **kwargs
        )

class ErrorResponse(APIResponse[T]):
    """Error response with detailed error information"""

    def __init__(self, message: str, status: ResponseStatus = ResponseStatus.ERROR,
                 error_code: str = None, errors: List[ErrorDetail] = None,
                 meta: Optional[ResponseMeta] = None, **kwargs):
        if not errors:
            errors = [ErrorDetail(code=error_code or "UNKNOWN", message=message)]

        super().__init__(
            success=False,
            status=status,
            message=message,
            errors=errors,
            meta=meta or ResponseMeta(),
            **kwargs
        )

class ValidationErrorResponse(ErrorResponse[T]):
    """Validation error response"""

    def __init__(self, errors: List[ErrorDetail], message: str = "Validation failed"):
        super().__init__(
            message=message,
            status=ResponseStatus.VALIDATION_ERROR,
            errors=errors
        )

class PaginatedResponse(APIResponse[List[T]]):
    """Enhanced paginated response"""
    pagination: PaginationMeta = Field(..., description="Pagination information")

    def __init__(self, data: List[T], pagination: PaginationMeta,
                 message: str = "Data retrieved successfully", **kwargs):
        meta = ResponseMeta(pagination=pagination)
        super().__init__(
            success=True,
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta,
            **kwargs
        )

# Response factory functions for easy creation
def create_success_response(
    data: T = None,
    message: str = "Operation successful",
    meta: Optional[ResponseMeta] = None
) -> SuccessResponse[T]:
    """Create a success response"""
    return SuccessResponse(data=data, message=message, meta=meta)

def create_error_response(
    message: str,
    status: ResponseStatus = ResponseStatus.ERROR,
    error_code: str = None,
    errors: List[ErrorDetail] = None,
    meta: Optional[ResponseMeta] = None
) -> ErrorResponse[T]:
    """Create an error response"""
    return ErrorResponse(
        message=message,
        status=status,
        error_code=error_code,
        errors=errors,
        meta=meta
    )

def create_paginated_response(
    data: List[T],
    page: int,
    size: int,
    total: int,
    message: str = "Data retrieved successfully",
    filters: Optional[FilterMeta] = None
) -> PaginatedResponse[T]:
    """Create a paginated response"""
    pagination = PaginationMeta(page=page, size=size, total=total)
    meta = ResponseMeta(pagination=pagination, filters=filters)
    return PaginatedResponse(data=data, pagination=pagination, message=message)