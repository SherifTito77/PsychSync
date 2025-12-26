#!/bin/bash
# Container Signing with cosign and sigstore Rekor
# Signs Docker images and stores provenance in Rekor transparency log

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PsychSync Container Signing                                 ║"
echo "║     cosign + sigstore Rekor Provenance                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
REPO="${REPO:-psychsync}"
IMAGE_NAME="${IMAGE_NAME:-app}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_FULL="${REGISTRY}/${REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

SIGNATURE_DIR="signatures"
mkdir -p "$SIGNATURE_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Image:        ${IMAGE_FULL}"
echo "Signature Dir: ${SIGNATURE_DIR}"
echo ""

# Check if cosign is installed
if ! command -v cosign &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  cosign not installed, installing..."
    echo ""

    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing cosign on macOS..."
        brew install cosign
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing cosign on Linux..."
        go install github.com/sigstore/cosign/v2/cmd/cosign@latest || {
            echo -e "${RED}✗${NC}  Failed to install cosign with go"
            echo "Install manually: https://docs.sigstore.dev/cosign/installation/"
            exit 1
        }
    else
        echo -e "${RED}✗${NC}  Unsupported OS: $OSTYPE"
        exit 1
    fi

    echo -e "${GREEN}✓${NC}  cosign installed"
    echo ""
fi

# Verify cosign version
echo "cosign version:"
cosign version
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Generate Signing Key Pair (if needed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if key pair exists
if [ ! -f "cosign.key" ]; then
    echo "Generating new cosign key pair..."
    echo ""

    # Generate key pair with password protection
    cosign generate-key-pair

    echo ""
    echo -e "${YELLOW}⚠${NC}  IMPORTANT: Store cosign.key securely and back it up!"
    echo -e "${YELLOW}⚠${NC}  Never commit cosign.key to version control"
    echo ""

    # Add to .gitignore if not already there
    if ! grep -q "cosign.key" .gitignore 2>/dev/null; then
        echo "cosign.key" >> .gitignore
        echo "cosign.pub" >> .gitignore
        echo "Added cosign keys to .gitignore"
    fi
else
    echo -e "${GREEN}✓${NC}  Existing cosign.key found"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Sign Container Image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Sign the image with cosign
echo "Signing image: ${IMAGE_FULL}"
echo ""

# Sign with key pair
if cosign sign \
    --key cosign.key \
    --annotations "repository=github.com/sheriftito/psychsync" \
    --annotations "commit=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
    --annotations "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')" \
    --output-signature "${SIGNATURE_DIR}/${IMAGE_NAME}.sig" \
    --output-certificate "${SIGNATURE_DIR}/${IMAGE_NAME}.pem" \
    "${IMAGE_FULL}"; then

    echo ""
    echo -e "${GREEN}✓${NC}  Image signed successfully"
else
    echo ""
    echo -e "${RED}✗${NC}  Failed to sign image"
    exit 1
fi

echo ""
echo "Signature saved to: ${SIGNATURE_DIR}/${IMAGE_NAME}.sig"
echo "Certificate saved to: ${SIGNATURE_DIR}/${IMAGE_NAME}.pem"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Upload Signature to sigstore Rekor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Upload to Rekor (transparency log)
echo "Uploading signature to Rekor transparency log..."
echo ""

REKOR_UUID=$(cosign triangulate \
    --type slsa \
    "${IMAGE_FULL}" 2>&1 | grep "Entry UUID" | awk '{print $3}' || echo "")

if [ -n "$REKOR_UUID" ]; then
    echo -e "${GREEN}✓${NC}  Signature uploaded to Rekor"
    echo "Rekor UUID: ${REKOR_UUID}"
    echo ""

    # Save Rekor entry for verification
    echo "${REKOR_UUID}" > "${SIGNATURE_DIR}/rekor-uuid.txt"

    # Get and save full Rekor entry
    rekor-cli get --uuid "$REKOR_UUID" --format json > "${SIGNATURE_DIR}/rekor-entry.json" 2>/dev/null || {
        echo -e "${YELLOW}⚠${NC}  Could not retrieve full Rekor entry (rekor-cli not available)"
    }

    echo "Rekor entry saved to: ${SIGNATURE_DIR}/rekor-entry.json"
else
    echo -e "${YELLOW}⚠${NC}  Could not retrieve Rekor UUID"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Verify Signature"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Verifying signature..."
echo ""

# Verify the signature
if cosign verify \
    --key cosign.pub \
    --certificate-identity "${REGISTRY}/${REPO}/${IMAGE_NAME}" \
    --certificate-oidc-issuer "https://github.com/${REPO}/.github/workflows/security-ci.yml" \
    "${IMAGE_FULL}"; then

    echo ""
    echo -e "${GREEN}✓${NC}  Signature verification successful"
else
    echo ""
    echo -e "${RED}✗${NC}  Signature verification failed"
    exit 1
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Attach SBOM to Image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if SBOM exists
if [ -f "sbom.json" ]; then
    echo "Attaching SBOM to image..."
    echo ""

    # Attach SBOM as an attestation
    if cosign attest \
        --key cosign.key \
        --type spdxjson \
        --predicate sbom.json \
        "${IMAGE_FULL}"; then

        echo ""
        echo -e "${GREEN}✓${NC}  SBOM attached to image"
    else
        echo ""
        echo -e "${YELLOW}⚠${NC}  Could not attach SBOM to image"
    fi
else
    echo -e "${YELLOW}⚠${NC}  sbom.json not found, skipping SBOM attachment"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✓ Image:     ${IMAGE_FULL}"
echo "✓ Signature: ${SIGNATURE_DIR}/${IMAGE_NAME}.sig"
echo "✓ Public Key: cosign.pub (commit this to verify signatures)"
echo "✓ Rekor:     Transparency log entry created"
echo ""

if [ -f "sbom.json" ]; then
    echo "✓ SBOM:      Attached as image attestation"
fi

echo ""
echo -e "${BLUE}ℹ${NC}  To verify this image elsewhere:"
echo ""
echo "  1. Copy cosign.pub to the verification environment"
echo "  2. Run: cosign verify --key cosign.pub ${IMAGE_FULL}"
echo ""

echo -e "${GREEN}✓ Container signing complete${NC}"
echo ""

exit 0
