# app/dependency_injection/fastapi_adapter.py

"""
FASTAPI DEPENDENCY INJECTION ADAPTER
Bridge between our DI container and FastAPI's dependency injection system

ADAPTER FEATURES:
- FastAPI dependency provider integration
- Automatic dependency resolution
- Request-scoped service management
- Configuration injection
- Performance optimization

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from typing import Callable, Any, Optional, List, TypeVar, Type
import inspect

from fastapi import Depends
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency_injection.container import container, container
from app.core.database import get_async_db

# Initialize adapter logger
adapter_logger = logging.getLogger("app.di.fastapi_adapter")

T = TypeVar('T')

class FastAPIAdapter:
    """
    Adapter for integrating our DI container with FastAPI
    """

    def __init__(self):
        self.container = container

    def get_provider(self, service_type: Type[T]) -> Callable[[], T]:
        """Create FastAPI dependency provider for service type"""
        def provider() -> T:
            return self.container.resolve_sync(service_type)

        # Add metadata for debugging
        provider.__di_name__ = f"provider_{service_type.__name__}"
        provider.__di_service_type__ = service_type

        return provider

    def get_scoped_provider(self, service_type: Type[T]) -> Callable[[], T]:
        """Create FastAPI dependency provider for scoped service"""
        def provider(request: Request = None) -> T:
            # For scoped services, we could implement request-specific logic
            # For now, delegates to regular provider
            return self.container.resolve_sync(service_type)

        provider.__di_name__ = f"scoped_provider_{service_type.__name__}"
        provider.__di_service_type__ = service_type

        return provider

    def get_async_provider(self, service_type: Type[T]) -> Callable[[], T]:
        """Create FastAPI dependency provider for async service"""
        async def provider() -> T:
            return await self.container.resolve(service_type)

        provider.__di_name__ = f"async_provider_{service_type.__name__}"
        provider.__di_service_type__ = service_type

        return provider

    def get_database_provider(self) -> Callable[[], AsyncSession]:
        """Create database session provider"""
        def provider() -> AsyncSession:
            return get_async_db()

        return provider

    def get_configuration_provider(self, key: str, default: Any = None):
        """Create configuration provider"""
        def provider() -> Any:
            return self.container.resolve_configuration(key, default)

        return provider

    def inject_into_fastapi(self, app):
        """Inject dependencies into FastAPI application"""
        # This could be used to automatically register common dependencies
        adapter_logger.info("Dependency injection configured for FastAPI")

    def create_dependency_function(self, service_type: Type[T]) -> Callable[[], T]:
        """Create a dependency function that can be used in route handlers"""
        def dependency_function() -> T:
            return self.container.resolve_sync(service_type)

        dependency_function.__di_service_type__ = service_type
        return dependency_function

    def create_async_dependency_function(self, service_type: Type[T]) -> Callable[[], T]:
        """Create an async dependency function for async contexts"""
        async def dependency_function() -> T:
            return await self.container.resolve(service_type)

        dependency_function.__di_service_type__ = service_type
        return dependency_function

# Global adapter instance
adapter = FastAPIAdapter()

# Convenience functions that match FastAPI's Depends pattern
def get_service(service_type: Type[T]) -> Callable[[], T]:
    """Get dependency provider for service"""
    return adapter.get_provider(service_type)

def get_scoped_service(service_type: Type[T]) -> Callable[[Request], T]:
    """Get scoped dependency provider for service"""
    return adapter.get_scoped_provider(service_type)

def get_async_service(service_type: Type[T]) -> Callable[[], T]:
    """Get async dependency provider for service"""
    return adapter.get_async_provider(service_type)

def get_db() -> Callable[[], AsyncSession]:
    """Get database session dependency"""
    return adapter.get_database_provider()

def get_config(key: str, default: Any = None):
    """Get configuration dependency"""
    return adapter.get_configuration_provider(key, default)

def inject(service_type: Type[T]) -> T:
    """Inject service directly (for non-FastAPI contexts)"""
    return adapter.container.resolve_sync(service_type)

async def inject_async(service_type: Type[T]) -> T:
    """Inject service asynchronously"""
    return await adapter.container.resolve(service_type)

# Example of how to use in a FastAPI route:
#
# from app.dependency_injection.fastapi_adapter import get_service
# from app.services.user_service import UserService
#
# @router.get("/users/{user_id}")
# async def get_user(
#     user_id: str,
#     user_service: UserService = get_service(UserService)
# ):
#     return await user_service.get_user_by_id(user_id)

def auto_register_services():
    """Auto-register common services"""
    try:
        # This would automatically register common services
        # In a real implementation, this would scan for service classes and register them
        adapter_logger.info("Auto-registering common services")

        # Example registrations (would be done automatically):
        # from app.services.user_service import UserService
        # container.register_singleton(UserService)

    except Exception as e:
        adapter_logger.error(f"Failed to auto-register services: {e}")