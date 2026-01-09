#!/bin/bash
# Week 1 Critical Fixes Verification Script
# Checks all fixes from the 30-day action plan (Day 1-5)

set -e

echo "🔍 Week 1 Critical Fixes Verification"
echo "======================================"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASS=0
FAIL=0
WARN=0

# 1. Security fixes - PyTorch version
echo "1️⃣ Checking security fixes..."
echo "   PyTorch version check:"

if command -v python3 &> /dev/null; then
    PYTORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "NOT_INSTALLED")

    if [[ "$PYTORCH_VERSION" == "NOT_INSTALLED" ]]; then
        echo -e "   ${YELLOW}⚠️  PyTorch not installed in current environment${NC}"
        echo -e "   ${YELLOW}   (This is OK if AI features are optional)${NC}"
        WARN=$((WARN + 1))
    else
        # Compare versions (simple string comparison for major.minor)
        PYTORCH_MAJOR=$(echo $PYTORTH_VERSION | cut -d. -f1)
        PYTORCH_MINOR=$(echo $PYTORCH_VERSION | cut -d. -f2)

        if [[ "$PYTORCH_MAJOR" -gt 2 ]] || [[ "$PYTORCH_MAJOR" -eq 2 && "$PYTORCH_MINOR" -ge 6 ]]; then
            echo -e "   ${GREEN}✅ PyTorch: $PYTORCH_VERSION (>= 2.6.0)${NC}"
            PASS=$((PASS + 1))
        else
            echo -e "   ${RED}❌ PyTorch: $PYTORCH_VERSION (< 2.6.0)${NC}"
            FAIL=$((FAIL + 1))
        fi
    fi
else
    echo -e "   ${YELLOW}⚠️  Python3 not found${NC}"
    WARN=$((WARN + 1))
fi

# Check requirements.txt files
echo "   Checking requirements.txt files..."
VULNERABLE_COUNT=0
for req_file in requirements.txt requirements-ai.txt docs/requirements_nlp.txt; do
    if [ -f "$req_file" ]; then
        if grep -q "torch==2.1.0" "$req_file" 2>/dev/null; then
            echo -e "   ${RED}❌ $req_file still has torch==2.1.0${NC}"
            FAIL=$((FAIL + 1))
            VULNERABLE_COUNT=$((VULNERABLE_COUNT + 1))
        fi
        if grep -q "transformers==4.3" "$req_file" 2>/dev/null; then
            echo -e "   ${RED}❌ $req_file has vulnerable transformers${NC}"
            FAIL=$((FAIL + 1))
            VULNERABLE_COUNT=$((VULNERABLE_COUNT + 1))
        fi
    fi
done

if [ $VULNERABLE_COUNT -eq 0 ]; then
    echo -e "   ${GREEN}✅ All requirements files updated${NC}"
    PASS=$((PASS + 1))
fi

# 2. Security backdoor removed
echo
echo "2️⃣ Checking for security backdoors..."
BACKDOOR_FILES=0

if [ -f "app/api/v1/endpoints/standalone_auth.py" ]; then
    echo -e "   ${RED}❌ standalone_auth.py still exists!${NC}"
    FAIL=$((FAIL + 1))
    BACKDOOR_FILES=$((BACKDOOR_FILES + 1))
fi

# Check for any backup files
BACKUP_COUNT=$(find app/api/v1/endpoints -name "*standalone_auth*" 2>/dev/null | wc -l)
if [ $BACKUP_COUNT -gt 0 ]; then
    echo -e "   ${RED}❌ Found $BACKUP_COUNT standalone_auth backup files${NC}"
    FAIL=$((FAIL + 1))
    BACKDOOR_FILES=$((BACKDOOR_FILES + 1))
fi

if [ $BACKDOOR_FILES -eq 0 ]; then
    echo -e "   ${GREEN}✅ No security backdoor files found${NC}"
    PASS=$((PASS + 1))
fi

# 3. Dead code removed
echo
echo "3️⃣ Checking for dead code..."
DEAD_COUNT=0

# Check for common dead code patterns
for pattern in "*_backup.py" "*_broken.py" "*_old.py"; do
    COUNT=$(find app/ -name "$pattern" 2>/dev/null | wc -l)
    if [ $COUNT -gt 0 ]; then
        echo -e "   ${RED}❌ Found $COUNT files matching $pattern${NC}"
        FAIL=$((FAIL + 1))
        DEAD_COUNT=$((DEAD_COUNT + 1))
    fi
done

# Check for .bak files
BAK_COUNT=$(find app/ -name "*.py.bak" 2>/dev/null | wc -l)
if [ $BAK_COUNT -gt 0 ]; then
    echo -e "   ${RED}❌ Found $BAK_COUNT .bak files${NC}"
    FAIL=$((FAIL + 1))
    DEAD_COUNT=$((DEAD_COUNT + 1))
fi

if [ $DEAD_COUNT -eq 0 ]; then
    echo -e "   ${GREEN}✅ No dead code files found${NC}"
    PASS=$((PASS + 1))
fi

# 4. Print statements replaced
echo
echo "4️⃣ Checking for print statements..."
PRINT_COUNT=$(grep -r "print(" app/ --include="*.py" 2>/dev/null | grep -v test_ | grep -v __pycache__ | wc -l)

if [ $PRINT_COUNT -gt 100 ]; then
    echo -e "   ${YELLOW}⚠️  Still found $PRINT_COUNT print statements (target: < 100)${NC}"
    echo -e "   ${YELLOW}   (Some print statements may be legitimate)${NC}"
    WARN=$((WARN + 1))
else
    echo -e "   ${GREEN}✅ Print statements mostly replaced ($PRINT_COUNT remaining)${NC}"
    PASS=$((PASS + 1))
fi

# Check for logger imports
LOGGER_IMPORTS=$(grep -r "import logging" app/ --include="*.py" 2>/dev/null | wc -l)
echo -e "   ${GREEN}   Found $LOGGER_IMPORTS files with logging imports${NC}"

# 5. Database indexes (only if DB is running)
echo
echo "5️⃣ Checking database indexes..."

if docker-compose ps db 2>/dev/null | grep -q "Up"; then
    INDEX_COUNT=$(docker-compose exec -T db psql -U postgres -d psychsync -t -c "
        SELECT COUNT(*) FROM pg_indexes
        WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
    " 2>/dev/null | tr -d ' ' || echo "0")

    if [ $INDEX_COUNT -ge 20 ]; then
        echo -e "   ${GREEN}✅ Found $INDEX_COUNT performance indexes${NC}"
        PASS=$((PASS + 1))

        # Show some example indexes
        echo "   Sample indexes:"
        docker-compose exec -T db psql -U postgres -d psychsync -c "
            SELECT indexname, tablename FROM pg_indexes
            WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
            LIMIT 5;
        " 2>/dev/null | grep -v "indexname\|rows\|---" | sed 's/^/     /'
    else
        echo -e "   ${YELLOW}⚠️  Found $INDEX_COUNT indexes (expected 20+)${NC}"
        echo -e "   ${YELLOW}   Run: ./scripts/apply_performance_indexes.sh${NC}"
        WARN=$((WARN + 1))
    fi
else
    echo -e "   ${YELLOW}⚠️  Database not running, cannot verify indexes${NC}"
    echo -e "   ${YELLOW}   Run: docker-compose up -d db && ./scripts/apply_performance_indexes.sh${NC}"
    WARN=$((WARN + 1))
fi

# 6. Code still works - import check
echo
echo "6️⃣ Checking code imports..."

if python3 -c "from app.main import app" 2>/dev/null; then
    echo -e "   ${GREEN}✅ Backend imports successfully${NC}"
    PASS=$((PASS + 1))
else
    echo -e "   ${RED}❌ Backend import failed${NC}"
    echo -e "   ${RED}   Run: python3 -c 'from app.main import app' to debug${NC}"
    FAIL=$((FAIL + 1))
fi

# Summary
echo
echo "======================================"
echo -e "${GREEN}✅ PASSED: $PASS${NC} | ${RED}❌ FAILED: $FAIL${NC} | ${YELLOW}⚠️  WARNINGS: $WARN${NC}"
echo "======================================"
echo

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 Week 1 verification PASSED!${NC}"
    echo
    echo "Next steps:"
    echo "  • If database is running: ./scripts/apply_performance_indexes.sh"
    echo "  • Continue to Week 2: Async cache implementation"
    echo "  • See docs/CRITICAL_ISSUES_ACTION_PLAN.md for details"
    exit 0
else
    echo -e "${RED}❌ Week 1 verification FAILED${NC}"
    echo
    echo "Please fix the failed items above before proceeding."
    exit 1
fi
