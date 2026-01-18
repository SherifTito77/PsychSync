"""
Service Provider - Dependency Injection Container
=================================================

This module provides centralized dependency injection for all application services.
Following the Dependency Inversion Principle (DIP), high-level modules depend on
these service abstractions rather than concrete implementations.

Architecture:
    - Singleton instances for stateless services
    - FastAPI Depends() integration
    - Lazy initialization for performance
    - Thread-safe service creation

Usage:
    # In API endpoints
    from fastapi import Depends
    from app.core.service_provider import get_password_service_dep
    from app.services.security import PasswordService

    @router.post("/login")
    async def login(
        password_service: PasswordService = Depends(get_password_service_dep),
    ):
        # Use injected service
        result = await password_service.verify_password(...)

Author: Development Team
Version: 1.0 (Phase 2 - Service Layer Refactoring)
"""

import threading
from typing import Optional

from app.services.assessment_scoring_strategies import (
    ScoringStrategyRegistry,
    get_scoring_strategy_registry,
)
from app.services.security.authorization_service import (
    AuthorizationService,
)
from app.services.security.input_sanitizer_service import (
    InputSanitizerService,
)
from app.services.security.password_service import (
    PasswordService,
)
from app.services.security.token_service import (
    TokenService,
)


# =============================================================================
# Thread-Safe Singleton Storage
# =============================================================================


class _ServiceStorage:
    """
    Thread-safe storage for singleton service instances.

    Uses threading.Lock to ensure thread-safe lazy initialization.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._password_service: Optional[PasswordService] = None
        self._token_service: Optional[TokenService] = None
        self._authorization_service: Optional[AuthorizationService] = None
        self._input_sanitizer_service: Optional[InputSanitizerService] = None
        self._scoring_strategy_registry: Optional[ScoringStrategyRegistry] = None

    def get_password_service(self) -> PasswordService:
        """Get or create PasswordService singleton."""
        if self._password_service is None:
            with self._lock:
                # Double-check locking pattern
                if self._password_service is None:
                    self._password_service = PasswordService()
        return self._password_service

    def get_token_service(self) -> TokenService:
        """Get or create TokenService singleton."""
        if self._token_service is None:
            with self._lock:
                if self._token_service is None:
                    self._token_service = TokenService()
        return self._token_service

    def get_authorization_service(self) -> AuthorizationService:
        """Get or create AuthorizationService singleton."""
        if self._authorization_service is None:
            with self._lock:
                if self._authorization_service is None:
                    self._authorization_service = AuthorizationService()
        return self._authorization_service

    def get_input_sanitizer_service(self) -> InputSanitizerService:
        """Get or create InputSanitizerService singleton."""
        if self._input_sanitizer_service is None:
            with self._lock:
                if self._input_sanitizer_service is None:
                    self._input_sanitizer_service = InputSanitizerService()
        return self._input_sanitizer_service

    def get_scoring_strategy_registry(self) -> ScoringStrategyRegistry:
        """Get or create ScoringStrategyRegistry singleton."""
        if self._scoring_strategy_registry is None:
            with self._lock:
                if self._scoring_strategy_registry is None:
                    self._scoring_strategy_registry = get_scoring_strategy_registry()
        return self._scoring_strategy_registry

    def reset_all(self):
        """
        Reset all service instances.

        WARNING: This should only be used in tests!
        Production code should never reset services.
        """
        with self._lock:
            self._password_service = None
            self._token_service = None
            self._authorization_service = None
            self._input_sanitizer_service = None
            self._scoring_strategy_registry = None


# Global service storage instance
_service_storage = _ServiceStorage()


# =============================================================================
# Service Getter Functions (Public API)
# =============================================================================


def get_password_service() -> PasswordService:
    """
    Get PasswordService singleton instance.

    Returns:
        PasswordService: Shared password service instance

    Example:
        >>> service = get_password_service()
        >>> hashed = service.hash_password("password123")
    """
    return _service_storage.get_password_service()


def get_token_service() -> TokenService:
    """
    Get TokenService singleton instance.

    Returns:
        TokenService: Shared token service instance

    Example:
        >>> service = get_token_service()
        >>> token = await service.create_access_token(subject="user123")
    """
    return _service_storage.get_token_service()


def get_authorization_service() -> AuthorizationService:
    """
    Get AuthorizationService singleton instance.

    Returns:
        AuthorizationService: Shared authorization service instance

    Example:
        >>> service = get_authorization_service()
        >>> result = service.has_role(user, Role.ADMIN)
    """
    return _service_storage.get_authorization_service()


def get_input_sanitizer_service() -> InputSanitizerService:
    """
    Get InputSanitizerService singleton instance.

    Returns:
        InputSanitizerService: Shared input sanitizer service instance

    Example:
        >>> service = get_input_sanitizer_service()
        >>> result = service.sanitize_input(user_input)
    """
    return _service_storage.get_input_sanitizer_service()


def get_scoring_strategy_registry() -> ScoringStrategyRegistry:
    """
    Get ScoringStrategyRegistry singleton instance.

    Returns:
        ScoringStrategyRegistry: Shared scoring strategy registry

    Example:
        >>> registry = get_scoring_strategy_registry()
        >>> strategy = registry.get_strategy("MBTI")
        >>> scores = strategy.calculate(responses)
    """
    return _service_storage.get_scoring_strategy_registry()


# =============================================================================
# FastAPI Dependency Functions
# =============================================================================


async def get_password_service_dep() -> PasswordService:
    """
    FastAPI dependency for PasswordService.

    Use this function with FastAPI's Depends() to inject PasswordService
    into endpoint functions.

    Returns:
        PasswordService: Shared password service instance

    Example:
        from fastapi import Depends, APIRouter

        @router.post("/login")
        async def login(
            password_service: PasswordService = Depends(get_password_service_dep),
        ):
            result = await password_service.verify_password(...)
    """
    return get_password_service()


async def get_token_service_dep() -> TokenService:
    """
    FastAPI dependency for TokenService.

    Use this function with FastAPI's Depends() to inject TokenService
    into endpoint functions.

    Returns:
        TokenService: Shared token service instance

    Example:
        from fastapi import Depends, APIRouter

        @router.post("/token")
        async def create_token(
            token_service: TokenService = Depends(get_token_service_dep),
        ):
            token = await token_service.create_access_token(...)
    """
    return get_token_service()


async def get_authorization_service_dep() -> AuthorizationService:
    """
    FastAPI dependency for AuthorizationService.

    Use this function with FastAPI's Depends() to inject AuthorizationService
    into endpoint functions.

    Returns:
        AuthorizationService: Shared authorization service instance

    Example:
        from fastapi import Depends, APIRouter

        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            auth_service: AuthorizationService = Depends(get_authorization_service_dep),
            current_user: User = Depends(get_current_user),
        ):
            if not auth_service.has_role(current_user, Role.ADMIN):
                raise HTTPException(status_code=403)
    """
    return get_authorization_service()


async def get_input_sanitizer_service_dep() -> InputSanitizerService:
    """
    FastAPI dependency for InputSanitizerService.

    Use this function with FastAPI's Depends() to inject InputSanitizerService
    into endpoint functions.

    Returns:
        InputSanitizerService: Shared input sanitizer service instance

    Example:
        from fastapi import Depends, APIRouter

        @router.post("/feedback")
        async def submit_feedback(
            feedback: FeedbackCreate,
            sanitizer: InputSanitizerService = Depends(get_input_sanitizer_service_dep),
        ):
            result = sanitizer.sanitize_input(feedback.message)
    """
    return get_input_sanitizer_service()


async def get_scoring_strategy_registry_dep() -> ScoringStrategyRegistry:
    """
    FastAPI dependency for ScoringStrategyRegistry.

    Use this function with FastAPI's Depends() to inject ScoringStrategyRegistry
    into endpoint functions.

    Returns:
        ScoringStrategyRegistry: Shared scoring strategy registry

    Example:
        from fastapi import Depends, APIRouter

        @router.post("/assessments/score")
        async def score_assessment(
            assessment_id: str,
            registry: ScoringStrategyRegistry = Depends(get_scoring_strategy_registry_dep),
        ):
            strategy = registry.get_strategy("MBTI")
            scores = strategy.calculate(responses)
    """
    return get_scoring_strategy_registry()


# =============================================================================
# Testing Utilities
# =============================================================================


def reset_all_services() -> None:
    """
    Reset all service instances.

    ⚠️  WARNING: This should ONLY be used in tests!
    Never call this in production code.

    This function clears all singleton instances, allowing tests
    to start with a clean slate.

    Example:
        def test_password_service():
            # Reset before test
            reset_all_services()

            # Test with fresh instance
            service = get_password_service()
            # ... test code ...

            # Reset after test
            reset_all_services()
    """
    _service_storage.reset_all()


# =============================================================================
# Public API Export
# =============================================================================


__all__ = [
    # Service getter functions
    "get_password_service",
    "get_token_service",
    "get_authorization_service",
    "get_input_sanitizer_service",
    "get_scoring_strategy_registry",
    # FastAPI dependency functions
    "get_password_service_dep",
    "get_token_service_dep",
    "get_authorization_service_dep",
    "get_input_sanitizer_service_dep",
    "get_scoring_strategy_registry_dep",
    # Testing utilities
    "reset_all_services",
]
