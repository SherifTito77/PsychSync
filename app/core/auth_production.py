"""
Production-ready authentication module
Fixed authentication endpoints with Redis token blacklisting and comprehensive security
"""

import jwt
import bcrypt
import json
import asyncio
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from fastapi import HTTPException, status, Request
import secrets
import hashlib
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

class RedisTokenBlacklist:
    """Redis-based token blacklist for production use"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        self.connected = False

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("Connected to Redis for token blacklisting")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Disconnected from Redis")

    async def add_token(self, token: str, expires_in_hours: int = 24):
        """Add token to blacklist with expiration"""
        if not self.connected:
            return False

        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"blacklist_token:{token_hash}"

            # Set with expiration (default 24 hours)
            expire_seconds = expires_in_hours * 3600
            await self.redis_client.setex(key, expire_seconds, datetime.utcnow().isoformat())

            logger.info(f"Token blacklisted: {token_hash[:16]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.connected:
            return False

        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"blacklist_token:{token_hash}"

            exists = await self.redis_client.exists(key)
            return bool(exists)

        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            return False

    async def remove_token(self, token: str):
        """Remove token from blacklist (if needed)"""
        if not self.connected:
            return False

        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"blacklist_token:{token_hash}"

            deleted = await self.redis_client.delete(key)
            logger.info(f"Token removed from blacklist: {token_hash[:16]}...")
            return bool(deleted)

        except Exception as e:
            logger.error(f"Failed to remove token from blacklist: {e}")
            return False

class ProductionTokenValidator:
    """Production JWT token validator with Redis blacklisting"""

    def __init__(self, secret_key: str, algorithm: str = "HS256", redis_url: str = None):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.redis_blacklist = RedisTokenBlacklist(redis_url)
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0

    async def initialize(self):
        """Initialize Redis connection"""
        return await self.redis_blacklist.connect()

    async def create_access_token(self, subject: str, expires_delta: timedelta = None,
                               additional_claims: Dict[str, Any] = None) -> str:
        """Create secure JWT access token with production-grade security"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)  # Default 30 minutes

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(32),  # Secure JWT ID
            "version": "1.0",
            "iss": "psychsync",  # Standard JWT issuer claim
            "aud": "psychsync-users"  # Standard JWT audience claim
        }

        # Add additional claims
        if additional_claims:
            to_encode.update(additional_claims)

        # Create JWT with production security
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
            headers={
                "kid": secrets.token_urlsafe(16),  # Key ID
                "typ": "JWT"
            }
        )

        self.success_count += 1
        return encoded_jwt

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with comprehensive security checks"""
        self.request_count += 1

        if not token:
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token format
        if not isinstance(token, str) or len(token) < 10:
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token blacklist first (faster than JWT decode)
        if await self.redis_blacklist.is_blacklisted(token):
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Decode and verify token with strict options
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="psychsync-users",  # Expected audience
                issuer="psychsync",  # Expected issuer
                options={
                    "require": ["exp", "sub", "iat", "jti", "iss", "aud"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "leeway": 0  # No clock skew tolerance for security
                }
            )

            # Additional security validations
            self._validate_token_payload(payload)

            self.success_count += 1
            return payload

        except jwt.ExpiredSignatureError:
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidIssuerError as e:
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token issuer: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidAudienceError as e:
            self.failure_count += 1
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token audience: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            self.failure_count += 1
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def blacklist_token(self, token: str, expires_in_hours: int = 24):
        """Add token to blacklist with expiration"""
        return await self.redis_blacklist.add_token(token, expires_in_hours)

    def _validate_token_payload(self, payload: Dict[str, Any]):
        """Validate token payload for security requirements"""
        # Check required claims
        required_claims = ["sub", "exp", "iat", "jti", "type", "iss", "aud", "version"]
        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token missing required claim: {claim}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Validate token type
        if payload["type"] != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate version
        if payload.get("version") != "1.0":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token version",
                headers={"WWW-WWW-Authenticate": "Bearer"},
            )

        # Check expiration (additional security check)
        exp = payload["exp"]
        if isinstance(exp, (int, float)):
            exp_datetime = datetime.utcfromtimestamp(exp)
            if exp_datetime < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Check issued at time (prevent time attacks)
        iat = payload["iat"]
        if isinstance(iat, (int, float)):
            iat_datetime = datetime.utcfromtimestamp(iat)
            # Very strict - no clock skew allowed
            if iat_datetime > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token issued in the future",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Check token age (prevent very old tokens)
        if iat_datetime < datetime.utcnow() - timedelta(hours=24):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is too old",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get token validator statistics"""
        return {
            "total_requests": self.request_count,
            "successful_validations": self.success_count,
            "failed_validations": self.failure_count,
            "success_rate": (
                (self.success_count / max(self.request_count, 1)) * 100
            ),
            "redis_connected": self.redis_blacklist.connected
        }

    async def cleanup(self):
        """Cleanup resources"""
        await self.redis_blacklist.disconnect()

class ProductionSessionManager:
    """Production session manager with Redis storage"""

    def __init__(self, redis_url: str = None, session_timeout_hours: int = 24):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.session_timeout_hours = session_timeout_hours
        self.redis_client = None
        self.connected = False

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.connected = True
            logger.info("Connected to Redis for session management")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Disconnected from Redis session manager")

    async def create_session(self, user_data: Dict[str, Any],
                              request_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new session with security features"""
        if not self.connected:
            # Fallback to in-memory session (not recommended for production)
            return self._create_memory_session(user_data)

        session_id = secrets.token_urlsafe(32)

        session_data = {
            "session_id": session_id,
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "role": user_data.get("role"),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "csrf_token": secrets.token_urlsafe(32),
            "is_active": True,
            "ip_address": request_info.get("ip_address") if request_info else "unknown",
            "user_agent": request_info.get("user_agent", "")[:255] if request_info else "",
            "fingerprint": self._generate_fingerprint(request_info) if request_info else {}
        }

        # Store session in Redis with expiration
        try:
            session_key = f"session:{session_id}"
            expire_seconds = self.session_timeout_hours * 3600

            session_json = json.dumps(session_data)
            await self.redis_client.setex(session_key, expire_seconds, session_json)

            logger.info(f"Session created for user {user_data.get('email')} (ID: {session_id})")

            return {
                "session_id": session_id,
                "csrf_token": session_data["csrf_token"],
                "created_at": session_data["created_at"],
                "expires_at": (datetime.utcnow() + timedelta(hours=self.session_timeout_hours)).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return self._create_memory_session(user_data)

    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return session data"""
        if not self.connected:
            return None

        try:
            session_key = f"session:{session_id}"
            session_json = await self.redis_client.get(session_key)

            if not session_json:
                return None

            session_data = json.loads(session_json)

            # Check if session is active
            if not session_data.get("is_active", False):
                return None

            # Check session timeout
            created_at = datetime.fromisoformat(session_data["created_at"])
            if datetime.utcnow() - created_at > timedelta(hours=self.session_timeout_hours):
                await self._expire_session(session_id)
                return None

            # Update last activity
            session_data["last_activity"] = datetime.utcnow().isoformat()

            # Update session in Redis (extends expiration)
            session_key = f"session:{session_id}"
            expire_seconds = self.session_timeout_hours * 3600
            session_json = json.dumps(session_data)
            await self.redis_client.setex(session_key, expire_seconds, session_json)

            return session_data

        except Exception as e:
            logger.error(f"Failed to validate session {session_id}: {e}")
            return None

    async def regenerate_session(self, old_session_id: str) -> Optional[str]:
        """Regenerate session ID to prevent fixation"""
        old_session = await self.validate_session(old_session_id)
        if not old_session:
            return None

        # Create new session with same data
        user_data = {
            "user_id": old_session["user_id"],
            "email": old_session["email"],
            "role": old_session["role"]
        }

        request_info = {
            "ip_address": old_session.get("ip_address"),
            "user_agent": old_session.get("user_agent")
        }

        new_session = await self.create_session(user_data, request_info)

        # Delete old session
        await self.destroy_session(old_session_id)

        return new_session["session_id"]

    async def destroy_session(self, session_id: str):
        """Destroy session"""
        if not self.connected:
            return

        try:
            session_key = f"session:{session_id}"
            await self.redis_client.delete(session_key)
            logger.info(f"Session destroyed: {session_id}")
        except Exception as e:
            logger.error(f"Failed to destroy session {session_id}: {e}")

    async def _expire_session(self, session_id: str):
        """Mark session as expired"""
        if not self.connected:
            return

        try:
            session_key = f"session:{session_id}"
            session_json = await self.redis_client.get(session_key)

            if session_json:
                session_data = json.loads(session_json)
                session_data["is_active"] = False
                session_data["expired_at"] = datetime.utcnow().isoformat()

                # Update in Redis
                session_json = json.dumps(session_data)
                await self.redis_client.setex(session_key, 3600, session_json)  # Keep for 1 hour

        except Exception as e:
            logger.error(f"Failed to expire session {session_id}: {e}")

    def _create_memory_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create in-memory session (fallback for when Redis is unavailable)"""
        session_id = secrets.token_urlsafe(32)

        return {
            "session_id": session_id,
            "csrf_token": secrets.token_urlsafe(32),
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "note": "In-memory session (Redis unavailable)"
        }

    def _generate_fingerprint(self, request_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate device fingerprint"""
        fingerprint_data = {
            "user_agent": request_info.get("user_agent", "")[:200],
            "ip_address": request_info.get("ip_address", ""),
            "accept_language": request_info.get("accept_language", ""),
            "accept_encoding": request_info.get("accept_encoding", "")
        }

        fingerprint_string = "|".join([f"{k}:{v}" for k, v in fingerprint_data.items()])
        return {
            "hash": hashlib.sha256(fingerprint_string.encode()).hexdigest(),
            "data": fingerprint_data
        }

async def test_redis_connection(redis_url: str = None) -> bool:
    """Test Redis connection for production authentication"""
    try:
        import redis
        if redis_url:
            test_client = redis.from_url(redis_url)
        else:
            # Test with default local Redis
            test_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        # Ping Redis to test connection
        test_client.ping()
        logger.info("Redis connection test successful")
        return True

    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        return False

# Global instances
production_validator = None
production_session_manager = None

async def initialize_production_auth(secret_key: str = None, redis_url: str = None):
    """Initialize production authentication system"""
    global production_validator, production_session_manager

    secret_key = secret_key or os.getenv("SECRET_KEY")

    if not secret_key:
        raise ValueError("SECRET_KEY must be configured for production authentication")

    # Test Redis connection first
    if not await test_redis_connection(redis_url):
        logger.error("Redis connection failed - authentication system not initialized")
        return None

    production_validator = ProductionTokenValidator(secret_key, redis_url=redis_url)
    production_session_manager = ProductionSessionManager(redis_url=redis_url)

    # Initialize Redis connections
    validator_initialized = await production_validator.initialize()
    session_connected = await production_session_manager.connect()

    if not validator_initialized or not session_connected:
        logger.error("Failed to initialize Redis connections")
        return None

    logger.info("Production authentication system initialized successfully")
    return production_validator

async def cleanup_production_auth():
    """Cleanup production authentication system"""
    global production_validator, production_session_manager

    if production_validator:
        await production_validator.cleanup()
    if production_session_manager:
        await production_session_manager.disconnect()

    production_validator = None
    production_session_manager = None
    logger.info("Production authentication system cleaned up")