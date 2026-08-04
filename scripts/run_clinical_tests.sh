#!/bin/bash

# =============================================================================
# Clinical Screening System Test Runner
# =============================================================================
# Runs all test suites for clinical screening functionality
# Usage: ./run_clinical_tests.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   PsychSync Clinical Screening Test Suite                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# =============================================================================
# LAYER 1: Unit Tests - Scoring Algorithms
# =============================================================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔬 LAYER 1: Unit Tests (Scoring Algorithms)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

pytest tests/test_clinical_scoring.py -v --tb=short --cov=app/services/clinical --cov-report=term-missing

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Unit tests passed!${NC}"
else
    echo -e "${RED}✗ Unit tests failed!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Press Enter to continue to Layer 2...${NC}"
read -r

# =============================================================================
# LAYER 2: API Tests - Endpoint Integration
# =============================================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 LAYER 2: API Tests (Endpoint Integration)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "${RED}✗ Backend is not running!${NC}"
    echo -e "${YELLOW}Start backend with: uvicorn app.main:app --reload${NC}"
    echo -e "${YELLOW}Skipping API tests...${NC}"
else
    pytest tests/api/test_clinical_screening_api.py -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ API tests passed!${NC}"
    else
        echo -e "${RED}✗ API tests failed!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Press Enter to continue to Layer 3...${NC}"
read -r

# =============================================================================
# LAYER 3: Integration Tests - Full User Flow
# =============================================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔄 LAYER 3: Integration Tests (Full User Flow)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

pytest tests/integration/test_clinical_screening.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests passed!${NC}"
else
    echo -e "${RED}✗ Integration tests failed!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ ALL TESTS PASSED! ✅                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Generate coverage report
echo -e "${BLUE}📊 Generating coverage report...${NC}"
pytest tests/ --cov=app/services/clinical --cov=app/api/v1/endpoints/screening --cov-report=html:htmlcov --cov-report=term

echo -e "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    TEST SUMMARY                              ${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ Layer 1: Unit Tests (Scoring)${NC}"
echo -e "${GREEN}✅ Layer 2: API Tests (Endpoints)${NC}"
echo -e "${GREEN}✅ Layer 3: Integration Tests (Full Flow)${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Review coverage report: htmlcov/index.html"
echo -e "   2. Run manual browser tests (see MANUAL_TESTING.md)"
echo -e "   3. Check test output logs above for any warnings"
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
