#!/bin/bash
###############################################################################
# HSTS Preload Status Monitoring Script
#
# Monitors the status of HSTS preload submission and verifies HSTS headers
# are properly configured.
#
# Usage: ./scripts/monitor_hsts_status.sh [--domain=<domain>]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${DOMAIN:-psychsync.com}"
API_URL="https://hstspreload.org/api/v2/status"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_hsts_header() {
    log_info "Checking HSTS header on https://$DOMAIN..."

    local response=$(curl -I "https://$DOMAIN" 2>&1)
    local hsts_header=$(echo "$response" | grep -i "Strict-Transport-Security" || true)

    if [ -z "$hsts_header" ]; then
        log_error "HSTS header not found!"
        echo ""
        echo "Response headers:"
        echo "$response"
        return 1
    fi

    log_success "HSTS header found:"
    echo "  $hsts_header"
    echo ""

    # Check for required directives
    local issues=0

    if echo "$hsts_header" | grep -q "includeSubDomains"; then
        log_success "✅ includeSubDomains directive present"
    else
        log_warning "❌ includeSubDomains directive missing"
        issues=$((issues + 1))
    fi

    if echo "$hsts_header" | grep -q "preload"; then
        log_success "✅ preload directive present"
    else
        log_warning "❌ preload directive missing"
        issues=$((issues + 1))
    fi

    # Check max-age (should be at least 31536000)
    local max_age=$(echo "$hsts_header" | grep -oP 'max-age=\K\d+' || echo "0")
    if [ "$max_age" -ge 31536000 ]; then
        log_success "✅ max-age is sufficient ($max_age seconds, $(($max_age / 86400)) days)"
    else
        log_warning "❌ max-age is too short ($max_age seconds, should be at least 31536000)"
        issues=$((issues + 1))
    fi

    echo ""

    if [ $issues -eq 0 ]; then
        log_success "All HSTS requirements met ✅"
        return 0
    else
        log_warning "Found $issues HSTS configuration issues"
        return 1
    fi
}

check_preload_status() {
    log_info "Checking HSTS preload status for $DOMAIN..."

    local response=$(curl -s "$API_URL?domain=$DOMAIN" 2>&1)

    if ! echo "$response" | jq empty 2>/dev/null; then
        log_error "Invalid JSON response from HSTS preload API"
        echo "Response: $response"
        return 1
    fi

    local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")

    log_success "HSTS preload status: $status"
    echo ""

    case "$status" in
        "unknown")
            log_warning "Domain is not in the preload list"
            echo "To submit, visit: https://hstspreload.org/?domain=$DOMAIN"
            ;;
        "pending")
            log_info "Domain is pending submission to preload list"
            echo "This typically takes a few weeks to process."
            ;;
        "preloaded")
            log_success "Domain is in the HSTS preload list! 🎉"
            echo "Browsers will automatically use HTTPS for this domain."
            ;;
        "rejected")
            log_error "Domain was rejected from preload list"
            local error=$(echo "$response" | jq -r '.errors' 2>/dev/null || echo "Unknown error")
            echo "Reason: $error"
            echo "Visit: https://hstspreload.org/?domain=$DOMAIN for details"
            ;;
        *)
            log_warning "Unknown status: $status"
            ;;
    esac

    echo ""

    # Show full response
    log_info "Full API response:"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    echo ""
}

check_subdomain_https() {
    log_info "Checking HTTPS on subdomains..."

    local subdomains=("www" "api" "mail" "app")
    local issues=0

    for subdomain in "${subdomains[@]}"; do
        local full_domain="$subdomain.$DOMAIN"
        echo -n "  Checking $full_domain... "

        if curl -I "https://$full_domain" &>/dev/null; then
            echo -e "${GREEN}✓ HTTPS works${NC}"

            # Check HSTS header on subdomain
            local hsts=$(curl -I "https://$full_domain" 2>&1 | grep -i "Strict-Transport-Security" || true)
            if [ -n "$hsts" ]; then
                echo "    $hsts"
            else
                echo -e "    ${YELLOW}⚠ No HSTS header${NC}"
                issues=$((issues + 1))
            fi
        else
            echo -e "${YELLOW}✓ HTTPS not configured (or subdomain doesn't exist)${NC}"
        fi
    done

    echo ""

    if [ $issues -eq 0 ]; then
        log_success "All subdomains have HSTS headers"
    else
        log_warning "Some subdomains are missing HSTS headers"
    fi
}

check_http_redirect() {
    log_info "Checking HTTP to HTTPS redirect..."

    local response=$(curl -I "http://$DOMAIN" 2>&1)
    local status_code=$(echo "$response" | grep -oP 'HTTP/\d\.\d \K\d+' || echo "000")

    echo "HTTP Status: $status_code"

    if [ "$status_code" = "301" ] || [ "$status_code" = "302" ] || [ "$status_code" = "307" ] || [ "$status_code" = "308" ]; then
        local location=$(echo "$response" | grep -i "Location" || true)
        log_success "HTTP redirects to HTTPS"
        echo "  $location"

        if echo "$location" | grep -q "https://"; then
            log_success "Redirect goes to HTTPS URL"
        else
            log_warning "Redirect does not go to HTTPS URL"
        fi
    else
        log_warning "HTTP does not redirect to HTTPS (status: $status_code)"
    fi

    echo ""
}

main() {
    echo "========================================================================================================"
    echo "     HSTS Preload Status Monitor"
    echo "========================================================================================================"
    echo ""
    echo "Domain: $DOMAIN"
    echo "Date: $(date)"
    echo ""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain=*)
                DOMAIN="${1#*=}"
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--domain=<domain>]"
                exit 1
                ;;
        esac
    done

    # Run checks
    check_hsts_header
    check_preload_status
    check_subdomain_https
    check_http_redirect

    # Summary
    echo "========================================================================================================"
    echo "Summary"
    echo "========================================================================================================"
    echo ""
    echo "HSTS Header: Configured ✅"
    echo "Preload Status: Check above for current status"
    echo "Subdomains: Check above for individual status"
    echo "HTTP Redirect: Check above"
    echo ""
    echo "For more information, visit: https://hstspreload.org/"
    echo ""
}

# Run main function
main "$@"
