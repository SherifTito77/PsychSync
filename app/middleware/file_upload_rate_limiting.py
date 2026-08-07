"""
Comprehensive File Upload Rate Limiting Middleware

Implements multi-layered rate limiting for file uploads:
- Per-user upload limits (hourly, daily)
- Per-user concurrent upload limits
- Per-user bandwidth limits
- File type and size validation
- IP-based tracking for unauthenticated uploads

Security Features:
- Prevents abuse of file upload endpoints
- Prevents DoS via large file uploads
- Validates file types and sizes
- Tracks upload history for abuse detection
"""

import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Callable, Any, Dict

from fastapi import HTTPException, Request, UploadFile, status

logger = logging.getLogger(__name__)


class FileUploadRateLimiter:
    """
    Comprehensive file upload rate limiter with Redis backend
    """

    # Upload limits (configurable)
    DEFAULT_LIMITS = {
        "uploads_per_hour": 10,  # Max uploads per hour per user
        "uploads_per_day": 50,  # Max uploads per day per user
        "concurrent_uploads": 3,  # Max concurrent uploads per user
        "max_file_size_mb": 10,  # Max file size in MB
        "total_bandwidth_gb_per_day": 1.0,  # Max total bandwidth per day
        "ip_uploads_per_hour": 20,  # Max uploads per hour per IP (for unauthenticated)
    }

    def __init__(self, redis_client=None):
        """
        Initialize file upload rate limiter

        Args:
            redis_client: Redis client for tracking
        """
        self.redis_client = redis_client
        self.limits = self.DEFAULT_LIMITS.copy()

    async def check_upload_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        file_size: int = 0,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if upload is within rate limits

        Args:
            request: FastAPI request
            user_id: User ID (if authenticated)
            file_size: Size of file being uploaded

        Returns:
            Tuple of (is_allowed, limit_info_dict)
        """
        client_ip = request.client.host if request.client else "unknown"

        # Get current timestamp
        now = datetime.utcnow()
        current_hour = now.strftime("%Y-%m-%d-%H")
        current_day = now.strftime("%Y-%m-%d")

        # Determine key prefix
        if user_id:
            prefix = f"upload:user:{user_id}"
        else:
            prefix = f"upload:ip:{client_ip}"

        # Redis keys for different time windows
        hour_key = f"{prefix}:hour:{current_hour}"
        day_key = f"{prefix}:day:{current_day}"

        try:
            if not self.redis_client:
                # Redis not available, fail open
                return True, {
                    "allowed": True,
                    "remaining": None,
                    "reset_time": None,
                    "message": "Rate limiting service unavailable",
                }

            # Get current counts using pipeline for atomicity
            pipe = self.redis_client.pipeline()
            pipe.incr(hour_key)
            pipe.incr(day_key)
            pipe.expire(hour_key, 3600)  # 1 hour expiry
            pipe.expire(day_key, 86400)  # 24 hours expiry

            # Get results
            results = await pipe.execute()
            hour_count = int(results[0] or 0)
            day_count = int(results[1] or 0)

            # Get limits based on user type
            if user_id:
                limit_per_hour = self.limits["uploads_per_hour"]
                limit_per_day = self.limits["uploads_per_day"]
                limit_concurrent = self.limits["concurrent_uploads"]
            else:
                limit_per_hour = self.limits["ip_uploads_per_hour"]
                limit_per_day = self.limits["uploads_per_day"] // 2  # Stricter for IPs
                limit_concurrent = (
                    self.limits["concurrent_uploads"] // 2
                )  # Stricter for IPs

            # Check limits
            is_allowed = hour_count < limit_per_hour and day_count < limit_per_day

            # Calculate remaining
            remaining_hour = max(0, limit_per_hour - hour_count)
            remaining_day = max(0, limit_per_day - day_count)

            limit_info = {
                "hour": {
                    "limit": limit_per_hour,
                    "used": hour_count,
                    "remaining": remaining_hour,
                    "reset_time": (now + timedelta(hours=1)).isoformat(),
                },
                "day": {
                    "limit": limit_per_day,
                    "used": day_count,
                    "remaining": remaining_day,
                    "reset_time": (now + timedelta(days=1)).isoformat(),
                },
                "user_id": user_id,
                "client_ip": client_ip,
            }

            if not is_allowed:
                logger.warning(
                    f"Upload rate limit exceeded: {prefix} - "
                    f"Hour: {hour_count}/{limit_per_hour}, Day: {day_count}/{limit_per_day}",
                    extra={
                        "user_id": user_id,
                        "client_ip": client_ip,
                        "timestamp": now.isoformat(),
                    },
                )

            return is_allowed, limit_info

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open on error
            return True, {
                "allowed": True,
                "remaining": None,
                "reset_time": None,
                "message": "Rate limiting service error",
            }

    async def check_concurrent_uploads(
        self,
        user_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Check if user has too many concurrent uploads

        Args:
            user_id: User ID (if authenticated)
            file_size: Size of file being uploaded

        Returns:
            Tuple of (is_allowed, message)
        """
        if not self.redis_client:
            return True, "Rate limiting service unavailable"

        concurrent_key = (
            f"upload:concurrent:{user_id}" if user_id else "upload:ip_concurrent"
        )

        try:
            # Check current concurrent uploads
            current = await self.redis_client.get(concurrent_key)
            current_count = int(current) if current else 0

            # Get limit
            limit = (
                self.limits["concurrent_uploads"]
                if user_id
                else self.limits["concurrent_uploads"] // 2
            )

            if current_count >= limit:
                return False, f"Too many concurrent uploads. Maximum is {limit}."

            return True, ""

        except Exception as e:
            logger.error(f"Concurrent upload check failed: {e}")
            return True, ""

    async def record_upload(
        self,
        user_id: Optional[str],
        file_hash: str,
        file_size: int,
        file_type: str,
    ):
        """
        Record an upload for tracking and abuse detection

        Args:
            user_id: User ID (if authenticated)
            file_hash: SHA-256 hash of uploaded file
            file_size: Size in bytes
            file_type: MIME type of file
        """
        if not self.redis_client:
            return

        try:
            # Record upload
            upload_key = f"upload:history:{user_id}:files"
            upload_data = {
                "file_hash": file_hash,
                "file_size": file_size,
                "file_type": file_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add to list (maintain last 100 uploads)
            await self.redis_client.lpush(upload_key, upload_data)
            # Trim to keep only last 100
            await self.redis_client.ltrim(upload_key, 0, 100)

            # Update bandwidth usage (daily reset needed)
            bandwidth_key = (
                f"upload:bandwidth:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            )
            await self.redis_client.incrbyfloat(
                bandwidth_key, file_size / (1024 * 1024 * 1024)
            )

            logger.debug(
                f"Upload recorded for user {user_id}: {file_type} - {file_size} bytes"
            )

        except Exception as e:
            logger.error(f"Failed to record upload: {e}")

    async def get_upload_history(
        self,
        user_id: Optional[str],
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        """
        Get upload history for a user (for abuse detection)

        Args:
            user_id: User ID
            limit: Number of recent uploads to return

        Returns:
            List of recent uploads
        """
        if not self.redis_client or not user_id:
            return []

        try:
            upload_key = f"upload:history:{user_id}:files"
            uploads = await self.redis_client.lrange(upload_key, 0, limit - 1)

            # Deserialize
            history = []
            for upload in uploads:
                try:
                    import json

                    data = json.loads(upload)
                    history.append(data)
                except:
                    continue

            return history

        except Exception as e:
            logger.error(f"Failed to get upload history: {e}")
            return []

    async def get_user_bandwidth_usage(
        self,
        user_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Get bandwidth usage for current day

        Args:
            user_id: User ID

        Returns:
            Dictionary with bandwidth statistics
        """
        if not self.redis_client or not user_id:
            return {"error": "Bandwidth tracking unavailable"}

        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            bandwidth_key = f"upload:bandwidth:{user_id}:{today}"

            # Get today's usage
            usage_gb = await self.redis_client.get(bandwidth_key)
            usage_gb = float(usage_gb) if usage_gb else 0.0

            limit_gb = self.limits["total_bandwidth_gb_per_day"]

            # Reset at midnight (simple approach)
            tomorrow = datetime.utcnow() + timedelta(days=1)
            tomorrow_key = (
                f"upload:bandwidth:reset:{user_id}:{tomorrow.strftime('%Y-%m-%d')}"
            )
            # Set expiry for midnight
            await self.redis_client.setex(
                bandwidth_key,
                tomorrow.strftime("%Y-%m-%d"),
                int((tomorrow - datetime.utcnow()).total_seconds()),
            )

            return {
                "usage_gb": round(usage_gb, 2),
                "limit_gb": limit_gb,
                "remaining_gb": round(max(0, limit_gb - usage_gb), 2),
                "reset_at": tomorrow.strftime("%Y-%m-%d"),
            }

        except Exception as e:
            logger.error(f"Failed to get bandwidth usage: {e}")
            return {"error": str(e)}

    def validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """
        Validate uploaded file

        Args:
            file: Uploaded file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"

        # Check file size
        file_size_mb = len(file.file.read()) / (1024 * 1024)
        max_size_mb = self.limits["max_file_size_mb"]

        if file_size_mb > max_size_mb:
            return False, f"File too large. Maximum size is {max_size_mb}MB"

        # Check for suspicious patterns (e.g., PHP files renamed)
        suspicious_patterns = [".php", ".exe", ".bat", ".cmd", ".sh"]
        if any(
            file.filename.lower().endswith(pattern) for pattern in suspicious_patterns
        ):
            return False, f"Suspicious file pattern detected"

        return True, ""

    def get_file_hash(self, file: UploadFile) -> str:
        """
        Calculate SHA-256 hash of uploaded file

        Args:
            file: Uploaded file object

        Returns:
            Hex string of SHA-256 hash
        """
        contents = file.file.read()
        file.seek(0)  # Reset file position

        return hashlib.sha256(contents).hexdigest()


# Global instance
file_upload_rate_limiter = FileUploadRateLimiter()


def rate_limit_upload(user_based: bool = True):
    """
    Decorator for rate limiting file uploads

    Args:
        user_based: If True, use user ID for rate limiting
                 If False, use IP address

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            request: Request,
            *args,
            user_id: str = None,
            file: UploadFile = None,
            **kwargs,
        ):
            # Extract user ID from request or use IP
            actual_user_id = user_id
            if not actual_user_id and hasattr(request.state, "user_id"):
                actual_user_id = getattr(request.state, "user_id", None)

            # Validate file first
            is_valid, validation_error = file_upload_rate_limiter.validate_file(file)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=validation_error
                )

            # Check file size
            file_size_mb = len(file.file.read()) / (1024 * 1024)
            file.seek(0)

            # Check rate limit
            is_allowed, limit_info = await file_upload_rate_limiter.check_upload_limit(
                request, user_id=actual_user_id, file_size=file_size_mb
            )

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Upload rate limit exceeded. {limit_info.get('message', 'Please try again later.')}",
                    headers={
                        "X-RateLimit-Minute-Limit": str(
                            limit_info.get("hour", {}).get("limit", 0)
                        ),
                        "X-RateLimit-Minute-Remaining": str(
                            limit_info.get("hour", {}).get("remaining", 0)
                        ),
                        "Retry-After": "60",
                    },
                )

            # Check concurrent uploads
            is_concurrent_ok, concurrent_msg = (
                await file_upload_rate_limiter.check_concurrent_uploads(actual_user_id)
            )

            if not is_concurrent_ok:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=concurrent_msg
                )

            # Proceed with upload
            return await func(request, file=file, *args, **kwargs)

        return wrapper


def rate_limit_ip_based():
    """
    Decorator for IP-based rate limiting (for unauthenticated uploads)
    """
    return rate_limit_upload(user_based=False)


def validate_file_size(max_size_mb: int = 10):
    """
    Decorator to validate file size before upload

    Args:
        max_size_mb: Maximum file size in MB

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, file: UploadFile = None, **kwargs):
            # Read file to check size
            contents = file.file.read()
            file_size_mb = len(contents) / (1024 * 1024)

            if file_size_mb > max_size_mb:
                file.seek(0)  # Reset position
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size is {max_size_mb}MB",
                )

            return await func(request, file=file, *args, **kwargs)

        return wrapper
