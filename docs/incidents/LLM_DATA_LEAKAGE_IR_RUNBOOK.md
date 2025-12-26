# Incident Response Runbook: LLM Data Leakage via Prompt Injection

**Runbook ID**: IR-LLM-001
**Version**: 1.0.0
**Last Updated**: 2025-12-26
**Owner**: Security Operations Team
**Classification**: CRITICAL

---

## Executive Summary

This runbook provides step-by-step procedures for responding to confirmed or suspected data leakage via Large Language Model (LLM) prompt injection attacks. Prompt injection can cause LLMs to leak sensitive information, bypass security controls, or execute unauthorized actions.

**Key Success Metrics**:
- **Time to Containment**: < 15 minutes
- **Time to Revocation**: < 30 minutes
- **Time to Audit Completion**: < 24 hours
- **Data Exposure Minimization**: < 1% of total sensitive data

---

## Table of Contents

1. [Detection & Identification](#detection--identification)
2. [Immediate Containment](#immediate-containment)
3. [Investigation & Analysis](#investigation--analysis)
4. [Eradication & Recovery](#eradication--recovery)
5. [Post-Incident Activities](#post-incident-activities)
6. [Communications Plan](#communications-plan)
7. [Checklist & Quick Reference](#checklist--quick-reference)

---

## Detection & Identification

### Alert Triggers

Automated monitoring systems may detect prompt injection via:

1. **Spotlighting SDK Alerts**
   - Delimiter detection in user inputs
   - Encoding pattern matches
   - Datamarker anomalies

2. **Behavioral Anomalies**
   - Unusual output patterns (suspiciously specific data)
   - Unexpected PII in responses
   - Out-of-context information

3. **User Reports**
   - Data leakage reports from users
   - Unexpected LLM responses
   - System behaving unusually

4. **Automated Scanning**
   - Regular prompt injection testing
   - Output sanitization failures
   - AI security monitoring alerts

### Initial Validation

**Step 1**: Verify alert legitimacy (5 minutes)

```bash
# Check if this is a false positive
# Review the flagged prompt/output pair
python -m ai.security.prompt_injection_validator \
  --prompt-id <ALERT_ID> \
  --output-id <OUTPUT_ID> \
  --validate
```

**Step 2**: Classify severity

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| **CRITICAL** | Confirmed PII leak, credentials, secrets | Immediate (< 5 min) |
| **HIGH** | Suspicious pattern, potential leak | < 15 minutes |
| **MEDIUM** | Attempted injection, no leak confirmed | < 1 hour |
| **LOW** | False positive or testing | < 24 hours |

**Step 3**: Activate Incident Response Team

```bash
# Page the on-call IR team
# Severity: CRITICAL/HIGH → Immediate page
# Severity: MEDIUM/LOW → Next business day

python -m incident_response.activate \
  --runbook IR-LLM-001 \
  --severity <SEVERITY> \
  --alert-id <ALERT_ID>
```

---

## Immediate Containment

### Phase 1: Stop the Leak (0-15 minutes)

#### Action 1.1: Disable Affected LLM Endpoints

**Priority**: CRITICAL
**Timeline**: < 5 minutes

```bash
# 1. Identify affected endpoints
GET /api/v1/ai/prompts/<PROMPT_ID>/details

# 2. Disable endpoint (maintenance mode)
curl -X POST https://api.psychsync.com/api/v1/admin/ai/endpoints/<ENDPOINT_ID>/disable \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "X-Reason: Prompt-Injection-Incident"

# 3. Verify endpoint is disabled
curl https://api.psychsync.com/api/v1/ai/endpoints/<ENDPOINT_ID>/status
# Expected: {"status": "maintenance", "reason": "Prompt-Injection-Incident"}
```

#### Action 1.2: Revoke Exposed Sessions/Tokens

**Priority**: CRITICAL
**Timeline**: < 10 minutes

```bash
# 1. Get list of sessions that accessed the LLM during the attack window
python -m incident_response.get_exposed_sessions \
  --start-time <ATTACK_START> \
  --end-time <ATTACK_END> \
  --endpoint-id <ENDPOINT_ID>

# 2. Revoke all exposed sessions
curl -X POST https://api.psychsync.com/api/v1/admin/sessions/bulk-revoke \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_ids": [<SESSION_IDS>], "reason": "prompt-injection-incident"}'

# 3. Invalidate all JWT tokens issued during window
python -m app.core.security.token_manager \
  --action invalidate-tokens \
  --window-start <ATTACK_START> \
  --window-end <ATTACK_END>

# 4. Force password reset for affected users
curl -X POST https://api.psychsync.com/api/v1/admin/users/bulk-password-reset \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [<USER_IDS>], "reason": "security-incident"}'
```

#### Action 1.3: Quarantine Affected Data

**Priority**: HIGH
**Timeline**: < 15 minutes

```bash
# 1. Identify data potentially exposed
python -m incident_response.analyze_exposure \
  --prompt-id <PROMPT_ID> \
  --output-id <OUTPUT_ID> \
  --export-exposed-data

# 2. Move to quarantine storage
aws s3 cp s3://psychsync-production/llm-outputs/<OUTPUT_ID> \
  s3://psychsync-quarantine/incident-<INCIDENT_ID>/ \
  --storage-class GLACIER

# 3. Mark records in database
UPDATE llm_outputs
SET status = 'quarantined',
    incident_id = '<INCIDENT_ID>',
    quarantine_reason = 'prompt-injection-data-leak'
WHERE output_id = '<OUTPUT_ID>';

# 4. Create access log
INSERT INTO data_quarantine_log (
  incident_id,
  data_type,
  record_count,
  quarantined_by,
  quarantine_time,
  retention_period
) VALUES (
  '<INCIDENT_ID>',
  'llm_outputs',
  <COUNT>,
  CURRENT_USER,
  NOW(),
  '7 years'
);
```

### Phase 2: Prevent Spread (15-30 minutes)

#### Action 2.1: Update Spotlighting Patterns

**Priority**: HIGH
**Timeline**: < 20 minutes

```python
# 1. Extract the attack pattern from the prompt
from ai.security.spotlighting import extract_attack_pattern

attack_pattern = extract_attack_pattern(
    prompt_text=<MALICIOUS_PROMPT>,
    output_text=<LEAKED_OUTPUT>
)

# 2. Add to detection rules
from ai.security.prompt_injection_detector import update_detection_rules

update_detection_rules(
    new_patterns=[attack_pattern],
    priority='CRITICAL',
    enabled_immediately=True
)

# 3. Deploy to all regions
python -m ai.security.deploy_rules \
  --pattern-id <NEW_PATTERN_ID> \
  --regions all
```

#### Action 2.2: Enable Enhanced Monitoring

**Priority**: HIGH
**Timeline**: < 25 minutes

```bash
# 1. Increase logging verbosity for AI endpoints
kubectl set env deployment/ai-api LOG_LEVEL=DEBUG -n production

# 2. Enable real-time monitoring
curl -X POST https://api.psychsync.com/api/v1/admin/monitoring/enable \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "ai-api",
    "metrics": ["prompt_injection_attempts", "data_leakage_events"],
    "realtime_alerts": true,
    "alert_channels": ["security-slack", "on-call-pager"]
  }'

# 3. Set up SIEM alerts
python -m app.core.siem_integration \
  --action create-alert \
  --rule-name "Prompt-Injection-Detection" \
  --condition "prompt_injection_score > 0.7" \
  --actions ["page-on-call", "disable-endpoint"]
```

---

## Investigation & Analysis

### Phase 3: Determine Scope (30 min - 4 hours)

#### Action 3.1: Analyze the Attack Vector

**Priority**: HIGH
**Timeline**: < 2 hours

```python
from ai.security.forensics import PromptInjectionAnalyzer

analyzer = PromptInjectionAnalyzer()

# 1. Reconstruct the attack chain
attack_chain = analyzer.reconstruct_attack(
    prompt_id=<PROMPT_ID>,
    user_id=<USER_ID>,
    session_id=<SESSION_ID>
)

# 2. Identify attack technique
attack_technique = analyzer.classify_attack(attack_chain)
# Examples: "jailbreak", "danz-level-injection", "context-overflow"

# 3. Assess success metrics
metrics = analyzer.calculate_impact(
    attack_chain=attack_chain,
    exposed_data=<EXPOSED_DATA>,
    affected_users=<USER_COUNT>
)

# 4. Generate forensic report
report = analyzer.generate_report(
    attack_chain=attack_chain,
    metrics=metrics,
    incident_id=<INCIDENT_ID>
)

report.save("s3://psychsync-security/incidents/<INCIDENT_ID>/forensic-report.json")
```

#### Action 3.2: Map Data Exposure

**Priority**: CRITICAL
**Timeline**: < 4 hours

```python
from app.services.data_exposure_mapper import DataExposureMapper

mapper = DataExposureMapper()

# 1. Scan all outputs for leaked data patterns
exposure_scan = mapper.scan_outputs(
    start_time=<ATTACK_START>,
    end_time=<ATTACK_END>,
    user_id=<ATTACKER_ID>,
    data_types=['PII', 'credentials', 'secrets', 'medical_records']
)

# 2. Identify affected data subjects
affected_subjects = mapper.identify_data_subjects(
    exposure_scan=exposure_scan
)

# 3. Classify exposure by sensitivity
exposure_classification = mapper.classify_exposure(
    scan_results=exposure_scan,
    affected_subjects=affected_subjects
)

# Classification matrix:
# - CRITICAL: SSN, financial account numbers, medical diagnoses
# - HIGH: Names, addresses, phone numbers, email addresses
# - MEDIUM: Demographics, preferences, non-sensitive health data
# - LOW: Aggregated/anonymized data

# 4. Generate GDPR/HIPAA breach notification list
breach_list = mapper.generate_breach_notification_list(
    classification=exposure_classification,
    regulations=['GDPR', 'HIPAA', 'CCPA']
)
```

#### Action 3.3: Audit Trail Analysis

**Priority**: HIGH
**Timeline**: < 4 hours

```bash
# 1. Extract complete audit trail for the attacker
python -m app.core.audit.extract_user_trail \
  --user-id <ATTACKER_ID> \
  --start-time <WINDOW_START> \
  --end-time <WINDOW_END> \
  --output audit_trail.json

# 2. Identify all accessed prompts
jq '.prompts[] | select(.timestamp >= "<WINDOW_START>" and .timestamp <= "<WINDOW_END>")' \
  audit_trail.json > accessed_prompts.json

# 3. Cross-reference with known attack patterns
python -m app.core.security.pattern_matcher \
  --input accessed_prompts.json \
  --pattern-library known_prompt_injections.json

# 4. Check for data exfiltration indicators
# - Large output sizes
# - Base64-encoded content
# - Unusual request frequencies
# - Suspicious user agents/IPs
python -m app.core.security.exfiltration_detector \
  --user-id <ATTACKER_ID> \
  --time-window <ATTACK_WINDOW>
```

---

## Eradication & Recovery

### Phase 4: Clean and Restore (4-24 hours)

#### Action 4.1: Sanitize Contaminated Data

**Priority**: HIGH
**Timeline**: < 8 hours

```python
from app.services.data_sanitizer import DataSanitizer

sanitizer = DataSanitizer()

# 1. Identify all outputs that may contain leaked data
contaminated_outputs = sanitizer.find_contaminated_outputs(
    incident_id=<INCIDENT_ID>,
    prompt_pattern=<ATTACK_PATTERN>
)

# 2. Apply PII redaction to quarantined outputs
sanitized = sanitizer.batch_redact(
    outputs=contaminated_outputs,
    redaction_level='AGGRESSIVE',  # Maximum redaction
    preserve_structure=True
)

# 3. Verify no residual PII
verification = sanitizer.verify_sanitization(
    sanitized_data=sanitized,
    original_data=contaminated_outputs
)

# 4. Re-index clean data (if needed)
if verification.passed:
    sanitizer.reindex_data(sanitized)
```

#### Action 4.2: Update AI Guardrails

**Priority**: CRITICAL
**Timeline**: < 12 hours

```python
# 1. Update Context Assembly rules
from ai.services.context_assembly import ContextAssemblyService

cas = ContextAssemblyService()

# Add stricter data minimization
cas.update_rules(
    rules={
        'data_minimization': 'AGGRESSIVE',
        'pii_detection': 'STRICT',
        'redaction_level': 'AGGRESSIVE',
        'max_context_size': 5000,  # Reduced from 10000
        'allow_list_fields': ['user_id', 'timestamp']  # Minimal fields
    }
)

# 2. Update Spotlighting patterns
from ai.security.spotlighting_sdk import SpotlightingPatterns

patterns = SpotlightingPatterns()

# Add new attack pattern to all modes
patterns.add_pattern(
    mode='DELIMITING',
    pattern=<EXTRACTED_ATTACK_PATTERN>,
    priority='CRITICAL',
    action='BLOCK'
)

patterns.add_pattern(
    mode='ENCODING',
    pattern=<ENCODED_VARIANT>,
    priority='CRITICAL',
    action='BLOCK'
)

# 3. Deploy updated guardrails
python -m ai.security.deploy_guardrails \
  --environment production \
  --skip-validation false
```

#### Action 4.3: Restore Services

**Priority**: HIGH
**Timeline**: < 24 hours

```bash
# 1. Gradually restore AI endpoints (canary deployment)
kubectl patch deployment ai-api -n production \
  -p '{"spec":{"replicas":1}}'

# 2. Monitor for 1 hour
python -m monitoring.watch_endpoint \
  --endpoint ai-api \
  --duration 3600 \
  --alert-threshold 0.05

# 3. If no issues, scale to full capacity
kubectl scale deployment ai-api --replicas=3 -n production

# 4. Verify all security controls are active
python -m app.core.security.verify_controls \
  --service ai-api \
  --controls ['spotlighting', 'context_assembly', 'uncertainty_detection']

# 5. Run synthetic tests
python -m tests.security.prompt_injection_tests \
  --endpoint production \
  --test-set comprehensive
```

---

## Post-Incident Activities

### Phase 5: Learn and Improve (1-7 days)

#### Action 5.1: Post-Mortem Analysis

**Priority**: MEDIUM
**Timeline**: < 3 days

```markdown
# Incident Post-Mortem Template

## Executive Summary
- **Incident ID**: INC-YYYY-001
- **Date**: [DATE]
- **Duration**: [X hours]
- **Severity**: [CRITICAL/HIGH/MEDIUM/LOW]
- **Impact**: [Affected users, data exposed]

## Timeline
| Time | Event | Owner |
|------|-------|-------|
| 00:00 | Initial detection | Automated Monitor |
| 00:05 | IR team paged | On-Call Engineer |
| 00:10 | Endpoint disabled | IR Lead |
| 00:30 | Sessions revoked | Security Team |
| ... | ... | ... |

## Root Cause Analysis
- **Attack Vector**: [Specific technique used]
- **Vulnerability**: [What allowed it to succeed]
- **Failure Points**: [Where defenses failed]

## Impact Assessment
- **Data Exposed**: [Types and counts]
- **Users Affected**: [Number and demographics]
- **Regulatory Impact**: [GDPR, HIPAA, etc.]
- **Financial Impact**: [Estimated costs]

## Lessons Learned
- **What Went Well**: [Positive aspects]
- **What Went Poorly**: [Areas for improvement]
- **Action Items**: [Specific improvements]
```

#### Action 5.2: Security Improvements

**Priority**: HIGH
**Timeline**: < 7 days

```python
# 1. Enhance prompt injection detection
from ai.security.prompt_injection_detector import EnhancedDetector

detector = EnhancedDetector()

# Add machine learning-based detection
detector.enable_ml_classifier(
    model_path='models/prompt_injection_classifier_v2.pkl',
    threshold=0.85,
    fallback_to_rules=True
)

# 2. Implement rate limiting per user
from app.core.security.rate_limiter import RateLimiter

limiter = RateLimiter()

limiter.set_limit(
    user_id=<USER_ID>,
    endpoint='/api/v1/ai/generate',
    requests_per_minute=10,
    burst_size=20
)

# 3. Add output scanning for data leakage
from ai.security.output_scanner import OutputScanner

scanner = OutputScanner()

scanner.enable_realtime_scanning(
    patterns=['PII', 'credentials', 'secrets'],
    action='BLOCK',
    quarantine=True
)

# 4. Implement uncertainty checks for all outputs
from ai.security.uncertainty_detection import UncertaintyGuard

guard = UncertaintyGuard()

# Add to all AI endpoints
@guard.protect(task_category=TaskCategory.GENERAL_ASSISTANCE)
def generate_response(prompt):
    return llm.generate(prompt)
```

#### Action 5.3: Documentation Updates

**Priority**: MEDIUM
**Timeline**: < 7 days

```bash
# 1. Update runbook with lessons learned
# Edit this file: docs/incidents/LLM_DATA_LEAKAGE_IR_RUNBOOK.md

# 2. Add attack pattern to knowledge base
python -m knowledge_base.add_attack_pattern \
  --pattern-id <PATTERN_ID> \
  --name <ATTACK_NAME> \
  --description <DESCRIPTION> \
  --mitigation <MITIGATION_STEPS>

# 3. Create training materials
python -m training.create_materials \
  --topic "Prompt Injection Response" \
  --audience "Security Team" \
  --include-incident <INCIDENT_ID>
```

---

## Communications Plan

### Internal Communications

#### Severity: CRITICAL

**Immediate (0-30 minutes)**:
```
TO: Executive Team, Engineering, Security
SUBJECT: 🔴 CRITICAL: Active Prompt Injection Incident - Data Leakage

EXECUTIVE SUMMARY:
- Incident ID: INC-2025-<ID>
- Severity: CRITICAL
- Status: CONTAINMENT IN PROGRESS
- Endpoint: <AFFECTED_ENDPOINT>
- Impact: <PRELIMINARY_ASSESSMENT>

ACTIONS TAKEN:
✅ Affected endpoints disabled
✅ Sessions being revoked
✅ Data quarantined

NEXT STEPS:
- Investigation ongoing
- ETA for service restoration: TBD

Please stand by for further updates.
```

**Update (1-2 hours)**:
```
TO: Executive Team, Engineering, Security
SUBJECT: 🔴 UPDATE: Prompt Injection Incident - Investigation Update

STATUS UPDATE:
- Incident ID: INC-2025-<ID>
- Phase: INVESTIGATION
- Containment: COMPLETE
- Impact Assessment: IN PROGRESS

PRELIMINARY FINDINGS:
- Attack technique: <TECHNIQUE>
- Data potentially exposed: <TYPES>
- Users affected: <COUNT>

ACTIONS IN PROGRESS:
- Mapping data exposure
- Identifying affected users
- Preparing notifications

NEXT UPDATE: <TIME>
```

**Resolution (24-48 hours)**:
```
TO: All Staff
SUBJECT: ✅ RESOLVED: Prompt Injection Incident

INCIDENT SUMMARY:
- Incident ID: INC-2025-<ID>
- Duration: <X> hours
- Status: RESOLVED

ROOT CAUSE:
<Summary of what happened and why>

ACTIONS TAKEN:
✅ Vulnerability patched
✅ Enhanced monitoring deployed
✅ All security controls restored
✅ Affected users notified

LESSONS LEARNED:
<Key improvements being implemented>

QUESTIONS: Contact <INCIDENT_COMMANDER>
```

### External Communications

#### Regulatory Notification (GDPR/HIPAA)

**Template**:

```markdown
# Data Breach Notification Letter

[Date]

Dear [Data Subject Name],

We are writing to inform you of a data privacy incident that may have involved your personal information.

## What Happened

On [Date], we detected suspicious activity affecting our AI-powered [Service Name]. Through our investigation, we discovered that an unauthorized party had used a technique known as "prompt injection" to potentially access certain information through our system.

## What Information Was Involved

The potentially affected information includes:
[List specific data types - e.g., name, email address, etc.]

## What We Are Doing

We have taken the following actions:
- Immediately disabled the affected system
- Engaged leading cybersecurity experts to investigate
- Enhanced our security controls to prevent similar incidents
- Notified appropriate regulatory authorities

## What You Can Do

We recommend that you:
[Specific actions based on data types exposed]

- Monitor your accounts for suspicious activity
- Be cautious of phishing attempts
- [Other relevant recommendations]

## Contact Us

If you have questions, please contact:
- Phone: [Number]
- Email: [Address]
- Website: [URL]

We sincerely apologize for any concern or inconvenience this incident may cause you.

Sincerely,

[Executive Name]
[Title]
[Company Name]
```

#### Customer Communication (If B2B)

```markdown
# Security Incident Notification - [Customer Name]

Dear [Customer Point of Contact],

We are notifying you of a security incident that may have affected data associated with your organization's account.

## Incident Summary

- **Incident Date**: [Date]
- **Incident Type**: Prompt Injection Attack
- **Potentially Affected Data**: [Data types]
- **Accounts Affected**: [Number]

## Our Response

We have:
1. Contained the incident within [X] minutes
2. Engaged [Forensic Firm] for investigation
3. Notified [Regulatory Authorities] as required
4. Enhanced our security controls

## Impact to Your Organization

[Specific assessment of what data from their organization was affected]

## Recommended Actions

[Steps they should take]

## Timeline for Further Information

We will provide updates every [X] hours until resolution.

## Contact

[Incident Response Team Contact Information]
```

#### Public Statement (If Required)

```markdown
# Security Incident Statement

[Company Name] recently detected and successfully contained a security incident affecting our [Service Name].

## What Happened

On [Date], we identified suspicious activity involving our AI-powered services. We immediately took action to secure our systems and investigate.

## What We're Doing

- We have contained the incident
- We are working with leading cybersecurity experts
- We have notified affected individuals and regulatory authorities
- We are implementing additional security measures

## What You Should Do

If you are a [Service Name] user, we recommend:
[Specific recommendations]

## Questions

If you have concerns, please contact: [Contact Information]

We take the security of our customers' data very seriously and sincerely apologize for any concern this incident may cause.
```

---

## Checklist & Quick Reference

### Immediate Response Checklist (First 15 Minutes)

- [ ] Verify alert legitimacy
- [ ] Classify severity (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] Page Incident Response Team
- [ ] Disable affected endpoints
- [ ] Begin session revocation
- [ ] Quarantine affected data
- [ ] Enable enhanced monitoring
- [ ] Begin documentation

### Containment Checklist (15-60 Minutes)

- [ ] All endpoints disabled
- [ ] All exposed sessions/tokens revoked
- [ ] All affected data quarantined
- [ ] Attack pattern extracted
- [ ] Spotlighting patterns updated
- [ ] Monitoring enhanced
- [ ] Legal/Compliance notified
- [ ] Executive team briefed

### Investigation Checklist (1-24 Hours)

- [ ] Attack vector identified
- [ ] Attack chain reconstructed
- [ ] Data exposure mapped
- [ ] Affected users identified
- [ ] Regulatory obligations assessed
- [ ] Forensic report generated
- [ ] Root cause determined
- [ ] Lessons learned documented

### Recovery Checklist (24-72 Hours)

- [ ] Vulnerability patched
- [ ] Guardrails updated
- [ ] Data sanitized
- [ ] Services restored (canary)
- [ ] Monitoring confirms normal operation
- [ ] Full capacity restored
- [ ] Post-mortem completed
- [ ] Improvements implemented

### Communication Checklist

- [ ] Internal executive brief sent
- [ ] Internal staff notified
- [ ] Affected users notified (if required)
- [ ] Regulatory bodies notified (if required)
- [ ] Customers notified (if required)
- [ ] Public statement issued (if required)
- [ ] Press release prepared (if required)

### Quick Commands

```bash
# Disable endpoint
curl -X POST https://api.psychsync.com/api/v1/admin/ai/endpoints/<ID>/disable

# Revoke sessions
curl -X POST https://api.psychsync.com/api/v1/admin/sessions/bulk-revoke

# Enable monitoring
kubectl set env deployment/ai-api LOG_LEVEL=DEBUG

# Check status
kubectl get pods -n production -l app=ai-api

# View logs
kubectl logs -f deployment/ai-api -n production --tail=1000
```

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **Incident Commander** | [Name] | [Phone] | [Email] |
| **Security Lead** | [Name] | [Phone] | [Email] |
| **Engineering Lead** | [Name] | [Phone] | [Email] |
| **Legal Counsel** | [Name] | [Phone] | [Email] |
| **PR/Media** | [Name] | [Phone] | [Email] |
| **Executive Sponsor** | [Name] | [Phone] | [Email] |

### Regulatory Reporting Deadlines

| Regulation | Deadline | Authority |
|------------|----------|-----------|
| **GDPR** | 72 hours | Data Protection Authority |
| **HIPAA** | 60 days | HHS OCR |
| **CCPA** | Reasonable promptness | California AG |
| **SOX** | 4 days (material) | SEC |

---

## Appendix: Tools and Resources

### Detection Tools

```bash
# Prompt injection testing
python -m tests.security.prompt_injection_tests

# Forensic analysis
python -m ai.security.forensics.analyze_prompt

# Data exposure mapping
python -m app.services.data_exposure_mapper
```

### Recovery Tools

```bash
# Data sanitization
python -m app.services.data_sanitizer

# Guardrail deployment
python -m ai.security.deploy_guardrails

# Service restoration
kubectl rollout restart deployment/ai-api
```

### References

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)
- [GDPR Data Breach Guidelines](https://gdpr-info.eu/issues-Personal-data-breach.htm)
- [HIPAA Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)

---

**Document Control**:
- **Owner**: Security Operations Team
- **Review Frequency**: Quarterly
- **Next Review**: 2026-03-26
- **Change History**:
  - 2025-12-26: Initial version (v1.0.0)

---

**END OF RUNBOOK**
