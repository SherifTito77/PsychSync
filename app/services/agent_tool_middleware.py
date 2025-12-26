"""
Agent Tool Policy Enforcement Middleware

This module enforces the agent tool policy including:
- Tool allow-list enforcement
- Role-based access control
- Consent requirements
- Rate limiting
- Audit logging

Usage:
    from app.services.agent_tool_middleware import AgentToolMiddleware

    middleware = AgentToolMiddleware()

    # Check if tool invocation is allowed
    result = await middleware.check_tool_access(
        user_id="user-123",
        tool_name="db_read_query",
        parameters={"query": "SELECT * FROM users LIMIT 10"}
    )

    if result.allowed:
        # Execute tool
        await middleware.execute_tool(result)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from functools import wraps

from fastapi import HTTPException
from pydantic import BaseModel


# ============================================================================
# Tool Definitions
# ============================================================================

class ToolSafetyLevel(Enum):
    """Tool safety levels"""
    SAFE = "safe"
    MEDIUM = "medium"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


class ToolDefinition(BaseModel):
    """Tool definition"""

    name: str
    description: str
    safety_level: ToolSafetyLevel
    allowed_roles: List[str]

    # Constraints
    rate_limit: Optional[int] = None  # per minute
    row_limit: Optional[int] = None
    requires_consent: bool = False
    consent_type: str = "explicit"  # explicit or implicit

    # Validation
    parameter_schema: Optional[Dict] = None

    class Config:
        use_enum_values = True


# Tool Registry (Allow-List)
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    # Database Tools
    "db_read_query": ToolDefinition(
        name="db_read_query",
        description="Execute read-only SQL queries",
        safety_level=ToolSafetyLevel.SAFE,
        allowed_roles=["clinician", "researcher", "admin", "super_admin"],
        rate_limit=10,
        row_limit=1000,
        requires_consent=False
    ),

    "db_anonymized_export": ToolDefinition(
        name="db_anonymized_export",
        description="Export anonymized data for research",
        safety_level=ToolSafetyLevel.MEDIUM,
        allowed_roles=["researcher", "admin", "super_admin"],
        rate_limit=1,  # per hour
        requires_consent=True
    ),

    # Email Tools
    "email_draft_create": ToolDefinition(
        name="email_draft_create",
        description="Create email draft (does not send)",
        safety_level=ToolSafetyLevel.SAFE,
        allowed_roles=["patient", "clinician", "admin", "super_admin"],
        rate_limit=5,
        requires_consent=False
    ),

    "email_send_verified": ToolDefinition(
        name="email_send_verified",
        description="Send pre-verified email templates",
        safety_level=ToolSafetyLevel.MEDIUM,
        allowed_roles=["clinician", "admin", "super_admin"],
        rate_limit=10,
        requires_consent=True,
        consent_type="explicit"
    ),

    # File System Tools
    "file_read_allowed": ToolDefinition(
        name="file_read_allowed",
        description="Read files from allowed directories",
        safety_level=ToolSafetyLevel.SAFE,
        allowed_roles=["clinician", "researcher", "admin", "super_admin"],
        rate_limit=20,
        requires_consent=False
    ),

    "file_write_allowed": ToolDefinition(
        name="file_write_allowed",
        description="Write files to allowed directories",
        safety_level=ToolSafetyLevel.MEDIUM,
        allowed_roles=["clinician", "researcher", "admin", "super_admin"],
        rate_limit=5,
        requires_consent=True  # For writes > 1MB
    ),

    # API Tools
    "api_external_call": ToolDefinition(
        name="api_external_call",
        description="Call approved external APIs",
        safety_level=ToolSafetyLevel.MEDIUM,
        allowed_roles=["researcher", "admin", "super_admin"],
        rate_limit=100,
        requires_consent=False,
        consent_type="implicit"
    ),

    # Shell Tools (BLOCKED)
    "shell_execute": ToolDefinition(
        name="shell_execute",
        description="Execute shell commands (BLOCKED)",
        safety_level=ToolSafetyLevel.BLOCKED,
        allowed_roles=[],  # No roles allowed
        rate_limit=0,
        requires_consent=True
    ),
}


# ============================================================================
# Role Permissions
# ============================================================================

ROLE_PERMISSIONS = {
    "patient": {
        "allowed_tools": ["email_draft_create"],
        "constraints": {
            "email_draft_create": {"max_per_day": 5}
        }
    },

    "clinician": {
        "allowed_tools": [
            "db_read_query",
            "email_draft_create",
            "email_send_verified",
            "file_read_allowed",
            "file_write_allowed"
        ],
        "constraints": {
            "db_read_query": {"row_limit": 100, "require_patient_id": True},
            "email_send_verified": {"templates": ["assessment_invitation", "reminder"]}
        }
    },

    "researcher": {
        "allowed_tools": [
            "db_anonymized_export",
            "file_read_allowed",
            "file_write_allowed",
            "api_external_call"
        ],
        "constraints": {
            "db_anonymized_export": {"requires_irb_approval": True},
            "api_external_call": {"require_approval": True}
        }
    },

    "admin": {
        "allowed_tools": [
            "db_read_query",
            "db_anonymized_export",
            "email_draft_create",
            "email_send_verified",
            "file_read_allowed",
            "file_write_allowed",
            "api_external_call"
        ],
        "constraints": {
            "db_read_query": {"row_limit": 10000}
        }
    },

    "super_admin": {
        "allowed_tools": [
            "db_read_query",
            "db_anonymized_export",
            "email_draft_create",
            "email_send_verified",
            "file_read_allowed",
            "file_write_allowed",
            "api_external_call"
            # Note: shell_execute is blocked even for super_admin (emergency only)
        ],
        "constraints": {}
    }
}


# ============================================================================
# Tool Access Check Result
# ============================================================================

class ToolAccessResult(BaseModel):
    """Result of tool access check"""

    allowed: bool
    reason: Optional[str] = None
    consent_required: bool = False
    consent_request_id: Optional[str] = None

    # Audit info
    user_id: str
    user_role: str
    tool_name: str
    timestamp: datetime = datetime.utcnow()


# ============================================================================
# Middleware Implementation
# ============================================================================

class AgentToolMiddleware:
    """
    Agent tool policy enforcement middleware

    Enforces:
    1. Tool allow-list
    2. Role-based access control
    3. Consent requirements
    4. Rate limiting
    5. Audit logging
    """

    def __init__(self):
        from app.core.redis_client import RedisClient
        from app.services.audit_logger import AuditLogger
        from app.db.session import get_db

        self.redis = RedisClient().get_client()
        self.audit_logger = AuditLogger()
        self.db = get_db()

    async def check_tool_access(
        self,
        user_id: str,
        user_role: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> ToolAccessResult:
        """
        Check if user is allowed to invoke tool

        Args:
            user_id: User requesting access
            user_role: User's role
            tool_name: Tool to invoke
            parameters: Tool parameters

        Returns:
            ToolAccessResult with allow/deny decision
        """

        # 1. Check if tool exists in registry
        if tool_name not in TOOL_REGISTRY:
            return ToolAccessResult(
                allowed=False,
                reason=f"Tool '{tool_name}' not found in registry",
                user_id=user_id,
                user_role=user_role,
                tool_name=tool_name
            )

        tool_def = TOOL_REGISTRY[tool_name]

        # 2. Check if tool is blocked
        if tool_def.safety_level == ToolSafetyLevel.BLOCKED:
            self._log_denied_access(
                user_id, user_role, tool_name,
                "Tool is blocked (shell execution)"
            )
            return ToolAccessResult(
                allowed=False,
                reason=f"Tool '{tool_name}' is blocked for security reasons",
                user_id=user_id,
                user_role=user_role,
                tool_name=tool_name
            )

        # 3. Check role-based access
        if user_role not in tool_def.allowed_roles:
            self._log_denied_access(
                user_id, user_role, tool_name,
                f"User role '{user_role}' not allowed"
            )
            return ToolAccessResult(
                allowed=False,
                reason=f"Role '{user_role}' is not allowed to use tool '{tool_name}'",
                user_id=user_id,
                user_role=user_role,
                tool_name=tool_name
            )

        # 4. Validate parameters against schema
        if tool_def.parameter_schema:
            validation_error = self._validate_parameters(
                parameters, tool_def.parameter_schema
            )
            if validation_error:
                return ToolAccessResult(
                    allowed=False,
                    reason=f"Parameter validation failed: {validation_error}",
                    user_id=user_id,
                    user_role=user_role,
                    tool_name=tool_name
                )

        # 5. Check rate limits
        rate_limit_ok = await self._check_rate_limit(user_id, tool_name, tool_def.rate_limit)
        if not rate_limit_ok:
            return ToolAccessResult(
                allowed=False,
                reason=f"Rate limit exceeded for tool '{tool_name}'",
                user_id=user_id,
                user_role=user_role,
                tool_name=tool_name
            )

        # 6. Check if consent is required
        if tool_def.requires_consent:
            # For now, we'll request consent
            # In production, this would prompt the user via WebSocket
            consent_request_id = f"consent_{user_id}_{tool_name}_{datetime.utcnow().timestamp()}"

            return ToolAccessResult(
                allowed=False,  # Not allowed until consent granted
                reason="Consent required for sensitive action",
                consent_required=True,
                consent_request_id=consent_request_id,
                user_id=user_id,
                user_role=user_role,
                tool_name=tool_name
            )

        # 7. All checks passed
        return ToolAccessResult(
            allowed=True,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name
        )

    async def execute_tool(
        self,
        access_result: ToolAccessResult,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool with logging and monitoring

        Args:
            access_result: Result from check_tool_access
            parameters: Tool parameters
            context: Execution context (IP, user agent, etc.)

        Returns:
            Tool execution result
        """

        start_time = datetime.utcnow()

        try:
            # Log invocation start
            await self._log_invocation_start(
                access_result, parameters, context
            )

            # Execute the tool
            result = await self._execute_tool_impl(
                access_result.tool_name,
                parameters,
                access_result.user_id,
                access_result.user_role
            )

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Log successful invocation
            await self._log_invocation_complete(
                access_result, parameters, result, execution_time, None
            )

            return {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time
            }

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Log failed invocation
            await self._log_invocation_complete(
                access_result, parameters, None, execution_time, str(e)
            )

            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time
            }

    async def grant_consent(
        self,
        consent_request_id: str,
        granted: bool
    ) -> bool:
        """
        Grant/deny consent for tool invocation

        Args:
            consent_request_id: Consent request ID
            granted: Whether consent was granted

        Returns:
            True if consent recorded successfully
        """

        key = f"consent:{consent_request_id}"

        # Store consent result in Redis (expires in 5 minutes)
        await self.redis.setex(
            key,
            300,  # 5 minutes
            json.dumps({"granted": granted, "timestamp": datetime.utcnow().isoformat()})
        )

        return True

    async def check_consent(
        self,
        consent_request_id: str
    ) -> Optional[bool]:
        """
        Check if consent was granted

        Args:
            consent_request_id: Consent request ID

        Returns:
            True if granted, False if denied, None if pending
        """

        key = f"consent:{consent_request_id}"

        result = await self.redis.get(key)

        if not result:
            return None  # Pending

        data = json.loads(result)
        return data.get("granted")

    # ========================================================================
    # Private Methods
    # ========================================================================

    def _validate_parameters(
        self,
        parameters: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Optional[str]:
        """Validate parameters against schema"""

        # Simplified validation - in production, use pydantic/jsonschema
        for field_name, field_schema in schema.items():
            if field_name not in parameters:
                if field_schema.get("required", False):
                    return f"Missing required parameter: {field_name}"

            # Type validation
            if field_name in parameters:
                expected_type = field_schema.get("type")
                if expected_type == "string" and not isinstance(parameters[field_name], str):
                    return f"Parameter '{field_name}' must be a string"
                elif expected_type == "integer" and not isinstance(parameters[field_name], int):
                    return f"Parameter '{field_name}' must be an integer"

        return None  # Validation passed

    async def _check_rate_limit(
        self,
        user_id: str,
        tool_name: str,
        rate_limit: Optional[int]
    ) -> bool:
        """Check if user is within rate limit"""

        if rate_limit is None:
            return True  # No limit

        key = f"tool_rate_limit:{tool_name}:{user_id}"

        # Get current count
        current = await self.redis.get(key)

        if current is None:
            # First invocation in window
            await self.redis.setex(key, 60, "1")  # 60 second window
            return True

        count = int(current)

        if count >= rate_limit:
            # Rate limit exceeded
            return False

        # Increment counter
        await self.redis.incr(key)
        return True

    async def _execute_tool_impl(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: str,
        user_role: str
    ) -> Any:
        """Execute the actual tool implementation"""

        # Import tool implementations
        from app.services.agent_tools import (
            db_read_query_impl,
            db_anonymized_export_impl,
            email_draft_create_impl,
            email_send_verified_impl,
            file_read_allowed_impl,
            file_write_allowed_impl,
            api_external_call_impl
        )

        # Map tool names to implementations
        tool_implementations = {
            "db_read_query": db_read_query_impl,
            "db_anonymized_export": db_anonymized_export_impl,
            "email_draft_create": email_draft_create_impl,
            "email_send_verified": email_send_verified_impl,
            "file_read_allowed": file_read_allowed_impl,
            "file_write_allowed": file_write_allowed_impl,
            "api_external_call": api_external_call_impl,
        }

        impl = tool_implementations.get(tool_name)

        if impl is None:
            raise ValueError(f"No implementation found for tool: {tool_name}")

        # Execute with user context
        result = await impl(parameters, user_id, user_role)

        return result

    async def _log_invocation_start(
        self,
        access_result: ToolAccessResult,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Log tool invocation start"""

        await self.audit_logger.log_security_event(
            event_type="AGENT_TOOL_INVOCATION_START",
            user_id=access_result.user_id,
            role=access_result.user_role,
            operation="invoke",
            resource_type="agent_tool",
            resource_id=access_result.tool_name,
            fields_accessed=list(parameters.keys()),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            service="agent_orchestration",
            status="started"
        )

    async def _log_invocation_complete(
        self,
        access_result: ToolAccessResult,
        parameters: Dict[str, Any],
        result: Any,
        execution_time_ms: float,
        error: Optional[str]
    ):
        """Log tool invocation completion"""

        status = "success" if error is None else "error"

        await self.audit_logger.log_security_event(
            event_type="AGENT_TOOL_INVOCATION_COMPLETE",
            user_id=access_result.user_id,
            role=access_result.user_role,
            operation="invoke",
            resource_type="agent_tool",
            resource_id=access_result.tool_name,
            fields_accessed=list(parameters.keys()),
            ip_address=None,  # Already logged in start
            user_agent=None,
            service="agent_orchestration",
            status=status,
            error_code=None if error is None else "TOOL_EXECUTION_ERROR",
            failure_reason=error
        )

    def _log_denied_access(
        self,
        user_id: str,
        user_role: str,
        tool_name: str,
        reason: str
    ):
        """Log denied tool access"""

        # This would use the audit logger in production
        pass


# ============================================================================
# Decorators for Easy Use
# ============================================================================

def require_tool_access(middleware: AgentToolMiddleware):
    """
    Decorator for tool functions that enforces access control

    Usage:
        @require_tool_access(middleware)
        async def my_tool(parameters: dict, user_id: str, user_role: str):
            # Tool implementation
            pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user info from kwargs
            user_id = kwargs.get('user_id')
            user_role = kwargs.get('user_role')
            tool_name = kwargs.get('tool_name', func.__name__)
            parameters = kwargs.get('parameters', {})

            # Check access
            access_result = await middleware.check_tool_access(
                user_id=user_id,
                user_role=user_role,
                tool_name=tool_name,
                parameters=parameters
            )

            if not access_result.allowed:
                raise HTTPException(
                    status_code=403,
                    detail=access_result.reason
                )

            # Call original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
