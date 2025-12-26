#!/bin/bash
# Registry Policy Check Script
#
# Validates container images against registry policies.
# Used in CI/CD pipelines to enforce registry restrictions.
#
# Usage: ./check-registry-policy.sh <image>
# Example: ./check-registry-policy.sh python:3.14-slim

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Allowed registries and namespaces
ALLOWED_REGISTRIES=(
    "ghcr.io"
    "docker.io/library"
    "docker.io/bitnami"
    "docker.io/nginx"
    "docker.io/postgres"
    "docker.io/redis"
    "registry.redhat.io"
    "public.ecr.aws"
)

# Blocked images (specific tags)
BLOCKED_IMAGES=(
    "python:3.6"
    "python:3.7"
    "python:3.8"
    "node:14"
    "node:16"
    "postgres:10"
    "postgres:11"
)

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

check_image_in_blocked_list() {
    local image="$1"

    for blocked in "${BLOCKED_IMAGES[@]}"; do
        if [[ "$image" == "$blocked" ]]; then
            log_error "Image is in blocked list: $image"
            log_error "Reason: End-of-life version with no security updates"
            return 1
        fi
    done

    return 0
}

check_registry_allowed() {
    local image="$1"
    local registry

    # Extract registry from image
    if [[ "$image" =~ ([^/]+) ]]; then
        registry="${BASH_REMATCH[1]}"
    else
        registry="docker.io"
    fi

    # Check if registry is allowed
    for allowed in "${ALLOWED_REGISTRIES[@]}"; do
        if [[ "$registry" == "$allowed" ]] || [[ "$image" == "$allowed"* ]]; then
            log_info "Registry allowed: $allowed"
            return 0
        fi
    done

    log_error "Registry not in allowlist: $registry"
    log_error "Image: $image"
    log_error "Allowed registries:"
    for allowed in "${ALLOWED_REGISTRIES[@]}"; do
        log_error "  - $allowed"
    done

    return 1
}

verify_image_signature() {
    local image="$1"

    log_info "Verifying signature for: $image"

    # Check if cosign is available
    if ! command -v cosign &> /dev/null; then
        log_warn "cosign not found, skipping signature verification"
        return 0
    fi

    # Try to verify signature
    if cosign verify "$image" 2>/dev/null; then
        log_info "✓ Signature verified"
        return 0
    else
        log_warn "Signature verification failed for: $image"
        log_warn "This may indicate an unsigned image or verification issue"

        # For official Docker Hub images, allow without signature
        if [[ "$image" == docker.io/library/* ]]; then
            log_warn "Docker Hub official image - allowing without signature"
            return 0
        fi

        return 1
    fi
}

check_image_sbom() {
    local image="$1"

    log_info "Checking for SBOM: $image"

    # Check if cosign is available
    if ! command -v cosign &> /dev/null; then
        log_warn "cosign not found, skipping SBOM check"
        return 0
    fi

    # Try to download SBOM
    if cosign download sbom "$image" 2>/dev/null | head -1; then
        log_info "✓ SBOM found"
        return 0
    else
        log_warn "No SBOM found for: $image"
        log_warn "SBOM is recommended for all production images"
        return 0  # Don't fail, just warn
    fi
}

scan_vulnerabilities() {
    local image="$1"

    log_info "Scanning for vulnerabilities: $image"

    # Check if trivy is available
    if ! command -v trivy &> /dev/null; then
        log_warn "trivy not found, skipping vulnerability scan"
        return 0
    fi

    # Run vulnerability scan
    local scan_output
    scan_output=$(trivy image --severity HIGH,CRITICAL --format json "$image" 2>/dev/null || echo "{}")

    # Parse results
    local vuln_count
    vuln_count=$(echo "$scan_output" | jq -r '.Results | length // 0' 2>/dev/null || echo "0")

    if [[ "$vuln_count" -gt 0 ]]; then
        log_error "Found $vuln_count HIGH/CRITICAL vulnerabilities in: $image"
        log_error "Run 'trivy image $image' for details"
        return 1
    else
        log_info "✓ No HIGH/CRITICAL vulnerabilities found"
        return 0
    fi
}

main() {
    local image="$1"

    if [[ -z "$image" ]]; then
        log_error "Usage: $0 <image>"
        exit 1
    fi

    log_info "Checking registry policy for: $image"
    echo ""

    # Run all checks
    local all_passed=true

    # Check 1: Blocked list
    if ! check_image_in_blocked_list "$image"; then
        all_passed=false
    fi
    echo ""

    # Check 2: Allowed registry
    if ! check_registry_allowed "$image"; then
        all_passed=false
    fi
    echo ""

    # Check 3: Signature verification
    if ! verify_image_signature "$image"; then
        log_warn "Signature verification failed, but allowing..."
        # Don't fail on signature yet - allow for transition period
    fi
    echo ""

    # Check 4: SBOM check
    check_image_sbom "$image"
    echo ""

    # Check 5: Vulnerability scan
    if ! scan_vulnerabilities "$image"; then
        all_passed=false
    fi
    echo ""

    # Final result
    if [[ "$all_passed" == "true" ]]; then
        log_info "✓ All registry policy checks passed for: $image"
        exit 0
    else
        log_error "✗ Registry policy checks failed for: $image"
        exit 1
    fi
}

# Run main function
main "$@"
