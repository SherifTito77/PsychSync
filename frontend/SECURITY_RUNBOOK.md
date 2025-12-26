# PsychSync Security Incident Response Runbook

**Version:** 1.0  
**Last Updated:** 2025-12-25  
**Team:** Security Operations

---

## 🚨 Incident Response Checklist

### Phase 1: Detection & Identification (0-15 minutes)

- [ ] **Confirm Incident**
  - Check security logs for anomalies
  - Review alert notifications
  - Verify incident scope (users affected, data exposed)

- [ ] **Classify Severity**
  - **Critical**: Active data breach, system compromise
  - **High**: Suspicious activity, potential breach
  - **Medium**: Security control failure, no data loss
  - **Low**: Policy violation, minimal impact

- [ ] **Activate Response Team**
  - Security Lead: [Name]
  - Engineering Lead: [Name]
  - Legal/Compliance: [Name]
  - Communications: [Name]

### Phase 2: Containment (15-60 minutes)

#### Immediate Actions

- [ ] **Isolate Affected Systems**
  ```bash
  # Block malicious IPs
  # Disable compromised accounts
  # Shut down affected services if necessary
  ```

- [ ] **Preserve Evidence**
  - Enable additional logging
  - Capture network traffic
  - Document all actions taken
  - Do NOT reboot or modify systems

- [ ] **Change Credentials**
  - Reset compromised user passwords
  - Rotate API keys and secrets
  - Update encryption keys if needed

#### System-Specific Actions

**If SQL Injection Detected:**
- Block attacking IP addresses
- Review database logs for unauthorized queries
- Enable query logging
- Check for data exfiltration

**If XSS Attack Detected:**
- Sanitize affected inputs
- Check for stored XSS in database
- Review Content Security Policy logs
- Scan for malicious scripts

**If CSRF Attack Detected:**
- Rotate CSRF secret key
- Review token validation logs
- Check for unauthorized transactions
- Verify referer headers

**If Data Breach Suspected:**
- Stop all data access
- Enable audit logging
- Check encryption keys
- Assess data exposure scope

### Phase 3: Eradication (1-4 hours)

- [ ] **Remove Threat**
  - Delete malicious code/scripts
  - Remove unauthorized accounts
  - Patch vulnerabilities exploited
  - Update firewall rules

- [ ] **Identify Root Cause**
  - Review code changes
  - Check access logs
  - Analyze attack vector
  - Document security gaps

- [ ] **Validate Fixes**
  - Run security test suite
  - Verify vulnerability removed
  - Test system functionality
  - Review with security team

### Phase 4: Recovery (4-24 hours)

- [ ] **Restore Systems**
  - Deploy patched code
  - Restore from clean backups
  - Restart services
  - Monitor for anomalies

- [ ] **Validate Recovery**
  - Run health checks
  - Test all functionality
  - Verify security controls
  - Monitor logs for 24 hours

- [ ] **Communicate**
  - Notify affected users (if required)
  - Report to authorities (if GDPR/HIPAA trigger)
  - Update stakeholders
  - Document timeline

### Phase 5: Post-Incident (24-72 hours)

- [ ] **Lessons Learned**
  - Document what happened
  - Identify timeline gaps
  - Review response effectiveness
  - Update procedures

- [ ] **Preventive Measures**
  - Implement additional monitoring
  - Update security policies
  - Enhance training programs
  - Schedule security review

---

## 🛠️ Common Incident Scenarios

### Scenario 1: Brute Force Attack Detected

**Symptoms:**
- Multiple failed login attempts from same IP
- Rate limit alerts triggered
- Account lockout notifications

**Response:**
1. Block attacking IP in firewall
2. Enable enhanced monitoring on target accounts
3. Force password reset for affected users
4. Review successful logins during attack window
5. Implement MFA if not already enabled

**Commands:**
```bash
# View failed attempts
tail -f logs/security.log | grep "AUTH_LOGIN_FAILURE"

# Block IP (example)
# Add to firewall/rate limiter configuration
```

### Scenario 2: SQL Injection Attempt

**Symptoms:**
- SQL patterns in request logs
- Database error messages
- Suspicious query patterns

**Response:**
1. Immediately block attacking IP
2. Enable query logging
3. Review database for unauthorized changes
4. Check for data exfiltration
5. Test input validation

**Verification:**
```bash
# Run SQL injection tests
python3 test_security_middleware.py
```

### Scenario 3: XSS Attack Detected

**Symptoms:**
- Script tags in user input
- JavaScript in unexpected places
- CSP violations logged

**Response:**
1. Sanitize affected data
2. Check for stored XSS in database
3. Review CSP logs
4. Test all input fields
5. Update WAF rules if applicable

### Scenario 4: Data Breach Suspected

**Symptoms:**
- Unusual database activity
- Large data exports
- Encrypted data accessed unexpectedly

**Response:**
1. **IMMEDIATE**: Stop all data access
2. Enable comprehensive audit logging
3. Check encryption key integrity
4. Assess data exposure scope
5. Legal/compliance notification (if applicable)

**GDPR Breach Notification (72 hours):**
- Document what happened
- Identify affected data subjects
- Describe likely impact
- Describe mitigation measures

**HIPAA Breach Notification (60 days):**
- Notify HHS (if >500 individuals)
- Notify affected individuals
- Notify media (if >500 individuals)
- Document breach

---

## 📞 Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Security Lead | [Name] | [Phone/Email] | 24/7 |
| Engineering Lead | [Name] | [Phone/Email] | Business hours |
| Legal Counsel | [Name] | [Phone/Email] | Business hours |
| Hosting Provider | [Provider] | [Support] | 24/7 |

---

## 🔍 Investigation Commands

### Check Security Logs

```bash
# Recent security events
tail -100 logs/security.log

# Failed authentication attempts
grep "AUTH_LOGIN_FAILURE" logs/security.log | tail -50

# SQL injection attempts
grep "SQL_INJECTION" logs/security.log | tail -50

# XSS attempts
grep "XSS_ATTEMPT" logs/security.log | tail -50
```

### Monitor Active Connections

```bash
# Active database connections
psql -U psychsync_user -d psychsync_db -c "SELECT * FROM pg_stat_activity;"

# Redis connections
redis-cli CLIENT LIST

# HTTP connections
lsof -i :8000
```

### Check System Integrity

```bash
# Verify security middleware active
curl -I http://localhost:8000/health | grep -i "x-\|content-\|strict-"

# Test encryption service
python3 test_encryption_service.py

# Run full security test suite
python3 test_security_middleware.py
```

---

## 📊 Severity Classification

| Severity | Definition | Response Time | Notification |
|----------|------------|---------------|--------------|
| **Critical** | Active breach, data exfiltration | < 15 minutes | Executive team, legal |
| **High** | System compromise, unauthorized access | < 1 hour | Security team, management |
| **Medium** | Security control failure | < 4 hours | Security team |
| **Low** | Policy violation, minor issue | < 24 hours | Team lead |

---

## 📋 Post-Incident Report Template

```markdown
# Security Incident Report

**Incident ID:** [YYYY-MM-DD-001]
**Date:** [Date]
**Severity:** [Critical/High/Medium/Low]
**Status:** [Open/Closed]

## Executive Summary
[Brief overview of what happened]

## Timeline
- **Detection:** [Date/time]
- **Containment:** [Date/time]
- **Eradication:** [Date/time]
- **Recovery:** [Date/time]

## Impact Assessment
- **Users Affected:** [Number]
- **Data Exposed:** [Yes/No - Details]
- **Systems Affected:** [List]
- **Downtime:** [Duration]

## Root Cause
[What caused the incident]

## Actions Taken
1. [Action 1]
2. [Action 2]
...

## Lessons Learned
[What went well, what could be improved]

## Preventive Measures
[What will be done to prevent recurrence]

## Appendix
- [Logs]
- [Screenshots]
- [Evidence]
```

---

**Next Review:** 2026-01-25

**For questions or updates, contact:** Security Team
