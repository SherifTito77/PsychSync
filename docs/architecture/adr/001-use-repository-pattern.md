# ADR 001: Use Repository Pattern for Data Access

## Status
**Accepted** - 2025-01-19

## Context

### Current State
PsychSync's service layer currently mixes business logic with direct database access:

```python
# ❌ Current approach (app/services/user_service.py)
async def get_user(db: AsyncSession, user_id: UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user
```

### Problems
1. **Tight coupling**: Services directly depend on SQLAlchemy
2. **Hard to test**: Cannot test business logic without a database
3. **Violates SRP**: Services handle both business logic AND data access
4. **Code duplication**: Similar queries scattered across services
5. **No abstraction**: Switching databases requires changing every service

### Impact
- Unit tests require database mocking
- Business logic is buried in SQL queries
- Reusing data access logic is difficult
- Onboarding new developers is confusing

## Decision

**Implement the Repository Pattern** to abstract data access behind a clean interface.

### Architecture
```
┌─────────────────────────────────────────┐
│  API Layer (FastAPI endpoints)          │
├─────────────────────────────────────────┤
│  Domain Services (business logic)       │
│  - UserService.create_user()            │
│  - AssessmentService.calculate_scores() │
├─────────────────────────────────────────┤
│  Repository Layer (data access)         │
│  - UserRepository.get(id)               │
│  - AssessmentRepository.list(filters)   │
├─────────────────────────────────────────┤
│  Infrastructure (SQLAlchemy, databases) │
└─────────────────────────────────────────┘
```

### Implementation

**BaseRepository** (`app/infrastructure/repositories/base.py`):
```python
class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    async def get(self, id: UUID) -> Optional[ModelType]
    async def list(self, skip: int, limit: int, filters: dict) -> List[ModelType]
    async def create(self, schema: CreateSchemaType) -> ModelType
    async def update(self, id: UUID, schema: UpdateSchemaType) -> ModelType
    async def delete(self, id: UUID) -> bool
```

**Example Repository** (`app/infrastructure/repositories/user_repository.py`):
```python
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

**Usage in Domain Service** (`app/domain/services/user_service.py`):
```python
class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def create_user(self, user_data: UserCreate) -> User:
        # Business logic: Check if email exists
        existing = await self._repository.get_by_email(user_data.email)
        if existing:
            raise ValidationError("Email already exists")

        # Create user
        user = await self._repository.create(user_data)
        return user
```

## Consequences

### Positive
✅ **Separation of Concerns**: Business logic isolated from data access
✅ **Testability**: Can mock repositories for unit tests
✅ **Reusability**: Common CRUD operations in BaseRepository
✅ **Flexibility**: Easy to swap implementations (SQL → NoSQL → Cache)
✅ **Consistency**: All repositories follow same interface
✅ **Single Responsibility**: Each layer has one job

### Negative
❌ **Initial complexity**: More files and abstractions to understand
❌ **Boilerplate**: Need to create repository for each entity
❌ **Learning curve**: Team must learn new pattern

### Mitigation
- Create comprehensive examples and documentation
- Use generics to reduce boilerplate
- Provide repository templates
- Pair programming during migration

## Implementation Notes

### Phase 1: Create Base Classes
- [x] Create BaseRepository with generic CRUD
- [x] Add common methods (get, list, create, update, delete)
- [x] Implement pagination and filtering helpers

### Phase 2: Implement Entity Repositories
- [ ] UserRepository (email lookup, existence checks)
- [ ] AssessmentRepository (query by type, template)
- [ ] ResponseRepository (user responses, scores)
- [ ] TeamRepository (member management, roles)

### Phase 3: Refactor Services
- [ ] Update UserService to use UserRepository
- [ ] Update AssessmentService to use repositories
- [ ] Remove direct SQL queries from all services
- [ ] Add unit tests with mocked repositories

### Phase 4: Migration
- [ ] Run existing tests to ensure no regressions
- [ ] Update endpoint dependency injection
- [ ] Remove old database access code

## Alternatives Considered

### Alternative 1: Active Record Pattern
**Rejected** - Keeps data access in domain entities, violating SRP

### Alternative 2: Data Mapper (Manual)
**Rejected** - Too much boilerplate, reinventing the wheel

### Alternative 3: Query Builder (SQLAlchemy directly)
**Rejected** - Doesn't solve coupling or testability issues

## References
- [Repository Pattern (Martin Fowler)](https://martinfowler.com/eaaCatalog/repository.html)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)

## Related Decisions
- [ADR 002: Separate AI Engine into Standalone Package](002-extract-ai-engine.md)
- [ADR 003: Standardize All Entity IDs to UUID](003-standardize-uuids.md)
