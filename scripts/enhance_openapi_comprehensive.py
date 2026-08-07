#!/usr/bin/env python3
"""
Comprehensive OpenAPI Enhancement
Adds examples, descriptions, and detailed parameters to critical endpoints
"""

import json
from pathlib import Path
from typing import Any, Dict, List

# Critical endpoints that need comprehensive documentation
CRITICAL_ENDPOINTS = {
    "auth": [
        ("POST /api/v1/auth/token", "Login endpoint - get access token"),
        ("POST /api/v1/auth/register", "Register new user account"),
        ("POST /api/v1/auth/refresh", "Refresh access token"),
        ("POST /api/v1/auth/password-reset", "Request password reset"),
        ("GET /api/v1/auth/me", "Get current user profile"),
    ],
    "users": [
        ("GET /api/v1/users/", "List all users (paginated)"),
        ("GET /api/v1/users/{id}", "Get user by ID"),
        ("PUT /api/v1/users/{id}", "Update user profile"),
        ("DELETE /api/v1/users/{id}", "Delete user account"),
        ("GET /api/v1/users/me", "Get current user details"),
    ],
    "teams": [
        ("GET /api/v1/teams/", "List all teams"),
        ("POST /api/v1/teams/", "Create new team"),
        ("GET /api/v1/teams/{id}", "Get team details"),
        ("PUT /api/v1/teams/{id}", "Update team"),
        ("DELETE /api/v1/teams/{id}", "Delete team"),
        ("POST /api/v1/teams/{id}/members", "Add team member"),
        ("DELETE /api/v1/teams/{id}/members/{user_id}", "Remove team member"),
    ],
    "assessments": [
        ("GET /api/v1/assessments/", "List all assessments"),
        ("POST /api/v1/assessments/", "Create new assessment"),
        ("GET /api/v1/assessments/{id}", "Get assessment details"),
        ("PUT /api/v1/assessments/{id}", "Update assessment"),
        ("DELETE /api/v1/assessments/{id}", "Delete assessment"),
        ("POST /api/v1/assessments/{id}/duplicate", "Duplicate assessment"),
        ("GET /api/v1/assessments/templates", "List assessment templates"),
    ],
    "responses": [
        ("POST /api/v1/responses/start", "Start assessment response"),
        ("POST /api/v1/responses/{response_id}/submit", "Submit assessment answers"),
        ("GET /api/v1/responses/{response_id}", "Get response details"),
        ("GET /api/v1/responses/", "List user responses"),
    ],
    "analytics": [
        ("GET /api/v1/analytics/dashboard", "Get analytics dashboard data"),
        ("GET /api/v1/analytics/team/{team_id}", "Get team analytics"),
        ("GET /api/v1/analytics/user/{user_id}", "Get user analytics"),
        ("POST /api/v1/analytics/report", "Generate custom report"),
    ],
    "predictions": [
        ("POST /api/v1/predictions/train", "Train ML model"),
        ("POST /api/v1/predictions/predict", "Get predictions"),
        ("GET /api/v1/predictions/models", "List available models"),
    ],
    "optimizer": [
        ("POST /api/v1/optimizer/optimize", "Optimize team composition"),
        ("GET /api/v1/optimizer/recommendations/{team_id}", "Get recommendations"),
    ],
    "admin": [
        ("GET /api/v1/admin/metrics", "Get system metrics"),
        ("GET /api/v1/admin/users", "Manage all users"),
        ("GET /api/v1/admin/health", "System health check"),
    ],
    "health": [
        ("GET /api/v1/health/public", "Public health check"),
        ("GET /api/v1/health", "Detailed health check"),
    ],
}

# Comprehensive examples for different endpoint types
ENDPOINT_EXAMPLES = {
    # Auth endpoints
    "POST /api/v1/auth/token": {
        "request": {
            "username": "user@example.com",
            "password": "SecurePass123!",
            "grant_type": "password",
        },
        "responses": {
            200: {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                },
            },
            401: {"detail": "Incorrect email or password"},
        },
    },
    "POST /api/v1/auth/register": {
        "request": {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Smith",
            "organization_name": "Acme Corp",
        },
        "responses": {
            201: {
                "id": 2,
                "email": "newuser@example.com",
                "full_name": "Jane Smith",
                "is_active": False,
                "message": "Please check your email to verify your account",
            },
            400: {"detail": "Email already registered"},
        },
    },
    "GET /api/v1/users/": {
        "parameters": {
            "skip": {
                "description": "Number of records to skip (pagination)",
                "example": 0,
                "schema": {"type": "integer"},
            },
            "limit": {
                "description": "Maximum number of records to return",
                "example": 10,
                "schema": {"type": "integer"},
            },
            "search": {
                "description": "Search term to filter users",
                "example": "john",
                "schema": {"type": "string"},
            },
            "role": {
                "description": "Filter by user role",
                "example": "user",
                "schema": {"type": "string", "enum": ["user", "admin", "manager"]},
            },
        },
        "responses": {
            200: {
                "items": [
                    {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "role": "user",
                        "created_at": "2025-01-01T00:00:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
            }
        },
    },
    "GET /api/v1/teams/": {
        "parameters": {
            "skip": {"description": "Number of teams to skip", "example": 0},
            "limit": {"description": "Maximum teams to return", "example": 20},
            "organization_id": {"description": "Filter by organization", "example": 1},
        },
        "responses": {
            200: {
                "items": [
                    {
                        "id": 1,
                        "name": "Engineering Team",
                        "description": "Software engineering team",
                        "organization_id": 1,
                        "member_count": 8,
                        "created_at": "2025-01-01T00:00:00Z",
                    }
                ],
                "total": 1,
            }
        },
    },
    "POST /api/v1/teams/": {
        "request": {
            "name": "Product Team",
            "description": "Product management and design team",
            "organization_id": 1,
        },
        "responses": {
            201: {
                "id": 2,
                "name": "Product Team",
                "description": "Product management and design team",
                "organization_id": 1,
                "created_at": "2025-01-13T10:00:00Z",
            }
        },
    },
    "GET /api/v1/assessments/": {
        "parameters": {
            "skip": {"description": "Number of assessments to skip", "example": 0},
            "limit": {"description": "Maximum assessments to return", "example": 20},
            "framework": {
                "description": "Filter by assessment framework",
                "example": "big_five",
            },
            "status": {"description": "Filter by status", "example": "active"},
        },
        "responses": {
            200: {
                "items": [
                    {
                        "id": 1,
                        "title": "Big Five Personality Test",
                        "description": "Measure personality traits across OCEAN dimensions",
                        "framework": "big_five",
                        "status": "active",
                        "question_count": 50,
                        "estimated_duration_minutes": 15,
                    }
                ],
                "total": 1,
            }
        },
    },
    "POST /api/v1/assessments/": {
        "request": {
            "title": "Custom Leadership Assessment",
            "description": "Evaluate leadership potential",
            "framework": "custom",
            "status": "draft",
            "questions": [
                {
                    "text": "I motivate my team effectively",
                    "type": "likert",
                    "options": [1, 2, 3, 4, 5],
                }
            ],
        },
        "responses": {
            201: {
                "id": 10,
                "title": "Custom Leadership Assessment",
                "description": "Evaluate leadership potential",
                "framework": "custom",
                "status": "draft",
                "created_by": 1,
                "created_at": "2025-01-13T10:00:00Z",
            }
        },
    },
    "POST /api/v1/responses/start": {
        "request": {"assessment_id": 1, "user_id": 1},
        "responses": {
            201: {
                "id": 123,
                "assessment_id": 1,
                "user_id": 1,
                "status": "in_progress",
                "started_at": "2025-01-13T10:00:00Z",
                "estimated_completion_minutes": 15,
            }
        },
    },
    "POST /api/v1/responses/{response_id}/submit": {
        "request": {
            "answers": [
                {"question_id": 1, "value": 4},
                {"question_id": 2, "value": 5},
                {"question_id": 3, "value": 3},
            ]
        },
        "responses": {
            200: {
                "id": 123,
                "status": "completed",
                "score": {
                    "openness": 4.2,
                    "conscientiousness": 3.8,
                    "extraversion": 4.0,
                    "agreeableness": 3.5,
                    "neuroticism": 2.8,
                },
                "completed_at": "2025-01-13T10:30:00Z",
                "interpretation": "Your personality shows high openness and conscientiousness...",
            }
        },
    },
    "GET /api/v1/analytics/dashboard": {
        "parameters": {
            "period": {
                "description": "Time period for analytics",
                "example": "30d",
                "enum": ["7d", "30d", "90d", "1y"],
            },
            "organization_id": {"description": "Filter by organization", "example": 1},
        },
        "responses": {
            200: {
                "overview": {
                    "total_users": 150,
                    "active_assessments": 25,
                    "completion_rate": 0.78,
                    "avg_score": 82.5,
                },
                "trends": [
                    {"date": "2025-01-01", "completions": 45},
                    {"date": "2025-01-02", "completions": 52},
                ],
                "top_performers": [
                    {"user_id": 1, "name": "John Doe", "score": 95},
                    {"user_id": 2, "name": "Jane Smith", "score": 92},
                ],
            }
        },
    },
    "POST /api/v1/predictions/train": {
        "request": {
            "model_type": "churn_prediction",
            "training_data": {"source": "historical_data", "time_period": "6m"},
            "parameters": {"epochs": 100, "learning_rate": 0.001, "test_split": 0.2},
        },
        "responses": {
            200: {
                "model_id": "churn_model_20250113",
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.87,
                "f1_score": 0.88,
                "training_samples": 1000,
                "training_time_seconds": 45,
                "created_at": "2025-01-13T10:00:00Z",
            }
        },
    },
    "POST /api/v1/optimizer/optimize": {
        "request": {
            "team_id": 1,
            "optimization_goals": ["communication", "productivity", "innovation"],
            "constraints": {"max_team_size": 10, "min_diversity_score": 0.7},
        },
        "responses": {
            200: {
                "team_id": 1,
                "current_score": 72,
                "optimized_score": 89,
                "improvement": "+23%",
                "recommendations": [
                    {
                        "type": "add_member",
                        "personality_type": "conscientious",
                        "reason": "Balance team diversity",
                        "impact": "+8%",
                    },
                    {
                        "type": "remove_member",
                        "user_id": 5,
                        "reason": "Skill redundancy",
                        "impact": "+3%",
                    },
                ],
                "projected_improvements": {
                    "communication": "+15%",
                    "productivity": "+12%",
                    "innovation": "+18%",
                },
            }
        },
    },
    "GET /api/v1/health/public": {
        "responses": {200: {"status": "healthy", "timestamp": "2025-01-13T10:00:00Z"}}
    },
    "GET /api/v1/health": {
        "responses": {
            200: {
                "status": "healthy",
                "version": "1.0.0",
                "database": {"status": "connected", "latency_ms": 5},
                "redis": {"status": "connected", "latency_ms": 1},
                "timestamp": "2025-01-13T10:00:00Z",
            }
        }
    },
}

# Schema examples
SCHEMA_EXAMPLES = {
    "UserCreate": {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe",
    },
    "UserUpdate": {
        "full_name": "John Smith",
        "phone": "+1234567890",
        "bio": "Software engineer passionate about psychology",
    },
    "UserResponse": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_active": True,
        "role": "user",
        "created_at": "2025-01-01T00:00:00Z",
    },
    "TeamCreate": {
        "name": "Engineering Team",
        "description": "Software development team",
    },
    "TeamResponse": {
        "id": 1,
        "name": "Engineering Team",
        "description": "Software development team",
        "organization_id": 1,
        "member_count": 8,
        "created_at": "2025-01-01T00:00:00Z",
    },
    "AssessmentCreate": {
        "title": "Big Five Personality Test",
        "description": "Measure personality traits",
        "framework": "big_five",
        "status": "active",
    },
    "AssessmentResponse": {
        "id": 1,
        "title": "Big Five Personality Test",
        "description": "Measure personality traits",
        "framework": "big_five",
        "question_count": 50,
    },
    "ResponseSubmit": {
        "answers": [{"question_id": 1, "value": 4}, {"question_id": 2, "value": 5}]
    },
    "LoginRequest": {"username": "user@example.com", "password": "SecurePass123!"},
    "TokenResponse": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800,
    },
}


def generate_openapi_enhancement_guide():
    """Generate a guide for manual OpenAPI enhancement."""
    guide = """# OpenAPI Enhancement Guide

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
"""

    with open("docs/OPENAPI_ENHANCEMENT_GUIDE.md", "w") as f:
        f.write(guide)

    print("✅ Created OpenAPI Enhancement Guide")


def main():
    """Main execution."""
    print("📚 OpenAPI Enhancement Toolkit")
    print("=" * 60)
    print(f"\n📋 Identified {len(CRITICAL_ENDPOINTS)} endpoint categories")
    print(
        f"📊 Total critical endpoints: {sum(len(endpoints) for endpoints in CRITICAL_ENDPOINTS.values())}"
    )
    print(f"📝 Schema examples: {len(SCHEMA_EXAMPLES)} schemas\n")

    # Generate enhancement guide
    generate_openapi_enhancement_guide()

    print("\n" + "=" * 60)
    print("🎯 Enhancement Strategy:")
    print("=" * 60)
    print("\n1. ✅ Endpoint examples: Generated for critical endpoints")
    print("2. ✅ Schema examples: Generated for common schemas")
    print("3. ✅ Enhancement guide: Created documentation")
    print("\nNext steps:")
    print("- Apply examples to endpoint files")
    print("- Add parameter descriptions")
    print("- Enhance schema definitions")
    print("- Regenerate OpenAPI spec")
    print("- Run final verification")


if __name__ == "__main__":
    main()
