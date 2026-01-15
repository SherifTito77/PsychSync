# PsychSync Core Architecture

## Overview

The core directory contains fundamental application infrastructure: configuration, middleware, security, utilities, and application factory patterns. This is the foundation upon which the entire PsychSync platform is built.

## Architecture

```
app/core/
├── config/
│   ├── __init__.py           # Settings export
│   ├── settings.py           # Pydantic settings model
│   └── security.py           # Security configuration
├── database.py               # Database connection management
├── redis_client.py           # Redis connection management
├── security/                 # Security utilities
│   ├── main.py              # Security middleware & headers
│   └── cors.py              # CORS configuration
├── middleware/              # Custom middleware
│   ├── request_tracking.py  # Request ID tracking
│   ├── response_compression.py # Gzip compression
│   └── security.py          # Security validation
└── application_factory.py   # FastAPI app factory
```

## Key Components

### 1. Configuration Management (`config/`)

#### Settings (`settings.py`)
Pydantic-based settings with environment variable support:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "PsychSync AI"
    API_VERSION: str = "2.0.0"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Usage**:
```python
from app.core.config.settings import settings

@app.get("/")
async def root():
    return {
        "app": settings.API_TITLE,
        "version": settings.API_VERSION
    }
```

### 2. Database Management (`database.py`)

#### Async Database Connection
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

engine = create_async_engine(settings.DATABASE_URL, echo=True)

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

#### Database Lifecycle
```python
@app.on_event("startup")
async def startup():
    await init_database()

@app.on_event("shutdown")
async def shutdown():
    await close_database()
```

### 3. Security (`security/`)

#### Security Headers (`main.py`)
Comprehensive security middleware:

- **CSP**: Content Security Policy (no unsafe-inline)
- **XSS Protection**: XSS attack prevention
- **CSRF Protection**: Double-submit cookie pattern
- **HSTS**: HTTP Strict Transport Security
- **Rate Limiting**: Request throttling

**Usage**:
```python
from app.security.main import setup_security_middleware

app = FastAPI()
setup_security_middleware(app)
```

#### CORS Configuration (`cors.py`)
```python
from app.core.cors import configure_cors

configure_cors(
    app,
    allowed_origins=[
        "http://localhost:3000",
        "https://app.psychsync.ai"
    ]
)
```

### 4. Middleware (`middleware/`)

#### Request Tracking
Adds unique request IDs for tracing:

```python
from app.middleware.request_tracking import setup_request_tracking

setup_request_tracking(app)
```

**Response Headers**:
```
X-Request-ID: abc123
X-Process-Time: 0.123s
```

#### Response Compression
Gzip compression for responses:

```python
from app.middleware.response_compression import setup_response_compression

setup_response_compression(app, min_size=1000)
```

### 5. Application Factory (`application_factory.py`)

Creates configured FastAPI application:

```python
from app.core.application_factory import create_application

app = create_application(
    title="PsychSync AI",
    description="Enterprise Psychological Assessment Platform",
    version="2.0.0"
)
```

**Features**:
- Dependency injection setup
- Security middleware
- CORS configuration
- Route registration
- Exception handlers
- Lifespan management

## Environment Configuration

### Development (`.env.dev`)
```bash
DATABASE_URL=postgresql+asyncpg://localhost:5432/psychsync_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
```

### Production (`.env.prod`)
```bash
DATABASE_URL=postgresql+asyncpg://prod-db:5432/psychsync
REDIS_URL=redis://prod-redis:6379/0
SECRET_KEY=<strong-random-key>
DEBUG=false
```

## Dependency Injection

### Integration (`di/integration.py`)

The application uses dependency injection for services:

```python
from app.di.integration import setup_di_integration

app = FastAPI()
setup_di_integration(app)
```

**Available Services**:
- Database sessions
- Redis connections
- External API clients
- Business logic services

## Common Patterns

### Accessing Settings
```python
from app.core.config.settings import settings

@api.get("/config")
async def get_config():
    return {
        "app_name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }
```

### Using Database
```python
from app.core.database import get_db
from sqlalchemy.orm import Session

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()
```

### Using Redis
```python
from app.core.redis_client import get_redis

@router.post("/cache")
async def cache_data(key: str, value: str, redis = Depends(get_redis)):
    await redis.set(key, value, ex=3600)
    return {"status": "cached"}
```

## Security Best Practices

### 1. Environment Variables
Never commit secrets. Use environment variables:
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set")
```

### 2. CORS Configuration
Restrict origins in production:
```python
allowed_origins = [
    "https://app.psychsync.ai"  # Production only
]
```

### 3. Rate Limiting
Enable advanced rate limiting:
```python
from app.middleware.security import setup_rate_limiting

setup_rate_limiting(
    app,
    redis_client=redis,
    default_limits=["100/minute"]
)
```

### 4. Input Validation
Use Pydantic for all inputs:
```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
```

## Startup & Shutdown Events

### Startup Sequence
```python
@app.on_event("startup")
async def startup_event():
    # 1. Connect to database
    await init_database()

    # 2. Connect to Redis
    await init_redis()

    # 3. Run migrations
    await run_migrations()

    # 4. Initialize background tasks
    start_background_tasks()
```

### Shutdown Sequence
```python
@app.on_event("shutdown")
async def shutdown_event():
    # 1. Stop background tasks
    stop_background_tasks()

    # 2. Close database connections
    await close_database()

    # 3. Close Redis connection
    await close_redis()
```

## Monitoring & Observability

### Request Tracking Middleware
Every request gets:
- Unique request ID
- Start time
- User context
- IP address

### Structured Logging
```python
import logging
import json

class StructuredLogger:
    def log(self, level: str, message: str, **context):
        log_entry = {
            "level": level,
            "message": message,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        logging.log(level, json.dumps(log_entry))
```

### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "version": settings.API_VERSION
    }
```

## Related Documentation

- [API Layer](../api/README.md) - How core is used by endpoints
- [Database Models](../db/models/README.md) - Data layer
- [Security Guide](../../docs/security/README.md) - Security best practices

## Troubleshooting

### Database Connection Issues
**Problem**: Can't connect to database
**Solution**: Check `DATABASE_URL` in `.env` file
```bash
echo $DATABASE_URL
```

### CORS Errors
**Problem**: Browser blocks API requests
**Solution**: Add origin to CORS allowed list
```python
CORS_ORIGINS=["http://localhost:3000"]
```

### Redis Connection Timeout
**Problem**: Redis operations timing out
**Solution**: Check Redis server is running
```bash
redis-cli ping
```

## Best Practices

1. **Always use dependency injection** for database/redis
2. **Validate settings** on application startup
3. **Use environment variables** for secrets
4. **Enable all security middleware** in production
5. **Implement graceful shutdown** for connections
6. **Log all errors** with context
7. **Monitor resource usage** (connections, memory)
