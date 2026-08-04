#!/bin/bash

# Performance Monitoring Setup Validation Script
# Tests all components of the monitoring system

echo "================================================"
echo "Performance Monitoring Setup Validation"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to check test result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

# Test 1: Backend is running
echo "🔍 Test 1: Check if backend is running"
curl -s http://localhost:8000/health > /dev/null 2>&1
check_result $? "Backend server is running on port 8000"
echo ""

# Test 2: Test imports
echo "🔍 Test 2: Check Python imports"
python3 -c "
from app.monitoring.performance_dashboard import setup_sqlalchemy_monitoring, PerformanceMonitoringMiddleware
from app.api.v1.endpoints.performance_monitoring import router
" 2>/dev/null
check_result $? "Monitoring modules import successfully"
echo ""

# Test 3: Check main.py has setup code
echo "🔍 Test 3: Verify main.py configuration"
grep -q "setup_sqlalchemy_monitoring" app/main.py
check_result $? "main.py has SQLAlchemy monitoring setup"

grep -q "PerformanceMonitoringMiddleware" app/main.py
check_result $? "main.py has PerformanceMonitoringMiddleware"

grep -q "performance_router" app/main.py
check_result $? "main.py has performance router registered"
echo ""

# Test 4: Check frontend files exist
echo "🔍 Test 4: Check frontend components"
[ -f "frontend/src/components/admin/PerformanceMonitoringDashboard.tsx" ]
check_result $? "PerformanceMonitoringDashboard component exists"

[ -f "frontend/src/pages/PerformanceMonitoring.tsx" ]
check_result $? "PerformanceMonitoring page exists"
echo ""

# Test 5: Check route is registered
echo "🔍 Test 5: Verify frontend routing"
grep -q "PerformanceMonitoringPage" frontend/src/App.tsx
check_result $? "PerformanceMonitoringPage imported in App.tsx"

grep -q 'path="/admin/performance"' frontend/src/App.tsx
check_result $? "Route /admin/performance registered in App.tsx"

grep -q "Performance Monitoring" frontend/src/components/layout/Sidebar.tsx
check_result $? "Performance Monitoring link in sidebar"
echo ""

# Test 6: Test API endpoints (if backend running)
echo "🔍 Test 6: Test API endpoints (requires backend)"
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/monitoring/health 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo -e "${YELLOW}⚠️  SKIP${NC}: API returns $HTTP_CODE (authentication required - expected)"
    ((PASSED++))
elif [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC}: API returns 200 OK (authentication working or disabled)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: API returns unexpected code: $HTTP_CODE"
    ((FAILED++))
fi
echo ""

# Test 7: Check database indexes file exists
echo "🔍 Test 7: Database scalability fixes"
[ -f "alembic/versions/2025_02_10_add_scalability_indexes.py" ]
check_result $? "Database index migration file exists"
echo ""

# Summary
echo "================================================"
echo "Validation Summary"
echo "================================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start backend: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo "2. Start frontend: cd frontend && npm run dev"
    echo "3. Open: http://localhost:5173/admin/performance"
    echo ""
    echo "To test with authentication:"
    echo "  1. Get your admin token from browser DevTools (Application → Cookies)"
    echo "  2. Run: curl -H \"Authorization: Bearer YOUR_TOKEN\" http://localhost:8000/api/v1/monitoring/health"
    exit 0
else
    echo -e "${RED}❌ Some checks failed${NC}"
    echo "Please fix the errors above and run again"
    exit 1
fi
