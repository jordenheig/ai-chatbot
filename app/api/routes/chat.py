from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import List
from app.db.models import ChatSession, ChatMessage
from app.core.security import get_current_user
from app.services.llm_service import generate_response
from app.services.vector_store import search_relevant_docs
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_db
from app.services.rag_service import rag_service
from app.db.repositories import ChatRepository
from fastapi import WebSocketDisconnect

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

@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    await websocket.accept()
    
    try:
        # Get chat session
        chat_repo = ChatRepository(db)
        session = chat_repo.get_session(session_id, current_user.id)
        if not session:
            await websocket.close(code=4004)
            return
        
        # Get chat history
        history = chat_repo.get_session_messages(session_id)
        history_formatted = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
        
        while True:
            # Receive message
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
                # Generate response using RAG
                response_stream = await rag_service.generate_response(
                    query=message,
                    chat_history=history_formatted
                )
                
                # Stream response
                full_response = []
                async for chunk in rag_service.process_stream(response_stream):
                    await websocket.send_text(chunk)
                    full_response.append(chunk)
                
                # Store assistant response
                chat_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content="".join(full_response)
                )
                db.add(chat_message)
                db.commit()
                
                # Update history
                history_formatted.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "".join(full_response)}
                ])
                
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                await websocket.send_text(
                    "I apologize, but I encountered an error processing your request."
                )
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}") 