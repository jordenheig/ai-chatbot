from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.models import ChatSession, ChatMessage
from app.core.security import get_current_user
from app.services.llm_service import generate_response
from app.services.vector_store import search_relevant_docs
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/sessions")
async def create_chat_session(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = ChatSession(
        title="New Chat",
        user_id=current_user.id
    )
    db.add(session)
    db.commit()
    return session

@router.get("/sessions")
async def get_chat_sessions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).all()

@router.post("/messages")
async def send_message(
    message: str,
    session_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message
    )
    db.add(user_message)
    db.commit()
    
    # Search relevant documents
    relevant_docs = await search_relevant_docs(message)
    
    # Generate streaming response
    async def response_stream():
        async for token in generate_response(message, relevant_docs):
            yield token
    
    return StreamingResponse(response_stream()) 