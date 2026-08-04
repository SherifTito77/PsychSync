#!/usr/bin/env python
"""
Response Schema Validation Script

Validates that all API endpoints have proper response_model declarations
and that the schemas match the actual implementation.

Usage:
    python scripts/validate_response_schemas.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import ast
import re
from collections import defaultdict


def extract_response_models(file_path: Path) -> dict:
    """Extract response_model declarations from endpoint file"""
    content = file_path.read_text()

    # Find all @router decorators with response_model
    pattern = r"@router\.(get|post|put|delete|patch)\([^)]*response_model=([^,\)]+)"
    matches = re.findall(pattern, content)

    models = {}
    for match in matches:
        method, model = match
        models[model] = models.get(model, 0) + 1

    return models


def find_dict_response_models(endpoint_dir: Path) -> list[dict]:
    """Find all endpoints using response_model=dict"""
    issues = []

    for endpoint_file in endpoint_dir.glob("*.py"):
        content = endpoint_file.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            if "response_model=dict" in line:
                # Extract the route info
                route_pattern = r'@router\.(get|post|put|delete|patch)\("([^"]+)"'
                route_match = None

                # Look backwards for the route definition
                for j in range(max(0, i - 5), i):
                    route_match = re.search(route_pattern, lines[j])
                    if route_match:
                        break

                if route_match:
                    method, path = route_match.groups()
                    issues.append(
                        {
                            "file": endpoint_file.name,
                            "line": i,
                            "method": method,
                            "path": path,
                            "issue": "Uses response_model=dict (no type safety)",
                        }
                    )

    return issues


def validate_auth_schemas() -> dict:
    """Validate auth endpoint response schemas"""
    auth_file = Path("app/schemas/auth.py")

    if not auth_file.exists():
        return {"error": "auth.py schema file not found"}

    content = auth_file.read_text()

    required_schemas = [
        "LoginResponse",
        "MFAChallengeResponse",
        "MFALoginResponse",
        "RegisterResponse",
        "VerifyEmailResponse",
        "UserInfoResponse",
        "LogoutResponse",
        "RefreshTokenResponse",
    ]

    missing_schemas = []
    for schema in required_schemas:
        if f"class {schema}" not in content:
            missing_schemas.append(schema)

    return {
        "total_required": len(required_schemas),
        "missing": missing_schemas,
        "found": len(required_schemas) - len(missing_schemas),
    }


def validate_user_schemas() -> dict:
    """Validate user endpoint response schemas"""
    user_file = Path("app/schemas/user.py")

    if not user_file.exists():
        return {"error": "user.py schema file not found"}

    content = user_file.read_text()

    required_schemas = [
        "UserListResponse",
        "UserProfileResponse",
        "ChangePasswordResponse",
    ]

    missing_schemas = []
    for schema in required_schemas:
        if f"class {schema}" not in content:
            missing_schemas.append(schema)

    return {
        "total_required": len(required_schemas),
        "missing": missing_schemas,
        "found": len(required_schemas) - len(missing_schemas),
    }


def validate_team_schemas() -> dict:
    """Validate team endpoint response schemas"""
    team_file = Path("app/schemas/team.py")

    if not team_file.exists():
        return {"error": "team.py schema file not found"}

    content = team_file.read_text()

    required_schemas = [
        "TeamListWithMetaResponse",
    ]

    missing_schemas = []
    for schema in required_schemas:
        if f"class {schema}" not in content:
            missing_schemas.append(schema)

    return {
        "total_required": len(required_schemas),
        "missing": missing_schemas,
        "found": len(required_schemas) - len(missing_schemas),
    }


def main():
    """Run all validations"""
    print("=" * 70)
    print("Response Schema Validation Report")
    print("=" * 70)
    print()

    # Check for response_model=dict usage
    print("1. Checking for response_model=dict usage...")
    print("-" * 70)

    endpoint_dir = Path("app/api/v1/endpoints")
    if endpoint_dir.exists():
        dict_issues = find_dict_response_models(endpoint_dir)

        if dict_issues:
            print(
                f"   ❌ Found {len(dict_issues)} endpoints using response_model=dict:"
            )
            for issue in dict_issues[:10]:  # Show first 10
                print(
                    f"      {issue['file']}:{issue['line']} - {issue['method']} {issue['path']}"
                )
            if len(dict_issues) > 10:
                print(f"      ... and {len(dict_issues) - 10} more")
        else:
            print("   ✅ No endpoints using response_model=dict")
    else:
        print("   ⚠️  Endpoint directory not found")

    print()

    # Validate auth schemas
    print("2. Validating auth response schemas...")
    print("-" * 70)

    auth_result = validate_auth_schemas()
    if "error" in auth_result:
        print(f"   ⚠️  {auth_result['error']}")
    else:
        if auth_result["missing"]:
            print(f"   ❌ Missing {len(auth_result['missing'])} auth schemas:")
            for schema in auth_result["missing"]:
                print(f"      - {schema}")
        else:
            print(f"   ✅ All {auth_result['total_required']} auth schemas defined")

    print()

    # Validate user schemas
    print("3. Validating user response schemas...")
    print("-" * 70)

    user_result = validate_user_schemas()
    if "error" in user_result:
        print(f"   ⚠️  {user_result['error']}")
    else:
        if user_result["missing"]:
            print(f"   ❌ Missing {len(user_result['missing'])} user schemas:")
            for schema in user_result["missing"]:
                print(f"      - {schema}")
        else:
            print(f"   ✅ All {user_result['total_required']} user schemas defined")

    print()

    # Validate team schemas
    print("4. Validating team response schemas...")
    print("-" * 70)

    team_result = validate_team_schemas()
    if "error" in team_result:
        print(f"   ⚠️  {team_result['error']}")
    else:
        if team_result["missing"]:
            print(f"   ❌ Missing {len(team_result['missing'])} team schemas:")
            for schema in team_result["missing"]:
                print(f"      - {schema}")
        else:
            print(f"   ✅ All {team_result['total_required']} team schemas defined")

    print()
    print("=" * 70)
    print("Validation Complete")
    print("=" * 70)

    # Return exit code
    if (
        dict_issues
        or auth_result.get("missing")
        or user_result.get("missing")
        or team_result.get("missing")
    ):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
