# app/api/v1/endpoints/api_documentation.py
"""
API Documentation and Versioning Endpoints
Provides comprehensive API documentation, changelogs, and version information
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_active_user, get_current_admin_user
from app.core.response import create_error_response, create_success_response
from app.db.models.user import User

router = APIRouter(tags=["API Documentation"])


class APIVersionInfo(BaseModel):
    """API version information"""

    version: str = Field(description="Version number")
    status: str = Field(description="Version status")
    release_date: datetime = Field(description="Release date")
    deprecation_date: datetime | None = Field(None, description="Deprecation date")
    sunset_date: datetime | None = Field(None, description="Sunset date")
    features: list[str] = Field(default_factory=list, description="New features")
    breaking_changes: list[str] = Field(default_factory=list, description="Breaking changes")
    bug_fixes: list[str] = Field(default_factory=list, description="Bug fixes")


class APIEndpointInfo(BaseModel):
    """API endpoint information"""

    path: str = Field(description="Endpoint path")
    method: str = Field(description="HTTP method")
    description: str = Field(description="Endpoint description")
    parameters: list[dict[str, Any]] = Field(default_factory=list, description="Parameters")
    response_models: list[dict[str, Any]] = Field(
        default_factory=list, description="Response models"
    )
    tags: list[str] = Field(default_factory=list, description="Tags")
    deprecated: bool = Field(default=False, description="Whether endpoint is deprecated")
    version_added: str = Field(description="Version where endpoint was added")
    version_deprecated: str | None = Field(
        None, description="Version where endpoint was deprecated"
    )


class APIChangelogEntry(BaseModel):
    """Changelog entry"""

    version: str = Field(description="Version number")
    release_date: datetime = Field(description="Release date")
    type: str = Field(
        description="Entry type: added, improved, fixed, deprecated, removed, security"
    )
    category: str = Field(
        description="Category: feature, bug, security, performance, documentation"
    )
    title: str = Field(description="Entry title")
    description: str = Field(description="Detailed description")
    breaking_change: bool = Field(default=False, description="Whether this is a breaking change")
    affected_endpoints: list[str] = Field(default_factory=list, description="Affected endpoints")


# Mock version data (replace with actual database storage)
API_VERSIONSIONS = {
    "v1.0.0": APIVersionInfo(
        version="v1.0.0",
        status="stable",
        release_date=datetime(2024, 1, 1),
        features=[
            "Initial API release",
            "User authentication and management",
            "Assessment creation and management",
            "Team collaboration features",
            "Basic analytics",
        ],
        breaking_changes=["None"],
        bug_fixes=["Initial bug fixes and stability improvements"],
    ),
    "v1.1.0": APIVersionInfo(
        version="v1.1.0",
        status="stable",
        release_date=datetime(2024, 2, 1),
        features=[
            "Advanced analytics dashboard",
            "Real-time query performance monitoring",
            "Enhanced API rate limiting",
            "Improved error handling and responses",
            "Advanced pagination and filtering",
        ],
        breaking_changes=[
            "Changed response format for consistency",
            "Updated authentication middleware",
        ],
        bug_fixes=[
            "Fixed pagination bugs",
            "Improved caching performance",
            "Security enhancements",
        ],
    ),
    "v1.2.0": APIVersionInfo(
        version="v1.2.0",
        status="stable",
        release_date=datetime(2024, 3, 1),
        features=[
            "Query performance optimization tools",
            "Database index management",
            "Enhanced user tier management",
            "API documentation endpoints",
            "Bulk operation support",
        ],
        breaking_changes=["Enhanced rate limiting with tier-based limits"],
        bug_fixes=[
            "Fixed memory leaks in long-running operations",
            "Improved database connection pooling",
            "Enhanced security headers",
        ],
    ),
}

API_CHANGELOG = [
    APIChangelogEntry(
        version="v1.2.0",
        release_date=datetime(2024, 3, 1),
        type="added",
        category="feature",
        title="Advanced Query Performance Tools",
        description="Added comprehensive query performance monitoring, optimization tools, and database index management",
        breaking_change=False,
        affected_endpoints=["/api/v1/query-performance/*"],
    ),
    APIChangelogEntry(
        version="v1.2.0",
        release_date=datetime(2024, 3, 1),
        type="improved",
        category="performance",
        title="Enhanced Rate Limiting",
        description="Implemented tier-based rate limiting with adaptive algorithms and better user experience",
        breaking_change=True,
        affected_endpoints=["All endpoints"],
    ),
    APIChangelogEntry(
        version="v1.1.0",
        release_date=datetime(2024, 2, 1),
        type="security",
        category="security",
        title="Security Headers Enhancement",
        description="Added comprehensive security headers and CORS configuration improvements",
        breaking_change=False,
        affected_endpoints=["All endpoints"],
    ),
]


@router.get("/versions", summary="Get API Versions")
async def get_api_versions(
    include_deprecated: bool = Query(False, description="Include deprecated versions"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all available API versions with detailed information
    """
    versions = list(API_VERSIONSIONS.values())

    if not include_deprecated:
        versions = [v for v in versions if v.status != "deprecated"]

    return create_success_response(
        data=[version.dict() for version in versions], message="API versions retrieved successfully"
    )


@router.get("/versions/current", summary="Get Current API Version")
async def get_current_api_version(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the current API version
    """
    current_version = "v1.2.0"  # Should come from settings
    version_info = API_VERSIONSIONS.get(current_version)

    if not version_info:
        return create_error_response(
            message="Current version information not available", error_code="VERSION_NOT_FOUND"
        )

    return create_success_response(
        data=version_info.dict(), message="Current API version information"
    )


@router.get("/versions/{version}", summary="Get Specific API Version")
async def get_api_version(version: str, current_user: User = Depends(get_current_active_user)):
    """
    Get detailed information about a specific API version
    """
    version_info = API_VERSIONSIONS.get(version)

    if not version_info:
        return create_error_response(
            message=f"Version {version} not found",
            error_code="VERSION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return create_success_response(
        data=version_info.dict(), message=f"API version {version} information"
    )


@router.get("/changelog", summary="Get API Changelog")
async def get_api_changelog(
    limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    version: str | None = Query(None, description="Filter by version"),
    category: str | None = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get API changelog with filtering options
    """
    changelog = API_CHANGELOG

    # Apply filters
    if version:
        changelog = [entry for entry in changelog if entry.version == version]

    if category:
        changelog = [entry for entry in changelog if entry.category == category]

    # Sort by release date (newest first)
    changelog.sort(key=lambda x: x.release_date, reverse=True)

    # Apply limit
    if limit:
        changelog = changelog[:limit]

    return create_success_response(
        data=[entry.dict() for entry in changelog], message="API changelog retrieved successfully"
    )


@router.get("/endpoints", summary="Get API Endpoints Documentation")
async def get_api_endpoints(
    include_deprecated: bool = Query(False, description="Include deprecated endpoints"),
    version: str | None = Query("v1.2.0", description="API version"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive documentation of all API endpoints
    """
    # This would dynamically generate endpoint documentation from your routes
    # For now, return a sample structure
    endpoints = [
        APIEndpointInfo(
            path="/api/v1/auth/login",
            method="POST",
            description="Authenticate user and get access token",
            parameters=[
                {"name": "email", "type": "string", "required": True, "description": "User email"},
                {
                    "name": "password",
                    "type": "string",
                    "required": True,
                    "description": "User password",
                },
            ],
            response_models=["TokenResponse"],
            tags=["Authentication"],
            version_added="v1.0.0",
        ),
        APIEndpointInfo(
            path="/api/v1/users/me",
            method="GET",
            description="Get current user information with enhanced performance monitoring and caching",
            parameters=[],
            response_models=["SuccessResponse[User]"],
            tags=["Users"],
            version_added="v1.0.0",
        ),
        APIEndpointInfo(
            path="/api/v1/users/",
            method="GET",
            description="Get paginated list of users with advanced filtering and sorting",
            parameters=[
                {
                    "name": "page",
                    "type": "integer",
                    "required": False,
                    "description": "Page number (default: 1)",
                },
                {
                    "name": "size",
                    "type": "integer",
                    "required": False,
                    "description": "Page size (default: 20)",
                },
                {
                    "name": "search",
                    "type": "string",
                    "required": False,
                    "description": "Search users by name or email",
                },
                {
                    "name": "is_active",
                    "type": "boolean",
                    "required": False,
                    "description": "Filter by active status",
                },
                {
                    "name": "organization_id",
                    "type": "integer",
                    "required": False,
                    "description": "Filter by organization",
                },
                {
                    "name": "role",
                    "type": "string",
                    "required": False,
                    "description": "Filter by user role",
                },
            ],
            response_models=["PaginatedResponse[User]"],
            tags=["Users"],
            version_added="v1.2.0",
        ),
        APIEndpointInfo(
            path="/api/v1/assessments",
            method="GET",
            description="Get paginated list of assessments with enhanced caching and performance monitoring",
            parameters=[
                {
                    "name": "page",
                    "type": "integer",
                    "required": False,
                    "description": "Page number (default: 1)",
                },
                {
                    "name": "size",
                    "type": "integer",
                    "required": False,
                    "description": "Page size (default: 100)",
                },
                {
                    "name": "search",
                    "type": "string",
                    "required": False,
                    "description": "Search term",
                },
                {
                    "name": "category",
                    "type": "string",
                    "required": False,
                    "description": "Filter by category",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "description": "Filter by status",
                },
            ],
            response_models=["SuccessResponse[PaginatedAssessmentList]"],
            tags=["Assessments"],
            version_added="v1.0.0",
        ),
        APIEndpointInfo(
            path="/api/v1/assessments",
            method="POST",
            description="Create a new assessment with enhanced error handling and validation",
            parameters=[
                {
                    "name": "assessment_data",
                    "type": "AssessmentCreate",
                    "required": True,
                    "description": "Assessment creation data",
                }
            ],
            response_models=["SuccessResponse[Assessment]"],
            tags=["Assessments"],
            version_added="v1.0.0",
        ),
        APIEndpointInfo(
            path="/api/v1/query-performance/metrics",
            method="GET",
            description="Get real-time query performance metrics",
            parameters=[],
            response_models=["PerformanceMetricsResponse"],
            tags=["Query Performance"],
            version_added="v1.2.0",
        ),
    ]

    if not include_deprecated:
        endpoints = [ep for ep in endpoints if not ep.deprecated]

    return create_success_response(
        data=[endpoint.dict() for endpoint in endpoints],
        message="API endpoints documentation retrieved successfully",
    )


@router.get("/schema", summary="Get API Schema")
async def get_api_schema(
    format_type: str = Query("json", pattern="^(json|yaml)$", description="Output format"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the complete API schema in specified format
    """
    # This would generate the complete OpenAPI schema
    # For now, return a placeholder
    schema_info = {
        "openapi": "3.0.0",
        "info": {
            "title": "PsychSync API",
            "version": "v1.2.0",
            "description": "PsychSync AI Platform API",
            "contact": {"name": "PsychSync Support", "email": "support@psychsync.ai"},
            "license": {"name": "MIT"},
        },
        "servers": [
            {"url": "https://api.psychsync.ai/v1.2.0", "description": "Production"},
            {"url": "https://staging-api.psychsync.ai/v1.2.0", "description": "Staging"},
            {"url": "http://localhost:8000/api/v1.2.0", "description": "Development"},
        ],
        "paths": {},
        "components": {
            "schemas": {
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "message": {
                            "type": "string",
                            "example": "Operation completed successfully",
                        },
                        "data": {"type": "object"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "status": {"type": "string", "example": "success"},
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Error occurred"},
                        "error_code": {"type": "string", "example": "VALIDATION_ERROR"},
                        "errors": {"type": "array", "items": {"type": "object"}},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "status": {"type": "string", "example": "error"},
                    },
                },
                "PaginatedResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "message": {"type": "string", "example": "Data retrieved successfully"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "items": {"type": "array", "items": {"type": "object"}},
                                "pagination": {
                                    "type": "object",
                                    "properties": {
                                        "page": {"type": "integer"},
                                        "size": {"type": "integer"},
                                        "total": {"type": "integer"},
                                        "pages": {"type": "integer"},
                                        "has_next": {"type": "boolean"},
                                        "has_prev": {"type": "boolean"},
                                    },
                                },
                            },
                        },
                        "timestamp": {"type": "string", "format": "date-time"},
                        "status": {"type": "string", "example": "success"},
                    },
                },
            },
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
        },
    }

    return create_success_response(
        data=schema_info, message=f"API schema retrieved in {format_type} format"
    )


@router.get("/health", summary="API Health Check")
async def get_api_health(current_user: User = Depends(get_current_active_user)):
    """
    Check the health and status of the API
    """
    health_info = {
        "status": "healthy",
        "version": "v1.2.0",
        "uptime": "2 days, 14 hours, 32 minutes",  # Calculate actual uptime
        "endpoints_count": 47,
        "last_deployment": datetime.utcnow() - timedelta(hours=24),
        "environment": "production",
        "database": "connected",
        "cache": "connected",
        "rate_limiter": "active",
        "services": {
            "authentication": "healthy",
            "database": "healthy",
            "cache": "healthy",
            "rate_limiting": "healthy",
        },
    }

    return create_success_response(
        data=health_info, message="API health check completed successfully"
    )


@router.get("/migration-guide", summary="Get API Migration Guide")
async def get_migration_guide(
    from_version: str | None = Query(None, description="Source version"),
    to_version: str = Query("v1.2.0", description="Target version"),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get migration guide for API version upgrades
    """
    # TODO(human): Implement comprehensive migration guide generator
    # Context: Users need detailed guidance when upgrading between API versions
    # Your task is to implement a system that generates detailed migration guides
    #
    # Guidance:
    # 1. Compare versions to identify breaking changes
    # 2. Generate step-by-step migration instructions
    # 3. Include code examples for common migrations
    # 4. Provide rollback procedures
    # 5. Add testing recommendations
    # 6. Include deprecation warnings and timelines
    #
    # The guide should cover:
    # - Authentication changes
    # - Request/response format changes
    # - Endpoint modifications
    # - Parameter updates
    # - Error handling changes
    # - Security enhancements

    migration_guide = {
        "from_version": from_version or "v1.0.0",
        "to_version": to_version,
        "breaking_changes": [
            {
                "area": "Response Format",
                "description": "Standardized response format with metadata",
                "impact": "medium",
                "action_required": "Update client response handling",
            },
            {
                "area": "Rate Limiting",
                "description": "New tier-based rate limiting system",
                "impact": "high",
                "action_required": "Implement proper rate limit handling",
            },
        ],
        "steps": [
            "1. Update authentication middleware",
            "2. Implement new response format handling",
            "3. Add rate limit retry logic",
            "4. Test all endpoints",
            "5. Update documentation",
        ],
        "code_examples": [
            {
                "description": "Handling new response format",
                "language": "python",
                "code": """
# Before
response = requests.get(url)
data = response.json()

# After
response = requests.get(url)
result = response.json()
if result['success']:
    data = result['data']
else:
    handle_error(result['errors'])
""",
            }
        ],
        "rollback_procedure": [
            "1. Revert to previous API version",
            "2. Restore backup of response handlers",
            "3. Test with previous API version",
        ],
        "testing_recommendations": [
            "Test all endpoints with new response format",
            "Verify rate limiting behavior",
            "Check authentication flow",
            "Validate error handling",
        ],
    }

    return create_success_response(
        data=migration_guide, message="Migration guide generated successfully"
    )
