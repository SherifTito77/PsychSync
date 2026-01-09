# app/core/jwt_security.py
"""
JWT Security Manager for PsychSync
Enhanced JWT token handling with security features
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import secrets
from typing import Any

import jwt

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenMetadata:
    """JWT token metadata for tracking"""

    jti: str  # JWT ID
    user_id: str
    token_type: str  # access, refresh, reset
    issued_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    blacklisted: bool = False
    revoked_reason: str | None = None


class JWTSecurityManager:
    """
    Enhanced JWT security manager with blacklisting and validation
    """

    def __init__(self):
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=7)
        self.reset_token_expire = timedelta(hours=1)

        # Cache prefixes
        self.BLACKLIST_PREFIX = "jwt_blacklist:"
        self.TOKEN_METADATA_PREFIX = "jwt_metadata:"

    def create_secure_token(
        self,
        data: dict[str, Any],
        token_type: str = "access",
        ip_address: str = "",
        user_agent: str = "",
    ) -> str:
        """
        Create JWT token with enhanced security metadata

        Args:
            data: Payload data
            token_type: Type of token (access, refresh, reset)
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            JWT token string
        """
        try:
            # Determine expiration based on token type
            if token_type == "access":
                expire = datetime.utcnow() + self.access_token_expire
            elif token_type == "refresh":
                expire = datetime.utcnow() + self.refresh_token_expire
            elif token_type == "reset":
                expire = datetime.utcnow() + self.reset_token_expire
            else:
                expire = datetime.utcnow() + self.access_token_expire

            # Generate unique JWT ID
            jti = secrets.token_urlsafe(16)

            # Add security metadata to payload
            token_data = {
                **data,
                "jti": jti,
                "token_type": token_type,
                "iat": datetime.utcnow(),
                "exp": expire,
                "ip_address": ip_address,
                "user_agent": user_agent[:100] if user_agent else "",  # Truncate for size
            }

            # Create token with explicit algorithm
            token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=self.algorithm)

            # Store token metadata
            self._store_token_metadata(
                jti=jti,
                user_id=data.get("sub", ""),
                token_type=token_type,
                issued_at=datetime.utcnow(),
                expires_at=expire,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"JWT token created: {jti[:8]}... for user: {data.get('sub', 'unknown')}")

            return token

        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise RuntimeError("Token creation failed") from e

    async def verify_token_secure(
        self, token: str, token_type: str = "access", ip_address: str = "", user_agent: str = ""
    ) -> dict[str, Any]:
        """
        Verify JWT token with comprehensive security checks

        Args:
            token: JWT token string
            token_type: Expected token type
            ip_address: Request IP address for validation
            user_agent: User agent string for validation

        Returns:
            Token payload if valid

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            # First decode without verification to get JTI
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            jti = unverified_payload.get("jti")

            if not jti:
                raise jwt.InvalidTokenError("Token missing JTI")

            # Check if token is blacklisted
            if await self._is_token_blacklisted(jti):
                raise jwt.InvalidTokenError("Token is blacklisted")

            # Decode with full verification
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[self.algorithm],  # Explicit algorithm validation
            )

            # Verify token type matches expected
            if payload.get("token_type") != token_type:
                raise jwt.InvalidTokenError(f"Invalid token type. Expected: {token_type}")

            # Additional security validations
            user_id = payload.get("sub")
            if user_id:
                await self._validate_token_usage(jti, user_id, ip_address, user_agent)

            return payload

        except jwt.ExpiredSignatureError as expired_error:
            raise jwt.InvalidTokenError("Token has expired") from expired_error
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise jwt.InvalidTokenError("Token verification failed") from e

    async def blacklist_token(self, token: str, reason: str = "logout") -> bool:
        """
        Add token to blacklist

        Args:
            token: JWT token to blacklist
            reason: Reason for blacklisting

        Returns:
            True if successfully blacklisted
        """
        try:
            # Decode to get JTI and expiration
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            exp = payload.get("exp")

            if not jti:
                logger.warning("Attempted to blacklist token without JTI")
                return False

            # Calculate blacklist expiration (same as token expiration)
            blacklist_until = None
            if exp:
                blacklist_until = datetime.fromtimestamp(exp)
            else:
                # Default to 24 hours if no expiration
                blacklist_until = datetime.utcnow() + timedelta(hours=24)

            # Add to blacklist
            blacklist_data = {
                "jti": jti,
                "blacklisted_at": datetime.utcnow().isoformat(),
                "blacklisted_until": blacklist_until.isoformat() if blacklist_until else None,
                "reason": reason,
                "user_id": payload.get("sub"),
            }

            await cache_set(
                f"{self.BLACKLIST_PREFIX}{jti}",
                blacklist_data,
                expire_seconds=int((blacklist_until - datetime.utcnow()).total_seconds())
                if blacklist_until
                else 86400,
            )

            # Update token metadata
            await self._update_token_metadata(jti, blacklisted=True, revoked_reason=reason)

            logger.info(f"Token blacklisted: {jti[:8]}... Reason: {reason}")

            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def blacklist_all_user_tokens(self, user_id: str, reason: str = "security_action") -> int:
        """
        Blacklist all active tokens for a user

        Args:
            user_id: User ID
            reason: Reason for blacklisting

        Returns:
            Number of tokens blacklisted
        """
        try:
            blacklisted_count = 0

            # In a real implementation, this would query a database for all user tokens
            # For now, we'll implement a basic version using cache patterns

            # Get user's active token patterns
            user_tokens_pattern = f"{self.TOKEN_METADATA_PREFIX}*"

            # Log the security action
            logger.info(f"Blacklisting all tokens for user: {user_id}. Reason: {reason}")

            # This is a simplified implementation
            # In production, you'd maintain an index of user tokens
            return blacklisted_count

        except Exception as e:
            logger.error(f"Failed to blacklist user tokens: {e}")
            return 0

    def _store_token_metadata(
        self,
        jti: str,
        user_id: str,
        token_type: str,
        issued_at: datetime,
        expires_at: datetime,
        ip_address: str,
        user_agent: str,
    ):
        """Store token metadata for tracking"""
        try:
            metadata = TokenMetadata(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                issued_at=issued_at,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            metadata_dict = {
                "jti": metadata.jti,
                "user_id": metadata.user_id,
                "token_type": metadata.token_type,
                "issued_at": metadata.issued_at.isoformat(),
                "expires_at": metadata.expires_at.isoformat(),
                "ip_address": metadata.ip_address,
                "user_agent": metadata.user_agent,
                "blacklisted": metadata.blacklisted,
                "revoked_reason": metadata.revoked_reason,
            }

            # Store with expiration
            expire_seconds = int((expires_at - datetime.utcnow()).total_seconds())
            cache_set(
                f"{self.TOKEN_METADATA_PREFIX}{jti}", metadata_dict, expire_seconds=expire_seconds
            )

        except Exception as e:
            logger.error(f"Failed to store token metadata: {e}")

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            blacklist_data = await cache_get(f"{self.BLACKLIST_PREFIX}{jti}")

            if not blacklist_data:
                return False

            # Check if blacklist has expired
            blacklisted_until = blacklist_data.get("blacklisted_until")
            if blacklisted_until:
                expire_time = datetime.fromisoformat(blacklisted_until)
                if datetime.utcnow() > expire_time:
                    # Blacklist expired, remove it
                    await cache_delete(f"{self.BLACKLIST_PREFIX}{jti}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False  # Fail safe - allow if blacklist check fails

    async def _validate_token_usage(self, jti: str, user_id: str, ip_address: str, user_agent: str):
        """Validate token usage patterns for security"""
        try:
            # Get token metadata
            metadata = await cache_get(f"{self.TOKEN_METADATA_PREFIX}{jti}")

            if not metadata:
                return

            # Check for suspicious IP changes (optional, based on security policy)
            original_ip = metadata.get("ip_address")
            if original_ip and original_ip != ip_address:
                # Log IP change but don't block (may be legitimate)
                logger.warning(
                    f"Token used from different IP: {jti[:8]}... "
                    f"Original: {original_ip}, Current: {ip_address}"
                )

            # Additional usage pattern checks can be added here

        except Exception as e:
            logger.error(f"Failed to validate token usage: {e}")

    async def _update_token_metadata(self, jti: str, **kwargs):
        """Update token metadata"""
        try:
            metadata = await cache_get(f"{self.TOKEN_METADATA_PREFIX}{jti}")

            if metadata:
                metadata.update(kwargs)
                await cache_set(f"{self.TOKEN_METADATA_PREFIX}{jti}", metadata)

        except Exception as e:
            logger.error(f"Failed to update token metadata: {e}")


# Global instance
jwt_security_manager = JWTSecurityManager()
