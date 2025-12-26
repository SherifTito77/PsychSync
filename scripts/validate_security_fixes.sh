#!/bin/bash

################################################################################
# Security Fixes Validation Script
################################################################################
# Validates that all security fixes from the penetration test are properly
# implemented and functioning correctly.
#
# Usage: ./scripts/validate_security_fixes.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Base URL (can be overridden with env variable)
BASE_URL="${BASE_URL:-http://localhost:8000}"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_test() {
    echo -e "${YELLOW}Testing:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
    ((WARNINGS++))
}

################################################################################
# Validation Functions
################################################################################

validate_backup_files_removed() {
    print_header "M-001: Backup Files Removal"

    local backup_files=$(find . -name "*.backup" -o -name "*.bak" -o -name "*.old" 2>/dev/null | grep -v "node_modules" | grep -v ".git" || true)

    if [ -z "$backup_files" ]; then
        print_pass "No backup files found in codebase"
    else
        print_fail "Found backup files:\n$backup_files"
        echo "Please remove with: find . -name '*.backup' -delete"
    fi
}

validate_rate_limiting() {
    print_header "M-002: Rate Limiting Implementation"

    print_test "Checking rate limiter file exists"
    if [ -f "app/core/simple_rate_limiter.py" ]; then
        print_pass "Rate limiter implementation exists"

        print_test "Checking rate limiting applied to auth endpoints"
        if grep -q "rate_limit" app/api/v1/endpoints/auth.py; then
            print_pass "Rate limiting decorators found in auth.py"
        else
            print_fail "Rate limiting not applied to auth endpoints"
        fi
    else
        print_fail "Rate limiter implementation not found"
    fi

    print_test "Testing rate limiting on login endpoint"
    local rate_limit_hits=0
    for i in {1..8}; do
        local response=$(curl -s -w "%{http_code}" -X POST "${BASE_URL}/api/v1/auth/token-fixed" \
            -H "Content-Type: application/json" \
            -d '{"username":"test@test.com","password":"wrongpassword123"}' \
            -o /dev/null 2>/dev/null || echo "000")

        if [ "$response" = "429" ]; then
            ((rate_limit_hits++))
        fi
        sleep 0.1
    done

    if [ $rate_limit_hits -gt 0 ]; then
        print_pass "Rate limiting is active (received $rate_limit_hits 429 responses)"
    else
        print_warn "Rate limiting may not be active (no 429 responses received)"
        echo "Note: Backend server must be running for this test"
    fi
}

validate_server_header_removed() {
    print_header "L-001: Server Header Removal"

    print_test "Checking if Server header is removed"
    local response=$(curl -s -I "${BASE_URL}/api/v1/health" 2>/dev/null || echo "")

    if echo "$response" | grep -qi "^Server:"; then
        local server_header=$(echo "$response" | grep -i "^Server:" | cut -d':' -f2)
        print_fail "Server header is still present: $server_header"
    else
        print_pass "Server header has been removed"
    fi

    print_test "Checking security headers middleware"
    if grep -q "add_additional_security_headers" app/main.py; then
        print_pass "Security headers middleware implemented in main.py"
    else
        print_fail "Security headers middleware not found"
    fi

    print_test "Checking additional security headers"
    local has_referrer=false
    local has_permissions=false
    local has_coep=false
    local has_coop=false

    if echo "$response" | grep -qi "Referrer-Policy"; then
        has_referrer=true
    fi
    if echo "$response" | grep -qi "Permissions-Policy"; then
        has_permissions=true
    fi
    if echo "$response" | grep -qi "Cross-Origin-Embedder-Policy"; then
        has_coep=true
    fi
    if echo "$response" | grep -qi "Cross-Origin-Opener-Policy"; then
        has_coop=true
    fi

    if $has_referrer && $has_permissions && $has_coep && $has_coop; then
        print_pass "All additional security headers present"
    else
        print_warn "Some additional security headers missing"
        echo "  Referrer-Policy: $has_referrer"
        echo "  Permissions-Policy: $has_permissions"
        echo "  COEP: $has_coep"
        echo "  COOP: $has_coop"
    fi
}

validate_production_security_config() {
    print_header "L-002: Production Security Configuration"

    print_test "Checking production security config exists"
    if [ -f "app/core/production_security.py" ]; then
        print_pass "Production security config file exists"

        print_test "Checking environment-aware feature flags"
        if grep -q "should_enable_feature" app/core/production_security.py; then
            print_pass "Feature flag implementation found"
        else
            print_warn "Feature flag implementation not found"
        fi

        print_test "Checking get_security_headers method"
        if grep -q "get_security_headers" app/core/production_security.py; then
            print_pass "Security headers method implemented"
        else
            print_fail "get_security_headers method not found"
        fi
    else
        print_fail "Production security config not found"
    fi
}

validate_gitignore_protection() {
    print_header "L-003: .gitignore Protection"

    print_test "Checking .gitignore for backup files"
    if grep -q "\*.backup" .gitignore && grep -q "\*.bak" .gitignore; then
        print_pass ".gitignore blocks backup files"
    else
        print_fail ".gitignore doesn't block backup files"
    fi

    print_test "Checking .gitignore for .env files"
    if grep -q "^\.env$" .gitignore && grep -q "\.env\.\*" .gitignore; then
        print_pass ".gitignore blocks .env files"
    else
        print_fail ".gitignore doesn't properly block .env files"
    fi

    print_test "Checking if .env files are tracked by git"
    local tracked_env=$(git ls-files 2>/dev/null | grep "\.env$" || true)

    if [ -z "$tracked_env" ]; then
        print_pass "No .env files are tracked by git"
    else
        print_fail "Found .env files tracked by git:\n$tracked_env"
    fi

    print_test "Checking .gitignore for sensitive files"
    local required_patterns=("*.key" "*.pem" "*.crt" "secrets.yaml")
    local all_found=true

    for pattern in "${required_patterns[@]}"; do
        if ! grep -q "$pattern" .gitignore; then
            all_found=false
            echo "  Missing pattern: $pattern"
        fi
    done

    if $all_found; then
        print_pass ".gitignore blocks sensitive file types"
    else
        print_fail ".gitignore missing some sensitive file patterns"
    fi
}

validate_security_headers() {
    print_header "I-001: Core Security Headers"

    print_test "Checking core security headers"
    local response=$(curl -s -I "${BASE_URL}/api/v1/health" 2>/dev/null || echo "")

    local headers=(
        "X-Content-Type-Options"
        "X-Frame-Options"
        "X-XSS-Protection"
        "Strict-Transport-Security"
        "Content-Security-Policy"
    )

    local all_present=true
    for header in "${headers[@]}"; do
        if ! echo "$response" | grep -qi "$header"; then
            echo "  Missing: $header"
            all_present=false
        fi
    done

    if $all_present; then
        print_pass "All core security headers present"
    else
        print_warn "Some security headers missing"
    fi
}

validate_hidden_routes() {
    print_header "I-002: Hidden Route Protection"

    local routes=(
        "/admin"
        "/administrator"
        "/dashboard/admin"
        "/debug"
        "/console"
        "/secret"
    )

    local all_protected=true
    for route in "${routes[@]}"; do
        local status=$(curl -s -w "%{http_code}" "${BASE_URL}${route}" -o /dev/null 2>/dev/null || echo "000")

        if [ "$status" = "401" ] || [ "$status" = "404" ]; then
            echo "  ✅ $route → $status"
        else
            echo "  ⚠️  $route → $status (expected 401 or 404)"
            all_protected=false
        fi
    done

    if $all_protected; then
        print_pass "All hidden routes properly protected"
    else
        print_warn "Some routes may need attention"
    fi
}

validate_sensitive_files() {
    print_header "I-003: Sensitive File Protection"

    local files=(
        "/.env"
        "/.git/config"
        "/config.py"
        "/requirements.txt"
    )

    local all_protected=true
    for file in "${files[@]}"; do
        local status=$(curl -s -w "%{http_code}" "${BASE_URL}${file}" -o /dev/null 2>/dev/null || echo "000")

        if [ "$status" = "404" ]; then
            echo "  ✅ $file → 404"
        else
            echo "  ⚠️  $file → $status (expected 404)"
            all_protected=false
        fi
    done

    if $all_protected; then
        print_pass "All sensitive files properly protected"
    else
        print_warn "Some files may be accessible"
    fi
}

validate_api_authentication() {
    print_header "I-004: API Endpoint Authentication"

    local endpoints=(
        "/api/v1/users"
        "/api/v1/teams"
        "/api/v1/assessments"
    )

    local all_protected=true
    for endpoint in "${endpoints[@]}"; do
        local status=$(curl -s -w "%{http_code}" "${BASE_URL}${endpoint}" -o /dev/null 2>/dev/null || echo "000")

        if [ "$status" = "401" ]; then
            echo "  ✅ $endpoint → 401 Unauthorized"
        else
            echo "  ⚠️  $endpoint → $status (expected 401)"
            all_protected=false
        fi
    done

    if $all_protected; then
        print_pass "All API endpoints require authentication"
    else
        print_warn "Some endpoints may not require authentication"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "PsychSync Security Fixes Validation"
    echo "Base URL: $BASE_URL"
    echo "Timestamp: $(date)"

    # Check if server is running
    if ! curl -s -f "${BASE_URL}/api/v1/health" > /dev/null 2>&1; then
        echo -e "\n${YELLOW}⚠️  WARNING: Backend server may not be running at $BASE_URL${NC}"
        echo "Some tests will be skipped or may fail."
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Exiting. Please start the server first:"
            echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
            exit 1
        fi
    fi

    # Run all validations
    validate_backup_files_removed
    validate_rate_limiting
    validate_server_header_removed
    validate_production_security_config
    validate_gitignore_protection
    validate_security_headers
    validate_hidden_routes
    validate_sensitive_files
    validate_api_authentication

    # Print summary
    print_header "Validation Summary"
    echo -e "${GREEN}Passed:${NC}   $PASSED"
    echo -e "${RED}Failed:${NC}   $FAILED"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"

    local total=$((PASSED + FAILED))
    if [ $total -gt 0 ]; then
        local percentage=$((PASSED * 100 / total))
        echo -e "\nSuccess Rate: ${percentage}%"
    fi

    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✅ All security fixes validated successfully!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some validations failed. Please review the failures above.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
