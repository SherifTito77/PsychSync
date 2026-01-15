# CRUD Operations Layer

## Overview

Database CRUD (Create, Read, Update, Delete) operations using SQLAlchemy.

## Purpose

Provides a clean abstraction layer between API endpoints and the database. Encapsulates all database access logic using SQLAlchemy's async patterns.

## Key Files

- **`crud_user.py`**: User CRUD operations
- **`organization.py`**: Organization CRUD operations
- **`tenant_aware.py`**: Base class for tenant-scoped CRUD operations
- **`crud_code_quality.py`**: Code quality metrics CRUD
- **`crud_sql_audit.py`**: SQL query audit logging CRUD
- **`crud_query_performance.py`**: Query performance tracking CRUD
- **`crud_build_analysis.py`**: Build analysis data CRUD
- **`crud_caching_config.py`**: Caching configuration CRUD
- **`crud_breaking_changes.py`**: Breaking changes tracking CRUD

## Usage

```python
from app.crud.crud_user import user_crud
from app.db.models import User

async def get_user(db: AsyncSession, user_id: int):
    return await user_crud.get(db, id=user_id)
```


## Key Components

- CRUD Base Classes
- User Operations
- Organization Operations
- Tenant-Aware Operations
- Analytics CRUD
- Product Operations CRUD

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
