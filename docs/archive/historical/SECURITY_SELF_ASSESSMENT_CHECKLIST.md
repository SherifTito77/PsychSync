# PsychSync Security Self-Assessment Checklist

## Purpose

This checklist is used to verify security controls are properly implemented and maintained. Use for:
- Internal security assessments
- Pre-audit preparation
- Quarterly security reviews
- Post-implementation verification

**Assessment Frequency**: Quarterly (or after major changes)

---

## Instructions

1. **Review each control** in the checklist
2. **Gather evidence** for each item
3. **Mark status**: ✅ Implemented | ⚠️ Partially Implemented | ❌ Not Implemented
4. **Document gaps** and remediation plans
5. **Sign off** with assessor name and date

---

## Part 1: Supply Chain Security (v2.0)

### 1.1 SBOM Generation

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| SBOM generated on every build | ☐ | Link to workflow run | |
| CycloneDX format used | ☐ | SBOM file example | |
| SBOM includes all dependencies | ☐ | Component count | |
| SBOM version 1.5 | ☐ | Format verification | |
| SBOM attached to releases | ☐ | Release link | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] SBOM JSON file from latest release
- [ ] CI/CD workflow run showing SBOM generation
- [ ] SBOM validation report

---

### 1.2 VEX Analysis

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| VEX generated with SBOM | ☐ | VEX file example | |
| OpenVEX format used | ☐ | Format verification | |
| Context-aware analysis performed | ☐ | VEX statements | |
| False positive rate tracked | ☐ | Metrics dashboard | |
| VEX attached to releases | ☐ | Release link | |
| VEX attached to container images | ☐ | cosign attest output | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] VEX JSON file from latest release
- [ ] VEX showing "not_affected" justifications
- [ ] False positive rate metrics

---

### 1.3 CVE Monitoring

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Automated CVE scanning enabled | ☐ | Workflow runs | |
| Multiple data sources used | ☐ | NVD, OSV, CISA KEV | |
| Monitoring frequency: every 6 hours | ☐ | Schedule config | |
| Automated alerting configured | ☐ | GitHub issues/Slack | |
| Vendor SLA tracking enabled | ☐ | SLA metrics | |
| CVE history maintained (90 days) | ☐ | History file | |
| Mean Time to Detection (MTTD) measured | ☐ | MTTD metric | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] CVE monitoring workflow runs
- [ ] Example GitHub issue created for CVE
- [ ] CVE metrics from `.github/cve-metrics.json`

---

### 1.4 Signed Releases

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| SLSA Level 3 provenance generated | ☐ | Provenance file | |
| All source artifacts signed | ☐ | Signature files | |
| Container images signed | ☐ | cosign verify output | |
| SBOM signed and attached | ☐ | Attached SBOM | |
| VEX signed and attached | ☐ | Attached VEX | |
| Signatures stored in Rekor | ☐ | Rekor entry | |
| Signature verification documented | ☐ | Verification guide | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] SLSA provenance JSON file
- [ ] Signature verification output
- [ ] Rekor transparency log entry

---

### 1.5 Build Infrastructure

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Ephemeral runners configured | ☐ | Runner config | |
| Auto-scaling enabled (0-10 runners) | ☐ | Scaling config | |
| Idle timeout configured (≤5 min) | ☐ | Timeout setting | |
| No persistent storage | ☐ | Storage config | |
| Network isolation implemented | ☐ | VPC/subnet config | |
| OIDC-only authentication | ☐ | No long-lived tokens | |
| Runner compliance verified | ☐ | Verification script | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] Runner configuration file
- [ ] Kubernetes deployment manifest (if applicable)
- [ ] Runner compliance check output

---

### 1.6 Registry Policies

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Allowed registries defined | ☐ | Policy file | |
| Blocked registries defined | ☐ | Policy file | |
| Image allow-list maintained | ☐ | Allow-list file | |
| Image block-list maintained | ☐ | Block-list file | |
| Policy enforcement in CI/CD | ☐ | Workflow config | |
| Registry check script executable | ☐ | Script permissions | |
| Violations blocked | ☐ | Build failure logs | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] Registry policy YAML file
- [ ] Example policy violation and block
- [ ] Registry check script output

---

### 1.7 Package Verification

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Sigstore integration enabled | ☐ | Workflow config | |
| Critical packages verified | ☐ | Verification logs | |
| Suspicious package detection | ☐ | Detection logs | |
| Typosquatting detection | ☐ | Detection logic | |
| Signature verification in CI/CD | ☐ | Workflow run | |
| Verification failures block builds | ☐ | Build logs | |

**Assessment**: ___________________________________________________________________

**Evidence Required**:
- [ ] Package signature verification workflow run
- [ ] Example signature verification output
- [ ] Blocked package example (if any)

---

## Part 2: Application Security (v1.0)

### 2.1 Authentication

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| MFA implemented (TOTP) | ☐ | Code location | |
| Backup codes supported | ☐ | Code location | |
| Password hashing (bcrypt) | ☐ | Hash cost ≥ 12 | |
| Password complexity enforced | ☐ | Validation rules | |
| Account lockout configured | ☐ | Lockout threshold | |
| Session timeout configured | ☐ | Timeout value | |

**Assessment**: ___________________________________________________________________

---

### 2.2 Authorization

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| RBAC implemented | ☐ | Roles defined | |
| 47 granular permissions | ☐ | Permission list | |
| ABAC implemented | ☐ | Policies defined | |
| Layered authorization (RBAC + ABAC) | ☐ | Integration code | |
| Authorization enforced on all endpoints | ☐ | Decorator usage | |
| Regular authorization audits | ☐ | Audit logs | |

**Assessment**: ___________________________________________________________________

---

### 2.3 Data Protection

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Field-level encryption | ☐ | Encrypted fields | |
| 5 sensitivity levels defined | ☐ | Sensitivity list | |
| Encryption at rest (AES-256) | ☐ | Encryption config | |
| Encryption in transit (TLS 1.2+) | ☐ | TLS configuration | |
| Key management process | ☐ | Key rotation | |
| Encrypted fields audit logged | ☐ | Access logs | |

**Assessment**: ___________________________________________________________________

---

### 2.4 Multi-Tenancy

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Row-level security implemented | ☐ | RLS service | |
| Organization-level isolation | ☐ | Filter logic | |
| Team-level isolation | ☐ | Filter logic | |
| Cross-tenant access blocked | ☐ | Blocking logic | |
| Cross-tenant attempts logged | ☐ | Audit logs | |
| Tenant isolation verified | ☐ | Test results | |

**Assessment**: ___________________________________________________________________

---

### 2.5 Session Management

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Session rotation (15 min) | ☐ | Rotation config | |
| Device fingerprinting | ☐ | Fingerprint logic | |
| Concurrent session limit (5) | ☐ | Limit enforcement | |
| IP change detection | ☐ | Detection logs | |
| Suspicious activity detection | ☐ | Detection logic | |
| Secure session termination | ☐ | Logout logic | |

**Assessment**: ___________________________________________________________________

---

### 2.6 Audit Logging

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| 20+ event types logged | ☐ | Event type list | |
| Authentication events logged | ☐ | Log examples | |
| Authorization events logged | ☐ | Log examples | |
| Data access logged (encrypted fields) | ☐ | Access logs | |
| Cross-tenant attempts logged | ☐ | Attempt logs | |
| Log retention (90 days) | ☐ | Retention config | |
| Log export capability | ☐ | Export function | |

**Assessment**: ___________________________________________________________________

---

## Part 3: Documentation & Training

### 3.1 Documentation

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Supply chain security guide | ☐ | Document location | |
| Quick start guide | ☐ | Document location | |
| Security integration guide | ☐ | Document location | |
| Executive summary | ☐ | Document location | |
| Runbooks for incident response | ☐ | Runbook location | |
| Architecture diagrams | ☐ | Diagram location | |

**Assessment**: ___________________________________________________________________

---

### 3.2 Training

| Control | Status | Evidence | Notes |
|---------|--------|----------|-------|
| Developer security training | ☐ | Training records | |
- Supply chain security covered | ☐ | Completion % |
- Application security covered | ☐ | Completion % |
| Security team training | ☐ | Training records | |
- Incident response training | ☐ | Drill records | |
- Training effectiveness measured | ☐ | Assessment results | |

**Assessment**: ___________________________________________________________________

---

## Part 4: Compliance Mapping

### 4.1 NIST SSDF v1.1

| Practice | Status | Evidence | Notes |
|----------|--------|----------|-------|
| PO.1.1: Security objectives | ☐ | | |
| PO.2.1: Leadership | ☐ | | |
| PO.3.1: Threat modeling | ☐ | | |
| PO.4.1: Risk assessment | ☐ | | |
| PO.5.1: Policy | ☐ | | |
| PO.6.1: Staff training | ☐ | | |
| PO.7.1: Tools selection | ☐ | | |
| PO.8.1: Work products | ☐ | | |
| PO.9.1: Metrics | ☐ | | |
| PO.10.1: Package selection | ☐ | | |
| PO.11.1: Architecture review | ☐ | | |
| PS.1.1: Build environment | ☐ | | |
| PS.2.1: Build provenance | ☐ | | |
| PS.3.1: Build infrastructure | ☐ | | |
| PS.4.1: Access controls | ☐ | | |
| PS.5.1: Change management | ☐ | | |
| PS.6.1: Configuration mgmt | ☐ | | |
| PS.7.1: Secrets management | ☐ | | |
| PS.8.1: Supply chain protection | ☐ | | |
| PW.1.1: Vulnerability scanning | ☐ | | |
| PW.2.1: Vulnerability response | ☐ | | |
| PW.3.1: Vulnerability monitoring | ☐ | | |
| PW.4.1: Vulnerability coordination | ☐ | | |
| PW.5.1: Penetration testing | ☐ | | |
| PW.6.1: Log analysis | ☐ | | |
| PW.7.1: Incident response | ☐ | | |
| PW.8.1: Recovery procedures | ☐ | | |
| RV.1.1: Reviews | ☐ | | |
| RV.2.1: Testing | ☐ | | |
| RV.3.1: Logging | ☐ | | |
| RV.4.1: Audits | ☐ | | |

**Total Compliance**: _____ / 44 practices (_____%)

**Assessment**: ___________________________________________________________________

---

### 4.2 SLSA Level 3

| Requirement | Status | Evidence | Notes |
|-------------|--------|----------|-------|
| Source tracking | ☐ | Git history | |
| Build artifact tracking | ☐ | Signed artifacts | |
| Build provenance | ☐ | SLSA provenance | |
| Isolated build | ☐ | Ephemeral runners | |
| Hermetic build | ☐ | No network deps | |
| Reproducible build | ☐ | Pinned versions | |

**SLSA Level**: _____

**Assessment**: ___________________________________________________________________

---

## Part 5: Evidence Collection

### Evidence Checklist

Attach/Link the following evidence:

#### Supply Chain Security
- [ ] Latest SBOM (CycloneDX JSON)
- [ ] Latest VEX (OpenVEX JSON)
- [ ] CVE monitoring workflow run
- [ ] SLSA provenance file
- [ ] Container image signature verification
- [ ] Registry policy file
- [ ] Ephemeral runner configuration
- [ ] Package signature verification logs

#### Application Security
- [ ] MFA implementation code
- [ ] RBAC/ABAC configuration
- [ ] Field encryption implementation
- [ ] Row-level security implementation
- [ ] Session rotation configuration
- [ ] Sample audit logs

#### Documentation
- [ ] Security architecture diagram
- [ ] Threat model documentation
- [ ] Incident response playbooks
- [ ] Security training materials
- [ ] Compliance matrices

---

## Part 6: Assessment Results

### Summary

| Category | Controls | Implemented | Partial | Not Implemented | % Complete |
|----------|----------|--------------|---------|-----------------|------------|
| Supply Chain | 7 | ___ | ___ | ___ | ___% |
| Application | 6 | ___ | ___ | ___ | ___% |
| Documentation | 2 | ___ | ___ | ___ | ___% |
| Training | 2 | ___ | ___ | ___ | ___% |
| NIST SSDF | 44 | ___ | ___ | ___ | ___% |
| SLSA | 6 | ___ | ___ | ___ | ___% |
| **TOTAL** | **67** | ___ | ___ | ___ | ___% |

### Overall Risk Assessment

**Supply Chain Risk**: ☐ Low ☐ Medium ☐ High

**Application Security Risk**: ☐ Low ☐ Medium ☐ High

**Overall Risk**: ☐ Low ☐ Medium ☐ High

### Findings and Recommendations

**Critical Findings** (require immediate action):
1. ___________________________________________________________________
2. ___________________________________________________________________

**High-Priority Findings** (address within 30 days):
1. ___________________________________________________________________
2. ___________________________________________________________________

**Medium-Priority Findings** (address within 90 days):
1. ___________________________________________________________________
2. ___________________________________________________________________

**Low-Priority Findings** (address next planning cycle):
1. ___________________________________________________________________
2. ___________________________________________________________________

---

## Part 7: Sign-Off

### Assessment Completed By

**Assessor Name**: _________________________

**Title**: _________________________

**Date**: _________________________

**Assessor Signature**: _________________________

### Review and Approval

**Security Lead**: _________________________ **Date**: _______ **Signature**: _______

**CTO/VP Engineering**: _________________________ **Date**: _______ **Signature**: _______

### Next Assessment Date

**Scheduled For**: _________________________

---

## Appendix A: Quick Reference

### How to Use This Checklist

1. **Pre-Assessment Preparation** (1 week before)
   - Review all documentation
   - Run verification scripts
   - Gather evidence files
   - Schedule stakeholder interviews

2. **Assessment Execution** (1-2 days)
   - Walk through each control
   - Document evidence locations
   - Mark implementation status
   - Note any gaps or issues

3. **Post-Assessment** (1 week after)
   - Compile findings report
   - Create remediation plans
   - Present to leadership
   - Schedule follow-up actions

### Verification Commands

```bash
# Verify supply chain security
./scripts/verify-supply-chain-security.sh

# Verify application security
pytest tests/test_security.py -v

# Generate compliance report
python3 scripts/compliance-report.py

# Check CVE monitoring status
cat .github/cve-metrics.json
```

---

**Checklist Version**: 1.0
**Last Updated**: 2024-12-25
**Next Review**: 2025-03-25
**Maintained By**: Security Team
