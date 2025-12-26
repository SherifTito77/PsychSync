# SLSA Verification Quick Reference
## Command Cheatsheet

Quick reference for verifying PsychSync build artifacts.

---

## 🔐 Docker Image Verification

### Quick Verify (Recommended)

```bash
# Verify signature and SLSA provenance in one command
slsa-verifier verify-image \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --source-uri github.com/YOUR_ORG/psychsync \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0
```

### Signature Only

```bash
cosign verify \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

### With Specific Commit

```bash
slsa-verifier verify-image \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --source-uri github.com/YOUR_ORG/psychsync \
  --source-sha256 COMMIT_HASH
```

### Verify Pull

```bash
# Verify then pull in one command
cosign verify IMAGE && docker pull IMAGE
```

---

## 📦 Frontend Artifact Verification

### Download and Verify

```bash
# Download release assets
wget https://github.com/YOUR_ORG/psychsync/releases/download/v1.0.0/frontend-build-SHA.tar.gz
wget https://github.com/YOUR_ORG/psychsync/releases/download/v1.0.0/frontend-build-SHA.sig
wget https://github.com/YOUR_ORG/psychsync/releases/download/v1.0.0/frontend-build-SHA.pem

# Verify
cosign verify-blob \
  frontend-build-SHA.tar.gz \
  --certificate frontend-build-SHA.pem \
  --signature frontend-build-SHA.sig \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

### Extract After Verification

```bash
cosign verify-blob frontend.tar.gz ... && tar -xzf frontend.tar.gz
```

---

## 🔍 Vulnerability Scanning

### Scan Image

```bash
docker run --rm aquasec/trivy:latest \
  image --severity CRITICAL,HIGH ghcr.io/YOUR_ORG/psychsync/backend:TAG
```

### Scan and Fail on Critical

```bash
docker run --rm aquasec/trivy:latest \
  image --severity CRITICAL --exit-code 1 IMAGE
```

### Scan SBOM

```bash
grype sbom:sbom.json --fail-on critical
```

---

## 📋 SBOM Operations

### Get SBOM from Image

```bash
cosign download sbom ghcr.io/YOUR_ORG/psychsync/backend:TAG
```

### Verify SBOM Signature

```bash
cosign verify-attestation \
  ghcr.io/YOUR_ORG/psychsync/backend:TAG \
  --type cyclonedx
```

---

## 🌐 Online Verification (No Tools)

### Web-Based Verification

1. Visit: https://search.sigstore.dev/
2. Enter image digest: `sha256:...`
3. View public verification results

### Check Transparency Log

```bash
# Get UUID from cosign output
UUID=$(cosign verify IMAGE --output-json | jq -r '.[0].bundles[0].payload.body')

# View in Rekor
curl "https://rekor.sigstore.dev/api/v1/log/entries?logIndex=$UUID"
```

---

## 🔧 Batch Operations

### Verify All Images

```bash
for image in backend frontend nginx worker; do
  echo "Verifying $image..."
  cosign verify ghcr.io/YOUR_ORG/psychsync/$image:latest \
    --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com
done
```

### Scan All Images

```bash
for image in backend frontend nginx worker; do
  echo "Scanning $image..."
  docker run aquasec/trivy:latest \
    image --severity CRITICAL,HIGH \
    ghcr.io/YOUR_ORG/psychsync/$image:latest
done
```

---

## 🚀 Pre-Deploy Checklist

```bash
#!/bin/bash
# pre-deploy-check.sh

IMAGE="ghcr.io/YOUR_ORG/psychsync/backend:TAG"

echo "1. Verifying signature..."
cosign verify "$IMAGE" \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com || exit 1

echo "2. Verifying SLSA provenance..."
slsa-verifier verify-image "$IMAGE" \
  --source-uri github.com/YOUR_ORG/psychsync || exit 1

echo "3. Scanning for vulnerabilities..."
docker run aquasec/trivy:latest \
  image --severity CRITICAL,HIGH --exit-code 1 "$IMAGE" || exit 1

echo "✅ All checks passed - safe to deploy"
```

---

## 🔄 Deployment Verification

### Verify Current Deployment

```bash
# Get current image
CURRENT_IMAGE=$(kubectl get deployment psychsync-backend -o jsonpath='{.spec.template.spec.containers[0].image}')

# Verify
cosign verify "$CURRENT_IMAGE" \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

### Monitor Deployments

```bash
watch -n 30 '
echo "Checking current deployment..."
IMAGE=$(kubectl get deployment psychsync-backend -o jsonpath="{.spec.template.spec.containers[0].image}")
echo "Image: $IMAGE"
cosign verify "$IMAGE" --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main --certificate-oidc-issuer https://token.actions.githubusercontent.com && echo "✅ Verified" || echo "❌ Failed"
'
```

---

## 🛠️ Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Verification aliases
alias verify-img='cosign verify --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main --certificate-oidc-issuer https://token.actions.githubusercontent.com'
alias slsa-verify='slsa-verifier verify-image --source-uri github.com/YOUR_ORG/psychsync'
alias scan-img='docker run --rm aquasec/trivy:latest image --severity CRITICAL,HIGH'

# Usage:
# verify-img ghcr.io/YOUR_ORG/psychsync/backend:latest
# slsa-verify ghcr.io/YOUR_ORG/psychsync/backend:latest
# scan-img ghcr.io/YOUR_ORG/psychsync/backend:latest
```

---

## 📊 JSON Output (for CI/CD)

### Verification as JSON

```bash
cosmin verify IMAGE --output-json > verification.json
```

### Parse Results

```bash
# Check if verified
jq '.[0].cert' verification.json

# Get digest
jq -r '.[0].payload.body' verification.json | base64 -d | jq -r '.critical.image.docker.manifestDigest'
```

---

## 🔴 Troubleshooting

### Force Pull New Image

```bash
docker pull --no-cache IMAGE
```

### Check Signature Details

```bash
cosign verify IMAGE --output-json | jq '.'
```

### View Certificate

```bash
cosign verify IMAGE --insecure-ignore-tlog --output-certificate cert.pem
openssl x509 -in cert.pem -text -noout
```

### Debug Mode

```bash
COSIGN_LOG_LEVEL=debug cosign verify IMAGE
```

---

## 📞 Quick Help

| Command | Help |
|---------|------|
| `cosign verify --help` | Verify options |
| `slsa-verifier verify-image --help` | SLSA verification options |
| `trivy image --help` | Scan options |
| `cosign public-key --help` | Key management |

---

## 🎯 Common Scenarios

### "I want to deploy this image"

```bash
# Run all checks
./pre-deploy-check.sh IMAGE

# Deploy if passed
kubectl set image deployment/psychsync-backend psychsync=IMAGE
```

### "Is my deployment verified?"

```bash
# Get current image
kubectl get deployment psychsync-backend -o jsonpath='{.spec.template.spec.containers[0].image}'

# Verify it
cosign verify IMAGE ... --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

### "What dependencies are in this image?"

```bash
# Get SBOM
cosign download sbom IMAGE > sbom.json

# View dependencies
jq '.components[] | {name, version, purl}' sbom.json
```

### "Is there a newer verified image?"

```bash
# Check latest tag
docker pull ghcr.io/YOUR_ORG/psychsync/backend:latest

# Verify it
cosign verify ghcr.io/YOUR_ORG/psychsync/backend:latest --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main --certificate-oidc-issuer https://token.actions.githubusercontent.com

# Check digest
docker inspect ghcr.io/YOUR_ORG/psychsync/backend:latest | jq '.[0].Digest'
```

---

## 📱 Mobile/Web Verification

### QR Code for Verification

Generate QR code for quick verification:

```bash
# Install qrencode
sudo apt install qrencode

# Generate QR
echo "https://search.sigstore.dev/?query=$(docker inspect IMAGE | jq -r '.[0].Digest')" | qrencode -o verify.png
```

### Web Interface

1. Visit: https://search.sigstore.dev/
2. Scan or enter: `ghcr.io/YOUR_ORG/psychsync/backend:TAG`
3. View verification status

---

**Print this reference and keep it at your desk!**

**Last Updated:** December 26, 2025
**SLSA Level:** 3
