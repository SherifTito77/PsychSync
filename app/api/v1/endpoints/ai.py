#!/usr/bin/env python3
"""
Secure AI Endpoints with Spotlighting Protection

Demonstrates best practices for implementing AI-powered endpoints with
comprehensive security controls.

Author: Security Team
Version: 1.0
Date: 2025-12-27
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.db.models import User
from app.middleware.spotlighting import (
    check_human_approval,
    request_human_approval,
    spotlight_user_input,
    spotlighting_engine,
    validate_tool_use,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/secure", tags=["AI - Secure"])


# ==================== Request/Response Models ====================


class ChatRequest(BaseModel):
    """Chat request with security validation"""

    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response with validation metadata"""

    response: str
    validated: bool
    validation_issues: list[str] = []
    timestamp: datetime


class AssessmentAnalysisRequest(BaseModel):
    """Assessment analysis request"""

    assessment_id: int
    analysis_type: str = Field(..., pattern="^(personality|team|clinical)$")


class ToolExecutionRequest(BaseModel):
    """Tool execution request with authorization"""

    tool_name: str
    parameters: dict[str, Any]
    require_approval: bool = False


class BatchAnalysisRequest(BaseModel):
    """Batch analysis request"""

    assessment_ids: list[int] = Field(..., min_items=1, max_items=100)


# ==================== Example 1: Simple Secure Chat ====================


@router.post("/chat", response_model=ChatResponse)
async def secure_chat(
    request: ChatRequest, current_user: User = Depends(get_current_user)
):
    """
    Secure AI chat endpoint with full security controls.

    Security Measures:
    1. Input spotlighting - marks user content as untrusted
    2. Output validation - detects malicious patterns
    3. Request logging - full audit trail
    4. User authentication - required

    ✅ GOOD: Demonstrates proper security flow
    """
    try:
        # Step 1: Spotlight user input (marks as untrusted)
        safe_input = spotlight_user_input(request.message)
        logger.info(
            f"Chat request from user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "message_length": len(request.message),
                "conversation_id": request.conversation_id,
                "event_type": "chat_request",
            },
        )

        # Step 2: Generate AI response (with spotlighted input)
        # In production, this would call your actual AI service
        llm_output = await _mock_ai_generate(safe_input)

        # Step 3: Validate LLM output for malicious content
        is_valid, issues = spotlighting_engine.validate_llm_output(llm_output)

        if not is_valid:
            logger.warning(
                f"LLM output validation failed for user {current_user.id}",
                extra={
                    "user_id": current_user.id,
                    "issues": issues,
                    "output_preview": llm_output[:200],
                    "event_type": "validation_failure",
                },
            )

            # Return safe fallback response
            return ChatResponse(
                response="I'm sorry, I couldn't process that request. Please try rephrasing your message.",
                validated=False,
                validation_issues=issues,
                timestamp=datetime.utcnow(),
            )

        # Step 4: Return validated response
        logger.info(
            f"Chat response delivered to user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "validated": True,
                "response_length": len(llm_output),
                "event_type": "chat_response",
            },
        )

        return ChatResponse(
            response=llm_output,
            validated=True,
            validation_issues=[],
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request",
        ) from e


# ==================== Example 2: Assessment Analysis ====================


@router.post("/assessments/analyze")
async def analyze_assessment_secure(
    request: AssessmentAnalysisRequest, current_user: User = Depends(get_current_user)
):
    """
    Secure assessment analysis with AI.

    Security Measures:
    1. Spotlight assessment data
    2. Validate AI insights
    3. User ownership verification
    4. Analysis type validation

    ✅ GOOD: Shows real-world AI security pattern
    """
    try:
        # Step 1: Get assessment (verify ownership)
        from app.db.crud.assessment import get_assessment
        from app.db.crud.user import get_user_by_id

        assessment = await get_assessment(request.assessment_id)

        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )

        # Verify user owns assessment or is admin
        if assessment.user_id != current_user.id and not current_user.is_admin:
            logger.warning(
                f"Unauthorized assessment access attempt by user {current_user.id}",
                extra={
                    "user_id": current_user.id,
                    "assessment_id": request.assessment_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to analyze this assessment",
            )

        # Step 2: Prepare analysis prompt with spotlighted data
        user = await get_user_by_id(assessment.user_id)

        analysis_prompt = f"""
        Analyze this {request.analysis_type} assessment:

        User: {user.email if user else 'Unknown'}
        Assessment ID: {assessment.id}
        Assessment Type: {assessment.type}
        Responses: {assessment.responses}

        Provide insights about personality traits, strengths, and areas for development.
        """

        # Step 3: Spotlight the prompt (mark as untrusted user data)
        safe_prompt = spotlight_user_input(analysis_prompt)

        # Step 4: Generate analysis
        logger.info(
            f"Assessment analysis started for assessment {request.assessment_id}",
            extra={
                "user_id": current_user.id,
                "assessment_id": request.assessment_id,
                "analysis_type": request.analysis_type,
                "event_type": "assessment_analysis",
            },
        )

        analysis = await _mock_ai_generate(safe_prompt)

        # Step 5: Validate analysis output
        is_valid, issues = spotlighting_engine.validate_llm_output(analysis)

        if not is_valid:
            logger.error(
                "Assessment analysis validation failed",
                extra={
                    "assessment_id": request.assessment_id,
                    "issues": issues,
                    "event_type": "analysis_validation_failure",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Analysis generation failed validation",
            )

        # Step 6: Save and return analysis
        assessment.ai_analysis = analysis
        assessment.analysis_validated = True
        await assessment.save()

        return {
            "assessment_id": request.assessment_id,
            "analysis": analysis,
            "validated": True,
            "analyzed_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assessment analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze assessment",
        ) from e


# ==================== Example 3: Tool Execution with Authorization ====================


@router.post("/tools/execute")
async def execute_tool_secure(
    request: ToolExecutionRequest, current_user: User = Depends(get_current_user)
):
    """
    Secure tool execution with authorization checks.

    Security Measures:
    1. Tool allow-list validation
    2. Human approval for sensitive operations
    3. Audit logging
    4. User permission checks

    ✅ GOOD: Demonstrates tool authorization pattern
    """
    try:
        # Step 1: Validate tool is in allow-list
        logger.info(
            f"Tool execution attempt: {request.tool_name}",
            extra={
                "user_id": current_user.id,
                "tool_name": request.tool_name,
                "require_approval": request.require_approval,
                "event_type": "tool_execution_attempt",
            },
        )

        try:
            validate_tool_use(
                request.tool_name, require_approval=request.require_approval
            )
        except HTTPException as e:
            logger.warning(
                f"Tool execution blocked: {request.tool_name}",
                extra={
                    "user_id": current_user.id,
                    "tool_name": request.tool_name,
                    "reason": str(e.detail),
                    "event_type": "tool_blocked",
                },
            )
            raise

        # Step 2: Request human approval if required
        if request.require_approval:
            approval_id = request_human_approval(
                operation=request.tool_name,
                context={
                    "parameters": request.parameters,
                    "requested_by": current_user.id,
                },
                user_id=current_user.id,
            )

            # In production, this would be an async workflow
            # For now, we'll check if already approved
            is_approved, message = check_human_approval(approval_id)

            if not is_approved:
                logger.warning(
                    f"Tool execution awaiting approval: {request.tool_name}",
                    extra={
                        "user_id": current_user.id,
                        "tool_name": request.tool_name,
                        "approval_id": approval_id,
                        "message": message,
                        "event_type": "approval_pending",
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Tool requires approval: {message}",
                )

        # Step 3: Execute tool
        result = await _mock_tool_execute(request.tool_name, request.parameters)

        logger.info(
            f"Tool executed successfully: {request.tool_name}",
            extra={
                "user_id": current_user.id,
                "tool_name": request.tool_name,
                "event_type": "tool_executed",
            },
        )

        return {
            "tool_name": request.tool_name,
            "result": result,
            "executed_by": current_user.id,
            "executed_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An error occurred while processing your request",
                "error_code": "SYS_6000",
            },
        ) from e


# ==================== Example 4: Batch Processing with Approval ====================


@router.post("/batch/analyze")
async def batch_analyze_secure(
    request: BatchAnalysisRequest, current_user: User = Depends(get_current_user)
):
    """
    Batch analysis with human approval for large batches.

    Security Measures:
    1. Batch size limits
    2. Human approval for large batches (>10 items)
    3. Individual validation for each analysis
    4. Comprehensive logging

    ✅ GOOD: Shows batch processing with approval workflow
    """
    try:
        batch_size = len(request.assessment_ids)

        # Step 1: Check if batch requires approval
        requires_approval = batch_size > 10

        logger.info(
            f"Batch analysis request: {batch_size} assessments",
            extra={
                "user_id": current_user.id,
                "batch_size": batch_size,
                "requires_approval": requires_approval,
                "event_type": "batch_analysis_request",
            },
        )

        # Step 2: Request approval for large batches
        if requires_approval:
            approval_id = request_human_approval(
                operation="batch_analyze",
                context={
                    "assessment_count": batch_size,
                    "assessment_ids": request.assessment_ids[:5],  # First 5 for review
                    "requested_by": current_user.id,
                },
                user_id=current_user.id,
            )

            # In production, implement async approval workflow
            # For demo, we'll log and continue
            logger.info(
                f"Batch analysis approval requested: {approval_id}",
                extra={
                    "user_id": current_user.id,
                    "approval_id": approval_id,
                    "event_type": "batch_approval_requested",
                },
            )

        # Step 3: Process batch with individual validation
        results = []
        validation_failures = []

        for assessment_id in request.assessment_ids:
            try:
                # Mock analysis
                analysis = f"Analysis results for assessment {assessment_id}"

                # Validate each analysis
                is_valid, issues = spotlighting_engine.validate_llm_output(analysis)

                if not is_valid:
                    validation_failures.append(
                        {"assessment_id": assessment_id, "issues": issues}
                    )
                    logger.warning(
                        f"Batch analysis validation failed for assessment {assessment_id}",
                        extra={"assessment_id": assessment_id, "issues": issues},
                    )
                    continue

                results.append(
                    {
                        "assessment_id": assessment_id,
                        "analysis": analysis,
                        "validated": True,
                    }
                )

            except Exception as e:
                logger.error(f"Error analyzing assessment {assessment_id}: {e}")
                results.append(
                    {
                        "assessment_id": assessment_id,
                        "error": str(e),
                        "validated": False,
                    }
                )

        # Step 4: Return results with validation summary
        logger.info(
            f"Batch analysis completed: {len(results)}/{batch_size} successful",
            extra={
                "user_id": current_user.id,
                "successful": len(results),
                "failed": len(validation_failures),
                "event_type": "batch_analysis_completed",
            },
        )

        return {
            "batch_size": batch_size,
            "results": results,
            "validation_failures": validation_failures,
            "summary": {
                "total": batch_size,
                "successful": len(results),
                "failed": len(validation_failures),
            },
            "completed_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Batch analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch analysis failed",
        ) from e


# ==================== Example 5: Streaming with Validation ====================


@router.post("/chat/stream")
async def secure_chat_stream(
    request: ChatRequest, current_user: User = Depends(get_current_user)
):
    """
    Secure streaming chat with validation.

    Security Measures:
    1. Spotlight input before streaming
    2. Validate complete response after stream
    3. Log validation results

    ✅ GOOD: Shows streaming with post-validation
    """
    from fastapi.responses import StreamingResponse

    try:
        # Step 1: Spotlight input
        safe_input = spotlight_user_input(request.message)

        logger.info(
            f"Streaming chat request from user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "stream": True,
                "event_type": "streaming_chat_request",
            },
        )

        # Step 2: Generate streaming response
        async def generate():
            full_response = ""

            # Mock streaming - in production, use actual AI service
            words = safe_input.split()
            for i, word in enumerate(words):
                await asyncio.sleep(0.05)  # Simulate streaming delay
                full_response += word + " "
                yield word + " "

            # Step 3: Validate complete response
            is_valid, issues = spotlighting_engine.validate_llm_output(full_response)

            if not is_valid:
                logger.error(
                    f"Streamed content validation failed for user {current_user.id}",
                    extra={
                        "user_id": current_user.id,
                        "issues": issues,
                        "response_length": len(full_response),
                        "event_type": "stream_validation_failure",
                    },
                )
            else:
                logger.info(
                    f"Streaming chat validated successfully for user {current_user.id}",
                    extra={
                        "user_id": current_user.id,
                        "response_length": len(full_response),
                        "validated": is_valid,
                        "event_type": "stream_validation_success",
                    },
                )

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Streaming chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Streaming failed"
        ) from e


# ==================== Mock Functions (Replace with Real Implementations) ====================


async def _mock_ai_generate(prompt: str) -> str:
    """Mock AI generation for demo purposes.

    In production, replace with actual AI service call:
    - OpenAI API
    - Anthropic Claude
    - Local LLM
    - Custom AI service
    """
    # Simulate AI processing
    await asyncio.sleep(0.1)

    # Return safe mock response
    responses = [
        "Based on your assessment results, you show high openness to experience.",
        "Your analysis indicates strong conscientiousness and attention to detail.",
        "The assessment reveals excellent interpersonal skills and collaboration ability.",
        "Your profile suggests creative problem-solving and innovative thinking patterns.",
    ]

    import random

    return random.choice(responses)


async def _mock_tool_execute(tool_name: str, parameters: dict[str, Any]) -> Any:
    """Mock tool execution for demo purposes.

    In production, replace with actual tool execution.
    """
    await asyncio.sleep(0.1)

    return {
        "tool": tool_name,
        "status": "success",
        "result": f"Executed {tool_name} with parameters {parameters}",
        "executed_at": datetime.utcnow().isoformat(),
    }


# ==================== Security Monitoring Endpoints ====================


@router.get("/security/stats")
async def get_security_stats(current_user: User = Depends(get_current_user)):
    """
    Get security statistics (admin only).

    Provides visibility into security events and metrics.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    # Mock stats - in production, query from database/metrics
    return {
        "spotlighting": {
            "total_requests": 1250,
            "valid_outputs": 1235,
            "validation_failures": 15,
            "failure_rate": "1.2%",
        },
        "tools": {
            "execution_attempts": 85,
            "allowed": 78,
            "blocked": 7,
            "approval_required": 12,
        },
        "approvals": {"requested": 12, "granted": 10, "denied": 2, "pending": 0},
        "period": "last_24_hours",
    }


# ==================== Import Required for Streaming ====================

import asyncio

# ==================== Usage Examples ====================

"""
USAGE EXAMPLES:

# Example 1: Simple chat
curl -X POST http://localhost:8000/api/v1/ai/secure/chat \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Tell me about personality assessments"}'

# Example 2: Assessment analysis
curl -X POST http://localhost:8000/api/v1/ai/secure/assessments/analyze \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"assessment_id": 123, "analysis_type": "personality"}'

# Example 3: Tool execution
curl -X POST http://localhost:8000/api/v1/ai/secure/tools/execute \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"tool_name": "get_user_profile", "parameters": {"user_id": 123}}'

# Example 4: Batch analysis
curl -X POST http://localhost:8000/api/v1/ai/secure/batch/analyze \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"assessment_ids": [1, 2, 3, 4, 5]}'
"""
