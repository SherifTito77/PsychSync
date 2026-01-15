#!/usr/bin/env python3
"""
Automated OpenAPI Documentation Enhancer
Adds comprehensive examples and response documentation to FastAPI endpoints
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple


# OpenAPI example templates for different endpoint types
EXAMPLE_TEMPLATES = {
    "auth_login": {
        "summary": "User login",
        "description": "Authenticate user with email and password, returning JWT access token",
        "request_example": {
            "email": "user@example.com",
            "password": "SecurePassword123!"
        },
        "responses": {
            200: {
                "description": "Login successful",
                "content": {
                    "application/json": {
                        "example": {
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer",
                            "user": {
                                "id": 1,
                                "email": "user@example.com",
                                "full_name": "John Doe"
                            }
                        }
                    }
                }
            },
            401: {"description": "Invalid credentials"},
            422: {"description": "Validation error"}
        }
    },

    "auth_register": {
        "summary": "Register new user",
        "description": "Create a new user account with email verification",
        "request_example": {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Jane Smith"
        },
        "responses": {
            201: {
                "description": "User registered successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 2,
                            "email": "newuser@example.com",
                            "full_name": "Jane Smith",
                            "is_active": False,
                            "message": "Please check your email to verify your account"
                        }
                    }
                }
            },
            400: {"description": "Email already registered"},
            422: {"description": "Validation error"}
        }
    },

    "users_list": {
        "summary": "List users",
        "description": "Get paginated list of users (admin/manager only)",
        "responses": {
            200: {
                "description": "Users retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "items": [
                                {
                                    "id": 1,
                                    "email": "user@example.com",
                                    "full_name": "John Doe",
                                    "is_active": True,
                                    "role": "user"
                                }
                            ],
                            "total": 1,
                            "page": 1,
                            "size": 10
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden - insufficient permissions"}
        }
    },

    "users_get": {
        "summary": "Get user by ID",
        "description": "Retrieve detailed information about a specific user",
        "responses": {
            200: {
                "description": "User retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "email": "user@example.com",
                            "full_name": "John Doe",
                            "is_active": True,
                            "role": "user",
                            "organization_id": 1,
                            "created_at": "2025-01-01T00:00:00Z"
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            404: {"description": "User not found"}
        }
    },

    "users_update": {
        "summary": "Update user",
        "description": "Update user profile information",
        "request_example": {
            "full_name": "John Smith",
            "phone": "+1234567890"
        },
        "responses": {
            200: {
                "description": "User updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "email": "user@example.com",
                            "full_name": "John Smith",
                            "phone": "+1234567890"
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            404: {"description": "User not found"},
            422: {"description": "Validation error"}
        }
    },

    "users_delete": {
        "summary": "Delete user",
        "description": "Permanently delete a user account (admin only)",
        "responses": {
            204: {"description": "User deleted successfully"},
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden - admin only"},
            404: {"description": "User not found"}
        }
    },

    "teams_list": {
        "summary": "List teams",
        "description": "Get all teams for current user's organization",
        "responses": {
            200: {
                "description": "Teams retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "items": [
                                {
                                    "id": 1,
                                    "name": "Engineering Team",
                                    "description": "Software engineering team",
                                    "organization_id": 1,
                                    "member_count": 5
                                }
                            ],
                            "total": 1
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"}
        }
    },

    "teams_create": {
        "summary": "Create team",
        "description": "Create a new team within your organization",
        "request_example": {
            "name": "Product Team",
            "description": "Product management and design team"
        },
        "responses": {
            201: {
                "description": "Team created successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 2,
                            "name": "Product Team",
                            "description": "Product management and design team",
                            "organization_id": 1,
                            "created_at": "2025-01-13T10:00:00Z"
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            422: {"description": "Validation error"}
        }
    },

    "assessments_list": {
        "summary": "List assessments",
        "description": "Get all assessments for your organization or team",
        "responses": {
            200: {
                "description": "Assessments retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "items": [
                                {
                                    "id": 1,
                                    "title": "Big Five Personality Test",
                                    "description": "Measure personality traits across 5 dimensions",
                                    "framework": "big_five",
                                    "status": "active",
                                    "question_count": 50
                                }
                            ],
                            "total": 1,
                            "page": 1
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"}
        }
    },

    "assessments_create": {
        "summary": "Create assessment",
        "description": "Create a new custom assessment",
        "request_example": {
            "title": "Custom Team Assessment",
            "description": "Evaluate team dynamics",
            "framework": "custom",
            "status": "draft"
        },
        "responses": {
            201: {
                "description": "Assessment created successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 5,
                            "title": "Custom Team Assessment",
                            "description": "Evaluate team dynamics",
                            "framework": "custom",
                            "status": "draft",
                            "created_by": 1
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            422: {"description": "Validation error"}
        }
    },

    "assessments_get": {
        "summary": "Get assessment details",
        "description": "Retrieve full assessment details including questions",
        "responses": {
            200: {
                "description": "Assessment retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "title": "Big Five Personality Test",
                            "description": "Measure personality traits",
                            "framework": "big_five",
                            "questions": [
                                {
                                    "id": 1,
                                    "text": "I am always prepared",
                                    "type": "likert",
                                    "options": [1, 2, 3, 4, 5]
                                }
                            ]
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            404: {"description": "Assessment not found"}
        }
    },

    "assessments_update": {
        "summary": "Update assessment",
        "description": "Update assessment details",
        "request_example": {
            "title": "Updated Assessment Title",
            "description": "Updated description",
            "status": "active"
        },
        "responses": {
            200: {
                "description": "Assessment updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "title": "Updated Assessment Title",
                            "description": "Updated description",
                            "status": "active",
                            "updated_at": "2025-01-13T10:00:00Z"
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            404: {"description": "Assessment not found"},
            422: {"description": "Validation error"}
        }
    },

    "assessments_delete": {
        "summary": "Delete assessment",
        "description": "Permanently delete an assessment",
        "responses": {
            204: {"description": "Assessment deleted successfully"},
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden - not your assessment"},
            404: {"description": "Assessment not found"}
        }
    },

    "responses_start": {
        "summary": "Start assessment response",
        "description": "Initialize a new response session for an assessment",
        "responses": {
            201: {
                "description": "Response session created",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 123,
                            "assessment_id": 5,
                            "user_id": 1,
                            "status": "in_progress",
                            "started_at": "2025-01-13T10:00:00Z"
                        }
                    }
                }
            },
            400: {"description": "Assessment not available"},
            401: {"description": "Unauthorized"},
            404: {"description": "Assessment not found"}
        }
    },

    "responses_submit": {
        "summary": "Submit assessment responses",
        "description": "Submit answers for an assessment",
        "request_example": {
            "responses": [
                {"question_id": 1, "value": 4},
                {"question_id": 2, "value": 5}
            ]
        },
        "responses": {
            200: {
                "description": "Responses submitted successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 123,
                            "status": "completed",
                            "score": {
                                "openness": 4.2,
                                "conscientiousness": 3.8
                            },
                            "completed_at": "2025-01-13T10:30:00Z"
                        }
                    }
                }
            },
            400: {"description": "Invalid responses"},
            401: {"description": "Unauthorized"}
        }
    },

    "predictions_train": {
        "summary": "Train prediction model",
        "description": "Train a machine learning model for predictions (admin only)",
        "request_example": {
            "model_type": "churn_prediction",
            "training_data": "historical_data",
            "parameters": {
                "epochs": 100,
                "learning_rate": 0.001
            }
        },
        "responses": {
            200: {
                "description": "Model trained successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "model_id": "model_20250113",
                            "accuracy": 0.92,
                            "training_samples": 1000,
                            "training_time_seconds": 45
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden - admin only"}
        }
    },

    "predictions_predict": {
        "summary": "Get prediction",
        "description": "Get AI-powered predictions for a user or team",
        "responses": {
            200: {
                "description": "Prediction generated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "prediction_type": "churn_risk",
                            "risk_level": "medium",
                            "confidence": 0.78,
                            "factors": [
                                {"factor": "low_engagement", "impact": 0.6},
                                {"factor": "declining_scores", "impact": 0.4}
                            ]
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            404: {"description": "User/team not found"}
        }
    },

    "optimizer_optimize": {
        "summary": "Optimize team composition",
        "description": "Get AI-powered team optimization recommendations",
        "responses": {
            200: {
                "description": "Optimization analysis completed",
                "content": {
                    "application/json": {
                        "example": {
                            "current_composition_score": 72,
                            "optimized_score": 89,
                            "recommendations": [
                                {
                                    "type": "add_member",
                                    "personality_type": "conscientious",
                                    "reason": "Balance team diversity"
                                }
                            ],
                            "potential_improvements": {
                                "communication": "+15%",
                                "productivity": "+12%"
                            }
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            404: {"description": "Team not found"}
        }
    },

    "analytics_dashboard": {
        "summary": "Get analytics dashboard data",
        "description": "Retrieve comprehensive analytics for organization or team",
        "responses": {
            200: {
                "description": "Analytics data retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "overview": {
                                "total_users": 150,
                                "active_assessments": 25,
                                "completion_rate": 0.78
                            },
                            "trends": [
                                {"date": "2025-01-01", "completions": 45},
                                {"date": "2025-01-02", "completions": 52}
                            ],
                            "top_performers": [
                                {"user_id": 1, "score": 95},
                                {"user_id": 2, "score": 92}
                            ]
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"}
        }
    },

    "health_check": {
        "summary": "Health check endpoint",
        "description": "Check API and database connectivity status",
        "responses": {
            200: {
                "description": "System is healthy",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "healthy",
                            "database": "connected",
                            "redis": "connected",
                            "timestamp": "2025-01-13T10:00:00Z"
                        }
                    }
                }
            }
        }
    },

    "default_success": {
        "responses": {
            200: {
                "description": "Request successful",
                "content": {
                    "application/json": {
                        "example": {
                            "success": True,
                            "message": "Operation completed successfully"
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            422: {"description": "Validation error"}
        }
    },

    "default_created": {
        "responses": {
            201: {
                "description": "Resource created successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "created_at": "2025-01-13T10:00:00Z"
                        }
                    }
                }
            },
            401: {"description": "Unauthorized"},
            422: {"description": "Validation error"}
        }
    },

    "default_deleted": {
        "responses": {
            204: {"description": "Resource deleted successfully"},
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"},
            404: {"description": "Resource not found"}
        }
    }
}


def detect_endpoint_type(file_path: str, function_name: str) -> str:
    """Detect the type of endpoint based on file and function name."""
    file_name = Path(file_path).stem

    # Auth endpoints
    if "auth" in file_name:
        if "login" in function_name:
            return "auth_login"
        elif "register" in function_name:
            return "auth_register"

    # User endpoints
    if "user" in file_name:
        if "list" in function_name or "get_multi" in function_name:
            return "users_list"
        elif "get" in function_name and "by_id" in function_name:
            return "users_get"
        elif "update" in function_name:
            return "users_update"
        elif "delete" in function_name:
            return "users_delete"

    # Team endpoints
    if "team" in file_name:
        if "list" in function_name or "get_multi" in function_name:
            return "teams_list"
        elif "create" in function_name:
            return "teams_create"

    # Assessment endpoints
    if "assessment" in file_name:
        if "list" in function_name or "get_multi" in function_name:
            return "assessments_list"
        elif "create" in function_name:
            return "assessments_create"
        elif "get" in function_name and "by_id" in function_name:
            return "assessments_get"
        elif "update" in function_name:
            return "assessments_update"
        elif "delete" in function_name:
            return "assessments_delete"

    # Response endpoints
    if "response" in file_name:
        if "start" in function_name:
            return "responses_start"
        elif "submit" in function_name:
            return "responses_submit"

    # Prediction endpoints
    if "prediction" in file_name:
        if "train" in function_name:
            return "predictions_train"
        elif "predict" in function_name:
            return "predictions_predict"

    # Optimizer endpoints
    if "optimizer" in file_name or "optimization" in function_name:
        return "optimizer_optimize"

    # Analytics endpoints
    if "analytics" in file_name or "dashboard" in function_name:
        return "analytics_dashboard"

    # Health check
    if "health" in file_name or function_name == "health_check":
        return "health_check"

    # Default patterns based on HTTP method
    if "create" in function_name or "add" in function_name:
        return "default_created"
    elif "delete" in function_name or "remove" in function_name:
        return "default_deleted"
    else:
        return "default_success"


def add_openapi_to_file(file_path: str) -> Tuple[int, int]:
    """Add OpenAPI documentation to a single endpoint file."""
    with open(file_path, 'r') as f:
        content = f.read()

    modified_count = 0
    endpoint_count = 0

    # Find all @router.get/post/delete/put/patch decorators
    pattern = r'@router\.(get|post|delete|put|patch)\(\s*[\'"](/[^\'\"]*)[\'"]\s*,?\s*([^)]*)\)'

    def replace_decorator(match):
        nonlocal modified_count, endpoint_count
        method = match.group(1)
        path = match.group(2)
        existing_params = match.group(3)
        endpoint_count += 1

        # Skip if already has responses or examples
        if 'responses=' in existing_params or 'example=' in existing_params:
            return match.group(0)

        # Detect endpoint type
        function_name_match = re.search(r'def\s+(\w+)\s*\(', content[match.end():match.end()+100])
        function_name = function_name_match.group(1) if function_name_match else "unknown"

        endpoint_type = detect_endpoint_type(file_path, function_name)
        template = EXAMPLE_TEMPLATES.get(endpoint_type, EXAMPLE_TEMPLATES["default_success"])

        # Build new decorator
        new_params = []

        # Add summary if available
        if "summary" in template:
            new_params.append(f'\n    summary="{template["summary"]}",')

        # Add description if available
        if "description" in template:
            new_params.append(f'\n    description="{template["description"]}",')

        # Add responses
        if "responses" in template:
            responses_str = str(template["responses"]).replace("True", "true").replace("False", "false")
            new_params.append(f'\n    responses={responses_str},')

        # Keep existing parameters
        if existing_params.strip():
            new_params.append(f'\n    {existing_params.strip()},')

        new_decorator = f'@router.{method}(\n    "{path}",' + ''.join(new_params) + '\n)'
        modified_count += 1

        return new_decorator

    new_content = re.sub(pattern, replace_decorator, content)

    if modified_count > 0:
        with open(file_path, 'w') as f:
            f.write(new_content)

    return modified_count, endpoint_count


def main():
    """Process all endpoint files and add OpenAPI documentation."""
    base_path = Path("/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints")

    total_modified = 0
    total_endpoints = 0
    files_processed = 0

    print("📝 Adding OpenAPI Documentation to Endpoints")
    print("="*60)

    for endpoint_file in base_path.glob("*.py"):
        if endpoint_file.name == "__init__.py":
            continue

        try:
            modified, endpoints = add_openapi_to_file(str(endpoint_file))
            if endpoints > 0:
                files_processed += 1
                total_modified += modified
                total_endpoints += endpoints
                if modified > 0:
                    print(f"✅ {endpoint_file.name}: Enhanced {modified}/{endpoints} endpoints")
                else:
                    print(f"⏭️  {endpoint_file.name}: Already documented ({endpoints} endpoints)")
        except Exception as e:
            print(f"❌ {endpoint_file.name}: Error - {e}")

    print("\n" + "="*60)
    print(f"📊 Documentation Enhancement Complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Total endpoints: {total_endpoints}")
    print(f"   Enhanced: {total_modified}")
    print(f"   Already documented: {total_endpoints - total_modified}")
    print("="*60)


if __name__ == "__main__":
    main()
