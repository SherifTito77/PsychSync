# PsychSync Onboarding Testing Guide

## 📋 Overview

This guide provides comprehensive instructions for running, maintaining, and extending the PsychSync user onboarding functional test suite.

## 🎯 Testing Strategy

The onboarding test suite follows a **multi-layered approach**:

### 1. Test Layers
- **Functional Tests**: Validate core user journey functionality
- **Security Tests**: Verify input validation, XSS/SQL injection prevention, and rate limiting
- **Performance Tests**: Measure response times, throughput, and resource usage
- **Integration Tests**: Test cross-service communication and data consistency
- **Load Tests**: Simulate realistic user traffic patterns

### 2. Test Categories
- **High Priority (P0)**: Core functionality that must work for basic onboarding
- **Medium Priority (P1)**: Important features with significant business impact
- **Low Priority (P2)**: Edge cases, performance optimization, and extended scenarios

## 🚀 Quick Start

### Running All Tests

```bash
# Run the complete test suite
python tests/test_onboarding_test_runner.py

# Run with pytest (recommended for CI/CD)
pytest tests/test_onboarding_functional.py tests/test_onboarding_service_layer.py -v
```

### Running Individual Test Suites

```bash
# Functional tests only
pytest tests/test_onboarding_functional.py -v

# Service layer tests only
pytest tests/test_onboarding_service_layer.py -v

# Quick assessment tests
pytest tests/test_onboarding_functional.py::TestAnonymousQuickAssessment -v

# Registration tests
pytest tests/test_onboarding_functional.py::TestUserRegistration -v
```

## 📁 Test File Structure

```
tests/
├── test_onboarding_functional.py          # Core API endpoint tests
├── test_onboarding_service_layer.py      # Business logic tests
├── test_onboarding_test_runner.py          # Master test orchestrator
└── ONBOARDING_TESTING_GUIDE.md          # This file
```

## 🔧 Test Configuration

### Test Parameters

Modify test configuration in `test_onboarding_test_runner.py`:

```python
config = TestConfiguration(
    test_timeout=300,                    # 5 minutes per test suite
    max_concurrent_users=10,              # Load test concurrent users
    load_test_duration=60,                # Load test duration in seconds
    security_scan_enabled=True,          # Enable security vulnerability scanning
    performance_thresholds={
        "quick_assessment_max_time": 2.0,
        "registration_max_time": 3.0,
        "team_creation_max_time": 2.5,
        "insights_generation_max_time": 5.0
    }
)
```

### Environment Variables

```bash
# Testing environment
export TESTING=true
export DATABASE_URL=sqlite+aiosqlite:///:memory:
export REDIS_URL=redis://localhost:6379/1

# Security settings
export SECRET_KEY=test-secret-key-for-testing
export ENVIRONMENT=testing
```

## 🧪 Test Coverage

### Functional Tests (80+ test cases)

#### Anonymous Quick Assessment
- ✅ Valid assessment request with all roles/challenges
- ✅ Input validation and error handling
- ✅ Analytics event tracking
- ✅ Rate limiting enforcement
- ✅ Performance benchmarks

#### User Registration
- ✅ Valid registration flow
- ✅ Password complexity validation
- ✅ Email format validation
- ✅ Duplicate email prevention
- ✅ SQL injection and XSS prevention

#### Authentication
- ✅ Valid login flow
- ✅ Token generation and refresh
- ✅ Invalid credential handling
- ✅ Brute force protection
- ✅ Account lockout mechanisms

#### Team Creation & Setup
- ✅ Team creation with proper permissions
- ✅ Setup wizard progression
- ✅ Data validation and sanitization
- ✅ Organization management

#### Onboarding Status & Progress
- ✅ Anonymous user status
- ✅ Authenticated user progress tracking
- ✅ Completion status validation
- ✅ Step-by-step progress verification

### Security Tests (60+ test cases)

#### Input Validation & Sanitization
- ✅ XSS prevention in all input fields
- ✅ SQL injection prevention
- ✅ CSRF protection verification
- ✅ Data size limit enforcement
- ✅ Malicious payload handling

#### Rate Limiting & Abuse Prevention
- ✅ Endpoint-specific rate limits
- ✅ Concurrent request handling
- ✅ IP-based blocking
- ✅ Account lockout enforcement
- ✅ Suspicious activity detection

#### Authentication Security
- ✅ Password strength validation
- ✅ Token security (generation, rotation, revocation)
- ✅ Session management
- ✅ Multi-device handling
- ✅ Security event logging

### Performance Tests (25+ test cases)

#### Response Time Benchmarks
- ✅ Quick assessment: <2 seconds
- ✅ User registration: <3 seconds
- ✅ Team creation: <2.5 seconds
- ✅ Insights generation: <5 seconds

#### Concurrent User Performance
- ✅ 10 concurrent users
- ✅ 50 concurrent requests
- ✅ Memory usage monitoring
- ✅ Database connection pooling
- ✅ Cache hit/miss ratios

#### Load Testing
- ✅ 10 concurrent users sustained load
- ✅ Error rate <5%
- ✅ Average response time <3 seconds
- ✅ System stability under load

## 📊 Test Reports

### Automated Report Generation

The test runner automatically generates comprehensive reports:

```json
{
  "execution_summary": {
    "start_time": "2024-01-28T12:00:00Z",
    "end_time": "2024-01-28T12:05:30Z",
    "total_duration": 330.5,
    "total_tests": 165,
    "successful_tests": 158,
    "failed_tests": 7,
    "success_rate": 0.958
  },
  "performance_summary": {
    "metrics": {...},
    "average_response_time": 1.2,
    "threshold_violations": 2
  },
  "security_summary": {
    "findings": [...],
    "total_findings": 5,
    "high_severity_findings": 1,
    "medium_severity_findings": 3,
    "low_severity_findings": 1
  }
}
```

### Report Files

Reports are automatically saved as:
- `onboarding_test_report_YYYYMMDD_HHMMSS.json`
- Includes detailed metrics, findings, and recommendations

## 🔍 Security Testing Focus

### Critical Security Tests

1. **Input Sanitization**
   - XSS prevention in all user input fields
   - HTML entity encoding verification
   - SQL injection pattern blocking
   - Command injection prevention

2. **Authentication Security**
   - Password complexity requirements
   - Token security (generation, rotation, revocation)
   - Session fixation prevention
   - Brute force protection

3. **Rate Limiting**
   - Endpoint-specific rate limits
   - IP-based throttling
   - Concurrent request handling
   - Distributed rate limiting (Redis)

4. **Data Protection**
   - PII masking in logs
   - Sensitive data encryption
   - Secure data transmission
   - Privacy compliance

## ⚡ Performance Optimization

### Key Performance Metrics

| Metric | Target | Acceptable Range |
|--------|--------|----------------|
| Quick Assessment Response | <2s | 0-3s |
| Registration Response | <3s | 0-5s |
| Insights Generation | <5s | 0-10s |
| Concurrent Users | 10+ | 5-50 |
| Error Rate | <5% | 0-10% |
| Memory Usage | <500MB | 200MB-1GB |

### Performance Optimization Techniques

1. **Database Optimization**
   - Connection pooling (40 connections)
   - Query result caching
   - Index optimization
   - Prepared statements

2. **Caching Strategy**
   - Redis-based session storage
   - Assessment result caching
   - API response caching
   - Cache invalidation policies

3. **Async Processing**
   - Non-blocking I/O operations
   - Background task processing
   - Event-driven architecture
   - Concurrent request handling

## 🔧 Test Maintenance

### Adding New Tests

1. **Create Test Class**
   ```python
   class TestNewFeature:
       """Test suite for new onboarding feature"""

       @pytest.fixture
       def client(self):
           return TestClient(app)

       def test_new_functionality(self, client):
           """Test new feature implementation"""
           response = client.post("/api/v1/onboarding/new-feature", json={})
           assert response.status_code == 200
   ```

2. **Update Test Runner**
   ```python
   # Add to functional_tests list in _run_functional_tests()
   functional_tests.append(("New Feature", self._test_new_feature_functionality))
   ```

3. **Update Documentation**
   - Add test case to this guide
   - Update test coverage metrics
   - Document any new configurations

### Test Data Management

#### Test Users
```python
@pytest.fixture
def test_user():
    """Create test user for testing"""
    return {
        "email": "test.user@psychsync.com",
        "password": "SecureTestPass123!@#",
        "full_name": "Test User"
    }
```

#### Mock Services
```python
@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for testing"""
    with patch('app.services.analytics_service.AnalyticsService') as mock:
        mock.return_value = AsyncMock()
        yield mock
```

### Test Environment Setup

#### Database Setup
```python
@pytest.fixture(scope="session")
async def test_database():
    """Set up test database"""
    # Create test database schema
    # Populate with test data
    yield
    # Cleanup
```

#### Redis Setup
```python
@pytest.fixture
def mock_redis():
    """Mock Redis for testing"""
    with patch('app.core.redis_client.get_redis_client') as mock:
        mock_client = AsyncMock()
        mock.return_value = mock_client
        yield mock_client
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Test Failures Due to Missing Dependencies
```bash
# Install missing dependencies
pip install pytest pytest-asyncio httpx
```

#### 2. Database Connection Issues
```bash
# Check database connection
python -c "from app.core.database import check_db_health; print(check_db_health())"
```

#### 3. Redis Connection Issues
```bash
# Check Redis connection
python -c "import redis; r=redis.Redis(); print(r.ping())"
```

#### 4. Import Errors
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Debug Mode

Run tests with detailed output:

```bash
# Run with verbose output
pytest tests/test_onboarding_functional.py -v -s

# Run with debugging
pytest tests/test_onboarding_functional.py -v -s --pdb
```

### Test Isolation

Ensure tests don't interfere with each other:

```python
# Use fixtures for test isolation
@pytest.fixture(autouse=True)
async def isolated_database():
    """Create isolated database for each test"""
    # Setup isolated test database
    yield
    # Cleanup
```

## 📈 Continuous Integration

### GitHub Actions Integration

Create `.github/workflows/onboarding-tests.yml`:

```yaml
name: Onboarding Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-onboarding:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.12"

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx

    - name: Run onboarding tests
      run: |
        export TESTING=true
        python tests/test_onboarding_test_runner.py

    - name: Upload test reports
      uses: actions/upload-artifact@v4
      with:
        name: onboarding-test-reports
        path: onboarding_test_report_*.json
        retention-days: 30
```

### Quality Gates

Set minimum quality thresholds:

- **Success Rate**: ≥90%
- **Performance**: All response times within thresholds
- **Security**: No high-severity vulnerabilities
- **Coverage**: ≥80% test coverage

## 📚 Best Practices

### Test Writing Guidelines

1. **Use Descriptive Names**
   ```python
   def test_quick_assessment_with_manager_role_and_communication_challenge(self):
       """Descriptive test name explaining the scenario"""
   ```

2. **Follow AAA Pattern**
   ```python
   def test_example(self):
       """Arrange, Act, Assert pattern"""
       # Arrange
       test_data = {"role": "manager"}

       # Act
       response = client.post("/api/v1/quick-assessment", json=test_data)

       # Assert
       assert response.status_code == 200
       assert response.json()["success"] is True
   ```

3. **Use Fixtures for Setup**
   ```python
   @pytest.fixture
   def authenticated_client():
       """Create authenticated test client"""
       # Setup authentication
       return client
   ```

4. **Test Edge Cases**
   ```python
   @pytest.mark.parametrize("invalid_data", [
       {"role": ""},  # Empty role
       {"challenge": None},  # None challenge
       {"team_size": "invalid"}  # Invalid team size
   ])
   def test_input_validation(self, invalid_data):
       """Test various invalid input scenarios"""
   ```

### Security Testing Guidelines

1. **Test All Input Vectors**
   - Form data
   - Query parameters
   - Headers
   - JSON payloads

2. **Verify Sanitization**
   - Check that malicious content is escaped
   - Verify no code execution
   - Confirm data integrity

3. **Test Security Controls**
   - Rate limiting
   - Input validation
   - Authentication checks
   - Authorization controls

### Performance Testing Guidelines

1. **Set Realistic Thresholds**
   - Based on production requirements
   - Consider user experience expectations
   - Account for system limitations

2. **Measure Key Metrics**
   - Response time
   - Throughput
   - Error rate
   - Resource usage

3. **Test Under Load**
   - Simulate realistic traffic patterns
   - Test concurrent users
   - Monitor system stability

## 🔄 Continuous Improvement

### Test Metrics Tracking

Track these metrics over time:
- Test execution time
- Success rate trends
- Performance degradation
- Security vulnerability trends
- Code coverage percentage

### Regular Reviews

- **Weekly**: Review test results and performance
- **Monthly**: Update test cases and thresholds
- **Quarterly**: Comprehensive test suite audit
- **Annually**: Review testing strategy and tools

### Test Suite Evolution

- **Add New Tests**: When new features are added
- **Update Existing Tests**: When functionality changes
- **Remove Obsolete Tests**: When features are deprecated
- **Refactor Tests**: Improve maintainability and readability

---

## 📞 Support

For questions or issues with the onboarding test suite:

1. **Check this guide** for common solutions
2. **Review test logs** for detailed error information
3. **Consult test source code** for implementation details
4. **Contact QA team** for complex issues

Remember: **Good tests are the foundation of reliable software!** 🚀
