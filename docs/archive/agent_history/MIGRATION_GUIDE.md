# Service Layer Migration Guide
## Migrating from Functional Services to BaseService Pattern

**Purpose**: This guide provides step-by-step instructions for migrating functional services to extend `BaseService`, ensuring architectural consistency across the codebase.

**Status**: 149 services identified for migration | 1 completed (UserService) | 148 remaining

---

## Table of Contents

1. [Why Migrate?](#why-migrate)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Migration Pattern](#migration-pattern)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Common Patterns](#common-patterns)
6. [Validation](#validation)
7. [Troubleshooting](#troubleshooting)

---

## Why Migrate?

### Current State (Functional Pattern)

```python
# ❌ BEFORE: Functional approach
from app.core.cache import cached

@cached(expire=1800, key_prefix="assessment")
async def get_assessment(db: AsyncSession, assessment_id: int) -> dict | None:
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if assessment:
        return assessment_to_dict(assessment)
    return None
```

**Problems:**
- ❌ Manual error handling required
- ❌ Decorator-based caching (inconsistent)
- ❌ No transaction management
- ❌ Inconsistent logging
- ❌ No audit trail
- ❌ Duplicated code across services

### Target State (BaseService Pattern)

```python
# ✅ AFTER: BaseService pattern
class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    async def get_by_id(self, db: AsyncSession, assessment_id: int) -> Assessment | None:
        # Automatic error handling, caching, logging
        return await super().get_by_id(db, assessment_id)
```

**Benefits:**
- ✅ Automatic error handling via `@handle_database_errors` decorator
- ✅ Consistent caching strategy via `CacheStrategy`
- ✅ Built-in transaction management
- ✅ Structured logging with `EventType`
- ✅ Audit trail integration
- ✅ 60% less code

---

## Pre-Migration Checklist

Before migrating a service, ensure:

- [ ] Read the existing service file completely
- [ ] Identify all public functions (non-`_` prefixed)
- [ ] Document current caching strategy
- [ ] List all database operations
- [ ] Note any special validation logic
- [ ] Identify dependencies on other services
- [ ] Check for existing tests

---

## Migration Pattern

### The 7-Step Migration Process

#### Step 1: Create Service Class Structure

```python
from app.services.base_service import BaseService
from app.db.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate

class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    """Assessment service extending BaseService."""
    pass
```

#### Step 2: Implement Abstract Properties

```python
class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    @property
    def model(self) -> type[Assessment]:
        return Assessment

    @property
    def cache_strategy(self) -> CacheStrategy:
        return CacheStrategy(
            enabled=True,
            ttl_seconds=1800,  # 30 minutes
            key_prefix="assessment",
        )

    def get_cache_key(self, operation: str, **kwargs) -> str:
        if operation == "get_by_id":
            return f"assessment:id:{kwargs.get('assessment_id')}"
        return f"assessment:{operation}"

    def validate_create_data(self, data: AssessmentCreate) -> None:
        if not data.name or len(data.name) < 3:
            raise ValidationException("Name must be at least 3 characters", field="name")

    def validate_update_data(self, data: AssessmentUpdate, existing: Assessment) -> None:
        if data.status and existing.status == "completed":
            raise ValidationException("Cannot modify completed assessment", field="status")
```

#### Step 3: Migrate CRUD Operations

**Before:**
```python
@cached(expire=1800, key_prefix="assessment")
async def get_assessment(db: AsyncSession, assessment_id: int) -> dict | None:
    try:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()
        if assessment:
            return assessment_to_dict(assessment)
        return None
    except Exception as e:
        logger.error(f"Failed to get assessment: {e}")
        raise
```

**After:**
```python
async def get_by_id(self, db: AsyncSession, assessment_id: int) -> Assessment | None:
    """Get assessment by ID (uses BaseService built-in features)."""
    return await super().get_by_id(db, assessment_id)
```

#### Step 4: Migrate Custom Queries

**Before:**
```python
@cached(expire=600, key_prefix="assessment")
async def get_assessments_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    assessments = result.scalars().all()
    return [assessment_to_dict(a) for a in assessments]
```

**After:**
```python
async def get_by_user(
    self,
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Assessment]:
    """Get assessments by user with automatic error handling and logging."""
    self.logger.debug(
        EventType.DATABASE_OPERATION,
        f"Retrieving assessments for user: {user_id}",
        operation="get_by_user",
        user_id=str(user_id),
    )

    query = select(Assessment).where(Assessment.user_id == user_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    assessments = result.scalars().all()

    self.logger.debug(
        EventType.DATABASE_OPERATION,
        f"Retrieved {len(assessments)} assessments",
        operation="get_by_user",
        count=len(assessments),
    )

    return assessments
```

#### Step 5: Migrate Write Operations

**Before:**
```python
async def create_assessment(db: AsyncSession, data: AssessmentCreate) -> Assessment:
    try:
        assessment = Assessment(**data.dict())
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment
    except IntegrityError as e:
        await db.rollback()
        raise ValueError(f"Failed to create assessment: {e}")
```

**After:**
```python
from app.core.database_transactions import transaction_manager

@transaction_manager.transaction
async def create_assessment(
    self, db: AsyncSession, data: AssessmentCreate
) -> Assessment:
    """Create assessment with automatic transaction management."""
    # Validate input
    self.validate_create_data(data)

    # Create
    assessment = Assessment(**data.model_dump())
    assessment.created_at = datetime.utcnow()

    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)

    self.logger.info(
        EventType.DATABASE_OPERATION,
        f"Assessment created: {assessment.id}",
        operation="create_assessment",
        assessment_id=assessment.id,
    )

    return assessment
```

#### Step 6: Remove Old Code

```python
# DELETE these lines:
# - Old standalone functions
# - @cached decorators
# - Manual error handling (try/except blocks)
# - Manual transaction management (commit/rollback)
```

#### Step 7: Update Dependencies

**In endpoint files:**

**Before:**
```python
from app.services.assessment_service import get_assessment, create_assessment

@router.get("/{assessment_id}")
async def get_assessment_endpoint(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
):
    assessment = await get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Not found")
    return assessment
```

**After:**
```python
from app.services.assessment_service_refactored import assessment_service

@router.get("/{assessment_id}")
async def get_assessment_endpoint(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
):
    assessment = await assessment_service.get_by_id(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Not found")
    return assessment
```

---

## Common Patterns

### Pattern 1: Removing Dict Conversion

**Before:**
```python
async def get_assessment(db: AsyncSession, assessment_id: int) -> dict | None:
    assessment = await _get_assessment_model(db, assessment_id)
    return assessment_to_dict(assessment) if assessment else None
```

**After:**
```python
async def get_by_id(self, db: AsyncSession, assessment_id: int) -> Assessment | None:
    """Returns model directly (FastAPI handles serialization)."""
    return await super().get_by_id(db, assessment_id)
```

### Pattern 2: Soft Delete Handling

**Before:**
```python
async def get_assessment(db: AsyncSession, assessment_id: int) -> dict | None:
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .where(Assessment.deleted_at.is_(None))  # Manual soft-delete filter
    )
    # ...
```

**After:**
```python
# BaseService handles soft-delete automatically!
async def get_by_id(self, db: AsyncSession, assessment_id: int) -> Assessment | None:
    return await super().get_by_id(db, assessment_id, include_deleted=False)
```

### Pattern 3: Eager Loading Relations

**Before:**
```python
async def get_assessment_with_questions(db: AsyncSession, assessment_id: int) -> dict:
    result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.questions))
        .where(Assessment.id == assessment_id)
    )
    # ...
```

**After:**
```python
async def get_with_questions(
    self, db: AsyncSession, assessment_id: int
) -> Assessment | None:
    """Get assessment with eager-loaded questions."""
    return await self.get_by_id(
        db,
        assessment_id,
        include_relations=True,
        relations=["questions"],
    )
```

### Pattern 4: Search/Filter Operations

**Before:**
```python
async def search_assessments(
    db: AsyncSession,
    query: str,
    skip: int = 0,
    limit: int = 20,
) -> list[dict]:
    # Complex query building
    filters = []
    if query:
        filters.append(Assessment.name.ilike(f"%{query}%"))

    result = await db.execute(
        select(Assessment)
        .where(*filters)
        .offset(skip)
        .limit(limit)
    )
    # ...
```

**After:**
```python
async def search(
    self,
    db: AsyncSession,
    query: str,
    skip: int = 0,
    limit: int = 20,
) -> list[Assessment]:
    """Search assessments with automatic error handling and logging."""
    self.logger.debug(
        EventType.DATABASE_OPERATION,
        f"Searching assessments: {query}",
        operation="search",
        query=query,
    )

    query_obj = select(Assessment)

    if query:
        query_obj = query_obj.where(Assessment.name.ilike(f"%{query}%"))

    query_obj = query_obj.offset(skip).limit(limit)
    result = await db.execute(query_obj)
    assessments = result.scalars().all()

    return assessments
```

---

## Validation

After migration, validate your changes:

### 1. Run Architecture Validation Script

```bash
python scripts/validate_architecture.py --services
```

Expected output should show **no issues** for your migrated service.

### 2. Run Type Checking

```bash
npm run type-check
```

### 3. Run Tests

```bash
pytest tests/api/test_assessments.py -v
```

### 4. Manual Testing

- [ ] Test CRUD operations via API
- [ ] Verify caching works (check Redis)
- [ ] Check error handling (try invalid inputs)
- [ ] Verify logging (check application logs)
- [ ] Test transaction rollback (simulate errors)

---

## Migration Priority Queue

Based on validation script results, migrate in this order:

### Phase 1: High-Frequency Services (Week 1-2)
1. `assessment_service.py` - Core business logic
2. `team_service.py` - Team operations
3. `response_service.py` - Response handling

### Phase 2: Integration Services (Week 3-4)
4. `email_service.py` - Email operations
5. `notification_service.py` - Notifications
6. `analytics_service.py` - Analytics

### Phase 3: Supporting Services (Week 5-6)
7. `hris_integration_service.py`
8. `data_export_service.py`
9. `reporting_service.py`

### Phase 4: Low-Priority Services (Week 7-8)
10. All remaining services

---

## Troubleshooting

### Issue 1: Caching Not Working

**Symptom:** Cache misses consistently

**Solution:**
```python
# Make sure cache_key returns unique values
def get_cache_key(self, operation: str, **kwargs) -> str:
    # Include all relevant parameters
    return f"assessment:{operation}:{kwargs.get('assessment_id')}:{kwargs.get('user_id', 'none')}"
```

### Issue 2: Validation Not Called

**Symptom:** Invalid data passes through

**Solution:**
```python
# Make sure to call validation in write operations
@transaction_manager.transaction
async def create(self, db: AsyncSession, data: AssessmentCreate) -> Assessment:
    self.validate_create_data(data)  # <-- Don't forget this!
    # ... rest of implementation
```

### Issue 3: Logging Not Appearing

**Symptom:** No logs in application output

**Solution:**
```python
# Make sure to use self.logger from BaseService
# NOT: logger = logging.getLogger(__name__)
self.logger.info(EventType.DATABASE_OPERATION, "Message", ...)
```

### Issue 4: Transaction Not Rolling Back

**Symptom:** Changes persist even after error

**Solution:**
```python
# Make sure to use @transaction_manager.transaction decorator
@transaction_manager.transaction
async def update(self, db: AsyncSession, ...):
    # Changes will auto-rollback on exception
```

---

## Quick Reference Card

### BaseService Methods Available

```python
# Inherited from BaseService (don't rewrite these):
await self.get_by_id(db, id)                          # Get single entity
await self.list(db, skip=0, limit=100)                # List entities
await self.create(db, obj_in)                         # Create entity
await self.update(db, db_obj, obj_in)                 # Update entity
await self.delete(db, id)                             # Delete entity

# Must implement (abstract):
self.model (property)                                 # SQLAlchemy model
self.cache_strategy (property)                        # Caching config
self.get_cache_key(operation, **kwargs)              # Cache key gen
self.validate_create_data(data)                       # Create validation
self.validate_update_data(data, existing)             # Update validation
```

### Common Decorators

```python
from app.core.database_transactions import transaction_manager
from app.core.error_handling import handle_database_errors

@transaction_manager.transaction                      # Auto commit/rollback
async def write_operation(self, db, ...):
    pass

@handle_database_errors("operation_name")            # Auto error handling
async def risky_operation(db, ...):
    pass
```

### Logging Events

```python
from app.core.structured_logging import EventType

self.logger.debug(EventType.DATABASE_OPERATION, "Debug msg", ...)
self.logger.info(EventType.DATABASE_OPERATION, "Info msg", ...)
self.logger.warning(EventType.SECURITY_EVENT, "Warning msg", ...)
self.logger.error(EventType.SECURITY_EVENT, "Error msg", ...)
```

---

## Success Metrics

Track migration progress:

```bash
# Run before migration
python scripts/validate_architecture.py --services > before.txt

# Run after migration
python scripts/validate_architecture.py --services > after.txt

# Compare
diff before.txt after.txt
```

**Target:**
- ✅ Zero critical issues in service layer
- ✅ Zero services without caching strategy
- ✅ 100% service inheritance from BaseService

---

## Additional Resources

- **Example Migration**: See `app/services/user_service_refactored.py`
- **BaseService Reference**: See `app/services/base_service.py`
- **Validation Script**: See `scripts/validate_architecture.py`
- **Architecture Docs**: See `REFACTORING_GUIDE.md`

---

**Questions?** Check the troubleshooting section or review the example migration in `user_service_refactored.py`.
