# Incident Response Runbooks

**Version**: 1.0.0
**Last Updated**: 2025-12-26
**Owner**: Security Operations Team

---

## Overview

This directory contains comprehensive incident response runbooks for critical AI/ML and supply chain security incidents. Each runbook provides step-by-step procedures for detection, containment, investigation, eradication, and recovery.

## Available Runbooks

### 1. LLM Data Leakage via Prompt Injection
**File**: [LLM_DATA_LEAKAGE_IR_RUNBOOK.md](./LLM_DATA_LEAKAGE_IR_RUNBOOK.md)
**Runbook ID**: IR-LLM-001

**Covers**:
- Prompt injection attacks causing data leakage
- Immediate endpoint containment
- Session/token revocation
- Data quarantine procedures
- Forensic analysis
- AI guardrail updates

**Key Metrics**:
- Time to Containment: < 15 minutes
- Time to Revocation: < 30 minutes
- Detection Rate: 94.2%

### 2. Poisoned RAG/Fine-Tuning Corpora
**File**: [POISONED_CORPORA_IR_RUNBOOK.md](./POISONED_CORPORA_IR_RUNBOOK.md)
**Runbook ID**: IR-ML-002

**Covers**:
- Data poisoning detection
- Model and corpus quarantine
- Provenance analysis
- Poisoning technique identification
- Data cleaning procedures
- Secure model retraining
- Adversarial training

**Key Metrics**:
- Time to Quarantine: < 30 minutes
- Time to Retrain: < 72 hours
- Model Integrity: 100% restoration

### 3. Supply Chain Compromise
**File**: [SUPPLY_CHAIN_COMPROMISE_IR_RUNBOOK.md](./SUPPLY_CHAIN_COMPROMISE_IR_RUNBOOK.md)
**Runbook ID**: IR-SC-003

**Covers**:
- Dependency vulnerability analysis
- SBOM rapid impact assessment
- Credential rotation
- SLSA rebuild procedures
- Build system hardening
- Dependency governance
- Software signing implementation

**Key Metrics**:
- Time to SBOM Analysis: < 1 hour
- Time to Credential Rotation: < 2 hours
- Time to SLSA Rebuild: < 12 hours

---

## Quick Reference

### Incident Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **CRITICAL** | Active exploitation, data breach | Immediate (< 5 min) | Confirmed data leak, active malware |
| **HIGH** | Serious security control failure | < 15 minutes | Suspicious activity, potential breach |
| **MEDIUM** | Security control weakness | < 1 hour | Attempted attack, policy violation |
| **LOW** | Minor security issue | < 24 hours | False positive, policy gap |

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **Incident Commander** | [Name] | +1-XXX-XXX-XXXX | incident-commander@psychsync.com |
| **Security Lead** | [Name] | +1-XXX-XXX-XXXX | security-lead@psychsync.com |
| **ML Security Lead** | [Name] | +1-XXX-XXX-XXXX | ml-security@psychsync.com |
| **Supply Chain Lead** | [Name] | +1-XXX-XXX-XXXX | supply-chain@psychsync.com |
| **Legal Counsel** | [Name] | +1-XXX-XXX-XXXX | legal@psychsync.com |
| **PR/Media Relations** | [Name] | +1-XXX-XXX-XXXX | pr@psychsync.com |

### Regulatory Reporting Deadlines

| Regulation | Deadline | Reporting Authority |
|------------|----------|-------------------|
| **GDPR** | 72 hours | Data Protection Authority |
| **HIPAA** | 60 days | HHS OCR |
| **CCPA/CPRA** | Reasonable promptness | California Attorney General |
| **SOX** | 4 days (material events) | SEC |

### Critical Commands

```bash
# Disable service endpoints
kubectl scale deployment --all --replicas=0 -n production

# Revoke sessions
curl -X POST https://api.psychsync.com/api/v1/admin/sessions/bulk-revoke

# Analyze SBOM
python -m supply_chain.sbom_analyzer --sbom sbom/latest/cyclonedx.json

# Check for prompt injection
python -m ai.security.detect_injection --prompt-id <ID>

# Rotate credentials
python -m security.credential_rotator --rotate-all

# Verify SLSA provenance
slsa-verifier verify-image --image <IMAGE> --provenance <PROVENANCE>
```

---

## Using These Runbooks

### During an Incident

1. **Identify the incident type** → Select appropriate runbook
2. **Read the Executive Summary** → Understand key metrics
3. **Follow the phase-by-phase procedures** → Systematic response
4. **Use checklists** → Ensure nothing is missed
5. **Adapt communication templates** → Customize for your incident

### Regular Maintenance

- **Quarterly Reviews**: Update runbooks based on lessons learned
- **Tabletop Exercises**: Practice response procedures
- **Tool Validation**: Verify all commands and scripts work
- **Contact Updates**: Keep emergency contacts current

### Integration with Existing Systems

These runbooks integrate with:

- **SIEM Systems**: Automated alerting and log analysis
- **Incident Management Platforms**: Jira, ServiceNow
- **Communication Platforms**: Slack, PagerDuty
- **Documentation Systems**: Confluence, Notion
- **Monitoring Systems**: Prometheus, Grafana

---

## Incident Lifecycle

### Phase 1: Detection & Identification (0-30 minutes)
- Alert validation
- Severity classification
- Team activation

### Phase 2: Immediate Containment (30-120 minutes)
- Isolate affected systems
- Prevent spread
- Preserve evidence

### Phase 3: Investigation & Analysis (1-24 hours)
- Determine root cause
- Assess impact
- Identify attackers (if applicable)

### Phase 4: Eradication & Recovery (4-72 hours)
- Remove threats
- Restore systems
- Verify security

### Phase 5: Post-Incident Activities (7-30 days)
- Lessons learned
- Security improvements
- Documentation updates

---

## Training and Exercises

### Recommended Training Frequency

- **New Team Members**: Immediate orientation
- **All Staff**: Quarterly refreshers
- **Incident Response Team**: Monthly drills
- **Tabletop Exercises**: Bi-annual
- **Live Simulations**: Annual

### Exercise Scenarios

1. **Prompt Injection Attack**
   - Malicious user attempts jailbreak
   - Data leakage occurs
   - Practice containment and notification

2. **Data Poisoning Discovery**
   - Model performance degrades
   - Suspicious outputs detected
   - Practice quarantine and retraining

3. **Dependency Vulnerability**
   - Critical CVE announced
   - Multiple systems affected
   - Practice SBOM analysis and patching

---

## Metrics and Reporting

### Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| **MTTD** (Mean Time to Detect) | < 15 minutes | Time from incident to detection |
| **MTTR** (Mean Time to Resolve) | < 4 hours | Time from detection to resolution |
| **Containment Time** | < 30 minutes | Time to isolate incident |
| **False Positive Rate** | < 5% | Alerts that aren't real incidents |

### Post-Incident Review Template

```markdown
# Post-Incident Review: [INCIDENT_ID]

## Executive Summary
[High-level overview]

## Timeline
[Detailed incident timeline]

## Root Cause Analysis
[What happened and why]

## Impact Assessment
[Business, technical, compliance impact]

## Lessons Learned
[What went well, what didn't]

## Action Items
[Specific improvements with owners and due dates]

## Appendix
[Logs, screenshots, supporting data]
```

---

## Related Documentation

- **Security Policies**: `../SECURITY_POLICY.md`
- **AI Security Guidelines**: `../AI_SECURITY_GUIDE.md`
- **Supply Chain Security**: `../SUPPLY_CHAIN_QUICK_START.md`
- **SLSA Verification Guide**: `../SLSA_VERIFICATION_GUIDE.md`
- **Testing Guidelines**: `../TESTING.md`

---

## Contributing

To suggest improvements or report issues:

1. Create a new branch: `git checkout -b runbook-improvement`
2. Make your changes
3. Submit a pull request to `security/incidents`
4. Include testing results if applicable

All runbook changes must be reviewed by:
- Security Operations Team
- Legal Counsel
- Affected Engineering Teams

---

**Document Control**:
- **Owner**: Security Operations Team
- **Review Frequency**: Monthly
- **Last Review**: 2025-12-26
- **Next Review**: 2026-01-26
- **Approved By**: [Chief Information Security Officer]

---

## Changelog

### Version 1.0.0 (2025-12-26)
- Initial release of IR runbooks
- LLM Data Leakage runbook
- Poisoned Corpora runbook
- Supply Chain Compromise runbook
