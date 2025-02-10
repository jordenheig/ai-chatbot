from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from app.db.models import ChatSession, ChatMessage
from app.core.security import get_current_user
from app.services.llm_service import generate_chat_response
from app.services.vector_store import vector_store
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_db
from app.services.rag_service import rag_service
from app.db.repositories import ChatRepository
from app.core.logging import logger

router = APIRouter()

"""Chat endpoints for the RAG Chatbot.

This module handles:
- Chat session management
- Message processing
- WebSocket connections
- RAG-powered responses
"""

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
    relevant_docs = await vector_store.search_relevant_docs(message)
    
    # Generate streaming response
    async def response_stream():
        async for token in generate_chat_response(message, relevant_docs):
            yield token
    
    return StreamingResponse(response_stream())

@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle WebSocket connection for chat session.
    
    Args:
        websocket: WebSocket connection
        session_id: Chat session ID
        current_user: Authenticated user
        db: Database session
        
    Flow:
        1. Accept WebSocket connection
        2. Load chat session and history
        3. Process incoming messages
        4. Generate and stream responses
        5. Store messages in database
        
    The WebSocket enables:
        - Real-time message streaming
        - Stateful chat sessions
        - Error handling and recovery
    """
    await websocket.accept()
    
    try:
        chat_repo = ChatRepository(db)
        session = chat_repo.get_session(session_id, current_user.id)
        if not session:
            await websocket.close(code=4004)
            return
        
        history = chat_repo.get_session_messages(session_id)
        history_formatted = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
        
        while True:
            message = await websocket.receive_text()
            
            # Store user message
            chat_message = ChatMessage(
                session_id=session_id,
                role="user",
                content=message
            )
            db.add(chat_message)
            db.commit()
            
            try:
                # Generate RAG response
                response_stream = await rag_service.generate_response(
                    query=message,
                    chat_history=history_formatted
                )
                
                # Stream response chunks
                full_response = []
                async for chunk in rag_service.process_stream(response_stream):
                    await websocket.send_text(chunk)
                    full_response.append(chunk)
                
                # Store complete response
                chat_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content="".join(full_response)
                )
                db.add(chat_message)
                db.commit()
                
                # Update chat history
                history_formatted.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "".join(full_response)}
                ])
                
            except Exception as e:
                logger.error(
                    "Chat response error",
                    extra={
                        "session_id": session_id,
                        "error": str(e)
                    }
                )
                await websocket.send_text(
                    "I apologize, but I encountered an error processing your request."
                )
                
    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected",
            extra={"session_id": session_id}
        ) 