# OpenAPI Enhancement Guide

This guide provides examples and patterns for enhancing OpenAPI documentation across all endpoints.

## Request Body Examples Pattern

```python
@router.post("/endpoint")
async def create_resource(
    request: RequestSchema
):
    '''
    Create a new resource.

    **Request Body Example:**
    ```json
    {
        "field1": "value1",
        "field2": "value2"
    }
    ```

    **Response 201:**
    ```json
    {
        "id": 1,
        "field1": "value1",
        "created_at": "2025-01-13T10:00:00Z"
    }
    ```

    **Response 400:**
    ```json
    {
        "detail": "Validation error message"
    }
    ```
    '''
```

## Query Parameter Documentation Pattern

```python
@router.get("/endpoint")
async def list_resources(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter results")
):
    '''
    List resources with pagination and filtering.

    **Query Parameters:**
    - `skip`: Integer ≥ 0, default=0 - Number of records to skip
    - `limit`: Integer 1-100, default=10 - Maximum records per page
    - `search`: Optional string - Search filter

    **Response 200:**
    Returns paginated list of resources.
    '''
```

## Schema Examples Pattern

```python
class UserCreate(BaseModel):
    '''Schema for creating a new user.

    **Example:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    }
    ```
    '''
    email: EmailStr
    password: str
    full_name: str

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }
```

## Response Documentation Pattern

```python
@router.get(
    "/endpoint/{id}",
    responses={
        200: {
            "description": "Resource retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Example Resource"
                    }
                }
            }
        },
        404: {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Resource with ID 999 not found"
                    }
                }
            }
        }
    }
)
```
