# Phase 2 Implementation Plan: Service Layer Refactoring

## 📋 Executive Summary

**Status:** Ready to Begin
**Priority:** HIGH
**Estimated Effort:** 120 hours (3-4 weeks)
**Dependencies:** Phase 1 ✅ Complete

**Goal:** Migrate the codebase from direct `app.core.security` imports to the new SOLID-compliant service architecture, and implement proper dependency injection.

---

## 🎯 Phase 2 Objectives

1. **Migrate all imports** from `app.core.security` to `app.services.security`
2. **Implement Dependency Injection container** for proper service lifecycle management
3. **Refactor API endpoints** to use injected services instead of direct imports
4. **Update all tests** to work with new service architecture
5. **Remove deprecated code** from `app.core.security` after migration is complete

---

## 📊 Migration Analysis

### Current State

- **Files to migrate:** 169 files
- **Import patterns identified:**
  - `get_password_hash` - Used in 45+ files
  - `verify_password` - Used in 60+ files
  - `get_current_user` - Used in 80+ files
  - `create_access_token` - Used in 35+ files
  - `validate_password` - Used in 25+ files
  - Other security functions - Used in 50+ files

### File Categories

| Category | Count | Priority | Migration Complexity |
|----------|-------|----------|---------------------|
| API Endpoints | 35 | CRITICAL | Medium |
| Services | 8 | HIGH | Low |
| CRUD Classes | 5 | HIGH | Low |
| Schemas | 3 | MEDIUM | Low |
| Tests | 110 | MEDIUM | Low-Medium |
| Scripts | 8 | LOW | Low |

---

## 🚀 Implementation Strategy

### Step 1: Dependency Injection Setup (Days 1-3)

**Objective:** Implement DI container to manage service lifecycles

**Tasks:**

1.1. Choose DI Framework
- **Option A:** FastAPI's built-in `Depends()` (Recommended - simplest)
- **Option B:** `dependency-injector` library (More features, steeper learning curve)
- **Option C:** Custom DI container (Maximum control, more maintenance)

**Recommendation:** Start with FastAPI `Depends()` for simplicity, can upgrade later.

1.2. Create Service Provider Module
```python
# app/core/service_provider.py
from fastapi import Depends
from app.services.security import (
    PasswordService,
    TokenService,
    AuthorizationService,
    InputSanitizerService,
)

# Singleton instances
_password_service: PasswordService | None = None
_token_service: TokenService | None = None
_authorization_service: AuthorizationService | None = None
_input_sanitizer_service: InputSanitizerService | None = None

def get_password_service() -> PasswordService:
    """Get password service instance (singleton)"""
    global _password_service
    if _password_service is None:
        _password_service = PasswordService()
    return _password_service

def get_token_service() -> TokenService:
    """Get token service instance (singleton)"""
    global _token_service
    if _token_service is None:
        _token_service = TokenService()
    return _token_service

def get_authorization_service() -> AuthorizationService:
    """Get authorization service instance (singleton)"""
    global _authorization_service
    if _authorization_service is None:
        _authorization_service = AuthorizationService()
    return _authorization_service

def get_input_sanitizer_service() -> InputSanitizerService:
    """Get input sanitizer service instance (singleton)"""
    global _input_sanitizer_service
    if _input_sanitizer_service is None:
        _input_sanitizer_service = InputSanitizerService()
    return _input_sanitizer_service
```

1.3. Update FastAPI Dependencies
```python
# app/api/deps.py (modify existing)
from fastapi import Depends, HTTPException, status
from app.core.service_provider import get_password_service, get_token_service
from app.services.security import PasswordService, TokenService

async def get_password_service_dep(
    service: PasswordService = Depends(get_password_service),
) -> PasswordService:
    """FastAPI dependency for password service"""
    return service

async def get_token_service_dep(
    service: TokenService = Depends(get_token_service),
) -> TokenService:
    """FastAPI dependency for token service"""
    return service
```

**Deliverables:**
- ✅ `app/core/service_provider.py` created
- ✅ `app/api/deps.py` updated with new dependencies
- ✅ Service lifecycle managed properly

**Success Criteria:**
- All services are singleton instances
- FastAPI can inject services via `Depends()`
- No circular dependencies

---

### Step 2: Automated Migration Script (Days 4-5)

**Objective:** Create automated script to update imports across codebase

**Tasks:**

2.1. Create Migration Script
```python
# scripts/migrate_security_imports.py
"""Automated import migration script from app.core.security to app.services.security"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Import mapping: old_import -> new_import
IMPORT_MIGRATIONS: Dict[str, str] = {
    # Password functions
    "from app.core.security import get_password_hash":
        "from app.services.security import get_password_hash",
    "from app.core.security import verify_password":
        "from app.services.security import verify_password",
    "from app.core.security import validate_password":
        "from app.services.security import validate_password",

    # Token functions
    "from app.core.security import create_access_token":
        "from app.services.security import create_access_token",
    "from app.core.security import create_refresh_token":
        "from app.services.security import create_refresh_token",
    "from app.core.security import create_token_pair":
        "from app.services.security import create_token_pair",
    "from app.core.security import verify_token":
        "from app.services.security import verify_token",

    # Auth functions
    "from app.core.security import get_current_user":
        "from app.services.security import get_current_user",
    "from app.core.security import get_current_active_user":
        "from app.services.security import get_current_active_user",

    # Authorization functions
    "from app.core.security import has_role":
        "from app.services.security import has_role",
    "from app.core.security import is_owner":
        "from app.services.security import is_owner",
    "from app.core.security import require_permissions":
        "from app.services.security import require_permissions",

    # Input sanitization
    "from app.core.security import sanitize_input":
        "from app.services.security import sanitize_input",
    "from app.core.security import escape_html":
        "from app.services.security import escape_html",
    "from app.core.security import validate_email":
        "from app.services.security import validate_email",

    # Other common imports
    "from app.core.security import generate_csrf_token":
        "from app.services.security import generate_csrf_token",
    "from app.core.security import constant_time_compare":
        "from app.services.security import constant_time_compare",
}

# Files to exclude from migration
EXCLUDE_PATTERNS = [
    "*.backup*",
    "*.pyc",
    "__pycache__",
    "venv/",
    ".venv/",
    "node_modules/",
    "migrations/",
]

def should_migrate_file(file_path: Path) -> bool:
    """Check if file should be migrated"""
    # Exclude backup files
    if any(pattern in str(file_path) for pattern in EXCLUDE_PATTERNS):
        return False

    # Only process Python files
    if file_path.suffix != ".py":
        return False

    return True

def migrate_file(file_path: Path) -> Tuple[bool, int]:
    """
    Migrate imports in a single file.

    Returns:
        (was_modified, changes_count)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        changes_count = 0

        # Apply migrations
        for old_import, new_import in IMPORT_MIGRATIONS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_count += 1

        # Handle multi-line imports
        # Match: from app.core.security import ( ... )
        multiline_pattern = r"from app\.core\.security import \((.*?)\)"
        multiline_match = re.search(multiline_pattern, content, re.DOTALL)

        if multiline_match:
            imported_items = multiline_match.group(1)
            # Update the import
            new_import = f"from app.services.security import ({imported_items})"
            content = content[:multiline_match.start()] + new_import + content[multiline_match.end():]
            changes_count += 1

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, changes_count

        return False, 0

    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return False, 0

def main():
    """Main migration function"""
    project_root = Path.cwd()
    python_files = list(project_root.rglob("*.py"))

    # Filter files
    files_to_migrate = [f for f in python_files if should_migrate_file(f)]

    print(f"🔍 Found {len(files_to_migrate)} Python files to check")
    print(f"📝 Migrating imports from app.core.security to app.services.security\n")

    migrated_count = 0
    total_changes = 0

    for file_path in files_to_migrate:
        was_modified, changes = migrate_file(file_path)
        if was_modified:
            migrated_count += 1
            total_changes += changes
            relative_path = file_path.relative_to(project_root)
            print(f"✅ Migrated {relative_path} ({changes} changes)")

    print(f"\n🎉 Migration complete!")
    print(f"   Files migrated: {migrated_count}")
    print(f"   Total changes: {total_changes}")

if __name__ == "__main__":
    main()
```

2.2. Create Verification Script
```python
# scripts/verify_migration.py
"""Verify that migration was successful"""

import subprocess
import sys
from pathlib import Path

def check_imports():
    """Check for remaining old imports"""
    result = subprocess.run(
        ["grep", "-r", "from app.core.security import", "--include=*.py", "."],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("⚠️  Found remaining old imports:")
        print(result.stdout)
        return False
    else:
        print("✅ No old imports found!")
        return True

def check_syntax():
    """Check Python syntax of all files"""
    result = subprocess.run(
        ["python", "-m", "compileall", "."],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("⚠️  Syntax errors found:")
        print(result.stderr)
        return False
    else:
        print("✅ All files compile successfully!")
        return True

def main():
    """Main verification function"""
    print("🔍 Verifying migration...\n")

    imports_ok = check_imports()
    syntax_ok = check_syntax()

    if imports_ok and syntax_ok:
        print("\n✅ Migration verification PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Migration verification FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Deliverables:**
- ✅ `scripts/migrate_security_imports.py` created
- ✅ `scripts/verify_migration.py` created
- ✅ Automated migration capability

**Success Criteria:**
- Script can migrate all 169 files automatically
- No manual intervention required for 95%+ of files
- Verification script confirms successful migration

---

### Step 3: Execute Migration (Days 6-8)

**Objective:** Migrate all files to use new service imports

**Tasks:**

3.1. Create Git Branch
```bash
git checkout -b feature/security-service-migration
```

3.2. Run Migration Script
```bash
python scripts/migrate_security_imports.py
```

3.3. Verify Migration
```bash
python scripts/verify_migration.py
```

3.4. Fix Any Manual Issues
- Review files with complex multi-line imports
- Handle edge cases (e.g., dynamic imports)
- Update test fixtures if needed

3.5. Run Test Suite
```bash
pytest tests/ -v --tb=short
```

3.6. Fix Test Failures
- Update test imports
- Mock new services if needed
- Verify all tests pass

**Deliverables:**
- ✅ All 169 files migrated
- ✅ All tests passing
- ✅ No remaining old imports

**Success Criteria:**
- 0 files with old imports
- 95%+ tests passing (allowing for some pre-existing failures)
- No syntax errors

---

### Step 4: Update API Endpoints with DI (Days 9-12)

**Objective:** Refactor API endpoints to use dependency injection

**Priority Order:**

1. **Critical Path (Days 9-10):**
   - `app/api/v1/endpoints/auth_unified.py`
   - `app/api/v1/endpoints/users.py`
   - `app/api/v1/endpoints/users_secure.py`
   - `app/api/deps.py`

2. **High Priority (Days 11-12):**
   - All other API endpoints (35 files total)

**Example Migration:**

**Before:**
```python
# app/api/v1/endpoints/users.py
from app.core.security import verify_password, get_password_hash
from app.api import deps

@router.post("/users/{user_id}/change-password")
async def change_password(
    user_id: str,
    new_password: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # Direct function call
    hashed = get_password_hash(new_password)
    is_valid = verify_password(new_password, current_user.hashed_password)
    # ...
```

**After:**
```python
# app/api/v1/endpoints/users.py
from app.api import deps
from app.services.security import PasswordService

@router.post("/users/{user_id}/change-password")
async def change_password(
    user_id: str,
    new_password: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    password_service: PasswordService = Depends(deps.get_password_service_dep),
):
    # Injected service
    hashed = password_service.hash_password(new_password)
    verification_result = await password_service.verify_password(
        new_password,
        current_user.hashed_password,
    )
    is_valid = verification_result.is_valid
    # ...
```

**Deliverables:**
- ✅ All 35 API endpoints using DI
- ✅ No direct security imports in endpoints
- ✅ Testable architecture (services can be mocked)

**Success Criteria:**
- All API endpoints use `Depends()` for services
- Endpoints are thin HTTP wrappers
- Business logic in services, not endpoints

---

### Step 5: Update Services and CRUD Classes (Days 13-14)

**Objective:** Migrate service layer to use new architecture

**Files to Update:**
- `app/services/user_service.py`
- `app/services/secure_password_reset_service.py`
- `app/crud/user.py`
- Other service classes (5-8 files)

**Example Migration:**

**Before:**
```python
# app/services/user_service.py
from app.core.security import get_password_hash, verify_password

class UserService:
    async def create_user(self, db: AsyncSession, user_create: UserCreate):
        hashed_password = get_password_hash(user_create.password)
        # ...
```

**After:**
```python
# app/services/user_service.py
from app.services.security import PasswordService

class UserService:
    def __init__(self, password_service: PasswordService):
        self.password_service = password_service

    async def create_user(self, db: AsyncSession, user_create: UserCreate):
        hashed_password = self.password_service.hash_password(user_create.password)
        # ...
```

**Deliverables:**
- ✅ All services using injected dependencies
- ✅ No direct security imports in services
- ✅ Constructor-based DI for services

**Success Criteria:**
- All services declare dependencies in `__init__`
- Services are testable (mock dependencies)
- No circular dependencies

---

### Step 6: Update Schemas (Days 15)

**Objective:** Migrate Pydantic schemas that import security functions

**Files to Update:**
- `app/schemas/user_secure.py`
- `app/schemas/user_service.py`
- `app/schemas/auth.py`

**Example Migration:**

**Before:**
```python
# app/schemas/user_secure.py
from app.core.security import validate_password

class UserCreate(BaseModel):
    password: str

    def validate_password_complexity(self):
        result = validate_password(self.password)
        if not result.is_valid:
            raise ValueError(", ".join(result.errors))
```

**After:**
```python
# app/schemas/user_secure.py
from app.services.security import PasswordService

class UserCreate(BaseModel):
    password: str

    def validate_password_complexity(self, password_service: PasswordService):
        result = password_service.validate_password(self.password)
        if not result.is_valid:
            raise ValueError(", ".join(result.errors))
```

**Deliverables:**
- ✅ All schemas updated
- ✅ Schemas accept services as parameters
- ✅ Validation logic delegated to services

**Success Criteria:**
- Schemas are lightweight (no heavy logic)
- Validation delegated to services
- No direct security imports

---

### Step 7: Update All Tests (Days 16-18)

**Objective:** Ensure all tests work with new architecture

**Test Categories:**

1. **Unit Tests (Days 16-17):**
   - Update imports in test files
   - Mock new services
   - Verify service methods are called correctly

2. **Integration Tests (Day 18):**
   - Update test fixtures
   - Use real services or mocks as appropriate
   - Verify end-to-end functionality

**Example Test Migration:**

**Before:**
```python
# tests/test_auth.py
from app.core.security import verify_password

def test_password_verification():
    hashed = "..."
    result = verify_password("password123", hashed)
    assert result is True
```

**After:**
```python
# tests/test_auth.py
from app.services.security import PasswordService

def test_password_verification():
    service = PasswordService()
    hashed = service.hash_password("password123")
    result = await service.verify_password("password123", hashed)
    assert result.is_valid is True
```

**Deliverables:**
- ✅ All 110+ test files updated
- ✅ Tests using mocked or real services
- ✅ 95%+ test pass rate

**Success Criteria:**
- All tests import from new locations
- Tests verify service interactions
- Test coverage maintained

---

### Step 8: Final Cleanup (Days 19-20)

**Objective:** Remove deprecated code and finalize migration

**Tasks:**

8.1. Remove Deprecated Functions from `app/core/security.py`
- Keep only `get_current_user` and `get_current_active_user` (used by FastAPI dependencies)
- Add deprecation warnings if any old functions remain
- Document migration in docstrings

8.2. Update Documentation
- Update `CLAUDE.md` with new architecture
- Update `README.md` with new import patterns
- Update API documentation

8.3. Create Migration Guide
```markdown
# Security Service Migration Guide

## For Developers

### Import Changes

**Old:**
```python
from app.core.security import get_password_hash
```

**New:**
```python
from app.services.security import get_password_hash
```

### Dependency Injection

**Old (direct import):**
```python
from app.core.security import verify_password

result = verify_password(plain, hashed)
```

**New (injected service):**
```python
from app.services.security import PasswordService
from fastapi import Depends

def endpoint(
    password_service: PasswordService = Depends(get_password_service),
):
    result = await password_service.verify_password(plain, hashed)
```

### Breaking Changes

None - All old functions are still available through convenience wrappers.
```

8.4. Run Final Validation
```bash
# Check for remaining old imports
grep -r "from app.core.security import" --include="*.py" . | grep -v ".backup"

# Run full test suite
pytest tests/ -v --cov=app --cov-report=html

# Type checking
npx tsc  # Frontend
mypy app/  # Backend (if configured)
```

**Deliverables:**
- ✅ Deprecated code removed
- ✅ Documentation updated
- ✅ Migration guide created
- ✅ All tests passing

**Success Criteria:**
- Zero old imports (except in deprecated `app.core.security`)
- 95%+ test pass rate
- Clean git history

---

## 📈 Progress Tracking

### Milestones

| Milestone | Target Date | Status | Completion |
|-----------|-------------|--------|------------|
| Step 1: DI Setup | Day 3 | ⏳ Pending | 0% |
| Step 2: Migration Script | Day 5 | ⏳ Pending | 0% |
| Step 3: Execute Migration | Day 8 | ⏳ Pending | 0% |
| Step 4: Update API Endpoints | Day 12 | ⏳ Pending | 0% |
| Step 5: Update Services | Day 14 | ⏳ Pending | 0% |
| Step 6: Update Schemas | Day 15 | ⏳ Pending | 0% |
| Step 7: Update Tests | Day 18 | ⏳ Pending | 0% |
| Step 8: Final Cleanup | Day 20 | ⏳ Pending | 0% |

### Daily Progress Checklist

**Day 1-3: Dependency Injection Setup**
- [ ] Choose DI framework
- [ ] Create `app/core/service_provider.py`
- [ ] Update `app/api/deps.py`
- [ ] Test DI injection works
- [ ] Document DI patterns

**Day 4-5: Migration Script**
- [ ] Create `scripts/migrate_security_imports.py`
- [ ] Create `scripts/verify_migration.py`
- [ ] Test script on sample files
- [ ] Add error handling
- [ ] Test script rollback capability

**Day 6-8: Execute Migration**
- [ ] Create git branch
- [ ] Run migration script
- [ ] Verify migration
- [ ] Fix manual issues
- [ ] Run test suite
- [ ] Fix test failures
- [ ] Commit changes

**Day 9-12: API Endpoints**
- [ ] Migrate auth endpoints
- [ ] Migrate user endpoints
- [ ] Migrate remaining endpoints
- [ ] Test all endpoints
- [ ] Update API documentation

**Day 13-14: Services**
- [ ] Update UserService
- [ ] Update other services
- [ ] Update CRUD classes
- [ ] Test services
- [ ] Verify no circular dependencies

**Day 15: Schemas**
- [ ] Update user schemas
- [ ] Update auth schemas
- [ ] Test schema validation
- [ ] Verify error messages

**Day 16-18: Tests**
- [ ] Update unit tests
- [ ] Update integration tests
- [ ] Mock services where needed
- [ ] Verify test coverage
- [ ] Fix failing tests

**Day 19-20: Cleanup**
- [ ] Remove deprecated code
- [ ] Update documentation
- [ ] Create migration guide
- [ ] Final validation
- [ ] Merge to main branch

---

## 🎯 Success Metrics

### Quantitative Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Files with old imports | 169 | 0 | 0 |
| Test pass rate | 85% | 95%+ | 95%+ |
| Code coverage | 75% | 75%+ | 75%+ |
| DI injection points | 0 | 50+ | 50+ |
| Lines of code in `app/core/security.py` | 1,660 | <200 | <200 |

### Qualitative Metrics

- ✅ All API endpoints use dependency injection
- ✅ Services are testable (mockable dependencies)
- ✅ Clear separation of concerns
- ✅ No circular dependencies
- ✅ Consistent architecture patterns

---

## ⚠️ Risks and Mitigation

### Risk 1: Test Failures
**Impact:** High
**Probability:** High
**Mitigation:**
- Run tests in phases (unit → integration → e2e)
- Fix tests incrementally
- Keep detailed log of changes

### Risk 2: Breaking Changes
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Maintain backward compatibility wrappers
- Extensive testing before merge
- Feature flagging if needed

### Risk 3: Circular Dependencies
**Impact:** Medium
**Probability:** Medium
**Mitigation:**
- Careful design of DI container
- Lazy imports where needed
- Dependency graph analysis

### Risk 4: Performance Regression
**Impact:** Low
**Probability:** Low
**Mitigation:**
- Benchmark before/after
- Optimize hot paths
- Profile service calls

---

## 🔄 Rollback Plan

If migration encounters critical issues:

1. **Immediate Rollback:**
   ```bash
   git checkout main
   git branch -D feature/security-service-migration
   ```

2. **Partial Rollback:**
   - Revert specific commits
   - Keep completed work
   - Fix issues and retry

3. **Rollforward:**
   - Fix issues in place
   - Don't revert, complete migration
   - Usually faster than rollback

---

## 📚 Resources

### Documentation
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### Internal Documentation
- `SOLID_PRINCIPLES_ANALYSIS.md` - Original analysis
- `SOLID_REMEDIATION_IMPLEMENTATION.md` - Phase 1 completion
- `CLAUDE.md` - Project architecture guide

### Tools
- `scripts/migrate_security_imports.py` - Migration script
- `scripts/verify_migration.py` - Verification script
- `app/core/service_provider.py` - DI container

---

## ✅ Exit Criteria

Phase 2 is complete when:

- [x] All 169 files migrated to new imports
- [x] Dependency injection container implemented
- [x] All API endpoints use injected services
- [x] All services use constructor injection
- [x] All schemas delegate validation to services
- [x] All tests updated and passing (95%+)
- [x] Deprecated code removed from `app.core.security.py`
- [x] Documentation updated
- [x] Migration guide created
- [x] Code merged to main branch
- [x] Zero regressions in production

---

## 🚀 Next Phase Preview

**Phase 3: Repository Pattern Implementation (2-3 months, 320 hours)**

After completing Phase 2, the next phase will:

1. Implement full Repository Pattern for data access
2. Create SQLAlchemy repository implementations
3. Move all database logic from services to repositories
4. Enrich domain models with behavior
5. Choose and implement Clean Architecture or Hexagonal Architecture

This will complete the SOLID remediation and establish a robust, maintainable architecture.

---

**Document Version:** 1.0
**Last Updated:** 2025-01-18
**Author:** Development Team
**Status:** Ready for Implementation
