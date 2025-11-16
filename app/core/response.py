# app/core/response.py
"""
Standardized API response formats for consistent client experience
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool = Field(description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Optional message about the operation")
    data: Optional[T] = Field(None, description="Response data payload")
    error_code: Optional[str] = Field(None, description="Error code if unsuccessful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class SuccessResponse(APIResponse[T]):
    """Successful response"""
    def __init__(self, data: T = None, message: str = "Operation successful", **kwargs):
        super().__init__(success=True, data=data, message=message, **kwargs)

class ErrorResponse(APIResponse[T]):
    """Error response"""
    def __init__(self, message: str, error_code: str = None, data: T = None, **kwargs):
        super().__init__(success=False, message=message, error_code=error_code, data=data, **kwargs)

class PaginatedResponse(APIResponse[T]):
    """Paginated response wrapper"""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Page size")
    pages: int = Field(description="Total number of pages")

    def __init__(self, data: list[T], total: int, page: int = 1, size: int = 100, **kwargs):
        pages = (total + size - 1) // size if size > 0 else 0
        super().__init__(
            success=True,
            data=data,
            total=total,
            page=page,
            size=size,
            pages=pages,
            **kwargs
        )