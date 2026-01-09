"""
Security Log Schemas

Defines structured schemas for all security event types following
the MITRE ATT&CK and NIST logging frameworks.
"""

from datetime import datetime
from enum import Enum
from typing import Any
import uuid

from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Types of security events"""

    # Authentication & Authorization
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    AUTH_MFA_DISABLED = "auth.mfa_disabled"
    AUTH_SESSION_CREATED = "auth.session_created"
    AUTH_SESSION_DESTROYED = "auth.session_destroyed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"

    # Privilege Changes
    PRIV_ROLE_GRANTED = "privilege.role_granted"
    PRIV_ROLE_REVOKED = "privilege.role_revoked"
    PRIV_PERMISSION_GRANTED = "privilege.permission_granted"
    PRIV_PERMISSION_REVOKED = "privilege.permission_revoked"
    PRIV_ESCALATION = "privilege.escalation"
    PRIV_DEESCALATION = "privilege.deescalation"

    # Tool/Agent Operations
    TOOL_INVOCATION = "tool.invocation"
    TOOL_INVOCATION_FAILED = "tool.invocation_failed"
    TOOL_INVOCATION_BLOCKED = "tool.invocation_blocked"
    AGENT_EXECUTION = "agent.execution"
    AGENT_EXECUTION_FAILED = "agent.execution_failed"

    # Data Access
    DATA_ACCESS_READ = "data.access.read"
    DATA_ACCESS_WRITE = "data.access.write"
    DATA_ACCESS_DELETE = "data.access.delete"
    DATA_EXPORT = "data.export"
    DATA_BULK_ACCESS = "data.bulk_access"
    DATA_SENSITIVE_ACCESS = "data.sensitive_access"

    # Model/AI Operations
    MODEL_PROMPT = "model.prompt"
    MODEL_RESPONSE = "model.response"
    MODEL_INJECTION_ATTEMPT = "model.injection_attempt"
    MODEL_ANOMALY_DETECTED = "model.anomaly_detected"
    MODEL_SAFETY_VIOLATION = "model.safety_violation"

    # System Events
    SYSTEM_ERROR = "system.error"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CONFIG_CHANGE = "system.config_change"


class EventSeverity(str, Enum):
    """Severity levels for security events"""

    CRITICAL = "critical"  # Immediate response required
    HIGH = "high"  # Urgent attention needed
    MEDIUM = "medium"  # Requires investigation
    LOW = "low"  # Informational
    INFO = "info"  # Normal operation


class SecurityEvent(BaseModel):
    """
    Base security event with all common fields.

    Follows NIST Special Publication 800-92 Guide to Computer Security Log Management
    and CloudAudit format.
    """

    # Event identification
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    severity: EventSeverity
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Actor information
    actor_user_id: str | None = None
    actor_username: str | None = None
    actor_role: str | None = None
    actor_ip_address: str | None = None
    actor_user_agent: str | None = None
    actor_session_id: str | None = None

    # Resource information
    resource_type: str | None = None  # e.g., "user", "assessment", "team"
    resource_id: str | None = None
    resource_path: str | None = None  # URL or file path

    # Event details
    description: str
    status: str = "success"  # success, failure, partial
    outcome: str | None = None  # Human-readable outcome

    # Additional context
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    # Integrity verification (hash-chain)
    previous_hash: str | None = None
    current_hash: str | None = None

    # Detection flags
    is_suspicious: bool = False
    detection_rules_matched: list[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator("tags")
    def add_default_tags(cls, v, values):
        """Add default tags based on event type and severity"""
        event_type = values.get("event_type")
        severity = values.get("severity")

        tags = list(v)  # Copy

        if event_type:
            category = event_type.value.split(".")[0]
            tags.append(f"category:{category}")

        if severity:
            tags.append(f"severity:{severity.value}")

        return tags


class AuthEvent(SecurityEvent):
    """
    Authentication and authorization event.

    Includes MFA status, session details, and authentication method.
    """

    auth_method: str | None = None  # password, oauth, saml, mfa
    mfa_verified: bool = False
    mfa_method: str | None = None  # totp, sms, email, hardware_key

    # Session information
    session_id: str | None = None
    session_expires: datetime | None = None

    # Failure details (if applicable)
    failure_reason: str | None = None  # invalid_credentials, account_locked, etc.

    # Geo-location (if available)
    country: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Risk indicators
    is_new_device: bool = False
    is_new_location: bool = False
    is_anomalous: bool = False
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)


class PrivilegeChangeEvent(SecurityEvent):
    """
    Privilege change event.

    Tracks all changes to user roles, permissions, and access levels.
    """

    # Target user
    target_user_id: str
    target_username: str | None = None
    target_old_role: str | None = None
    target_new_role: str | None = None

    # Change details
    permission_name: str | None = None
    permission_resource: str | None = None
    permission_action: str | None = None  # grant, revoke, modify

    # Justification
    reason: str | None = None
    approval_ticket: str | None = None
    approved_by: str | None = None

    # Scope
    scope: str = "user"  # user, team, organization, global
    organization_id: str | None = None
    team_id: str | None = None


class ToolInvocationEvent(SecurityEvent):
    """
    Tool/agent invocation event.

    Logs all calls to external tools, APIs, and agent systems.
    """

    # Tool information
    tool_name: str
    tool_version: str | None = None
    tool_category: str | None = None  # llm, database, api, filesystem, etc.

    # Invocation details
    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parameters: dict[str, Any] = Field(default_factory=dict)

    # Execution results
    execution_time_ms: int | None = None
    result_count: int | None = None
    result_size_bytes: int | None = None

    # Error details (if applicable)
    error_type: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None

    # Agent context (if applicable)
    agent_id: str | None = None
    agent_type: str | None = None  # claude, gpt, custom_agent
    conversation_id: str | None = None
    turn_id: str | None = None

    # Detection flags
    is_abnormal: bool = False
    abnormality_reason: str | None = None


class DataAccessEvent(SecurityEvent):
    """
    Data access event.

    Tracks all reads, writes, and deletions of sensitive data.
    """

    # Data information
    data_type: str  # user_profile, assessment_results, team_data, etc.
    data_classification: str  # public, internal, confidential, restricted
    record_count: int | None = None

    # Access details
    access_method: str  # api, webui, cli, integration
    query_type: str | None = None  # select, insert, update, delete
    query_pattern: str | None = None  # For detection (e.g., "SELECT * FROM users")

    # Filter details (what data was accessed)
    filters: dict[str, Any] = Field(default_factory=dict)
    fields_accessed: list[str] = Field(default_factory=list)

    # Export details (if applicable)
    export_format: str | None = None  # csv, json, pdf, etc.
    export_destination: str | None = None  # email, s3, local, etc.
    export_size_bytes: int | None = None
    export_record_count: int | None = None

    # Bulk access indicators
    is_bulk_access: bool = False
    bulk_threshold_exceeded: bool = False


class ModelEvent(SecurityEvent):
    """
    Model/AI operation event.

    Logs prompts, responses, and security-related model interactions.
    """

    # Model information
    model_name: str
    model_version: str | None = None
    model_provider: str | None = None  # anthropic, openai, custom

    # Prompt details (redacted)
    prompt_length: int
    prompt_tokens: int | None = None
    prompt_hash: str | None = None  # Hash of original prompt for integrity

    # Response details (redacted)
    response_length: int | None = None
    response_tokens: int | None = None
    response_hash: str | None = None

    # Redacted content (for audit, not raw)
    prompt_preview: str | None = None  # First 100 chars, redacted
    response_preview: str | None = None

    # Safety and security
    safety_score: float | None = Field(default=None, ge=0.0, le=1.0)
    flagged_content: list[str] = Field(default_factory=list)
    injection_indicators: list[str] = Field(default_factory=list)

    # Tool use (if applicable)
    tools_used: list[str] = Field(default_factory=list)
    tool_results_count: int = 0

    # Performance
    latency_ms: int | None = None
    cache_hit: bool = False


class SecurityLogBatch(BaseModel):
    """
    Batch of security events for efficient storage/transmission.
    """

    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    events: list[SecurityEvent]
    batch_timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_count: int = Field(alias="count")

    # Integrity
    batch_hash: str | None = None
    signature: str | None = None  # Cryptographic signature

    # Transmission
    transmitted: bool = False
    transmitted_at: datetime | None = None
    transmission_attempts: int = 0

    @validator("event_count")
    def calculate_count(cls, v, values):
        """Calculate event count from events list"""
        events = values.get("events", [])
        return len(events)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
