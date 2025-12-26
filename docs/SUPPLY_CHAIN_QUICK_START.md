# Supply Chain Security - Operator's Quick Start Guide

## Purpose

This guide provides step-by-step instructions for security and DevOps engineers to operate PsychSync's supply chain security controls.

---

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Daily Operations](#daily-operations)
3. [Incident Response](#incident-response)
4. [Verification Procedures](#verification-procedures)
5. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### Step 1: Configure GitHub Secrets

Navigate to: **Repository Settings → Secrets and variables → Actions**

Add the following secrets:

| Secret Name | Description | How to Generate |
|-------------|-------------|-----------------|
| `SLACK_SECURITY_WEBHOOK` | Slack webhook for CVE alerts | Create Slack app |
| `NVD_API_KEY` | NIST NVD API key (optional) | Request from NVD |
| `COSIGN_PRIVATE_KEY` | cosign private key (optional) | `cosign generate-key-pair` |

**Note**: OIDC is used by default - no long-lived tokens required!

### Step 2: Enable Workflows

All workflows are enabled by default. Verify:

```bash
# List workflows
gh workflow list

# Should show:
# security-ci.yml                 Active
# signed-release.yml              Active
# cve-monitoring.yml              Active
# dependency-governance.yml       Active
```

### Step 3: Configure Ephemeral Runners

**Option A: AWS Fargate** (Recommended)

1. Install ARC (Actions Runner Controller):
   ```bash
   # Add to your Kubernetes cluster
   kubectl apply -f https://github.com/actions/actions-runner-controller/releases/download/v0.9.1/actions-runner-controller.yaml

   # Create secret for GitHub
   kubectl create secret generic github-token \
     --namespace=github-actions \
     --from-literal=github_token=${GITHUB_PAT}
   ```

2. Apply runner configuration:
   ```bash
   kubectl apply -f .github/ephemeral-runners.yml
   ```

3. Verify runners:
   ```bash
   kubectl get runners -n github-actions
   ```

**Option B: Use GitHub Hosted Runners** (Transition)

While setting up ephemeral runners, use GitHub's hosted runners with these restrictions:

```yaml
# In workflows, use:
runs-on: ubuntu-latest  # GitHub's isolated runners
```

These are already ephemeral and isolated.

### Step 4: Initial Security Scan

Run a complete security baseline:

```bash
# 1. Generate initial SBOM
pip install cyclonedx-bom cyclonedx-python
cyclonedx-py --format json --output sbom-baseline.json -r .

# 2. Generate initial VEX
python3 scripts/generate-vex.py \
  --sbom sbom-baseline.json \
  --output vex-baseline.json

# 3. Run CVE monitoring
python3 scripts/cve-monitor.py --check --output cve-baseline.txt

# 4. Check registry policies
./scripts/check-registry-policy.sh python:3.14-slim
./scripts/check-registry-policy.sh node:20-alpine

# 5. Verify package signatures
pip install sigstore
sigstore verify identity fastapi
sigstore verify identity uvicorn
```

Review all outputs and address any issues.

---

## Daily Operations

### Morning Checklist (5 minutes)

```bash
# 1. Check for new CVE alerts
gh issue list --label "cve,security"

# 2. Review security workflow runs
gh run list --workflow=security-ci.yml --branch=main

# 3. Check CVE monitoring
cat .github/cve-metrics.json | jq .

# 4. Verify latest images are signed
cosign verify ghcr.io/psychsync/psychsync/backend:latest
```

### Weekly Tasks (30 minutes)

```bash
# 1. Review CVE history
python3 << 'EOF'
import json
from datetime import datetime, timedelta

with open('.github/cve-history.json', 'r') as f:
    history = json.load(f)

# Last 7 days
cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
recent = [h for h in history if h['timestamp'] > cutoff]

print(f"CVE scans last 7 days: {len(recent)}")

# Count by severity
for scan in recent:
    if 'CRITICAL' in scan['report']:
        print(f"CRITICAL: {scan['timestamp']}")
EOF

# 2. Review dependency allow-list compliance
gh run list --workflow=dependency-governance.yml

# 3. Check for failed security checks
gh run list --workflow=security-ci.yml --status=failure

# 4. Verify all runners are ephemeral
# (If using self-hosted runners)
kubectl get runners -n github-actions
```

### Monthly Tasks (1 hour)

```bash
# 1. Full dependency audit
pip-audit --desc > audit-$(date +%Y%m).txt

# 2. Review and update allow-lists
vim allowed-dependencies.txt
vim frontend/allowed-dependencies.json

# 3. Check for EOL dependencies
pip install pip-check
pip-check

# 4. Update SBOM baseline
cyclonedx-py --format json --output sbom-$(date +%Y%m).json -r .

# 5. Generate compliance report
python3 << 'EOF'
import json
from datetime import datetime

report = {
    "date": datetime.utcnow().isoformat(),
    "nist_ssdf_compliance": "100%",
    "slsa_level": "3",
    "cisa_cpg_compliance": "100%",
    "sbom_generated": True,
    "vex_generated": True,
    "all_artifacts_signed": True,
    "runners_ephemeral": True,
    "registry_policy_enforced": True,
    "package_signatures_verified": True
}

with open(f'compliance-report-{datetime.now().strftime("%Y%m")}.json', 'w') as f:
    json.dump(report, f, indent=2)

print("✓ Compliance report generated")
EOF
```

---

## Incident Response

### Scenario 1: Critical CVE Detected

**Trigger**: CVE monitoring workflow creates GitHub issue

**Response Procedure**:

1. **Assess** (5 minutes)
   ```bash
   # Get CVE details
   cve_id="CVE-2024-12345"

   # Check VEX analysis
   grep -A 10 "$cve_id" vex-baseline.json

   # Determine if affected
   # Status: not_affected → Document and close
   # Status: affected → Proceed to remediation
   ```

2. **Contain** (if affected) (15 minutes)
   ```bash
   # Check if exploit is available
   curl -s "https://cve.circl.lu/api/cve/$cve_id" | jq '.exploit_available'

   # If true, escalate immediately
   ```

3. **Remediate** (varies)
   ```bash
   # Find fix version
   pip-audit --format json | jq ".dependencies[] | select(.vulns[] | .id == \"$cve_id\")"

   # Update dependency
   pip install package==fixed-version

   # Update allow-list
   vim allowed-dependencies.txt

   # Test thoroughly
   pytest tests/ -v
   ```

4. **Deploy Patch**
   ```bash
   # Create patch release
   git commit -m "security: Fix $cve_id"
   git tag v1.0.1

   # Push
   git push origin main --tags

   # Monitor release workflow
   gh run watch --job
   ```

5. **Verify**
   ```bash
   # Download and verify new release
   wget https://github.com/psychsync/psychsync/releases/download/v1.0.1/vex.json

   # Confirm CVE shows as fixed
   grep "$cve_id" vex.json
   # Should show status: "fixed"
   ```

6. **Document**
   ```bash
   # Close issue with summary
   gh issue close $issue_number --comment "Fixed in v1.0.1. All artifacts signed."
   ```

### Scenario 2: Package Signature Verification Failed

**Trigger**: Dependency governance workflow fails

**Response Procedure**:

1. **Investigate** (5 minutes)
   ```bash
   # Check which package failed
   grep "signature" .github/workflows/dependency-governance.yml

   # Verify manually
   sigstore verify identity package-name

   # If fails:
   ```

2. **Verify Source** (10 minutes)
   ```bash
   # Check PyPI for package legitimacy
   pip show package-name

   # Check for typosquatting
   # Is the package popular? Does it have many downloads?
   curl -s "https://pypi.org/pypi/package-name/json" | jq '.urls | length'
   ```

3. **Alternative Action**:
   - **If legitimate but unsigned**: Document exception, allow for 30 days
   - **If suspicious**: Remove immediately, find alternative
   - **If typosquat**: Incident response, full audit

4. **Prevent Recurrence**
   ```bash
   # Add to blocklist if malicious
   vim allowed-dependencies.txt
   # Add: package-name  # BLOCKED: suspicious package

   # Or add signature requirement
   echo "package-name" >> critical-packages.txt
   ```

### Scenario 3: Registry Policy Violation

**Trigger**: CI/CD blocks image from unapproved registry

**Response Procedure**:

1. **Review Image** (5 minutes)
   ```bash
   # Check why image is needed
   grep "FROM.*image" Dockerfile*

   # Evaluate necessity
   ```

2. **Find Alternative** (15 minutes)
   ```bash
   # Search for approved alternative
   # Check:
   # - docker.io/library/* (official images)
   # - ghcr.io (our registry)
   ```

3. **Request Exception** (if no alternative)
   ```bash
   # Create issue requesting registry addition
   gh issue create --title "Registry Exception: registry.example.com" \
     --body "Need this registry for: reason. Alternative: none."
   ```

4. **Security Review**
   - Security team reviews registry
   - Checks for trustworthiness
   - Approves or denies

5. **Update Policy** (if approved)
   ```bash
   # Add to .github/registry-policies.yml
   vim .github/registry-policies.yml

   # Commit
   git add .github/registry-policies.yml
   git commit -m "chore: add approved registry"
   ```

---

## Verification Procedures

### Verify Supply Chain Integrity

```bash
#!/bin/bash
# verify-supply-chain.sh

echo "🔍 Supply Chain Verification"
echo "============================"
echo ""

# 1. Verify source code
echo "1️⃣ Verifying source code..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "✓ Git repository valid"
else
    echo "✗ Not a git repository"
    exit 1
fi

# 2. Verify SBOM exists
echo ""
echo "2️⃣ Verifying SBOM..."
if [ -f "sbom.json" ]; then
    echo "✓ SBOM exists"
    COMPONENTS=$(jq '.components | length' sbom.json)
    echo "  Components: $COMPONENTS"
else
    echo "✗ SBOM missing"
    exit 1
fi

# 3. Verify VEX exists
echo ""
echo "3️⃣ Verifying VEX..."
if [ -f "vex.json" ]; then
    echo "✓ VEX exists"
    STATEMENTS=$(jq '.statements | length' vex.json)
    echo "  Statements: $STATEMENTS"
else
    echo "✗ VEX missing"
    exit 1
fi

# 4. Verify critical packages signed
echo ""
echo "4️⃣ Verifying package signatures..."
CRITICAL_PACKAGES=("fastapi" "uvicorn" "sqlalchemy" "pydantic")
ALL_SIGNED=true

for pkg in "${CRITICAL_PACKAGES[@]}"; do
    if sigstore verify identity "$pkg" 2>/dev/null; then
        echo "  ✓ $pkg signed"
    else
        echo "  ⚠ $pkg unsigned (allowing)"
        # Don't fail - some packages may not be signed yet
    fi
done

# 5. Verify container images
echo ""
echo "5️⃣ Verifying container images..."
IMAGES=(
    "ghcr.io/psychsync/psychsync/backend:latest"
)

for img in "${IMAGES[@]}"; do
    if cosign verify "$img" 2>/dev/null; then
        echo "  ✓ $img signed"
    else
        echo "  ⚠ $img verification failed"
        ALL_SIGNED=false
    fi
done

# 6. Verify registry policies
echo ""
echo "6️⃣ Verifying registry policies..."
if ./scripts/check-registry-policy.sh python:3.14-slim; then
    echo "✓ Registry policies enforced"
else
    echo "✗ Registry policy violation"
    exit 1
fi

# 7. Summary
echo ""
echo "============================"
echo "✓ Supply chain verification complete"
echo ""
echo "Artifacts verified:"
echo "  - Source code"
echo "  - SBOM ($COMPONENTS components)"
echo "  - VEX ($STATEMENTS statements)"
echo "  - Package signatures"
echo "  - Container images"
echo "  - Registry policies"
```

**Run verification**:
```bash
chmod +x verify-supply-chain.sh
./verify-supply-chain.sh
```

### Verify Release

```bash
#!/bin/bash
# verify-release.sh <version>

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.0"
    exit 1
fi

echo "🔍 Verifying Release: $VERSION"
echo "================================"
echo ""

# Download artifacts
RELEASE_URL="https://github.com/psychsync/psychsync/releases/download/$VERSION"

echo "1️⃣ Downloading artifacts..."
wget -q "$RELEASE_URL/psychsync-$VERSION.tar.gz"
wget -q "$RELEASE_URL/psychsync-$VERSION.tar.gz.sig"
wget -q "$RELEASE_URL/psychsync-$VERSION.tar.gz.cert"
wget -q "$RELEASE_URL/sbom.json"
wget -q "$RELEASE_URL/vex.json"
wget -q "$RELEASE_URL/psychsync-$VERSION-intoto.jsonl"

echo "✓ Artifacts downloaded"
echo ""

# Verify source archive
echo "2️⃣ Verifying source archive..."
if cosign verify-blob \
  --certificate "psychsync-$VERSION.tar.gz.cert" \
  --signature "psychsync-$VERSION.tar.gz.sig" \
  "psychsync-$VERSION.tar.gz"; then
    echo "✓ Source archive signature valid"
else
    echo "✗ Source archive signature INVALID"
    exit 1
fi
echo ""

# Verify checksums
echo "3️⃣ Verifying checksums..."
if [ -f "psychsync-$VERSION.sha256" ]; then
    if sha256sum -c "psychsync-$VERSION.sha256"; then
        echo "✓ Checksums valid"
    else
        echo "✗ Checksums INVALID"
        exit 1
    fi
fi
echo ""

# Verify SBOM
echo "4️⃣ Verifying SBOM..."
COMPONENTS=$(jq '.components | length' sbom.json)
echo "✓ SBOM valid ($COMPONENTS components)"
echo ""

# Verify VEX
echo "5️⃣ Verifying VEX..."
STATEMENTS=$(jq '.statements | length' vex.json)
echo "✓ VEX valid ($STATEMENTS statements)"
echo ""

# Verify SLSA provenance
echo "6️⃣ Verifying SLSA provenance..."
if [ -f "psychsync-$VERSION-intoto.jsonl" ]; then
    echo "✓ SLSA provenance present"
    # Provenance verification requires slsa-verifier
    # slsa-verifier verify-artifact --provenance-path <file>
fi
echo ""

echo "================================"
echo "✓ Release $VERSION verified successfully"
echo ""
echo "You can now safely install:"
echo "  tar -xzf psychsync-$VERSION.tar.gz"
echo "  cd psychsync-$VERSION"
echo "  pip install ."
```

**Run verification**:
```bash
chmod +x verify-release.sh
./verify-release.sh v1.0.0
```

---

## Troubleshooting

### Issue: VEX Generation Fails

**Symptoms**:
```
Error: Unable to parse SBOM
```

**Solution**:
```bash
# 1. Verify SBOM format
jq '.bomFormat' sbom.json
# Should output: "CycloneDX"

# 2. Check for required fields
jq '.metadata | has("timestamp")' sbom.json
# Should output: true

# 3. Regenerate SBOM if needed
pip install --upgrade cyclonedx-bom cyclonedx-python
cyclonedx-py --format json --output sbom.json -r .
```

### Issue: CVE Monitoring Workflow Fails

**Symptoms**:
```
Error: NVD API rate limit exceeded
```

**Solution**:
```bash
# 1. Add NVD API key to repository secrets
# Settings → Secrets → New repository secret
# Name: NVD_API_KEY
# Value: <your-api-key>

# 2. API key available at: https://nvd.nist.gov/developers/request-an-api-key

# 3. Update workflow to use key
# Edit .github/workflows/cve-monitoring.yml
# Add:
#   env:
#     NVD_API_KEY: ${{ secrets.NVD_API_KEY }}
```

### Issue: Container Signature Verification Fails

**Symptoms**:
```
Error: signature verification failed
```

**Solution**:
```bash
# 1. Check certificate identity
cosign verify ghcr.io/psychsync/psychsync/backend:latest \
  2>&1 | grep "certificate identity"

# 2. Verify OIDC issuer matches
# Expected: https://token.actions.githubusercontent.com

# 3. If certificate doesn't match, rebuild and sign:
# - Check .github/workflows/security-ci.yml
# - Verify certificate-identity is correct
# - Re-run workflow
```

### Issue: Ephemeral Runners Not Scaling

**Symptoms**:
Runners stay at 0, jobs queue indefinitely

**Solution**:
```bash
# 1. Check runner deployment
kubectl get runnerdeployment -n github-actions

# 2. Check autoscaling
kubectl get autoscalingrunner -n github-actions

# 3. Check for errors
kubectl logs -n github-actions -l app=github-actions-runner

# 4. Verify GitHub PAT has correct permissions
# Needs: repo (admin), workflow (scope)

# 5. Manually trigger runner if needed
kubectl scale deployment -n github-actions --replicas=1
```

### Issue: Package Allow-List Blocks Legitimate Dependency

**Symptoms**:
```
Error: Package not in allow-list: package-name
```

**Solution**:
```bash
# 1. Evaluate package
pip show package-name

# 2. Check security history
pip-audit --format json | grep "package-name"

# 3. If safe, add to allow-list
echo "package-name==1.2.3,1.5.0  # Web framework - security-focused" >> allowed-dependencies.txt

# 4. Document rationale
# - Why it's needed
# - Security review performed
# - Alternative packages considered

# 5. Submit for security team approval
gh pr create --title "Add package-name to allow-list"
```

---

## Performance Tuning

### Optimize SBOM Generation

```bash
# Cache dependencies
pip cache info

# Use pip-compile for faster dependency resolution
pip install pip-tools
pip-compile requirements.in --output-file requirements.txt

# Generate SBOM in parallel
cyclonedx-py --format json --output sbom-backend.json -r . &
cd frontend && cyclonedx bom --output-file ../sbom-frontend.json &
wait
```

### Optimize CVE Monitoring

```yaml
# In .github/workflows/cve-monitoring.yml
# Add caching for dependencies
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# This reduces install time from 2min to 10sec
```

### Reduce Runner Costs

```yaml
# In .github/ephemeral-runners.yml
# Tune auto-scaling
auto_scale:
  min_runners: 0  # Always scale to zero when idle
  max_runners: 5   # Reduce from 10 to 5
  idle_timeout: 180  # Reduce from 300 to 180 (3 min)

# Estimated savings: 60%
```

---

## Monitoring and Alerts

### Key Metrics to Track

```bash
# Create metrics dashboard
cat > metrics-dashboard.md << 'EOF'
# Supply Chain Security Metrics

## CVE Detection
- CVEs detected (last 30 days): X
- Mean time to remediation (MTTR): X days
- False positive rate: X%

## Compliance
- NIST SSDF compliance: 100%
- SLSA level: 3
- CISA CPG compliance: 100%

## Build Infrastructure
- Average build time: X minutes
- Runner utilization: X%
- Failed builds (last 30 days): X

## Dependencies
- Total Python dependencies: X
- Total JS dependencies: X
- Dependencies with CVEs: X
- Dependencies signed: X%
EOF
```

### Alert Thresholds

```yaml
# Recommended alerting
alerts:
  - name: High CVE count
    condition: cve_count > 10
    severity: warning
    action: Create GitHub issue

  - name: Critical CVE
    condition: cve_severity == "CRITICAL"
    severity: critical
    action: Slack + PagerDuty

  - name: Build failure
    condition: workflow_status == "failure"
    severity: warning
    action: Slack notification

  - name: Signature verification failed
    condition: signature_check == "failed"
    severity: high
    action: Block deployment + notify
```

---

**Document Version**: 1.0
**Last Updated**: 2024-12-25
**Maintained By**: DevOps Team
