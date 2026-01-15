#!/usr/bin/env python3
"""
Enhance Critical Endpoints with Comprehensive Examples
Adds request/response examples to the most important API endpoints
"""

import re
from pathlib import Path


def enhance_auth_endpoints():
    """Enhance authentication endpoints with examples."""
    file_path = "app/api/v1/endpoints/auth.py"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return

    # Check if already enhanced
    if '"example"' in content or 'schema_extra' in content:
        print("⏭️  auth.py already enhanced")
        return

    modifications = 0

    # Enhance login endpoint
    login_pattern = r'(@router\.post\("/token[^"]*"\))'
    login_replacement = r'''\1
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect email or password"}
                }
            }
        }
    }'''

    if re.search(login_pattern, content):
        content = re.sub(login_pattern, login_replacement, content, count=1)
        modifications += 1

    # Enhance register endpoint
    register_pattern = r'(@router\.post\("/register[^"]*"\))'
    register_replacement = r'''\1
    responses={
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
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        }
    }'''

    if re.search(register_pattern, content):
        content = re.sub(register_pattern, register_replacement, content, count=1)
        modifications += 1

    if modifications > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Enhanced auth.py: +{modifications} endpoint examples")


def enhance_users_endpoints():
    """Enhance user management endpoints."""
    file_path = "app/api/v1/endpoints/users.py"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return

    if '"example"' in content:
        print("⏭️  users.py already enhanced")
        return

    modifications = 0

    # Enhance list users endpoint
    list_pattern = r'(@router\.get\("/"\s*))'
    list_replacement = r'''\1
    responses={
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
                                "role": "user",
                                "created_at": "2025-01-01T00:00:00Z"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "size": 10
                    }
                }
            }
        }
    }'''

    if re.search(list_pattern, content):
        content = re.sub(list_pattern, list_replacement, content, count=1)
        modifications += 1

    # Enhance get user endpoint
    get_pattern = r'(@router\.get\("/{{id}}"\s*))'
    get_replacement = r'''\1
    responses={
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
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        }
    }'''

    if re.search(get_pattern, content):
        content = re.sub(get_pattern, get_replacement, content, count=1)
        modifications += 1

    if modifications > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Enhanced users.py: +{modifications} endpoint examples")


def enhance_teams_endpoints():
    """Enhance team management endpoints."""
    file_path = "app/api/v1/endpoints/teams.py"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return

    if '"example"' in content:
        print("⏭️  teams.py already enhanced")
        return

    modifications = 0

    # Enhance create team endpoint
    create_pattern = r'(@router\.post\("/"\s*))'
    create_replacement = r'''\1
    responses={
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
        }
    }'''

    if re.search(create_pattern, content):
        content = re.sub(create_pattern, create_replacement, content, count=1)
        modifications += 1

    if modifications > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Enhanced teams.py: +{modifications} endpoint examples")


def enhance_assessments_endpoints():
    """Enhance assessment endpoints."""
    file_path = "app/api/v1/endpoints/assessments.py"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return

    if '"example"' in content:
        print("⏭️  assessments.py already enhanced")
        return

    modifications = 0

    # Enhance list assessments endpoint
    list_pattern = r'(@router\.get\("/"\s*))'
    list_replacement = r'''\1
    responses={
        200: {
            "description": "Assessments retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "title": "Big Five Personality Test",
                                "description": "Measure personality traits",
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
        }
    }'''

    if re.search(list_pattern, content):
        content = re.sub(list_pattern, list_replacement, content, count=1)
        modifications += 1

    if modifications > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Enhanced assessments.py: +{modifications} endpoint examples")


def enhance_responses_endpoints():
    """Enhance response submission endpoints."""
    file_path = "app/api/v1/endpoints/responses.py"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return

    if '"example"' in content:
        print("⏭️  responses.py already enhanced")
        return

    modifications = 0

    # Enhance start response endpoint
    start_pattern = r'(@router\.post\("/start"\s*))'
    start_replacement = r'''\1
    responses={
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
        }
    }'''

    if re.search(start_pattern, content):
        content = re.sub(start_pattern, start_replacement, content, count=1)
        modifications += 1

    if modifications > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Enhanced responses.py: +{modifications} endpoint examples")


def main():
    """Enhance all critical endpoints."""
    print("🚀 Enhancing Critical Endpoints with Examples")
    print("="*60)

    print("\n📝 Authentication Endpoints:")
    enhance_auth_endpoints()

    print("\n👥 User Management:")
    enhance_users_endpoints()

    print("\n👨‍👩‍👧‍👦 Team Management:")
    enhance_teams_endpoints()

    print("\n📋 Assessment Management:")
    enhance_assessments_endpoints()

    print("\n✅ Response Submission:")
    enhance_responses_endpoints()

    print("\n" + "="*60)
    print("✅ Endpoint Enhancement Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
