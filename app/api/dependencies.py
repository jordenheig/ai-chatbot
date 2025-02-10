"""API dependencies for the RAG Chatbot.

This module provides FastAPI dependencies for:
- Database session management
- User authentication
- Request validation
"""

from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.crud.crud_user import user_crud

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

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

async def verify_token(token: str, credentials_exception: HTTPException, db: Session):
    """Verify JWT token and return user.
    
    Args:
        token: JWT token to verify
        credentials_exception: Exception to raise if verification fails
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = user_crud.get_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

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
    return await verify_token(token, credentials_exception, db) 