#!/bin/bash
# SAST Runner for PsychSync
# Runs Static Application Security Testing on every PR

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PsychSync SAST Runner                                      ║"
echo "║     Static Application Security Testing                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

HIGH_SEVERITY_FOUND=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Python SAST (Bandit)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if bandit is installed
if ! command -v bandit &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Bandit not installed, installing..."
    pip install bandit
fi

# Run bandit on Python code
echo "Running Bandit on Python code..."
echo ""

if bandit -r app/ -c .bandit -f json -o bandit-report.json 2>&1; then
    echo -e "${GREEN}✓${NC}  No high-severity issues found in Python code"
else
    BANDIT_EXIT=$?
    echo -e "${RED}✗${NC}  Bandit found security issues"

    # Parse JSON for high severity issues
    if [ -f bandit-report.json ]; then
        HIGH_COUNT=$(python3 << 'EOF'
import json
with open('bandit-report.json') as f:
    data = json.load(f)
    high = sum(1 for r in data.get('results', []) if r.get('issue_severity') == 'HIGH')
    print(high)
EOF
)
        HIGH_SEVERITY_FOUND=$HIGH_COUNT

        if [ "$HIGH_SEVERITY_FOUND" -gt 0 ]; then
            echo ""
            echo -e "${RED}✗ BLOCKING: $HIGH_SEVERITY_FOUND high-severity issues found${NC}"
            echo "See bandit-report.json for details"
            echo ""
            echo "Issues:"
            bandit -r app/ -c .bandit | grep ">> Issue:" | head -10
        fi
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "JavaScript SAST (ESLint Security Plugins)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if frontend exists
if [ -d "frontend" ]; then
    echo "Running ESLint security checks on frontend..."
    echo ""

    cd frontend

    # Check if npm dependencies are installed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    # Run ESLint with security rules
    if npm run lint 2>&1 | grep -q "error"; then
        echo -e "${YELLOW}⚠${NC}  ESLint found issues (review above)"
    else
        echo -e "${GREEN}✓${NC}  No critical linting issues"
    fi

    cd ..
else
    echo -e "${YELLOW}⚠${NC}  Frontend directory not found, skipping JavaScript SAST"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Secret Scanning (gitleaks)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if gitleaks is installed
if ! command -v gitleaks &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Gitleaks not installed, installing..."
    go install github.com/zricethezav/gitleaks/v8@latest || echo "Skipping gitleaks (Go not available)"
fi

if command -v gitleaks &> /dev/null; then
    echo "Scanning for secrets in code..."
    echo ""

    if gitleaks detect --source . --report-path gitleaks-report.json 2>&1; then
        echo -e "${GREEN}✓${NC}  No secrets found in code"
    else
        echo -e "${RED}✗ BLOCKING: Secrets detected in code${NC}"
        echo "See gitleaks-report.json for details"
        HIGH_SEVERITY_FOUND=1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$HIGH_SEVERITY_FOUND" -gt 0 ]; then
    echo -e "${RED}✗ SAST FAILED: High-severity issues must be fixed before merging${NC}"
    echo ""
    echo "Generated Reports:"
    echo "  • bandit-report.json - Python security issues"
    echo "  • gitleaks-report.json - Secret detection results"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ SAST PASSED: No blocking issues found${NC}"
    echo ""
    exit 0
fi
