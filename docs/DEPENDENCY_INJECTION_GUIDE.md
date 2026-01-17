# Dependency Injection System Guide

## Overview

PsychSync AI implements an enterprise-grade dependency injection (DI) system that provides:

- **Service Lifecycle Management**: Singleton, scoped, and transient service lifetimes
- **Automatic Dependency Resolution**: Constructor injection with automatic wiring
- **Clean Architecture Integration**: Supports domain, application, and infrastructure layers
- **FastAPI Integration**: Seamless integration with FastAPI's dependency injection
- **Performance Optimization**: Efficient service resolution and caching
- **Testing Support**: Easy service mocking and test isolation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                DI Integration Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  FastAPI        │  │  DI Middleware  │  │  Lifespan    │ │
│  │  Adapter        │  │                 │  │  Management  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                DI Container Core                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Service        │  │  Lifetime       │  │  Dependency  │ │
│  │  Registry       │  │  Management     │  │  Resolution  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                Service Registrations                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Core Services  │  │  Domain         │  │  Infrastructure│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Basic Service Registration

```python
from app.dependency_injection.container import register_singleton, register_scoped

# Register a singleton service
register_singleton(MyService)

# Register a scoped service with dependencies
register_scoped(
    MyComplexService,
    dependencies={"repository": "UserRepository", "cache": "RedisClient"}
)
```

### 2. Using Services in FastAPI Endpoints

```python
from app.dependency_injection.fastapi_adapter import get_service
from app.services.my_service import MyService

@router.get("/data")
async def get_data(
    my_service: MyService = get_service(MyService)
):
    return await my_service.get_data()
```

### 3. Manual Service Resolution

```python
from app.dependency_injection.container import container

# Synchronous resolution
service = container.resolve_sync(MyService)

# Asynchronous resolution
service = await container.resolve(MyService)
```

## Service Lifetimes

### Singleton
- **Purpose**: One instance per application lifetime
- **Use Cases**: Configuration, caches, expensive resources
- **Example**: Database connection pools, HTTP clients

```python
@register_singleton
class DatabaseConnection:
    def __init__(self):
        self.connection = create_database_connection()
```

### Scoped
- **Purpose**: One instance per request/scope
- **Use Cases**: Unit of work, request-specific data
- **Example**: Database sessions, user context

```python
@register_scoped
class DatabaseSession:
    def __init__(self):
        self.session = create_session()
```

### Transient
- **Purpose**: New instance every time it's requested
- **Use Cases**: Stateless services, lightweight objects
- **Example**: Calculators, validators, transformers

```python
@register_transient
class CalculatorService:
    def calculate(self, a, b):
        return a + b
```

## Integration Patterns

### 1. Clean Architecture Integration

```python
# Domain Entity (no DI dependencies)
class User:
    def __init__(self, email: str, name: str):
        self.email = email
        self.name = name

# Application Use Case (depends on interfaces)
@register_scoped
class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository, email_service: EmailService):
        self.user_repository = user_repository
        self.email_service = email_service

# Infrastructure Implementation
@register_scoped
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
```

### 2. FastAPI Route Integration

```python
from app.dependency_injection.fastapi_adapter import get_scoped_service

@router.post("/register")
async def register_user(
    data: RegistrationData,
    use_case: RegisterUserUseCase = get_scoped_service(RegisterUserUseCase)
):
    result = await use_case.execute(data)
    return result
```

### 3. Configuration Injection

```python
from app.dependency_injection.fastapi_adapter import get_config

@router.get("/info")
def get_info(
    environment: str = get_config("environment"),
    version: str = get_config("version", default="1.0.0")
):
    return {"environment": environment, "version": version}
```

## Advanced Usage

### 1. Factory Functions

```python
def create_repository(db_session: AsyncSession) -> UserRepository:
    return SQLAlchemyUserRepository(db_session)

register_scoped(
    "user_repository",
    factory=create_repository,
    dependencies={"db_session": "AsyncSession"}
)
```

### 2. Conditional Registration

```python
from app.core.config.settings import settings

if settings.ENVIRONMENT == "production":
    register_singleton(ProductionEmailService)
else:
    register_singleton(DevEmailService)
```

### 3. Service Validation

```python
# Validate service registrations
errors = container.validate_dependencies()
if errors:
    raise ValueError(f"DI configuration errors: {errors}")
```

## Testing with DI

### 1. Test Service Replacement

```python
import pytest
from unittest.mock import Mock

def test_user_registration():
    # Replace services with mocks
    container.register_instance("email_service", Mock())
    container.register_instance("user_repository", Mock())

    # Run test
    # ...
```

### 2. Test Container Isolation

```python
from app.dependency_injection.integration import create_test_di_container

@pytest.fixture
def test_container():
    return create_test_di_container()

def test_with_container(test_container):
    # Test with isolated container
    # ...
```

## Performance Considerations

### 1. Service Resolution Caching
- Singleton services are cached automatically
- Scoped services are cached per request
- Transient services are created each time

### 2. Constructor Injection
- Dependencies are resolved once per service instance
- Circular dependencies are detected and prevented
- Performance overhead is minimal after first resolution

### 3. Memory Management
- Container automatically disposes services with `dispose()` method
- Scoped services are cleared at request end
- Memory leaks are prevented through proper lifecycle management

## Best Practices

### 1. Service Design
- Keep services focused and single-purpose
- Depend on abstractions, not implementations
- Make services stateless when possible

### 2. Lifetime Selection
- Use Singleton for expensive, shared resources
- Use Scoped for request-specific data
- Use Transient for lightweight, stateless services

### 3. Dependency Management
- Prefer constructor injection over property injection
- Avoid service locator pattern when possible
- Keep dependency graphs shallow

### 4. Error Handling
- Handle service resolution failures gracefully
- Provide meaningful error messages
- Log registration and resolution issues

## Monitoring and Debugging

### 1. Service Information

```python
from app.dependency_injection.container import container

# Get all registered services
services = container.get_service_info()

# Check service health
errors = container.validate_dependencies()
```

### 2. Performance Metrics

```python
from app.dependency_injection.integration import get_di_performance_metrics

metrics = get_di_performance_metrics()
print(f"Total services: {metrics['total_services']}")
```

### 3. Health Checks

```python
from app.dependency_injection.integration import di_health_check

health = await di_health_check()
if health["status"] != "healthy":
    # Handle degraded system
    pass
```

## Migration Guide

### From Manual Instantiation

**Before:**
```python
@router.get("/users")
async def get_users():
    db_session = get_db_session()
    user_repo = SQLAlchemyUserRepository(db_session)
    return await user_repo.find_all()
```

**After:**
```python
@router.get("/users")
async def get_users(
    user_repo: UserRepository = get_service(UserRepository)
):
    return await user_repo.find_all()
```

### From FastAPI Depends

**Before:**
```python
@router.get("/users")
async def get_users(
    user_repo: UserRepository = Depends(get_user_repository)
):
    return await user_repo.find_all()
```

**After:**
```python
@router.get("/users")
async def get_users(
    user_repo: UserRepository = get_service(UserRepository)
):
    return await user_repo.find_all()
```

## Troubleshooting

### Common Issues

1. **Service Not Registered**
   ```
   ValueError: Service MyService is not registered
   ```
   Solution: Register the service in `service_registrations.py`

2. **Circular Dependency**
   ```
   ValueError: Circular dependency detected
   ```
   Solution: Redesign service dependencies to break the cycle

3. **Import Error**
   ```
   ImportError: cannot import name 'MyService'
   ```
   Solution: Check import paths and service registration order

### Debug Mode

Enable debug logging for DI system:

```python
import logging
logging.getLogger("app.di").setLevel(logging.DEBUG)
```

This will show detailed information about:
- Service registration
- Dependency resolution
- Lifetime management
- Performance metrics

## Conclusion

The dependency injection system provides a robust foundation for building maintainable, testable, and scalable applications. By following the patterns and best practices outlined in this guide, you can leverage the full power of DI while avoiding common pitfalls.

For more examples and advanced usage patterns, see the example files in the codebase and the test suites.
