# Service Boundary Migration Guide

**Date**: February 10, 2026
**Status**: Complete Architectural Refactoring

This guide explains how to migrate from the old service boundary violations to the correct architecture.

---

## 📋 Summary of Changes

### Problems Fixed

| Problem | Old Way | New Way | File |
|---------|---------|---------|------|
| Direct DB queries in services | Services queried database directly | Services use repositories | `analytics_service_refactored_v2.py` |
| HTML in services | `EmailService` rendered templates | `EmailTemplateRenderer` handles presentation | `presentation/email_template_renderer.py` |
| Dict returns from services | Services returned `dict` for HTTP | Services return domain objects | `domain/value_objects/analytics.py` |
| No dependency injection | Services created dependencies | Services receive dependencies via constructor | `user_service_refactored_v2.py` |
| Fat controllers | API endpoints contained business logic | Controllers are thin, delegate to services | `users_refactored.py` |

---

## 🗂️ New File Structure

```
app/
├── domain/
│   └── value_objects/
│       ├── analytics.py          # NEW: Analytics domain objects
│       └── email.py              # EXISTING: Email value objects
├── repositories/
│   ├── base_repository.py        # EXISTING: Base repository interface
│   ├── user_repository.py        # EXISTING: User repository
│   ├── team_repository.py        # NEW: Team repository
│   ├── response_repository.py    # NEW: Response repository
│   └── assessment_repository.py  # NEW: Assessment repository
├── presentation/
│   └── email_template_renderer.py  # NEW: Template rendering (presentation layer)
├── services/
│   ├── email_service_refactored_v2.py          # NEW: Email business logic only
│   ├── user_service_refactored_v2.py           # NEW: User business logic only
│   └── analytics_service_refactored_v2.py      # NEW: Analytics business logic only
└── api/v1/endpoints/
    └── users_refactored.py    # NEW: Thin controller example
```

---

## 🔄 Migration Steps

### Step 1: Create Domain Objects

**Before**: Services returned dictionaries shaped for HTTP responses

```python
# OLD: Service returns HTTP response structure
async def get_user_analytics(db, user_id) -> dict:
    responses = await db.execute(select(Response))  # Direct DB query!
    return {
        "success": True,
        "data": {"user_id": str(user_id), ...}  # HTTP shape
    }
```

**After**: Services return domain objects

```python
# NEW: Service returns domain object
async def get_user_analytics(db, user_id) -> UserAnalytics:
    responses = await self._response_repo.get_by_user(db, user_id)  # Via repository
    return UserAnalytics(  # Domain object
        user_id=user_id,
        total_responses=len(responses),
        ...
    )
```

**Files Created**:
- `domain/value_objects/analytics.py`

---

### Step 2: Extract Repository Layer

**Before**: Services queried database directly

```python
# OLD: Service contains SQL
query = select(Team).options(selectinload(Team.members)).where(Team.id == team_id)
result = await db.execute(query)
team = result.scalar_one_or_none()
```

**After**: Services use repositories

```python
# NEW: Service delegates to repository
team = await self._team_repo.get_with_members(team_id)
```

**Files Created**:
- `repositories/team_repository.py`
- `repositories/response_repository.py`
- `repositories/assessment_repository.py`

**Key Principle**: Repositories encapsulate ALL data access logic. Services should NEVER import SQLAlchemy select, or use `db.execute()`.

---

### Step 3: Separate Presentation from Business Logic

**Before**: `EmailService` contained HTML rendering

```python
# OLD: Service renders HTML (presentation concern in business logic)
class EmailService:
    def _render_template(self, template_name, context):
        template = self.env.get_template(template_name)
        return bleach.clean(template.render(**context))  # HTML sanitization!
```

**After**: Separate presentation layer

```python
# NEW: Presentation in separate component
# app/presentation/email_template_renderer.py
class EmailTemplateRenderer:
    def render_template(self, template_name, context):
        # Presentation logic only

# NEW: Service focuses on business logic
class EmailService:
    def __init__(self, template_renderer, email_provider):
        self._renderer = template_renderer  # Inject presentation dependency
        self._provider = email_provider      # Inject infrastructure dependency

    async def send_welcome_email(self, user_email, user_name):
        # Business rules only
        html = self._renderer.render_template(...)  # Delegate presentation
        await self._provider.send(...)               # Delegate infrastructure
```

**Files Created**:
- `presentation/email_template_renderer.py`
- `services/email_service_refactored_v2.py`

**Key Principle**: Services should be framework-agnostic. They shouldn't know about Jinja2, HTML, or SMTP.

---

### Step 4: Implement Dependency Injection

**Before**: Services created their own dependencies

```python
# OLD: Tight coupling to implementation
class UserService:
    def __init__(self):
        self.db = AsyncSession()  # Creates own DB session!
```

**After**: Services receive dependencies via constructor

```python
# NEW: Dependencies injected
class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo  # Received as parameter

# Factory function for easy instantiation
def create_user_service(db: AsyncSession) -> UserService:
    return UserService(user_repo=UserRepository(db))
```

**Files Created**:
- `services/user_service_refactored_v2.py`
- `services/analytics_service_refactored_v2.py`

**Benefits**:
- Easy to test (can mock repositories)
- Flexible (can swap implementations)
- Clear dependencies (visible in constructor)

---

### Step 5: Thin Your Controllers

**Before**: API endpoints contained business logic

```python
# OLD: Fat controller
@router.post("/change-password")
async def change_password(password_change, db, current_user):
    # Business validation in endpoint!
    current_validation = security_validator.validate_text_input(
        password_change.current_password, "current_password", max_length=128
    )
    new_validation = security_validator.validate_text_input(
        password_change.new_password, "new_password", max_length=128
    )

    # Business logic in endpoint!
    if not current_validation.is_valid:
        raise HTTPException(status_code=400, detail="Invalid current password")
```

**After**: Thin controller delegates to service

```python
# NEW: Thin controller
@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Just delegate to service
    user_service = create_user_service(db)

    try:
        # All business logic in service
        await user_service.change_password(
            user_id=current_user.id,
            current_password=password_change.current_password,
            new_password=password_change.new_password,
        )
        return ChangePasswordResponse(success=True, message="Password changed")
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Files Created**:
- `api/v1/endpoints/users_refactored.py`

**Key Principle**: API layer = HTTP concerns only. Business logic = service layer.

---

## 📊 Architecture Comparison

### Before (Incorrect)

```
┌─────────────────────────────────────────┐
│  API Endpoint (Fat Controller)          │
│  • Business validation                  │
│  • Password strength checks             │
│  • Response formatting                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Service (Mixed Concerns)               │
│  • SQL queries                          │
│  • HTML rendering                       │
│  • Email sending                        │
│  • Business logic                       │
│  • Caching                              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Database (Direct Access)               │
└─────────────────────────────────────────┘
```

### After (Correct)

```
┌─────────────────────────────────────────┐
│  API Layer (Thin)                       │
│  • HTTP routing                         │
│  • Serialization                        │
│  • Status codes                         │
└──────────────┬──────────────────────────┘
               │ Only calls service methods
┌──────────────▼──────────────────────────┐
│  Service Layer (Business Logic Only)    │
│  • Use cases                            │
│  • Business rules                       │
│  • Domain logic                         │
└──────────────┬──────────────────────────┘
               │ Only uses repositories
┌──────────────▼──────────────────────────┐
│  Repository Layer (Data Access)         │
│  • Queries                              │
│  • CRUD operations                      │
│  • Mappings                             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Database / External Services           │
└─────────────────────────────────────────┘

Separate Infrastructure Layers:
• Presentation: EmailTemplateRenderer
• Infrastructure: EmailProvider
• Domain: Value objects (Email, UserAnalytics)
```

---

## 🧪 Testing Benefits

### Before (Hard to Test)

```python
# OLD: Hard to test - requires database
async def test_get_user_analytics():
    # Need actual database!
    async with async_session_maker() as db:
        result = await analytics_service.get_user_analytics(db, user_id)
        assert result["success"] == True  # Tightly coupled to HTTP shape
```

### After (Easy to Test)

```python
# NEW: Easy to test - can mock repositories
async def test_get_user_analytics():
    # Mock repositories - no database needed!
    mock_user_repo = Mock(spec=UserRepository)
    mock_response_repo = Mock(spec=ResponseRepository)

    service = AnalyticsService(
        user_repo=mock_user_repo,
        response_repo=mock_response_repo,
        ...
    )

    # Set up mock data
    mock_response_repo.get_by_user.return_value = [...]

    # Test business logic only
    result = await service.get_user_analytics(user_id)

    # Assert domain object (not HTTP response)
    assert isinstance(result, UserAnalytics)
    assert result.total_responses == 5
```

---

## ✅ Checklist for Each Service

Use this checklist when refactoring services:

- [ ] **No direct database access**: Service doesn't import `select`, `db.execute()`, or use SQLAlchemy directly
- [ ] **No HTTP concerns**: Service doesn't return dicts shaped for HTTP responses
- [ ] **No presentation logic**: Service doesn't render HTML, templates, or format output
- [ ] **No infrastructure details**: Service doesn't know about caching, email providers, etc.
- [ ] **Dependency injection**: All dependencies received via constructor
- [ ] **Domain objects**: Returns domain objects, not dicts or primitive types
- [ ] **Business logic only**: Contains use cases, workflows, business rules

---

## 🚀 Next Steps

### Immediate Actions

1. **Review new files**: Examine the refactored services to understand the pattern
2. **Pick one service**: Start with a simple service (e.g., UserService)
3. **Write tests**: Create unit tests for the refactored service
4. **Update endpoints**: Convert endpoints to use new service
5. **Run integration tests**: Ensure everything still works

### Gradual Migration Strategy

1. **Keep old services**: Don't delete `user_service.py` yet
2. **Create new services**: Add `*_refactored_v2.py` files (already done)
3. **Migrate endpoints one at a time**: Update endpoints to use new services
4. **Test thoroughly**: Ensure behavior matches
5. **Delete old code**: Once migration is complete and tested

---

## 📖 Key Design Patterns Used

1. **Repository Pattern**: Abstraction over data access
2. **Dependency Injection**: Pass dependencies via constructor
3. **Factory Pattern**: Factory functions create service instances
4. **Domain Objects**: Value objects encapsulate business concepts
5. **Service Layer Pattern**: Business logic isolated from infrastructure
6. **Presentation Layer Separation**: UI/rendering separated from business logic

---

## 🎯 Benefits Achieved

✅ **Testability**: Services can be unit tested without database
✅ **Maintainability**: Each layer has single responsibility
✅ **Reusability**: Services usable in CLI, GraphQL, message queues
✅ **Flexibility**: Can swap implementations (caching, email providers, etc.)
✅ **Clarity**: Clear separation of concerns
✅ **Scalability**: Can optimize layers independently

---

## 📝 Examples to Study

### Good Examples (Refactored)
- `services/user_service_refactored_v2.py` - Clean service with DI
- `services/analytics_service_refactored_v2.py` - Uses repositories, returns domain objects
- `presentation/email_template_renderer.py` - Presentation separated from logic
- `api/v1/endpoints/users_refactored.py` - Thin controller

### Bad Examples (What to Avoid)
- `services/user_service.py` - Direct DB access, mixed concerns
- `services/analytics_service.py` - SQL in service, returns HTTP-shaped dicts
- `services/email_service.py` - HTML rendering in business logic

---

## 🔧 Quick Reference

### Creating a New Service

```python
# 1. Create repository (if needed)
class MyRepository(BaseRepository[Model, CreateSchema, UpdateSchema]):
    async def find_by_something(self, something) -> list[Model]:
        # Data access logic here
        pass

# 2. Create domain objects (if needed)
@dataclass(frozen=True)
class MyResult:
    result_id: UUID
    value: float
    def to_dict(self) -> dict: ...

# 3. Create service with DI
class MyService:
    def __init__(self, my_repo: MyRepository):
        self._my_repo = my_repo

    async def do_something(self, input: str) -> MyResult:
        # Business logic here
        # Use repository for data access
        # Return domain objects
        pass

# 4. Create factory function
def create_my_service(db: AsyncSession) -> MyService:
    return MyService(my_repo=MyRepository(db))

# 5. Use in endpoint
@router.post("/do-something")
async def do_something_endpoint(
    input: str,
    db: AsyncSession = Depends(get_db),
):
    service = create_my_service(db)
    result = await service.do_something(input)
    return result.to_dict()
```

---

## 🎓 Learning Resources

### Concepts to Study
- **Repository Pattern**: Martin Fowler's patterns
- **Dependency Injection**: Inversion of Control principle
- **Domain-Driven Design**: Bounded contexts, ubiquitous language
- **Clean Architecture**: Robert C. Martin's layering principles
- **Service Layer Pattern**: Pattern for application logic

### Books
- "Clean Architecture" by Robert C. Martin
- "Domain-Driven Design" by Eric Evans
- "Patterns of Enterprise Application Architecture" by Martin Fowler

---

**Questions? Refer to the inline code comments in the refactored files for detailed explanations of each decision.**
