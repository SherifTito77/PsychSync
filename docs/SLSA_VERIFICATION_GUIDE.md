# SLSA Verification Guide
## PsychSync Supply Chain Security

This guide explains how to verify the integrity and provenance of PsychSync build artifacts using **SLSA Level 3** attestations and **sigstore/cosign** signatures.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Verifying Docker Images](#verifying-docker-images)
4. [Verifying Frontend Artifacts](#verifying-frontend-artifacts)
5. [Verifying SBOMs](#verifying-sboms)
6. [CI/CD Workflow Overview](#cicd-workflow-overview)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Verify a Docker Image (One Command)

```bash
cosign verify \
  ghcr.io/YOUR_ORG/psychsync/backend:latest \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

**Expected Output:**
```
Verification for ghcr.io/YOUR_ORG/psychsync/backend:latest --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The code-signing certificate was checked using the certificate authority
  - The code-signing certificate was verified for the current commit
  - The verified claims matched the expected values

Certificate:
  Identity: https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main
  Issuer: https://token.actions.githubusercontent.com
```

---

## 📦 Prerequisites

### Install Verification Tools

```bash
# Install cosign (signature verification)
curl -L https://github.com/sigstore/cosign/releases/download/v2.2.4/cosign-linux-amd64 -o cosign
chmod +x cosign
sudo mv cosign /usr/local/bin/

# Install slsa-verifier (SLSA provenance verification)
go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@latest

# Install Docker (for pulling images)
# See: https://docs.docker.com/engine/install/

# Verify installations
cosign version
slsa-verifier version
docker --version
```

### Authenticate to GitHub Container Registry

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

---

## 🔐 Verifying Docker Images

### Method 1: Verify Signature Only

Verify that the image was signed by GitHub Actions OIDC:

```bash
cosign verify \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

**What this checks:**
- ✅ Signature is valid and untampered
- ✅ Signature was created by GitHub Actions OIDC
- ✅ Signature is recorded in Rekor transparency log
- ✅ Certificate identity matches expected workflow

### Method 2: Verify SLSA Provenance (Recommended)

Verify the complete SLSA Level 3 provenance:

```bash
slsa-verifier verify-image \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --source-uri github.com/YOUR_ORG/psychsync \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0 \
  --provenance-path https://rekor.sigstore.dev/api/v1/log/entries?logIndex=INDEX
```

**What this checks:**
- ✅ All signature checks (from Method 1)
- ✅ Source repository matches `github.com/YOUR_ORG/psychsync`
- ✅ Builder is trusted SLSA generator
- ✅ Build was performed on GitHub Actions
- ✅ Git commit hash is recorded in provenance
- ✅ All build materials and dependencies are listed

### Method 3: Verify with Specific Commit

Verify that the image was built from a specific commit:

```bash
slsa-verifier verify-image \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --source-uri github.com/YOUR_ORG/psychsync \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0 \
  --source-sha256 COMMIT_HASH
```

### Method 4: Verify in Production (Before Deployment)

```bash
# 1. Verify signature
cosign verify IMAGE \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# 2. Verify SLSA provenance
slsa-verifier verify-image IMAGE \
  --source-uri github.com/YOUR_ORG/psychsync \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0

# 3. Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest \
  image --severity CRITICAL,HIGH IMAGE

# 4. Pull and deploy only if all checks pass
docker pull IMAGE
```

---

## 📦 Verifying Frontend Artifacts

### Download Artifact from Release

```bash
# Download from GitHub release
wget https://github.com/YOUR_ORG/psychsync/releases/download/v1.0.0/frontend-build-SHA.tar.gz
wget https://github.com/YOUR_ORG/psychsync/releases/download/v1.0.0/frontend-build-SHA.sig
wget https://github.com/YOUR_ORG/psychsync/releases/download/v1.0.0/frontend-build-SHA.pem
```

### Verify Artifact Signature

```bash
cosign verify-blob \
  frontend-build-SHA.tar.gz \
  --certificate frontend-build-SHA.pem \
  --signature frontend-build-SHA.sig \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

**Expected Output:**
```
Verified OK
```

### Extract and Deploy

```bash
# Only extract if verification succeeds
tar -xzf frontend-build-SHA.tar.gz

# Deploy to CDN/web server
rsync -avz build/ user@server:/var/www/psychsync/
```

---

## 📋 Verifying SBOMs

### Extract SBOM from Image

```bash
# Get SBOM from image (attached via cosign)
cosign download sbom ghcr.io/YOUR_ORG/psychsync/backend:TAG

# Or get from registry API
curl -L \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://ghcr.io/v2/YOUR_ORG/psychsync/backend/manifests/TAG" | \
  jq -r '.layers[] | select(.annotations["vnd.docker.reference.type"] == "attestation-manifest") | .digest'
```

### Verify SBOM Integrity

```bash
# Download SBOM
cosign attach sbom --type cyclonedx --sbom sbom.json ghcr.io/YOUR_ORG/psychsync/backend:TAG

# Verify SBOM signature
cosign verify-attestation \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --type cyclonedx \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

### Scan SBOM for Vulnerabilities

```bash
# Install grype (vulnerability scanner)
curl -L https://github.com/anchore/grype/releases/download/v0.74.0/grype-linux-amd64 -o grype
chmod +x grype
sudo mv grype /usr/local/bin/

# Scan SBOM
grype sbom:sbom.json --fail-on critical
```

---

## 🔄 CI/CD Workflow Overview

### Build and Sign Workflow

**File:** `.github/workflows/slsa-build-and-sign.yml`

**Triggers:**
- Push to `main` branch
- Release creation
- Manual workflow dispatch

**Jobs:**

1. **Build and Sign Backend**
   - Build Docker image with Buildx
   - Push to GitHub Container Registry (GHCR)
   - Sign with cosign using OIDC (no private key)
   - Generate SLSA Level 3 provenance
   - Attach SBOM to image

2. **Build and Sign Frontend**
   - Build React frontend
   - Create tar.gz artifact
   - Sign artifact with cosign
   - Generate SLSA Level 3 provenance
   - Upload to GitHub release

3. **Verify All Signatures**
   - Verify Docker image signature
   - Verify SLSA provenance
   - Verify frontend artifact signature
   - Store verification results

4. **Record Immutable Log**
   - Append build event to immutable log
   - Upload logs as artifacts (365-day retention)

### Deploy and Verify Workflow

**File:** `.github/workflows/slsa-deploy-verify.yml`

**Triggers:**
- After successful build workflow
- Manual workflow dispatch (with image tag)

**Jobs:**

1. **Verify Before Deploy**
   - Verify Docker image signature
   - Verify SLSA provenance
   - Scan for vulnerabilities (Trivy)
   - Block deployment if any check fails

2. **Deploy to Production**
   - Deploy verified image to ECS/Kubernetes
   - Run health checks
   - Record deployment to immutable log

3. **Rollback (Manual)**
   - Query immutable log for previous stable image
   - Rollback to previous version
   - Verify health after rollback

---

## 🔍 Transparency Log Verification

All signatures and attestations are recorded in the **Rekor transparency log** for public verification.

### View Signature in Rekor

```bash
# Get signature UUID from cosign verification output
UUID=$(cosign verify IMAGE --output-json | jq -r '.[0].bundles[0].payload.body')

# View in Rekor
curl "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=$UUID"
```

### Online Verification (No Tools Required)

Visit: **https://search.sigstore.dev/**

Enter:
- Image digest: `sha256:...`
- Or artifact signature

**This provides:**
- ✅ Public proof of signature existence
- ✅ Timestamp when signature was created
- ✅ Certificate chain
- ✅ Build metadata

---

## 🛠️ Troubleshooting

### Error: "no matching signatures"

**Cause:** Image not signed or wrong tag

**Solution:**
```bash
# Check available tags
curl -L -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://ghcr.io/v2/YOUR_ORG/psychsync/backend/tags/list"

# Verify correct tag is being used
cosign verify ghcr.io/YOUR_ORG/psychsync/backend:CORRECT_TAG
```

### Error: "certificate identity does not match"

**Cause:** Certificate was issued by different workflow

**Solution:**
```bash
# Check actual certificate identity
cosign verify IMAGE --output-json | jq -r '.[0].cert.identityUrl'

# Update verification command to match actual identity
```

### Error: "failed to verify: invalid signature"

**Cause:** Image was tampered with or corrupted

**Solution:**
```bash
# Do NOT deploy! Investigate immediately:
# 1. Check immutable build logs
# 2. Compare image digests
# 3. Review GitHub Actions logs
# 4. Contact security team
```

### Error: "source-uri mismatch"

**Cause:** Image was built from different repository

**Solution:**
```bash
# Verify source repository
slsa-verifier verify-image IMAGE \
  --source-uri github.com/CORRECT_REPO/psychsync

# Or rebuild from correct repository
```

### Vulnerabilities Found During Scan

**Cause:** Image contains vulnerable dependencies

**Solution:**
```bash
# 1. View vulnerability details
docker run aquasec/trivy:latest image --severity CRITICAL,HIGH IMAGE

# 2. Update dependencies and rebuild
# 3. Run CI/CD workflow again
# 4. Only deploy after vulnerabilities are fixed
```

---

## 📚 Advanced Verification

### Verify Multiple Images (Batch)

```bash
#!/bin/bash
# verify-all-images.sh

IMAGES=(
  "ghcr.io/YOUR_ORG/psychsync/backend:latest"
  "ghcr.io/YOUR_ORG/psychsync/frontend:latest"
  "ghcr.io/YOUR_ORG/psychsync/nginx:latest"
)

for IMAGE in "${IMAGES[@]}"; do
  echo "Verifying $IMAGE..."

  if cosign verify "$IMAGE" \
    --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com; then
    echo "✅ $IMAGE verified"
  else
    echo "❌ $IMAGE verification FAILED"
    exit 1
  fi
done

echo "All images verified successfully!"
```

### Continuous Monitoring

```bash
#!/bin/bash
# monitor-deployments.sh

while true; do
  # Get current deployed image
  CURRENT_IMAGE=$(kubectl get deployment psychsync-backend -o jsonpath='{.spec.template.spec.containers[0].image}')

  echo "Checking: $CURRENT_IMAGE"

  # Verify signature
  if ! cosign verify "$CURRENT_IMAGE" \
    --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>/dev/null; then
    echo "⚠️  WARNING: Deployed image signature verification failed!"
    # Send alert to monitoring system
    curl -X POST https://hooks.slack.com/... -d "{\"text\":\"Signature verification failed for $CURRENT_IMAGE\"}"
  fi

  sleep 300  # Check every 5 minutes
done
```

---

## 🎯 Best Practices

### Before Every Deployment

1. ✅ **Verify signature** with cosign
2. ✅ **Verify SLSA provenance** with slsa-verifier
3. ✅ **Scan for vulnerabilities** with Trivy
4. ✅ **Check immutable log** for build metadata
5. ✅ **Verify health checks** before marking as successful

### After Every Security Incident

1. 🔒 **Revoke compromised certificates** (if applicable)
2. 🔍 **Audit immutable logs** for all deployments
3. 🔄 **Rotate all secrets** and credentials
4. 🚫 **Block unverified images** from running
5. 📢 **Notify stakeholders** of verification failures

### For Compliance Audits

1. 📋 Export verification reports: `cosign verify --output-json > report.json`
2. 📊 Collect SLSA provenance: `slsa-verifier verify-image --provenance-path ...`
3. 📝 Document verification procedures in security policy
4. ✅ Show transparency log entries for public proof
5. 📈 Maintain verification metrics dashboard

---

## 📞 Support

**Documentation:**
- SLSA: https://slsa.dev/
- sigstore/cosign: https://docs.sigstore.dev/
- slsa-verifier: https://github.com/slsa-framework/slsa-verifier

**Issues:**
- GitHub Issues: https://github.com/YOUR_ORG/psychsync/issues
- Security: security@psychsync.com

---

**Last Updated:** December 26, 2025
**SLSA Level:** 3
**Compliance:** NIST SSDF, SOC 2, FedRAMP Ready
