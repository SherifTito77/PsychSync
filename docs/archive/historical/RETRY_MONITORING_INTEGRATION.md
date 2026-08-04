# Integration Guide: Adding Retry Monitoring Endpoints

To add the retry monitoring endpoints to your FastAPI application, follow these steps:

## Option 1: Add to Main API Router (Recommended)

Edit `app/api/v1/api.py` and add the retry monitoring router:

```python
# In app/api/v1/api.py, add to CORE_ENDPOINTS:

CORE_ENDPOINTS = [
    # ... existing endpoints ...
    "admin/retry_monitoring",  # ✅ NEW: Retry monitoring and DLQ management
]
```

Then update the `safe_import_endpoint` function to handle nested paths:

```python
def safe_import_endpoint(module_name: str) -> APIRouter | None:
    """Safely import an endpoint module with proper error handling"""
    try:
        # Handle nested paths like "admin/retry_monitoring"
        module_path = f"app.api.v1.endpoints.{module_name.replace('/', '.')}"
        module = __import__(module_path, fromlist=[module_name.split('/')[-1]])
        router = getattr(module, "router", None)
        if router is None:
            logger.warning(f"Module {module_name} imported but no router found")
            return None
        logger.info(f"✅ Successfully imported endpoint: {module_name} with {len(router.routes)} routes")
        return router
    except ImportError as e:
        logger.warning(f"❌ Could not import endpoint {module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error importing endpoint {module_name}: {e}")
        return None
```

## Option 2: Direct Router Inclusion

In your main application file (`app/main.py`), add:

```python
from app.api.v1.endpoints.admin.retry_monitoring import router as retry_router

# Include the router
app.include_router(
    retry_router,
    prefix="/api/v1/admin",
    tags=["retry-monitoring"]
)
```

## Option 3: Add to Monitoring Module

Create `app/api/v1/endpoints/monitoring/retry.py`:

```python
"""Retry monitoring endpoints"""
from app.api.v1.endpoints.admin.retry_monitoring import router

__all__ = ["router"]
```

Then add "monitoring/retry" to FEATURE_ENDPOINTS in `app/api/v1/api.py`.

## Verification

After adding, test the endpoints:

```bash
# Health check
curl http://localhost:8000/api/v1/admin/retry/health

# Get summary
curl http://localhost:8000/api/v1/admin/retry/summary

# Prometheus metrics
curl http://localhost:8000/api/v1/admin/retry/metrics

# DLQ stats
curl http://localhost:8000/api/v1/admin/retry/dlq/stats
```

## Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'psychsync-retry-metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/admin/retry/metrics'
```

## Grafana Dashboard JSON

See `monitoring/grafana/dashboards/retry-metrics.json` for a complete dashboard configuration.

Key panels:
- Retry Rate by Component (Graph)
- Failure Rate vs Time (Graph)
- DLQ Size (Single Stat)
- Components with High Retry Rate (Table)
- Circuit Breaker Status (Stat)
