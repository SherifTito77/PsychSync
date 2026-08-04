# Regression Testing Quick Start Guide

## Overview

This guide provides quick instructions for running the PsychSync regression test suites.

## Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Key dependencies:
# - pytest >= 7.4.0
# - pytest-asyncio >= 0.21.0
# - pytest-cov >= 4.1.0
# - httpx >= 0.24.0
# - faker >= 18.0.0
# - memory-profiler >= 0.61.0 (for performance tests)
```

## Test Structure

```
tests/
├── api/                              # API endpoint regression tests
│   ├── test_regression_auth.py       # Authentication endpoints (P0)
│   ├── test_regression_assessments.py # Assessment endpoints (P0)
│   └── test_regression_responses.py  # Response endpoints (P0)
├── services/                         # Service layer regression tests
│   └── test_regression_response_service.py (P0)
├── performance/                      # Performance & load tests
│   └── test_load_critical_endpoints.py (P1)
├── security/                         # Security regression tests
│   └── test_input_validation_regression.py (P0)
├── integration/                      # Existing integration tests
└── conftest.py                       # Test configuration & fixtures
```

## Running Tests

### All Regression Tests

```bash
# Run all regression tests
pytest tests/api/test_regression_*.py \
       tests/services/test_regression_*.py \
       tests/security/test_input_validation_regression.py \
       -v

# With coverage
pytest tests/ -k "regression" \
       --cov=app \
       --cov-report=html \
       --cov-report=term \
       -v
```

### By Category

```bash
# API Tests Only
pytest tests/api/test_regression_*.py -v

# Service Tests Only
pytest tests/services/test_regression_*.py -v

# Security Tests Only
pytest tests/security/test_input_validation_regression.py -v

# Performance Tests Only
pytest tests/performance/test_load_critical_endpoints.py -v
```

### By Priority

```bash
# P0 (Critical) Tests Only
pytest tests/ -m "P0" -v

# P1 (High) Tests Only
pytest tests/ -m "P1" -v

# All Tests
pytest tests/ -m "P0 or P1" -v
```

### By Test Class

```bash
# Authentication Tests
pytest tests/api/test_regression_auth.py::TestAuthLoginRegression -v

# Assessment Tests
pytest tests/api/test_regression_assessments.py::TestAssessmentCRUDRegression -v

# SQL Injection Tests
pytest tests/security/test_input_validation_regression.py::TestSQLInjectionRegression -v
```

### Specific Tests

```bash
# Single test
pytest tests/api/test_regression_auth.py::TestAuthLoginRegression::test_login_success_valid_credentials -v

# Tests matching pattern
pytest tests/ -k "login" -v

# Tests in specific file
pytest tests/api/test_regression_auth.py -v
```

## Test Execution Examples

### Quick Smoke Test (P0 only)

```bash
# Run only P0 tests (fastest feedback)
pytest tests/ -m "P0" --maxfail=5 -x
```

### Full Regression Suite

```bash
# Complete regression with coverage
pytest tests/api/test_regression_*.py \
       tests/services/test_regression_*.py \
       tests/security/test_input_validation_regression.py \
       --cov=app \
       --cov-report=html \
       --cov-report=xml \
       --cov-report=term-missing \
       -v \
       --tb=short \
       --durations=10
```

### Parallel Execution (faster)

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto-detect CPU count)
pytest tests/ -n auto -v

# Specify worker count
pytest tests/ -n 4 -v
```

### Performance Tests Only

```bash
# Run performance tests (slower)
pytest tests/performance/ -v -s

# With memory profiling
python -m memory_profiler pytest tests/performance/test_load_critical_endpoints.py -v
```

### Security Tests Only

```bash
# Run all security tests
pytest tests/security/test_input_validation_regression.py -v

# SQL Injection tests
pytest tests/security/test_input_validation_regression.py::TestSQLInjectionRegression -v

# XSS tests
pytest tests/security/test_input_validation_regression.py::TestXSSRegression -v
```

## Viewing Results

### Console Output

```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -v -s

# Show slowest tests
pytest tests/ --durations=10
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Terminal coverage summary
pytest tests/ --cov=app --cov-report=term-missing
```

### JUnit XML (for CI/CD)

```bash
# Generate JUnit XML report
pytest tests/ --junitxml=test-results.xml

# With coverage
pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Regression Tests

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
      - name: Run P0 tests
        run: |
          pytest tests/ -m "P0" --maxfail=5 -x
      - name: Run full regression with coverage
        run: |
          pytest tests/api/test_regression_*.py \
                 tests/services/test_regression_*.py \
                 tests/security/test_input_validation_regression.py \
                 --cov=app \
                 --cov-report=xml \
                 --cov-report=term
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Ensure test database is configured
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export TESTING="True"

# Or use .env.test file
cp .env.test .env
```

#### 2. Import Errors

```bash
# Ensure app is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/psychsync
pytest tests/
```

#### 3. Async Test Errors

```bash
# Ensure pytest-asyncio is configured
cat >> pytest.ini << EOF
[pytest]
asyncio_mode = auto
EOF
```

#### 4. Redis Connection Errors

```bash
# Start Redis for tests
redis-server --port 6379

# Or skip Redis tests
pytest tests/ -v -p no:warnings
```

### Debugging Failed Tests

```bash
# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Drop into debugger on failure
pytest tests/ --pdb

# Show full traceback
pytest tests/ --tb=long

# Run last failed tests
pytest tests/ --lf

# Run failed tests first
pytest tests/ --ff
```

## Test Markers Reference

```bash
# List all markers
pytest --markers

# Output:
# P0: Critical tests (must pass)
# P1: High-priority tests
# P2: Medium-priority tests
# unit: Unit tests
# integration: Integration tests
# security: Security tests
# performance: Performance tests
```

## Custom Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    P0: Critical tests (must pass)
    P1: High-priority tests
    P2: Medium-priority tests
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    performance: Performance tests
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
```

### .coveragerc

```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

## Performance Baselines

Current performance targets (to be updated after initial runs):

- **Login**: p95 < 2s (100 concurrent)
- **Assessment List**: p95 < 500ms (100 concurrent)
- **Response Submit**: p95 < 1s (50 concurrent)

## Next Steps

1. **Initial Run**: Execute all tests and establish baselines
2. **Fix Failures**: Address any failing P0 tests
3. **Measure Coverage**: Ensure > 85% coverage
4. **Set Baselines**: Document performance baselines
5. **CI Integration**: Configure automated test execution
6. **Maintenance**: Review and update tests quarterly

## Support

For issues or questions:
- See: `/docs/TESTING_REGRESSION_SUITE_DESIGN.md`
- Check: `tests/conftest.py` for fixture documentation
- Review: Test docstrings for specific requirements
