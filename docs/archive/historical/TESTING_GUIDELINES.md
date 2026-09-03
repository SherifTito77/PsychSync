# PsychSync Testing Guidelines

**Version:** 1.0.0
**Last Updated:** 2025-01-19

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Pyramid](#test-pyramid)
3. [Writing Unit Tests](#writing-unit-tests)
4. [Writing Integration Tests](#writing-integration-tests)
5. [Writing E2E Tests](#writing-e2e-tests)
6. [Test Coverage](#test-coverage)
7. [Best Practices](#best-practices)
8. [CI/CD Integration](#cicd-integration)

---

## Testing Philosophy

At PsychSync, we follow the **Testing Pyramid** approach:

```
        ▲
       /E\        Few E2E tests (slow, expensive)
      /___\
     / I  \      More integration tests (medium)
    /______\
   /   U    \    Most unit tests (fast, cheap)
  /__________\
```

**Key Principles:**

1. **Fast Feedback:** Unit tests should run in milliseconds
2. **Isolation:** Each test should be independent
3. **Clarity:** Tests should serve as documentation
4. **Reliability:** Tests should be flake-free
5. **Maintainability:** Tests should be easy to update

---

## Test Pyramid

### Level 1: Unit Tests (70% of tests)

**Purpose:** Test individual components in isolation

**Characteristics:**
- Run in < 10ms each
- No external dependencies (database, API, filesystem)
- Mock all external interactions
- Test business logic, validation, edge cases

**Examples:**
- Domain entities (User, Assessment)
- Value objects (Email, Password)
- Services with mocked repositories
- AI processors without HTTP layer

### Level 2: Integration Tests (20% of tests)

**Purpose:** Test component interactions

**Characteristics:**
- Run in < 1 second each
- Real database (test database)
- No external APIs (mock HTTP)
- Test repositories, data access, ORM

**Examples:**
- Repository CRUD operations
- Database queries and filters
- Transaction handling
- Cache integration

### Level 3: E2E Tests (10% of tests)

**Purpose:** Test critical user journeys

**Characteristics:**
- Run in < 10 seconds each
- Full stack (API → Service → Repository → Database)
- Test only critical paths
- Focus on user-facing features

**Examples:**
- User registration flow
- Assessment submission
- Authentication flow
- Payment processing

---

## Writing Unit Tests

### Test Structure

Follow the **AAA Pattern** (Arrange, Act, Assert):

```python
@pytest.mark.asyncio
async def test_create_user_with_valid_data():
    # Arrange - Set up test data
    email = Email(value="user@example.com")
    password = Password.create(plaintext="SecureP@ss99!")

    # Act - Execute the code
    user = User.create(email=email, password=password)

    # Assert - Verify results
    assert user.email == email
    assert user.is_active is True
```

### Naming Conventions

```python
# Test function names should describe:
# 1. What is being tested
# 2. Under what conditions
# 3. What the expected result is

def test_[method]_[scenario]_[expected_result]()

# Examples:
def test_create_user_with_valid_email_succeeds()
def test_verify_email_with_invalid_token_fails()
def test_update_profile_with_short_name_raises_error()
```

### Fixtures

Use fixtures for common test data:

```python
# tests/conftest.py
@pytest.fixture
def valid_email():
    """Provide a valid email for testing"""
    return Email(value="test@example.com")

@pytest.fixture
def valid_password():
    """Provide a valid password for testing"""
    return Password.create(plaintext="SecureP@ss99!")

# Use fixtures in tests
def test_user_creation(valid_email, valid_password):
    user = User.create(email=valid_email, password=valid_password)
    assert user.is_active is True
```

### Mocking

Mock external dependencies:

```python
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_service_with_mocked_repository():
    # Arrange
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_by_email.return_value = None
    mock_repo.create.return_value = user_instance

    service = UserService(repository=mock_repo)

    # Act
    result = await service.create_user(user_data)

    # Assert
    mock_repo.create.assert_called_once()
    assert result.email == user_data.email
```

### Test Markers

Use pytest markers to categorize tests:

```python
# Unit test (fast, no dependencies)
@pytest.mark.unit
def test_email_validation():
    pass

# Integration test (database required)
@pytest.mark.asyncio
@pytest.mark.integration
async def test_repository_create():
    pass

# Slow test (> 5 seconds)
@pytest.mark.slow
async def test_bulk_operation():
    pass

# Security test
@pytest.mark.security
def test_sql_injection_prevention():
    pass
```

---

## Writing Integration Tests

### Database Setup

Use test database fixtures:

```python
@pytest.mark.asyncio
@pytest.mark.integration
class TestUserRepository:
    async def test_create_user(self, test_db):
        """test_db fixture creates fresh database for each test"""
        repo = UserRepository(db=test_db)

        user = await repo.create(user_data)

        assert user.id is not None
```

### Transaction Isolation

Each test gets a clean database:

```python
@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create fresh database session for each test"""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Clean up - drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Testing Repositories

Focus on data access logic:

```python
@pytest.mark.asyncio
@pytest.mark.integration
class TestUserRepository:
    async def test_get_by_email_case_insensitive(self, test_db):
        # Create user with lowercase email
        user = await repo.create(UserCreate(email="test@example.com"))

        # Find with uppercase
        found = await repo.get_by_email("TEST@EXAMPLE.COM")

        assert found is not None
        assert found.email == "test@example.com"
```

---

## Writing E2E Tests

### Critical User Journeys

Test only the most important flows:

```python
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_user_registration_flow(client):
    # 1. Register user
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "SecureP@ss99!",
        "full_name": "John Doe"
    })
    assert response.status_code == 201
    data = response.json()
    user_id = data["id"]

    # 2. Verify email
    token = generate_verification_token(user_id)
    response = await client.post(f"/api/v1/auth/verify?token={token}")
    assert response.status_code == 200

    # 3. Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "SecureP@ss99!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Test Data Management

Use factories for complex test data:

```python
@pytest.fixture
async def test_user_with_assessment(test_db):
    """Create user with completed assessment"""
    user = await create_test_user(test_db)
    assessment = await create_test_assessment(test_db, user_id=user.id)
    response = await create_test_response(test_db, assessment_id=assessment.id)

    return {
        "user": user,
        "assessment": assessment,
        "response": response
    }
```

---

## Test Coverage

### Coverage Configuration

`.coveragerc` configuration:

```ini
[run]
source = app
omit = */tests/*, */venv/*
branch = True  # Enable branch coverage

[report]
precision = 2
show_missing = True
fail_under = 80  # Require 80% coverage
```

### Coverage Targets

| Component | Target Coverage | Notes |
|-----------|----------------|-------|
| Domain Entities | 95%+ | Critical business logic |
| Value Objects | 95%+ | Validation is crucial |
| Services | 90%+ | Business rules |
| Repositories | 85%+ | Data access |
| API Endpoints | 75%+ | HTTP layer |
| Utilities | 80%+ | Helper functions |

### Running Coverage

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check specific module
pytest --cov=app.domain.entities --cov-report=term-missing
```

### Coverage Auditing

```bash
# Run coverage audit script
python scripts/audit_test_coverage.py

# View detailed report
cat reports/test_coverage_audit.json
```

---

## Best Practices

### DO ✅

1. **Write tests first** (TDD approach when possible)
   ```python
   # Write the test first
   def test_password_must_be_12_chars():
       with pytest.raises(ValidationError):
           Password.create(plaintext="Short1!")

   # Then implement the feature
   ```

2. **Use descriptive test names**
   ```python
   # Good
   def test_verify_email_with_invalid_token_raises_error()

   # Bad
   def test_verify()
   ```

3. **Test one thing per test**
   ```python
   # Good
   def test_create_user_sets_active_flag_true()
   def test_create_user_sets_verified_flag_false()

   # Bad
   def test_create_user_sets_all_flags()
   ```

4. **Use fixtures for setup**
   ```python
   @pytest.fixture
   def test_user():
       return User.create(email=Email("test@example.com"), ...)
   ```

5. **Mock external dependencies**
   ```python
   def test_service_with_mocked_repo():
       mock_repo = Mock()
   ```

6. **Clean up in tests**
   ```python
   async def test_with_cleanup(test_db):
       user = await create_user(test_db)
       # ... test code ...
       # Cleanup happens automatically via fixture
   ```

### DON'T ❌

1. **Don't test implementation details**
   ```python
   # Bad - tests internal method
   def test__private_method():

   # Good - tests public behavior
   def test_calculate_total_price():
   ```

2. **Don't write flaky tests**
   ```python
   # Bad - depends on timing
   await asyncio.sleep(1)  # Hope it's ready

   # Good - use explicit waits
   await wait_for_condition(lambda: result is ready)
   ```

3. **Don't test external libraries**
   ```python
   # Bad - tests bcrypt
   def test_password_hashing():

   # Good - tests our wrapper
   def test_password_value_object():
   ```

4. **Don't use shared state**
   ```python
   # Bad - tests depend on order
   global_counter = 0

   # Good - each test is isolated
   def test_with_isolated_data():
   ```

5. **Don't ignore test failures**
   ```python
   # Bad
   @pytest.mark.skipif(True, reason="Broken")

   # Good - fix the test or the code
   def test_feature():
       assert feature_works()
   ```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest -m unit --cov=app --cov-report=xml

      - name: Run integration tests
        run: pytest -m integration --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest -m unit
        language: system
        pass_filenames: false

      - id: pytest-coverage
        name: Check coverage
        entry: pytest --cov=app --cov-fail-under=80
        language: system
        pass_filenames: false
```

---

## Test Execution

### Run All Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Verbose output
pytest -v
```

### Run Specific Tests

```bash
# By marker
pytest -m unit
pytest -m integration
pytest -m "not slow"

# By file
pytest tests/unit/domain/entities/test_user.py

# By function name
pytest -k "test_create_user"

# By class
pytest tests/unit/test_user.py::TestUserEntity
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Parallel by test file
pytest -n 4
```

### Debug Failed Tests

```bash
# Stop on first failure
pytest -x

# Drop to debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Print output (don't capture)
pytest -s
```

---

## Common Patterns

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_service():
    result = await service.process_data(data)
    assert result is not None
```

### Testing Exceptions

```python
def test_raises_error():
    with pytest.raises(ValidationError, match="Invalid email"):
        Email(value="not-an-email")
```

### Testing Warnings

```python
import warnings

def test_deprecated_method():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        old_method()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
```

### Parameterized Tests

```python
@pytest.mark.parametrize("email,valid", [
    ("user@example.com", True),
    ("invalid", False),
    ("@example.com", False),
])
def test_email_validation(email, valid):
    if valid:
        Email(value=email)
    else:
        with pytest.raises(ValidationError):
            Email(value=email)
```

---

## Resources

- **Pytest Documentation:** https://docs.pytest.org/
- **Async Testing:** https://pytest-asyncio.readthedocs.io/
- **Coverage.py:** https://coverage.readthedocs.io/
- **Factory Boy:** https://factoryboy.readthedocs.io/

---

**Generated:** 2025-01-19
**Phase:** 5 (Comprehensive Testing)
**Status:** ✅ Complete
