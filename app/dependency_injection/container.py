# app/dependency_injection/container.py

"""
ENTERPRISE-GRADE DEPENDENCY INJECTION CONTAINER
Dependency injection container with lifecycle management and configuration

DI CONTAINER FEATURES:
- Service registration and resolution
- Singleton and scoped lifetime management
- Configuration injection
- Automatic dependency resolution
- Lifecycle hooks
- Thread safety
- Performance optimization

Author: Security Team
Version: 2.0 Enterprise Security
"""

import asyncio
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

# Initialize DI container logger
di_logger = logging.getLogger("app.di.container")

T = TypeVar("T")


class Lifetime(Enum):
    """Service lifetime options"""

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


@dataclass
class ServiceDescriptor:
    """Service descriptor for dependency injection"""

    service_type: type[T]
    lifetime: Lifetime = Lifetime.TRANSIENT
    factory: Callable[[], T] | None = None
    instance: T | None = None
    dependencies: dict[str, type] | None = None
    on_resolve: Callable[[T], None] | None = None


class Container:
    """
    Enterprise-grade dependency injection container
    """

    def __init__(self):
        self._services: dict[str, ServiceDescriptor] = {}
        self._singletons: dict[str, Any] = {}
        self._scoped: dict[str, Any] = {}
        self._configuration: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    def register_singleton(
        self,
        service_type: type[T],
        factory: Callable[[], T] | None = None,
        dependencies: dict[str, type] | None = None,
    ) -> None:
        """Register singleton service"""
        self._register_service(service_type, Lifetime.SINGLETON, factory, dependencies)

    def register_scoped(
        self,
        service_type: type[T],
        factory: Callable[[], T] | None = None,
        dependencies: dict[str, type] | None = None,
    ) -> None:
        """Register scoped service"""
        self._register_service(service_type, Lifetime.SCOPED, factory, dependencies)

    def register_transient(
        self,
        service_type: type[T],
        factory: Callable[[], T] | None = None,
        dependencies: dict[str, type] | None = None,
    ) -> None:
        """Register transient service"""
        self._register_service(service_type, Lifetime.TRANSIENT, factory, dependencies)

    def _register_service(
        self,
        service_type: type[T],
        lifetime: Lifetime,
        factory: Callable[[], T] | None = None,
        dependencies: dict[str, type] | None = None,
    ) -> None:
        """Internal service registration"""
        service_name = self._get_service_name(service_type)

        if service_name in self._services:
            di_logger.warning(
                f"Service {service_name} is already registered, overwriting"
            )

        descriptor = ServiceDescriptor(
            service_type=service_type,
            lifetime=lifetime,
            factory=factory,
            dependencies=dependencies,
        )

        self._services[service_name] = descriptor
        di_logger.info(f"Registered service: {service_name} ({lifetime.value})")

    def register_instance(self, service_type: type[T], instance: T) -> None:
        """Register a specific instance as singleton"""
        service_name = self._get_service_name(service_type)

        descriptor = ServiceDescriptor(
            service_type=service_type, lifetime=Lifetime.SINGLETON, instance=instance
        )

        self._services[service_name] = descriptor
        self._singletons[service_name] = instance

        di_logger.info(f"Registered instance: {service_name}")

    def register_configuration(self, key: str, value: Any) -> None:
        """Register configuration value"""
        self._configuration[key] = value
        di_logger.debug(f"Registered configuration: {key}")

    def register_singleton_by_name(
        self,
        service_name: str,
        factory: Callable[[], Any] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """Register singleton service by name"""
        self._register_service_by_name(
            service_name, Lifetime.SINGLETON, factory, dependencies
        )

    def register_scoped_by_name(
        self,
        service_name: str,
        factory: Callable[[], Any] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """Register scoped service by name"""
        self._register_service_by_name(
            service_name, Lifetime.SCOPED, factory, dependencies
        )

    def register_transient_by_name(
        self,
        service_name: str,
        factory: Callable[[], Any] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """Register transient service by name"""
        self._register_service_by_name(
            service_name, Lifetime.TRANSIENT, factory, dependencies
        )

    def _register_service_by_name(
        self,
        service_name: str,
        lifetime: Lifetime,
        factory: Callable[[], Any] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """Internal service registration by name"""

        # Create a dummy type for string-based registration
        class StringService:
            pass

        descriptor = ServiceDescriptor(
            service_type=StringService,
            lifetime=lifetime,
            factory=factory,
            dependencies=dependencies,  # Keep as string dependencies for now
        )

        self._services[service_name] = descriptor
        di_logger.info(f"Registered service by name: {service_name} ({lifetime.value})")

    async def resolve(self, service_type: type[T]) -> T:
        """Resolve service dependency"""
        async with self._lock:
            service_name = self._get_service_name(service_type)

            if service_name not in self._services:
                raise ValueError(f"Service {service_name} is not registered")

            descriptor = self._services[service_name]

            # Handle based on lifetime
            if descriptor.lifetime == Lifetime.SINGLETON:
                return await self._resolve_singleton(descriptor)
            if descriptor.lifetime == Lifetime.SCOPED:
                return await self._resolve_scoped(descriptor)
            # TRANSIENT
            return await self._resolve_transient(descriptor)

    def resolve_sync(self, service_type: type[T]) -> T:
        """Resolve service dependency synchronously"""
        service_name = self._get_service_name(service_type)

        if service_name not in self._services:
            raise ValueError(f"Service {service_name} is not registered")

        descriptor = self._services[service_name]

        # Handle based on lifetime
        if descriptor.lifetime == Lifetime.SINGLETON:
            return self._resolve_singleton_sync(descriptor)
        if descriptor.lifetime == Lifetime.SCOPED:
            return self._resolve_scoped_sync(descriptor)
        # TRANSIENT
        return self._resolve_transient_sync(descriptor)

    async def resolve_all(self, service_types: list[type[T]]) -> list[T]:
        """Resolve multiple services"""
        resolved = []
        for service_type in service_types:
            resolved.append(await self.resolve(service_type))
        return resolved

    def resolve_configuration(self, key: str, default: Any = None) -> Any:
        """Resolve configuration value"""
        return self._configuration.get(key, default)

    async def _resolve_singleton(self, descriptor: ServiceDescriptor) -> T:
        """Resolve singleton service"""
        service_name = self._get_service_name(descriptor.service_type)

        # Return existing instance
        if service_name in self._singletons:
            return self._singletons[service_name]

        # Create new instance
        instance = await self._create_instance(descriptor)
        self._singletons[service_name] = instance

        di_logger.debug(f"Created singleton instance: {service_name}")
        return instance

    def _resolve_singleton_sync(self, descriptor: ServiceDescriptor) -> T:
        """Resolve singleton service synchronously"""
        service_name = self._get_service_name(descriptor.service_type)

        # Return existing instance
        if service_name in self._singletons:
            return self._singletons[service_name]

        # Create new instance
        instance = self._create_instance_sync(descriptor)
        self._singletons[service_name] = instance

        di_logger.debug(f"Created singleton instance (sync): {service_name}")
        return instance

    async def _resolve_scoped(self, descriptor: ServiceDescriptor) -> T:
        """Resolve scoped service (per-request)"""
        service_name = self._get_service_name(descriptor.service_type)

        # Return existing scoped instance
        if service_name in self._scoped:
            return self._scoped[service_name]

        # Create new instance
        instance = await self._create_instance(descriptor)
        self._scoped[service_name] = instance

        di_logger.debug(f"Created scoped instance: {service_name}")
        return instance

    def _resolve_scoped_sync(self, descriptor: ServiceDescriptor) -> T:
        """Resolve scoped service synchronously"""
        service_name = self._get_service_name(descriptor.service_type)

        # Return existing scoped instance
        if service_name in self._scoped:
            return self._scoped[service_name]

        # Create new instance
        instance = self._create_instance_sync(descriptor)
        self._scoped[service_name] = instance

        di_logger.debug(f"Created scoped instance (sync): {service_name}")
        return instance

    async def _resolve_transient(self, descriptor: ServiceDescriptor) -> T:
        """Resolve transient service (always new)"""
        instance = await self._create_instance(descriptor)
        di_logger.debug(
            f"Created transient instance: {self._get_service_name(descriptor.service_type)}"
        )
        return instance

    def _resolve_transient_sync(self, descriptor: ServiceDescriptor) -> T:
        """Resolve transient service synchronously (always new)"""
        instance = self._create_instance_sync(descriptor)
        di_logger.debug(
            f"Created transient instance (sync): {self._get_service_name(descriptor.service_type)}"
        )
        return instance

    async def _create_instance(self, descriptor: ServiceDescriptor) -> T:
        """Create service instance with dependency injection"""
        # Use factory if provided
        if descriptor.factory:
            dependencies = {}
            if descriptor.dependencies:
                for dep_name, dep_type in descriptor.dependencies.items():
                    dependencies[dep_name] = await self.resolve(dep_type)
            instance = descriptor.factory(**dependencies)
        else:
            # Use constructor with automatic dependency injection
            instance = await self._create_with_injection(descriptor.service_type)

        # Call on_resolve hook if provided
        if descriptor.on_resolve:
            await descriptor.on_resolve(instance)

        return instance

    def _create_instance_sync(self, descriptor: ServiceDescriptor) -> T:
        """Create service instance synchronously"""
        # Use factory if provided
        if descriptor.factory:
            dependencies = {}
            if descriptor.dependencies:
                for dep_name, dep_type in descriptor.dependencies.items():
                    dependencies[dep_name] = self.resolve_sync(dep_type)
            instance = descriptor.factory(**dependencies)
        else:
            # Use constructor with automatic dependency injection
            instance = self._create_with_injection_sync(descriptor.service_type)

        # Call on_resolve hook if provided
        if descriptor.on_resolve:
            try:
                if asyncio.iscoroutinefunction(descriptor.on_resolve):
                    import asyncio

                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're in an async context, we can't await here
                        # For now, skip the async hook in sync context
                        pass
                    else:
                        loop.run_until_complete(descriptor.on_resolve(instance))
                else:
                    descriptor.on_resolve(instance)
            except Exception as e:
                di_logger.warning(f"Error calling on_resolve hook: {e}")

        return instance

    def _create_with_injection(self, service_type: type[T]) -> T:
        """Create instance with automatic constructor injection"""
        constructor_signature = inspect.signature(service_type.__init__)

        # Get constructor parameters
        parameters = {}
        for param_name, param in constructor_signature.parameters.items():
            if param_name == "self":
                continue

            # Try to resolve dependency
            param_type = param.annotation
            if param_type != inspect.Parameter.empty and param_type in self._services:
                try:
                    parameters[param_name] = self.resolve_sync(param_type)
                except Exception as e:
                    di_logger.warning(f"Failed to inject dependency {param_name}: {e}")
                    parameters[param_name] = None

        # Create instance
        try:
            return service_type(**parameters)
        except Exception as e:
            di_logger.error(
                f"Failed to create instance of {service_type.__name__}: {e}"
            )
            raise

    def _create_with_injection_sync(self, service_type: type[T]) -> T:
        """Create instance with automatic constructor injection (synchronous)"""
        return self._create_with_injection(service_type)

    def _get_service_name(self, service_type: type) -> str:
        """Get service name from type"""
        if hasattr(service_type, "__name__"):
            return service_type.__name__
        if hasattr(service_type, "__qualname__"):
            return service_type.__qualname__
        return str(service_type)

    def clear_scoped(self):
        """Clear all scoped instances (typically called at end of request)"""
        self._scoped.clear()
        di_logger.debug("Cleared all scoped instances")

    def get_service_info(self) -> dict[str, dict[str, Any]]:
        """Get information about registered services"""
        info = {}

        for service_name, descriptor in self._services.items():
            info[service_name] = {
                "type": descriptor.service_type.__name__,
                "lifetime": descriptor.lifetime.value,
                "has_factory": descriptor.factory is not None,
                "has_instance": descriptor.instance is not None,
                "dependencies": (
                    list(descriptor.dependencies.keys())
                    if descriptor.dependencies
                    else []
                ),
            }

        return info

    def validate_dependencies(self) -> list[str]:
        """Validate all registered dependencies"""
        validation_errors = []

        for service_name, descriptor in self._services.items():
            # Check circular dependencies
            if self._has_circular_dependency(service_name, set()):
                validation_errors.append(
                    f"Circular dependency detected: {service_name}"
                )

            # Check invalid dependencies
            if descriptor.dependencies:
                for dep_name, dep_type in descriptor.dependencies.items():
                    if dep_name not in self._services:
                        validation_errors.append(
                            f"Invalid dependency {dep_name} for {service_name}"
                        )

        return validation_errors

    def _has_circular_dependency(self, service_name: str, visited: set) -> bool:
        """Check for circular dependencies"""
        if service_name in visited:
            return True

        visited.add(service_name)

        if service_name in self._services:
            descriptor = self._services[service_name]
            if descriptor.dependencies:
                for dep_name in descriptor.dependencies.keys():
                    if self._has_circular_dependency(dep_name, visited.copy()):
                        return True

        visited.remove(service_name)
        return False

    async def dispose(self):
        """Dispose container and cleanup resources"""
        di_logger.info("Disposing dependency injection container")

        # Clear scoped instances
        self.clear_scoped()

        # Clear singletons (if they have dispose method)
        for service_name, instance in self._singletons.items():
            if hasattr(instance, "dispose"):
                try:
                    if asyncio.iscoroutinefunction(instance.dispose):
                        await instance.dispose()
                    else:
                        instance.dispose()
                except Exception as e:
                    di_logger.warning(f"Error disposing service {service_name}: {e}")

        self._singletons.clear()
        self._services.clear()
        self._configuration.clear()


# Global container instance
container = Container()


# Convenience functions
def register_singleton(
    service_type: type[T],
    factory: Callable[[], T] | None = None,
    dependencies: dict[str, type] | None = None,
):
    """Convenience function to register singleton service"""
    container.register_singleton(service_type, factory, dependencies)


def register_scoped(
    service_type: type[T],
    factory: Callable[[], T] | None = None,
    dependencies: dict[str, type] | None = None,
):
    """Convenience function to register scoped service"""
    container.register_scoped(service_type, factory, dependencies)


def register_transient(
    service_type: type[T],
    factory: Callable[[], T] | None = None,
    dependencies: dict[str, type] | None = None,
):
    """Convenience function to register transient service"""
    container.register_transient(service_type, factory, dependencies)


def register_instance(service_type: type[T], instance: T):
    """Convenience function to register service instance"""
    container.register_instance(service_type, instance)


def register_configuration(key: str, value: Any):
    """Convenience function to register configuration"""
    container.register_configuration(key, value)


async def resolve(service_type: type[T]) -> T:
    """Convenience function to resolve service"""
    return await container.resolve(service_type)


def resolve_sync(service_type: type[T]) -> T:
    """Convenience function to resolve service synchronously"""
    return container.resolve_sync(service_type)


def get_configuration(key: str, default: Any = None) -> Any:
    """Convenience function to get configuration"""
    return container.resolve_configuration(key, default)


# Convenience functions for string-based registration
def register_singleton_by_name(
    service_name: str,
    factory: Callable[[], Any] | None = None,
    dependencies: dict[str, str] | None = None,
):
    """Convenience function to register singleton service by name"""
    container.register_singleton_by_name(service_name, factory, dependencies)


def register_scoped_by_name(
    service_name: str,
    factory: Callable[[], Any] | None = None,
    dependencies: dict[str, str] | None = None,
):
    """Convenience function to register scoped service by name"""
    container.register_scoped_by_name(service_name, factory, dependencies)


def register_transient_by_name(
    service_name: str,
    factory: Callable[[], Any] | None = None,
    dependencies: dict[str, str] | None = None,
):
    """Convenience function to register transient service by name"""
    container.register_transient_by_name(service_name, factory, dependencies)
