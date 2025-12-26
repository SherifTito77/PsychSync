#!/bin/bash
# Supply Chain Security Verification Script
#
# This script validates that all supply chain security controls
# are properly implemented and functioning.
#
# Usage: ./scripts/verify-supply-chain-security.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

log_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASS++))
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAIL++))
}

log_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARN++))
}

log_info() {
    echo -e "${BLUE}ℹ INFO${NC}: $1"
}

# Header
echo "================================================"
echo "  PsychSync Supply Chain Security Verification"
echo "================================================"
echo ""

# ============================================================================
# 1. FILE STRUCTURE VERIFICATION
# ============================================================================
echo "[1/8] Verifying File Structure..."
echo ""

REQUIRED_FILES=(
    "scripts/generate-vex.py"
    "scripts/cve-monitor.py"
    "scripts/check-registry-policy.sh"
    ".github/workflows/security-ci.yml"
    ".github/workflows/signed-release.yml"
    ".github/workflows/cve-monitoring.yml"
    ".github/workflows/dependency-governance.yml"
    ".github/ephemeral-runners.yml"
    ".github/registry-policies.yml"
    "allowed-dependencies.txt"
    "frontend/allowed-dependencies.json"
    "docs/SUPPLY_CHAIN_SECURITY_V2.md"
    "docs/SUPPLY_CHAIN_QUICK_START.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_pass "File exists: $file"
    else
        log_fail "File missing: $file"
    fi
done

echo ""

# ============================================================================
# 2. WORKFLOW CONFIGURATION VERIFICATION
# ============================================================================
echo "[2/8] Verifying Workflow Configurations..."
echo ""

# Check security-ci.yml for VEX generation
if grep -q "generate-vex.py" .github/workflows/security-ci.yml 2>/dev/null; then
    log_pass "VEX generation integrated in security-ci.yml"
else
    log_fail "VEX generation NOT found in security-ci.yml"
fi

# Check signed-release.yml for SLSA provenance
if grep -q "slsa-framework/slsa-github-generator" .github/workflows/signed-release.yml 2>/dev/null; then
    log_pass "SLSA provenance generation configured"
else
    log_fail "SLSA provenance generation NOT configured"
fi

# Check cve-monitoring.yml schedule
if grep -q "cron: '0 */6 * * *'" .github/workflows/cve-monitoring.yml 2>/dev/null; then
    log_pass "CVE monitoring scheduled every 6 hours"
else
    log_warn "CVE monitoring schedule may not be optimal"
fi

# Check dependency-governance.yml for signature verification
if grep -q "sigstore" .github/workflows/dependency-governance.yml 2>/dev/null; then
    log_pass "Package signature verification configured"
else
    log_fail "Package signature verification NOT configured"
fi

echo ""

# ============================================================================
# 3. TOOL AVAILABILITY VERIFICATION
# ============================================================================
echo "[3/8] Verifying Security Tool Availability..."
echo ""

# Check for Python tools
PYTHON_TOOLS=("bandit" "pip-audit" "cyclonedx-py")
for tool in "${PYTHON_TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        log_pass "Tool available: $tool"
    else
        log_warn "Tool not found: $tool (will be installed in CI/CD)"
    fi
done

# Check for container tools
CONTAINER_TOOLS=("cosign" "docker")
for tool in "${CONTAINER_TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        log_pass "Tool available: $tool"
    else
        log_warn "Tool not found: $tool"
    fi
done

echo ""

# ============================================================================
# 4. ALLOW-LIST VERIFICATION
# ============================================================================
echo "[4/8] Verifying Dependency Allow-Lists..."
echo ""

# Check Python allow-list
if [ -f "allowed-dependencies.txt" ]; then
    PYTHON_COUNT=$(grep -E '^[a-zA-Z0-9_-]+' allowed-dependencies.txt | grep -v '^#' | wc -l | tr -d ' ')
    log_pass "Python allow-list contains $PYTHON_COUNT packages"

    # Check format
    if grep -E '==[0-9]+\.[0-9]+\.[0-9]+,[0-9]+\.[0-9]+\.[0-9]+' allowed-dependencies.txt | grep -v '^#' | wc -l | tr -d ' ' > 0; then
        log_pass "Python allow-list uses correct version format"
    else
        log_warn "Some Python dependencies may not have version ranges"
    fi
else
    log_fail "Python allow-list not found"
fi

# Check JavaScript allow-list
if [ -f "frontend/allowed-dependencies.json" ]; then
    if python3 -c "import json; json.load(open('frontend/allowed-dependencies.json'))" 2>/dev/null; then
        log_pass "JavaScript allow-list is valid JSON"

        # Count allowed dependencies
        JS_COUNT=$(python3 << 'EOF'
import json
with open('frontend/allowed-dependencies.json', 'r') as f:
    data = json.load(f)
    count = sum(len(cat) for cat in data.get('allowedDependencies', {}).values())
    print(count)
EOF
)
        log_pass "JavaScript allow-list contains $JS_COUNT packages"
    else
        log_fail "JavaScript allow-list has invalid JSON"
    fi
else
    log_fail "JavaScript allow-list not found"
fi

echo ""

# ============================================================================
# 5. REGISTRY POLICY VERIFICATION
# ============================================================================
echo "[5/8] Verifying Registry Policies..."
echo ""

# Check if registry policy file exists and is valid
if [ -f ".github/registry-policies.yml" ]; then
    log_pass "Registry policy file exists"

    # Check for allowed registries
    if grep -q "allowed_registries:" .github/registry-policies.yml; then
        log_pass "Allowed registries defined"

        # Count allowed registries
        ALLOWED_COUNT=$(grep -A 100 "allowed_registries:" .github/registry-policies.yml | grep -E "^\s+- url:" | wc -l | tr -d ' ')
        log_info "Found $ALLOWED_COUNT allowed registries"
    else
        log_fail "No allowed registries defined"
    fi

    # Check for blocked registries
    if grep -q "blocked_registries:" .github/registry-policies.yml; then
        log_pass "Blocked registries defined"
    else
        log_warn "No blocked registries defined"
    fi
else
    log_fail "Registry policy file not found"
fi

# Check if registry check script is executable
if [ -f "scripts/check-registry-policy.sh" ]; then
    if [ -x "scripts/check-registry-policy.sh" ]; then
        log_pass "Registry check script is executable"
    else
        log_warn "Registry check script not executable (run: chmod +x scripts/check-registry-policy.sh)"
    fi
else
    log_fail "Registry check script not found"
fi

echo ""

# ============================================================================
# 6. SBOM GENERATION VERIFICATION
# ============================================================================
echo "[6/8] Verifying SBOM Generation Capability..."
echo ""

# Check if cyclonedx is available
if command -v "cyclonedx-py" &> /dev/null; then
    log_pass "CycloneDX tool available"

    # Try to generate a test SBOM
    if [ -f "requirements.txt" ]; then
        log_info "Attempting to generate test SBOM..."
        if cyclonedx-py --format json --output /tmp/test-sbom.json -r . &> /dev/null; then
            log_pass "SBOM generation successful"

            # Verify SBOM format
            if python3 -c "import json; data = json.load(open('/tmp/test-sbom.json')); assert data['bomFormat'] == 'CycloneDX'" 2>/dev/null; then
                log_pass "SBOM format is valid CycloneDX"

                # Check component count
                COMPONENTS=$(python3 -c "import json; data = json.load(open('/tmp/test-sbom.json')); print(len(data.get('components', [])))" 2>/dev/null || echo "0")
                log_info "Test SBOM contains $COMPONENTS components"
            else
                log_fail "Generated SBOM has invalid format"
            fi
        else
            log_warn "SBOM generation failed (may need dependencies installed)"
        fi
    else
        log_warn "requirements.txt not found, skipping SBOM test"
    fi
else
    log_warn "CycloneDX tool not available (will be installed in CI/CD)"
fi

echo ""

# ============================================================================
# 7. VEX GENERATION VERIFICATION
# ============================================================================
echo "[7/8] Verifying VEX Generation Capability..."
echo ""

# Check if VEX script exists and is valid Python
if [ -f "scripts/generate-vex.py" ]; then
    log_pass "VEX generation script exists"

    # Check if script is syntactically valid
    if python3 -m py_compile scripts/generate-vex.py 2>/dev/null; then
        log_pass "VEX script is valid Python"

        # Check for required VEX classes
        if grep -q "class VEXGenerator" scripts/generate-vex.py; then
            log_pass "VEXGenerator class found"
        else
            log_fail "VEXGenerator class not found"
        fi

        # Check for OpenVEX format support
        if grep -q "openvex" scripts/generate-vex.py; then
            log_pass "OpenVEX format supported"
        else
            log_warn "OpenVEX format may not be supported"
        fi
    else
        log_fail "VEX script has syntax errors"
    fi
else
    log_fail "VEX generation script not found"
fi

# Check for VEX integration in CI/CD
if grep -q "generate-vex.py" .github/workflows/security-ci.yml 2>/dev/null; then
    log_pass "VEX generation integrated in CI/CD"
else
    log_fail "VEX generation NOT integrated in CI/CD"
fi

echo ""

# ============================================================================
# 8. DOCUMENTATION VERIFICATION
# ============================================================================
echo "[8/8] Verifying Documentation..."
echo ""

DOCS=(
    "docs/SUPPLY_CHAIN_SECURITY_V2.md"
    "docs/SUPPLY_CHAIN_QUICK_START.md"
    "docs/SECURITY_IMPLEMENTATION_SUMMARY.md"
    "docs/SECURITY_README.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        log_pass "Documentation exists: $(basename $doc)"

        # Check document size (should be substantial)
        SIZE=$(wc -c < "$doc" 2>/dev/null || echo "0")
        if [ "$SIZE" -gt 1000 ]; then
            log_info "  Document size: $(($SIZE / 1024))KB"
        fi
    else
        log_fail "Documentation missing: $doc"
    fi
done

# Check for SECURITY_INTEGRATION_GUIDE.md
if [ -f "COMPLETE_SECURITY_INTEGRATION_GUIDE.md" ]; then
    log_pass "Application security integration guide exists"
else
    log_warn "Application security integration guide not found"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "================================================"
echo "  VERIFICATION SUMMARY"
echo "================================================"
echo ""
echo -e "${GREEN}PASSED${NC}: $PASS checks"
echo -e "${YELLOW}WARNINGS${NC}: $WARN checks"
echo -e "${RED}FAILED${NC}: $FAIL checks"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Supply chain security implementation is complete."

    if [ $WARN -gt 0 ]; then
        echo ""
        echo "Note: There are $WARN warnings that should be addressed."
        echo "These are non-critical but should be reviewed for optimal security."
    fi

    exit 0
else
    echo -e "${RED}✗ Some critical checks failed${NC}"
    echo ""
    echo "Please address the failed checks before proceeding."
    echo "See documentation in docs/SUPPLY_CHAIN_QUICK_START.md for guidance."

    exit 1
fi
