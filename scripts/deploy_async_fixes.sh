#!/bin/bash
###############################################################################
# Deployment Validation Script for Async Conversion Fixes
# Validates that all async conversion fixes are working correctly
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS_COUNT++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

info() {
    echo -e "${NC}ℹ️  $1"
}

echo "══════════════════════════════════════════════════════════════════════════════"
echo "ASYNC CONVERSION DEPLOYMENT VALIDATION"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""

###############################################################################
# Phase 1: Syntax Validation
###############################################################################
echo "🔍 Phase 1: Syntax Validation"
echo "─────────────────────────────────────────────────────────────────────────────"

FILES=(
    "app/api/v1/endpoints/responses.py"
    "app/services/response_service.py"
    "app/api/v1/endpoints/feature_requests.py"
    "app/api/v1/endpoints/activation.py"
    "app/api/v1/endpoints/toxic_behavior_detection.py"
    "app/api/v1/endpoints/reports.py"
    "app/api/v1/endpoints/health_monitoring.py"
    "app/api/v1/endpoints/enterprise_sales.py"
    "app/api/v1/endpoints/discrimination_analysis.py"
    "app/api/v1/endpoints/communication_analysis.py"
    "app/api/v1/endpoints/ab_testing.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        if python -m py_compile "$file" 2>/dev/null; then
            pass "$file compiles successfully"
        else
            fail "$file has syntax errors"
        fi
    else
        warn "$file not found"
    fi
done

echo ""

###############################################################################
# Phase 2: Import Validation
###############################################################################
echo "📦 Phase 2: Import Validation"
echo "─────────────────────────────────────────────────────────────────────────────"

check_import() {
    local file=$1
    local import=$2

    if grep -q "$import" "$file" 2>/dev/null; then
        pass "$file has '$import'"
    else
        fail "$file missing '$import'"
    fi
}

check_import "app/api/v1/endpoints/responses.py" "from uuid import UUID"
check_import "app/api/v1/endpoints/feature_requests.py" "import asyncio"
check_import "app/api/v1/endpoints/activation.py" "import asyncio"
check_import "app/api/v1/endpoints/toxic_behavior_detection.py" "import asyncio"

echo ""

###############################################################################
# Phase 3: Type Annotation Validation
###############################################################################
echo "🏷️  Phase 3: Type Annotation Validation"
echo "─────────────────────────────────────────────────────────────────────────────"

# Check that helpers use AsyncSession
check_async_helper() {
    local file=$1
    local func=$2

    if grep -q "async def $func.*AsyncSession" "$file" 2>/dev/null; then
        pass "$file - $func() has AsyncSession type"
    else
        fail "$file - $func() missing AsyncSession type"
    fi
}

check_async_helper "app/api/v1/endpoints/feature_requests.py" "_feature_request_to_response"
check_async_helper "app/api/v1/endpoints/feature_requests.py" "_get_vote_count"
check_async_helper "app/api/v1/endpoints/activation.py" "_calculate_funnel"
check_async_helper "app/api/v1/endpoints/activation.py" "_check_and_mark_activated"

echo ""

###############################################################################
# Phase 4: Service Method Validation
###############################################################################
echo "🔧 Phase 4: Service Method Validation"
echo "─────────────────────────────────────────────────────────────────────────────"

# Check that new service methods exist
check_service_method() {
    local file=$1
    local method=$2

    if grep -q "async def $method" "$file" 2>/dev/null; then
        pass "$file has $method() method"
    else
        fail "$file missing $method() method"
    fi
}

check_service_method "app/services/response_service.py" "get_response_score"
check_service_method "app/services/response_service.py" "save_progress"
check_service_method "app/services/response_service.py" "validate_response_data"
check_service_method "app/services/response_service.py" "submit_response"
check_service_method "app/services/response_service.py" "delete_response"

echo ""

###############################################################################
# Phase 5: Async Pattern Validation
###############################################################################
echo "⚡ Phase 5: Async Pattern Validation"
echo "─────────────────────────────────────────────────────────────────────────────"

# Check for run_in_executor usage (should exist in converted files)
check_run_in_executor() {
    local file=$1

    if grep -q "run_in_executor" "$file" 2>/dev/null; then
        pass "$file uses run_in_executor() for non-blocking operations"
    else
        info "$file may not need run_in_executor() (uses native async)"
    fi
}

check_run_in_executor "app/api/v1/endpoints/toxic_behavior_detection.py"
check_run_in_executor "app/api/v1/endpoints/activation.py"
check_run_in_executor "app/api/v1/endpoints/feature_requests.py"

# Check for improper db.query() usage (should be wrapped)
check_no_unwrapped_query() {
    local file=$1

    # Look for unwrapped db.query() calls (not in run_in_executor)
    unwrapped=$(grep -n "db\.query(" "$file" 2>/dev/null | grep -v "run_in_executor" | grep -v "lambda:" | wc -l)

    if [ "$unwrapped" -eq 0 ]; then
        pass "$file has no unwrapped db.query() calls"
    else
        fail "$file has $unwrapped unwrapped db.query() calls"
    fi
}

check_no_unwrapped_query "app/api/v1/endpoints/toxic_behavior_detection.py"
check_no_unwrapped_query "app/api/v1/endpoints/activation.py"

echo ""

###############################################################################
# Phase 6: Endpoint Type Validation
###############################################################################
echo "🔌 Phase 6: Endpoint Type Validation"
echo "─────────────────────────────────────────────────────────────────────────────"

# Check endpoints use get_async_db
check_async_db_dep() {
    local file=$1

    if grep -q "get_async_db" "$file" 2>/dev/null; then
        pass "$file uses get_async_db dependency"
    else
        warn "$file may not use get_async_db"
    fi
}

check_async_db_dep "app/api/v1/endpoints/responses.py"
check_async_db_dep "app/api/v1/endpoints/feature_requests.py"
check_async_db_dep "app/api/v1/endpoints/activation.py"

echo ""

###############################################################################
# Final Summary
###############################################################################
echo "══════════════════════════════════════════════════════════════════════════════"
echo "VALIDATION SUMMARY"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""
echo -e "Tests Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "Tests Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║          ✅ ALL VALIDATION CHECKS PASSED! ✅                  ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║    The async conversion fixes are ready for deployment!      ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run unit tests:     pytest tests/api/test_async_response_endpoints.py -v"
    echo "  2. Run load tests:     python tests/load_test_async_endpoints.py"
    echo "  3. Deploy to staging:  ./scripts/deploy_staging.sh"
    echo "  4. Monitor production: Watch for 500 errors and performance metrics"
    echo ""
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║          ❌ SOME VALIDATION CHECKS FAILED ❌                  ║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║         Please fix the issues above before deploying          ║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 1
fi
