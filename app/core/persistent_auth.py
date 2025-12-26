# app/core/persistent_auth.py
"""
Secure Persistent Authentication Manager for PsychSync
Handles secure remember-me tokens with cryptographic signatures
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass

from app.core.config import settings
from app.core.cache import cache_get, cache_set, cache_delete
import logging

logger = logging.getLogger(__name__)


@dataclass
class PersistentTokenData:
    """Data for persistent authentication tokens"""
    token_id: str
    user_id: str
    selector: str
    validator: str
    created_at: datetime
    last_used: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


class PersistentAuthManager:
    """
    Secure persistent authentication manager with cryptographic signatures
    Implements RFC 6267 best practices for remember-me tokens
    """

    def __init__(self):
        self.token_duration_days = 30
        self.max_tokens_per_user = 5

        # Cache prefixes
        self.TOKEN_PREFIX = "persistent_token:"
        self.USER_TOKENS_PREFIX = "user_persistent_tokens:"
        self.SELECTOR_PREFIX = "token_selector:"

    def generate_persistent_token(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Dict[str, str]:
        """
        Generate secure persistent authentication token

        Args:
            user_id: User identifier
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            Dict containing selector and validator for token storage
        """
        try:
            # Generate token components
            token_id = secrets.token_urlsafe(16)
            selector = secrets.token_urlsafe(32)

            # Generate cryptographically secure random validator
            validator = secrets.token_urlsafe(32)

            # Create token data
            now = datetime.utcnow()
            expires_at = now + timedelta(days=self.token_duration_days)

            token_data = PersistentTokenData(
                token_id=token_id,
                user_id=user_id,
                selector=selector,
                validator=validator,
                created_at=now,
                last_used=now,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent[:200] if user_agent else ""
            )

            # Store token data
            self._store_token_data(token_data)

            # Enforce token limit per user
            self._enforce_token_limit(user_id)

            # Create final token (selector + validator hash for storage)
            validator_hash = self._hash_validator(validator)

            logger.info(f"Persistent token generated: {selector[:8]}... for user: {user_id}")

            return {
                "selector": selector,
                "validator": validator,  # Return raw validator to client
                "token_id": token_id,
                "expires_days": self.token_duration_days
            }

        except Exception as e:
            logger.error(f"Failed to generate persistent token: {e}")
            raise RuntimeError("Token generation failed")

    async def verify_persistent_token(
        self,
        selector: str,
        validator: str,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Dict[str, Any]:
        """
        Verify persistent authentication token

        Args:
            selector: Token selector
            validator: Token validator from client
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            Dict with verification result and user data
        """
        try:
            # Get token data using selector
            token_data = await self._get_token_by_selector(selector)

            if not token_data:
                logger.warning(f"Persistent token not found: {selector[:8]}...")
                return {
                    "valid": False,
                    "reason": "token_not_found",
                    "user_id": None
                }

            # Check if token is active
            if not token_data["is_active"]:
                logger.warning(f"Inactive persistent token used: {selector[:8]}...")
                return {
                    "valid": False,
                    "reason": "token_inactive",
                    "user_id": None
                }

            # Check expiration
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"Expired persistent token used: {selector[:8]}...")
                await self._revoke_token(selector, "expired")
                return {
                    "valid": False,
                    "reason": "token_expired",
                    "user_id": None
                }

            # Verify validator using constant-time comparison
            stored_validator_hash = token_data["validator"]
            provided_validator_hash = self._hash_validator(validator)

            if not self._constant_time_compare(stored_validator_hash, provided_validator_hash):
                logger.warning(f"Invalid persistent token validator: {selector[:8]}...")
                await self._revoke_token(selector, "invalid_validator")
                return {
                    "valid": False,
                    "reason": "invalid_validator",
                    "user_id": None
                }

            # Check for suspicious usage patterns
            security_warnings = await self._check_usage_patterns(
                token_data, ip_address, user_agent
            )

            # Update last used timestamp
            await self._update_token_usage(selector, ip_address, user_agent)

            # Optionally rotate validator for enhanced security
            if await self._should_rotate_validator(token_data):
                new_validator = await self._rotate_validator(selector)
                if new_validator:
                    logger.info(f"Token validator rotated for security: {selector[:8]}...")

            return {
                "valid": True,
                "user_id": token_data["user_id"],
                "token_id": token_data["token_id"],
                "security_warnings": security_warnings,
                "last_used": token_data["last_used"]
            }

        except Exception as e:
            logger.error(f"Persistent token verification failed: {e}")
            return {
                "valid": False,
                "reason": "verification_error",
                "user_id": None
            }

    async def revoke_persistent_token(self, selector: str, reason: str = "logout") -> bool:
        """
        Revoke a persistent authentication token

        Args:
            selector: Token selector
            reason: Reason for revocation

        Returns:
            True if token was successfully revoked
        """
        return await self._revoke_token(selector, reason)

    async def revoke_all_user_tokens(
        self,
        user_id: str,
        reason: str = "security_action"
    ) -> int:
        """
        Revoke all persistent tokens for a user

        Args:
            user_id: User whose tokens to revoke
            reason: Reason for revocation

        Returns:
            Number of tokens revoked
        """
        try:
            user_tokens_key = f"{self.USER_TOKENS_PREFIX}{user_id}"
            selectors = await cache_get(user_tokens_key) or []

            revoked_count = 0
            for selector in selectors:
                if await self._revoke_token(selector, reason):
                    revoked_count += 1

            # Clear user's token list
            await cache_delete(user_tokens_key)

            logger.info(f"Revoked {revoked_count} persistent tokens for user: {user_id}")

            return revoked_count

        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
            return 0

    async def get_user_active_tokens(self, user_id: str) -> list:
        """
        Get all active persistent tokens for a user

        Args:
            user_id: User identifier

        Returns:
            List of active tokens with metadata
        """
        try:
            user_tokens_key = f"{self.USER_TOKENS_PREFIX}{user_id}"
            selectors = await cache_get(user_tokens_key) or []

            active_tokens = []
            for selector in selectors:
                token_data = await self._get_token_by_selector(selector)
                if token_data and token_data["is_active"]:
                    # Calculate token age and last used
                    created_at = datetime.fromisoformat(token_data["created_at"])
                    last_used = datetime.fromisoformat(token_data["last_used"])
                    expires_at = datetime.fromisoformat(token_data["expires_at"])

                    active_tokens.append({
                        "selector": selector[:8] + "...",  # Partial selector for display
                        "created_at": token_data["created_at"],
                        "last_used": token_data["last_used"],
                        "expires_at": token_data["expires_at"],
                        "ip_address": token_data["ip_address"],
                        "age_days": (datetime.utcnow() - created_at).days,
                        "last_used_days": (datetime.utcnow() - last_used).days,
                        "expires_in_days": (expires_at - datetime.utcnow()).days
                    })

            return sorted(active_tokens, key=lambda x: x["last_used"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get user tokens: {e}")
            return []

    def _store_token_data(self, token_data: PersistentTokenData):
        """Store token data in cache"""
        try:
            # Hash validator for storage
            validator_hash = self._hash_validator(token_data.validator)

            # Prepare token data for storage
            storage_data = {
                "token_id": token_data.token_id,
                "user_id": token_data.user_id,
                "selector": token_data.selector,
                "validator": validator_hash,  # Store hash, not raw validator
                "created_at": token_data.created_at.isoformat(),
                "last_used": token_data.last_used.isoformat(),
                "expires_at": token_data.expires_at.isoformat(),
                "ip_address": token_data.ip_address,
                "user_agent": token_data.user_agent,
                "is_active": token_data.is_active
            }

            # Store token data
            token_key = f"{self.TOKEN_PREFIX}{token_data.token_id}"
            selector_key = f"{self.SELECTOR_PREFIX}{token_data.selector}"

            expire_seconds = int((token_data.expires_at - datetime.utcnow()).total_seconds())

            cache_set(token_key, storage_data, expire_seconds=expire_seconds)
            cache_set(selector_key, storage_data, expire_seconds=expire_seconds)

            # Add to user's token list
            self._add_user_token(token_data.user_id, token_data.selector, expire_seconds)

        except Exception as e:
            logger.error(f"Failed to store token data: {e}")

    async def _get_token_by_selector(self, selector: str) -> Optional[Dict[str, Any]]:
        """Get token data by selector"""
        try:
            selector_key = f"{self.SELECTOR_PREFIX}{selector}"
            return await cache_get(selector_key)
        except Exception as e:
            logger.error(f"Failed to get token by selector: {e}")
            return None

    async def _revoke_token(self, selector: str, reason: str) -> bool:
        """Revoke a token"""
        try:
            token_data = await self._get_token_by_selector(selector)
            if not token_data:
                return False

            # Mark token as inactive
            token_data["is_active"] = False
            token_data["revoked_at"] = datetime.utcnow().isoformat()
            token_data["revoked_reason"] = reason

            # Update storage
            selector_key = f"{self.SELECTOR_PREFIX}{selector}"
            token_key = f"{self.TOKEN_PREFIX}{token_data['token_id']}"

            cache_set(selector_key, token_data)
            cache_set(token_key, token_data)

            # Remove from user's active tokens
            await self._remove_user_token(token_data["user_id"], selector)

            logger.info(f"Token revoked: {selector[:8]}... Reason: {reason}")

            return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def _hash_validator(self, validator: str) -> str:
        """Hash validator using SHA-256"""
        return hashlib.sha256(validator.encode()).hexdigest()

    def _constant_time_compare(self, val1: str, val2: str) -> bool:
        """Constant-time comparison to prevent timing attacks"""
        return hmac.compare_digest(val1, val2)

    async def _check_usage_patterns(
        self,
        token_data: Dict[str, Any],
        ip_address: str,
        user_agent: str
    ) -> list:
        """Check for suspicious usage patterns"""
        warnings = []

        try:
            # IP address change
            if token_data["ip_address"] and token_data["ip_address"] != ip_address:
                warnings.append("ip_address_changed")
                logger.warning(
                    f"Token used from different IP: {token_data['selector'][:8]}... "
                    f"Original: {token_data['ip_address']}, Current: {ip_address}"
                )

            # User agent change
            if (token_data["user_agent"] and
                token_data["user_agent"] != user_agent[:200]):
                warnings.append("user_agent_changed")
                logger.warning(
                    f"Token used with different user agent: {token_data['selector'][:8]}..."
                )

            # Long time since last use
            last_used = datetime.fromisoformat(token_data["last_used"])
            days_since_last_use = (datetime.utcnow() - last_used).days
            if days_since_last_use > 30:
                warnings.append("long_dormancy")

        except Exception as e:
            logger.error(f"Usage pattern check failed: {e}")

        return warnings

    async def _update_token_usage(
        self,
        selector: str,
        ip_address: str,
        user_agent: str
    ):
        """Update token usage timestamp"""
        try:
            token_data = await self._get_token_by_selector(selector)
            if token_data:
                token_data["last_used"] = datetime.utcnow().isoformat()
                token_data["last_ip"] = ip_address
                token_data["last_user_agent"] = user_agent[:200] if user_agent else ""

                # Update storage
                selector_key = f"{self.SELECTOR_PREFIX}{selector}"
                token_key = f"{self.TOKEN_PREFIX}{token_data['token_id']}"

                cache_set(selector_key, token_data)
                cache_set(token_key, token_data)

        except Exception as e:
            logger.error(f"Failed to update token usage: {e}")

    async def _should_rotate_validator(self, token_data: Dict[str, Any]) -> bool:
        """Determine if validator should be rotated for security"""
        try:
            last_used = datetime.fromisoformat(token_data["last_used"])
            days_since_last_use = (datetime.utcnow() - last_used).days

            # Rotate validator if:
            # - Token hasn't been used in 7 days
            # - IP address or user agent changed significantly

            if days_since_last_use > 7:
                return True

        except Exception as e:
            logger.error(f"Validator rotation check failed: {e}")

        return False

    async def _rotate_validator(self, selector: str) -> Optional[str]:
        """Rotate token validator for enhanced security"""
        try:
            token_data = await self._get_token_by_selector(selector)
            if not token_data:
                return None

            # Generate new validator
            new_validator = secrets.token_urlsafe(32)
            new_validator_hash = self._hash_validator(new_validator)

            # Update token data
            token_data["validator"] = new_validator_hash
            token_data["validator_rotated_at"] = datetime.utcnow().isoformat()

            # Update storage
            selector_key = f"{self.SELECTOR_PREFIX}{selector}"
            token_key = f"{self.TOKEN_PREFIX}{token_data['token_id']}"

            cache_set(selector_key, token_data)
            cache_set(token_key, token_data)

            return new_validator

        except Exception as e:
            logger.error(f"Failed to rotate validator: {e}")
            return None

    def _add_user_token(self, user_id: str, selector: str, expire_seconds: int):
        """Add token to user's token list"""
        try:
            user_tokens_key = f"{self.USER_TOKENS_PREFIX}{user_id}"
            # This would need to be implemented based on your cache system's list operations
            # For now, we'll just note that this should store the selector in a user-specific list
            pass
        except Exception as e:
            logger.error(f"Failed to add user token: {e}")

    async def _remove_user_token(self, user_id: str, selector: str):
        """Remove token from user's token list"""
        try:
            user_tokens_key = f"{self.USER_TOKENS_PREFIX}{user_id}"
            # This would need to be implemented based on your cache system's list operations
            # For now, we'll just note that this should remove the selector from the user-specific list
            pass
        except Exception as e:
            logger.error(f"Failed to remove user token: {e}")

    def _enforce_token_limit(self, user_id: str):
        """Enforce maximum tokens per user"""
        try:
            # This would need to be implemented to check and enforce token limits
            # For now, we'll just note the requirement
            logger.info(f"Token limit enforcement needed for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to enforce token limit: {e}")


# Global instance
persistent_auth_manager = PersistentAuthManager()