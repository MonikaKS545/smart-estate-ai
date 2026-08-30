from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.common import ChatSession, ChatMessage, SenderEnum
from app.rag.chatbot import answer_query
from app.schemas.ai_schemas import ChatMessageRequest, ChatMessageResponse
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])


@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get or create the chat session
    if payload.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == payload.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        session = ChatSession(user_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save the user's message
    user_msg = ChatMessage(
        session_id=session.id,
        sender=SenderEnum.user,
        message_text=payload.message,
    )
    db.add(user_msg)
    db.commit()

    # Run the RAG pipeline
    result = answer_query(payload.message)

    # Save the assistant's reply
    assistant_msg = ChatMessage(
        session_id=session.id,
        sender=SenderEnum.assistant,
        message_text=result["response_text"],
    )
    db.add(assistant_msg)
    db.commit()

    return ChatMessageResponse(
        session_id=session.id,
        response_text=result["response_text"],
        referenced_property_ids=result["referenced_property_ids"],
    )