# app/api/v1/endpoints/slack_events.py
"""
Slack Events API Webhook Endpoint

Receives real-time events from Slack for passive signal collection.
Verifies request signatures and processes events asynchronously.
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.slack_events_service import slack_events_service

router = APIRouter(prefix="/slack-events", tags=["slack-events"])


@router.post("/webhook", response_model=dict[str, Any])
async def slack_events_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_slack_request_timestamp: str = Header(default=""),
    x_slack_signature: str = Header(default=""),
):
    """
    Slack Events API webhook receiver.

    Handles:
    - URL verification challenge (initial setup)
    - Message events (metadata only, no content stored)
    - Reaction events (emoji sentiment tracking)
    - Channel membership changes (network edge generation)
    """
    body = await request.body()

    # Verify request signature
    if not slack_events_service.verify_request(
        body, x_slack_request_timestamp, x_slack_signature
    ):
        raise HTTPException(status_code=401, detail="Invalid request signature")

    payload = await request.json()

    # Handle URL verification (Slack sends this during app setup)
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    # Process event
    result = await slack_events_service.process_event(db, payload)
    return result
