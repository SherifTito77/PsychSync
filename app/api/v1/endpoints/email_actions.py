"""
Email Actions API Endpoints
Handle reply, forward, and compose actions
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.email_action_service import email_action_service
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


# Request schemas
class ReplyEmailRequest(BaseModel):
    original_email: dict
    reply_body: str
    reply_all: bool = False


class ForwardEmailRequest(BaseModel):
    original_email: dict
    forward_to: EmailStr
    forward_message: str = ""


class ComposeEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    is_html: bool = False
    in_reply_to: Optional[str] = None
    references: Optional[str] = None


@router.post("/reply")
async def reply_to_email(
    request: ReplyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reply to an email

    Args:
        request: Reply request with original email and reply body
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and message
    """
    # Get user's email for sending
    from_email = current_user.email

    # Send reply
    result = await email_action_service.reply_to_email(
        original_email=request.original_email,
        reply_body=request.reply_body,
        from_email=from_email,
        reply_all=request.reply_all,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/forward")
async def forward_email(
    request: ForwardEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Forward an email

    Args:
        request: Forward request with original email and recipient
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and message
    """
    # Get user's email for sending
    from_email = current_user.email

    # Send forward
    result = await email_action_service.forward_email(
        original_email=request.original_email,
        forward_to=request.forward_to,
        forward_message=request.forward_message,
        from_email=from_email,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/compose")
async def compose_new_email(
    request: ComposeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compose and send a new email

    Args:
        request: Compose request with recipients and content
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and message
    """
    # Get user's email for sending
    from_email = current_user.email

    # Send email
    result = await email_action_service.compose_new_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
        from_email=from_email,
        cc=request.cc,
        bcc=request.bcc,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a raw email (advanced)

    Args:
        request: Send email request with all details
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and message
    """
    # Get user's email for sending
    from_email = current_user.email

    # Send email
    result = await email_action_service.send_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
        from_email=from_email,
        is_html=request.is_html,
        in_reply_to=request.in_reply_to,
        references=request.references,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.get("/drafts")
async def get_draft_emails(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get draft emails for the current user

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of draft emails
    """
    # TODO: Implement drafts storage in database
    return {"drafts": [], "message": "Draft feature coming soon"}


@router.post("/save-draft")
async def save_draft_email(
    request: ComposeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save email as draft

    Args:
        request: Email content to save
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and draft ID
    """
    # TODO: Implement draft saving
    return {
        "success": True,
        "message": "Draft saved (feature coming soon)",
        "draft_id": "placeholder",
    }
