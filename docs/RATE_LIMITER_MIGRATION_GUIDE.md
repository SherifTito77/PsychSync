# Rate Limiter Consolidation - Migration Guide

## Overview

The codebase had **7 different rate limiter implementations** across ~2,000 lines of duplicate code. These have been consolidated into a single, unified system using the Strategy pattern.

## What Changed

### Old Files (TO BE DELETED)
- `app/core/rate_limiter.py` (706 lines)
- `app/core/simple_rate_limiter.py` (127 lines)
- `app/core/advanced_rate_limiter.py` (296 lines)
- `app/middleware/rate_limiter.py` (875 lines)
- `RateLimiter` classes in `app/core/resilience.py`
- `RateLimiter` classes in `app/core/enhanced_cache.py`

### New File
- `app/core/rate_limiter_unified.py` (~600 lines)

## Features of the Unified Rate Limiter

### 1. **Multiple Strategies**
- **Sliding Window** (default): Most accurate, uses Redis sorted sets
- **Token Bucket**: Smooth rate limiting with burst capacity
- **Fixed Window**: Simple counter-based, least accurate

### 2. **Multiple Backends**
- **Redis** (default): Distributed, production-ready
- **Memory**: In-memory, for development/testing

### 3. **Decorator Interface**
```python
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy, StorageBackend

@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
async def my_endpoint(request: Request):
    return {"message": "Hello"}
```

### 4. **Middleware Interface**
```python
from app.core.rate_limiter_unified import RateLimitMiddleware, RateLimitConfig
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(
    RateLimitMiddleware,
    default_config=RateLimitConfig(limit=100, window=60),
)
```

### 5. **Direct Usage**
```python
from app.core.rate_limiter_unified import UnifiedRateLimiter, RateLimitConfig, RateLimitStrategy

limiter = UnifiedRateLimiter(
    config=RateLimitConfig(limit=100, window=60),
    strategy=RateLimitStrategy.SLIDING_WINDOW,
)

result = await limiter.check("user:123")
if not result.allowed:
    raise RateLimitExceeded(result)
```

## Migration Steps

### Step 1: Update Imports

**Before:**
```python
from app.core.rate_limiter import RateLimiter, rate_limit
from app.core.advanced_rate_limiter import AdvancedRateLimiter, init_rate_limiter
from app.middleware.rate_limiter import RateLimitMiddleware
```

**After:**
```python
from app.core.rate_limiter_unified import (
    UnifiedRateLimiter,
    rate_limit,
    RateLimitMiddleware,
    RateLimitConfig,
    RateLimitStrategy,
    StorageBackend,
)
```

### Step 2: Update Decorator Usage

**Before:**
```python
from app.core.rate_limiter import RateLimiter

@RateLimiter(limit=5, window_seconds=300)
async def login_endpoint(request: Request):
    pass
```

**After:**
```python
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy

@rate_limit(limit=5, window=300, strategy=RateLimitStrategy.TOKEN_BUCKET)
async def login_endpoint(request: Request):
    pass
```

### Step 3: Update Middleware

**Before:**
```python
from app.middleware.rate_limiter import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
```

**After:**
```python
from app.core.rate_limiter_unified import RateLimitMiddleware, RateLimitConfig, RateLimitStrategy

app.add_middleware(
    RateLimitMiddleware,
    default_config=RateLimitConfig(
        limit=100,
        window=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW,
    ),
)
```

### Step 4: Update Direct Usage

**Before:**
```python
from app.core.advanced_rate_limiter import AdvancedRateLimiter

limiter = AdvancedRateLimiter(redis)
allowed, reason, info = await limiter.check_rate_limit(request, username)
```

**After:**
```python
from app.core.rate_limiter_unified import UnifiedRateLimiter, RateLimitConfig

limiter = UnifiedRateLimiter(
    config=RateLimitConfig(limit=100, window=60),
    strategy=RateLimitStrategy.SLIDING_WINDOW,
)
result = await limiter.check(identifier="api", endpoint=request.url.path)
```

## Configuration Presets

Common configurations are available as presets:

```python
from app.core.rate_limiter_unified import DEFAULT, STRICT, AUTH, API

# 100 requests per minute
DEFAULT

# 10 requests per minute (strict)
STRICT

# 5 requests per 5 minutes (for auth endpoints)
AUTH

# 1000 requests per minute (for APIs)
API
```

## Strategy Selection Guide

| Strategy | Best For | Accuracy | Burst Support |
|----------|----------|----------|---------------|
| **Sliding Window** | Production APIs | High | Medium |
| **Token Bucket** | Burst traffic | Medium | High |
| **Fixed Window** | Simple rate limiting | Low | Low |

## Error Handling

The unified rate limiter **fails open** - if Redis is down or an error occurs, requests are allowed:

```python
try:
    result = await limiter.check("user:123")
    if not result.allowed:
        raise RateLimitExceeded(result)
except Exception as e:
    logger.error(f"Rate limiter failed: {e}")
    # Fail open - allow request
```

## Testing

Use the Memory backend for testing:

```python
from app.core.rate_limiter_unified import UnifiedRateLimiter, StorageBackend

limiter = UnifiedRateLimiter(
    config=RateLimitConfig(limit=10, window=60),
    backend=StorageBackend.MEMORY,  # Use in-memory storage
)
```

## Files to Delete (After Migration)

Once all imports are updated, delete these files:

1. `app/core/rate_limiter.py`
2. `app/core/simple_rate_limiter.py`
3. `app/core/advanced_rate_limiter.py`
4. `app/middleware/rate_limiter.py`
5. Remove `RateLimiter` classes from `app/core/resilience.py`
6. Remove `RateLimiter` classes from `app/core/enhanced_cache.py`

## Benefits of Consolidation

1. **Single Source of Truth**: One rate limiter to maintain
2. **Consistent Behavior**: All endpoints use same rate limiting logic
3. **Security**: Easier to audit and patch
4. **Flexibility**: Strategy pattern allows easy algorithm switching
5. **Testing**: Easier to test with mock backend
6. **Code Reduction**: ~1,400 lines of duplicate code eliminated

## Rollback Plan

If issues occur, the old files are still available. To rollback:

1. Restore old imports
2. Comment out unified rate limiter
3. Delete `app/core/rate_limiter_unified.py`

## Support

For questions or issues, refer to:
- Unified rate limiter docstrings in `app/core/rate_limiter_unified.py`
- Test files in `tests/test_rate_limiter.py`
