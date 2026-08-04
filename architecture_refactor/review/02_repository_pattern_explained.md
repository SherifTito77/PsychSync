# Repository Pattern: Complete Explanation

## 🎯 What Is It?

A **Repository** is a **data access abstraction layer**. It sits between your business logic and the database.

### Analogy: Restaurant Kitchen

```
WITHOUT Repository:
Customer → Waiter knows how to cook → Food
(Too much responsibility on waiter)

WITH Repository:
Customer → Waiter (takes order) → Kitchen Staff (cooks) → Food
(Each has one job)
```

In code:
```
WITHOUT Repository:
Service → SELECT * FROM users WHERE id = ? → User
(Service knows SQL!)

WITH Repository:
Service → repository.get(id) → User
(Service doesn't know SQL)
```

---

## 📦 The BaseRepository: What It Provides

### Core CRUD Operations (Ready to Use)

```python
# app/infrastructure/repositories/base.py

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common operations"""

    # READ
    async def get(self, id: UUID) -> Optional[ModelType]:
        """Get one entity by ID"""

    async def get_or_404(self, id: UUID) -> ModelType:
        """Get by ID or raise error"""

    async def list(self, skip: int, limit: int, filters: dict) -> tuple[List[ModelType], int]:
        """Get list with pagination and filtering"""

    async def exists(self, id: UUID) -> bool:
        """Check if entity exists"""

    # WRITE
    async def create(self, schema: CreateSchemaType) -> ModelType:
        """Create new entity"""

    async def update(self, id: UUID, schema: UpdateSchemaType) -> ModelType:
        """Update existing entity"""

    async def delete(self, id: UUID) -> bool:
        """Delete entity"""

    # BULK
    async def bulk_create(self, schemas: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple at once"""

    async def count(self, filters: dict) -> int:
        """Count matching entities"""
```

**Key Features:**
- ✅ **Generic**: Works for any model (User, Team, Assessment, etc.)
- ✅ **Type-safe**: Uses Python generics for IDE support
- ✅ **Pagination built-in**: No more writing OFFSET/LIMIT manually
- ✅ **Filtering support**: Pass dict of filters
- ✅ **Consistent interface**: All repositories work the same way

---

## 🔧 How to Use It: Step by Step

### Step 1: Create Your Repository

```python
# app/infrastructure/repositories/user_repository.py

from app.infrastructure.repositories.base import BaseRepository
from app.db.models.user import User as UserModel  # SQLAlchemy model
from app.schemas.user import UserCreate, UserUpdate  # Pydantic schemas

class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    """User repository with specific queries"""

    def __init__(self, db: AsyncSession):
        # Pass model and database session to base
        super().__init__(UserModel, db)

    # ✅ You get all CRUD operations for FREE from BaseRepository
    # No need to write get, list, create, update, delete!

    # ✅ Add custom queries specific to User
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Find user by email address"""
        result = await self._db.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100):
        """Get only active users"""
        users, total = await self.list(
            skip=skip,
            limit=limit,
            filters={"is_active": True}  # ✅ Uses base list() method!
        )
        return users, total
```

### Step 2: Use in Domain Service

```python
# app/domain/services/user_service.py

class UserService:
    """Business logic for users"""

    def __init__(self, repository: UserRepository):
        # ✅ Dependency injection - we'll discuss this soon
        self._repo = repository

    async def create_user(self, data: UserCreate) -> User:
        """Create new user with business rules"""

        # ✅ Use repository for data access
        existing = await self._repo.get_by_email(data.email)

        if existing:
            raise ValidationError("Email already exists")

        # ✅ Create user (repository handles SQL)
        user_model = await self._repo.create(data)

        # Convert to domain entity (business logic)
        user = User.from_db(
            id=user_model.id,
            email_str=user_model.email,
            password_hash=user_model.password_hash
        )

        return user
```

### Step 3: Inject in API Endpoint

```python
# app/api/v1/endpoints/users.py

from fastapi import Depends

# ✅ Dependency injection provider
def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)  # ✅ Injected
):
    # ✅ Pure HTTP layer - no SQL here
    try:
        user = await service.create_user(user_data)
        return {"id": user.id, "email": str(user.email)}
    except ValidationError as e:
        raise HTTPException(400, str(e))
```

---

## 💪 The Power: Testing Without Database

### BEFORE (Hard to Test):

```python
# Need to set up database, create tables, etc.
async def test_create_user():
    # ❌ Setup database
    engine = create_engine("...")
    Base.metadata.create_all(engine)

    # ❌ Create session
    session = Session(engine)

    # ❌ Insert test data
    user = User(email="test@example.com")
    session.add(user)
    session.commit()

    # ❌ Finally test
    result = await create_user(session, ...)
    assert result.email == "test@example.com"

    # ❌ Cleanup
    session.delete(user)
    session.commit()
```

### AFTER (Easy to Test):

```python
# ✅ No database needed - just mock the repository!
async def test_create_user():
    # ✅ Create mock repository
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = None  # Email doesn't exist
    mock_repo.create.return_value = UserModel(id=uuid4(), ...)

    # ✅ Inject mock into service
    service = UserService(mock_repo)

    # ✅ Test business logic
    result = await service.create_user(UserCreate(email="test@example.com"))

    # ✅ Assertions
    assert result.email == "test@example.com"
    mock_repo.create.assert_called_once()  # ✅ Verify interaction
```

**Benefits:**
- ✅ **Fast**: No database setup/teardown
- ✅ **Isolated**: Tests only the business logic
- ✅ **Reliable**: No database state issues
- ✅ **Clear**: Mocks show what the service needs

---

## 🎨 Advanced: Custom Queries

### Scenario: Complex User Search

```python
class UserRepository(BaseRepository[...]):

    async def search_users(
        self,
        email_contains: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        created_after: datetime | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[UserModel], int]:
        """
        Complex search with multiple filters.

        Note: Even custom queries are isolated here,
        not scattered across the codebase.
        """
        query = select(UserModel)

        # Build filters dynamically
        if email_contains:
            query = query.where(UserModel.email.ilike(f"%{email_contains}%"))

        if role:
            query = query.where(UserModel.role == role)

        if is_active is not None:
            query = query.where(UserModel.is_active == is_active)

        if created_after:
            query = query.where(UserModel.created_at >= created_after)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self._db.execute(query)
        users = result.scalars().all()

        return list(users), total
```

**Usage:**

```python
# In service
users, total = await self._repo.search_users(
    email_contains="@company.com",
    role=UserRole.ADMIN,
    is_active=True,
    created_after=datetime(2025, 1, 1),
    skip=0,
    limit=50
)
```

---

## 🔄 Comparison: Old vs New

### OLD WAY (Direct DB Access):

```python
# In service (bad)
async def get_user(db: AsyncSession, user_id: UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Problems:
# ❌ Can't test without database
# ❌ Scattered SQL queries everywhere
# ❌ Hard to reuse (tied to AsyncSession)
# ❌ Can't swap database (PostgreSQL → SQLite needs changes everywhere)
```

### NEW WAY (Repository Pattern):

```python
# In service (good)
async def get_user(repo: UserRepository, user_id: UUID):
    return await repo.get(user_id)

# Benefits:
# ✅ Testable (mock repo)
# ✅ Reusable (repo can be swapped)
# ✅ Clear (one place to look for queries)
# ✅ Flexible (change DB, just update repo)
```

---

## 📊 Summary: What We Gained

| Aspect | Before Repository | After Repository |
|--------|-------------------|------------------|
| **Testing** | Need database | Mock repository |
| **SQL Queries** | Scattered everywhere | In one place |
| **Reusability** | Tied to database | Swappable |
| **Consistency** | Each query different | Standardized interface |
| **Maintainability** | Changes everywhere | Change in repo only |

---

## 🎓 Key Takeaways

1. **Repository = Data Access Layer**: All SQL goes here
2. **BaseRepository = Free CRUD**: Don't repeat yourself
3. **Services use Repositories**: Business logic delegates data access
4. **Testing becomes easy**: Mock the repository
5. **Custom queries go in repository**: Not in services or endpoints

---

**Ready for the next stop? We'll explore Domain Entities!**
