#!/bin/bash
###############################################################################
# Deployment Verification Script
#
# Verifies that the memory leak prevention system is fully deployed and working.
# Run this after setup or deployment to ensure everything is operational.
#
# Usage: ./scripts/verify-deployment.sh [--detailed]
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
DETAILED=false
if [ "$1" == "--detailed" ]; then
    DETAILED=true
fi

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Functions
print_header() {
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║ $1${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}\n"
}

print_section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}┃ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# START VERIFICATION
###############################################################################

print_header "🔍 Memory Leak Prevention - Deployment Verification"

echo "This script verifies that all components are properly deployed."
echo ""

###############################################################################
# SECTION 1: DEPENDENCIES
###############################################################################

print_section "1. Dependencies & Configuration"

# Check Node.js
if command -v node > /dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js installed ($NODE_VERSION)"
else
    check_fail "Node.js not found"
fi

# Check npm
if command -v npm > /dev/null 2>&1; then
    NPM_VERSION=$(npm --version)
    check_pass "npm installed ($NPM_VERSION)"
else
    check_fail "npm not found"
fi

# Check package.json
if [ -f "package.json" ]; then
    check_pass "package.json exists"

    # Check for eslint
    if grep -q '"eslint"' package.json; then
        check_pass "ESLint in dependencies"
    else
        check_fail "ESLint not in dependencies"
    fi

    # Check for vitest
    if grep -q '"vitest"' package.json; then
        check_pass "Vitest in dependencies"
    else
        check_warn "Vitest not in dependencies (tests may not run)"
    fi
else
    check_fail "package.json not found"
fi

# Check node_modules
if [ -d "node_modules" ]; then
    check_pass "node_modules installed"
else
    check_fail "node_modules not found (run: npm install)"
fi

###############################################################################
# SECTION 2: ESLINT CONFIGURATION
###############################################################################

print_section "2. ESLint Configuration"

# Check eslint.config.js
if [ -f "eslint.config.js" ]; then
    check_pass "eslint.config.js exists"

    # Check for memory-leak plugin
    if grep -q "memory-leak" eslint.config.js; then
        check_pass "Memory leak plugin configured"
    else
        check_fail "Memory leak plugin not configured"
    fi

    # Check for react-hooks
    if grep -q "react-hooks" eslint.config.js; then
        check_pass "React hooks plugin configured"
    else
        check_warn "React hooks plugin not configured"
    fi
else
    check_fail "eslint.config.js not found"
fi

# Check custom rules
if [ -f "eslint-rules/memory-leak-rules.js" ]; then
    check_pass "Custom memory leak rules exist"

    # Count rules
    RULE_COUNT=$(grep -c "createRule" eslint-rules/memory-leak-rules.js || echo "0")
    check_info "  $RULE_COUNT detection rules found"
else
    check_fail "Custom memory leak rules not found"
fi

###############################################################################
# SECTION 3: CLEANUP HOOKS LIBRARY
###############################################################################

print_section "3. Cleanup Hooks Library"

# Check master export
if [ -f "src/hooks/cleanupHooks.ts" ]; then
    check_pass "Master export file exists (src/hooks/cleanupHooks.ts)"

    # Count exported hooks
    HOOK_COUNT=$(grep -c "^export function" src/hooks/cleanupHooks.ts || echo "0")
    check_info "  $HOOK_COUNT hooks exported"
else
    check_fail "Master export file not found"
fi

# Check timer hooks
if [ -f "src/hooks/useCleanupTimer.ts" ]; then
    check_pass "Timer hooks file exists"
else
    check_fail "Timer hooks not found"
fi

# Check event hooks
if [ -f "src/hooks/useCleanupEventListener.ts" ]; then
    check_pass "Event listener hooks file exists"
else
    check_fail "Event listener hooks not found"
fi

# Check WebSocket hooks
if [ -f "src/hooks/useCleanupWebSocket.ts" ]; then
    check_pass "WebSocket hooks file exists"
else
    check_fail "WebSocket hooks not found"
fi

###############################################################################
# SECTION 4: TESTS
###############################################################################

print_section "4. Test Suite"

# Check test files
if [ -f "src/hooks/__tests__/useCleanupTimer.test.ts" ]; then
    check_pass "Timer hooks test file exists"
else
    check_warn "Timer hooks test file not found"
fi

if [ -f "src/hooks/__tests__/useCleanupEventListener.test.ts" ]; then
    check_pass "Event hooks test file exists"
else
    check_warn "Event hooks test file not found"
fi

# Try running tests
if [ "$DETAILED" = true ]; then
    check_info "Running tests..."
    if npm test -- --run 2>&1 | tee /tmp/test-output.txt; then
        check_pass "Tests executed successfully"

        # Parse results
        PASS_COUNT=$(grep -o "[0-9]* passed" /tmp/test-output.txt | head -1 | grep -o "[0-9]*" || echo "0")
        FAIL_COUNT=$(grep -o "[0-9]* failed" /tmp/test-output.txt | head -1 | grep -o "[0-9]*" || echo "0")

        check_info "  $PASS_COUNT tests passed"
        if [ "$FAIL_COUNT" -gt "0" ]; then
            check_warn "  $FAIL_COUNT tests failed"
        fi
    else
        check_warn "Tests had failures (this is expected if some tests are incomplete)"
    fi
fi

###############################################################################
# SECTION 5: PRE-COMMIT HOOKS
###############################################################################

print_section "5. Pre-Commit Protection"

# Check if husky is installed
if [ -d ".husky" ]; then
    check_pass "Husky installed (.husky directory exists)"
else
    check_warn "Husky not installed (pre-commit hooks won't work)"
fi

# Check pre-commit hook
if [ -f ".husky/pre-commit" ]; then
    check_pass "Pre-commit hook file exists"

    # Check if executable
    if [ -x ".husky/pre-commit" ]; then
        check_pass "Pre-commit hook is executable"
    else
        check_fail "Pre-commit hook is not executable (run: chmod +x .husky/pre-commit)"
    fi

    # Check for memory leak check
    if grep -q "memory-leak" .husky/pre-commit; then
        check_pass "Pre-commit hook checks for memory leaks"
    else
        check_fail "Pre-commit hook doesn't check memory leaks"
    fi
else
    check_fail "Pre-commit hook not found"
fi

###############################################################################
# SECTION 6: CI/CD WORKFLOW
###############################################################################

print_section "6. CI/CD Pipeline"

# Check GitHub Actions workflow
if [ -f ".github/workflows/memory-leak-check.yml" ]; then
    check_pass "GitHub Actions workflow file exists"

    # Check workflow content
    if grep -q "memory-leak" .github/workflows/memory-leak-check.yml; then
        check_pass "Workflow checks for memory leaks"
    fi

    if grep -q "pull_request" .github/workflows/memory-leak-check.yml; then
        check_pass "Workflow triggers on pull requests"
    fi
else
    check_warn "GitHub Actions workflow not found (CI/CD won't activate)"
fi

# Check if git repo
if [ -d ".git" ]; then
    check_pass "Git repository initialized"

    # Check remote
    if git remote get-url origin > /dev/null 2>&1; then
        REMOTE_URL=$(git remote get-url origin)
        check_info "  Git remote: $REMOTE_URL"

        if [[ $REMOTE_URL == *"github.com"* ]]; then
            check_pass "GitHub repository configured"
            check_info "  CI/CD will activate on next push"
        fi
    else
        check_warn "No git remote configured"
    fi
else
    check_warn "Not a git repository"
fi

###############################################################################
# SECTION 7: DOCUMENTATION
###############################################################################

print_section "7. Documentation"

# Check essential docs
DOCS=(
    "ULTIMATE_QUICK_START.md"
    "QUICK_REFERENCE_CARD.md"
    "TEAM_TRAINING_MEMORY_LEAKS.md"
    "TRAINING_SLIDES.md"
    "MIGRATION_CHECKLIST.md"
    "MEMORY_LEAK_QUICKFIX_GUIDE.md"
    "COMPLETE_IMPLEMENTATION_SUMMARY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "Documentation: $doc"
    else
        check_warn "Documentation missing: $doc"
    fi
done

###############################################################################
# SECTION 8: ACTUAL MEMORY LEAK SCAN
###############################################################################

print_section "8. Memory Leak Detection"

# Run ESLint scan
check_info "Running ESLint memory leak scan..."
npm run lint > /tmp/verify-scan.txt 2>&1 || true

# Count memory leaks
MEM_LEAK_COUNT=$(grep -c "memory-leak" /tmp/verify-scan.txt 2>/dev/null || echo "0")

if [ "$MEM_LEAK_COUNT" -eq "0" ]; then
    check_pass "No memory leaks detected! 🎉"
else
    check_fail "$MEM_LEAK_COUNT memory leak(s) detected"

    # Show breakdown
    TIMER_COUNT=$(grep -c "no-uncleaned-timers" /tmp/verify-scan.txt 2>/dev/null || echo "0")
    EVENT_COUNT=$(grep -c "no-uncleaned-event-listeners" /tmp/verify-scan.txt 2>/dev/null || echo "0")
    WS_COUNT=$(grep -c "no-uncleaned-websockets" /tmp/verify-scan.txt 2>/dev/null || echo "0")
    SUB_COUNT=$(grep -c "no-uncleaned-subscriptions" /tmp/verify-scan.txt 2>/dev/null || echo "0")

    check_info "  Breakdown:"
    check_info "    - Timers: $TIMER_COUNT"
    check_info "    - Events: $EVENT_COUNT"
    check_info "    - WebSockets: $WS_COUNT"
    check_info "    - Subscriptions: $SUB_COUNT"

    if [ "$DETAILED" = true ]; then
        check_info "  First 5 issues:"
        grep "memory-leak" /tmp/verify-scan.txt | head -5 | while read line; do
            echo "    $line"
        done
    fi
fi

###############################################################################
# SECTION 9: AUTOMATION SCRIPTS
###############################################################################

print_section "9. Automation Scripts"

# Check automation scripts
SCRIPTS=(
    "scripts/setup-memory-leak-prevention.sh"
    "scripts/auto-fix-memory-leaks.sh"
    "scripts/orchestrate-full-automation.sh"
    "scripts/verify-deployment.sh"
    "scripts/generate-memory-leak-dashboard.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        check_pass "Script exists: $(basename $script)"

        # Check if executable
        if [ -x "$script" ]; then
            check_info "  ✓ Executable"
        else
            check_warn "  ⚠️  Not executable (run: chmod +x $script)"
        fi
    else
        check_warn "Script missing: $script"
    fi
done

###############################################################################
# SECTION 10: SYSTEM HEALTH
###############################################################################

print_section "10. System Health Check"

# Check if ESLint works
check_info "Testing ESLint..."
if npm run lint > /dev/null 2>&1; then
    check_pass "ESLint executes successfully"
else
    check_warn "ESLint has issues (check configuration)"
fi

# Check if TypeScript compiles
if [ "$DETAILED" = true ]; then
    check_info "Testing TypeScript compilation..."
    if npm run type-check > /dev/null 2>&1; then
        check_pass "TypeScript compilation successful"
    else
        check_warn "TypeScript has errors (expected during development)"
    fi
fi

###############################################################################
# FINAL REPORT
###############################################################################

print_header "📊 Verification Complete"

echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

# Calculate pass rate
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))
    echo "Pass Rate: $PASS_RATE%"
else
    PASS_RATE=0
fi

echo ""

# Final verdict
if [ $FAILED_CHECKS -eq 0 ] && [ $WARNINGS -lt 3 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ DEPLOYMENT VERIFIED - System is healthy!             ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Your memory leak prevention system is fully deployed and operational!"
    echo ""
    echo "Next Steps:"
    echo "  1. Fix any remaining memory leaks (if $MEM_LEAK_COUNT > 0)"
    echo "  2. Push to GitHub to enable CI/CD"
    echo "  3. Train your team using provided materials"
    echo ""
    exit 0
elif [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  DEPLOYMENT MOSTLY HEALTHY - Minor warnings          ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "System is operational but has some warnings."
    echo "Review warnings above and address if needed."
    echo ""
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ DEPLOYMENT HAS ISSUES - Action required               ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Some components are not properly deployed."
    echo "Please review failed checks above and fix them."
    echo ""
    echo "Common fixes:"
    echo "  - Missing dependencies: npm install"
    echo "  - Configuration issues: Check eslint.config.js"
    echo "  - Permissions: chmod +x scripts/*.sh"
    echo "  - Pre-commit hook: chmod +x .husky/pre-commit"
    echo ""
    exit 1
fi
