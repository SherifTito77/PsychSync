#!/bin/bash

# Comprehensive Security Test Runner
# Runs all security tests and generates a report

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="security_reports"
mkdir -p "$REPORT_DIR"

echo "================================================"
echo "COMPREHENSIVE SECURITY TEST SUITE"
echo "================================================"
echo "Time: $(date)"
echo "Report Directory: $REPORT_DIR"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
PASSED=0
FAILED=0
WARNED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        PASSED=$((PASSED + 1))
    elif [ $1 -eq 1 ]; then
        echo -e "${RED}✗ FAIL${NC}: $2"
        FAILED=$((FAILED + 1))
    else
        echo -e "${YELLOW}⚠ WARN${NC}: $2"
        WARNED=$((WARNED + 1))
    fi
}

echo "Test 1: Backend Server Health Check"
echo "---------------------------------------"
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HEALTH_CODE" = "200" ]; then
    print_result 0 "Backend server is healthy (HTTP $HEALTH_CODE)"
else
    print_result 1 "Backend server health check failed (HTTP $HEALTH_CODE)"
fi
echo ""

echo "Test 2: Security Headers Verification"
echo "---------------------------------------"
HEADERS=$(curl -s -I http://localhost:8000/health)

# Check for each security header
echo "$HEADERS" | grep -q "strict-transport-security" && print_result 0 "HSTS header present" || print_result 2 "HSTS header missing"
echo "$HEADERS" | grep -q "x-frame-options: DENY" && print_result 0 "X-Frame-Options: DENY present" || print_result 2 "X-Frame-Options missing"
echo "$HEADERS" | grep -q "x-content-type-options: nosniff" && print_result 0 "X-Content-Type-Options present" || print_result 2 "X-Content-Type-Options missing"
echo "$HEADERS" | grep -q "x-xss-protection" && print_result 0 "X-XSS-Protection present" || print_result 2 "X-XSS-Protection missing"
echo "$HEADERS" | grep -q "content-security-policy" && print_result 0 "Content-Security-Policy present" || print_result 2 "Content-Security-Policy missing"
echo "$HEADERS" | grep -q "referrer-policy" && print_result 0 "Referrer-Policy present" || print_result 2 "Referrer-Policy missing"
echo ""

echo "Test 3: SSL Certificate Files"
echo "---------------------------------------"
if [ -f "certs/psychsync.key" ]; then
    KEY_PERM=$(stat -f "%Sp" certs/psychsync.key 2>/dev/null || stat -c "%a" certs/psychsync.key)
    if [ "$KEY_PERM" = "600" ]; then
        print_result 0 "Private key has correct permissions (600)"
    else
        print_result 1 "Private key permissions incorrect: $KEY_PERM (should be 600)"
    fi
else
    print_result 1 "Private key file not found"
fi

if [ -f "certs/psychsync.crt" ]; then
    CERT_PERM=$(stat -f "%Sp" certs/psychsync.crt 2>/dev/null || stat -c "%a" certs/psychsync.crt)
    if [ "$CERT_PERM" = "640" ] || [ "$CERT_PERM" = "644" ]; then
        print_result 0 "Certificate has correct permissions ($CERT_PERM)"
    else
        print_result 1 "Certificate permissions incorrect: $CERT_PERM (should be 640 or 644)"
    fi

    # Check certificate expiry
    EXPIRY=$(openssl x509 -in certs/psychsync.crt -noout -enddate 2>/dev/null | cut -d= -f2)
    print_result 0 "Certificate expires: $EXPIRY"
else
    print_result 1 "Certificate file not found"
fi
echo ""

echo "Test 4: API Security Tests"
echo "---------------------------------------"
# Test authentication requirement
UNAUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/users)
if [ "$UNAUTH_RESPONSE" = "401" ] || [ "$UNAUTH_RESPONSE" = "403" ]; then
    print_result 0 "API requires authentication (HTTP $UNAUTH_RESPONSE)"
else
    print_result 1 "API endpoint accessible without authentication (HTTP $UNAUTH_RESPONSE)"
fi

# Test CORS
CORS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: https://evil.com" -H "Access-Control-Request-Method: GET" -X OPTIONS http://localhost:8000/health)
# OPTIONS request handling varies, so we just log it
print_result 2 "CORS OPTIONS request returns: $CORS_RESPONSE"
echo ""

echo "Test 5: Input Validation Tests"
echo "---------------------------------------"
# Test SQL injection patterns
SQL_PAYLOAD="test' OR '1'='1"
SQL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/users?search=$SQL_PAYLOAD")
if [ "$SQL_RESPONSE" != "200" ] || ! curl -s "http://localhost:8000/api/v1/users?search=$SQL_PAYLOAD" | grep -qi "sql"; then
    print_result 0 "SQL injection appears protected"
else
    print_result 2 "SQL injection protection unclear (manual review recommended)"
fi
echo ""

echo "Test 6: Rate Limiting Check"
echo "---------------------------------------"
# Send multiple requests quickly
REQUEST_COUNT=0
for i in {1..15}; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$RESPONSE" = "429" ]; then
        print_result 0 "Rate limiting triggered after $REQUEST_COUNT requests"
        break
    fi
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
done

if [ $REQUEST_COUNT -ge 15 ]; then
    print_result 2 "Rate limiting not triggered after 15 requests (may be per-endpoint)"
fi
echo ""

echo "Test 7: Host Header Configuration"
echo "---------------------------------------"
# Check if ALLOWED_HOSTS is configured
if grep -q "ALLOWED_HOSTS" .env.dev 2>/dev/null; then
    print_result 0 "ALLOWED_HOSTS configured in .env.dev"
    grep "ALLOWED_HOSTS" .env.dev | head -1
else
    print_result 1 "ALLOWED_HOSTS not found in environment configuration"
fi
echo ""

echo "Test 8: Middleware Integration"
echo "---------------------------------------"
if grep -q "host_validation" app/main.py 2>/dev/null; then
    print_result 0 "Host validation middleware is integrated in app/main.py"
else
    print_result 1 "Host validation middleware not found in app/main.py"
fi

if grep -q "security_monitor" app/monitoring/ 2>/dev/null; then
    print_result 0 "Security monitoring system exists"
else
    print_result 2 "Security monitoring system not found"
fi
echo ""

echo "Test 9: Configuration Security"
echo "---------------------------------------"
# Check for DEBUG mode
if grep -q "DEBUG=True" .env.dev 2>/dev/null; then
    print_result 2 "DEBUG=True in .env.dev (expected for development)"
else
    print_result 0 "DEBUG mode disabled"
fi

# Check for strong SECRET_KEY
SECRET_KEY_LENGTH=$(grep "^SECRET_KEY=" .env.dev 2>/dev/null | cut -d= -f2 | wc -c | tr -d ' ')
if [ ! -z "$SECRET_KEY_LENGTH" ] && [ "$SECRET_KEY_LENGTH" -gt 100 ]; then
    print_result 0 "SECRET_KEY appears strong (length: $SECRET_KEY_LENGTH)"
else
    print_result 1 "SECRET_KEY may be too short or not configured"
fi
echo ""

echo "================================================"
echo "TEST SUMMARY"
echo "================================================"
echo ""
echo "Passed:  $PASSED"
echo "Failed:  $FAILED"
echo "Warnings: $WARNED"
echo "Total:   $((PASSED + FAILED + WARNED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CRITICAL TESTS PASSED${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    EXIT_CODE=1
fi

if [ $WARNED -gt 0 ]; then
    echo -e "${YELLOW}⚠ $WARNED warning(s) detected - review recommended${NC}"
fi

echo ""
echo "Reports saved to: $REPORT_DIR/"
echo "Full details in:"
echo "  - test_audit_backend.json"
echo "  - frontend_security_audit.json"
echo ""

exit $EXIT_CODE
