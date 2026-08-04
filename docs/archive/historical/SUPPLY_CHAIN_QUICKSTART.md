# 🚀 SLSA Supply Chain Security - Quick Start

**Version**: 1.0
**Date**: 2025-12-27

---

## ⚡ Quick Start (3 Steps)

### Step 1: Install Tools

```bash
# Install Cosign
brew install cosign

# Install SLSA Verifier
brew install slsa-verifier

# Or download directly
curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o cosign
chmod +x cosign && sudo mv cosign /usr/local/bin/
```

---

### Step 2: Trigger SLSA Build

```bash
# Tag your release
git tag v1.0.0
git push origin v1.0.0

# Or create a GitHub release
gh release create v1.0.0
```

This automatically triggers `.github/workflows/slsa-sign.yaml` which:
- ✅ Builds the Docker image (multi-platform)
- ✅ Generates SLSA provenance
- ✅ Signs with Cosign (OIDC)
- ✅ Attaches SBOM
- ✅ Verifies everything before deployment

---

### Step 3: Verify Before Deploy

```bash
# Quick verification
./scripts/verify-quick.sh ghcr.io/your-org/psychsync:v1.0.0

# Or complete verification
./scripts/verify-cosign-signature.sh ghcr.io/your-org/psychsync:v1.0.0
```

---

## 📋 Verification Commands Reference

### Basic Cosign Verification

```bash
export IMAGE="ghcr.io/your-org/psychsync:v1.0.0"

cosign verify \
  --certificate-identity "https://github.com/your-org/psychsync/.github/workflows/slsa-sign.yaml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE"
```

### SLSA Provenance Verification

```bash
slsa-verifier verify-image \
  --source-uri github.com/your-org/psychsync \
  --provenance-path "https://github.com/your-org/psychsync/releases/download/slsa-provenance/provenance.intoto.jsonl" \
  "$IMAGE_DIGEST"
```

### SBOM Download

```bash
cosign download sbom "$IMAGE" > sbom.spdx.json
```

---

## 🔒 What This Protects Against

| Threat | Protection |
|--------|------------|
| **Tampered Images** | Cryptographic signatures ✅ |
| **Unauthorized Builds** | SLSA provenance verification ✅ |
| **Supply Chain Attacks** | Complete provenance tracking ✅ |
| **Unknown Dependencies** | SBOM with all packages ✅ |
| **Compromised CI/CD** | OIDC-based authentication ✅ |

---

## 📚 Documentation

- **Complete Guide**: `/docs/SUPPLY_CHAIN_SECURITY.md`
- **Workflow**: `.github/workflows/slsa-sign.yaml`
- **Verification Scripts**: `/scripts/verify-*.sh`

---

## 🎯 Common Tasks

### Verify Image Before Deploying

```bash
# In your deployment script
IMAGE="ghcr.io/your-org/psychsync:v1.0.0"

if ! cosign verify "$IMAGE" --certificate-identity "..." --certificate-oidc-issuer "..."; then
  echo "❌ Image verification failed - aborting deployment"
  exit 1
fi

echo "✅ Image verified - deploying..."
kubectl apply -f deployment.yaml
```

### View Image SBOM

```bash
cosign sbom ghcr.io/your-org/psychsync:v1.0.0
```

### Check Image Digest

```bash
docker manifest inspect ghcr.io/your-org/psychsync:v1.0.0 | jq -r '.manifests[0].digest'
```

---

## ✅ Checklist Before Production

- [ ] Cosign installed
- [ ] SLSA Verifier installed
- [ ] Workflow triggered (tag pushed)
- [ ] Image signed (check with `cosign verify`)
- [ ] Provenance generated (check GitHub releases)
- [ ] SBOM attached (check with `cosign sbom`)
- [ ] Verification script tested

---

## 🆘 Troubleshooting

### "cosign: command not found"
```bash
brew install cosign
# OR
curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o cosign
chmod +x cosign && sudo mv cosign /usr/local/bin/
```

### "certificate identity mismatch"
Ensure the `--certificate-identity` matches:
```
https://github.com/YOUR_ORG/YOUR_REPO/.github/workflows/slsa-sign.yaml@refs/tags/YOUR_TAG
```

### "provenance not found"
Check the GitHub release:
```bash
gh release view slsa-provenance
```

---

## 📊 What Gets Built

For every release, you get:

1. **Multi-platform Docker Image** (amd64 + arm64)
2. **Cosign Signature** (OIDC-backed)
3. **SLSA Level 1 Provenance**
4. **SPDX SBOM**
5. **Automatic Verification** before deployment

---

**Need Help?** See `/docs/SUPPLY_CHAIN_SECURITY.md` or contact security@psychsync.ai
