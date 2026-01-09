# PsychSync LLM Security Policy

**Document Version**: 1.0
**Last Updated**: 2025-12-27
**Next Review Date**: 2026-03-27
**Owner**: Security Team
**Approved By**: CTO, Security Lead

---

## Table of Contents

1. [Policy Overview](#policy-overview)
2. [Scope](#scope)
3. [Security Principles](#security-principles)
4. [Spotlighting Policy](#spotlighting-policy)
5. [Tool Allow-Listing Policy](#tool-allow-listing-policy)
6. [Human Approval Policy](#human-approval-policy)
7. [Content Validation Policy](#content-validation-policy)
8. [Incident Response](#incident-response)
9. [Compliance & Audit](#compliance--audit)
10. [Implementation Guidelines](#implementation-guidelines)

---

## Policy Overview

This policy establishes security requirements for LLM (Large Language Model) integration within the PsychSync platform. It implements defense-in-depth through content spotlighting, tool allow-listing, and human approval workflows.

### Objectives

- **Prevent prompt injection attacks** against LLM systems
- **Control LLM-generated content** to prevent malicious outputs
- **Restrict tool access** to authorized operations only
- **Ensure human oversight** for sensitive operations
- **Maintain audit trails** for all LLM interactions

### Compliance Frameworks

This policy aligns with:
- **NIST AI Risk Management Framework (AI RMF)**
- **OWASP LLM Top 10**
- **ISO 27001/27018** (Information Security)
- **SOC 2 Type II** (Trust Services Criteria)
- **HIPAA** (Protected Health Information)

---

## Scope

This policy applies to:

1. **All LLM integrations** in PsychSync platform
2. **AI-generated content** processing and storage
3. **Agent tool execution** and automation
4. **Third-party AI services** integration
5. **Developer teams** implementing AI features

### Exclusions

- Static content templates (non-AI generated)
- Read-only database queries (non-tool operations)
- Internal system logging (non-user-facing)

---

## Security Principles

### 1. Zero Trust for User Input

**Policy**: All user input must be treated as untrusted and explicitly marked.

```python
from app.middleware.spotlighting import spotlight_user_input

# Required: Mark all user input
safe_prompt = spotlight_user_input(user_prompt)
```

**Implementation**:
- Use `ContentSource.USER` for all direct user input
- Apply `TrustLevel.UNTRUSTED` by default
- Never bypass spotlighting for "trusted users"

### 2. Explicit Tool Authorization

**Policy**: All tools must be explicitly authorized before execution.

```python
from app.middleware.spotlighting import validate_tool_use

# Required: Validate tool use
if not validate_tool_use("export_all_data", require_approval=True):
    raise HumanApprovalRequired("This operation requires approval")
```

**Implementation**:
- Default-deny: Tools not in allow-list are blocked
- Human approval required for sensitive operations
- Audit log all tool execution attempts

### 3. Output Validation

**Policy**: All LLM outputs must be validated before use.

```python
from app.middleware.spotlighting import spotlighting_engine

# Required: Validate LLM output
is_valid, issues = spotlighting_engine.validate_llm_output(llm_response)
if not is_valid:
    # Log and block/sanitize
    logger.warning(f"LLM output validation failed: {issues}")
```

**Implementation**:
- Check for dangerous patterns (XSS, SQL injection, etc.)
- Verify no input leakage (> 80% overlap)
- Detect spotlight marker manipulation

### 4. Human-in-the-Loop for Sensitive Operations

**Policy**: High-risk operations require explicit human approval.

```python
from app.middleware.spotlighting import request_human_approval, check_human_approval

# Required: Request approval for sensitive operations
approval_id = request_human_approval(
    operation="delete_user",
    context={"user_id": user.id, "reason": reason},
    user_id=current_user.id
)

# Later: Check approval status
is_approved, message = check_human_approval(approval_id)
if not is_approved:
    raise HTTPException(status_code=403, detail=message)
```

**Implementation**:
- Operations with data destruction require approval
- Bulk data exports require approval
- Security configuration changes require approval
- Approval timeout: 5 minutes (configurable)

---

## Spotlighting Policy

### What is Spotlighting?

**Spotlighting** is the practice of explicitly marking untrusted content with special delimiters as it flows through the system. This enables:

1. **Content provenance tracking** - Know where data originated
2. **Automatic validation** - Enforce validation at processing boundaries
3. **Audit trail** - Track all untrusted content processing

### Spotlighting Requirements

#### 4.1 All User Input Must Be Spotlighted

**Requirement**: Direct user input MUST be wrapped with spotlight markers before LLM processing.

```python
# ✓ CORRECT
safe_prompt = spotlight_user_input(user_prompt)
response = llm.generate(safe_prompt)

# ✗ INCORRECT
response = llm.generate(user_prompt)  # Unmarked content!
```

**Compliance Check**:
- [ ] All user input endpoints apply spotlighting
- [ ] Spotlight markers are present in LLM prompts
- [ ] Content hash is generated and stored

#### 4.2 External API Responses Must Be Spotlighted

**Requirement**: Responses from external APIs MUST be marked as `ContentSource.EXTERNAL_API`.

```python
spotlighted = spotlighting_engine.spotlight_content(
    content=api_response,
    source=ContentSource.EXTERNAL_API,
    trust_level=TrustLevel.PARTIAL
)
```

**Compliance Check**:
- [ ] External API responses are spotlighted
- [ ] Trust level reflects API verification status
- [ ] Content integrity is verified via hash

#### 4.3 LLM Outputs Must Be Spotlighted

**Requirement**: LLM-generated content MUST be marked as `ContentSource.LLM_OUTPUT`.

```python
spotlighted = spotlighting_engine.spotlight_content(
    content=llm_response,
    source=ContentSource.LLM_OUTPUT,
    trust_level=TrustLevel.PARTIAL  # Not fully trusted until validated
)
```

**Compliance Check**:
- [ ] All LLM outputs are spotlighted
- [ ] Validation is performed before use
- [ ] Failed validations are logged and blocked

#### 4.4 Spotlight Markers Must Not Be Removed

**Requirement**: Spotlight markers MUST remain in place until content is validated and sanitized.

```python
# ✓ CORRECT: Keep markers until validation
is_valid, issues = spotlighting_engine.validate_llm_output(spotlighted_output)
if is_valid:
    clean_content = spotlighting_engine.unwrap_content(spotlighted_output)

# ✗ INCORRECT: Remove markers before validation
clean_content = spotlighting_engine.unwrap_content(spotlighted_output)
is_valid, issues = spotlighting_engine.validate_llm_output(clean_content)
```

**Compliance Check**:
- [ ] Markers are present during validation
- [ ] Markers are only removed after successful validation
- [ ] Marker removal attempts are logged

### Spotlighting Mode Configuration

**Production Environment**:
```python
SpotlightingMode.STRICT  # All content must be explicitly marked
```

**Development Environment**:
```python
SpotlightingMode.PERMISSIVE  # Auto-mark unmarked content
```

**Testing Environment**:
```python
SpotlightingMode.DISABLED  # Only for unit tests
```

---

## Tool Allow-Listing Policy

### What is Tool Allow-Listing?

**Tool Allow-Listing** is a security control where only explicitly authorized tools can be executed by AI agents. This prevents unauthorized operations.

### Allow-List Categories

#### 5.1 Default Allowed Tools

Safe operations that can be executed without approval:

```python
DEFAULT_ALLOWED_TOOLS = {
    # AI/ML operations
    "analyze_assessment_results",
    "process_personality_test",
    "calculate_psychometric_scores",

    # Database read operations
    "get_user_profile",
    "get_assessment_results",
    "get_team_analytics",

    # Cache operations
    "cache_get",
    "cache_set",

    # Validation operations
    "validate_email",
    "validate_password",
}
```

**Criteria for Default Allow-List**:
- Read-only operations
- No sensitive data access
- No system modifications
- No external network calls (except approved APIs)

#### 5.2 Human Approval Required Tools

Sensitive operations requiring explicit approval:

```python
HUMAN_APPROVAL_TOOLS = {
    "delete_user",
    "delete_assessment",
    "export_all_data",
    "modify_system_settings",
    "access_all_users",
}
```

**Criteria for Human Approval**:
- Data destruction operations
- Bulk data exports
- Security setting changes
- Administrative functions

#### 5.3 Blocked Tools

Operations that are NEVER allowed:

```python
BLOCKED_TOOLS = {
    "execute_arbitrary_code",
    "execute_system_command",
    "modify_security_settings",
    "access_passwords",
    "bypass_authentication",
    "access_raw_database",
    "modify_database_directly",
}
```

**Criteria for Blocking**:
- Arbitrary code execution
- Direct system command execution
- Security control bypass
- Credential access

### Tool Authorization Requirements

#### 6.1 All Tool Calls Must Be Validated

**Requirement**: Every tool execution MUST be validated against the allow-list.

```python
# ✓ CORRECT
is_allowed, reason = tool_allowlist.is_tool_allowed(tool_name)
if not is_allowed:
    raise HTTPException(status_code=403, detail=reason)

# ✗ INCORRECT
result = execute_tool(tool_name)  # No validation!
```

**Compliance Check**:
- [ ] All tool calls are validated
- [ ] Blocked tools are rejected
- [ ] Audit log includes tool validation results

#### 6.2 Custom Tools Must Be Explicitly Added

**Requirement**: New tools MUST be added to the allow-list before use.

```python
# Add to allow-list via configuration
tool_allowlist.add_allowed_tool("my_new_tool")

# Or via configuration file
CUSTOM_ALLOWED_TOOLS = {
    "my_new_tool",
    "another_safe_tool",
}
```

**Approval Process for New Tools**:
1. Security review of tool functionality
2. Risk assessment (data access, permissions)
3. Classification (default/approval-required/blocked)
4. Documentation update
5. Security team approval

#### 6.3 Tool Execution Must Be Logged

**Requirement**: All tool execution attempts MUST be logged.

```python
logger.info(
    "Tool execution attempted",
    extra={
        "tool_name": tool_name,
        "allowed": is_allowed,
        "user_id": user.id,
        "approval_id": approval_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

**Log Fields**:
- Tool name
- Allow-list decision (allowed/blocked)
- User ID
- Approval ID (if required)
- Timestamp
- Reason (if blocked)

---

## Human Approval Policy

### What is Human Approval?

**Human Approval** is a workflow where sensitive operations require explicit authorization from a designated approver before execution.

### Approval Requirements

#### 7.1 Operations Requiring Approval

**Mandatory Approval Required**:

| Operation | Approval Required | Approver Role | Timeout |
|-----------|------------------|---------------|---------|
| Delete user | Yes | Admin, Security Lead | 5 min |
| Delete assessment | Yes | Admin, Manager | 5 min |
| Export all data | Yes | Admin, Compliance | 5 min |
| Modify system settings | Yes | Admin, DevOps | 5 min |
| Access all users | Yes | Admin, Security Lead | 5 min |

#### 7.2 Approval Workflow

**Step 1: Request Approval**

```python
approval_id = approval_manager.request_approval(
    operation="delete_user",
    context={
        "user_id": target_user.id,
        "reason": reason,
        "requested_by": current_user.id
    },
    user_id=current_user.id
)
```

**Step 2: Wait for Approval**

```python
# Poll for approval status
max_wait_time = 300  # 5 minutes
start_time = time.time()

while time.time() - start_time < max_wait_time:
    is_approved, message = approval_manager.check_approval(approval_id)
    if is_approved:
        # Execute operation
        execute_operation()
        break
    elif "denied" in message.lower():
        raise HTTPException(status_code=403, detail=message)
    else:
        time.sleep(2)  # Wait before checking again
```

**Step 3: Execute or Deny**

```python
if is_approved:
    # Log approval
    logger.info(f"Operation approved: {approval_id}")
    # Execute
    result = execute_operation()
else:
    # Log denial
    logger.warning(f"Operation denied: {approval_id} - {message}")
    raise HTTPException(status_code=403, detail=message)
```

#### 7.3 Approval Roles & Permissions

**Who Can Approve**:

| Operation | Approver Roles | Self-Approval Allowed |
|-----------|---------------|---------------------|
| Delete user | Admin, Security Lead | No |
| Delete assessment | Admin, Manager | No |
| Export all data | Admin, Compliance | No |
| Modify system settings | Admin, DevOps | No |
| Access all users | Admin, Security Lead | No |

**Policy**: Self-approval is **NEVER** allowed for destructive operations.

#### 7.4 Approval Audit Trail

**Required Log Fields**:

```python
{
    "approval_id": "abc123...",
    "operation": "delete_user",
    "requested_by": "user_123",
    "requested_at": "2025-12-27T10:00:00Z",
    "approved_by": "admin_456",
    "approved_at": "2025-12-27T10:02:00Z",
    "denied": False,
    "denial_reason": None,
    "context": {
        "user_id": 789,
        "reason": "Policy violation"
    }
}
```

---

## Content Validation Policy

### LLM Output Validation

#### 8.1 Dangerous Pattern Detection

**Required Checks**:

1. **XSS (Cross-Site Scripting)**
   ```python
   r'<script[^>]*>.*?</script>'
   r'javascript:'
   ```

2. **SQL Injection**
   ```python
   r"('|(-{2})|(;)|(\b(ALTER|CREATE|DELETE|DROP|EXEC(UTE){0,1}|INSERT( +INTO){0,1}|MERGE|SELECT|UPDATE|UNION( +ALL){0,1})\b)"
   ```

3. **Path Traversal**
   ```python
   r'\.\.[/\\]'
   ```

4. **Command Injection**
   ```python
   r'[;&|`$]'
   ```

5. **Template Injection**
   ```python
   r'\{\{.*?\}\}'
   r'\${.*?}'
   ```

#### 8.2 Input Leakage Detection

**Requirement**: Detect when LLM output contains too much of the input (> 80% overlap).

```python
def _contains_input_leakage(self, output: str, input_content: str) -> bool:
    input_words = set(input_content.lower().split())
    output_words = set(output.lower().split())

    if not input_words or not output_words:
        return False

    overlap = len(input_words & output_words) / len(input_words)
    return overlap > 0.8
```

#### 8.3 Spotlight Marker Manipulation Detection

**Requirement**: Detect attempts to manipulate or remove spotlight markers.

**Suspicious Phrases**:
- "ignore spotlight"
- "remove markers"
- "strip comments"
- "UNTRUSTED_CONTENT_START"
- "UNTRUSTED_CONTENT_END"

#### 8.4 Validation Failure Handling

**Required Actions on Validation Failure**:

1. **Log the incident** with full context
2. **Block the output** from being used
3. **Sanitize if safe**, otherwise reject entirely
4. **Alert security team** for high-severity failures

```python
is_valid, issues = spotlighting_engine.validate_llm_output(llm_output)

if not is_valid:
    logger.critical(
        "LLM output validation failed",
        extra={
            "issues": issues,
            "output": llm_output[:500],  # First 500 chars
            "user_id": user.id,
            "session_id": session.id
        }
    )

    # Determine severity
    if any("critical" in issue.lower() for issue in issues):
        # Block entirely
        raise HTTPException(status_code=403, detail="Malicious content detected")
    else:
        # Sanitize and warn
        sanitized_output = sanitize_content(llm_output)
        return sanitized_output
```

---

## Incident Response

### Security Incident Categories

#### 9.1 Prompt Injection Attack

**Indicators**:
- Jailbreak patterns detected in input
- Attempt to override system instructions
- Suspicious linguistic patterns

**Response Actions**:
1. **Immediate**: Block request, log incident
2. **Short-term**: Flag user account for monitoring
3. **Long-term**: Update detection patterns, review similar requests

**Severity Levels**:
- **LOW**: Linguistic anomalies only
- **MEDIUM**: Known jailbreak patterns
- **HIGH**: Multiple patterns, high confidence
- **CRITICAL**: Successful bypass detected

#### 9.2 Tool Authorization Bypass

**Indicators**:
- Attempted execution of blocked tool
- Approval workflow bypass
- Allow-list manipulation

**Response Actions**:
1. **Immediate**: Block operation, revoke session
2. **Short-term**: Audit all tool executions by user
3. **Long-term**: Review allow-list configuration, update policies

#### 9.3 Output Validation Failure

**Indicators**:
- Dangerous patterns in LLM output
- Input leakage detected
- Marker manipulation attempt

**Response Actions**:
1. **Immediate**: Block output, sanitize if possible
2. **Short-term**: Review LLM prompts, update validation rules
3. **Long-term**: Consider LLM provider change if persistent

### Incident Reporting

**Required Report Fields**:

```python
{
    "incident_id": "inc-20251227-001",
    "timestamp": "2025-12-27T10:00:00Z",
    "category": "prompt_injection",
    "severity": "HIGH",
    "user_id": "user_123",
    "session_id": "sess-abc",
    "description": "Jailbreak attempt detected",
    "indicators": ["direct_injection_pattern", "role_playing"],
    "actions_taken": ["blocked", "logged", "user_flagged"],
    "resolution": "blocked",
    "resolved_by": "automated_system",
    "resolved_at": "2025-12-27T10:00:01Z"
}
```

---

## Compliance & Audit

### Audit Requirements

#### 10.1 Logging Requirements

**All LLM interactions MUST log**:

1. **Input**
   - User ID
   - Session ID
   - Content (spotlighted)
   - Timestamp
   - Content hash

2. **Processing**
   - LLM model used
   - Tool calls made
   - Approval IDs
   - Processing time

3. **Output**
   - LLM output (spotlighted)
   - Validation results
   - Issues detected
   - Actions taken

**Log Retention**:
- **Production**: 1 year
- **Development**: 90 days
- **Testing**: 30 days

#### 10.2 Audit Trail

**Required Auditable Events**:

1. User input received
2. Content spotlighted
3. LLM prompt sent
4. LLM response received
5. Output validated
6. Tool execution attempted
7. Approval requested/granted/denied
8. Security incident detected
9. Content blocked/sanitized

#### 10.3 Compliance Reports

**Monthly Reports**:

1. **Security Metrics**
   - Total LLM requests
   - Jailbreak attempts detected
   - Validation failures
   - Tools blocked

2. **Approval Metrics**
   - Approvals requested
   - Approvals granted
   - Approvals denied
   - Average approval time

3. **Incident Summary**
   - Incidents by category
   - Incidents by severity
   - Resolution time
   - Trends (vs. previous month)

---

## Implementation Guidelines

### Developer Guidelines

#### 11.1 Mandatory Spotlighting

**DO**:
```python
from app.middleware.spotlighting import spotlight_user_input

# Always spotlight user input
safe_input = spotlight_user_input(user_data)
response = llm.generate(safe_input)
```

**DON'T**:
```python
# Never send unmarked input to LLM
response = llm.generate(user_data)  # ✗ WRONG
```

#### 11.2 Mandatory Tool Validation

**DO**:
```python
from app.middleware.spotlighting import validate_tool_use

# Always validate tools
if validate_tool_use(tool_name):
    result = execute_tool(tool_name)
```

**DON'T**:
```python
# Never execute tools without validation
result = execute_tool(tool_name)  # ✗ WRONG
```

#### 11.3 Mandatory Output Validation

**DO**:
```python
from app.middleware.spotlighting import spotlighting_engine

# Always validate LLM output
is_valid, issues = spotlighting_engine.validate_llm_output(llm_output)
if is_valid:
    use_output(llm_output)
else:
    handle_validation_failure(issues)
```

**DON'T**:
```python
# Never use unvalidated output
use_output(llm_output)  # ✗ WRONG
```

### Security Team Guidelines

#### 11.4 Review Allow-List Quarterly

**Review Checklist**:
- [ ] Remove unused tools
- [ ] Add new safe tools
- [ ] Re-classify tools based on incidents
- [ ] Update documentation

#### 11.5 Monitor Approval Metrics

**Key Metrics**:
- Approval rate (granted / requested)
- Average approval time
- Most frequently approved operations
- Denial reasons

**Alert Thresholds**:
- Approval denial rate > 20%
- Average approval time > 3 minutes
- More than 5 denial for same operation in 24h

#### 11.6 Update Detection Patterns

**Frequency**: Monthly or after major incidents

**Process**:
1. Review recent incidents
2. Identify new attack patterns
3. Update regex patterns
4. Test against false positives
5. Deploy to staging
6. Monitor for 1 week
7. Deploy to production

---

## Policy Violations

### Violation Categories

#### 12.1 Critical Violations

**Examples**:
- Sending unmarked user input to LLM
- Executing blocked tools
- Bypassing approval workflow
- Disabling validation in production

**Consequences**:
1. Immediate action: Block deployment
2. Security review within 24h
3. Mandatory retraining
4. Possible termination for repeat offenses

#### 12.2 High Severity Violations

**Examples**:
- Missing spotlight markers in some inputs
- Late tool validation (after execution)
- Incomplete output validation
- Approval timeout exceeded significantly

**Consequences**:
1. Immediate action: Flag for review
2. Remediation plan within 48h
3. Security review within 1 week
4. Performance improvement plan if repeated

#### 12.3 Medium Severity Violations

**Examples**:
- Missing documentation for custom tools
- Incomplete logging
- Delayed log submission
- Minor documentation gaps

**Consequences**:
1. Action: Issue reminder
2. Remediation plan within 1 week
3. Manager notification

### Reporting Violations

**Process**:
1. Document violation (time, location, specifics)
2. Report to security team (security@psychsync.ai)
3. Security team triages within 24h
4. Investigation completed within 5 business days
5. Remediation plan agreed upon
6. Follow-up verification

---

## Document Control

### Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-27 | Initial policy creation | Security Team |

### Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| CTO | | | |
| Security Lead | | | |
| Compliance Officer | | | |

### Next Review

**Review Date**: 2026-03-27
**Review Trigger**:
- Quarterly review
- After major security incident
- After framework changes
- After compliance audit

---

## Appendix

### A. Quick Reference

**Spotlighting**:
```python
from app.middleware.spotlighting import spotlight_user_input
safe = spotlight_user_input(user_data)
```

**Tool Validation**:
```python
from app.middleware.spotlighting import validate_tool_use
validate_tool_use("tool_name", require_approval=True)
```

**Output Validation**:
```python
from app.middleware.spotlighting import spotlighting_engine
is_valid, issues = spotlighting_engine.validate_llm_output(output)
```

**Human Approval**:
```python
from app.middleware.spotlighting import request_human_approval, check_human_approval
approval_id = request_human_approval("operation", {}, user_id)
is_approved, message = check_human_approval(approval_id)
```

### B. Contact Information

**Security Team**: security@psychsync.ai
**Incident Response**: incidents@psychsync.ai
**Policy Questions: compliance@psychsync.ai

### C. Related Documents

- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [ISO 27001](https://www.iso.org/standard/27001)
- [SOC 2](https://www.aicpa.org/soc4so)

---

**END OF POLICY DOCUMENT**
