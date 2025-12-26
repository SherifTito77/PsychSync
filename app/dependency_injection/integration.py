# app/dependency_injection/integration.py

"""
DEPENDENCY INJECTION INTEGRATION
Integration layer for DI system with existing FastAPI application

INTEGRATION FEATURES:
- Seamless FastAPI integration
- Middleware for DI lifecycle management
- Request-scoped service cleanup
- Application startup/shutdown hooks
- Development and testing support

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from typing import Callable, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.dependency_injection.service_registrations import (
    register_all_services,
    dispose_services,
    is_services_registered
)
from app.dependency_injection.container import container
from app.dependency_injection.fastapi_adapter import adapter

# Initialize integration logger
integration_logger = logging.getLogger("app.di.integration")

class DIMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage DI container lifecycle per request
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Clear scoped services at the start of each request
        container.clear_scoped()

        try:
            response = await call_next(request)
            return response
        finally:
            # Clean up scoped services at the end of each request
            container.clear_scoped()

@asynccontextmanager
async def di_lifespan(app: FastAPI):
    """
    Application lifespan manager for dependency injection
    Handles service registration and disposal during application startup/shutdown
    """
    integration_logger.info("Initializing dependency injection system...")

    try:
        # Register all services during startup
        if not is_services_registered():
            register_all_services()
            integration_logger.info("All services registered successfully")
        else:
            integration_logger.info("Services already registered, skipping registration")

        # Integration with FastAPI adapter
        adapter.inject_into_fastapi(app)

        yield

    except Exception as e:
        integration_logger.error(f"DI system initialization failed: {e}")
        raise
    finally:
        # Clean up services during shutdown
        try:
            dispose_services()
            integration_logger.info("DI system shutdown completed")
        except Exception as e:
            integration_logger.error(f"Error during DI shutdown: {e}")

def setup_di_integration(app: FastAPI) -> None:
    """
    Set up dependency injection integration with FastAPI application

    Args:
        app: FastAPI application instance
    """
    try:
        integration_logger.info("Setting up DI integration...")

        # Add DI lifecycle management
        app.router.lifespan_context = di_lifespan

        # Add DI middleware for request-scoped service management
        app.add_middleware(DIMiddleware)

        integration_logger.info("DI integration setup completed")

    except Exception as e:
        integration_logger.error(f"Failed to setup DI integration: {e}")
        raise

def get_di_integration_status() -> dict:
    """Get the status of DI integration"""
    try:
        service_info = container.get_service_info()

        return {
            "services_registered": len(service_info) > 0,
            "total_services": len(service_info),
            "singletons": sum(1 for info in service_info.values() if info["lifetime"] == "singleton"),
            "scoped": sum(1 for info in service_info.values() if info["lifetime"] == "scoped"),
            "transient": sum(1 for info in service_info.values() if info["lifetime"] == "transient"),
            "container_healthy": container is not None,
            "adapter_available": adapter is not None
        }
    except Exception as e:
        integration_logger.error(f"Error getting DI integration status: {e}")
        return {
            "services_registered": False,
            "error": str(e)
        }

# Convenience functions for common integration patterns

def inject_service(service_type: type):
    """
    Decorator for injecting services into route handlers
    Uses the FastAPI adapter for dependency injection
    """
    return adapter.get_provider(service_type)

def inject_scoped_service(service_type: type):
    """Decorator for injecting scoped services"""
    return adapter.get_scoped_provider(service_type)

def inject_async_service(service_type: type):
    """Decorator for injecting async services"""
    return adapter.get_async_provider(service_type)

# Development and testing helpers

def reset_di_container():
    """Reset DI container (useful for testing)"""
    try:
        integration_logger.warning("Resetting DI container...")
        import asyncio
        asyncio.run(container.dispose())
        integration_logger.info("DI container reset completed")
    except Exception as e:
        integration_logger.error(f"Error resetting DI container: {e}")

def create_test_di_container():
    """Create a fresh DI container for testing"""
    try:
        reset_di_container()
        register_all_services()
        integration_logger.info("Test DI container created successfully")
        return container
    except Exception as e:
        integration_logger.error(f"Failed to create test DI container: {e}")
        raise

# Health check integration

async def di_health_check() -> dict:
    """Health check for the DI system"""
    try:
        # Check if container is responsive
        service_info = container.get_service_info()

        # Validate dependencies
        validation_errors = container.validate_dependencies()

        return {
            "status": "healthy" if not validation_errors else "degraded",
            "services_count": len(service_info),
            "validation_errors": validation_errors,
            "container_status": "active"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "container_status": "error"
        }

# Performance monitoring integration

def get_di_performance_metrics() -> dict:
    """Get performance metrics for the DI system"""
    try:
        service_info = container.get_service_info()

        # Calculate service distribution
        lifetimes = {"singleton": 0, "scoped": 0, "transient": 0}
        for info in service_info.values():
            lifetimes[info["lifetime"]] += 1

        return {
            "total_services": len(service_info),
            "service_distribution": lifetimes,
            "memory_usage": "unknown",  # Could be implemented with psutil
            "resolution_time_avg": "unknown"  # Could be measured
        }
    except Exception as e:
        integration_logger.error(f"Error getting DI performance metrics: {e}")
        return {"error": str(e)}