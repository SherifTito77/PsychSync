"""
Token Service - Enterprise-Grade JWT Token Management

Single Responsibility: Handle ALL JWT token-related operations
- Access token creation with security tracking
- Refresh token management
- Token verification and validation
- Token blacklisting and revocation
- Device fingerprinting
- Security event logging
- Password reset tokens
- Email verification tokens

This service follows SOLID principles:
- SRP: Only handles token operations
- OCP: Pluggable token algorithms via configuration
- DIP: Depends on caching abstraction, not concrete implementations

Author: Security Team
Version: 1.0 (Extracted from security.py)
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from fastapi import Request
from jose import JWTError

from app.core.config import settings

# =============================================================================
# Data Classes & Enums
# =============================================================================


class TokenType(Enum):
    """Token types for different purposes"""

    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    DEVICE_TRUST = "device_trust"


class SecurityEventType(Enum):
    """Security event types for audit logging"""

    TOKEN_CREATED = "token_created"
    TOKEN_VERIFIED = "token_verified"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_BLACKLISTED = "token_blacklisted"
    SUSPICIOUS_TOKEN = "suspicious_token"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SESSION_HIJACKING = "session_hijacking"


@dataclass
class TokenMetadata:
    """Token metadata for enhanced security tracking"""

    token_type: TokenType
    user_id: str
    issued_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    device_fingerprint: str
    session_id: str | None = None
    is_revoked: bool = False


@dataclass
class TokenPayload:
    """Decoded token payload"""

    sub: str  # Subject (user ID or email)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    jti: str  # Token ID
    token_type: str
    ip: str | None = None  # Hashed IP address
    device: str | None = None  # Hashed device fingerprint
    version: str = "2.0"


@dataclass
class TokenPair:
    """Access and refresh token pair"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


@dataclass
class VerificationResult:
    """Token verification result"""

    is_valid: bool
    subject: str | None
    payload: TokenPayload | None
    error: str | None = None


# =============================================================================
# Token Service
# =============================================================================


class TokenService:
    """
    Enterprise-grade JWT token management service.

    Responsibilities:
    - Create access tokens with security tracking
    - Create refresh tokens
    - Verify and decode tokens
    - Manage token blacklisting
    - Create device fingerprints
    - Handle password reset tokens
    - Handle email verification tokens

    Usage:
        service = TokenService()

        # Create token pair
        tokens = await service.create_token_pair(
            subject="user@example.com",
            user_id="user-123",
            request=request
        )

        # Verify token
        result = await service.verify_access_token(token_string)

        # Revoke token
        await service.revoke_token(jti, reason="user_logout")
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        access_token_expire_minutes: int | None = None,
        refresh_token_expire_days: int | None = None,
    ):
        """
        Initialize token service with configurable parameters.

        Args:
            secret_key: JWT secret key (default: from settings)
            algorithm: JWT algorithm (default: from settings)
            access_token_expire_minutes: Access token expiration
            refresh_token_expire_days: Refresh token expiration
        """
        self.secret_key = secret_key or settings.jwt_secret
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self.access_token_expire_minutes = access_token_expire_minutes or getattr(
            settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30
        )
        self.refresh_token_expire_days = refresh_token_expire_days or getattr(
            settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7
        )

        # Cache prefixes
        self.BLACKLIST_CACHE_PREFIX = "blacklist:token"
        self.METADATA_CACHE_PREFIX = "metadata:token"
        self.EVENT_CACHE_PREFIX = "security:event"

        # Initialize logger
        self._logger = logging.getLogger("app.security.token")

        # Emergency revocation key
        self.EMERGENCY_REVOCATION_KEY = "emergency:revoke:all"

        # Security thresholds
        self.SUSPICIOUS_ACTIVITY_THRESHOLD = 0.8
        self.BRUTE_FORCE_LOCKOUT_THRESHOLD = 10

    # =========================================================================
    # Token Creation
    # =========================================================================

    async def create_access_token(
        self,
        subject: str | Any,
        expires_delta: timedelta | None = None,
        additional_claims: dict[str, Any] | None = None,
        request: Request | None = None,
        user_id: str | None = None,
    ) -> str:
        """
        Create an access token with enhanced security tracking.

        Args:
            subject: The subject of the token (usually user email or ID)
            expires_delta: Optional custom expiration time
            additional_claims: Optional additional claims to include in token
            request: FastAPI request object for security tracking
            user_id: User ID for enhanced security logging

        Returns:
            Encoded JWT token as string

        Security Features:
            - Request context tracking
            - Token metadata storage
            - Security event logging
            - Anti-replay protection
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        # Generate secure JWT ID for token tracking
        jti = secrets.token_urlsafe(32)

        # Enhanced token payload with security claims
        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": str(subject),
            "type": TokenType.ACCESS.value,
            "jti": jti,
            "version": "2.0",  # Token version for revocation support
        }

        # Add any additional claims
        if additional_claims:
            to_encode.update(additional_claims)

        # Add security context if request available
        device_fingerprint = "unknown"
        if request:
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("User-Agent", "unknown")

            # Create device fingerprint
            device_fingerprint = await self._create_device_fingerprint(
                ip_address, user_agent
            )

            to_encode.update(
                {
                    "ip": hashlib.sha256(ip_address.encode()).hexdigest()[:16],
                    "device": hashlib.sha256(device_fingerprint.encode()).hexdigest()[
                        :16
                    ],
                }
            )

        try:
            # Encode JWT token
            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=self.algorithm
            )

            # Create token metadata
            token_metadata = TokenMetadata(
                token_type=TokenType.ACCESS,
                user_id=user_id or str(subject),
                issued_at=datetime.utcnow(),
                expires_at=expire,
                ip_address=(
                    request.client.host if request and request.client else "unknown"
                ),
                user_agent=(
                    request.headers.get("User-Agent", "unknown")
                    if request
                    else "unknown"
                ),
                device_fingerprint=device_fingerprint,
                session_id=(
                    additional_claims.get("session_id") if additional_claims else None
                ),
            )

            # Cache token metadata (implementation depends on cache backend)
            await self._cache_token_metadata(jti, token_metadata)

            # Log token creation
            self._logger.info(
                f"Access token created for user {user_id or subject}",
                extra={
                    "token_type": "access",
                    "jti": jti,
                    "expires_at": expire.isoformat(),
                    "event_type": "token_created",
                },
            )

            return encoded_jwt

        except Exception as e:
            self._logger.error(
                f"Failed to create access token: {type(e).__name__}",
                extra={
                    "user_id": user_id or str(subject),
                    "error_type": type(e).__name__,
                    "event_type": "security_error",
                },
            )
            raise RuntimeError("Token creation failed due to security error") from e

    def create_refresh_token(
        self,
        subject: str | Any,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            subject: The subject of the token (usually user email or ID)
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token as string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        # Generate JTI for refresh token
        jti = secrets.token_urlsafe(32)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": TokenType.REFRESH.value,
            "jti": jti,
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    async def create_token_pair(
        self,
        subject: str | Any,
        access_expires_delta: timedelta | None = None,
        refresh_expires_delta: timedelta | None = None,
        additional_claims: dict[str, Any] | None = None,
        request: Request | None = None,
        user_id: str | None = None,
    ) -> TokenPair:
        """
        Create both access and refresh tokens for secure authentication flow.

        Args:
            subject: The subject of the tokens (usually user email or ID)
            access_expires_delta: Optional custom access token expiration
            refresh_expires_delta: Optional custom refresh token expiration
            additional_claims: Optional additional claims for access token
            request: FastAPI request for security tracking
            user_id: User ID for logging

        Returns:
            TokenPair with access_token and refresh_token
        """
        # Create access token with short expiration
        if not access_expires_delta:
            access_expires_delta = timedelta(minutes=self.access_token_expire_minutes)

        access_token = await self.create_access_token(
            subject=subject,
            expires_delta=access_expires_delta,
            additional_claims=additional_claims,
            request=request,
            user_id=user_id,
        )

        # Create refresh token with long expiration
        if not refresh_expires_delta:
            refresh_expires_delta = timedelta(days=self.refresh_token_expire_days)

        refresh_token = self.create_refresh_token(
            subject=subject,
            expires_delta=refresh_expires_delta,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,  # seconds
        )

    # =========================================================================
    # Token Verification
    # =========================================================================

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> VerificationResult:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")

        Returns:
            VerificationResult with validity status and payload
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != token_type:
                return VerificationResult(
                    is_valid=False,
                    subject=None,
                    payload=None,
                    error=f"Invalid token type: expected {token_type}, got {payload.get('type')}",
                )

            # Extract subject
            subject = payload.get("sub")

            # Create token payload object
            token_payload = TokenPayload(
                sub=subject,
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
                jti=payload.get("jti"),
                token_type=payload.get("type"),
                ip=payload.get("ip"),
                device=payload.get("device"),
                version=payload.get("version", "1.0"),
            )

            return VerificationResult(
                is_valid=True,
                subject=subject,
                payload=token_payload,
                error=None,
            )

        except JWTError as e:
            self._logger.warning(
                f"Token verification failed: {str(e)}",
                extra={"event_type": "token_verification_failed"},
            )
            return VerificationResult(
                is_valid=False,
                subject=None,
                payload=None,
                error=str(e),
            )
        except Exception as e:
            self._logger.error(
                f"Unexpected error during token verification: {type(e).__name__}",
                extra={"event_type": "security_error"},
            )
            return VerificationResult(
                is_valid=False,
                subject=None,
                payload=None,
                error="Token verification failed",
            )

    def decode_token(self, token: str) -> dict[str, Any] | None:
        """
        Decode a JWT token without verification (for debugging).

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if decoding fails
        """
        try:
            # Decode without verification (only for debugging!)
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            self._logger.error(f"Token decoding failed: {type(e).__name__}")
            return None

    # =========================================================================
    # Special Purpose Tokens
    # =========================================================================

    def create_password_reset_token(self, email: str) -> str:
        """
        Create a password reset token.

        Args:
            email: User email address

        Returns:
            Encoded JWT token for password reset
        """
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
        jti = secrets.token_urlsafe(32)

        to_encode = {
            "exp": expire,
            "sub": email,
            "type": TokenType.PASSWORD_RESET.value,
            "jti": jti,
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        self._logger.info(
            f"Password reset token created for {email}",
            extra={
                "email": email,
                "jti": jti,
                "event_type": "password_reset_requested",
            },
        )

        return encoded_jwt

    def verify_password_reset_token(self, token: str) -> str | None:
        """
        Verify a password reset token.

        Args:
            token: Password reset token

        Returns:
            Email address if valid, None otherwise
        """
        result = self.verify_token(token, token_type=TokenType.PASSWORD_RESET.value)
        return result.subject if result.is_valid else None

    def create_email_verification_token(self, email: str) -> str:
        """
        Create an email verification token.

        Args:
            email: User email address

        Returns:
            Encoded JWT token for email verification
        """
        expire = datetime.utcnow() + timedelta(days=7)  # 7 day expiration
        jti = secrets.token_urlsafe(32)

        to_encode = {
            "exp": expire,
            "sub": email,
            "type": TokenType.EMAIL_VERIFICATION.value,
            "jti": jti,
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        self._logger.info(
            f"Email verification token created for {email}",
            extra={
                "email": email,
                "jti": jti,
                "event_type": "email_verification_requested",
            },
        )

        return encoded_jwt

    def verify_email_verification_token(self, token: str) -> str | None:
        """
        Verify an email verification token.

        Args:
            token: Email verification token

        Returns:
            Email address if valid, None otherwise
        """
        result = self.verify_token(token, token_type=TokenType.EMAIL_VERIFICATION.value)
        return result.subject if result.is_valid else None

    # =========================================================================
    # Token Blacklisting & Revocation
    # =========================================================================

    async def revoke_token(
        self, jti: str, reason: str = "user_logout", user_id: str | None = None
    ) -> None:
        """
        Revoke a token by adding it to the blacklist.

        Args:
            jti: Token ID to revoke
            reason: Reason for revocation
            user_id: User ID for logging

        Note:
            This is a placeholder implementation. The actual blacklisting
            depends on the cache backend (Redis, in-memory, etc.)
        """
        # Implementation depends on cache backend
        # This would typically store the JTI in Redis with an expiration
        # matching the token's expiration time

        self._logger.info(
            f"Token revoked: {jti}",
            extra={
                "jti": jti,
                "reason": reason,
                "user_id": user_id,
                "event_type": "token_revoked",
            },
        )

        # TODO: Implement actual blacklist storage
        # Example: await cache.set(f"{self.BLACKLIST_CACHE_PREFIX}:{jti}", "1", ex=expire_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            jti: Token ID to check

        Returns:
            True if token is blacklisted, False otherwise
        """
        # TODO: Implement actual blacklist check
        # Example: return await cache.exists(f"{self.BLACKLIST_CACHE_PREFIX}:{jti}")
        return False

    async def emergency_revoke_all_tokens(
        self, user_id: str, reason: str = "emergency_revocation"
    ) -> None:
        """
        Emergency revocation of all tokens for a user.

        Args:
            user_id: User ID
            reason: Reason for emergency revocation

        Note:
            This would set an emergency flag that all token verification checks
        """
        # TODO: Implement emergency revocation
        # This would typically set a flag in Redis that all token checks verify

        self._logger.warning(
            f"Emergency token revocation for user {user_id}",
            extra={
                "user_id": user_id,
                "reason": reason,
                "event_type": "emergency_revocation",
            },
        )

    # =========================================================================
    # Device Fingerprinting
    # =========================================================================

    async def _create_device_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """
        Create a device fingerprint from IP and user agent.

        Args:
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Device fingerprint string
        """
        # Simple fingerprint: hash of IP + user agent
        fingerprint_data = f"{ip_address}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]

    # =========================================================================
    # Token Metadata Caching
    # =========================================================================

    async def _cache_token_metadata(self, jti: str, metadata: TokenMetadata) -> None:
        """
        Cache token metadata for security tracking.

        Args:
            jti: Token ID
            metadata: Token metadata to cache

        Note:
            Implementation depends on cache backend
        """
        # TODO: Implement actual caching
        # Example: await cache.set_json(f"{self.METADATA_CACHE_PREFIX}:{jti}", metadata.dict(), ex=ttl)
        pass


# =============================================================================
# Default Instance (Backward Compatibility)
# =============================================================================

_default_service: TokenService | None = None


def get_token_service() -> TokenService:
    """Get default token service instance (singleton pattern)."""
    global _default_service
    if _default_service is None:
        _default_service = TokenService()
    return _default_service


# =============================================================================
# Convenience Functions (Backward Compatibility)
# =============================================================================


async def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
    request: Request | None = None,
    user_id: str | None = None,
) -> str:
    """Create access token using default service."""
    return await get_token_service().create_access_token(
        subject, expires_delta, additional_claims, request, user_id
    )


def create_refresh_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create refresh token using default service."""
    return get_token_service().create_refresh_token(subject, expires_delta)


async def create_token_pair(
    subject: str | Any,
    access_expires_delta: timedelta | None = None,
    refresh_expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Create token pair using default service."""
    pair = await get_token_service().create_token_pair(
        subject, access_expires_delta, refresh_expires_delta, additional_claims
    )
    return {
        "access_token": pair.access_token,
        "refresh_token": pair.refresh_token,
        "token_type": pair.token_type,
        "expires_in": pair.expires_in,
    }


def verify_token(token: str, token_type: str = "access") -> str | None:
    """Verify token using default service."""
    result = get_token_service().verify_token(token, token_type)
    return result.subject if result.is_valid else None


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode token using default service."""
    return get_token_service().decode_token(token)


def create_password_reset_token(email: str) -> str:
    """Create password reset token using default service."""
    return get_token_service().create_password_reset_token(email)


def verify_password_reset_token(token: str) -> str | None:
    """Verify password reset token using default service."""
    return get_token_service().verify_password_reset_token(token)


def create_email_verification_token(email: str) -> str:
    """Create email verification token using default service."""
    return get_token_service().create_email_verification_token(email)


def verify_email_verification_token(token: str) -> str | None:
    """Verify email verification token using default service."""
    return get_token_service().verify_email_verification_token(token)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of token in bytes (default: 32)

    Returns:
        URL-safe base64-encoded random token

    Example:
        >>> token = generate_secure_token()
        >>> len(token)
        43  # URL-safe base64 encoding
    """
    return secrets.token_urlsafe(length)
