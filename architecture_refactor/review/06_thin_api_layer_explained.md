# Thin API Layer: Complete Guide

## 🎯 What Is a "Thin" API Layer?

A **thin API layer** means endpoints handle **only HTTP concerns**:
- Request validation (Pydantic schemas)
- Authentication (check tokens)
- Authorization (check permissions)
- Response formatting (JSON, status codes)
- Error translation (domain errors → HTTP errors)

**What it does NOT do:**
- ❌ Business logic
- ❌ Data access
- ❌ Complex validation
- ❌ Calculations

---

## 📊 Before vs After Comparison

### BEFORE: Fat Endpoints (Current)

```python
# app/api/v1/endpoints/users.py - CURRENT CODE
@router.post("/users")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """❌ Fat endpoint - too many responsibilities"""

    # ❌ Responsibility 1: Data access
    existing = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email exists")

    # ❌ Responsibility 2: Business logic
    if len(user_data.password) < 12:
        raise HTTPException(400, "Password too short")

    # ❌ Responsibility 3: Password hashing
    hashed = hash_password(user_data.password)

    # ❌ Responsibility 4: Data creation
    new_user = User(
        email=user_data.email,
        password_hash=hashed,
        full_name=user_data.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # ❌ Responsibility 5: Response formatting
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "full_name": new_user.full_name
    }
```

**Problems:**
- ❌ Hard to test (need database)
- ❌ Can't reuse logic (tied to HTTP)
- ❌ Mixed concerns (HTTP + business + data)
- ❌ Violates SRP (Single Responsibility Principle)

### AFTER: Thin Endpoints (New)

```python
# app/api/v1/endpoints/users.py - REFACTORED CODE
@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)  # ✅ Dependency injection
):
    """✅ Thin endpoint - HTTP concerns only"""

    try:
        # ✅ Delegate to domain service
        user = await user_service.create_user(user_data)

        # ✅ Format response (HTTP concern)
        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except ValidationError as e:
        # ✅ Domain error → HTTP error
        raise HTTPException(status_code=400, detail=str(e))

    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

**Benefits:**
- ✅ Easy to test (mock service)
- ✅ Reusable logic (service works anywhere)
- ✅ Single responsibility (HTTP only)
- ✅ Clear separation of concerns

---

## 🔌 Dependency Injection in Action

### How It Works

```python
# Step 1: Define dependency providers
def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Provide UserRepository instance"""
    return UserRepository(db)

def get_user_service(
    repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Provide UserService instance"""
    return UserService(repo)

# Step 2: Use in endpoint
@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service)  # ✅ Injected
):
    """Endpoint gets service automatically"""
    user = await service.get_user_by_id(user_id)
    return user.to_dict()
```

### The Injection Chain

```
Endpoint (create_user)
    ↓ Depends(get_user_service)
UserService
    ↓ Depends(get_user_repository)
UserRepository
    ↓ Depends(get_db)
AsyncSession (database)
```

**Key Points:**
1. FastAPI handles injection automatically
2. Each dependency is testable (can mock)
3. Clear dependency graph
4. Easy to swap implementations

---

## 📝 Complete Example: User CRUD

### 1. Create User

```python
@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Create new user.

    ✅ HTTP concerns only:
    - Validate request (Pydantic)
    - Call service
    - Return response
    - Handle errors
    """
    try:
        user = await service.create_user(user_data)

        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

### 2. Get User

```python
@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    try:
        user = await service.get_user_by_id(user_id)

        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

### 3. Update User

```python
@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)  # Auth check
):
    """Update user"""
    try:
        user = await service.update_user(user_id, user_data)

        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except NotFoundError as e:
        raise HTTPException(404, str(e))

    except ValidationError as e:
        raise HTTPException(400, str(e))

    except AuthorizationError as e:
        raise HTTPException(403, str(e))
```

### 4. Delete User

```python
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """Delete user (admin only)"""
    try:
        await service.delete_user(user_id, current_user)

    except NotFoundError as e:
        raise HTTPException(404, str(e))

    except AuthorizationError as e:
        raise HTTPException(403, str(e))

    return Response(status_code=204)  # No content
```

---

## 🎨 Real-World Example: Assessment Processing

### Current (Fat Endpoint):

```python
# ❌ Current: Everything in endpoint
@router.post("/assessments/{id}/process")
async def process_assessment(
    assessment_id: UUID,
    responses: dict,
    db: AsyncSession = Depends(get_db)
):
    # Get assessment
    assessment = await db.get(Assessment, assessment_id)

    # Process based on framework
    if assessment.framework == "mbti":
        result = mbti_processor.process(responses)  # Direct call
    elif assessment.framework == "big_five":
        result = big_five_processor.process(responses)
    # ... more frameworks

    # Save results
    user_response = Response(
        assessment_id=assessment_id,
        user_id=current_user.id,
        results=result
    )
    db.add(user_response)
    await db.commit()

    return result
```

### Refactored (Thin Endpoint):

```python
# ✅ Refactored: Delegate to service
@router.post("/assessments/{id}/process")
async def process_assessment(
    assessment_id: UUID,
    responses: AssessmentResponses,
    service: AssessmentProcessingService = Depends(get_assessment_processing_service),
    current_user: User = Depends(get_current_user)
):
    """
    Process assessment responses.

    ✅ HTTP concerns only:
    - Validate request
    - Check auth
    - Call service
    - Return response
    """
    try:
        # ✅ Delegate to service (handles AI processing + saving)
        result = await service.process_assessment(
            assessment_id=assessment_id,
            user_id=current_user.id,
            responses=responses.dict()
        )

        # ✅ Return HTTP response
        return {
            "assessment_id": str(assessment_id),
            "framework": result.framework,
            "results": result.data,
            "confidence": result.confidence,
            "warnings": result.warnings
        }

    except NotFoundError:
        raise HTTPException(404, "Assessment not found")

    except ValidationError as e:
        raise HTTPException(400, str(e))

    except ProcessingError as e:
        raise HTTPException(500, f"Processing failed: {e}")
```

**Benefits:**
- ✅ Endpoint doesn't know about AI processors
- ✅ Service handles all frameworks consistently
- ✅ Easy to test (mock service)
- ✅ Clear error handling

---

## 🧪 Testing Thin Endpoints

### Unit Test (Mock Service):

```python
# tests/unit/api/test_users.py
def test_create_user_endpoint():
    """Test endpoint with mocked service"""
    # Arrange
    mock_service = AsyncMock()
    mock_service.create_user.return_value = User(
        id=uuid4(),
        email=Email("test@example.com"),
        password=Password.create("SecurePass123!")
    )

    app.dependency_overrides[get_user_service] = lambda: mock_service

    client = TestClient(app)

    # Act
    response = client.post("/users", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })

    # Assert
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    mock_service.create_user.assert_called_once()
```

### Integration Test (Real Service):

```python
# tests/integration/api/test_users.py
@pytest.mark.asyncio
async def test_create_user_integration(client, db_session):
    """Test endpoint with real service and database"""
    # Act
    response = await client.post("/users", json={
        "email": "integration@example.com",
        "password": "SecurePass123!"
    })

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "integration@example.com"

    # Verify in database
    user = await db_session.get(User, data["id"])
    assert user is not None
```

---

## 📊 Summary: Endpoint Responsibilities

| Concern | Who Handles | Example |
|---------|-------------|---------|
| **Request validation** | Pydantic schema | `UserCreate(email=...)` |
| **Authentication** | FastAPI security | `Depends(get_current_user)` |
| **Business logic** | Domain service | `service.create_user()` |
| **Data access** | Repository | `repository.get_by_email()` |
| **Response formatting** | Endpoint | `UserRead(**data)` |
| **Error translation** | Endpoint | `raise HTTPException(...)` |

---

## 🎓 Key Takeaways

1. **Endpoints = Thin**: Only HTTP concerns
2. **Services = Thick**: Business logic lives here
3. **Repositories = Data access**: SQL queries go here
4. **Dependency Injection**: Wire it all together
5. **Testability**: Mock services for unit tests

---

## 🚀 Migration Checklist

When refactoring endpoints:

- [ ] Remove business logic (move to service)
- [ ] Remove database queries (move to repository)
- [ ] Add dependency injection
- [ ] Add proper error handling
- [ ] Write unit tests (mock service)
- [ ] Write integration tests (real service)
- [ ] Verify API contract (same response format)

---

**🎉 Guided Tour Complete! Ready for summary?**
