# API Resilience Migration Guide

## Overview

This guide helps you migrate existing HTTP client code to use the new `ResilientHTTPClient`, which provides production-grade resilience patterns including timeouts, retries, circuit breakers, and connection pooling.

**Benefits of Migration:**
- ✅ Prevents hanging requests with configurable timeouts
- ✅ Handles transient failures automatically with exponential backoff
- ✅ Prevents cascading failures with circuit breakers
- ✅ Better performance with connection pooling
- ✅ Comprehensive logging for debugging
- ✅ Production-ready error handling

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Migration Patterns](#migration-patterns)
3. [Configuration Options](#configuration-options)
4. [Common Use Cases](#common-use-cases)
5. [Error Handling](#error-handling)
6. [Testing](#testing)
7. [Rollback Plan](#rollback-plan)

---

## Quick Start

### Before (Typical httpx Usage)

```python
import httpx

async def call_external_api(data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/endpoint",
            json=data,
            # No timeout - can hang indefinitely!
            # No retry - transient failures cause errors!
            # No circuit breaker - cascading failures!
        )
        return response.json()
```

**Problems:**
- ❌ No timeout - request can hang forever
- ❌ No retry - transient network blip causes failure
- ❌ No circuit breaker - failing service takes down your app
- ❌ No connection pooling - slower performance

### After (Resilient Usage)

```python
from app.core.resilient_client import resilient_http_client

async def call_external_api(data: dict):
    response = await resilient_http_client.post(
        "https://api.example.com/endpoint",
        json=data,
        # Timeouts, retries, circuit breakers all included!
    )
    return response.json()
```

**Benefits:**
- ✅ 30s timeout prevents hanging
- ✅ 3 automatic retries with exponential backoff
- ✅ Circuit breaker prevents cascading failures
- ✅ Connection pooling for better performance
- ✅ Comprehensive logging

---

## Migration Patterns

### Pattern 1: Simple GET Request

**Before:**
```python
import httpx

async def fetch_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()
```

**After:**
```python
from app.core.resilient_client import resilient_http_client

async def fetch_user(user_id: int):
    response = await resilient_http_client.get(
        f"https://api.example.com/users/{user_id}"
    )
    return response.json()
```

**What Changed:**
- Import changed from `httpx` to `resilient_http_client`
- No `async with` context manager needed
- All resilience patterns now included automatically

---

### Pattern 2: POST with Custom Timeout

**Before:**
```python
import httpx

async def create_user(user_data: dict):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.example.com/users",
            json=user_data
        )
        return response.json()
```

**After:**
```python
from app.core.resilient_client import resilient_http_client, HTTPRequestConfig

async def create_user(user_data: dict):
    response = await resilient_http_client.post(
        "https://api.example.com/users",
        json=user_data,
        timeout=10.0  # Override default timeout for this request
    )
    return response.json()
```

**What Changed:**
- Use global client but override timeout per-request
- Still get retries and circuit breaker

---

### Pattern 3: Custom Configuration (Per-Client)

**Before:**
```python
import httpx

async def call_critical_api(data: dict):
    # Need custom timeout and retries for critical API
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(
                    "https://critical-api.example.com",
                    json=data,
                    timeout=60.0
                )
                return response.json()
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Manual backoff
```

**After:**
```python
from app.core.resilient_client import ResilientHTTPClient, HTTPRequestConfig

# Create client with custom config
critical_api_client = ResilientHTTPClient(
    config=HTTPRequestConfig(
        timeout=60.0,          # Longer timeout
        max_retries=5,         # More retries for critical API
        retry_max=30.0,        # Longer wait between retries
    )
)

async def call_critical_api(data: dict):
    response = await critical_api_client.post(
        "https://critical-api.example.com",
        json=data
    )
    return response.json()
```

**What Changed:**
- Create dedicated client instance with custom config
- Automatic retries and backoff (no manual loop needed)
- Clean, declarative configuration

---

### Pattern 4: Multiple Requests (Connection Pooling)

**Before:**
```python
import httpx

async def fetch_multiple_users(user_ids: list[int]):
    async with httpx.AsyncClient() as client:
        results = []
        for user_id in user_ids:
            response = await client.get(f"https://api.example.com/users/{user_id}")
            results.append(response.json())
        return results
```

**After:**
```python
from app.core.resilient_client import resilient_http_client

async def fetch_multiple_users(user_ids: list[int]):
    # Connection pooling is automatic (100 max connections, 20 keepalive)
    results = []
    for user_id in user_ids:
        response = await resilient_http_client.get(
            f"https://api.example.com/users/{user_id}"
        )
        results.append(response.json())
    return results
```

**What Changed:**
- No code change needed!
- Connection pooling is automatic with global client
- Better performance than creating new client each time

**Note:** For concurrent requests, use `asyncio.gather`:

```python
from app.core.resilient_client import resilient_http_client
import asyncio

async def fetch_multiple_users_concurrent(user_ids: list[int]):
    tasks = [
        resilient_http_client.get(f"https://api.example.com/users/{user_id}")
        for user_id in user_ids
    ]
    responses = await asyncio.gather(*tasks)
    return [r.json() for r in responses]
```

---

### Pattern 5: Error Handling

**Before:**
```python
import httpx

async def call_api(data: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.example.com", json=data)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutError:
        # Handle timeout
        return None
    except httpx.HTTPError:
        # Handle other errors
        return None
```

**After:**
```python
from app.core.resilient_client import (
    resilient_http_client,
    TimeoutError,
    HTTPClientError,
    RetryExhaustedError,
    CircuitBreakerOpenError
)

async def call_api(data: dict):
    try:
        response = await resilient_http_client.post(
            "https://api.example.com",
            json=data
        )
        response.raise_for_status()
        return response.json()
    except TimeoutError:
        # Request timed out after retries
        logger.error("Request timed out")
        return None
    except CircuitBreakerOpenError:
        # Too many failures, circuit is open
        logger.warning("Circuit breaker open - service unavailable")
        return None
    except RetryExhaustedError:
        # All retry attempts exhausted
        logger.error("All retries exhausted")
        return None
    except HTTPClientError as e:
        # Other HTTP client errors
        logger.error(f"HTTP client error: {e.message}")
        return None
```

**Benefits:**
- Specific exception types for different failure scenarios
- Automatic retry means fewer exceptions reach your code
- Circuit breaker prevents spamming failing services

---

## Configuration Options

### HTTPRequestConfig Parameters

```python
from app.core.resilient_client import HTTPRequestConfig

config = HTTPRequestConfig(
    # Timeout settings
    timeout=30.0,                    # Default timeout for requests (seconds)
    connect_timeout=10.0,            # Timeout for initial connection

    # Retry settings
    max_retries=3,                   # Maximum number of retry attempts
    retry_multiplier=1.0,            # Exponential backoff multiplier
    retry_min=1.0,                   # Minimum wait between retries (seconds)
    retry_max=10.0,                  # Maximum wait between retries (seconds)

    # Circuit breaker settings
    circuit_failure_threshold=5,     # Failures before opening circuit
    circuit_recovery_timeout=60.0,   # Seconds before trying again
    circuit_half_open_attempts=3,    # Attempts in half-open state
    enable_circuit_breaker=True,     # Enable/disable circuit breaker

    # Validation settings
    validate_response=True,          # Validate response structure
    max_response_size=10*1024*1024,  # 10MB max response size
)
```

### Retry Configuration Examples

**Conservative (Quick Failure):**
```python
config = HTTPRequestConfig(
    timeout=10.0,
    max_retries=1,
    retry_min=0.5,
    retry_max=2.0,
)
```

**Aggressive (Maximum Resilience):**
```python
config = HTTPRequestConfig(
    timeout=60.0,
    max_retries=5,
    retry_min=2.0,
    retry_max=30.0,
)
```

**Balanced (Recommended Default):**
```python
config = HTTPRequestConfig(
    timeout=30.0,
    max_retries=3,
    retry_min=1.0,
    retry_max=10.0,
)
```

---

## Common Use Cases

### Use Case 1: External API Integration

```python
from app.core.resilient_client import resilient_http_client

class ExternalAPIService:
    """Service for integrating with external API"""

    BASE_URL = "https://api.external-service.com/v1"

    async def get_user_profile(self, user_id: int):
        response = await resilient_http_client.get(
            f"{self.BASE_URL}/users/{user_id}"
        )
        return response.json()

    async def update_user(self, user_id: int, data: dict):
        response = await resilient_http_client.patch(
            f"{self.BASE_URL}/users/{user_id}",
            json=data,
            timeout=15.0  # Slightly longer for updates
        )
        return response.json()

    async def delete_user(self, user_id: int):
        response = await resilient_http_client.delete(
            f"{self.BASE_URL}/users/{user_id}"
        )
        return response.status_code == 204
```

### Use Case 2: AI/ML API Calls

```python
from app.core.resilient_client import ResilientHTTPClient, HTTPRequestConfig

# AI APIs often need longer timeouts and more retries
ai_client = ResilientHTTPClient(
    config=HTTPRequestConfig(
        timeout=120.0,       # 2 minutes for AI processing
        max_retries=2,       # AI requests are expensive, retry less
        retry_min=5.0,       # Wait longer between retries
        retry_max=30.0,
        enable_circuit_breaker=True,
        circuit_failure_threshold=3,  # Fewer failures before opening
    )
)

async def call_ai_model(prompt: str):
    response = await ai_client.post(
        "https://ai-api.example.com/generate",
        json={"prompt": prompt, "max_tokens": 1000}
    )
    return response.json()
```

### Use Case 3: Webhook Delivery

```python
from app.core.resilient_client import resilient_http_client, CircuitBreakerOpenError

async def send_webhook(url: str, payload: dict):
    """Send webhook with resilience but handle circuit breaker gracefully"""
    try:
        response = await resilient_http_client.post(
            url,
            json=payload,
            timeout=10.0,  # Webhooks should be quick
        )
        return {"status": "delivered", "code": response.status_code}
    except CircuitBreakerOpenError:
        # Webhook endpoint is down - queue for retry
        return {"status": "queued", "reason": "circuit_open"}
    except Exception as e:
        return {"status": "failed", "reason": str(e)}
```

### Use Case 4: Microservice Communication

```python
from app.core.resilient_client import resilient_http_client

class MicroserviceClient:
    """Client for communicating with other microservices"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def health_check(self):
        """Quick health check - should be fast"""
        response = await resilient_http_client.get(
            f"{self.base_url}/health",
            timeout=5.0  # Quick timeout for health checks
        )
        return response.status_code == 200

    async def process_data(self, data: dict):
        """Normal processing - standard timeout"""
        response = await resilient_http_client.post(
            f"{self.base_url}/process",
            json=data
        )
        return response.json()

    async def bulk_operation(self, items: list):
        """Bulk operation - longer timeout"""
        response = await resilient_http_client.post(
            f"{self.base_url}/bulk",
            json={"items": items},
            timeout=60.0  # Longer timeout for bulk
        )
        return response.json()
```

---

## Error Handling

### Exception Hierarchy

```
HTTPClientError (base exception)
├── TimeoutError (request timed out)
├── RetryExhaustedError (all retries failed)
└── CircuitBreakerOpenError (circuit is open)
```

### Handling Each Exception Type

#### 1. TimeoutError
```python
from app.core.resilient_client import resilient_http_client, TimeoutError

async def handle_timeout():
    try:
        response = await resilient_http_client.get("https://slow-api.example.com")
    except TimeoutError:
        # Request took too long even after retries
        logger.error("Request timed out")
        # Fallback logic
        return cached_data
```

#### 2. CircuitBreakerOpenError
```python
from app.core.resilient_client import resilient_http_client, CircuitBreakerOpenError

async def handle_circuit_breaker():
    try:
        response = await resilient_http_client.post("https://flaky-api.example.com")
    except CircuitBreakerOpenError:
        # Too many failures, circuit is open
        logger.warning("Service degraded - using fallback")
        # Use fallback service or cached data
        return fallback_data
```

#### 3. RetryExhaustedError
```python
from app.core.resilient_client import resilient_http_client, RetryExhaustedError

async def handle_retry_exhausted():
    try:
        response = await resilient_http_client.get("https://unreliable-api.example.com")
    except RetryExhaustedError:
        # All retry attempts failed
        logger.error("Service unavailable after retries")
        # Queue for later processing
        return queue_for_retry()
```

### Best Practices for Error Handling

1. **Always handle CircuitBreakerOpenError explicitly** - This means the service is down
2. **Log TimeoutError** - Might need to increase timeout for specific operations
3. **Monitor RetryExhaustedError** - Too many retries might indicate deeper issues
4. **Use fallbacks** - Cached data, alternative services, graceful degradation

---

## Testing

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.core.resilient_client import resilient_http_client

@pytest.mark.asyncio
async def test_api_call():
    # Mock the HTTP client
    with patch.object(resilient_http_client, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = AsyncMock(
            json=AsyncMock(return_value={"id": 1, "name": "Test"})
        )

        # Call your function
        result = await fetch_user(1)

        # Assertions
        assert result["name"] == "Test"
        mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### Testing Error Handling

```python
import pytest
from app.core.resilient_client import resilient_http_client, CircuitBreakerOpenError
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_circuit_breaker_handling():
    with patch.object(
        resilient_http_client,
        'get',
        new_callable=AsyncMock,
        side_effect=CircuitBreakerOpenError("Circuit open")
    ):
        result = await fetch_user(1)
        assert result is None  # Fallback value
```

### Integration Testing with Test Server

```python
import pytest
from httpx import ASGITransport
from app.core.resilient_client import resilient_http_client

@pytest.mark.asyncio
async def test_resilience_patterns():
    # Test against actual server
    response = await resilient_http_client.get("https://httpbin.org/status/500")
    # Should retry and handle gracefully
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_timeout():
    # Test timeout handling
    from app.core.resilient_client import TimeoutError
    with pytest.raises(TimeoutError):
        await resilient_http_client.get(
            "https://httpbin.org/delay/60",
            timeout=5.0
        )
```

---

## Rollback Plan

If you encounter issues with the resilient client, you can easily rollback:

### Option 1: Disable Circuit Breaker
```python
from app.core.resilient_client import ResilientHTTPClient, HTTPRequestConfig

client = ResilientHTTPClient(
    config=HTTPRequestConfig(
        enable_circuit_breaker=False,  # Disable circuit breaker
        max_retries=0,  # Disable retries
    )
)
```

### Option 2: Use Standard httpx
```python
# Temporarily revert to standard httpx
import httpx

async def call_api(data: dict):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post("https://api.example.com", json=data)
        return response.json()
```

### Option 3: Git Revert
```bash
# Revert the migration commit
git revert <commit-hash>
```

---

## Monitoring and Observability

### Logging

The resilient client automatically logs:
- All requests with unique request IDs
- Retry attempts with wait times
- Circuit breaker state changes
- Success/failure with timing

**Example Log Output:**
```
INFO: [a1b2c3d4] POST https://api.example.com/endpoint (attempt 1/4)
WARNING: [a1b2c3d4] Got 503, retrying in 2.0s...
INFO: [a1b2c3d4] Success: POST https://api.example.com/endpoint → 200 (0.523s)
```

### Metrics to Monitor

1. **Retry Rate**: High retry rate indicates flaky services
2. **Circuit Breaker Trips**: Frequent trips indicate service issues
3. **Timeout Rate**: High timeout rate indicates performance problems
4. **Request Duration**: Track p50, p95, p99 latencies

---

## Advanced Usage

### Decorator Pattern

```python
from app.core.resilient_client import with_resilience

@with_resilience(max_retries=3, timeout=30.0, circuit_breaker=True)
async def call_external_api(data: dict):
    # Your existing HTTP code here
    async with httpx.AsyncClient() as client:
        return await client.post("https://api.example.com", json=data)
```

### Custom Circuit Breaker per Endpoint

```python
from app.core.resilient_client import ResilientHTTPClient, HTTPRequestConfig

# Different circuit breaker settings for different endpoints
primary_api_client = ResilientHTTPClient(
    config=HTTPRequestConfig(
        circuit_failure_threshold=5,
        circuit_recovery_timeout=60.0,
    )
)

backup_api_client = ResilientHTTPClient(
    config=HTTPRequestConfig(
        circuit_failure_threshold=10,  # More lenient for backup
        circuit_recovery_timeout=30.0,
    )
)
```

---

## Frequently Asked Questions

### Q: Should I use the global client or create my own instance?

**A:** Use the global `resilient_http_client` for most cases. Create your own instance only when you need:
- Different timeout/retry settings
- Separate circuit breakers for different services
- Custom configuration for specific use cases

### Q: What if the service is down?

**A:** The circuit breaker will open after `circuit_failure_threshold` failures and block requests for `circuit_recovery_timeout` seconds. This prevents cascading failures and allows the service to recover.

### Q: How do I know if retries are happening?

**A:** Check the logs. Each retry is logged with the request ID, attempt number, and wait time.

### Q: Can I disable retries for specific requests?

**A:** Yes, create a client with `max_retries=0` or use `retry=False` parameter (not implemented in base version, would need custom client).

### Q: What about streaming responses?

**A:** The resilient client supports streaming. Use `response.aiter_bytes()` or `response.aiter_lines()` as normal.

---

## Next Steps

1. **Audit your codebase** for HTTP client usage:
   ```bash
   grep -r "httpx.AsyncClient" app/
   grep -r "import httpx" app/
   grep -r "import requests" app/
   ```

2. **Update service layer files** to use resilient client

3. **Add error handling** for specific exception types

4. **Test thoroughly** in development environment

5. **Monitor metrics** in production

---

## Support and Documentation

- **Main Implementation**: `app/core/resilient_client.py`
- **Related Docs**:
  - [Circuit Breaker Pattern](./CIRCUIT_BREAKER_GUIDE.md)
  - [Rate Limiter Migration](./RATE_LIMITER_MIGRATION_GUIDE.md)
  - [Security Middleware Migration](./SECURITY_MIDDLEWARE_MIGRATION_GUIDE.md)

---

**Migration Guide Version**: 1.0
**Last Updated**: 2025-01-18
**Maintainer**: Development Team
