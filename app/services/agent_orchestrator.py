"""
Agent Orchestration Layer

This module provides the orchestration layer for AI agent tool invocations.
It enforces the agent tool policy and manages the tool execution lifecycle.

Usage:
    from app.services.agent_orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    # Invoke tool
    result = await orchestrator.invoke_tool(
        user_id="user-123",
        tool_name="db_read_query",
        parameters={"query": "SELECT * FROM assessments LIMIT 10"},
        context={"ip_address": "192.168.1.1", "user_agent": "..."}
    )
"""

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

from app.services.agent_tool_middleware import TOOL_REGISTRY, AgentToolMiddleware

# ============================================================================
# Tool Invocation Request
# ============================================================================


class ToolInvocationRequest(BaseModel):
    """Request to invoke an agent tool"""

    user_id: str
    user_role: str
    tool_name: str
    parameters: dict[str, Any]

    # Context
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None


# ============================================================================
# Tool Invocation Response
# ============================================================================


class ToolInvocationResponse(BaseModel):
    """Response from tool invocation"""

    success: bool
    result: Any | None = None
    error: str | None = None
    consent_required: bool = False
    consent_request_id: str | None = None
    execution_time_ms: float | None = None


# ============================================================================
# Agent Orchestrator
# ============================================================================


class AgentOrchestrator:
    """
    Agent orchestration layer with policy enforcement

    Responsibilities:
    1. Validate tool access (middleware)
    2. Request consent if needed
    3. Execute tools
    4. Log all invocations
    5. Return results
    """

    def __init__(self):
        self.middleware = AgentToolMiddleware()

    async def invoke_tool(
        self, request: ToolInvocationRequest
    ) -> ToolInvocationResponse:
        """
        Invoke an agent tool with full policy enforcement

        Args:
            request: Tool invocation request

        Returns:
            ToolInvocationResponse
        """

        try:
            # Step 1: Check tool access
            access_result = await self.middleware.check_tool_access(
                user_id=request.user_id,
                user_role=request.user_role,
                tool_name=request.tool_name,
                parameters=request.parameters,
            )

            # Step 2: Handle consent requirement
            if access_result.consent_required:
                # Request consent from user
                consent_request_id = access_result.consent_request_id

                # In production, this would:
                # 1. Store consent request in database
                # 2. Send WebSocket message to user
                # 3. Wait for user response
                # 4. Check consent status

                # For now, return consent_required response
                return ToolInvocationResponse(
                    success=False,
                    consent_required=True,
                    consent_request_id=consent_request_id,
                    error="Consent required for sensitive action",
                )

            # Step 3: Access denied
            if not access_result.allowed:
                return ToolInvocationResponse(success=False, error=access_result.reason)

            # Step 4: Execute tool
            context = {
                "ip_address": request.ip_address,
                "user_agent": request.user_agent,
                "session_id": request.session_id,
            }

            execution_result = await self.middleware.execute_tool(
                access_result=access_result,
                parameters=request.parameters,
                context=context,
            )

            # Step 5: Return result
            return ToolInvocationResponse(
                success=execution_result["success"],
                result=execution_result.get("result"),
                error=execution_result.get("error"),
                execution_time_ms=execution_result.get("execution_time_ms"),
            )

        except Exception as e:
            # Log error
            return ToolInvocationResponse(
                success=False, error=f"Tool invocation failed: {e!s}"
            )

    async def invoke_tool_with_consent(
        self, request: ToolInvocationRequest, consent_granted: bool
    ) -> ToolInvocationResponse:
        """
        Invoke tool after consent has been granted/denied

        Args:
            request: Original tool invocation request
            consent_granted: Whether user granted consent

        Returns:
            ToolInvocationResponse
        """

        if not consent_granted:
            return ToolInvocationResponse(
                success=False, error="Consent was denied by user"
            )

        # Proceed with tool invocation
        # (consent already granted, so consent_required check will be skipped)
        return await self.invoke_tool(request)

    async def list_available_tools(self, user_role: str) -> list[dict[str, Any]]:
        """
        List tools available to user based on role

        Args:
            user_role: User's role

        Returns:
            List of available tools with metadata
        """

        available_tools = []

        for tool_name, tool_def in TOOL_REGISTRY.items():
            # Check if user's role is allowed
            if user_role in tool_def.allowed_roles:
                available_tools.append(
                    {
                        "name": tool_def.name,
                        "description": tool_def.description,
                        "safety_level": tool_def.safety_level.value,
                        "requires_consent": tool_def.requires_consent,
                        "rate_limit": tool_def.rate_limit,
                    }
                )

        return available_tools

    async def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get information about a specific tool

        Args:
            tool_name: Tool name

        Returns:
            Tool information or None if not found
        """

        tool_def = TOOL_REGISTRY.get(tool_name)

        if tool_def is None:
            return None

        return {
            "name": tool_def.name,
            "description": tool_def.description,
            "safety_level": tool_def.safety_level.value,
            "allowed_roles": tool_def.allowed_roles,
            "requires_consent": tool_def.requires_consent,
            "consent_type": tool_def.consent_type,
            "rate_limit": tool_def.rate_limit,
            "row_limit": tool_def.row_limit,
        }


# ============================================================================
# FastAPI Router for Agent Tools
# ============================================================================

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter(prefix="/agent/tools", tags=["agent-tools"])


@router.post("/invoke", response_model=ToolInvocationResponse)
async def invoke_agent_tool(
    request: ToolInvocationRequest, current_user=Depends(get_current_user)
):
    """
    Invoke an agent tool

    This endpoint enforces the agent tool policy including:
    - Tool allow-list enforcement
    - Role-based access control
    - Consent requirements
    - Rate limiting
    - Audit logging
    """

    # Override user_id from authenticated user
    request.user_id = current_user.id
    request.user_role = current_user.role

    orchestrator = AgentOrchestrator()
    return await orchestrator.invoke_tool(request)


@router.post(
    "/invoke/{consent_request_id}/consent", response_model=ToolInvocationResponse
)
async def grant_tool_consent(
    consent_request_id: str, granted: bool, current_user=Depends(get_current_user)
):
    """
    Grant or deny consent for tool invocation

    Used when a tool requires explicit user consent.
    """

    # Record consent
    middleware = AgentToolMiddleware()
    await middleware.grant_consent(consent_request_id, granted)

    # Get original request from consent request
    # (In production, this would be stored in the database)
    # For now, return error indicating we need the original request
    if granted:
        return ToolInvocationResponse(
            success=False,
            error="Consent granted. Please retry original tool invocation.",
        )
    return ToolInvocationResponse(success=False, error="Consent denied by user.")


@router.get("/list", response_model=list[dict[str, Any]])
async def list_available_tools(current_user=Depends(get_current_user)):
    """
    List tools available to current user
    """

    orchestrator = AgentOrchestrator()
    return await orchestrator.list_available_tools(current_user.role)


@router.get("/{tool_name}", response_model=dict[str, Any])
async def get_tool_info(tool_name: str, current_user=Depends(get_current_user)):
    """
    Get information about a specific tool
    """

    orchestrator = AgentOrchestrator()
    tool_info = await orchestrator.get_tool_info(tool_name)

    if tool_info is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Check if user has access
    if current_user.role not in tool_info["allowed_roles"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return tool_info


# ============================================================================
# WebSocket Endpoint for Real-Time Consent
# ============================================================================

from fastapi import WebSocket


@router.websocket("/ws/consent")
async def consent_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time consent requests

    When a tool requires consent, the agent will send a consent request
    through this WebSocket. The user can then grant or deny consent.
    """

    await websocket.accept()

    try:
        while True:
            # Receive consent request
            data = await websocket.receive_json()

            consent_request_id = data.get("consent_request_id")
            tool_name = data.get("tool_name")
            action_description = data.get("action_description")

            # Display to user (in production, this would be UI)
            await websocket.send_json(
                {
                    "type": "consent_request",
                    "consent_request_id": consent_request_id,
                    "tool_name": tool_name,
                    "action_description": action_description,
                }
            )

            # Wait for user response
            response = await websocket.receive_json()

            consent_granted = response.get("granted", False)

            # Record consent
            middleware = AgentToolMiddleware()
            await middleware.grant_consent(consent_request_id, consent_granted)

            # Send acknowledgment
            await websocket.send_json(
                {
                    "type": "consent_recorded",
                    "consent_request_id": consent_request_id,
                    "granted": consent_granted,
                }
            )

    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
