#!/bin/bash
###############################################################################
# Pre-Deployment Validation Script
# Validates all critical fixes before deployment
###############################################################################

set -e  # Exit on any error

echo "═══════════════════════════════════════════════════════════════"
echo "     PRE-DEPLOYMENT VALIDATION - PsychSync Platform"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASS++))
    elif [ $1 -eq 1 ]; then
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAIL++))
    else
        echo -e "${YELLOW}⚠ WARN${NC}: $2"
        ((WARN++))
    fi
}

###############################################################################
# Phase 1: Python Environment Validation
###############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Python Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_result 0 "Virtual environment active"
else
    print_result 2 "Virtual environment not active (recommended)"
fi

# Check critical dependencies
echo "Checking dependencies..."
dependencies=("fastapi" "pydantic" "sqlalchemy" "uuid")
for dep in "${dependencies[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        print_result 0 "$dep installed"
    else
        print_result 1 "$dep NOT installed"
    fi
done

echo ""

###############################################################################
# Phase 2: Backend Validation
###############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2: Backend Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test schema imports
echo "Testing schema imports..."
if python3 -c "from app.schemas.assessment import Assessment, Question, Section; print('✓ Schemas OK')" 2>/dev/null; then
    print_result 0 "Assessment schemas import"
else
    print_result 1 "Assessment schemas import FAILED"
fi

# Verify UUID types
echo "Verifying UUID type usage..."
uuid_check=$(python3 << 'EOF'
from app.schemas.assessment import Assessment, Question
from uuid import UUID

assessment_id = Assessment.__annotations__.get('id')
question_id = Question.__annotations__.get('id')

if assessment_id == UUID and question_id == UUID:
    print("PASS")
    exit(0)
else:
    print("FAIL")
    exit(1)
EOF
)
if [ "$uuid_check" == "PASS" ]; then
    print_result 0 "UUID types verified"
else
    print_result 1 "UUID type verification FAILED"
fi

# Test critical endpoint imports
echo "Testing endpoint imports..."
endpoints=("organizations" "teams")
for endpoint in "${endpoints[@]}"; do
    if python3 -c "from app.api.v1.endpoints.${endpoint} import router" 2>/dev/null; then
        print_result 0 "${endpoint} endpoint imports"
    else
        print_result 1 "${endpoint} endpoint import FAILED"
    fi
done

# Check for syntax errors
echo "Checking for syntax errors..."
if python3 -m py_compile app/main.py 2>/dev/null; then
    print_result 0 "main.py has no syntax errors"
else
    print_result 1 "main.py has syntax errors"
fi

echo ""

###############################################################################
# Phase 3: Rate Limiter Migration Validation
###############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3: Rate Limiter Migration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count files with old import
old_import_count=$(grep -r "from app.core.rate_limiter_unified import.*check_rate_limit" app/api/v1/endpoints/ 2>/dev/null | wc -l)
if [ "$old_import_count" -eq 0 ]; then
    print_result 0 "No old check_rate_limit imports found (all migrated)"
else
    print_result 1 "Found $old_import_count files still using old imports"
fi

# Check for new rate_limit usage
new_import_count=$(grep -r "from app.core.rate_limiter_unified import.*rate_limit" app/api/v1/endpoints/ 2>/dev/null | wc -l)
if [ "$new_import_count" -gt 0 ]; then
    print_result 0 "Found $new_import_count files using new rate_limit"
else
    print_result 2 "No files using new rate_limit (unexpected)"
fi

echo ""

###############################################################################
# Phase 4: Frontend Validation
###############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4: Frontend Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if node_modules exists
if [ -d "frontend/node_modules" ]; then
    print_result 0 "node_modules directory exists"
else
    print_result 1 "node_modules missing - run 'npm install' in frontend/"
    echo ""
    echo "⚠️  Skipping frontend tests - node_modules not found"
    echo ""
    # Continue to summary
    goto_summary=true
fi

if [ "$goto_summary" != true ]; then
    # Check for TypeScript
    if command -v npx &> /dev/null; then
        print_result 0 "TypeScript/npx available"

        # Run type check on modified files
        echo "Running TypeScript type check..."
        cd frontend

        # Check specific files we modified
        files_to_check=("src/utils/safeJSON.ts" "src/services/teamService.ts" "src/services/abTestingService.ts")
        all_ok=true

        for file in "${files_to_check[@]}"; do
            if [ -f "$file" ]; then
                if npx tsc --noEmit "$file" 2>/dev/null; then
                    echo "  ✓ $file"
                else
                    echo "  ✗ $file has type errors"
                    all_ok=false
                fi
            fi
        done

        if [ "$all_ok" = true ]; then
            print_result 0 "Modified files have no type errors"
        else
            print_result 1 "Some modified files have type errors"
        fi

        cd ..
    else
        print_result 2 "npx not available - skipping TypeScript checks"
    fi

    # Check for safeJSON utility
    if [ -f "frontend/src/utils/safeJSON.ts" ]; then
        print_result 0 "safeJSON.ts utility exists"
    else
        print_result 1 "safeJSON.ts utility NOT found"
    fi
fi

echo ""

###############################################################################
# Phase 5: Build Validation
###############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 5: Build Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if we can do a quick build test
if [ -d "frontend/node_modules" ] && command -v npm &> /dev/null; then
    echo "Testing frontend build (this may take a few minutes)..."
    cd frontend

    if timeout 180 npm run build > /tmp/frontend_build.log 2>&1; then
        print_result 0 "Frontend build completed successfully"

        # Check build output size
        if [ -d "dist/assets" ]; then
            total_size=$(du -sh dist | awk '{print $1}')
            echo "  Build size: $total_size"
        fi
    else
        print_result 1 "Frontend build FAILED - check /tmp/frontend_build.log"
    fi

    cd ..
else
    print_result 2 "Skipping build test (npm/node_modules not available)"
fi

echo ""

###############################################################################
# Summary
###############################################################################
: << 'EOF'
goto_summary=false
EOF

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                    VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}PASSED: $PASS${NC}"
echo -e "${RED}FAILED: $FAIL${NC}"
echo -e "${YELLOW}WARNINGS: $WARN${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}═════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}          ✅ ALL CRITICAL CHECKS PASSED${NC}"
    echo -e "${GREEN}              Ready for deployment!${NC}"
    echo -e "${GREEN}═════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review any warnings above"
    echo "  2. Run: bash scripts/deploy.sh"
    echo "  3. Monitor logs post-deployment"
    echo ""
    exit 0
else
    echo -e "${RED}═════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}          ⚠️  VALIDATION FAILED${NC}"
    echo -e "${RED}      Please fix the errors above before deploying${NC}"
    echo -e "${RED}═════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Failed checks:"
    echo "  1. Review errors marked with ✗ FAIL above"
    echo "  2. Fix the issues"
    echo "  3. Re-run this script"
    echo ""
    exit 1
fi
