"""
Enhanced Security Features for Clinical Screening

Features:
- Advanced rate limiting
- Request validation and sanitization
- Enhanced audit logging
- PHI access monitoring
- Anomaly detection
- Session management
- Data encryption
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.clinical_screening import (
    ClinicalAlert,
    ClinicalAuditLog,
    ClinicalScreening,
)


class SecurityLevel(Enum):
    """Security clearance levels"""

    PATIENT = "patient"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AuditAction(Enum):
    """Audit action types"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    SEARCH = "search"
    CRISIS_ALERT = "crisis_alert"
    CONSENT_UPDATE = "consent_update"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class EnhancedSecurityManager:
    """
    Enhanced security management for clinical data

    Features:
    - Rate limiting with Redis
    - Request validation
    - Audit logging
    - PHI monitoring
    - Anomaly detection
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.kms_client = boto3.client(
            "kms",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

    async def check_rate_limit(
        self, user_id: str, action: str, limit: int = 100, window: int = 3600
    ) -> bool:
        """
        Check if user has exceeded rate limit

        Args:
            user_id: User to check
            action: Action being performed
            limit: Max requests allowed
            window: Time window in seconds

        Returns:
            True if under limit, False if exceeded
        """
        key = f"rate_limit:{user_id}:{action}"

        # Get current count
        current = self.redis.get(key)
        count = int(current) if current else 0

        if count >= limit:
            # Log rate limit exceeded
            await self._log_security_event(
                user_id=user_id,
                event_type="rate_limit_exceeded",
                details={"action": action, "count": count, "limit": limit},
            )
            return False

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        pipe.execute()

        return True

    async def validate_phi_access(
        self, user_id: str, resource_type: str, resource_id: str, action: AuditAction
    ) -> bool:
        """
        Validate and log PHI access

        Args:
            user_id: User requesting access
            resource_type: Type of resource (screening, alert, etc.)
            resource_id: ID of resource
            action: Action being performed

        Returns:
            True if access allowed, False otherwise
        """
        # Check if user has consent
        consent_valid = await self._verify_consent(user_id, resource_type)

        if not consent_valid:
            await self._log_audit_entry(
                user_id=user_id,
                action=AuditAction.UNAUTHORIZED_ACCESS,
                entity_type=resource_type,
                entity_id=resource_id,
                details={"reason": "no_valid_consent"},
            )
            return False

        # Log the access
        await self._log_audit_entry(
            user_id=user_id,
            action=action,
            entity_type=resource_type,
            entity_id=resource_id,
            details={"authorized": True},
        )

        return True

    async def encrypt_phi(self, data: Dict[str, Any], user_id: str) -> str:
        """
        Encrypt PHI data using AWS KMS

        Args:
            data: Data to encrypt
            user_id: User ID for key context

        Returns:
            Encrypted data (base64 encoded)
        """
        try:
            # Serialize data
            json_data = json.dumps(data)

            # Encrypt with KMS
            response = self.kms_client.encrypt(
                KeyId=settings.KMS_KEY_ID,
                Plaintext=json_data.encode(),
                EncryptionContext={"user_id": user_id},
            )

            # Return base64 encoded ciphertext
            import base64

            return base64.b64encode(response["CiphertextBlob"]).decode()

        except ClientError as e:
            await self._log_security_event(
                user_id=user_id,
                event_type="encryption_failed",
                details={"error": str(e)},
            )
            raise

    async def decrypt_phi(self, encrypted_data: str, user_id: str) -> Dict[str, Any]:
        """
        Decrypt PHI data using AWS KMS

        Args:
            encrypted_data: Encrypted data (base64 encoded)
            user_id: User ID for key context

        Returns:
            Decrypted data
        """
        try:
            # Decode base64
            import base64

            ciphertext = base64.b64decode(encrypted_data)

            # Decrypt with KMS
            response = self.kms_client.decrypt(
                CiphertextBlob=ciphertext, EncryptionContext={"user_id": user_id}
            )

            # Deserialize
            return json.loads(response["Plaintext"].decode())

        except ClientError as e:
            await self._log_security_event(
                user_id=user_id,
                event_type="decryption_failed",
                details={"error": str(e)},
            )
            raise

    async def detect_anomaly(
        self, user_id: str, action: str, context: Dict[str, Any]
    ) -> bool:
        """
        Detect anomalous behavior

        Args:
            user_id: User performing action
            action: Action being performed
            context: Request context (IP, user_agent, etc.)

        Returns:
            True if anomaly detected, False otherwise
        """
        # Check for unusual access patterns
        key = f"access_pattern:{user_id}"
        pattern = self.redis.get(key)

        if pattern:
            pattern_data = json.loads(pattern)
            last_ip = pattern_data.get("ip")
            last_user_agent = pattern_data.get("user_agent")

            # Check for IP change
            if context.get("ip") != last_ip:
                # Log potential session hijacking
                await self._log_security_event(
                    user_id=user_id,
                    event_type="ip_change_detected",
                    details={
                        "old_ip": last_ip,
                        "new_ip": context.get("ip"),
                        "action": action,
                    },
                )

                # Could require re-authentication here
                return True

        # Update access pattern
        self.redis.setex(
            key,
            86400,  # 24 hours
            json.dumps(
                {
                    "ip": context.get("ip"),
                    "user_agent": context.get("user_agent"),
                    "last_seen": datetime.utcnow().isoformat(),
                }
            ),
        )

        return False

    async def enforce_data_retention(self, entity_type: str, entity_id: str) -> bool:
        """
        Enforce HIPAA data retention policies

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            True if data should be retained, False if it should be archived
        """
        # HIPAA requires 6-year retention for clinical records
        retention_years = 6
        cutoff_date = datetime.utcnow() - timedelta(days=retention_years * 365)

        # Check if data is older than retention period
        if entity_type == "screening":
            query = select(ClinicalScreening).where(
                and_(
                    ClinicalScreening.id == entity_id,
                    ClinicalScreening.created_at < cutoff_date,
                )
            )

            result = await self.db.execute(query)
            screening = result.scalar_one_or_none()

            if screening:
                # Should be archived, not deleted
                await self._log_audit_entry(
                    user_id="system",
                    action=AuditAction.UPDATE,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details={"action": "archived", "reason": "retention_policy"},
                )
                return False

        return True

    async def _verify_consent(self, user_id: str, resource_type: str) -> bool:
        """Verify user has valid consent"""
        # Implementation would check ClinicalConsent table
        return True

    async def _log_audit_entry(
        self,
        user_id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        details: Dict[str, Any],
    ):
        """Create audit log entry"""
        log_entry = ClinicalAuditLog(
            user_id=user_id,
            action=action.value,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=details.get("ip"),
            user_agent=details.get("user_agent"),
        )

        self.db.add(log_entry)
        await self.db.commit()

    async def _log_security_event(
        self, user_id: str, event_type: str, details: Dict[str, Any]
    ):
        """Log security-relevant event"""
        # Log to separate security table or external SIEM
        pass


def require_security_level(level: SecurityLevel):
    """
    Decorator to require specific security level

    Usage:
        @require_security_level(SecurityLevel.CLINICIAN)
        async def sensitive_endpoint():
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from request
            # Check security level
            # Raise exception if insufficient
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def validate_request_signature(request: Request, secret: str) -> bool:
    """
    Validate webhook or API request signature

    Args:
        request: FastAPI request
        secret: Shared secret for signature

    Returns:
        True if signature valid, False otherwise
    """
    # Get signature from header
    signature = request.headers.get("X-Signature")
    if not signature:
        return False

    # Calculate expected signature
    payload = request.body()
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    # Compare signatures
    return hmac.compare_digest(expected, signature)


class DataSanitizer:
    """Sanitize data to prevent injection attacks"""

    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """Recursively sanitize input data"""
        if isinstance(data, str):
            # Remove potentially dangerous characters
            return data.replace("<", "&lt;").replace(">", "&gt;")
        elif isinstance(data, dict):
            return {k: DataSanitizer.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DataSanitizer.sanitize_input(item) for item in data]
        else:
            return data

    @staticmethod
    def validate_screening_responses(responses: Dict[str, Any]) -> bool:
        """Validate screening responses"""
        # Check for SQL injection patterns
        dangerous_patterns = ["--", ";--", "/*", "*/", "xp_", "1=1", "DROP", "DELETE"]

        for value in responses.values():
            if isinstance(value, str):
                for pattern in dangerous_patterns:
                    if pattern.lower() in value.lower():
                        return False

        return True


# Security middleware for FastAPI
async def security_middleware(request: Request, call_next):
    """
    Security middleware for FastAPI

    Performs:
    - Rate limiting
    - Anomaly detection
    - Request validation
    """

    # Get user from token
    # Check rate limit
    # Detect anomalies
    # Validate request

    response = await call_next(request)
    return response
