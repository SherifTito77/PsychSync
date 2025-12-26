from fastapi import APIRouter, Depends, HTTPException

from app.middleware.rate_limiter import check_rate_limit
from pydantic import BaseModel
from typing import Dict
from app.dependencies import get_db, get_current_user
from app.services.notifications import notify_user_email, notify_event

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationRequest(BaseModel):
    user_id: int
    event: str
    payload: Dict

class EmailNotificationRequest(BaseModel):
    email: str
    subject: str
    body: str


@check_rate_limit(identifier="public", endpoint_type="public")
@router.post("/send-event")
async def send_notification(req: NotificationRequest, current_user=Depends(get_current_user)):
    notify_event(req.
@check_rate_limit(identifier="public", endpoint_type="public")
user_id, req.event, req.payload)
    return {"status": "sent"}

@router.post("/send-email")
async def send_email_notification(req: EmailNotificationRequest, current_user=Depends(get_current_user)):
    notify_user_email(req.email, req.subject, req.body)
    return {"status": "sent"}