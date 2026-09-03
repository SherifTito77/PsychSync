# app/factory/app_factory.py

"""
ENTERPRISE-GRADE APPLICATION FACTORY
FastAPI application factory with modular architecture and comprehensive configuration

APPLICATION FACTORY FEATURES:
- Modular application creation
- Environment-specific configuration
- Middleware orchestration
- Route registration
- Dependency injection setup
- Health check configuration
- Lifecycle management

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import configure_cors
from app.middleware.security_middleware import SecurityMiddleware

# Initialize application factory logger
app_factory_logger = logging.getLogger("app.factory.app")


class ApplicationFactory:
    """
    Enterprise-grade FastAPI application factory
    """

    def __init__(self):
        self.app: FastAPI | None = None
        self._middleware_stack: list[Callable] = []
        self._routes: list[Callable] = []

    def create_app(
        self,
        title: str | None = None,
        description: str | None = None,
        version: str | None = None,
        debug: bool | None = None,
    ) -> FastAPI:
        """
        Create and configure FastAPI application

        Args:
            title: Application title
            description: Application description
            version: Application version
            debug: Debug mode override

        Returns:
            Configured FastAPI application
        """
        # Use settings as defaults
        app_title = title or settings.PROJECT_NAME
        app_description = description or settings.APP_DESCRIPTION
        app_version = version or settings.APP_VERSION
        app_debug = debug if debug is not None else settings.DEBUG

        app_factory_logger.info(
            f"Creating FastAPI application: {app_title} v{app_version}",
            extra={
                "title": app_title,
                "version": app_version,
                "environment": settings.ENVIRONMENT,
                "debug": app_debug,
            },
        )

        # Create FastAPI instance
        self.app = FastAPI(
            title=app_title,
            description=app_description,
            version=app_version,
            debug=app_debug,
            docs_url=settings.API_DOCS_URL if settings.API_DOCS_ENABLED else None,
            redoc_url=settings.API_REDOC_URL if settings.API_DOCS_ENABLED else None,
            openapi_url="/openapi.json" if settings.API_DOCS_ENABLED else None,
        )

        # Configure application
        self._configure_lifecycle()
        self._register_middleware()
        self._register_routes()
        self._register_exception_handlers()
        self._configure_health_checks()

        app_factory_logger.info("FastAPI application created successfully")
        return self.app

    def _configure_lifecycle(self):
        """Configure application lifecycle events"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            app_factory_logger.info("Application starting up...")
            await self._startup_tasks()
            yield
            # Shutdown
            app_factory_logger.info("Application shutting down...")
            await self._shutdown_tasks()

        self.app.router.lifespan_context = lifespan

    async def _startup_tasks(self):
        """Execute startup tasks"""
        try:
            # Initialize security middleware
            if hasattr(self.app, "security_middleware"):
                self.app.security_middleware.enable_emergency_mode(False)

            # Log application startup
            app_factory_logger.info(
                "Application startup completed",
                extra={
                    "environment": settings.ENVIRONMENT,
                    "version": settings.APP_VERSION,
                },
            )

        except Exception as e:
            app_factory_logger.error(f"Startup task failed: {e}")
            raise

    async def _shutdown_tasks(self):
        """Execute shutdown tasks"""
        try:
            # Cleanup security middleware
            if hasattr(self.app, "security_middleware"):
                stats = self.app.security_middleware.get_security_stats()
                app_factory_logger.info("Security middleware stats", extra=stats)

            app_factory_logger.info("Application shutdown completed")

        except Exception as e:
            app_factory_logger.error(f"Shutdown task failed: {e}")

    def _register_middleware(self):
        """Register middleware in the correct order"""
        try:
            # 1. Security middleware (highest priority)
            security_middleware = SecurityMiddleware(self.app)
            self.app.add_middleware(SecurityMiddleware)

            # Store reference for external access
            self.app.security_middleware = security_middleware

            # 2. CORS middleware (centralized configuration)
            configure_cors(self.app)

            # 3. Additional middleware from the stack
            for middleware in self._middleware_stack:
                self.app.add_middleware(middleware)

            app_factory_logger.info("Middleware registration completed")

        except Exception as e:
            app_factory_logger.error(f"Middleware registration failed: {e}")
            raise

    def _register_routes(self):
        """Register application routes"""
        try:
            # Import and register API routes
            from app.api.v1.api import api_router

            self.app.include_router(api_router, prefix=settings.API_V1_STR)

            # Register additional routes
            for route_func in self._routes:
                route_func(self.app)

            app_factory_logger.info("Route registration completed")

        except Exception as e:
            app_factory_logger.error(f"Route registration failed: {e}")
            raise

    def _register_exception_handlers(self):
        """Register exception handlers"""
        try:
            from fastapi import HTTPException, Request, status
            from fastapi.exceptions import RequestValidationError
            from fastapi.responses import JSONResponse
            from sqlalchemy.exc import SQLAlchemyError

            @self.app.exception_handler(RequestValidationError)
            async def validation_exception_handler(
                request: Request, exc: RequestValidationError
            ):
                app_factory_logger.warning(
                    f"Validation error: {exc}",
                    extra={
                        "path": str(request.url),
                        "method": request.method,
                        "errors": exc.errors(),
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error": "Validation failed",
                        "details": exc.errors(),
                        "type": "validation_error",
                    },
                )

            @self.app.exception_handler(HTTPException)
            async def http_exception_handler(request: Request, exc: HTTPException):
                app_factory_logger.warning(
                    f"HTTP exception: {exc.status_code} - {exc.detail}",
                    extra={
                        "path": str(request.url),
                        "method": request.method,
                        "status_code": exc.status_code,
                    },
                )
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"error": exc.detail, "type": "http_error"},
                )

            @self.app.exception_handler(SQLAlchemyError)
            async def database_exception_handler(
                request: Request, exc: SQLAlchemyError
            ):
                app_factory_logger.error(
                    f"Database error: {exc}",
                    extra={
                        "path": str(request.url),
                        "method": request.method,
                        "error_type": type(exc).__name__,
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Database operation failed",
                        "type": "database_error",
                    },
                )

            @self.app.exception_handler(Exception)
            async def general_exception_handler(request: Request, exc: Exception):
                app_factory_logger.error(
                    f"Unhandled exception: {exc}",
                    extra={
                        "path": str(request.url),
                        "method": request.method,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"error": "Internal server error", "type": "general_error"},
                )

            app_factory_logger.info("Exception handlers registered")

        except Exception as e:
            app_factory_logger.error(f"Exception handler registration failed: {e}")
            raise

    def _configure_health_checks(self):
        """Configure health check endpoints"""
        try:

            @self.app.get("/health")
            async def health_check():
                """Basic health check"""
                return {
                    "status": "healthy",
                    "timestamp": "2024-01-01T00:00:00Z",  # Will be dynamic
                    "version": settings.APP_VERSION,
                    "environment": settings.ENVIRONMENT,
                }

            @self.app.get("/health/detailed")
            async def detailed_health_check():
                """Detailed health check with system status"""
                try:
                    # Check database connection
                    # This would be implemented with actual database health check
                    database_status = "healthy"

                    # Check external services
                    services_status = {
                        "database": database_status,
                        "cache": "healthy",  # Would check Redis/Cache
                        "email": "healthy",  # Would check email service
                    }

                    overall_status = (
                        "healthy"
                        if all(
                            status == "healthy" for status in services_status.values()
                        )
                        else "degraded"
                    )

                    return {
                        "status": overall_status,
                        "timestamp": "2024-01-01T00:00:00Z",
                        "version": settings.APP_VERSION,
                        "environment": settings.ENVIRONMENT,
                        "services": services_status,
                    }

                except Exception as e:
                    app_factory_logger.error(f"Health check failed: {e}")
                    return {
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": "2024-01-01T00:00:00Z",
                    }

            @self.app.get("/metrics")
            async def metrics():
                """Application metrics endpoint"""
                if not settings.ENABLE_METRICS:
                    return {"error": "Metrics not enabled"}

                # This would return actual metrics
                return {
                    "request_count": 0,
                    "error_count": 0,
                    "average_response_time": 0,
                    "uptime": 0,
                    "memory_usage": 0,
                }

            app_factory_logger.info("Health checks configured")

        except Exception as e:
            app_factory_logger.error(f"Health check configuration failed: {e}")
            raise

    def add_middleware(self, middleware_class: Callable, **kwargs):
        """Add custom middleware to the application"""
        self._middleware_stack.append(
            lambda app: app.add_middleware(middleware_class, **kwargs)
        )
        app_factory_logger.info(f"Custom middleware added: {middleware_class.__name__}")

    def add_route(self, route_func: Callable):
        """Add custom route function"""
        self._routes.append(route_func)
        app_factory_logger.info(f"Custom route function added: {route_func.__name__}")

    def get_app(self) -> FastAPI:
        """Get the created application"""
        if self.app is None:
            raise RuntimeError("Application not created. Call create_app() first.")
        return self.app


# Global application factory instance
app_factory = ApplicationFactory()


def create_application(
    title: str | None = None,
    description: str | None = None,
    version: str | None = None,
    debug: bool | None = None,
) -> FastAPI:
    """
    Convenience function to create application

    Args:
        title: Application title
        description: Application description
        version: Application version
        debug: Debug mode override

    Returns:
        Configured FastAPI application
    """
    return app_factory.create_app(title, description, version, debug)
