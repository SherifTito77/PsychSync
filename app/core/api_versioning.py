# app/core/api_versioning.py
"""
Comprehensive API Versioning System
Supports multiple versioning strategies:
- URL path versioning (/api/v1/, /api/v2/)
- Header-based versioning (Accept: application/vnd.psychsync.v1+json)
- Query parameter versioning (?version=1)
- Custom version negotiation and deprecation policies
"""

import re
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.routing import APIRoute


class APIVersioningStrategy(Enum):
    """API versioning strategies"""

    URL_PATH = "url_path"  # /api/v1/, /api/v2/
    HEADER = "header"  # Accept: application/vnd.psychsync.v1+json
    QUERY_PARAM = "query_param"  # ?version=1
    CUSTOM_HEADER = "custom_header"  # X-API-Version: 1


class APIVersionStatus(Enum):
    """API version status"""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    BETA = "beta"
    ALPHA = "alpha"


class APIVersion:
    """API version configuration"""

    def __init__(
        self,
        version: str,
        status: APIVersionStatus = APIVersionStatus.ACTIVE,
        deprecation_date: datetime | None = None,
        sunset_date: datetime | None = None,
        description: str = "",
        supported_strategies: list[APIVersioningStrategy] = None,
        custom_headers: dict[str, str] = None,
        migration_guide: str | None = None,
        breaking_changes: list[str] = None,
    ):
        self.version = version
        self.status = status
        self.deprecation_date = deprecation_date
        self.sunset_date = sunset_date
        self.description = description
        self.supported_strategies = supported_strategies or [
            APIVersioningStrategy.URL_PATH
        ]
        self.custom_headers = custom_headers or {}
        self.migration_guide = migration_guide
        self.breaking_changes = breaking_changes or []
        self.created_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if version is still active"""
        return self.status == APIVersionStatus.ACTIVE

    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        if self.status == APIVersionStatus.DEPRECATED:
            return True
        if self.deprecation_date and datetime.utcnow() >= self.deprecation_date:
            return True
        return False

    def is_sunset(self) -> bool:
        """Check if version is sunset (no longer supported)"""
        if self.status == APIVersionStatus.SUNSET:
            return True
        if self.sunset_date and datetime.utcnow() >= self.sunset_date:
            return True
        return False

    def get_warning_headers(self) -> dict[str, str]:
        """Get warning headers for deprecated/sunset versions"""
        headers = {}

        if self.is_deprecated():
            headers["Deprecation"] = "true"
            if self.sunset_date:
                headers["Sunset"] = self.sunset_date.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            if self.migration_guide:
                headers["Link"] = f'<{self.migration_guide}>; rel="deprecation"'

        if self.is_sunset():
            headers["Sunset"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        return headers


class APIVersionManager:
    """Manages API versions and version negotiation"""

    def __init__(self):
        self.versions: dict[str, APIVersion] = {}
        self.default_version = "1"
        self.supported_versions = ["1"]
        self.version_strategies = {
            APIVersioningStrategy.URL_PATH: self._extract_from_url,
            APIVersioningStrategy.HEADER: self._extract_from_header,
            APIVersioningStrategy.QUERY_PARAM: self._extract_from_query,
            APIVersioningStrategy.CUSTOM_HEADER: self._extract_from_custom_header,
        }

        # Initialize with default version
        self.register_version(
            APIVersion(
                version="1",
                status=APIVersionStatus.ACTIVE,
                description="Initial stable API version",
                supported_strategies=[
                    APIVersioningStrategy.URL_PATH,
                    APIVersioningStrategy.HEADER,
                    APIVersioningStrategy.QUERY_PARAM,
                ],
            )
        )

    def register_version(self, version: APIVersion) -> None:
        """Register a new API version"""
        self.versions[version.version] = version
        if version.is_active() and version.version not in self.supported_versions:
            self.supported_versions.append(version.version)

    def get_version(self, version: str) -> APIVersion | None:
        """Get version configuration"""
        return self.versions.get(version)

    def negotiate_version(
        self, request: Request, preferred_strategies: list[APIVersioningStrategy] = None
    ) -> str:
        """
        Negotiate API version based on request

        Args:
            request: FastAPI request object
            preferred_strategies: Preferred versioning strategies in order

        Returns:
            Negotiated version string
        """
        preferred_strategies = preferred_strategies or list(APIVersioningStrategy)

        for strategy in preferred_strategies:
            if strategy not in self.version_strategies:
                continue

            version = self.version_strategies[strategy](request)
            if version and version in self.supported_versions:
                return version

        # Fallback to default version
        return self.default_version

    def _extract_from_url(self, request: Request) -> str | None:
        """Extract version from URL path (/api/v1/ -> 1)"""
        path = request.url.path
        # Match patterns like /api/v1/, /api/v2/, etc.
        match = re.search(r"/api/v(\d+)/", path)
        if match:
            return match.group(1)
        return None

    def _extract_from_header(self, request: Request) -> str | None:
        """Extract version from Accept header"""
        accept_header = request.headers.get("accept", "")
        # Look for patterns like application/vnd.psychsync.v1+json
        match = re.search(r"application/vnd\.psychsync\.v(\d+)\+json", accept_header)
        if match:
            return match.group(1)
        return None

    def _extract_from_query(self, request: Request) -> str | None:
        """Extract version from query parameter"""
        return request.query_params.get("version")

    def _extract_from_custom_header(self, request: Request) -> str | None:
        """Extract version from X-API-Version header"""
        return request.headers.get("x-api-version")

    def validate_version(self, version: str) -> bool:
        """Validate if version is supported and active"""
        if version not in self.supported_versions:
            return False

        version_config = self.get_version(version)
        if not version_config:
            return False

        # Check if version is sunset
        if version_config.is_sunset():
            return False

        return True

    def get_version_info(self, version: str) -> dict[str, Any]:
        """Get comprehensive version information"""
        version_config = self.get_version(version)
        if not version_config:
            raise ValueError(f"Version {version} not found")

        return {
            "version": version_config.version,
            "status": version_config.status.value,
            "description": version_config.description,
            "supported_strategies": [
                s.value for s in version_config.supported_strategies
            ],
            "deprecation_date": (
                version_config.deprecation_date.isoformat()
                if version_config.deprecation_date
                else None
            ),
            "sunset_date": (
                version_config.sunset_date.isoformat()
                if version_config.sunset_date
                else None
            ),
            "created_at": version_config.created_at.isoformat(),
            "breaking_changes": version_config.breaking_changes,
            "migration_guide": version_config.migration_guide,
        }

    def list_versions(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        """List all versions"""
        versions = []
        for version in self.versions.values():
            if not include_inactive and version.is_sunset():
                continue
            versions.append(self.get_version_info(version.version))

        return sorted(versions, key=lambda x: int(x["version"]), reverse=True)


# Global version manager
_version_manager: APIVersionManager | None = None


def get_version_manager() -> APIVersionManager:
    """Get global version manager instance"""
    global _version_manager
    if _version_manager is None:
        _version_manager = APIVersionManager()
    return _version_manager


class VersionedAPIRoute(APIRoute):
    """Custom API route that supports versioning"""

    def __init__(
        self,
        *args,
        version: str | None = None,
        version_from: APIVersioningStrategy = APIVersioningStrategy.URL_PATH,
        deprecated: bool = False,
        deprecation_message: str | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.version = version
        self.version_from = version_from
        self.deprecated = deprecated
        self.deprecation_message = deprecation_message

    def get_route_handler(self) -> Callable:
        """Get route handler with version support"""
        original_route_handler = super().get_route_handler()

        async def versioned_route_handler(request: Request) -> Response:
            # Negotiate version
            version_manager = get_version_manager()
            negotiated_version = version_manager.negotiate_version(
                request, [self.version_from]
            )

            # Add version info to request state
            request.state.api_version = negotiated_version
            request.state.version_strategy = self.version_from.value

            # Validate version
            if not version_manager.validate_version(negotiated_version):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"API version {negotiated_version} is not supported",
                )

            # Get version configuration
            version_config = version_manager.get_version(negotiated_version)

            # Call original handler
            response = await original_route_handler(request)

            # Add version headers
            response.headers["API-Version"] = negotiated_version
            response.headers["API-Version-Status"] = version_config.status.value

            # Add deprecation/sunset headers
            warning_headers = version_config.get_warning_headers()
            for header, value in warning_headers.items():
                response.headers[header] = value

            # Add custom headers for this version
            for header, value in version_config.custom_headers.items():
                response.headers[header] = value

            # Add deprecation warning if route is deprecated
            if self.deprecated:
                response.headers["Deprecated"] = "true"
                if self.deprecation_message:
                    response.headers["Deprecation-Message"] = self.deprecation_message

            return response

        return versioned_route_handler


# FastAPI dependencies
async def get_api_version(request: Request) -> str:
    """Get negotiated API version from request"""
    return getattr(request.state, "api_version", "1")


async def get_version_info(version: str = Depends(get_api_version)) -> dict[str, Any]:
    """Get version information for current request"""
    version_manager = get_version_manager()
    return version_manager.get_version_info(version)


# Version decorators
def api_version(
    version: str,
    strategy: APIVersioningStrategy = APIVersioningStrategy.URL_PATH,
    deprecated: bool = False,
    deprecation_message: str | None = None,
):
    """
    Decorator for API versioning endpoints

    Args:
        version: API version string
        strategy: Versioning strategy
        deprecated: Whether this endpoint is deprecated
        deprecation_message: Custom deprecation message
    """

    def decorator(func):
        # Add version metadata to function
        func._api_version = version
        func._version_strategy = strategy
        func._deprecated = deprecated
        func._deprecation_message = deprecation_message
        return func

    return decorator


def versioned_response(
    version_mapping: dict[str, Any], default_version: str | None = None
):
    """
    Decorator for versioned responses

    Args:
        version_mapping: Mapping of version -> response handler/serializer
        default_version: Default version if negotiation fails
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract version from request state
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                return await func(*args, **kwargs)

            api_version = getattr(request.state, "api_version", default_version or "1")

            # Get appropriate response handler for version
            if api_version in version_mapping:
                response_handler = version_mapping[api_version]
                if callable(response_handler):
                    result = await func(*args, **kwargs)
                    return response_handler(result)
                return version_mapping[api_version]

            # Fallback to default version or original function
            if default_version and default_version in version_mapping:
                return version_mapping[default_version]

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Version middleware
class APIVersionMiddleware:
    """Middleware for API version management"""

    def __init__(self, version_manager: APIVersionManager = None):
        self.version_manager = version_manager or get_version_manager()

    async def __call__(self, request: Request, call_next):
        # Negotiate version
        version = self.version_manager.negotiate_version(request)
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers if not already added
        if "API-Version" not in response.headers:
            response.headers["API-Version"] = version
            version_config = self.version_manager.get_version(version)
            response.headers["API-Version-Status"] = version_config.status.value

        return response


# Initialize default versions
def setup_api_versions():
    """Setup default API versions"""
    manager = get_version_manager()

    # Register version 2 (future version example)
    manager.register_version(
        APIVersion(
            version="2",
            status=APIVersionStatus.BETA,
            description="Enhanced API with improved performance and new features",
            deprecation_date=None,
            sunset_date=None,
            breaking_changes=[
                "Changed response format for user profiles",
                "Updated authentication flow",
                "Modified pagination structure",
            ],
            migration_guide="https://docs.psychsync.com/api/v2/migration",
        )
    )
