# PsychSync API Layer

## Overview

The API layer provides RESTful endpoints for the PsychSync psychological assessment platform. This directory contains all route definitions, request/response schemas, and API integration logic.

## Architecture

```
app/api/
├── v1/                    # API version 1
│   ├── api.py            # Main router aggregator
│   ├── deps.py           # Dependency injections (auth, db, etc.)
│   └── endpoints/        # Individual endpoint modules
│       ├── auth.py       # Authentication endpoints
│       ├── assessments.py # Assessment management
│       ├── responses.py  # Response submission
│       └── ...           # Other feature endpoints
└── ...
```

## Key Components

### Router Aggregator (`api.py`)
- **Purpose**: Centralizes all endpoint registration
- **Features**:
  - Modular endpoint inclusion
  - Error handling for broken endpoint files
  - Prefix management (`/api/v1`)
  - Route organization (CORE, FEATURE, SEPARATED_SERVICE)

### Dependencies (`deps.py`)
- **Purpose**: Provides reusable dependencies for route handlers
- **Common Dependencies**:
  - `get_db()`: Database session
  - `get_current_user()`: Authenticated user
  - `get_current_active_user()`: Active user verification

### Endpoint Modules (`endpoints/`)
Each file contains related endpoints:
- **auth.py**: Login, registration, token refresh
- **assessments.py**: CRUD for psychological assessments
- **responses.py**: Assessment response submission
- **teams.py**: Team and organization management
- And 40+ other feature-specific modules

## Usage Example

```python
from fastapi import APIRouter, Depends
from app.api.v1.deps import get_db, get_current_user
from app.db.models import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/items/{item_id}")
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an item by ID"""
    # Implementation here
    pass
```

## Adding New Endpoints

1. **Create new endpoint file** in `app/api/v1/endpoints/`
2. **Define router** with prefix and tags:
   ```python
   router = APIRouter(prefix="/feature", tags=["Feature Name"])
   ```
3. **Add endpoints** using decorators:
   - `@router.get()`, `@router.post()`, etc.
   - Include proper response models and status codes
4. **Register** in `app/api/v1/api.py`:
   ```python
   FEATURE_ENDPOINTS = ["your_new_feature"]
   ```

## Response Documentation

Always include response schemas:

```python
@router.delete("/{item_id}",
             responses={
                 200: {"description": "Item deleted successfully"},
                 404: {"description": "Item not found"},
                 403: {"description": "Permission denied"}
             })
async def delete_item(item_id: int):
    pass
```

## API Versioning

Current version: **v1** (`/api/v1/*`)

Versioning strategy:
- URL-based versioning (recommended)
- Backwards compatibility maintained within major versions
- Deprecation notices for old endpoints

## Error Handling

All endpoints use standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Related Documentation

- [OpenAPI Spec](../../../openapi.json) - Full API documentation
- [Core Architecture](../core/README.md) - Application structure
- [Database Models](../db/models/README.md) - Data models

## Maintenance

- **Test endpoints**: Use the automated syntax checker
  ```bash
  check-api
  ```
- **Regenerate docs**: After adding endpoints
  ```bash
  python generate_openapi_spec.py
  ```
- **View API docs**: http://localhost:8000/docs
