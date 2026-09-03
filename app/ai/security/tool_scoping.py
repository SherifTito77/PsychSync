"""
Tool/Agent Scoping Framework (OWASP LLM Top 10: LLM06)

Implements least privilege access control for AI tools and agents.
Prevents over-privileged AI operations by enforcing scoping rules and allowlists.

Key Features:
- Tool allowlists/denylists
- Permission levels
- Operation auditing
- Human approval workflows
- Rate limiting per tool
- Usage monitoring

Resources:
- OWASP LLM Top 10 LLM06: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- Principle of Least Privilege: https://en.wikipedia.org/wiki/Principle_of_least_privilege
"""

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class PermissionLevel(Enum):
    """Permission levels for AI tools"""

    NONE = "none"  # No access
    READ = "read"  # Read-only access
    WRITE = "write"  # Write access
    EXECUTE = "execute"  # Execute operations
    ADMIN = "admin"  # Full administrative access


class ToolCategory(Enum):
    """Categories of AI tools"""

    CLINICAL = "clinical"  # Clinical assessment tools
    ANALYTICS = "analytics"  # Data analytics tools
    COMMUNICATION = "communication"  # Communication tools
    FILE_OPERATIONS = "file_operations"  # File system operations
    DATABASE = "database"  # Database operations
    NETWORK = "network"  # Network operations
    SYSTEM = "system"  # System-level operations
    INTEGRATION = "integration"  # Third-party integrations


@dataclass
class ToolDefinition:
    """Definition of an AI tool/operation"""

    name: str
    category: ToolCategory
    description: str
    required_permission: PermissionLevel
    requires_human_approval: bool = False
    rate_limit: Optional[int] = None  # Max calls per minute
    allowed_contexts: Set[str] = field(default_factory=set)
    denied_contexts: Set[str] = field(default_factory=set)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolInvocation:
    """Record of a tool invocation"""

    tool_name: str
    timestamp: datetime
    user_id: str
    context: str
    parameters: Dict[str, Any]
    approved: bool
    approver_id: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class ToolScopeManager:
    """
    Manages tool scoping and permissions

    Enforces least privilege by:
    1. Maintaining allowlists/denylists
    2. Checking permissions before execution
    3. Requiring approval for sensitive operations
    4. Auditing all tool usage
    5. Enforcing rate limits
    """

    # Predefined tools with scoping rules
    PREDEFINED_TOOLS = {
        "clinical_assessment": ToolDefinition(
            name="clinical_assessment",
            category=ToolCategory.CLINICAL,
            description="Analyze clinical assessment responses",
            required_permission=PermissionLevel.READ,
            requires_human_approval=False,
            allowed_contexts={"clinical", "assessment"},
        ),
        "sentiment_analysis": ToolDefinition(
            name="sentiment_analysis",
            category=ToolCategory.ANALYTICS,
            description="Analyze sentiment in text",
            required_permission=PermissionLevel.READ,
            requires_human_approval=False,
        ),
        "personality_profiling": ToolDefinition(
            name="personality_profiling",
            category=ToolCategory.ANALYTICS,
            description="Generate personality profile",
            required_permission=PermissionLevel.READ,
            requires_human_approval=False,
        ),
        "file_read": ToolDefinition(
            name="file_read",
            category=ToolCategory.FILE_OPERATIONS,
            description="Read file contents",
            required_permission=PermissionLevel.READ,
            requires_human_approval=True,
            allowed_contexts={"assessment_results", "reports"},
            denied_contexts={"credentials", "keys", "secrets"},
        ),
        "file_write": ToolDefinition(
            name="file_write",
            category=ToolCategory.FILE_OPERATIONS,
            description="Write file contents",
            required_permission=PermissionLevel.WRITE,
            requires_human_approval=True,
            allowed_contexts={"reports", "exports"},
            denied_contexts={"config", "credentials"},
        ),
        "database_query": ToolDefinition(
            name="database_query",
            category=ToolCategory.DATABASE,
            description="Execute database query",
            required_permission=PermissionLevel.READ,
            requires_human_approval=True,
            rate_limit=10,
        ),
        "database_write": ToolDefinition(
            name="database_write",
            category=ToolCategory.DATABASE,
            description="Write to database",
            required_permission=PermissionLevel.WRITE,
            requires_human_approval=True,
            rate_limit=5,
        ),
        "send_notification": ToolDefinition(
            name="send_notification",
            category=ToolCategory.COMMUNICATION,
            description="Send user notification",
            required_permission=PermissionLevel.WRITE,
            requires_human_approval=False,
            rate_limit=20,
        ),
        "api_integration": ToolDefinition(
            name="api_integration",
            category=ToolCategory.INTEGRATION,
            description="Call external API",
            required_permission=PermissionLevel.EXECUTE,
            requires_human_approval=True,
        ),
        "system_command": ToolDefinition(
            name="system_command",
            category=ToolCategory.SYSTEM,
            description="Execute system command",
            required_permission=PermissionLevel.ADMIN,
            requires_human_approval=True,
            rate_limit=2,
        ),
    }

    def __init__(self):
        """Initialize tool scope manager"""
        self.tools: Dict[str, ToolDefinition] = {}
        self.user_permissions: Dict[str, Dict[str, PermissionLevel]] = {}
        self.invocation_log: List[ToolInvocation] = []
        self.rate_limit_tracker: Dict[str, List[datetime]] = {}
        self.lock = threading.Lock()

        # Load predefined tools
        self.tools.update(self.PREDEFINED_TOOLS)

    def register_tool(self, tool: ToolDefinition) -> None:
        """
        Register a new tool definition

        Args:
            tool: Tool definition to register
        """
        with self.lock:
            self.tools[tool.name] = tool

    def grant_permission(
        self, user_id: str, tool_name: str, permission: PermissionLevel
    ) -> None:
        """
        Grant permission to user for tool

        Args:
            user_id: User identifier
            tool_name: Tool name
            permission: Permission level to grant
        """
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = {}

        self.user_permissions[user_id][tool_name] = permission

    def revoke_permission(self, user_id: str, tool_name: str) -> None:
        """
        Revoke user's permission for tool

        Args:
            user_id: User identifier
            tool_name: Tool name
        """
        if user_id in self.user_permissions:
            self.user_permissions[user_id].pop(tool_name, None)

    def check_permission(
        self, user_id: str, tool_name: str, context: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has permission to use tool

        Args:
            user_id: User identifier
            tool_name: Tool to check
            context: Optional context for allowlist/denylist check

        Returns:
            Tuple of (has_permission, error_message)
        """
        # Check if tool exists
        if tool_name not in self.tools:
            return False, f"Tool '{tool_name}' not found"

        tool = self.tools[tool_name]

        # Check user's permission level
        user_perms = self.user_permissions.get(user_id, {})
        user_perm_level = user_perms.get(tool_name, PermissionLevel.NONE)

        # Compare permission levels (higher enum value = higher permission)
        if user_perm_level.value < tool.required_permission.value:
            return False, (
                f"Insufficient permission. "
                f"Required: {tool.required_permission.value}, "
                f"User has: {user_perm_level.value}"
            )

        # Check context allowlist
        if context and tool.allowed_contexts:
            if context not in tool.allowed_contexts:
                return False, (
                    f"Context '{context}' not in allowed contexts: "
                    f"{tool.allowed_contexts}"
                )

        # Check context denylist
        if context and tool.denied_contexts:
            if context in tool.denied_contexts:
                return False, (f"Context '{context}' is explicitly denied")

        return True, None

    def check_rate_limit(
        self, user_id: str, tool_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit for tool

        Args:
            user_id: User identifier
            tool_name: Tool to check

        Returns:
            Tuple of (within_limit, error_message)
        """
        tool = self.tools.get(tool_name)
        if not tool or not tool.rate_limit:
            return True, None

        now = datetime.now(timezone.utc)
        key = f"{user_id}:{tool_name}"

        with self.lock:
            # Clean old entries (older than 1 minute)
            if key in self.rate_limit_tracker:
                self.rate_limit_tracker[key] = [
                    ts
                    for ts in self.rate_limit_tracker[key]
                    if (now - ts).total_seconds() < 60
                ]
            else:
                self.rate_limit_tracker[key] = []

            # Check rate limit
            recent_calls = len(self.rate_limit_tracker[key])

            if recent_calls >= tool.rate_limit:
                return False, (
                    f"Rate limit exceeded. " f"Max {tool.rate_limit} calls per minute."
                )

            # Add current call
            self.rate_limit_tracker[key].append(now)

        return True, None

    def requires_approval(self, tool_name: str) -> bool:
        """
        Check if tool requires human approval

        Args:
            tool_name: Tool name

        Returns:
            True if approval required
        """
        tool = self.tools.get(tool_name)
        return tool.requires_human_approval if tool else False

    def invoke_tool(
        self,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[str] = None,
        approver_id: Optional[str] = None,
        tool_function: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Invoke a tool with full permission checking

        Args:
            user_id: User invoking the tool
            tool_name: Tool to invoke
            parameters: Tool parameters
            context: Optional context
            approver_id: Approver user ID (if approval required)
            tool_function: Actual function to execute

        Returns:
            Result dictionary
        """
        result = {
            "success": False,
            "error": None,
            "output": None,
            "invocation_id": None,
        }

        # Check permission
        has_perm, perm_error = self.check_permission(user_id, tool_name, context)
        if not has_perm:
            result["error"] = perm_error
            self._log_invocation(
                tool_name,
                user_id,
                context,
                parameters,
                approved=False,
                success=False,
                error=perm_error,
            )
            return result

        # Check rate limit
        within_limit, rate_error = self.check_rate_limit(user_id, tool_name)
        if not within_limit:
            result["error"] = rate_error
            self._log_invocation(
                tool_name,
                user_id,
                context,
                parameters,
                approved=False,
                success=False,
                error=rate_error,
            )
            return result

        # Check if approval required
        if self.requires_approval(tool_name):
            if not approver_id:
                result["error"] = (
                    f"Tool '{tool_name}' requires human approval. "
                    f"Please provide approver_id."
                )
                self._log_invocation(
                    tool_name,
                    user_id,
                    context,
                    parameters,
                    approved=False,
                    success=False,
                    error=result["error"],
                )
                return result

            # Check approver has admin permission
            has_admin, _ = self.check_permission(approver_id, tool_name, context)
            if not has_admin:
                result["error"] = "Approver lacks required permissions"
                self._log_invocation(
                    tool_name,
                    user_id,
                    context,
                    parameters,
                    approved=False,
                    success=False,
                    error=result["error"],
                )
                return result

        # Execute tool function
        try:
            if tool_function:
                output = tool_function(**parameters)
                result["output"] = output
                result["success"] = True

                self._log_invocation(
                    tool_name, user_id, context, parameters, approved=True, success=True
                )

            else:
                result["error"] = "No tool function provided"

        except Exception as e:
            result["error"] = str(e)
            self._log_invocation(
                tool_name,
                user_id,
                context,
                parameters,
                approved=True,
                success=False,
                error=str(e),
            )

        return result

    def _log_invocation(
        self,
        tool_name: str,
        user_id: str,
        context: Optional[str],
        parameters: Dict[str, Any],
        approved: bool,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log tool invocation"""
        invocation = ToolInvocation(
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            context=context or "",
            parameters=parameters,
            approved=approved,
            success=success,
            error=error,
        )

        with self.lock:
            self.invocation_log.append(invocation)

    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ToolInvocation]:
        """
        Get audit log with optional filters

        Args:
            user_id: Filter by user
            tool_name: Filter by tool
            limit: Max results

        Returns:
            Filtered audit log
        """
        with self.lock:
            log = self.invocation_log

            if user_id:
                log = [inv for inv in log if inv.user_id == user_id]

            if tool_name:
                log = [inv for inv in log if inv.tool_name == tool_name]

            # Return most recent first
            return sorted(log, key=lambda x: x.timestamp, reverse=True)[:limit]

    def export_audit_log(self, output_file: str) -> None:
        """
        Export audit log to JSON file

        Args:
            output_file: Output file path
        """
        with self.lock:
            log_data = [
                {
                    "tool_name": inv.tool_name,
                    "timestamp": inv.timestamp.isoformat(),
                    "user_id": inv.user_id,
                    "context": inv.context,
                    "parameters": inv.parameters,
                    "approved": inv.approved,
                    "success": inv.success,
                    "error": inv.error,
                }
                for inv in self.invocation_log
            ]

            with open(output_file, "w") as f:
                json.dump(log_data, f, indent=2)


# Singleton instance
_tool_scope_manager = None


def get_tool_scope_manager() -> ToolScopeManager:
    """Get global tool scope manager instance"""
    global _tool_scope_manager
    if _tool_scope_manager is None:
        _tool_scope_manager = ToolScopeManager()
    return _tool_scope_manager


# Example usage and testing
if __name__ == "__main__":
    print("Tool Scoping Framework Demo")
    print("=" * 60)

    # Initialize manager
    manager = ToolScopeManager()

    # Grant permissions
    print("\n1. Granting Permissions")
    print("-" * 60)

    manager.grant_permission("user_123", "sentiment_analysis", PermissionLevel.READ)
    manager.grant_permission("user_123", "file_read", PermissionLevel.READ)
    manager.grant_permission("admin_456", "system_command", PermissionLevel.ADMIN)

    print("✓ Granted permissions to user_123 and admin_456")

    # Test permission checks
    print("\n2. Testing Permission Checks")
    print("-" * 60)

    # Allowed
    has_perm, error = manager.check_permission("user_123", "sentiment_analysis")
    print(f"user_123 -> sentiment_analysis: {has_perm} ({error or 'Allowed'})")

    # Denied (no permission)
    has_perm, error = manager.check_permission("user_123", "database_write")
    print(f"user_123 -> database_write: {has_perm} ({error or 'Allowed'})")

    # Denied (context not in allowlist)
    has_perm, error = manager.check_permission(
        "user_123", "file_read", context="credentials"
    )
    print(
        f"user_123 -> file_read (credentials context): {has_perm} ({error or 'Allowed'})"
    )

    # Test tool invocation with approval
    print("\n3. Testing Tool Invocation with Approval")
    print("-" * 60)

    def mock_read_file(filepath: str) -> str:
        return f"Contents of {filepath}"

    # Without approval (should fail)
    result = manager.invoke_tool(
        user_id="user_123",
        tool_name="file_read",
        parameters={"filepath": "results.json"},
        context="reports",
        tool_function=mock_read_file,
    )
    print(f"Invoke file_read (no approval): {result['success']}")
    print(f"  Error: {result['error']}")

    # With approval (should succeed)
    result = manager.invoke_tool(
        user_id="user_123",
        tool_name="file_read",
        parameters={"filepath": "results.json"},
        context="reports",
        approver_id="admin_456",
        tool_function=mock_read_file,
    )
    print(f"Invoke file_read (with approval): {result['success']}")
    print(f"  Output: {result['output']}")

    # Test rate limiting
    print("\n4. Testing Rate Limiting")
    print("-" * 60)

    # system_command has rate limit of 2 per minute
    manager.grant_permission("user_789", "system_command", PermissionLevel.ADMIN)

    for i in range(4):
        result = manager.invoke_tool(
            user_id="user_789",
            tool_name="system_command",
            parameters={"command": "echo test"},
            approver_id="admin_456",
            tool_function=lambda **kwargs: f"Executed: {kwargs['command']}",
        )
        print(f"Call {i+1}: {result['success']} ({result.get('error', 'OK')})")

    # Audit log
    print("\n5. Audit Log")
    print("-" * 60)

    log = manager.get_audit_log(limit=5)
    print(f"Recent invocations: {len(log)}")
    for inv in log:
        status = "✓" if inv.success else "✗"
        print(f"  {status} {inv.tool_name} by {inv.user_id} at {inv.timestamp}")

    print("\n" + "=" * 60)
    print("Demo complete!")
