# GEMINI.md - Senior Peer Programmer Instructions

This file provides foundational mandates for Gemini CLI when working in the PsychSync repository. These instructions take absolute precedence over general defaults.

## 🧠 Engineering Philosophy
- **Security-First:** PsychSync handles sensitive clinical data. Security is not a feature; it is the foundation.
- **Service-Oriented Monolith:** Maintain clear boundaries between API endpoints, Services, and CRUD/Repository layers.
- **Reproduce then Fix:** Never fix a bug without first creating a reproduction script or test case that fails in the current state.
- **Surgical Changes:** Minimize diff size. Avoid unrelated refactoring or "cleanup" unless specifically requested.

## 🛠 Project Standards

### Backend (FastAPI + SQLAlchemy)
- **BaseService Pattern:** All new services MUST inherit from `app.services.base_service.BaseService`. Refer to `BASESERVICE_PATTERNS_CHEAT_SHEET.md` for implementation details.
- **Async Everywhere:** Use `async`/`await` for all I/O bound operations (database, cache, external APIs).
- **Type Safety:** Use Pydantic schemas for request/response validation. Every function must have type hints.
- **Exception Handling (B904):** Always raise exceptions using the `raise ... from err` pattern in `except` blocks.
- **Validation:** Business logic validation belongs in the service layer's `validate_create_data` and `validate_update_data` methods.

### Frontend (React + TypeScript)
- **Vite + Vitest:** Use the established build and test runner.
- **Context for State:** Use React Context for global state (Auth, Notification, Team).
- **Service Layer:** Abstract API calls into `frontend/src/services/`.
- **Styling:** Adhere to the existing design system and Tailwind/CSS variables.

## 🔒 Security Mandates
- **PII Protection:** Never log personally identifiable information. Use the established logging masking utilities.
- **SQL Injection:** Always use SQLAlchemy's expression language or ORM. Never use raw f-strings for queries.
- **Role-Based Access (RBAC):** Every endpoint must verify permissions via `Depends(check_permission(...))`.
- **Dependency Management:** Only use libraries from `requirements.txt` or `package.json`. Verify new dependencies with the security team first.

## 📂 Clutter Management
- **Script Location:** Do NOT create new scripts in the root directory. Place all utility, migration, and one-off scripts in `scripts/`.
- **Temp Files:** Always clean up temporary files and test artifacts.
- **Backups:** Use the `backups/` or `*_backups/` directories for file-system backups before major refactors.

## ✅ Quality & Validation
- **Testing:** New features require both unit and integration tests.
- **CI/CD:** Ensure all `ruff` and `npm run lint` checks pass before considering a task complete.
- **Documentation:** Update `CLAUDE.md` and relevant `.md` files in `docs/` if architectural changes are made.

## 🚀 Common Workflows

### Reproducing a Bug
```bash
# Create a reproduction script
touch scripts/repro_bug_XXX.py
# Run it to confirm failure
python scripts/repro_bug_XXX.py
# After fix, run again to confirm success
python scripts/repro_bug_XXX.py
```

### Adding a New Service
1. Define Pydantic schemas in `app/schemas/`.
2. Create service class in `app/services/` inheriting from `BaseService`.
3. Implement `model`, `cache_strategy`, and validation methods.
4. Add API routes in `app/api/v1/`.
5. Add unit tests in `tests/services/`.
