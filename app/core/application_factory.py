# app/core/application_factory.py

"""
APPLICATION FACTORY WITH DEPENDENCY INJECTION
Factory pattern for creating and configuring FastAPI applications

APPLICATION FACTORY FEATURES:
- Dependency injection integration
- Environment-based configuration
- Security middleware setup
- CORS and performance optimization
- Lifecycle management
- Development and testing support

Author: Security Team
Version: 2.0 Enterprise Security
"""

from contextlib import asynccontextmanager
import logging
from typing import Any

from fastapi import FastAPI

from app.core.config.settings import settings
from app.core.cors import configure_cors
from app.dependency_injection.integration import di_health_check, setup_di_integration
from app.middleware.request_tracking import setup_request_tracking
from app.middleware.response_compression import setup_response_compression
from app.middleware.security import setup_security_middleware

# Initialize application factory logger
factory_logger = logging.getLogger("app.core.application_factory")


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    """
    Application lifespan manager with DI integration
    Handles startup and shutdown events for the application
    """
    factory_logger.info("Starting PsychSync application...")

    try:
        # Initialize dependency injection system
        from app.dependency_injection.integration import di_lifespan

        async with di_lifespan(app):
            # Application startup logic
            await startup_application(app)

            yield

            # Application shutdown logic
            await shutdown_application(app)

    except Exception as e:
        factory_logger.error(f"Application lifespan error: {e}")
        raise


async def startup_application(app: FastAPI):
    """Application startup logic"""
    try:
        factory_logger.info("Initializing application services...")

        # Initialize database connections
        from app.core.database import init_db

        await init_db()
        factory_logger.info("Database initialized")

        # Initialize Redis connection
        from app.core.redis_client import init_redis

        await init_redis()
        factory_logger.info("Redis initialized")

        # Initialize background tasks
        from app.core.tasks import start_background_tasks

        start_background_tasks()
        factory_logger.info("Background tasks started")

        factory_logger.info("✅ Application startup completed")

    except Exception as e:
        factory_logger.error(f"Application startup failed: {e}")
        raise


async def shutdown_application(app: FastAPI):
    """Application shutdown logic"""
    try:
        factory_logger.info("Shutting down application...")

        # Stop background tasks
        from app.core.tasks import stop_background_tasks

        stop_background_tasks()
        factory_logger.info("Background tasks stopped")

        # Close database connections
        from app.core.database import close_db

        await close_db()
        factory_logger.info("Database connections closed")

        # Close Redis connection
        from app.core.redis_client import close_redis

        await close_redis()
        factory_logger.info("Redis connection closed")

        factory_logger.info("✅ Application shutdown completed")

    except Exception as e:
        factory_logger.error(f"Application shutdown error: {e}")


def create_application(
    title: str | None = None,
    description: str | None = None,
    version: str | None = None,
    debug: bool | None = None,
    **kwargs,
) -> FastAPI:
    """
    Factory function to create and configure a FastAPI application

    Args:
        title: Application title (defaults to settings)
        description: Application description (defaults to settings)
        version: Application version (defaults to settings)
        debug: Debug mode (defaults to settings)
        **kwargs: Additional FastAPI configuration

    Returns:
        Configured FastAPI application instance
    """
    try:
        factory_logger.info("Creating FastAPI application...")

        # Filter out conflicting parameters from kwargs
        conflicting_params = [
            "docs_url",
            "redoc_url",
            "openapi_url",
            "debug",
            "title",
            "description",
            "version",
            "lifespan",
        ]
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in conflicting_params}

        # Debug logging to see what parameters are causing conflicts
        if any(param in kwargs for param in conflicting_params):
            factory_logger.warning(
                f"Found conflicting parameters in kwargs: {[k for k in kwargs if k in conflicting_params]}"
            )
            factory_logger.debug(f"Original kwargs: {list(kwargs.keys())}")

        # Create FastAPI instance with configuration
        app = FastAPI(
            title=title or settings.PROJECT_NAME,
            description=description
            or "PsychSync AI - Enterprise Psychological Assessment Platform",
            version=version or settings.APP_VERSION,
            lifespan=application_lifespan,
            debug=debug if debug is not None else settings.DEBUG,
            docs_url="/docs" if (debug if debug is not None else settings.DEBUG) else None,
            redoc_url="/redoc" if (debug if debug is not None else settings.DEBUG) else None,
            openapi_url="/openapi.json"
            if (debug if debug is not None else settings.DEBUG)
            else None,
            **filtered_kwargs,
        )

        # Configure application components
        _configure_cors(app)
        _configure_middleware(app)
        _configure_routes(app)
        _configure_exception_handlers(app)
        _configure_dependency_injection(app)

        factory_logger.info("✅ FastAPI application created successfully")
        return app

    except Exception as e:
        factory_logger.error(f"Failed to create FastAPI application: {e}")
        raise


def _configure_cors(app: FastAPI):
    """Configure CORS settings"""
    try:
        configure_cors(app)
        factory_logger.info("CORS configuration completed")
    except Exception as e:
        factory_logger.error(f"CORS configuration failed: {e}")
        raise


def _configure_middleware(app: FastAPI):
    """Configure application middleware"""
    try:
        # Request tracking middleware
        setup_request_tracking(app)
        factory_logger.info("Request tracking middleware configured")

        # Security middleware
        setup_security_middleware(app)
        factory_logger.info("Security middleware configured")

        # Response compression middleware
        setup_response_compression(app)
        factory_logger.info("Response compression middleware configured")

    except Exception as e:
        factory_logger.error(f"Middleware configuration failed: {e}")
        raise


def _configure_routes(app: FastAPI):
    """Configure application routes"""
    try:
        # API router configuration
        from app.api.v1.api import api_router

        app.include_router(api_router, prefix="/api/v1")

        # Health check route
        @app.get("/health", tags=["Health"])
        async def health_check():
            """Application health check with DI system status"""
            di_status = await di_health_check()
            return {
                "status": "healthy",
                "application": "PsychSync AI",
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "dependency_injection": di_status,
            }

        # Root endpoint
        @app.get("/", tags=["Root"])
        async def root():
            return {
                "message": "PsychSync AI - Enterprise Psychological Assessment Platform",
                "version": settings.APP_VERSION,
                "docs": "/docs" if settings.DEBUG else None,
            }

        factory_logger.info("Routes configured successfully")

    except Exception as e:
        factory_logger.error(f"Route configuration failed: {e}")
        raise


def _configure_exception_handlers(app: FastAPI):
    """Configure exception handlers"""
    try:
        from fastapi.exceptions import RequestValidationError
        from sqlalchemy.exc import SQLAlchemyError
        from starlette.exceptions import HTTPException as StarletteHTTPException

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request, exc):
            factory_logger.warning(f"Validation error: {exc}")
            return {"error": "Validation error", "details": exc.errors(), "status": 422}

        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request, exc):
            factory_logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
            return {"error": exc.detail, "status": exc.status_code}

        @app.exception_handler(SQLAlchemyError)
        async def database_exception_handler(request, exc):
            factory_logger.error(f"Database error: {exc}")
            return {"error": "Internal server error", "status": 500}

        @app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            factory_logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return {"error": "Internal server error", "status": 500}

        factory_logger.info("Exception handlers configured successfully")

    except Exception as e:
        factory_logger.error(f"Exception handler configuration failed: {e}")
        raise


def _configure_dependency_injection(app: FastAPI):
    """Configure dependency injection system"""
    try:
        setup_di_integration(app)
        factory_logger.info("Dependency injection configured successfully")
    except Exception as e:
        factory_logger.error(f"Dependency injection configuration failed: {e}")
        raise


def create_development_application(**kwargs) -> FastAPI:
    """Create application optimized for development"""
    return create_application(debug=True, **kwargs)


def create_production_application(**kwargs) -> FastAPI:
    """Create application optimized for production"""
    return create_application(debug=False, **kwargs)


def create_testing_application(**kwargs) -> FastAPI:
    """Create application optimized for testing"""
    # Reset DI container for clean testing environment
    from app.dependency_injection.integration import reset_di_container

    reset_di_container()

    return create_application(debug=True, **kwargs)


# Environment-based application factory
def create_application_for_environment(environment: str | None = None, **kwargs) -> FastAPI:
    """
    Create application based on environment

    Args:
        environment: Environment name (defaults to settings.ENVIRONMENT)
        **kwargs: Additional FastAPI configuration
    """
    env = environment or settings.ENVIRONMENT.lower()

    if env == "development":
        return create_development_application(**kwargs)
    if env == "production":
        return create_production_application(**kwargs)
    if env == "testing":
        return create_testing_application(**kwargs)
    factory_logger.warning(f"Unknown environment: {env}, using default configuration")
    return create_application(**kwargs)


# Application factory for backward compatibility
def app_factory(**kwargs) -> FastAPI:
    """Default application factory"""
    return create_application_for_environment(**kwargs)


# Get application configuration info
def get_application_info() -> dict[str, Any]:
    """Get information about the application configuration"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_url": settings.database_url,
        "redis_url": settings.redis_url,
        "cors_origins": settings.cors_origins,
        "dependency_injection_enabled": True,
    }
