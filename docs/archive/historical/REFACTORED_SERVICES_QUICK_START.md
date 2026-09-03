# Refactored Services Quick Start Guide

**For Developers**: How to use the new BaseService-based services

---

## 🚀 Quick Reference

### Using Refactored Services

```python
# Import the refactored service (singleton instance)
from app.services.user_service_refactored import user_service
from app.services.team_service_refactored import team_service
from app.services.assessment_service_refactored import assessment_service

# All services work the same way!
```

---

## 📋 Common Patterns

### Pattern 1: Basic CRUD Operations

All refactored services inherit these from `BaseService`:

```python
from app.services.user_service_refactored import user_service
from sqlalchemy.ext.asyncio import AsyncSession

# Get by ID
user = await user_service.get_by_id(db, user_id=uuid)

# List with pagination and filtering
users = await user_service.list(
    db,
    skip=0,
    limit=100,
    filters={"organization_id": org_id, "status": "active"},
    sort_by="created_at",
    sort_desc=True
)

# Count
count = await user_service.count(db, filters={"status": "active"})

# Create
new_user = await user_service.create(db, user_create_data)

# Update
updated_user = await user_service.update(db, user_id, user_update_data)

# Delete
deleted = await user_service.delete(db, user_id, deleted_by_id=current_user_id)
```

### Pattern 2: Service-Specific Methods

Each service has additional business logic methods:

```python
# UserService
await user_service.verify_user_email(db, user_id)
await user_service.request_password_reset(db, email)
await user_service.confirm_password_reset(db, token, new_password)
await user_service.update_last_login(db, user_id)

# TeamService
team = await team_service.create_team(db, team_data, creator_id)
await team_service.add_member(db, team_id, user_id, role)
await team_service.remove_member(db, team_id, user_id)
await team_service.update_member_role(db, team_id, user_id, new_role)
is_member = await team_service.is_member(db, team_id, user_id)
is_admin = await team_service.is_admin_or_owner(db, team_id, user_id)

# AssessmentService
assessment = await assessment_service.complete(db, assessment_id, user_id)
results = await assessment_service.get_assessment_results(db, assessment_id)
assessments = await assessment_service.get_user_assessments(db, user_id, status="completed")
```

### Pattern 3: Using Built-in Caching

Caching is automatic - you don't need to do anything special:

```python
# First call - fetches from database
user = await user_service.get_by_id(db, user_id)

# Second call within TTL - returns from cache automatically!
user = await user_service.get_by_id(db, user_id)

# Cache is automatically invalidated on updates
await user_service.update(db, user_id, update_data)
# Next get_by_id will fetch fresh data from database
```

**Cache Strategies** (predefined TTL):
- `USER_PROFILE` - 5 minutes
- `TEAM_DATA` - 10 minutes
- `ASSESSMENT_DATA` - 30 minutes
- `ASSESSMENT_RESULTS` - 1 hour

### Pattern 4: Error Handling

Errors are handled automatically by BaseService:

```python
from app.core.error_handling import ValidationException

try:
    user = await user_service.get_by_id(db, user_id)
except ValidationException as e:
    # Invalid data or business rule violation
    return {"error": str(e)}
except Exception as e:
    # Database error, network issue, etc.
    # Already logged by BaseService
    return {"error": "An error occurred"}
```

### Pattern 5: Transaction Management

Write operations use `@transaction_manager` decorator:

```python
# In endpoints - don't need explicit transactions!
@router.post("/teams")
async def create_team(team_data: TeamCreate, db: AsyncSession = Depends(get_db)):
    # This automatically:
    # 1. Begins transaction
    # 2. Executes create_team
    # 3. Commits on success
    # 4. Rolls back on failure
    team = await team_service.create_team(db, team_data, current_user.id)
    return team
```

---

## 🔍 Comparing Old vs New

### OLD: Functional Service
```python
from app.services import user_service

# Static methods, manual error handling
user = await user_service.get_user(db, user_id)
# Manual try/except
# Manual caching decorator
# Manual transaction handling
```

### NEW: BaseService-Based
```python
from app.services.user_service_refactored import user_service

# Instance methods, automatic everything
user = await user_service.get_by_id(db, user_id)
# Automatic error handling
# Automatic caching
# Automatic transactions
# Better logging
```

---

## ⚠️ Breaking Changes

**None!** The refactored services maintain the same method signatures where possible.

**Method name changes**:
- `get_user()` → `get_by_id()` (use BaseService method)
- `update_user()` → `update()` (use BaseService method)
- Static methods are now instance methods

**Benefits of instance methods**:
- Can use `self.logger` for structured logging
- Can access `self.cache_strategy` for configuration
- More consistent with OOP patterns

---

## 🎯 Best Practices

### DO ✅

```python
# 1. Use the singleton instance
from app.services.user_service_refactored import user_service

# 2. Let BaseService handle errors
user = await user_service.get_by_id(db, user_id)  # No try/except needed!

# 3. Trust the cache
user = await user_service.get_by_id(db, user_id)  # Automatic caching

# 4. Use filters for listing
users = await user_service.list(
    db,
    filters={"organization_id": org_id, "status": "active"}
)

# 5. Leverage BaseService CRUD
await user_service.create(db, data)
await user_service.update(db, id, data)
await user_service.delete(db, id)
```

### DON'T ❌

```python
# 1. Don't instantiate services yourself
user_service = UserService()  # ❌ Wrong
# Use the singleton instead  # ✅

# 2. Don't manually cache results
@cached(...)  # ❌ BaseService handles this
# Remove caching decorators   # ✅

# 3. Don't wrap in transactions manually
async with db.begin():  # ❌ Service handles this
    # Just call the method  # ✅

# 4. Don't add try/except for every call
try:  # ❌ BaseService handles errors
    user = await user_service.get_by_id(db, id)
except:  # ❌
# Just call the method  # ✅
```

---

## 🛠️ Creating New Services

### Template for New Service

```python
from app.core.cache_strategy import CacheStrategy
from app.core.database_transactions import transaction_manager
from app.core.error_handling import ValidationException
from app.core.structured_logging import EventType, get_logger
from app.db.models.your_model import YourModel
from app.schemas.your_schema import YourCreate, YourUpdate
from app.services.base_service import BaseService

logger = get_logger(__name__)


class YourService(BaseService[YourModel, YourCreate, YourUpdate]):
    """Your service extending BaseService."""

    # Required: Model class
    @property
    def model(self) -> type[YourModel]:
        return YourModel

    # Required: Cache strategy
    @property
    def cache_strategy(self) -> CacheStrategy:
        return CacheStrategy.USER_PROFILE  # Choose appropriate strategy

    # Required: Cache key generation
    def get_cache_key(self, operation: str, **kwargs) -> str:
        if operation == "get_by_id":
            return f"your_model:id:{kwargs.get('id')}"
        return f"your_model:{operation}"

    # Required: Validation for creation
    def validate_create_data(self, data: YourCreate) -> None:
        if not data.name:
            raise ValidationException("Name is required", field="name")

    # Required: Validation for update
    def validate_update_data(self, data: YourUpdate, existing: YourModel) -> None:
        if data.name and len(data.name) < 3:
            raise ValidationException("Name too short", field="name")

    # Optional: Custom business logic
    @transaction_manager.transaction
    async def your_custom_method(self, db: AsyncSession, ...) -> YourModel:
        # Your business logic here
        # Automatic transaction management
        # Automatic error handling
        # Automatic logging
        pass


# Singleton instance
your_service = YourService()
```

---

## 🧪 Testing Refactored Services

```python
import pytest
from app.services.user_service_refactored import user_service

def test_service_properties():
    """Test service has required properties."""
    assert user_service.model is not None
    assert user_service.cache_strategy is not None

@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test user creation."""
    from app.schemas.user import UserCreate
    from uuid import uuid4

    data = UserCreate(
        email="test@example.com",
        password="SecurePass123!",
        full_name="Test User",
    )

    user = await user_service.create(db_session, data)
    assert user.email == "test@example.com"
    assert user.is_verified is False
```

---

## 📊 Monitoring & Debugging

### Check Cache Performance

```python
from app.core.cache_strategy import intelligent_cache

stats = intelligent_cache.get_cache_stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
print(f"Total requests: {stats['total_requests']}")
print(f"Active keys: {stats['active_keys']}")
```

### View Service Logs

Logs are automatically structured with EventType:

```python
# In your service methods
self.logger.info(
    EventType.DATABASE_OPERATION,
    "Message here",
    operation="method_name",
    entity_id=str(id),
    # Additional context...
)
```

Logs include:
- Timestamp
- Event type
- Operation name
- Entity ID
- User ID (if applicable)
- Additional context

---

## 🐛 Troubleshooting

### Issue: "Service method not found"

**Solution**: Make sure you're importing the refactored service:
```python
# ❌ Old
from app.services import user_service

# ✅ New
from app.services.user_service_refactored import user_service
```

### Issue: "Cache not working"

**Solution**: Check that `cache_strategy` property returns enum value:
```python
@property
def cache_strategy(self) -> CacheStrategy:
    return CacheStrategy.USER_PROFILE  # ✅ Enum value
    # Not CacheStrategy(...)  # ❌ Don't instantiate
```

### Issue: "Transaction not committing"

**Solution**: Ensure method uses `@transaction_manager.transaction`:
```python
@transaction_manager.transaction  # ✅ Required for write operations
async def create(self, db: AsyncSession, data: YourCreate) -> YourModel:
    # ...
```

---

## 📚 Additional Resources

- **MIGRATION_GUIDE.md** - How to migrate existing services
- **SERVICE_MIGRATION_PATTERNS.md** - Real-world examples
- **ARCHITECTURAL_MIGRATION_PHASES_1_2_COMPLETE.md** - Full technical details
- **MIGRATION_PROGRESS.md** - Track migration status

---

## 💡 Tips & Tricks

1. **Use BaseService CRUD first** - Only implement custom methods if you need special business logic

2. **Leverage filtering** - The `list()` method supports powerful filtering:
   ```python
   users = await user_service.list(
       db,
       filters={"status": "active", "organization_id": org_id}
   )
   ```

3. **Cache keys are automatic** - Don't manually manage cache keys, BaseService handles it

4. **Trust the logging** - BaseService automatically logs all operations with structured context

5. **Keep old services** - Until migration is complete, keep the old service as backup

---

**Questions?** Check the documentation or ask the architecture team!

**Last Updated**: 2025-12-02
**Version**: 1.0
