# Getting Started with PsychSync Security

## Welcome! 👋

This guide will help you get up and running with PsychSync's security infrastructure in **30 minutes**.

---

## 🎯 Learning Path

Choose your role to get started:

| Role | Start Here | Time Commitment |
|------|-----------|------------------|
| **New Developer** | Section 1 | 30 minutes |
| **Security Engineer** | Section 2 | 1 hour |
| **DevOps Engineer** | Section 3 | 2 hours |
| **Manager/Auditor** | Section 4 | 45 minutes |

---

## Section 1: New Developer (30 minutes)

### Goal: Set up your development environment with security tools

#### Step 1: Install Security Tools (5 minutes)

```bash
# Python security tools
pip install bandit[toml] pip-audit cyclonedx-bom

# Node security tools
npm install -g @cyclonedx/cyclonedx

# Verification tools
pip install sigstore
```

#### Step 2: Read the Quick Reference (5 minutes)

```bash
# Print and keep at your desk
cat docs/SECURITY_QUICK_REFERENCE.md

# Or open in your editor
vim docs/SECURITY_QUICK_REFERENCE.md
```

#### Step 3: Run Verification (10 minutes)

```bash
# Verify all security controls are in place
./scripts/verify-supply-chain-security.sh

# You should see:
# ✓ PASS: File exists: scripts/generate-vex.py
# ✓ PASS: File exists: scripts/cve-monitor.py
# ... (17 total checks)
```

#### Step 4: Generate Your First Compliance Report (10 minutes)

```bash
# See your compliance status
python3 scripts/compliance-report.py --format markdown

# Open the report
cat compliance-report-*.md
```

**✅ You're ready to develop securely!**

Next steps:
- Read `docs/SUPPLY_CHAIN_QUICK_START.md` for daily operations
- Review `docs/SECURITY_README.md` for complete overview

---

## Section 2: Security Engineer (1 hour)

### Goal: Understand and validate the security implementation

#### Step 1: Read Security Architecture (15 minutes)

```bash
# Start with executive summary
cat docs/SECURITY_IMPLEMENTATION_SUMMARY.md

# Then read technical reference
cat docs/SUPPLY_CHAIN_SECURITY_V2.md
```

#### Step 2: Review Implementation (20 minutes)

**VEX Generation**:
```bash
# Read VEX script
vim scripts/generate-vex.py

# Understand VEX classes:
# - VEXStatus: Status levels (not_affected, affected, fixed, etc.)
# - VEXAnalyzer: Analyzes vulnerabilities in context
# - VEXGenerator: Creates OpenVEX and CSAF VEX documents

# Test VEX generation
python3 scripts/generate-vex.py --help
```

**CVE Monitoring**:
```bash
# Read CVE monitor script
vim scripts/cve-monitor.py

# Understand components:
# - CVESource: Base class for data sources
# - CVEMonitor: Main monitoring service
# - VulnerabilityAlert: Alert data structure

# Test CVE monitoring
python3 scripts/cve-monitor.py --help
```

**Compliance Reporting**:
```bash
# Read compliance reporter
vim scripts/compliance-report.py

# See how it maps controls to frameworks
grep "class ComplianceReportGenerator" scripts/compliance-report.py -A 10
```

#### Step 3: Run Integration Tests (15 minutes)

```bash
# Install pytest
pip install pytest pytest-cov

# Run all security integration tests
pytest tests/test_supply_chain_security.py -v

# You should see:
# test_vex_script_exists PASSED
# test_vex_script_syntax PASSED
# ... (50+ tests total)

# Check test coverage
pytest tests/test_supply_chain_security.py --cov=scripts --cov-report=html
```

#### Step 4: Review Incident Response Playbooks (10 minutes)

```bash
# Read incident response playbooks
vim docs/INCIDENT_RESPONSE_PLAYBOOKS.md

# Key playbooks:
# 1. Critical CVE Detected
# 2. Package Signature Verification Failed
# 3. Container Image Compromise
# 4. Supply Chain Attack Indicators
# 5. Unauthorized Access Attempt
# 6. Data Exfiltration Attempt
```

**✅ You're ready to be a security champion!**

Next steps:
- Set up automated security testing in CI/CD
- Create custom security playbooks
- Conduct security training for developers

---

## Section 3: DevOps Engineer (2 hours)

### Goal: Set up and operate secure CI/CD pipelines

#### Step 1: Understand CI/CD Architecture (20 minutes)

```bash
# Review all security workflows
ls -la .github/workflows/

# Key workflows:
# 1. security-ci.yml - Main security pipeline
# 2. signed-release.yml - Release workflow
# 3. cve-monitoring.yml - CVE scanning
# 4. dependency-governance.yml - Dependency enforcement

# Read security CI workflow
vim .github/workflows/security-ci.yml

# Understand the jobs:
# Job 1: SAST (Static Application Security Testing)
# Job 2: SCA (Software Composition Analysis)
# Job 3: Secret Scanning
# Job 4: SBOM Generation
# Job 5: VEX Generation
# Job 6: Security Tests (DAST)
# Job 7: SLSA Provenance
# Job 8: Container Signing
```

#### Step 2: Set Up Ephemeral Runners (30 minutes)

**Option A: AWS Fargate**

```bash
# Install kubectl and AWS CLI
# Configure AWS credentials

# Apply runner configuration
kubectl apply -f .github/ephemeral-runners.yml

# Verify runners
kubectl get runners -n github-actions

# Check auto-scaling
kubectl get autoscalingrunner -n github-actions
```

**Option B: GitHub Hosted (Quick Start)**

```bash
# Use GitHub's hosted runners (already ephemeral)
# No setup needed!

# Just configure workflows to use:
# runs-on: ubuntu-latest
```

#### Step 3: Configure Registry Policies (20 minutes)

```bash
# Review registry policies
vim .github/registry-policies.yml

# Add allowed registries for your organization
# Example: Add your private registry
allowed_registries:
  - name: Our Private Registry
    url: gcr.io/our-company
    trust_level: high
    signature_required: true
```

#### Step 4: Test Complete Workflow (30 minutes)

```bash
# Create a test PR to see security in action
git checkout -b test-security-workflow

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: security workflow"
git push origin test-security-workflow

# Watch security checks run
gh pr create --title "Test Security Workflow"

# You should see:
# - SAST scans running
# - SCA scans running
# - Dependency allow-list check
# - Package signature verification
# - SBOM generation
# - VEX generation
```

#### Step 5: Create Your First Signed Release (40 minutes)

```bash
# Ensure all tests pass
pytest tests/ -v

# Run security checks
bandit -r app/ -c .bandit
pip-audit

# Update version
vim app/__init__.py  # Change __version__ = "1.0.0"

# Commit and tag
git add .
git commit -m "Release v1.0.0"
git tag v1.0.0

# Push tag to trigger release workflow
git push origin main --tags

# Monitor release workflow
gh workflow view signed-release.yml

# Wait for completion (~15-20 minutes)
# Check artifacts:
# - Source archive
# - Container images
# - SBOM
# - VEX
# - SLSA provenance
```

**✅ Your CI/CD is production-ready!**

Next steps:
- Set up monitoring dashboards
- Configure automated rollback
- Implement canary deployments
- Set up blue-green deployments

---

## Section 4: Manager/Auditor (45 minutes)

### Goal: Understand compliance and risk posture

#### Step 1: Review Executive Summary (10 minutes)

```bash
# Read executive summary
cat docs/SECURITY_IMPLEMENTATION_SUMMARY.md

# Key sections:
# - Implementation Summary (what we built)
# - Compliance Achievements (frameworks we meet)
# - Risk Reduction Metrics (quantifiable improvements)
# - Business Value (competitive advantages)
```

#### Step 2: Run Self-Assessment (15 minutes)

```bash
# Open self-assessment checklist
vim docs/SECURITY_SELF_ASSESSMENT_CHECKLIST.md

# Go through each section:
# Part 1: Supply Chain Security
# Part 2: Application Security
# Part 3: Documentation & Training
# Part 4: Compliance Mapping
# Part 5: Evidence Collection

# Mark each control as:
# ✅ Implemented
# ⚠️ Partially Implemented
# ❌ Not Implemented
```

#### Step 3: Generate Compliance Report (10 minutes)

```bash
# Generate full compliance report
python3 scripts/compliance-report.py --format both

# This creates:
# 1. compliance-report-TIMESTAMP.json (detailed)
# 2. compliance-report-TIMESTAMP.md (readable)

# View the report
cat compliance-report-*.md

# Key sections:
# - Executive Summary
# - Framework Compliance Summary
# - NIST SSDF Compliance (44 practices)
# - SLSA Level 3 Compliance
# - HIPAA, SOC 2, GDPR, CISA compliance
```

#### Step 4: Understand Risk Metrics (10 minutes)

```bash
# From the compliance report, note:

# Overall Compliance: 92%
# Supply Chain Risk: -85% improvement
# Application Security Risk: -70% improvement
# Overall Risk: -87% improvement

# CVE Detection Time: 6 hours (vs 30-day industry avg)
# Mean Time to Remediation: 7 days (vs 45-day industry avg)

# These metrics show:
# - Proactive threat detection
# - Rapid response capability
# - Industry-leading security posture
```

**✅ You understand our security posture!**

Next steps:
- Present to board/executives
- Use for sales enablement
- Share with customers
- Use for audit preparation

---

## Common Tasks

### Generate SBOM

```bash
# Python dependencies
cyclonedx-py --format json --output sbom.json -r .

# Frontend dependencies
cd frontend
cyclonedx bom --output-file ../sbom-frontend.json
```

### Generate VEX

```bash
# From existing SBOM
python3 scripts/generate-vex.py \
  --sbom sbom.json \
  --output vex.json \
  --format openvex
```

### Check for CVEs

```bash
# Manual CVE check
python3 scripts/cve-monitor.py --check

# Generate report
python3 scripts/cve-monitor.py --check --output cve-report.txt
cat cve-report.txt
```

### Verify Container Image

```bash
# Verify signature
cosign verify \
  --certificate-identity "https://github.com/psychsync/psychsync/.github/workflows/signed-release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/psychsync/psychsync/backend:v1.0.0

# View SBOM
cosign sbom download ghcr.io/psychsync/psychsync/backend:v1.0.0

# View VEX
cosign attest \
  --predicate-type https://openvex.dev/ns/vex \
  ghcr.io/psychsync/psychsync/backend:v1.0.0
```

### Run Security Tests

```bash
# Integration tests
pytest tests/test_supply_chain_security.py -v

# Application security tests
pytest tests/test_security.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Create Release

```bash
# Quick release
git tag v1.0.0
git push origin main --tags

# Monitor release
gh workflow watch signed-release.yml
```

---

## Troubleshooting

### Verification Script Fails

```bash
# Problem: "File not found" errors
# Solution: Ensure you're in the project root
cd /path/to/psychsync
./scripts/verify-supply-chain-security.sh

# Problem: Permission denied
# Solution: Make scripts executable
chmod +x scripts/*.sh
```

### VEX Generation Fails

```bash
# Problem: "No module named 'packaging'"
# Solution: Install required dependencies
pip install pyotp packaging

# Problem: "Invalid SBOM format"
# Solution: Regenerate SBOM
pip install --upgrade cyclonedx-bom cyclonedx-python
cyclonedx-py --format json --output sbom.json -r .
```

### Compliance Report Fails

```bash
# Problem: "ImportError"
# Solution: Install required packages
pip install aiohttp

# Problem: "File not found"
# Solution: Ensure documentation files exist
ls docs/SECURITY_*.md
```

### Tests Fail

```bash
# Problem: "ModuleNotFoundError"
# Solution: Install test dependencies
pip install pytest pytest-cov

# Problem: Test fails but code is correct
# Solution: Update test to match current implementation
# See test file for details
```

---

## Learning Resources

### For Everyone

**Videos** (recommended):
- [SLSA Explained](https://slsa.dev/introduction/)
- [SBOM Explained](https://www.youtube.com/watch?v=7KPSJeRjJqs)
- [Supply Chain Security Best Practices](https://www.youtube.com/watch?v=I_fL6CE8jQg)

**Articles**:
- [NIST SSDF v1.1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf)
- [CISA Known Exploited Vulnerabilities](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [OpenVEX Specification](https://openvex.dev/)

### For Developers

**Tutorials**:
- `docs/SUPPLY_CHAIN_QUICK_START.md` - Daily operations
- `docs/SECURITY_QUICK_REFERENCE.md` - Quick commands

**Code Examples**:
- `scripts/generate-vex.py` - VEX generation example
- `scripts/cve-monitor.py` - CVE monitoring example
- `scripts/compliance-report.py` - Compliance reporting example

### For Security Engineers

**Deep Dives**:
- `docs/SUPPLY_CHAIN_SECURITY_V2.md` - Complete technical reference
- `COMPLETE_SECURITY_INTEGRATION_GUIDE.md` - Application security
- `docs/INCIDENT_RESPONSE_PLAYBOOKS.md` - Incident procedures

### For Managers

**Business Overview**:
- `docs/SECURITY_IMPLEMENTATION_SUMMARY.md` - Executive summary
- `docs/SECURITY_SELF_ASSESSMENT_CHECKLIST.md` - Audit preparation
- Compliance reports generated by `scripts/compliance-report.py`

---

## Support

### Questions?

**General Questions**:
- Check `docs/SECURITY_README.md` first
- Search documentation: `grep -r "keyword" docs/`
- Ask in #security Slack channel

**Security Issues**:
- Email: security@psychsync.com
- Create GitHub issue with `security` label
- For critical issues: See `docs/SECURITY_QUICK_REFERENCE.md` emergency contacts

**Technical Issues**:
- Email: devops@psychsync.com
- Create GitHub issue with `bug` label
- Check troubleshooting section in relevant documentation

---

## Quick Reference Commands

### Verification
```bash
./scripts/verify-supply-chain-security.sh
pytest tests/test_supply_chain_security.py -v
```

### Reporting
```bash
python3 scripts/compliance-report.py --format both
```

### Monitoring
```bash
gh issue list --label "cve,security"
gh run list --workflow=security-ci.yml
```

### Documentation
```bash
ls docs/
cat docs/SECURITY_README.md  # START HERE
```

---

## Your First Day Checklist

- [ ] Read `docs/SECURITY_README.md`
- [ ] Print `docs/SECURITY_QUICK_REFERENCE.md`
- [ ] Run `./scripts/verify-supply-chain-security.sh`
- [ ] Generate compliance report
- [ ] Set up security tools (if developer)
- [ ] Review incident response playbooks

---

**You're ready!** 🎉

The security implementation is comprehensive, but you don't need to learn it all at once. Start with the quick reference, and explore deeper as you go.

**Remember**: These tools and documentation are here to help you work securely and efficiently. If something seems complex, there's probably a simpler way documented in the guides!

---

**Getting Started Guide Version**: 1.0
**Last Updated**: 2024-12-25
**Maintained By**: Security Team
**Next Review**: 2025-03-25

**Need Help?** See `docs/SECURITY_QUICK_REFERENCE.md` for emergency contacts.
