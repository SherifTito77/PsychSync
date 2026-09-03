#!/bin/bash

###############################################################################
# Memory Leak Load Test Runner
#
# Quick script to launch browser-based memory leak testing
#
# Usage:
#   ./run-memory-test.sh          # Quick 2-minute test
#   ./run-memory-test.sh --full   # Full 10-minute test
###############################################################################

set -e

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_FILE="$FRONTEND_DIR/scripts/quick-memory-test.html"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🧪 PsychSync Memory Leak Load Test${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if test file exists
if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}❌ Error: Test file not found at $TEST_FILE${NC}"
    exit 1
fi

# Check if frontend is running
if ! curl -s http://localhost:5173 > /dev/null; then
    echo -e "${YELLOW}⚠️  Frontend not detected at http://localhost:5173${NC}"
    echo ""
    echo -e "${YELLOW}Starting frontend...${NC}"
    cd "$FRONTEND_DIR"
    npm run dev > /dev/null 2>&1 &
    DEV_PID=$!

    echo -e "${YELLOW}Waiting for frontend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null; then
            echo -e "${GREEN}✅ Frontend is ready!${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
fi

# Open the test file
echo -e "${BLUE}📋 Opening memory test in browser...${NC}"
echo ""

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$TEST_FILE"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$TEST_FILE" 2>/dev/null || google-chrome "$TEST_FILE" 2>/dev/null || firefox "$TEST_FILE"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start "$TEST_FILE"
else
    echo -e "${YELLOW}⚠️  Could not auto-open browser${NC}"
    echo -e "${YELLOW}Please open manually: $TEST_FILE${NC}"
fi

echo ""
echo -e "${GREEN}✅ Test opened in browser!${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📝 Instructions${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "1. Click the ⚡ Quick Test (2 min) button for fast validation"
echo "2. Or click ▶️ Start 10-Minute Test for thorough testing"
echo "3. Wait for the test to complete"
echo "4. Review the results:"
echo "   - ✅ PASS = Memory stable (< 50 MB growth)"
echo "   - ⚠️  WARN = Review before deploy (50-100 MB growth)"
echo "   - ❌ FAIL = Memory leak detected (> 100 MB growth)"
echo ""
echo "5. Download results JSON (automatic)"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📚 Resources${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📖 Full QA Guide:     docs/QA_LOAD_TESTING_GUIDE.md"
echo "🎓 Team Training:     docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md"
echo "🔧 Advanced Testing:  frontend/scripts/memory-leak-load-test.md"
echo ""
echo -e "${GREEN}Happy Testing! 🚀${NC}"
echo ""

# Keep script running if frontend was started
if [ ! -z "$DEV_PID" ]; then
    echo -e "${YELLOW}Frontend running in background (PID: $DEV_PID)${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    wait $DEV_PID
fi
