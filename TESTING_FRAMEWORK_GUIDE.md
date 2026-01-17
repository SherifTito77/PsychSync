# Comprehensive Testing Framework Guide

This guide documents the complete pytest testing framework for PsychSync, including automated test generation, coverage validation, and comprehensive reporting.

## 🎯 Overview

The PsychSync testing framework provides:

- **70% Unit Tests** - Individual function and method testing with mocked dependencies
- **20% Integration Tests** - End-to-end testing with real database and API interactions
- **10% Security & Performance Tests** - Specialized testing for vulnerabilities and performance
- **>80% Coverage Target** - Comprehensive code coverage analysis and validation
- **Automated Reporting** - Interactive HTML dashboards with detailed metrics

## 📁 Framework Components

### 1. Core Testing Infrastructure

#### `tests/conftest.py` - Test Configuration & Fixtures
```python
# Comprehensive test fixtures for:
# - Async database sessions
# - Authentication mocks
# - Test data factories
# - HTTP client setup
# - Mock services
```

#### `tests/test_auth_complete.py` - Authentication Security Tests
- **85+ comprehensive tests** covering password security, JWT tokens, account lockout
- **OWASP Top 10 security testing** patterns
- **Timing attack resistance** and **brute force prevention** validation

#### `tests/test_api_integration.py` - API Integration Tests
- **45+ integration tests** for all API endpoints
- **End-to-end authentication flows** testing
- **Database transaction validation** and **error handling** verification

#### `tests/test_coverage_validator.py` - Coverage Analysis System
- **Real-time coverage parsing** and **detailed reporting**
- **Coverage trend tracking** and **branch analysis**
- **HTML/JSON export** capabilities

### 2. Automated Test Generation

#### `scripts/generate_tests.py` - Test Suite Generator
```bash
# Generate tests for specific module
python scripts/generate_tests.py --module app.services.user_service

# Generate tests for all modules
python scripts/generate_tests.py --all --type comprehensive

# Generate only unit tests
python scripts/generate_tests.py --module app.api.v1.endpoints.users --type unit
```

**Features:**
- **AST-based code analysis** to understand function structure
- **Complexity scoring** to determine test depth required
- **Automatic fixture generation** based on function parameters
- **Security-aware testing** for authentication and data handling functions
- **Performance test templates** for complex functions

#### Generated Test Structure
```python
class TestUnitFunctions:
    """Unit tests for module functions"""

    def test_function_name_valid_inputs(self):
        """Test function_name - valid inputs"""
        # Arrange - Setup mocks and test data
        # Act - Execute function with test data
        # Assert - Verify expected behavior
        pass

    def test_function_name_invalid_inputs(self):
        """Test function_name - invalid inputs"""
        # Test error handling and edge cases
        pass

    def test_function_name_edge_cases(self):
        """Test function_name - edge cases"""
        # Test boundary conditions and special values
        pass
```

### 3. Reporting & Analytics

#### `scripts/test_report_dashboard.py` - Test Reporting Dashboard
```bash
# Generate comprehensive report
python scripts/test_report_dashboard.py --generate

# Generate report with CSV export
python scripts/test_report_dashboard.py --generate --export-format csv

# View HTML dashboard
open test_reports/test_dashboard_*.html
```

**Dashboard Features:**
- **Real-time test execution monitoring**
- **Interactive charts** for test results, coverage, and security
- **Performance benchmarking** with trend analysis
- **Security vulnerability tracking** with CWE mapping
- **Historical data comparison** and coverage trends

## 🧪 Test Categories & Patterns

### Unit Tests (70% of tests)

**Characteristics:**
- Test individual functions in isolation
- Mock all external dependencies (database, APIs, services)
- Fast execution with no external requirements
- Focus on business logic and edge cases

**Pattern:**
```python
@pytest.mark.unit
class TestUserService:
    def test_create_user_valid_data(self, mock_db, mock_email_service):
        # Arrange
        user_data = {"email": "test@example.com", "name": "Test User"}
        mock_db.return_value = Mock()

        # Act
        result = user_service.create_user(user_data)

        # Assert
        assert result.email == "test@example.com"
        mock_email_service.send_welcome_email.assert_called_once()
```

### Integration Tests (20% of tests)

**Characteristics:**
- Test multiple components working together
- Use real database connections (test database)
- Test API endpoints end-to-end
- Verify data flow and transactions

**Pattern:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_registration_flow(self, async_client):
    # Complete user registration flow
    response = await async_client.post("/api/v1/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201

    # Verify email verification
    # Verify database entry created
    # Verify authentication works
```

### Security Tests

**OWASP Top 10 Coverage:**
- **A01: Broken Access Control** - Authorization testing
- **A02: Cryptographic Failures** - Password hashing, JWT security
- **A03: Injection** - SQL injection, XSS prevention
- **A05: Security Misconfiguration** - Headers, CORS, CSRF
- **A07: Authentication Failures** - Login security, session management
- **A09: Security Logging** - Audit trail validation

**Security Test Pattern:**
```python
@pytest.mark.security
class TestAuthenticationSecurity:
    def test_password_brute_force_protection(self):
        # Test account lockout after failed attempts
        # Verify progressive lockout timing
        # Test lockout bypass prevention

    def test_jwt_token_security(self):
        # Test token manipulation resistance
        # Test signature validation
        # Test token expiration enforcement
```

### Performance Tests

**Performance Metrics:**
- **Response time benchmarks** (< 200ms for API calls)
- **Memory usage validation** (< 100MB for typical operations)
- **Database query optimization** (index usage analysis)
- **Concurrent request handling** (100+ concurrent users)

**Performance Test Pattern:**
```python
@pytest.mark.performance
def test_api_response_times(self):
    start_time = time.time()

    # Execute typical API operations
    response = client.get("/api/v1/users")

    duration = time.time() - start_time
    assert duration < 0.2  # 200ms limit
    assert response.status_code == 200
```

## 📊 Coverage Analysis & Validation

### Coverage Targets
- **Overall Coverage: >80%**
- **Unit Test Coverage: >90%**
- **Integration Test Coverage: >70%**
- **Security Test Coverage: 100%** for authentication functions

### Coverage Validation
```python
# Run coverage analysis
pytest --cov=app --cov-report=html --cov-report=term-missing

# Validate coverage meets targets
python scripts/test_report_dashboard.py --generate
```

### Coverage Reporting Features
- **Line-by-line coverage analysis**
- **Branch coverage tracking**
- **Missing line identification**
- **Coverage trend visualization**
- **File-level coverage breakdown**

## 🔧 Usage Instructions

### Quick Start
```bash
# 1. Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# 2. Generate comprehensive report
python scripts/test_report_dashboard.py --generate

# 3. View interactive dashboard
open test_reports/test_dashboard_*.html
```

### Test Generation Workflow
```bash
# 1. Generate tests for new module
python scripts/generate_tests.py --module app.services.new_service

# 2. Customize generated tests
# Edit tests/app/services/new_service_test.py
# Add business logic specific assertions
# Configure mock return values

# 3. Run and validate tests
pytest tests/app/services/new_service_test.py -v

# 4. Check coverage impact
pytest --cov=app.services.new_service --cov-report=term-missing
```

### Continuous Integration Integration
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Run Tests
      run: |
        pytest tests/ -v --cov=app --cov-fail-under=80

    - name: Generate Report
      run: python scripts/test_report_dashboard.py --generate

    - name: Upload Coverage
      uses: codecov/codecov-action@v1
```

## 📈 Test Metrics & KPIs

### Quality Metrics
- **Test Pass Rate:** Target >90%
- **Coverage Percentage:** Target >80%
- **Security Score:** Target >95/100
- **Performance Score:** Target >85/100
- **Test Execution Time:** Target <5 minutes

### Monitoring Dashboard
The HTML dashboard provides:
- **Real-time test status** with color-coded indicators
- **Coverage trends** over time
- **Performance benchmarking** against previous runs
- **Security vulnerability tracking** with severity classification
- **Detailed test failure analysis** with error messages and stack traces

### Alerting Thresholds
- **Critical:** Coverage < 70%, Security Score < 80, Pass Rate < 80%
- **Warning:** Coverage < 80%, Security Score < 90, Performance Score < 70
- **Info:** All metrics within target ranges

## 🛡️ Security Testing Best Practices

### Authentication Security
```python
def test_password_security(self):
    # Test password complexity requirements
    weak_passwords = ["123", "password", "qwerty"]
    for password in weak_passwords:
        assert not is_strong_password(password)

    # Test secure password hashing
    hashed = hash_password("SecurePassword123!")
    assert hashed.startswith("$2b$")  # bcrypt
    assert len(hashed) == 60
```

### Input Validation Security
```python
def test_sql_injection_prevention(self):
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "' UNION SELECT * FROM sensitive_data --"
    ]

    for payload in malicious_inputs:
        # Should not cause SQL errors or data leakage
        result = user_service.search_users(payload)
        assert isinstance(result, list)
```

### XSS Prevention
```python
def test_xss_prevention(self):
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>"
    ]

    for payload in xss_payloads:
        # Output should be escaped
        result = template_engine.render(user_input=payload)
        assert "<script>" not in result
        assert "javascript:" not in result
```

## ⚡ Performance Testing Guidelines

### Response Time Benchmarks
- **API Endpoints:** < 200ms (95th percentile)
- **Database Queries:** < 100ms average
- **File Operations:** < 500ms
- **Authentication:** < 150ms

### Load Testing Patterns
```python
@pytest.mark.performance
def test_concurrent_requests(self):
    import asyncio
    import concurrent.futures

    async def make_request():
        return await async_client.get("/api/v1/users")

    # Test 100 concurrent requests
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(asyncio.run, make_request()) for _ in range(100)]
        responses = [future.result() for future in futures]

    duration = time.time() - start_time

    # All requests should succeed
    assert all(r.status_code == 200 for r in responses)

    # Average response time should be reasonable
    avg_response_time = duration / 100
    assert avg_response_time < 0.5  # 500ms average
```

## 🔧 Test Data Management

### Test Data Factory
```python
class TestDataFactory:
    @staticmethod
    def create_user(**overrides):
        data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "is_verified": False
        }
        data.update(overrides)
        return data

    @staticmethod
    def create_organization(**overrides):
        data = {
            "name": "Test Organization",
            "domain": "test.example.com",
            "is_active": True
        }
        data.update(overrides)
        return data
```

### Database Isolation
```python
@pytest.fixture
async def test_db_session():
    """Isolated test database session"""
    async with TestSession() as session:
        # Start transaction
        transaction = await session.begin()

        try:
            yield session
        finally:
            # Rollback changes for test isolation
            await transaction.rollback()
```

## 📚 Advanced Testing Patterns

### Property-Based Testing
```python
import hypothesis
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=100))
def test_email_validation_property(self, email_input):
    """Test email validation with random inputs"""
    if "@" in email_input and "." in email_input.split("@")[-1]:
        assert is_valid_email(email_input) == True
    else:
        # Property: Invalid emails should be rejected
        assert is_valid_email(email_input) == False
```

### Mutation Testing
```python
def test_mutation_testing(self):
    """Verify tests catch intentional code changes"""
    # Temporarily modify code to introduce bugs
    # Run tests to ensure they catch the mutations
    # Restore original code
    pass
```

### Contract Testing
```python
def test_api_contract(self):
    """Verify API contract compliance"""
    response = client.get("/api/v1/users/1")

    assert response.status_code == 200

    # Verify response schema
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert isinstance(data["id"], int)
```

## 🎯 Best Practices Summary

### Test Design Principles
1. **Arrange-Act-Assert Pattern** - Clear test structure
2. **Single Assertion per Test** - Focused test cases
3. **Descriptive Test Names** - Self-documenting code
4. **Test Independence** - No test dependencies
5. **Realistic Test Data** - Production-like scenarios

### Security Testing Principles
1. **Think Like an Attacker** - Test for vulnerabilities
2. **Validate All Inputs** - Never trust user input
3. **Test Error Conditions** - Secure error handling
4. **Verify Data Sanitization** - Prevent injection attacks
5. **Check Access Controls** - Authorization validation

### Performance Testing Principles
1. **Set Clear Benchmarks** - Measurable performance goals
2. **Test Under Load** - Realistic usage scenarios
3. **Monitor Resource Usage** - Memory, CPU, database connections
4. **Establish Baselines** - Compare against previous performance
5. **Test Scalability** - Performance under increasing load

### Coverage Principles
1. **Aim for High Coverage** - But focus on critical paths
2. **Test Edge Cases** - Boundary conditions and error scenarios
3. **Cover All Branches** - Conditional logic testing
4. **Validate Exception Paths** - Error handling verification
5. **Monitor Coverage Trends** - Regression detection

---

**This comprehensive testing framework provides the foundation for maintaining high code quality, security, and performance throughout the PsychSync application lifecycle. Regular use of these tools and patterns will help identify issues early, prevent regressions, and ensure reliable software delivery.**
