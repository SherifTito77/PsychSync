# API v1 Router

## Overview

Version 1 API router aggregation and configuration.

## Purpose

Central API router that aggregates all endpoint modules and applies common middleware, prefixes, and tags.

## Key Files

- **`api.py`**: Main API router aggregating all endpoint modules
- **`routes.py`**: Route configuration and inclusion
- **`deps.py`**: Shared dependencies for v1 endpoints

## Usage

```python
from app.api.v1.api import api_router

app.include_router(api_router, prefix="/api/v1")
```


## Key Components

- Router Configuration
- Endpoint Modules
- Common Middleware
- API Versioning Strategy

## Related Documentation

- [Main README](../../../README.md)
- [API Documentation](../api/README.md)
- [Services Documentation](../services/README.md)
- [Database Documentation](../db/README.md)
- [Core Documentation](../core/README.md)

## Contributing

When adding new files to this directory, please:
1. Follow existing code patterns
2. Add comprehensive docstrings
3. Update this README with key changes
4. Ensure proper error handling
5. Add tests for new functionality

## Testing

Test files in this directory using:
```bash
pytest tests/path/to/this/directory/ -v
```
