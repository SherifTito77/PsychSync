# API Dependencies

## Overview

FastAPI dependency injection functions for authentication, database sessions, and common endpoint dependencies.

## Purpose

Provides reusable dependency functions for FastAPI endpoints using the `Depends()` pattern. Centralizes authentication, authorization, and resource access logic.

## Key Files

- **`auth.py`**: Authentication dependencies - get_current_user, get_current_active_user, require_role
- **`__init__.py`**: Package initialization and exports

## Usage

```python
from fastapi import Depends
from app.api.dependencies.auth import get_current_user, get_current_active_user

@router.get("/users/me")
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user
```


## Key Components

- Authentication Flow
- Authorization & Role-Based Access
- Database Session Management
- Tenant Context Management
- Rate Limiting Dependencies

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
