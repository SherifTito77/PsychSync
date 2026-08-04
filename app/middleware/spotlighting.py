#!/usr/bin/env python3
"""
Spotlighting Middleware for LLM Security

Implements content spotlighting to mark, track, and validate untrusted content
as it flows through LLM processing pipelines. This is a critical defense-in-depth
measure that:

1. Wraps untrusted content with explicit markers
2. Tracks content provenance (user, system, external)
3. Validates LLM outputs to prevent malicious transformations
4. Enforces tool allow-listing for agent operations
5. Requires human approval for sensitive operations

Based on NIST AI RMF and OWASP LLM Top 10 recommendations.

Author: Security Team
Version: 1.0
Date: 2025-12-27
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class ContentSource(Enum):
    """Source of content"""

    USER = "user"  # Direct user input
    EXTERNAL_API = "external_api"  # External API responses
    DATABASE = "database"  # Database queries
    LLM_OUTPUT = "llm_output"  # LLM generated content
    SYSTEM = "system"  # System-generated content
    FILE = "file"  # File uploads


class TrustLevel(Enum):
    """Trust level for content"""

    UNTRUSTED = "untrusted"  # Must be validated/sanitized
    PARTIAL = "partial"  # Some validation performed
    TRUSTED = "trusted"  # Fully validated


class SpotlightingMode(Enum):
    """Spotlighting mode"""

    STRICT = "strict"  # All content must be explicitly marked
    PERMISSIVE = "permissive"  # Auto-mark unmarked content as untrusted
    DISABLED = "disabled"  # No spotlighting (testing only)


@dataclass
class SpotlightedContent:
    """Content with security metadata"""

    content: str
    source: ContentSource
    trust_level: TrustLevel
    content_hash: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    spotlight_markers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "source": self.source.value,
            "trust_level": self.trust_level.value,
            "content_hash": self.content_hash,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "spotlight_markers": self.spotlight_markers,
        }


class SpotlightingEngine:
    """
    Core spotlighting engine for marking and tracking untrusted content.
    """

    # Spotlight markers (XML-like for easy parsing)
    MARKER_START = "<!-- UNTRUSTED_CONTENT_START -->"
    MARKER_END = "<!-- UNTRUSTED_CONTENT_END -->"

    # Special markers for different sources
    SOURCE_MARKERS = {
        ContentSource.USER: "USER_INPUT",
        ContentSource.EXTERNAL_API: "EXTERNAL_API",
        ContentSource.DATABASE: "DATABASE",
        ContentSource.LLM_OUTPUT: "LLM_OUTPUT",
        ContentSource.SYSTEM: "SYSTEM",
        ContentSource.FILE: "FILE_UPLOAD",
    }

    # Dangerous patterns to detect in LLM outputs
    DANGEROUS_PATTERNS = [
        # Attempting to execute code
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        # SQL injection keywords
        r";\s*DROP\s+TABLE",
        r";\s*DELETE\s+FROM",
        r";\s*INSERT\s+INTO",
        r";\s*UPDATE\s+\w+\s+SET",
        r"UNION\s+SELECT",
        # Path traversal
        r"\.\.[/\\]",
        # Command injection
        r"[;&|`$]",
        # Template injection
        r"\{\{.*?\}\}",
        r"\${.*?}",
        # Attempting to bypass spotlighting
        r"(ignore|remove|strip).*(spotlight|marker|comment)",
    ]

    def __init__(
        self,
        mode: SpotlightingMode = SpotlightingMode.STRICT,
        enable_hash_verification: bool = True,
        max_content_size: int = 100000,
    ):
        """
        Initialize spotlighting engine.

        Args:
            mode: Spotlighting mode
            enable_hash_verification: Enable content hash verification
            max_content_size: Maximum content size to process
        """
        self.mode = mode
        self.enable_hash_verification = enable_hash_verification
        self.max_content_size = max_content_size

        # Compile regex patterns
        self.dangerous_pattern_regex = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.DANGEROUS_PATTERNS
        ]

        logger.info(f"SpotlightingEngine initialized in {mode.value} mode")

    def spotlight_content(
        self,
        content: str,
        source: ContentSource,
        trust_level: TrustLevel = TrustLevel.UNTRUSTED,
        metadata: dict[str, Any] | None = None,
    ) -> SpotlightedContent:
        """
        Mark content with spotlighting for tracking.

        Args:
            content: Content to spotlight
            source: Source of content
            trust_level: Trust level
            metadata: Additional metadata

        Returns:
            SpotlightedContent with security markers
        """
        if len(content) > self.max_content_size:
            logger.warning(
                f"Content exceeds max size: {len(content)} > {self.max_content_size}"
            )
            content = content[: self.max_content_size]

        # Generate content hash for integrity checking
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Create spotlight markers
        source_marker = self.SOURCE_MARKERS[source]
        markers = {
            "start": f"{self.MARKER_START}\n<!-- SOURCE: {source_marker} -->\n<!-- TRUST: {trust_level.value} -->\n<!-- HASH: {content_hash} -->",
            "end": f"\n{self.MARKER_END}",
        }

        # Add metadata markers
        if metadata:
            for key, value in metadata.items():
                markers[key] = f"<!-- {key.upper()}: {value} -->"

        return SpotlightedContent(
            content=content,
            source=source,
            trust_level=trust_level,
            content_hash=content_hash,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            spotlight_markers=markers,
        )

    def wrap_content(self, content: str, spotlighted: SpotlightedContent) -> str:
        """
        Wrap content with spotlighting markers.

        Returns content formatted as:
        <!-- UNTRUSTED_CONTENT_START -->
        <!-- SOURCE: USER_INPUT -->
        <!-- TRUST: untrusted -->
        <!-- HASH: abc123 -->
        [content here]
        <!-- UNTRUSTED_CONTENT_END -->
        """
        marker_start = spotlighted.spotlight_markers.get("start", "")
        marker_end = spotlighted.spotlight_markers.get("end", "")

        metadata_str = ""
        for key, value in spotlighted.spotlight_markers.items():
            if key not in ["start", "end"]:
                metadata_str += f"\n{value}"

        return f"{marker_start}{metadata_str}\n{content}\n{marker_end}"

    def unwrap_content(self, wrapped_content: str) -> str:
        """
        Remove spotlighting markers from content.

        Args:
            wrapped_content: Content with markers

        Returns:
            Clean content without markers
        """
        # Remove spotlight markers
        content = wrapped_content

        # Remove start/end markers
        content = re.sub(
            rf"{re.escape(self.MARKER_START)}.*?{re.escape(self.MARKER_END)}\s*",
            lambda m: self._extract_content_from_markers(m.group(0)),
            content,
            flags=re.DOTALL,
        )

        # Remove any remaining comment markers
        content = re.sub(r"<!--.*?-->\s*", "", content, flags=re.DOTALL)

        return content.strip()

    def _extract_content_from_markers(self, marked_block: str) -> str:
        """Extract actual content from spotlighted block"""
        lines = marked_block.split("\n")
        content_lines = []

        in_markers = True
        for line in lines:
            if self.MARKER_START in line or self.MARKER_END in line:
                continue
            if line.strip().startswith("<!--"):
                continue
            if in_markers and not line.strip().startswith("<!--"):
                in_markers = False
            if not in_markers:
                content_lines.append(line)

        return "\n".join(content_lines)

    def validate_llm_output(
        self, output: str, input_content: SpotlightedContent | None = None
    ) -> tuple[bool, list[str]]:
        """
        Validate LLM output for security issues.

        Args:
            output: LLM output to validate
            input_content: Original input (for comparison)

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for dangerous patterns
        for pattern in self.dangerous_pattern_regex:
            matches = pattern.findall(output)
            if matches:
                issues.append(f"Dangerous pattern detected: {pattern.pattern[:50]}")

        # Check if output tries to replicate input (potential prompt injection)
        if input_content:
            if self._contains_input_leakage(output, input_content.content):
                issues.append("Potential input leakage detected")

        # Check for spotlight marker manipulation
        if self._has_marker_manipulation(output):
            issues.append("Possible spotlight marker manipulation")

        return len(issues) == 0, issues

    def _contains_input_leakage(self, output: str, input_content: str) -> bool:
        """Check if output contains suspicious amount of input"""
        input_words = set(input_content.lower().split())
        output_words = set(output.lower().split())

        if not input_words or not output_words:
            return False

        # Calculate overlap
        overlap = len(input_words & output_words) / len(input_words)

        # If > 80% of input appears in output, flag it
        return overlap > 0.8

    def _has_marker_manipulation(self, output: str) -> bool:
        """Check if output tries to manipulate spotlight markers"""
        suspicious_phrases = [
            "ignore spotlight",
            "remove markers",
            "strip comments",
            "UNTRUSTED_CONTENT_START",
            "UNTRUSTED_CONTENT_END",
        ]

        output_lower = output.lower()
        return any(phrase.lower() in output_lower for phrase in suspicious_phrases)

    def verify_integrity(self, content: str, original_hash: str) -> bool:
        """
        Verify content integrity using hash.

        Args:
            content: Content to verify
            original_hash: Original hash to compare against

        Returns:
            True if integrity verified
        """
        if not self.enable_hash_verification:
            return True

        current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return current_hash == original_hash


class ToolAllowList:
    """
    Manage allowed tools for agent operations.
    Implements strict tool allow-listing to prevent unauthorized operations.
    """

    # Default allowed tools (safe operations)
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

    # High-risk tools requiring human approval
    HUMAN_APPROVAL_TOOLS = {
        "delete_user",
        "delete_assessment",
        "export_all_data",
        "modify_system_settings",
        "access_all_users",
    }

    # Blocked tools (never allowed)
    BLOCKED_TOOLS = {
        "execute_arbitrary_code",
        "execute_system_command",
        "modify_security_settings",
        "access_passwords",
        "bypass_authentication",
        "access_raw_database",
        "modify_database_directly",
    }

    def __init__(
        self,
        custom_allowed_tools: set[str] | None = None,
        custom_blocked_tools: set[str] | None = None,
    ):
        """
        Initialize tool allow-list.

        Args:
            custom_allowed_tools: Additional allowed tools
            custom_blocked_tools: Additional blocked tools
        """
        self.allowed_tools = self.DEFAULT_ALLOWED_TOOLS.copy()
        self.blocked_tools = self.BLOCKED_TOOLS.copy()

        if custom_allowed_tools:
            self.allowed_tools.update(custom_allowed_tools)

        if custom_blocked_tools:
            self.blocked_tools.update(custom_blocked_tools)

        logger.info(
            f"ToolAllowList initialized: "
            f"{len(self.allowed_tools)} allowed, {len(self.blocked_tools)} blocked"
        )

    def is_tool_allowed(
        self, tool_name: str, require_human_approval: bool = False
    ) -> tuple[bool, str | None]:
        """
        Check if tool is allowed.

        Args:
            tool_name: Name of tool to check
            require_human_approval: Whether human approval is required

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check blocked list first
        if tool_name in self.blocked_tools:
            return False, f"Tool '{tool_name}' is explicitly blocked"

        # Check if human approval required
        if tool_name in self.HUMAN_APPROVAL_TOOLS:
            if require_human_approval:
                return True, f"Tool '{tool_name}' requires human approval (approved)"
            return False, f"Tool '{tool_name}' requires human approval (not approved)"

        # Check allowed list
        if tool_name in self.allowed_tools:
            return True, f"Tool '{tool_name}' is allowed"

        # Tool not in any list - block by default
        return False, f"Tool '{tool_name}' not in allow-list (blocked by default)"

    def add_allowed_tool(self, tool_name: str):
        """Add tool to allow-list"""
        self.allowed_tools.add(tool_name)
        logger.info(f"Added tool to allow-list: {tool_name}")

    def add_blocked_tool(self, tool_name: str):
        """Add tool to block-list"""
        self.blocked_tools.add(tool_name)
        logger.info(f"Added tool to block-list: {tool_name}")


class SpotlightingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic content spotlighting.

    Automatically wraps request/response content with spotlighting markers.
    """

    def __init__(
        self,
        app,
        engine: SpotlightingEngine | None = None,
        tool_allowlist: ToolAllowList | None = None,
        enable_path_filtering: bool = True,
    ):
        """
        Initialize spotlighting middleware.

        Args:
            app: FastAPI app
            engine: SpotlightingEngine instance
            tool_allowlist: ToolAllowList instance
            enable_path_filtering: Enable path-based filtering
        """
        super().__init__(app)

        self.engine = engine or SpotlightingEngine()
        self.tool_allowlist = tool_allowlist or ToolAllowList()
        self.enable_path_filtering = enable_path_filtering

        # Paths that don't need spotlighting
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
        }

        # Paths that require strict spotlighting
        self.strict_paths = {
            "/api/v1/ai/",
            "/api/v1/assessments/",
            "/api/v1/analytics/",
        }

        logger.info("SpotlightingMiddleware initialized")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with spotlighting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with spotlighting applied
        """
        path = request.url.path

        # Skip excluded paths
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # Process request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            request = await self._process_request(request, path)

        # Call next middleware/handler
        response = await call_next(request)

        # Process response
        response = await self._process_response(response, path)

        return response

    async def _process_request(self, request: Request, path: str) -> Request:
        """Process incoming request with spotlighting"""
        try:
            # Read request body
            body = await request.body()

            if not body:
                return request

            # Parse JSON
            try:
                data = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, skip spotlighting
                return request

            # Apply spotlighting to text fields
            spotlighted_data = self._spotlight_dict(data, ContentSource.USER)

            # Update request body
            spotlighted_body = json.dumps(spotlighted_data).encode()

            # Replace body in request
            request._body = spotlighted_body

        except Exception as e:
            logger.error(f"Error spotlighting request: {e}")

        return request

    async def _process_response(self, response: Response, path: str) -> Response:
        """Process outgoing response with spotlighting"""
        try:
            # Check if response is JSON
            content_type = response.headers.get("content-type", "")

            if "application/json" not in content_type:
                return response

            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Parse JSON
            try:
                data = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, return as-is
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

            # Validate LLM output if this is AI endpoint
            if any(path.startswith(strict) for strict in self.strict_paths):
                is_valid, issues = self.engine.validate_llm_output(json.dumps(data))

                if not is_valid:
                    logger.warning(f"LLM output validation failed: {issues}")
                    # Return sanitized response
                    data = self._sanitize_response(data)

            # Apply spotlighting to LLM-generated content
            if path.startswith("/api/v1/ai/"):
                spotlighted_data = self._spotlight_dict(data, ContentSource.LLM_OUTPUT)
            else:
                spotlighted_data = data

            # Create new response
            spotlighted_body = json.dumps(spotlighted_data).encode()

            return Response(
                content=spotlighted_body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except Exception as e:
            logger.error(f"Error spotlighting response: {e}")
            return response

    def _spotlight_dict(self, data: Any, source: ContentSource) -> Any:
        """Recursively spotlight dictionary/string values"""
        if isinstance(data, dict):
            return {k: self._spotlight_dict(v, source) for k, v in data.items()}
        if isinstance(data, list):
            return [self._spotlight_dict(item, source) for item in data]
        if isinstance(data, str):
            # Spotlight string content
            spotlighted = self.engine.spotlight_content(data, source)
            return self.engine.wrap_content(data, spotlighted)
        return data

    def _sanitize_response(self, data: Any) -> Any:
        """Sanitize response by removing dangerous content"""
        if isinstance(data, dict):
            return {k: self._sanitize_response(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._sanitize_response(item) for item in data]
        if isinstance(data, str):
            # Remove script tags and dangerous content
            sanitized = re.sub(
                r"<script[^>]*>.*?</script>", "", data, flags=re.IGNORECASE
            )
            sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
            return sanitized
        return data


# ==================== Human Approval System ====================


class HumanApprovalRequired(Exception):
    """Raised when human approval is required"""


class ApprovalManager:
    """
    Manage human approval workflow for sensitive operations.

    Implements a checkpoint system where certain operations require
    explicit human approval before execution.
    """

    def __init__(self, approval_timeout: int = 300):
        """
        Initialize approval manager.

        Args:
            approval_timeout: Approval timeout in seconds (default 5 min)
        """
        self.approval_timeout = approval_timeout
        self.pending_approvals: dict[str, dict] = {}

    def request_approval(
        self, operation: str, context: dict[str, Any], user_id: str
    ) -> str:
        """
        Request human approval for operation.

        Args:
            operation: Operation name
            context: Operation context
            user_id: User requesting approval

        Returns:
            Approval request ID
        """
        approval_id = hashlib.sha256(
            f"{operation}:{user_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        self.pending_approvals[approval_id] = {
            "operation": operation,
            "context": context,
            "user_id": user_id,
            "requested_at": datetime.utcnow(),
            "approved": False,
            "denied": False,
        }

        logger.info(
            f"Human approval requested: {approval_id} "
            f"(operation: {operation}, user: {user_id})"
        )

        return approval_id

    def approve_operation(self, approval_id: str, approver_id: str) -> bool:
        """
        Approve operation.

        Args:
            approval_id: Approval request ID
            approver_id: User approving the operation

        Returns:
            True if approved successfully
        """
        if approval_id not in self.pending_approvals:
            logger.warning(f"Invalid approval ID: {approval_id}")
            return False

        approval = self.pending_approvals[approval_id]

        # Check timeout
        if (
            datetime.utcnow() - approval["requested_at"]
        ).total_seconds() > self.approval_timeout:
            logger.warning(f"Approval request expired: {approval_id}")
            del self.pending_approvals[approval_id]
            return False

        # Check if already processed
        if approval["approved"] or approval["denied"]:
            logger.warning(f"Approval already processed: {approval_id}")
            return False

        # Approve
        approval["approved"] = True
        approval["approved_by"] = approver_id
        approval["approved_at"] = datetime.utcnow()

        logger.info(f"Operation approved: {approval_id} by {approver_id}")
        return True

    def deny_operation(
        self, approval_id: str, denier_id: str, reason: str = ""
    ) -> bool:
        """
        Deny operation.

        Args:
            approval_id: Approval request ID
            denier_id: User denying the operation
            reason: Reason for denial

        Returns:
            True if denied successfully
        """
        if approval_id not in self.pending_approvals:
            logger.warning(f"Invalid approval ID: {approval_id}")
            return False

        approval = self.pending_approvals[approval_id]

        # Check timeout
        if (
            datetime.utcnow() - approval["requested_at"]
        ).total_seconds() > self.approval_timeout:
            logger.warning(f"Approval request expired: {approval_id}")
            del self.pending_approvals[approval_id]
            return False

        # Check if already processed
        if approval["approved"] or approval["denied"]:
            logger.warning(f"Approval already processed: {approval_id}")
            return False

        approval["denied"] = True
        approval["denied_by"] = denier_id
        approval["denied_at"] = datetime.utcnow()
        approval["denial_reason"] = reason

        logger.info(f"Operation denied: {approval_id} by {denier_id} - {reason}")
        return True

    def check_approval(self, approval_id: str) -> tuple[bool, str]:
        """
        Check if operation is approved.

        Args:
            approval_id: Approval request ID

        Returns:
            Tuple of (is_approved, status_message)
        """
        if approval_id not in self.pending_approvals:
            return False, "Invalid approval ID"

        approval = self.pending_approvals[approval_id]

        if approval["approved"]:
            return True, "Operation approved"

        if approval["denied"]:
            return (
                False,
                f"Operation denied: {approval.get('denial_reason', 'No reason provided')}",
            )

        # Check timeout
        if (
            datetime.utcnow() - approval["requested_at"]
        ).total_seconds() > self.approval_timeout:
            return False, "Approval request expired"

        return False, "Approval pending"

    def cleanup_expired(self):
        """Remove expired approval requests"""
        now = datetime.utcnow()
        expired_ids = [
            approval_id
            for approval_id, approval in self.pending_approvals.items()
            if (now - approval["requested_at"]).total_seconds() > self.approval_timeout
        ]

        for approval_id in expired_ids:
            del self.pending_approvals[approval_id]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired approval requests")


# ==================== Convenience Functions ====================

# Global instances
spotlighting_engine = SpotlightingEngine()
tool_allowlist = ToolAllowList()
approval_manager = ApprovalManager()


def spotlight_user_input(content: str, metadata: dict | None = None) -> str:
    """
    Convenience function to spotlight user input.

    Usage:
        from app.middleware.spotlighting import spotlight_user_input

        safe_prompt = spotlight_user_input(user_prompt)
    """
    spotlighted = spotlighting_engine.spotlight_content(
        content=content,
        source=ContentSource.USER,
        trust_level=TrustLevel.UNTRUSTED,
        metadata=metadata,
    )
    return spotlighting_engine.wrap_content(content, spotlighted)


def validate_tool_use(tool_name: str, require_approval: bool = False) -> bool:
    """
    Convenience function to validate tool use.

    Usage:
        from app.middleware.spotlighting import validate_tool_use

        if not validate_tool_use("export_all_data", require_approval=True):
            raise HumanApprovalRequired("This operation requires human approval")

    Raises:
        HumanApprovalRequired: If tool not allowed or approval required
    """
    is_allowed, reason = tool_allowlist.is_tool_allowed(tool_name, require_approval)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Tool not allowed: {reason}"
        )

    return True


def request_human_approval(
    operation: str, context: dict[str, Any], user_id: str
) -> str:
    """
    Convenience function to request human approval.

    Usage:
        from app.middleware.spotlighting import request_human_approval, check_human_approval

        approval_id = request_human_approval("delete_user", {"user_id": 123}, current_user.id)

        # Later...
        is_approved, message = check_human_approval(approval_id)
    """
    return approval_manager.request_approval(operation, context, user_id)


def check_human_approval(approval_id: str) -> tuple[bool, str]:
    """
    Convenience function to check human approval status.

    Returns:
        Tuple of (is_approved, status_message)
    """
    return approval_manager.check_approval(approval_id)


# ==================== Usage Examples ====================


def example_usage():
    """Example usage of spotlighting system"""

    # Example 1: Spotlight user input
    logger.info("Example 1: Spotlighting user input")
    user_input = "Tell me about personality assessment results"
    spotlighted = spotlight_user_input(user_input)
    logger.info(f"Original: {user_input}")
    logger.info(f"Spotlighted:\n{spotlighted}\n")

    # Example 2: Validate LLM output
    logger.info("Example 2: Validating LLM output")
    llm_output = "Here are the assessment results..."
    is_valid, issues = spotlighting_engine.validate_llm_output(llm_output)
    logger.info(f"Valid: {is_valid}")
    logger.info(f"Issues: {issues}\n")

    # Example 3: Check tool allow-list
    logger.info("Example 3: Checking tool allow-list")
    tool_name = "export_all_data"
    is_allowed, reason = tool_allowlist.is_tool_allowed(tool_name)
    logger.info(f"Tool: {tool_name}")
    logger.info(f"Allowed: {is_allowed}")
    logger.info(f"Reason: {reason}\n")

    # Example 4: Request human approval
    logger.info("Example 4: Requesting human approval")
    approval_id = request_human_approval(
        operation="delete_user",
        context={"user_id": 123, "reason": "policy violation"},
        user_id="admin_456",
    )
    logger.info(f"Approval ID: {approval_id}")

    # Simulate approval
    approval_manager.approve_operation(approval_id, approver_id="security_admin")
    is_approved, message = check_human_approval(approval_id)
    logger.info(f"Approved: {is_approved}")
    logger.info(f"Message: {message}\n")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("SPOTLIGHTING MIDDLEWARE - LLM Security")
    logger.info("=" * 80)
    example_usage()
