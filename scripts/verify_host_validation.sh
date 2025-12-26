#!/bin/bash

# Host Validation Middleware Verification Script
# Verifies that the Host header validation middleware is working correctly

echo "================================================"
echo "HOST VALIDATION MIDDLEWARE VERIFICATION"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="http://localhost:8000"
HEALTH_ENDPOINT="$BASE_URL/health"

echo "Target: $BASE_URL"
echo "Time: $(date)"
echo ""

# Check if server is running
echo "Step 1: Checking if server is running..."
echo "-------------------------------------------"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null)

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✓ Server is running (HTTP $HEALTH_CHECK)${NC}"
else
    echo -e "${RED}✗ Server is not responding (HTTP $HEALTH_CHECK)${NC}"
    echo ""
    echo "Please start the server first:"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    exit 1
fi
echo ""

# Test valid hosts
echo "Step 2: Testing VALID hosts (should return 200)"
echo "---------------------------------------------------"

VALID_HOSTS=(
    "localhost:8000"
    "127.0.0.1:8000"
    "0.0.0.0:8000"
)

VALID_PASSED=0
VALID_TOTAL=${#VALID_HOSTS[@]}

for host in "${VALID_HOSTS[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $host" "$HEALTH_ENDPOINT")
    if [ "$RESPONSE" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $host → HTTP $RESPONSE"
        VALID_PASSED=$((VALID_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $host → HTTP $RESPONSE (expected 200)"
    fi
done
echo ""

# Test invalid hosts
echo "Step 3: Testing INVALID hosts (should return 400)"
echo "---------------------------------------------------"

INVALID_HOSTS=(
    "evil.com"
    "attacker.com"
    "malicious-site.com"
    "totally-legit-domain.com"
)

INVALID_PASSED=0
INVALID_TOTAL=${#INVALID_HOSTS[@]}

for host in "${INVALID_HOSTS[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $host" "$HEALTH_ENDPOINT")
    if [ "$RESPONSE" = "400" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $host → HTTP $RESPONSE (correctly rejected)"
        INVALID_PASSED=$((INVALID_PASSED + 1))
    elif [ "$RESPONSE" = "200" ]; then
        echo -e "${RED}✗ FAIL${NC}: $host → HTTP $RESPONSE (should be rejected!)"
        echo -e "  ${YELLOW}⚠ Middleware not active - restart server?${NC}"
    else
        echo -e "${YELLOW}⚠ UNKNOWN${NC}: $host → HTTP $RESPONSE"
    fi
done
echo ""

# Test suspicious patterns
echo "Step 4: Testing SUSPICIOUS patterns (should return 400)"
echo "--------------------------------------------------------"

SUSPICIOUS_HOSTS=(
    "payload.evil.com"
    "xss.example.com"
    "<script>.com"
    "javascript:void(0).com"
)

SUSPICIOUS_PASSED=0
SUSPICIOUS_TOTAL=${#SUSPICIOUS_HOSTS[@]}

for host in "${SUSPICIOUS_HOSTS[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $host" "$HEALTH_ENDPOINT")
    if [ "$RESPONSE" = "400" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $host → HTTP $RESPONSE (correctly blocked)"
        SUSPICIOUS_PASSED=$((SUSPICIOUS_PASSED + 1))
    elif [ "$RESPONSE" = "200" ]; then
        echo -e "${RED}✗ FAIL${NC}: $host → HTTP $RESPONSE (suspicious pattern not detected!)"
        echo -e "  ${YELLOW}⚠ Middleware not active - restart server?${NC}"
    else
        echo -e "${YELLOW}⚠ UNKNOWN${NC}: $host → HTTP $RESPONSE"
    fi
done
echo ""

# Summary
echo "================================================"
echo "VERIFICATION SUMMARY"
echo "================================================"
echo ""
echo "Valid Hosts Test:     $VALID_PASSED/$VALID_TOTAL passed"
echo "Invalid Hosts Test:   $INVALID_PASSED/$INVALID_TOTAL passed"
echo "Suspicious Patterns:   $SUSPICIOUS_PASSED/$SUSPICIOUS_TOTAL passed"
echo ""
echo "Total: $((VALID_PASSED + INVALID_PASSED + SUSPICIOUS_PASSED))/$((VALID_TOTAL + INVALID_TOTAL + SUSPICIOUS_TOTAL)) passed"
echo ""

# Overall result
TOTAL_PASSED=$((VALID_PASSED + INVALID_PASSED + SUSPICIOUS_PASSED))
TOTAL_TESTS=$((VALID_TOTAL + INVALID_TOTAL + SUSPICIOUS_TOTAL))

if [ $TOTAL_PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}✓ HOST VALIDATION MIDDLEWARE IS WORKING!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "The middleware is correctly:"
    echo "  ✓ Accepting valid hosts (localhost, 127.0.0.1)"
    echo "  ✓ Rejecting invalid hosts (evil.com, attacker.com)"
    echo "  ✓ Blocking suspicious patterns"
    echo ""
    echo "Your application is protected from DNS rebinding attacks!"
    echo ""
    exit 0
elif [ $INVALID_PASSED -eq 0 ] && [ $SUSPICIOUS_PASSED -eq 0 ]; then
    echo -e "${YELLOW}================================================${NC}"
    echo -e "${YELLOW}⚠ MIDDLEWARE MAY NOT BE ACTIVE${NC}"
    echo -e "${YELLOW}================================================${NC}"
    echo ""
    echo "The middleware is rejecting requests, but not as expected."
    echo ""
    echo "Possible causes:"
    echo "  1. Server not restarted after integrating middleware"
    echo "  2. ALLOWED_HOSTS not configured correctly"
    echo "  3. Middleware configuration issue"
    echo ""
    echo "Next steps:"
    echo "  1. Restart the backend server"
    echo "  2. Verify ALLOWED_HOSTS in .env.dev"
    echo "  3. Check server logs for errors"
    echo ""
    exit 1
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}✗ HOST VALIDATION NOT WORKING${NC}"
    echo -e "${RED}================================================${NC}"
    echo ""
    echo "Invalid hosts are being accepted (HTTP 200)."
    echo ""
    echo "The middleware code is integrated but not active."
    echo ""
    echo "TO FIX:"
    echo "  1. Stop the current server (Ctrl+C in terminal)"
    echo "  2. Restart server: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo "  3. Run this verification script again"
    echo ""
    echo "For detailed debugging, check the server logs for middleware initialization."
    echo ""
    exit 2
fi
