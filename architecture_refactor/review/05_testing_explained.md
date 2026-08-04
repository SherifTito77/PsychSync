# Testing Infrastructure: Complete Guide

## 🎯 The Testing Pyramid

```
                    ▲
                   /E\          Few (10-20)
                  /E2E\         Slow, expensive
                 /-----\        Critical paths only
                /       \
               /Integration\   More (20-30)
              /_____________\   Medium speed
             /              \    Component interaction
            /                \
           /    Unit Tests    \  Many (50-70)
          /____________________\ Fast, cheap
                                     Isolated logic
```

**Philosophy:**
- **Unit tests**: Test business logic in isolation (mock dependencies)
- **Integration tests**: Test components work together (real database)
- **E2E tests**: Test critical user workflows (full stack)

---

## 🧪 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Fast, isolated tests
│   ├── domain/
│   │   ├── entities/              # Test domain entities
│   │   └── services/              # Test domain services
│   ├── infrastructure/
│   │   └── repositories/          # Test repositories
│   └── schemas/                   # Test Pydantic schemas
├── integration/                   # Component tests
│   ├── api/                       # Test API endpoints
│   └── database/                  # Test database integration
├── e2e/                           # Full workflow tests
│   ├── test_onboarding.py
│   └── test_assessment_flow.py
└── fixtures/                      # Test data helpers
```

---

## 📦 Key Fixtures (conftest.py)

### Database Fixtures

```python
# tests/conftest.py

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    test_db_url = settings.DATABASE_URL.replace("/psychsync", "/psychsync_test")

    engine = create_async_engine(test_db_url, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create database session with automatic rollback"""
    async_session_maker = sessionmaker(test_engine, class_=AsyncSession)

    async with async_session_maker() as session:
        async with session.begin():
            yield session

        await session.rollback()  # Never commit to test DB
```

### Mock Fixtures

```python
@pytest.fixture
def mock_user_repository():
    """Mock repository for unit tests"""
    repo = AsyncMock()
    repo.get = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo

@pytest.fixture
def mock_ai_processor():
    """Mock AI processor"""
    processor = MagicMock()
    processor.process = MagicMock(return_value=ProcessingResult.success(
        framework="test",
        data={"result": "test"},
        confidence=0.95
    ))
    return processor
```

### Authentication Fixture

```python
@pytest.fixture
def auth_headers(client):
    """Get authenticated request headers"""
    # Register user
    client.post("/api/v1/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })

    # Login
    response = client.post("/api/v1/login", data={
        "username": "test@example.com",
        "password": "SecurePass123!"
    })

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

---

## ✍️ Writing Unit Tests

### Example: Testing Domain Service

```python
# tests/unit/domain/services/test_user_service.py

import pytest
from unittest.mock import AsyncMock

class TestUserService:
    """Unit tests for UserService"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_user_repository):
        """Should create user with valid data"""
        # Arrange
        mock_user_repository.get_by_email.return_value = None  # Email doesn't exist
        mock_user_repository.create.return_value = User(...)

        service = UserService(mock_user_repository)

        # Act
        user = await service.create_user({
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Assert
        assert user.email == "test@example.com"
        mock_user_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, mock_user_repository):
        """Should reject duplicate email"""
        # Arrange
        existing_user = User(email=Email("test@example.com"), ...)
        mock_user_repository.get_by_email.return_value = existing_user

        service = UserService(mock_user_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="already exists"):
            await service.create_user({
                "email": "test@example.com",
                "password": "SecurePass123!"
            })
```

### Key Points:

1. **Mock dependencies**: Don't use real database in unit tests
2. **Test behavior**: WHAT it does, not HOW
3. **Arrange-Act-Assert**: Clear test structure
4. **One assertion per test**: Tests should test one thing

---

## 🔌 Writing Integration Tests

### Example: Testing API Endpoint

```python
# tests/integration/api/test_users.py

@pytest.mark.asyncio
async def test_register_user(client):
    """Test user registration endpoint"""
    # Arrange
    user_data = {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "full_name": "New User"
    }

    # Act
    response = await client.post("/api/v1/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data  # Never return password!

@pytest.mark.asyncio
async def test_login_success(client):
    """Test user login"""
    # Arrange - register first
    await client.post("/api/v1/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })

    # Act - login
    response = await client.post("/api/v1/login", data={
        "username": "test@example.com",
        "password": "SecurePass123!"
    })

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

### Key Points:

1. **Real database**: Integration tests use real DB
2. **Full stack**: Tests request → service → DB → response
3. **Transaction rollback**: Tests don't pollute database
4. **FastAPI TestClient**: Async client for testing

---

## 🎭 Writing E2E Tests

### Example: Testing User Journey

```python
# tests/e2e/test_onboarding.py

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_onboarding_flow(client):
    """Test user onboarding: register → verify → login → complete profile"""

    # Step 1: Register
    response = await client.post("/api/v1/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Step 2: Verify email (simulate)
    await client.post(f"/api/v1/users/{user_id}/verify", json={
        "token": "verification-token"
    })

    # Step 3: Login
    response = await client.post("/api/v1/login", data={
        "username": "newuser@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Step 4: Complete profile
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.patch("/api/v1/users/me", json={
        "full_name": "New User",
        "timezone": "America/New_York"
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "New User"

    # Step 5: Create first assessment
    response = await client.post("/api/v1/assessments", json={
        "title": "My First Assessment",
        "framework": "mbti"
    }, headers=headers)
    assert response.status_code == 201
```

### Key Points:

1. **Critical paths only**: Test important workflows
2. **Real API**: Use TestClient like real HTTP client
3. **Multiple steps**: Test complete user journeys
4. **Slow but valuable**: Catch integration issues

---

## 🎯 Test Markers

```python
# pytest.ini
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (database)
    e2e: End-to-end tests (full stack)
    slow: Slow-running tests
    smoke: Critical path tests
```

### Usage:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run smoke tests (quick health check)
pytest -m smoke

# Skip slow tests
pytest -m "not slow"
```

---

## 📊 Coverage Goals

```python
# pytest.ini
addopts =
    --cov=app
    --cov=app.ai
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85  # Require 85% coverage
```

### Check Coverage:

```bash
# Run with coverage
pytest --cov=app --cov=app.ai

# View HTML report
open htmlcov/index.html
```

---

## 🚀 Running Tests

### Development

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/unit/domain/services/test_user_service.py

# Run specific test
pytest tests/unit/domain/services/test_user_service.py::TestUserService::test_create_user_success

# Run with coverage
pytest --cov=app --cov-report=html
```

### CI/CD

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest tests/unit/ -v --cov=app

- name: Run integration tests
  run: pytest tests/integration/ -v

- name: Run smoke tests
  run: pytest -m smoke
```

---

## 💡 Best Practices

### DO ✅

1. **Test behavior, not implementation**
   ```python
   # ✅ Good: Tests WHAT
   assert user.can_login() == True

   # ❌ Bad: Tests HOW
   assert user.is_active == True and user.is_verified == True
   ```

2. **One assertion per test**
   ```python
   # ✅ Good: Clear what failed
   def test_user_email():
       assert user.email == "test@example.com"

   # ❌ Bad: Which assertion failed?
   def test_user_everything():
       assert user.email == "test@example.com"
       assert user.name == "Test"
       assert user.active == True
   ```

3. **Use descriptive names**
   ```python
   # ✅ Good: Know what it tests
   def test_create_user_with_duplicate_email_raises_error():
       pass

   # ❌ Bad: Vague
   def test_user():
       pass
   ```

4. **Arrange-Act-Assert pattern**
   ```python
   def test_user_creation():
       # Arrange: Setup test data
       data = {"email": "test@example.com"}

       # Act: Execute code
       user = create_user(data)

       # Assert: Verify result
       assert user.email == "test@example.com"
   ```

### DON'T ❌

1. **Don't test private methods**
   ```python
   # ❌ Bad: Testing implementation detail
   def test_private_method():
       result = user._private_method()

   # ✅ Good: Test public behavior
   def test_public_behavior():
       result = user.public_method()
   ```

2. **Don't mock what you don't own**
   ```python
   # ❌ Bad: Mocking third-party library
   with mock('sqlalchemy.create_engine'):
       # Test

   # ✅ Good: Use real library or integration test
   engine = create_engine("sqlite:///:memory:")
   ```

3. **Don't test trivial code**
   ```python
   # ❌ Bad: Testing getter
   def test_get_email():
       assert user.email == user.email

   # ✅ Good: Test business logic
   def test_can_login_with_active_verified_user():
       assert user.can_login() == True
   ```

---

## 📊 Summary: Testing Levels

| Level | Speed | Cost | Scope | Example |
|-------|-------|------|-------|---------|
| **Unit** | Fast (ms) | Low | Single function | `user.can_login()` |
| **Integration** | Medium (s) | Medium | Multiple components | API endpoint |
| **E2E** | Slow (min) | High | Full workflow | User onboarding |

**Target mix:**
- 70% Unit tests (fast, many)
- 20% Integration tests (medium, some)
- 10% E2E tests (slow, few)

---

**Ready for Stop 6: Thin API Layer Examples?**
