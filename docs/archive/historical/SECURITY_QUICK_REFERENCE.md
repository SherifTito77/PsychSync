# PsychSync Security Quick Reference Card

**Print this and keep at your desk for quick reference!**

---

## 🔒 Daily Security Operations (5 minutes)

```bash
# 1. Check for new CVE alerts
gh issue list --label "cve,security"

# 2. Review security workflow runs
gh run list --workflow=security-ci.yml --branch=main --limit 5

# 3. Verify latest images are signed
cosign verify ghcr.io/psychsync/psychsync/backend:latest
```

---

## 🚨 Critical CVE Response

**When a critical CVE is detected:**

```bash
# Step 1: Get CVE details
cve_id="CVE-2024-12345"
grep -A 10 "$cve_id" vex-baseline.json

# Step 2: Check if affected
# If status: "not_affected" → Document and close
# If status: "affected" → Proceed below

# Step 3: Find fix
pip-audit --format json | jq ".dependencies[] | select(.vulns[] | .id == \"$cve_id\")"

# Step 4: Update dependency
pip install package==fixed-version

# Step 5: Test and deploy
pytest tests/ -v
git commit -m "security: Fix $cve_id"
git tag v1.0.1
git push origin main --tags
```

---

## 📦 Creating a Signed Release

```bash
# 1. Ensure all tests pass
pytest tests/ -v

# 2. Run security checks
bandit -r app/ -c .bandit
pip-audit

# 3. Update version
vim app/__init__.py  # Update __version__

# 4. Commit and tag
git add .
git commit -m "Release v1.0.0"
git tag v1.0.0

# 5. Push
git push origin main --tags

# 6. Monitor workflow
gh workflow view signed-release.yml
```

---

## 🔐 Adding New Dependencies

```bash
# 1. Research the package
# - Check security history
# - Look for signatures
# - Verify it's actively maintained

# 2. Add to allow-list
echo "package==1.2.3,1.5.0  # Library for X - security-focused" >> allowed-dependencies.txt

# 3. Install with version pinning
pip install package==1.2.3

# 4. Update requirements.txt
echo "package==1.2.3" >> requirements.txt

# 5. Run checks
./scripts/check-allowlist.sh

# 6. Commit
git add allowed-dependencies.txt requirements.txt
git commit -m "deps: add package"
```

---

## ✅ Verify Supply Chain

```bash
# Quick verification
./scripts/verify-supply-chain-security.sh

# Verify specific release
./scripts/verify-release.sh v1.0.0

# Verify container image
cosign verify \
  --certificate-identity "https://github.com/psychsync/psychsync/.github/workflows/signed-release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/psychsync/psychsync/backend:v1.0.0

# View SBOM
cosign sbom download ghcr.io/psychsync/psychsync/backend:latest

# View VEX
cosign attest \
  --predicate-type https://openvex.dev/ns/vex \
  ghcr.io/psychsync/psychsync/backend:latest
```

---

## 🛠️ Common Commands

### SBOM Operations

```bash
# Generate SBOM
cyclonedx-py --format json --output sbom.json -r .

# View SBOM components
jq '.components | length' sbom.json

# Search SBOM for specific package
jq '.components[] | select(.name == "fastapi")' sbom.json
```

### VEX Operations

```bash
# Generate VEX
python3 scripts/generate-vex.py \
  --sbom sbom.json \
  --output vex.json \
  --format openvex

# Check VEX for specific CVE
jq '.statements[] | select(.vulnerability == "CVE-2023-1234")' vex.json

# Count VEX statements by status
jq '.statements | group_by(.status) | map({status: .[0].status, count: length})' vex.json
```

### CVE Monitoring

```bash
# Run CVE check
python3 scripts/cve-monitor.py --check --output cve-report.txt

# Check CVE history
jq '. | length' .github/cve-history.json  # Total scans

# Get CVE metrics
jq '.' .github/cve-metrics.json
```

### Registry Policy

```bash
# Check if image is allowed
./scripts/check-registry-policy.sh python:3.14-slim

# Check all base images
./scripts/check-registry-policy.sh python:3.14-slim
./scripts/check-registry-policy.sh node:20-alpine
./scripts/check-registry-policy.sh postgres:15-alpine
```

---

## 📊 Generate Compliance Report

```bash
# Generate both JSON and Markdown reports
python3 scripts/compliance-report.py --format both

# Generate JSON only
python3 scripts/compliance-report.py --format json

# Generate Markdown only
python3 scripts/compliance-report.py --format markdown
```

---

## 🔍 Troubleshooting

### VEX Generation Fails

```bash
# Verify SBOM is valid
jq '.bomFormat' sbom.json
# Should output: "CycloneDX"

# Regenerate SBOM if needed
pip install --upgrade cyclonedx-bom cyclonedx-python
cyclonedx-py --format json --output sbom.json -r .
```

### Signature Verification Fails

```bash
# Check certificate identity
cosign verify ghcr.io/psychsync/psychsync/backend:latest 2>&1 | grep "certificate identity"

# Expected: https://github.com/psychsync/psychsync/...

# If fails, rebuild and sign
gh workflow run signed-release.yml
```

### CVE Monitoring Rate Limited

```bash
# Add NVD API key to repository secrets
# Settings → Secrets → New repository secret
# Name: NVD_API_KEY
# Get API key at: https://nvd.nist.gov/developers/request-an-api-key
```

### Package Not in Allow-List

```bash
# Check why it's blocked
grep "package-name" allowed-dependencies.txt

# If safe, add to allow-list
echo "package==1.2.3,1.5.0  # Security-focused library" >> allowed-dependencies.txt

# Get security team approval if needed
gh pr create --title "Add package-name to allow-list"
```

---

## 📞 Emergency Contacts

| Issue | Contact | Response Time |
|-------|----------|---------------|
| Critical CVE | security@psychsync.com | 1 hour |
| Security Incident | security@psychsync.com | 1 hour |
| Build Failure | devops@psychsync.com | 4 hours |
| General Question | #security-channel (Slack) | 1 business day |

---

## 📚 Documentation Locations

| Document | Location |
|----------|----------|
| Master Index | `docs/SECURITY_README.md` |
| Operator's Guide | `docs/SUPPLY_CHAIN_QUICK_START.md` |
| Supply Chain Security | `docs/SUPPLY_CHAIN_SECURITY_V2.md` |
| Application Security | `COMPLETE_SECURITY_INTEGRATION_GUIDE.md` |
| Self-Assessment | `docs/SECURITY_SELF_ASSESSMENT_CHECKLIST.md` |
| Executive Summary | `docs/SECURITY_IMPLEMENTATION_SUMMARY.md` |

---

## 🎯 Quarterly Tasks (30 minutes)

```bash
# 1. Full dependency audit
pip-audit --desc > audit-$(date +%Y%m).txt

# 2. Review allow-lists
vim allowed-dependencies.txt
vim frontend/allowed-dependencies.json

# 3. Check for EOL packages
pip install pip-check
pip-check

# 4. Update SBOM baseline
cyclonedx-py --format json --output sbom-$(date +%Y%m).json -r .

# 5. Generate compliance report
python3 scripts/compliance-report.py --format both

# 6. Review CVE metrics
cat .github/cve-metrics.json | jq '.'
```

---

## ⚡ One-Liner Quick Checks

```bash
# Verify everything at once
./scripts/verify-supply-chain-security.sh && echo "✅ All checks passed"

# Check for critical CVEs
gh issue list --label "cve,security" --label "critical"

# Latest security workflow status
gh run list --workflow=security-ci.yml --limit 1 --json status,conclusion | jq -r '.[0] | "\(.status | ascii_upcase) - \(.conclusion | ascii_upcase)"'

# Generate and view compliance
python3 scripts/compliance-report.py --format markdown | grep "Overall Compliance"
```

---

## 🔐 Security Best Practices

✅ **DO:**
- Always read the VEX analysis before acting on CVEs
- Keep dependencies pinned to specific versions
- Enable MFA on all accounts
- Review security workflow runs weekly
- Update dependencies monthly
- Document security decisions

❌ **DON'T:**
- Ignore security workflow failures
- Use `pip install` without version pinning
- Commit secrets to git
- Disable MFA for convenience
- Skip security tests for speed
- Use dependencies not in allow-list

---

## 🎓 Learning Resources

**Internal**:
- Security training: https://training.psychsync.com/security
- Documentation: `docs/` directory
- Runbooks: `docs/SUPPLY_CHAIN_QUICK_START.md`

**External**:
- NIST SSDF v1.1: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf
- SLSA Framework: https://slsa.dev
- CycloneDX: https://cyclonedx.org/
- OpenVEX: https://openvex.dev/

---

**Last Updated**: 2024-12-25
**Version**: 1.0
**Next Review**: 2025-03-25

For the latest version, check the repository: `docs/SECURITY_QUICK_REFERENCE.md`
