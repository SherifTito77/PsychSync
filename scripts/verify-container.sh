#!/bin/bash
# Container Verification with cosign
# Verifies signed Docker images against public key

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PsychSync Container Verification                            ║"
echo "║     Verify image signatures and provenance                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
IMAGE_FULL="${1}"
PUBLIC_KEY="${PUBLIC_KEY:-cosign.pub}"

if [ -z "$IMAGE_FULL" ]; then
    echo -e "${RED}✗${NC}  Usage: $0 <image:tag>"
    echo ""
    echo "Example: $0 ghcr.io/psychsync/app:latest"
    echo ""
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Image:       ${IMAGE_FULL}"
echo "Public Key:  ${PUBLIC_KEY}"
echo ""

# Check if cosign is installed
if ! command -v cosign &> /dev/null; then
    echo -e "${RED}✗${NC}  cosign not installed"
    echo "Install with: brew install cosign"
    exit 1
fi

# Check if public key exists
if [ ! -f "$PUBLIC_KEY" ]; then
    echo -e "${RED}✗${NC}  Public key not found: ${PUBLIC_KEY}"
    echo ""
    echo "The public key should be distributed with the repository"
    echo "so that images can be verified."
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Verify Image Signature"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Verifying image signature..."
echo ""

# Verify the signature
if cosign verify \
    --key "$PUBLIC_KEY" \
    "$IMAGE_FULL" 2>&1; then

    echo ""
    echo -e "${GREEN}✓${NC}  Signature verification PASSED"
    echo ""
else
    echo ""
    echo -e "${RED}✗${NC}  Signature verification FAILED"
    echo ""
    echo -e "${YELLOW}⚠${NC}  This image may be tampered with or not signed by the expected key"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Check Rekor Transparency Log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking Rekor transparency log..."
echo ""

# Get Rekor UUID
REKOR_UUID=$(cosign triangulate \
    --type slsa \
    "$IMAGE_FULL" 2>&1 | grep "Entry UUID" | awk '{print $3}' || echo "")

if [ -n "$REKOR_UUID" ]; then
    echo -e "${GREEN}✓${NC}  Found Rekor entry"
    echo "UUID: ${REKOR_UUID}"
    echo ""

    # Verify entry exists in Rekor
    if command -v rekor-cli &> /dev/null; then
        echo "Full Rekor entry:"
        rekor-cli get --uuid "$REKOR_UUID" --format json | jq . 2>/dev/null || rekor-cli get --uuid "$REKOR_UUID"
    else
        echo -e "${YELLOW}⚠${NC}  rekor-cli not installed, cannot fetch full entry"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No Rekor entry found"
    echo "The signature may not be uploaded to the transparency log"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Verify SBOM Attestation (if present)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking for SBOM attestation..."
echo ""

# Try to get SBOM attestation
if cosign verify-attestation \
    --key "$PUBLIC_KEY" \
    --type spdxjson \
    "$IMAGE_FULL" 2>&1 | grep -q "spdx"; then

    echo -e "${GREEN}✓${NC}  SBOM attestation found"
    echo ""
    echo "Extracting SBOM..."
    cosign verify-attestation \
        --key "$PUBLIC_KEY" \
        --type spdxjson \
        "$IMAGE_FULL" | jq -r .payload | jq . > verified-sbom.json 2>/dev/null || echo "Could not extract SBOM"

    if [ -f "verified-sbom.json" ]; then
        echo "SBOM saved to: verified-sbom.json"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No SBOM attestation found"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${GREEN}✓${NC}  Image:          ${IMAGE_FULL}"
echo -e "${GREEN}✓${NC}  Signature:      VALID"
echo -e "${GREEN}✓${NC}  Public Key:     ${PUBLIC_KEY}"

if [ -n "$REKOR_UUID" ]; then
    echo -e "${GREEN}✓${NC}  Rekor Entry:    ${REKOR_UUID}"
fi

if [ -f "verified-sbom.json" ]; then
    echo -e "${GREEN}✓${NC}  SBOM:           verified-sbom.json"
fi

echo ""
echo -e "${GREEN}✓ Container is TRUSTED and VERIFIED${NC}"
echo ""

exit 0
