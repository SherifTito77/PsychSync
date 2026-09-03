# GEMINI.md - Testing Standards & Protocols

This directory contains the comprehensive test suite for PsychSync. Adhering to these standards is MANDATORY to maintain platform stability and clinical safety.

## 🧪 Core Testing Principles
- **Reproduction First:** All bug fixes MUST have a corresponding reproduction script in `scripts/` or a new test case in `tests/` that confirms the failure BEFORE the fix is applied.
- **Idempotency:** Tests must be repeatable and leave the database/environment in the same state they found it.
- **Isolation:** Tests should be as isolated as possible. Use mock objects for external services (e.g., email, payment, external AI APIs).
- **Fast Feedback:** Prioritize fast-running unit tests. Heavy integration and load tests should be run in CI or on-demand.

## 🛠 Frameworks
- **Backend:** Use `pytest` with `pytest-asyncio` for all Python tests.
- **Frontend:** Use `vitest` for React component and service tests.
- **E2E:** Use `Cypress` or `Playwright` (verify current usage in `package.json`).

## 📁 Structure & Organization
- `tests/unit/`: Logic-only tests (no database/network).
- `tests/integration/`: Service and API layer tests with a test database.
- `tests/security/`: Security-specific scans and attack vector tests.
- `tests/ai/`: AI Agent and AI Engine validation.
- `tests/fixtures/`: Shared pytest fixtures. Use `tests/conftest.py` for global fixtures.

## ✅ Quality Standards
- **Transactions:** Use the `@transaction_manager.transaction` decorator or a database rollback fixture for all database tests.
- **Mocks:** Use `unittest.mock` or `pytest-mock`. NEVER use real production credentials or data.
- **Cleanup:** Always delete test users, organizations, and assessments created during a test run.
- **Coverage:** Aim for 80%+ coverage on all new features. Check existing coverage with `pytest --cov=app`.

## 🚀 Common Commands
```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests (requires test database)
pytest tests/integration/ -v

# Run specific test file
pytest tests/api/test_auth.py -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

## 🔒 Security Testing Mandates
- **RBAC:** Every new API endpoint MUST have a test case for:
  1. Success (user with correct permissions).
  2. Failure (unauthenticated user).
  3. Failure (user with incorrect permissions/role).
- **PII:** Verify that test logs do not contain sensitive patient data or passwords.
- **Injection:** Include basic SQLi and XSS payloads in input validation tests.
