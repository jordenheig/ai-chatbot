"""API dependencies for the RAG Chatbot.

This module provides FastAPI dependencies for:
- Database session management
- User authentication
- Request validation
"""

from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import oauth2_scheme, verify_token
from fastapi import Depends, HTTPException, status

def get_db() -> Generator[Session, None, None]:
    """Get database session.
    
    Yields:
        SQLAlchemy database session
        
    Note:
        Session is automatically closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception, db) 