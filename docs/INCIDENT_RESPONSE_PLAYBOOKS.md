# Security Incident Response Playbooks

## Purpose

This document provides step-by-step procedures for responding to security incidents. Use these playbooks during actual security incidents and for training purposes.

---

## Table of Contents

1. [Critical CVE Detected](#playbook-1-critical-cve-detected)
2. [Package Signature Verification Failed](#playbook-2-package-signature-verification-failed)
3. [Container Image Compromise](#playbook-3-container-image-compromise)
4. [Supply Chain Attack Indicators](#playbook-4-supply-chain-attack-indicators)
5. [Unauthorized Access Attempt](#playbook-5-unauthorized-access-attempt)
6. [Data Exfiltration Attempt](#playbook-6-data-exfiltration-attempt)

---

## Playbook 1: Critical CVE Detected

### Trigger
- CVE monitoring workflow creates GitHub issue with CRITICAL label
- CISA KEV catalog lists CVE affecting PsychSync dependencies
- Active exploitation detected in the wild

### Severity
**CRITICAL** - Respond within 1 hour

### Response Team
- **Incident Commander**: Security Lead
- **Technical Lead**: Senior Backend Engineer
- **Communications**: Security + DevOps Engineers

### Procedure

#### Phase 1: Assessment (0-15 minutes)

**1.1 Gather Initial Information**

```bash
# Get CVE details
cve_id="CVE-2024-12345"

# Check VEX analysis
python3 << 'EOF'
import json
with open('vex-baseline.json', 'r') as f:
    vex = json.load(f)

for statement in vex['statements']:
    if statement['vulnerability'] == cve_id:
        print(json.dumps(statement, indent=2))
EOF

# Check CVE monitoring history
grep -A 20 "$cve_id" .github/cve-history.json
```

**1.2 Determine Impact**

```bash
# Check if vulnerable code is in execution path
# Use VEX analysis to determine:

# Status: not_affected
# → Document justification and close issue

# Status: affected
# → Proceed to Phase 2
```

**1.3 Escalate if Critical**

If CVE is in CISA KEV or has known exploits:
```bash
# Create incident ticket
gh issue create \
  --title "🚨 SECURITY INCIDENT: $cve_id - Active Exploitation" \
  --label "security,critical,incident" \
  --body "Critical CVE detected with active exploitation. Immediate response required."

# Notify security team
# Slack: #security-incidents channel
# Email: security@psychsync.com, leadership@psychsync.com
```

#### Phase 2: Containment (15-60 minutes)

**2.1 Identify Affected Systems**

```bash
# Check which packages/components are affected
pip show package-name

# Find all versions of package in use
pip list | grep package-name

# Check if package is in critical path
grep -r "import package-name" app/
```

**2.2 Determine Mitigation Options**

```bash
# Option A: Update package (if fix available)
pip show package-name | grep "Version"

# Option B: Disable feature (if workaround available)
# Review VEX for mitigation guidance

# Option C: Shutdown service (worst case)
```

**2.3 Implement Temporary Mitigation**

```bash
# If update available:
pip install package==fixed-version

# Update allow-list
vim allowed-dependencies.txt
# Update version range for package

# Test thoroughly
pytest tests/test_package.py -v

# Commit and deploy
git commit -m "security: Emergency fix for $cve_id"
git tag v1.0.1-emergency
git push origin main --tags
```

#### Phase 3: Eradication (1-24 hours)

**3.1 Verify Fix**

```bash
# Download new release
wget https://github.com/psychsync/psychsync/releases/download/v1.0.1/vex.json

# Verify CVE shows as fixed
jq '.statements[] | select(.vulnerability == "$cve_id")' vex.json

# Should show: "status": "fixed"
```

**3.2 Comprehensive Testing**

```bash
# Run full test suite
pytest tests/ -v

# Run security tests
pytest tests/test_security.py -v

# Manual verification
# - Test affected functionality
# - Verify no regressions
# - Check performance
```

**3.3 Deploy to Production**

```bash
# Monitor deployment
gh workflow view signed-release.yml

# Verify in production
curl -f https://api.psychsync.com/health
```

#### Phase 4: Recovery (24-72 hours)

**4.1 Monitor for Issues**

```bash
# Check logs for any anomalies
# - Application logs
# - Security logs
# - Performance metrics

# Monitor CVE database for any new related CVEs
python3 scripts/cve-monitor.py --check
```

**4.2 Post-Incident Review**

```bash
# Generate incident report
python3 << 'EOF'
import json
from datetime import datetime

report = {
    "incident_type": "CVE",
    "cve_id": "$cve_id",
    "detected_at": "$DETECTION_TIME",
    "resolved_at": datetime.utcnow().isoformat(),
    "mttd": "6 hours",
    "mttr": "24 hours",
    "impact": "Critical vulnerability patched before exploitation",
    "lessons_learned": [
        "CVE monitoring worked as expected",
        "VEX analysis enabled rapid prioritization",
        "Automated deployment reduced MTTR"
    ]
}

with open('incident-report-$cve_id.json', 'w') as f:
    json.dump(report, f, indent=2)
EOF
```

**4.3 Update Documentation**

```bash
# Update runbooks
# Create knowledge base article
# Present at incident review meeting
```

---

## Playbook 2: Package Signature Verification Failed

### Trigger
- Dependency governance workflow fails
- Sigstore verification fails for a package
- cosign verify reports signature mismatch

### Severity
**HIGH** - Respond within 4 hours

### Response Team
- **Incident Commander**: Security Lead
- **Technical Lead**: DevOps Engineer
- **Investigator**: Security Engineer

### Procedure

#### Phase 1: Investigation (0-30 minutes)

**1.1 Identify Failed Package**

```bash
# Check workflow logs
gh run view [run-id] --log-failed

# Identify which package failed
# Look for: "signature verification failed" or "sigstore verify failed"
```

**1.2 Manual Verification**

```bash
# Try manual verification
package_name="package-name"
sigstore verify identity "$package_name"

# Check error message
# Common errors:
# - "signature not found": Package not signed
# - "signature mismatch": Package tampered with
# - "untrusted issuer": Publisher changed
```

**1.3 Check Package Source**

```bash
# Get package details
pip show "$package_name"

# Check PyPI page
curl -s "https://pypi.org/pypi/$package_name/json" | jq '.'

# Check:
# - Is package popular? (download count)
# - Is package actively maintained? (upload date)
# - Is publisher legitimate? (author, email)
# - Are there similar package names? (typosquatting)
```

#### Phase 2: Assessment (30-120 minutes)

**2.1 Determine Category**

**Category A: Legitimate but Unsigned**
- Package is from trusted source
- Package is widely used
- No signs of compromise
- **Action**: Allow for 30 days while publisher adds signing

**Category B: Suspicious**
- Unknown author
- Very recent upload
- No other downloads
- Similar name to popular package (typosquatting)
- **Action**: Block immediately, investigate further

**Category C: Compromised**
- Signature doesn't match
- File hash mismatch
- Publisher changed
- **Action**: CRITICAL - Full incident response

**2.2 Document Findings**

```bash
cat > investigation-report.md << 'EOF'
# Package Signature Verification Investigation

## Package: package-name
## Date: $(date)

## Findings
- Verification Error: [error message]
- Package Source: PyPI
- Download Count: [count]
- Last Update: [date]
- Author: [author]

## Category
- [ ] Legitimate but Unsigned
- [ ] Suspicious
- [ ] Compromised

## Recommendation
[Explain what should be done]
EOF
```

#### Phase 3: Resolution (2-24 hours)

**3.1 For Legitimate but Unsigned**

```bash
# Add to allow-list temporarily
echo "package-name==1.2.3,1.5.0  # Unsigned but verified" >> allowed-dependencies.txt

# Create issue with publisher
# Request them to sign their packages with sigstore

# Set review reminder for 30 days
gh issue create \
  --title "Package signature required: package-name" \
  --label "security,signature" \
  --body "Package needs to be signed. Reminder to follow up in 30 days."
```

**3.2 For Suspicious**

```bash
# Block package immediately
echo "package-name  # BLOCKED: Suspicious package, under investigation" >> allowed-dependencies.txt

# Search for usage
grep -r "package-name" app/ frontend/

# Remove if found
# Replace with alternative package

# Report to PyPI if typosquatting
# https://pypi.org/report/
```

**3.3 For Compromised**

```bash
# This is a security incident - activate full incident response
# See Playbook 6: Data Exfiltration Attempt

# Immediate actions:
# 1. Block package
# 2. Check for any usage in production
# 3. Scan for indicators of compromise
# 4. Rotate credentials if package was deployed
# 5. Notify security team
```

#### Phase 4: Prevention (Ongoing)

**4.1 Update Allow-List Policy**

```bash
# Add policy for unsigned packages
cat >> allowed-dependencies.txt << 'EOF'
# Policy for Unsigned Packages
# All critical packages MUST be signed
# Temporarily allow unsigned packages for 30 days
# after security team approval
EOF
```

**4.2 Enhance Monitoring**

```yaml
# Add to .github/workflows/dependency-governance.yml
# Alert on unsigned packages in critical path
- name: Alert on unsigned critical packages
  if: contains(needs.signature-verification.outputs.unsigned_packages, 'critical-package')
  run: |
    gh issue create \
      --title "⚠️ Critical Package Unsigned" \
      --label "security,critical" \
      --body "Critical package without signature detected"
```

---

## Playbook 3: Container Image Compromise

### Trigger
- Container image verification fails
- cosign verify shows signature mismatch
- Security scanner finds malware in image
- Image contains unexpected packages

### Severity
**CRITICAL** - Respond within 1 hour

### Response Team
- **Incident Commander**: Security Lead
- **Technical Lead**: DevOps Lead
- **Infrastructure**: Site Reliability Engineer
- **Communications**: PR/Security Manager

### Procedure

#### Phase 1: Immediate Response (0-15 minutes)

**1.1 Identify Compromised Image**

```bash
# Get image digest
IMAGE="ghcr.io/psychsync/psychsync/backend:latest"
docker inspect $IMAGE | jq '.[0].RepoDigests'

# Check when image was built
gh workflow view [workflow-run]
```

**1.2 Determine Scope**

```bash
# Check if image is deployed to production
kubectl get pods -l app=psychsync-backend
# Look for affected image digest

# Check registry
cosign verify $IMAGE 2>&1 | head -20
```

**1.3 Activate Incident Response**

```bash
# Create incident ticket
gh issue create \
  --title "🚨 INCIDENT: Container Image Compromise" \
  --label "security,critical,incident" \
  --body "Container image signature verification failed. Image may be compromised."

# Notify all teams
# Slack: #general, #engineering, #security
# Email: all@psychsync.com
```

#### Phase 2: Investigation (15-60 minutes)

**2.1 Pull Image for Analysis**

```bash
# Pull image
docker pull $IMAGE

# Export image filesystem
docker export $IMAGE > compromised-image.tar

# Extract and scan
mkdir /tmp/image-analysis
tar -xf compromised-image.tar -C /tmp/image-analysis

# Scan for suspicious files
find /tmp/image-analysis -name "*.sh" -o -name "*.exe" -o -name "*.dll"
```

**2.2 Scan for Malware**

```bash
# Install Trivy if not available
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image $IMAGE

# Look for:
# - Critical vulnerabilities
# - Known malware signatures
# - Suspicious packages
```

**2.3 Check Build Logs**

```bash
# Check GitHub Actions workflow logs
gh run view [workflow-run] --log

# Look for:
# - Unauthorized access
# - Unexpected dependencies
# - Modified build steps
# - Failed security checks
```

#### Phase 3: Containment (60-120 minutes)

**3.1 Roll Back Deployment**

```bash
# Identify last known good image
cosign verify ghcr.io/psychsync/psychsync/backend:previous-good-tag

# Roll back
kubectl rollout undo deployment/psychsync-backend

# Verify rollback
kubectl get pods -l app=psychsync-backend
curl -f https://api.psychsync.com/health
```

**3.2 Revoke Compromised Image**

```bash
# Remove from registry
# This requires GitHub admin access

# Tag image as compromised
# Or remove entirely from registry
```

**3.3 Scan Production Environment**

```bash
# Run vulnerability scan on all containers
kubectl get pods -o json | jq -r '.items[].spec.containers[].image' | sort -u | \
  xargs -I {} docker run --rm aquasec/trivy image {}

# Check for running pods using compromised image
kubectl get pods -o json | \
  jq -r '.items[] | select(.spec.containers[].image | contains("COMPROMISED_DIGEST")) | .metadata.name'
```

#### Phase 4: Recovery (2-24 hours)

**4.1 Rebuild and Sign New Image**

```bash
# Ensure build environment is clean
# Verify no CI/CD runners are compromised

# Trigger clean build
gh workflow run signed-release.yml

# Verify new image
NEW_IMAGE="ghcr.io/psychsync/psychsync/backend:clean-tag"
cosign verify $NEW_IMAGE
```

**4.2 Deploy Clean Image**

```bash
# Update deployment
kubectl set image deployment/psychsync-backend \
  backend=$NEW_IMAGE

# Verify
kubectl rollout status deployment/psychsync-backend
curl -f https://api.psychsync.com/health
```

**4.3 Post-Incident Actions**

```bash
# Rotate all secrets
# - Kubernetes secrets
# - Environment variables
# - API keys

# Force password reset for all users
# Require MFA re-setup

# Audit all access logs
grep "COMPROMISED_DIGEST" /var/log/auth.log
```

---

## Playbook 4: Supply Chain Attack Indicators

### Trigger
- Multiple CVEs detected in quick succession
- Unusual dependency update patterns
- Unknown packages appearing in allow-list requests
- Failed signature verifications across multiple packages

### Severity
**CRITICAL** - Respond within 30 minutes

### Response Team
- **Incident Commander**: CTO
- **Technical Lead**: Security Lead
- **Investigation**: Security + DevOps Teams
- **Communications**: PR Manager

### Procedure

#### Phase 1: Detection (0-30 minutes)

**1.1 Check Attack Indicators**

```bash
# Check for multiple CVEs
python3 scripts/cve-monitor.py --check | grep "CRITICAL" | wc -l
# If > 3, potential supply chain attack

# Check for unusual PRs
gh pr list --state merged --limit 50 | grep "dependency"

# Check allow-list modification history
git log --oneline --all -- allowed-dependencies.txt | head -20

# Check for failed signature verifications
gh run list --workflow=dependency-governance.yml --status failure
```

**1.2 Determine Attack Vector**

```bash
# Common attack vectors:
# 1. Dependency confusion (publishing malicious package)
# 2. Typosquatting (fake package with similar name)
# 3. Compromised maintainer account
# 4. Build system compromise
# 5. Container registry compromise
```

**1.3 Activate Incident Response**

```bash
# Declare major security incident
gh issue create \
  --title "🚨 MAJOR INCIDENT: Potential Supply Chain Attack" \
  --label "security,critical,incident,supply-chain" \
  --body "Multiple supply chain attack indicators detected. Full incident response activated."

# Assemble war room
# Set up incident bridge
# Notify leadership
```

#### Phase 2: Investigation (30-120 minutes)

**2.1 Scope Assessment**

```bash
# Check all recent dependency changes
git log --all --since="7 days ago" -- requirements.txt frontend/package.json

# Audit all merged PRs
gh pr list --state merged --since="7 days ago"

# Check build logs
gh run list --workflow=signed-release.yml --limit 20

# Check for unauthorized commits
git log --all --since="7 days ago" --pretty="%h %an %s"
```

**2.2 Identify Affected Systems**

```bash
# List all deployed images
kubectl get pods -o json | jq -r '.items[].spec.containers[].image' | sort -u

# Check all installed packages
pip list --format=json > installed-packages.json
npm list --json --depth=0 > frontend-packages.json

# Compare with baseline
diff baseline-packages.json installed-packages.json
```

**2.3 Forensic Analysis**

```bash
# Check CI/CD runner logs
# Look for:
# - Unusual commands executed
# - Network connections to unexpected IPs
# - File system modifications

# Check GitHub actions logs for:
# - Failed authentication attempts
# - Authorization changes
# - Workflow modifications
```

#### Phase 3: Containment (2-4 hours)

**3.1 Pause All Deployments**

```bash
# Protect production by pausing deployments
# GitHub: Settings → Branches → Add rule
# Block all pushes to main

# Protect CI/CD
# Disable auto-deployment
# Require manual approval for all deployments
```

**3.2 Rotate All Credentials**

```bash
# Rotate:
# - GitHub tokens (repo, workflow, PAT)
# - Container registry credentials
# - Cloud provider credentials (AWS, GCP)
# - Database credentials
# - API keys

# Assume all secrets are compromised
```

**3.3 Revert to Known Good State**

```bash
# Identify last known good commit
git log --all --since="14 days ago" --pretty="%h %s" | grep "security"

# Revert to that commit
# Rebuild all images
# Redeploy from known good source

# Verify all signatures
cosign verify ghcr.io/psychsync/psychsync/backend:tag
```

#### Phase 4: Recovery (24-72 hours)

**4.1 Clean Build Environment**

```bash
# Terminate all CI/CD runners
kubectl delete runners --all -n github-actions

# Create fresh runners
# Apply .github/ephemeral-runners.yml from clean backup

# Verify no backdoors
```

**4.2 Rebuild Everything**

```bash
# Clone repository to fresh directory
git clone https://github.com/psychsync/psychsync.git fresh-copy
cd fresh-copy

# Verify all signatures
# Verify all allow-lists
# Run all tests
# Create new signed release
```

**4.3 Gradual Restoration**

```bash
# Deploy to staging first
# Monitor for 24 hours
# Fix any issues

# Then deploy to production
# Monitor for 48 hours
# Have rollback plan ready

# Full operational after 72 hours of monitoring
```

---

## Playbook 5: Unauthorized Access Attempt

### Trigger
- Multiple failed authentication attempts
- Authorization denials for sensitive resources
- Cross-tenant access attempts detected
- Unusual IP addresses accessing systems

### Severity
**MEDIUM** - Respond within 8 hours

### Response Team
- **Incident Commander**: Security Lead
- **Technical Lead**: DevOps Engineer

### Procedure

#### Phase 1: Investigation (0-60 minutes)

**1.1 Check Audit Logs**

```bash
# Check authentication logs
grep "AUTH_LOGIN_FAILED" /var/log/audit.log | tail -50

# Check authorization denials
grep "AUTHZ_ACCESS_DENIED" /var/log/audit.log | tail -50

# Check cross-tenant attempts
grep "TENANT_CROSS_ACCESS" /var/log/audit.log | tail -50
```

**1.2 Identify Pattern**

```bash
# Look for:
# - Same IP, multiple users (password spraying)
# - Same user, multiple IPs (credential stuffing)
# - Multiple users, same IP (botnet)
# - Targeted user (spear phishing)

# Check IP reputation
# https://abuseipdb.com/check/[IP]
```

**1.3 Determine Scope**

```bash
# Check if access was successful
grep "AUTH_LOGIN_SUCCESS" /var/log/audit.log | grep [IP]

# Check what resources were accessed
grep [USER_ID] /var/log/audit.log | grep "DATA_ACCESSED"
```

#### Phase 2: Response (1-4 hours)

**2.1 Block Attackers**

```bash
# Block IP at firewall
# Option A: Cloud firewall (AWS, GCP, Azure)
# Option B: Application firewall (WAF)
# Option C: Kubernetes network policy

# Example: Kubernetes denylist
kubectl annotate namespace default "firewall/blocked-ips=[IP1,IP2]"
```

**2.2 Compromised Accounts**

```bash
# If access was successful:
# - Lock account
# - Rotate credentials
# - Revoke all sessions
python3 << 'EOF'
from app.services.session_service import session_service

# Revoke all sessions for user
user_id = "compromised-user-id"
await session_service.revoke_all_user_sessions(user_id, "Security incident")
EOF

# Force password reset
# Require MFA re-setup
```

**2.3 Strengthen Controls**

```bash
# Temporarily enable:
# - Rate limiting (stricter)
# - MFA requirement (all users)
# - IP whitelist (if applicable)
# - CAPTCHA on login

# Example: Update rate limiting
# app/core/advanced_rate_limiter.py
# Reduce threshold to 3 attempts per 5 minutes
```

#### Phase 3: Prevention (Ongoing)

**3.1 Update Security Policies**

```bash
# Add to security policy:
# - 3 failed logins → 30-minute lockout
# - 5 failed logins → 1-hour lockout
# - Failed logins from new country → notify
```

**3.2 Implement Improvements**

```bash
# Add geo-blocking for high-risk countries
# Implement device fingerprinting
# Add behavioral analysis
# Enhance monitoring and alerting
```

---

## Playbook 6: Data Exfiltration Attempt

### Trigger
- Unusually large data export
- Access to encrypted fields at unusual times
- Cross-tenant data access
- Mass download requests

### Severity
**CRITICAL** - Respond within 30 minutes

### Response Team
- **Incident Commander**: CTO + Security Lead
- **Technical Lead**: Security Engineer
- **Communications**: PR Manager + Legal Counsel
- **Executive**: CEO + Board

### Procedure

#### Phase 1: Immediate Response (0-15 minutes)

**1.1 Identify Activity**

```bash
# Check audit logs for data access
grep "DATA_EXPORTED" /var/log/audit.log | tail -100

# Check for large transfers
# Look for unusually large API responses
# Check download logs

# Identify user account
grep [USER_ID] /var/log/audit.log | tail -100
```

**1.2 Contain Threat**

```bash
# IMMEDIATE ACTIONS:
# 1. Revoke all user sessions
python3 -c "from app.services.session_service import session_service; import asyncio; asyncio.run(session_service.revoke_all_user_sessions('$USER_ID'))"

# 2. Lock user account
# Via admin panel or direct DB update

# 3. Block IP address
# At firewall/WAF

# 4. Enable enhanced monitoring
# Enable additional logging for all activity
```

**1.3 Activate Incident Response**

```bash
# Create critical incident ticket
gh issue create \
  --title "🚨 CRITICAL: Data Exfiltration Attempt" \
  --label "security,critical,incident,data-breach" \
  --body "Potential data exfiltration detected. Immediate containment in progress."

# Notify legal counsel
# Notify executive team
# Prepare breach notification (if required)
```

#### Phase 2: Investigation (15-120 minutes)

**2.1 Determine Scope**

```bash
# Check all access by user
grep [USER_ID] /var/log/audit.log

# Check data accessed
grep "DATA_ACCESSED" /var/log/audit.log | grep [USER_ID]

# Check what was exported
grep "DATA_EXPORTED" /var/log/audit.log | grep [USER_ID]

# Check encrypted field access
grep "data_encrypted" /var/log/audit.log | grep [USER_ID]

# Check cross-tenant access
grep "TENANT_CROSS_ACCESS" /var/log/audit.log | grep [USER_ID]
```

**2.2 Preserve Evidence**

```bash
# Export audit logs for user
grep [USER_ID] /var/log/audit.log > incident-[USER_ID]-$(date +%Y%m%d-%H%M%S).log

# Preserve database records
# Export all user data before any changes

# Save session data
# Save authentication logs

# Hash of all data accessed
# Create chain of custody documentation
```

**2.3 Assess Impact**

```bash
# Determine:
# - What data was accessed?
# - What data was exported?
# - Was data encrypted?
# - Were other accounts accessed?
# - Was this an insider or external attacker?

# Classify incident type:
# - Confidentiality breach
# - Privacy breach
# - Compliance violation (HIPAA, GDPR, etc.)
```

#### Phase 3: Notification (2-72 hours)

**3.1 Internal Notification**

```bash
# Notify:
# - Executive team
# - Security team
# - Legal team
# - PR team
# - Affected customers (if required)
```

**3.2 External Notification (if required)**

**If personal data breached** (under GDPR, HIPAA, etc.):
- **GDPR**: Notify within 72 hours
- **HIPAA**: Notify within 60 days
- **State Laws**: Varies (some require immediate)

**3.3 Regulatory Reporting**

```bash
# Document for regulators:
# - What happened
# - When it happened
# - What data was affected
# - What we're doing about it
# - How we're preventing recurrence
```

#### Phase 4: Recovery (7-30 days)

**4.1 Root Cause Analysis**

```bash
# Conduct full investigation:
# - How did attacker get access?
#   - Compromised credentials?
#   - Session hijacking?
#   - Authorization bypass?
#   - Cross-tenant vulnerability?

# - What allowed exfiltration?
#   - Lack of monitoring?
#   - Missing rate limits?
#   - No data loss prevention?
```

**4.2 Implement Improvements**

```bash
# Based on root cause, implement:
# - Stronger authentication
# - Enhanced monitoring
# - Data loss prevention (DLP)
# - Rate limiting
# - Anomaly detection
# - Security awareness training
```

**4.3 Post-Incident Review**

```bash
# Generate incident report
python3 scripts/compliance-report.py --format json > incident-report.json

# Present to stakeholders
# Document lessons learned
# Update policies and procedures
# Schedule follow-up security review
```

---

## Post-Incident Review Template

After any security incident, complete this review within 7 days:

### Incident Summary

| Field | Value |
|-------|-------|
| **Incident Type** | CVE / Signature Failure / Image Compromise / Unauthorized Access / Data Exfiltration |
| **Severity** | Critical / High / Medium / Low |
| **Duration** | Start: ____ End: ____ |
| **Impact** | Systems affected: ____ Data affected: ____ |
| **Root Cause** | ____ |

### Timeline

| Time | Event | Action Taken |
|------|-------|--------------|
| 0h | Incident detected | ____ |
| 1h | Incident response activated | ____ |
| 4h | Containment achieved | ____ |
| 24h | Eradication complete | ____ |
| 72h | Full recovery | ____ |

### Lessons Learned

1. **What went well?**
   - ____
   - ____

2. **What could be improved?**
   - ____
   - ____

3. **Action Items**
   - [ ] ___
   - [ ] ___
   - [ ] ___

### Approval

**Incident Commander**: _________________________ **Date**: _______

**Security Lead**: _________________________ **Date**: _______

**CTO**: _________________________ **Date**: _______

---

**Playbook Version**: 1.0
**Last Updated**: 2024-12-25
**Next Review**: 2025-03-25
**Maintained By**: Security Team
