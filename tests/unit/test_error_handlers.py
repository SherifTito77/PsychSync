"""Tests for error handler stack trace sanitization.

Verifies that production mode strips internal error details from responses
while development mode preserves them for debugging.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.handlers import (
    _is_production,
    general_exception_handler,
    http_exception_handler,
)


# ── _is_production() ──────────────────────────────────────────

class TestIsProduction:
    def test_defaults_to_non_production(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ENVIRONMENT", None)
            assert _is_production() is False

    def test_development_is_not_production(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert _is_production() is False

    def test_production_detected(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert _is_production() is True

    def test_case_insensitive(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "Production"}):
            assert _is_production() is True


# ── http_exception_handler ─────────────────────────────────────

class TestHTTPExceptionHandler:
    @pytest.fixture
    def mock_request(self):
        req = MagicMock()
        req.url = MagicMock()
        req.url.__str__ = lambda self: "http://test/api/v1/test"
        req.method = "GET"
        return req

    @pytest.mark.asyncio
    async def test_4xx_detail_preserved_in_production(self, mock_request):
        """Client errors should show the actual detail even in production."""
        from fastapi import HTTPException

        exc = HTTPException(status_code=404, detail="User not found")

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 404
        import json
        body = json.loads(response.body)
        assert "User not found" in body["message"]

    @pytest.mark.asyncio
    async def test_5xx_detail_sanitized_in_production(self, mock_request):
        """Server errors must NOT leak internal details in production."""
        from fastapi import HTTPException

        exc = HTTPException(
            status_code=500,
            detail="sqlalchemy.exc.OperationalError: connection refused to db:5432",
        )

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert "sqlalchemy" not in body["message"]
        assert "connection refused" not in body["message"]
        assert "internal server error" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_5xx_detail_visible_in_development(self, mock_request):
        """In development, the full error detail should be visible."""
        from fastapi import HTTPException

        exc = HTTPException(status_code=500, detail="KeyError: 'missing_field'")

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            response = await http_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body)
        assert "KeyError" in body["message"]


# ── general_exception_handler ──────────────────────────────────

class TestGeneralExceptionHandler:
    @pytest.fixture
    def mock_request(self):
        req = MagicMock()
        req.url = MagicMock()
        req.url.__str__ = lambda self: "http://test/api/v1/test"
        req.method = "POST"
        return req

    @pytest.mark.asyncio
    async def test_returns_500(self, mock_request):
        exc = RuntimeError("unexpected failure")
        response = await general_exception_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_never_leaks_exception_message(self, mock_request):
        """The actual exception message must never reach the client."""
        exc = ValueError("secret DB password: hunter2")
        response = await general_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body)
        assert "hunter2" not in json.dumps(body)
        assert "An unexpected error occurred" in body["message"]

    @pytest.mark.asyncio
    async def test_error_type_stripped_in_production(self, mock_request):
        exc = ConnectionRefusedError("db:5432")

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = await general_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body)
        details = body.get("details", {})
        assert "error_type" not in details
        assert "ConnectionRefusedError" not in json.dumps(body)

    @pytest.mark.asyncio
    async def test_error_type_visible_in_development(self, mock_request):
        exc = ZeroDivisionError("division by zero")

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            response = await general_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body)
        assert body["details"]["error_type"] == "ZeroDivisionError"


# ── create_error_response sanitization ─────────────────────────

class TestCreateErrorResponse:
    def test_strips_original_error_in_production(self):
        from app.core.exceptions import ErrorCode, PsychSyncException, create_error_response

        exc = PsychSyncException(
            message="Database error",
            error_code=ErrorCode.DATABASE_ERROR,
            details={"original_error": "psycopg2.OperationalError: FATAL: password authentication failed"},
        )

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            resp = create_error_response(exc)

        assert "original_error" not in resp.get("details", {})
        assert "psycopg2" not in str(resp)

    def test_preserves_original_error_in_development(self):
        from app.core.exceptions import ErrorCode, PsychSyncException, create_error_response

        exc = PsychSyncException(
            message="Database error",
            error_code=ErrorCode.DATABASE_ERROR,
            details={"original_error": "some SQL error", "operation": "GET /api"},
        )

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            resp = create_error_response(exc)

        assert resp["details"]["original_error"] == "some SQL error"
