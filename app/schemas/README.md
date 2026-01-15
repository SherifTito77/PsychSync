# Pydantic Schemas

## Overview

Request/response validation schemas using Pydantic.

## Purpose

Defines data validation schemas for API requests and responses. Ensures type safety, validation, and automatic OpenAPI documentation generation.

## Key Files

- **`user.py`**: User schemas - UserCreate, UserUpdate, UserResponse
- **`auth.py`**: Authentication schemas - login, register, token
- **`team.py`**: Team and team member schemas
- **`assessment.py`**: Assessment schemas
- **`response.py`**: Assessment response schemas
- **`prediction.py`**: Prediction result schemas
- **`team_optimization.py`**: Team optimization schemas
- **`user_service.py`**: User service metrics schemas
- **`onboarding.py`**: Onboarding progress schemas
- **`team_personality.py`**: Team personality analysis schemas
- **`code_quality.py`**: Code quality metric schemas
- **`jira_integration.py`**: Jira integration schemas
- **`sql_audit.py`**: SQL audit schemas
- **`query_performance.py`**: Query performance schemas
- **`build_analysis.py`**: Build analysis schemas
- **`caching_config.py`**: Caching configuration schemas
- **`breaking_changes.py`**: Breaking changes schemas

## Usage

```python
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserCreate, UserResponse

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
```


## Key Components

- Base Schema Classes
- Authentication Schemas
- User & Team Schemas
- Assessment Schemas
- Analytics Schemas
- Integration Schemas
- Product Operations Schemas

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
