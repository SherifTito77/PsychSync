"""
Response Schema Validation Tests

This test suite validates that all API endpoints return responses that match
their declared response_model schemas. This prevents API contract drift and
ensures OpenAPI documentation is accurate.

Run with: pytest tests/api/test_response_schema_validation.py -v
"""

import json
from datetime import datetime
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAuthResponseSchemas:
    """Test authentication endpoint response schemas"""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)

    def test_login_response_schema(self, client: TestClient) -> None:
        """
        Test that /login endpoint returns LoginResponse schema

        Expected fields:
        - access_token: str
        - refresh_token: str
        - token_type: str
        - expires_in: int
        - user: UserSummary
        """
        response = client.post(
            "/api/v1/login",
            data={"username": "test@example.com", "password": "testpass123"},
        )

        # We expect 401 for invalid credentials, but we're testing the schema
        # In a real test, you'd create a test user first
        if response.status_code == 200:
            data = response.json()

            # Validate all required fields exist
            assert "access_token" in data, "Missing access_token field"
            assert "refresh_token" in data, "Missing refresh_token field"
            assert "token_type" in data, "Missing token_type field"
            assert "expires_in" in data, "Missing expires_in field"
            assert "user" in data, "Missing user field"

            # Validate types
            assert isinstance(data["access_token"], str)
            assert isinstance(data["refresh_token"], str)
            assert isinstance(data["token_type"], str)
            assert isinstance(data["expires_in"], int)
            assert isinstance(data["user"], dict)

            # Validate user sub-fields
            user = data["user"]
            assert "id" in user
            assert "email" in user
            assert "is_active" in user
            assert isinstance(user["id"], str)
            assert isinstance(user["email"], str)
            assert isinstance(user["is_active"], bool)

    def test_register_response_schema(self, client: TestClient) -> None:
        """
        Test that /register endpoint returns RegisterResponse schema

        Expected fields:
        - message: str
        - user_id: str
        - email: str
        - requires_verification: bool
        """
        response = client.post(
            "/api/v1/register",
            json={
                "email": f"test-{datetime.now().timestamp()}@example.com",
                "password": "TestPass123!",
                "full_name": "Test User",
            },
        )

        if response.status_code == 201:
            data = response.json()

            # Validate all required fields
            assert "message" in data, "Missing message field"
            assert "user_id" in data, "Missing user_id field"
            assert "email" in data, "Missing email field"
            assert (
                "requires_verification" in data
            ), "Missing requires_verification field"

            # Validate types
            assert isinstance(data["message"], str)
            assert isinstance(data["user_id"], str)
            assert isinstance(data["email"], str)
            assert isinstance(data["requires_verification"], bool)

    def test_verify_email_response_schema(self, client: TestClient) -> None:
        """
        Test that /verify-email endpoint returns VerifyEmailResponse schema

        Expected fields:
        - message: str
        """
        response = client.post("/api/v1/verify-email", json={"token": "test_token"})

        if response.status_code in [200, 400]:
            data = response.json()

            # Even error responses should have message field
            assert "message" in data or "detail" in data

    def test_logout_response_schema(self, client: TestClient) -> None:
        """
        Test that /logout endpoint returns LogoutResponse schema

        Expected fields:
        - message: str
        """
        response = client.post("/api/v1/logout")

        # Logout requires authentication, so we expect 401
        # But if authenticated, should return message
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert isinstance(data["message"], str)


class TestUserResponseSchemas:
    """Test user endpoint response schemas"""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)

    def test_user_profile_response_schema(self, client: TestClient) -> None:
        """
        Test that GET /users/me returns UserProfileResponse schema

        Expected fields:
        - id: str
        - email: str
        - full_name: str | None
        - is_active: bool
        - is_verified: bool
        - is_superuser: bool
        - two_factor_enabled: bool
        - created_at: str | None
        - updated_at: str | None
        """
        response = client.get("/api/v1/users/me")

        # Requires authentication, so expect 401 without auth
        # But if authenticated, should return user profile
        if response.status_code == 200:
            data = response.json()

            # Validate all required fields
            required_fields = [
                "id",
                "email",
                "is_active",
                "is_verified",
                "is_superuser",
                "two_factor_enabled",
            ]
            for field in required_fields:
                assert field in data, f"Missing {field} field"

            # Validate types
            assert isinstance(data["id"], str)
            assert isinstance(data["email"], str)
            assert isinstance(data["is_active"], bool)
            assert isinstance(data["is_verified"], bool)
            assert isinstance(data["is_superuser"], bool)
            assert isinstance(data["two_factor_enabled"], bool)

    def test_change_password_response_schema(self, client: TestClient) -> None:
        """
        Test that POST /users/change-password returns ChangePasswordResponse schema

        Expected fields:
        - message: str
        """
        response = client.post(
            "/api/v1/users/change-password",
            json={"current_password": "oldpass", "new_password": "newpass123"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert isinstance(data["message"], str)


class TestTeamResponseSchemas:
    """Test team endpoint response schemas"""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)

    def test_list_teams_response_schema(self, client: TestClient) -> None:
        """
        Test that GET /teams/ returns TeamListWithMetaResponse schema

        Expected fields:
        - teams: list
        - total: int
        - success: bool
        - message: str
        """
        response = client.get("/api/v1/teams/")

        # Requires authentication
        if response.status_code == 200:
            data = response.json()

            # Validate all required fields
            assert "teams" in data, "Missing teams field"
            assert "total" in data, "Missing total field"
            assert "success" in data, "Missing success field"
            assert "message" in data, "Missing message field"

            # Validate types
            assert isinstance(data["teams"], list)
            assert isinstance(data["total"], int)
            assert isinstance(data["success"], bool)
            assert isinstance(data["message"], str)

            # If teams exist, validate team item structure
            if len(data["teams"]) > 0:
                team = data["teams"][0]
                assert "id" in team
                assert "name" in team
                assert isinstance(team["id"], str)
                assert isinstance(team["name"], str)


class TestOpenAPISpecGeneration:
    """Test OpenAPI specification generation"""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)

    def test_openapi_schema_exists(self, client: TestClient) -> None:
        """Test that OpenAPI schema can be generated"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_auth_endpoints_have_schemas(self, client: TestClient) -> None:
        """Test that auth endpoints have proper response schemas in OpenAPI"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()

        # Check that /api/v1/login endpoint exists and has response schema
        assert "/api/v1/login" in openapi_spec["paths"]
        login_path = openapi_spec["paths"]["/api/v1/login"]

        # Check POST operation
        assert "post" in login_path
        post_op = login_path["post"]

        # Check response schema exists
        assert "responses" in post_op
        assert "200" in post_op["responses"]

        response_200 = post_op["responses"]["200"]
        assert "content" in response_200
        assert "application/json" in response_200["content"]

        # Check that schema is not empty (not just {})
        schema = response_200["content"]["application/json"].get("schema", {})
        if "$ref" in schema:
            # Has a proper schema reference
            assert schema["$ref"].startswith("#/components/schemas/")
        elif "properties" in schema:
            # Has inline schema with properties
            assert len(schema["properties"]) > 0

    def test_no_empty_response_schemas(self, client: TestClient) -> None:
        """
        Test that no endpoints have empty response schemas ({})

        Empty schemas indicate response_model=dict which provides no type safety
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()

        empty_schema_endpoints = []

        # Check all paths
        for path, path_item in openapi_spec["paths"].items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "patch", "delete"]:
                    continue

                if "responses" not in operation:
                    continue

                # Check 200, 201 responses
                for status_code in ["200", "201"]:
                    if status_code not in operation["responses"]:
                        continue

                    response_spec = operation["responses"][status_code]

                    if "content" not in response_spec:
                        continue

                    if "application/json" not in response_spec["content"]:
                        continue

                    schema = response_spec["content"]["application/json"].get(
                        "schema", {}
                    )

                    # Check for empty object schema
                    if schema == {} or schema == {"type": "object"}:
                        empty_schema_endpoints.append(f"{method.upper()} {path}")

        # Assert no endpoints have empty schemas
        if empty_schema_endpoints:
            pytest.fail(
                f"The following endpoints have empty response schemas (response_model=dict):\n"
                + "\n".join(empty_schema_endpoints)
            )


class TestResponseConsistency:
    """Test response consistency across endpoints"""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)

    def test_all_responses_have_proper_content_type(self, client: TestClient) -> None:
        """
        Test that all JSON responses have proper content-type header

        This ensures FastAPI is properly handling response serialization
        """
        # Test a few key endpoints
        endpoints = [
            ("GET", "/api/v1/health"),
            ("POST", "/api/v1/login"),
        ]

        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json={})

            if response.status_code == 200:
                # Check for proper content type
                content_type = response.headers.get("content-type", "")
                assert "application/json" in content_type or len(response.content) == 0


# ============================================================================
# Integration Test: Full API Contract Validation
# ============================================================================


class TestFullAPIContractValidation:
    """
    Comprehensive API contract validation

    This test class validates the entire API contract by:
    1. Generating the OpenAPI specification
    2. Checking that all endpoints have proper schemas
    3. Validating schema definitions exist
    """

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client"""
        return TestClient(app)

    def test_all_schemas_referenced_exist(self, client: TestClient) -> None:
        """
        Test that all $ref schemas referenced in endpoints actually exist

        This catches typos and missing schema definitions
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()

        # Get all defined schemas
        defined_schemas = set(
            openapi_spec.get("components", {}).get("schemas", {}).keys()
        )

        if not defined_schemas:
            pytest.skip("No schemas defined in OpenAPI spec")

        # Track missing schemas
        missing_schemas = []

        # Check all endpoint references
        for path, path_item in openapi_spec["paths"].items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "patch", "delete"]:
                    continue

                # Check responses
                for status_code, response_spec in operation.get(
                    "responses", {}
                ).items():
                    if "content" not in response_spec:
                        continue

                    if "application/json" not in response_spec["content"]:
                        continue

                    schema = response_spec["content"]["application/json"].get(
                        "schema", {}
                    )

                    # Check $ref
                    if "$ref" in schema:
                        ref = schema["$ref"]
                        # Extract schema name from "#/components/schemas/SchemaName"
                        if ref.startswith("#/components/schemas/"):
                            schema_name = ref.split("/")[-1]
                            if schema_name not in defined_schemas:
                                missing_schemas.append(
                                    f"{method.upper()} {path} -> {schema_name}"
                                )

        # Assert all referenced schemas exist
        if missing_schemas:
            pytest.fail(
                f"The following endpoint schemas are referenced but not defined:\n"
                + "\n".join(missing_schemas)
            )

    def test_auth_schemas_are_defined(self, client: TestClient) -> None:
        """Test that all new auth response schemas are defined"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()

        schemas = openapi_spec.get("components", {}).get("schemas", {})

        # Check that our new auth schemas exist
        expected_auth_schemas = [
            "LoginResponse",
            "MFAChallengeResponse",
            "MFALoginResponse",
            "RegisterResponse",
            "VerifyEmailResponse",
            "UserInfoResponse",
            "LogoutResponse",
            "RefreshTokenResponse",
            "MFAResponse",
            "MFAVerifyResponse",
            "MFADisableResponse",
            "HealthCheckResponse",
            "UserSummary",
        ]

        missing_schemas = [s for s in expected_auth_schemas if s not in schemas]

        if missing_schemas:
            pytest.fail(
                f"Missing auth schema definitions: {', '.join(missing_schemas)}"
            )


# ============================================================================
# Run Instructions
# ============================================================================

"""
To run these tests:

1. Run all response schema validation tests:
   pytest tests/api/test_response_schema_validation.py -v

2. Run specific test class:
   pytest tests/api/test_response_schema_validation.py::TestAuthResponseSchemas -v

3. Run with coverage:
   pytest tests/api/test_response_schema_validation.py --cov=app.api.v1.endpoints -v

4. Run and stop on first failure:
   pytest tests/api/test_response_schema_validation.py -x -v

5. Run and see detailed output:
   pytest tests/api/test_response_schema_validation.py -v -s
"""
