# Team Assessment Creation Test Suite

This directory contains comprehensive test cases for validating team assessment creation functionality in the PsychSync SaaS platform.

## 📋 Test Suite Overview

### 🚀 Automated Tests
- **File**: `test_team_assessment_creation.py`
- **Framework**: pytest + FastAPI TestClient
- **Coverage**: Unit tests, integration tests, performance tests, security tests

### 🔧 Manual Tests
- **File**: `test_team_assessment_creation_manual.py`
- **Tools**: curl, Postman, or any API testing tool
- **Coverage**: Step-by-step manual testing procedures

## 🧪 Test Categories

### 1. **Happy Path Tests**
- ✅ Successful assessment creation with valid data
- ✅ Assessment creation with questions and sections
- ✅ Team assignment functionality
- ✅ Assessment retrieval and updates

### 2. **Authorization & Permissions**
- ✅ Admin user access (full permissions)
- ✅ Team lead access (limited permissions)
- ✅ Regular user restrictions (no assessment creation)
- ✅ Unauthenticated access rejection

### 3. **Data Validation & Business Rules**
- ✅ Required field validation
- ✅ Data type validation
- ✅ Business rule enforcement
- ✅ Edge case handling

### 4. **Error Handling & Edge Cases**
- ✅ Invalid data rejection
- ✅ Error response formatting
- ✅ Database constraint violations
- ✅ Concurrent modification handling

### 5. **Performance & Security**
- ✅ Response time benchmarks
- ✅ Large content handling
- ✅ SQL injection protection
- ✅ XSS prevention
- ✅ Rate limiting validation

### 6. **Database Operations**
- ✅ Data persistence verification
- ✅ Cascade operation testing
- ✅ Transaction integrity
- ✅ Constraint validation

## 🚀 Quick Start

### Prerequisites
1. **FastAPI Server**: `uvicorn app.main:app --reload`
2. **Database**: PostgreSQL with test data
3. **Authentication**: Valid user tokens for different roles
4. **Dependencies**: `pip install pytest httpx`

### Running Automated Tests
```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/test_team_assessment_creation.py -v

# Run specific test class
python -m pytest tests/test_team_assessment_creation.py::TestHappyPaths -v

# Run with coverage
python -m pytest tests/test_team_assessment_creation.py --cov=app --cov-report=html

# Run performance tests only
python -m pytest tests/test_team_assessment_creation.py::TestTeamAssessmentPerformanceBenchmarks -v -m performance
```

### Manual Testing Setup
```bash
# 1. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Run manual test generator
python tests/test_team_assessment_creation_manual.py

# 3. Follow the generated curl commands
# 4. Replace YOUR_ACCESS_TOKEN with actual token
```

## 📊 Test Data Structure

### Sample Assessment Data
```json
{
  "title": "Team Performance Assessment Q1 2024",
  "description": "Quarterly team performance assessment",
  "assessment_type": "team_performance",
  "category": "performance",
  "is_active": true,
  "instructions": "Complete this assessment honestly...",
  "estimated_duration_minutes": 45,
  "deadline": "2024-12-15T23:59:59Z",
  "max_attempts": 3,
  "is_anonymous": false,
  "requires_proctoring": false,
  "configuration": {
    "scoring_algorithm": "weighted_average",
    "passing_score": 70,
    "show_results_immediately": true
  },
  "sections": [
    {
      "title": "Technical Skills",
      "description": "Evaluate technical competencies",
      "order": 1,
      "is_required": true,
      "weight": 0.5,
      "questions": [
        {
          "question_text": "Rate your database proficiency",
          "question_type": "rating",
          "options": ["1 - Beginner", "2 - Novice", "3 - Intermediate", "4 - Advanced", "5 - Expert"],
          "required": true,
          "order": 1,
          "weight": 1.0
        }
      ]
    }
  ]
}
```

## 🔐 Authentication Setup

### Create Test Users
```bash
# Create Admin User
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "AdminTest123!",
    "full_name": "Test Admin"
  }'

# Login to Get Token
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@test.com&password=AdminTest123!"
```

### Expected Token Response
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "admin@test.com",
      "full_name": "Test Admin"
    }
  }
}
```

## 📝 Test Case Matrix

| Test ID | Category | Description | Priority |
|---------|----------|-------------|---------|
| TC-001 | Happy Path | Valid assessment creation | **High** |
| TC-002 | Happy Path | Assessment with questions | **High** |
| TC-003 | Authorization | Admin user access | **High** |
| TC-004 | Authorization | Team lead access | **Medium** |
| TC-005 | Authorization | Regular user restrictions | **High** |
| TC-006 | Validation | Empty title rejection | **High** |
| TC-007 | Validation | Invalid assessment type | **High** |
| TC-008 | Validation | Negative duration | **Medium** |
| TC-009 | Validation | Past deadline | **Medium** |
| TC-010 | Error Handling | Malformed JSON | **Medium** |
| TC-011 | Security | SQL injection protection | **Critical** |
| TC-012 | Security | XSS prevention | **Critical** |
| TC-013 | Performance | Large content handling | **Medium** |
| TC-014 | Performance | Response time benchmark | **Medium** |
| TC-015 | Database | Data persistence | **High** |
| TC-016 | Database | Cascade operations | **Medium** |
| TC-017 | Integration | Complete workflow | **High** |

## 🎯 Test Scenarios

### Scenario 1: Team Assessment Creation Workflow
1. **Admin** creates assessment with multiple sections
2. **Admin** assigns assessment to specific team
3. **Team members** receive notification
4. **Team members** complete assessment
5. **Admin** reviews aggregated results

### Scenario 2: Multi-Role Assessment Access
1. **Regular User** tries to create assessment → **403 Forbidden**
2. **Team Lead** creates assessment for their team → **201 Created**
3. **Admin** creates assessment for any team → **201 Created**
4. **Unauthorized** user tries to create assessment → **401 Unauthorized**

### Scenario 3: Assessment Data Validation
1. **Required Fields**: Title, description, type validation
2. **Business Rules**: Future deadlines, positive durations
3. **Security**: Input sanitization, SQL injection prevention
4. **Performance**: Size limits, response time constraints

## 📈 Expected Results

### Success Criteria
- ✅ All tests pass with 100% success rate
- ✅ Response times under 2 seconds for single requests
- ✅ Large content handled efficiently (<5 seconds)
- ✅ Security tests prevent all injection attempts
- ✅ Database operations maintain data integrity

### Performance Benchmarks
- **Single Assessment Creation**: < 500ms
- **Assessment with Questions**: < 1 second
- **Large Content Assessment**: < 5 seconds
- **Bulk Operations**: < 30 seconds for 10 assessments

### Security Validation
- **SQL Injection**: All attempts blocked or sanitized
- **XSS Prevention**: Scripts removed or escaped
- **Authorization**: Proper role-based access control
- **Rate Limiting**: Request throttling enforced

## 🐛 Debugging Common Issues

### Test Failures
```bash
# Check server logs
tail -f logs/app.log

# Verify database connection
python scripts/db_healthcheck.py

# Check authentication
curl -X GET "http://localhost:8000/health"
```

### Common Error Codes
- **400 Bad Request**: Invalid data format
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **422 Validation Error**: Data validation failure
- **500 Internal Error**: Server error

## 🔄 Continuous Integration

### GitHub Actions Workflow
```yaml
name: Team Assessment Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install -r requirements-test.txt
          pip install pytest httpx
      - name: Run tests
        run: |
          python -m pytest tests/test_team_assessment_creation.py -v --cov=app
```

### Local CI/CD Pipeline
```bash
#!/bin/bash
# Run test suite
echo "Running Team Assessment Tests..."

# Environment setup
source .venv/bin/activate

# Run automated tests
python -m pytest tests/test_team_assessment_creation.py -v --tb=short

# Run performance benchmarks
python -m pytest tests/test_team_assessment_creation.py::TestTeamAssessmentPerformanceBenchmarks -v -m performance

# Generate coverage report
python -m pytest tests/test_team_assessment_creation.py --cov=app --cov-report=html --cov-report=term-missing

echo "Test suite completed successfully!"
```

## 📚 Additional Resources

### API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### Testing Tools
- **Postman**: API testing with collections
- **Insomnia**: REST client for API testing
- **HTTPie**: Command-line HTTP client
- **curl**: Basic HTTP requests

### Monitoring & Debugging
- **Server Logs**: Check application logs for errors
- **Database Logs**: Monitor database operations
- **Network Traffic**: Use tools like Wireshark for HTTP debugging

---

## 📞 Support

For questions or issues with the test suite:
1. Check existing test cases for similar scenarios
2. Review API documentation for correct endpoints
3. Verify server and database status
4. Check authentication and authorization setup