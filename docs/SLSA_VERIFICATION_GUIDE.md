# SLSA Provenance & Artifact Verification Guide

**Repository**: `<ORG>/<REPO>` (PsychSync)
**Workflow**: `.github/workflows/slsa-sign.yaml`
**Status**: ✅ Active

---

## Overview

This guide explains how to verify the integrity and provenance of PsychSync container images using:

1. **Cosign** - Signature verification using OIDC
2. **SLSA Provenance** - Supply chain Levels for Software Artifacts verification

All artifacts are built on ephemeral GitHub Actions runners, signed with OIDC tokens, and include comprehensive provenance metadata.

---

## Quick Start

### Prerequisites

Install the required tools:

```bash
# Install Cosign (signature verification)
curl -fsSL https://sigstore.github.io/cosign/install.sh | sh -s -- -b /usr/local/bin

# Install SLSA Verifier (provenance verification)
curl -L https://github.com/slsa-framework/slsa-verifier/releases/download/v2.4.0/slsa-verifier-linux-amd64 -o slsa-verifier
chmod +x slsa-verifier
sudo mv slsa-verifier /usr/local/bin/

# Install ORAS (for pulling OCI artifacts)
curl -fsSL https://raw.githubusercontent.com/oras-project/oras/main/install.sh | bash -s -- -b /usr/local/bin

# Verify installations
cosign version
slsa-verifier version
oras version
```

---

## Cosign Verification

### Verify Image Signature

Verify that a container image was signed by the official PsychSync CI/CD pipeline:

```bash
# Format
cosign verify \
  --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/<TAG>" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/<ORG>/<REPO>:<TAG>

# Example
cosign verify \
  --certificate-identity "https://github.com/sheriftito/psychsync/.github/workflows/slsa-sign.yaml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/sheriftito/psychsync:v1.0.0
```

**Expected Output**:
```
Verification for ghcr.io/sheriftito/psychsync:v1.0.0 --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - The signatures were verified against the specified identity
```

### Verify Image with Digest

For maximum security, verify by digest (SHA256) instead of tag:

```bash
# Get the digest first
docker pull ghcr.io/<ORG>/<REPO>:<TAG>
DIGEST=$(docker inspect ghcr.io/<ORG>/<REPO>:<TAG> --format='{{.RepoDigests[0]}}')

# Verify by digest
cosign verify \
  --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/<TAG>" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$DIGEST"
```

### Verify SBOM Attestation

Verify that the attached SBOM is authentic:

```bash
cosign verify-attestation \
  --type spdxjson \
  --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/<TAG>" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/<ORG>/<REPO>:<TAG>
```

### View Signatures

View all signatures attached to an image:

```bash
cosign triangulate ghcr.io/<ORG>/<REPO>:<TAG>
```

### Download Public Key

Download the Cosign public key for offline verification:

```bash
cosign public-key \
  --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/<TAG>" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/<ORG>/<REPO>:<TAG> > cosign.pub
```

Then verify using the public key:

```bash
cosign verify --key cosign.pub ghcr.io/<ORG>/<REPO>:<TAG>
```

---

## SLSA Provenance Verification

### Verify Image Provenance

Verify the SLSA provenance attestation to ensure the image was built by GitHub Actions:

```bash
# Format
slsa-verifier verify-image \
  --source-uri github.com/<ORG>/<REPO> \
  --provenance-path "https://github.com/<ORG>/<REPO>/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  ghcr.io/<ORG>/<REPO>:<TAG>

# Example
slsa-verifier verify-image \
  --source-uri github.com/sheriftito/psychsync \
  --provenance-path "https://github.com/sheriftito/psychsync/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  ghcr.io/sheriftito/psychsync:v1.0.0
```

**Expected Output**:
```
VERIFIED: SLSA provenance
Source URI: github.com/sheriftito/psychsync
Digest: sha256:abc123...
```

### Verify with Digest

Verify provenance using the image digest:

```bash
slsa-verifier verify-image \
  --source-uri github.com/<ORG>/<REPO> \
  --provenance-path "https://github.com/<ORG>/<REPO>/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  ghcr.io/<ORG>/<REPO>@sha256:<DIGEST>
```

### Download and Inspect Provenance

Download the provenance file for manual inspection:

```bash
# Download provenance
curl -L "https://github.com/<ORG>/<REPO>/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  -o provenance.intoto.jsonl

# View pretty-printed
jq '.' provenance.intoto.jsonl

# Extract build information
jq '.payload' provenance.intoto.jsonl | base64 -d | jq '.'
```

### Verify Build Parameters

Verify specific build parameters from provenance:

```bash
# Extract builder ID
jq -r '.payload' provenance.intoto.jsonl | \
  base64 -d | \
  jq '.prediction.builder.id'
# Expected: https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@refs/tags/v1.10.0

# Extract build type
jq -r '.payload' provenance.intoto.jsonl | \
  base64 -d | \
  jq '.prediction.buildType'
# Expected: https://slsa.dev/provenance/v1

# Extract source repository
jq -r '.payload' provenance.intoto.jsonl | \
  base64 -d | \
  jq '.common.buildConfig.uri'
# Expected: git+https://github.com/<ORG>/<REPO>@refs/tags/<TAG>

# Extract GitHub Actions workflow
jq -r '.payload' provenance.intoto.jsonl | \
  base64 -d | \
  jq '.prediction.invocation.configSource.uri'
# Expected: git+https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/<TAG>
```

---

## Combined Verification Workflow

### Complete Verification Script

Run all verifications in one command:

```bash
#!/bin/bash
set -euo pipefail

IMAGE="ghcr.io/<ORG>/<REPO>:<TAG>"
WORKFLOW="https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/<TAG>"
ISSUER="https://token.actions.githubusercontent.com"
SOURCE_URI="github.com/<ORG>/<REPO>"

echo "🔒 Verifying PsychSync container image..."
echo "Image: $IMAGE"
echo ""

# 1. Cosign signature verification
echo "1️⃣  Verifying Cosign signature..."
cosign verify \
  --certificate-identity "$WORKFLOW" \
  --certificate-oidc-issuer "$ISSUER" \
  "$IMAGE"
echo "✅ Cosign signature valid"
echo ""

# 2. SLSA provenance verification
echo "2️⃣  Verifying SLSA provenance..."
slsa-verifier verify-image \
  --source-uri "$SOURCE_URI" \
  --provenance-path "https://github.com/<ORG>/<REPO>/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  "$IMAGE"
echo "✅ SLSA provenance valid"
echo ""

# 3. SBOM verification
echo "3️⃣  Verifying SBOM attestation..."
cosign verify-attestation \
  --type spdxjson \
  --certificate-identity "$WORKFLOW" \
  --certificate-oidc-issuer "$ISSUER" \
  "$IMAGE"
echo "✅ SBOM attestation valid"
echo ""

echo "🎉 All verifications passed!"
echo "✅ Image integrity confirmed"
echo "✅ Supply chain integrity confirmed"
```

Save as `verify-psychsync.sh` and run:

```bash
chmod +x verify-psychsync.sh
./verify-psychsync.sh
```

---

## Pre-Deployment Verification

### Before Deploying to Production

Verify all artifacts before deploying:

```bash
#!/bin/bash
set -e

TAG="${1:-latest}"
IMAGE="ghcr.io/<ORG>/<REPO>:$TAG"

echo "🚀 Pre-deployment verification for: $IMAGE"
echo ""

# 1. Pull image
echo "1️⃣  Pulling image..."
docker pull "$IMAGE"

# 2. Verify signature
echo "2️⃣  Verifying signature..."
cosign verify \
  --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/$TAG" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE"

# 3. Verify provenance
echo "3️⃣  Verifying provenance..."
slsa-verifier verify-image \
  --source-uri "github.com/<ORG>/<REPO>" \
  --provenance-path "https://github.com/<ORG>/<REPO>/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  "$IMAGE"

# 4. Scan for vulnerabilities
echo "4️⃣  Scanning for vulnerabilities..."
trivy image --severity HIGH,CRITICAL "$IMAGE"

# 5. Check image digest
echo "5️⃣  Checking image digest..."
DIGEST=$(docker inspect "$IMAGE" --format='{{.RepoDigests[0]}}')
echo "Digest: $DIGEST"

echo ""
echo "✅ All pre-deployment checks passed!"
echo "Ready to deploy: $IMAGE"
```

Usage:

```bash
./pre-deploy-check.sh v1.0.0
```

---

## Troubleshooting

### Error: No matching signatures

**Problem**:
```
Error: no matching signatures:
expected certificate identity https://github.com/<ORG>/<REPO>/...
```

**Solution**:
- Check that the tag is correct
- Ensure the release was created and the workflow completed
- Verify the workflow name matches: `.github/workflows/slsa-sign.yaml`

### Error: Failed to verify provenance

**Problem**:
```
Error: verifying provenance for image
```

**Solution**:
- Ensure the provenance file exists in the GitHub release
- Check that the `slsa-provenance` tag exists in releases
- Verify the SLSA verifier version: `slsa-verifier version`

### Error: Certificate OIDC issuer mismatch

**Problem**:
```
Error: verifying certificate: certificate issuer does not match expected issuer
```

**Solution**:
- The issuer must be: `https://token.actions.githubusercontent.com`
- This is GitHub's OIDC issuer for Actions

### View Workflow Logs

Check the workflow run that signed the image:

```bash
# List recent workflow runs
gh run list --workflow=slsa-sign.yaml

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

---

## Advanced Usage

### Verify Multiple Tags

Verify all tags for a release:

```bash
for TAG in v1.0.0 v1.0 v1 latest; do
  echo "Verifying: $TAG"
  cosign verify \
    --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@refs/tags/v1.0.0" \
    --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
    "ghcr.io/<ORG>/<REPO>:$TAG"
done
```

### Verify Offline

Download all artifacts for offline verification:

```bash
# Download image
docker pull ghcr.io/<ORG>/<REPO>:<TAG>
docker save ghcr.io/<ORG>/<REPO>:<TAG> -o psychsync.tar

# Download signature
cosign save ghcr.io/<ORG>/<REPO>:<TAG> > signatures.json

# Download provenance
curl -L "https://github.com/<ORG>/<REPO>/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  -o provenance.intoto.jsonl

# Verify offline
cosign verify --key cosign.pub ghcr.io/<ORG>/<REPO>:<TAG>
```

### Integrate with CI/CD

Add verification to your deployment pipeline:

```yaml
# .github/workflows/deploy.yaml
name: Deploy

on:
  workflow_run:
    workflows: [SLSA Build & Sign]
    types: [completed]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    steps:
      - uses: actions/checkout@v4

      - name: Install Cosign
        uses: sigstore/cosign-installer@v3.1.2

      - name: Verify before deploy
        run: |
          cosign verify \
            --certificate-identity "https://github.com/${{ github.repository }}/.github/workflows/slsa-sign.yaml@refs/tags/${{ github.ref_name }}" \
            --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
            "ghcr.io/${{ github.repository }}:${{ github.ref_name }}"

      - name: Deploy
        run: |
          # Your deployment commands here
```

---

## Security Best Practices

### 1. Always Verify by Digest

Tags are mutable (can be moved), digests are immutable:

```bash
# ❌ Avoid (tag can change)
cosign verify ghcr.io/<ORG>/<REPO>:latest

# ✅ Prefer (digest is immutable)
cosign verify ghcr.io/<ORG>/<REPO>@sha256:abc123...
```

### 2. Pin Specific Workflow Revisions

Pin to specific workflow runs for maximum security:

```bash
# Pin to specific Git SHA
cosign verify \
  --certificate-identity "https://github.com/<ORG>/<REPO>/.github/workflows/slsa-sign.yaml@<GIT_SHA>" \
  ...
```

### 3. Verify in Production Pipeline

Always verify in your production deployment pipeline, not just locally:

```yaml
# Kubernetes deployment example
apiVersion: v1
kind: Pod
metadata:
  name: psychsync
spec:
  containers:
  - name: psychsync
    image: ghcr.io/<ORG>/<REPO>@sha256:VERIFIED_DIGEST  # Use verified digest
```

### 4. Monitor for Signature Revocation

Monitor GitHub Security for any signature revocations:

```bash
# Check for security advisories
gh api repos/<ORG>/<REPO>/security-advisories
```

---

## Compliance Mapping

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| **NIST SSDF** | Verify provenance | SLSA provenance verification |
| **CISA SBOM** | Verify SBOM authenticity | Cosign SBOM attestation |
| **PCI DSS** | Verify vendor software | Signature verification before deploy |
| **SOC 2** | Monitor supply chain | Provenance verification logs |
| **ISO 27001** | Verify third-party software | Complete verification workflow |

---

## References

- **Cosign Documentation**: https://sigstore.github.io/cosign/
- **SLSA Verifier**: https://github.com/slsa-framework/slsa-verifier
- **SLSA Levels**: https://slsa.dev/spec/v1.0/levels
- **GitHub OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **PsychSync Workflow**: `.github/workflows/slsa-sign.yaml`

---

## Support

For issues or questions:

1. Check the workflow logs: `.github/workflows/slsa-sign.yaml`
2. Review this guide's troubleshooting section
3. Open an issue in the repository

**Quick Help Commands**:
```bash
# Check Cosign version
cosign version

# Check SLSA verifier version
slsa-verifier version

# View latest signatures
cosign triangulate ghcr.io/<ORG>/<REPO>:latest

# View workflow status
gh run list --workflow=slsa-sign.yaml
```

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-27
**Status**: ✅ Active
**Repository**: `<ORG>/<REPO>`
