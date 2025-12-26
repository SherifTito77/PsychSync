# GitHub Actions Workflows
## SLSA Level 3 Supply Chain Security

This directory contains production-ready GitHub Actions workflows that implement **SLSA Level 3** compliant build, signing, and verification for the PsychSync platform.

---

## 🎯 Overview

Our CI/CD pipeline uses:
- **slsa-github-generator** - Official SLSA framework for provenance generation
- **sigstore/cosign** - OIDC-based signing (no private keys to manage)
- **Fulcio** - OIDC certificate authority for code signing certificates
- **Rekor** - Transparency log for all signatures (publicly verifiable)
- **Immutable logging** - Tamper-evident build and deployment logs

### SLSA Compliance Level: 3

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Provenance** | Complete build instructions and materials | ✅ |
| **Isolated Build** | Ephemeral GitHub Actions runners | ✅ |
| **Hermetic Build** | Reproducible builds with pinned dependencies | ✅ |
| **Signing** | Cryptographic signatures with cosign | ✅ |
| **Verification** | Automated verification before deployment | ✅ |

---

## 📁 Workflows

### 1. SLSA Build and Sign (`slsa-build-and-sign.yml`)

**Purpose:** Build, sign, and generate SLSA provenance for all artifacts

**Triggers:**
- Push to `main` branch
- Release creation
- Manual workflow dispatch

**Artifacts Produced:**
- Docker images (backend, nginx)
- Frontend static assets (tar.gz)
- SBOMs (CycloneDX 1.4)
- SLSA provenance attestations (.intoto.jsonl)
- Cryptographic signatures (.sig, .pem)

**Jobs:**
1. **Build and Sign Backend** - Docker image with cosign + SLSA
2. **Build and Sign Frontend** - Static assets with cosign + SLSA
3. **Verify Signatures** - All signatures verified before completion
4. **Record Immutable Log** - Build event recorded to tamper-evident log

**Outputs:**
- Image digest and tag
- Verification commands
- Provenance metadata

**Usage:**
```yaml
# Manual trigger
- Go to Actions tab
- Select "SLSA Build and Sign"
- Click "Run workflow"
- Choose environment (production/staging)
```

---

### 2. SLSA Deploy with Verification (`slsa-deploy-verify.yml`)

**Purpose:** Deploy verified artifacts to production

**Triggers:**
- After successful build workflow
- Manual workflow dispatch (with image tag)

**Pre-deployment Gates:**
1. ✅ Docker signature verification
2. ✅ SLSA provenance verification
3. ✅ Vulnerability scanning (Trivy)
4. ✅ Health check validation

**Jobs:**
1. **Verify Before Deploy** - All verifications must pass
2. **Deploy Production** - Deploy verified image to ECS/Kubernetes
3. **Rollback** - Manual rollback to previous stable version

**Usage:**
```bash
# Deploy specific image tag
gh workflow run slsa-deploy-verify.yml \
  -f environment=production \
  -f image_tag=v1.2.3
```

---

### 3. SBOM Verify (`sbom-verify.yml`)

**Purpose:** Generate and verify SBOMs for dependency transparency

**Triggers:**
- Every push and pull request

**Features:**
- CycloneDX 1.4 SBOM generation
- NTIA minimum element compliance
- Dependency vulnerability scanning
- SBOM drift detection

---

### 4. Build Signing (`build-signing.yml`)

**Purpose:** Alternative/custom build signing (legacy, being phased out)

**Note:** This workflow is being replaced by `slsa-build-and-sign.yml`

---

## 🚀 Quick Start

### Initial Setup

1. **Enable GitHub Actions OIDC**
   - Go to: Repository Settings → Actions → General
   - Enable "Allow GitHub Actions to create approving reviews"
   - Workflow permissions: Read and write permissions

2. **Set up Container Registry**
   ```bash
   # Login to GHCR
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

3. **Configure Secrets**
   - `AWS_ACCESS_KEY_ID` - For ECS/Kubernetes deployment
   - `AWS_SECRET_ACCESS_KEY` - For ECS/Kubernetes deployment
   - `GITHUB_TOKEN` - Auto-provided, no configuration needed

### First Build

```bash
# Trigger build workflow
git push origin main

# Monitor workflow at:
# https://github.com/YOUR_ORG/psychsync/actions
```

### Verify Build Artifacts

```bash
# Verify Docker image
cosign verify \
  ghcr.io/YOUR_ORG/psychsync/backend:latest \
  --certificate-identity https://github.com/YOUR_ORG/psychsync/.github/workflows/slsa-build-and-sign.yml@refs/heads/main \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# Verify SLSA provenance
slsa-verifier verify-image \
  ghcr.io/YOUR_ORG/psychsync/backend:latest \
  --source-uri github.com/YOUR_ORG/psychsync \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0
```

---

## 📊 Workflow Status Badge

Add to README.md:

```markdown
[![SLSA Build](https://github.com/YOUR_ORG/psychsync/actions/workflows/slsa-build-and-sign.yml/badge.svg)](https://github.com/YOUR_ORG/psychsync/actions/workflows/slsa-build-and-sign.yml)
```

---

## 🔐 Security Guarantees

### What We Protect Against

| Threat | Protection |
|--------|------------|
| **Compromised Build Server** | Isolated ephemeral runners, verified provenance |
| **Tampered Artifacts** | Cryptographic signatures, immutable logs |
| **Supply Chain Attack** | SBOM verification, dependency scanning |
| **Unauthorized Deployment** | Pre-deployment verification gates |
| **Malicious Dependency** | Vulnerability scanning, SBOM drift detection |

### Verification in Depth

Each deployment verifies:
1. ✅ **Identity** - Certificate issued by GitHub Actions OIDC
2. ✅ **Integrity** - Artifact hash matches signature
3. ✅ **Provenance** - SLSA Level 3 build metadata
4. ✅ **Vulnerabilities** - No CRITICAL/HIGH CVEs
5. ✅ **Source** - Built from expected repository

---

## 🛠️ Customization

### Change Target Environment

Edit `slsa-deploy-verify.yml`:

```yaml
deploy-production:
  environment:
    name: staging  # Change from production
    url: https://staging.psychsync.com
```

### Add Additional Verification

Add to `verify-before-deploy` job:

```yaml
- name: Custom verification
  run: |
    # Add your custom checks here
    ./scripts/custom-verification.sh
```

### Modify SLSA Builder

Edit `slsa-build-and-sign.yml`:

```yaml
- name: Generate SLSA Provenance
  uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.10.0
  with:
    builder-id: https://github.com/YOUR_ORG/custom-builder@v1.0.0
```

---

## 📈 Monitoring

### Workflow Runs

- **Build Status:** https://github.com/YOUR_ORG/psychsync/actions/workflows/slsa-build-and-sign.yml
- **Deploy Status:** https://github.com/YOUR_ORG/psychsync/actions/workflows/slsa-deploy-verify.yml

### Verification Dashboard

```bash
# Check latest verified deployments
./scripts/immutable_log.py << EOF
from scripts.immutable_log import ImmutableLog
log = ImmutableLog("deployment")
for deployment in log.get_last_n(10):
    print(deployment)
EOF
```

### Alerts

Configure Slack/email alerts for:
- Failed signature verification
- Failed SLSA provenance verification
- Vulnerabilities found in scan
- Deployment health check failure

---

## 📚 Documentation

**Detailed Verification Guide:** [docs/SLSA_VERIFICATION_GUIDE.md](../docs/SLSA_VERIFICATION_GUIDE.md)

**Security Policy:** [docs/SECURITY_POLICY.md](../docs/SECURITY_POLICY.md)

**SLSA Specification:** https://slsa.dev/spec/v0.1/index.html

**sigstore Documentation:** https://docs.sigstore.dev/

---

## 🐛 Troubleshooting

### Workflow Fails at Signing Step

**Error:** "Error: getting signer: no matching certificates"

**Cause:** OIDC permissions not configured

**Solution:**
1. Go to Repository Settings → Actions → General
2. Set "Workflow permissions" to "Read and write permissions"
3. Enable "Allow GitHub Actions to create approving reviews"

### Verification Fails in Deployment

**Error:** "certificate identity does not match"

**Cause:** Certificate issued by different workflow or branch

**Solution:**
```bash
# Check actual certificate identity
cosign verify IMAGE --output-json | jq -r '.[0].cert.identityUrl'

# Update verification command in workflow
```

### Image Not Found

**Error:** "ERROR: pulling image: unauthorized"

**Cause:** Not authenticated to GHCR

**Solution:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

---

## 🔄 Migration from Legacy Workflows

### Old Approach (Manual Signing)

```yaml
- name: Sign artifact
  run: |
    gpg --detach-sign artifact.tar.gz
```

**Problems:**
- ❌ Private key management
- ❌ No transparency log
- ❌ No SLSA provenance
- ❌ Manual verification

### New Approach (OIDC Signing)

```yaml
- name: Sign artifact
  uses: sigstore/cosign-installer@v3.5.0
- name: Sign with OIDC
  run: |
    cosign sign-blob artifact.tar.gz
```

**Benefits:**
- ✅ No private keys (OIDC certificates)
- ✅ Rekor transparency log
- ✅ SLSA Level 3 provenance
- ✅ Automated verification

---

## 🎓 Training

### For Developers

1. Read: [docs/SLSA_VERIFICATION_GUIDE.md](../docs/SLSA_VERIFICATION_GUIDE.md)
2. Run: `cosign verify ghcr.io/YOUR_ORG/psychsync/backend:latest`
3. Test: Trigger manual workflow build
4. Verify: Check verification outputs

### For Security Engineers

1. Understand: SLSA Level 3 requirements
2. Review: Provenance metadata structure
3. Audit: Immutable logs for build events
4. Test: Tamper detection (modify artifact, verify fails)

### For DevOps Engineers

1. Deploy: Use `slsa-deploy-verify.yml` workflow
2. Monitor: Check workflow run status
3. Rollback: Test rollback procedure
4. Scale: Add additional verification checks

---

## ✅ Checklist

### Before First Deployment

- [ ] GitHub Actions OIDC enabled
- [ ] Container registry access configured
- [ ] AWS credentials set (for deployment)
- [ ] Verification tools installed locally
- [ ] Test build workflow run completed
- [ ] Verification commands tested
- [ ] Immutable logging functional

### Before Every Deployment

- [ ] Build workflow completed successfully
- [ ] Signature verified locally
- [ ] SLSA provenance verified locally
- [ ] No CRITICAL/HIGH vulnerabilities found
- [ ] Immutable log shows verified build

---

## 📞 Support

**Documentation:** See docs/ directory

**Issues:** https://github.com/YOUR_ORG/psychsync/issues

**Security:** security@psychsync.com

**24/7 Hotline:** +1 (555) SEC-URE1

---

**Workflow Status:** ✅ Production Ready
**SLSA Level:** 3 (Highest)
**Last Updated:** December 26, 2025

---

## 🔍 Security Testing Workflows

### Overview

PsychSync implements comprehensive security testing with **SAST, DAST, and SCA** scanning:

- **SAST (Static Application Security Testing)** - Semgrep
- **DAST (Dynamic Application Security Testing)** - OWASP ZAP
- **SCA (Software Composition Analysis)** - Trivy, Snyk, npm audit, Safety

---

### Security Testing Workflows

#### 1. SAST - Semgrep Security Scan

**File:** `sast-semgrep.yml`

**Triggers:** Pull requests, Push to main/develop

**What it does:**
- Scans Python code for security issues
- OWASP Top 10 rule sets
- Publishes to GitHub Security tab
- Requires security review for high-severity findings

**Severity Levels:**
- 🔴 Error (High): Security review required
- ⚠️ Warning (Medium): Review recommended
- ℹ️ Info (Low): Best practices

**Actions on Findings:**
1. Uploads SARIF to GitHub Security
2. Comments on PR
3. Labels as `security-review-required` if high severity
4. Blocks merge until review complete

---

#### 2. DAST - OWASP ZAP Security Scan

**File:** `dast-zap.yml`

**Triggers:** Push to main/develop, Daily schedule (2 AM UTC)

**What it does:**
- Dynamic security testing on staging
- Tests running application for vulnerabilities
- Scans for authentication, authorization, injection attacks

**Scan Types:**
- **Baseline Scan:** Every push (15 min)
- **Full Scan:** Weekly (2 hours)

**Reports:**
- HTML (visual dashboard)
- Markdown (summary)
- XML (machine-readable)
- SARIF (GitHub Security)

---

#### 3. SCA - Dependency Vulnerability Scan

**File:** `sca-trivy-snyk.yml`

**Triggers:** Pull requests, Push, Daily schedule (3 AM UTC)

**What it does:**
- Generates SBOM (Software Bill of Materials)
- Scans dependencies for known vulnerabilities
- Checks Python packages (Trivy, Safety)
- Checks Node.js packages (npm audit)
- License compliance verification

**Tools Used:**
| Tool | Purpose |
|------|---------|
| Trivy | SBOM vulnerability scanning |
| Snyk | Deep dependency analysis |
| npm audit | Frontend dependency check |
| Safety | Python security database |
| Dependency Review | License compliance |

**Fail Conditions:**
- Any Critical or High severity vulnerabilities
- GPL/AGPL license violations
- Known CVEs in dependencies

---

### Security Review Process

#### Automatic Security Review Requirement

**Triggered when:**
- SAST finds high-severity issues
- SCA finds critical/high vulnerabilities
- DAST finds critical/high issues

**Process:**
1. PR labeled as `security-review-required` + `do-not-merge`
2. Security team notified
3. Review must be completed before merge
4. Labels removed after approval

#### Manual Security Review Request

**To request security review:**

1. Label PR with `security-review`
2. Assign to `@security-team`
3. Add comment describing changes

**Review SLA:**
- Low risk: 24 hours
- Medium risk: 4 hours
- High risk: 1 hour

---

### Results and Dashboards

#### GitHub Security Tab

All results uploaded to:
**Repository → Security → Alerts**

Features:
- View all findings in one place
- Filter by severity
- Track remediation progress
- Integration with PR comments

#### Scan Reports (Artifacts)

**SAST:**
- `semgrep-results` - SARIF + JSON

**DAST:**
- `zap-dast-report` - HTML + Markdown + XML
- `zap-full-scan-report` - Weekly comprehensive scan

**SCA:**
- `trivy-scan-results` - SARIF report
- `snyk-scan-results` - Snyk analysis
- `npm-audit-results` - npm audit JSON
- `safety-check-results` - Python safety check
- `sbom` - Software Bill of Materials

---

### Required Secrets

| Secret | Description | Required For |
|--------|-------------|--------------|
| `ZAP_API_KEY` | OWASP ZAP API key | DAST scans |
| `STAGING_AUTH_TOKEN` | Auth token for staging | DAST authenticated scans |
| `SNYK_TOKEN` | Snyk API token | SCA deep scan |

**Setup:** Repository → Settings → Secrets and variables → Actions

---

### Best Practices

#### For Developers

1. **Run scans locally before pushing:**
   ```bash
   # Semgrep
   semgrep --config=auto

   # Trivy
   trivy fs .

   # npm audit
   cd frontend && npm audit
   ```

2. **Fix high-severity findings immediately**

3. **Keep dependencies updated**

#### For Security Team

1. **Review security dashboard daily**

2. **Tune scanning rules to reduce false positives**

3. **Maintain scan schedules**

---

### Troubleshooting

**Problem:** Scan takes too long
**Solution:** Reduce scope, use `--exclude` patterns

**Problem:** Too many false positives
**Solution:** Customize rules, add exclude patterns

**Problem:** ZAP can't access staging
**Solution:** Verify `STAGING_AUTH_TOKEN`, check staging environment

---

### Quick Start Guide

#### First Time Setup

1. **Configure secrets** (see Required Secrets above)

2. **Test workflows manually:**
   ```bash
   # Test SAST
   gh workflow run sast-semgrep.yml

   # Test DAST (manual target)
   gh workflow run dast-zap.yml -f target_url=https://your-staging.com

   # Test SCA
   gh workflow run sca-trivy-snyk.yml -f scan_type=full
   ```

3. **Verify results:**
   - Check Actions tab for workflow runs
   - Check Security tab for findings
   - Review job summaries

#### Daily Monitoring

**Check:**
1. GitHub Security tab for new alerts
2. Actions tab for workflow failures
3. PRs requiring security review
4. Vulnerability trends

---

### Metrics and KPIs

**Track These Metrics:**
- Scan duration (average)
- False positive rate
- Time to fix vulnerabilities
- Critical vulnerabilities over time
- High/Medium vulnerabilities over time
- Security review turnaround time

**View at:**
```
Repository → Security → Overview
Repository → Actions → Security workflows → Summary
```

---

### Integration with Other Tools

**Continuous Monitoring:**
- Snyk - Continuous dependency monitoring
- Dependabot - Automated PRs for updates
- CodeQL - Additional static analysis
- SonarQube - Code quality + security

**Alerting:**
- Configure Slack notifications for failures
- Page on-call for critical findings
- Create JIRA tickets for vulnerabilities

---

### Further Reading

**Internal:**
- `docs/SECURITY_MASTER_INDEX.md` - Complete security guide
- `docs/SECRET_LEAK_REMEDIATION_PLAYBOOK.md` - Incident response

**External:**
- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)

---

### Support

**Questions?**
- Security Team: @security-team
- DevOps: @devops
- Create issue in repository

---

**Security Testing Status:** ✅ Production Ready
**Last Updated:** December 26, 2025
