# AssessmentService Migration Plan

**Service**: `app/services/assessment_service.py` → `app/services/assessment_service_refactored.py`
**Complexity**: High (complex scoring algorithms, security checks, caching)
**Estimated Effort**: 4-6 hours

---

## Current State Analysis

### Service Structure
- **Type**: Class-based service (already well-structured)
- **Lines of Code**: 584
- **Public Methods**: 9
- **Private Methods**: 4
- **Dependencies**: Already uses `@transaction_manager`, `@async_cached`

### Methods to Migrate

#### CRUD Operations (BaseService provides most)
1. ✅ `get_by_id(assessment_id)` → Can use BaseService `get_by_id()`
2. ✅ `create(data, user_id)` → Can use BaseService `create()`
3. ✅ `update(id, data, user_id)` → Can use BaseService `update()`
4. ✅ `delete(id, user_id)` → Can use BaseService `delete()`

#### Custom Business Logic (must implement)
5. ⚠️ `complete(assessment_id, user_id, responses)` - **Complex scoring**
6. ⚠️ `get_assessment_results(assessment_id, user_id)` - **Complex queries**
7. ⚠️ `get_user_assessments(user_id, status)` - **List with filters**
8. ⚠️ `get_organization_assessments(org_id)` - **Aggregation**
9. ⚠️ `to_dict(assessment)` - **Serialization helper**

#### Security & Validation (must preserve)
10. 🔒 `_verify_ownership(assessment_id, user_id)` - **Critical security**
11. 🔒 `_validate_framework(framework_code)` - **Business validation**
12. 🔒 `_is_admin(user_id)` - **Authorization check**
13. 💰 `_calculate_scores(assessment, responses)` - **Core algorithm**

---

## Migration Strategy

### Phase 1: Basic Structure (30 minutes)
- [x] Create `assessment_service_refactored.py`
- [x] Extend `BaseService[Assessment, AssessmentCreate, AssessmentUpdate]`
- [x] Implement abstract properties: `model`, `cache_strategy`, `get_cache_key`
- [x] Implement validation methods: `validate_create_data`, `validate_update_data`

### Phase 2: CRUD Methods (30 minutes)
- [x] Remove `@async_cached` decorators (BaseService handles caching)
- [x] Keep `@transaction_manager` for write operations
- [x] Update `create()` to use BaseService pattern
- [x] Update `update()` to use BaseService pattern
- [x] Remove redundant CRUD methods (use BaseService inherited)

### Phase 3: Business Logic (2-3 hours)
- [ ] Migrate `complete()` with scoring logic
- [ ] Migrate `get_assessment_results()` with complex queries
- [ ] Migrate list methods with filtering
- [ ] Preserve all security checks

### Phase 4: Testing (1 hour)
- [ ] Create test suite
- [ ] Verify scoring accuracy
- [ ] Test security features
- [ ] Performance testing

---

## Key Design Decisions Needed

### Decision 1: Scoring Algorithm Architecture ⚠️

**Context**: The `_calculate_scores()` method contains complex business logic that:
- Iterates through assessment responses
- Applies framework-specific scoring rules
- Calculates trait scores and percentages
- Returns complex score structure

**Current Implementation**:
```python
@staticmethod
def _calculate_scores(assessment: Assessment, responses: list[Response]) -> dict:
    # 50+ lines of complex scoring logic
    # Framework-specific calculations (MBTI, Big Five, DISC, etc.)
    # Returns dict with trait_scores, percentages, framework_type
```

**Question**: How should we handle this in the refactored service?

**Options**:

**A) Keep as Static Method** (Recommended)
```python
class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    @staticmethod
    def _calculate_scores(assessment: Assessment, responses: list[Response]) -> dict:
        # Keep existing logic unchanged
```
- ✅ Preserves proven algorithm
- ✅ No risk of breaking scoring
- ✅ Easy to test in isolation
- ❌ Not using BaseService features

**B) Make Instance Method**
```python
class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    def _calculate_scores(self, assessment: Assessment, responses: list[Response]) -> dict:
        # Can use self.logger, etc.
```
- ✅ Can use BaseService logging
- ✅ More consistent with rest of service
- ❌ Requires self parameter everywhere
- ❌ Minimal benefit

**C) Extract to Separate ScoringService**
```python
class AssessmentScoringStrategy:
    @staticmethod
    def calculate(assessment: Assessment, responses: list[Response]) -> dict:
        # Pure scoring logic, no database dependencies

class AssessmentService(BaseService[...]):
    scoring_strategy = AssessmentScoringStrategy()
```
- ✅ Separation of concerns
- ✅ Easier to test
- ✅ Could be reused elsewhere
- ❌ More complex architecture
- ❌ Over-engineering for current needs

### Decision 2: Security Check Placement

**Context**: `_verify_ownership()` is called in multiple methods to ensure users can only access their own assessments.

**Question**: Should this remain a private method or be implemented differently?

**Options**:

**A) Keep as Private Method**
```python
class AssessmentService(BaseService[...]):
    async def _verify_ownership(self, db, assessment_id, user_id):
        # Keep existing implementation
```
- ✅ Simple, proven pattern
- ✅ Encapsulated within service

**B) Move to Endpoint Layer**
```python
# In endpoint:
async def update_assessment(assessment_id, ...):
    await permission_service.check_assessment_ownership(assessment_id, user_id)
    # Then call service
```
- ✅ Clearer separation (security vs business logic)
- ✅ Reusable across services
- ❌ Requires new permission service
- ❌ More complex

**C) Use FastAPI Dependencies**
```python
async def get_assessment_if_owner(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Assessment:
    # Check ownership and return assessment
```
- ✅ FastAPI best practice
- ✅ Reusable across endpoints
- ❌ Changes all endpoint signatures
- ❌ More work upfront

---

## Implementation Order

### Step 1: Setup BaseService Pattern
```python
class AssessmentService(BaseService[Assessment, AssessmentCreate, AssessmentUpdate]):
    @property
    def model(self) -> type[Assessment]:
        return Assessment

    @property
    def cache_strategy(self) -> CacheStrategy:
        return CacheStrategy.ASSESSMENT_DATA

    def get_cache_key(self, operation: str, **kwargs) -> str:
        if operation == "get_by_id":
            return f"assessment:id:{kwargs.get('assessment_id')}"
        # ... other keys
```

### Step 2: Implement Validation
```python
def validate_create_data(self, data: AssessmentCreate) -> None:
    # Check framework is supported
    if data.framework_code not in SUPPORTED_FRAMEWORKS:
        raise ValidationException(...)

def validate_update_data(self, data: AssessmentUpdate, existing: Assessment) -> None:
    # Only allow certain fields to be updated
    for field in data.dict(exclude_unset=True):
        if field not in ALLOWED_UPDATE_FIELDS:
            raise ValidationException(...)
```

### Step 3: Migrate Business Logic
```python
@transaction_manager.transaction
async def complete(self, db: AsyncSession, assessment_id: UUID, user_id: UUID, responses: list) -> Assessment:
    # Verify ownership
    assessment = await self._verify_ownership(db, assessment_id, user_id)

    # Calculate scores
    scores = self._calculate_scores(assessment, responses)

    # Update assessment
    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()
    assessment.scores = scores

    return assessment
```

---

## Testing Strategy

### Unit Tests
- [ ] Test scoring algorithm accuracy
- [ ] Test ownership verification
- [ ] Test framework validation
- [ ] Test CRUD operations

### Integration Tests
- [ ] Test complete assessment flow
- [ ] Test security checks
- [ ] Test concurrent updates
- [ ] Test cache invalidation

### Comparison Tests
- [ ] Run same test against old and new service
- [ ] Compare results for identical inputs
- [ ] Verify no regressions

---

## Risk Mitigation

### High Risk Areas
1. **Scoring Algorithm** - Core business logic, must be exact
   - Mitigation: Keep as static method, comprehensive tests

2. **Security Checks** - Ownership verification
   - Mitigation: Preserve exact logic, add security tests

3. **Caching** - Cache key consistency
   - Mitigation: Use BaseService pattern, test cache hits/misses

### Rollback Plan
- Keep old service until refactored version is fully tested
- Use feature flags to switch between old/new
- Monitor metrics after deployment

---

## Success Criteria

✅ All existing tests pass with refactored service
✅ No performance degradation
✅ Security features preserved
✅ Cache hit rate maintained or improved
✅ Code reduction > 40%
✅ Easier to extend with new features

---

**Next Step**: Implement Phase 1 (Basic Structure) and Phase 2 (CRUD Methods)
