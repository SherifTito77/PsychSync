# app/api/v1/endpoints/org_chat.py
"""
Organizational Chat Endpoint

Conversational interface for querying organizational intelligence.
"""

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.organizational_chat_service import organizational_chat_service
from app.services.security import get_current_user

router = APIRouter(prefix="/org-chat", tags=["org-chat"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[List[ChatMessage]] = None


@router.post("/{organization_id}/ask", response_model=dict[str, Any])
async def ask_organizational_question(
    organization_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Ask a question about organizational health.

    The system queries relevant intelligence engines (BI, ONA, Pulse,
    Digital Twin, OKR) based on the question, then generates a
    data-grounded answer via Claude.

    Examples:
    - "Why is Engineering's collaboration dropping?"
    - "Which teams are at highest burnout risk?"
    - "What interventions have worked this quarter?"
    - "Should we restructure the Platform team?"
    """
    history = [
        {"role": m.role, "content": m.content}
        for m in (body.conversation_history or [])
    ]

    result = await organizational_chat_service.ask(
        db, organization_id, body.question, history
    )
    return result
