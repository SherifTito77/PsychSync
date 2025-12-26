# app/core/api_key_auth.py
"""
API Key Authentication System for Service-to-Service Communication
- Secure API key generation and validation
- Rate limiting per API key
- Usage tracking and analytics
- Key revocation and expiration
"""

import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import HTTPException, status, Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.config import settings
from app.core.enhanced_cache import get_cache_manager

class APIKeyPermission(Enum):
    """API key permission levels"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    FULL_ACCESS = "full_access"

class APIKeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"

class APIKey:
    """
    API Key management class
    """

    @staticmethod
    def generate_key(prefix: str = "psync", length: int = 32) -> str:
        """
        Generate a secure API key

        Args:
            prefix: Key prefix for identification
            length: Length of random portion

        Returns:
            Secure API key string
        """
        random_bytes = secrets.token_bytes(length)
        key = random_bytes.hex()
        return f"{prefix}_{key}"

    @staticmethod
    def hash_key(api_key: str) -> str:
        """
        Hash API key for secure storage

        Args:
            api_key: Plain API key

        Returns:
            Hashed API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def verify_key(plain_key: str, hashed_key: str) -> bool:
        """
        Verify API key against hash

        Args:
            plain_key: Plain API key to verify
            hashed_key: Hashed key to verify against

        Returns:
            True if key matches
        """
        return APIKey.hash_key(plain_key) == hashed_key


class APIKeyManager:
    """
    API Key management with Redis caching
    """

    def __init__(self, cache_manager=None):
        self.cache = cache_manager or get_cache_manager()
        self.key_prefix = "api_key:"
        self.usage_prefix = "api_usage:"

    async def create_api_key(
        self,
        name: str,
        permissions: List[APIKeyPermission],
        expires_at: Optional[datetime] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key

        Args:
            name: Key name/description
            permissions: List of permissions
            expires_at: Optional expiration date
            rate_limit: Optional rate limit per hour
            metadata: Additional metadata

        Returns:
            API key information (including plain key - only shown once)
        """
        # Generate API key
        api_key = APIKey.generate_key()
        key_id = secrets.token_urlsafe(16)
        hashed_key = APIKey.hash_key(api_key)

        # Prepare key data
        key_data = {
            "key_id": key_id,
            "name": name,
            "hashed_key": hashed_key,
            "permissions": [p.value for p in permissions],
            "status": APIKeyStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "rate_limit": rate_limit or 1000,  # Default 1000 requests per hour
            "last_used": None,
            "usage_count": 0,
            "metadata": metadata or {}
        }

        # Cache the key data
        cache_key = f"{self.key_prefix}{key_id}"
        if self.cache:
            await self.cache.set(cache_key, key_data, ttl=86400 * 30)  # 30 days

        return {
            "key_id": key_id,
            "api_key": api_key,  # Only returned once
            "name": name,
            "permissions": [p.value for p in permissions],
            "expires_at": expires_at.isoformat() if expires_at else None,
            "rate_limit": rate_limit or 1000,
            "created_at": key_data["created_at"]
        }

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return key information

        Args:
            api_key: Plain API key to validate

        Returns:
            Key information if valid, None otherwise
        """
        if not api_key:
            return None

        hashed_key = APIKey.hash_key(api_key)

        # Try to find the key in cache
        if self.cache:
            # Search through all API keys (this is inefficient, in production use a reverse index)
            # For now, we'll implement a simple lookup by caching a reverse mapping
            reverse_key = f"{self.key_prefix}reverse:{hashed_key}"
            key_id = await self.cache.get(reverse_key)

            if key_id:
                cache_key = f"{self.key_prefix}{key_id}"
                key_data = await self.cache.get(cache_key)

                if key_data:
                    # Check if key is still valid
                    if await self._is_key_valid(key_data):
                        await self._update_key_usage(key_id, key_data)
                        return key_data
                    else:
                        # Key is invalid, remove from cache
                        await self.cache.delete(cache_key)
                        await self.cache.delete(reverse_key)

        return None

    async def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key

        Args:
            key_id: Key ID to revoke

        Returns:
            True if revoked successfully
        """
        if not self.cache:
            return False

        cache_key = f"{self.key_prefix}{key_id}"
        key_data = await self.cache.get(cache_key)

        if key_data:
            key_data["status"] = APIKeyStatus.REVOKED.value
            key_data["revoked_at"] = datetime.utcnow().isoformat()
            await self.cache.set(cache_key, key_data, ttl=86400 * 30)

            # Remove reverse mapping
            reverse_key = f"{self.key_prefix}reverse:{key_data['hashed_key']}"
            await self.cache.delete(reverse_key)

            return True

        return False

    async def get_key_usage(self, key_id: str, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get API key usage statistics

        Args:
            key_id: Key ID
            time_range: Time range for stats (1h, 24h, 7d, 30d)

        Returns:
            Usage statistics
        """
        if not self.cache:
            return {}

        usage_key = f"{self.usage_prefix}{key_id}:{time_range}"
        usage_data = await self.cache.get(usage_key)

        if not usage_data:
            usage_data = {
                "request_count": 0,
                "last_request": None,
                "endpoints": {},
                "status_codes": {},
                "errors": 0
            }

        return usage_data

    async def _is_key_valid(self, key_data: Dict[str, Any]) -> bool:
        """Check if API key is still valid"""
        # Check status
        if key_data.get("status") != APIKeyStatus.ACTIVE.value:
            return False

        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at:
            try:
                expire_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.utcnow() > expire_date:
                    return False
            except:
                pass

        return True

    async def _update_key_usage(self, key_id: str, key_data: Dict[str, Any]):
        """Update key usage statistics"""
        if not self.cache:
            return

        # Update last used and usage count
        key_data["last_used"] = datetime.utcnow().isoformat()
        key_data["usage_count"] = key_data.get("usage_count", 0) + 1

        # Save updated key data
        cache_key = f"{self.key_prefix}{key_id}"
        await self.cache.set(cache_key, key_data, ttl=86400 * 30)

        # Update usage statistics
        usage_key = f"{self.usage_prefix}{key_id}:1h"
        current_usage = await self.cache.get(usage_key) or {
            "request_count": 0,
            "last_request": None,
            "endpoints": {},
            "status_codes": {},
            "errors": 0
        }

        current_usage["request_count"] += 1
        current_usage["last_request"] = datetime.utcnow().isoformat()

        await self.cache.set(usage_key, current_usage, ttl=3600)  # 1 hour TTL

        # Create reverse mapping for faster lookups
        reverse_key = f"{self.key_prefix}reverse:{key_data['hashed_key']}"
        await self.cache.set(reverse_key, key_id, ttl=86400 * 30)


# FastAPI dependencies
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_api_key_manager: Optional[APIKeyManager] = None

def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


async def verify_api_key(
    api_key: str = Security(api_key_header)
) -> Dict[str, Any]:
    """
    FastAPI dependency to verify API key

    Args:
        api_key: API key from header

    Returns:
        API key data

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    manager = get_api_key_manager()
    key_data = await manager.validate_api_key(api_key)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key_data


async def verify_api_key_permission(
    required_permission: APIKeyPermission
):
    """
    FastAPI dependency factory for specific permission requirements

    Args:
        required_permission: Required permission level

    Returns:
        Dependency function
    """
    async def permission_dependency(
        api_key_data: Dict[str, Any] = Depends(verify_api_key)
    ) -> Dict[str, Any]:
        permissions = api_key_data.get("permissions", [])

        # Check if user has required permission or higher
        permission_hierarchy = [
            APIKeyPermission.READ,
            APIKeyPermission.WRITE,
            APIKeyPermission.ADMIN,
            APIKeyPermission.FULL_ACCESS
        ]

        required_level = permission_hierarchy.index(required_permission)
        user_level = max([
            permission_hierarchy.index(APIKeyPermission(p))
            for p in permissions
            if p in [perm.value for perm in permission_hierarchy]
        ]) if permissions else -1

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}"
            )

        return api_key_data

    return permission_dependency


# Predefined permission dependencies
verify_read_api_key = verify_api_key_permission(APIKeyPermission.READ)
verify_write_api_key = verify_api_key_permission(APIKeyPermission.WRITE)
verify_admin_api_key = verify_api_key_permission(APIKeyPermission.ADMIN)
verify_full_access_api_key = verify_api_key_permission(APIKeyPermission.FULL_ACCESS)


# Rate limiting middleware for API keys
class APIKeyRateLimiter:
    """Rate limiter specifically for API keys"""

    def __init__(self, cache_manager=None):
        self.cache = cache_manager or get_cache_manager()
        self.rate_limit_prefix = "api_rate_limit:"

    async def check_rate_limit(
        self,
        key_id: str,
        limit: int,
        window: int = 3600  # 1 hour
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if API key is within rate limit

        Args:
            key_id: API key identifier
            limit: Request limit
            window: Time window in seconds

        Returns:
            (allowed, info_dict)
        """
        if not self.cache:
            return True, {"remaining": limit - 1, "reset_time": time.time() + window}

        rate_limit_key = f"{self.rate_limit_prefix}{key_id}"
        current_time = int(time.time())
        window_start = current_time - window

        # Use Redis sorted set for sliding window
        try:
            # Remove old entries
            await self.cache.redis.zremrangebyscore(rate_limit_key, 0, window_start)

            # Count current requests
            current_requests = await self.cache.redis.zcard(rate_limit_key)

            if current_requests >= limit:
                # Get oldest request for reset time
                oldest = await self.cache.redis.zrange(rate_limit_key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1]) + window if oldest else current_time + window

                return False, {
                    "remaining": 0,
                    "reset_time": reset_time,
                    "limit": limit,
                    "current": current_requests
                }

            # Add current request
            await self.cache.redis.zadd(rate_limit_key, {str(current_time): current_time})
            await self.cache.redis.expire(rate_limit_key, window)

            remaining = limit - current_requests - 1
            reset_time = current_time + window

            return True, {
                "remaining": max(0, remaining),
                "reset_time": reset_time,
                "limit": limit,
                "current": current_requests + 1
            }

        except Exception as e:
            # Fail open if rate limiter fails
            return True, {"remaining": limit - 1, "reset_time": time.time() + window}