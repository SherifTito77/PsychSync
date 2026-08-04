#!/usr/bin/env python3
"""
Apply OpenAPI Enhancements to Code
Automatically enhances endpoints and schemas with examples and documentation
"""

import re
from pathlib import Path

# Enhancements to apply to schema files
SCHEMA_ENHANCEMENTS = {
    "app/schemas/user.py": {
        "UserCreate": """    '''
    Schema for creating a new user.

    **Example:**
    ```json
    {{
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    }}
    ```

    **Fields:**
    - email: User's email address (must be unique)
    - password: User's password (min 8 characters)
    - full_name: User's full name
    '''
    """,
        "UserUpdate": """    '''
    Schema for updating user information.

    **Example:**
    ```json
    {{
        "full_name": "John Smith",
        "phone": "+1234567890",
        "bio": "Software engineer"
    }}
    ```

    **Fields:**
    - full_name: Updated full name (optional)
    - phone: Phone number (optional)
    - bio: User biography (optional)
    - All fields are optional
    '''
    """,
        "UserResponse": """    '''
    Schema for user response data.

    **Example:**
    ```json
    {{
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_active": true,
        "role": "user",
        "created_at": "2025-01-01T00:00:00Z"
    }}
    ```
    '''
    """,
    },
    "app/schemas/auth.py": {
        "LoginRequest": """    '''
    Schema for user login request.

    **Example:**
    ```json
    {{
        "username": "user@example.com",
        "password": "SecurePass123!"
    }}
    ```
    '''
    """,
        "TokenResponse": """    '''
    Schema for authentication token response.

    **Example:**
    ```json
    {{
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800
    }}
    ```
    '''
    """,
    },
    "app/schemas/team.py": {
        "TeamCreate": """    '''
    Schema for creating a team.

    **Example:**
    ```json
    {{
        "name": "Engineering Team",
        "description": "Software development team"
    }}
    ```
    '''
    """,
        "TeamResponse": """    '''
    Schema for team response.

    **Example:**
    ```json
    {{
        "id": 1,
        "name": "Engineering Team",
        "description": "Software development team",
        "organization_id": 1,
        "member_count": 8,
        "created_at": "2025-01-01T00:00:00Z"
    }}
    ```
    '''
    """,
    },
    "app/schemas/response.py": {
        "ResponseCreate": """    '''
    Schema for starting an assessment response.

    **Example:**
    ```json
    {{
        "assessment_id": 1,
        "user_id": 1
    }}
    ```
    '''
    """,
        "ResponseSubmit": """    '''
    Schema for submitting assessment answers.

    **Example:**
    ```json
    {{
        "answers": [
            {{"question_id": 1, "value": 4}},
            {{"question_id": 2, "value": 5}}
        ]
    }}
    ```
    '''
    """,
    },
}


def enhance_schema_file(file_path: str, enhancements: dict):
    """Add docstrings and examples to schema classes."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return 0

    modifications = 0

    for class_name, docstring in enhancements.items():
        # Pattern to find class definition
        pattern = rf'(class {class_name}\(BaseModel\):\s*\n\s*)"""'

        if re.search(pattern, content):
            # Already has docstring, skip
            continue

        # Pattern to find class without docstring
        pattern = rf"(class {class_name}\(BaseModel\):\s*\n)"

        def add_docstring(match):
            nonlocal modifications
            modifications += 1
            return match.group(1) + docstring + "\n"

        content = re.sub(pattern, add_docstring, content, count=1)

    if modifications > 0:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Enhanced {file_path}: +{modifications} docstrings")
    else:
        print(f"⏭️  {file_path}: Already documented")

    return modifications


def enhance_endpoint_with_examples(file_path: str, endpoint_name: str, examples: dict):
    """Add examples to endpoint file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return 0

    # This is a placeholder for future enhancement
    # For now, we'll focus on schemas
    return 0


def main():
    """Apply all enhancements."""
    print("🔧 Applying OpenAPI Enhancements")
    print("=" * 60)

    total_enhancements = 0

    # Enhance schema files
    print("\n📝 Enhancing Schema Files:")
    for schema_file, enhancements in SCHEMA_ENHANCEMENTS.items():
        total_enhancements += enhance_schema_file(schema_file, enhancements)

    print("\n" + "=" * 60)
    print(f"✅ Enhancement Complete!")
    print(f"   Total enhancements: {total_enhancements}")
    print("=" * 60)

    print("\n📋 Next Steps:")
    print("1. Review the enhanced schema files")
    print("2. Test the changes: python -m py_compile app/schemas/*.py")
    print("3. Regenerate OpenAPI spec")
    print("4. Run final verification")


if __name__ == "__main__":
    main()
