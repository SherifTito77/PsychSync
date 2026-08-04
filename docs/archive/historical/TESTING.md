# Testing Guide for PsychSync

This comprehensive testing guide covers all aspects of testing the PsychSync psychological assessment platform.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Writing Tests](#writing-tests)
- [Test Fixtures](#test-fixtures)
- [Mock Services](#mock-services)
- [Coverage](#coverage)
- [Performance Testing](#performance-testing)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

PsychSync uses a comprehensive testing strategy with multiple test types:

- **Unit Tests**: Fast, isolated tests for individual functions and classes
- **Integration Tests**: Tests for service layers and database interactions
- **API Tests**: End-to-end API endpoint testing
- **Performance Tests**: Load and performance benchmarking
- **Security Tests**: Security vulnerability and validation testing

### Key Testing Tools

- **pytest**: Primary testing framework with async support
- **pytest-asyncio**: Async testing support
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel test execution
- **httpx**: Async HTTP client for API testing
- **factory-boy**: Test data factories
- **faker**: Realistic test data generation

## Test Structure

```
tests/
├── conftest.py                 # Global test configuration and fixtures
├── test_auth_comprehensive.py  # Authentication system tests
├── test_api_endpoints_comprehensive.py  # API endpoint tests
├── test_services_comprehensive.py     # Service layer tests
├── api/                        # API-specific tests
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_teams.py
│   └── test_assessments.py
├── integration/                # Integration tests
│   └── test_full_flow.py
└── scripts/                    # Test utility scripts
    └── run_tests.py
```

## Running Tests

### Quick Development Tests

```bash
# Run unit tests only (fast)
python scripts/run_tests.py unit

# Run development checks (unit + auth)
python scripts/run_tests.py dev

# Run specific test file
python scripts/run_tests.py -f tests/test_auth_comprehensive.py
```

### Comprehensive Test Suites

```bash
# Run all tests with full coverage
python scripts/run_tests.py all

# Run CI pipeline
python scripts/run_tests.py ci

# Run tests in parallel
python scripts/run_tests.py parallel --workers 4
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m auth
pytest -m performance

# Run specific test file
pytest tests/test_auth_comprehensive.py

# Run with verbose output
pytest -v

# Run with detailed traceback
pytest --tb=long
```

### Test Categories

```bash
# Unit tests (fast, isolated)
pytest -m unit

# Integration tests (database dependencies)
pytest -m integration

# Authentication tests
pytest -m auth

# API endpoint tests
pytest -m api

# Service layer tests
pytest -m service

# Performance tests
pytest -m performance

# Security tests
pytest -m security

# Slow tests (for CI/nightly runs)
pytest -m slow
```

## Test Types

### Unit Tests

Unit tests are fast, isolated tests that test individual functions and classes without external dependencies.

**Characteristics:**
- Run in milliseconds
- Use mocks for external dependencies
- Test single functions or methods
- No database or network calls

**Example:**
```python
@pytest.mark.unit
def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)
```

### Integration Tests

Integration tests verify that different parts of the system work together correctly.

**Characteristics:**
- Test database interactions
- Test service layer functionality
- Use real database (in-memory SQLite)
- Run in seconds

**Example:**
```python
@pytest.mark.integration
async def test_create_user_with_database(async_db: AsyncSession):
    """Test user creation with real database"""
    user_data = UserCreate(
        email="test@example.com",
        full_name="Test User",
        password="SecurePassword123!"
    )

    user = await create_user(async_db, user_data)

    assert user.email == user_data.email
    assert user.password_hash is not None
```

### API Tests

API tests verify that HTTP endpoints work correctly.

**Characteristics:**
- Test HTTP requests/responses
- Test authentication and authorization
- Test pagination, filtering, sorting
- Test error handling

**Example:**
```python
@pytest.mark.api
async def test_register_user_success(async_client: AsyncClient):
    """Test successful user registration endpoint"""
    user_data = {
        "email": "newuser@test.com",
        "full_name": "New Test User",
        "password": "SecurePassword123!"
    }

    response = await async_client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data
```

## Writing Tests

### Test Structure

Each test should follow the AAA pattern:
- **Arrange**: Set up test data and mocks
- **Act**: Execute the code being tested
- **Assert**: Verify the results

### Test Naming

Use descriptive test names that explain what is being tested:

```python
# Good
def test_user_registration_with_valid_data_succeeds()
def test_login_with_invalid_credentials_returns_401()
def test_password_reset_token_expires_after_24_hours()

# Avoid
def test_user()
def test_login()
def test_reset()
```

### Async Tests

Use `pytest-asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_user_creation():
    """Test async user creation"""
    user = await create_user(async_db, user_data)
    assert user is not None
```

### Test Markers

Use appropriate test markers to categorize tests:

```python
@pytest.mark.unit
@pytest.mark.auth
async def test_user_authentication():
    """Test user authentication"""
    pass

@pytest.mark.integration
@pytest.mark.database
async def test_user_database_operations():
    """Test user database operations"""
    pass
```

## Test Fixtures

Fixtures provide test setup and teardown functionality. Key fixtures are defined in `conftest.py`:

### Database Fixtures

```python
@pytest_asyncio.fixture
async def async_db():
    """Create async test database session"""
    # Setup
    yield session
    # Cleanup
```

### Client Fixtures

```python
@pytest_asyncio.fixture
async def async_client(async_db):
    """Create async test client"""
    # Setup
    yield client
    # Cleanup
```

### Authentication Fixtures

```python
@pytest_asyncio.fixture
async def test_user(async_db):
    """Create test user"""
    user = await create_user(async_db, user_data)
    yield user

@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Create authentication headers"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### Mock Service Fixtures

```python
@pytest.fixture
def mock_email_service():
    """Mock email service"""
    with patch('app.services.email_service.EmailService') as mock:
        yield mock
```

## Mock Services

Use mocks to isolate tests from external dependencies:

### Email Service Mock

```python
@pytest.fixture
def mock_email_service():
    """Mock email service"""
    with patch('app.services.email_service.EmailService') as mock:
        service = AsyncMock()
        service.send_email.return_value = {"message_id": fake.uuid4()}
        mock.return_value = service
        yield service
```

### Cache Mock

```python
@pytest.fixture
def mock_cache_manager():
    """Mock cache manager"""
    with patch('app.core.enhanced_cache.get_cache_manager') as mock:
        cache = AsyncMock()
        cache.get.return_value = None
        cache.set.return_value = True
        mock.return_value = cache
        yield cache
```

### Redis Mock

```python
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('redis.asyncio.from_url') as mock:
        redis_client = AsyncMock()
        redis_client.ping.return_value = True
        mock.return_value = redis_client
        yield redis_client
```

## Coverage

### Coverage Configuration

Coverage is configured in `pytest.ini` and `conftest.py`:

```ini
[tool:pytest]
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### Coverage Reports

Generate coverage reports:

```bash
# HTML report (detailed)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=app --cov-report=term-missing

# XML report (for CI)
pytest --cov=app --cov-report=xml
```

### Coverage Exclusions

Exclude from coverage:
- Test files
- Migration files
- Configuration files
- Development/debugging code

## Performance Testing

### Benchmark Tests

Use `pytest-benchmark` for performance testing:

```python
@pytest.mark.performance
def test_password_hashing_performance(benchmark):
    """Test password hashing performance"""
    password = "TestPassword123!"

    def hash_password():
        return get_password_hash(password)

    result = benchmark(hash_password)
    assert result is not None
```

### Load Testing

Use Locust for load testing:

```python
from locust import HttpUser, task, between

class AuthUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login on start"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]

    @task(3)
    def view_profile(self):
        """View user profile"""
        self.client.get("/api/v1/users/me", headers={
            "Authorization": f"Bearer {self.token}"
        })
```

### Memory Profiling

Use memory-profiler for memory testing:

```python
@pytest.mark.performance
@profile
def test_memory_usage():
    """Test memory usage of operations"""
    # Memory-intensive operation
    pass
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        python scripts/run_tests.py ci

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python scripts/run_tests.py dev
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

#### Test Database Issues

**Problem**: Tests fail with database connection errors
**Solution**: Check database configuration and ensure test database exists

```bash
# Check database connection
python -c "from app.core.database import engine; print(engine.url)"
```

#### Async Test Issues

**Problem**: Async tests hang or fail
**Solution**: Ensure proper async/await usage and fixture setup

```python
# Correct
@pytest.mark.asyncio
async def test_async_function(async_db):
    result = await async_function(async_db)
    assert result

# Incorrect
def test_async_function(async_db):
    result = async_function(async_db)  # Missing await
    assert result
```

#### Mock Issues

**Problem**: Mocks not working as expected
**Solution**: Check patch paths and mock setup

```python
# Correct patch path
with patch('app.services.email_service.EmailService') as mock:
    pass

# Incorrect patch path
with patch('services.email_service.EmailService') as mock:
    pass
```

#### Coverage Issues

**Problem**: Coverage reporting incorrect results
**Solution**: Check coverage configuration and exclusions

```bash
# Debug coverage
pytest --cov=app --cov-report=term-missing --cov-config=pyproject.toml
```

### Debugging Tests

#### Verbose Output

```bash
pytest -v -s --tb=long
```

#### Debug with pdb

```python
import pdb; pdb.set_trace()
```

#### Print Statements

```python
def test_debug_example():
    print("Debug point 1")
    result = some_function()
    print(f"Result: {result}")
    assert result
```

#### Logging

Configure logging in tests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Best Practices

1. **Keep tests fast and focused**
2. **Use descriptive test names**
3. **Test one thing per test**
4. **Use fixtures for setup**
5. **Mock external dependencies**
6. **Maintain high test coverage**
7. **Run tests frequently**
8. **Use CI/CD automation**
9. **Document complex test scenarios**
10. **Regularly review and update tests**

### Test Performance Tips

1. **Use in-memory databases for testing**
2. **Parallelize test execution**
3. **Reuse fixtures and setup**
4. **Avoid unnecessary I/O operations**
5. **Use mocks for slow operations**
6. **Profile slow tests**
7. **Optimize test data generation**

## Testing Checklist

Before committing code:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] API tests pass
- [ ] Coverage is >= 80%
- [ ] No test regressions
- [ ] Tests are properly categorized
- [ ] Test data is realistic
- [ ] Error cases are tested
- [ ] Performance tests pass
- [ ] Security tests pass

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test Coverage Documentation](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
