# 🔐 Supply Chain Security & SLSA Verification

**Version**: 1.0
**Last Updated**: 2025-12-27
**SLSA Level**: 1 (Provenance + Signing + Verification)

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Verification Commands](#verification-commands)
4. [Workflow Details](#workflow-details)
5. [Security Guarantees](#security-guarantees)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Overview

This repository implements **SLSA (Supply-chain Levels for Software Artifacts)** Level 1 provenance generation with **Cosign signing** and **OIDC-based authentication**.

### What is SLSA?

SLSA is a security framework that provides:
- **Provenance**: Verifiable information about how an artifact was built
- **Integrity**: Cryptographic guarantees that artifacts haven't been tampered with
- **Traceability**: Complete supply chain visibility from source to deployment

### Key Features

✅ **SLSA Level 1 Provenance** - Complete build metadata
✅ **Cosign Signing** - OCI image signatures with OIDC
✅ **SBOM Generation** - Software Bill of Materials
✅ **Multi-Platform Builds** - linux/amd64, linux/arm64
✅ **Verification Pipeline** - Automated verification before deployment
✅ **GitHub Actions Integration** - Uses ephemeral runners

---

## Quick Start

### Prerequisites

Install required tools:

```bash
# Cosign - for signing and verification
curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o cosign
chmod +x cosign
sudo mv cosign /usr/local/bin/

# SLSA Verifier - for provenance verification
curl -L https://github.com/slsa-framework/slsa-verifier/releases/latest/download/slsa-verifier-linux-amd64 -o slsa-verifier
chmod +x slsa-verifier
sudo mv slsa-verifier /usr/local/bin/

# OR use Homebrew (macOS/Linux)
brew install cosign slsa-verifier
```

### Basic Verification

```bash
# Set your image tag
export IMAGE_TAG="ghcr.io/your-org/psychsync:v1.0.0"

# Verify the image signature
cosign verify $IMAGE_TAG

# Verify SLSA provenance
slsa-verifier verify-image \
  --source-uri github.com/your-org/psychsync \
  --provenance-path provenance.intoto.jsonl \
  $IMAGE_TAG
```

---

## Verification Commands

### 1. Cosign Signature Verification

Verify the Docker image signature using Cosign:

```bash
#!/bin/bash
# verify-cosign-signature.sh

IMAGE="ghcr.io/${{ github.repository }}:${TAG}"

cosign verify \
  --certificate-identity "https://github.com/${{ github.repository }}/.github/workflows/slsa-sign.yaml@refs/tags/${TAG}" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE"
```

**What this does**:
- ✅ Verifies the image was signed by the GitHub Actions workflow
- ✅ Checks the certificate identity matches the expected workflow
- ✅ Validates the OIDC issuer is GitHub Actions
- ✅ Ensures the signature is cryptographically valid

**Expected Output**:
```
Verification for ghcr.io/your-org/psychsync:v1.0.0 --
The following checks were performed on each of the signatures discovered during verification:
  - The cosign claims were validated
  - The signatures were verified against the specified public key
  - Any certificates were verified against the Fulcio roots

Certificate options:
  - SourceRepository:    github.com/your-org/psychsync
  - BuilderWorkflow:      .github/workflows/slsa-sign.yaml@refs/tags/v1.0.0
  - BuilderRef:           https://github.com/your-org/psychsync/.github/workflows/slsa-sign.yaml@refs/tags/v1.0.0

✅ Verified signature
```

---

### 2. SLSA Provenance Verification

Verify the SLSA provenance attestation:

```bash
#!/bin/bash
# verify-slsa-provenance.sh

IMAGE_DIGEST="sha256:abc123..."  # Your image digest
SOURCE_REPO="github.com/your-org/psychsync"

slsa-verifier verify-image \
  --source-uri "$SOURCE_REPO" \
  --provenance-path "https://github.com/your-org/psychsync/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  "$IMAGE_DIGEST"
```

**What this does**:
- ✅ Downloads and verifies SLSA provenance
- ✅ Validates the provenance matches the image digest
- ✅ Checks the builder identity (GitHub Actions)
- ✅ Verifies the complete build recipe

**Expected Output**:
```
Verifying image for source: github.com/your-org/psychsync

PASSED: SLSA provenance verification
Verified builder: https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v1.10.0
Verified digest: sha256:abc123...

✅ SLSA provenance is valid
```

---

### 3. SBOM Verification

Retrieve and verify the Software Bill of Materials:

```bash
#!/bin/bash
# verify-sbom.sh

IMAGE="ghcr.io/your-org/psychsync:v1.0.0"

# Download SBOM from image
cosign download sbom "$IMAGE" > sbom.spdx.json

# Verify SBOM signature
cosign verify-attestation \
  --type spdxjson \
  "$IMAGE"

# Or simply display the SBOM
cosign sbom "$IMAGE"
```

**What this does**:
- ✅ Downloads the SBOM attached to the image
- ✅ Verifies the SBOM signature
- ✅ Lists all dependencies and their versions
- ✅ Shows licenses for each component

---

### 4. Complete Verification Script

Combine all verifications into one script:

```bash
#!/bin/bash
# verify-complete.sh - Complete supply chain verification

set -e

IMAGE="${1:-ghcr.io/your-org/psychsync:latest}"
PROVENANCE_URL="https://github.com/your-org/psychsync/releases/download/slsa-provenance/provenance.intoto.jsonl"

echo "🔍 Supply Chain Verification"
echo "============================="
echo "Image: $IMAGE"
echo ""

# Step 1: Verify Cosign signature
echo "1️⃣  Verifying Cosign signature..."
cosign verify \
  --certificate-identity "https://github.com/your-org/psychsync/.github/workflows/slsa-sign.yaml" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE"

echo "✅ Signature verified"
echo ""

# Step 2: Verify SLSA provenance
echo "2️⃣  Verifying SLSA provenance..."
IMAGE_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE" | cut -d'@' -f2)

slsa-verifier verify-image \
  --source-uri "github.com/your-org/psychsync" \
  --provenance-path "$PROVENANCE_URL" \
  "$IMAGE_DIGEST"

echo "✅ Provenance verified"
echo ""

# Step 3: Verify SBOM
echo "3️⃣  Verifying SBOM..."
cosign verify-attestation \
  --type spdxjson \
  "$IMAGE"

echo "✅ SBOM verified"
echo ""

# Step 4: Display summary
echo "✅ All verifications passed!"
echo ""
echo "📊 Summary:"
echo "  - Signature: VALID"
echo "  - Provenance: SLSA Level 1"
echo "  - SBOM: VERIFIED"
echo ""
echo "🔒 Supply chain integrity confirmed!"
```

**Usage**:
```bash
chmod +x verify-complete.sh
./verify-complete.sh ghcr.io/your-org/psychsync:v1.0.0
```

---

### 5. Local Image Verification (Before Pull)

Verify an image exists and is signed before pulling:

```bash
#!/bin/bash
# verify-before-pull.sh

IMAGE="$1"

# Check if signature exists in registry
echo "Checking signature for $IMAGE..."
cosign verify "$IMAGE" 2>&1 | grep -q "Verification for"

if [ $? -eq 0 ]; then
  echo "✅ Image signature found and valid"
  echo "Pulling image..."
  docker pull "$IMAGE"
else
  echo "❌ Image signature not found or invalid"
  echo "Refusing to pull unsigned image!"
  exit 1
fi
```

---

### 6. Deploy-Time Verification

Verify images during Kubernetes deployment:

```yaml
# deployment-with-verification.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: verify-script
data:
  verify.sh: |
    #!/bin/sh
    IMAGE=$1
    cosign verify \
      --certificate-identity "https://github.com/your-org/psychsync/.github/workflows/slsa-sign.yaml" \
      --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
      "$IMAGE"
    if [ $? -ne 0 ]; then
      echo "❌ Image verification failed"
      exit 1
    fi
    echo "✅ Image verified successfully"

---
apiVersion: v1
kind: Pod
metadata:
  name: psychsync
spec:
  initContainers:
  - name: verify
    image: ghcr.io/sigstore/cosign:v2.2.3
    command: ["/bin/sh", "/scripts/verify.sh"]
    args: ["$(IMAGE)"]
    volumeMounts:
    - name: verify-script
      mountPath: /scripts
  containers:
  - name: app
    image: ghcr.io/your-org/psychsync:v1.0.0
  volumes:
  - name: verify-script
    configMap:
      name: verify-script
      defaultMode: 0755
```

---

## Workflow Details

### Triggering the Workflow

The SLSA signing workflow is triggered by:

1. **Tag Push** (Automatic)
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Release** (Automatic)
   ```bash
   gh release create v1.0.0
   ```

3. **Manual Dispatch**
   ```bash
   gh workflow run slsa-sign.yaml -f release_tag=v1.0.0
   ```

### Workflow Steps

```
┌─────────────────────────────────────────────────────────────┐
│                    BUILD & SIGN                             │
├─────────────────────────────────────────────────────────────┤
│ 1. Checkout repository (full history for provenance)       │
│ 2. Set up Docker Buildx (multi-platform)                  │
│ 3. Log in to GHCR                                           │
│ 4. Extract metadata (tags, labels)                          │
│ 5. Build & push Docker image                                │
│ 6. Generate SBOM (Syft)                                     │
│ 7. Sign with Cosign (OIDC)                                  │
│ 8. Attach SBOM signature                                    │
│ 9. Generate SLSA provenance                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    VERIFY                                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Install Cosign + SLSA verifier                          │
│ 2. Verify Cosign signature                                 │
│ 3. Verify SLSA provenance                                  │
│ 4. Verify SBOM signature                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              DEPLOY (on release only)                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Deploy verified image to production                     │
│ 2. Post-deployment verification                            │
└─────────────────────────────────────────────────────────────┘
```

### Artifacts Generated

For each build, the following artifacts are generated:

1. **Docker Image** (multi-arch)
   - `ghcr.io/your-org/psychsync:v1.0.0`
   - `ghcr.io/your-org/psychsync:v1.0`
   - `ghcr.io/your-org/psychsync:v1`
   - `ghcr.io/your-org/psychsync:latest`

2. **Cosign Signatures**
   - Stored in GHCR registry
   - Attached to image digest

3. **SLSA Provenance**
   - `provenance.intoto.jsonl`
   - Attached to GitHub release

4. **SBOM** (Software Bill of Materials)
   - `sbom.spdx.json`
   - Attached to image with signature

---

## Security Guarantees

### What SLSA Level 1 Provides

✅ **Source Integrity**: Source code matches provenance
✅ **Build Platform**: Build ran on GitHub Actions (ephemeral runner)
✅ **Build Recipe**: Complete build inputs and configuration
✅ **Digest Verification**: Artifact digest matches provenance
✅ **Builder Identity**: Builder is a trusted GitHub Actions workflow

### What Cosign Signing Provides

✅ **Cryptographic Signature**: SHA256 signature over image manifest
✅ **OIDC Authentication**: Signature backed by GitHub OIDC token
✅ **Certificate Transparency**: Public certificate logged to Rekor
✅ **Timestamp**: When the signature was created

### Defense in Depth

```
┌──────────────────────────────────────────────────────────┐
│                  Supply Chain Defense                     │
├──────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: Source Code (Git + SHA verification)         │
│       ↓                                                │
│  Layer 2: CI/CD (GitHub Actions + ephemeral runners)   │
│       ↓                                                │
│  Layer 3: Build (SLSA provenance + reproducibility)    │
│       ↓                                                │
│  Layer 4: Signing (Cosign + OIDC + Rekor)             │
│       ↓                                                │
│  Layer 5: Registry (GHCR with signature storage)       │
│       ↓                                                │
│  Layer 6: Verification (Before deployment)             │
│       ↓                                                │
│  Layer 7: Runtime (Signed images only)                │
│                                                         │
└──────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: "Certificate identity mismatch"

**Error**:
```
error: verifying certificate: certificate identity does not match
expected: https://github.com/org/repo/.github/workflows/slsa-sign.yaml@refs/tags/v1.0.0
actual: https://github.com/org/repo/.github/workflows/slsa-sign.yaml@refs/heads/main
```

**Solution**: The certificate identity must match the git ref. Use the correct tag in the `--certificate-identity` parameter.

---

### Issue: "OIDC issuer not trusted"

**Error**:
```
error: verifying certificate: issuer not recognized
```

**Solution**: Verify the OIDC issuer URL is correct:
```
https://token.actions.githubusercontent.com
```

---

### Issue: "Provenance not found"

**Error**:
```
error: downloading provenance: 404 Not Found
```

**Solution**: Ensure the SLSA provenance was attached to the release:
```bash
gh release view slsa-provenance --json assets -q .[]
```

---

### Issue: "SBOM verification failed"

**Error**:
```
error: verifying attestation: no matching attestation
```

**Solution**: Ensure SBOM was attached during build:
```bash
cosign attach sbom --type spdx --sbom sbom.spdx.json $IMAGE
```

---

## Best Practices

### 1. Always Verify Before Deploy

Never deploy an image without verification:
```bash
# ❌ BAD
docker pull psychsync:latest
kubectl apply -f deployment.yaml

# ✅ GOOD
cosign verify ghcr.io/your-org/psychsync:latest
docker pull ghcr.io/your-org/psychsync:latest
kubectl apply -f deployment.yaml
```

---

### 2. Use Specific Tags, Not :latest

```bash
# ❌ BAD - latest can change
cosign verify ghcr.io/your-org/psychsync:latest

# ✅ GOOD - specific version
cosign verify ghcr.io/your-org/psychsync:v1.0.0
```

---

### 3. Verify Digest, Not Tag

```bash
# Better: verify by digest (immutable)
IMAGE_DIGEST="sha256:abc123..."
cosign verify ghcr.io/your-org/psychsync@$IMAGE_DIGEST
```

---

### 4. Enable Cosign in Docker

Configure Docker daemon to verify signatures:
```json
// /etc/docker/daemon.json
{
  "plugins": {
    "sigstore": {
      "enabled": true
    }
  }
}
```

Then pull with verification:
```bash
docker pull --cosign=ghcr.io/your-org/psychsync:v1.0.0
```

---

### 5. Integrate with Admission Controllers

Use Kubernetes admission controllers to enforce signature verification:
```yaml
# Cosigned admission controller
apiVersion: cosigned.sigstore.dev/v1alpha1
kind: ClusterImagePolicy
metadata:
  name: psychsync-policy
spec:
  images:
  - glob: ghcr.io/your-org/psychsync/**
    authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        issuer: https://token.actions.githubusercontent.com
        identities:
        - issuerRegExp: ".*"
          subjectRegExp: "https://github.com/your-org/psychsync/.*"
```

---

## Quick Reference

### Verify Commands

```bash
# Cosign verification
cosign verify $IMAGE \
  --certificate-identity "https://github.com/org/repo/.github/workflows/slsa-sign.yaml@refs/tags/$TAG" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

# SLSA provenance verification
slsa-verifier verify-image \
  --source-uri github.com/org/repo \
  --provenance-path "https://github.com/org/repo/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  $IMAGE_DIGEST

# SBOM verification
cosign sbom $IMAGE

# Download SBOM
cosign download sbom $IMAGE > sbom.spdx.json

# Verify attestation
cosign verify-attestation --type spdxjson $IMAGE
```

---

## Resources

- **SLSA Specification**: https://slsa.dev/spec/v1.0/
- **Cosign Documentation**: https://sigstore.github.io/cosign/
- **SLSA Verifier**: https://github.com/slsa-framework/slsa-verifier
- **SLSA GitHub Generator**: https://github.com/slsa-framework/slsa-github-generator
- **Sigstore**: https://sigstore.dev/

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/psychsync/issues
- Security Team: security@psychsync.ai

---

**END OF DOCUMENTATION**
