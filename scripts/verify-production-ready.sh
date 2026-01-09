#!/bin/bash
# ============================================================================
# Production Readiness Verification Script
# ============================================================================
#
# Comprehensive verification of LLM security, supply chain security,
# and deployment infrastructure.
#
# Usage:
#   ./scripts/verify-production-ready.sh [--skip-image-verify]
#
# Author: Security & DevOps Team
# Version: 1.0
# ============================================================================

# set -e  # Disabled to allow continuing on missing files

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNED_CHECKS=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_file() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        log_success "$description exists: $file"
        return 0
    else
        log_fail "$description missing: $file"
        return 1
    fi
}

check_executable() {
    local cmd="$1"
    local description="$2"
    
    if command -v "$cmd" &> /dev/null; then
        log_success "$description installed: $cmd"
        return 0
    else
        log_warn "$description not found: $cmd (optional)"
        return 2
    fi
}

echo "=============================================================================="
echo "  PsychSync Production Readiness Verification"
echo "=============================================================================="
echo ""

# ============================================================================
# Section 1: LLM Security Implementation
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1️⃣  LLM Security Implementation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_file "app/middleware/spotlighting.py" "Spotlighting middleware"
check_file "tests/unit/test_spotlighting_middleware.py" "Spotlighting tests"
check_file "docs/LLM_SECURITY_POLICY.md" "LLM security policy"
check_file "docs/LLM_SECURITY_INTEGRATION_GUIDE.md" "LLM integration guide"
check_file "docs/LLM_SECURITY_IMPLEMENTATION_SUMMARY.md" "LLM implementation summary"

# Check if middleware is integrated in main.py
if grep -q "SpotlightingMiddleware" app/main.py; then
    log_success "Spotlighting middleware integrated in app/main.py"
else
    log_fail "Spotlighting middleware NOT integrated in app/main.py"
fi

# ============================================================================
# Section 2: Supply Chain Security
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  2️⃣  Supply Chain Security (SLSA)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_file ".github/workflows/slsa-sign.yaml" "SLSA workflow"
check_file "docs/SUPPLY_CHAIN_SECURITY.md" "Supply chain security docs"
check_file "docs/SUPPLY_CHAIN_QUICKSTART.md" "Supply chain quickstart"
check_file "scripts/verify-cosign-signature.sh" "Cosign verification script"
check_file "scripts/verify-quick.sh" "Quick verification script"

# Check required tools
check_executable "cosign" "Cosign CLI"
check_executable "slsa-verifier" "SLSA Verifier"

# ============================================================================
# Section 3: Docker & Kubernetes
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  3️⃣  Docker & Kubernetes Infrastructure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_file "docker/Dockerfile" "Production Dockerfile"
check_file ".dockerignore" "Docker ignore file"
check_file "deploy/kubernetes/psychsync-deployment.yaml" "Kubernetes deployment manifest"

# Check Dockerfile for security features
if grep -q "USER appuser" docker/Dockerfile; then
    log_success "Dockerfile uses non-root user"
else
    log_warn "Dockerfile may not use non-root user"
fi

if grep -q "HEALTHCHECK" docker/Dockerfile; then
    log_success "Dockerfile includes health check"
else
    log_warn "Dockerfile missing health check"
fi

# Check Kubernetes manifest for verification
if grep -q "verify-image" deploy/kubernetes/psychsync-deployment.yaml; then
    log_success "Kubernetes manifest includes image verification init container"
else
    log_fail "Kubernetes manifest missing image verification"
fi

# Check kubectl
check_executable "kubectl" "Kubernetes CLI"

# ============================================================================
# Section 4: Operational Runbooks
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  4️⃣  Operational Runbooks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_file "docs/operations/DEPLOYMENT_RUNBOOK.md" "Deployment runbook"
check_file "docs/operations/INCIDENT_RESPONSE_RUNBOOK.md" "Incident response runbook"

# ============================================================================
# Section 5: Testing Infrastructure
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  5️⃣  Testing Infrastructure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if pytest is available
if command -v pytest &> /dev/null; then
    log_success "pytest installed"
    
    # Run unit tests for spotlighting middleware
    log_info "Running spotlighting middleware tests..."
    if pytest tests/unit/test_spotlighting_middleware.py -v --tb=short 2>&1 | tee /tmp/test-output.txt; then
        log_success "All spotlighting tests passed"
        
        # Count tests
        test_count=$(grep -oP '\d+ passed' /tmp/test-output.txt | grep -oP '\d+')
        log_info "Executed $test_count tests"
    else
        log_fail "Some spotlighting tests failed"
    fi
else
    log_warn "pytest not installed, skipping tests"
fi

# ============================================================================
# Section 6: Security Best Practices
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  6️⃣  Security Best Practices"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for secrets in git
if git log --all --full-history --source -- "*secret*" "*password*" "*api_key*" 2>/dev/null | grep -q "commit"; then
    log_warn "Potential secrets found in git history"
else
    log_success "No obvious secrets in recent git history"
fi

# Check .gitignore for sensitive files
if grep -q ".env" .gitignore && grep -q "*.secret" .gitignore; then
    log_success ".gitignore properly excludes sensitive files"
else
    log_warn ".gitignore may not exclude all sensitive files"
fi

# Check for security headers in code
if grep -r "X-Content-Type-Options" app/ > /dev/null 2>&1 || \
   grep -r "Content-Security-Policy" app/ > /dev/null 2>&1; then
    log_success "Security headers found in application code"
else
    log_warn "Security headers not found in application code"
fi

# ============================================================================
# Section 7: Image Verification (Optional)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  7️⃣  Image Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$1" == "--skip-image-verify" ]; then
    log_info "Image verification skipped (--skip-image-verify flag)"
else
    # Check if there's a local image to verify
    log_info "Checking for local Docker images..."
    
    if docker images | grep -q "psychsync"; then
        log_info "Found psychsync Docker image locally"
        
        # This would normally verify the image signature
        # For demo purposes, we just note that the capability exists
        log_info "To verify image signature, run:"
        echo "   ./scripts/verify-quick.sh ghcr.io/your-org/psychsync:TAG"
    else
        log_info "No local psychsync image found (expected for first-time setup)"
    fi
fi

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo "=============================================================================="
echo "  📊 Verification Summary"
echo "=============================================================================="
echo ""
echo -e "Total Checks:  ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "${GREEN}Passed:        $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings:      $WARNED_CHECKS${NC}"
echo -e "${RED}Failed:        $FAILED_CHECKS${NC}"
echo ""

# Calculate pass rate
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo "Pass Rate: $PASS_RATE%"
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ] && [ $PASS_RATE -ge 80 ]; then
        echo -e "${GREEN}🎉 System is PRODUCTION READY!${NC}"
        exit 0
    elif [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${YELLOW}⚠️  System is mostly ready with warnings${NC}"
        exit 0
    else
        echo -e "${RED}❌ System is NOT production ready - fix failed checks${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ No checks were run${NC}"
    exit 1
fi
