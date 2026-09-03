# BaseService Patterns Cheat Sheet

**Developer Reference** - Common patterns when working with BaseService

---

## 🎯 BaseService Inheritance Template

```python
from app.services.base_service import BaseService

class YourService(BaseService[ModelType, CreateSchema, UpdateSchema]):
    """Minimal viable service."""

    @property
    def model(self) -> type[ModelType]: return ModelType

    @property
    def cache_strategy(self) -> CacheStrategy: return CacheStrategy.YOUR_CHOICE

    def get_cache_key(self, operation: str, **kwargs) -> str:
        return f"your_prefix:{operation}:{kwargs.get('id')}"

    def validate_create_data(self, data: CreateSchema) -> None: pass

    def validate_update_data(self, data: UpdateSchema, existing: ModelType) -> None: pass
```

---

## 📦 CRUD Operations (Inherited)

| Operation | Method | Returns | Cache |
|-----------|--------|---------|-------|
| **Get One** | `get_by_id(db, id)` | Model \| None | ✅ |
| **List Many** | `list(db, skip, limit, filters, sort_by, sort_desc)` | List[Model] | ✅ |
| **Count** | `count(db, filters)` | int | ✅ |
| **Create** | `create(db, data, **kwargs)` | Model | Auto-invalidate |
| **Update** | `update(db, id, data, **kwargs)` | Model \| None | Auto-invalidate |
| **Delete** | `delete(db, id, deleted_by_id)` | bool | Auto-invalidate |
| **Bulk Create** | `bulk_create(db, data_list, **kwargs)` | List[Model] | Auto-invalidate |

---

## 🔒 Cache Strategy Options

```python
from app.core.cache_strategy import CacheStrategy

CacheStrategy.USER_PROFILE         # 5 min TTL, user data
CacheStrategy.TEAM_DATA           # 10 min TTL, team data
CacheStrategy.ASSESSMENT_DATA     # 30 min TTL, assessment configs
CacheStrategy.ASSESSMENT_RESULTS  # 1 hour TTL, completed assessments
CacheStrategy.ORGANIZATION_DATA   # 1 hour TTL, org settings
CacheStrategy.AUTH_TOKENS         # 30 min TTL, authentication
CacheStrategy.API_RESPONSES       # 1 min TTL, API responses
CacheStrategy.SESSION_DATA        # 2 hours TTL, user sessions
```

---

## 🎨 Common Patterns

### Pattern 1: Simple List with Filters

```python
async def get_active_users(self, db: AsyncSession, org_id: UUID) -> List[User]:
    """Get active users for an organization."""
    return await self.list(
        db,
        filters={"organization_id": org_id, "status": "active"},
        sort_by="created_at",
        sort_desc=True
    )
```

### Pattern 2: Create with Extra Fields

```python
@transaction_manager.transaction
async def create_with_owner(self, db: AsyncSession, data: TeamCreate, creator_id: UUID) -> Team:
    """Create team and assign creator as owner."""
    # BaseService.create() handles validation, timestamps, caching
    team = await self.create(db, data, created_by_id=creator_id)

    # Add owner as team member
    member = TeamMember(team_id=team.id, user_id=creator_id, role=TeamRole.OWNER)
    db.add(member)
    await db.flush()

    return team
```

### Pattern 3: Update with Validation

```python
@transaction_manager.transaction
async def safe_update(self, db: AsyncSession, id: UUID, data: UpdateSchema, user_id: UUID) -> Model:
    """Update with ownership verification."""
    # Verify ownership first
    existing = await self.get_by_id(db, id)
    if existing.user_id != user_id:
        raise ValidationException("Not authorized", field="authorization")

    # BaseService.update() handles validation, timestamps, cache invalidation
    return await self.update(db, id, data)
```

### Pattern 4: Soft Delete

```python
@transaction_manager.transaction
async def soft_delete(self, db: AsyncSession, id: UUID, deleted_by_id: UUID) -> bool:
    """Soft delete by setting deleted_at timestamp."""
    from datetime import datetime

    # Don't use BaseService.delete() - it's a hard delete
    entity = await self.get_by_id(db, id)
    if not entity:
        return False

    entity.deleted_at = datetime.utcnow()
    entity.deleted_by_id = deleted_by_id
    await db.flush()

    # Manually invalidate cache
    await self._invalidate_related_caches(entity, "delete")

    return True
```

### Pattern 5: Get or Create

```python
async def get_or_create(self, db: AsyncSession, **filters) -> Model:
    """Get entity matching filters or create new one."""
    # Try to find existing
    existing = await self.list(db, filters=filters, limit=1)
    if existing:
        return existing[0]

    # Create new
    create_data = CreateSchema(**filters)
    return await self.create(db, create_data)
```

---

## 🧩 Validation Patterns

### Validate Required Fields

```python
def validate_create_data(self, data: CreateSchema) -> None:
    if not data.email or "@" not in data.email:
        raise ValidationException("Invalid email", field="email")
    if not data.full_name or len(data.full_name) < 3:
        raise ValidationException("Name too short", field="full_name")
```

### Validate Business Rules

```python
def validate_update_data(self, data: UpdateSchema, existing: Model) -> None:
    # Prevent changing immutable fields
    if data.organization_id and data.organization_id != existing.organization_id:
        raise ValidationException("Cannot change organization", field="organization_id")

    # Validate status transitions
    if data.status and existing.status == "completed":
        raise ValidationException("Cannot modify completed assessment", field="status")
```

### Validate Related Data

```python
def validate_create_data(self, data: TeamCreate) -> None:
    # Check if team name already exists in organization
    existing = await self.list(
        db,
        filters={"organization_id": data.organization_id, "name": data.name},
        limit=1
    )
    if existing:
        raise ValidationException("Team name already exists", field="name")
```

---

## 🔐 Security Patterns

### Ownership Verification

```python
async def _verify_ownership(self, db: AsyncSession, id: UUID, user_id: UUID) -> Model:
    """Verify user owns the resource."""
    entity = await self.get_by_id(db, id)
    if not entity or entity.user_id != user_id:
        raise ValidationException("Not authorized", field="authorization")
    return entity
```

### Role-Based Access

```python
async def check_permission(self, db: AsyncSession, team_id: UUID, user_id: UUID, required_role: TeamRole) -> bool:
    """Check if user has required role or higher."""
    user_role = await self.get_user_role(db, team_id, user_id)
    if not user_role:
        return False

    role_hierarchy = {
        TeamRole.MEMBER: 1,
        TeamRole.ADMIN: 2,
        TeamRole.OWNER: 3,
    }

    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
```

---

## 📊 Advanced Query Patterns

### Complex Filtering

```python
async def search_advanced(self, db: AsyncSession, **criteria) -> List[Model]:
    """Advanced search with multiple criteria."""
    filters = {}

    if criteria.get("status"):
        filters["status"] = criteria["status"]
    if criteria.get("organization_id"):
        filters["organization_id"] = criteria["organization_id"]
    if criteria.get("created_after"):
        filters["created_at"] = criteria["created_after"]

    return await self.list(
        db,
        skip=criteria.get("skip", 0),
        limit=criteria.get("limit", 100),
        filters=filters,
        sort_by=criteria.get("sort_by", "created_at"),
        sort_desc=criteria.get("sort_desc", True)
    )
```

### Using Query Builder

```python
async def complex_query(self, db: AsyncSession) -> List[Model]:
    """Use BaseService query builder for complex queries."""
    query = self.query(db)
    result = await query.join("related_table") \
        .filter(Model.status == "active", RelatedTable.enabled == True) \
        .order_by("created_at", desc=True) \
        .limit(100) \
        .execute()

    return result
```

---

## 🧪 Testing Patterns

### Test CRUD Operations

```python
@pytest.mark.asyncio
async def test_create_and_get(db: AsyncSession):
    """Test create and get operations."""
    data = YourCreate(name="Test", value=123)
    created = await service.create(db, data)

    retrieved = await service.get_by_id(db, created.id)
    assert retrieved.name == "Test"
    assert retrieved.value == 123
```

### Test Validation

```python
def test_validate_create_data():
    """Test validation logic."""
    service = YourService()

    # Valid data
    valid = YourCreate(name="Valid Name")
    service.validate_create_data(valid)  # Should not raise

    # Invalid data
    invalid = YourCreate(name="")
    with pytest.raises(ValidationException):
        service.validate_create_data(invalid)
```

### Test Cache Invalidation

```python
@pytest.mark.asyncio
async def test_cache_invalidation(db: AsyncSession):
    """Test that cache is invalidated on updates."""
    entity = await service.create(db, data)

    # First call - cache miss, fetches from DB
    first = await service.get_by_id(db, entity.id)

    # Update entity
    await service.update(db, entity.id, UpdateSchema(name="Updated"))

    # Second call - should fetch updated data from DB, not cache
    second = await service.get_by_id(db, entity.id)
    assert second.name == "Updated"
```

---

## ⚡ Performance Tips

### 1. Use Filters Effectively

```python
# ❌ Bad - Fetch all then filter in Python
all_users = await service.list(db, limit=10000)
active_users = [u for u in all_users if u.status == "active"]

# ✅ Good - Let database filter
active_users = await service.list(db, filters={"status": "active"})
```

### 2. Select Only Needed Relations

```python
# ❌ Bad - Fetches all relations
user = await service.get_by_id(db, user_id, include_relations=True)

# ✅ Good - Fetches specific relations
user = await service.get_by_id(
    db,
    user_id,
    include_relations=True,
    relations=["organization", "team"]
)
```

### 3. Use Pagination

```python
# ❌ Bad - Could fetch thousands of records
all_users = await service.list(db)

# ✅ Good - Paginate
users = await service.list(db, skip=0, limit=100)
```

### 4. Leverage Cache

```python
# ❌ Bad - Queries database every time
for user_id in user_ids:
    user = await raw_sql_query(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ Good - Uses cached data when available
for user_id in user_ids:
    user = await service.get_by_id(db, user_id)  # Automatic caching
```

---

## 🐛 Common Mistakes

### ❌ Mistake 1: Forgetting to Call Super

```python
# ❌ Wrong
def __init__(self):
    self.my_cache = {}  # Missing super().__init__()

# ✅ Correct
def __init__(self):
    super().__init__()  # Initialize BaseService first
    self.my_cache = {}  # Then your custom initialization
```

### ❌ Mistake 2: Instantiating CacheStrategy

```python
# ❌ Wrong
@property
def cache_strategy(self) -> CacheStrategy:
    return CacheStrategy(enabled=True, ttl_seconds=300)  # Can't instantiate Enum

# ✅ Correct
@property
def cache_strategy(self) -> CacheStrategy:
    return CacheStrategy.USER_PROFILE  # Return enum value
```

### ❌ Mistake 3: Manual Transaction Handling

```python
# ❌ Wrong
@transaction_manager.transaction
async def create(self, db: AsyncSession, data: CreateSchema) -> Model:
    async with db.begin():  # Don't need this!
        return await self.create(db, data)

# ✅ Correct
@transaction_manager.transaction
async def create(self, db: AsyncSession, data: CreateSchema) -> Model:
    return await self.create(db, data)  # Decorator handles transactions
```

### ❌ Mistake 4: Not Using Validation

```python
# ❌ Wrong
async def create(self, db: AsyncSession, data: CreateSchema) -> Model:
    if not data.name:  # Validation should be in validate_create_data()
        raise ValidationException("Name required")
    return await self.create(db, data)

# ✅ Correct
def validate_create_data(self, data: CreateSchema) -> None:
    if not data.name:
        raise ValidationException("Name required")

async def create(self, db: AsyncSession, data: CreateSchema) -> Model:
    # BaseService automatically calls validate_create_data()
    return await super().create(db, data)
```

---

## 📝 Quick Decision Tree

```
Need to interact with database?
├─ Yes → Is it a simple CRUD operation?
│   ├─ Yes → Use BaseService method (get_by_id, list, create, update, delete)
│   └─ No → Is it complex business logic?
│       ├─ Yes → Create custom method with @transaction_manager.transaction
│       └─ No → Can BaseService.list() with filters handle it?
│           ├─ Yes → Use list() with filters
│           └─ No → Use query builder
└─ No → Should this be a helper method?
    └─ Yes → Create @staticmethod or @classmethod
```

---

## 🎓 Learning Resources

- **REFACTORED_SERVICES_QUICK_START.md** - Getting started guide
- **MIGRATION_GUIDE.md** - How to migrate existing services
- **app/services/base_service.py** - Read the source!
- **tests/test_refactored_services.py** - Example tests

---

**Last Updated**: 2025-12-02
**Version**: 1.0
