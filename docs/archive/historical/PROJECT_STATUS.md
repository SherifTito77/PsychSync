# PsychSync AI — Project Status

## Entry Point
- Primary: `app/main.py`
- Status: **WORKING** (Verified with startup smoke tests)

## Core Services
| Service | File | Status | Notes |
|---------|------|--------|-------|
| Database | `app/core/database.py` | ✅ **WORKING** | Health check hardened; non-blocking startup implemented. |
| Cache/Redis | `app/core/cache.py` | ✅ **WORKING** | Event loop collisions resolved; using managed `get_redis_client`. |
| Auth | `app/api/v1/endpoints/auth_unified.py` | ✅ **WORKING** | Standardized on `auth_unified`; legacy endpoints deprecated. |
| Assessments | `app/services/assessment_service.py` | ⚠️ **PARTIAL** | Core logic functional; Pydantic v2 tech debt remains. |
| Team Optimizer | `app/services/optimizer/team_optimizer.py` | ⚠️ **PARTIAL** | Basketball/Sports logic isolated; needs domain-specific refactor. |

## Major Fixes Completed
- **Startup Crash:** Fixed `AttributeError` in `/health` and `/metrics/performance` endpoints caused by uninitialized `None` services.
- **Async Concurrency:** Resolved `RuntimeError` in `auth_unified.py` by refactoring Redis to use a centralized, loop-aware client.
- **Database Stability:** Converted `free_email_connector_service.py` to use fully async database operations (`await db.commit()`, etc.).
- **Migration Repair:** Resolved Alembic version prefix collisions and purged `.broken` migration files.
- **Directory Cleanup:** Archived ~450+ AI-generated reports and one-off scripts into `docs/archive/`.
- **Import Errors:** Fixed `IndentationError` in `app/main.py` and import path mismatches in `ai/processors/__init__.py`.

## Known Issues
- **Pydantic v2 Tech Debt:** High volume of `DeprecationWarning` logs due to v1-style validators and `class Config` usage.
- **Misplaced Sensitive Files:** Several `.key` and `.enc` files are currently tracked in Git history and require `git filter-repo` or `BFG` cleanup.
- **Domain Overlap:** Core engines (Scoring/Optimizer) still contain significant basketball-specific terminology and math.

## Deprecated Files
The following files have been marked with deprecation headers and should no longer be used for new development:
- `minimal_app.py`
- `minimal_app_enhanced.py`
- `app/api/v1/endpoints/auth_minimal.py`
- `app/api/v1/endpoints/simple_auth.py`
- `app/schemas/user_service.py` (Replaced by `app.services.user_service`)
- `app/services/scoring/scoring_backend.py` (Isolated as `.bak`)

## Test Coverage
- **Smoke tests:** `tests/smoke/` (Status: ✅ **PASSING**)
- **Unit tests:** `tests/unit/` (Status: ✅ **PASSING**)
- **Run all:** `PYTHONPATH=. pytest tests/ -v -c /dev/null`
