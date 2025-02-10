"""Authentication routes for the RAG Chatbot.

This module handles:
- User registration
- Login and token generation
- Password reset
- Session management
- Token validation
- User profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict

from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash
)
from app.core.config import settings
from app.db.repositories import UserRepository
from app.schemas.user import UserCreate, User, UserLogin, Token
from app.api.dependencies import get_db
from app.core.logging import logger

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Register a new user.
    
    Args:
        user_data: User registration data (email and password)
        db: Database session
        
    Returns:
        Token object containing access token and token type
        
    Raises:
        HTTPException: If email already exists or validation fails
        
    Note:
        Password is automatically hashed before storage
    """
    try:
        # Check if user exists
        user_repo = UserRepository(db)
        if user_repo.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = user_repo.create_user(
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        # Generate access token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"New user registered: {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(
            "User registration failed",
            extra={"email": user_data.email, "error": str(e)}
        )
        raise

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Authenticate user and generate access token.
    
    Args:
        form_data: OAuth2 form containing username (email) and password
        db: Database session
        
    Returns:
        Dict containing access token and token type
        
    Raises:
        HTTPException: If authentication fails
        
    Note:
        Uses OAuth2 password flow for authentication
    """
    try:
        # Verify user exists
        user = UserRepository(db).get_user_by_email(form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate access token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(
            "Login failed",
            extra={
                "email": form_data.username,
                "error": str(e)
            }
        )
        raise

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get information about the currently authenticated user.
    
    Args:
        current_user: Currently authenticated user (from token)
        
    Returns:
        User object with profile information
        
    Note:
        Requires valid authentication token
    """
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """Log out current user.
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        Success message
        
    Note:
        Client should discard the access token after logout
    """
    try:
        logger.info(f"User logged out: {current_user.email}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(
            "Logout failed",
            extra={"user_id": current_user.id, "error": str(e)}
        )
        raise

@router.post("/reset-password")
async def reset_password(
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Initiate password reset process.
    
    Args:
        email: User's email address
        db: Database session
        
    Returns:
        Success message
        
    Note:
        Sends password reset link to user's email
        (Email sending functionality to be implemented)
    """
    try:
        user = UserRepository(db).get_user_by_email(email)
        if user:
            # TODO: Implement password reset email sending
            logger.info(f"Password reset requested for: {email}")
            return {
                "message": "If an account exists with this email, "
                          "you will receive a password reset link"
            }
        return {
            "message": "If an account exists with this email, "
                      "you will receive a password reset link"
        }
    except Exception as e:
        logger.error(
            "Password reset failed",
            extra={"email": email, "error": str(e)}
        )
        raise 