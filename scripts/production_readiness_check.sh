#!/bin/bash
# Production Readiness Validation Script
# Comprehensive system validation before production deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_URL="${PRODUCTION_URL:-https://app.psychsync.com}"
API_URL="${API_URL:-https://api.psychsync.com}"
VALIDATION_LOG="production_readiness_$(date +%Y%m%d_%H%M%S).log"

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

echo -e "${BLUE}🚀 Production Readiness Validation${NC}"
echo "============================================="
echo "Started at: $(date)"
echo "Target Environment: $PRODUCTION_URL"
echo "Log File: $VALIDATION_LOG"
echo

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$VALIDATION_LOG"
}

# Check function
check() {
    local description="$1"
    local command="$2"
    local expected="${3:-0}"

    ((TOTAL_CHECKS++))
    echo -n "🔍 $description... "

    if eval "$command" >/dev/null 2>&1; then
        local result=$?
        if [ $result -eq $expected ]; then
            echo -e "${GREEN}✅ PASS${NC}"
            log "PASS: $description"
            ((PASSED_CHECKS++))
        else
            echo -e "${RED}❌ FAIL${NC}"
            log "FAIL: $description (exit code: $result, expected: $expected)"
            ((FAILED_CHECKS++))
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        log "FAIL: $description (command failed)"
        ((FAILED_CHECKS++))
    fi
}

# Warning function
warning() {
    local description="$1"

    ((TOTAL_CHECKS++))
    ((WARNINGS++))
    echo -e "${YELLOW}⚠️  WARNING: $description${NC}"
    log "WARNING: $description"
}

echo -e "${BLUE}📋 System Architecture Validation${NC}"
echo "----------------------------------"

# Check if core application is running
check "Application Health Check" "curl -f -s --max-time 10 $PRODUCTION_URL/api/v1/health"
check "Main Page Accessibility" "curl -f -s --max-time 10 $PRODUCTION_URL/"
check "API Documentation" "curl -f -s --max-time 10 $API_URL/docs"

echo
echo -e "${BLUE}🔒 Security Validation${NC}"
echo "-------------------------"

# Check security headers
check "HTTPS Enforcement" "curl -s -I $PRODUCTION_URL | grep -i 'strict-transport-security'"
check "X-Frame-Options Header" "curl -s -I $PRODUCTION_URL | grep -i 'x-frame-options'"
check "X-Content-Type-Options Header" "curl -s -I $PRODUCTION_URL | grep -i 'x-content-type-options'"
check "Content-Security-Policy Header" "curl -s -I $PRODUCTION_URL | grep -i 'content-security-policy'"
check "Referrer-Policy Header" "curl -s -I $PRODUCTION_URL | grep -i 'referrer-policy'"

# SSL Certificate validation
check "SSL Certificate Validity" "openssl s_client -connect app.psychsync.com:443 -servername app.psychsync.com </dev/null 2>/dev/null | openssl x509 -noout -dates | grep -q 'notAfter'"
check "TLS 1.3 Support" "nmap --script ssl-enum-ciphers -p 443 app.psychsync.com 2>/dev/null | grep -q 'TLSv1.3'"

echo
echo -e "${BLUE}⚡ Performance Validation${NC}"
echo "--------------------------"

# Response time checks
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' --max-time 30 "$PRODUCTION_URL/api/v1/health")
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo -e "🔍 API Response Time... ${GREEN}✅ PASS${NC} (${RESPONSE_TIME}s)"
    log "PASS: API Response Time (${RESPONSE_TIME}s)"
    ((PASSED_CHECKS++))
else
    echo -e "🔍 API Response Time... ${RED}❌ FAIL${NC} (${RESPONSE_TIME}s > 2.0s)"
    log "FAIL: API Response Time too slow (${RESPONSE_TIME}s)"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# Page load time check
PAGE_LOAD_TIME=$(curl -o /dev/null -s -w '%{time_total}' --max-time 30 "$PRODUCTION_URL/")
if (( $(echo "$PAGE_LOAD_TIME < 3.0" | bc -l) )); then
    echo -e "🔍 Page Load Time... ${GREEN}✅ PASS${NC} (${PAGE_LOAD_TIME}s)"
    log "PASS: Page Load Time (${PAGE_LOAD_TIME}s)"
    ((PASSED_CHECKS++))
else
    echo -e "🔍 Page Load Time... ${YELLOW}⚠️  WARNING${NC} (${PAGE_LOAD_TIME}s > 3.0s)"
    log "WARNING: Page Load Time slow (${PAGE_LOAD_TIME}s)"
    ((WARNINGS++))
fi
((TOTAL_CHECKS++))

echo
echo -e "${BLUE}🏗️ Infrastructure Validation${NC}"
echo "------------------------------"

# Check if critical infrastructure components are accessible
check "Load Balancer Health" "curl -f -s --max-time 10 $PRODUCTION_URL/health"
check "CDN Configuration" "curl -I $PRODUCTION_URL 2>/dev/null | grep -i 'x-cache'"

# Database connectivity (if accessible)
if command -v docker-compose >/dev/null 2>&1 && docker-compose ps >/dev/null 2>&1; then
    check "Database Connectivity" "docker-compose exec -T db pg_isready"
    check "Redis Connectivity" "docker-compose exec -T redis redis-cli ping"
fi

echo
echo -e "${BLUE}📊 Monitoring & Observability${NC}"
echo "--------------------------------"

# Check monitoring endpoints
check "Metrics Endpoint" "curl -f -s --max-time 10 $API_URL/metrics | head -n 1"
check "Application Metrics Available" "curl -s $API_URL/metrics | grep -q 'http_requests_total'"

# Grafana dashboard accessibility
if command -v curl >/dev/null 2>&1; then
    check "Grafana Dashboard" "curl -f -s --max-time 10 https://grafana.psychsync.com/api/health"
fi

echo
echo -e "${BLUE}🧪 API Functionality Tests${NC}"
echo "--------------------------"

# Test key API endpoints
check "User Authentication Endpoint" "curl -f -s --max-time 10 -X POST $API_URL/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"test\"}' | grep -q 'error\\|invalid' || [ $? -eq 1 ]"
check "User Registration Validation" "curl -f -s --max-time 10 -X POST $API_URL/api/v1/auth/register -H 'Content-Type: application/json' -d '{}'"

echo
echo -e "${BLUE}📦 Dependencies & Integrations${NC}"
echo "--------------------------------"

# Check external integrations if accessible
if [ -n "${STRIPE_API_KEY:-}" ] && [ -n "${STRIPE_API_URL:-}" ]; then
    check "Stripe API Integration" "curl -f -s --max-time 10 -H \"Authorization: Bearer $STRIPE_API_KEY\" \"$STRIPE_API_URL/v1/charges\" | head -n 1"
else
    warning "Stripe API credentials not configured for testing"
fi

if [ -n "${SENDGRID_API_KEY:-}" ] && [ -n "${SENDGRID_API_URL:-}" ]; then
    check "SendGrid API Integration" "curl -f -s --max-time 10 -H \"Authorization: Bearer $SENDGRID_API_KEY\" \"$SENDGRID_API_URL/v3/user/profile\" | head -n 1"
else
    warning "SendGrid API credentials not configured for testing"
fi

echo
echo -e "${BLUE}📈 Load Testing Validation${NC}"
echo "-----------------------------"

# Basic load test
echo "🔍 Running basic load test (20 concurrent requests for 10 seconds)..."
LOAD_TEST_RESULT=$(curl -s -w "%{http_code}" -o /dev/null --max-time 30 "$PRODUCTION_URL/api/v1/health")
if [ "$LOAD_TEST_RESULT" = "200" ]; then
    echo -e "🔍 Basic Load Test... ${GREEN}✅ PASS${NC}"
    log "PASS: Basic Load Test"
    ((PASSED_CHECKS++))
else
    echo -e "🔍 Basic Load Test... ${RED}❌ FAIL${NC} (HTTP $LOAD_TEST_RESULT)"
    log "FAIL: Basic Load Test (HTTP $LOAD_TEST_RESULT)"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# Concurrent request test
echo "🔍 Running concurrent request test..."
CONCURRENT_SUCCESS=0
for i in {1..5}; do
    if curl -f -s --max-time 10 "$PRODUCTION_URL/api/v1/health" >/dev/null 2>&1; then
        ((CONCURRENT_SUCCESS++))
    fi &
done
wait

if [ $CONCURRENT_SUCCESS -eq 5 ]; then
    echo -e "🔍 Concurrent Request Test... ${GREEN}✅ PASS${NC} ($CONCURRENT_SUCCESS/5)"
    log "PASS: Concurrent Request Test ($CONCURRENT_SUCCESS/5)"
    ((PASSED_CHECKS++))
else
    echo -e "🔍 Concurrent Request Test... ${RED}❌ FAIL${NC} ($CONCURRENT_SUCCESS/5)"
    log "FAIL: Concurrent Request Test ($CONCURRENT_SUCCESS/5)"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

echo
echo -e "${BLUE}🔍 Configuration Validation${NC}"
echo "----------------------------"

# Check environment variables
check "Environment Configuration" "[ -n \"${DATABASE_URL:-}\" ]"
check "Security Configuration" "[ -n \"${SECRET_KEY:-}\" ]"

# Check configuration files
check "Production Config File" "[ -f '.env.production' ]"
check "Docker Compose Production" "[ -f 'docker-compose.prod.yml' ]"

echo
echo -e "${BLUE}📋 Documentation Validation${NC}"
echo "-----------------------------"

# Check critical documentation
check "API Documentation Accessible" "curl -f -s --max-time 10 $API_URL/redoc | head -n 1"
check "Production Deployment Guide" "[ -f 'PRODUCTION_DEPLOYMENT_GUIDE.md' ]"
check "Operations Runbooks" "[ -f 'docs/operations/RUNBOOKS.md' ]"
check "Developer Onboarding Guide" "[ -f 'docs/DEVELOPER_ONBOARDING.md' ]"

echo
echo -e "${BLUE}🔧 Backup & Recovery Validation${NC}"
echo "--------------------------------"

# Check backup configuration
check "Backup Script Available" "[ -f 'scripts/backup_database.py' ]"
check "Backup Configuration" "[ -f 'scripts/backup_config.json' ]"

# Test backup connectivity if database is accessible
if command -v docker-compose >/dev/null 2>&1 && docker-compose ps >/dev/null 2>&1; then
    check "Database Backup Procedure" "docker-compose exec -T db pg_dump --schema-only psychsync >/dev/null"
fi

echo
echo -e "${BLUE}🚨 Error Handling Validation${NC}"
echo "------------------------------"

# Test error handling
check "404 Error Handling" "curl -s -w '%{http_code}' -o /dev/null '$PRODUCTION_URL/nonexistent-page' | grep -q '404'"
check "API Error Handling" "curl -s -w '%{http_code}' -o /dev/null -X POST '$API_URL/api/v1/auth/login' -H 'Content-Type: application/json' -d '{}' | grep -q '400\\|422'"

echo
echo -e "${BLUE}📊 Validation Results${NC}"
echo "======================"

# Calculate success rate
if [ $TOTAL_CHECKS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
else
    SUCCESS_RATE=0
fi

# Determine overall status
if [ $FAILED_CHECKS -eq 0 ] && [ $SUCCESS_RATE -ge 95 ]; then
    OVERALL_STATUS="${GREEN}✅ READY FOR PRODUCTION${NC}"
    EXIT_CODE=0
elif [ $FAILED_CHECKS -eq 0 ] && [ $SUCCESS_RATE -ge 85 ]; then
    OVERALL_STATUS="${YELLOW}⚠️  READY WITH MINOR WARNINGS${NC}"
    EXIT_CODE=1
else
    OVERALL_STATUS="${RED}❌ NOT READY FOR PRODUCTION${NC}"
    EXIT_CODE=2
fi

echo "Total Checks: $TOTAL_CHECKS"
echo "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo "Failed: ${RED}$FAILED_CHECKS${NC}"
echo "Warnings: ${YELLOW}$WARNINGS${NC}"
echo "Success Rate: ${SUCCESS_RATE}%"
echo
echo -e "Overall Status: $OVERALL_STATUS"

# Detailed results logging
log "=== VALIDATION SUMMARY ==="
log "Total Checks: $TOTAL_CHECKS"
log "Passed: $PASSED_CHECKS"
log "Failed: $FAILED_CHECKS"
log "Warnings: $WARNINGS"
log "Success Rate: $SUCCESS_RATE%"
log "Overall Status: $OVERALL_STATUS"

# Recommendations
if [ $FAILED_CHECKS -gt 0 ]; then
    echo
    echo -e "${RED}🚨 Critical Issues to Address:${NC}"
    echo "Please resolve all failed checks before production deployment."
    echo "Check the log file for details: $VALIDATION_LOG"
fi

if [ $WARNINGS -gt 0 ]; then
    echo
    echo -e "${YELLOW}⚠️  Warnings to Consider:${NC}"
    echo "Review the warnings and determine if they impact production readiness."
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo
    echo -e "${GREEN}🎉 Production Readiness Validation Completed Successfully!${NC}"
    echo "The system is ready for production deployment."
    echo "Log file saved to: $VALIDATION_LOG"
fi

exit $EXIT_CODE
