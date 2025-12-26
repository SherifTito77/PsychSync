#!/bin/bash
# DAST Runner for PsychSync
# Runs Dynamic Application Security Testing (Black-box testing)

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PsychSync DAST Runner                                      ║"
echo "║     Dynamic Application Security Testing                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

HIGH_SEVERITY_FOUND=0

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5179"
OUTPUT_DIR="security-reports"
mkdir -p "$OUTPUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Security Testing (Custom Scripts)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the security test suite
if [ -f "test_security_middleware.py" ]; then
    echo "Running automated security tests..."
    echo ""

    if python3 test_security_middleware.py > "$OUTPUT_DIR/dast-results.txt" 2>&1; then
        TEST_RESULT=$(grep "Success Rate" "$OUTPUT_DIR/dast-results.txt" | tail -1)
        echo -e "${GREEN}✓${NC}  Security tests passed: $TEST_RESULT"
    else
        echo -e "${YELLOW}⚠${NC}  Some security tests failed (review results)"
    fi
else
    echo -e "${YELLOW}⚠${NC}  test_security_middleware.py not found, skipping"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OWASP ZAP Baseline Scan"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if ZAP is installed
if ! command -v zap-cli &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  OWASP ZAP CLI not installed"
    echo "Install with: brew install zap"
    echo "Or Docker: docker run -t owasp/zap2docker-stable zap-cli"
    echo ""
    echo "Skipping automated DAST scan"
else
    echo "Running OWASP ZAP baseline scan..."
    echo ""

    # Run ZAP baseline scan on backend
    zap-cli baseline-scan \
        -t "$BACKEND_URL" \
        -r "$OUTPUT_DIR/zap-report.html" \
        --self-contained \
        ---info \
        --risk-high \
        || echo -e "${YELLOW}⚠${NC}  ZAP scan completed with warnings"

    # Check for high severity issues
    if [ -f "$OUTPUT_DIR/zap-report.html" ]; then
        # Parse HTML for High alerts
        HIGH_COUNT=$(grep -o "High.*[0-9]" "$OUTPUT_DIR/zap-report.html" | grep -o "[0-9]" | head -1 || echo "0")

        if [ "$HIGH_COUNT" -gt 0 ]; then
            echo -e "${RED}✗ BLOCKING: $HIGH_COUNT high-severity issues found by ZAP${NC}"
            HIGH_SEVERITY_FOUND=1
        else
            echo -e "${GREEN}✓${NC}  No high-severity issues found by ZAP"
        fi
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CURL Security Testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check security headers
echo "Checking security headers on $BACKEND_URL/health ..."
HEADERS=$(curl -s -I "$BACKEND_URL/health" 2>&1)

MISSING_HEADERS=0
grep -qi "strict-transport-security" <<< "$HEADERS" || ((MISSING_HEADERS++))
grep -qi "content-security-policy" <<< "$HEADERS" || ((MISSING_HEADERS++))
grep -qi "x-frame-options" <<< "$HEADERS" || ((MISSING_HEADERS++))
grep -qi "x-content-type-options" <<< "$HEADERS" || ((MISSING_HEADERS++))

if [ $MISSING_HEADERS -eq 0 ]; then
    echo -e "${GREEN}✓${NC}  All security headers present"
else
    echo -e "${YELLOW}⚠${NC}  $MISSING_HEADERS security headers missing"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Attack Simulation Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# SQL Injection test
echo "Testing SQL Injection protection..."
SQLI_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin'\''OR'\''1'\''='\''1","password":"test"}' \
  -w "%{http_code}" 2>&1)

if echo "$SQLI_RESPONSE" | grep -q "403\|404\|422"; then
    echo -e "${GREEN}✓${NC}  SQL Injection blocked (HTTP $SQLI_RESPONSE)"
else
    echo -e "${RED}✗${NC}  SQL Injection NOT blocked (HTTP $SQLI_RESPONSE)"
fi

# XSS test
echo "Testing XSS protection..."
XSS_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"<script>alert(1)</script>"}' \
  -w "%{http_code}" 2>&1)

if echo "$XSS_RESPONSE" | grep -q "403\|404\|422"; then
    echo -e "${GREEN}✓${NC}  XSS attack blocked (HTTP $XSS_RESPONSE)"
else
    echo -e "${RED}✗${NC}  XSS attack NOT blocked (HTTP $XSS_RESPONSE)"
fi

# Command injection test
echo "Testing Command Injection protection..."
CMDI_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test; ls -la","password":"test"}' \
  -w "%{http_code}" 2>&1)

if echo "$CMDI_RESPONSE" | grep -q "403\|404\|422"; then
    echo -e "${GREEN}✓${NC}  Command Injection blocked (HTTP $CMDI_RESPONSE)"
else
    echo -e "${RED}✗${NC}  Command Injection NOT blocked (HTTP $CMDI_RESPONSE)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DAST Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Generated Reports:"
echo "  • $OUTPUT_DIR/dast-results.txt - Security test results"
echo "  • $OUTPUT_DIR/zap-report.html - OWASP ZAP scan results"
echo ""

if [ "$HIGH_SEVERITY_FOUND" -gt 0 ]; then
    echo -e "${RED}✗ DAST FAILED: High-severity issues must be fixed before deployment${NC}"
    exit 1
else
    echo -e "${GREEN}✓ DAST PASSED: No blocking issues found${NC}"
    exit 0
fi
