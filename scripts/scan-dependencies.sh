#!/bin/bash
###############################################################################
# Comprehensive Dependency Vulnerability Scanner
# Scans both npm (frontend) and pip (backend) dependencies
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
FRONTEND_DIR="frontend"
BACKEND_DIR="."
REPORT_DIR="security-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create report directory
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}🔍 PsychSync Dependency Security Scanner${NC}"
echo "=========================================="
echo ""

###############################################################################
# Frontend (npm) Dependency Scanning
###############################################################################

echo -e "${BLUE}[1/3] Scanning Frontend Dependencies (npm)...${NC}"

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"

    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}⚠️  npm not found, skipping frontend scan${NC}"
    else
        # Run npm audit
        echo "Running npm audit..."
        if npm audit --json > "../$REPORT_DIR/npm-audit-$TIMESTAMP.json" 2>/dev/null; then
            echo -e "${GREEN}✅ No vulnerabilities found${NC}"
        else
            VULN_COUNT=$(npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities.info + .metadata.vulnerabilities.low + .metadata.vulnerabilities.moderate + .metadata.vulnerabilities.high + .metadata.vulnerabilities.critical // 0')

            if [ "$VULN_COUNT" -gt 0 ]; then
                echo -e "${RED}❌ Found $VULN_COUNT vulnerabilities${NC}"
                echo "Report saved to: $REPORT_DIR/npm-audit-$TIMESTAMP.json"

                # Check for critical/high vulnerabilities
                CRITICAL=$(npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities.critical // 0')
                HIGH=$(npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities.high // 0')

                if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
                    echo -e "${RED}🚨 CRITICAL/HIGH vulnerabilities detected!${NC}"
                    echo "Run 'npm audit fix' in $FRONTEND_DIR to attempt automatic fixes"
                fi
            fi
        fi

        # Check for outdated packages
        echo "Checking for outdated packages..."
        npm outdated --json > "../$REPORT_DIR/npm-outdated-$TIMESTAMP.json" 2>/dev/null || true

        cd ..
    fi
else
    echo -e "${YELLOW}⚠️  Frontend directory not found: $FRONTEND_DIR${NC}"
fi

echo ""

###############################################################################
# Backend (pip) Dependency Scanning
###############################################################################

echo -e "${BLUE}[2/3] Scanning Backend Dependencies (pip)...${NC}"

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip-audit not found, installing...${NC}"
    pip install pip-audit
fi

# Run pip-audit
echo "Running pip-audit..."
if pip-audit --format json --output "$REPORT_DIR/pip-audit-$TIMESTAMP.json" --desc json 2>/dev/null; then
    echo -e "${GREEN}✅ No vulnerabilities found${NC}"
else
    # Count vulnerabilities
    if command -v jq &> /dev/null; then
        VULN_COUNT=$(cat "$REPORT_DIR/pip-audit-$TIMESTAMP.json" | jq '. | length' 2>/dev/null || echo "0")

        if [ "$VULN_COUNT" -gt 0 ]; then
            echo -e "${RED}❌ Found $VULN_COUNT vulnerabilities${NC}"
            echo "Report saved to: $REPORT_DIR/pip-audit-$TIMESTAMP.json"

            # Show details
            echo ""
            echo "Vulnerable packages:"
            cat "$REPORT_DIR/pip-audit-$TIMESTAMP.json" | jq -r '.[] | "\(.name)@\(.version): \(.vulnerabilities[0].id)"' 2>/dev/null || true

            echo ""
            echo -e "${YELLOW}Run 'pip install --upgrade <package>' to fix${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  jq not found, cannot parse vulnerability count${NC}"
        echo "Report saved to: $REPORT_DIR/pip-audit-$TIMESTAMP.json"
    fi
fi

# Check for safety (alternative to pip-audit)
if command -v safety &> /dev/null; then
    echo "Running safety check..."
    safety check --json > "$REPORT_DIR/safety-report-$TIMESTAMP.json" 2>/dev/null || true
fi

echo ""

###############################################################################
# Generate Summary Report
###############################################################################

echo -e "${BLUE}[3/3] Generating Summary Report...${NC}"

SUMMARY_FILE="$REPORT_DIR/security-summary-$TIMESTAMP.txt"

cat > "$SUMMARY_FILE" << EOF
PsychSync Security Scan Summary
===============================
Date: $(date)
Timestamp: $TIMESTAMP

FRONTEND (npm)
--------------
EOF

if [ -f "$REPORT_DIR/npm-audit-$TIMESTAMP.json" ]; then
    if command -v jq &> /dev/null; then
        cat "$REPORT_DIR/npm-audit-$TIMESTAMP.json" | jq -r '
            "Vulnerabilities:
              - Critical: \(.metadata.vulnerabilities.critical // 0)
              - High: \(.metadata.vulnerabilities.high // 0)
              - Medium: \(.metadata.vulnerabilities.moderate // 0)
              - Low: \(.metadata.vulnerabilities.low // 0)
              - Info: \(.metadata.vulnerabilities.info // 0)
            Total Dependencies: \(.metadata.dependencies.total)"' >> "$SUMMARY_FILE" 2>/dev/null
    fi
fi

cat >> "$SUMMARY_FILE" << EOF

BACKEND (pip)
-------------

EOF

if [ -f "$REPORT_DIR/pip-audit-$TIMESTAMP.json" ]; then
    if command -v jq &> /dev/null; then
        VULN_COUNT=$(cat "$REPORT_DIR/pip-audit-$TIMESTAMP.json" | jq '. | length' 2>/dev/null || echo "0")
        echo "Total Vulnerabilities: $VULN_COUNT" >> "$SUMMARY_FILE"
    fi
fi

cat >> "$SUMMARY_FILE" << EOF

RECOMMENDATIONS
----------------
1. Review all reports in $REPORT_DIR
2. Update packages with critical/high vulnerabilities immediately
3. Run 'npm audit fix' for frontend vulnerabilities
4. Run 'pip install --upgrade <package>' for backend vulnerabilities
5. Consider pinning dependency versions in requirements.txt
6. Set up automated scanning in CI/CD pipeline

FILES GENERATED
--------------
- npm-audit-$TIMESTAMP.json
- npm-outdated-$TIMESTAMP.json
- pip-audit-$TIMESTAMP.json
- safety-report-$TIMESTAMP.json (if safety is installed)
- security-summary-$TIMESTAMP.txt
EOF

echo -e "${GREEN}✅ Summary report generated: $SUMMARY_FILE${NC}"
echo ""

# Display summary
cat "$SUMMARY_FILE"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}✅ Security scan complete!${NC}"
echo ""
echo "Reports saved to: $REPORT_DIR"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the vulnerability reports"
echo "2. Fix critical/high vulnerabilities"
echo "3. Update package versions where needed"
echo "4. Commit the fixed versions"
echo ""
echo -e "${YELLOW}To fix vulnerabilities automatically:${NC}"
echo "  Frontend: cd $FRONTEND_DIR && npm audit fix"
echo "  Backend:  pip install --upgrade <package-name>"
echo ""
