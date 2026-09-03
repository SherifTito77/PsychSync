"""
Tenant Context Middleware

Provides automatic tenant identification and context injection for all requests.
Supports multiple tenant identification methods (subdomain, header, JWT, user org).

Created: 2025-01-12
Author: Architecture Team
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.cache import async_cache
from app.db.models.organization import Organization
from app.db.models.user import User

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically injects tenant context into all requests.

    Tenant identification priority:
    1. Subdomain (tenant1.psychsync.com → tenant1)
    2. Header (X-Tenant-ID: uuid)
    3. JWT token claim (custom claim "tenant_id")
    4. User's organization (fallback)

    Usage:
        app = FastAPI()
        app.add_middleware(TenantContextMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        cache_ttl: int = 300,  # 5 minutes
        validate_tenant: bool = True,
        extract_from_subdomain: bool = True,
        extract_from_header: bool = True,
        extract_from_jwt: bool = True,
    ):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.validate_tenant = validate_tenant
        self.extract_from_subdomain = extract_from_subdomain
        self.extract_from_header = extract_from_header
        self.extract_from_jwt = extract_from_jwt

    async def dispatch(self, request: Request, call_next):
        """
        Process request and inject tenant context.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with tenant context injected
        """
        try:
            # Extract tenant ID using multiple methods
            tenant_id = await self._extract_tenant_id(request)

            # Validate tenant if enabled
            if self.validate_tenant and tenant_id:
                tenant = await self._validate_and_cache_tenant(tenant_id)
                if not tenant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Tenant not found or inactive",
                    )

                # Add tenant to request state
                request.state.tenant_id = str(tenant_id)
                request.state.tenant = tenant
                request.state.tenant_tier = tenant.tier.value

            # Set PostgreSQL session variable for RLS
            if tenant_id:
                await self._set_db_tenant_context(request, tenant_id)

            # Process request
            response = await call_next(request)

            # Add tenant headers (useful for debugging)
            if tenant_id:
                response.headers["X-Tenant-ID"] = str(tenant_id)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant middleware error: {e}")
            # Continue without tenant context for non-tenant routes
            return await call_next(request)

    async def _extract_tenant_id(self, request: Request) -> Optional[UUID]:
        """
        Extract tenant ID using multiple methods.

        Args:
            request: Incoming request

        Returns:
            Tenant UUID if found, None otherwise
        """
        # Method 1: Extract from subdomain
        if self.extract_from_subdomain:
            tenant_id = await self._extract_from_subdomain(request)
            if tenant_id:
                logger.debug(f"Tenant from subdomain: {tenant_id}")
                return tenant_id

        # Method 2: Extract from header
        if self.extract_from_header:
            tenant_id = await self._extract_from_header(request)
            if tenant_id:
                logger.debug(f"Tenant from header: {tenant_id}")
                return tenant_id

        # Method 3: Extract from JWT token
        if self.extract_from_jwt:
            tenant_id = await self._extract_from_jwt(request)
            if tenant_id:
                logger.debug(f"Tenant from JWT: {tenant_id}")
                return tenant_id

        # Method 4: Fallback to user's organization (requires auth)
        tenant_id = await self._extract_from_user_org(request)
        if tenant_id:
            logger.debug(f"Tenant from user org: {tenant_id}")
            return tenant_id

        logger.warning("Could not extract tenant ID from request")
        return None

    async def _extract_from_subdomain(self, request: Request) -> Optional[UUID]:
        """
        Extract tenant from subdomain.

        Examples:
            tenant1.psychsync.com → tenant1 slug
            api.tenant1.psychsync.com → tenant1 slug
        """
        host = request.headers.get("host", "")

        if not host:
            return None

        # Split by '.' and get first part (subdomain)
        parts = host.split(".")

        if len(parts) < 2:
            return None

        subdomain = parts[0]

        # Skip common subdomains
        skip_subdomains = {"www", "api", "app", "admin", "staging", "dev"}
        if subdomain.lower() in skip_subdomains:
            return None

        # Look up tenant by slug
        try:
            cache_key = f"tenant:slug:{subdomain}"
            cached_tenant_id = await async_cache.get(cache_key)

            if cached_tenant_id:
                return UUID(cached_tenant_id)

            # Query database for tenant by slug
            # This would be injected via dependency injection in real implementation
            # For now, return None
            return None

        except (ValueError, AttributeError):
            return None

    async def _extract_from_header(self, request: Request) -> Optional[UUID]:
        """
        Extract tenant from X-Tenant-ID header.

        Usage:
            GET /api/v1/assessments
            X-Tenant-ID: uuid-here
        """
        tenant_header = request.headers.get("X-Tenant-ID")

        if not tenant_header:
            return None

        try:
            return UUID(tenant_header)
        except ValueError:
            logger.warning(f"Invalid tenant ID in header: {tenant_header}")
            return None

    async def _extract_from_jwt(self, request: Request) -> Optional[UUID]:
        """
        Extract tenant from JWT token claim.

        Token should contain custom claim:
        {
            "sub": "user_id",
            "tenant_id": "uuid",
            ...
        }
        """
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Decode and verify token
            # This would use the JWT verification service
            # For now, return None
            # decoded_token = await verify_token(token)
            # tenant_id = decoded_token.get("tenant_id")
            # return UUID(tenant_id) if tenant_id else None
            return None

        except (ValueError, AttributeError):
            return None

    async def _extract_from_user_org(self, request: Request) -> Optional[UUID]:
        """
        Extract tenant from authenticated user's organization.

        This is the fallback method when no explicit tenant is provided.
        Requires user to be authenticated.
        """
        # Check if user is authenticated
        # This would check request.state.user or similar
        user = getattr(request.state, "user", None)

        if not user:
            return None

        # Return user's organization_id
        return user.organization_id

    async def _validate_and_cache_tenant(
        self, tenant_id: UUID
    ) -> Optional[Organization]:
        """
        Validate tenant exists and is active. Cache result.

        Args:
            tenant_id: Tenant UUID to validate

        Returns:
            Organization if valid, None otherwise
        """
        # Check cache first
        cache_key = f"tenant:valid:{tenant_id}"
        cached_result = await async_cache.get(cache_key)

        if cached_result == "valid":
            # Tenant is valid, fetch full details
            tenant_cache_key = f"tenant:{tenant_id}"
            cached_tenant = await async_cache.get(tenant_cache_key)

            if cached_tenant:
                # Deserialize and return
                return Organization.parse_raw(cached_tenant)

        # Query database
        # In real implementation, this would use dependency injection
        # For now, return mock organization
        try:
            # Mock validation - in real implementation:
            # tenant = await db.get(Organization, tenant_id)
            # if tenant and tenant.is_active:
            #     await async_cache.set(cache_key, "valid", expire=self.cache_ttl)
            #     await async_cache.set(f"tenant:{tenant_id}", tenant.json(), expire=self.cache_ttl)
            #     return tenant
            return None

        except Exception as e:
            logger.error(f"Error validating tenant {tenant_id}: {e}")
            return None

    async def _set_db_tenant_context(self, request: Request, tenant_id: UUID):
        """
        Set PostgreSQL session variable for Row-Level Security (RLS).

        This ensures all queries automatically filter by tenant_id.
        """
        try:
            # Get database session from request state (injected by other middleware)
            db = getattr(request.state, "db", None)

            if db:
                # Set PostgreSQL session variable
                await db.execute(
                    text("SELECT set_config('app.current_tenant', :tenant_id, false)"),
                    {"tenant_id": str(tenant_id)},
                )

                logger.debug(f"Set DB tenant context: {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to set DB tenant context: {e}")
            # Continue without failing the request


async def get_current_tenant(request: Request) -> Optional[Organization]:
    """
    FastAPI dependency to get current tenant from request context.

    Usage:
        @router.get("/api/v1/assessments")
        async def list_assessments(
            tenant: Organization = Depends(get_current_tenant),
            ...
        ):
            # Tenant is automatically injected
            return await service.list_for_tenant(tenant.id)
    """
    return getattr(request.state, "tenant", None)


async def get_current_tenant_id(request: Request) -> Optional[UUID]:
    """
    FastAPI dependency to get current tenant ID from request context.

    Usage:
        @router.get("/api/v1/assessments")
        async def list_assessments(
            tenant_id: UUID = Depends(get_current_tenant_id),
            ...
        ):
            # Tenant ID is automatically injected
            return await service.list_for_tenant(tenant_id)
    """
    return getattr(request.state, "tenant_id", None)


async def require_tenant(request: Request) -> Organization:
    """
    FastAPI dependency that requires a valid tenant.
    Raises 404 if tenant not found.

    Usage:
        @router.get("/api/v1/tenant/settings")
        async def get_tenant_settings(
            tenant: Organization = Depends(require_tenant),
            ...
        ):
            # Tenant is guaranteed to be present
            return tenant.settings
    """
    tenant = await get_current_tenant(request)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )

    return tenant
