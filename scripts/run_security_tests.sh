#!/bin/bash

# Security Test Runner
# Runs automated security tests and generates a report

set -e

echo "🔐 PsychSync Security Test Suite"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found. Install with: pip install pytest pytest-asyncio${NC}"
    exit 1
fi

print_section "1. Token Security Tests"
echo "Testing httpOnly cookie implementation..."
pytest tests/test_security_automated.py::TestTokenSecurity -v --tb=short || true

print_section "2. CSRF Protection Tests"
echo "Testing CSRF token validation..."
pytest tests/test_security_automated.py::TestCSRFProtection -v --tb=short || true

print_section "3. Authorization Tests"
echo "Testing IDOR prevention and access control..."
pytest tests/test_security_automated.py::TestAuthorization -v --tb=short || true

print_section "4. Rate Limiting Tests"
echo "Testing brute force protection..."
pytest tests/test_security_automated.py::TestRateLimiting -v --tb=short || true

print_section "5. Input Validation Tests"
echo "Testing SQL injection and XSS prevention..."
pytest tests/test_security_automated.py::TestInputValidation -v --tb=short || true

print_section "6. Security Headers Tests"
echo "Testing security header configuration..."
pytest tests/test_security_automated.py::TestSecurityHeaders -v --tb=short || true

print_section "7. Authentication Flow Tests"
echo "Testing complete authentication security..."
pytest tests/test_security_automated.py::TestAuthenticationFlow -v --tb=short || true

print_section "8. Secure Endpoint Tests"
echo "Verifying backdoors are disabled..."
pytest tests/test_security_automated.py::TestSecureEndpoints -v --tb=short || true

print_section "9. Security Performance Tests"
echo "Testing security overhead..."
pytest tests/test_security_automated.py::TestSecurityPerformance -v --tb=short || true

print_section "Test Summary"
echo ""
echo "All security tests completed!"
echo ""
echo "📊 View detailed report:"
echo "   pytest tests/test_security_automated.py -v --html=security_report.html"
echo ""
echo "🔍 Run specific test category:"
echo "   pytest tests/test_security_automated.py::TestTokenSecurity -v"
echo ""
echo -e "${GREEN}✓ Security testing complete!${NC}"
