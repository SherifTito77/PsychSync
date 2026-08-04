#!/usr/bin/env python3
"""
Add Config classes with schema_extra examples to Pydantic schemas
This adds examples that appear in OpenAPI documentation
"""

import re
from pathlib import Path

# Schema examples to add
SCHEMA_CONFIGS = {
    "UserCreate": {
        "example": {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe",
        }
    },
    "UserUpdate": {
        "example": {
            "full_name": "John Smith",
            "phone": "+1234567890",
            "bio": "Software engineer passionate about psychology",
        }
    },
    "TeamCreate": {
        "example": {
            "name": "Engineering Team",
            "description": "Software development team focused on AI",
        }
    },
    "AssessmentCreate": {
        "example": {
            "title": "Big Five Personality Test",
            "description": "Measure personality traits across OCEAN dimensions",
            "framework": "big_five",
            "status": "active",
        }
    },
    "ResponseSubmit": {
        "example": {
            "answers": [
                {"question_id": 1, "value": 4},
                {"question_id": 2, "value": 5},
                {"question_id": 3, "value": 3},
            ]
        }
    },
}


def add_config_to_schema(file_path: str, schema_configs: dict):
    """Add Config class with schema_extra to schema classes."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return 0

    modifications = 0

    for class_name, config_data in schema_configs.items():
        # Check if class already has Config
        config_pattern = rf"(class {class_name}\(BaseModel\):.*?)(\n    class Config:)"
        if re.search(config_pattern, content, re.DOTALL):
            continue

        # Find the class and add Config at the end
        # Pattern to match class definition until next class or end of file
        pattern = rf"(class {class_name}\(BaseModel\):.*?)(?=\nclass |\Z)"

        def add_config(match):
            nonlocal modifications
            class_content = match.group(1)

            # Check if already has Config
            if "class Config:" in class_content:
                return match.group(0)

            modifications += 1
            example_json = (
                str(config_data)
                .replace("'", '"')
                .replace("True", "true")
                .replace("False", "false")
            )

            config = f"""{class_content}

    class Config:
        schema_extra = {{
            "example": {config_data}
        }}
"""
            return config

        content = re.sub(pattern, add_config, content, flags=re.DOTALL)

    if modifications > 0:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Enhanced {file_path}: +{modifications} Config classes")
    else:
        print(f"⏭️  {file_path}: Already has Config classes")

    return modifications


def main():
    """Add Config examples to all schema files."""
    print("📝 Adding Config Examples to Schemas")
    print("=" * 60)

    schema_files = {
        "app/schemas/user.py": {
            "UserCreate": SCHEMA_CONFIGS["UserCreate"],
            "UserUpdate": SCHEMA_CONFIGS["UserUpdate"],
        },
        "app/schemas/team.py": {"TeamCreate": SCHEMA_CONFIGS["TeamCreate"]},
        "app/schemas/assessment.py": {
            "AssessmentCreate": SCHEMA_CONFIGS["AssessmentCreate"]
        },
        "app/schemas/response.py": {"ResponseSubmit": SCHEMA_CONFIGS["ResponseSubmit"]},
    }

    total = 0
    for schema_file, configs in schema_files.items():
        total += add_config_to_schema(schema_file, configs)

    print("\n" + "=" * 60)
    print(f"✅ Complete! Added {total} Config classes")
    print("=" * 60)


if __name__ == "__main__":
    main()
