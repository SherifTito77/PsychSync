#!/bin/bash
# Quick chaos test runner script

echo "🔥 PSYCHSYNC CHAOS TESTING SUITE"
echo "=================================="
echo ""
echo "Running resilience tests..."
echo ""

# Run tests with nice formatting
python -m pytest tests/chaos/test_system_boundary_resilience.py \
    -v \
    --tb=short \
    --cov=app.core.resilience \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/chaos \
    2>&1 | tee test_results.log

# Extract summary
echo ""
echo "=================================="
echo "TEST SUMMARY"
echo "=================================="
grep -E "passed|failed|error" test_results.log | tail -5

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All chaos tests completed successfully!"
    echo "📊 Coverage report: htmlcov/chaos/index.html"
else
    echo ""
    echo "⚠️  Some tests failed - check test_results.log for details"
fi

echo ""
echo "Next steps:"
echo "1. Review test results above"
echo "2. Check coverage report: htmlcov/chaos/index.html"
echo "3. Run specific tests: pytest tests/chaos/test_system_boundary_resilience.py::TestCircuitBreakerResilience -v"
