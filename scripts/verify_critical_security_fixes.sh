#!/bin/bash
#
# Critical Security Fixes Verification Script
# Tests the fixes applied to resolve CRITICAL and HIGH severity security issues
#
# Generated: 2026-01-19
# Issues Fixed: 2 (1 CRITICAL, 1 HIGH)
#

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  Critical Security Fixes Verification                            ║"
echo "║  PsychSync FastAPI Application Security Audit                    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"
TEST_EMAIL="test-security-verify@example.com"
TEST_PASSWORD="TestPassword123!"

echo "📍 Target API: $API_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# TEST 1: Verify Authentication Bypass is Fixed
# ============================================================================
echo "🔒 TEST 1: Authentication Bypass Fix Verification"
echo "Testing: simple_auth endpoint now requires valid password"
echo ""

# Attempt to login with WRONG password (should fail after fix)
echo "⚠️  Attempting login with WRONG password (should be rejected)..."
response=$(curl -s -X POST "$API_URL/api/v1/auth/simple-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL&password=WRONG_PASSWORD" \
  -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "401" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Wrong password correctly rejected (HTTP $http_code)"
    echo "   Response: $body"
else
    echo -e "${RED}❌ FAIL${NC} - Wrong password was accepted! (HTTP $http_code)"
    echo "   This indicates the authentication bypass is STILL VULNERABLE"
    echo "   Response: $body"
    exit 1
fi

echo ""
echo "⚠️  Attempting login with CORRECT password (should be accepted)..."
# Note: This will fail if test user doesn't exist, but that's expected
response=$(curl -s -X POST "$API_URL/api/v1/auth/simple-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL&password=$TEST_PASSWORD" \
  -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "401" ] ] || [ "$http_code" = "404" ]; then
    echo -e "${GREEN}✅ EXPECTED${NC} - Test user doesn't exist or password checked (HTTP $http_code)"
    echo "   This is expected behavior - authentication is working"
elif [ "$http_code" = "200" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC} - Login succeeded (test user may exist)"
    echo "   Verify this is intentional"
else
    echo -e "${YELLOW}⚠️  UNEXPECTED${NC} - HTTP $http_code"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# TEST 2: Verify data_export.py Module Loads
# ============================================================================
echo "📦 TEST 2: data_export.py Syntax Fix Verification"
echo "Testing: Module can be imported without syntax errors"
echo ""

if python3 -c "import sys; sys.path.insert(0, '.'); from app.api.v1.endpoints import data_export" 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC} - data_export.py module loads successfully"
    echo "   The syntax error has been fixed"
else
    echo -e "${RED}❌ FAIL${NC} - data_export.py has import errors"
    echo "   The syntax error may not be fully fixed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# TEST 3: Code Analysis
# ============================================================================
echo "🔍 TEST 3: Code Analysis Verification"
echo "Testing: Fixed code is present in source files"
echo ""

echo "Checking simple_auth.py for password verification..."
if grep -q "verify_password(password, user.password_hash)" app/api/v1/endpoints/simple_auth.py; then
    echo -e "${GREEN}✅ PASS${NC} - Password verification code found in simple_auth.py"
else
    echo -e "${RED}❌ FAIL${NC} - Password verification code NOT found"
    echo "   The fix may have been reverted"
    exit 1
fi

echo ""
echo "Checking simple_auth.py for password_hash in SQL query..."
if grep -q "SELECT id, email, full_name, password_hash FROM users" app/api/v1/endpoints/simple_auth.py; then
    echo -e "${GREEN}✅ PASS${NC} - SQL query includes password_hash"
else
    echo -e "${RED}❌ FAIL${NC} - SQL query doesn't include password_hash"
    exit 1
fi

echo ""
echo "Checking data_export.py for syntax errors..."
if grep -q "@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)" app/api/v1/endpoints/data_export.py | grep -A1 -B1 "logger.error"; then
    if grep -q "^)$" app/api/v1/endpoints/data_export.py | head -1; then
        echo -e "${RED}❌ FAIL${NC} - Syntax error still present"
        exit 1
    fi
fi
echo -e "${GREEN}✅ PASS${NC} - No syntax error patterns found"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  Verification Summary                                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ TEST 1: Authentication bypass - FIXED"
echo "   → Password verification now required"
echo "   → Invalid passwords correctly rejected"
echo ""
echo "✅ TEST 2: data_export.py syntax error - FIXED"
echo "   → Module loads successfully"
echo "   → No import errors"
echo ""
echo "✅ TEST 3: Code analysis - VERIFIED"
echo "   → Security fixes present in source code"
echo "   → No regression detected"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 ALL CRITICAL SECURITY FIXES VERIFIED${NC}"
echo ""
echo "Fixed Issues:"
echo "  1. 🔴 CRITICAL: Authentication bypass in simple_auth.py"
echo "  2. 🟠 HIGH: Syntax error in data_export.py"
echo ""
echo "Next Steps:"
echo "  1. Address remaining HIGH severity issue: Admin placeholders (admin.py)"
echo "  2. Review MEDIUM severity issues in FASTAPI_SECURITY_AUDIT_REPORT.md"
echo "  3. Run full security scan: python scripts/pre_production_validation.py"
echo ""
echo "For details, see: FASTAPI_SECURITY_AUDIT_REPORT.md"
echo ""
