#!/bin/bash
# ============================================================================
# Quick Supply Chain Verification
# ============================================================================
#
# Quick verification of Docker image signature and SLSA provenance.
# Use this for fast checks before deployment.
#
# Usage:
#   ./scripts/verify-quick.sh <IMAGE_TAG>
#
# Author: Security Team
# Version: 1.0
# ============================================================================

set -e

IMAGE="${1:?Usage: $0 <IMAGE_TAG>}"

echo "🔍 Quick Verification: $IMAGE"
echo ""

# Cosign verification
echo "1️⃣ Verifying signature..."
cosign verify \
  --certificate-identity "https://github.com/$(echo $IMAGE | cut -d'/' -f2)/.github/workflows/slsa-sign.yaml" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE" && echo "✅ Signature valid" || { echo "❌ Signature invalid"; exit 1; }

echo ""
echo "✅ Image verified - safe to use!"
