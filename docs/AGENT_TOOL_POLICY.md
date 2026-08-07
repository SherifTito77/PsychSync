# Agent Tool Policy

**Version**: 1.0
**Effective Date**: 2025-12-26
**Owner**: Security Team, AI Engineering
**Approved By**: CTO, Security Lead, AI Engineering Lead

---

## Policy Statement

**Objective**: Establish strict controls over AI agent tool access to prevent unauthorized actions while maintaining agent functionality.

**Scope**: All AI agent tools in the orchestration layer, including:
- Database access tools
- Email communication tools
- File system tools
- API integration tools
- Shell execution tools (BLOCKED by default)

**Core Principles**:
1. ✅ **Tool Allow-List**: Only explicitly allowed tools can be invoked
2. ✅ **Role-Based Access**: Tools mapped to user roles
3. ✅ **Consent Required**: Sensitive actions require explicit user consent
4. ✅ **Rate Limiting**: All tools have rate limits to prevent abuse
5. ✅ **Audit Logging**: All tool invocations are logged

---

## Tool Enumeration

### Database Tools

#### `db_read_query`
**Capability**: Execute read-only SQL queries
**Safety**: SAFE (with validation)
**Access Level**: READ-ONLY

**Constraints**:
- ❌ No WRITE, INSERT, UPDATE, DELETE operations
- ❌ No ALTER, DROP, CREATE operations
- ❌ No administrative commands
- ✅ Only SELECT queries allowed
- ✅ Query timeout: 30 seconds
- ✅ Result limit: 1000 rows

**Validation**:
```python
def validate_db_read_query(query: str) -> bool:
    """Validate query is read-only"""

    # Check for dangerous keywords
    dangerous = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'GRANT', 'REVOKE', 'TRUNCATE'
    ]

    query_upper = query.upper()
    for keyword in dangerous:
        if keyword in query_upper:
            return False

    # Must start with SELECT
    if not query_upper.strip().startswith('SELECT'):
        return False

    # Check for comment injection
    if '--' in query or '/*' in query:
        return False

    return True
```

---

#### `db_anonymized_export`
**Capability**: Export anonymized data for analysis
**Safety**: SAFE (PII removed)
**Access Level**: READ-ONLY + ANONYMIZED

**Constraints**:
- ✅ Automatic PII redaction
- ✅ One-way hash for user IDs
- ✅ Aggregate-only for sensitive fields
- ✅ Requires researcher role

**PII Redaction**:
```python
PII_FIELDS = {
    'email', 'phone', 'ssn', 'address',
    'first_name', 'last_name', 'full_name'
}

def anonymize_row(row: dict) -> dict:
    """Redact PII from database row"""

    anonymized = {}
    for key, value in row.items():
        if key in PII_FIELDS:
            # One-way hash
            anonymized[key] = hashlib.sha256(value.encode()).hexdigest()[:16]
        else:
            anonymized[key] = value

    return anonymized
```

---

### Email Tools

#### `email_draft_create`
**Capability**: Create email draft (does not send)
**Safety**: SAFE (manual send required)
**Access Level**: WRITE-DRAFT

**Constraints**:
- ✅ Creates draft only (no automatic send)
- ✅ Requires user review before sending
- ✅ Logs draft creation
- ❌ No direct send capability

---

#### `email_send_verified`
**Capability**: Send pre-verified email templates
**Safety**: MEDIUM (template-only)
**Access Level**: CLINICIAN, ADMIN

**Constraints**:
- ✅ Only pre-approved templates
- ✅ No custom content
- ✅ Requires explicit consent
- ✅ Logged with patient ID

**Approved Templates**:
```python
APPROVED_EMAIL_TEMPLATES = {
    'assessment_invitation': {
        'template': 'emails/assessment_invite.html',
        'required_consent': True,
        'allowed_roles': ['clinician', 'admin']
    },
    'reminder': {
        'template': 'emails/reminder.html',
        'required_consent': True,
        'allowed_roles': ['clinician', 'admin']
    },
    'results_available': {
        'template': 'emails/results_ready.html',
        'required_consent': False,  # Automated
        'allowed_roles': ['system']
    }
}
```

---

### File System Tools

#### `file_read_allowed`
**Capability**: Read files from allowed directories
**Safety**: SAFE (directory-restricted)
**Access Level**: READ-ONLY

**Constraints**:
- ✅ Only whitelisted directories
- ❌ No access to /etc, /home, config files
- ❌ No symlink following
- ✅ File size limit: 10MB

**Allowed Directories**:
```python
ALLOWED_READ_DIRS = [
    '/app/public/',           # Public assets
    '/app/templates/',        # Email templates
    '/app/docs/',             # Documentation
    '/var/assessment-exports/' # Assessment exports
]
```

**Path Validation**:
```python
def validate_file_read(path: str) -> bool:
    """Validate file path is in allowed directory"""

    # Normalize path
    normalized = os.path.normpath(path)

    # Check against allowed directories
    for allowed_dir in ALLOWED_READ_DIRS:
        if normalized.startswith(allowed_dir):
            # Prevent directory traversal
            if '..' in normalized:
                return False
            return True

    return False
```

---

#### `file_write_allowed`
**Capability**: Write files to allowed directories
**Safety**: MEDIUM (restricted paths)
**Access Level**: WRITE-ALLOWED

**Constraints**:
- ✅ Only whitelisted directories
- ❌ No overwrite of existing files
- ✅ File size limit: 50MB
- ✅ Requires consent for writes > 1MB

**Allowed Write Directories**:
```python
ALLOWED_WRITE_DIRS = [
    '/var/assessment-exports/',  # Assessment exports
    '/var/tmp/',                 # Temporary files
    '/var/user-uploads/',        # User uploads
]
```

---

### API Tools

#### `api_external_call`
**Capability**: Call approved external APIs
**Safety**: MEDIUM (allow-listed URLs)
**Access Level**: API-ACCESS

**Constraints**:
- ✅ Only whitelisted domains
- ✅ Request body size limit: 1MB
- ✅ Response timeout: 30 seconds
- ✅ No credential passing

**Allowed Domains**:
```python
ALLOWED_API_DOMAINS = {
    'api.openai.com': {
        'purposes': ['llm_inference'],
        'rate_limit': '100/minute',
        'data_types': ['text']
    },
    'api.anthropic.com': {
        'purposes': ['llm_inference'],
        'rate_limit': '100/minute',
        'data_types': ['text']
    },
    'api.sendgrid.com': {
        'purposes': ['email_delivery'],
        'rate_limit': '10/second',
        'data_types': ['email_metadata']
    }
}
```

---

### Shell Tools

#### `shell_execute`
**Capability**: Execute shell commands
**Safety**: **BLOCKED**
**Access Level**: **NOT ALLOWED**

**Rationale**:
- Shell execution is highest-risk tool
- Enables arbitrary code execution
- Cannot be made safe for production
- Even with allow-listed commands, argument injection is possible

**Blocked Commands**:
```bash
# ALL shell commands are BLOCKED
# No exceptions for production

# For admin operations, use:
# - Dedicated admin interfaces (not agent tools)
# - SSH with MFA (not via agent)
# - Infrastructure as code (Terraform, CloudFormation)
```

**Exception Process** (Emergency Only):
```python
# Emergency override requires ALL of:
# 1. CTO approval
# 2. Security team approval
# 3. Time-limited (1 hour)
# 4. Specific command documented
# 5. Real-time monitoring
# 6. Post-incident review required

# In practice: NEVER use this in production
```

---

## Role-Based Tool Mapping

### Tool Access Matrix

| Tool | Patient | Clinician | Researcher | Admin | Super Admin |
|------|---------|----------|-----------|-------|-------------|
| `db_read_query` | ❌ | ✅ Own data | ✅ Anonymized | ✅ All | ✅ All |
| `db_anonymized_export` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `email_draft_create` | ✅ Own | ✅ Patients | ❌ | ✅ | ✅ |
| `email_send_verified` | ❌ | ✅ Template | ❌ | ✅ | ✅ |
| `file_read_allowed` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `file_write_allowed` | ❌ | ✅ Exports | ✅ Exports | ✅ | ✅ |
| `api_external_call` | ❌ | ❌ | ✅ With approval | ✅ | ✅ |
| `shell_execute` | ❌ | ❌ | ❌ | ❌ | ❌ (emergency only) |

**Role Definitions**:

```python
ROLE_PERMISSIONS = {
    'patient': {
        'tools': ['email_draft_create'],
        'constraints': {
            'email_draft_create': {
                'max_per_day': 5,
                'requires_consent': False
            }
        }
    },

    'clinician': {
        'tools': [
            'db_read_query',           # Own patients only
            'email_draft_create',
            'email_send_verified',     # Template only
            'file_read_allowed',
            'file_write_allowed'       # Exports only
        ],
        'constraints': {
            'db_read_query': {
                'row_limit': 100,
                'require_patient_id': True
            },
            'email_send_verified': {
                'templates': ['assessment_invitation', 'reminder'],
                'require_consent': True
            }
        }
    },

    'researcher': {
        'tools': [
            'db_anonymized_export',
            'file_read_allowed',
            'file_write_allowed',
            'api_external_call'        # With approval
        ],
        'constraints': {
            'db_anonymized_export': {
                'requires_irb_approval': True,
                'log_all_queries': True
            },
            'api_external_call': {
                'require_approval': True,
                'allowed_apis': ['openai', 'anthropic']
            }
        }
    },

    'admin': {
        'tools': [
            'db_read_query',
            'db_anonymized_export',
            'email_draft_create',
            'email_send_verified',
            'file_read_allowed',
            'file_write_allowed',
            'api_external_call'
        ],
        'constraints': {
            'db_read_query': {
                'row_limit': 10000
            }
        }
    },

    'super_admin': {
        'tools': [
            'db_read_query',
            'db_anonymized_export',
            'email_draft_create',
            'email_send_verified',
            'file_read_allowed',
            'file_write_allowed',
            'api_external_call',
            'shell_execute'  # Emergency only, requires CTO approval
        ],
        'constraints': {
            'shell_execute': {
                'requires_cto_approval': True,
                'time_limited': 3600,  # 1 hour
                'log_all_commands': True,
                'require_reason': True
            }
        }
    }
}
```

---

## Consent Requirements

### Sensitive Actions Require Consent

**Actions Always Requiring Consent**:

| Tool | Action | Consent Type | Justification |
|------|--------|--------------|---------------|
| `db_read_query` | Export > 100 rows | Explicit | Large data export |
| `email_send_verified` | Send any email | Explicit | PHI communication |
| `file_write_allowed` | Write > 1MB | Explicit | Large file write |
| `api_external_call` | External API call | Implicit | Pre-approved domains |
| `db_anonymized_export` | Export research data | Explicit | IRB compliance |

**Consent Flow**:

```python
async def request_consent(
    user_id: str,
    tool_name: str,
    action_description: str,
    consent_type: str = "explicit"
) -> bool:
    """
    Request user consent for sensitive action

    Args:
        user_id: User requesting action
        tool_name: Tool being invoked
        action_description: What the tool will do
        consent_type: "explicit" (must click OK) or "implicit" (can proceed)

    Returns:
        True if consent granted, False otherwise
    """

    if consent_type == "implicit":
        # Log and proceed
        log_consent_request(user_id, tool_name, "implicit", True)
        return True

    # Explicit consent - prompt user
    consent_request = {
        "user_id": user_id,
        "tool": tool_name,
        "action": action_description,
        "timestamp": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }

    # Store request in database
    await store_consent_request(consent_request)

    # Wait for user response (via WebSocket or API)
    consent_granted = await wait_for_consent(user_id, tool_name, timeout=300)

    # Log result
    log_consent_request(user_id, tool_name, "explicit", consent_granted)

    return consent_granted
```

---

## Rate Limiting

### Per-Tool Rate Limits

**Default Limits**:

| Tool | Rate Limit | Burst | Window |
|------|-----------|-------|--------|
| `db_read_query` | 10/minute | 20 | 1 minute |
| `db_anonymized_export` | 1/hour | - | 1 hour |
| `email_draft_create` | 5/minute | 10 | 1 minute |
| `email_send_verified` | 10/minute | 20 | 1 minute |
| `file_read_allowed` | 20/minute | 40 | 1 minute |
| `file_write_allowed` | 5/minute | 10 | 1 minute |
| `api_external_call` | 100/minute | 200 | 1 minute |

**Rate Limit Implementation**:

```python
from ratelimit import RateLimiter
from functools import wraps

class AgentToolRateLimiter:
    """Rate limiter for agent tools"""

    def __init__(self):
        self.limiters = {}
        self.redis = Redis.from_url(settings.REDIS_URL)

    def get_limiter(self, tool_name: str, user_id: str) -> RateLimiter:
        """Get or create rate limiter for tool"""

        key = f"tool_rate_limit:{tool_name}:{user_id}"

        if key not in self.limiters:
            # Get tool-specific limits
            limits = TOOL_RATE_LIMITS.get(tool_name, {
                'rate': 10,
                'burst': 20,
                'period': 60  # seconds
            })

            self.limiters[key] = RateLimiter(
                key=key,
                rate=limits['rate'],
                burst=limits['burst'],
                redis=self.redis
            )

        return self.limiters[key]

    async def check_rate_limit(self, tool_name: str, user_id: str) -> bool:
        """Check if user is within rate limit"""

        limiter = self.get_limiter(tool_name, user_id)

        # Try to acquire token
        allowed = await limiter.acquire()

        if not allowed:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {tool_name} by user {user_id}",
                extra={
                    "tool": tool_name,
                    "user_id": user_id,
                    "event_type": "tool_rate_limit_exceeded"
                }
            )

        return allowed


# Usage in middleware
@tool_rate_limiter.check_rate_limit
async def invoke_tool(tool_name: str, user_id: str, **kwargs):
    """Tool invocation with rate limiting"""
    pass
```

---

## Audit Logging

### Log All Tool Invocations

**Required Fields**:

```python
class ToolInvocationLog(BaseModel):
    """Log entry for tool invocation"""

    # Who
    user_id: str
    user_role: str
    session_id: str

    # What
    tool_name: str
    tool_parameters: dict

    # When
    timestamp: datetime

    # Where
    ip_address: str
    user_agent: str

    # Outcome
    status: str  # "allowed", "blocked", "error"
    error_message: Optional[str]

    # Consent
    consent_required: bool
    consent_granted: Optional[bool]

    # Result
    result_summary: Optional[str]
    execution_time_ms: Optional[int]
```

**Logging Implementation**:

```python
class ToolInvocationLogger:
    """Log all agent tool invocations"""

    async def log_invocation(
        self,
        invocation: ToolInvocationLog
    ):
        """Log tool invocation to multiple destinations"""

        # 1. Structured log (application log)
        logger.info(
            "Tool invocation",
            extra={
                "event_type": "agent_tool_invocation",
                "user_id": invocation.user_id,
                "tool": invocation.tool_name,
                "status": invocation.status,
                "consent": invocation.consent_granted
            }
        )

        # 2. Audit log (database)
        await self.db.execute(
            """INSERT INTO audit_logs
               (user_id, tool_name, parameters, status, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            [
                invocation.user_id,
                invocation.tool_name,
                json.dumps(invocation.tool_parameters),
                invocation.status,
                invocation.timestamp
            ]
        )

        # 3. Security monitoring (real-time)
        await self.security_monitoring.track(
            event_type="tool_invocation",
            user_id=invocation.user_id,
            tool=invocation.tool_name,
            status=invocation.status
        )

        # 4. SIEM (for analysis)
        await self.siem.send({
            "timestamp": invocation.timestamp.isoformat(),
            "event_type": "agent_tool_invocation",
            "user": {
                "id": invocation.user_id,
                "role": invocation.user_role
            },
            "tool": {
                "name": invocation.tool_name,
                "parameters": self._sanitize_parameters(invocation.tool_parameters)
            },
            "outcome": {
                "status": invocation.status,
                "error": invocation.error_message
            }
        })

    def _sanitize_parameters(self, params: dict) -> dict:
        """Remove sensitive data from parameters"""

        sensitive_keys = {'password', 'token', 'secret', 'key', 'ssn'}

        sanitized = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized
```

---

## Policy Enforcement Middleware

**Complete middleware implementation** (see next section)

---

## Compliance

| Framework | Requirement | Implementation |
|-----------|-------------|----------------|
| **NIST AI RMF** | Govern | ✅ Tool governance |
| **NIST AI RMF** | Map | ✅ Tool mapping to roles |
| **NIST SSDF** | PO.3.1 | ✅ Threat modeling |
| **HIPAA** | §164.312(a)(1) | ✅ Access controls |
| **HIPAA** | §164.312(e)(1) | ✅ Audit logging |
| **SOC 2** | CC6.1 | ✅ Logical access |
| **SOC 2** | CC7.2 | ✅ System monitoring |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-26
**Next Review**: 2026-03-26
**Approved By**: CTO, Security Lead, AI Engineering Lead
