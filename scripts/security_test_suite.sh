#!/bin/bash

# PsychSync Security Testing Suite
# Tests for common security vulnerabilities and misconfigurations
# ⚠️  ONLY use on systems you own or have explicit permission to test

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     PsychSync Security Testing Suite                         ║"
echo "║     ⚠️  Only test on systems you own/have permission        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

BASE_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:5174}"

echo "📍 Target: $BASE_URL"
echo "📍 Frontend: $FRONTEND_URL"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0
WARNINGS=0

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ═════════════════════════════════════════════════════════════════════
# TEST 1: HTTP Security Headers
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 1: HTTP Security Headers"

HEADERS=$(curl -s -I "$BASE_URL/api/v1/health" 2>/dev/null)

check_header() {
    local header="$1"
    local description="$2"

    if echo "$HEADERS" | grep -qi "$header"; then
        print_success "$description - Present"
    else
        print_failure "$description - MISSING"
    fi
}

check_header "Strict-Transport-Security" "HSTS (HTTP Strict Transport Security)"
check_header "Content-Security-Policy" "CSP (Content Security Policy)"
check_header "X-Frame-Options" "X-Frame-Options (Clickjacking Protection)"
check_header "X-Content-Type-Options" "X-Content-Type-Options (MIME Sniffing Protection)"
check_header "X-XSS-Protection" "X-XSS-Protection (XSS Filter)"

# Check for information disclosure
if echo "$HEADERS" | grep -qi "x-powered-by"; then
    print_warning "X-Powered-By header exposes server technology"
fi

if echo "$HEADERS" | grep -qi "server:"; then
    SERVER_INFO=$(echo "$HEADERS" | grep -i "^server:" | cut -d':' -f2)
    print_warning "Server header disclosure: $SERVER_INFO"
fi

# ═════════════════════════════════════════════════════════════════════
# TEST 2: Hidden/Admin Routes Discovery
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 2: Hidden/Admin Routes Discovery"

COMMON_ADMIN_ROUTES=(
    "/admin"
    "/administrator"
    "/dashboard/admin"
    "/api/admin"
    "/api/v1/admin"
    "/hidden"
    "/debug"
    "/test"
    "/secret"
    "/console"
    "/adminer"
    "/phpmyadmin"
    "/.env"
    "/config"
    "/api/docs"
    "/docs"
)

for route in "${COMMON_ADMIN_ROUTES[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$route")
    if [ "$STATUS" = "200" ]; then
        print_warning "Publicly accessible: $route (200 OK)"
    elif [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
        print_success "Protected route: $route ($STATUS)"
    elif [ "$STATUS" = "404" ]; then
        print_success "Not found: $route ($STATUS)"
    else
        print_info "Route $route returned: $STATUS"
    fi
done

# ═════════════════════════════════════════════════════════════════════
# TEST 3: Abandoned/Backup Files
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 3: Abandoned/Backup Files Exposure"

BACKUP_PATTERNS=(
    ".backup"
    ".bak"
    ".old"
    ".orig"
    "~"
    ".swp"
    ".tmp"
    "backup."
    "copy of"
    "_backup"
)

for pattern in "${BACKUP_PATTERNS[@]}"; do
    # Check API endpoints
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth$pattern")
    if [ "$RESPONSE" = "200" ]; then
        print_failure "Exposed backup file: api/v1/auth$pattern"
    fi
done

# Check for backup files in filesystem
BACKUP_COUNT=$(find app/api/v1/endpoints -name "*.backup" -o -name "*.bak" -o -name "*.old" 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 0 ]; then
    print_warning "Found $BACKUP_COUNT backup files in codebase - should be removed before deployment"
fi

# ═════════════════════════════════════════════════════════════════════
# TEST 4: CAPTCHA & Rate Limiting
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 4: Rate Limiting & CAPTCHA"

# Test rate limiting on login endpoint
print_info "Testing rate limiting on /api/v1/auth/login..."

REQUEST_COUNT=0
for i in {1..15}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"wrongpassword"}')
    if [ "$STATUS" = "429" ]; then
        print_success "Rate limiting active after $i requests"
        ((REQUEST_COUNT++))
        break
    fi
done

if [ $REQUEST_COUNT -eq 0 ]; then
    print_warning "No rate limiting detected on login endpoint (15 requests allowed)"
fi

# Check for CAPTCHA
if grep -r "captcha\|recaptcha\|hcaptcha" app/ frontend/src/ 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -v ".backup" | head -1; then
    print_success "CAPTCHA implementation found"
else
    print_warning "No CAPTCHA implementation found - vulnerable to automated attacks"
fi

# ═════════════════════════════════════════════════════════════════════
# TEST 5: Version Information Disclosure
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 5: Version Information Disclosure"

# Check API response for version info
VERSION_RESPONSE=$(curl -s "$BASE_URL/api/v1/health" 2>/dev/null)
if echo "$VERSION_RESPONSE" | grep -q "version\|Version\|VERSION"; then
    print_warning "Version information exposed in API response"
else
    print_success "No version disclosure in API response"
fi

# Check backend files for version strings
if grep -r "__version__\|VERSION\|version.*=" app/ 2>/dev/null | grep -v ".git" | grep -v ".backup" | grep -v "node_modules" | head -1; then
    print_info "Version strings found in backend code (normal for development)"
fi

# Check if debugging mode is exposed
if echo "$VERSION_RESPONSE" | grep -qi "debug\|traceback\|stack"; then
    print_failure "Debug information exposed in API response!"
fi

# ═════════════════════════════════════════════════════════════════════
# TEST 6: CORS Configuration
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 6: CORS Configuration"

# Test CORS headers
ORIGIN_TEST="http://malicious-site.com"
CORS_HEADERS=$(curl -s -I -H "Origin: $ORIGIN_TEST" "$BASE_URL/api/v1/health" 2>/dev/null)

if echo "$CORS_HEADERS" | grep -qi "access-control-allow-origin.*\*"; then
    print_warning "CORS allows all origins (*) - may be too permissive"
elif echo "$CORS_HEADERS" | grep -qi "access-control-allow-origin"; then
    ALLOWED_ORIGIN=$(echo "$CORS_HEADERS" | grep -i "access-control-allow-origin" | cut -d':' -f2)
    print_info "CORS restricted to: $ALLOWED_ORIGIN"
else
    print_success "CORS not allowing external origins"
fi

# ═════════════════════════════════════════════════════════════════════
# TEST 7: Sensitive File Exposure
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 7: Sensitive File Exposure"

SENSITIVE_FILES=(
    "/.env"
    "/.git/config"
    "/package.json"
    "/requirements.txt"
    "/README.md"
    "/.env.local"
    "/config.py"
)

for file in "${SENSITIVE_FILES[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$file")
    if [ "$STATUS" = "200" ]; then
        print_failure "Sensitive file exposed: $file"
    elif [ "$STATUS" = "404" ]; then
        print_success "File not accessible: $file"
    else
        print_info "File $file returned: $STATUS"
    fi
done

# Check for .env files in project
ENV_FILES=$(find . -maxdepth 2 -name ".env*" -type f 2>/dev/null | grep -v node_modules | wc -l)
if [ "$ENV_FILES" -gt 0 ]; then
    print_warning "Found $ENV_FILES .env files - ensure they're not committed to git"
fi

# ═════════════════════════════════════════════════════════════════════
# TEST 8: API Endpoint Security
# ═════════════════════════════════════════════════════════════════════
print_header "TEST 8: API Endpoint Security"

# Test for unauthenticated access to protected endpoints
PROTECTED_ENDPOINTS=(
    "/api/v1/users"
    "/api/v1/teams"
    "/api/v1/assessments"
)

for endpoint in "${PROTECTED_ENDPOINTS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
        print_success "Protected endpoint requires auth: $endpoint ($STATUS)"
    elif [ "$STATUS" = "200" ]; then
        print_warning "Unauthenticated access: $endpoint (200 OK)"
    else
        print_info "Endpoint $endpoint returned: $STATUS"
    fi
done

# ═════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════
print_header "SECURITY TEST SUMMARY"

echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 No critical security issues found!${NC}"
else
    echo -e "${RED}⚠️  Found $FAILED security issue(s) that need attention${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}ℹ️  $WARNINGS warning(s) to review${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Security testing complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
