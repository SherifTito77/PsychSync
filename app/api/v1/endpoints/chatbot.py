from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.db.models.user import User
from app.services.ai.mental_health_chatbot import MentalHealthChatbot

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    response: str
    action: str
    crisis_detected: bool
    crisis_level: Optional[str] = None
    crisis_resources: Optional[List[Dict[str, Any]]] = None
    suggested_resources: Optional[List[Dict[str, Any]]] = None
    intent: Optional[str] = None
    sentiment: Optional[float] = None


@router.post("/message", response_model=ChatMessageResponse)
async def send_chatbot_message(
    request: ChatMessageRequest, current_user: User = Depends(get_current_user)
):
    """
    Send a message to the mental health AI chatbot.

    The chatbot will:
    1. Detect potential crisis situations
    2. Provide empathetic support
    3. Suggest relevant resources
    4. Log the conversation for clinical review
    """
    chatbot = MentalHealthChatbot()

    # Handle session ID conversion to UUID
    try:
        if request.session_id:
            # Try parsing as UUID
            session_id = str(UUID(request.session_id))
        else:
            session_id = str(uuid4())
    except (ValueError, AttributeError):
        # If not a valid UUID string (like frontend's 'chat_123'),
        # use a deterministic UUID based on the string
        import hashlib
        from uuid import UUID as PyUUID

        hash_obj = hashlib.md5(request.session_id.encode())
        session_id = str(PyUUID(hash_obj.hexdigest()))

    # Get response from chatbot service
    result = await chatbot.respond(
        user_id=str(current_user.id),
        message=request.message,
        session_id=session_id,
        context=request.context,
    )

    if result.get("action") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get(
                "error", "An error occurred while processing your message"
            ),
        )

    return ChatMessageResponse(**result)
