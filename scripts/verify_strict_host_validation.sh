#!/bin/bash

# ============================================================================
# StrictHostValidationMiddleware Verification Script
# ============================================================================
# This script verifies that the StrictHostValidationMiddleware is active
# and working correctly in production environment.
#
# Usage:
#   ./scripts/verify_strict_host_validation.sh [--url https://api.psychsync.com]
#
# Exit Codes:
#   0 - All tests passed
#   1 - Some tests failed
#   2 - Configuration error
# ============================================================================

set -e

# Default configuration
DEFAULT_URL="https://api.psychsync.com"
API_URL="${DEFAULT_URL}"
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            API_URL="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--url URL] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --url URL       API base URL (default: $DEFAULT_URL)"
            echo "  --verbose, -v   Show detailed output"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 2
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0
WARNED=0

# Print header
echo "================================================"
echo "STRICT HOST VALIDATION MIDDLEWARE VERIFICATION"
echo "================================================"
echo ""
echo "Target URL: $API_URL"
echo "Time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Function to print result
print_result() {
    local result=$1
    local message=$2

    case $result in
        "PASS")
            echo -e "${GREEN}✓ PASS${NC}: $message"
            PASSED=$((PASSED + 1))
            ;;
        "FAIL")
            echo -e "${RED}✗ FAIL${NC}: $message"
            FAILED=$((FAILED + 1))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠ WARN${NC}: $message"
            WARNED=$((WARNED + 1))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ INFO${NC}: $message"
            ;;
    esac
}

# Function to make HTTP request and get status code
make_request() {
    local host=$1
    local endpoint=$2
    local url="$API_URL$endpoint"

    if [ "$VERBOSE" = true ]; then
        echo "    Request: Host=$host URL=$url"
    fi

    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Host: $host" \
        --connect-timeout 10 \
        --max-time 30 \
        "$url" 2>/dev/null)

    echo "$response"
}

# Function to extract error message from JSON response
get_error_message() {
    local host=$1
    local endpoint=$2
    local url="$API_URL$endpoint"

    local response=$(curl -s -H "Host: $host" \
        --connect-timeout 10 \
        --max-time 30 \
        "$url" 2>/dev/null)

    echo "$response" | grep -o '"error":"[^"]*"' | cut -d'"' -f4 || echo "Unknown error"
}

# ============================================================================
# PRE-CHECKS
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PRE-CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check 1: curl is available
if ! command -v curl &> /dev/null; then
    print_result "FAIL" "curl is not installed"
    echo ""
    echo "Please install curl: sudo apt install curl"
    exit 2
fi
print_result "PASS" "curl is available ($(curl --version | head -1 | cut -d' ' -f2))"
echo ""

# Check 2: jq is available (optional)
if command -v jq &> /dev/null; then
    print_result "PASS" "jq is available ($(jq --version | cut -d' ' -f2))"
else
    print_result "WARN" "jq is not installed (optional, for better error parsing)"
fi
echo ""

# Check 3: API is reachable
HEALTH_CHECK=$(make_request "api.psychsync.com" "/health")
if [ "$HEALTH_CHECK" = "000" ]; then
    print_result "FAIL" "Cannot reach API at $API_URL"
    echo ""
    echo "Please check:"
    echo "  1. API is running"
    echo "  2. URL is correct (use --url to specify)"
    echo "  3. Network connectivity"
    echo "  4. Firewall is not blocking the connection"
    exit 2
fi
print_result "PASS" "API is reachable (HTTP $HEALTH_CHECK on /health)"
echo ""

# ============================================================================
# TEST SUITE
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUITE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# Test 1: Valid Production Hosts
# ============================================================================
echo "Test 1: Valid Production Hosts"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

VALID_HOSTS=(
    "psychsync.com"
    "www.psychsync.com"
    "api.psychsync.com"
)

for host in "${VALID_HOSTS[@]}"; do
    RESPONSE=$(make_request "$host" "/api/v1/users")

    # Valid hosts should return:
    # - 401 (Unauthorized - passed to auth)
    # - 200 (OK - if endpoint doesn't require auth)
    # - 404 (Not Found - if endpoint doesn't exist)
    # - Anything BUT 400 (which would indicate middleware blocked it)

    if [ "$RESPONSE" = "400" ]; then
        print_result "FAIL" "$host → HTTP $RESPONSE (should NOT be blocked)"
    elif [ "$RESPONSE" = "401" ] || [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "404" ]; then
        print_result "PASS" "$host → HTTP $RESPONSE (correctly allowed through)"
    else
        print_result "INFO" "$host → HTTP $RESPONSE (unexpected but not blocked by middleware)"
    fi
done
echo ""

# ============================================================================
# Test 2: Invalid Hosts (Malicious)
# ============================================================================
echo "Test 2: Invalid Hosts (Malicious - Should Be BLOCKED)"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

MALICIOUS_HOSTS=(
    "evil.com"
    "attacker.com"
    "malicious-site.com"
    "xss.evil.com"
)

for host in "${MALICIOUS_HOSTS[@]}"; do
    RESPONSE=$(make_request "$host" "/api/v1/users")

    if [ "$RESPONSE" = "400" ]; then
        ERROR_MSG=$(get_error_message "$host" "/api/v1/users")
        if [ -n "$ERROR_MSG" ]; then
            print_result "PASS" "$host → HTTP $RESPONSE (BLOCKED: $ERROR_MSG)"
        else
            print_result "PASS" "$host → HTTP $RESPONSE (BLOCKED)"
        fi
    else
        print_result "FAIL" "$host → HTTP $RESPONSE (should be BLOCKED with 400!)"
    fi
done
echo ""

# ============================================================================
# Test 3: Localhost (Should Be BLOCKED in Production)
# ============================================================================
echo "Test 3: Localhost (Should Be BLOCKED in Production)"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

LOCALHOST_HOSTS=(
    "localhost"
    "127.0.0.1"
    "0.0.0.0"
)

for host in "${LOCALHOST_HOSTS[@]}"; do
    RESPONSE=$(make_request "$host" "/api/v1/users")

    if [ "$RESPONSE" = "400" ]; then
        print_result "PASS" "$host → HTTP $RESPONSE (correctly BLOCKED in production)"
    else
        print_result "FAIL" "$host → HTTP $RESPONSE (should be BLOCKED in production!)"
    fi
done
echo ""

# ============================================================================
# Test 4: Suspicious Patterns
# ============================================================================
echo "Test 4: Suspicious Patterns (Should Be BLOCKED)"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

SUSPICIOUS_HOSTS=(
    "payload.evil.com"
    "script.com"
    "<script>.com"
    "javascript:void.com"
)

for host in "${SUSPICIOUS_HOSTS[@]}"; do
    RESPONSE=$(make_request "$host" "/api/v1/users")

    if [ "$RESPONSE" = "400" ]; then
        ERROR_MSG=$(get_error_message "$host" "/api/v1/users")
        if [ -n "$ERROR_MSG" ]; then
            print_result "PASS" "$host → HTTP $RESPONSE (BLOCKED: $ERROR_MSG)"
        else
            print_result "PASS" "$host → HTTP $RESPONSE (BLOCKED)"
        fi
    else
        print_result "FAIL" "$host → HTTP $RESPONSE (should be BLOCKED!)"
    fi
done
echo ""

# ============================================================================
# Test 5: Health Check Endpoints (Behavior Check)
# ============================================================================
echo "Test 5: Health Check Endpoints (Should Allow Invalid Hosts in Dev, Block in Prod)"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

HEALTH_ENDPOINTS=(
    "/health"
    "/ping"
    "/metrics"
)

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    RESPONSE=$(make_request "evil.com" "$endpoint")

    # In PRODUCTION with StrictHostValidationMiddleware:
    # - These should ALSO be blocked (no exemptions)
    # - Should return 400

    # In DEVELOPMENT with HostValidationMiddleware:
    # - These are exempted and return 200 or 404

    if [ "$RESPONSE" = "400" ]; then
        print_result "PASS" "evil.com → $endpoint → HTTP $RESPONSE (Strict mode: blocked)"
    elif [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "404" ]; then
        print_result "WARN" "evil.com → $endpoint → HTTP $RESPONSE (Dev mode: exempted)"
    else
        print_result "INFO" "evil.com → $endpoint → HTTP $RESPONSE"
    fi
done
echo ""

# ============================================================================
# Test 6: HTTP Security Headers
# ============================================================================
echo "Test 6: HTTP Security Headers (Best Practices)"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

SECURITY_HEADERS=(
    "strict-transport-security"
    "x-frame-options"
    "x-content-type-options"
    "x-xss-protection"
    "content-security-policy"
    "referrer-policy"
)

for header in "${SECURITY_HEADERS[@]}"; do
    HEADER_VALUE=$(curl -s -I "$API_URL/health" | grep -i "$header:" || echo "")

    if [ -n "$HEADER_VALUE" ]; then
        print_result "PASS" "$header is present"
    else
        print_result "WARN" "$header is missing"
    fi
done
echo ""

# ============================================================================
# Test 7: TLS/SSL Configuration
# ============================================================================
echo "Test 7: TLS/SSL Configuration"
echo "─────────────────────────────────────────────────────────────────────"
echo ""

# Check if URL uses HTTPS
if [[ "$API_URL" == https://* ]]; then
    print_result "PASS" "Using HTTPS protocol"

    # Check TLS version (requires openssl s_client)
    if command -v openssl &> /dev/null; then
        TLS_INFO=$(echo | openssl s_client -connect "$(echo "$API_URL" | sed 's|https://||'):443" 2>/dev/null | grep -E "Protocol|TLS" | head -1 || echo "")

        if [ -n "$TLS_INFO" ]; then
            print_result "INFO" "TLS: $TLS_INFO"
        fi
    fi
else
    print_result "WARN" "Not using HTTPS (HTTP only)"
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFICATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "Target URL: $API_URL"
echo ""
echo "Results:"
echo "  ✓ Passed: $PASSED"
echo "  ✗ Failed: $FAILED"
echo "  ⚠ Warnings: $WARNED"
echo "  Total Tests: $((PASSED + FAILED + WARNED))"
echo ""

# Determine overall result
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}✓ ALL CRITICAL TESTS PASSED${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "The StrictHostValidationMiddleware is working correctly!"
    echo ""
    echo "Security Protections Active:"
    echo "  ✓ Valid production hosts allowed through"
    echo "  ✓ Malicious hosts blocked with HTTP 400"
    echo "  ✓ localhost blocked in production"
    echo "  ✓ Suspicious patterns detected and blocked"
    echo ""

    if [ $WARNED -gt 0 ]; then
        echo -e "${YELLOW}Note: $WARNED warning(s) detected - review above${NC}"
        echo ""
    fi

    echo "Next Steps:"
    echo "  1. Monitor logs for blocked host attempts"
    echo "  2. Set up alerts for repeated blocks from same IP"
    echo "  3. Review ALLOWED_HOSTS configuration regularly"
    echo "  4. Run this script periodically to verify configuration"
    echo ""

    exit 0
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}================================================${NC}"
    echo ""
    echo "Issues detected that need attention:"
    echo ""

    if [ $FAILED -gt 0 ]; then
        echo "1. Middleware may not be active"
        echo "   - Check: ENVIRONMENT=production in .env.production"
        echo "   - Check: ALLOWED_HOSTS is configured with your domains"
        echo "   - Check: Service is using StrictHostValidationMiddleware"
        echo "   - Action: Restart the service after config changes"
        echo ""
    fi

    echo "Troubleshooting Commands:"
    echo "  # Check service logs"
    echo "  sudo journalctl -u psychsync-api.service | grep -i 'middleware'"
    echo ""
    echo "  # Check environment configuration"
    echo "  grep -E 'ENVIRONMENT|ALLOWED_HOSTS' /var/www/psychsync/.env.production"
    echo ""
    echo "  # Test middleware directly"
    echo "  curl -H 'Host: evil.com' $API_URL/api/v1/users"
    echo ""

    exit 1
fi
