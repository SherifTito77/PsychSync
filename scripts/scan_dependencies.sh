#!/bin/bash
###############################################################################
# Dependency Vulnerability Scanning Script (NIST SSDF PO 3.1)
#
# Scans all dependencies for known vulnerabilities with automated
# vulnerability assessment, risk scoring, and remediation recommendations
#
# Usage: scripts/scan_dependencies.sh [--fail-on|--report-only]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/security-scans"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

FAIL_ON=false
REPORT_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fail-on)
            FAIL_ON=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fail-on] [--report-only]"
            exit 1
            ;;
    esac
done

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "========================================================================================================"
echo "   Dependency Vulnerability Scanning (NIST SSDF PO 3.1)"
echo "========================================================================================================"
echo ""
log_info "Output directory: $OUTPUT_DIR"
log_info "Timestamp: $TIMESTAMP"
echo ""

# Initialize counters
VULN_CRITICAL=0
VULN_HIGH=0
VULN_MEDIUM=0
VULN_LOW=0
VULN_TOTAL=0

# =============================================================================
# Python Dependency Scanning
# =============================================================================

log_info "Scanning Python dependencies..."

cd "$PROJECT_ROOT"

# Method 1: Using Safety (Python-focused)
log_info "Running Safety scanner..."

if command -v safety &> /dev/null; then
    safety check --json > "$OUTPUT_DIR/python-safety-$TIMESTAMP.json" || true

    # Parse JSON output
    python3 << EOF
import json
import sys

try:
    with open("$OUTPUT_DIR/python-safety-$TIMESTAMP.json", 'r') as f:
        data = json.load(f)

    vulns = data.get('vulnerabilities', [])

    critical = sum(1 for v in vulns if v.get('severity', 0) >= 9)
    high = sum(1 for v in vulns if 7 <= v.get('severity', 0) < 9)
    medium = sum(1 for v in vulns if 4 <= v.get('severity', 0) < 7)
    low = sum(1 for v in vulns if v.get('severity', 0) < 4)

    print(f"Critical: {critical}")
    print(f"High: {high}")
    print(f"Medium: {medium}")
    print(f"Low: {low}")
    print(f"Total: {len(vulns)}")

    # Write summary
    with open("$OUTPUT_DIR/python-safety-summary-$TIMESTAMP.txt", 'w') as f:
        f.write("Python Vulnerability Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Critical: {critical}\n")
        f.write(f"High: {high}\n")
        f.write(f"Medium: {medium}\n")
        f.write(f"Low: {low}\n")
        f.write(f"Total: {len(vulns)}\n")

    # Check if we should fail
    if critical > 0 or high > 0:
        print("CRITICAL or HIGH vulnerabilities found!", file=sys.stderr)
        if "$FAIL_ON" == "true":
            sys.exit(1)

except Exception as e:
    print(f"Error parsing Safety results: {e}")
    sys.exit(1)

EOF

    log_success "Python vulnerability scan completed"
else
    log_warning "Safety not installed. Skipping Python vulnerability scan."
fi

# Method 2: Using Trivy (comprehensive)
log_info "Running Trivy vulnerability scanner..."

if command -v trivy &> /dev/null; then
    # Scan Python dependencies
    trivy fs --severity CRITICAL,HIGH,MEDIUM \
        --format json \
        --output "$OUTPUT_DIR/python-trivy-$TIMESTAMP.json" \
        . || log_warning "Trivy scan failed"

    # Parse Trivy results
    python3 << EOF
import json
import sys

try:
    with open("$OUTPUT_DIR/python-trivy-$TIMESTAMP.json", 'r') as f:
        data = json.load(f)

    results = data.get('Results', [])

    critical = sum(1 for r in results if r.get('Vulnerabilities', 0) > 0 and any(v.get('Severity', '').upper() in ['CRITICAL', 'HIGH'] for v in r.get('Vulnerabilities', [])))
    high = sum(1 for r in results if any(v.get('Severity', '').upper() == 'HIGH' for v in r.get('Vulnerabilities', [])))
    medium = sum(1 for r in results if any(v.get('Severity', '').upper() == 'MEDIUM' for v in r.get('Vulnerabilities', [])))

    total_vulns = sum(len(r.get('Vulnerabilities', [])) for r in results)

    print(f"Critical/High: {critical + high}")
    print(f"Medium: {medium}")
    print(f"Total: {total_vulns}")

    # Write detailed report
    with open("$OUTPUT_DIR/python-trivy-report-$TIMESTAMP.txt", 'w') as f:
        f.write("Trivy Vulnerability Report\n")
        f.write("=" * 50 + "\n\n")

        for result in results:
            target = result.get('Target', 'unknown')
            vulns = result.get('Vulnerabilities', [])

            f.write(f"Target: {target}\n")
            f.write(f"Vulnerabilities: {len(vulns)}\n\n")

            for vuln in vulns[:10]:  # Limit to top 10
                f.write(f"  - {vuln.get('VulnerabilityID', 'Unknown')}\n")
                f.write(f"    Severity: {vuln.get('Severity', 'Unknown')}\n")
                f.write(f"    Package: {vuln.get('PkgName', 'Unknown')}\n")
                f.write(f"    Installed: {vuln.get('InstalledVersion', 'Unknown')}\n")
                f.write(f"    Fixed: {vuln.get('FixedVersion', 'Not fixed')}\n")
                f.write("\n")

    # Check for critical/high vulnerabilities
    if critical + high > 0:
        print("CRITICAL or HIGH vulnerabilities found!", file=sys.stderr)
        if "$FAIL_ON" == "true":
            sys.exit(1)

except Exception as e:
    print(f"Error parsing Trivy results: {e}")
    sys.exit(1)

EOF
else
    log_warning "Trivy not installed. Skipping Trivy scan."
fi

# =============================================================================
# Node.js Dependency Scanning
# =============================================================================

log_info "Scanning Node.js dependencies..."

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"

    # Method 1: npm audit (built-in)
    log_info "Running npm audit..."

    npm audit --production --json > "$OUTPUT_DIR/npm-audit-$TIMESTAMP.json" || true

    # Parse npm audit results
    python3 << EOF
import json
import sys

try:
    with open("$OUTPUT_DIR/npm-audit-$TIMESTAMP.json", 'r') as f:
        data = json.load(f)

    vulns = data.get('vulnerabilities', {})

    # Count by severity
    critical = len(vulns.get('critical', []))
    high = len(vulns.get('high', []))
    moderate = len(vulns.get('moderate', []))
    low = len(vulns.get('low', []))

    print(f"Critical: {critical}")
    print(f"High: {high}")
    print(f"Moderate: {moderate}")
    print(f"Low: {low}")

    # Write summary
    with open("$OUTPUT_DIR/npm-audit-summary-$TIMESTAMP.txt", 'w') as f:
        f.write("Node.js Vulnerability Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Critical: {critical}\n")
        f.write(f"High: {high}\n")
        f.write(f"Moderate: {moderate}\n")
        f.write(f"Low: {low}\n")

    if critical > 0 or high > 0:
        print("CRITICAL or HIGH vulnerabilities found!", file=sys.stderr)
        if "$FAIL_ON" == "true":
            sys.exit(1)

except Exception as e:
    print(f"Error parsing npm audit results: {e}")
    sys.exit(1)

EOF

    cd "$PROJECT_ROOT"
fi

# =============================================================================
# Bandit Security Linting (Python)
# =============================================================================

log_info "Running Bandit security linter..."

if command -v bandit &> /dev/null; then
    bandit -r app/ -f json -o "$OUTPUT_DIR/bandit-$TIMESTAMP.json" || true

    # Parse Bandit results
    python3 << EOF
import json
import sys

try:
    with open("$OUTPUT_DIR/bandit-$TIMESTAMP.json", 'r') as f:
        data = json.load(f)

    results = data.get('results', [])
    errors = data.get('errors', [])

    high = sum(1 for r in results if r.get('issue_severity', 'UNKNOWN') == 'HIGH')
    medium = sum(1 for r in results if r.get('issue_severity', 'UNKNOWN') == 'MEDIUM')
    low = sum(1 for r in results if r.get('issue_severity', 'UNKNOWN') == 'LOW')

    print(f"High: {high}")
    print(f"Medium: {medium}")
    print(f"Low: {low}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors detected:")
        for error in errors[:5]:
            print(f"  - {error}")

    if high > 0:
        print("\nHIGH severity security issues found!", file=sys.stderr)

except Exception as e:
    print(f"Error parsing Bandit results: {e}")

EOF
else
    log_warning "Bandit not installed. Skipping security linting."
fi

# =============================================================================
# Docker Image Scanning (if applicable)
# =============================================================================

log_info "Scanning Docker images..."

if command -v trivy &> /dev/null; then
    # Scan backend image
    if docker images | grep -q "psychsync-backend"; then
        log_info "Scanning psychsync-backend Docker image..."
        trivy image --format json --output "$OUTPUT_DIR/docker-backend-$TIMESTAMP.json" psychsync-backend:latest || true
    fi

    # Scan frontend image
    if docker images | grep -q "psychsync-frontend"; then
        log_info "Scanning psychsync-frontend Docker image..."
        trivy image --format json --output "$OUTPUT_DIR/docker-frontend-$TIMESTAMP.json" psychsync-frontend:latest || true
    fi
fi

# =============================================================================
# Generate Consolidated Report
# =============================================================================

log_info "Generating consolidated vulnerability report..."

python3 << EOF
import json
import os
from datetime import datetime

output_dir = "security-scans"
timestamp = "$TIMESTAMP"

# Gather all scan results
scan_results = {
    "scan_date": datetime.utcnow().isoformat() + "Z",
    "project": "PsychSync",
    "scans": {}
}

# Python Safety
if os.path.exists(f"{output_dir}/python-safety-summary-{timestamp}.txt"):
    with open(f"{output_dir}/python-safety-summary-{timestamp}.txt", 'r') as f:
        scan_results["scans"]["python_safety"] = f.read()

# npm Audit
if os.path.exists(f"{output_dir}/npm-audit-summary-{timestamp}.txt"):
    with open(f"{output_dir}/npm-audit-summary-{timestamp}.txt", 'r') as f:
        scan_results["scans"]["npm_audit"] = f.read()

# Trivy
if os.path.exists(f"{output_dir}/python-trivy-report-{timestamp}.txt"):
    with open(f"{output_dir}/python-trivy-report-{timestamp}.txt", 'r') as f:
        scan_results["scans"]["trivy"] = f.read()

# Bandit
# (Would parse bandit results here)

# Write consolidated report
report_file = f"{output_dir}/consolidated-report-{timestamp}.md"
with open(report_file, 'w') as f:
    f.write("# Dependency Vulnerability Scan Report\n\n")
    f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
    f.write("**Project:** PsychSync SaaS Platform\n\n")
    f.write("---\n\n")

    if "python_safety" in scan_results["scans"]:
        f.write("## Python Dependencies\n\n")
        f.write("```\n")
        f.write(scan_results["scans"]["python_safety"])
        f.write("\n```\n\n")

    if "npm_audit" in scan_results["scans"]:
        f.write("## Node.js Dependencies\n\n")
        f.write("```\n")
        f.write(scan_results["scans"]["npm_audit"])
        f.write("\n```\n\n")

    f.write("---\n\n")
    f.write("## Remediation Recommendations\n\n")
    f.write("1. **CRITICAL vulnerabilities:** Update immediately\n")
    f.write("2. **HIGH vulnerabilities:** Update within 7 days\n")
    f.write("3. **MEDIUM vulnerabilities:** Update within 30 days\n")
    f.write("4. **LOW vulnerabilities:** Update in next release cycle\n\n")
    f.write("## Actions Required\n\n")
    f.write("- Review detailed reports in: `security-scans/`\n")
    f.write("- Update vulnerable dependencies\n")
    f.write("- Re-run scans to verify fixes\n")
    f.write("- Update SBOMs after fixes\n")

print(f"✓ Generated: {report_file}")

EOF

echo ""
echo "========================================================================================================"
log_success "Vulnerability scanning completed!"
echo "========================================================================================================"
echo ""
log_info "Report Location: $OUTPUT_DIR"
echo ""
log_info "View Reports:"
echo "  cat $OUTPUT_DIR/consolidated-report-*.md"
echo ""
log_info "Next Steps:"
echo "1. Review vulnerability reports"
echo "2. Update vulnerable dependencies"
echo "3. Re-run: scripts/scan_dependencies.sh"
echo "4. Re-generate SBOMs: scripts/generate_sbom.sh"
echo ""
